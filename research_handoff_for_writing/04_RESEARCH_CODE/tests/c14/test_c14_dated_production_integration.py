from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from alphacomb.tax import (
    DatedC12Patch,
    DatedPatchConfig,
    DatedRegimeSchedule,
    LossCarryforwardBook,
    PointInTimeFXStore,
    SecurityReferenceValueStore,
    production_architecture_gate,
)
from alphacomb.tax.backtest import TaxConfig
from alphacomb.tax.backtest import _DatedYearBook
from alphacomb.tax.lots import TaxLotLedger
from alphacomb.tax.regimes import get_regime


ROOT = Path(__file__).resolve().parents[2]
SCHEDULE = ROOT / "data" / "intl_c14" / "candidate_working" / "c14_regime_candidate_source_frozen.csv"


def engine(**kwargs) -> DatedC12Patch:
    schedule = DatedRegimeSchedule.from_csv(SCHEDULE)
    return DatedC12Patch(DatedPatchConfig(schedule=schedule, **kwargs))


def test_packaged_architecture_gate_passes() -> None:
    gate = production_architecture_gate()
    assert gate["verdict"] == "PASS_DATED_C12_PRODUCTION_ARCHITECTURE"
    assert all(gate["capabilities"].values())


def test_packaged_germany_and_japan_transition_semantics() -> None:
    patch = engine()
    old = patch.resolve_event("DEU", "2009-02-28", acquisition_date="2008-12-31")
    new = patch.resolve_event("DEU", "2009-02-28", acquisition_date="2009-01-02")
    assert old.applied_rule_id == old.acquisition_rule_id
    assert new.applied_rule_id == new.event_rule_id
    assert patch.transaction_tax(
        "JPN", "1999-03-31", buy_notional=200, sell_notional=100
    ).total == pytest.approx(0.1)
    assert patch.transaction_tax(
        "JPN", "1999-04-01", buy_notional=200, sell_notional=100
    ).total == 0.0


def test_packaged_india_reference_basis_and_loss_vintages() -> None:
    references = SecurityReferenceValueStore()
    references.add(
        "IND", 101, "2018-01-31", 180, close_price=100,
        currency="INR", source="test",
    )
    patch = engine(reference_values=references)
    lot = patch.acquire("IND", 101, "2017-01-15", basis=100, currency="INR")
    lot = patch.attach_statutory_reference(lot, close_value_local=100)
    event = patch.realise(lot, "2018-04-30", sale_value=150, currency="INR")
    assert event.tax_basis == 150
    assert event.taxable_gain == 0

    losses = LossCarryforwardBook()
    losses.add_loss(2000, 100, "LISTED", carryforward_years=3)
    assert losses.offset(2003, 40, "LISTED", ring_fenced=True) == (0, 40)
    assert losses.vintages()[0].origin_year == 2000
    assert losses.offset(2004, 60, "LISTED", ring_fenced=True) == (60, 0)


def test_tax_config_requires_country_for_packaged_dated_engine() -> None:
    with pytest.raises(ValueError, match="dated_country"):
        TaxConfig(dated_engine=engine())
    with pytest.raises(ValueError, match="dated_local_currency"):
        TaxConfig(dated_engine=engine(), dated_country="JPN")
    configured = TaxConfig(
        dated_engine=engine(), dated_country="JPN", dated_local_currency="JPY"
    )
    assert configured.dated_country == "JPN"


def test_rate_overrides_are_unique_by_applied_rule_effective_date() -> None:
    patch = engine(rate_overrides={
        ("IND:TEMPORARY_TRANSITION:2003-03-01", "cgt_short"): 0.31,
        ("IND:TEMPORARY_TRANSITION:2003-04-01", "cgt_short"): 0.29,
    })
    march = patch.acquire("IND", 1, "2003-03-01", basis=100, currency="INR")
    april = patch.acquire("IND", 1, "2003-04-01", basis=100, currency="INR")
    assert patch.realise(march, "2003-03-15", sale_value=110, currency="INR").tax_rate == .31
    assert patch.realise(april, "2003-04-15", sale_value=110, currency="INR").tax_rate == .29


def test_event_date_dividend_rate_is_fail_closed() -> None:
    patch = engine()
    assert patch.dividend_tax_rate("IND", "2018-01-31") == 0.0
    with pytest.raises(RuntimeError, match="dividend_rate unresolved"):
        patch.dividend_tax_rate("JPN", "2002-12-31")


def test_section_112a_reference_contract_validates_fields(tmp_path: Path) -> None:
    path = tmp_path / "india_112a.csv"
    pd.DataFrame([{
        "country": "IND", "permno": 101, "reference_date": "2018-01-31",
        "fmv_price_local": 180, "close_price_local": 150, "currency": "INR",
        "source_field": "prchd", "source_cache": "frozen.csv.gz",
        "source_cache_sha256": "a" * 64,
        "statutory_definition": SecurityReferenceValueStore.INDIA_112A_DEFINITION,
        "endpoint_date": "2018-01-31",
    }]).to_csv(path, index=False)
    store = SecurityReferenceValueStore.from_validated_csv(path)
    assert store.get("IND", 101, "2018-01-31").high_to_close_ratio == pytest.approx(1.2)

    broken = pd.read_csv(path)
    broken["source_field"] = "prccd"
    broken.to_csv(path, index=False)
    with pytest.raises(RuntimeError, match="must be INR Compustat prchd"):
        SecurityReferenceValueStore.from_validated_csv(path)


