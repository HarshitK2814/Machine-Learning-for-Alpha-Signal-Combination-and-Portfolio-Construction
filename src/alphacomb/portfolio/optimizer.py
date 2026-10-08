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
from .cost_terms import (BorrowFeeProxy, borrow_fee_proxy_from_cost_config, cost_inputs_for,
                         cvx_borrow_cost, cvx_trade_cost, eligible_cost_input_permnos,
                         ineligible_held_permnos, partition_prior_book)
from .tax_terms import TaxState, apply_wash_block, cvx_tax_cost

log = logging.getLogger(__name__)

# Dimensionless: a solution is treated as satisfying a bound if it is within this fraction of it.
# Loose enough to absorb conic residue on a 1e-6 trade cap, tight enough that a real breach - the
# gross-769-against-2 case that motivated the check - is four orders of magnitude clear of it.
BREACH_TOL = 1e-4


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
    borrow_fee_proxy_name: str | None = None
    borrow_fee_proxy_annual: float | None = None
    # Price of breaching a drift-sensitive bound (gross, dollar-neutrality, factor exposures).
    # Large relative to the objective, whose terms are O(1e-3), so a bound is respected exactly
    # whenever the trade caps permit; it only bends when the alternative is an infeasible solve.
    violation_penalty: float = 1.0e4
    # Permit median imputation of missing C6 market fields (spread, sigma_d, adv_usd).
    #
    # Must stay False for real data: handoff document 13 requirement 2 says a security-month with
    # a missing or invalid market field is NOT tradeable, and ``cost_inputs_for`` enforces that by
    # raising. The synthetic generator, however, plants a handful of names with missing market
    # data on purpose, so a fail-closed consumer stops the synthetic pipeline dead - which is
    # exactly what happened on the first run after Workstream A's cost_terms landed.
    #
    # Set it from the data source, never by hand: ``from_files`` reads ``data_source`` and turns
    # it on only for synthetic. That way the development pipeline runs and the real-data path
    # keeps failing closed, which is the behaviour the contract requires.
    allow_synthetic_market_imputation: bool = False

    @staticmethod
    def from_files(cfg: dict | None = None, portfolio_cfg: dict | None = None) -> "OptimizerConfig":
        cfg = cfg or load_config("base")
        pcfg = portfolio_cfg or read_yaml(paths.REPO_ROOT / "configs" / "portfolio.yaml")
        p, c = cfg["portfolio"], cfg["costs"]
        borrow_proxy = borrow_fee_proxy_from_cost_config(c)
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
            borrow_fee_proxy_name=borrow_proxy.name if borrow_proxy else None,
            borrow_fee_proxy_annual=borrow_proxy.annual_rate if borrow_proxy else None,
            # Only the synthetic panel may impute missing market fields; real data fails closed.
            allow_synthetic_market_imputation=(str(cfg.get("data_source", "")).lower() == "synthetic"),
        )

    def borrow_fee_proxy(self) -> BorrowFeeProxy | None:
        if self.borrow_fee_proxy_name is None or self.borrow_fee_proxy_annual is None:
            return None
        return BorrowFeeProxy(self.borrow_fee_proxy_name, self.borrow_fee_proxy_annual)


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


