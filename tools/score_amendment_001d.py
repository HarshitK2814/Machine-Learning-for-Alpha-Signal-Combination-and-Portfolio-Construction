#!/usr/bin/env python
"""Score Japan against the five predictions of AMENDMENT_001D, mechanically.

Why this is a script and not a judgement
----------------------------------------
This file is written and committed **before Japan's portfolios exist**, so the scoring rule is
fixed in advance rather than chosen once the answer is visible. That is the whole point of the
amendment, and a pre-registration whose evaluation is done by hand afterwards is not one.

Every threshold below is copied from `docs/AMENDMENT_001D_CAPACITY_CHANNEL_SIGN_FLIP.md` section 4
as revised at 12:06 IST on 2026-10-09. The reference values from the exploratory sample
(Germany and India) are hard-coded here so that a later change to those files cannot silently move
the goalposts.

What it does
------------
1. Reads Japan's composite capacity-channel inference table.
2. Evaluates D1-D5, printing PASS / FAIL / VOID with the number that decided each.
3. Prints the overall verdict using the section-5 falsification rules, including the case where
   D3's antecedent is false and the mechanism therefore rests on Germany alone.

Usage
-----
    python tools/repair_source_index.py --country JPN
    python tools/exp_signal_vs_portfolio_wedge.py --country JPN --dump-monthly \
        --aum 1e3 3e3 1e4 3e4 1e5 3e5 1e6 3e6 1e7 3e7 1e8 1e9 1e10 --tag infer
    python tools/exp_capacity_channel_inference.py --country JPN
    python tools/score_amendment_001d.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# ---- frozen reference values from the exploratory sample (001D sections 3a, 4) ----------------
IND_GROSS_SHARPE = 1.209      # India composite gross decile Sharpe - D3's antecedent threshold
DEU_ASYMPTOTIC_RATIO = 4.58   # Germany asymptotic channel / gross Sharpe
IND_ASYMPTOTIC_RATIO = 4.82   # India, same
D4_BAND = (3.5, 5.5)          # D4 band
D5_THRESHOLD = 4.00           # Germany's channel at $1bn scaled by gross Sharpe (11.0552/2.763)
D1_TOLERANCE = 0.05           # D1: no decrease exceeding this between adjacent rungs
ALPHA = 0.05


def load(country: str, src: Path) -> pd.DataFrame:
    p = src / f"capacity_channel_inference_{country}.csv"
    if not p.exists():
        raise SystemExit(f"no inference table at {p}; run exp_capacity_channel_inference.py first")
    d = pd.read_csv(p)
    comp = d[d.scope == "composite"].sort_values("aum").reset_index(drop=True)
    if comp.empty:
        raise SystemExit(f"{p} has no composite rows")
    return comp


def gross_sharpe(country: str, src: Path) -> float:
    """Composite gross decile Sharpe, from the monthly dump - needed by D3, D4, D5."""
    p = src.parent / "signal_vs_portfolio" / f"monthly_{country}_infer.csv"
    if not p.exists():
        raise SystemExit(f"no monthly series at {p}")
    mon = pd.read_csv(p, parse_dates=["date"])
    mon = mon[mon.cell.str.contains("-P-")]
    one = mon[np.isclose(mon.aum, mon.aum.min())]
    piv = one.pivot_table(index="date", columns="cell", values="gross_ret").dropna()
    g = piv.mean(axis=1)
    return float(g.mean() / g.std(ddof=1) * np.sqrt(12))


def score(country: str, src: Path) -> int:
    comp = load(country, src)
    gs = gross_sharpe(country, src)
    ch = comp.capacity_channel.to_numpy()
    aum = comp.aum.to_numpy()
    p = comp.p_value.to_numpy()

    print(f"\n{'='*78}\nAMENDMENT 001D scorecard - {country}\n{'='*78}")
    print(f"composite gross decile Sharpe: {gs:+.4f}   "
          f"(India reference {IND_GROSS_SHARPE:+.4f})")
    print(f"ladder: ${aum[0]:.0e} .. ${aum[-1]:.0e}, {len(aum)} rungs, "
          f"{int(comp.months.iloc[0])} months\n")

    results: dict[str, tuple[str, str]] = {}

    # ---- D1: monotone non-decreasing, tolerance 0.05 -----------------------------------------
    drops = np.diff(ch)
    worst = float(drops.min()) if drops.size else 0.0
    j = int(np.argmin(drops)) if drops.size else 0
    ok = worst >= -D1_TOLERANCE
    results["D1"] = ("PASS" if ok else "FAIL",
                     f"largest decrease between adjacent rungs {worst:+.4f} "
                     f"(at ${aum[j]:.0e}->${aum[j+1]:.0e}); tolerance {-D1_TOLERANCE:+.2f}")

    # ---- D2: significantly positive at $1bn ---------------------------------------------------
    i1b = int(np.argmin(np.abs(aum - 1e9)))
    if not np.isclose(aum[i1b], 1e9):
        results["D2"] = ("VOID", "no $1bn rung in the ladder")
    else:
        ok = ch[i1b] > 0 and p[i1b] < ALPHA
        results["D2"] = ("PASS" if ok else "FAIL",
                         f"channel at $1bn {ch[i1b]:+.4f}, p={p[i1b]:.4f} "
                         f"(need >0 and p<{ALPHA})")

    # ---- D3: conditional on gross Sharpe exceeding India's ------------------------------------
    low = aum <= 1e6
    neg_in_low = bool((ch[low] < 0).any()) if low.any() else False
    if gs <= IND_GROSS_SHARPE:
        results["D3"] = ("VOID",
                         f"antecedent false: gross Sharpe {gs:+.4f} <= India's "
                         f"{IND_GROSS_SHARPE:+.4f}, so no flip was predicted")
    else:
        results["D3"] = ("PASS" if neg_in_low else "FAIL",
                         f"antecedent true (gross Sharpe {gs:+.4f} > {IND_GROSS_SHARPE:+.4f}); "
                         f"negative channel somewhere in $1k..$1mn: {neg_in_low}")

    # ---- D4: asymptotic ratio in band ---------------------------------------------------------
    ratio = float(ch[-1] / gs) if gs else float("nan")
    ok = D4_BAND[0] <= ratio <= D4_BAND[1]
    results["D4"] = ("PASS" if ok else "FAIL",
                     f"asymptotic channel {ch[-1]:+.4f} / gross {gs:+.4f} = {ratio:.3f}; "
                     f"band [{D4_BAND[0]}, {D4_BAND[1]}] "
                     f"(DEU {DEU_ASYMPTOTIC_RATIO}, IND {IND_ASYMPTOTIC_RATIO})")

    # ---- D5: scaled channel at $1bn below Germany's -------------------------------------------
    if not np.isclose(aum[i1b], 1e9):
        results["D5"] = ("VOID", "no $1bn rung in the ladder")
    else:
        scaled = float(ch[i1b] / gs) if gs else float("nan")
        ok = scaled < D5_THRESHOLD
        results["D5"] = ("PASS" if ok else "FAIL",
                         f"channel at $1bn / gross = {scaled:.3f}; "
                         f"need < {D5_THRESHOLD} (Germany's value)")

    weight = {"D1": "primary (consistency check)", "D2": "primary",
              "D3": "primary, conditional", "D4": "secondary (n=2)", "D5": "secondary"}
    for key in ("D1", "D2", "D3", "D4", "D5"):
        verdict, why = results[key]
        mark = {"PASS": "PASS", "FAIL": "FAIL", "VOID": "VOID"}[verdict]
        print(f"  {key}  {mark:4s}  [{weight[key]}]")
        print(f"        {why}")

    print(f"\n{'-'*78}\nVERDICT\n{'-'*78}")
    d1, d2, d3 = (results[k][0] for k in ("D1", "D2", "D3"))
    if d2 == "FAIL" and d3 == "FAIL":
        print("  H-FLIP FALSIFIED. Section 5: the joint failure of D2 and D3 means scale does not")
        print("  govern the sign and the reconciliation of the literature fails. Report this with")
        print("  the same prominence as the two failures in RESULTS_WEDGE_TEST.md.")
    elif d2 == "FAIL":
        print("  H-FLIP's CORE CLAIM FAILS. A channel not positive at $1bn, well past Japan's")
        print("  $413mn frontier, breaks the claim that the cap pays once kappa is large.")
    elif d1 == "FAIL":
        print("  PIPELINE SUSPECT, not H-FLIP. D1 is near-mechanical given the cost model;")
        print("  investigate the pipeline before interpreting anything else here.")
    elif d3 == "VOID":
        print("  H-FLIP PARTIALLY CONFIRMED. D2 holds, so the cap pays at scale in a third market.")
        print("  D3 is void (Japan's signal is no stronger than India's), so the SIGN FLIP itself")
        print("  rests on GERMANY ALONE and must be reported that way - one market, exploratory.")
    elif d3 == "FAIL":
        print("  MECHANISM EXPLANATION FALSIFIED. D2 holds but the section-3c illiquid-tail-alpha")
        print("  account of why Germany flips and India does not is wrong. The flip becomes an")
        print("  unexplained one-market fact.")
    else:
        print("  H-FLIP CONFIRMED on the pre-registered sample. D1, D2 and D3 all hold.")
        print("  Report Japan as a pre-registered out-of-sample test, citing the 001D commit date.")
    sec = [k for k in ("D4", "D5") if results[k][0] == "FAIL"]
    if sec:
        print(f"\n  Secondary predictions failing: {', '.join(sec)}. Per section 4 these are")
        print("  failures of the candidate regularity, not of H-FLIP, and must still be reported.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", default="JPN")
    ap.add_argument("--src", type=Path, default=ROOT / "outputs" / "capacity_inference")
    a = ap.parse_args(argv)
    return score(a.country, a.src)


if __name__ == "__main__":
    raise SystemExit(main())
