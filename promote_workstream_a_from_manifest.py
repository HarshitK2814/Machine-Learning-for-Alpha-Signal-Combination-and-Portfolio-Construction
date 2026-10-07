"""Promote exactly the Workstream-A artefacts authorized on 2026-10-07.

This utility is intentionally narrow.  It treats the frozen promotion manifest
as the sole authority, verifies every listed source before writing, copies the
two listed data candidates byte-for-byte into production namespaces, and
records a complete before/after hash ledger.  It never materializes data/real,
runs models, or writes to Git/Drive.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
AUTHORITY = ROOT / "data/workstream_a_closeout/FINAL_PRODUCTION_PROMOTION_MANIFEST_2026-10-07.json"
BASELINE = ROOT / "data/workstream_a_closeout/WORKSTREAM_A_PRE_PROMOTION_BASELINE_2026-10-07.json"
POST_MANIFEST = ROOT / "data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_MANIFEST_2026-10-07.json"

PROMOTIONS = {
    "data/intl_c6/candidate_working/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz":
        "data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz",
    "data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv":
        "data/intl_c14/production/c14_regime_candidate_source_frozen.csv",
}

UNCHANGED_ROOTS = [
    "data/intl_c1/production",
    "data/intl_c2/production",
    "data/intl_c4/production",
    "data/intl_c5/candidate_final_working",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def tree_records(relative_roots: list[str]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for relative_root in relative_roots:
        directory = ROOT / relative_root
        if not directory.is_dir():
            raise FileNotFoundError(directory)
        records.extend(record(path) for path in sorted(directory.rglob("*")) if path.is_file())
    return records


def assert_manifest_entry(entry: dict[str, object]) -> Path:
    path = ROOT / str(entry["path"])
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_hash = sha256(path)
    if actual_hash != entry["sha256"]:
        raise RuntimeError(f"Manifest hash mismatch for {path}: {actual_hash} != {entry['sha256']}")
    expected_bytes = entry.get("bytes")
    if expected_bytes is not None and path.stat().st_size != expected_bytes:
        raise RuntimeError(f"Manifest byte-size mismatch for {path}")
    return path


def main() -> None:
    authority_hash = sha256(AUTHORITY)
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if authority.get("verdict") != "READY_FOR_EXPLICIT_PROMOTION":
        raise RuntimeError("Promotion authority is not READY_FOR_EXPLICIT_PROMOTION")
    if authority.get("real_results_inspected") is not False:
        raise RuntimeError("Promotion authority does not preserve the pre-results boundary")

    integration = [assert_manifest_entry(item) for item in authority["integration_files"]]
    candidates = [assert_manifest_entry(item) for item in authority["candidate_inputs"]]
    listed_candidates = {path.relative_to(ROOT).as_posix() for path in candidates}
    if listed_candidates != set(PROMOTIONS):
        raise RuntimeError(
            "Candidate set differs from the two explicitly mapped promotion operations: "
            f"{sorted(listed_candidates)}"
        )

    unchanged_before = tree_records(UNCHANGED_ROOTS)
    baseline = {
        "authority_manifest": record(AUTHORITY),
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "C1-C5 files that the promotion authority does not authorize changing",
        "files": unchanged_before,
    }
    BASELINE.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")

    operations: list[dict[str, object]] = []
    for source_relative, destination_relative in PROMOTIONS.items():
        source = ROOT / source_relative
        destination = ROOT / destination_relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if sha256(destination) != sha256(source):
                raise RuntimeError(f"Refusing to overwrite differing production file: {destination}")
            operation = "verified_existing_identical_copy"
        else:
            shutil.copy2(source, destination)
            operation = "byte_for_byte_copy"
        if sha256(destination) != sha256(source):
            raise RuntimeError(f"Post-copy hash mismatch for {destination}")
        operations.append({
            "operation": operation,
            "source": record(source),
            "destination": record(destination),
            "transformation": "NONE",
        })

    unchanged_after = tree_records(UNCHANGED_ROOTS)
    if unchanged_before != unchanged_after:
        raise RuntimeError("An unlisted C1-C5 input changed during promotion")

    post = {
        "verdict": "PROMOTION_APPLIED_PENDING_POST_VALIDATION",
        "promoted_at_utc": datetime.now(timezone.utc).isoformat(),
        "sole_authority": {
            "path": AUTHORITY.relative_to(ROOT).as_posix(),
            "sha256": authority_hash,
        },
        "scope_resolution": {
            "new_data_promotions": 2,
            "integration_files_verified_in_place": len(integration),
            "C1_C5_action": "VERIFIED_IN_PLACE_NO_COPY_NO_TRANSFORMATION",
            "data_real_materialized": False,
        },
        "operations": operations,
        "integration_files": [record(path) for path in integration],
        "unchanged_C1_C5": unchanged_after,
        "drive_reconciliation": {
            "project_folder_id": "1XHmzhzKpOnqMFLGPG1MF-Zyr6L7_0Hrr",
            "observed_snapshot_date": "2026-10-02",
            "exact_current_authority_manifest_found": False,
            "exact_current_C6_or_C14_candidate_found": False,
            "resolution": "CURRENT_LOCAL_MANIFEST_LISTED_FILES_ARE_AUTHORITATIVE; DRIVE_LEFT_UNCHANGED",
        },
        "production_promoted": True,
        "github_written": False,
        "real_results_inspected": False,
    }
    POST_MANIFEST.write_text(json.dumps(post, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": post["verdict"],
        "authority_sha256": authority_hash,
        "promotion_operations": len(operations),
        "integration_files_verified": len(integration),
        "unchanged_C1_C5_files": len(unchanged_after),
    }, indent=2))


if __name__ == "__main__":
    main()
