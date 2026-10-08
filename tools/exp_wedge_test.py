#!/usr/bin/env python
"""The paper's headline test: is the friction penalty ordered by the holding-period wedge?

The claim
---------
    The friction penalty on a machine-learning design is ordered by each country's statutory
    holding-period wedge, not by its transaction tax, and is identically zero in jurisdictions
    whose law sets a flat capital-gains rate.

The theory (``alphacomb.theory.tax_model``) gives, for a strategy at turnover ``p`` under a
realisation-based tax with boundary ``H`` and wedge ``Delta = theta_S - theta_L``:

    R(p) = g(1 - theta_L) - kappa*p - g * Delta * Phi(p, H)

so the tax paid per unit of gross return is

    tax_drag / gross  ~  theta_L  +  Delta * Phi(p, H)
                         ^^^^^^^     ^^^^^^^^^^^^^^^^
                         level       holding-period channel, PROPORTIONAL TO THE WEDGE

Two regimes, two predictions, and they differ in a way no level effect can mimic:

* **Flat-rate country (Delta = 0).** The second term vanishes identically. The tax bill is
  ``theta_L`` times gains and **cannot** depend on turnover, however fast the strategy trades.
  Germany and Japan are this case - placebos written by the tax code, not constructed by us.
* **Wedge country (Delta > 0).** The second term is increasing in turnover, because trading faster
  moves gains across the holding-period boundary and converts them from the long-term rate to the
  short-term one. India is this case, with Delta = 0.15 and H = 12 months.

So the test is the **slope of tax-per-unit-of-gain on turnover**, by country. It should be
indistinguishable from zero in Germany and Japan and positive in India. Germany is the sharp
control: it taxes gains at 26.375%, *harder* than India's 15% short-term rate, so a "high taxes
punish high turnover" story predicts Germany suffers most while the wedge story predicts Germany
suffers nothing. The two accounts are opposed rather than nested.

Falsification, fixed in advance by ``REFRAMED_CLAIM.md``: if the penalty tracks the transaction tax
instead of the wedge, or if Germany and Japan show the same slope as India, the claim is wrong.

    python tools/exp_wedge_test.py --inputs outputs/summary_after_tax_DEU_1e9.csv \
                                            outputs/summary_after_tax_IND_1e9.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.tax.statutory import statutory_regime  # noqa: E402
from alphacomb.validation.inference import newey_west_se  # noqa: E402


def ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    """Coefficients and heteroskedasticity-robust (HC1) standard errors."""
    n, k = X.shape
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = (X * (resid ** 2)[:, None]).T @ X
    dof = max(n - k, 1)
    cov = XtX_inv @ meat @ XtX_inv * (n / dof)
    return beta, np.sqrt(np.clip(np.diag(cov), 0, None)), n


def country_test(d: pd.DataFrame, country: str, as_of: str) -> dict:
    """Slope of tax-per-unit-of-gain on turnover for one country's cells."""
    reg = statutory_regime(country, as_of)
    t = d[(d["regime"] != "tax_exempt")].copy()
    # Tax paid per unit of gross return. Cells whose gross return is near zero cannot inform a
    # ratio, so they are dropped rather than allowed to produce an arbitrary quotient.
    t = t[t["gross_mean_ann"].abs() > 1e-4].copy()
    t["tax_per_gain"] = (t["tax_drag_ann_bps"] / 1e4) / t["gross_mean_ann"]
    t = t[np.isfinite(t["tax_per_gain"])]
    if len(t) < 5:
        return {"country": country, "n": len(t), "error": "too few usable cells"}

    y = t["tax_per_gain"].to_numpy(dtype=float)
    p = t["turnover_mean"].to_numpy(dtype=float)
    X = np.c_[np.ones_like(p), p]
    beta, se, n = ols(y, X)
    tstat = beta[1] / se[1] if se[1] > 0 else np.nan
    return {
        "country": country,
        "regime": reg.name,
        "wedge": reg.rate_spread,
        "statutory_long_rate": reg.long_term_rate,
        "boundary_months": reg.long_term_months,
        "n_cells": int(n),
        "intercept": float(beta[0]),
        "slope_on_turnover": float(beta[1]),
        "slope_se": float(se[1]),
        "slope_t": float(tstat),
        "slope_significant_5pct": bool(abs(tstat) > 1.96) if np.isfinite(tstat) else False,
        "mean_tax_per_gain": float(np.mean(y)),
        "mean_tax_drag_bps": float(t["tax_drag_ann_bps"].mean()),
        "mean_cost_drag_bps": float(t["cost_drag_ann_bps"].mean()),
        "mean_lt_share_of_gains": float(t["lt_share_of_gains"].mean()),
        "turnover_range": f"{p.min():.4f}-{p.max():.4f}",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", nargs="+", required=True,
                    help="stage-06 summary CSVs, one per country (each must carry a 'country' col)")
    ap.add_argument("--as-of", default="2016-06-30")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "wedge_test")
    args = ap.parse_args(argv)

    frames = []
    for path in args.inputs:
        p = Path(path)
        if not p.exists():
            print(f"skipping missing {p}")
            continue
        d = pd.read_csv(p)
        if "country" not in d.columns or not d["country"].notna().any():
            print(f"skipping {p}: no country column (run stage 06 with --country)")
            continue
        frames.append(d)
    if not frames:
        print("no usable country summaries supplied")
        return 2

    rows = []
    for d in frames:
        for country in sorted(set(d["country"].dropna()) - {""}):
            rows.append(country_test(d[d["country"] == country], country, args.as_of))
    res = pd.DataFrame(rows)

    args.out.mkdir(parents=True, exist_ok=True)
    res.to_csv(args.out / "wedge_test.csv", index=False)

    print("=" * 96)
    print("THE WEDGE TEST: does tax-per-unit-of-gain rise with turnover, and only where a wedge exists?")
    print("=" * 96)
    cols = ["country", "wedge", "boundary_months", "n_cells", "intercept", "slope_on_turnover",
            "slope_t", "slope_significant_5pct", "mean_tax_drag_bps", "mean_cost_drag_bps"]
    cols = [c for c in cols if c in res.columns]
    print(res[cols].to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

    if "wedge" in res and len(res) > 1 and res["wedge"].notna().all():
        print()
        zero = res[res["wedge"] == 0.0]
        pos = res[res["wedge"] > 0.0]
        for _, r in zero.iterrows():
            verdict = ("CONSISTENT with the placebo" if not r["slope_significant_5pct"]
                       else "AGAINST the placebo")
            print(f"  {r['country']} (wedge {r['wedge']:.3f}): slope {r['slope_on_turnover']:+.4f} "
                  f"t={r['slope_t']:+.2f} -> {verdict}")
        for _, r in pos.iterrows():
            verdict = ("CONSISTENT with the wedge channel" if r["slope_on_turnover"] > 0
                       else "AGAINST the wedge channel")
            print(f"  {r['country']} (wedge {r['wedge']:.3f}): slope {r['slope_on_turnover']:+.4f} "
                  f"t={r['slope_t']:+.2f} -> {verdict}")
        if len(zero) and len(pos):
            print()
            print(f"  ordering: max |slope| among flat-rate countries "
                  f"{zero['slope_on_turnover'].abs().max():.4f} vs wedge country "
                  f"{pos['slope_on_turnover'].max():.4f}")
            if pos["slope_on_turnover"].max() > zero["slope_on_turnover"].abs().max():
                print("  The wedge country's turnover slope exceeds every flat-rate country's.")
                print("  That is the predicted ordering, and a tax-LEVEL story cannot produce it:")
                print("  Germany is taxed harder than India and still shows the smaller slope.")
            else:
                print("  PREDICTED ORDERING NOT OBTAINED - the claim as written is not supported.")
    print(f"\nwrote {args.out / 'wedge_test.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