def solve_escalating(problem, w, cfg: OptimizerConfig, date, breach_fn=None) -> tuple[str, str]:
    """Try solvers in preference order and keep the answer that is actually *feasible*.

    This rule was wrong until 22 September, and wrong in a way that reached published results. The
    original version preferred the first solver reporting ``optimal`` over one reporting
    ``optimal_inaccurate``, justified by the two objectives agreeing to five significant figures.
    The objectives do agree. The solutions do not:

        CLARABEL   optimal_inaccurate    0 of 827 names over their position cap
        SCS        optimal             139 of 827 names over, worst 3.54x the cap

    So the preference selected SCS's infeasible book over CLARABEL's feasible one, on every month.
    The comparison had been made on the objective value alone; nobody measured the constraints. The
    caps being walked through are the ADV participation limits, so the effect is to take positions
    that could not be traded at the modelled impact cost, concentrated in the least liquid names.

    With ``breach_fn`` supplied, a candidate is scored by how far it violates the bounds and the
    status is used only to break ties. A feasible ``optimal_inaccurate`` beats an infeasible
    ``optimal`` every time. Without it the old status-only behaviour is kept, for callers that have
    no constraint set to measure against.
    """
    import cvxpy as cp

    best = None            # (breach, status_rank, w_value, solver, status)
    for solver in available_solvers(cfg.solver_order):
        try:
            # The tax-aware objective can distinguish two books whose aggregate
            # sales differ by only a few parts in 1e6.  Default conic tolerances
            # are too loose at that scale and previously allowed numerical
            # residue to reverse the intended tax-deferral ordering.  Tighten
            # tolerances without changing the optimisation problem itself.
            # The 1e-10 tolerances exist for the *tax-aware* objective only, and they are not
            # free: on a real cross-section of ~230 names with a power cone per name, CLARABEL
            # cannot reach 1e-10 inside 500 iterations, so it burns the whole budget, returns
            # `optimal_inaccurate`, declines the early break, and hands the month to SCS at
            # eps=1e-7 - about 25s per month, per solver, before the breach check. Where there is
            # no tax term to resolve, 1e-8 is five orders below the smallest weight the book can
            # express and converges in a fraction of the iterations. The optimisation problem is
            # unchanged either way; only the convergence criterion moves.
            tight = bool(getattr(cfg, "tax_aware", False))
            solver_options = {
                "CLARABEL": {
                    "tol_gap_abs": 1e-10 if tight else 1e-8,
                    "tol_gap_rel": 1e-10 if tight else 1e-8,
                    "tol_feas": 1e-10 if tight else 1e-8,
                    "max_iter": 500 if tight else 2_000,
                },
                "SCS": {"eps": 1e-7 if tight else 1e-6, "max_iters": 100_000 if tight else 20_000},
                "ECOS": {
                    "abstol": 1e-10 if tight else 1e-8,
                    "reltol": 1e-10 if tight else 1e-8,
                    "feastol": 1e-10 if tight else 1e-8,
                    "max_iters": 1_000,
                },
            }.get(solver, {})
            problem.solve(solver=getattr(cp, solver), verbose=False, **solver_options)
            if w.value is None or problem.status not in {"optimal", "optimal_inaccurate"}:
                continue
            value = np.asarray(w.value).ravel().copy()
            breach = float(breach_fn(value)) if breach_fn is not None else 0.0
            rank = 0 if problem.status == "optimal" else 1
            cand = (breach if breach > BREACH_TOL else 0.0, rank, value, solver, problem.status)
            if best is None or cand[:2] < best[:2]:
                best = cand
            if cand[0] == 0.0 and rank == 0:
                break                      # feasible and cleanly optimal; nothing can beat it
        except Exception as exc:  # pragma: no cover - solver availability varies
            log.debug("solver %s failed on %s: %s", solver, date, exc)
    if best is None:
        return "failed", ""
    w.value = best[2]
    return best[4], best[3]


