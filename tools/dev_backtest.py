#!/usr/bin/env python
"""TEMPORARY development backtest - delete when workstream A delivers ``alphacomb.backtest``.

Absar owns the real engine (contract C12). This stand-in exists only so workstream B can check its
own outputs end to end. It implements exactly the agreed cost formula, applies a one-month holding
period with weight drift, and writes a contract-valid C12 table so Maham's statistics code can be
developed against real files.

Known simplifications (documented so nobody mistakes this for the real engine):
* trades are assumed to execute at the month-end price, without the one-day implementation lag;
* no delisting-month special handling beyond what the targets table already applies;
* borrow costs use the monthly fee from C6 with no hard-to-borrow escalation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alphacomb.contracts import load_bundle, load_config, new_run_id, paths, read_table, write_table  # noqa: E402
from alphacomb.portfolio.cost_terms import cost_inputs_for, trade_cost_numpy  # noqa: E402


def backtest(weights: pd.DataFrame, bundle, cfg: dict, cost_multiplier: float = 1.0) -> pd.DataFrame:
    costs_cfg = cfg["costs"]
    aum = float(costs_cfg["aum_usd_2020"])
    k = float(costs_cfg["impact_k"]) * cost_multiplier
    commission = float(costs_cfg["commission_bps"])
    returns = bundle.targets.set_index(["date", "permno"])["ret_next"]

    rows = []
    prev = pd.Series(dtype=float)
    for date, group in weights.groupby("date"):
        w = pd.Series(group["w"].to_numpy(), index=group["permno"].to_numpy())
        idx = w.index.union(prev.index)
        w_full = w.reindex(idx).fillna(0.0)
        prev_full = prev.reindex(idx).fillna(0.0)
        ci = cost_inputs_for(date, bundle.cost_inputs, idx)
        dw = (w_full - prev_full).to_numpy()
        spread_cost = float((0.5 * ci["spread"].to_numpy() * cost_multiplier * np.abs(dw)).sum()
                            + commission / 10_000.0 * np.abs(dw).sum())
        total_cost = float(trade_cost_numpy(dw, ci["spread"].to_numpy() * cost_multiplier, ci["sigma_d"].to_numpy(),
                                            ci["adv_usd"].to_numpy(), aum, k, commission).sum())
        impact_cost = max(total_cost - spread_cost, 0.0)
        borrow_cost = float((ci["borrow_fee"].to_numpy() / 12.0 * np.clip(-w_full.to_numpy(), 0, None)).sum())

        r = returns.reindex(pd.MultiIndex.from_product([[pd.Timestamp(date)], idx])).fillna(0.0).to_numpy()
        gross = float((w_full.to_numpy() * r).sum())
        long_ret = float((np.clip(w_full.to_numpy(), 0, None) * r).sum())
        short_ret = float((np.clip(w_full.to_numpy(), None, 0) * r).sum())
        rows.append({"date": pd.Timestamp(date), "gross_ret": gross,
                     "net_ret": gross - spread_cost - impact_cost - borrow_cost,
                     "turnover": float(np.abs(dw).sum() / 2), "cost_spread": spread_cost,
                     "cost_impact": impact_cost, "cost_borrow": borrow_cost,
                     "long_ret": long_ret, "short_ret": short_ret})
        drifted = w_full.to_numpy() * (1.0 + r)
        prev = pd.Series(drifted / (1.0 + gross), index=idx)
    return pd.DataFrame(rows)


def summarise(returns: pd.DataFrame) -> dict:
    net, gross = returns["net_ret"], returns["gross_ret"]
    ann = np.sqrt(12)
    def sharpe(x):
        return float(x.mean() / x.std(ddof=1) * ann) if x.std(ddof=1) > 0 else float("nan")
    cum = (1 + net).cumprod()
    dd = float((cum / cum.cummax() - 1).min())
    return {"months": len(returns), "gross_sharpe": sharpe(gross), "net_sharpe": sharpe(net),
            "gross_mean_ann": float(gross.mean() * 12), "net_mean_ann": float(net.mean() * 12),
            "vol_ann": float(net.std(ddof=1) * ann), "max_drawdown": dd,
            "turnover_mean": float(returns["turnover"].mean()),
            "cost_drag_ann_bps": float((gross.mean() - net.mean()) * 12 * 10_000)}


def main() -> None:
    p = argparse.ArgumentParser(description="TEMPORARY stand-in backtest (workstream A owns the real one).")
    p.add_argument("--strategies", nargs="+", default=["all"])
    p.add_argument("--data", default=None)
    p.add_argument("--cost-multiplier", type=float, default=1.0)
    a = p.parse_args()

    cfg = load_config("base")
    bundle = load_bundle(a.data or cfg["data_source"])
    root = paths.outputs_root() / "weights"
    if not root.exists():
        raise SystemExit("no weights found; run pipelines/04_construct_portfolios.py first")

    summary = []
    for folder in sorted(root.iterdir()):
        if a.strategies != ["all"] and folder.name not in a.strategies:
            continue
        latest = paths.latest_run("weights", folder.name)
        if latest is None:
            continue
        weights = read_table(latest, "weights")
        out = backtest(weights, bundle, cfg, a.cost_multiplier)
        run_id = new_run_id(f"bt_{folder.name}")
        write_table(out, paths.returns_path(folder.name, run_id), "returns")
        summary.append({"strategy": folder.name, **summarise(out)})
    frame = pd.DataFrame(summary).sort_values("net_sharpe", ascending=False)
    path = paths.outputs_root() / "summary_dev_backtest.csv"
    frame.to_csv(path, index=False)
    print(frame.to_string(index=False))
    print(f"\nsummary: {path}\nNOTE: development stand-in, not the contract C12 engine.")


if __name__ == "__main__":
    main()
