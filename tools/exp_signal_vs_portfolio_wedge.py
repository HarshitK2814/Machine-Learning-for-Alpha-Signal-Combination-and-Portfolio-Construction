#!/usr/bin/env python
"""The friction wedge, in commensurable units: what a signal paper reports vs what you can run.

The gap this closes
-------------------
The project's headline is that the signal is strong and does not reach the portfolio. Until now
that was argued by comparing an **information coefficient** (t up to +10.4) with a **portfolio
Sharpe ratio** (0 of 21 surviving deflation). Those are not commensurable, and a referee would say
so immediately: an IC is a rank correlation, a Sharpe is a risk-adjusted return, and no reader can
convert one into the other.

The literature's standard object is the **decile-spread long/short portfolio**: rank the
cross-section on the signal, buy the top decile, sell the bottom, equal- or value-weight within
each. No optimiser, no risk model, no participation cap. That is what a signal-level paper reports,
and nothing in this repository has ever built one - even the BASE-EW comparators route through the
constrained optimiser, so every number we have is already capacity-constrained.

What this measures
------------------
From the **same** stage-02 scores, four portfolios per cell, so the wedge decomposes into channels
that are each attributable:

1. **Decile spread, gross.** What a signal-level paper reports. No costs, no constraints.
2. **Decile spread, net of costs** at a given AUM, using the project's own cost model
   (``trade_cost_numpy``: half-spread + commission + the square-root impact term). Still **no
   participation cap**, so a position may trade a multiple of a name's daily volume. This is the
   portfolio the literature implicitly assumes is attainable.
3. **Decile spread, net, participation-capped.** Each name's weight is clipped to
   ``adv_participation_max * ADV_i / AUM`` and the book renormalised. This is the first number that
   is actually executable.
4. The **optimised** book from stage 04, for reference, which adds the risk model and the full
   constraint set.

The difference 1 -> 2 is the **cost channel**. The difference 2 -> 3 is the **capacity channel**.
Reporting both separately is the point: it says how much of the wedge is paying for liquidity and
how much is not being allowed to have the position at all.

Infeasibility is reported, not hidden: for portfolio 2 the tool prints what multiple of ADV the
median and 95th-percentile position would require, so the reader can see that the literature's
portfolio is not merely expensive but unexecutable at scale.

    python tools/exp_signal_vs_portfolio_wedge.py --country DEU --aum 1e8 1e9 1e10
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

P_CELLS = [f"cell_{a}-{b}-P-{d}" for a in "LN" for b in "SC" for d in ("0", "U")]


def decile_weights(scores: pd.Series, n_groups: int, gross: float) -> pd.Series:
    """Equal-weighted long-short spread over the extreme groups, scaled to ``gross``."""
    if scores.notna().sum() < n_groups * 2:
        return pd.Series(dtype=float)
    ranks = scores.rank(method="first", na_option="keep")
    valid = ranks.notna()
    k = int(valid.sum())
    edge = max(int(np.floor(k / n_groups)), 1)
    order = ranks[valid].sort_values()
    short_idx, long_idx = order.index[:edge], order.index[-edge:]
    w = pd.Series(0.0, index=scores.index)
    w.loc[long_idx] = (gross / 2) / edge
    w.loc[short_idx] = -(gross / 2) / edge
    return w


def run(country: str, aum: float, n_groups: int, gross: float,
        cells: list[str], impact_k: float | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    from alphacomb.contracts import intl, paths, read_table
    from alphacomb.portfolio.cost_terms import trade_cost_numpy

    bundle = intl.load_country_bundle(country)
    cfg_costs = __import__("alphacomb.contracts", fromlist=["load_config"]).load_config("base")["costs"]
    # k = 1 is Grinold-Kahn. The SIGN of the capacity channel depends on kappa, so the
    # crossover moves with k and the dependence has to be reported as a panel rather than
    # asserted to be bounded.
    k = float(cfg_costs["impact_k"] if impact_k is None else impact_k)
    comm = float(cfg_costs["commission_bps"])
    from alphacomb.portfolio.optimizer import OptimizerConfig
    part = OptimizerConfig.from_files().adv_participation_max

    tg = bundle.targets[["date", "permno", "ret_next"]].copy()
    tg["date"] = pd.to_datetime(tg["date"])
    ci = bundle.cost_inputs[["date", "permno", "spread", "sigma_d", "adv_usd"]].copy()
    ci["date"] = pd.to_datetime(ci["date"])

    index = paths.outputs_root() / "source_index" / f"{country}.csv"
    if not index.exists():
        raise SystemExit(f"no source index at {index}; stage 02 writes it, or rebuild from its log")
    src = pd.read_csv(index)
    src = dict(zip(src["strategy"].astype(str), src["artefact"].astype(str)))

    rows, feas, monthlies = [], [], []
    for cell in cells:
        path = src.get(cell)
        if path is None or not Path(path).exists():
            continue
        f = read_table(Path(path), "predictions")
        col = "score" if "score" in f.columns else [c for c in f.columns
                                                    if c not in ("date", "permno", "unc_sd")][0]
        d = f[["date", "permno", col]].rename(columns={col: "score"}).copy()
        d["date"] = pd.to_datetime(d["date"])
        d = d.merge(tg, on=["date", "permno"], how="inner").merge(ci, on=["date", "permno"],
                                                                  how="left")
        monthly, prev_u, prev_c, prev_inputs = [], None, None, None
        for date, g in d.groupby("date"):
            g = g.set_index("permno")
            w = decile_weights(g["score"], n_groups, gross)
            if w.empty:
                continue
            r = g["ret_next"].reindex(w.index).fillna(0.0).to_numpy(dtype=float)
            # (2) uncapped: the literature's portfolio
            wu = w.to_numpy(dtype=float)
            # (3) participation-capped, then renormalised back toward the same gross
            cap = (part * g["adv_usd"].reindex(w.index).to_numpy(dtype=float) / aum)
            cap = np.where(np.isfinite(cap), cap, 0.0)
            wc = np.clip(np.abs(wu), 0, cap) * np.sign(wu)
            sp = g["spread"].reindex(w.index).to_numpy(dtype=float)
            sd = g["sigma_d"].reindex(w.index).to_numpy(dtype=float)
            ad = g["adv_usd"].reindex(w.index).to_numpy(dtype=float)
            ok = np.isfinite(sp) & np.isfinite(sd) & np.isfinite(ad) & (ad > 0)

            def cost(curr, prev):
                # The cross-section changes every month, so the trade must be aligned on permno
                # rather than on position: a positional difference would charge a name that simply
                # entered the universe as if it had been traded from someone else's weight.
                cur_s = pd.Series(curr, index=w.index)
                prev_s = (pd.Series(dtype=float) if prev is None else prev)
                dw = cur_s.sub(prev_s.reindex(cur_s.index).fillna(0.0), fill_value=0.0)
                # A name that LEFT the book is also a trade - back to zero - and must be charged.
                gone = prev_s.index.difference(cur_s.index)
                dw_arr = dw.reindex(cur_s.index).to_numpy(dtype=float)
                c = np.zeros_like(dw_arr)
                c[ok] = trade_cost_numpy(dw_arr[ok], sp[ok], sd[ok], ad[ok], aum, k, comm)
                total = float(c.sum())
                if len(gone):
                    # Exits are priced on the prior month's market inputs, which are the inputs
                    # that existed when the position did.
                    ex = prev_s.reindex(gone).abs()
                    pin = prev_inputs.reindex(gone) if prev_inputs is not None else None
                    if pin is not None:
                        m = pin.notna().all(axis=1) & (pin["adv_usd"] > 0)
                        if m.any():
                            total += float(trade_cost_numpy(
                                ex[m].to_numpy(dtype=float),
                                pin.loc[m, "spread"].to_numpy(dtype=float),
                                pin.loc[m, "sigma_d"].to_numpy(dtype=float),
                                pin.loc[m, "adv_usd"].to_numpy(dtype=float),
                                aum, k, comm).sum())
                return total

            gross_ret = float((wu * r).sum())
            monthly.append({
                "date": date,
                "gross_ret": gross_ret,
                "net_ret_uncapped": gross_ret - cost(wu, prev_u),
                "gross_ret_capped": float((wc * r).sum()),
                "net_ret_capped": float((wc * r).sum()) - cost(wc, prev_c),
                "gross_capped": float(np.abs(wc).sum()),
            })
            # how infeasible is the literature's portfolio?
            held = np.abs(wu) > 0
            with np.errstate(divide="ignore", invalid="ignore"):
                mult = np.abs(wu[held & ok]) * aum / (part * ad[held & ok])
            if mult.size:
                feas.append({"cell": cell, "date": date,
                             "median_x_cap": float(np.median(mult)),
                             "p95_x_cap": float(np.quantile(mult, 0.95))})
            prev_u = pd.Series(wu, index=w.index)
            prev_c = pd.Series(wc, index=w.index)
            prev_inputs = g.reindex(w.index)[["spread", "sigma_d", "adv_usd"]]
        if not monthly:
            continue
        m = pd.DataFrame(monthly)
        mm = m.copy()
        mm["cell"] = cell.removeprefix("cell_")
        monthlies.append(mm)

        def sharpe(x):
            s = x.std(ddof=1)
            return float(x.mean() / s * np.sqrt(12)) if s > 0 else np.nan

        rows.append({
            "cell": cell.removeprefix("cell_"), "months": len(m),
            "sharpe_gross_uncapped": sharpe(m["gross_ret"]),
            "sharpe_net_uncapped": sharpe(m["net_ret_uncapped"]),
            "sharpe_net_capped": sharpe(m["net_ret_capped"]),
            "mean_gross_attained_capped": float(m["gross_capped"].mean()),
            "cost_bps_uncapped": float((m["gross_ret"] - m["net_ret_uncapped"]).mean()*12*1e4),
        })
    monthly_all = (pd.concat(monthlies, ignore_index=True) if monthlies
                   else pd.DataFrame())
    return pd.DataFrame(rows), pd.DataFrame(feas), monthly_all


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", default="DEU", choices=["DEU", "IND", "JPN"])
    ap.add_argument("--aum", nargs="+", type=float, default=[1e8, 1e9, 1e10])
    ap.add_argument("--groups", type=int, default=10, help="10 = deciles, 5 = quintiles")
    ap.add_argument("--gross", type=float, default=2.0,
                    help="gross of the spread portfolio; 2.0 matches the registered budget")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "signal_vs_portfolio")
    ap.add_argument("--impact-k", type=float, default=None,
                    help="override the square-root impact coefficient (config default is "
                         "1.0, Grinold-Kahn). The capacity channel's sign depends on it, "
                         "so the crossover location is a function of k")
    ap.add_argument("--dump-monthly", action="store_true",
                    help="also write the per-cell monthly return series (gross, net uncapped, net "
                         "capped) for every AUM rung. Required for any inference on the capacity "
                         "channel, which is a difference of two Sharpe ratios on paired months")
    ap.add_argument("--tag", default="",
                    help="suffix for the output filename; set it when sweeping a "
                         "different AUM ladder or group count so a later run cannot "
                         "silently overwrite an earlier one (this has happened)")
    args = ap.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"{args.country}: {args.groups}-group long/short spread at gross {args.gross}, "
          f"from the same stage-02 scores as the optimised book"
          + (f", impact_k={args.impact_k}" if args.impact_k is not None else ""))
    print()
    all_res, all_mon = [], []
    for aum in sorted(args.aum):
        res, feas, mon = run(args.country, aum, args.groups, args.gross, P_CELLS,
                             impact_k=args.impact_k)
        if res.empty:
            print(f"  AUM {aum:.0e}: no cells resolved")
            continue
        res["aum"] = aum
        all_res.append(res)
        if args.dump_monthly and not mon.empty:
            mon = mon.copy()
            mon["aum"] = aum
            all_mon.append(mon)
        m = res.mean(numeric_only=True)
        print(f"AUM {aum:.0e}  ({len(res)} prediction cells, {int(res['months'].iloc[0])} months)")
        print(f"   1) decile spread, GROSS, no costs no caps : Sharpe {m['sharpe_gross_uncapped']:+.4f}"
              f"   <- what a signal paper reports")
        print(f"   2) decile spread, NET of costs, no caps   : Sharpe {m['sharpe_net_uncapped']:+.4f}"
              f"   (cost {m['cost_bps_uncapped']:,.0f} bps p.a.)")
        print(f"   3) decile spread, NET, participation-capped: Sharpe {m['sharpe_net_capped']:+.4f}"
              f"   (attained gross {m['mean_gross_attained_capped']:.4f} of {args.gross})")
        if not feas.empty:
            print(f"      the uncapped portfolio needs a median {feas['median_x_cap'].mean():,.1f}x "
                  f"and p95 {feas['p95_x_cap'].mean():,.1f}x the participation limit per position")
        print(f"      COST channel     1->2 : {m['sharpe_net_uncapped']-m['sharpe_gross_uncapped']:+.4f}")
        print(f"      CAPACITY channel 2->3 : {m['sharpe_net_capped']-m['sharpe_net_uncapped']:+.4f}")
        print()
    suffix = f"_{args.tag}" if args.tag else ""
    if all_res:
        out = pd.concat(all_res, ignore_index=True)
        dest = args.out / f"wedge_{args.country}{suffix}.csv"
        out.to_csv(dest, index=False)
        print(f"wrote {dest}")
    if all_mon:
        md = args.out / f"monthly_{args.country}{suffix}.csv"
        pd.concat(all_mon, ignore_index=True).to_csv(md, index=False)
        print(f"wrote {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
