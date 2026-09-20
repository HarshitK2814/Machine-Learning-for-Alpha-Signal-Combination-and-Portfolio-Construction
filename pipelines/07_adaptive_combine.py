#!/usr/bin/env python
"""Stage 07 (workstream B): the self-adapting combination, and the benchmarks it must beat.

Each member cell is scored month by month on the return a taxable investor actually keeps. An
exponentially weighted aggregator - fixed before the out-of-sample period, never tuned on it -
re-weights the members from those realised outcomes, and the combined alpha goes through the same
optimiser and the same after-tax ledger as everything else.

The output deliberately puts the adaptive row next to the equal-weighted blend and the best member
chosen in hindsight. Online aggregation frequently loses to an equal-weighted blend of the same
models; if that is what happened, the table says so.

    python pipelines/07_adaptive_combine.py --members cell_L-S-P-0 cell_N-S-P-0 cell_N-C-P-0
    python pipelines/07_adaptive_combine.py --members all --share 0.05 --regime taxable_us_top_bracket
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alphacomb.adaptive import (HedgeConfig, adaptation_report, build_members, combine,  # noqa: E402
                                compare, member_rewards, refit_schedule)
from alphacomb.adaptive.meta import equal_weight_alpha  # noqa: E402
from alphacomb.contracts import load_bundle, load_config, new_run_id, paths, write_table  # noqa: E402
from alphacomb.portfolio import OptimizerConfig, construct  # noqa: E402
from alphacomb.risk import RiskCache, StructuralRiskModel  # noqa: E402
from alphacomb.tax import TaxConfig, after_tax_backtest, get_regime  # noqa: E402

log = logging.getLogger("stage07")


def weights_from_alpha(alpha_table: pd.DataFrame, bundle, risk: RiskCache,
                       opt: OptimizerConfig) -> pd.DataFrame:
    """Run the combined alpha through the same optimiser every other strategy uses."""
    rows, prev = [], None
    returns = bundle.targets.set_index(["date", "permno"])["ret_next"]
    for date, group in alpha_table.groupby("date"):
        alpha = pd.Series(group["alpha"].to_numpy(), index=group["permno"].to_numpy()).dropna()
        if alpha.empty:
            continue
        res = construct(date, alpha, prev, risk.model(date), bundle.cost_inputs, opt)
        w = res.weights
        if w.empty:
            continue
        rows.append(pd.DataFrame({"date": pd.Timestamp(date), "permno": w.index.astype("int32"),
                                  "w": w.to_numpy()}))
        r = returns.reindex(pd.MultiIndex.from_product([[pd.Timestamp(date)], w.index])).fillna(0.0).to_numpy()
        port = float((w.to_numpy() * r).sum())
        prev = pd.Series(w.to_numpy() * (1.0 + r) / (1.0 + port), index=w.index)
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Self-adapting model combination (stage 07).")
    p.add_argument("--members", nargs="+", default=["all"])
    p.add_argument("--data", default=None)
    p.add_argument("--regime", default="taxable_us_top_bracket")
    p.add_argument("--reward", default="after_tax_ret",
                   choices=["after_tax_ret", "net_ret", "gross_ret"],
                   help="what the aggregator optimises; after-tax is the point of the exercise")
    p.add_argument("--eta", type=float, default=None, help="learning rate (default: parameter-free)")
    p.add_argument("--share", type=float, default=0.02, help="Herbster-Warmuth fixed share")
    p.add_argument("--warmup", type=int, default=12, help="months of equal weighting before adapting")
    p.add_argument("--aum", type=float, default=None)
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config("base")
    if a.aum is not None:
        cfg = {**cfg, "costs": {**cfg["costs"], "aum_usd_2020": a.aum}}
    bundle = load_bundle(a.data or cfg["data_source"])

    root = paths.outputs_root() / "predictions"
    names = ([f.name for f in sorted(root.iterdir())] if a.members == ["all"] else a.members)
    names = [n for n in names if paths.latest_run("weights", n) is not None]
    if len(names) < 2:
        raise SystemExit(f"need at least two members with weights; found {names}")
    log.info("members: %s", names)

    tax_cfg = TaxConfig(regime=get_regime(a.regime), initial_nav=float(cfg["costs"]["aum_usd_2020"]))
    members = build_members(names, bundle, cfg, tax_cfg)
    log.info("scored %d members on %s", len(members), a.reward)

    hedge_cfg = HedgeConfig(eta=a.eta, share=a.share, warmup=a.warmup)
    weight_panel, alpha_table = combine(members, hedge_cfg, a.reward)
    log.info("combination weights built for %d months", len(weight_panel))

    risk = RiskCache(StructuralRiskModel(bundle, cfg))
    opt = OptimizerConfig.from_files(cfg)
    if a.aum is not None:
        opt = OptimizerConfig(**{**opt.__dict__, "aum_usd": a.aum})
    weights = weights_from_alpha(alpha_table, bundle, risk, opt)
    run_id = new_run_id("pf_adaptive_hedge")
    write_table(weights, paths.weights_path("adaptive_hedge", run_id), "weights")

    combined_returns = after_tax_backtest(weights, bundle, cfg, tax_cfg)

    # The benchmark that actually isolates adaptation. "adaptive_hedge" averages member ALPHAS and
    # re-optimises once; averaging member RETURNS instead compares three separately optimised books.
    # Those differ for reasons that have nothing to do with the online rule - forecast averaging
    # smooths the alpha, which lowers turnover and cost. Holding the pipeline fixed and changing
    # only the weights is the comparison that answers "does adapting help?".
    log.info("building the fixed-weight alpha blend (the like-for-like benchmark)")
    eq_alpha = equal_weight_alpha(members)
    eq_weights = weights_from_alpha(eq_alpha, bundle, risk, opt)
    eq_returns = after_tax_backtest(eq_weights, bundle, cfg, tax_cfg)

    table = compare(members, combined_returns, a.reward, fixed_weight_returns=eq_returns)
    report = adaptation_report(weight_panel, members, a.reward)

    out_dir = paths.outputs_root()
    weight_panel.to_csv(out_dir / "adaptive_weights.csv", index=False)
    table.to_csv(out_dir / "summary_adaptive.csv", index=False)
    (out_dir / "adaptive_report.json").write_text(json.dumps(report, indent=2, default=str),
                                                  encoding="utf-8")
    rewards = member_rewards(members, a.reward)
    refit_schedule(rewards.mean(axis=1)).to_csv(out_dir / "adaptive_refit_schedule.csv", index=False)

    pd.set_option("display.width", 220)
    print(table.round(4).to_string(index=False))
    print("\nadaptation:")
    for key in ("mean_effective_members", "weight_turnover_monthly", "regret_bound", "best_member"):
        print(f"  {key}: {report[key]}")
    print(f"  final weights: {report['final_weights']}")
    print(f"  drift events: {report['drift_events']}")
    print(f"\nwrote {out_dir / 'summary_adaptive.csv'}")
    _verdict(table)


def _verdict(table: pd.DataFrame) -> None:
    """State plainly whether ADAPTATION earned its place - not whether blending did."""
    try:
        adaptive = float(table[table["kind"] == "adaptive"]["after_tax_sharpe"].iloc[0])
        best_member = float(table[table["kind"] == "member"]["after_tax_sharpe"].max())
    except (IndexError, KeyError, ValueError):
        return
    fixed = table[table["strategy"] == "equal_weight_alpha"]["after_tax_sharpe"]
    print("\nverdict")
    print(f"  adaptive {adaptive:.3f} vs best single member {best_member:.3f}")
    if not len(fixed):
        print("  NO like-for-like benchmark was built, so this says nothing about adaptation.")
        return
    fixed = float(fixed.iloc[0])
    gap = adaptive - fixed
    print(f"  adaptive {adaptive:.3f} vs FIXED equal-weight alpha blend {fixed:.3f}  ({gap:+.3f})")
    print("  The second line is the one that matters: same members, same optimiser, same ledger,")
    print("  only the combination weights differ. The first line mostly measures the value of")
    print("  averaging forecasts, which is not what the adaptive rule is for.")
    if gap <= 0.02:
        print("  ADAPTATION DID NOT PAY. The online rule is no better than fixing the weights at")
        print("  1/N. Report that. It matches Remlinger et al. (2023), who find the uniform")
        print("  mixture beats their online rule on small-cap stocks.")


if __name__ == "__main__":
    main()
