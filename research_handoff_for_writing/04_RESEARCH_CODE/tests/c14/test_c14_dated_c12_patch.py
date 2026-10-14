from __future__ import annotations

from pathlib import Path

import pytest

from research.c14_dated_c12_patch import (
    DatedC12Patch,
    DatedPatchConfig,
    LossCarryforwardBook,
    MissingDatedTaxConfiguration,
    SecurityReferenceValueStore,
    StatutoryAmount,
)
from research.c14_dated_engine_reference import DatedRegimeSchedule


ROOT = Path(__file__).resolve().parents[2]
SCHEDULE_PATH = (
    ROOT / "data" / "intl_c14" / "candidate_working"
    / "c14_regime_candidate_source_frozen.csv"
)


def schedule() -> DatedRegimeSchedule:
    return DatedRegimeSchedule.from_csv(SCHEDULE_PATH)


def patch(**kwargs) -> DatedC12Patch:
    return DatedC12Patch(DatedPatchConfig(schedule=schedule(), **kwargs))


def test_germany_keeps_acquisition_transition_state_across_2009() -> None:
    engine = patch()
    old = engine.resolve_event("DEU", "2009-02-28", acquisition_date="2008-12-31")
    new = engine.resolve_event("DEU", "2009-02-28", acquisition_date="2009-01-02")

    assert old.event_rule_id == "DEU:ABGELTUNGSTEUER:2009-01-01"
    assert old.acquisition_rule_id == "DEU:PRIVATE_SALE_12M_HALBEINKUENFTE:2002-01-01"
    assert old.applied_rule_id == old.acquisition_rule_id
    assert old.transition_rule == "DEU_PRE_2009_ACQUISITION_GRANDFATHERED"
    assert new.applied_rule_id == new.event_rule_id


def test_india_112a_uses_security_specific_reference_value() -> None:
    values = SecurityReferenceValueStore()
    values.add("IND", 101, "2018-01-31", 180.0, currency="INR", source="certified-test")
    values.add("IND", 202, "2018-01-31", 120.0, currency="INR", source="certified-test")
    engine = patch(reference_values=values)

    lot_101 = engine.acquire("IND", 101, "2017-01-15", basis=100.0, currency="INR")
    lot_202 = engine.acquire("IND", 202, "2017-01-15", basis=100.0, currency="INR")
    first = engine.realise(lot_101, "2018-04-30", sale_value=150.0, currency="INR")
    second = engine.realise(lot_202, "2018-04-30", sale_value=150.0, currency="INR")

    assert first.tax_basis == 150.0
    assert first.taxable_gain == 0.0
    assert second.tax_basis == 120.0
    assert second.taxable_gain == 30.0
    assert first.basis_rule == "IND_SECTION_55_2_AC"


def test_missing_india_reference_value_fails_closed() -> None:
    lot = patch().acquire("IND", 303, "2017-01-15", basis=100.0, currency="INR")
    with pytest.raises(MissingDatedTaxConfiguration, match="31-Jan-2018 reference value"):
        patch().realise(lot, "2018-04-30", sale_value=150.0, currency="INR")


def test_india_112a_basis_is_not_applied_to_a_short_term_lot() -> None:
    engine = patch()
    lot = engine.acquire("IND", 404, "2017-12-31", basis=100.0, currency="INR")
    realised = engine.realise(lot, "2018-04-30", sale_value=150.0, currency="INR")
    assert not realised.long_term
    assert realised.basis_rule is None
    assert realised.tax_basis == 100.0
    assert realised.taxable_gain == 50.0


def test_japan_transaction_tax_changes_on_exact_abolition_date() -> None:
    engine = patch()
    before = engine.transaction_tax("JPN", "1999-03-31", buy_notional=200.0, sell_notional=100.0)
    after = engine.transaction_tax("JPN", "1999-04-01", buy_notional=200.0, sell_notional=100.0)
    assert before.buy_tax == 0.0
    assert before.sell_tax == pytest.approx(0.1)
    assert before.total == pytest.approx(0.1)
    assert after.total == 0.0


def test_holding_period_boundary_is_evaluated_per_lot() -> None:
    engine = patch(rate_overrides={
        ("DEU", "PRIVATE_SALE_12M_HALBEINKUENFTE", "cgt_short"): 0.40,
    })
    lot = engine.acquire("DEU", 1, "2007-01-31", basis=100.0, currency="EUR")
    on_boundary = engine.realise(lot, "2008-01-31", sale_value=110.0, currency="EUR")
    after_boundary = engine.realise(lot, "2008-02-01", sale_value=110.0, currency="EUR")
    assert not on_boundary.long_term
    assert on_boundary.tax_rate == 0.40
    assert after_boundary.long_term
    assert after_boundary.tax_rate == 0.0


