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

from dataclasses import dataclass

import numpy as np
import pandas as pd


class MissingCostInput(RuntimeError):
    """Raised when a cost-aware consumer would otherwise impute certified C6 data."""


@dataclass(frozen=True)
class BorrowFeeProxy:
    """Explicit experiment-layer proxy; it never mutates certified C6 observations."""

    name: str
    annual_rate: float

    def __post_init__(self) -> None:
        if not self.name.startswith("MODELLED_"):
            raise ValueError("borrow-fee proxy must be explicitly labelled MODELLED")
        if not 0 <= self.annual_rate <= 1:
            raise ValueError("annual borrow-fee proxy must be a fraction in [0, 1]")


def borrow_fee_proxy_from_cost_config(costs_cfg: dict) -> BorrowFeeProxy | None:
    """Resolve the approved proxy only from explicit experiment configuration."""

    raw = costs_cfg.get("borrow_fee_model")
    if not raw or not bool(raw.get("enabled", False)):
        return None
    if raw.get("certified_c6_unchanged") is not True:
        raise ValueError("borrow proxy requires certified_c6_unchanged=true")
    return BorrowFeeProxy(str(raw["name"]), float(raw["annual_rate"]))


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


def eligible_cost_input_permnos(date, cost_inputs: pd.DataFrame, permnos: pd.Index) -> pd.Index:
    """Names with certified spread, volatility and positive USD ADV at ``date``."""

    row = cost_inputs[cost_inputs["date"] == pd.Timestamp(date)].set_index("permno")
    out = row.reindex(permnos)
    valid = out[["spread", "sigma_d", "adv_usd"]].notna().all(axis=1)
    valid &= np.isfinite(out[["spread", "sigma_d", "adv_usd"]]).all(axis=1)
    valid &= out["spread"].ge(0) & out["sigma_d"].ge(0) & out["adv_usd"].gt(0)
    return pd.Index(out.index[valid])


def ineligible_held_permnos(date, cost_inputs: pd.DataFrame,
                            w_prev: pd.Series | None) -> pd.Index:
    """Previously held names that cannot be traded with certified market inputs."""

    if w_prev is None:
        return pd.Index([])
    held = pd.Index(w_prev.index[np.abs(w_prev.to_numpy(dtype=float)) > 1e-12])
    eligible = eligible_cost_input_permnos(date, cost_inputs, held)
    return held.difference(eligible, sort=False)


def cost_inputs_for(
    date,
    cost_inputs: pd.DataFrame,
    permnos: pd.Index,
    *,
    borrow_fee_proxy: BorrowFeeProxy | None = None,
    allow_synthetic_market_imputation: bool = False,
) -> pd.DataFrame:
    """Align C6 without imputing market data; apply an explicit borrow model in memory only."""

    row = cost_inputs[cost_inputs["date"] == pd.Timestamp(date)].set_index("permno")
    out = row.reindex(permnos).copy()
    invalid_market = ~out.index.isin(eligible_cost_input_permnos(date, cost_inputs, permnos))
    if np.any(invalid_market) and allow_synthetic_market_imputation:
        for column, fallback in (("spread", 0.01), ("sigma_d", 0.02), ("adv_usd", 1e6)):
            median = out[column].median()
            fill = float(median) if np.isfinite(median) else fallback
            out[column] = out[column].fillna(fill)
        valid = np.isfinite(out[["spread", "sigma_d", "adv_usd"]]).all(axis=1)
        valid &= out["spread"].ge(0) & out["sigma_d"].ge(0) & out["adv_usd"].gt(0)
        invalid_market = ~valid.to_numpy()
    if np.any(invalid_market):
        missing = out.index[invalid_market].tolist()[:10]
        raise MissingCostInput(
            f"{pd.Timestamp(date).date()}: missing/invalid certified spread, sigma_d, or adv_usd "
            f"for {int(np.sum(invalid_market))} names; first={missing}"
        )
    missing_borrow = out["borrow_fee"].isna()
    if missing_borrow.any():
        if borrow_fee_proxy is None:
            raise MissingCostInput(
                f"{pd.Timestamp(date).date()}: borrow_fee missing for {int(missing_borrow.sum())} "
                "names and no explicit MODELLED proxy was configured"
            )
        out.loc[missing_borrow, "borrow_fee"] = borrow_fee_proxy.annual_rate
        out.attrs["borrow_fee_proxy"] = borrow_fee_proxy.name
        out.attrs["borrow_fee_proxy_rows"] = int(missing_borrow.sum())
    if not np.isfinite(out["borrow_fee"]).all() or out["borrow_fee"].lt(0).any():
        raise MissingCostInput("borrow_fee must be finite and non-negative after explicit policy")
    return out[["spread", "sigma_d", "adv_usd", "borrow_fee"]]
