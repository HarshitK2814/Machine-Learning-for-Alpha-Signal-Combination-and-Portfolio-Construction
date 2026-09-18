"""Shared machinery for the model cells (workstream B).

Feature construction, target construction, validation metrics and the hyperparameter loop live here
so that every cell differs *only* in the ingredient the factorial design switches on.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..contracts import DataBundle, Split, log_trial
from ..contracts.interfaces import CellSpec

# States used for linear interactions (the full set is available to nonlinear cells).
DEFAULT_INTERACTION_STATES = ["MKTVOL", "BEAR", "ILLIQ", "SENT", "CREDIT", "TERM"]


@dataclass
class FeatureSpec:
    """Which columns a cell sees. Conditional cells add state columns and theme x state interactions."""

    signal_cols: list[str]
    miss_cols: list[str] = field(default_factory=list)
    theme_cols: list[str] = field(default_factory=list)
    state_cols: list[str] = field(default_factory=list)
    interaction_cols: list[str] = field(default_factory=list)

    @property
    def all(self) -> list[str]:
        return [*self.signal_cols, *self.miss_cols, *self.theme_cols, *self.state_cols, *self.interaction_cols]


def build_design(bundle: DataBundle, spec: CellSpec, horizon: int = 1,
                 interaction_states: list[str] | None = None) -> tuple[pd.DataFrame, FeatureSpec]:
    """Join signals, targets, states and cost inputs into one modelling frame.

    Conditional cells get: the state variables themselves, plus theme-composite x state interactions.
    Interactions are built on 13 theme composites rather than on all ~150 signals, which keeps the
    linear conditional cell estimable and makes its coefficients interpretable (experiment E61).
    """
    interaction_states = interaction_states or DEFAULT_INTERACTION_STATES
    signals, meta, states = bundle.signals, bundle.signal_meta, bundle.states
    signal_cols = [c for c in signals.columns if c.startswith("sig_")]
    miss_cols = [c for c in signals.columns if c.startswith("miss_")]

    universe = bundle.universe.loc[bundle.universe["in_universe"], ["date", "permno", "me", "ff49"]]
    target_col = f"r_{horizon}m"
    df = (universe
          .merge(signals, on=["date", "permno"], how="inner")
          .merge(bundle.targets[["date", "permno", target_col, "ret_next"]], on=["date", "permno"], how="left")
          .merge(bundle.cost_inputs, on=["date", "permno"], how="left"))

    theme_frames = {}
    for theme, group in meta.groupby("theme"):
        cols = [c for c in group["signal"] if c in df.columns]
        if cols:
            theme_frames[f"thm_{theme}"] = df[cols].mean(axis=1).astype("float32")
    theme_cols = list(theme_frames)
    df = pd.concat([df, pd.DataFrame(theme_frames, index=df.index)], axis=1)

    state_cols: list[str] = []
    interaction_cols: list[str] = []
    if spec.is_conditional:
        state_cols = [c for c in states.columns if c != "date"]
        df = df.merge(states, on="date", how="left")
        df[state_cols] = df[state_cols].fillna(0.0)
        blocks = {}
        for s in [c for c in interaction_states if c in state_cols]:
            for t in theme_cols:
                name = f"{t}_x_{s}"
                blocks[name] = (df[t] * df[s]).astype("float32")
                interaction_cols.append(name)
        if blocks:
            df = pd.concat([df, pd.DataFrame(blocks, index=df.index)], axis=1)

    df["y"] = df.groupby("date")[target_col].transform(lambda v: v - v.mean())   # cross-sectionally demeaned
    df = df.sort_values(["date", "permno"]).reset_index(drop=True)
    features = FeatureSpec(signal_cols, miss_cols, theme_cols, state_cols, interaction_cols)
    return df, features


def split_frames(df: pd.DataFrame, split: Split) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[split.mask(df["date"], "train") & df["y"].notna()]
    val = df[split.mask(df["date"], "val") & df["y"].notna()]
    test = df[split.mask(df["date"], "test")]
    return train, val, test


def rank_ic(pred: np.ndarray, actual: np.ndarray, dates: pd.Series) -> float:
    """Mean monthly Spearman correlation between predictions and realised returns."""
    frame = pd.DataFrame({"date": pd.to_datetime(dates).to_numpy(), "p": pred, "a": actual}).dropna()
    if frame.empty:
        return float("nan")
    per_month = frame.groupby("date").apply(lambda d: d["p"].corr(d["a"], method="spearman"), include_groups=False)
    return float(per_month.mean())


def grid(params: dict) -> list[dict]:
    """Cartesian product of a hyperparameter dictionary (scalars are treated as fixed)."""
    keys = [k for k, v in params.items() if isinstance(v, (list, tuple))]
    fixed = {k: v for k, v in params.items() if not isinstance(v, (list, tuple))}
    if not keys:
        return [dict(fixed)]
    out = []
    for combo in itertools.product(*[params[k] for k in keys]):
        item = dict(fixed)
        item.update(dict(zip(keys, combo)))
        out.append(item)
    return out


def select_by_validation(candidates, train, val, features: list[str], run_id: str, strategy: str,
                         cell: str, split: Split, seed: int = 0):
    """Fit every grid point, log it as a trial, and keep the one with the best validation rank IC.

    Logging losing configurations is not optional: the deflated Sharpe ratio and the probability of
    backtest overfitting are only honest if the trial count is complete.
    """
    best, best_metric, best_params = None, -np.inf, None
    for model, params in candidates:
        model.fit(train, val, features, "y")
        pred = model.predict(val, features)["score"].to_numpy()
        metric = rank_ic(pred, val["y"].to_numpy(), val["date"])
        log_trial(run_id, strategy, cell, params, seed, split.train_end, metric if np.isfinite(metric) else 0.0)
        if np.isfinite(metric) and metric > best_metric:
            best, best_metric, best_params = model, metric, params
    if best is None:  # pragma: no cover - only if every fit failed
        raise RuntimeError(f"no candidate model could be fitted for cell {cell} {split.label}")
    return best, best_metric, best_params
