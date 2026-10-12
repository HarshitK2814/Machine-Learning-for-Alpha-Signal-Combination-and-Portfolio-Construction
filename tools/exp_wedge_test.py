#!/usr/bin/env python
"""The wedge test: does the holding-period channel operate, and only where a boundary exists?

The claim under test (``research/05_Selected_Research_Design/REFRAMED_CLAIM.md``)
-------------------------------------------------------------------------------
    The friction penalty on a machine-learning design is ordered by each country's statutory
    holding-period wedge, not by its transaction tax, and is identically zero in jurisdictions
    whose law sets a flat capital-gains rate.

The theory (``alphacomb.theory.tax_model``) gives, for a strategy at turnover ``p`` under a
realisation-based tax with boundary ``H`` and wedge ``Delta = theta_S - theta_L``:

    R(p) = g(1 - theta_L) - kappa*p - g * Delta * Phi(p, H)

    tax_drag / gross  ~  theta_L  +  Delta * Phi(p, H)
                         level       holding-period channel, proportional to the wedge

``Phi(p, H)`` is the share of gains pushed across the boundary by trading at rate ``p``.

Four statistics, and why there are four
---------------------------------------
1. **The pre-registered statistic**: slope of ``tax_drag / gross`` on turnover. It is reported
   first and unchanged, because it is what was registered. **It is also not trustworthy on this
   data**, and the tool says so rather than letting a reader take it at face value. Roughly half
   the cells in every country run so far have a *negative* mean gross return - the economic-loss
   cells lose money - so the denominator changes sign across the sample and "tax per unit of gain"
   is being computed for cells that have no gains. The statistic's sign flips with specification:
   on Germany it is -21.99 across all cells and +11.56 on the cells with gains.
2. **The same ratio restricted to cells with ``gross > 0``**, where it is at least well defined.
3. **Levels**: ``tax_drag_bps`` on turnover controlling for gross return, which avoids the ratio
   altogether. Weakly identified, because turnover and gross return are nearly collinear across
   the sixteen cells (corr about -0.8 to -0.9: the cells that trade fastest are the ones that lose
   money), so this is reported for completeness rather than as evidence.
4. **The mechanism, measured directly**: ``lt_share_of_gains`` on turnover. This is
   ``1 - Phi(p, H)`` as the ledger actually realised it, so it tests the holding-period channel
   without routing through a money quantity that the loss-making cells and a zero long-term rate
   both distort. **This is post-hoc**: it was promoted to primary after the registered statistic
   was found to be ill-defined. It is not a new measurement - ``lt_share_of_gains`` is a frozen
   column of the stage-06 report and is the theory's own ``Phi`` - but the decision to lead with it
   was taken after seeing (1) fail, and the write-up must say so.

What a flat-rate country does to statistic 4 is the sharpest form of the placebo: ``lt_share`` is
not merely small there, it is **identically zero in every cell**, because with no holding-period
boundary there is no long-term category for a gain to fall into. The variable the mechanism works
through does not exist. Germany is the sharp control because it taxes gains at 26.375%, *harder*
than India's 15% short-term rate, so a "high taxes punish high turnover" story predicts Germany
suffers most while the wedge story predicts the channel is absent there entirely.

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


def slope_on(y: np.ndarray, p: np.ndarray, *, extra: np.ndarray | None = None) -> tuple:
    """Slope of ``y`` on turnover ``p``, optionally controlling for ``extra``."""
    cols = [np.ones_like(p), p] + ([extra] if extra is not None else [])
    beta, se, n = ols(y, np.column_stack(cols))
    t = beta[1] / se[1] if se[1] > 0 else np.nan
    return float(beta[1]), float(se[1]), float(t), n


def country_test(d: pd.DataFrame, country: str, as_of: str) -> dict:
    """Every statistic for one country's cells, with the pre-registered one first."""
    reg = statutory_regime(country, as_of)
    t = d[d["regime"] != "tax_exempt"].copy()
    # Only the factorial cells. A comparator has a different turnover for reasons unrelated to the
    # design axes, so mixing them in would change what the slope is a slope of.
    t = t[t["strategy"].str.startswith("cell_")]
    t = t[t["gross_mean_ann"].abs() > 1e-4].copy()
    if len(t) < 5:
        return {"country": country, "n_cells": len(t), "error": "too few usable cells"}

    p = t["turnover_mean"].to_numpy(dtype=float)
    g = t["gross_mean_ann"].to_numpy(dtype=float)
    tax_bps = t["tax_drag_ann_bps"].to_numpy(dtype=float)
    lt = t["lt_share_of_gains"].to_numpy(dtype=float)
    ratio = (tax_bps / 1e4) / g

    out: dict = {
        "country": country,
        "regime": reg.name,
        "wedge": reg.rate_spread,
        "statutory_long_rate": reg.long_term_rate,
        "boundary_months": reg.long_term_months,
        "n_cells": int(len(t)),
        "n_cells_with_gains": int((g > 0).sum()),
        "corr_turnover_gross": float(np.corrcoef(p, g)[0, 1]),
        "mean_tax_drag_bps": float(tax_bps.mean()),
        "mean_cost_drag_bps": float(t["cost_drag_ann_bps"].mean()),
        "turnover_range": f"{p.min():.4f}-{p.max():.4f}",
    }

    # (1) the pre-registered statistic, computed exactly as registered
    b, se, tt, _ = slope_on(ratio, p)
    out.update(prereg_slope=b, prereg_se=se, prereg_t=tt,
               prereg_significant_5pct=bool(abs(tt) > 1.96) if np.isfinite(tt) else False,
               # The registered statistic is only well defined if every cell has gains to divide by.
               prereg_well_defined=bool((g > 0).all()))

    # (2) the ratio where it is defined
    m = g > 0
    if m.sum() >= 5:
        b2, se2, t2, _ = slope_on(ratio[m], p[m])
        out.update(ratio_gains_only_slope=b2, ratio_gains_only_t=t2,
                   ratio_gains_only_n=int(m.sum()))
    else:
        out.update(ratio_gains_only_slope=np.nan, ratio_gains_only_t=np.nan,
                   ratio_gains_only_n=int(m.sum()))

    # (3) levels, controlling for gross
    b3, se3, t3, _ = slope_on(tax_bps, p, extra=g)
    out.update(tax_level_slope=b3, tax_level_t=t3)

    # (4a) The factorial's two objective arms occupy DISJOINT turnover ranges - the economic-loss
    # cells all trade several times faster than every prediction-loss cell - so a slope fitted
    # across all sixteen is a comparison of two tight clusters, not a gradient, and its n is
    # effectively two. Worse, the high-turnover cluster is the arm with negative GROSS Sharpe in
    # both countries, i.e. the one that failed to train. The within-arm slopes are therefore
    # computed and reported alongside, and the full-sample slope must never be read without them.
    arm = t["strategy"].str.extract(r"cell_[LN]-[SC]-([PE])-")[0].to_numpy()
    for label in ("P", "E"):
        m = arm == label
        key = f"lt_share_slope_{label}_only"
        if m.sum() < 4 or np.nanstd(lt[m]) < 1e-12:
            out[key], out[f"lt_share_t_{label}_only"] = np.nan, np.nan
        else:
            bb, _, tt2, _ = slope_on(lt[m], p[m])
            out[key], out[f"lt_share_t_{label}_only"] = bb, tt2
        out[f"turnover_range_{label}_only"] = (
            f"{p[m].min():.4f}-{p[m].max():.4f}" if m.any() else "")
    if (arm == "P").any() and (arm == "E").any():
        out["arms_turnover_overlap"] = bool(p[arm == "P"].max() >= p[arm == "E"].min())

    # (4) the mechanism: lt_share_of_gains on turnover
    degenerate = bool(np.nanstd(lt) < 1e-12)
    out["lt_share_degenerate"] = degenerate
    out["lt_share_mean"] = float(np.nanmean(lt))
    out["lt_share_range"] = f"{np.nanmin(lt):.4f}-{np.nanmax(lt):.4f}"
    if degenerate:
        # Not a slope of zero - no variation at all, because the category does not exist.
        out.update(lt_share_slope=0.0, lt_share_se=np.nan, lt_share_t=np.nan,
                   lt_share_significant_5pct=False,
                   corr_turnover_lt_share=np.nan)
    else:
        b4, se4, t4, _ = slope_on(lt, p)
        out.update(lt_share_slope=b4, lt_share_se=se4, lt_share_t=t4,
                   lt_share_significant_5pct=bool(abs(t4) > 1.96) if np.isfinite(t4) else False,
                   corr_turnover_lt_share=float(np.corrcoef(p, lt)[0, 1]))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", nargs="+", required=True,
                    help="stage-06 summary CSVs, one per country (each must carry a 'country' col)")
    ap.add_argument("--as-of", default="2016-06-30")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "wedge_test")
    ap.add_argument("--overwrite", action="store_true",
        help="discard an earlier output written by a different run (or of unknown origin); by default such a collision is refused (alphacomb.output_guard)")
    args = ap.parse_args(argv)
    from alphacomb.output_guard import claim_run
    claim_run([args.out / "wedge_test.csv"], args)

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

    fmt = lambda v: f"{v:,.4f}"  # noqa: E731
    print("=" * 104)
    print("THE WEDGE TEST")
    print("=" * 104)

    print("\n(1) PRE-REGISTERED: slope of tax-per-unit-of-gain on turnover")
    cols = [c for c in ["country", "wedge", "boundary_months", "n_cells", "n_cells_with_gains",
                        "prereg_slope", "prereg_t", "prereg_significant_5pct",
                        "prereg_well_defined"] if c in res.columns]
    print(res[cols].to_string(index=False, float_format=fmt))
    if "prereg_well_defined" in res and not res["prereg_well_defined"].all():
        bad = res.loc[~res["prereg_well_defined"], "country"].tolist()
        print(f"\n  *** THE PRE-REGISTERED STATISTIC IS NOT WELL DEFINED for {', '.join(bad)}. ***")
        print("  It divides tax paid by mean gross return, and these countries contain cells whose")
        print("  mean gross return is NEGATIVE - the economic-loss cells lose money - so the")
        print("  denominator changes sign across the sample and the quantity is 'tax per unit of")
        print("  gain' for cells that have no gains. Its sign is an artefact of that, not evidence.")
        for _, r in res[~res["prereg_well_defined"]].iterrows():
            print(f"    {r['country']}: {r['n_cells_with_gains']} of {r['n_cells']} cells have "
                  f"gross > 0; corr(turnover, gross) = {r['corr_turnover_gross']:+.3f}")

    print("\n(2) the same ratio, restricted to cells that have gains")
    cols = [c for c in ["country", "wedge", "ratio_gains_only_n", "ratio_gains_only_slope",
                        "ratio_gains_only_t"] if c in res.columns]
    print(res[cols].to_string(index=False, float_format=fmt))

    print("\n(3) levels: tax drag in bps on turnover, controlling for gross return")
    print("    weakly identified - turnover and gross return are nearly collinear across 16 cells")
    cols = [c for c in ["country", "wedge", "corr_turnover_gross", "tax_level_slope",
                        "tax_level_t", "mean_tax_drag_bps", "mean_cost_drag_bps"]
            if c in res.columns]
    print(res[cols].to_string(index=False, float_format=fmt))

    print("\n(4) THE MECHANISM (post-hoc primary): long-term share of gains on turnover")
    print("    this is 1 - Phi(p,H) as realised, the object the theory's wedge term acts on")
    cols = [c for c in ["country", "wedge", "boundary_months", "lt_share_range", "lt_share_slope",
                        "lt_share_t", "lt_share_significant_5pct", "corr_turnover_lt_share",
                        "lt_share_degenerate"] if c in res.columns]
    print(res[cols].to_string(index=False, float_format=fmt))

    print("\n(4b) THE SAME SLOPE, WITHIN EACH OBJECTIVE ARM - read this before believing (4)")
    print("     the two arms occupy disjoint turnover ranges, so a slope across all 16 cells is a")
    print("     two-cluster comparison with an effective n of 2, and the fast cluster is the arm")
    print("     with negative GROSS Sharpe in every country measured, i.e. the one that failed.")
    cols = [c for c in ["country", "lt_share_slope", "lt_share_t", "lt_share_slope_P_only",
                        "lt_share_t_P_only", "lt_share_slope_E_only", "lt_share_t_E_only",
                        "turnover_range_P_only", "turnover_range_E_only",
                        "arms_turnover_overlap"] if c in res.columns]
    print(res[cols].to_string(index=False, float_format=fmt))
    for _, r in res.iterrows():
        if r.get("lt_share_degenerate"):
            continue
        survives = (np.isfinite(r.get("lt_share_t_P_only", np.nan))
                    and abs(r["lt_share_t_P_only"]) > 1.96)
        if not survives:
            print(f"\n  *** {r['country']}: the full-sample slope does NOT survive within the")
            print(f"  prediction-loss arm (t = {r.get('lt_share_t_P_only', float('nan')):+.2f}). The")
            print("  full-sample figure is a between-arm artefact and must not be reported as a")
            print("  turnover gradient. What remains is the CROSS-COUNTRY contrast in the level of")
            print("  lt_share, which is a statutory fact and needs no regression.")

    print("\nREADING, by country:")
    for _, r in res.iterrows():
        if "error" in res.columns and isinstance(r.get("error"), str):
            print(f"  {r['country']}: {r['error']}")
            continue
        wedge = r["wedge"]
        if r["lt_share_degenerate"]:
            if wedge == 0.0:
                print(f"  {r['country']} (wedge {wedge:.3f}): lt_share is identically "
                      f"{r['lt_share_mean']:.4f} in all {r['n_cells']} cells. The holding-period "
                      f"category does not exist, so the channel cannot operate. PLACEBO HOLDS, and "
                      f"in the strongest form - no variation, not merely a small slope.")
            else:
                print(f"  {r['country']} (wedge {wedge:.3f}): lt_share is degenerate although a "
                      f"boundary of {r['boundary_months']}m exists. UNEXPECTED - investigate "
                      f"before reporting.")
        else:
            direction = "falls" if r["lt_share_slope"] < 0 else "rises"
            t_p = r.get("lt_share_t_P_only", float("nan"))
            # A full-sample slope only means something if it also holds inside an arm, because the
            # arms do not overlap in turnover. Without that, it is a two-cluster difference.
            within = bool(np.isfinite(t_p) and abs(t_p) > 1.96 and r["lt_share_slope_P_only"] < 0)
            if within:
                verdict = "CONSISTENT with the holding-period channel, and it survives within-arm"
            elif r["lt_share_slope"] < 0:
                verdict = (f"NOT ESTABLISHED as a turnover gradient - between-arm artefact "
                           f"(within prediction-loss arm t = {t_p:+.2f}); the cross-country "
                           f"LEVEL contrast is what stands")
            else:
                verdict = "AGAINST the channel - faster trading should not raise the long-term share"
            print(f"  {r['country']} (wedge {wedge:.3f}, boundary {r['boundary_months']}m): "
                  f"lt_share {direction} with turnover across all cells, slope "
                  f"{r['lt_share_slope']:+.3f} t={r['lt_share_t']:+.2f}, range "
                  f"{r['lt_share_range']} -> {verdict}")

    zero = res[res["wedge"] == 0.0]
    pos = res[res["wedge"] > 0.0]
    if len(zero) and len(pos):
        print("\nCROSS-COUNTRY ORDERING on the mechanism:")
        flat_degenerate = bool(zero["lt_share_degenerate"].all())
        t_p = pos.get("lt_share_t_P_only")
        wedge_within = bool(t_p is not None and t_p.notna().all()
                            and (t_p.abs() > 1.96).all()
                            and (pos["lt_share_slope_P_only"] < 0).all())
        print(f"  every flat-rate country has lt_share identically zero       : {flat_degenerate}")
        print(f"  every wedge country's gradient survives WITHIN an arm       : {wedge_within}")
        print("\n  WHAT STANDS: the cross-country contrast in the LEVEL of lt_share. It is")
        print("  identically 0.0000 in every flat-rate cell because the statute creates no")
        print(f"  long-term category, against {pos['lt_share_range'].iloc[0]} where it creates one.")
        print("  That is a statutory fact about which gains can exist, not an estimate, and a")
        print("  tax-LEVEL story cannot produce it: Germany is taxed at 26.375% against India's")
        print("  15% short-term rate and still has no holding-period category at all.")
        if not wedge_within:
            print("\n  WHAT DOES NOT STAND: the within-country turnover gradient. The objective")
            print("  arms occupy disjoint turnover ranges and the fast arm failed to train")
            print("  (negative gross Sharpe), so the full-sample slope is a two-cluster")
            print("  difference. It must not be reported as a turnover gradient.")
        print("\n  Note the magnitudes before calling this a large effect:")
        for _, r in res.iterrows():
            print(f"    {r['country']}: tax drag {r['mean_tax_drag_bps']:.2f} bps vs cost drag "
                  f"{r['mean_cost_drag_bps']:.2f} bps "
                  f"({r['mean_cost_drag_bps'] / max(abs(r['mean_tax_drag_bps']), 1e-9):.0f}x)")
    print(f"\nwrote {args.out / 'wedge_test.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
