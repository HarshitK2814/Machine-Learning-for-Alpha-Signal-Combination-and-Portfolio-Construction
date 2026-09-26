"""Online expert aggregation: the models re-weight themselves from realised after-tax results.

The request behind this module is "I want the models to change on their own". There are two ways to
do that, and only one of them survives a referee.

The version that does not survive: pick, each month, whichever model looked best recently. That is a
specification search run once per month, it has no guarantee, and the falsification audit in
``alphacomb.validation`` shows how much spurious performance an adaptive search manufactures.

The version that does: fix an aggregation rule *ex ante*, feed it only realised out-of-sample
outcomes, and inherit a regret bound. The exponentially weighted average forecaster (Vovk 1990;
Littlestone and Warmuth 1994; Cesa-Bianchi and Lugosi 2006) guarantees that cumulative performance
falls short of the single best model in hindsight by at most O(sqrt(T log N)) - without knowing in
advance which model that is. Herbster and Warmuth's (1998) fixed-share variant goes further and
competes with the best *sequence* of models, which is the right object when the world has regimes.

Nothing here is tuned on test data. The learning rate is either the parameter-free
``eta_t = sqrt(8 log N / t)`` or a value chosen on validation months only, and the whole update uses
information available strictly before the month it acts on.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class HedgeConfig:
    """All of these are fixed before the out-of-sample period starts."""

    eta: float | None = None       # None -> parameter-free sqrt(8 log N / t)
    share: float = 0.02            # Herbster-Warmuth fixed share; 0 -> plain Hedge
    floor: float = 1e-4            # minimum weight, so a model can recover after a bad run
    scale: float | None = None     # loss scale; None -> running robust estimate
    long_only: bool = True         # weights on the simplex (no shorting another model)
    warmup: int = 12               # months of equal weighting before the rule starts acting


@dataclass
class HedgeState:
    experts: list[str]
    weights: np.ndarray
    t: int = 0
    cumulative: np.ndarray = field(default_factory=lambda: np.zeros(0))

    def as_series(self) -> pd.Series:
        return pd.Series(self.weights, index=self.experts)


class HedgeAggregator:
    """Exponentially weighted average forecaster with an optional fixed share.

    ``update`` is called once per month with each expert's realised reward for that month (we use
    the after-tax net return, which is the quantity the investor actually keeps). The weights it
    returns are the ones to use *next* month.
    """

    def __init__(self, experts: list[str], cfg: HedgeConfig | None = None):
        if len(experts) < 2:
            raise ValueError("aggregation needs at least two experts")
        self.cfg = cfg or HedgeConfig()
        n = len(experts)
        self.state = HedgeState(experts=list(experts), weights=np.full(n, 1.0 / n),
                                cumulative=np.zeros(n))
        self._rewards: list[np.ndarray] = []

    # ------------------------------------------------------------------ properties
    @property
    def n(self) -> int:
        return len(self.state.experts)

    def _eta(self) -> float:
        if self.cfg.eta is not None:
            return float(self.cfg.eta)
        t = max(self.state.t, 1)
        return float(np.sqrt(8.0 * np.log(self.n) / t))

    def _scale(self) -> float:
        if self.cfg.scale is not None:
            return float(self.cfg.scale)
        if not self._rewards:
            return 1.0
        flat = np.concatenate(self._rewards)
        mad = float(np.median(np.abs(flat - np.median(flat))))
        return max(4.0 * 1.4826 * mad, 1e-6)   # roughly a 4-sigma range for a normal

    # ------------------------------------------------------------------ the rule
    def update(self, rewards: pd.Series | np.ndarray) -> pd.Series:
        """Feed one month of realised expert rewards; return the weights to use next month."""
        r = (rewards.reindex(self.state.experts).to_numpy(dtype=float)
             if isinstance(rewards, pd.Series) else np.asarray(rewards, dtype=float))
        if r.shape != (self.n,):
            raise ValueError(f"expected {self.n} rewards, got {r.shape}")
        r = np.nan_to_num(r, nan=0.0)
        self._rewards.append(r.copy())
        self.state.t += 1
        self.state.cumulative += r

        if self.state.t <= self.cfg.warmup:
            self.state.weights = np.full(self.n, 1.0 / self.n)
            return self.state.as_series()

        scaled = np.clip(r / self._scale(), -1.0, 1.0)     # bounded losses: the bound needs this
        log_w = np.log(np.maximum(self.state.weights, 1e-300)) + self._eta() * scaled
        log_w -= log_w.max()
        w = np.exp(log_w)
        w /= w.sum()

        if self.cfg.share > 0:                             # Herbster-Warmuth: track a changing best
            w = (1.0 - self.cfg.share) * w + self.cfg.share / self.n
        if self.cfg.floor > 0:
            w = np.maximum(w, self.cfg.floor)
        w /= w.sum()
        self.state.weights = w
        return self.state.as_series()

    # ------------------------------------------------------------------ diagnostics
    def regret_bound(self) -> float:
        """Worst-case shortfall against the best fixed expert, in the units of the reward."""
        t = max(self.state.t, 1)
        return float(self._scale() * np.sqrt(0.5 * t * np.log(self.n)))

    def realised_regret(self, realised_total: float) -> float:
        """Cumulative reward of the best expert in hindsight minus what the aggregate achieved."""
        return float(self.state.cumulative.max() - realised_total)


def run_aggregation(expert_returns: pd.DataFrame, cfg: HedgeConfig | None = None) -> pd.DataFrame:
    """Replay the rule over a panel of monthly expert returns (index = date, columns = experts).

    Returns one row per month with the weights that were *in force* that month, the realised
    aggregate return, and the running regret. Because the weights in force at month t come from
    ``update`` calls on months up to t-1, the series is strictly out of sample.
    """
    experts = list(expert_returns.columns)
    agg = HedgeAggregator(experts, cfg)
    rows = []
    weights = agg.state.as_series()
    for date, row in expert_returns.sort_index().iterrows():
        realised = float((weights * row.reindex(experts)).sum())
        rows.append({"date": pd.Timestamp(date), "aggregate_ret": realised,
                     "n_effective": float(1.0 / np.sum(weights.to_numpy() ** 2)),
                     **{f"w_{e}": float(weights[e]) for e in experts}})
        weights = agg.update(row)
    frame = pd.DataFrame(rows)
    total = frame["aggregate_ret"].sum()
    frame.attrs["regret_bound"] = agg.regret_bound()
    frame.attrs["realised_regret"] = agg.realised_regret(total)
    frame.attrs["best_expert"] = experts[int(np.argmax(agg.state.cumulative))]
    frame.attrs["best_expert_total"] = float(agg.state.cumulative.max())
    frame.attrs["aggregate_total"] = float(total)
    return frame


def equal_weight_benchmark(expert_returns: pd.DataFrame) -> pd.Series:
    """The benchmark online learning has to beat, and frequently does not."""
    return expert_returns.mean(axis=1)


def best_in_hindsight(expert_returns: pd.DataFrame) -> pd.Series:
    """Not implementable - reported only as the ceiling the regret bound is measured against."""
    return expert_returns[expert_returns.sum().idxmax()]
