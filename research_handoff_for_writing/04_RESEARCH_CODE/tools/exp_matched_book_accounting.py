#!/usr/bin/env python
"""Cost, capacity and tax on ONE book: matched-book accounting.

The gap this closes
-------------------
The friction horse race has always compared two different books. Cost and capacity drags were
measured on the decile-spread book (the only one with an uncapped counterfactual) while tax drag was
measured on the optimised book (because the lot-level engine runs on realised weights). The
resulting table compares orders of magnitude and cannot be read as a decomposition that sums. A
reviewer is right to say so.

The tax engine runs on *any* weight history, so the fix is to feed it the decile weights. For each
of the two decile books - uncapped and participation-capped - this runs the identical
``after_tax_backtest`` twice, once under the zero-tax control regime and once under the country's
statutory regime, on identical dates and an identical investable universe. Then the whole ladder
is on one book:

    gross  ->  net of cost  ->  after tax          (uncapped book)
    gross  ->  net of cost  ->  after tax          (capped book)

so that  cost channel, capacity channel and tax channel are all differences within or between rows
of ONE table.

Reconciliation, which is what makes the numbers trustworthy
-----------------------------------------------------------
The wedge tool already computes net returns for these same weights with its own cost code. The tax
backtest computes net returns with the pipeline's cost code. They should agree. If they do not, one
of the two has a different treatment (the likeliest candidate is how a held name that loses
cost-input coverage is handled: the wedge tool lets it exit, the pipeline freezes it). The tool
prints the discrepancy rather than hiding it.

What this does NOT establish
----------------------------
It establishes what taxes do to the existing decile strategies. It does not show that a tax-aware
optimiser improves them; that is a separate experiment with its own go/no-go rule.

Usage
-----
    python tools/exp_matched_book_accounting.py --country DEU IND JPN --aum 1e9
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts import intl, load_config  # noqa: E402
from alphacomb.tax import LotMethod, TaxConfig, after_tax_backtest, get_regime  # noqa: E402
from alphacomb.tax.statutory import statutory_regime  # noqa: E402
from alphacomb.validation.inference import newey_west_se, sharpe_difference_test  # noqa: E402

PERIODS = 12
AS_OF = "2016-06-30"


def sharpe(x) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    sd = x.std(ddof=1)
    return float(x.mean() / sd * np.sqrt(PERIODS)) if sd > 0 else float("nan")


def t_vs_zero(x) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    sd = x.std(ddof=1)
    if not sd > 0:
        return float("nan")
    return float(x.mean() / sd / float(newey_west_se(x / sd)))


def run_one(weights: pd.DataFrame, bundle, cfg, regime, aum: float) -> pd.DataFrame:
    tc = TaxConfig(regime=regime, lot_method=LotMethod("hifo"), accounting="accrual",
                   dividend_yield_annual=0.02, initial_nav=float(aum))
    return after_tax_backtest(weights, bundle, cfg, tc, 1.0)


def pick(frame: pd.DataFrame, *names: str) -> str:
    for n in names:
        if n in frame.columns:
            return n
    raise SystemExit(f"none of {names} in columns {list(frame.columns)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", nargs="+", default=["DEU", "IND", "JPN"])
    ap.add_argument("--aum", type=float, default=1e9)
    ap.add_argument("--tag", default="matched")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "matched_book")
    ap.add_argument("--overwrite", action="store_true",
        help="discard an earlier output written by a different run (or of unknown origin); by default such a collision is refused (alphacomb.output_guard)")
    a = ap.parse_args(argv)
    from alphacomb.output_guard import claim_run
    claim_run([a.out / f"matched_book_{a.aum:.0e}.csv"], a)      # before any work
    a.out.mkdir(parents=True, exist_ok=True)

    cfg0 = load_config("base")
    cfg = {**cfg0, "costs": {**cfg0["costs"], "aum_usd_2020": float(a.aum)}}
    allrows = []

    for country in a.country:
        wdir = ROOT / "outputs" / "decile_weights" / country / a.tag / f"aum_{a.aum:.0e}"
        if not wdir.exists():
            print(f"\n{country}: no weights at {wdir}; run the wedge tool with --dump-weights")
            continue
        bundle = intl.load_country_bundle(country, max_names=600)
        stat = statutory_regime(country, AS_OF)
        zero = get_regime("tax_exempt")
        wmon = ROOT / "outputs" / "signal_vs_portfolio" / f"monthly_{country}_{a.tag}.csv"
        wedge = pd.read_csv(wmon, parse_dates=["date"]) if wmon.exists() else None

        print(f"\n{'='*92}\n{country}  -  MATCHED-BOOK ACCOUNTING at AUM {a.aum:.0e}   "
              f"(statutory: {stat.name}, wedge {stat.rate_spread:.3f})\n{'='*92}")

        per_book = {}
        for book in ("uncapped", "capped"):
            files = sorted(wdir.glob(f"{book}_*.parquet"))
            if len(files) != 8:
                print(f"  {book}: expected 8 prediction cells, found {len(files)}")
                continue
            series = {k: [] for k in ("gross", "net", "after_tax")}
            recon = []
            insolvent = []
            for f in files:
                cell = f.stem.split("_", 1)[1]
                w = pd.read_parquet(f)
                fz = run_one(w, bundle, cfg, zero, a.aum)
                fs = run_one(w, bundle, cfg, stat, a.aum)
                n_dates = w["date"].nunique()
                if len(fz) < n_dates or len(fs) < n_dates:
                    # after_tax_backtest stops the moment NAV reaches zero. A book whose first
                    # months cost more than 100% of NAV is not a strategy with a bad Sharpe; it is
                    # an account that no longer exists, and there is nothing left to tax.
                    insolvent.append((cell, min(len(fz), len(fs)), n_dates))
                    continue
                gcol = pick(fz, "gross_ret", "gross_return")
                ncol = pick(fz, "net_ret", "net_return")
                tcol = pick(fs, "after_tax_ret", "after_tax_return")
                dz = fz.set_index("date")
                ds = fs.set_index("date")
                series["gross"].append(dz[gcol].rename(cell))
                series["net"].append(dz[ncol].rename(cell))
                series["after_tax"].append(ds[tcol].rename(cell))
                if wedge is not None:
                    ref = wedge[(wedge.cell == cell) & np.isclose(wedge.aum, a.aum)]
                    col = "net_ret_uncapped" if book == "uncapped" else "net_ret_capped"
                    if not ref.empty:
                        r = ref.set_index("date")[col]
                        j = dz[ncol].index.intersection(r.index)
                        recon.append(float(np.nanmax(np.abs(dz[ncol].loc[j] - r.loc[j]))))
            if insolvent:
                worst = min(m for _, m, _ in insolvent)
                print(f"  {book:8s} INSOLVENT: {len(insolvent)} of {len(files)} cells exhaust NAV "
                      f"(shortest survives {worst} of {insolvent[0][2]} months). "
                      f"The counterfactual is not a feasible account at this AUM.")
            if not series["gross"]:
                continue
            if insolvent:
                print(f"           the remaining {len(series['gross'])} cells are not comparable "
                      f"with an 8-cell composite and are not reported.")
                continue
            per_book[book] = {k: pd.concat(v, axis=1).dropna().mean(axis=1)
                              for k, v in series.items()}
            if recon:
                print(f"  {book:8s} reconciliation vs wedge tool net return: "
                      f"max |diff| over months/cells = {max(recon):.3e} "
                      f"(median across cells {np.median(recon):.3e})")

        if not per_book:
            continue
        print(f"\n  {'':10s} {'SR gross':>9} {'SR net':>9} {'SR after tax':>13} "
              f"{'cost ch':>9} {'tax ch':>9} {'t(tax ch)':>10} {'SR net t':>9}")
        for book in ("uncapped", "capped"):
            if book not in per_book:
                continue
            b = per_book[book]
            idx = b["gross"].index.intersection(b["net"].index).intersection(b["after_tax"].index)
            g, n, t = b["gross"].loc[idx], b["net"].loc[idx], b["after_tax"].loc[idx]
            rr = sharpe_difference_test(t.to_numpy(), n.to_numpy(), periods=PERIODS,
                                        n_boot=a.n_boot, block=6, seed=0)
            print(f"  {book:10s} {sharpe(g):+9.3f} {sharpe(n):+9.3f} {sharpe(t):+13.3f} "
                  f"{sharpe(n)-sharpe(g):+9.3f} {rr.statistic:+9.3f} "
                  f"{rr.detail['studentized']:+10.2f} {t_vs_zero(n):+9.2f}")
            allrows.append({"country": country, "aum": a.aum, "book": book,
                            "sharpe_gross": sharpe(g), "sharpe_net": sharpe(n),
                            "sharpe_after_tax": sharpe(t), "cost_channel": sharpe(n) - sharpe(g),
                            "tax_channel": rr.statistic, "tax_t": rr.detail["studentized"],
                            "tax_p": rr.p_value, "net_t_vs_zero": t_vs_zero(n),
                            "months": len(idx)})
        if "uncapped" in per_book and "capped" in per_book:
            u, c = per_book["uncapped"], per_book["capped"]
            cap_ch = sharpe(c["net"]) - sharpe(u["net"])
            print(f"\n  capacity channel (net capped - net uncapped): {cap_ch:+.3f}")
            print(f"  ONE-BOOK LADDER:  cost {allrows[-2]['cost_channel']:+.3f}   "
                  f"capacity {cap_ch:+.3f}   tax(capped) {allrows[-1]['tax_channel']:+.3f}")
        else:
            print("\n  capacity channel not computable: the uncapped book is insolvent here, so "
                  "only the executable (capped) book is accounted.")

    if allrows:
        d = pd.DataFrame(allrows)
        p = a.out / f"matched_book_{a.aum:.0e}.csv"
        d.to_csv(p, index=False)
        print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
