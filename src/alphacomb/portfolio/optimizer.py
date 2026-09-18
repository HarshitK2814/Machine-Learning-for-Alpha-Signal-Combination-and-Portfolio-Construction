"""Transaction-cost-aware mean-variance optimiser and the projection step (workstream B).

Contract C11 producer. One optimiser serves every cell, every baseline and every benchmark, so that
differences in net performance come from the model rather than from the portfolio construction.

    maximise   alpha'w - (gamma/2) w'(B F B' + D)w - trade_cost(w - w_prev) - borrow_cost(w)
    subject to sum(w) = 0, ||w||_1 <= gross_max, |beta'w| <= beta_max,
               |industry_g'w| <= industry_max for every industry g,
               |w_i| <= min(weight_max, ADV_i * participation / AUM),
               |dw_i| <= ADV_i * participation / AUM
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..contracts import load_config
from ..contracts.io import read_yaml
from ..contracts import paths
from ..risk.structural import RiskModel
from .cost_terms import cost_inputs_for, cvx_borrow_cost, cvx_trade_cost

log = logging.getLogger(__name__)


@dataclass
class OptimizerConfig:
    gross_max: float = 2.0
    dollar_neutral: bool = True
    beta_abs_max: float = 0.05
    industry_abs_max: float = 0.02
    weight_abs_max: float = 0.01
    adv_participation_max: float = 0.05
    gamma: float = 25.0
    aum_usd: float = 1.0e9
    impact_k: float = 1.0
    commission_bps: float = 1.0
    cost_multiplier: float = 1.0
    solver_order: tuple[str, ...] = ("CLARABEL", "ECOS", "SCS")
    max_seconds: float = 30.0
    long_only: bool = False
    tracking_error_max: float = 0.04
    fallback_hold_on_failure: bool = True

    @staticmethod
    def from_files(cfg: dict | None = None, portfolio_cfg: dict | None = None) -> "OptimizerConfig":
        cfg = cfg or load_config("base")
        pcfg = portfolio_cfg or read_yaml(paths.REPO_ROOT / "configs" / "portfolio.yaml")
        p, c = cfg["portfolio"], cfg["costs"]
        return OptimizerConfig(
            gross_max=float(p["gross_max"]), dollar_neutral=bool(p["dollar_neutral"]),
            beta_abs_max=float(p["beta_abs_max"]), industry_abs_max=float(p["industry_abs_max"]),
            weight_abs_max=float(p["weight_abs_max"]), adv_participation_max=float(p["adv_participation_max"]),
            aum_usd=float(c["aum_usd_2020"]), impact_k=float(c["impact_k"]),
            commission_bps=float(c["commission_bps"]),
            solver_order=tuple(p.get("solver_order", ["CLARABEL", "ECOS", "SCS"])),
            max_seconds=float(pcfg.get("solver", {}).get("max_seconds", 30)),
            long_only=bool(pcfg.get("long_only_variant", {}).get("enabled", False)),
            tracking_error_max=float(pcfg.get("long_only_variant", {}).get("tracking_error_max", 0.04)),
        )


@dataclass
class OptimizationResult:
    weights: pd.Series
    status: str
    objective: float = float("nan")
    predicted_vol: float = float("nan")
    expected_cost: float = float("nan")
    turnover: float = float("nan")
    diagnostics: dict = field(default_factory=dict)


def available_solvers(preferred: tuple[str, ...]) -> list[str]:
    """Keep only solvers that are actually installed, preserving the configured preference order.

    The cost term uses a 1.5-power cone, so QP-only solvers (OSQP) cannot be used.
    """
    import cvxpy as cp

    installed = set(cp.installed_solvers())
    order = [s for s in preferred if s in installed]
    for fallback in ("CLARABEL", "SCS", "ECOS", "MOSEK"):
        if fallback in installed and fallback not in order:
            order.append(fallback)
    if not order:  # pragma: no cover - cvxpy always ships at least one conic solver
        raise RuntimeError(f"no supported conic solver installed; found {sorted(installed)}")
    return order


def _risk_factor(risk: RiskModel) -> tuple[np.ndarray, np.ndarray]:
    """Return (L, d) with F = L L' (eigenvalue-clipped) and d the specific variances."""
    F = risk.F.to_numpy(dtype=float)
    vals, vecs = np.linalg.eigh((F + F.T) / 2)
    vals = np.clip(vals, 0.0, None)
    L = vecs @ np.diag(np.sqrt(vals))
    return L, risk.D.to_numpy(dtype=float)


