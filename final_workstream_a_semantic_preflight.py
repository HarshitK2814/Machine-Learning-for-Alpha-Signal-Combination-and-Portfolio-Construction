"""Fail-closed final Workstream-A semantic preflight.

This script validates the approved decisions and the non-production integration
without promoting candidates, running real results, or writing to Git.  A human
choice is not treated as a substitute for a missing dated numeric schedule.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
from alphacomb.contracts.io import read_yaml
from alphacomb.tax import SecurityReferenceValueStore, production_architecture_gate
from research.c14_dated_engine_reference import static_engine_compatibility_gate


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "workstream_a_closeout"
DECISIONS = ROOT / "configs" / "workstream_a_frozen_decisions.json"
C6 = ROOT / "data" / "intl_c6" / "candidate_working" / "C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz"
C14 = ROOT / "data" / "intl_c14" / "candidate_working" / "c14_regime_candidate_source_frozen.csv"
JUNIT = OUT / "WORKSTREAM_A_FULL_TESTS_2026-10-07.xml"
REFERENCE = ROOT / "data" / "intl_c14" / "candidate_working" / "IND_SECTION_112A_REFERENCE_VALUES.csv"
SOURCE_PASS = ROOT / "data" / "intl_c14" / "audit" / "C14_BOUNDED_PRIMARY_SOURCE_PASS_2026-10-07.json"
SAMPLE_CONFIG = ROOT / "configs" / "workstream_a_c14_evaluation_sample_2026-10-07.json"
SAMPLE_VALIDATION = ROOT / "data" / "intl_c14" / "audit" / "C14_EVALUATION_SAMPLE_VALIDATION_2026-10-07.json"
SAMPLE_AMENDMENT = ROOT / "data" / "intl_c14" / "audit" / "WORKSTREAM_A_PRE_RESULTS_SAMPLE_AMENDMENT_2026-10-07.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def junit_summary(path: Path) -> dict[str, int | bool]:
    if not path.exists():
        return {"present": False, "tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    return {
        "present": True,
        "tests": sum(int(s.attrib.get("tests", 0)) for s in suites),
        "failures": sum(int(s.attrib.get("failures", 0)) for s in suites),
        "errors": sum(int(s.attrib.get("errors", 0)) for s in suites),
        "skipped": sum(int(s.attrib.get("skipped", 0)) for s in suites),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    expected_choices = {
        "representative_taxable_investor_rate_paths": "1A",
        "allowance_allocation": "2C",
        "statutory_currency_FX_timing": "3A",
        "brokerage_platform_fee_scope": "4A",
        "pre_2003_Japan_taxpayer_route": "5A",
        "missing_borrow_fee_treatment": "6B",
    }
    actual_choices = {key: value.get("choice") for key, value in decisions.get("decisions", {}).items()}
    check(
        "human_decisions_6_of_6_frozen",
        decisions.get("status") == "FROZEN_6_OF_6"
        and decisions.get("approved_by") == "Absar Wani"
        and decisions.get("approval_date") == "2026-10-07"
        and actual_choices == expected_choices,
        actual_choices,
    )
    borrow = decisions["decisions"]["missing_borrow_fee_treatment"]
    check(
        "borrow_proxy_preregistered",
        borrow["model"] == "MODELLED_FLAT_BORROW_PROXY_V1"
        and borrow["annual_rate"] == 0.01
        and borrow["sensitivity_annual_rates"] == [0.003, 0.006, 0.043, 0.07]
        and borrow["certified_C6_borrow_fee_column"] == "PRESERVE_NULL",
        borrow,
    )

    base = read_yaml(ROOT / "configs" / "base.yaml")
    configured = base["costs"]["borrow_fee_model"]
    check(
        "borrow_proxy_explicit_consumer_configuration",
        configured == {
            "enabled": True,
            "name": "MODELLED_FLAT_BORROW_PROXY_V1",
            "annual_rate": 0.01,
            "sensitivity_annual_rates": [0.003, 0.006, 0.043, 0.07],
            "certified_c6_unchanged": True,
        },
        configured,
    )
    runtime_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src" / "alphacomb").rglob("*.py")
    )
    legacy_tokens = [token for token in ("fillna(0.0025)", "borrow_gc_bps_pa", "borrow_htb_bps_pa") if token in runtime_text]
    check("legacy_25bp_borrow_fallback_absent", not legacy_tokens, legacy_tokens)

    c6 = pd.read_csv(C6, usecols=["spread", "sigma_d", "adv_usd", "borrow_fee"])
    check("certified_C6_borrow_fee_preserved_null", c6["borrow_fee"].isna().all(), int(c6["borrow_fee"].notna().sum()))
    eligible = c6[["spread", "sigma_d", "adv_usd"]].notna().all(axis=1) & c6["adv_usd"].gt(0)
    check(
        "C6_missing_spread_fail_closed",
        int(c6["spread"].isna().sum()) == 58_389 and int(eligible.sum()) == 622_817,
        {"missing_spread": int(c6["spread"].isna().sum()), "fully_observable_market_rows": int(eligible.sum())},
    )
    mechanical = json.loads((OUT / "WORKSTREAM_A_MECHANICAL_PREFLIGHT_2026-10-07.json").read_text(encoding="utf-8"))
    check("C1_to_C6_mechanical_preflight", not mechanical.get("failures"), mechanical.get("verdict"))

    india = json.loads(
        (ROOT / "data" / "intl_c5" / "candidate_term_drate_working" / "IND_TERM_RBI_91D_CUTOFF_CERTIFICATION.json")
        .read_text(encoding="utf-8")
    )
    check(
        "India_TERM_activation_and_gap_gate",
        india.get("verdict") == "PASS_WORKING_CERTIFIED_RBI_91D_CUTOFF"
        and india.get("new_activation") == "1998-08-31"
        and india.get("post_activation_gaps") == [],
        {key: india.get(key) for key in ("verdict", "new_activation", "post_activation_gaps")},
    )

    architecture = production_architecture_gate()
    compatibility = static_engine_compatibility_gate(ROOT)
    check("dated_C12_packaged_architecture", architecture["verdict"] == "PASS_DATED_C12_PRODUCTION_ARCHITECTURE", architecture)
    check("dated_C12_static_compatibility", compatibility["verdict"] == "PASS", compatibility)
    backtest_text = (ROOT / "src" / "alphacomb" / "tax" / "backtest.py").read_text(encoding="utf-8")
    lots_text = (ROOT / "src" / "alphacomb" / "tax" / "lots.py").read_text(encoding="utf-8")
    dated_text = (ROOT / "src" / "alphacomb" / "tax" / "dated.py").read_text(encoding="utf-8")
    capital_gain_wired = "dated_engine.realise" in lots_text
    dividend_wired = "dividend_tax_rate" in backtest_text
    bucket_book_wired = "LossCarryforwardBook" in backtest_text and "_DatedYearBook" in backtest_text
    semantic_wiring = {
        "capital_gain_events_use_dated_engine": capital_gain_wired,
        "dividend_events_use_dated_engine": dividend_wired,
        "bucketed_loss_book_used_by_backtest": bucket_book_wired,
        "side_specific_transaction_tax_used": "dated_engine.transaction_tax" in backtest_text,
        "rule_id_effective_date_override_key": "RateKey = tuple[str, str]" in dated_text,
        "static_adapter_retained": "book: _YearBook | _DatedYearBook" in backtest_text,
        "annual_section_112A_threshold_wired": "SECTION_112A_EXCESS_ONLY_THRESHOLD" in backtest_text,
        "explicit_tax_year_boundaries_wired": "tax_year_end_month" in backtest_text and "def tax_year(" in dated_text,
        "decision_3A_year_end_accounting_fail_closed": "requires year_end accounting under frozen decision 3A" in backtest_text,
    }
    check("dated_C12_full_backtest_wiring", all(semantic_wiring.values()), semantic_wiring)

    source_pass = json.loads(SOURCE_PASS.read_text(encoding="utf-8"))
    remaining_source_facts = source_pass.get("remaining_source_facts", [])
    sample_config = json.loads(SAMPLE_CONFIG.read_text(encoding="utf-8"))
    sample_validation = json.loads(SAMPLE_VALIDATION.read_text(encoding="utf-8"))
    check(
        "C14_evaluation_window_2009_2019_complete",
        sample_validation.get("C14_EVALUATION_WINDOW") == "PASS"
        and sample_validation.get("failures") == []
        and sample_validation.get("primary_after_tax_evaluation_window") == ["2009-01-01", "2019-12-31"]
        and sample_validation.get("all_events_avoid_nine_historical_source_blockers") is True
        and sample_validation.get("hashes", {}).get("schedule") == sha256(C14)
        and sample_validation.get("hashes", {}).get("decisions") == sha256(DECISIONS)
        and sample_validation.get("hashes", {}).get("sample_configuration") == sha256(SAMPLE_CONFIG),
        {
            "validation": str(SAMPLE_VALIDATION.relative_to(ROOT)),
            "window": sample_validation.get("primary_after_tax_evaluation_window"),
            "failures": sample_validation.get("failures"),
        },
    )
    check(
        "C14_clean_mechanism_subwindow_2014_to_2018Q1_complete",
        sample_validation.get("clean_mechanism_subwindow") == ["2014-01-01", "2018-03-31"]
        and all(
            item.get("status") == "PASS"
            for item in sample_validation.get("checks", [])
            if str(item.get("check", "")).startswith("mechanism_")
        ),
        sample_validation.get("clean_mechanism_subwindow"),
    )
    check(
        "C14_historical_source_blockers_retained_nonproduction",
        len(remaining_source_facts) == 9
        and sample_config.get("pre_2009_acquisition_lots_permitted") is False
        and sample_validation.get("all_events_avoid_nine_historical_source_blockers") is True,
        {"retained_blockers": len(remaining_source_facts), "imputed": False},
    )
    amendment_text = SAMPLE_AMENDMENT.read_text(encoding="utf-8") if SAMPLE_AMENDMENT.exists() else ""
    required_declarations = [
        "No real results had been inspected before this amendment",
        "C1-C6 historical\ndata remain unchanged",
        "tax-dependent\ninternational evaluation",
        "not because of observed strategy\nperformance",
        "1990-2008 observations remain available for model training",
        "unresolved\nearlier C14 regimes remain explicitly non-production",
    ]
    check(
        "C14_pre_results_sample_amendment_frozen",
        SAMPLE_AMENDMENT.exists()
        and all(token in amendment_text for token in required_declarations)
        and sample_config.get("real_results_inspected_before_amendment") is False,
        {"path": str(SAMPLE_AMENDMENT.relative_to(ROOT)), "required_declarations": required_declarations},
    )
    reference_detail: object
    try:
        reference_store = SecurityReferenceValueStore.from_validated_csv(REFERENCE)
        reference_detail = {"path": str(REFERENCE.relative_to(ROOT)), "rows": len(reference_store)}
        reference_valid = len(reference_store) == 546
    except Exception as exc:
        reference_detail = {"path": str(REFERENCE.relative_to(ROOT)), "error": str(exc)}
        reference_valid = False
    check(
        "India_section_112A_reference_values_available",
        reference_valid,
        reference_detail,
    )
    check(
        "C14_closeout_scope_artifacts_present",
        SOURCE_PASS.exists() and REFERENCE.exists() and SAMPLE_CONFIG.exists()
        and SAMPLE_VALIDATION.exists() and SAMPLE_AMENDMENT.exists(),
        {
            "source_pass": str(SOURCE_PASS.relative_to(ROOT)),
            "reference": str(REFERENCE.relative_to(ROOT)),
            "sample_config": str(SAMPLE_CONFIG.relative_to(ROOT)),
            "sample_validation": str(SAMPLE_VALIDATION.relative_to(ROOT)),
            "sample_amendment": str(SAMPLE_AMENDMENT.relative_to(ROOT)),
        },
    )

    tests = junit_summary(JUNIT)
    check("full_repository_test_suite", bool(tests["present"]) and tests["failures"] == 0 and tests["errors"] == 0, tests)

    failures = [item for item in checks if item["status"] == "FAIL"]
    c14_failures = {
        item["check"] for item in failures
        if item["check"].startswith("C14_")
        or item["check"].startswith("dated_C12_")
        or item["check"].startswith("India_section")
    }
    status = {
        "WORKSTREAM_A_SEMANTIC_PREFLIGHT": "PASS" if not failures else "BLOCKED",
        "HUMAN_DECISIONS": "6/6 FROZEN",
        "C1-C6": "READY_FOR_PRODUCTION_PROMOTION" if not any(item["check"].startswith(("C1_", "C6_", "borrow_", "certified_C6", "legacy_", "India_TERM")) for item in failures) else "BLOCKED",
        "C14_EVALUATION_WINDOW": "PASS" if not c14_failures else "BLOCKED",
        "C14": (
            "READY_FOR_PRODUCTION_PROMOTION" if not c14_failures
            else "BLOCKED"
        ),
        "DATED_C12_INTEGRATION": "PASS" if not any(item["check"].startswith("dated_C12_") for item in failures) else "BLOCKED",
        "LEGACY_25BP_BORROW_FALLBACK": "ABSENT/BLOCKED" if not legacy_tokens else "PRESENT",
        "REAL_RESULTS_INSPECTED": "NO",
    }
    audit = {
        "verdict": status["WORKSTREAM_A_SEMANTIC_PREFLIGHT"],
        "status": status,
        "checks": checks,
        "failures": failures,
        "decision_config_sha256": sha256(DECISIONS),
        "certified_C6_sha256": sha256(C6),
        "production_promoted": False,
        "github_written": False,
    }
    audit_path = OUT / "WORKSTREAM_A_SEMANTIC_PREFLIGHT_2026-10-07.json"
    audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

    integration_paths = [
        DECISIONS,
        ROOT / "configs" / "base.yaml",
        ROOT / "src" / "alphacomb" / "portfolio" / "cost_terms.py",
        ROOT / "src" / "alphacomb" / "portfolio" / "optimizer.py",
        ROOT / "src" / "alphacomb" / "portfolio" / "robust.py",
        ROOT / "src" / "alphacomb" / "models" / "economic.py",
        ROOT / "src" / "alphacomb" / "models" / "cells.py",
        ROOT / "src" / "alphacomb" / "tax" / "dated.py",
        ROOT / "src" / "alphacomb" / "tax" / "backtest.py",
        ROOT / "src" / "alphacomb" / "tax" / "__init__.py",
        ROOT / "tests" / "portfolio" / "test_borrow_fee_policy.py",
        ROOT / "tests" / "c14" / "test_c14_dated_production_integration.py",
        SAMPLE_CONFIG,
        ROOT / "validate_c14_evaluation_sample.py",
        SAMPLE_VALIDATION,
        SAMPLE_AMENDMENT,
    ]
    diff_stat = subprocess.run(
        ["git", "diff", "--stat"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    manifest = {
        "verdict": "READY_FOR_EXPLICIT_PROMOTION" if not failures else "BLOCKED_BEFORE_PROMOTION",
        "semantic_preflight": str(audit_path.relative_to(ROOT)),
        "integration_files": [
            {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in integration_paths
        ],
        "candidate_inputs": [
            {"path": str(C6.relative_to(ROOT)), "sha256": sha256(C6)},
            {"path": str(C14.relative_to(ROOT)), "sha256": sha256(C14)},
        ],
        "tracked_diff_stat": diff_stat,
        "production_promoted": False,
        "github_written": False,
        "real_results_inspected": False,
    }
    (OUT / "FINAL_PRODUCTION_PROMOTION_MANIFEST_2026-10-07.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": status, "failure_count": len(failures), "failures": [x["check"] for x in failures]}, indent=2))


if __name__ == "__main__":
    main()
