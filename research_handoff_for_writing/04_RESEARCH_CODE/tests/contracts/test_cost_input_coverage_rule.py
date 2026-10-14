"""The cost-input coverage rule, as a regression test.

Document 13 requirement 2 makes an uncertified security-month **non-tradeable** and prohibits
imputation (`docs/NON_TRADEABLE_TREATMENT.md`). On 2026-10-09 a tool violated that rule by forming
decile portfolios on the *signal-bearing* cross-section rather than the *investable* one, which
silently:

  * charged an uncovered name **zero cost** in an uncapped book, and
  * gave the same name **cap = 0** in a capped book,

both of which push a capacity channel downward. Because Germany's cost-input coverage is 65% and
India's is 99%, that produced a spurious, highly significant (t = -6.10) sign-flipping
cross-country contrast that survived a value-weighting robustness check and a six-fold
impact-coefficient sweep. It was retracted the same day
(`docs/RESULTS_CAPACITY_CHANNEL_2026-10-09.md` section 6).

These tests pin the two behaviours that made it possible, so the defect cannot return silently.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.portfolio.cost_terms import eligible_cost_input_permnos, trade_cost_numpy


@pytest.fixture
def cost_inputs() -> pd.DataFrame:
    """Four names: one fully priced, and one failing each of the three required fields."""
    d = pd.Timestamp("2015-06-30")
    return pd.DataFrame({
        "date": [d] * 4,
        "permno": [1, 2, 3, 4],
        "spread": [0.001, np.nan, 0.002, 0.003],
        "sigma_d": [0.02, 0.02, np.nan, 0.02],
        "adv_usd": [5e6, 5e6, 5e6, 0.0],
    })


def test_only_the_fully_priced_name_is_eligible(cost_inputs):
    """A missing spread, a missing sigma_d and a zero ADV each make a name non-tradeable."""
    got = eligible_cost_input_permnos(pd.Timestamp("2015-06-30"), cost_inputs,
                                      pd.Index([1, 2, 3, 4]))
    assert list(got) == [1], (
        "eligibility must require spread AND sigma_d AND positive ADV; "
        f"got {list(got)}"
    )


def test_zero_adv_is_not_eligible_even_though_the_field_is_present(cost_inputs):
    """``adv_usd == 0`` is the case a finite-check alone would wrongly admit."""
    got = eligible_cost_input_permnos(pd.Timestamp("2015-06-30"), cost_inputs, pd.Index([4]))
    assert len(got) == 0


def test_eligibility_does_not_impute(cost_inputs):
    """Imputation is prohibited: an ineligible name must be dropped, never filled."""
    got = eligible_cost_input_permnos(pd.Timestamp("2015-06-30"), cost_inputs,
                                      pd.Index([1, 2, 3, 4]))
    # The returned index is a subset; nothing is renamed, defaulted or back-filled.
    assert set(got).issubset({1, 2, 3, 4})
    assert cost_inputs.spread.isna().sum() == 1, "fixture must not be mutated"
    assert cost_inputs.sigma_d.isna().sum() == 1
    assert (cost_inputs.adv_usd == 0).sum() == 1


def test_a_traded_name_is_never_free():
    """The bug's first half: an uncovered name was charged zero cost in the uncapped book.

    Any name that moves must cost something. This pins that the cost model is strictly positive
    for a non-zero trade, so a caller cannot get a free position by leaving it out of its ``ok``
    mask without the universe shrinking too.
    """
    dw = np.array([0.01])
    c = trade_cost_numpy(dw, np.array([0.001]), np.array([0.02]), np.array([5e6]),
                         1e9, 1.0, 1.0)
    assert float(c[0]) > 0.0


def test_cost_rises_with_trade_size_superlinearly():
    """The square-root impact law: doubling the trade more than doubles its cost."""
    sp, sd, ad = np.array([0.001]), np.array([0.02]), np.array([5e6])
    c1 = float(trade_cost_numpy(np.array([0.01]), sp, sd, ad, 1e9, 1.0, 1.0)[0])
    c2 = float(trade_cost_numpy(np.array([0.02]), sp, sd, ad, 1e9, 1.0, 1.0)[0])
    assert c2 > 2.0 * c1, f"expected superlinear impact, got {c1:.6g} -> {c2:.6g}"


def test_participation_cap_of_an_unpriced_name_is_zero_not_unbounded():
    """The bug's second half, stated as the arithmetic that caused it.

    ``cap = part * adv_usd / aum`` is 0 or NaN when ADV is missing or zero. A caller that clips
    weights to ``cap`` therefore DROPS the name from a capped book. That is the correct treatment
    only if the same name is also excluded from the uncapped comparison; otherwise the two books
    hold different universes and their Sharpe difference is not a capacity effect. This test
    documents the arithmetic so the asymmetry is not re-introduced.
    """
    part, aum = 0.05, 1e9
    for adv in (0.0, np.nan):
        cap = part * adv / aum
        assert not (np.isfinite(cap) and cap > 0), (
            "an unpriced name must not receive a positive participation cap"
        )


@pytest.mark.parametrize("coverage,expect_bias", [(1.00, False), (0.65, True)])
def test_coverage_asymmetry_biases_a_paired_sharpe_difference(coverage, expect_bias):
    """Why a 65%-vs-99% coverage gap manufactured a cross-country contrast.

    Builds two books on the same returns. The 'uncapped' book gets its uncovered positions free;
    the 'capped' book drops them. With full coverage the two books are identical and the channel
    is zero. With partial coverage the channel is driven negative by construction, with no
    liquidity constraint anywhere in the simulation.
    """
    rng = np.random.default_rng(0)
    T, N = 132, 100
    r = rng.normal(0.004, 0.05, (T, N))
    covered = np.zeros(N, dtype=bool)
    covered[: int(round(coverage * N))] = True
    cost = 0.004  # flat per-name cost, charged only where covered

    w = np.full(N, 1.0 / N)
    # uncapped: holds everything, pays cost only on covered names (the defect)
    net_unc = (r * w).sum(axis=1) - cost * w[covered].sum()
    # capped: drops uncovered names entirely, pays cost on what it holds
    wc = np.where(covered, w, 0.0)
    net_cap = (r * wc).sum(axis=1) - cost * wc.sum()

    def sr(x):
        return float(x.mean() / x.std(ddof=1) * np.sqrt(12))

    channel = sr(net_cap) - sr(net_unc)
    if expect_bias:
        assert channel < -0.05, (
            f"a {coverage:.0%}-coverage panel should show a spurious negative channel, "
            f"got {channel:+.4f}"
        )
    else:
        assert abs(channel) < 1e-9, (
            f"a fully covered panel must show no channel, got {channel:+.4f}"
        )
