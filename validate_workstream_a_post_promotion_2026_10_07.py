"""Fail-closed validation of the manifest-authorized Workstream-A promotion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from alphacomb.contracts import validate


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_VALIDATION_2026-10-07.json"
AUTHORITY = ROOT / "data/workstream_a_closeout/FINAL_PRODUCTION_PROMOTION_MANIFEST_2026-10-07.json"
BASELINE = ROOT / "data/workstream_a_closeout/WORKSTREAM_A_PRE_PROMOTION_BASELINE_2026-10-07.json"
POST_MANIFEST = ROOT / "data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_MANIFEST_2026-10-07.json"
DECISIONS = ROOT / "configs/workstream_a_frozen_decisions.json"
SAMPLE = ROOT / "configs/workstream_a_c14_evaluation_sample_2026-10-07.json"
SOURCE_LEDGER = ROOT / "data/intl_c14/audit/C14_BOUNDED_PRIMARY_SOURCE_PASS_2026-10-07.json"
COUNTRIES = ("DEU", "IND", "JPN")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_parquet(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    if "date" in frame:
        frame["date"] = pd.to_datetime(frame["date"])
    return frame


def exact_keys(left: pd.DataFrame, right: pd.DataFrame, keys: list[str]) -> bool:
    merged = left[keys].merge(right[keys], on=keys, how="outer", indicator=True, validate="one_to_one")
    return len(left) == len(right) and bool(merged["_merge"].eq("both").all())


def main() -> None:
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object = None) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    post = json.loads(POST_MANIFEST.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    check(
        "sole_promotion_authority_identity",
        post["sole_authority"]["sha256"] == sha256(AUTHORITY)
        and authority["verdict"] == "READY_FOR_EXPLICIT_PROMOTION",
        post["sole_authority"],
    )

    listed_ok = True
    listed_detail: list[dict[str, object]] = []
    for item in authority["integration_files"] + authority["candidate_inputs"]:
        path = ROOT / item["path"]
        actual = sha256(path) if path.is_file() else None
        ok = actual == item["sha256"] and (
            "bytes" not in item or (path.is_file() and path.stat().st_size == item["bytes"])
        )
        listed_ok &= ok
        listed_detail.append({"path": item["path"], "expected": item["sha256"], "actual": actual})
    check("all_authorized_source_and_integration_hashes", listed_ok, listed_detail)

    promoted_ok = True
    for operation in post["operations"]:
        source = ROOT / operation["source"]["path"]
        destination = ROOT / operation["destination"]["path"]
        promoted_ok &= (
            source.is_file() and destination.is_file()
            and sha256(source) == operation["source"]["sha256"]
            and sha256(destination) == operation["destination"]["sha256"]
            and sha256(source) == sha256(destination)
            and operation["transformation"] == "NONE"
        )
    check("promoted_files_are_exact_byte_copies", promoted_ok, post["operations"])

    unchanged_ok = True
    unchanged_detail: list[dict[str, object]] = []
    for item in baseline["files"]:
        path = ROOT / item["path"]
        ok = bool(path.is_file() and sha256(path) == item["sha256"] and path.stat().st_size == item["bytes"])
        unchanged_ok &= ok
        unchanged_detail.append({"path": item["path"], "unchanged": ok})
    check("C1_C5_unchanged_from_pre_promotion_baseline", unchanged_ok, unchanged_detail)

    contract_results: dict[str, object] = {}
    spines: dict[str, object] = {}
    for country in COUNTRIES:
        c1 = read_parquet(ROOT / f"data/intl_c1/production/{country}/universe.parquet")
        c2 = read_parquet(ROOT / f"data/intl_c2/production/{country}/signals.parquet")
        c4 = read_parquet(ROOT / f"data/intl_c4/production/{country}/targets.parquet")
        c5 = read_parquet(ROOT / f"data/intl_c5/candidate_final_working/{country}/states.parquet")
        validate(c1, "universe")
        validate(c2, "signals")
        validate(c4, "targets")
        validate(c5, "states")
        contract_results[country] = {"C1": len(c1), "C2": len(c2), "C4": len(c4), "C5": len(c5)}
        spines[country] = {
            "C2_exact_C1": exact_keys(c1, c2, ["date", "permno"]),
            "C4_exact_C1": exact_keys(c1, c4, ["date", "permno"]),
        }
    c3 = pd.read_csv(ROOT / "data/intl_c2/production/signal_meta.csv")
    validate(c3, "signal_meta")
    check("frozen_C1_C5_contract_validators", True, {**contract_results, "C3": len(c3)})
    check("C2_C4_exact_C1_spines", all(all(item.values()) for item in spines.values()), spines)

    c6_path = ROOT / "data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz"
    c6 = pd.read_csv(c6_path, low_memory=False)
    c6["date"] = pd.to_datetime(c6["date"])
    required = {"country", "date", "permno", "spread", "sigma_d", "adv_usd", "borrow_fee", "spread_source"}
    nonnegative = all((c6[column].dropna() >= 0).all() for column in ("spread", "sigma_d", "adv_usd"))
    c6_ok = (
        required.issubset(c6.columns)
        and not c6.duplicated(["date", "permno"]).any()
        and c6["date"].eq(c6["date"] + pd.offsets.MonthEnd(0)).all()
        and nonnegative
        and c6["borrow_fee"].isna().all()
        and c6.loc[c6["spread_source"].eq("MISSING"), "spread"].isna().all()
    )
    check(
        "C6_certified_fail_closed_contract",
        c6_ok,
        {
            "rows": len(c6),
            "unique_keys": int(c6.drop_duplicates(["date", "permno"]).shape[0]),
            "borrow_fee_nonnull": int(c6["borrow_fee"].notna().sum()),
            "spread_missing": int(c6["spread"].isna().sum()),
            "note": "Frozen C6 intentionally permits certified source gaps; the legacy strict schema is not used to impute them.",
        },
    )

    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    policy = decisions["decisions"]["missing_borrow_fee_treatment"]
    consumer_text = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "src/alphacomb/portfolio/cost_terms.py",
            "src/alphacomb/portfolio/optimizer.py",
            "src/alphacomb/portfolio/robust.py",
            "src/alphacomb/models/economic.py",
            "src/alphacomb/models/cells.py",
        )
    )
    legacy_tokens = [token for token in ("fillna(0.0025)", "borrow_gc_bps_pa", "borrow_htb_bps_pa") if token in consumer_text]
    check(
        "modelled_borrow_proxy_configuration_only",
        policy["choice"] == "6B"
        and policy["model"] == "MODELLED_FLAT_BORROW_PROXY_V1"
        and policy["annual_rate"] == 0.01
        and policy["sensitivity_annual_rates"] == [0.003, 0.006, 0.043, 0.07]
        and policy["injection_layer"] == "C11_and_experiment_consumers_only"
        and c6["borrow_fee"].isna().all(),
        policy,
    )
    check("legacy_25bp_borrow_fallback_absent", not legacy_tokens, legacy_tokens)

    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    primary = sample["primary_after_tax_evaluation_window"]
    mechanism = sample["clean_mechanism_subwindow"]
    domain_ok = (
        primary == {"start": "2009-01-01", "end": "2019-12-31"}
        and mechanism["start"] == "2014-01-01"
        and mechanism["end"] == "2018-03-31"
        and sample["tax_ledger_inception"] == "2009-01-01"
        and sample["opening_tax_lots"] == "NONE_COLD_START_AT_FIRST_EVALUATION_REBALANCE"
        and sample["pre_2009_acquisition_lots_permitted"] is False
        and sample["real_results_inspected_before_amendment"] is False
    )
    check(
        "C14_frozen_consumer_domain_gate",
        domain_ok,
        {
            "primary": primary,
            "mechanism": mechanism,
            "enforcement": "Workstream-B input gate; dated resolver remains reusable outside this approved experiment",
        },
    )
    source_ledger = json.loads(SOURCE_LEDGER.read_text(encoding="utf-8"))
    blockers = source_ledger.get("remaining_source_facts", [])
    check("nine_historical_C14_regimes_retained_nonproduction", len(blockers) == 9 and domain_ok, {"count": len(blockers), "facts": blockers})

    semantic = json.loads((ROOT / authority["semantic_preflight"]).read_text(encoding="utf-8"))
    check("full_semantic_preflight_pass", semantic["verdict"] == "PASS" and semantic["failures"] == [], semantic["status"])
    check("real_results_not_inspected", post["real_results_inspected"] is False)
    check("github_not_written", post["github_written"] is False)

    failures = [item for item in checks if item["status"] == "FAIL"]
    result = {
        "verdict": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failures": failures,
        "status": {
            "WORKSTREAM_A_PRODUCTION_PROMOTION": "PASS" if not failures else "BLOCKED",
            "WORKSTREAM_A_SEMANTIC_PREFLIGHT": "PASS" if not failures else "BLOCKED",
            "C1-C6": "PROMOTED_OR_FROZEN_IN_PLACE",
            "C14_EVALUATION_DOMAIN": "2009-01-01/2019-12-31",
            "C14_MECHANISM_SUBWINDOW": "2014-01-01/2018-03-31",
            "LEGACY_25BP_BORROW_FALLBACK": "ABSENT/BLOCKED" if not legacy_tokens else "PRESENT",
            "REAL_RESULTS_INSPECTED": "NO",
            "GITHUB_WRITTEN": "NO",
        },
        "authority_manifest_sha256": sha256(AUTHORITY),
    }
    OUT.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "checks": len(checks), "failures": [x["check"] for x in failures]}, indent=2))
    if failures:
        raise RuntimeError("Workstream-A post-promotion validation failed")


if __name__ == "__main__":
    main()
