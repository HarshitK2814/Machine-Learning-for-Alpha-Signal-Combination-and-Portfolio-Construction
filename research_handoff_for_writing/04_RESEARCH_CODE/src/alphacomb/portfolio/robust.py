"""Uncertainty-aware portfolio construction (design v2, uncertainty level D3).

Two ways to let calibrated forecast uncertainty change the *decision* rather than only the forecast:

1. **Ellipsoidal robustness.** With per-stock uncertainty ``s_i`` around alpha, the worst case over
   an ellipsoid of radius ``kappa`` is ``alpha'w - kappa * ||S^{1/2} w||_2`` (Goldfarb & Iyengar
   2003). This penalises concentration in names the model is unsure about.
2. **Wasserstein distributionally robust mean-variance.** For a type-2 Wasserstein ball of radius
   ``epsilon`` around the empirical return distribution, the worst-case mean is
   ``alpha'w - epsilon * ||w||_2`` (Blanchet, Chen & Zhou 2022), which is the same shape with a
   uniform radius - a useful contrast, because it separates "uncertainty about *this stock*" from
   "uncertainty about the distribution as a whole".

Both keep the problem convex, so the optimiser stays a single solve and the comparison with the
non-robust cell is exact: radius zero reproduces the base optimiser.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from ..risk.structural import RiskModel
from .cost_terms import (cost_inputs_for, cvx_borrow_cost, cvx_trade_cost,
                         eligible_cost_input_permnos, ineligible_held_permnos,
                         partition_prior_book)
from .optimizer import (FrozenSleeve, OptimizationResult, OptimizerConfig, _risk_factor,
                        book_constraints, BREACH_TOL, bound_breach, realised_violations,
                        solve_escalating)

log = logging.getLogger(__name__)


def construct_robust(date, alpha: pd.Series, w_prev: pd.Series | None, risk: RiskModel,
                     cost_inputs: pd.DataFrame, uncertainty: pd.Series | None = None,
                     kappa_robust: float = 0.0, wasserstein_eps: float = 0.0,
                     cfg: OptimizerConfig | None = None) -> OptimizationResult:
    """Cost-aware mean-variance with an uncertainty penalty.

    ``kappa_robust`` scales the per-stock (ellipsoidal) penalty; ``wasserstein_eps`` scales the
    uniform distributional penalty. Setting both to zero reproduces ``portfolio.construct`` exactly,
    which keeps the uncertainty axis nested for the factorial comparison.
    """
    import cvxpy as cp

    cfg = cfg or OptimizerConfig.from_files()
    # Identical non-tradeability treatment to ``construct``; see partition_prior_book. The two
    # paths must agree, because the uncertainty axis of the factorial is the contrast between
    # them and any difference in how a frozen position is handled would be attributed to
    # uncertainty.
    _, frozen_idx, exited_idx = partition_prior_book(date, cost_inputs, w_prev)
    sleeve = FrozenSleeve.build(frozen_idx, w_prev, risk)
    permnos = alpha.dropna().index
    permnos = eligible_cost_input_permnos(date, cost_inputs, permnos)
    permnos = permnos.difference(sleeve.permnos, sort=False)
    risk_full = risk
    risk = risk.align(permnos)
    n = len(permnos)
    if n < 10:
        return OptimizationResult(pd.Series(dtype=float), "too_few_assets")

    a = alpha.reindex(permnos).to_numpy(dtype=float)
    prev = (w_prev.reindex(permnos).fillna(0.0).to_numpy(dtype=float) if w_prev is not None else np.zeros(n))
    ci = cost_inputs_for(date, cost_inputs, permnos, borrow_fee_proxy=cfg.borrow_fee_proxy(),
                         allow_synthetic_market_imputation=getattr(cfg, "allow_synthetic_market_imputation", False))
    spread = ci["spread"].to_numpy() * cfg.cost_multiplier
    sigma_d = ci["sigma_d"].to_numpy()
    adv = ci["adv_usd"].to_numpy()
    borrow = ci["borrow_fee"].to_numpy()
    k = cfg.impact_k * cfg.cost_multiplier

    if uncertainty is not None:
        s = uncertainty.reindex(permnos).astype(float)
        s = s.fillna(s.median() if np.isfinite(s.median()) else 0.0).to_numpy()
        s = s / (s.mean() if s.mean() > 0 else 1.0)          # relative uncertainty, mean 1
    else:
        s = np.ones(n)

    L, d = _risk_factor(risk)
    B = risk.B.to_numpy(dtype=float)
    beta = risk.B["beta"].to_numpy(dtype=float)

    adv_cap = np.clip(adv * cfg.adv_participation_max / cfg.aum_usd, 1e-6, None)
    pos_cap = np.minimum(cfg.weight_abs_max, np.maximum(adv_cap, 1e-5))

    w = cp.Variable(n)
    dw = w - prev
    factor_vec = B.T @ w if sleeve.empty else B.T @ w + sleeve.factor_exposure
    risk_term = cp.sum_squares(L.T @ factor_vec) + cp.sum(cp.multiply(d, cp.square(w)))
    cost_term = cvx_trade_cost(dw, spread, sigma_d, adv, cfg.aum_usd, k, cfg.commission_bps)
    borrow_term = cvx_borrow_cost(w, borrow)
    robust_term = 0
    if kappa_robust > 0:
        scale = np.sqrt(np.clip(s, 1e-8, None)) * float(np.mean(np.abs(a)) if np.any(a) else 1.0)
        robust_term = robust_term + kappa_robust * cp.norm2(cp.multiply(scale, w))
    if wasserstein_eps > 0:
        robust_term = robust_term + wasserstein_eps * cp.norm2(w)

    def breach_of(value):
        return bound_breach(value, prev, adv_cap, pos_cap, cfg, risk, frozen=sleeve)

    def attempt(soft: bool):
        cons, penalty, caps = book_constraints(w, prev, adv_cap, pos_cap, cfg, risk, soft=soft,
                                               frozen=sleeve)
        problem = cp.Problem(
            cp.Maximize(a @ w - 0.5 * cfg.gamma * risk_term - cost_term - borrow_term
                        - robust_term - penalty), cons)
        st, sv = solve_escalating(problem, w, cfg, date, breach_fn=breach_of)
        return problem, st, sv, caps
    # Same two stages as `construct`, from the same shared builder.
    problem, status, used_solver, caps = attempt(soft=False)
    breach = (bound_breach(w.value, prev, adv_cap, pos_cap, cfg, risk, frozen=sleeve)
              if status != "failed" else float("inf"))
    if status == "failed" or breach > BREACH_TOL:
        log.info("hard constraint set unsatisfiable on %s (status=%s, relative breach=%.3g); "
                 "retrying with breachable bounds", pd.Timestamp(date).date(), status, breach)
        problem, status, used_solver, caps = attempt(soft=True)
    if status == "failed" or w.value is None:
        held = pd.Series(prev, index=permnos)
        if not sleeve.empty:
            held = pd.concat([held, sleeve.weights])
        return OptimizationResult(held, "failed_hold",
                                  diagnostics={"n_assets": n, "n_frozen": len(sleeve.permnos)})

    traded = pd.Series(np.asarray(w.value).ravel(), index=permnos).round(10)
    traded[traded.abs() < 1e-9] = 0.0
    trade = traded.to_numpy() - prev
    weights = pd.concat([traded, sleeve.weights]) if not sleeve.empty else traded
    return OptimizationResult(
        weights=weights, status=status, objective=float(problem.value),
        predicted_vol=risk_full.align(weights.index).volatility(weights),
        turnover=float(np.abs(trade).sum() / 2),
        diagnostics={"n_assets": n, "kappa_robust": kappa_robust, "wasserstein_eps": wasserstein_eps,
                     "gross": float(np.abs(weights).sum()), "solver": used_solver,
                     "n_frozen": len(sleeve.permnos), "gross_frozen": sleeve.gross,
                     "n_exited": len(exited_idx),
                     "pos_cap_relaxed": caps["pos_cap_relaxed"], **realised_violations(caps)},
    )


def prediction_inflation(alpha: pd.Series, weights: pd.Series, realised: pd.Series) -> dict:
    """Diagnostic for the SPO critique (Wang & Hasuike 2026).

    Decision-focused objectives can inflate the implied expected return and churn the portfolio.
    We report the ratio of implied expected return to realised return, and the concentration of the
    book, so the paper can show whether the economic-objective cells suffer from this pathology.
    """
    idx = weights.index
    a = alpha.reindex(idx).fillna(0.0).to_numpy(dtype=float)
    r = realised.reindex(idx).fillna(0.0).to_numpy(dtype=float)
    w = weights.to_numpy(dtype=float)
    implied = float(a @ w)
    achieved = float(r @ w)
    gross = float(np.abs(w).sum())
    return {
        "implied_expected_return": implied,
        "realised_return": achieved,
        "inflation_ratio": implied / achieved if abs(achieved) > 1e-12 else np.nan,
        "gross_exposure": gross,
        "effective_names": float(gross ** 2 / np.sum(w ** 2)) if np.any(w) else 0.0,
    }
