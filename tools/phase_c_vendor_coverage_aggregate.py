#!/usr/bin/env python
"""Phase C vendor-coverage feasibility: aggregate counts only (no price, return, dividend, factor, FX, cost, tax value).

Inputs: committed audit ``C1_WRDS_ALL_SECURITY_DAILY_COVERAGE.csv`` (one row per C1 security; only count and date
columns are loaded) and the C4 gap population as presence flags (same definition as the earlier presence check).
Security identifiers are used only as in-memory join keys and are never written. Output is country-level counts.

    python tools/phase_c_vendor_coverage_aggregate.py --out results/phase_c_vendor_coverage_2026-10-14
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = ["DEU", "IND", "JPN"]
WINDOW = (pd.Period("2009-01", "M").ordinal, pd.Period("2019-12", "M").ordinal)
COUNT_COLS = ["country", "permno", "daily_rows", "actual_price_status_rows", "carry_forward_status_rows",
              "first_daily_date", "last_daily_date"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def gap_runs_keyed(ret_ok: pd.DataFrame, lo: int, hi: int) -> pd.DataFrame:
    """ret_ok: columns mi, permno, ret_ok (bool). One row per gap run: permno, start, end, recovers (in memory only)."""
    rows = []
    for p, g in ret_ok.sort_values(["permno", "mi"]).groupby("permno", sort=False):
        mi, ok = g["mi"].to_numpy(), g["ret_ok"].to_numpy()
        n, i = len(g), 0
        while i < n:
            if ok[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and (not ok[j + 1]) and mi[j + 1] == mi[j] + 1:
                j += 1
            if lo <= mi[i] <= hi:
                rows.append((p, int(mi[i]), int(mi[j]), bool(j + 1 < n and mi[j + 1] == mi[j] + 1 and ok[j + 1])))
            i = j + 1
    return pd.DataFrame(rows, columns=["permno", "start", "end", "recovers"])


def summarise(runs: pd.DataFrame, cov: pd.DataFrame) -> dict:
    """Country-level counts. Security-level vendor counts span the whole queried interval, not the gap months."""
    cov = cov.copy()
    cov["permno"] = cov["permno"].astype("int64")
    # Period ordinal = (year - 1970) * 12 + (month - 1)
    for k, col in (("first_m", "first_daily_date"), ("last_m", "last_daily_date")):
        d = pd.to_datetime(cov[col], errors="coerce")
        cov[k] = ((d.dt.year - 1970) * 12 + d.dt.month - 1).fillna(-1).astype("int64")
    cov["other_status_rows"] = cov["daily_rows"] - cov["actual_price_status_rows"] - cov["carry_forward_status_rows"]
    m = runs.merge(cov[["permno", "daily_rows", "actual_price_status_rows", "carry_forward_status_rows",
                        "first_m", "last_m"]], how="left", on="permno")
    has = m["daily_rows"].fillna(0) > 0
    span = has & (m["first_m"] <= m["start"]) & (m["last_m"] >= m["end"])
    secs = m.drop_duplicates("permno")
    return {
        "gap_runs": int(len(m)), "gap_months": int((m["end"] - m["start"] + 1).sum()),
        "gap_securities": int(len(secs)),
        "gap_securities_with_any_vendor_daily": int((secs["daily_rows"].fillna(0) > 0).sum()),
        "gap_securities_with_any_carry_forward_rows": int((secs["carry_forward_status_rows"].fillna(0) > 0).sum()),
        "gap_runs_vendor_date_range_spans_run": int(span.sum()),
        "gap_runs_not_in_vendor_file_or_no_daily": int((~has).sum()),
        "vendor_rows_in_all_securities": int(cov["daily_rows"].sum()),
        "vendor_actual_status_rows_all_securities": int(cov["actual_price_status_rows"].sum()),
        "vendor_carry_forward_status_rows_all_securities": int(cov["carry_forward_status_rows"].sum()),
        "vendor_other_status_rows_all_securities": int(cov["other_status_rows"].sum()),
        "month_level_status_for_gap_months": "unknown (security-level counts only; no month-level status on disk)"}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out) if Path(a.out).is_absolute() else ROOT / a.out
    if out.exists():
        sys.exit(f"refusing to overwrite existing {out}")
    out.mkdir(parents=True)
    cp = ROOT / "data/intl_c6/audit/C1_WRDS_ALL_SECURITY_DAILY_COVERAGE.csv"
    cov_all = pd.read_csv(cp, usecols=COUNT_COLS)
    res, inputs = {}, {str(cp.relative_to(ROOT)): sha(cp)}
    for c in COUNTRIES:
        p4 = ROOT / f"data/intl_c4/production/{c}/targets.parquet"
        inputs[str(p4.relative_to(ROOT))] = sha(p4)
        t = pq.read_table(p4, columns=["date", "permno", "ret_next"]).to_pandas()
        flags = pd.DataFrame({"mi": pd.PeriodIndex(pd.to_datetime(t["date"]).dt.to_period("M")).asi8,
                              "permno": t["permno"].to_numpy(), "ret_ok": np.isfinite(t["ret_next"].to_numpy(dtype=float))})
        del t
        res[c] = summarise(gap_runs_keyed(flags, *WINDOW), cov_all[cov_all["country"] == c])
    (out / "vendor_coverage_aggregate.json").write_text(json.dumps(res, indent=2))
    (out / "MANIFEST.json").write_text(json.dumps({
        "label": "OUTCOME-FREE AGGREGATE COVERAGE COUNTS - not a result",
        "fields": {"vendor_audit_csv": [c for c in COUNT_COLS if c != "permno"] + ["permno (join key, not written)"],
                   "C4": ["date", "permno", "ret_next (isfinite flag only)"]},
        "window": ["2009-01", "2019-12"], "input_sha256": inputs,
        "limit": "vendor counts are per security over the queried interval; no month-level status is available"}, indent=2))
    print("done", out)


if __name__ == "__main__":
    main()