def test_unresolved_rate_requires_explicit_configuration() -> None:
    engine = patch()
    lot = engine.acquire("DEU", 1, "2007-01-31", basis=100.0, currency="EUR")
    with pytest.raises(MissingDatedTaxConfiguration, match="cgt_short"):
        engine.realise(lot, "2007-12-31", sale_value=110.0, currency="EUR")


def test_ring_fenced_and_unfenced_loss_offsets_differ() -> None:
    ringed = LossCarryforwardBook()
    ringed.add_loss(2000, 100.0, "LISTED", carryforward_years=3)
    assert ringed.offset(2001, 60.0, "OTHER", ring_fenced=True) == (60.0, 0.0)

    broad = LossCarryforwardBook()
    broad.add_loss(2000, 100.0, "LISTED", carryforward_years=3)
    assert broad.offset(2001, 60.0, "OTHER", ring_fenced=False) == (0.0, 60.0)


def test_loss_buckets_support_asymmetric_india_st_lt_offsets() -> None:
    short_loss = LossCarryforwardBook()
    short_loss.add_loss(
        2018,
        100.0,
        "IND_ST",
        carryforward_years=8,
        eligible_gain_buckets={"IND_ST", "IND_LT"},
    )
    assert short_loss.offset(2019, 60.0, "IND_LT", ring_fenced=True) == (0.0, 60.0)

    long_loss = LossCarryforwardBook()
    long_loss.add_loss(
        2018,
        100.0,
        "IND_LT",
        carryforward_years=8,
        eligible_gain_buckets={"IND_LT"},
    )
    assert long_loss.offset(2019, 60.0, "IND_ST", ring_fenced=True) == (60.0, 0.0)


@pytest.mark.parametrize("life", [3, 8])
def test_loss_is_usable_in_final_year_and_expires_in_following_year(life: int) -> None:
    final_year = 2000 + life
    book = LossCarryforwardBook()
    book.add_loss(2000, 50.0, "CAPITAL", carryforward_years=life)
    assert book.offset(final_year, 20.0, "CAPITAL", ring_fenced=True) == (0.0, 20.0)
    assert book.offset(final_year + 1, 30.0, "CAPITAL", ring_fenced=True) == (30.0, 0.0)


def test_partial_use_does_not_refresh_original_loss_vintage() -> None:
    book = LossCarryforwardBook()
    vintage_id = book.add_loss(2000, 100.0, "LISTED", carryforward_years=3)
    assert book.offset(2002, 40.0, "LISTED", ring_fenced=True) == (0.0, 40.0)
    remaining = book.vintages()[0]
    assert remaining.vintage_id == vintage_id
    assert remaining.origin_year == 2000
    assert remaining.original_amount == 100.0
    assert remaining.remaining_amount == 60.0
    assert book.offset(2004, 60.0, "LISTED", ring_fenced=True) == (60.0, 0.0)


def test_statutory_amount_retains_local_source_and_converts_at_event_date() -> None:
    rates = {
        ("INR", "USD", "2018-04-30"): 0.015,
        ("INR", "USD", "2019-04-30"): 0.014,
    }

    def fx(local: str, accounting: str, date) -> float:
        return rates[(local, accounting, str(date.date()))]

    threshold = StatutoryAmount(100_000.0, "INR", "SECTION_112A_EXCESS_ONLY_THRESHOLD")
    assert threshold.amount_local == 100_000.0
    assert threshold.currency == "INR"
    assert threshold.in_accounting_currency("USD", "2018-04-30", fx) == 1_500.0
    assert threshold.in_accounting_currency("USD", "2019-04-30", fx) == 1_400.0


def test_side_specific_transaction_tax_requires_sourced_rate() -> None:
    with pytest.raises(MissingDatedTaxConfiguration, match="stt_buy"):
        patch().transaction_tax("DEU", "1990-06-30", buy_notional=100.0, sell_notional=0.0)


def test_allowance_and_brokerage_remain_explicit_parameters() -> None:
    with pytest.raises(MissingDatedTaxConfiguration, match="allowance allocation"):
        patch().allocated_allowance("DEU", "2010-12-31")
    with pytest.raises(MissingDatedTaxConfiguration, match="brokerage assumption"):
        patch().brokerage_rate("DEU", "2010-12-31")

    def fx(local: str, accounting: str, date) -> float:
        assert (local, accounting, str(date.date())) == ("EUR", "USD", "2010-12-31")
        return 1.25

    configured = patch(
        fx_provider=fx,
        allowance_allocations={("DEU", "ABGELTUNGSTEUER"): 0.5},
        brokerage_rates={("DEU", "ABGELTUNGSTEUER"): 0.0004},
    )
    assert configured.allocated_allowance("DEU", "2010-12-31") == pytest.approx(500.625)
    assert configured.brokerage_rate("DEU", "2010-12-31") == 0.0004