def bound_breach(w_val: np.ndarray, prev: np.ndarray, adv_cap: np.ndarray, pos_cap: np.ndarray,
                 cfg: OptimizerConfig, risk: RiskModel,
                 frozen: "FrozenSleeve | None" = None) -> float:
    """Largest breach of the configured bounds by a candidate solution, **relative to each bound**.

    Needed because **a solver status cannot be trusted on this problem**. On a drifted book, where
    the hard constraint set is genuinely empty, SCS does not always report `infeasible`: it returns
    `optimal_inaccurate` together with a solution that breaches the gross budget by two orders of
    magnitude. Accepting that status produced a book at gross 769 against a budget of 2 with nothing
    recorded anywhere - the same silent-failure shape as the bug this exercise is about, only now
    manufactured by the repair. The answer is to measure the solution rather than believe the label.

    The measure is **relative** because the bounds span six orders of magnitude: `adv_cap` floors at
    1e-6 while `gross_max` is 2. An absolute tolerance tight enough to catch a real gross breach
    treats ordinary conic residue on a 1e-6 trade cap as a violation, which sent every undrifted
    month down the soft path and cost it a clean `optimal`. Each breach is therefore divided by its
    own bound, and the caller compares against a single dimensionless tolerance.

    ``frozen`` must be the same sleeve the constraints were built with. The aggregate bounds are
    written on the whole book, so a correct solution satisfies ``sum(w) + net_frozen == 0`` and its
    traded-only net is deliberately non-zero. Measuring ``|sum(w)|`` against zero would score every
    correct solution as a gross violation, send every month down the soft path, and double the solve
    cost while reporting a breach of order one.
    """
    if w_val is None:
        return float("inf")
    w = np.asarray(w_val, dtype=float).ravel()
    scale = max(cfg.gross_max, 1e-12)
    fz = frozen if frozen is not None and not frozen.empty else None
    g_fz = fz.gross if fz else 0.0
    n_fz = fz.net if fz else 0.0
    b_fz = fz.beta if fz else 0.0
    worst = [float(np.max((np.abs(w) - pos_cap) / np.maximum(pos_cap, 1e-12))),
             float(np.max((np.abs(w - prev) - adv_cap) / np.maximum(adv_cap, 1e-12))),
             (float(np.abs(w).sum()) + g_fz - cfg.gross_max) / scale,
             (abs(float(risk.B["beta"].to_numpy(dtype=float) @ w) + b_fz) - cfg.beta_abs_max)
             / max(cfg.beta_abs_max, 1e-12)]
    if cfg.dollar_neutral and not cfg.long_only:
        worst.append(abs(float(w.sum()) + n_fz) / scale)   # equality: any net exposure is a breach
    if cfg.long_only:
        worst += [abs(float(w.sum()) + n_fz - 1.0), float(np.max(-w)) / scale]
    for col in [c for c in risk.B.columns if c.startswith("ind_")]:
        i_fz = fz.industry.get(col, 0.0) if fz else 0.0
        worst.append((abs(float(risk.B[col].to_numpy(dtype=float) @ w) + i_fz) - cfg.industry_abs_max)
                     / max(cfg.industry_abs_max, 1e-12))
    return max(0.0, max(worst))


@dataclass
class FrozenSleeve:
    """Held positions that cannot be traded at a certified cost this month.

    They are not part of the optimisation vector - there is no admissible trade for them - but they
    are still *in the book*, so every aggregate limit has to count them. Leaving them out of the
    gross budget, dollar neutrality or the factor caps would let the optimiser spend a budget the
    portfolio has already committed, and the reported exposures would not be the exposures held.

    ``factor_exposure`` is ``B_f' w_f``, the sleeve's contribution to the factor risk term.
    """

    permnos: pd.Index
    weights: pd.Series
    gross: float
    net: float
    beta: float
    industry: dict
    factor_exposure: np.ndarray

    @property
    def empty(self) -> bool:
        return len(self.permnos) == 0

    @classmethod
    def build(cls, frozen: pd.Index, w_prev: pd.Series | None, risk: RiskModel) -> "FrozenSleeve":
        if w_prev is None or not len(frozen):
            n_factors = risk.B.shape[1]
            return cls(pd.Index([]), pd.Series(dtype=float), 0.0, 0.0, 0.0, {},
                       np.zeros(n_factors))
        wf = w_prev.reindex(frozen).fillna(0.0).astype(float)
        # A frozen name the risk model does not cover contributes no exposure but still consumes
        # gross; reindex+fillna keeps that explicit rather than dropping the position.
        Bf = risk.B.reindex(frozen).fillna(0.0)
        vec = wf.to_numpy(dtype=float)
        ind = {c: float(Bf[c].to_numpy(dtype=float) @ vec)
               for c in Bf.columns if c.startswith("ind_")}
        return cls(
            permnos=frozen,
            weights=wf,
            gross=float(np.abs(vec).sum()),
            net=float(vec.sum()),
            beta=float(Bf["beta"].to_numpy(dtype=float) @ vec) if "beta" in Bf else 0.0,
            industry=ind,
            factor_exposure=Bf.to_numpy(dtype=float).T @ vec,
        )


