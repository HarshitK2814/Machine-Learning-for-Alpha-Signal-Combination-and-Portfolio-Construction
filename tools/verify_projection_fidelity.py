#!/usr/bin/env python
"""Does `project()` keep the economic cell's proposal, or does it replace it?

The economic-loss half of the factorial reaches C11 as a weight *proposal* (C10) that is projected
onto the constraint set. If that projection does not preserve what the model asked for, then the
design's cost-objective axis measures the projection rather than the objective - and on this panel
the objective is the only significant main effect, so the question decides whether the headline
result is a finding or an implementation artefact.

**Measure fidelity weighted by position size.** An unweighted sign-agreement rate is misleading
here and nearly caused me to retract a correct result. A proposal contains a long tail of
essentially zero positions whose sign carries no information; the projection reshuffles those
freely, which drags unweighted agreement down to ~76% while the positions that carry the book agree
almost perfectly. On the promoted DEU panel:

    cell       all positions   top half   top quintile   gross-weighted
    L-S-E-0        75.8%        94.0%        99.5%           89.0%
    N-C-E-0        76.8%        93.2%        99.7%           93.6%
    N-S-E-U        79.4%        95.0%        99.2%           94.8%

So the projection is faithful where it matters. Judge it by the gross-weighted and top-quintile
columns; the unweighted column is dominated by noise positions.

(A rescaling of the target to the attainable gross was tested as a way to improve fidelity, on the
theory that projecting a gross-2.0 proposal onto a 0.2 ceiling must distort it. It does not help:
fidelity moves from 0.649 to 0.697 rank correlation while realised gross falls from 0.144 to
0.048, because a uniformly shrunk target leaves every name far inside its cap and the neutrality
and beta constraints then shrink it further. Recorded so it is not retried.)

    python tools/verify_projection_fidelity.py --country DEU
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts import paths  # noqa: E402

ECONOMIC_CELLS = [f"{n}-{c}-E-{u}" for n in "LN" for c in "SC" for u in ("0", "U")]


def check_cell(code: str) -> dict | None:
    weights = paths.latest_run("weights", f"cell_{code}")
    proposals = paths.latest_run("weight_proposals", f"cell_{code}")
    if weights is None or proposals is None:
        return None
    W = pd.read_parquet(weights)
    P = pd.read_parquet(proposals)
    W["date"] = pd.to_datetime(W["date"])
    P["date"] = pd.to_datetime(P["date"])

    acc = {k: [] for k in ("all", "top50", "top20", "wtd", "rank")}
    for date, g in W.groupby("date"):
        m = g.merge(P.loc[P["date"] == date], on=["date", "permno"], how="inner")
        if len(m) < 40:
            continue
        absp = m["w_prop"].abs()
        agree = np.sign(m["w"]) == np.sign(m["w_prop"])
        acc["all"].append(float(agree.mean()))
        acc["top50"].append(float(agree[absp >= absp.quantile(0.50)].mean()))
        acc["top20"].append(float(agree[absp >= absp.quantile(0.80)].mean()))
        acc["wtd"].append(float((agree * absp).sum() / max(absp.sum(), 1e-12)))
        acc["rank"].append(float(m["w"].corr(m["w_prop"], method="spearman")))
    if not acc["all"]:
        return None
    return {
        "cell": code,
        "months": len(acc["all"]),
        "sign_all": float(np.nanmean(acc["all"])),
        "sign_top_half": float(np.nanmean(acc["top50"])),
        "sign_top_quintile": float(np.nanmean(acc["top20"])),
        "sign_gross_weighted": float(np.nanmean(acc["wtd"])),
        "rank_corr": float(np.nanmean(acc["rank"])),
        "weights_file": weights.name,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--country", default="DEU", help="recorded in the output only")
    ap.add_argument("--cells", nargs="*", default=None)
    ap.add_argument("--min-weighted", type=float, default=0.85,
                    help="fail under --strict if gross-weighted sign agreement falls below this")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    rows = [r for r in (check_cell(c) for c in (args.cells or ECONOMIC_CELLS)) if r]
    if not rows:
        print("no economic cells with both C10 proposals and C11 weights found")
        return 2
    frame = pd.DataFrame(rows)
    cols = ["cell", "months", "sign_all", "sign_top_half", "sign_top_quintile",
            "sign_gross_weighted", "rank_corr"]
    print(f"country={args.country}  projection fidelity of the economic-loss cells")
    print("judge by gross_weighted and top_quintile; sign_all is dominated by near-zero "
          "proposal positions\n")
    print(frame[cols].to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(args.out, index=False)
        print(f"\nwrote {args.out}")

    bad = frame.loc[frame["sign_gross_weighted"] < args.min_weighted]
    print(f"\ncells below {args.min_weighted:.0%} gross-weighted agreement: {len(bad)}")
    if len(bad):
        print(bad[["cell", "sign_gross_weighted", "sign_top_quintile"]].to_string(index=False))
        print("\nIf the projection does not carry the proposal, the cost-objective axis of the\n"
              "factorial is measuring the projection. Do not report the objective effect.")
    return 1 if (args.strict and len(bad)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