def test_realised_events_and_losses_use_dated_engine_and_loss_book() -> None:
    patch = engine(accounting_currency="JPY")
    ledger = TaxLotLedger(
        get_regime("taxable"), dated_engine=patch,
        dated_country="JPN", dated_currency="JPY",
    )
    ledger.buy(1, "2014-01-31", 100)
    ledger.accrue_returns(pd.Series({1: -0.20}))
    loss = ledger.sell(1, "2014-12-31", 80)[0]
    assert loss.dated_event is not None
    assert loss.dated_event.taxable_gain == pytest.approx(-20)

    book = _DatedYearBook(patch, "JPN", "JPY")
    book.add_event(loss.dated_event)
    book.close_year(2014)
    assert book.carry.vintages()[0].origin_year == 2014

    ledger.buy(1, "2017-01-31", 100)
    ledger.accrue_returns(pd.Series({1: 0.20}))
    gain = ledger.sell(1, "2017-12-31", 120)[0]
    assert gain.dated_event is not None
    book.add_event(gain.dated_event)
    assert book.owed(2017) == pytest.approx(0)
    book.close_year(2017)
    assert book.carry.vintages() == ()


def test_section_112a_threshold_is_annual_and_applied_after_losses() -> None:
    patch = engine(tax_year_end_months={"IND": 3})
    loss_lot = patch.acquire("IND", 1, "2018-05-01", basis=200_000, currency="INR")
    gain_lot_a = patch.acquire("IND", 2, "2018-05-01", basis=100_000, currency="INR")
    gain_lot_b = patch.acquire("IND", 3, "2018-05-01", basis=100_000, currency="INR")
    loss = patch.realise(loss_lot, "2019-06-30", sale_value=150_000, currency="INR")
    gain_a = patch.realise(gain_lot_a, "2019-06-30", sale_value=180_000, currency="INR")
    gain_b = patch.realise(gain_lot_b, "2019-12-31", sale_value=220_000, currency="INR")

    book = _DatedYearBook(patch, "IND", "INR")
    for event in (loss, gain_a, gain_b):
        book.add_event(event)
    # 200k aggregate LTCG - 50k loss - 100k section 112A threshold = 50k.
    assert book.owed(2020) == pytest.approx(5_000)


def test_frozen_tax_year_boundaries_are_explicit() -> None:
    patch = engine(tax_year_end_months={"DEU": 12, "JPN": 12, "IND": 3})
    assert patch.tax_year("DEU", "2019-12-31") == 2019
    assert patch.tax_year("JPN", "2019-12-31") == 2019
    assert patch.tax_year("IND", "2019-03-31") == 2019
    assert patch.tax_year("IND", "2019-04-01") == 2020


def test_point_in_time_fx_uses_previous_business_day(tmp_path: Path) -> None:
    path = tmp_path / "fx.csv"
    pd.DataFrame([
        {"datadate": "2019-12-27", "currency": "INR", "usd_per_local": 0.0140},
        {"datadate": "2019-12-29", "currency": "INR", "usd_per_local": 0.0999},
        {"datadate": "2019-12-27", "currency": "EUR", "usd_per_local": 1.10},
    ]).to_csv(path, index=False)
    fx = PointInTimeFXStore.from_validated_csv(path)
    assert fx.source_date("INR", "2019-12-29") == pd.Timestamp("2019-12-27")
    assert fx("INR", "USD", "2019-12-29") == pytest.approx(0.0140)
    assert fx("INR", "EUR", "2019-12-29") == pytest.approx(0.0140 / 1.10)


def test_germany_zero_strategy_allowance_is_explicit() -> None:
    patch = engine(
        accounting_currency="EUR",
        allowance_allocations={("DEU", "ABGELTUNGSTEUER"): 0.0},
    )
    amount = patch.annual_amount_local("DEU", "2019-12-31")
    assert amount is not None
    assert amount.kind == "CAPITAL_INCOME_ALLOWANCE"
    assert amount.amount_local == 0.0


def test_frozen_sample_materializes_complete_engine() -> None:
    patch = DatedC12Patch.from_frozen_evaluation_artifacts(ROOT)
    assert patch.tax_year_end_month("DEU") == 12
    assert patch.tax_year_end_month("JPN") == 12
    assert patch.tax_year_end_month("IND") == 3
    assert patch.dividend_tax_rate("JPN", "2014-01-01") == pytest.approx(0.20315)
    assert patch.config.fx_provider is not None
    assert patch.config.fx_provider("INR", "USD", pd.Timestamp("2019-12-31")) > 0
    assert len(patch.config.reference_values) == 546
