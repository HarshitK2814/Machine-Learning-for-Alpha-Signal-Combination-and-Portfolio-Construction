#!/usr/bin/env python
"""Recover the configuration and weight identity of the original multi-regime after-tax runs (pipelines/06).

Configuration fields only. From each ``outputs/summary_after_tax*.csv`` ONLY these columns are read:
strategy, country, regime, lot_method, months, dated, wedge (``usecols``); no Sharpe, drag, NAV or any outcome column.
Weight files are hashed (bytes) and located by file name; their contents are not opened.

    python tools/phase_c_recover_after_tax_config.py --out results/phase_c_after_tax_config_recovery_2026-10-14
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONFIG_COLUMNS = ["strategy", "country", "regime", "lot_method", "months", "dated", "wedge"]
SUMMARY_TO_ARM = {   # summary file -> (country, aum label, whether the recorded command pinned the weights with --weights-aum)
    "summary_after_tax_DEU_1e9.csv": ("DEU", "1e9"), "summary_after_tax_IND_1e9.csv": ("IND", "1e9"),
    "summary_after_tax_JPN_1e9.csv": ("JPN", "1e9"), "summary_after_tax_DEU_1e8.csv": ("DEU", "1e8"),
    "summary_after_tax_DEU_1e10.csv": ("DEU", "1e10"), "summary_after_tax_JPN_1e8.csv": ("JPN", "1e8"),
    "summary_after_tax_JPN_1e10.csv": ("JPN", "1e10"),
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def stamp(p: Path) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime))


def latest_by_mtime(name: str) -> str | None:
    d = ROOT / "outputs" / "weights" / name
    files = sorted(d.glob("*.parquet"), key=lambda p: p.stat().st_mtime) if d.exists() else []
    return files[-1].stem if files else None


def run_time(stem: str) -> str:
    """pf_<strategy>_<YYYYMMDD>_<HHMMSS>_<hash> -> 'YYYY-MM-DD HH:MM:SS' (local time of the stage-04 run)."""
    parts = stem.split("_")
    d, t = parts[-3], parts[-2]
    return f"{d[:4]}-{d[4:6]}-{d[6:]} {t[:2]}:{t[2:4]}:{t[4:]}"


def runs_between(name: str, indexed_run: str, upper: str) -> int:
    """Other stage-04 runs of the same strategy created after the indexed run and no later than ``upper``."""
    d = ROOT / "outputs" / "weights" / name
    lo = run_time(indexed_run)
    return sum(1 for p in d.glob("*.parquet") if p.stem != indexed_run and lo < run_time(p.stem) <= upper) if d.exists() else -1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out) if Path(a.out).is_absolute() else ROOT / a.out
    if out.exists():
        sys.exit(f"refusing to overwrite existing {out}")
    out.mkdir(parents=True)
    arms, ident = [], []
    for fname, (ctry, aum) in SUMMARY_TO_ARM.items():
        sp = ROOT / "outputs" / fname
        d = pd.read_csv(sp, usecols=lambda c: c in CONFIG_COLUMNS)
        ip = ROOT / "outputs" / "weights_index" / f"{ctry}_{aum}.csv"
        idx = pd.read_csv(ip)
        arms.append({
            "summary_file": fname, "country": ctry, "aum_label": aum, "summary_mtime": stamp(sp),
            "summary_sha256": sha(sp), "n_rows": len(d), "n_strategies": d["strategy"].nunique(),
            "regimes": "|".join(sorted(d["regime"].unique())), "lot_methods": "|".join(sorted(d["lot_method"].unique())),
            "months": "|".join(str(m) for m in sorted(d["months"].unique())),
            "dated_column": "|".join(sorted(d["dated"].astype(str).unique())) if "dated" in d else "absent (older code)",
            "weights_index": str(ip.relative_to(ROOT)), "weights_index_mtime": stamp(ip), "weights_index_sha256": sha(ip),
            "index_written_before_summary": stamp(ip) < stamp(sp)})
        snap = ROOT / "docs" / "attachments" / f"SUMMARY_AFTER_TAX_{ctry}_{aum.upper()}_2026-10-09.csv"
        arms[-1]["tracked_snapshot"] = str(snap.relative_to(ROOT)) if snap.exists() else "none"
        arms[-1]["snapshot_sha256_equals_live_file"] = (sha(snap) == arms[-1]["summary_sha256"]) if snap.exists() else ""
        cells = set(d["strategy"])
        for _, r in idx[idx["strategy"].isin(cells)].iterrows():
            wp = ROOT / r["weights"]
            ident.append({
                "country": ctry, "aum_label": aum, "strategy": r["strategy"], "indexed_run_id": r["run_id"],
                "weights_file": str(Path(r["weights"])), "exists": wp.exists(),
                "weights_sha256": sha(wp) if wp.exists() else "", "weights_mtime": stamp(wp) if wp.exists() else "",
                "latest_run_by_mtime_today": latest_by_mtime(r["strategy"]),
                "index_equals_latest_by_mtime_today": latest_by_mtime(r["strategy"]) == r["run_id"],
                "indexed_run_created": run_time(r["run_id"]), "summary_mtime": stamp(sp),
                "indexed_run_predates_summary": run_time(r["run_id"]) <= stamp(sp),
                "other_runs_of_strategy_between_indexed_run_and_summary": runs_between(r["strategy"], r["run_id"], stamp(sp))})
    pd.DataFrame(arms).to_csv(out / "after_tax_arms.csv", index=False)
    pd.DataFrame(ident).to_csv(out / "after_tax_weight_identity.csv", index=False)
    (out / "MANIFEST.json").write_text(json.dumps({
        "label": "CONFIGURATION RECOVERY - no outcome value read; revised analysis, not confirmatory",
        "columns_read_from_summaries": CONFIG_COLUMNS,
        "weights": "hashed as bytes; contents not opened",
        "note": "weight hashes describe the files as they are now, not necessarily as at run time"}, indent=2))
    print("done", out)


if __name__ == "__main__":
    main()
