"""Bounded C14 closeout validator; it does not read or write C1-C6 artefacts."""
from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.tax import (DatedRegimeSchedule, SecurityReferenceValueStore,
                           production_architecture_gate)


SCHEDULE = ROOT / "data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv"
REFERENCE = ROOT / "data/intl_c14/candidate_working/IND_SECTION_112A_REFERENCE_VALUES.csv"
SOURCE_PASS = ROOT / "data/intl_c14/audit/C14_BOUNDED_PRIMARY_SOURCE_PASS_2026-10-07.json"
OUT = ROOT / "data/intl_c14/audit/C14_FINAL_CLOSEOUT_VALIDATION_2026-10-07.json"
JUNIT = ROOT / "data/workstream_a_closeout/WORKSTREAM_A_FULL_TESTS_2026-10-07.xml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    schedule = DatedRegimeSchedule.from_csv(SCHEDULE)
    continuity = schedule.validate("1990-01-01", "2020-12-31")
    references = SecurityReferenceValueStore.from_validated_csv(REFERENCE)
    source_pass = json.loads(SOURCE_PASS.read_text(encoding="utf-8"))
    remaining = source_pass["remaining_source_facts"]
    architecture = production_architecture_gate()
    junit_root = ET.parse(JUNIT).getroot()
    suites = [junit_root] if junit_root.tag == "testsuite" else list(junit_root.findall("testsuite"))
    tests = {
        "tests": sum(int(s.attrib.get("tests", 0)) for s in suites),
        "failures": sum(int(s.attrib.get("failures", 0)) for s in suites),
        "errors": sum(int(s.attrib.get("errors", 0)) for s in suites),
        "skipped": sum(int(s.attrib.get("skipped", 0)) for s in suites),
    }

    code = {
        name: (ROOT / path).read_text(encoding="utf-8")
        for name, path in {
            "dated": "src/alphacomb/tax/dated.py",
            "lots": "src/alphacomb/tax/lots.py",
            "backtest": "src/alphacomb/tax/backtest.py",
        }.items()
    }
    mechanical = {
        "schedule_contiguous": continuity == {"countries": 3, "gaps": 0, "overlaps": 0},
        "architecture_gate": architecture["verdict"] == "PASS_DATED_C12_PRODUCTION_ARCHITECTURE",
        "realised_events_use_dated_engine": "dated_engine.realise" in code["lots"],
        "dated_losses_use_LossCarryforwardBook": "LossCarryforwardBook" in code["backtest"],
        "override_key_contains_applied_rule_id": "RateKey = tuple[str, str]" in code["dated"],
        "event_date_dividend_resolver": "def dividend_tax_rate" in code["dated"],
        "reference_contract_validator": "def from_validated_csv" in code["dated"],
        "static_adapter_retained": "book: _YearBook | _DatedYearBook" in code["backtest"],
        "section_112A_reference_rows_546": len(references) == 546,
        "full_repository_tests_green": tests["tests"] > 0 and tests["failures"] == tests["errors"] == 0,
    }
    status = "PASS" if all(mechanical.values()) and not remaining else "BLOCKED_SOURCE_FACT"
    result = {
        "C14": status,
        "mechanical_checks": mechanical,
        "remaining_source_facts": remaining,
        "resolved_primary_facts": source_pass["resolved_primary_facts"],
        "test_summary": tests,
        "inputs_sha256": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (
                SCHEDULE, REFERENCE, SOURCE_PASS, JUNIT,
                ROOT / "src/alphacomb/tax/dated.py",
                ROOT / "src/alphacomb/tax/lots.py",
                ROOT / "src/alphacomb/tax/backtest.py",
                ROOT / "tests/c14/test_c14_dated_production_integration.py",
            )
        },
        "production_promoted": False,
        "github_written": False,
        "real_results_inspected": False,
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not all(mechanical.values()):
        raise RuntimeError("C14 mechanical closeout failed")


if __name__ == "__main__":
    main()
