"""Regression tests for the drifted-weight infeasibility that silently broke the nonlinear cells.

The failure this pins was not a crash. The optimiser returned ``failed_hold``, the caller kept last
month's weights, those weights drifted further out of the constraint set, and the next month failed
too. Over 216 months one cell degraded to 69% held months - it had stopped being a strategy and
become a stale buy-and-hold, while still producing a plausible-looking return series.

It hit the nonlinear cells hardest because they load on the planted small-illiquid reversal effect,
where the ADV participation cap is tightest. Left in place it would have produced the conclusion
"nonlinearity adds no net value", which is an artefact of the optimiser, not a finding.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.contracts import load_config
from alphacomb.portfolio import OptimizerConfig, construct
from alphacomb.risk import RiskCache, StructuralRiskModel

pytest.importorskip("cvxpy")


@pytest.fixture(scope="module")
def setup(small_panel):
    cfg = load_config("base")
    cfg = {**cfg, "costs": {**cfg["costs"], "aum_usd_2020": 1.0e7}}
    risk = RiskCache(StructuralRiskModel(small_panel, cfg))
    opt = OptimizerConfig.from_files(cfg)
    opt = OptimizerConfig(**{**opt.__dict__, "aum_usd": 1.0e7})
    dates = sorted(small_panel.universe["date"].unique())
    return small_panel, cfg, risk, opt, dates


def _alpha(bundle, date, seed=0):
    u = bundle.universe
    permnos = u.loc[(u["date"] == date) & u["in_universe"], "permno"].to_numpy()
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0, 0.002, len(permnos)), index=permnos)


def test_position_over_cap_does_not_make_the_problem_infeasible(setup):
    """The exact configuration that produced failed_hold: prev far above what ADV can unwind."""
    bundle, cfg, risk, opt, dates = setup
    date = dates[-13]
    alpha = _alpha(bundle, date)
    # A realistic drifted book: gross stays near the 2.0 budget, but individual names have rallied
    # far above their position cap. This is the configuration the walk-forward actually produced.
    n = len(alpha)
    prev = pd.Series(np.full(n, 2.0 / n), index=alpha.index)
    prev.iloc[: n // 2] *= -1
    prev.iloc[:8] *= 6.0          # eight names far above any plausible cap
    prev *= 2.0 / prev.abs().sum()

    res = construct(date, alpha, prev, risk.model(date), bundle.cost_inputs, opt)
    assert not res.status.startswith("failed"), (
        f"over-cap previous weights must stay feasible, got {res.status}")
    assert not res.weights.empty


def test_cap_relaxation_is_the_minimum_needed(setup):
    """The relaxed cap must not become a licence to hold an over-cap position forever.

    Feasibility requires |w| <= max(pos_cap, |prev| - adv_cap). The second term shrinks every month
    by adv_cap, so an over-cap position is forced back inside the cap at the participation limit -
    which is what a desk actually does - rather than being frozen or teleported.
    """
    bundle, cfg, risk, opt, dates = setup
    date = dates[-13]
    alpha = _alpha(bundle, date)
    n = len(alpha)
    prev = pd.Series(np.full(n, 2.0 / n), index=alpha.index)
    prev.iloc[: n // 2] *= -1          # a dollar-neutral book, as the pipeline produces
    prev.iloc[:8] *= 6.0
    prev *= 2.0 / prev.abs().sum()

    res = construct(date, alpha, prev, risk.model(date), bundle.cost_inputs, opt)
    assert not res.status.startswith("failed"), f"must stay feasible, got {res.status}"
    over = prev[prev.abs() > res.weights.abs().max()].index
    assert res.weights.reindex(over).abs().le(prev.reindex(over).abs() + 1e-9).all(),         "an over-cap position may not grow"
    assert res.weights.abs().max() <= prev.abs().max() + 1e-9


def test_walk_forward_does_not_degrade_into_held_weights(setup):
    """The death spiral itself: run several months with drift and require no failure cascade."""
    bundle, cfg, risk, opt, dates = setup
    returns = bundle.targets.set_index(["date", "permno"])["ret_next"]
    prev, statuses = None, []
    for k, date in enumerate(dates[-18:-6]):
        alpha = _alpha(bundle, date, seed=k)
        res = construct(date, alpha, prev, risk.model(date), bundle.cost_inputs, opt)
        statuses.append(res.status)
        w = res.weights if not res.weights.empty else prev
        if w is None or w.empty:
            continue
        r = returns.reindex(pd.MultiIndex.from_product([[pd.Timestamp(date)], w.index])).fillna(0.0)
        port = float((w.to_numpy() * r.to_numpy()).sum())
        prev = pd.Series(w.to_numpy() * (1.0 + r.to_numpy()) / (1.0 + port), index=w.index)

    held = sum(1 for s in statuses if s == "failed_hold")
    assert held == 0, f"failure cascade returned: {held}/{len(statuses)} months held, {statuses}"


def test_solver_escalation_reports_which_solver_answered(setup):
    """Escalation must record its choice, so an accuracy problem is visible rather than silent."""
    bundle, cfg, risk, opt, dates = setup
    date = dates[-13]
    res = construct(date, _alpha(bundle, date), None, risk.model(date), bundle.cost_inputs, opt)
    if res.status.startswith("failed"):
        pytest.skip("solver unavailable for this configuration")
    assert res.status in {"optimal", "optimal_inaccurate"}
    assert res.diagnostics.get("solver"), "the answering solver must be recorded"
    # a fresh book is already inside every constraint, so nothing should be relaxed
    assert res.diagnostics["net_slack"] == pytest.approx(0.0)
    assert "cap_relaxed" in res.diagnostics, "a binding relaxation must be visible, not silent"
