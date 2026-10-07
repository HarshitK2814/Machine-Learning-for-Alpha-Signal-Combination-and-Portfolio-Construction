from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from alphacomb.contracts import load_config
from alphacomb.portfolio.cost_terms import (
    BorrowFeeProxy,
    MissingCostInput,
    borrow_cost_numpy,
    borrow_fee_proxy_from_cost_config,
    cost_inputs_for,
    eligible_cost_input_permnos,
    ineligible_held_permnos,
)


DATE = pd.Timestamp("2020-01-31")


def frame() -> pd.DataFrame:
    return pd.DataFrame({
        "date": [DATE, DATE],
        "permno": pd.Series([1, 2], dtype="int32"),
        "spread": [0.002, 0.003],
        "sigma_d": [0.02, 0.03],
        "adv_usd": [1e7, 2e7],
        "borrow_fee": [np.nan, np.nan],
    })


def test_approved_proxy_is_explicit_and_does_not_mutate_certified_c6() -> None:
    c6 = frame()
    before = c6.copy(deep=True)
    policy = borrow_fee_proxy_from_cost_config(load_config("base")["costs"])
    assert policy == BorrowFeeProxy("MODELLED_FLAT_BORROW_PROXY_V1", 0.01)

    aligned = cost_inputs_for(DATE, c6, pd.Index([1, 2]), borrow_fee_proxy=policy)
    assert aligned["borrow_fee"].eq(0.01).all()
    assert aligned.attrs["borrow_fee_proxy"] == "MODELLED_FLAT_BORROW_PROXY_V1"
    pd.testing.assert_frame_equal(c6, before)
    assert c6["borrow_fee"].isna().all()


def test_missing_borrow_fee_without_approved_proxy_fails_closed() -> None:
    with pytest.raises(MissingCostInput, match="no explicit MODELLED proxy"):
        cost_inputs_for(DATE, frame(), pd.Index([1, 2]))


def test_missing_spread_is_ineligible_and_never_median_filled_for_real_path() -> None:
    c6 = frame()
    c6.loc[c6["permno"].eq(2), "spread"] = np.nan
    assert eligible_cost_input_permnos(DATE, c6, pd.Index([1, 2])).tolist() == [1]
    with pytest.raises(MissingCostInput, match="missing/invalid certified"):
        cost_inputs_for(
            DATE,
            c6,
            pd.Index([1, 2]),
            borrow_fee_proxy=BorrowFeeProxy("MODELLED_FLAT_BORROW_PROXY_V1", 0.01),
        )


def test_previously_held_missing_spread_is_flagged_not_silently_liquidated() -> None:
    c6 = frame()
    c6.loc[c6["permno"].eq(2), "spread"] = np.nan
    previous = pd.Series({1: 0.01, 2: -0.01})
    assert ineligible_held_permnos(DATE, c6, previous).tolist() == [2]


def test_one_percent_proxy_cost_is_8_33bp_monthly_at_short_gross_one() -> None:
    w = np.array([1.0, -1.0])
    fees = np.array([0.01, 0.01])
    assert borrow_cost_numpy(w, fees).sum() == pytest.approx(0.01 / 12.0)


def test_legacy_25bp_fallback_is_absent() -> None:
    root = Path(__file__).resolve().parents[2]
    source = (root / "src" / "alphacomb" / "portfolio" / "cost_terms.py").read_text()
    assert "fillna(0.0025)" not in source
    base = (root / "configs" / "base.yaml").read_text()
    assert "borrow_gc_bps_pa" not in base
