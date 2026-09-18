"""Turning model scores into comparable alphas (workstream B).

Every prediction-loss cell and every baseline goes through the same scaling, so no model can win
simply by producing larger numbers. Following the Grinold convention:

    alpha_i = IC * sigma_i * z_i

where ``z`` is the cross-sectional z-score of the model's score, ``sigma_i`` is the stock's
predicted monthly volatility from the risk model, and ``IC`` is the model's *validation-period*
information coefficient (never the test period).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..risk.structural import RiskModel


def cross_sectional_z(scores: pd.Series, clip: float = 4.0) -> pd.Series:
    s = scores.astype(float)
    mu, sd = s.mean(), s.std(ddof=0)
    if not np.isfinite(sd) or sd < 1e-12:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return ((s - mu) / sd).clip(-clip, clip)


def stock_volatility(risk: RiskModel) -> pd.Series:
    """Predicted monthly total volatility per stock from the risk model."""
    B = risk.B.to_numpy(dtype=float)
    F = risk.F.to_numpy(dtype=float)
    common = np.einsum("ij,jk,ik->i", B, F, B)
    return pd.Series(np.sqrt(np.clip(common + risk.D.to_numpy(dtype=float), 1e-12, None)), index=risk.B.index)


def information_coefficient(scores: pd.Series, realised: pd.Series, dates: pd.Series,
                            method: str = "rank", floor: float = 0.005, cap: float = 0.10) -> float:
    """Average per-month IC between scores and realised returns, clipped to a sane band."""
    df = pd.DataFrame({"date": pd.to_datetime(dates), "s": scores.to_numpy(), "r": realised.to_numpy()}).dropna()
    if df.empty:
        return floor
    per_month = df.groupby("date").apply(
        lambda d: d["s"].corr(d["r"], method="spearman" if method == "rank" else "pearson"),
        include_groups=False)
    ic = float(per_month.mean())
    if not np.isfinite(ic):
        return floor
    return float(np.clip(ic, -cap, cap)) if abs(ic) > floor else float(np.sign(ic) * floor or floor)


def grinold_alpha(scores: pd.Series, risk: RiskModel, ic: float) -> pd.Series:
    """Scale scores into expected monthly excess returns."""
    idx = scores.index.intersection(risk.B.index)
    z = cross_sectional_z(scores.loc[idx])
    sigma = stock_volatility(risk).reindex(idx)
    return (ic * sigma * z).rename("alpha")


def shrink_by_uncertainty(alpha: pd.Series, unc_sd: pd.Series | None, kappa: float) -> pd.Series:
    """Uncertainty shrinkage: alpha_i / (1 + kappa * (s_i / mean(s))^2).

    With kappa = 0 this is the identity, so the "no uncertainty" cells are exactly nested inside the
    uncertainty cells (hypothesis H4 is then a clean one-parameter comparison).
    """
    if unc_sd is None or kappa == 0:
        return alpha
    s = unc_sd.reindex(alpha.index).astype(float)
    mean = s.mean()
    if not np.isfinite(mean) or mean <= 0:
        return alpha
    ratio = (s / mean).fillna(1.0) ** 2
    return alpha / (1.0 + kappa * ratio)
