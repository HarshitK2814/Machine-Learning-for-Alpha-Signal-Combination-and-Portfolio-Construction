"""The model. Every test pins a claim the paper will make in words.

The closed form for Phi is checked against brute-force simulation, because an algebra slip here
would propagate into the paper's central comparative static and nothing downstream would catch it.
"""
from __future__ import annotations

import numpy as np
import pytest

from alphacomb.theory import (TaxedStrategy, after_tax_return, channel_decomposition,
                              comparative_static, long_term_share, marginal_cost_of_turnover,
                              optimal_turnover, short_term_share)


# ------------------------------------------------------------------ the closed form

@pytest.mark.parametrize("p", [0.02, 0.05, 0.1, 0.2, 0.4, 0.8])
@pytest.mark.parametrize("H", [6, 12, 24])
def test_closed_form_matches_simulation(p, H):
    """Phi(p,H) = 1 - H(1-p)^(H-1) + (H-1)(1-p)^H, checked by Monte Carlo."""
    rng = np.random.default_rng(0)
    D = rng.geometric(p, size=400_000)
    simulated = float((D * (D < H)).mean() * p)     # p * E[D * 1{D < H}]
    assert short_term_share(p, H) == pytest.approx(simulated, abs=0.01)


def test_boundaries_are_zero_and_one():
    assert short_term_share(0.0, 12) == pytest.approx(0.0)
    assert short_term_share(1.0, 12) == pytest.approx(1.0)
    assert long_term_share(0.0, 12) == pytest.approx(1.0)


def test_short_term_share_increases_with_turnover():
    ps = np.linspace(0.01, 0.99, 50)
    phi = np.asarray(short_term_share(ps, 12))
    assert np.all(np.diff(phi) > -1e-12), "faster trading must not lower the short-term share"


def test_a_longer_boundary_pushes_more_gains_short_term():
    """A 24-month boundary is harder to clear than a 6-month one."""
    assert short_term_share(0.1, 24) > short_term_share(0.1, 6)


def test_boundary_of_one_period_makes_everything_short_term():
    assert short_term_share(0.3, 1) == pytest.approx(1.0)


# ------------------------------------------------------------------ the flat-rate result

def test_under_a_flat_rate_the_tax_bill_does_not_depend_on_turnover():
    """The result that makes Germany and Japan placebos: with Delta = 0, turnover is tax-neutral.

    Any turnover dependence left in the after-tax return must be the trading cost, nothing else.
    """
    flat = TaxedStrategy(g=0.01, kappa=0.0, theta_s=0.26375, theta_l=0.26375, H=12)
    returns = [after_tax_return(flat, p) for p in (0.02, 0.1, 0.3, 0.6, 0.95)]
    assert np.allclose(returns, returns[0], atol=1e-12), returns


def test_under_a_flat_rate_the_holding_period_channel_is_identically_zero():
    flat = TaxedStrategy(g=0.01, kappa=0.002, theta_s=0.20315, theta_l=0.20315, H=12)
    for p in (0.05, 0.2, 0.5):
        dec = channel_decomposition(flat, p)
        assert dec["holding_period_channel"] == pytest.approx(0.0, abs=1e-12)
        assert dec["turnover_channel"] == pytest.approx(flat.kappa)


def test_with_a_wedge_the_holding_period_channel_is_positive():
    us = TaxedStrategy(g=0.01, kappa=0.0005, theta_s=0.408, theta_l=0.238, H=12)
    dec = channel_decomposition(us, 0.15)
    assert dec["holding_period_channel"] > 0
    assert dec["wedge"] == pytest.approx(0.17)


def test_holding_period_channel_scales_with_the_wedge():
    """Proportionality is what produces the cross-country dose-response ordering."""
    base = dict(g=0.01, kappa=0.0005, theta_l=0.238, H=12)
    small = channel_decomposition(TaxedStrategy(theta_s=0.238 + 0.05, **base), 0.15)
    large = channel_decomposition(TaxedStrategy(theta_s=0.238 + 0.15, **base), 0.15)
    ratio = large["holding_period_channel"] / small["holding_period_channel"]
    assert ratio == pytest.approx(3.0, rel=1e-6), ratio


# ------------------------------------------------------------------ the comparative static

def test_optimal_turnover_falls_as_the_wedge_rises():
    """THE prediction. Its empirical counterpart is US < India < flat-rate in turnover."""
    base = TaxedStrategy(g=0.01, kappa=0.001, theta_s=0.238, theta_l=0.238, H=12)
    table = comparative_static(base)
    assert table["p_star"].is_monotonic_decreasing, table[["wedge", "p_star"]]
    assert table["p_star"].iloc[-1] < table["p_star"].iloc[0]


def test_long_term_share_rises_with_the_wedge():
    base = TaxedStrategy(g=0.01, kappa=0.001, theta_s=0.238, theta_l=0.238, H=12)
    table = comparative_static(base)
    assert table["lt_share_of_gains"].is_monotonic_increasing, table[["wedge", "lt_share_of_gains"]]


def test_the_us_wedge_moves_turnover_more_than_the_india_wedge():
    """Dose-response: 17 points must bite harder than 7.5 points, all else equal."""
    base = TaxedStrategy(g=0.01, kappa=0.001, theta_s=0.238, theta_l=0.238, H=12)
    table = comparative_static(base, wedges=[0.0, 0.075, 0.17]).set_index("wedge")
    flat, india, us = (table.loc[w, "p_star"] for w in (0.0, 0.075, 0.17))
    assert us < india < flat, (flat, india, us)


def test_transaction_tax_moves_turnover_without_touching_the_holding_channel():
    """India's STT versus the US wedge: two different mechanisms, distinguishable in the model."""
    cheap = TaxedStrategy(g=0.01, kappa=0.0005, theta_s=0.238, theta_l=0.238, H=12)
    dear = TaxedStrategy(g=0.01, kappa=0.005, theta_s=0.238, theta_l=0.238, H=12)
    assert optimal_turnover(dear)["p_star"] < optimal_turnover(cheap)["p_star"]
    # but neither has a holding-period channel, because both are flat-rate
    for s in (cheap, dear):
        assert channel_decomposition(s, 0.2)["holding_period_channel"] == pytest.approx(0.0, abs=1e-12)


# ------------------------------------------------------------------ sanity

def test_marginal_cost_of_turnover_is_positive():
    us = TaxedStrategy(g=0.01, kappa=0.001, theta_s=0.408, theta_l=0.238, H=12)
    assert marginal_cost_of_turnover(us, 0.15) > 0


def test_effective_rate_lies_between_the_two_statutory_rates():
    from alphacomb.theory.tax_model import effective_tax_rate
    for p in (0.01, 0.1, 0.5, 0.9):
        r = effective_tax_rate(p, theta_s=0.408, theta_l=0.238, H=12)
        assert 0.238 - 1e-12 <= r <= 0.408 + 1e-12


def test_deferral_makes_turnover_costly_even_without_a_wedge():
    """Why deferral is off by default: it blurs the placebo the identification depends on."""
    flat = TaxedStrategy(g=0.01, kappa=0.0, theta_s=0.26, theta_l=0.26, H=12, discount=0.005)
    assert after_tax_return(flat, 0.8) < after_tax_return(flat, 0.05)