def book_constraints(w, prev: np.ndarray, adv_cap: np.ndarray, pos_cap: np.ndarray,
                     cfg: OptimizerConfig, risk: RiskModel,
                     soft: bool = False,
                     frozen: "FrozenSleeve | None" = None) -> tuple[list, object, dict]:
    """Position, budget, neutrality and exposure constraints. Never infeasible, never loosened.

    Extracted so there is exactly **one** implementation: ``construct`` and
    ``robust.construct_robust`` used to build these separately, and the 21 September feasibility fix
    reached only the first. No test caught the divergence because every test of the robust path
    passes ``w_prev=None`` - a fresh book, the one case in which a drifted position cannot make the
    constraints conflict.

    **The failure being prevented.** A book that has drifted outside its caps cannot always be
    traded back inside them in one month, because ``|w - prev| <= adv_cap`` pins ``w`` near ``prev``.
    The constraint set is then empty, the solve fails, the caller holds stale weights, ``prev``
    drifts further, and the next month is worse - a self-reinforcing failure that silently turns a
    strategy into a stale buy-and-hold. It bites hardest in small illiquid names, where ``adv_cap``
    is smallest, so it penalises exactly the cells that trade them and reads as "nonlinearity adds
    no net value".

    **Two repairs that did not work**, both recorded because each looked correct and passed tests:

    1. Relaxing each bound to the least value *that bound alone* can reach from ``prev`` (the
       21 September fix). The minimisers differ - shrinking ``||w||_1`` and neutralising ``beta'w``
       call for different trades - so the floors are not jointly attainable and the intersection is
       still empty. Relaxing three of five bounds that way merely moved the infeasibility into beta.
    2. Anchoring every bound at its value at ``prev``. That does guarantee feasibility, since
       ``w = prev`` satisfies everything at once, but it **silently loosens the book**: ``net_slack``
       becomes ``|sum prev|`` rather than zero, so dollar-neutrality stops binding after any drift.
       Buying feasibility by weakening a property the paper claims is not a repair.

    **What is correct** is to make the drift-sensitive bounds *soft*. The hard set is the trade caps
    plus per-name position caps widened only where that pair is individually empty, which is a
    non-empty box by construction. The gross budget, dollar-neutrality and every factor exposure
    carry a non-negative slack priced at ``cfg.violation_penalty`` in the objective. The solver
    therefore satisfies each bound **exactly** whenever the box permits - the normal case, where this
    is identical to the hard formulation - and when it genuinely cannot, it violates by the least
    possible amount and reports it, instead of failing and freezing the book. That is also what a
    desk does: an over-limit position is worked down as fast as participation allows, and the breach
    is reported rather than pretended away.

    ``soft=False`` builds the bounds as hard constraints with no slack variables, which is
    numerically identical to the pre-existing formulation. Callers should try that first and only
    fall back to ``soft=True`` when it proves infeasible: slack variables priced at 1e4 against
    objective terms of order 1e-3 measurably worsen the conditioning, and on this problem's scaling
    that is the difference between a clean ``optimal`` and ``optimal_inaccurate``. Paying that cost
    on every month to protect against a case that arises in almost none of them is the wrong trade,
    and it would also perturb results computed before any of this existed.

    Returns ``(constraints, penalty_expression, caps)``. The caller must subtract the penalty from
    its objective; ``caps`` records the realised violations so a breach appears in the manifest.
    """
    import cvxpy as cp

    # Hard, and non-empty by construction: each w_i may range over
    # [max(-pos_cap, prev - adv_cap), min(pos_cap, prev + adv_cap)], which is non-empty once
    # pos_cap >= |prev| - adv_cap.
    pos_cap = np.maximum(pos_cap, np.abs(prev) - adv_cap)
    cons = [cp.abs(w) <= pos_cap, cp.abs(w - prev) <= adv_cap]

    penalty, violations = 0.0, {}

    def bound_it(expr, bound: float, name: str, equality: bool = False):
        """|expr| <= bound, violable at a price when `soft`, otherwise exactly as configured."""
        nonlocal penalty
        if not soft:
            cons.append(expr == bound if equality else cp.abs(expr) <= bound)
            return
        slack = cp.Variable(nonneg=True)
        cons.append(cp.abs(expr - bound if equality else expr) <= (0.0 if equality else bound) + slack)
        penalty = penalty + cfg.violation_penalty * slack
        violations[name] = slack

    # Untradeable held positions are part of the book, so each aggregate bound is written on the
    # whole book: the optimisable names plus the frozen sleeve's committed exposure.
    fz = frozen if frozen is not None and not frozen.empty else None
    bound_it(cp.norm1(w) + (fz.gross if fz else 0.0), cfg.gross_max, "gross")
    if cfg.dollar_neutral and not cfg.long_only:
        bound_it(cp.sum(w) + (fz.net if fz else 0.0), 0.0, "net", equality=True)
    if cfg.long_only:
        cons.append(w >= 0)
        bound_it(cp.sum(w) + (fz.net if fz else 0.0), 1.0, "net_long_only", equality=True)
    bound_it(risk.B["beta"].to_numpy(dtype=float) @ w + (fz.beta if fz else 0.0),
             cfg.beta_abs_max, "beta")
    for col in [c for c in risk.B.columns if c.startswith("ind_")]:
        bound_it(risk.B[col].to_numpy(dtype=float) @ w + (fz.industry.get(col, 0.0) if fz else 0.0),
                 cfg.industry_abs_max, f"ind:{col}")

    return cons, penalty, {"violations": violations,
                           "pos_cap_relaxed": bool(float(pos_cap.max()) > cfg.weight_abs_max + 1e-12)}


