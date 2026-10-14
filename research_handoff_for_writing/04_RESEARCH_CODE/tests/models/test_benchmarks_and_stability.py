"""Benchmarks (E13) and seed stability (E56) tests."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.contracts import read_table, validate
from alphacomb.models import CellRunConfig, PRESETS, compare_to_cell_gap, dispersion, jkmp_instructions, run_benchmark
from alphacomb.risk import RiskCache, StructuralRiskModel


def test_benchmark_presets_are_documented():
    assert set(PRESETS) == {"gkx_nn3", "gkx_gbrt"}
    assert "Portfolio-ML" in jkmp_instructions()
    assert "outputs/weights/benchmark_jkmp_portfolio_ml" in jkmp_instructions()


def test_gbrt_benchmark_runs_and_writes_predictions(small_panel, tmp_path, monkeypatch):
    monkeypatch.setenv("ALPHACOMB_OUTPUTS", str(tmp_path))
    risk = RiskCache(StructuralRiskModel(small_panel))
    cfg = CellRunConfig(horizon=1, first_test_year=2003, last_test_year=2003, fast=True)
    result = run_benchmark("gkx_gbrt", small_panel, risk, cfg)
    table = read_table(result["artefact"])
    validate(table, "predictions")
    assert result["experiment"] == "E13"
    assert set(pd.to_datetime(table["date"]).dt.year) == {2003}
    trials = pd.read_csv(tmp_path / "trials.csv")
    assert (trials["strategy"] == "benchmark_gkx_gbrt").any()


def test_unknown_benchmark_is_rejected(small_panel):
    risk = RiskCache(StructuralRiskModel(small_panel))
    with pytest.raises(KeyError, match="unknown benchmark"):
        run_benchmark("not_a_benchmark", small_panel, risk)


def test_dispersion_and_cell_gap_verdict():
    frame = pd.DataFrame({"cell": "N-S-P-0", "seed": [0, 1, 2, 3], "mean_test_ic": [0.030, 0.034, 0.028, 0.032]})
    d = dispersion(frame)
    assert d["n_seeds"] == 4 and 0 < d["sd"] < 0.01
    assert compare_to_cell_gap(frame, cell_gap=0.001)["verdict"] == "gap is within seed noise"
    assert compare_to_cell_gap(frame, cell_gap=0.020)["verdict"] == "gap exceeds seed noise"


def test_dispersion_handles_a_single_seed():
    frame = pd.DataFrame({"cell": "N-S-P-0", "seed": [0], "mean_test_ic": [0.03]})
    d = dispersion(frame)
    assert d["n_seeds"] == 1 and np.isnan(d["sd"])
