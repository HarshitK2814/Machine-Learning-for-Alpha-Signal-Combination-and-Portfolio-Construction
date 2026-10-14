from __future__ import annotations

from pathlib import Path

import pandas as pd

from research.c14_dated_engine_reference import (
    DatedRegimeSchedule,
    LossCarryforwardLedger,
    india_section_112a_deemed_cost,
    is_long_term,
    static_engine_compatibility_gate,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEDULE = ROOT / "data" / "intl_c14" / "candidate_working" / "c14_regime_candidate_source_frozen.csv"


def schedule() -> DatedRegimeSchedule:
    return DatedRegimeSchedule.from_csv(SCHEDULE)


def test_schedule_has_exact_daily_coverage_without_overlap() -> None:
    result = schedule().validate("1990-01-01", "2020-12-31")
    assert result == {"countries": 3, "gaps": 0, "overlaps": 0}


def test_deu_2009_sale_preserves_pre_2009_acquisition_regime() -> None:
    resolved = schedule().resolve(
        "DEU",
        event_date="2009-02-28",
        acquisition_date="2008-12-31",
    )
    assert resolved.legal_regime == "PRIVATE_SALE_12M_HALBEINKUENFTE"
    assert resolved.transition_rule == "DEU_PRE_2009_ACQUISITION_GRANDFATHERED"

    new_lot = schedule().resolve(
        "DEU",
        event_date="2009-02-28",
        acquisition_date="2009-01-02",
    )
    assert new_lot.legal_regime == "ABGELTUNGSTEUER"


def test_india_2018_section_112a_grandfathered_basis() -> None:
    assert india_section_112a_deemed_cost(
        actual_cost=100.0,
        fmv_2018_01_31=180.0,
        sale_value=150.0,
    ) == 150.0
    assert india_section_112a_deemed_cost(
        actual_cost=200.0,
        fmv_2018_01_31=180.0,
        sale_value=150.0,
    ) == 200.0

    resolved = schedule().resolve(
        "IND",
        event_date="2018-04-30",
        acquisition_date="2018-01-15",
    )
    assert resolved.basis_rule == "IND_SECTION_55_2_AC"


def test_japan_transaction_tax_abolition_boundary() -> None:
    before = schedule().resolve("JPN", "1999-03-31")
    after = schedule().resolve("JPN", "1999-04-01")
    assert before.stt_buy == 0.0
    assert before.stt_sell == 0.001
    assert after.stt_buy == 0.0
    assert after.stt_sell == 0.0


def test_holding_period_boundary_is_strictly_beyond_anniversary() -> None:
    acquired = pd.Timestamp("2007-01-31")
    assert not is_long_term(acquired, "2008-01-31", months=12)
    assert is_long_term(acquired, "2008-02-01", months=12)


def test_loss_carryforward_includes_final_allowed_year_and_is_ring_fenced() -> None:
    book = LossCarryforwardLedger(carryforward_years=3, ring_fenced=True)
    book.add_loss(origin_year=2000, amount=100.0, bucket="LISTED_SHARES")

    assert book.offset(year=2002, gain=40.0, bucket="OTHER_CAPITAL") == (40.0, 0.0)
    assert book.offset(year=2003, gain=60.0, bucket="LISTED_SHARES") == (0.0, 60.0)

    book.add_loss(origin_year=2000, amount=25.0, bucket="LISTED_SHARES")
    assert book.offset(year=2004, gain=25.0, bucket="LISTED_SHARES") == (25.0, 0.0)


def test_static_engine_gate_passes_after_dated_engine_integration() -> None:
    gate = static_engine_compatibility_gate(ROOT)
    assert gate["verdict"] == "PASS"
    assert gate["blocking_capabilities"] == []
    assert gate["evidence"]["production_dated_engine_packaged"] is True
    assert gate["evidence"]["production_backtest_accepts_dated_engine"] is True
