"""Fail-closed validation of the frozen 2009--2019 C14 evaluation sample.

This is a configuration-completeness proof.  It performs no source research,
does not run real portfolio results, and does not write C1--C6 artefacts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from alphacomb.tax import (
    DatedC12Patch,
    DatedRegimeSchedule,
    PointInTimeFXStore,
    SecurityReferenceValueStore,
)
from alphacomb.tax.backtest import _DatedYearBook


ROOT = Path(__file__).resolve().parent
SCHEDULE = ROOT / "data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv"
DECISIONS = ROOT / "configs/workstream_a_frozen_decisions.json"
SAMPLE = ROOT / "configs/workstream_a_c14_evaluation_sample_2026-10-07.json"
REFERENCE = ROOT / "data/intl_c14/candidate_working/IND_SECTION_112A_REFERENCE_VALUES.csv"
IND_UNIVERSE = ROOT / "data/intl_c1/production/IND/universe.parquet"
FX_CACHE = ROOT / "data/intl_c6/cache/C6_WRDS_DAILY_FX_TO_USD.csv.gz"
FX_AUDIT = ROOT / "data/intl_c6/audit/C6_WRDS_DAILY_FX_TO_USD_AUDIT.json"
SOURCE_PASS = ROOT / "data/intl_c14/audit/C14_BOUNDED_PRIMARY_SOURCE_PASS_2026-10-07.json"
OUT = ROOT / "data/intl_c14/audit/C14_EVALUATION_SAMPLE_VALIDATION_2026-10-07.json"

WINDOW = (pd.Timestamp("2009-01-01"), pd.Timestamp("2019-12-31"))
MECHANISM = (pd.Timestamp("2014-01-01"), pd.Timestamp("2018-03-31"))
COUNTRY_CURRENCY = {"DEU": "EUR", "JPN": "JPY", "IND": "INR"}
REQUIRED_FIELDS = (
    "stt_buy", "stt_sell", "cgt_short", "cgt_long", "dividend_rate",
    "loss_carryforward_years", "losses_ring_fenced", "ordinary_income_offset",
    "loss_bucket",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _intersects(row: dict[str, object], start: pd.Timestamp, end: pd.Timestamp) -> bool:
    return pd.Timestamp(row["effective_to"]) >= start and pd.Timestamp(row["effective_from"]) <= end


def _blocker_intersects(blocker: dict[str, object], start: pd.Timestamp, end: pd.Timestamp) -> bool:
    raw = str(blocker["date_range"])
    left, right = raw.split(" and ") if " and " in raw else (raw, "")
    ranges = [left, right] if right else [left]
    for item in ranges:
        lo, hi = (token.strip() for token in item.split("/"))
        if pd.Timestamp(hi) >= start and pd.Timestamp(lo) <= end:
            return True
    return False


def main() -> None:
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    expected_choices = ["1A", "2C", "3A", "4A", "5A", "6B"]
    actual_choices = [entry["choice"] for entry in decisions["decisions"].values()]
    check(
        "six_human_decisions_frozen_pre_results",
        decisions["status"] == "FROZEN_6_OF_6"
        and actual_choices == expected_choices
        and decisions["real_results_inspected_before_freeze"] is False
        and sample["real_results_inspected_before_amendment"] is False,
        actual_choices,
    )
    check(
        "sample_dates_and_cold_start_frozen",
        sample["primary_after_tax_evaluation_window"] == {"start": "2009-01-01", "end": "2019-12-31"}
        and sample["clean_mechanism_subwindow"]["start"] == "2014-01-01"
        and sample["clean_mechanism_subwindow"]["end"] == "2018-03-31"
        and sample["tax_ledger_inception"] == "2009-01-01"
        and sample["pre_2009_acquisition_lots_permitted"] is False,
        sample,
    )

    schedule_frame = pd.read_csv(SCHEDULE, dtype=str, keep_default_na=False)
    schedule = DatedRegimeSchedule.from_csv(SCHEDULE)
    for label, (start, end) in {"primary": WINDOW, "mechanism": MECHANISM}.items():
        coverage = schedule.validate(start, end)
        check(
            f"{label}_window_exact_daily_regime_coverage",
            coverage == {"countries": 3, "gaps": 0, "overlaps": 0},
            coverage,
        )
        unresolved: list[dict[str, str]] = []
        intersecting = [row for row in schedule_frame.to_dict("records") if _intersects(row, start, end)]
        for row in intersecting:
            for field in REQUIRED_FIELDS:
                if row.get(field, "") == "":
                    unresolved.append({
                        "country": row["country"], "effective_from": row["effective_from"],
                        "legal_regime": row["legal_regime"], "field": field,
                    })
            if row.get("annual_exempt_local", "") and not (
                row.get("annual_exempt_currency", "") and row.get("annual_exempt_kind", "")
            ):
                unresolved.append({
                    "country": row["country"], "effective_from": row["effective_from"],
                    "legal_regime": row["legal_regime"], "field": "annual_amount_contract",
                })
            if row.get("basis_rule", "") and not row.get("basis_reference_date", ""):
                unresolved.append({
                    "country": row["country"], "effective_from": row["effective_from"],
                    "legal_regime": row["legal_regime"], "field": "basis_reference_date",
                })
        check(
            f"{label}_window_required_C14_fields_numeric",
            not unresolved,
            {"intersecting_rule_count": len(intersecting), "unresolved": unresolved},
        )

    source_pass = json.loads(SOURCE_PASS.read_text(encoding="utf-8"))
    blockers = source_pass["remaining_source_facts"]
    primary_hits = [item for item in blockers if _blocker_intersects(item, *WINDOW)]
    mechanism_hits = [item for item in blockers if _blocker_intersects(item, *MECHANISM)]
    check(
        "nine_historical_blockers_outside_primary_event_and_acquisition_domain",
        len(blockers) == 9 and not primary_hits
        and sample["pre_2009_acquisition_lots_permitted"] is False,
        {"ledger_blockers": len(blockers), "intersections": primary_hits},
    )
    check(
        "nine_historical_blockers_outside_mechanism_subwindow",
        not mechanism_hits,
        mechanism_hits,
    )

    reference_store = SecurityReferenceValueStore.from_validated_csv(REFERENCE)
    india = pd.read_parquet(IND_UNIVERSE, columns=["date", "permno", "in_universe"])
    india["date"] = pd.to_datetime(india["date"])
    required_keys = set(
        india.loc[
            india["date"].eq(pd.Timestamp("2018-01-31")) & india["in_universe"],
            "permno",
        ].astype(str)
    )
    reference_keys = set(
        pd.read_csv(REFERENCE, dtype={"permno": str})["permno"].astype(str)
    )
    check(
        "section_112a_reference_contract_exact_for_snapshot_holdings",
        len(reference_store) == 546 and required_keys == reference_keys,
        {
            "required_investible_keys": len(required_keys), "validated_reference_keys": len(reference_keys),
            "missing": sorted(required_keys - reference_keys), "extraneous": sorted(reference_keys - required_keys),
            "ledger_order": "trade_to_target_then_snapshot_reference",
        },
    )

    fx_audit = json.loads(FX_AUDIT.read_text(encoding="utf-8"))
    fx = PointInTimeFXStore.from_validated_csv(FX_CACHE)
    fx_failures: list[dict[str, str]] = []
    for country, currency in COUNTRY_CURRENCY.items():
        dates = pd.date_range(WINDOW[0], WINDOW[1], freq="ME").union(
            pd.DatetimeIndex([WINDOW[0], WINDOW[1]])
        )
        for date in dates:
            try:
                source_date = fx.source_date(currency, date)
                rate = fx(currency, "USD", date)
                if source_date > date or source_date.dayofweek >= 5 or rate <= 0:
                    raise ValueError("forward/non-business/non-positive FX")
            except Exception as exc:  # fail-closed audit detail
                fx_failures.append({"country": country, "date": str(date.date()), "error": str(exc)})
    check(
        "decision_3A_point_in_time_FX_complete",
        fx_audit["verdict"] == "PASS_WRDS_DAILY_FX_TO_USD_WITH_EXPLICIT_SOURCE_DATE_GAPS"
        and fx_audit["output_sha256"] == sha256(FX_CACHE)
        and not fx_failures,
        {"cache_sha256": sha256(FX_CACHE), "failures": fx_failures},
    )

    engine = DatedC12Patch.from_frozen_evaluation_artifacts(ROOT)
    runtime_failures: list[dict[str, str]] = []
    for country, currency in COUNTRY_CURRENCY.items():
        for date in pd.date_range(WINDOW[0], WINDOW[1], freq="ME"):
            try:
                engine.transaction_tax(country, date, buy_notional=1.0, sell_notional=1.0)
                engine.dividend_tax_rate(country, date)
                engine.tax_year(country, date)
                fx(currency, "USD", date)
            except Exception as exc:
                runtime_failures.append({"country": country, "date": str(date.date()), "error": str(exc)})
    check(
        "every_monthly_event_date_resolves_fail_closed_without_historical_blocker",
        not runtime_failures,
        runtime_failures,
    )

    first_reference = next(iter(sorted(reference_keys)))
    lot = engine.acquire("IND", first_reference, "2017-01-31", basis=100_000, currency="INR")
    lot = engine.attach_statutory_reference(lot, close_value_local=100_000)
    event = engine.realise(lot, "2018-12-31", sale_value=350_000, currency="INR")
    book = _DatedYearBook(engine, "IND", "INR")
    book.add_event(event)
    threshold_tax = book.owed(engine.tax_year("IND", event.disposal_date))
    check(
        "section_112a_basis_and_annual_threshold_executable",
        event.basis_rule == "IND_SECTION_55_2_AC"
        and event.annual_amount_kind == "SECTION_112A_EXCESS_ONLY_THRESHOLD"
        and threshold_tax >= 0,
        {
            "permno": first_reference, "basis_rule": event.basis_rule,
            "threshold_kind": event.annual_amount_kind, "computed_tax_local": threshold_tax,
        },
    )
    deu_allowance = engine.annual_amount_local("DEU", "2019-12-31")
    check(
        "decision_2C_Germany_allowance_zero_allocated_explicitly",
        deu_allowance is not None and deu_allowance.amount_local == 0
        and deu_allowance.currency == "EUR",
        None if deu_allowance is None else deu_allowance.__dict__,
    )

    failures = [item for item in checks if item["status"] == "FAIL"]
    result = {
        "C14_EVALUATION_WINDOW": "PASS" if not failures else "BLOCKED",
        "primary_after_tax_evaluation_window": [str(WINDOW[0].date()), str(WINDOW[1].date())],
        "clean_mechanism_subwindow": [str(MECHANISM[0].date()), str(MECHANISM[1].date())],
        "all_events_avoid_nine_historical_source_blockers": not primary_hits and not mechanism_hits,
        "checks": checks,
        "failures": failures,
        "hashes": {
            "schedule": sha256(SCHEDULE), "decisions": sha256(DECISIONS),
            "sample_configuration": sha256(SAMPLE), "section_112a_reference": sha256(REFERENCE),
            "fx_cache": sha256(FX_CACHE),
        },
        "real_results_inspected": False,
        "production_promoted": False,
        "github_written": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "C14_EVALUATION_WINDOW": result["C14_EVALUATION_WINDOW"],
        "checks": len(checks), "failure_count": len(failures),
        "failures": [item["check"] for item in failures],
    }, indent=2))
    if failures:
        raise RuntimeError("C14 evaluation-sample validation failed")


if __name__ == "__main__":
    main()
