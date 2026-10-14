"""Falsification audit (design v2, credibility layer).

"Spurious Predictability in Financial Machine Learning" (2026) shows that adaptive specification
search produces significant backtests even when the data-generating process has no predictability.
A modern referee should therefore ask: *what does your pipeline report when there is nothing to
find?* This module answers that question before the referee asks it.

Three controls:

1. **Zero-predictability panel** - the synthetic generator with every planted coefficient set to
   zero. Returns are pure factor structure plus noise; signals are noise. Any measured alpha here is
   produced by the research process itself.
2. **Microstructure placebo** - real signal panel replaced by autocorrelation-matched noise, which
   keeps the turnover and cost profile of the strategy while destroying its information.
3. **Shuffled states** - block-shuffled state variables, which destroy conditioning information but
   keep the marginal distribution (this one is produced by the data workstream as
   ``states_placebo.parquet``).

The audit also reports the **inflation gap**: the difference between the best in-sample/validation
metric found during the search and the realised out-of-sample metric, together with the expected
maximum of that many independent draws. If the realised gap is no larger than the expected gap under
the null, the finding is indistinguishable from search noise.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from ..contracts import DataBundle
from ..synthetic.generate import Truth, generate


def zero_predictability_panel(out_dir: Path | str, n_stocks: int = 400, start: str = "1980-01-31",
                              end: str = "2020-12-31", seed: int = 909) -> dict:
    """Generate a panel with the same structure but no planted predictability at all."""
    null_truth = Truth(b_value=0.0, b_quality=0.0, b_value_x_quality=0.0, b_momentum_normal=0.0,
                       b_momentum_crash=0.0, b_reversal_small_illiquid=0.0, b_investment=0.0,
                       notes="ZERO-PREDICTABILITY NULL: every planted coefficient is zero.")
    return generate(out_dir, n_stocks=n_stocks, start=start, end=end, seed=seed, truth=null_truth)


def microstructure_placebo(bundle: DataBundle, seed: int = 0) -> DataBundle:
    """Replace signals with AR(1) noise matched to each signal's own persistence.

    Turnover and trading costs of a strategy built on these placebos resemble the real thing, so any
    performance difference is information rather than mechanical trading behaviour.
    """
    rng = np.random.default_rng(seed)
    signals = bundle.signals.sort_values(["permno", "date"]).copy()
    sig_cols = [c for c in signals.columns if c.startswith("sig_")]
    out = signals.copy()
    for col in sig_cols:
        series = signals[col].to_numpy(dtype=float)
        grouped = signals.groupby("permno")[col]
        rho = float(np.clip(grouped.apply(lambda s: s.autocorr(1) if len(s) > 5 else 0.0).mean(), -0.95, 0.95))
        noise = rng.normal(0, 1, len(series))
        placebo = np.zeros_like(series)
        placebo[0] = noise[0]
        for i in range(1, len(series)):
            placebo[i] = rho * placebo[i - 1] + np.sqrt(max(1 - rho ** 2, 1e-6)) * noise[i]
        out[col] = placebo.astype("float32")
    # re-rank cross-sectionally so the contract still holds
    out[sig_cols] = out.groupby("date")[sig_cols].transform(
        lambda s: (s.rank(method="first") - 1) / max(len(s) - 1, 1) - 0.5).astype("float32")
    return DataBundle(universe=bundle.universe, signals=out.sort_values(["date", "permno"]).reset_index(drop=True),
                      signal_meta=bundle.signal_meta, targets=bundle.targets, states=bundle.states,
                      cost_inputs=bundle.cost_inputs, source=f"{bundle.source}-placebo")


@dataclass
class InflationGap:
    best_in_sample: float
    realised_out_of_sample: float
    n_trials: int
    trial_correlation: float
    expected_max_under_null: float
    realised_gap: float
    verdict: str


def expected_max_of_trials(n_trials: int, sd: float = 1.0, correlation: float = 0.0) -> float:
    """Expected maximum of ``n_trials`` draws, used as the null benchmark for a specification search.

    Independent draws use the standard extreme-value approximation (as in the deflated Sharpe ratio);
    correlation between trials reduces the effective number of independent searches.
    """
    n = max(int(n_trials), 1)
    effective = max(n * (1.0 - float(np.clip(correlation, 0.0, 0.99))), 1.0)
    if effective <= 1:
        return 0.0
    gamma = 0.5772156649
    z1 = stats.norm.ppf(1 - 1 / effective)
    z2 = stats.norm.ppf(1 - 1 / (effective * np.e))
    return float(sd * ((1 - gamma) * z1 + gamma * z2))


def inflation_gap(best_in_sample: float, realised_out_of_sample: float, n_trials: int,
                  metric_sd: float, trial_correlation: float = 0.0) -> InflationGap:
    """How much of the in-sample-to-out-of-sample drop is explained by the search itself?"""
    expected = expected_max_of_trials(n_trials, sd=metric_sd, correlation=trial_correlation)
    gap = best_in_sample - realised_out_of_sample
    verdict = ("gap is within what the search alone would produce" if gap <= expected else
               "gap exceeds search noise; evidence survives the audit")
    return InflationGap(best_in_sample, realised_out_of_sample, int(n_trials), float(trial_correlation),
                        float(expected), float(gap), verdict)


def audit_report(real_metric: float, null_metrics: dict[str, float], trials: pd.DataFrame | None = None,
                 metric_sd: float | None = None, metric_name: str = "net_sharpe") -> pd.DataFrame:
    """Side-by-side comparison of the real result and every falsification control."""
    rows = [{"scenario": "real data", metric_name: real_metric, "interpretation": "claimed result"}]
    for name, value in null_metrics.items():
        rows.append({"scenario": name, metric_name: value,
                     "interpretation": "should be indistinguishable from zero"})
    frame = pd.DataFrame(rows)
    worst_null = max(abs(v) for v in null_metrics.values()) if null_metrics else 0.0
    frame.attrs["passes_falsification"] = bool(abs(real_metric) > 2 * worst_null) if worst_null else True
    if trials is not None and len(trials) and metric_sd:
        best = float(trials["val_metric"].max())
        gap = inflation_gap(best, real_metric, len(trials), metric_sd)
        frame.attrs["inflation_gap"] = gap.__dict__
    return frame
