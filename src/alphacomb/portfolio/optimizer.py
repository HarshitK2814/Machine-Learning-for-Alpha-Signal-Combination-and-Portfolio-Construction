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
from .tax_terms import TaxState, apply_wash_block, cvx_tax_cost

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
    tax_aware: bool = False          # put the tax consequence of a trade in the objective
    tax_harvest_haircut: float = 1.0  # how usable a realised loss is; sensitivity parameter
    wash_block: bool = False         # forbid repurchasing a name inside the s1091 window

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
              cost_inputs: pd.DataFrame, cfg: OptimizerConfig | None = None,
              tax_state: TaxState | None = None) -> OptimizationResult:
    """Solve the cost-aware mean-variance problem for one month (contract C11).

    ``tax_state`` is optional and comes from the same tax-lot ledger that scores the result, so the
    optimiser cannot be optimising against a tax model the accountant would not recognise.
    """
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
    # A position that drifts above its cap cannot always be traded back inside it in one month:
    # |w_i| <= pos_cap and |w_i - prev_i| <= adv_cap have an empty intersection whenever
    # |prev_i| - adv_cap > pos_cap. Left alone this makes the whole problem infeasible, the solver
    # fails, the caller holds stale weights, prev drifts further and the next month is worse - a
    # self-reinforcing failure that silently turns a strategy into a stale buy-and-hold. It bites
    # hardest in small illiquid names, where adv_cap is smallest, so it penalises exactly the cells
    # that trade them and would have looked like "nonlinearity adds no net value".
    # A real desk unwinds an over-cap position as fast as the participation limit allows rather
    # than teleporting, so that is what we encode: the cap relaxes only as far as feasibility needs.
    pos_cap = np.maximum(pos_cap, np.abs(prev) - adv_cap)

    w = cp.Variable(n)
    dw = w - prev
    risk_term = cp.sum_squares(L.T @ (B.T @ w)) + cp.sum(cp.multiply(d, cp.square(w)))
    cost_term = cvx_trade_cost(dw, spread, sigma_d, adv, cfg.aum_usd, k, cfg.commission_bps)
    borrow_term = cvx_borrow_cost(w, borrow)
    tax_term, tax_cons = 0.0, []
    if cfg.tax_aware and tax_state is not None and not tax_state.empty:
        g_vec, rate_vec, blocked = tax_state.aligned(permnos)
        tax_term, tax_cons = cvx_tax_cost(w, prev, g_vec, rate_vec,
                                          allow_harvest=tax_state.allow_harvest,
                                          harvest_haircut=cfg.tax_harvest_haircut)
        if cfg.wash_block:
            tax_cons += apply_wash_block(w, prev, blocked)

    objective = cp.Maximize(a @ w - 0.5 * cfg.gamma * risk_term - cost_term - borrow_term - tax_term)

    # The same feasibility argument applies to the gross budget: if the book drifts above
    # gross_max by more than one month of participation-capped trading, ||w||_1 <= gross_max and
    # |dw| <= adv_cap have no common solution. Relax to the minimum reachable level so the book
    # walks back to budget instead of the solver failing and the caller freezing the portfolio.
    gross_cap = max(cfg.gross_max, float(np.abs(prev).sum() - adv_cap.sum()))
    net_slack = 0.0
    cons = [cp.norm1(w) <= gross_cap, cp.abs(w) <= pos_cap, cp.abs(dw) <= adv_cap]
    cons += tax_cons
    if cfg.dollar_neutral and not cfg.long_only:
        # Third instance of the same feasibility trap: sum(w) == 0 is unreachable in one month if
        # the book has drifted net-long or net-short by more than the participation caps allow.
        # An equality cannot be relaxed gracefully, so it becomes a band of exactly the width
        # feasibility requires - zero in the normal case, where it is identical to the equality.
        net_slack = max(0.0, abs(float(prev.sum())) - float(adv_cap.sum()))
        cons.append(cp.abs(cp.sum(w)) <= net_slack)
    if cfg.long_only:
        cons += [w >= 0, cp.sum(w) == 1]
    cons.append(cp.abs(beta @ w) <= cfg.beta_abs_max)
    for col in industry_cols:
        cons.append(cp.abs(risk.B[col].to_numpy(dtype=float) @ w) <= cfg.industry_abs_max)

    problem = cp.Problem(objective, cons)
    # Escalate rather than accept the first answer. CLARABEL is fast but reports
    # "optimal_inaccurate" on this problem's scaling (trade caps near 1e-6 against a gross budget
    # of 2), where SCS returns a clean "optimal" with an objective agreeing to five significant
    # figures. Take the first genuinely optimal solution; fall back to the best inaccurate one.
    status, used_solver = "failed", ""
    fallback = None
    for solver in available_solvers(cfg.solver_order):
        try:
            problem.solve(solver=getattr(cp, solver), verbose=False)
            if w.value is None:
                continue
            if problem.status == "optimal":
                status, used_solver = problem.status, solver
                break
            if problem.status == "optimal_inaccurate" and fallback is None:
                fallback = (np.asarray(w.value).ravel().copy(), solver)
        except Exception as exc:  # pragma: no cover - solver availability varies
            log.debug("solver %s failed on %s: %s", solver, date, exc)
    if status != "optimal" and fallback is not None:
        w.value, used_solver = fallback[0], fallback[1]
        status = "optimal_inaccurate"
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
        diagnostics={"n_assets": n, "gross": float(np.abs(weights).sum()), "net": float(weights.sum()),
                     "tax_term": float(tax_term.value) if hasattr(tax_term, "value") else 0.0,
                     "solver": used_solver,
                     # both recorded so a binding relaxation is visible in the manifest rather
                     # than silently changing what the constraint means
                     "gross_cap": float(gross_cap), "net_slack": float(net_slack),
                     "cap_relaxed": bool(gross_cap > cfg.gross_max + 1e-12
                                         or float(pos_cap.max()) > cfg.weight_abs_max + 1e-12)},
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
        # project() has no previous book - a proposal is not a position - so there is no drift to
        # accommodate and dollar neutrality stays a hard equality.
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
