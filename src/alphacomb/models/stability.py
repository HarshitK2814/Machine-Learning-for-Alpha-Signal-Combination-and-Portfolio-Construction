"""Seed and hyperparameter stability (workstream B, experiment E56).

Neural cells are stochastic. If the spread of results across seeds is comparable to the gap between
factorial cells, then the attribution is noise. This module runs a cell under several seeds and
reports the dispersion so the paper can state it rather than hope it is small.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..contracts import DataBundle
from ..contracts.interfaces import CellSpec
from ..risk.cache import RiskCache
from .cells import CellRunConfig, run_cell


def run_seeds(spec: CellSpec | str, bundle: DataBundle, risk: RiskCache, seeds: list[int],
              cfg: CellRunConfig | None = None, base_cfg: dict | None = None) -> pd.DataFrame:
    """Run the same cell under several seeds; returns one row per seed with its artefact path."""
    spec = CellSpec.parse(spec) if isinstance(spec, str) else spec
    rows = []
    for seed in seeds:
        run_cfg = CellRunConfig(**{**(cfg or CellRunConfig()).__dict__, "seed": seed, "diagnostics": []})
        result = run_cell(spec, bundle, risk, run_cfg, base_cfg=base_cfg)
        diag = pd.read_csv(result["diagnostics"])
        rows.append({"cell": spec.code, "seed": seed, "artefact": str(result["artefact"]),
                     "mean_val_ic": diag["val_rank_ic"].mean() if "val_rank_ic" in diag else np.nan,
                     "mean_test_ic": diag["test_rank_ic"].mean() if "test_rank_ic" in diag else np.nan,
                     "mean_val_utility": diag["val_utility"].mean() if "val_utility" in diag else np.nan})
    return pd.DataFrame(rows)


def dispersion(seed_results: pd.DataFrame, metric: str = "mean_test_ic") -> dict:
    """Summary of seed dispersion; compare this with the gap between cells before claiming an effect."""
    values = seed_results[metric].dropna().to_numpy(dtype=float)
    if len(values) < 2:
        return {"metric": metric, "n_seeds": int(len(values)), "mean": float(values.mean()) if len(values) else np.nan,
                "sd": np.nan, "min": np.nan, "max": np.nan, "range": np.nan}
    return {"metric": metric, "n_seeds": int(len(values)), "mean": float(values.mean()),
            "sd": float(values.std(ddof=1)), "min": float(values.min()), "max": float(values.max()),
            "range": float(values.max() - values.min())}


def compare_to_cell_gap(seed_results: pd.DataFrame, cell_gap: float, metric: str = "mean_test_ic") -> dict:
    """Is the measured difference between two cells larger than seed noise?"""
    disp = dispersion(seed_results, metric)
    ratio = abs(cell_gap) / disp["sd"] if disp["sd"] and np.isfinite(disp["sd"]) and disp["sd"] > 0 else np.inf
    return {**disp, "cell_gap": float(cell_gap), "gap_over_seed_sd": float(ratio),
            "verdict": "gap exceeds seed noise" if ratio > 2 else "gap is within seed noise"}
