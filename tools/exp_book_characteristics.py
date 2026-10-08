#!/usr/bin/env python
"""Book characteristics per cell, plus the capacity ceiling the universe can carry.

Two tables that belong beside every performance number in the exhibit:

**Capacity.** The largest gross the eligible universe can support at a given AUM, which is
``sum_i min(weight_abs_max, adv_usd_i * adv_participation_max / AUM)``. On the German panel this
is about 0.20 at $1bn against a pre-registered budget of 2.0, so the risk budget never binds - the
participation limit does. See ``docs/CAPACITY_CONSTRAINT_DEU.md``.

**Realised books.** Mean gross and mean names held per cell, from the C11 weights. The two
objectives do not choose the same leverage: economic-loss cells ask for the whole budget and are
projected onto the capacity ceiling, prediction-loss cells stop at an interior mean-variance
optimum. A reader has to be able to see that next to the Sharpe ratios rather than infer it.

    python tools/exp_book_characteristics.py --country DEU
    python tools/exp_book_characteristics.py --country DEU --aum 1e9 1e10
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts import intl, paths  # noqa: E402
from alphacomb.portfolio import OptimizerConfig  # noqa: E402
from alphacomb.portfolio.cost_terms import eligible_cost_input_permnos  # noqa: E402

CELLS = [f"{n}-{c}-{e}-{u}" for n in "LN" for c in "SC" for e in "PE" for u in ("0", "U")]


def capacity_table(cost_inputs: pd.DataFrame, cfg: OptimizerConfig,
                   aums: list[float], dates: list[pd.Timestamp]) -> pd.DataFrame:
    rows = []
    for aum in aums:
        for d in dates:
            at_date = cost_inputs.loc[cost_inputs["date"] == d]
            if at_date.empty:
                continue
            names = eligible_cost_input_permnos(d, cost_inputs, pd.Index(at_date["permno"]))
            row = at_date.set_index("permno").reindex(names)
            adv = row["adv_usd"].to_numpy(dtype=float)
            adv_cap = np.clip(adv * cfg.adv_participation_max / aum, 1e-6, None)
            pos_cap = np.minimum(cfg.weight_abs_max, np.maximum(adv_cap, 1e-5))
            rows.append({
                "aum": aum,
                "date": str(pd.Timestamp(d).date()),
                "eligible_names": len(names),
                "max_attainable_gross": float(pos_cap.sum()),
                "gross_budget": cfg.gross_max,
                "share_adv_capped": float((adv_cap < cfg.weight_abs_max).mean()),
                "median_adv_usd": float(np.nanmedian(adv)),
            })
    return pd.DataFrame(rows)


def realised_books(require_source: str | None = None) -> pd.DataFrame:
    rows = []
    for code in CELLS:
        strategy = f"cell_{code}"
        latest = paths.latest_run("weights", strategy)
        if latest is None:
            continue
        w = pd.read_parquet(latest)
        gross = w.groupby("date")["w"].apply(lambda x: float(np.abs(x).sum()))
        names = w.groupby("date")["w"].apply(lambda x: int((np.abs(x) > 1e-9).sum()))
        net = w.groupby("date")["w"].apply(lambda x: float(x.sum()))
        rows.append({
            "cell": code,
            "objective": "economic" if code.split("-")[2] == "E" else "prediction",
            "months": len(gross),
            "mean_gross": gross.mean(),
            "median_gross": gross.median(),
            "max_gross": gross.max(),
            "mean_names": names.mean(),
            "mean_abs_net": net.abs().mean(),
            "weights_file": latest.name,
        })
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--country", default="DEU", choices=["DEU", "IND", "JPN"])
    ap.add_argument("--aum", nargs="*", type=float, default=[1e9, 1e10])
    ap.add_argument("--dates", nargs="*", default=["2009-06-30", "2014-06-30", "2019-06-30"])
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "book_characteristics")
    args = ap.parse_args(argv)

    bundle = intl.load_country_bundle(args.country)
    cfg = OptimizerConfig.from_files()
    dates = [pd.Timestamp(d) for d in args.dates]

    cap = capacity_table(bundle.cost_inputs, cfg, args.aum, dates)
    books = realised_books()

    args.out.mkdir(parents=True, exist_ok=True)
    cap.to_csv(args.out / f"capacity_{args.country}.csv", index=False)
    books.to_csv(args.out / f"realised_books_{args.country}.csv", index=False)

    print(f"country={args.country}  gross_budget={cfg.gross_max}  "
          f"weight_abs_max={cfg.weight_abs_max}  adv_participation_max={cfg.adv_participation_max}")
    print(f"\n--- capacity ceiling: largest gross the eligible universe can carry ---")
    show = cap.assign(aum=cap["aum"].map(lambda v: f"{v:.0e}"),
                      median_adv_usd_mn=(cap["median_adv_usd"] / 1e6).round(2)).drop(
                          columns=["median_adv_usd"])
    print(show.to_string(index=False, float_format=lambda v: f"{v:,.4f}"))
    if len(cap):
        worst = cap.loc[cap["max_attainable_gross"].idxmin()]
        print(f"\nThe pre-registered gross budget of {cfg.gross_max} is unreachable: the ceiling "
              f"ranges {cap['max_attainable_gross'].min():.3f} to "
              f"{cap['max_attainable_gross'].max():.3f}.")
        print(f"At AUM {worst['aum']:.0e} the book can be at most "
              f"{100 * worst['max_attainable_gross']:.1f}% invested.")

    if books.empty:
        print("\nno C11 weights found; run pipelines/04_construct_portfolios.py first")
        return 0
    print(f"\n--- realised books per cell (C11) ---")
    cols = ["cell", "objective", "months", "mean_gross", "median_gross", "mean_names",
            "mean_abs_net"]
    print(books[cols].to_string(index=False, float_format=lambda v: f"{v:,.4f}"))
    by_obj = books.groupby("objective").agg(
        mean_gross=("mean_gross", "mean"), mean_names=("mean_names", "mean"), cells=("cell", "size"))
    print(f"\n--- by objective ---")
    print(by_obj.to_string(float_format=lambda v: f"{v:,.4f}"))
    if len(by_obj) == 2:
        ratio = by_obj.loc["economic", "mean_gross"] / max(by_obj.loc["prediction", "mean_gross"],
                                                           1e-12)
        print(f"\nEconomic-loss cells run at {ratio:.1f}x the gross of prediction-loss cells. That "
              f"is a leverage difference bundled into the objective contrast; see\n"
              f"docs/CAPACITY_CONSTRAINT_DEU.md for why it is reported rather than normalised away,"
              f"\nand for the volatility-matched check that would separate the two.")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
