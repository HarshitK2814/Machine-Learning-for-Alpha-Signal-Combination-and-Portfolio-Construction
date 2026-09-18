"""Forecast-uncertainty shrinkage and its validation-period tuning (workstream B).

The uncertainty factor of the design is a single parameter, kappa, applied to alphas:

    alpha_shrunk_i = alpha_i / (1 + kappa * (s_i / mean(s))^2)

where ``s_i`` is the dispersion of the model ensemble's forecasts for stock i. kappa = 0 recovers the
non-uncertainty cell exactly, so hypothesis H4 is a clean nested comparison.

kappa is chosen on validation months with a fast diagonal mean-variance proxy portfolio rather than
the full optimiser: the proxy keeps the tuning cost linear in the number of months, and it never
touches test data. The proxy is only used for selection; all reported results use the real optimiser.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..portfolio.alpha_scaling import shrink_by_uncertainty
from ..portfolio.cost_terms import trade_cost_numpy
from ..risk.cache import MonthlyRisk


def proxy_weights(alpha: pd.Series, risk: MonthlyRisk, gross: float = 2.0, weight_cap: float = 0.01) -> pd.Series:
    """Diagonal mean-variance proxy: w ~ alpha / sigma^2, dollar-neutral, capped and gross-scaled."""
    idx = pd.Index(risk.permnos)
    a = alpha.reindex(idx).fillna(0.0).to_numpy(dtype=float)
    vol = risk.stock_vol()
    raw = a / np.clip(vol ** 2, 1e-8, None)
    raw = raw - raw.mean()
    denom = np.abs(raw).sum()
    if denom < 1e-12:
        return pd.Series(np.zeros(len(idx)), index=idx)
    w = np.clip(gross * raw / denom, -weight_cap, weight_cap)
    # restore dollar neutrality by scaling the long and short sides to equal size; this can only
    # shrink positions, so the cap keeps holding
    pos, neg = w > 0, w < 0
    long_sum, short_sum = w[pos].sum(), -w[neg].sum()
    if long_sum > 0 and short_sum > 0:
        target = min(long_sum, short_sum)
        w[pos] *= target / long_sum
        w[neg] *= target / short_sum
    else:
        w = np.zeros_like(w)
    scale = np.abs(w).sum()
    if scale > gross > 0:
        w = gross * w / scale
    return pd.Series(w, index=idx)


def proxy_net_return(w: pd.Series, w_prev: pd.Series, realised: pd.Series, costs: pd.DataFrame,
                     aum: float, impact_k: float, commission_bps: float) -> float:
    """Realised next-month return of the proxy portfolio net of modelled trading costs."""
    idx = w.index
    r = realised.reindex(idx).fillna(0.0).to_numpy(dtype=float)
    prev = w_prev.reindex(idx).fillna(0.0).to_numpy(dtype=float) if w_prev is not None else np.zeros(len(idx))
    c = costs.reindex(idx)
    cost = trade_cost_numpy(w.to_numpy() - prev, c["spread"].to_numpy(), c["sigma_d"].to_numpy(),
                            c["adv_usd"].to_numpy(), aum, impact_k, commission_bps).sum()
    borrow = (c["borrow_fee"].to_numpy() / 12.0 * np.clip(-w.to_numpy(), 0, None)).sum()
    return float((w.to_numpy() * r).sum() - cost - borrow)


def select_kappa(val_alphas: dict, val_costs: dict, val_returns: dict, risk_cache, kappa_grid,
                 unc: dict, aum: float, impact_k: float, commission_bps: float,
                 gross: float = 2.0, weight_cap: float = 0.01) -> tuple[float, dict]:
    """Pick the shrinkage strength that maximises validation net return of the proxy portfolio."""
    scores: dict[float, float] = {}
    for kappa in kappa_grid:
        prev_w, total = None, 0.0
        for date in sorted(val_alphas):
            alpha = shrink_by_uncertainty(val_alphas[date], unc.get(date), kappa)
            risk = risk_cache.monthly(date)
            w = proxy_weights(alpha, risk, gross=gross, weight_cap=weight_cap)
            total += proxy_net_return(w, prev_w, val_returns[date], val_costs[date], aum, impact_k, commission_bps)
            prev_w = w
        scores[float(kappa)] = total
    best = max(scores, key=scores.get) if scores else 0.0
    return float(best), scores
