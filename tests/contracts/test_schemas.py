"""Contract C1 industry coding and the shared date convention.

Added 27 September 2026 answering the six questions in Absar's US C1 pilot certification.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.contracts import validate
from alphacomb.contracts.schemas import SchemaError


# ---------------------------------------------------------------------------------------------
# Unknown Industry (ff49 = 0) — added 27 September 2026 answering Absar's US C1 pilot questions.
# The pilot found 3,763 of 83,596 investible stock-months with no defensible contemporaneous FF49.
# The agreed convention is to retain the security and code its industry 0, rather than drop it
# (a non-random size/exchange selection) or backfill a later SIC (look-ahead).
# ---------------------------------------------------------------------------------------------

def _universe_row(ff49: int, date: str = "2000-12-31") -> pd.DataFrame:
    return pd.DataFrame({
        "date": [pd.Timestamp(date)], "permno": np.array([10001], dtype="int32"),
        "in_universe": [True], "me": [1.0e9], "price": [25.0],
        "exchcd": np.array([1], dtype="int32"), "ff49": np.array([ff49], dtype="int32"),
        "nyse_size_pct": [55.0],
    })


def test_unknown_industry_zero_is_a_valid_ff49_code():
    """0 means Unknown Industry and must pass the contract, not be rejected as out of range."""
    validate(_universe_row(0), "universe")


@pytest.mark.parametrize("code", [1, 25, 49])
def test_genuine_ff49_codes_still_pass(code):
    validate(_universe_row(code), "universe")


@pytest.mark.parametrize("code", [-1, 50, 999, 3999])
def test_ff49_outside_its_domain_is_rejected(code):
    """Previously `Column("ff49", "int")` had no domain, so -1 and 9999 passed silently.

    That mattered because the risk model builds industry exposures with `pd.get_dummies(ff49)` and
    the optimiser constrains every resulting `ind_*` column: a typo'd code would have become both a
    new estimated risk factor and a new neutrality constraint with nothing objecting. 3999 is in
    the list because it is the real CRSP SIC that the pilot found outside the FF49 definition — it
    must arrive recoded as 0, not passed through raw.
    """
    with pytest.raises(SchemaError, match="permitted domain"):
        validate(_universe_row(code), "universe")


def test_dates_must_be_calendar_month_end():
    """CRSP month-end dates are last-trading-day, and every contract merges on `date`.

    One table dated 1972-12-29 and another 1972-12-31 makes every cross-contract join silently
    empty — both are valid dates, so no other check would object. This is the one integration
    failure that produces no error message anywhere.
    """
    with pytest.raises(SchemaError, match="calendar month-end"):
        validate(_universe_row(1, date="1972-12-29"), "universe")
