"""Canonical paths. SHARED FILE - nobody hard-codes paths anywhere else."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def data_root() -> Path:
    return Path(os.environ.get("ALPHACOMB_DATA", REPO_ROOT / "data"))


def outputs_root() -> Path:
    return Path(os.environ.get("ALPHACOMB_OUTPUTS", REPO_ROOT / "outputs"))


def processed_dir(source: str = "synthetic") -> Path:
    """``source`` is 'synthetic' or 'real' (configs/base.yaml: data_source)."""
    return data_root() / source


def universe_path(source: str = "synthetic") -> Path:
    return processed_dir(source) / "universe.parquet"


def signals_path(source: str = "synthetic") -> Path:
    return processed_dir(source) / "signals.parquet"


def signal_meta_path(source: str = "synthetic") -> Path:
    return processed_dir(source) / "signal_meta.csv"


def targets_path(source: str = "synthetic") -> Path:
    return processed_dir(source) / "targets.parquet"


def states_path(source: str = "synthetic") -> Path:
    return processed_dir(source) / "states.parquet"


def states_placebo_path(source: str = "synthetic") -> Path:
    return processed_dir(source) / "states_placebo.parquet"


def cost_inputs_path(source: str = "synthetic") -> Path:
    return processed_dir(source) / "cost_inputs.parquet"


def truth_path(source: str = "synthetic") -> Path:
    """Planted data-generating process of the synthetic data (never available for real data)."""
    return processed_dir(source) / "truth.json"


def predictions_path(strategy: str, run_id: str) -> Path:
    return outputs_root() / "predictions" / strategy / f"{run_id}.parquet"


def weight_proposals_path(strategy: str, run_id: str) -> Path:
    return outputs_root() / "weight_proposals" / strategy / f"{run_id}.parquet"


def weights_path(strategy: str, run_id: str) -> Path:
    return outputs_root() / "weights" / strategy / f"{run_id}.parquet"


def returns_path(strategy: str, run_id: str) -> Path:
    return outputs_root() / "returns" / strategy / f"{run_id}.parquet"


def interpret_path(strategy: str, run_id: str, name: str) -> Path:
    return outputs_root() / "interpret" / strategy / f"{run_id}__{name}.csv"


def trials_path() -> Path:
    return outputs_root() / "trials.csv"


def models_dir(strategy: str, run_id: str) -> Path:
    return outputs_root() / "models" / strategy / run_id


def latest_run(kind: str, strategy: str) -> Path | None:
    """Most recent artefact of ``kind`` ('predictions', 'weights', ...) for a strategy."""
    folder = outputs_root() / kind / strategy
    if not folder.exists():
        return None
    files = sorted(folder.glob("*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None
