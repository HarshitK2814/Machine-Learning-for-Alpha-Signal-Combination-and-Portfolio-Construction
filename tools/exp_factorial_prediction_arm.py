#!/usr/bin/env python
"""The factorial main effects, restricted to the arm that actually learned.

Why restrict
------------
The 16-cell design has four axes: representation (L/N), conditioning (S/C), objective (P/E) and
uncertainty (0/U). Its only significant main effect is the **objective** one, and
``docs/ECONOMIC_ARM_CAPABILITY_GAP.md`` shows the economic arm is not a competent implementation of
its objective: its information coefficient is an order of magnitude below the prediction arm's in
both countries (+0.0072 against +0.0757 in Germany; **negative** in India), partly because it is
forced to a gross budget that capacity makes infeasible. An effect estimated against an arm that
barely learns measures the implementation, not the design axis.

So this estimates the **2^3 design on the eight prediction-loss cells**, where every cell's scores
carry real and significant signal. The question it answers is the one that survives regardless of
what happens to the economic arm: *among the design choices this literature debates, which matter
once the portfolio is built from scores that demonstrably work?*

``validation.factorial`` cannot do this directly - ``parse_cell`` requires all four positions, so
restricting to P leaves a constant column with no contrast - so the three-factor contrasts are
formed here, with the same conventions: contrast coding on the **time domain** (the cells are ~0.9
correlated, so a cross-sectional contrast would understate the standard errors badly), and
Newey-West HAC standard errors.

    python tools/exp_factorial_prediction_arm.py --country DEU
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

#: (axis name, the letter that means ON, the letter that means OFF, position in the cell code)
AXES = [("representation_nonlinear", "N", "L", 0),
        ("conditioning_state", "C", "S", 1),
        ("uncertainty_shrinkage", "U", "0", 3)]
P_POSITION = 2


def load_monthly(country: str, cells: list[str], column: str) -> pd.DataFrame:
    """Months x cells of the chosen return column, from the saved C12 monthly tables."""
    from alphacomb.contracts import paths, read_table

    root = paths.outputs_root() / "returns"
    if not root.exists():
        raise SystemExit("no outputs/returns/; re-run stage 06 with --save-returns")
    out = {}
    for cell in cells:
        folder = root / cell
        if not folder.exists():
            continue
        latest = paths.latest_run("returns", cell)
        if latest is None:
            continue
        frame = read_table(latest, "returns")
        if column not in frame.columns:
            raise SystemExit(f"{latest} has no column {column!r}; have {list(frame.columns)}")
        s = frame.set_index(pd.to_datetime(frame["date"]))[column]
        out[cell.removeprefix("cell_")] = s
    if not out:
        raise SystemExit("none of the requested cells have saved monthly returns")
    panel = pd.DataFrame(out).sort_index()
    # An unbalanced panel makes each contrast compare different months, which is the exact failure
    # validation.factorial was changed to refuse. Refuse it here too rather than drop quietly.
    missing = panel.isna().any(axis=1).sum()
    if missing:
        raise SystemExit(f"{missing} months are incomplete across the {len(out)} cells; "
                         f"the contrasts would compare different periods")
    return panel


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", default="DEU", choices=["DEU", "IND", "JPN"])
    ap.add_argument("--column", default="net_ret",
                    help="which monthly return column to contrast (net_ret, after_tax_ret, ...)")
    ap.add_argument("--suffix", default="", help="cell-name suffix, e.g. _g013")
    ap.add_argument("--periods", type=int, default=12)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "factorial_prediction_arm")
    args = ap.parse_args(argv)

    from alphacomb.validation.inference import newey_west_se

    codes = [f"{a}-{b}-P-{d}" for a in "LN" for b in "SC" for d in ("0", "U")]
    cells = [f"cell_{c}{args.suffix}" for c in codes]
    panel = load_monthly(args.country, cells, args.column)
    panel.columns = [c.removesuffix(args.suffix) if args.suffix else c for c in panel.columns]
    n_months = len(panel)
    print(f"{args.country}: {panel.shape[1]} prediction-loss cells, {n_months} complete months, "
          f"column {args.column!r}")
    print()

    rows = []
    for name, on, off, pos in AXES:
        on_cells = [c for c in panel.columns if c.split("-")[pos] == on]
        off_cells = [c for c in panel.columns if c.split("-")[pos] == off]
        if len(on_cells) != len(off_cells) or not on_cells:
            raise SystemExit(f"axis {name} is unbalanced: {on_cells} vs {off_cells}")
        series = panel[on_cells].mean(axis=1) - panel[off_cells].mean(axis=1)
        mean = float(series.mean())
        se = float(newey_west_se(series.to_numpy(dtype=float)))
        t = mean / se if se > 0 else np.nan
        rows.append({"axis": name, "on": on, "off": off, "n_on": len(on_cells),
                     "effect_monthly": mean, "effect_annual": mean * args.periods,
                     "hac_se_monthly": se, "t_stat": t,
                     "significant_5pct": bool(abs(t) > 1.96) if np.isfinite(t) else False})
    res = pd.DataFrame(rows)
    args.out.mkdir(parents=True, exist_ok=True)
    res.to_csv(args.out / f"factorial_P_{args.country}{args.suffix}.csv", index=False)

    print("Main effects on the 2^3 prediction-arm design, contrast-coded in the TIME domain,")
    print("Newey-West HAC standard errors. Effect = mean(ON cells) - mean(OFF cells).")
    print()
    print(res[["axis", "on", "off", "effect_annual", "hac_se_monthly", "t_stat",
               "significant_5pct"]].to_string(index=False, float_format=lambda v: f"{v:,.5f}"))
    print()
    sig = res[res["significant_5pct"]]
    if sig.empty:
        print("  NO design axis has a significant main effect once the economic arm is removed.")
        print("  That is the result, not an absence of one: among choices made on scores that")
        print("  demonstrably carry signal, none of them moves net-of-cost performance detectably.")
        print("  It is also what the capacity mechanism predicts - the constraint, not the model,")
        print("  is setting the book, so design choices cannot express themselves.")
    else:
        for _, r in sig.iterrows():
            print(f"  {r['axis']}: {r['effect_annual']:+.5f} p.a. (t = {r['t_stat']:+.2f}) "
                  f"- survives with the economic arm removed")
    print(f"\nwrote {args.out / f'factorial_P_{args.country}{args.suffix}.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
