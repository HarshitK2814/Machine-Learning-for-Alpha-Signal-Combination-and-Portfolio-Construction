"""Test 0: pin the CURRENT (``as_run``) exit behaviour on synthetic fixtures.

These tests describe what the evaluator did when Phase 1 and Phase 2 were produced. They are
characterisation tests, not endorsements: each failure mode below conflicts with the 2026-10-13
exit-policy ruling and is the reason ``exit_policy="carry_v1"`` exists. The golden frame is generated
from the unmodified evaluator and guards that the default stays byte-identical.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from exit_fixtures import DATES, SCENARIOS, run

GOLDEN = Path(__file__).parent / "golden" / "as_run_exit_scenarios.parquet"


def test_as_run_matches_golden_frames():
    golden = pd.read_parquet(GOLDEN)
    for name, make in SCENARIOS.items():
        b, w = make()
        f, _ = run(b, w)                      # exit_policy omitted: the default must be as_run
        want = golden[golden["scenario"] == name].drop(columns="scenario").reset_index(drop=True)
        pd.testing.assert_frame_equal(f.reset_index(drop=True), want, check_exact=True, obj=name)


def test_f1_alive_uncertified_name_is_sold_to_zero_with_a_realised_gain():
    """F1: a held name missing from the weights file gets target 0 and is sold."""
    b, w = SCENARIOS["frozen_omitted"]()
    f, ledger = run(b, w)
    assert ledger.position(1) == 0.0
    assert f.loc[3, "realised_st"] > 0.01          # the sale realised the whole lot


def test_f2_sale_of_uncertified_name_is_not_charged():
    """F2: the sale's trade size never reaches the cost function, so the exit is free."""
    base_f, _ = run(*SCENARIOS["baseline"]())
    f, _ = run(*SCENARIOS["frozen_omitted"]())
    # Month 3 sells a ~28% position yet costs LESS than the baseline's routine rebalance.
    assert f.loc[3, "cost_spread"] < base_f.loc[3, "cost_spread"]
    assert f.loc[3, "turnover"] < base_f.loc[3, "turnover"]


def test_f3_exited_name_leaves_a_ghost_lot_that_is_never_realised():
    """F3: no C6 row -> dropped from the book index, but the lot stays in the ledger unrealised."""
    b, w = SCENARIOS["exit_unevidenced"]()
    f, ledger = run(b, w)
    assert ledger.position(2) > 1e6                                   # ghost lot survives
    late = [g for g in ledger.realised if g.permno == 2 and g.date >= DATES[3]]
    assert late == []                                                 # never closed, never taxed
    # and the terminal return does not close it: the lot keeps being counted as unrealised gain
    assert f["unrealised"].iloc[-1] > f["unrealised"].iloc[2]


def test_f3_ghost_lot_is_closed_late_at_a_stale_value_if_the_name_reappears():
    b, w = SCENARIOS["exit_then_reappear"]()
    f, ledger = run(b, w)
    late = [g for g in ledger.realised if g.permno == 2 and g.date == DATES[6]]
    assert len(late) == 1 and late[0].amount > 1e5                    # realised on the stale lot


def test_f4_missing_return_on_a_held_name_is_filled_with_zero():
    b, w = SCENARIOS["unpriced"]()
    f, _ = run(b, w)
    assert f.loc[3, "gross_ret"] == pytest.approx(0.010)             # name 1's 2% silently became 0
    assert not np.isnan(f["gross_ret"]).any()


def test_as_run_frame_has_no_exit_policy_columns():
    f, _ = run(*SCENARIOS["baseline"]())
    assert "valuation_status" not in f.columns and "nav_diag" not in f.columns


def test_as_run_drops_a_total_loss_lot_without_realising_the_loss():
    """A -100% return empties the lot in accrue_returns; no loss is ever booked (carry_v1 fixes this)."""
    b = SCENARIOS["baseline"]()[0]
    b.targets.loc[(b.targets["permno"] == 2) & (b.targets["date"] == DATES[2]), "ret_next"] = -1.0
    from exit_fixtures import build_weights
    f, ledger = run(b, build_weights({2: 3}))
    big_losses = [g for g in ledger.realised if g.permno == 2 and g.amount < -1e6]
    assert big_losses == []
    assert ledger.position(2) == 0.0
