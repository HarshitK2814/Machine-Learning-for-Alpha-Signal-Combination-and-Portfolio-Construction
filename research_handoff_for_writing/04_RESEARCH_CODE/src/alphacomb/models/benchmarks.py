"""Published ML benchmarks (workstream B, experiment E13).

These are *not* new cells. They are the published configurations the paper has to beat or match, run
through exactly the same design matrix, split calendar, alpha scaling, optimiser and cost model as
the factorial cells, so the comparison is about the model rather than the plumbing.

* ``gkx_nn3``  - the three-hidden-layer network configuration used in the Gu, Kelly and Xiu (2020)
  style horse race: 32-16-8 with L1 penalty and early stopping, ensembled over seeds.
* ``gkx_gbrt`` - their gradient-boosted regression trees, with shallow trees and a small learning rate.
* ``jkmp_portfolio_ml`` - a placeholder that documents how the Jensen, Kelly, Malamud and Pedersen
  (2026) Portfolio-ML benchmark will be produced: their public R code is run separately and its
  weights are dropped in as contract C11 under the strategy name below. It is *not* reimplemented
  here, because a home-grown version would be a weaker straw man than the authors' own code.
"""
from __future__ import annotations

import logging

import pandas as pd

from ..contracts import DataBundle, new_run_id, paths, splits as split_mod, write_table
from ..contracts.interfaces import CellSpec
from ..contracts.io import load_config, read_yaml
from ..risk.cache import RiskCache
from .base import build_design
from .cells import CellRunConfig, run_prediction_cell
from .nonlinear import LGBMCell, NNCell

log = logging.getLogger(__name__)

JKMP_STRATEGY = "benchmark_jkmp_portfolio_ml"

PRESETS = {
    "gkx_nn3": dict(kind="nn", layers=(32, 16, 8), l1=1e-4, learning_rate=1e-3, max_epochs=60,
                    patience=5, n_members=5),
    "gkx_gbrt": dict(kind="lgbm", num_leaves=15, learning_rate=0.01, min_data_in_leaf=1000,
                     feature_fraction=0.5, lambda_l2=10.0, num_boost_round=2000, n_members=1),
}


def _candidate(name: str, seed: int, fast: bool):
    cfg = dict(PRESETS[name])
    kind = cfg.pop("kind")
    if fast:
        cfg["n_members"] = min(int(cfg.get("n_members", 1)), 2)
        if kind == "nn":
            cfg["max_epochs"] = 15
        else:
            cfg["num_boost_round"] = 300
    if kind == "nn":
        model = NNCell(seed=seed, **cfg)
    else:
        model = LGBMCell(early_stopping_rounds=50, seed=seed, **cfg)
    params = {"benchmark": name, **{k: (list(v) if isinstance(v, tuple) else v) for k, v in cfg.items()}}
    return model, params


def run_benchmark(name: str, bundle: DataBundle, risk: RiskCache, cfg: CellRunConfig | None = None,
                  base_cfg: dict | None = None, models_cfg: dict | None = None) -> dict:
    """Run one published benchmark configuration and write contract C9."""
    if name not in PRESETS:
        raise KeyError(f"unknown benchmark '{name}'; available: {sorted(PRESETS)} (plus {JKMP_STRATEGY})")
    cfg = cfg or CellRunConfig()
    base_cfg = base_cfg or load_config("base")
    models_cfg = models_cfg or read_yaml(paths.REPO_ROOT / "configs" / "models.yaml")
    run_id = new_run_id(f"benchmark_{name}")
    strategy = f"benchmark_{name}"

    # Published benchmarks are static, prediction-loss models without uncertainty shrinkage.
    spec = CellSpec.parse("N-S-P-0")
    df, features = build_design(bundle, spec, horizon=cfg.horizon)
    calendar = split_mod.generate(horizon_months=cfg.horizon, cfg=base_cfg,
                                  first_test_year=cfg.first_test_year, last_test_year=cfg.last_test_year)
    df = df[df["date"] <= calendar[-1].test_end].copy()
    split_mod.assert_not_lockbox(df["date"].unique(), base_cfg)
    risk.warm([d for d in sorted(df["date"].unique()) if pd.Timestamp(d) >= calendar[0].val_start])

    # Reuse the cell runner but with a single fixed candidate, so the benchmark gets the same
    # treatment (validation IC, alpha scaling, trial logging) as every cell.
    import alphacomb.models.cells as cells_module

    original = cells_module._candidates
    cells_module._candidates = lambda spec_, models_cfg_, features_, cfg_: [_candidate(name, cfg.seed, cfg.fast)]
    try:
        table = run_prediction_cell(spec, df, features, calendar, risk, cfg, base_cfg, models_cfg, run_id, strategy)
    finally:
        cells_module._candidates = original

    out = paths.predictions_path(strategy, run_id)
    write_table(table, out, "predictions")
    return {"benchmark": name, "experiment": "E13", "strategy": strategy, "run_id": run_id,
            "artefact": out, "contract": "predictions", "rows": len(table)}


def jkmp_instructions() -> str:
    """How to add the Portfolio-ML benchmark without reimplementing it."""
    return (
        "Portfolio-ML (Jensen, Kelly, Malamud & Pedersen 2026) is run from the authors' public code\n"
        "(github.com/theisij/ml-and-the-implementable-efficient-frontier) on the same universe and\n"
        "signal library, with our cost parameters. Export their monthly weights as a parquet file\n"
        f"with columns date, permno, w and place it at outputs/weights/{JKMP_STRATEGY}/<run_id>.parquet.\n"
        "From that point it flows through our backtest and statistics like any other strategy."
    )
