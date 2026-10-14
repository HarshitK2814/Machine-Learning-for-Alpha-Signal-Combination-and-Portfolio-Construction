"""Optimiser tests (workstream B): constraints, cost-awareness, projection and scaling."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.portfolio import (OptimizerConfig, construct, grinold_alpha, information_coefficient,
                                 project, shrink_by_uncertainty, stock_volatility, trade_cost_numpy)
from alphacomb.portfolio.cost_terms import cvx_trade_cost
from alphacomb.risk import StructuralRiskModel

DATE = pd.Timestamp("2000-12-31")
TOL = 1e-4


@pytest.fixture(scope="module")
def setup(small_panel):
    risk_provider = StructuralRiskModel(small_panel).prepare()
    risk = risk_provider.load(DATE)
    rng = np.random.default_rng(3)
    scores = pd.Series(rng.normal(size=len(risk.B)), index=risk.B.index)
    alpha = grinold_alpha(scores, risk, ic=0.05)
    cfg = OptimizerConfig.from_files()
    cfg = OptimizerConfig(**{**cfg.__dict__, "gamma": 40.0})
    return small_panel, risk_provider, risk, alpha, cfg


def test_cvx_cost_matches_numpy_formula():
    import cvxpy as cp

    rng = np.random.default_rng(0)
    n = 25
    dw = rng.normal(0, 0.004, n)
    spread = rng.uniform(0.001, 0.02, n)
    sigma_d = rng.uniform(0.01, 0.05, n)
    adv = rng.uniform(1e5, 1e8, n)
    expr = cvx_trade_cost(cp.Constant(dw), spread, sigma_d, adv, aum=1e9, k=1.0, commission_bps=1.0)
    expected = trade_cost_numpy(dw, spread, sigma_d, adv, aum=1e9, k=1.0, commission_bps=1.0).sum()
    assert float(expr.value) == pytest.approx(expected, rel=1e-8)


def test_optimiser_respects_every_constraint(setup):
    panel, _, risk, alpha, cfg = setup
    res = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    w = res.weights
    assert res.status.startswith("optimal")
    assert abs(w.sum()) < TOL                                   # dollar neutral
    assert w.abs().sum() <= cfg.gross_max + TOL                 # gross exposure
    assert w.abs().max() <= cfg.weight_abs_max + TOL            # position limit
    assert abs(float(risk.B["beta"].reindex(w.index) @ w)) <= cfg.beta_abs_max + TOL
    for col in [c for c in risk.B.columns if c.startswith("ind_")]:
        assert abs(float(risk.B[col].reindex(w.index) @ w)) <= cfg.industry_abs_max + TOL
    assert res.predicted_vol > 0


def test_weights_follow_alpha(setup):
    panel, _, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg).weights
    boosted = alpha.copy()
    winner = alpha.index[int(np.argmin(alpha.to_numpy()))]       # take the most negative name
    boosted.loc[winner] = alpha.max() * 3
    after = construct(DATE, boosted, None, risk, panel.cost_inputs, cfg).weights
    assert after.loc[winner] > base.loc[winner] + 1e-6


def test_higher_costs_reduce_turnover(setup):
    panel, _, risk, alpha, cfg = setup
    prev = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg).weights
    flipped = -alpha                                            # force a large rebalance incentive
    cheap = construct(DATE, flipped, prev, risk, panel.cost_inputs,
                      OptimizerConfig(**{**cfg.__dict__, "cost_multiplier": 0.5}))
    dear = construct(DATE, flipped, prev, risk, panel.cost_inputs,
                     OptimizerConfig(**{**cfg.__dict__, "cost_multiplier": 6.0}))
    assert dear.turnover < cheap.turnover
    assert dear.status.startswith("optimal") and cheap.status.startswith("optimal")


def test_higher_risk_aversion_reduces_predicted_volatility(setup):
    panel, _, risk, alpha, cfg = setup
    low = construct(DATE, alpha, None, risk, panel.cost_inputs, OptimizerConfig(**{**cfg.__dict__, "gamma": 5.0}))
    high = construct(DATE, alpha, None, risk, panel.cost_inputs, OptimizerConfig(**{**cfg.__dict__, "gamma": 400.0}))
    assert high.predicted_vol < low.predicted_vol


def test_projection_is_feasible_and_close_to_the_proposal(setup):
    panel, _, risk, alpha, cfg = setup
    rng = np.random.default_rng(5)
    raw = pd.Series(rng.normal(0, 0.02, len(risk.B)), index=risk.B.index)   # violates every limit
    res = project(DATE, raw, risk, panel.cost_inputs, cfg)
    w = res.weights
    assert abs(w.sum()) < TOL
    assert w.abs().sum() <= cfg.gross_max + TOL
    assert w.abs().max() <= cfg.weight_abs_max + TOL
    assert np.linalg.norm(w - raw) < np.linalg.norm(raw)          # closer than the zero portfolio


def test_alpha_scaling_is_comparable_across_models(setup):
    _, _, risk, _, _ = setup
    rng = np.random.default_rng(1)
    small = pd.Series(rng.normal(0, 0.001, len(risk.B)), index=risk.B.index)
    large = small * 1000.0                                        # same information, bigger numbers
    a_small = grinold_alpha(small, risk, ic=0.04)
    a_large = grinold_alpha(large, risk, ic=0.04)
    pd.testing.assert_series_equal(a_small, a_large, rtol=1e-8)
    assert stock_volatility(risk).gt(0).all()


def test_uncertainty_shrinkage_downweights_uncertain_names(setup):
    _, _, risk, alpha, _ = setup
    unc = pd.Series(np.linspace(0.5, 2.0, len(alpha)), index=alpha.index)
    shrunk = shrink_by_uncertainty(alpha, unc, kappa=2.0)
    ratio = (shrunk / alpha).to_numpy()
    assert ratio[0] > ratio[-1]                                   # the most uncertain name shrinks most
    pd.testing.assert_series_equal(shrink_by_uncertainty(alpha, unc, kappa=0.0), alpha)


def test_information_coefficient_recovers_a_known_relationship():
    rng = np.random.default_rng(2)
    dates = np.repeat(pd.date_range("2000-01-31", periods=24, freq="ME"), 100)
    signal = rng.normal(size=len(dates))
    realised = 0.05 * signal + rng.normal(0, 1, len(dates))
    ic = information_coefficient(pd.Series(signal), pd.Series(realised), pd.Series(dates))
    assert 0.005 < ic < 0.10
