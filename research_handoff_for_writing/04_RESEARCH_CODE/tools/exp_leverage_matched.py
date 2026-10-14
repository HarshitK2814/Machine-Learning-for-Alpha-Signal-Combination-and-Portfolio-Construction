#!/usr/bin/env python
"""Compare AUM arms at MATCHED gross, because net Sharpe is not leverage-neutral.

The problem with comparing arms as they come
--------------------------------------------
Write the net Sharpe of a long-short book at gross ``G``, holding the direction of the book fixed:

    gross return   ~ a*G          volatility ~ v*G
    spread cost    ~ b*G          impact cost ~ d*G^1.5     (the cost model's |dw|^1.5 term)

    net Sharpe = (a*G - b*G - d*G^1.5) / (v*G) = (a - b)/v - (d/v) * G^0.5

So **net Sharpe falls with gross for mechanical reasons**, with no change in how good the book's
direction is. Comparing the $1e8 arm (realised gross 0.42) against the $1e9 arm (0.13) on raw net
Sharpe therefore charges the smaller-AUM arm for the larger book its optimiser chose, and the
comparison conflates two things:

* **opportunity** - how good the achievable direction is, which is what capacity should affect;
* **leverage** - how much of it the optimiser decided to take, which is a separate decision.

Raw net Sharpe said the $1e8 arm was worse (-0.116 against +0.128). Gross Sharpe, which *is*
scale-invariant, said its direction was much better (+0.654 against +0.423). Both cannot be the
headline, and this resolves which.

What this does
--------------
Rescales every arm's book, month by month, to a **common target gross**, then re-runs the same
net-of-cost backtest. Scaling *down* is always feasible - every position shrinks, so no
participation cap, position cap, gross budget or dollar-neutrality constraint can be newly violated
- which is why the target defaults to the gross the most constrained arm naturally runs at. Scaling
*up* is refused for exactly the opposite reason.

    python tools/exp_leverage_matched.py --country DEU --aum 1e8 1e9 --target-gross 0.13
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


def rescale_arm(country: str, aum: float, target: float, suffix: str,
                cost_inputs: pd.DataFrame) -> list[str]:
    """Write a leverage-matched copy of each cell's book. Returns the new strategy names.

    **The frozen sleeve must not be rescaled.** A position in a name with no certified market
    inputs that month cannot be traded at all, only carried, so changing its weight by any amount
    is a trade that cannot be priced. A first version of this scaled the whole book uniformly and
    the backtest refused it outright - "87 unpriceable names moved by 2.04e-05 (budget 1.6e-05);
    a frozen position must be carried, not traded". Correct here, so only the tradeable part is
    scaled and the frozen weights are carried through untouched.
    """
    from alphacomb.contracts import new_run_id, paths, provenance, read_table, write_table
    from alphacomb.portfolio.cost_terms import eligible_cost_input_permnos

    tag = f"{aum:.0e}".replace("e+0", "e").replace("e+", "e")
    resolved = provenance.country_weights(country, tag)
    written, index_rows, skipped = [], [], []
    for cell in CELLS:
        path = resolved.get(cell)
        if path is None:
            continue
        w = read_table(path, "weights")
        wcol = "w" if "w" in w.columns else ("weight" if "weight" in w.columns else w.columns[-1])
        w = w.copy()
        w["date"] = pd.to_datetime(w["date"])

        pieces, refuse = [], None
        for date, g in w.groupby("date"):
            g = g.copy()
            held = pd.Index(g.loc[np.abs(g[wcol]) > 1e-12, "permno"])
            tradeable = eligible_cost_input_permnos(date, cost_inputs, held)
            is_tradeable = g["permno"].isin(set(tradeable))
            frozen_gross = float(np.abs(g.loc[~is_tradeable, wcol]).sum())
            trade_gross = float(np.abs(g.loc[is_tradeable, wcol]).sum())
            room = target - frozen_gross
            # Refuse to scale a month UP: it could breach a participation or position cap the book
            # was already sitting against, and the result would not be an attainable portfolio.
            if room <= 0 or trade_gross < room - 1e-12:
                refuse = (f"{cell} ({date.date()}: tradeable gross {trade_gross:.5f} cannot reach "
                          f"{room:.5f} after a frozen sleeve of {frozen_gross:.5f})")
                break
            g.loc[is_tradeable, wcol] = g.loc[is_tradeable, wcol] * (room / trade_gross)
            pieces.append(g)
        if refuse is not None:
            skipped.append(refuse)
            continue
        w = pd.concat(pieces, ignore_index=True)
        name = f"{cell}{suffix}"
        run_id = new_run_id(f"pf_{name}")
        out = paths.weights_path(name, run_id)
        write_table(w, out, "weights")
        written.append(name)
        index_rows.append({"country": country, "aum": aum, "strategy": name,
                           "run_id": run_id, "weights": str(out)})
    if index_rows:
        index_dir = paths.outputs_root() / "weights_index"
        index_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(index_rows).to_csv(index_dir / f"{country}_{tag}{suffix}.csv", index=False)
    if skipped:
        print(f"  AUM {tag}: refused to scale up {len(skipped)} cells:")
        for s in skipped[:4]:
            print(f"    {s}")
    print(f"  AUM {tag}: wrote {len(written)} leverage-matched books at gross {target}")
    return written


REFUSAL = """
This approach DOES NOT WORK and this tool will not write books. Kept as the record of why.

