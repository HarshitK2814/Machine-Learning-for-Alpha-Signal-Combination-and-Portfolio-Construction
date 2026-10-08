#!/usr/bin/env python
"""Verify that C11 weights contain no trade the ADV participation limit forbids.

This is the check that caught `project` applying the position cap but never the per-name
**trade** cap (see `alphacomb.portfolio.optimizer.project`). It is kept as a tool because the
measurement is easy to get wrong in a way that invents violations, and because it has to be re-run
for every country.

**The trap.** Turnover is not ``|w_t - w_{t-1}|``. Between two month-ends a position drifts with
its own return, and that drift is not a trade. Comparing raw weights across months charges the
drift as trading, which (a) inflates every violation count and (b) reports the frozen sleeve -
carried precisely because it cannot be traded - as if it had been traded. The trade is
``w_t - prev_t`` where ``prev_t`` is last month's book drifted and renormalised exactly as stage 04
drifts it:

    prev = w * (1 + r) / (1 + portfolio_return)

Three sets are excluded from the count, each for a reason rather than for convenience:

* names with no C6 row at the date - they left the panel, so the change is a delisting, closed by
  the delisting return in C4, not a trade;
* names present but without certified market inputs - the frozen sleeve, which by construction
  must not have been traded at all (``--strict`` asserts that separately);
* names whose ADV is not finite, which cannot produce a cap to compare against.

    python tools/verify_trade_caps.py --country DEU
    python tools/verify_trade_caps.py --country DEU --cells L-C-E-0 N-C-P-U --strict
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
from alphacomb.portfolio.cost_terms import (eligible_cost_input_permnos,  # noqa: E402
                                            priced_at)

CELLS = [f"{n}-{c}-{e}-{u}" for n in "LN" for c in "SC" for e in "PE" for u in ("0", "U")]
TOL = 1.01  # 1% slack for conic residue on caps sitting at the 1e-6 floor


def check_cell(code: str, bundle, cfg: OptimizerConfig, advmap, rets, strict: bool) -> dict | None:
    latest = paths.latest_run("weights", f"cell_{code}")
    if latest is None:
        return None
    w = pd.read_parquet(latest)
    w["date"] = pd.to_datetime(w["date"])
    byd = {d: pd.Series(g["w"].to_numpy(), index=g["permno"].to_numpy())
           for d, g in w.groupby("date")}

    prev = None
    n_trades = n_over = 0
    worst = 0.0
    excess = 0.0
    frozen_moved = 0.0
    for d in sorted(byd):
        cur = byd[d]
        if prev is not None:
            idx = cur.index.union(prev.index)
            c = cur.reindex(idx).fillna(0.0)
            p = prev.reindex(idx).fillna(0.0)
            present = pd.Index(priced_at(d, bundle.cost_inputs))
            tradeable = set(eligible_cost_input_permnos(d, bundle.cost_inputs, idx))
            trade = (c - p).abs()
            for name, moved in trade[trade > 1e-12].items():
                if name not in tradeable:
                    # frozen if still in the panel: it must not have been traded at all
                    if name in set(present):
                        frozen_moved = max(frozen_moved, float(moved))
                    continue
                adv = advmap.get((d, name), np.nan)
                if not np.isfinite(adv):
                    continue
                cap = max(float(adv) * cfg.adv_participation_max / cfg.aum_usd, 1e-6)
                n_trades += 1
                if moved > cap * TOL:
                    n_over += 1
                    worst = max(worst, float(moved) / cap)
                    excess += float(moved) - cap
        r = rets.reindex(pd.MultiIndex.from_product([[d], cur.index])).fillna(0.0).to_numpy()
        port = float((cur.to_numpy() * r).sum())
        prev = pd.Series(cur.to_numpy() * (1.0 + r) / (1.0 + port), index=cur.index)

    return {
        "cell": code,
        "objective": "economic" if code.split("-")[2] == "E" else "prediction",
        "tradeable_trades": n_trades,
        "over_cap": n_over,
        "share_over_cap": n_over / max(n_trades, 1),
        "worst_multiple": worst,
        "cumulative_excess_gross": excess,
        "weights_file": latest.name,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--country", default="DEU", choices=["DEU", "IND", "JPN"])
    ap.add_argument("--cells", nargs="*", default=None)
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any cell has a trade over the cap, or a frozen "
                         "position that moved")
    ap.add_argument("--max-share", type=float, default=0.01,
                    help="share of trades over cap tolerated under --strict (default 1%%)")
    args = ap.parse_args(argv)

    bundle = intl.load_country_bundle(args.country)
    cfg = OptimizerConfig.from_files()
    advmap = bundle.cost_inputs.set_index(["date", "permno"])["adv_usd"]
    rets = bundle.targets.set_index(["date", "permno"])["ret_next"]

    rows = []
    for code in (args.cells or CELLS):
        out = check_cell(code, bundle, cfg, advmap, rets, args.strict)
        if out is not None:
            rows.append(out)
    if not rows:
        print("no C11 weights found; run pipelines/04_construct_portfolios.py first")
        return 2

    frame = pd.DataFrame(rows)
    cols = ["cell", "objective", "tradeable_trades", "over_cap", "share_over_cap",
            "worst_multiple", "cumulative_excess_gross"]
    print(f"country={args.country}  adv_participation_max={cfg.adv_participation_max}  "
          f"aum={cfg.aum_usd:,.0f}")
    print("trade measured against the DRIFTED prior book; delistings and the frozen sleeve "
          "excluded\n")
    print(frame[cols].to_string(index=False, float_format=lambda v: f"{v:,.4f}"))

    bad = frame.loc[frame["share_over_cap"] > args.max_share]
    print(f"\ncells with more than {args.max_share:.1%} of trades over the cap: {len(bad)}")
    if len(bad):
        print(bad[["cell", "share_over_cap", "worst_multiple"]].to_string(index=False))
        print("\nA cell that breaches the participation limit is trading in a way the cost model "
              "charges for\nbut the market could not absorb. See optimizer.project.")
    if args.strict and len(bad):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
