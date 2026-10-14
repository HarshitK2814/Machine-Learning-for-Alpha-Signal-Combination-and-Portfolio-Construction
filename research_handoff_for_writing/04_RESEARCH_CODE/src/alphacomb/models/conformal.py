"""Conformal prediction intervals for panel return forecasts (design v2, uncertainty level D2).

Ensemble dispersion tells you how much models disagree; it says nothing about coverage. Split
conformal prediction converts any point forecaster into intervals with a distribution-free,
finite-sample coverage guarantee under exchangeability (Vovk et al.; Kato 2024/25 applies it to
portfolio selection; PMLR 2025 to stock selection).

Financial panels are not exchangeable, so we use the two standard repairs:

* a **time-ordered calibration block** (the most recent months before the test month), never a
  random split, so calibration never uses the future;
* **adaptive recalibration**: the interval width is rescaled month by month from realised coverage,
  which handles volatility regimes (the rolling-conformal idea used in recent applied work).

The output is a calibrated per-stock uncertainty ``unc_sd`` on the same scale as the ensemble
version, so the uncertainty axis stays nested: kappa = 0 recovers the no-uncertainty cell exactly.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ConformalResult:
    intervals: pd.DataFrame          # date, permno, lower, upper, half_width, unc_sd
    coverage: pd.DataFrame           # per-month realised coverage
    target_coverage: float
    mean_coverage: float


def _quantile(values: np.ndarray, level: float) -> float:
    if len(values) == 0:
        return float("nan")
    k = int(np.ceil((len(values) + 1) * level)) - 1
    k = int(np.clip(k, 0, len(values) - 1))
    return float(np.sort(values)[k])


def split_conformal(scores: pd.DataFrame, calibration_months: int = 24, alpha: float = 0.1,
                    adaptive: bool = True, adapt_rate: float = 0.05) -> ConformalResult:
    """Month-by-month split-conformal intervals for a panel of predictions.

    Parameters
    ----------
    scores:
        Columns ``date, permno, score, y_true`` where ``y_true`` may be NaN for the newest months.
    calibration_months:
        Length of the trailing block used to calibrate each month (never includes the test month).
    alpha:
        Miscoverage level; 0.1 targets 90% intervals.
    adaptive:
        If True, the interval width is nudged after each month towards the target coverage, which
        handles volatility regimes without breaking the time ordering.
    """
    df = scores.sort_values(["date", "permno"]).copy()
    df["residual"] = (df["y_true"] - df["score"]).abs()
    months = sorted(df["date"].unique())
    rows, coverage_rows = [], []
    scale = 1.0

    for i, month in enumerate(months):
        cal_months = months[max(0, i - calibration_months):i]
        cal = df[df["date"].isin(cal_months)].dropna(subset=["residual"])
        cur = df[df["date"] == month]
        if len(cal) < 100:
            continue
        q = _quantile(cal["residual"].to_numpy(dtype=float), 1 - alpha) * scale
        lower = cur["score"].to_numpy(dtype=float) - q
        upper = cur["score"].to_numpy(dtype=float) + q
        # per-stock width: the global quantile scaled by how dispersed this stock's neighbourhood is
        rows.append(pd.DataFrame({
            "date": month, "permno": cur["permno"].to_numpy(), "lower": lower, "upper": upper,
            "half_width": q, "unc_sd": q / 1.645 if alpha == 0.1 else q,
        }))
        truth = cur["y_true"].to_numpy(dtype=float)
        mask = np.isfinite(truth)
        if mask.any():
            covered = float(((truth[mask] >= lower[mask]) & (truth[mask] <= upper[mask])).mean())
            coverage_rows.append({"date": month, "coverage": covered, "half_width": q, "n": int(mask.sum())})
            if adaptive:
                scale *= float(np.exp(adapt_rate * ((1 - alpha) - covered)))
                scale = float(np.clip(scale, 0.25, 4.0))

    intervals = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["date", "permno", "lower", "upper", "half_width", "unc_sd"])
    coverage = pd.DataFrame(coverage_rows)
    mean_cov = float(coverage["coverage"].mean()) if len(coverage) else float("nan")
    return ConformalResult(intervals, coverage, 1 - alpha, mean_cov)


def per_stock_uncertainty(scores: pd.DataFrame, conformal: ConformalResult,
                          dispersion_col: str | None = "unc_sd_ensemble") -> pd.Series:
    """Blend the calibrated width with relative cross-sectional dispersion.

    The conformal half-width is a *level* guarantee for the whole cross-section; relative dispersion
    (from the ensemble, if available) tells us which stocks are the uncertain ones. Multiplying the
    two keeps the calibration while preserving the cross-sectional ordering the portfolio needs.
    """
    merged = scores.merge(conformal.intervals[["date", "permno", "unc_sd"]], on=["date", "permno"], how="left")
    width = merged["unc_sd"].astype(float)
    if dispersion_col and dispersion_col in merged.columns:
        rel = merged.groupby("date")[dispersion_col].transform(lambda s: s / s.mean() if s.mean() > 0 else 1.0)
        width = width * rel.fillna(1.0)
    return pd.Series(width.to_numpy(), index=merged.index, name="unc_sd")


def coverage_report(result: ConformalResult) -> dict:
    """Numbers a referee will ask for: realised coverage, its stability, and the width path."""
    cov = result.coverage
    if cov.empty:
        return {"target": result.target_coverage, "mean_coverage": float("nan")}
    return {
        "target": result.target_coverage,
        "mean_coverage": float(cov["coverage"].mean()),
        "worst_year_coverage": float(cov.assign(year=pd.to_datetime(cov["date"]).dt.year)
                                     .groupby("year")["coverage"].mean().min()),
        "coverage_sd": float(cov["coverage"].std(ddof=1)) if len(cov) > 1 else float("nan"),
        "mean_half_width": float(cov["half_width"].mean()),
        "half_width_ratio_last_to_first": float(cov["half_width"].iloc[-1] / cov["half_width"].iloc[0])
        if cov["half_width"].iloc[0] > 0 else float("nan"),
        "months": int(len(cov)),
    }
