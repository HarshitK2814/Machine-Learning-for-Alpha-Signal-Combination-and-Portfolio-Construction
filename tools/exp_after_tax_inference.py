#!/usr/bin/env python
"""Is the after-tax Sharpe significantly different from the net Sharpe, and is it below zero?

Why this matters
----------------
The three-country tax result says taxes are second-order as a *channel* and first-order for
*survival*: India keeps 98% of its net Sharpe after tax, Germany 14%, and **Japan's book goes
negative** (+0.057 -> -0.049). That is the strongest claim available to this project, because it
would mean the viability of a machine-learning equity strategy at institutional scale is decided by
capital-gains statute rather than by the model.

But it is currently a comparison of point estimates, and Japan's net Sharpe (+0.057) is small enough
that "goes negative" could be noise moving to noise. **If the tax channel is not significant, the
claim is not a claim.** This tool decides it.

What it measures
----------------
For each country, from the monthly after-tax frames produced by the same `after_tax_backtest` the
pipeline uses (so there is no second implementation to drift):

1. the **tax channel**, `SR(after tax) - SR(net)`, with the paired studentized bootstrap - paired
   because the two series are the same months of the same book differing only by the tax ledger,
   which is about as dependent as two series get;
2. whether the **after-tax Sharpe is significantly below zero**, via a one-sided HAC test on the
   after-tax series itself;
3. the same for the **net** Sharpe, so the reader can see whether the book was viable *before* tax.

Composite across the 8 prediction cells (one equal-weighted book), and per cell with Holm.

Usage
-----
    python tools/exp_after_tax_inference.py --country DEU IND JPN --aum 1e9
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts import intl, load_config, read_table  # noqa: E402
from alphacomb.tax import LotMethod, TaxConfig, after_tax_backtest  # noqa: E402
from alphacomb.tax.statutory import statutory_regime  # noqa: E402
from alphacomb.validation.inference import newey_west_se, sharpe_difference_test  # noqa: E402

PERIODS = 12
# The regime is derived from the frozen C14 schedule rather than hardcoded, exactly as stage 06
# does it, so this tool cannot drift from the pipeline's notion of each country's statute.
AS_OF = "2016-06-30"


def holm(p: dict[str, float]) -> dict[str, float]:
    items = sorted(((k, v) for k, v in p.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out = {k: float("nan") for k in p}
    run = 0.0
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - i) * v))
        out[k] = run
    return out


def sharpe_vs_zero(x: np.ndarray) -> tuple[float, float, float]:
    """Annualised Sharpe, its HAC t statistic, and a two-sided p value.

    The t statistic on a Sharpe ratio is the t statistic on the mean when the series is scaled by
    its own standard deviation, so a HAC standard error of the mean of ``x/sd`` is the right thing
    and it inherits the autocorrelation correction.
    """
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    sd = x.std(ddof=1)
    if not sd > 0:
        return float("nan"), float("nan"), float("nan")
    sr = float(x.mean() / sd * np.sqrt(PERIODS))
    se = float(newey_west_se(x / sd)) * np.sqrt(PERIODS)
    if not se > 0:
        return sr, float("nan"), float("nan")
    t = sr / se
    from scipy import stats
    return sr, float(t), float(2.0 * stats.norm.sf(abs(t)))


def frames_for(country: str, aum: float, n_boot: int, seed: int) -> pd.DataFrame:
    cfg = load_config("base")
    cfg = {**cfg, "costs": {**cfg["costs"], "aum_usd_2020": float(aum)}}
    bundle = intl.load_country_bundle(country, max_names=600)
    tag = f"{aum:.0e}".replace("e+0", "e").replace("e+", "e")
    index = ROOT / "outputs" / "weights_index" / f"{country}_{tag}.csv"
    if not index.exists():
        raise SystemExit(f"no weights index at {index}")
    idx = pd.read_csv(index)
    idx = idx[idx.strategy.str.contains("-P-")]
    if idx.empty:
        raise SystemExit(f"{country}: no prediction cells in {index.name}")

    reg = statutory_regime(country, AS_OF)
    tc = TaxConfig(regime=reg, lot_method=LotMethod("hifo"),
                   accounting="accrual", dividend_yield_annual=0.02, initial_nav=float(aum))
    print(f"  {country} statutory regime: {reg.name}  short={reg.short_term_rate:.5f} "
          f"long={reg.long_term_rate:.5f} wedge={reg.rate_spread:.5f}")
    out = []
    for _, r in idx.iterrows():
        w = read_table(Path(r.weights), "weights")
        f = after_tax_backtest(w, bundle, cfg, tc, 1.0)
        f = f.copy()
        f["cell"] = str(r.strategy).removeprefix("cell_")
        out.append(f)
    return pd.concat(out, ignore_index=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", nargs="+", default=["DEU", "IND", "JPN"])
    ap.add_argument("--aum", type=float, default=1e9)
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--block", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "after_tax_inference")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)

    rows = []
    for c in a.country:
        try:
            fr = frames_for(c, a.aum, a.n_boot, a.seed)
        except SystemExit as exc:
            print(f"\n{c}: SKIPPED - {exc}")
            continue
        netcol = "net_ret" if "net_ret" in fr.columns else "net_return"
        taxcol = ("after_tax_ret" if "after_tax_ret" in fr.columns
                  else "after_tax_return" if "after_tax_return" in fr.columns else None)
        if taxcol is None:
            print(f"{c}: columns are {list(fr.columns)}")
            raise SystemExit("cannot find the after-tax return column")

        piv_n = fr.pivot_table(index="date", columns="cell", values=netcol).dropna()
        piv_t = fr.pivot_table(index="date", columns="cell", values=taxcol).dropna()
        idx = piv_n.index.intersection(piv_t.index)
        net, tax = piv_n.loc[idx].mean(axis=1), piv_t.loc[idx].mean(axis=1)

        r = sharpe_difference_test(tax.to_numpy(), net.to_numpy(), periods=PERIODS,
                                   n_boot=a.n_boot, block=a.block, seed=a.seed)
        sr_n, t_n, p_n = sharpe_vs_zero(net.to_numpy())
        sr_t, t_t, p_t = sharpe_vs_zero(tax.to_numpy())

        print(f"\n{'='*86}\n{c}  -  AFTER-TAX INFERENCE at AUM {a.aum:.0e} "
              f"({len(idx)} months, {piv_n.shape[1]} prediction cells)\n{'='*86}")
        print(f"  net Sharpe        {sr_n:+.4f}   t = {t_n:+.2f}   p = {p_n:.4f}"
              f"   {'(viable)' if sr_n > 0 and p_n < 0.05 else '(not distinguishable from zero)' if sr_n > 0 else '(negative)'}")
        print(f"  after-tax Sharpe  {sr_t:+.4f}   t = {t_t:+.2f}   p = {p_t:.4f}")
        print(f"  tax channel       {r.statistic:+.4f}   t = {r.detail['studentized']:+.2f}"
              f"   p = {r.p_value:.4f}   95% CI "
              f"[{r.detail['ci95_low']:+.4f}, {r.detail['ci95_high']:+.4f}]"
              f"   {'SIGNIFICANT' if r.p_value < 0.05 else 'not significant'}")

        pv, per = {}, []
        for cell in piv_n.columns:
            rc = sharpe_difference_test(piv_t[cell].loc[idx].to_numpy(),
                                        piv_n[cell].loc[idx].to_numpy(), periods=PERIODS,
                                        n_boot=min(a.n_boot, 800), block=a.block, seed=a.seed)
            pv[cell] = rc.p_value
            per.append({"country": c, "aum": a.aum, "scope": "cell", "cell": cell,
                        "tax_channel": rc.statistic, "t": rc.detail["studentized"],
                        "p": rc.p_value})
        adj = holm(pv)
        for d in per:
            d["p_holm"] = adj.get(d["cell"], np.nan)
        nsig = sum(1 for d in per if d["p_holm"] < 0.05)
        print(f"  per-cell tax channel significant after Holm: {nsig} of {len(per)}")

        rows.append({"country": c, "aum": a.aum, "scope": "composite", "cell": "ALL",
                     "months": len(idx), "sharpe_net": sr_n, "t_net": t_n, "p_net": p_n,
                     "sharpe_after_tax": sr_t, "t_after_tax": t_t, "p_after_tax": p_t,
                     "tax_channel": r.statistic, "t": r.detail["studentized"], "p": r.p_value,
                     "ci95_low": r.detail["ci95_low"], "ci95_high": r.detail["ci95_high"],
                     "cells_holm_sig": nsig, "n_cells": len(per)})
        rows.extend(per)

    if rows:
        d = pd.DataFrame(rows)
        tag = f"{a.aum:.0e}".replace("e+0", "e").replace("e+", "e")
        p = a.out / f"after_tax_inference_{tag}.csv"
        d.to_csv(p, index=False)
        print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
