#!/usr/bin/env python
"""Install a single promoted data file from the browser's download folder, verifying its hash.

Drive's folder-ZIP download fails above roughly 90 MB for this shared tree, so the C1/C2/C4
parquet files have to be fetched one at a time. This script closes the loop: it matches whatever
landed in Downloads against the promotion manifest **by content hash**, puts it at the manifest's
own path, and refuses anything it cannot identify.

Matching on the hash rather than the filename matters here. Three countries each have a
``universe.parquet`` and a ``targets.parquet``; a download named ``universe (1).parquet`` carries
no reliable indication of which country it came from. The hash does.

    python tools/install_promoted_file.py universe.parquet
    python tools/install_promoted_file.py --all        # sweep the download folder
    python tools/install_promoted_file.py --status     # what is still missing
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT.parent / "absar sent work" / "WORKSTREAM_A_POST_PROMOTION_MANIFEST_2026-10-07.json"
DOWNLOADS = Path(os.path.expanduser("~")) / "Downloads"
CHUNK = 1 << 20


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def expected() -> dict[str, tuple[str, int]]:
    """sha256 -> (manifest path, bytes) for every promoted data file."""
    blob = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = {e["sha256"]: (e["path"], e["bytes"]) for e in blob["unchanged_C1_C5"]}
    for op in blob.get("operations", []):
        d = op["destination"]
        out[d["sha256"]] = (d["path"], d["bytes"])
    return out


def install(src: Path, table: dict[str, tuple[str, int]], keep: bool = False) -> bool:
    if not src.exists():
        print(f"  {src.name}: not found")
        return False
    digest = sha256_of(src)
    if digest not in table:
        print(f"  {src.name}: {src.stat().st_size:,} bytes, hash not in the promotion manifest "
              f"- left in place rather than guessing where it belongs")
        return False
    rel, size = table[digest]
    dest = ROOT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    assert dest.stat().st_size == size, f"{rel} wrote {dest.stat().st_size} bytes, expected {size}"
    print(f"  VERIFIED {rel}  ({size:,} bytes)")
    if not keep:
        src.unlink()
    return True


def status(table: dict[str, tuple[str, int]]) -> int:
    present = missing = 0
    missing_paths = []
    for digest, (rel, size) in sorted(table.items(), key=lambda kv: kv[1][0]):
        path = ROOT / rel
        if path.exists() and sha256_of(path) == digest:
            present += 1
        else:
            missing += 1
            missing_paths.append((rel, size))
    print(f"promoted data files: {present} verified, {missing} outstanding")
    for rel, size in missing_paths:
        print(f"  MISSING {rel}  ({size / 1e6:.1f} MB)")
    return 0 if missing == 0 else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("names", nargs="*", help="file names inside the Downloads folder")
    ap.add_argument("--all", action="store_true", help="sweep every parquet/csv/gz in Downloads")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--keep", action="store_true", help="do not delete the source after installing")
    args = ap.parse_args(argv)

    if not MANIFEST.exists():
        print(f"promotion manifest not found at {MANIFEST}")
        return 2
    table = expected()

    if args.status:
        return status(table)

    targets: list[Path] = [DOWNLOADS / n for n in args.names]
    if args.all:
        for pattern in ("*.parquet", "*.csv", "*.csv.gz"):
            targets.extend(sorted(DOWNLOADS.glob(pattern)))
    if not targets:
        print("nothing to install; pass file names or --all")
        return 2

    installed = 0
    for src in dict.fromkeys(targets):  # de-duplicate, keep order
        installed += int(install(src, table, keep=args.keep))
    print(f"\n{installed} file(s) installed and verified")
    return 0 if installed else 1


if __name__ == "__main__":
    raise SystemExit(main())
