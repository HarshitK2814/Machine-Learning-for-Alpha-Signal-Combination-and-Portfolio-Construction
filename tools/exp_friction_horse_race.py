#!/usr/bin/env python
"""The friction horse race: cost, capacity and tax drag in one place, in one unit.

The gap this closes
-------------------
Every input to this table has existed for some time and it has never been assembled, so the
project has been asserting that "capacity dominates and taxes are second-order" from numbers that
live in three different files, measured on two different books, averaged over a cell set that
includes an arm known to be broken. Assembling it immediately exposed that the published
"cost beats tax 5x in Germany and 53x in India" figures are **all-16-cell** averages: on the
prediction cells alone - the only cells whose scores carry signal, and the only cells amendments
001C and 001D concern - the ratios are 2.70x and 87.4x. Germany's margin is one order of
magnitude, not two.

What this measures, and the one thing it cannot
-----------------------------------------------
All quantities are **annualised basis points of drag on return**, plus the same decomposition in
**Sharpe points**, so the three frictions are directly comparable.

* **Cost drag** and **capacity drag** are measured on the **decile-spread book**, because that is
  the only book for which the uncapped counterfactual exists.
* **Tax drag** is measured on the **optimised book** from stage 06, because the lot-level tax
  engine runs on realised portfolio weights and the decile-spread book has never been through it.

Those are two different books, and this table therefore compares **orders of magnitude, not a
decomposition that sums to the total**. That limitation is stated in the output rather than hidden,
and it is not fixable by arithmetic: the uncapped *optimised* book cannot be constructed at all,
which is itself one of the project's findings (`docs/ECONOMIC_ARM_CAPABILITY_GAP.md`, and the two
backtest refusals recorded in `docs/RESULTS_CAPACITY_2026-10-09.md`). The honest reading is that
the tax channel is being given its best case - measured on the lower-turnover, constrained book -
and still loses.

Usage
-----
    python tools/exp_friction_horse_race.py --country DEU IND
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BPS = 12 * 1e4


def decile_panel(country: str, src: Path, tag: str = "cov") -> pd.DataFrame:
    """Cost and capacity drag by AUM, from the decile-spread monthly series."""
    path = src / f"monthly_{country}_{tag}.csv"
    if not path.exists():
        raise SystemExit(f"no monthly series at {path}; "
                         f"run exp_signal_vs_portfolio_wedge.py --dump-monthly")
    mon = pd.read_csv(path, parse_dates=["date"])
    mon = mon[mon.cell.str.contains("-P-")]
    if mon.empty:
        raise SystemExit(f"{country}: no prediction cells in {path}")

    out = []
    for aum, g in mon.groupby("aum"):
        piv = g.pivot_table(index="date", columns="cell",
                            values=["gross_ret", "net_ret_uncapped",
                                    "gross_ret_capped", "net_ret_capped"]).dropna()
        gross = piv["gross_ret"].mean(axis=1)
        net_u = piv["net_ret_uncapped"].mean(axis=1)
        gros_c = piv["gross_ret_capped"].mean(axis=1)
        net_c = piv["net_ret_capped"].mean(axis=1)

        def sr(x):
            s = x.std(ddof=1)
            return float(x.mean() / s * np.sqrt(12)) if s > 0 else np.nan

        out.append({
            "country": country, "aum": float(aum), "months": len(piv),
            "gross_ret_ann_bps": float(gross.mean() * BPS),
            "cost_drag_ann_bps": float((gross - net_u).mean() * BPS),
            "capacity_drag_ann_bps": float((gross - gros_c).mean() * BPS),
            "net_capped_ret_ann_bps": float(net_c.mean() * BPS),
            "sharpe_gross": sr(gross),
            "sharpe_net_uncapped": sr(net_u),
            "sharpe_net_capped": sr(net_c),
            "cost_channel_sharpe": sr(net_u) - sr(gross),
            "capacity_channel_sharpe": sr(net_c) - sr(net_u),
        })
    return pd.DataFrame(out).sort_values("aum")


def tax_panel(country: str, aum_tag: str = "1e9") -> pd.DataFrame:
    """Cost and tax drag on the optimised book, split by arm so nothing is averaged away."""
    path = ROOT / "outputs" / f"summary_after_tax_{country}_{aum_tag}.csv"
    if not path.exists():
        raise SystemExit(f"no after-tax summary at {path}; run pipelines/06_after_tax_eval.py")
    d = pd.read_csv(path)
    if "dated" in d.columns:
        d = d[~d["dated"].astype(str).str.lower().isin({"true", "1"})]
    tx = d[d.regime != "tax_exempt"].copy()
    tx["arm"] = np.where(tx.strategy.str.contains("-P-"), "prediction",
                         np.where(tx.strategy.str.contains("-E-"), "economic", "other"))
    rows = []
    for arm, g in tx.groupby("arm"):
        rows.append({
            "country": country, "arm": arm, "cells": len(g),
            "regime": g.regime.iloc[0],
            "cost_drag_ann_bps": float(g.cost_drag_ann_bps.mean()),
            "tax_drag_ann_bps": float(g.tax_drag_ann_bps.mean()),
            "sharpe_gross": float(g.gross_sharpe.mean()),
            "sharpe_net": float(g.net_sharpe.mean()),
            "sharpe_after_tax": float(g.after_tax_sharpe.mean()),
            "tax_channel_sharpe": float((g.after_tax_sharpe - g.net_sharpe).mean()),
            "lt_share_of_gains": float(g.lt_share_of_gains.mean()),
            "turnover_mean": float(g.turnover_mean.mean()),
        })
    allrow = {
        "country": country, "arm": "ALL 16 (as previously published)", "cells": len(tx),
        "regime": tx.regime.iloc[0],
        "cost_drag_ann_bps": float(tx.cost_drag_ann_bps.mean()),
        "tax_drag_ann_bps": float(tx.tax_drag_ann_bps.mean()),
        "sharpe_gross": float(tx.gross_sharpe.mean()),
        "sharpe_net": float(tx.net_sharpe.mean()),
        "sharpe_after_tax": float(tx.after_tax_sharpe.mean()),
        "tax_channel_sharpe": float((tx.after_tax_sharpe - tx.net_sharpe).mean()),
        "lt_share_of_gains": float(tx.lt_share_of_gains.mean()),
        "turnover_mean": float(tx.turnover_mean.mean()),
    }
    rows.append(allrow)
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", nargs="+", default=["DEU", "IND"])
    ap.add_argument("--src", type=Path, default=ROOT / "outputs" / "signal_vs_portfolio")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "horse_race")
    ap.add_argument("--tag", default="cov",
                    help="which decile ladder to read. Default 'cov' is the COMPLIANT, "
                         "investable-universe ladder (--require-cost-inputs). The 'infer' ladder "
                         "was built on the signal-bearing cross-section and its Panel A is not "
                         "compliant with document 13 requirement 2; see "
                         "docs/RESULTS_CAPACITY_CHANNEL_2026-10-09.md section 6")
    ap.add_argument("--aum-tag", default="1e9",
                    help="which optimised-book after-tax summary to use for the tax column")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)

    dec_all, tax_all = [], []
    for c in a.country:
        dec = decile_panel(c, a.src, a.tag)
        tx = tax_panel(c, a.aum_tag)
        dec_all.append(dec)
        tax_all.append(tx)

        print(f"\n{'='*100}")
        print(f"{c}  -  FRICTION HORSE RACE")
        print(f"{'='*100}")
        warn = "" if a.tag == "cov" else "   *** NOT THE COMPLIANT LADDER ***"
        print(f"\nPanel A. Decile-spread book, prediction cells, "
              f"{int(dec.months.iloc[0])} months, ladder '{a.tag}'.{warn}")
        print("  Annualised bps of drag on return, and the same decomposition in Sharpe points.\n")
        print(f"  {'AUM':>9} | {'gross':>9} {'cost':>10} {'capacity':>10} {'net capped':>11} | "
              f"{'SR gross':>9} {'cost ch':>8} {'cap ch':>8} {'SR net cap':>10}")
        print(f"  {'-'*9}-+-{'-'*9}-{'-'*10}-{'-'*10}-{'-'*11}-+-{'-'*9}-{'-'*8}-{'-'*8}-{'-'*10}")
        for _, r in dec.iterrows():
            print(f"  {r.aum:>9.0e} | {r.gross_ret_ann_bps:>9.0f} "
                  f"{r.cost_drag_ann_bps:>10.0f} {r.capacity_drag_ann_bps:>10.0f} "
                  f"{r.net_capped_ret_ann_bps:>11.0f} | "
                  f"{r.sharpe_gross:>+9.3f} {r.cost_channel_sharpe:>+8.3f} "
                  f"{r.capacity_channel_sharpe:>+8.3f} {r.sharpe_net_capped:>+10.3f}")

        print(f"\nPanel B. Optimised book at {a.aum_tag}, stage 06, taxable regime "
              f"({tx.regime.iloc[0]}).")
        print("  Split by arm, because averaging the broken economic arm into this is exactly how")
        print("  the previously published cost-versus-tax ratios were formed.\n")
        print(f"  {'arm':<34} {'n':>3} {'cost bps':>9} {'tax bps':>8} {'cost/tax':>9} "
              f"{'SR net':>8} {'SR a/tax':>9} {'tax ch':>8} {'turnover':>9}")
        print(f"  {'-'*34} {'-'*3} {'-'*9} {'-'*8} {'-'*9} {'-'*8} {'-'*9} {'-'*8} {'-'*9}")
        for _, r in tx.sort_values("arm").iterrows():
            ratio = (r.cost_drag_ann_bps / r.tax_drag_ann_bps
                     if r.tax_drag_ann_bps else float("inf"))
            print(f"  {r.arm:<34} {r.cells:>3} {r.cost_drag_ann_bps:>9.2f} "
                  f"{r.tax_drag_ann_bps:>8.3f} {ratio:>8.1f}x {r.sharpe_net:>+8.3f} "
                  f"{r.sharpe_after_tax:>+9.3f} {r.tax_channel_sharpe:>+8.3f} "
                  f"{r.turnover_mean:>9.4f}")

        pred = tx[tx.arm == "prediction"]
        if not pred.empty:
            p = pred.iloc[0]
            at_1e9 = dec[np.isclose(dec.aum, 1e9)]
            print(f"\n  Verdict for {c}, prediction cells only:")
            print(f"    tax drag           {p.tax_drag_ann_bps:>10.3f} bps p.a.   "
                  f"(Sharpe {p.tax_channel_sharpe:+.4f})")
            print(f"    cost drag          {p.cost_drag_ann_bps:>10.3f} bps p.a.   "
                  f"= {p.cost_drag_ann_bps / p.tax_drag_ann_bps:,.1f}x the tax drag"
                  if p.tax_drag_ann_bps else "")
            if not at_1e9.empty:
                q = at_1e9.iloc[0]
                print(f"    capacity drag      {q.capacity_drag_ann_bps:>10.0f} bps p.a.   "
                      f"= {q.capacity_drag_ann_bps / p.tax_drag_ann_bps:,.0f}x the tax drag"
                      if p.tax_drag_ann_bps else "")
                print(f"    (capacity and cost on the decile book at $1bn; tax on the optimised "
                      f"book - orders of magnitude, not a decomposition)")

    pd.concat(dec_all, ignore_index=True).to_csv(a.out / "horse_race_decile_panel.csv", index=False)
    pd.concat(tax_all, ignore_index=True).to_csv(a.out / "horse_race_tax_panel.csv", index=False)
    print(f"\nwrote {a.out / 'horse_race_decile_panel.csv'}")
    print(f"wrote {a.out / 'horse_race_tax_panel.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