def realised_violations(caps: dict, tol: float = 1e-6) -> dict:
    """Read the slack values back after a solve, keeping only the bounds genuinely breached.

    ``tol`` exists because a conic solver leaves numerical residue of order 1e-7 in a non-negative
    slack even when the bound is not binding at all. Reporting that as a breach would put fifteen
    spurious violations in the manifest for every month.
    """
    out = {}
    for name, var in caps.get("violations", {}).items():
        v = float(var.value) if var.value is not None else 0.0
        if v > tol:
            out[name] = v
    return {"n_violated": len(out), "max_violation": max(out.values()) if out else 0.0,
            "violated": out}


def construct(date, alpha: pd.Series, w_prev: pd.Series | None, risk: RiskModel,
              cost_inputs: pd.DataFrame, cfg: OptimizerConfig | None = None,
              tax_state: TaxState | None = None) -> OptimizationResult:
    """Solve the cost-aware mean-variance problem for one month (contract C11).

    ``tax_state`` is optional and comes from the same tax-lot ledger that scores the result, so the
    optimiser cannot be optimising against a tax model the accountant would not recognise.
    """
    import cvxpy as cp

    cfg = cfg or OptimizerConfig.from_files()
    # A held name without certified market inputs cannot be traded, but that is not a reason to
    # stop trading everything else. It is carried at its drifted weight (a frozen sleeve) and the
    # optimiser works around it; a name that has left the panel entirely is closed by the
    # delisting return the targets table already applies. Holding the *whole* book instead - the
    # earlier behaviour - converted one unpriceable name into a permanently frozen portfolio,
    # because the book then never changed and so never regained eligibility: on the promoted DEU
    # panel that was 131 held months out of 132.
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
    prev = (w_prev.reindex(permnos).fillna(0.0).to_numpy(dtype=float)
            if w_prev is not None else np.zeros(n))
    ci = cost_inputs_for(date, cost_inputs, permnos, borrow_fee_proxy=cfg.borrow_fee_proxy(),
                         allow_synthetic_market_imputation=cfg.allow_synthetic_market_imputation)
    spread = ci["spread"].to_numpy() * cfg.cost_multiplier
    sigma_d = ci["sigma_d"].to_numpy()
    adv = ci["adv_usd"].to_numpy()
    borrow = ci["borrow_fee"].to_numpy()
    k = cfg.impact_k * cfg.cost_multiplier

    L, d = _risk_factor(risk)
    B = risk.B.to_numpy(dtype=float)
    beta = risk.B["beta"].to_numpy(dtype=float)
    # The sleeve's factor exposure is committed, so the risk the optimiser minimises is the risk of
    # the whole book. Its specific variance is an additive constant and does not change the argmin.
    fx_offset = sleeve.factor_exposure if not sleeve.empty else None
    adv_cap = np.clip(adv * cfg.adv_participation_max / cfg.aum_usd, 1e-6, None)
    pos_cap = np.minimum(cfg.weight_abs_max, np.maximum(adv_cap, 1e-5))

    w = cp.Variable(n)
    dw = w - prev
    factor_vec = B.T @ w if fx_offset is None else B.T @ w + fx_offset
    risk_term = cp.sum_squares(L.T @ factor_vec) + cp.sum(cp.multiply(d, cp.square(w)))
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

    def breach_of(value):
        return bound_breach(value, prev, adv_cap, pos_cap, cfg, risk, frozen=sleeve)

    def attempt(soft: bool):
        cons, penalty, caps = book_constraints(w, prev, adv_cap, pos_cap, cfg, risk, soft=soft,
                                               frozen=sleeve)
        problem = cp.Problem(
            cp.Maximize(a @ w - 0.5 * cfg.gamma * risk_term - cost_term - borrow_term
                        - tax_term - penalty),
            cons + tax_cons)
        st, sv = solve_escalating(problem, w, cfg, date, breach_fn=breach_of)
        return problem, st, sv, caps

    # Two stages, so the ordinary month pays nothing for the drifted month's insurance. The hard
    # formulation is what every result before this existed was computed with; the soft one exists
    # only to stop a drifted book from freezing, and its slack variables cost real conditioning.
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
        log.warning("optimiser failed on %s; holding previous weights", pd.Timestamp(date).date())
        return OptimizationResult(held, "failed_hold",
                                  diagnostics={"n_assets": n, "n_frozen": len(sleeve.permnos)})

    traded = pd.Series(np.asarray(w.value).ravel(), index=permnos).round(10)
    traded[traded.abs() < 1e-9] = 0.0
    trade = traded.to_numpy() - prev
    # The reported book is what is actually held: the optimised names plus the frozen sleeve.
    # Exited names are absent by construction - their position was closed by the delisting return.
    weights = pd.concat([traded, sleeve.weights]) if not sleeve.empty else traded
    return OptimizationResult(
        weights=weights,
        status=status,
        objective=float(problem.value),
        predicted_vol=risk_full.align(weights.index).volatility(weights),
        expected_cost=float(cost_term.value) if hasattr(cost_term, "value") else float("nan"),
        turnover=float(np.abs(trade).sum() / 2),
        diagnostics={"n_assets": n, "gross": float(np.abs(weights).sum()), "net": float(weights.sum()),
                     "tax_term": float(tax_term.value) if hasattr(tax_term, "value") else 0.0,
                     "solver": used_solver,
                     # The sleeve is reported every month: it is a constraint on the result, and a
                     # reader has to be able to see how much of the book could not be traded.
                     "n_frozen": len(sleeve.permnos),
                     "gross_frozen": sleeve.gross,
                     "n_exited": len(exited_idx),
                     # recorded so a breached bound is visible in the manifest rather than
                     # silently changing what the constraint means
                     "pos_cap_relaxed": caps["pos_cap_relaxed"],
                     **realised_violations(caps)},
    )