def construct(date, alpha: pd.Series, w_prev: pd.Series | None, risk: RiskModel,
              cost_inputs: pd.DataFrame, cfg: OptimizerConfig | None = None) -> OptimizationResult:
    """Solve the cost-aware mean-variance problem for one month (contract C11)."""
    import cvxpy as cp

    cfg = cfg or OptimizerConfig.from_files()
    permnos = alpha.dropna().index
    risk = risk.align(permnos)
    n = len(permnos)
    if n < 10:
        return OptimizationResult(pd.Series(dtype=float), "too_few_assets")

    a = alpha.reindex(permnos).to_numpy(dtype=float)
    prev = (w_prev.reindex(permnos).fillna(0.0).to_numpy(dtype=float)
            if w_prev is not None else np.zeros(n))
    ci = cost_inputs_for(date, cost_inputs, permnos)
    spread = ci["spread"].to_numpy() * cfg.cost_multiplier
    sigma_d = ci["sigma_d"].to_numpy()
    adv = ci["adv_usd"].to_numpy()
    borrow = ci["borrow_fee"].to_numpy()
    k = cfg.impact_k * cfg.cost_multiplier

    L, d = _risk_factor(risk)
    B = risk.B.to_numpy(dtype=float)
    beta = risk.B["beta"].to_numpy(dtype=float)
    industry_cols = [c for c in risk.B.columns if c.startswith("ind_")]

    adv_cap = np.clip(adv * cfg.adv_participation_max / cfg.aum_usd, 1e-6, None)
    pos_cap = np.minimum(cfg.weight_abs_max, np.maximum(adv_cap, 1e-5))

    w = cp.Variable(n)
    dw = w - prev
    risk_term = cp.sum_squares(L.T @ (B.T @ w)) + cp.sum(cp.multiply(d, cp.square(w)))
    cost_term = cvx_trade_cost(dw, spread, sigma_d, adv, cfg.aum_usd, k, cfg.commission_bps)
    borrow_term = cvx_borrow_cost(w, borrow)
    objective = cp.Maximize(a @ w - 0.5 * cfg.gamma * risk_term - cost_term - borrow_term)

    cons = [cp.norm1(w) <= cfg.gross_max, cp.abs(w) <= pos_cap, cp.abs(dw) <= adv_cap]
    if cfg.dollar_neutral and not cfg.long_only:
        cons.append(cp.sum(w) == 0)
    if cfg.long_only:
        cons += [w >= 0, cp.sum(w) == 1]
    cons.append(cp.abs(beta @ w) <= cfg.beta_abs_max)
    for col in industry_cols:
        cons.append(cp.abs(risk.B[col].to_numpy(dtype=float) @ w) <= cfg.industry_abs_max)

    problem = cp.Problem(objective, cons)
    status = "failed"
    for solver in available_solvers(cfg.solver_order):
        try:
            problem.solve(solver=getattr(cp, solver), verbose=False)
            if w.value is not None and problem.status in {"optimal", "optimal_inaccurate"}:
                status = problem.status
                break
        except Exception as exc:  # pragma: no cover - solver availability varies
            log.debug("solver %s failed on %s: %s", solver, date, exc)
    if status == "failed" or w.value is None:
        held = pd.Series(prev, index=permnos)
        log.warning("optimiser failed on %s; holding previous weights", pd.Timestamp(date).date())
        return OptimizationResult(held, "failed_hold", diagnostics={"n_assets": n})

    weights = pd.Series(np.asarray(w.value).ravel(), index=permnos).round(10)
    weights[weights.abs() < 1e-9] = 0.0
    trade = weights.to_numpy() - prev
    return OptimizationResult(
        weights=weights,
        status=status,
        objective=float(problem.value),
        predicted_vol=risk.volatility(weights),
        expected_cost=float(cost_term.value) if hasattr(cost_term, "value") else float("nan"),
        turnover=float(np.abs(trade).sum() / 2),
        diagnostics={"n_assets": n, "gross": float(np.abs(weights).sum()), "net": float(weights.sum())},
    )


