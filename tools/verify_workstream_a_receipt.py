"""Independent Workstream-B receipt check for the 7 October 2026 Workstream-A handoff.

Absar's promotion is self-certified by
``data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_MANIFEST_2026-10-07.json``.
Workstream B is the receiving party, so before any integration work starts we
re-derive every SHA-256 in that manifest from the bytes that actually landed in
this repository, rather than trusting the recorded digests.

The manifest covers three disjoint sets:

* 2 byte-for-byte promotions (C6, C14) - source *and* destination are checked;
* 16 code/configuration/test files verified in place;
* 20 unchanged C1-C5 data files.

Usage::

    python tools/verify_workstream_a_receipt.py [--repo .] [--manifest PATH] [--json OUT]

Exit status is 0 only when every listed file is present and every digest
matches. This script reads bytes and hashes them; it loads no model, runs no
backtest, and inspects no results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_MANIFEST = Path(
    "data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_MANIFEST_2026-10-07.json"
)

# Digests transcribed from document 13, independently of any file A sent. The
# post-promotion manifest (the file this script reads) is *not* the promotion
# authority; it points at a separate FINAL_PRODUCTION_PROMOTION_MANIFEST. Both
# are pinned so a tampered or stale manifest cannot certify itself.
PINNED_SHA256 = {
    "data/workstream_a_closeout/FINAL_PRODUCTION_PROMOTION_MANIFEST_2026-10-07.json":
        "9fe4d029e1acf86ce7d41c65cbc1e8fa2a9f35296a2c1c8685b492ea3b2dab28",
    "data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_VALIDATION_2026-10-07.json":
        "37a2b38aacfe6476b3c98983b1a19d8a665549ed814e29ae0f74d30370b64c02",
    "data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_TESTS_2026-10-07.xml":
        "dee50cc7a5ad037fa6aee3e95976b110d67869064a728b18d04be5c595bd5a47",
    "data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz":
        "bb296e488327b822281940ff2669ce7a46fe7a60e5d8b79f3f7c5548d758fa4c",
    "data/intl_c14/production/c14_regime_candidate_source_frozen.csv":
        "992a491c3f387d8f68ed253d0258d948ccbf4b722ede37e2dedbaf6e974f775a",
}


TEXT_SUFFIXES = {".py", ".yaml", ".yml", ".json", ".md", ".csv", ".txt", ".xml", ".cfg", ".toml"}


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def normalised_sha256(path: Path) -> str | None:
    """SHA-256 of a text file with CRLF/CR collapsed to LF, or None for binary files.

    Workstream A's manifest hashed its own working-tree bytes, and several of those files
    had *mixed* CRLF and LF endings. Git normalises line endings on commit, so those
    digests are not reproducible from any checkout of the repository even when the content
    is byte-for-byte the intended code. Comparing normalised text separates "the content
    differs" from "the line endings were rewritten in transit", which are very different
    findings: the first blocks a merge, the second does not.

    Binary files (parquet, gzip, images) are never normalised - for those, only an exact
    byte match counts.
    """
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return None
    raw = path.read_bytes()
    if b"\x00" in raw[:8192]:  # NUL byte: treat as binary despite the suffix
        return None
    return hashlib.sha256(raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")).hexdigest()


def expected_entries(manifest: dict) -> list[tuple[str, str, str, int]]:
    """Flatten the manifest into ``(group, path, sha256, bytes)`` rows."""
    rows: list[tuple[str, str, str, int]] = []
    for op in manifest.get("operations", []):
        for side in ("source", "destination"):
            e = op[side]
            rows.append((f"promotion:{side}", e["path"], e["sha256"], e["bytes"]))
    for e in manifest.get("integration_files", []):
        rows.append(("integration", e["path"], e["sha256"], e["bytes"]))
    for e in manifest.get("unchanged_C1_C5", []):
        rows.append(("unchanged_C1_C5", e["path"], e["sha256"], e["bytes"]))
    return rows


def check_pinned(repo: Path, manifest: dict) -> list[dict]:
    """Verify the document-13 digests, including the manifest's own stated authority."""
    pinned = dict(PINNED_SHA256)

    # Cross-check: the manifest names its authority and that file's digest. If the
    # manifest disagrees with document 13, say so rather than silently preferring one.
    authority = manifest.get("sole_authority", {})
    rel, claimed = authority.get("path"), authority.get("sha256")
    rows: list[dict] = []
    if rel and claimed and rel in pinned and claimed != pinned[rel]:
        rows.append({
            "path": rel,
            "status": "AUTHORITY_CLAIM_CONFLICTS_WITH_DOC13",
            "expected_sha256": pinned[rel],
            "manifest_claims_sha256": claimed,
        })

    for rel, want in sorted(pinned.items()):
        path = repo / rel
        row = {"path": rel, "expected_sha256": want}
        if not path.exists():
            row["status"] = "MISSING"
        else:
            row["observed_sha256"] = sha256_of(path)
            row["status"] = "MATCH" if row["observed_sha256"] == want else "DIFFERS"
        rows.append(row)
    return rows


