#!/usr/bin/env python
"""Stage 04 (workstream B): turn predictions (C9) or proposals (C10) into portfolio weights (C11).

Prediction cells and baselines go through the cost-aware optimiser; economic-objective cells are
projected onto the same constraint set. Every strategy therefore faces identical limits and costs.

    python pipelines/04_construct_portfolios.py --strategies all
    python pipelines/04_construct_portfolios.py --strategies cell_L-S-P-0 --cost-multiplier 2.0
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alphacomb.contracts import load_bundle, load_config, new_run_id, paths, read_table, write_table  # noqa: E402
from alphacomb.portfolio import OptimizerConfig, construct, project  # noqa: E402
from alphacomb.risk import RiskCache, StructuralRiskModel  # noqa: E402

log = logging.getLogger("stage04")


def discover(kind: str) -> dict[str, Path]:
    root = paths.outputs_root() / kind
    out: dict[str, Path] = {}
    if not root.exists():
        return out
    for folder in sorted(root.iterdir()):
        latest = paths.latest_run(kind, folder.name)
        if latest is not None:
            out[folder.name] = latest
    return out


def build_weights(strategy: str, artefact: Path, kind: str, bundle, risk: RiskCache, cfg: OptimizerConfig,
                  run_id: str) -> Path:
    table = read_table(artefact)
    weights_rows, statuses = [], []
    prev: pd.Series | None = None
    returns = bundle.targets.set_index(["date", "permno"])["ret_next"]
    for date, group in table.groupby("date"):
        rm = risk.model(date)
        if kind == "predictions":
            alpha = pd.Series(group["alpha"].to_numpy(), index=group["permno"].to_numpy()).dropna()
            res = construct(date, alpha, prev, rm, bundle.cost_inputs, cfg)
        else:
            proposal = pd.Series(group["w_prop"].to_numpy(), index=group["permno"].to_numpy()).dropna()
            res = project(date, proposal, rm, bundle.cost_inputs, cfg)
        statuses.append(res.status)
        w = res.weights
        weights_rows.append(pd.DataFrame({"date": pd.Timestamp(date), "permno": w.index.astype("int32"),
                                          "w": w.to_numpy()}))
        # drift last month's weights with realised returns so next month's trade is measured honestly
        r = returns.reindex(pd.MultiIndex.from_product([[pd.Timestamp(date)], w.index])).fillna(0.0).to_numpy()
        drifted = w.to_numpy() * (1.0 + r)
        port_ret = float((w.to_numpy() * r).sum())
        prev = pd.Series(drifted / (1.0 + port_ret), index=w.index)
    frame = pd.concat(weights_rows, ignore_index=True)
    out = paths.weights_path(strategy, run_id)
    write_table(frame, out, "weights")
    log.info("%s: %d months, statuses %s", strategy, len(weights_rows), pd.Series(statuses).value_counts().to_dict())
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Construct portfolios from model outputs (contract C11).")
    p.add_argument("--strategies", nargs="+", default=["all"])
    p.add_argument("--data", default=None)
    p.add_argument("--gamma", type=float, default=None, help="risk aversion (default: configs/portfolio.yaml)")
    p.add_argument("--cost-multiplier", type=float, default=1.0, help="cost sensitivity (E31)")
    p.add_argument("--aum", type=float, default=None, help="AUM in 2020 dollars (E30/E32)")
    p.add_argument("--long-only", action="store_true")
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config("base")
    bundle = load_bundle(a.data or cfg["data_source"])
    risk = RiskCache(StructuralRiskModel(bundle, cfg))

    opt = OptimizerConfig.from_files(cfg)
    updates = {"cost_multiplier": a.cost_multiplier, "long_only": a.long_only}
    if a.gamma is not None:
        updates["gamma"] = a.gamma
    if a.aum is not None:
        updates["aum_usd"] = a.aum
    opt = OptimizerConfig(**{**opt.__dict__, **updates})

    available = {("predictions", k): v for k, v in discover("predictions").items()}
    available.update({("weight_proposals", k): v for k, v in discover("weight_proposals").items()})
    if not available:
        raise SystemExit("no model outputs found; run pipelines/02_train_models.py first")
    wanted = None if a.strategies == ["all"] else set(a.strategies)

    rows = []
    for (kind, strategy), artefact in sorted(available.items(), key=lambda kv: kv[0][1]):
        if wanted and strategy not in wanted:
            continue
        started = time.time()
        run_id = new_run_id(f"pf_{strategy}")
        out = build_weights(strategy, artefact, kind, bundle, risk, opt, run_id)
        rows.append({"strategy": strategy, "source_artefact": str(artefact), "weights": str(out),
                     "run_id": run_id, "cost_multiplier": a.cost_multiplier, "aum": opt.aum_usd,
                     "gamma": opt.gamma, "minutes": round((time.time() - started) / 60, 2)})
    manifest = pd.DataFrame(rows)
    path = paths.outputs_root() / "manifest_portfolios.csv"
    manifest.to_csv(path, mode="a", header=not path.exists(), index=False)
    print(manifest.to_string(index=False))
    print(f"\nmanifest: {path}")


if __name__ == "__main__":
    main()
