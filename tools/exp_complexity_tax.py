#!/usr/bin/env python
"""Falsify our own premise: does model complexity shorten holding periods?

The gap in ``03_Research_Gaps/GAP_The_Tax_Wedge_in_Complexity.md`` rests on one mechanism:

    complexity  ->  more transient signal  ->  holding-period distribution shifts left
                ->  realisations move from the long-term rate to the short-term rate
                ->  an after-tax penalty that turnover does not capture

If the long-term share of realised gains does NOT fall as complexity rises, the mechanism is dead
and we should abandon the framing this week rather than after a real-data build. That is what this
script tests, and it is deliberately set up so the answer can be no.

Unlike ``models.complexity.candidates``, which picks the best complexity by validation and so
collapses the sweep, this keeps **every** rung as its own strategy. The point is the gradient, not
the winner.

    python tools/exp_complexity_tax.py --years 2015 2020 --grid 0.25 0.5 1 2 4

Writes ``outputs/exp_complexity_tax.csv``.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alphacomb.contracts import load_bundle, load_config, paths  # noqa: E402
from alphacomb.contracts import splits as split_mod  # noqa: E402
from alphacomb.contracts.interfaces import CellSpec  # noqa: E402
from alphacomb.models.base import build_design, rank_ic, split_frames  # noqa: E402
from alphacomb.models.complexity import ComplexityCell  # noqa: E402
from alphacomb.portfolio import OptimizerConfig, construct  # noqa: E402
from alphacomb.portfolio.alpha_scaling import grinold_alpha  # noqa: E402
from alphacomb.risk import RiskCache, StructuralRiskModel  # noqa: E402
from alphacomb.tax import TaxConfig, after_tax_backtest, get_regime, summarise_after_tax  # noqa: E402

log = logging.getLogger("exp_complexity")


def run_rung(n_feat: int, penalty: str, bundle, cfg, risk, opt, calendar, df, features, seed: int,
             train_rows: int):
    """Walk-forward one complexity rung and return its predictions (contract C9 shape).

    Complexity is indexed by the **feature count P**, with the training sample subsampled to a
    fixed ``train_rows`` so that ``c = P / T`` actually sweeps - including past c = 1 into the
    interpolating regime the virtue-of-complexity literature is about.

    Why the subsample is necessary rather than a shortcut: on the full panel T is ~300k stock-months,
    so reaching c = 1 would need 300k random features (a 300k x 300k design matrix, ~700 GB). Kelly,
    Malamud and Zhou work in the small-T large-P regime; on a panel we have to create it deliberately.
    The cost is noisier fits, which is acceptable because this is a mechanism test, not a
    performance claim.
    """
    rows = []
    rng = np.random.default_rng(seed)
    for split in calendar:
        train, val, test = split_frames(df, split)
        if train.empty or val.empty or test.empty:
            continue
        if len(train) > train_rows:
            train = train.iloc[rng.choice(len(train), size=train_rows, replace=False)]
        c = n_feat / max(len(train), 1)
        model = ComplexityCell(complexity=c, penalty=penalty, max_features=n_feat,
                               alpha=1e-6 if penalty == "ridge" else 1e-4, seed=seed)
        model.fit(train, val, features.all, "y")
        val_pred = model.predict(val, features.all)["score"].to_numpy()
        ic = rank_ic(val_pred, val["y"].to_numpy(), val["date"])
        scores = model.predict(test, features.all)
        frame = test[["date", "permno"]].copy()
        frame["score"] = scores["score"].to_numpy()
        frame["val_ic"] = ic if np.isfinite(ic) else 0.0
        frame["c"] = c
        rows.append(frame)
    if not rows:
        return None
    out = pd.concat(rows, ignore_index=True)
    # Grinold scaling per month with that split's validation IC, exactly as the main pipeline does,
    # so rungs are comparable and a higher-IC rung is not simply handed a bigger book.
    alphas = []
    for date, group in out.groupby("date"):
        scores = pd.Series(group["score"].to_numpy(), index=group["permno"].to_numpy())
        a = grinold_alpha(scores, risk.model(date), float(group["val_ic"].iloc[0]))
        alphas.append(pd.DataFrame({"date": date, "permno": a.index, "alpha": a.to_numpy()}))
    scaled = pd.concat(alphas, ignore_index=True)
    return out.merge(scaled, on=["date", "permno"], how="inner")


def weights_for(preds: pd.DataFrame, bundle, risk, opt) -> pd.DataFrame:
    rows, prev = [], None
    returns = bundle.targets.set_index(["date", "permno"])["ret_next"]
    for date, group in preds.groupby("date"):
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
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main() -> None:
    p = argparse.ArgumentParser(description="Complexity x tax mechanism test (P1/P2/P3).")
    p.add_argument("--features", nargs="+", type=int, default=[50, 200, 500, 1000, 2000, 4000],
                   help="number of random features P; with --train-rows this sweeps c = P/T")
    p.add_argument("--train-rows", type=int, default=2000,
                   help="subsample size T, so that c = P/T crosses the interpolating boundary")
    p.add_argument("--penalty", default="ridge", choices=["ridge", "l1"])
    p.add_argument("--years", nargs=2, type=int, default=[2015, 2020])
    p.add_argument("--data", default=None)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--regimes", nargs="+",
                   default=["tax_exempt", "taxable_us_top_bracket", "trader_475f_mtm"])
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config("base")
    bundle = load_bundle(a.data or cfg["data_source"])
    risk = RiskCache(StructuralRiskModel(bundle, cfg))
    opt = OptimizerConfig.from_files(cfg)

    spec = CellSpec.parse("N-S-P-0")          # nonlinear static: the complexity arm lives here
    df, features = build_design(bundle, spec, horizon=1)
    calendar = split_mod.generate(horizon_months=1, cfg=cfg,
                                  first_test_year=a.years[0], last_test_year=a.years[1])
    df = df[df["date"] <= calendar[-1].test_end].copy()
    split_mod.assert_not_lockbox(df["date"].unique(), cfg)

    results = []
    for n_feat in a.features:
        started = time.time()
        log.info("=== P = %d features (T = %d, c = %.3g), %s ===",
                 n_feat, a.train_rows, n_feat / a.train_rows, a.penalty)
        preds = run_rung(n_feat, a.penalty, bundle, cfg, risk, opt, calendar, df, features,
                         a.seed, a.train_rows)
        if preds is None or preds.empty:
            log.warning("P=%d produced no predictions", n_feat)
            continue
        weights = weights_for(preds, bundle, risk, opt)
        if weights.empty:
            log.warning("P=%d produced no weights", n_feat)
            continue
        c = float(preds["c"].iloc[0])
        for regime in a.regimes:
            tc = TaxConfig(regime=get_regime(regime),
                           initial_nav=float(cfg["costs"]["aum_usd_2020"]))
            frame = after_tax_backtest(weights, bundle, cfg, tc)
            s = summarise_after_tax(frame)
            results.append({"n_features": n_feat, "complexity": c, "penalty": a.penalty, "regime": regime,
                            "months": s["months"], "val_ic": float(preds["val_ic"].iloc[0]),
                            "turnover_mean": s["turnover_mean"],
                            "lt_share_of_gains": s["lt_share_of_gains"],
                            "tax_share_of_gross": s["tax_share_of_gross"],
                            "tax_drag_ann_bps": s["tax_drag_ann_bps"],
                            "cost_drag_ann_bps": s["cost_drag_ann_bps"],
                            "net_sharpe": s["net_sharpe"],
                            "after_tax_sharpe": s["after_tax_sharpe"],
                            "gross_sharpe": s["gross_sharpe"]})
        log.info("P=%d done in %.1f min", n_feat, (time.time() - started) / 60)

    if not results:
        raise SystemExit("no rungs completed")
    out = pd.DataFrame(results)
    path = paths.outputs_root() / "exp_complexity_tax.csv"
    out.to_csv(path, index=False)
    pd.set_option("display.width", 220)
    print(out.round(4).to_string(index=False))
    print(f"\nwrote {path}")
    _verdict(out)


def _verdict(out: pd.DataFrame) -> None:
    """P1 is the gate. If long-term share does not fall in complexity, the mechanism is dead."""
    tax = out[out["regime"] == "taxable_us_top_bracket"].sort_values("complexity")
    if len(tax) < 3:
        print("\nnot enough rungs to judge")
        return
    from scipy import stats

    rho_lt, p_lt = stats.spearmanr(tax["complexity"], tax["lt_share_of_gains"])
    rho_to, p_to = stats.spearmanr(tax["complexity"], tax["turnover_mean"])
    rho_ts, p_ts = stats.spearmanr(tax["complexity"], tax["tax_share_of_gross"])

    print("\nP1  long-term share of gains vs complexity : "
          f"Spearman {rho_lt:+.3f} (p={p_lt:.3f})   [predicted: NEGATIVE]")
    print(f"    turnover vs complexity                 : Spearman {rho_to:+.3f} (p={p_to:.3f})")
    print(f"P2  tax share of gross vs complexity       : Spearman {rho_ts:+.3f} (p={p_ts:.3f})"
          "   [predicted: POSITIVE]")
    print(f"    turnover spread across rungs           : "
          f"{tax['turnover_mean'].max() / max(tax['turnover_mean'].min(), 1e-9):.2f}x")
    print(f"    tax-share spread across rungs          : "
          f"{tax['tax_share_of_gross'].max() / max(tax['tax_share_of_gross'].min(), 1e-9):.2f}x")

    print("\nP3  is net-of-cost rising while after-tax turns over?")
    for _, r in tax.iterrows():
        print(f"    c={r['complexity']:<6.3g} net {r['net_sharpe']:+.3f}   after-tax {r['after_tax_sharpe']:+.3f}")
    best_net = tax.loc[tax["net_sharpe"].idxmax(), "complexity"]
    print(f"    argmax net-of-cost  c = {best_net:g}")
    for regime, g in out.groupby("regime"):
        g = g.sort_values("complexity")
        print(f"    argmax after-tax [{regime}] c = {g.loc[g['after_tax_sharpe'].idxmax(), 'complexity']:g}")

    print("\nVERDICT")
    if rho_lt < -0.5:
        print("  P1 SUPPORTED on this sample: complexity shortens holding periods.")
    elif rho_lt > 0.5:
        print("  P1 REJECTED, and in the WRONG DIRECTION: complexity lengthens holding periods.")
        print("  The tax-wedge mechanism as written is dead. Do not build on it.")
    else:
        print("  P1 NOT SUPPORTED: no monotone relationship between complexity and holding period.")
        print("  The mechanism is not visible on this sample. Treat the gap as unproven.")
    print("  Synthetic data. The holding-period distribution here is an artefact of the generator,")
    print("  so a positive result is permission to continue, never evidence for the paper.")


if __name__ == "__main__":
    main()
