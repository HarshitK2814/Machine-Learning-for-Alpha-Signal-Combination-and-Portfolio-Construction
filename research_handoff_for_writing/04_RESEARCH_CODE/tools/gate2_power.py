#!/usr/bin/env python
"""Gate 2 pre-estimate: how large an improvement could a paired test detect on the OPTIMISED book?

Why
---
The proposal assumed a paired standard error of 0.10 Sharpe points, and under that assumption
recovering 30% of the gross-to-net gap is roughly t = 1. The only empirical paired standard errors
we had were measured on the decile-spread book (median 0.22, which would make even full recovery of
the gap undetectable). The decile book is nearly empty at institutional AUM, so that may overstate
the noise of the book an investor actually runs. This measures the paired SE on the optimised book
with the same instrument used everywhere else (`sharpe_difference_test`).

What it does
------------
For each country, at the given AUM, take the optimised weights of the 8 prediction cells, run them
through the pipeline's own `after_tax_backtest` under the zero-tax control, and for each of the
three design axes compare the equal-weighted composite of the 4 cells at one level against the 4 at
the other, exactly as `exp_design_identifiability.py` does. The HAC standard error of each paired
Sharpe difference is the quantity a promotion test would have to beat.

It then converts the median SE into the minimum detectable effect (5% two-sided, and 80% power) for
132 months and for the 72 months a 2020-2025 extension would supply, and compares that with the
recoverable ceiling (the optimised-book gross-to-net Sharpe gap).

Usage
-----
    python tools/gate2_power.py --country DEU IND JPN --aum 1e9
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from alphacomb.contracts import intl, load_config, read_table  # noqa: E402
from alphacomb.tax import LotMethod, TaxConfig, after_tax_backtest, get_regime  # noqa: E402
from alphacomb.validation.inference import sharpe_difference_test  # noqa: E402

AXES = {"representation": (0, "N", "L"), "conditioning": (1, "C", "S"), "uncertainty": (3, "U", "0")}
PERIODS = 12


def sharpe(x) -> float:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    sd = x.std(ddof=1)
    return float(x.mean() / sd * np.sqrt(PERIODS)) if sd > 0 else float("nan")


def cell_frames(country: str, aum: float) -> dict[str, pd.DataFrame]:
    cfg0 = load_config("base")
    cfg = {**cfg0, "costs": {**cfg0["costs"], "aum_usd_2020": float(aum)}}
    bundle = intl.load_country_bundle(country, max_names=600)
    tag = f"{aum:.0e}".replace("e+0", "e").replace("e+", "e")
    idx = pd.read_csv(ROOT / "outputs" / "weights_index" / f"{country}_{tag}.csv")
    idx = idx[idx.strategy.str.contains("-P-")]
    tc = TaxConfig(regime=get_regime("tax_exempt"), lot_method=LotMethod("hifo"),
                   accounting="accrual", dividend_yield_annual=0.02, initial_nav=float(aum))
    out = {}
    for _, r in idx.iterrows():
        out[str(r.strategy).removeprefix("cell_")] = after_tax_backtest(
            read_table(Path(r.weights), "weights"), bundle, cfg, tc, 1.0)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", nargs="+", default=["DEU", "IND", "JPN"])
    ap.add_argument("--aum", type=float, default=1e9)
    ap.add_argument("--n-boot", type=int, default=800)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "gate2")
    ap.add_argument("--overwrite", action="store_true",
        help="discard an earlier output written by a different run (or of unknown origin); by default such a collision is refused (alphacomb.output_guard)")
    a = ap.parse_args(argv)
    from alphacomb.output_guard import claim_run
    claim_run([a.out / f"gate2_power_{a.aum:.0e}.csv"], a)
    a.out.mkdir(parents=True, exist_ok=True)

    rows = []
    for c in a.country:
        fr = cell_frames(c, a.aum)
        if len(fr) != 8:
            print(f"{c}: expected 8 prediction cells, found {len(fr)}")
            continue
        net = pd.concat({k: v.set_index("date")["net_ret"] for k, v in fr.items()}, axis=1).dropna()
        gross = pd.concat({k: v.set_index("date")["gross_ret"] for k, v in fr.items()}, axis=1).dropna()
        sr_net, sr_gross = sharpe(net.mean(axis=1)), sharpe(gross.mean(axis=1))
        print(f"\n{c} at AUM {a.aum:.0e}: composite gross SR {sr_gross:+.3f}, net SR {sr_net:+.3f}, "
              f"gross-to-net gap {sr_gross - sr_net:.3f}   ({len(net)} months)")
        for axis, (pos, hi, lo) in AXES.items():
            ca = [k for k in net.columns if k.split("-")[pos] == hi]
            cb = [k for k in net.columns if k.split("-")[pos] == lo]
            r = sharpe_difference_test(net[ca].mean(axis=1).to_numpy(), net[cb].mean(axis=1).to_numpy(),
                                       periods=PERIODS, n_boot=a.n_boot, block=6, seed=0)
            rows.append({"country": c, "aum": a.aum, "axis": axis, "effect": r.statistic,
                         "se": r.detail["se_hac"], "t": r.detail["studentized"],
                         "gap": sr_gross - sr_net, "months": len(net)})
            print(f"   {axis:<15} effect {r.statistic:+.3f}   paired HAC SE {r.detail['se_hac']:.3f}"
                  f"   t {r.detail['studentized']:+.2f}")
    if not rows:
        return 1
    d = pd.DataFrame(rows)
    d.to_csv(a.out / f"gate2_power_{a.aum:.0e}.csv", index=False)

    print(f"\n{'='*86}\nMINIMUM DETECTABLE EFFECT (paired Sharpe difference)\n{'='*86}")
    print(f"  {'':10s}{'median SE':>10}  {'MDE 5% @132m':>13}{'80% pwr @132m':>14}"
          f"{'MDE 5% @72m':>13}{'80% pwr @72m':>13}  {'recoverable gap':>16}")
    for c, g in d.groupby("country"):
        se = float(g.se.median())
        s72 = se * np.sqrt(132 / 72)
        gap = float(g.gap.iloc[0])
        print(f"  {c:<10}{se:>10.3f}  {1.96*se:>13.3f}{(1.96+0.8416)*se:>14.3f}"
              f"{1.96*s72:>13.3f}{(1.96+0.8416)*s72:>13.3f}  {gap:>16.3f}")
    print("\n  Gate 2 passes for a market only if the 80%-power MDE at 72 months is BELOW the recoverable")
    print("  gap AND below any improvement that is economically plausible. A 30% recovery of the gap is")
    print("  the planning figure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
