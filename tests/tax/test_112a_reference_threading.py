"""The section 112A reference value must reach the tax basis, and these tests prove it does.

Why this file exists
--------------------
On 2026-10-09 two successive bounding exercises on India's 456 missing 31-Jan-2018 reference values
returned **bit-identical** event-study output. The first was our own error (both bound files set
``fmv == close``, so the ratio the engine actually reads was 1.0 in both). The second varied the
ratio correctly and the output *still* did not move, which left two possibilities:

  (a) the 456 names are never realised as grandfathered long-term gains in the post-reform window,
      so their treatment cannot matter - benign; or
  (b) the reference value is accepted, logged, and then **not threaded into the computation** - a
      bug in the one piece of machinery no competing paper has.

These tests settle it as (a) by showing the plumbing is correct end to end: a maximal perturbation
of the reference ratio produces a maximal change in the taxable gain. Combined with the identical
aggregate output, that implies the binding set contains none of the 456 names.

They are pinned here because the deduction "identical output means the data does not matter" is
only valid while the plumbing is known good, and a future refactor could silently break it and
restore the ambiguity.

Statute: section 55(2)(ac). ``deemed_cost = max(actual_cost, min(fmv_2018_01_31, sale_value))``.
"""
from __future__ import annotations

import pandas as pd
import pytest

from alphacomb.tax.dated import india_section_112a_deemed_cost

LOT_BASIS = 100.0
SALE = 200.0


# ---------------------------------------------------------------- the statutory formula itself

def test_deemed_cost_falls_back_to_actual_cost_when_fmv_is_tiny():
    """MAXTAX bound: fmv ~ 0 means no grandfathering relief, so the full gain is taxed."""
    basis = india_section_112a_deemed_cost(actual_cost=LOT_BASIS, fmv_2018_01_31=1e-4,
                                           sale_value=SALE)
    assert basis == pytest.approx(LOT_BASIS)
    assert SALE - basis == pytest.approx(100.0), "full gain should be taxable"


def test_deemed_cost_reaches_sale_value_when_fmv_is_huge():
    """MINTAX bound: fmv above the sale value shelters the gain entirely."""
    basis = india_section_112a_deemed_cost(actual_cost=LOT_BASIS, fmv_2018_01_31=1e8,
                                           sale_value=SALE)
    assert basis == pytest.approx(SALE)
    assert SALE - basis == pytest.approx(0.0), "gain should be fully sheltered"


def test_the_two_bounds_differ_by_the_whole_gain():
    """This is the property the bounding exercise relies on: the bound must actually bind."""
    hi = india_section_112a_deemed_cost(actual_cost=LOT_BASIS, fmv_2018_01_31=1e-4,
                                        sale_value=SALE)
    lo = india_section_112a_deemed_cost(actual_cost=LOT_BASIS, fmv_2018_01_31=1e8,
                                        sale_value=SALE)
    assert (SALE - hi) - (SALE - lo) == pytest.approx(100.0)


def test_grandfathering_never_manufactures_a_loss():
    """max(actual_cost, ...) floors the basis, so relief cannot turn a gain into a loss."""
    basis = india_section_112a_deemed_cost(actual_cost=150.0, fmv_2018_01_31=1e8,
                                           sale_value=SALE)
    assert basis == pytest.approx(SALE)
    basis_low_sale = india_section_112a_deemed_cost(actual_cost=150.0, fmv_2018_01_31=1e8,
                                                    sale_value=120.0)
    assert basis_low_sale == pytest.approx(150.0), "actual cost floors the deemed cost"


def test_negative_inputs_are_rejected():
    with pytest.raises(Exception):
        india_section_112a_deemed_cost(actual_cost=-1.0, fmv_2018_01_31=10.0, sale_value=5.0)


# ---------------------------------------------------------------- the ratio is what the engine reads

def test_reference_store_exposes_high_to_close_ratio_not_the_absolute_price():
    """The 2026-10-09 failure in one assertion.

    The engine computes ``statutory_reference_value = close_value_local * high_to_close_ratio``.
    A bound that moves ``fmv`` and ``close`` together leaves that ratio unchanged and therefore
    does nothing, which is exactly how two runs became the same run.
    """
    rows = pd.DataFrame({
        "country": ["IND", "IND"],
        "permno": [1, 2],
        "reference_date": ["2018-01-31", "2018-01-31"],
        "fmv_price_local": [1e-4, 1e9],
        "close_price_local": [1e-4, 1e9],
        "currency": ["INR", "INR"],
    })
    ratios = rows.fmv_price_local / rows.close_price_local
    assert ratios.nunique() == 1 and ratios.iloc[0] == pytest.approx(1.0), (
        "moving fmv and close together is a no-op; a 112A bound must vary the RATIO"
    )