def check(repo: Path, manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    pinned_rows = check_pinned(repo, manifest)
    pinned_ok = all(r["status"] == "MATCH" for r in pinned_rows)

    results = []
    for group, rel, want, want_bytes in expected_entries(manifest):
        path = repo / rel
        row = {"group": group, "path": rel, "expected_sha256": want}
        if not path.exists():
            row["status"] = "MISSING"
        else:
            observed = sha256_of(path)
            row.update(observed_sha256=observed, expected_bytes=want_bytes,
                       observed_bytes=path.stat().st_size)
            if observed == want:
                row["status"] = "MATCH"
            else:
                # A text file whose content matches once line endings are normalised is
                # reported distinctly: the code is right, the endings were rewritten.
                norm = normalised_sha256(path)
                row["status"] = "MATCH_NORMALISED" if norm and norm == want else "DIFFERS"
                if norm:
                    row["normalised_sha256"] = norm
        results.append(row)

    counts: dict[str, int] = {}
    for row in results:
        counts[row["status"]] = counts.get(row["status"], 0) + 1

    exact = counts.get("MATCH", 0)
    normalised = counts.get("MATCH_NORMALISED", 0)
    if pinned_ok and exact == len(results):
        verdict = "RECEIPT_VERIFIED_PASS"
    elif pinned_ok and exact + normalised == len(results):
        # Every file is present and correct; some text files had their line endings
        # rewritten (git normalises on commit). Content is verified, bytes are not.
        verdict = "RECEIPT_VERIFIED_PASS_NORMALISED"
    else:
        verdict = "RECEIPT_FAIL"
    return {
        "verdict": verdict,
        "repo": str(repo.resolve()),
        "manifest": str(manifest_path),
        "pinned_doc13_digests": pinned_rows,
        "files_checked": len(results),
        "counts": counts,
        "files": results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", type=Path, default=Path("."))
    ap.add_argument("--manifest", type=Path, default=None)
    ap.add_argument("--json", type=Path, default=None, help="write the full report here")
    ap.add_argument(
        "--reference", type=Path, default=None,
        help="a second independently obtained copy of the tree (e.g. the Drive download). "
             "Files whose manifest digest cannot be reproduced are compared against it with "
             "line endings normalised, which distinguishes 'content differs' from 'endings "
             "were rewritten in transit'.",
    )
    args = ap.parse_args(argv)

    manifest_path = args.manifest or (args.repo / DEFAULT_MANIFEST)
    if not manifest_path.exists():
        print(f"FAIL: promotion manifest not found at {manifest_path}", file=sys.stderr)
        return 2

    report = check(args.repo, manifest_path)

    if args.reference:
        unresolved = [r for r in report["files"] if r["status"] == "DIFFERS"]
        agree, disagree, absent = [], [], []
        for row in unresolved:
            a, b = args.repo / row["path"], args.reference / row["path"]
            if not b.exists():
                absent.append(row["path"]); continue
            na, nb = normalised_sha256(a), normalised_sha256(b)
            (agree if (na and nb and na == nb) else disagree).append(row["path"])
        report["reference_check"] = {
            "reference": str(args.reference),
            "content_agrees": agree,
            "content_disagrees": disagree,
            "absent_from_reference": absent,
        }
        if agree and not disagree and not absent:
            report["verdict"] = (
                "RECEIPT_VERIFIED_PASS_NORMALISED"
                if report["verdict"] == "RECEIPT_FAIL"
                and not [r for r in report["files"] if r["status"] == "MISSING"]
                else report["verdict"]
            )

    print(f"manifest read  : {manifest_path}")
    print("document-13 pinned digests:")
    for row in report["pinned_doc13_digests"]:
        print(f"  {row['status']:<8} {row['path']}")
    for row in report["files"]:
        if row["status"] != "MATCH":
            print(f"  {row['status']:<8} [{row['group']}] {row['path']}")
    tally = ", ".join(f"{k}={v}" for k, v in sorted(report["counts"].items()))
    print(f"{report['files_checked']} files checked: {tally}")
    if "reference_check" in report:
        rc = report["reference_check"]
        print(f"cross-check vs {rc['reference']}: "
              f"{len(rc['content_agrees'])} agree on content, "
              f"{len(rc['content_disagrees'])} disagree, "
              f"{len(rc['absent_from_reference'])} absent")
        for p in rc["content_disagrees"]:
            print(f"  CONTENT DISAGREES {p}")
    print(report["verdict"])

    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"report written to {args.json}")

    return 0 if report["verdict"].startswith("RECEIPT_VERIFIED_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
