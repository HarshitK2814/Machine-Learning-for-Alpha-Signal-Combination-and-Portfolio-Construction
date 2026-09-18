"""Transaction-cost terms used *inside* the optimiser (workstream B).

Absar owns the evaluation-time cost model (``alphacomb.costs.trade_cost``, contract C6 consumer).
The optimiser needs the same cost function expressed as a convex term, so the two implementations
must agree exactly. ``tests/portfolio/test_cost_terms.py`` pins the agreed formula:

    cost_i(dw) = 0.5 * spread_i * |dw_i|                       (half effective spread)
               + commission * |dw_i|                            (commissions)
               + k * sigma_d_i * sqrt(AUM / adv_i) * |dw_i|^1.5 (square-root price impact)

plus a holding cost for short positions:

    borrow_i(w) = (borrow_fee_i / 12) * max(-w_i, 0)

All quantities are in monthly return units of the portfolio's own capital, so ``dw`` is a change in
portfolio weight and ``AUM`` converts it to dollars. The 1.5 power follows from a square-root impact
per dollar traded: impact per dollar ~ sigma * sqrt(Q / ADV), total cost ~ Q * impact.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def impact_coefficient(sigma_d: np.ndarray, adv_usd: np.ndarray, aum: float, k: float = 1.0) -> np.ndarray:
    """Coefficient multiplying ``|dw|^1.5`` in monthly return units."""
    return k * np.asarray(sigma_d, dtype=float) * np.sqrt(aum / np.clip(np.asarray(adv_usd, dtype=float), 1.0, None))


def trade_cost_numpy(dw: np.ndarray, spread: np.ndarray, sigma_d: np.ndarray, adv_usd: np.ndarray,
                     aum: float, k: float = 1.0, commission_bps: float = 1.0) -> np.ndarray:
    """Per-stock trading cost in return units (matches Absar's evaluation-time implementation)."""
    a = np.abs(np.asarray(dw, dtype=float))
    lin = (0.5 * np.asarray(spread, dtype=float) + commission_bps / 10_000.0) * a
    imp = impact_coefficient(sigma_d, adv_usd, aum, k) * a ** 1.5
    return lin + imp


def borrow_cost_numpy(w: np.ndarray, borrow_fee: np.ndarray) -> np.ndarray:
    """Monthly borrow cost of short positions in return units."""
    short = np.clip(-np.asarray(w, dtype=float), 0.0, None)
    return np.asarray(borrow_fee, dtype=float) / 12.0 * short


def cvx_trade_cost(dw, spread: np.ndarray, sigma_d: np.ndarray, adv_usd: np.ndarray, aum: float,
                   k: float = 1.0, commission_bps: float = 1.0):
    """Convex CVXPY expression for the total trading cost of the trade vector ``dw``."""
    import cvxpy as cp

    lin = (0.5 * np.asarray(spread, dtype=float) + commission_bps / 10_000.0)
    imp = impact_coefficient(sigma_d, adv_usd, aum, k)
    abs_dw = cp.abs(dw)
    return lin @ abs_dw + imp @ cp.power(abs_dw, 1.5)


def cvx_borrow_cost(w, borrow_fee: np.ndarray):
    import cvxpy as cp

    return (np.asarray(borrow_fee, dtype=float) / 12.0) @ cp.neg(w)


def cost_inputs_for(date, cost_inputs: pd.DataFrame, permnos: pd.Index) -> pd.DataFrame:
    """Align contract C6 rows to the optimisation universe, filling gaps conservatively."""
    row = cost_inputs[cost_inputs["date"] == pd.Timestamp(date)].set_index("permno")
    out = row.reindex(permnos)
    out["spread"] = out["spread"].fillna(out["spread"].median() if np.isfinite(out["spread"].median()) else 0.01)
    out["sigma_d"] = out["sigma_d"].fillna(out["sigma_d"].median() if np.isfinite(out["sigma_d"].median()) else 0.02)
    out["adv_usd"] = out["adv_usd"].fillna(out["adv_usd"].median() if np.isfinite(out["adv_usd"].median()) else 1e6)
    out["borrow_fee"] = out["borrow_fee"].fillna(0.0025)
    return out[["spread", "sigma_d", "adv_usd", "borrow_fee"]]
