"""The code must not out-search its own pre-registration.

A deflated Sharpe ratio is only meaningful if N was fixed in advance, and N is only honest if the
code actually searches the grid the plan registered. On 8 October the two had drifted: PLAN_001
registered a two-level shrinkage dimension while ``CellRunConfig`` searched five kappa values, so
the real confirmatory search was 2.5x wider than the N it would have been deflated against.

These tests bind the two together, so the next drift fails the suite instead of quietly inflating
a t-statistic.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from alphacomb.models.cells import (CONFIRMATORY_KAPPA_GRID, EXPLORATORY_KAPPA_GRID,
                                    CellRunConfig)

PREREG = Path(__file__).resolve().parents[2] / "prereg"
AMENDMENT = PREREG / "AMENDMENT_001A_international_scenario_freeze_2026-10-08.json"
PLAN_001 = PREREG / "PLAN_001_after_tax_attribution.json"


@pytest.fixture()
def amendment():
    if not AMENDMENT.exists():
        pytest.skip("amendment 001A not present in this checkout")
    return json.loads(AMENDMENT.read_text(encoding="utf-8"))


def test_default_kappa_grid_is_the_confirmatory_one():
    """The shipped default must be the frozen grid, not the wider exploratory search."""
    assert CellRunConfig().kappa_grid == CONFIRMATORY_KAPPA_GRID


def test_confirmatory_grid_matches_the_amendment(amendment):
    defs = amendment["scenario_label_definitions"]["shrinkage"]
    assert set(CONFIRMATORY_KAPPA_GRID) == {defs["low"], defs["high"]}, (
        "cells.CONFIRMATORY_KAPPA_GRID and amendment 001A disagree about what shrinkage "
        "low/high mean; changing either requires changing both, and a new amendment"
    )


def test_confirmatory_grid_has_exactly_two_levels(amendment):
    """PLAN_001 registered shrinkage as a two-level dimension; N = 64 depends on it."""
    assert len(CONFIRMATORY_KAPPA_GRID) == 2
    assert amendment["confirmatory_trial_count_N"] == 64


def test_exploratory_grid_is_strictly_wider():
    assert set(CONFIRMATORY_KAPPA_GRID) < set(EXPLORATORY_KAPPA_GRID)


def test_amendment_preserves_the_parent_plan_fingerprint(amendment):
    """An amendment that changed the grid would have to change the fingerprint and N.

    The whole justification for keeping N = 64 is that the *search* did not change - only the
    empirical setting it runs in. If the fingerprint ever stops matching PLAN_001, that claim is
    no longer true and the deflation hurdle has to be recomputed.
    """
    if not PLAN_001.exists():
        pytest.skip("PLAN_001 not present")
    parent = json.loads(PLAN_001.read_text(encoding="utf-8"))
    assert amendment["parent_fingerprint"] == parent["fingerprint"]
    assert amendment["parent_fingerprint_unchanged"] is True
    assert amendment["trial_count_changed"] is False
    assert amendment["confirmatory_trial_count_N"] == parent["n_configurations"]


def test_distinct_configuration_count_is_below_the_reported_N(amendment):
    """N = 64 is a conservative upper bound; the arithmetic behind that must hold.

    Shrinkage is inert in the eight U = 0 cells, so distinct configurations number
    8*2*2 + 8*1*2 = 48. Reporting 64 raises the hurdle, which is the safe direction.
    """
    conv = amendment["trial_count_convention"]
    assert conv["distinct_configuration_count"] == 8 * 2 * 2 + 8 * 1 * 2 == 48
    assert conv["deflated_sharpe_uses_N"] == 64
    assert conv["N_is_conservative_upper_bound"] is True
    assert conv["deflated_sharpe_uses_N"] > conv["distinct_configuration_count"]


def test_baselines_are_excluded_from_N_and_the_ridge_exception_is_disclosed(amendment):
    conv = amendment["trial_count_convention"]
    from alphacomb.models.baselines import BASELINES
    assert set(conv["comparators_excluded_from_N"]) == set(BASELINES)
    assert "BASE-RIDGE" in conv["disclosed_exception"], (
        "BASE-RIDGE selects its penalty on validation, so it is itself selected; that exception "
        "must stay disclosed rather than being quietly folded into 'comparators are not searched'"
    )


def test_panel_mode_is_frozen_to_separate_countries(amendment):
    panel = amendment["panel_structure"]
    assert panel["mode"] == "SEPARATE_PER_COUNTRY"
    assert panel["countries"] == ["DEU", "IND", "JPN"]
    assert panel["pooled_fit_variant"] == "EXPLORATORY_ONLY"


def test_evaluation_window_matches_workstream_a(amendment):
    w = amendment["evaluation_windows"]
    assert w["primary_after_tax"] == {"start": "2009-01-01", "end": "2019-12-31"}
    assert w["clean_mechanism_subwindow"] == {"start": "2014-01-01", "end": "2018-03-31"}
    assert w["pre_2009_may_seed_tax_lots"] is False
    assert w["windows_usable_for_selection"] is False


def test_borrow_proxy_band_is_frozen_and_the_legacy_fallback_prohibited(amendment):
    b = amendment["borrow_fee_proxy"]
    assert b["primary_annual_rate"] == 0.01
    assert b["preregistered_robustness_rates"] == [0.0030, 0.0060, 0.0430, 0.0700]
    assert b["legacy_25bp_fallback"] == "PROHIBITED"
    assert b["certified_C6_borrow_fee_column"] == "PRESERVE_NULL"


def test_amendment_records_that_no_result_was_inspected_first(amendment):
    """Frozen decision 6B: scenarios fixed before results are seen. This is the audit trail."""
    assert amendment["real_results_inspected_before_amendment"] is False
    assert amendment["status"].startswith("FROZEN_PRE_RESULTS")