def project(date, w_prop: pd.Series, risk: RiskModel, cost_inputs: pd.DataFrame,
            cfg: OptimizerConfig | None = None) -> OptimizationResult:
    """Project an economic-objective cell's raw proposal (C10) onto the constraint set (C11).

    Minimises squared distance to the proposal, so the comparison between prediction-loss cells and
    economic-objective cells is about the model, not about a different constraint treatment.
    """
    import cvxpy as cp

    cfg = cfg or OptimizerConfig.from_files()
    permnos = w_prop.dropna().index
    risk = risk.align(permnos)
    n = len(permnos)
    if n < 10:
        return OptimizationResult(pd.Series(dtype=float), "too_few_assets")

    target = w_prop.reindex(permnos).to_numpy(dtype=float)
    ci = cost_inputs_for(date, cost_inputs, permnos)
    adv_cap = np.clip(ci["adv_usd"].to_numpy() * cfg.adv_participation_max / cfg.aum_usd, 1e-6, None)
    pos_cap = np.minimum(cfg.weight_abs_max, np.maximum(adv_cap, 1e-5))
    beta = risk.B["beta"].to_numpy(dtype=float)

    w = cp.Variable(n)
    cons = [cp.norm1(w) <= cfg.gross_max, cp.abs(w) <= pos_cap, cp.abs(beta @ w) <= cfg.beta_abs_max]
    if cfg.dollar_neutral and not cfg.long_only:
        cons.append(cp.sum(w) == 0)
    if cfg.long_only:
        cons += [w >= 0, cp.sum(w) == 1]
    for col in [c for c in risk.B.columns if c.startswith("ind_")]:
        cons.append(cp.abs(risk.B[col].to_numpy(dtype=float) @ w) <= cfg.industry_abs_max)

    problem = cp.Problem(cp.Minimize(cp.sum_squares(w - target)), cons)
    status = "failed"
    for solver in available_solvers(cfg.solver_order):
        try:
            problem.solve(solver=getattr(cp, solver), verbose=False)
            if w.value is not None and problem.status in {"optimal", "optimal_inaccurate"}:
                status = problem.status
                break
        except Exception as exc:  # pragma: no cover
            log.debug("projection solver %s failed: %s", solver, exc)
    if status == "failed" or w.value is None:
        return OptimizationResult(pd.Series(0.0, index=permnos), "failed_hold")
    weights = pd.Series(np.asarray(w.value).ravel(), index=permnos).round(10)
    weights[weights.abs() < 1e-9] = 0.0
    return OptimizationResult(weights=weights, status=status, predicted_vol=risk.volatility(weights),
                              diagnostics={"n_assets": n, "distance": float(np.linalg.norm(weights - target))})


def calibrate_gamma(dates, alphas: dict, risk_provider, cost_inputs: pd.DataFrame,
                    cfg: OptimizerConfig | None = None, target_vol_annual: float = 0.10,
                    bounds: tuple[float, float] = (1.0, 2000.0), iterations: int = 8) -> float:
    """Bisect on the risk-aversion parameter until ex-ante volatility hits the target.

    Calibration uses validation dates only; it never looks at test-period data.
    """
    cfg = cfg or OptimizerConfig.from_files()
    lo, hi = bounds
    for _ in range(iterations):
        mid = float(np.sqrt(lo * hi))
        trial = OptimizerConfig(**{**cfg.__dict__, "gamma": mid})
        vols = []
        for date in dates:
            alpha = alphas.get(pd.Timestamp(date))
            if alpha is None or alpha.dropna().empty:
                continue
            res = construct(date, alpha, None, risk_provider.load(date), cost_inputs, trial)
            if np.isfinite(res.predicted_vol):
                vols.append(res.predicted_vol)
        if not vols:
            return mid
        vol = float(np.median(vols))
        if vol > target_vol_annual:
            lo = mid
        else:
            hi = mid
    return float(np.sqrt(lo * hi))
