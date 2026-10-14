#!/usr/bin/env python
"""Gate 1 for the stock-level liquidity arm: does the illiquid-vs-liquid pattern survive controls?

Written and committed BEFORE the value-weighted and size-neutral variants were run, so the pass
criterion cannot be chosen once the answer is visible.

Background
----------
The baseline diagnostic (equal-weighted, raw dollar ADV, 13 themes) found illiquid above liquid in
10 of 13 German themes (mean gap +0.50 Sharpe) and 11 of 13 Indian themes (mean +0.45), and
neither in Japan (5 of 13, mean -0.03). The obvious alternative explanation is that equal-weighting
lets tiny stocks dominate each decile. Gate 1 asks whether the pattern is still there when
(a) legs are value-weighted, (b) liquidity is made size-neutral, and (c) both.

Frozen pass criterion
---------------------
The premise "alpha is concentrated in illiquid names" PASSES Gate 1 in a market iff, in EVERY one
of the three variants (vw/adv, ew/adv_resid, vw/adv_resid):

    * the mean (illiquid - liquid) Sharpe gap across the 13 themes is >= 50% of that market's
      baseline mean gap, AND
    * at least 8 of 13 themes still have illiquid > liquid.

The arm proceeds only if Germany AND India both pass. Japan is reported, not gated: the baseline
already contradicts the premise there, and the gate is about whether the shallow-market pattern
is real or a size artefact.

Usage
-----
    python tools/gate1_liquidity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "outputs" / "theme_liquidity"

KEEP_FRACTION = 0.50      # variant mean gap must keep at least this share of the baseline's
MIN_THEMES = 8            # of 13
GATED = ("DEU", "IND")
VARIANTS = (("vw", "adv"), ("ew", "adv_resid"), ("vw", "adv_resid"))


def load(country: str, w: str, liq: str) -> pd.DataFrame | None:
    sfx = "" if (w, liq) == ("ew", "adv") else f"_{w}_{liq}"
    p = D / f"theme_liquidity_{country}{sfx}.csv"
    return pd.read_csv(p) if p.exists() else None


def summarise(t: pd.DataFrame) -> dict:
    return {"n_pos": int((t.sr_illiquid > t.sr_liquid).sum()), "n": len(t),
            "mean_gap": float(t.diff_illiq_minus_liq.mean()),
            "holm_sig": int((t.diff_p_holm < 0.05).sum()),
            "raw_sig": int((t.diff_p < 0.05).sum())}


def main() -> int:
    verdict: dict[str, bool | None] = {}
    for c in ("DEU", "IND", "JPN"):
        base = load(c, "ew", "adv")
        if base is None:
            print(f"{c}: no baseline file")
            continue
        b = summarise(base)
        print(f"\n{'='*92}\n{c}   baseline (ew, adv): {b['n_pos']}/{b['n']} themes illiquid>liquid, "
              f"mean gap {b['mean_gap']:+.3f}, Holm-sig {b['holm_sig']}, raw-sig {b['raw_sig']}\n{'='*92}")
        print(f"  {'variant':<16}{'#illiq>liq':>11}{'mean gap':>10}{'% of base':>11}"
              f"{'Holm':>6}{'raw':>5}   criterion")
        ok_all = True
        missing = False
        for w, liq in VARIANTS:
            t = load(c, w, liq)
            if t is None:
                print(f"  {w+'/'+liq:<16}{'-- not run --':>34}")
                missing = True
                continue
            s = summarise(t)
            share = s["mean_gap"] / b["mean_gap"] if b["mean_gap"] else float("nan")
            ok = (share >= KEEP_FRACTION) and (s["n_pos"] >= MIN_THEMES)
            ok_all &= ok
            print(f"  {w+'/'+liq:<16}{s['n_pos']:>8}/13{s['mean_gap']:>+10.3f}{share*100:>10.0f}%"
                  f"{s['holm_sig']:>6}{s['raw_sig']:>5}   {'PASS' if ok else 'FAIL'}")
        verdict[c] = None if missing else ok_all
        if c not in GATED:
            print(f"  ({c} is reported, not gated)")

    print(f"\n{'-'*92}\nGATE 1 VERDICT\n{'-'*92}")
    gated = [verdict.get(c) for c in GATED]
    if any(v is None for v in gated):
        print("  INCOMPLETE: not all gated variants have been run.")
        return 2
    if all(gated):
        print("  PASS in both Germany and India. The pattern is not a size artefact; proceed to Gate 2.")
        return 0
    failed = [c for c in GATED if not verdict[c]]
    print(f"  FAIL in {', '.join(failed)}. The illiquid-tercile advantage is largely an equal-weighting")
    print("  / small-cap effect. Stop: do not build the stock-level liquidity arm as a flagship candidate;")
    print("  retain the baseline as a diagnostic result.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
