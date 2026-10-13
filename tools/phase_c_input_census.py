#!/usr/bin/env python
"""Phase C outcome-free input census (docs/PHASE_C_REVISED_ANALYSIS_SPEC_2026-10-14.md + addendum 1).

Reads IDENTIFIERS AND MEMBERSHIP ONLY. Columns accessed (nothing else is ever loaded):
  C1 universe   : date, permno, in_universe
  C4 targets    : date, permno                      (row presence only; ret_next/div_next are NOT read)
  C6 cost inputs: country, date, permno             (row presence only; no cost value is read)
  weights files : date, permno, w                   (w only as the held / not-held test ``w != 0``)
  weights_index : country, aum, strategy, weights   (paths)
No return, price, dividend, cost, tax, NAV or performance value is read. A missing row is NOT treated as a
delisting: "panel exit" below means only "present at month t, absent at month t+1".

    python tools/phase_c_input_census.py --out results/phase_c_census_2026-10-14
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
WINDOW = (pd.Timestamp("2009-01-01"), pd.Timestamp("2019-12-31"))      # AMENDMENT_001A section 2
COUNTRIES = ["DEU", "IND", "JPN"]
# weights_index files that correspond one-to-one (by file name) to outputs/summary_after_tax_<country>_<aum>.csv
INDEX_FILES = ["DEU_1e8", "DEU_1e9", "DEU_1e10", "IND_1e9", "JPN_1e8", "JPN_1e9", "JPN_1e10"]
ACCESSED = {
    "C1 universe": ["date", "permno", "in_universe"],
    "C4 targets": ["date", "permno"],
    "C6 cost inputs": ["country", "date", "permno"],
    "weights": ["date", "permno", "w"],
    "weights_index": ["country", "aum", "strategy", "weights"],
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def month_key(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s).dt.to_period("M")


def membership_flows(panel: pd.DataFrame) -> pd.DataFrame:
    """panel: columns month (Period), permno. Per month: n, entries, exits, permanent exits, temporary gaps."""
    months = sorted(panel["month"].unique())
    nxt = {m: months[i + 1] for i, m in enumerate(months[:-1])}
    sets = {m: set(g["permno"]) for m, g in panel.groupby("month")}
    last_seen = panel.groupby("permno")["month"].max()
    rows = []
    for i, m in enumerate(months):
        cur = sets[m]
        prev = sets[months[i - 1]] if i else set()
        entries = len(cur - prev) if i else np.nan
        if m in nxt:
            gone = cur - sets[nxt[m]]
            perm = sum(1 for p in gone if last_seen[p] == m)
            exits, permanent, gap = len(gone), perm, len(gone) - perm
        else:
            exits = permanent = gap = np.nan
        rows.append({"month": str(m), "n": len(cur), "entries": entries, "exits": exits,
                     "exits_permanent_in_panel": permanent, "exits_with_later_return": gap})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = (ROOT / a.out) if not Path(a.out).is_absolute() else Path(a.out)
    if out.exists():
        sys.exit(f"refusing to overwrite existing {out}")
    out.mkdir(parents=True)

    c6_path = ROOT / "data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz"
    c6 = pd.read_csv(c6_path, usecols=ACCESSED["C6 cost inputs"], parse_dates=["date"])
    c6["month"] = month_key(c6["date"])
    inputs = {str(c6_path.relative_to(ROOT)): sha(c6_path)}

    flows, coverage, last_month = [], [], {}
    c4_sets = {}
    for ctry in COUNTRIES:
        p1 = ROOT / f"data/intl_c1/production/{ctry}/universe.parquet"
        p4 = ROOT / f"data/intl_c4/production/{ctry}/targets.parquet"
        for p in (p1, p4):
            inputs[str(p.relative_to(ROOT))] = sha(p)
        u = pq.read_table(p1, columns=ACCESSED["C1 universe"]).to_pandas()
        t = pq.read_table(p4, columns=ACCESSED["C4 targets"]).to_pandas()
        u["month"], t["month"] = month_key(u["date"]), month_key(t["date"])
        uu = u[u["in_universe"].astype(bool)][["month", "permno"]].drop_duplicates()
        tt = t[["month", "permno"]].drop_duplicates()
        cc = c6[c6["country"] == ctry][["month", "permno"]].drop_duplicates()
        c4_sets[ctry] = {m: set(g["permno"]) for m, g in tt.groupby("month")}
        last_month[ctry] = tt.groupby("permno")["month"].max()
        for name, pan in (("C1_in_universe", uu), ("C4_row_present", tt), ("C6_row_present", cc)):
            f = membership_flows(pan)
            f.insert(0, "panel", name)
            f.insert(0, "country", ctry)
            flows.append(f)
        # coverage: C4 rows that also have a C6 row / are in the C1 universe (row presence only)
        m = tt.merge(cc.assign(c6=1), how="left", on=["month", "permno"]).merge(
            uu.assign(c1=1), how="left", on=["month", "permno"])
        g = m.groupby("month").agg(c4_rows=("permno", "size"), c4_with_c6_row=("c6", "sum"), c4_in_c1_universe=("c1", "sum"))
        g.insert(0, "country", ctry)
        coverage.append(g.reset_index().astype({"month": str}))
    flows = pd.concat(flows, ignore_index=True)
    coverage = pd.concat(coverage, ignore_index=True)
    lo, hi = WINDOW[0].to_period("M"), WINDOW[1].to_period("M")
    in_win = lambda s: (pd.PeriodIndex(s, freq="M") >= lo) & (pd.PeriodIndex(s, freq="M") <= hi)
    flows = flows[in_win(flows["month"])].reset_index(drop=True)
    coverage = coverage[in_win(coverage["month"])].reset_index(drop=True)
    flows.to_csv(out / "panel_flows_by_country_month.csv", index=False)
    coverage.to_csv(out / "panel_coverage_by_country_month.csv", index=False)

    # held names affected by panel exits (identifiers/membership only)
    held_rows, first_rows = [], []
    for stem in INDEX_FILES:
        ip = ROOT / f"outputs/weights_index/{stem}.csv"
        inputs[str(ip.relative_to(ROOT))] = sha(ip)
        idx = pd.read_csv(ip, usecols=ACCESSED["weights_index"])
        for r in idx.itertuples(index=False):
            wp = Path(r.weights)
            wp = wp if wp.is_absolute() else ROOT / wp
            if not wp.exists():
                held_rows.append({"index": stem, "strategy": r.strategy, "note": "weights file missing"})
                continue
            inputs[str(wp.relative_to(ROOT)) if wp.is_relative_to(ROOT) else str(wp)] = sha(wp)
            w = pq.read_table(wp, columns=ACCESSED["weights"]).to_pandas()
            w = w[w["w"].to_numpy() != 0.0][["date", "permno"]]
            w["month"] = month_key(w["date"])
            w = w[(w["month"] >= lo) & (w["month"] <= hi)]
            ctry = r.country
            sets, last = c4_sets[ctry], last_month[ctry]
            months = sorted(sets)
            nxt = {m: months[i + 1] for i, m in enumerate(months[:-1])}
            per, first = [], None
            for m, g in w.groupby("month"):
                held = set(g["permno"])
                absent = {p for p in held if m in nxt and p not in sets[nxt[m]]}
                perm = {p for p in absent if last[p] == m} if absent else set()
                per.append({"index": stem, "country": ctry, "aum": r.aum, "strategy": r.strategy, "month": str(m),
                            "n_held": len(held), "n_held_not_in_next_c4": len(absent),
                            "n_held_not_in_next_c4_permanent": len(perm),
                            "n_held_not_in_c4_this_month": len(held - sets.get(m, set()))})
                if absent and first is None:
                    first = m
            held_rows.extend(per)
            nm = w["month"].nunique()
            if first is not None:
                months_win = sorted(w["month"].unique())
                n_after = sum(1 for m in months_win if m >= first)
            else:
                n_after = 0
            first_rows.append({"index": stem, "country": ctry, "aum": r.aum, "strategy": r.strategy,
                               "months_with_weights": nm, "first_month_with_held_panel_exit": str(first) if first else "",
                               "months_from_first_exit_to_end": n_after,
                               "projected_unresolved_share_if_first_held_exit_is_unresolved":
                                   round(n_after / nm, 4) if nm else np.nan})
    held = pd.DataFrame(held_rows)
    firsts = pd.DataFrame(first_rows)
    held.to_csv(out / "held_names_affected_by_panel_exits.csv", index=False)
    firsts.to_csv(out / "projected_unresolved_share_by_strategy.csv", index=False)

    def tier(x):
        return "0%" if x == 0 else "(0,5%]" if x <= 0.05 else "(5%,25%]" if x <= 0.25 else ">25%"
    col = "projected_unresolved_share_if_first_held_exit_is_unresolved"
    tiers = firsts.assign(tier=firsts[col].map(tier)).groupby(["country", "aum", "tier"]).size().rename("n_strategies").reset_index()
    tiers.to_csv(out / "projected_tier_counts.csv", index=False)

    scan = {"terminal_event_fields_found": [], "fields_scanned": {
        "C1": pq.read_schema(ROOT / "data/intl_c1/production/DEU/universe.parquet").names,
        "C4": pq.read_schema(ROOT / "data/intl_c4/production/DEU/targets.parquet").names,
        "C6": pd.read_csv(c6_path, nrows=0).columns.tolist()}}
    names = [n.lower() for v in scan["fields_scanned"].values() for n in v]
    scan["terminal_event_fields_found"] = [n for n in names if any(k in n for k in ("delist", "terminal", "dlst", "event", "exit"))]
    # 'endpoint_date' in C6 is a price-endpoint field, not a terminal-event field; it is listed here, never read.
    (out / "terminal_event_field_scan.json").write_text(json.dumps(scan, indent=2))

    manifest = {
        "label": "OUTCOME-FREE INPUT CENSUS - not a result; revised analysis, not confirmatory",
        "spec": "docs/PHASE_C_REVISED_ANALYSIS_SPEC_2026-10-14.md + PHASE_C_SPEC_ADDENDUM_1_2026-10-14.md",
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "git_dirty": bool(subprocess.run(["git", "status", "--porcelain", "--", "tools/phase_c_input_census.py"],
                                         cwd=ROOT, capture_output=True, text=True).stdout.strip()),
        "window": [str(WINDOW[0].date()), str(WINDOW[1].date())],
        "columns_accessed": ACCESSED,
        "values_not_read": "returns, prices, dividends, cost values, tax results, NAV, Sharpe, any performance summary",
        "definition_panel_exit": "present at month t and absent at month t+1 in the named panel; NOT inferred to be a delisting",
        "definition_held": "weights-file row with w != 0 (identifier membership test only)",
        "projection_note": "projected_unresolved_share assumes only the carry_v1 rule that a held name absent from C4 with no exit evidence "
                           "makes that month and all later months unresolved; it is derived from membership alone and is not a result",
        "pandas": pd.__version__, "numpy": np.__version__,
        "input_sha256": inputs,
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print("done", out)


if __name__ == "__main__":
    main()
