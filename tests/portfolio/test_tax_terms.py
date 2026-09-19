"""The optimiser's tax term must agree with the ledger that later scores the result."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.portfolio.tax_terms import (TaxState, apply_wash_block, cvx_tax_cost,
                                           tax_alpha_adjustment, tax_cost_numpy)
from alphacomb.tax import TaxLotLedger, get_regime

cp = pytest.importorskip("cvxpy")


def test_numpy_tax_cost_only_charges_sales_of_gains():
    prev = np.array([0.02, 0.02, -0.02])
    w = np.array([0.00, 0.03, 0.00])          # sell the first, add to the second, cover the short
    gain = np.array([0.25, 0.25, 0.25])
    rate = np.array([0.408, 0.408, 0.408])
    cost = tax_cost_numpy(w, prev, gain, rate)
    assert cost[0] == pytest.approx(0.408 * 0.25 * 0.02)
    assert cost[1] == 0.0                      # buying is never a taxable event
    assert cost[2] == 0.0                      # short positions are handled by the ledger, not here


def test_convex_term_matches_the_direct_computation_for_gains():
    prev = np.array([0.02, 0.01, 0.03])
    gain = np.array([0.20, 0.10, 0.40])
    rate = np.full(3, 0.408)
    w = cp.Variable(3)
    expr, cons = cvx_tax_cost(w, prev, gain, rate, allow_harvest=False)
    target = np.array([0.00, 0.01, 0.01])
    problem = cp.Problem(cp.Minimize(cp.sum_squares(w - target)), cons)
    problem.solve()
    w.value = target                            # evaluate the expression at a known point
    assert float(expr.value) == pytest.approx(float(tax_cost_numpy(target, prev, gain, rate).sum()),
                                              rel=1e-6)


def test_harvesting_reward_is_bounded_by_the_position():
    """Without the bound the solver would manufacture unlimited loss harvesting."""
    prev = np.array([0.02, 0.02])
    gain = np.array([-0.30, -0.30])             # both positions are at a loss
    rate = np.full(2, 0.408)
    w = cp.Variable(2)
    expr, cons = cvx_tax_cost(w, prev, gain, rate, allow_harvest=True)
    problem = cp.Problem(cp.Maximize(-expr), cons + [w >= -0.05, w <= 0.05])
    problem.solve()
    assert problem.status in {"optimal", "optimal_inaccurate"}
    assert np.isfinite(problem.value)
    best = 0.408 * 0.30 * prev.sum()            # cannot harvest more than the whole position
    assert problem.value <= best + 1e-6


def test_harvest_haircut_scales_the_benefit():
    prev = np.array([0.02])
    gain = np.array([-0.30])
    rate = np.array([0.408])

    def solved(haircut):
        w = cp.Variable(1)
        expr, cons = cvx_tax_cost(w, prev, gain, rate, harvest_haircut=haircut)
        p = cp.Problem(cp.Maximize(-expr), cons + [w >= 0, w <= 0.05])
        p.solve()
        return p.value

    assert solved(0.0) == pytest.approx(0.0, abs=1e-8)
    assert solved(1.0) > solved(0.5) > solved(0.0) - 1e-9


def test_wash_block_forbids_re_establishing_a_blocked_name():
    prev = np.array([0.0, 0.02])
    blocked = np.array([True, False])
    w = cp.Variable(2)
    cons = apply_wash_block(w, prev, blocked)
    problem = cp.Problem(cp.Maximize(cp.sum(w)), cons + [w <= 0.05, w >= -0.05])
    problem.solve()
    assert w.value[0] <= 1e-8                   # cannot go long the blocked name
    assert w.value[1] == pytest.approx(0.05, abs=1e-6)


def test_wash_block_is_a_no_op_when_nothing_is_blocked():
    assert apply_wash_block(cp.Variable(3), np.zeros(3), np.zeros(3, dtype=bool)) == []


def test_tax_state_comes_from_the_same_ledger_that_scores_the_result():
    led = TaxLotLedger(get_regime("taxable"))
    led.buy(1, "2020-01-31", 100.0)
    led.buy(2, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: 0.25, 2: -0.25}))
    state = TaxState.from_ledger(led, pd.Index([1, 2, 3]), "2020-02-29")
    g, rate, blocked = state.aligned(pd.Index([1, 2, 3]))
    assert g[0] == pytest.approx(25.0 / 125.0)
    assert g[1] == pytest.approx(-25.0 / 75.0)
    assert g[2] == 0.0                          # not held
    assert rate[0] == pytest.approx(0.408)
    assert not blocked.any()


def test_tax_state_reports_the_wash_window():
    led = TaxLotLedger(get_regime("taxable"))
    led.buy(1, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: -0.20}))
    led.sell(1, "2020-02-29", 80.0)
    state = TaxState.from_ledger(led, pd.Index([1]), "2020-03-05", wash_block=True)
    assert 1 in state.blocked


def test_tax_state_is_empty_for_a_tax_exempt_ledger():
    led = TaxLotLedger(get_regime("tax_exempt"))
    led.buy(1, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: 0.25}))
    assert TaxState.from_ledger(led, pd.Index([1]), "2020-02-29").empty


def test_deferral_bonus_only_applies_near_the_boundary():
    alpha = pd.Series({1: 0.01, 2: 0.01, 3: 0.01})
    months = pd.Series({1: 2.0, 2: 10.0, 3: 20.0})
    gain = pd.Series({1: 0.2, 2: 0.2, 3: 0.2})
    out = tax_alpha_adjustment(alpha, months, rate_spread=0.17, expected_gain=gain)
    assert out[1] == pytest.approx(0.01)        # too early to bother waiting
    assert out[2] > 0.01                        # approaching twelve months: worth holding
    assert out[3] == pytest.approx(0.01)        # already long-term


def test_optimiser_with_tax_awareness_holds_embedded_gains(small_panel):
    """End to end: the same alpha, with and without the tax term, on one month."""
    from alphacomb.contracts import load_config
    from alphacomb.portfolio import OptimizerConfig, construct
    from alphacomb.risk import RiskCache, StructuralRiskModel

    cfg = load_config("base")
    cfg = {**cfg, "costs": {**cfg["costs"], "aum_usd_2020": 1.0e7}}
    risk = RiskCache(StructuralRiskModel(small_panel, cfg))
    date = sorted(small_panel.universe["date"].unique())[-13]
    permnos = small_panel.universe.loc[(small_panel.universe["date"] == date)
                                       & small_panel.universe["in_universe"], "permno"]
    rng = np.random.default_rng(0)
    alpha = pd.Series(rng.normal(0, 0.01, len(permnos)), index=permnos.to_numpy())
    prev = pd.Series(0.0, index=alpha.index)
    winners = alpha.nlargest(20).index
    prev[winners] = 0.005

    led = TaxLotLedger(get_regime("taxable"))
    for p in winners:
        led.buy(int(p), pd.Timestamp(date) - pd.DateOffset(months=3), 100.0)
    led.accrue_returns(pd.Series(0.40, index=[int(p) for p in winners]))
    state = TaxState.from_ledger(led, pd.Index(alpha.index), date)

    base_cfg = OptimizerConfig.from_files(cfg)
    base_cfg = OptimizerConfig(**{**base_cfg.__dict__, "aum_usd": 1.0e7})
    taxed_cfg = OptimizerConfig(**{**base_cfg.__dict__, "tax_aware": True})

    blind = construct(date, alpha, prev, risk.model(date), small_panel.cost_inputs, base_cfg)
    aware = construct(date, alpha, prev, risk.model(date), small_panel.cost_inputs, taxed_cfg, state)
    if blind.status.startswith("failed") or aware.status.startswith("failed"):
        pytest.skip("solver unavailable for this configuration")

    sold_blind = float(np.clip(prev[winners] - blind.weights.reindex(winners).fillna(0), 0, None).sum())
    sold_aware = float(np.clip(prev[winners] - aware.weights.reindex(winners).fillna(0), 0, None).sum())
    assert sold_aware <= sold_blind + 1e-9, "the tax term must not increase sales of embedded gains"
