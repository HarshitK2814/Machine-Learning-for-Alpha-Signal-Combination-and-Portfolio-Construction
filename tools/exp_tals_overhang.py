#!/usr/bin/env python
"""Does a levered, tax-aware book accumulate the deferral overhang its critics describe?

`docs/PRACTITIONER_GAP.md` section 5 says plainly what our first overhang result did NOT show: our
book is unlevered and does not deliberately defer, while the product under dispute is levered and
engineered to defer. This script closes that gap by moving our strategy toward the product and
watching what happens to the overhang.

The two design features the criticism turns on:

* **Leverage.** Tax-aware long/short runs well past 100% gross - often 200/100 or higher -
  *specifically* to hold more positions and so create more harvesting opportunities. More positions
  also means more embedded gains sitting unrealised.
* **A tax-aware objective.** The optimiser is told what selling a gain costs, so it holds winners
  and sells losers. That is the "perpetually deferring the realization of gains" the critics name.

We sweep both, hold everything else fixed, and report the overhang trajectory for each cell. If the
criticism is right, the overhang should grow with gross exposure and with tax-awareness, and keep
growing as the book ages. If the carryforward keeps cancelling it, it should not.

    python tools/exp_tals_overhang.py --strategy cell_N-C-P-0 --gross 2 4 6

Writes ``outputs/exp_tals_overhang.csv``.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alphacomb.contracts import load_bundle, load_config, paths, read_table  # noqa: E402
from alphacomb.portfolio import OptimizerConfig, TaxState, construct  # noqa: E402
from alphacomb.risk import RiskCache, StructuralRiskModel  # noqa: E402
from alphacomb.tax import (TaxLotLedger, deferral_overhang, get_regime,  # noqa: E402
                           harvesting_decomposition, overhang_trajectory)

log = logging.getLogger("exp_tals")


def build(preds: pd.DataFrame, bundle, cfg, risk, opt, tax_aware: bool, regime: str):
    """Walk the book forward, optionally telling the optimiser what a gain costs to sell."""
    rows, prev = [], None
    returns = bundle.targets.set_index(["date", "permno"])["ret_next"]
    ledger = TaxLotLedger(get_regime(regime)) if tax_aware else None
    nav = opt.aum_usd
    for date, group in preds.groupby("date"):
        alpha = pd.Series(group["alpha"].to_numpy(), index=group["permno"].to_numpy()).dropna()
        if alpha.empty:
            continue
        state = None
        if ledger is not None:
            ledger.expire_wash_window(date)
            state = TaxState.from_ledger(ledger, alpha.index, date)
        res = construct(date, alpha, prev, risk.model(date), bundle.cost_inputs, opt, state)
        w = res.weights
        if w.empty:
            continue
        rows.append(pd.DataFrame({"date": pd.Timestamp(date), "permno": w.index.astype("int32"),
                                  "w": w.to_numpy()}))
        r = returns.reindex(pd.MultiIndex.from_product([[pd.Timestamp(date)], w.index])).fillna(0.0).to_numpy()
        port = float((w.to_numpy() * r).sum())
        prev = pd.Series(w.to_numpy() * (1.0 + r) / (1.0 + port), index=w.index)
        if ledger is not None:
            held = pd.Index(sorted(set(ledger.lots) | {int(x) for x in w.index}))
            target = pd.Series(0.0, index=held)
            target.loc[[int(x) for x in w.index]] = w.to_numpy() * nav
            for permno in held:
                ledger.trade_to(int(permno), date, float(target[permno]))
            ledger.accrue_returns(pd.Series(r, index=[int(x) for x in w.index]))
            nav *= (1.0 + port)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main() -> None:
    p = argparse.ArgumentParser(description="TALS-like leverage x tax-awareness overhang sweep.")
    p.add_argument("--strategy", default="cell_N-C-P-0")
    p.add_argument("--gross", nargs="+", type=float, default=[2.0, 4.0, 6.0])
    p.add_argument("--regime", default="taxable_us_top_bracket")
    p.add_argument("--data", default=None)
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config("base")
    bundle = load_bundle(a.data or cfg["data_source"])
    risk = RiskCache(StructuralRiskModel(bundle, cfg))
    base = OptimizerConfig.from_files(cfg)
    preds = read_table(paths.latest_run("predictions", a.strategy), "predictions")

    rows, trajectories = [], []
    for gross in a.gross:
        for tax_aware in (False, True):
            started = time.time()
            label = f"gross={gross:g}, {'tax-aware' if tax_aware else 'tax-blind'}"
            log.info("=== %s ===", label)
            opt = OptimizerConfig(**{**base.__dict__, "gross_max": gross,
                                     "weight_abs_max": base.weight_abs_max * gross / 2.0,
                                     "tax_aware": tax_aware})
            weights = build(preds, bundle, cfg, risk, opt, tax_aware, a.regime)
            if weights.empty:
                log.warning("%s produced no weights", label)
                continue
            r = deferral_overhang(weights, bundle, cfg, regime=a.regime)
            d = harvesting_decomposition(weights, bundle, cfg, regime=a.regime)
            rows.append({"gross": gross, "tax_aware": tax_aware,
                         "months": r.months,
                         "pre_liquidation_ann": r.pre_liquidation_ann,
                         "liquidation_ann": r.liquidation_ann,
                         "overhang_share": r.overhang_share,
                         "embedded_gain_pct_nav": r.terminal_embedded_gain,
                         "carryforward_pct_nav": r.terminal_carryforward,
                         "deferred_tax_pct_nav": r.terminal_deferred_tax,
                         "realised_st_ann": d["realised_short_term_ann"],
                         "realised_lt_ann": d["realised_long_term_ann"],
                         "wash_disallowed_ann": d["wash_disallowed_ann"]})
            traj = overhang_trajectory(weights, bundle, cfg, regime=a.regime)
            traj.insert(0, "tax_aware", tax_aware)
            traj.insert(0, "gross", gross)
            trajectories.append(traj)
            log.info("%s done in %.1f min", label, (time.time() - started) / 60)

    if not rows:
        raise SystemExit("no cells completed")
    out = pd.DataFrame(rows)
    traj = pd.concat(trajectories, ignore_index=True)
    out.to_csv(paths.outputs_root() / "exp_tals_overhang.csv", index=False)
    traj.to_csv(paths.outputs_root() / "exp_tals_overhang_trajectory.csv", index=False)

    pd.set_option("display.width", 220)
    print("\n=== LEVERAGE x TAX-AWARENESS: does the overhang appear? ===")
    print(out.round(5).to_string(index=False))
    print("\n=== TRAJECTORY: does it compound as the book ages? ===")
    print(traj.round(5).to_string(index=False))
    _verdict(out, traj)


def _verdict(out: pd.DataFrame, traj: pd.DataFrame) -> None:
    print("\nverdict")
    hi = out[out["gross"] == out["gross"].max()]
    aware = hi[hi["tax_aware"]]
    blind = hi[~hi["tax_aware"]]
    if aware.empty or blind.empty:
        print("  incomplete sweep")
        return
    a_share = float(aware["overhang_share"].iloc[0])
    b_share = float(blind["overhang_share"].iloc[0])
    print(f"  at the highest gross, overhang share: tax-aware {a_share:+.4f} vs "
          f"tax-blind {b_share:+.4f}")

    worst = traj.loc[traj["overhang_share"].abs().idxmax()]
    print(f"  largest overhang anywhere in the sweep: {worst['overhang_share']:+.4f} "
          f"at gross={worst['gross']:g}, tax_aware={worst['tax_aware']}, "
          f"{worst['years']:.0f} years")

    grew = []
    for (g, t), sub in traj.groupby(["gross", "tax_aware"]):
        sub = sub.sort_values("months")
        if len(sub) >= 3 and sub["overhang_share"].iloc[-1] > sub["overhang_share"].iloc[0] + 0.02:
            grew.append((g, t))
    if grew:
        print(f"  overhang GREW with age in: {grew}")
        print("  consistent with the criticism: deferral accumulating rather than being recycled.")
    else:
        print("  overhang did NOT grow with age in any cell.")
        print("  the carryforward keeps cancelling the embedded gain, so on this book the")
        print("  'perpetually deferring' criticism does not bite. That is a result, not a defence")
        print("  of the product - our book is still not the levered, deliberately deferring")
        print("  design under dispute, and this runs on synthetic data.")


if __name__ == "__main__":
    main()
