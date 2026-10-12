#!/usr/bin/env python
"""Does the participation constraint destroy the identifiability of ML design choice?

The question
------------
The project's factorial has three design axes on the prediction-loss cells - representation
(L inear / N onlinear), conditioning (S tatic / C onditional) and uncertainty shrinkage (0 / U) -
and on the optimised book **none of them is detectable** (t = +0.48, -1.20, +1.53) even though the
signals themselves carry IC t up to +10.4. That null has been reported but never explained.

The capacity result suggests an explanation. If the ADV participation cap governs the book above a
critical mandate size, then at institutional scale the cap, not the model, is choosing the weights -
and the design axes should become **less** distinguishable as the cap binds harder. At small
mandates, where the cap is slack, the axes should be distinguishable if they differ at all.

That is a falsifiable statement about a *null*, which is much stronger than the null alone: it says
the design literature's question (@GKX2020 and successors) is **not answerable at institutional
scale in a market of this depth**, and says why.

What this measures
------------------
From the compliant monthly dumps (``--require-cost-inputs``), at every AUM rung, for each axis:

* build the equal-weighted composite of the 4 cells at each level of the axis;
* test the **difference of their net Sharpe ratios** with the paired studentized bootstrap
  (``sharpe_difference_test``), which is the same instrument used for the capacity channel;
* report the axis effect, its t statistic, and Holm-adjusted p across the three axes;
* report it for the **capped** book (what an investor can run) and the **uncapped** book (what a
  signal paper reports), so the cap's contribution is visible rather than inferred.

The prediction, stated before looking: axis effects on the **capped** book shrink toward zero as
cap slack falls, while axis effects on the **uncapped** book do not.

Usage
-----
    python tools/exp_design_identifiability.py --country DEU IND JPN
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.validation.inference import sharpe_difference_test  # noqa: E402

PERIODS = 12

# cell names look like L-S-P-0: representation - conditioning - loss - uncertainty
AXES = {
    "representation": (0, "N", "L"),   # position in the name, level A, level B  -> effect = A - B
    "conditioning":   (1, "C", "S"),
    "uncertainty":    (3, "U", "0"),
}


def holm(p: dict[str, float]) -> dict[str, float]:
    items = sorted(((k, v) for k, v in p.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out = {k: float("nan") for k in p}
    run = 0.0
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - i) * v))
        out[k] = run
    return out


def composite(df: pd.DataFrame, cells: list[str], col: str) -> pd.Series:
    piv = df[df.cell.isin(cells)].pivot_table(index="date", columns="cell", values=col)
    return piv.dropna().mean(axis=1)


def run_country(country: str, src: Path, n_boot: int, block: int, seed: int) -> pd.DataFrame:
    path = src / f"monthly_{country}_cov.csv"
    if not path.exists():
        raise SystemExit(f"no compliant monthly series at {path}; run the wedge tool with "
                         f"--require-cost-inputs --tag cov")
    mon = pd.read_csv(path, parse_dates=["date"])
    mon = mon[mon.cell.str.contains("-P-")]
    cells = sorted(mon.cell.unique())
    if len(cells) != 8:
        raise SystemExit(f"{country}: expected 8 prediction cells, found {len(cells)}: {cells}")

    rows = []
    for aum, g in mon.groupby("aum"):
        slack = 1.0 - float(g.gross_capped.mean()) / 2.0
        for book, col in (("capped", "net_ret_capped"), ("uncapped", "net_ret_uncapped")):
            pv = {}
            per = []
            for axis, (pos, hi, lo) in AXES.items():
                a_cells = [c for c in cells if c.split("-")[pos] == hi]
                b_cells = [c for c in cells if c.split("-")[pos] == lo]
                if len(a_cells) != 4 or len(b_cells) != 4:
                    raise SystemExit(f"{country} {axis}: split is {len(a_cells)}/{len(b_cells)}")
                ra = composite(g, a_cells, col)
                rb = composite(g, b_cells, col)
                idx = ra.index.intersection(rb.index)
                r = sharpe_difference_test(ra.loc[idx].to_numpy(), rb.loc[idx].to_numpy(),
                                           periods=PERIODS, n_boot=n_boot, block=block, seed=seed)
                pv[axis] = r.p_value
                per.append({
                    "country": country, "aum": float(aum), "cap_slack": slack, "book": book,
                    "axis": axis, "levels": f"{hi}-{lo}",
                    "effect": r.statistic, "se": r.detail["se_hac"],
                    "t": r.detail["studentized"], "p": r.p_value,
                    "sharpe_hi": r.detail["sharpe_a"], "sharpe_lo": r.detail["sharpe_b"],
                    "months": r.detail["n_obs"],
                })
            adj = holm(pv)
            for d in per:
                d["p_holm"] = adj.get(d["axis"], np.nan)
            rows.extend(per)
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", nargs="+", default=["DEU", "IND"])
    ap.add_argument("--src", type=Path, default=ROOT / "outputs" / "signal_vs_portfolio")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "design_identifiability")
    ap.add_argument("--n-boot", type=int, default=1500)
    ap.add_argument("--block", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true",
        help="discard an earlier output written by a different run (or of unknown origin); by default such a collision is refused (alphacomb.output_guard)")
    a = ap.parse_args(argv)
    from alphacomb.output_guard import claim_run
    claim_run([a.out / f"design_identifiability_{c}.csv" for c in a.country]
              + [a.out / "design_identifiability_all.csv"], a)
    a.out.mkdir(parents=True, exist_ok=True)

    allr = []
    for c in a.country:
        t = run_country(c, a.src, a.n_boot, a.block, a.seed)
        allr.append(t)
        t.to_csv(a.out / f"design_identifiability_{c}.csv", index=False)
        print(f"\n{'='*96}\n{c}  -  IS ML DESIGN CHOICE IDENTIFIABLE?\n{'='*96}")
        for book in ("capped", "uncapped"):
            s = t[t.book == book]
            print(f"\n  {book.upper()} book  (axis effect = difference of net Sharpe ratios, "
                  f"paired test)\n")
            hdr = f"  {'AUM':>9} {'slack':>7} |"
            for axis in AXES:
                hdr += f" {axis[:6]:>7} {'t':>6} |"
            print(hdr)
            print("  " + "-" * (len(hdr) - 2))
            for aum in sorted(s.aum.unique()):
                r = s[s.aum == aum]
                line = f"  {aum:>9.0e} {r.cap_slack.iloc[0]*100:>6.2f}% |"
                for axis in AXES:
                    q = r[r.axis == axis]
                    if q.empty:
                        line += f" {'--':>7} {'--':>6} |"
                        continue
                    star = "*" if q.p_holm.iloc[0] < 0.05 else " "
                    line += f" {q.effect.iloc[0]:>+7.3f} {q.t.iloc[0]:>+6.2f}{star}|"
                print(line)
            nsig = int((s.p_holm < 0.05).sum())
            print(f"\n    axis-rungs significant after Holm: {nsig} of {len(s)}")
        # the headline comparison
        cap = t[t.book == "capped"]
        unc = t[t.book == "uncapped"]
        lo_aum, hi_aum = cap.aum.min(), cap.aum.max()
        for name, s in (("capped", cap), ("uncapped", unc)):
            l = s[s.aum == lo_aum].effect.abs().mean()
            h = s[s.aum == hi_aum].effect.abs().mean()
            print(f"    {name:>8}: mean |axis effect| {l:.4f} at ${lo_aum:.0e}  ->  "
                  f"{h:.4f} at ${hi_aum:.0e}   ({'shrinks' if h < l else 'grows'})")
    out = pd.concat(allr, ignore_index=True)
    out.to_csv(a.out / "design_identifiability_all.csv", index=False)
    print(f"\nwrote {a.out / 'design_identifiability_all.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
