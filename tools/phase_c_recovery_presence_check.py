#!/usr/bin/env python
"""Phase C recovery feasibility: presence-only census of ``ret_next`` gaps (no value is read into any output).

Fields: C4 ``date, permno`` + flags ``ret_next`` finite, ``div_next`` finite; C1 ``date, permno, in_universe`` +
flag ``price`` non-null. Each numeric column is reduced to a boolean at load time and discarded. Nothing numeric
is printed, stored or aggregated. A "gap run" is a maximal sequence of consecutive C4 months in which the row is
present and ``ret_next`` is unusable. This is a count of positions, not an interpretation of any event.

    python tools/phase_c_recovery_presence_check.py --out results/phase_c_recovery_feasibility_2026-10-14
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
WINDOW = (pd.Period("2009-01", "M"), pd.Period("2019-12", "M"))
COUNTRIES = ["DEU", "IND", "JPN"]
C4_COLS = ["date", "permno", "ret_next", "div_next"]
C1_COLS = ["date", "permno", "in_universe", "price"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def flags_c4(t: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"mi": pd.PeriodIndex(pd.to_datetime(t["date"]).dt.to_period("M")).asi8,
                         "permno": t["permno"].to_numpy(),
                         "ret_ok": np.isfinite(t["ret_next"].to_numpy(dtype=float)),
                         "div_ok": np.isfinite(t["div_next"].to_numpy(dtype=float))})


def flags_c1(u: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"mi": pd.PeriodIndex(pd.to_datetime(u["date"]).dt.to_period("M")).asi8,
                         "permno": u["permno"].to_numpy(), "in_univ": u["in_universe"].astype(bool).to_numpy(),
                         "price_present": u["price"].notna().to_numpy()})


def gap_runs(c4: pd.DataFrame, c1: pd.DataFrame, lo: int, hi: int) -> pd.DataFrame:
    """One row per gap run of a name, positions and presence flags only."""
    m = c4.merge(c1, how="left", on=["mi", "permno"]).sort_values(["permno", "mi"])
    m["price_present"] = m["price_present"].eq(True)
    m["in_univ"] = m["in_univ"].eq(True)
    rows = []
    for p, g in m.groupby("permno", sort=False):
        mi, ok, dv = g["mi"].to_numpy(), g["ret_ok"].to_numpy(), g["div_ok"].to_numpy()
        pr, iu = g["price_present"].to_numpy(), g["in_univ"].to_numpy()
        n, i = len(g), 0
        while i < n:
            if ok[i]:
                i += 1
                continue
            j = i
            while j + 1 < n and (not ok[j + 1]) and mi[j + 1] == mi[j] + 1:
                j += 1
            if lo <= mi[i] <= hi:
                nxt_ok = j + 1 < n and mi[j + 1] == mi[j] + 1 and ok[j + 1]
                nxt_row = j + 1 < n and mi[j + 1] == mi[j] + 1
                rows.append({
                    "run_len_months": int(j - i + 1),
                    "ends": "recovers_to_usable_ret_next" if nxt_ok else
                            "next_c4_month_present_but_unusable_or_after_window" if nxt_row else "no_next_c4_row",
                    "all_run_months_in_universe": bool(iu[i:j + 1].all()),
                    "div_next_unusable_throughout_run": bool((~dv[i:j + 1]).all()),
                    "c1_price_present_at_every_run_month": bool(pr[i:j + 1].all()),
                    "c1_price_present_at_recovery_month": bool(nxt_ok and pr[j + 1]),
                    "prior_month_ret_next_usable": bool(i > 0 and mi[i - 1] == mi[i] - 1 and ok[i - 1])})
            i = j + 1
    return pd.DataFrame(rows)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out) if Path(a.out).is_absolute() else ROOT / a.out
    if out.exists():
        sys.exit(f"refusing to overwrite existing {out}")
    out.mkdir(parents=True)
    lo, hi = WINDOW[0].ordinal, WINDOW[1].ordinal
    summ, inputs = [], {}
    for c in COUNTRIES:
        p4 = ROOT / f"data/intl_c4/production/{c}/targets.parquet"
        p1 = ROOT / f"data/intl_c1/production/{c}/universe.parquet"
        inputs[str(p4.relative_to(ROOT))], inputs[str(p1.relative_to(ROOT))] = sha(p4), sha(p1)
        runs = gap_runs(flags_c4(pq.read_table(p4, columns=C4_COLS).to_pandas()),
                        flags_c1(pq.read_table(p1, columns=C1_COLS).to_pandas()), lo, hi)
        runs["bucket"] = pd.cut(runs["run_len_months"], [0, 1, 3, 12, 10**6], labels=["1", "2-3", "4-12", ">12"])
        g = runs.groupby(["bucket", "ends", "all_run_months_in_universe", "div_next_unusable_throughout_run",
                          "c1_price_present_at_every_run_month", "c1_price_present_at_recovery_month"],
                         observed=True).size().rename("n_runs").reset_index()
        g.insert(0, "country", c)
        summ.append(g)
    pd.concat(summ, ignore_index=True).to_csv(out / "gap_runs_summary.csv", index=False)
    (out / "MANIFEST.json").write_text(json.dumps({
        "label": "OUTCOME-FREE PRESENCE CHECK - not a result",
        "fields": {"C4": C4_COLS, "C1": C1_COLS},
        "reduction": "ret_next/div_next -> isfinite flag; price -> notna flag; values discarded at load",
        "window": ["2009-01", "2019-12"], "input_sha256": inputs}, indent=2))
    print("done", out)


if __name__ == "__main__":
    main()