Post-hoc rescaling cannot leverage-match a book that carries a frozen, non-tradeable sleeve:

  1. Scaling the whole book uniformly moves frozen positions, and a name with no certified market
     inputs that month cannot be traded at all. The backtest refuses it:
       "87 unpriceable names moved by 2.04e-05 (budget 1.6e-05) in the C11 weights.
        A frozen position must be carried, not traded."

  2. Scaling only the tradeable names and carrying the frozen weights through verbatim fails too,
     and this one is structural. The drifted prior book is w*(1+r)/(1+port_ret), so changing the
     tradeable weights changes the portfolio return, which changes what the frozen weight WOULD
     have drifted to. The frozen sleeve is endogenous to the whole book: you cannot alter the
     tradeable part without altering what the frozen part should be, and you cannot alter the
     frozen part at all. The backtest refuses this as well:
       "13 unpriceable names moved by 0.00017"

So no post-hoc reweighting of these books is available - not leverage matching, not volatility
matching, not a risk-parity overlay - while a non-tradeable sleeve is present.

DO THIS INSTEAD. Re-optimise under a different gross budget, which is a feasible portfolio by
construction:

    python pipelines/04_construct_portfolios.py --country DEU --aum 1e8         --gross-max 0.13 --suffix _g013 --strategies <cells>

See docs/CANDIDATE_REFRAMING_CAPACITY.md §10.
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", default="DEU", choices=["DEU", "IND", "JPN"])
    ap.add_argument("--aum", nargs="+", type=float, default=[1e8, 1e9])
    ap.add_argument("--target-gross", type=float, default=None,
                    help="default: the smallest mean gross across the arms, so nothing scales up")
    ap.add_argument("--i-know-this-does-not-work", action="store_true",
                    help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    if not getattr(args, "i_know_this_does_not_work", False):
        print(REFUSAL)
        return 2

    from alphacomb.contracts import intl, provenance, read_table
    from alphacomb.contracts.provenance import MissingProvenance

    bundle = intl.load_country_bundle(args.country)
    cost_inputs = bundle.cost_inputs

    # Pick a target no arm has to scale up to reach.
    if args.target_gross is None:
        mins = []
        for aum in args.aum:
            tag = f"{aum:.0e}".replace("e+0", "e").replace("e+", "e")
            try:
                resolved = provenance.country_weights(args.country, tag)
            except MissingProvenance as exc:
                print(f"  skipping {tag}: {exc}")
                continue
            for cell, path in resolved.items():
                if not cell.startswith("cell_"):
                    continue
                w = read_table(path, "weights")
                wcol = "w" if "w" in w.columns else w.columns[-1]
                w = w.copy()
                w["date"] = pd.to_datetime(w["date"])
                mins.append(float(w.groupby("date")[wcol].apply(
                    lambda x: float(np.abs(x).sum())).min()))
        if not mins:
            print("no arms resolved")
            return 2
        args.target_gross = float(np.floor(min(mins) * 1000) / 1000)
        print(f"target gross chosen so no arm scales up: {args.target_gross:.4f}")

    tags = []
    for aum in sorted(args.aum):
        tag = f"{aum:.0e}".replace("e+0", "e").replace("e+", "e")
        try:
            names = rescale_arm(args.country, aum, args.target_gross, f"_lm{tag}", cost_inputs)
        except MissingProvenance as exc:
            print(f"  skipping {tag}: {exc}")
            continue
        if names:
            tags.append((tag, names))

    if not tags:
        print("nothing to compare")
        return 2
    print()
    print("Now run the backtest on these, then compare. For each arm:")
    for tag, names in tags:
        print(f"  python tools/dev_backtest.py --country {args.country} --strategies "
              f"{' '.join(names[:2])} ...   ({len(names)} strategies, suffix _lm{tag})")
    print()
    print("The comparison that matters: at a COMMON gross, does the smaller-AUM arm's book earn")
    print("more net? If yes, capacity was suppressing real opportunity and the raw net-Sharpe")
    print("ordering was a leverage artefact. If no, the two-sided squeeze stands as reported.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
