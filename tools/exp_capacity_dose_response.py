#!/usr/bin/env python
"""Does the book stop tracking liquidity and start tracking alpha as AUM falls?

The capacity reframing (``docs/CANDIDATE_REFRAMING_CAPACITY.md``) claims that at $1bn the ADV
participation constraint, not the signal, determines the portfolio. A single AUM cannot establish
that — the claim is only a mechanism if it varies the right way when the dose varies. So for each
AUM arm this measures, per month and per cell, two cross-sectional correlations:

    corr(|w|, adv_cap)   where adv_cap_i = adv_usd_i * adv_participation_max / AUM
    corr(|w|, |score|)   the cell's own stage-02 signal

**The prediction, fixed before the arms were run.** As AUM falls the participation cap loosens, so
``corr(|w|, adv_cap)`` should fall and ``corr(|w|, |score|)`` should rise — the book should decouple
from liquidity and couple to the signal. If both are flat across two orders of magnitude of AUM,
the reframing is wrong and capacity is not what is binding.

At $1bn on the German panel the starting point is stark: position size correlates **+0.871 with the
ADV cap** and **−0.080 with alpha**. A liquidity-weighted index with a small alpha tilt.

Provenance: weights come from each arm's own ``outputs/weights_index/<C>_<aum>.csv`` and scores from
``outputs/source_index/<C>.csv``, never from modification time — the directories are shared across
countries and four separate tools were caught resolving the wrong country's artefacts in one night.

    python tools/exp_capacity_dose_response.py --country DEU --aum 1e8 1e9 1e10
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CELLS = [f"cell_{a}-{b}-{c}-{d}" for a in "LN" for b in "SC" for c in "PE" for d in "0U"]


def cross_sectional_corr(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 10:
        return np.nan
    if np.nanstd(x) < 1e-15 or np.nanstd(y) < 1e-15:
        return np.nan
    return float(np.corrcoef(x, y)[0, 1])


def arm_table(country: str, aum: float, scores: dict[str, pd.DataFrame],
              cost_inputs: pd.DataFrame, adv_participation_max: float) -> pd.DataFrame:
    """One row per (cell, month): how much of the book is explained by liquidity vs by signal."""
    from alphacomb.contracts import provenance, read_table

    tag = f"{aum:.0e}".replace("e+0", "e").replace("e+", "e")
    weights = provenance.country_weights(country, tag)
    rows = []
    for cell in CELLS:
        path = weights.get(cell)
        if path is None:
            continue
        w = read_table(path, "weights")
        wcol = "w" if "w" in w.columns else ("weight" if "weight" in w.columns else w.columns[-1])
        w = w[["date", "permno", wcol]].copy()
        w["date"] = pd.to_datetime(w["date"])
        w = w[np.abs(w[wcol]) > 1e-12]
        joined = w.merge(cost_inputs, on=["date", "permno"], how="left")
        sc = scores.get(cell)
        if sc is not None:
            joined = joined.merge(sc, on=["date", "permno"], how="left")
        for date, g in joined.groupby("date"):
            abs_w = np.abs(g[wcol].to_numpy(dtype=float))
            cap = g["adv_usd"].to_numpy(dtype=float) * adv_participation_max / aum
            ok = np.isfinite(cap) & np.isfinite(abs_w)
            row = {"cell": cell, "date": date, "aum": aum, "n": int(ok.sum()),
                   "gross": float(abs_w.sum()),
                   "corr_w_advcap": cross_sectional_corr(abs_w[ok], cap[ok]),
                   # Share of positions sitting AT their participation limit, which is the
                   # constraint actually binding rather than the one that was budgeted for.
                   "share_at_cap": float(np.mean(abs_w[ok] >= cap[ok] * 0.999)) if ok.sum() else np.nan}
            if "signal" in g.columns:
                s = np.abs(g["signal"].to_numpy(dtype=float))
                ok2 = np.isfinite(s) & np.isfinite(abs_w)
                row["corr_w_alpha"] = cross_sectional_corr(abs_w[ok2], s[ok2])
            rows.append(row)
    return pd.DataFrame(rows)


def load_scores(country: str) -> dict[str, pd.DataFrame]:
    """Each cell's own stage-02 output, pinned by country rather than by modification time."""
    from alphacomb.contracts import paths, read_table

    index = paths.outputs_root() / "source_index" / f"{country}.csv"
    if not index.exists():
        print(f"  no source index at {index}; alpha correlations will be omitted")
        return {}
    frame = pd.read_csv(index)
    out: dict[str, pd.DataFrame] = {}
    for _, r in frame.iterrows():
        strategy, kind, artefact = str(r["strategy"]), str(r["kind"]), Path(str(r["artefact"]))
        if not strategy.startswith("cell_") or not artefact.exists():
            continue
        f = read_table(artefact, kind)
        col = ("score" if "score" in f.columns
               else [c for c in f.columns if c not in ("date", "permno", "unc_sd")][0])
        d = f[["date", "permno", col]].rename(columns={col: "signal"}).copy()
        d["date"] = pd.to_datetime(d["date"])
        out[strategy] = d
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", default="DEU", choices=["DEU", "IND", "JPN"])
    ap.add_argument("--aum", nargs="+", type=float, default=[1e8, 1e9, 1e10])
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "capacity_dose_response")
    args = ap.parse_args(argv)

    from alphacomb.contracts import intl
    from alphacomb.contracts.provenance import MissingProvenance
    from alphacomb.portfolio.optimizer import OptimizerConfig

    cfg = OptimizerConfig.from_files()
    bundle = intl.load_country_bundle(args.country)
    ci = bundle.cost_inputs[["date", "permno", "adv_usd"]].copy()
    ci["date"] = pd.to_datetime(ci["date"])
    scores = load_scores(args.country)
    print(f"{args.country}: {len(scores)} cells' scores pinned; "
          f"adv_participation_max={cfg.adv_participation_max}, gross_budget={cfg.gross_max}")

    frames = []
    for aum in sorted(args.aum):
        try:
            t = arm_table(args.country, aum, scores, ci, cfg.adv_participation_max)
        except MissingProvenance as exc:
            print(f"  skipping AUM {aum:.0e}: {exc}")
            continue
        if t.empty:
            print(f"  skipping AUM {aum:.0e}: no cells resolved")
            continue
        frames.append(t)
        print(f"  AUM {aum:.0e}: {t['cell'].nunique()} cells, {t['date'].nunique()} months")
    if not frames:
        print("no AUM arms available; run stage 04 at each AUM with --country first")
        return 2
    panel = pd.concat(frames, ignore_index=True)
    args.out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.out / f"dose_panel_{args.country}.csv", index=False)

    cols = ["gross", "share_at_cap", "corr_w_advcap"] + (
        ["corr_w_alpha"] if "corr_w_alpha" in panel.columns else [])
    summary = panel.groupby("aum")[cols].mean()
    summary["n_months"] = panel.groupby("aum")["date"].nunique()
    summary.to_csv(args.out / f"dose_summary_{args.country}.csv")

    print()
    print("=" * 92)
    print(f"CAPACITY DOSE-RESPONSE, {args.country}: does the book track liquidity or alpha?")
    print("=" * 92)
    print(summary.to_string(float_format=lambda v: f"{v:,.4f}"))
    print()
    print("  prediction: as AUM FALLS, corr(|w|, adv_cap) should FALL and corr(|w|, alpha) RISE.")
    print()
    aums = sorted(summary.index)
    if len(aums) < 2:
        print("  only one arm present - the dose-response needs at least two.")
        return 0
    lo, hi = aums[0], aums[-1]
    cap_lo, cap_hi = summary.loc[lo, "corr_w_advcap"], summary.loc[hi, "corr_w_advcap"]
    print(f"  corr(|w|, adv_cap): {cap_lo:+.4f} at {lo:.0e}  ->  {cap_hi:+.4f} at {hi:.0e}")
    cap_ok = cap_hi > cap_lo
    print(f"    {'AS PREDICTED' if cap_ok else 'AGAINST THE PREDICTION'}: liquidity matters "
          f"{'more' if cap_ok else 'less'} as AUM rises")
    if "corr_w_alpha" in summary.columns:
        a_lo, a_hi = summary.loc[lo, "corr_w_alpha"], summary.loc[hi, "corr_w_alpha"]
        print(f"  corr(|w|, alpha)  : {a_lo:+.4f} at {lo:.0e}  ->  {a_hi:+.4f} at {hi:.0e}")
        alpha_ok = a_lo > a_hi
        print(f"    {'AS PREDICTED' if alpha_ok else 'AGAINST THE PREDICTION'}: the signal "
              f"{'does' if alpha_ok else 'does not'} matter more at smaller size")
    sc_lo, sc_hi = summary.loc[lo, "share_at_cap"], summary.loc[hi, "share_at_cap"]
    print(f"  share at the cap  : {sc_lo:.4f} at {lo:.0e}  ->  {sc_hi:.4f} at {hi:.0e}")
    print()
    if len(aums) >= 3:
        mono = all(summary.loc[a, "corr_w_advcap"] <= summary.loc[b, "corr_w_advcap"] + 1e-9
                   for a, b in zip(aums, aums[1:]))
        print(f"  corr(|w|, adv_cap) monotone increasing in AUM across all {len(aums)} arms: {mono}")
        print("  A monotone curve is what turns the capacity story from a single-point observation")
        print("  into a mechanism. Report the curve, not one AUM.")
    print(f"\nwrote {args.out / f'dose_summary_{args.country}.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