def project(date, w_prop: pd.Series, risk: RiskModel, cost_inputs: pd.DataFrame,
            cfg: OptimizerConfig | None = None,
            w_prev: pd.Series | None = None) -> OptimizationResult:
    """Project an economic-objective cell's raw proposal (C10) onto the constraint set (C11).

    Minimises squared distance to the proposal, so the comparison between prediction-loss cells and
    economic-objective cells is about the model, not about a different constraint treatment.

    **That claim was false until 8 October 2026.** This function built its own constraint list and
    took no prior book, so it applied the per-name *position* cap but never the per-name *trade*
    cap ``|w - prev| <= adv_cap`` that ``construct`` applies to every prediction cell. A proposal
    is not a position, which is why there was no book to difference against - but the projected
    weights *are* a position, and the month-to-month change in them is a trade that has to clear
    the same participation limit as anyone else's.

    Measured on the promoted DEU panel with ``tools/verify_trade_caps.py``, which differences
    against the **drifted** prior book - a position's drift between month-ends is not a trade, and
    comparing raw weights across months invents violations and misreports the frozen sleeve as
    traded:

    | cell | tradeable trades | over ``adv_cap`` | worst | cumulative excess gross |
    |---|---|---|---|---|
    | `N-C-E-U` before | 32,361 | **4,984 (15.4%)** | 24.4x | 0.838 |
    | `L-C-E-0` after | 32,363 | 53 (0.16%) | 5.2x | 0.0001 |

    So roughly one trade in six could not have been executed at the participation limit the cost
    model charges, and the excess concentrated in the least liquid names - the same shape as the
    position-cap failure recorded in ``solve_escalating``, one layer along. Because the affected
    cells are exactly the ``*-E-*`` half of the design, the error sat directly on the cost-aware
    objective axis: the economic cells were being allowed to trade in a way the prediction cells
    were not, and the difference would have been attributed to the objective.

    The 53 residual trades after the fix are conic residue on caps sitting at the ``1e-6`` floor -
    five micro-units of gross in total across 132 months - not a relaxation of the constraint,
    which is hard in both the soft and hard formulations.

    The fix is to stop hand-rolling the constraint set and call the same ``book_constraints``
    builder ``construct`` uses, with the same prior book, the same frozen sleeve and the same
    two-stage hard/soft escalation. The only thing that now differs between a prediction cell and
    an economic cell at C11 is the objective: squared distance to the proposal here, risk- and
    cost-adjusted alpha there.
    """
    import cvxpy as cp

    cfg = cfg or OptimizerConfig.from_files()
    _, frozen_idx, exited_idx = partition_prior_book(date, cost_inputs, w_prev)
    sleeve = FrozenSleeve.build(frozen_idx, w_prev, risk)
    permnos = w_prop.dropna().index
    permnos = eligible_cost_input_permnos(date, cost_inputs, permnos)
    permnos = permnos.difference(sleeve.permnos, sort=False)
    risk_full = risk
    risk = risk.align(permnos)
    n = len(permnos)
    if n < 10:
        return OptimizationResult(pd.Series(dtype=float), "too_few_assets")

    target = w_prop.reindex(permnos).to_numpy(dtype=float)
    prev = (w_prev.reindex(permnos).fillna(0.0).to_numpy(dtype=float)
            if w_prev is not None else np.zeros(n))
    ci = cost_inputs_for(date, cost_inputs, permnos, borrow_fee_proxy=cfg.borrow_fee_proxy(),
                         allow_synthetic_market_imputation=cfg.allow_synthetic_market_imputation)
    adv_cap = np.clip(ci["adv_usd"].to_numpy() * cfg.adv_participation_max / cfg.aum_usd, 1e-6, None)
    pos_cap = np.minimum(cfg.weight_abs_max, np.maximum(adv_cap, 1e-5))

    w = cp.Variable(n)

    def breach_of(value):
        return bound_breach(value, prev, adv_cap, pos_cap, cfg, risk, frozen=sleeve)

    def attempt(soft: bool):
        cons, penalty, caps = book_constraints(w, prev, adv_cap, pos_cap, cfg, risk, soft=soft,
                                               frozen=sleeve)
        problem = cp.Problem(cp.Minimize(cp.sum_squares(w - target) + penalty), cons)
        st, sv = solve_escalating(problem, w, cfg, date, breach_fn=breach_of)
        return problem, st, sv, caps

    problem, status, used_solver, caps = attempt(soft=False)
    breach = (bound_breach(w.value, prev, adv_cap, pos_cap, cfg, risk, frozen=sleeve)
              if status != "failed" else float("inf"))
    if status == "failed" or breach > BREACH_TOL:
        log.info("projection constraint set unsatisfiable on %s (status=%s, relative breach=%.3g); "
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
        weights=weights,
        status=status,
        predicted_vol=risk_full.align(weights.index).volatility(weights),
        turnover=float(np.abs(trade).sum() / 2),
        diagnostics={"n_assets": n,
                     "distance": float(np.linalg.norm(traded.to_numpy() - target)),
                     "gross": float(np.abs(weights).sum()), "net": float(weights.sum()),
                     "solver": used_solver,
                     "n_frozen": len(sleeve.permnos),
                     "gross_frozen": sleeve.gross,
                     "n_exited": len(exited_idx),
                     "pos_cap_relaxed": caps["pos_cap_relaxed"],
                     **realised_violations(caps)},
    )


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
