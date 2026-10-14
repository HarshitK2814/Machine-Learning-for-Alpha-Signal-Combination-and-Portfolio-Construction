"""Shared fixtures: a small synthetic panel that every workstream's tests can use."""
from __future__ import annotations

import pandas as pd
import pytest

from alphacomb.contracts import DataBundle, read_table
from alphacomb.synthetic import generate


def bundle_from_dir(path) -> DataBundle:
    return DataBundle(
        universe=read_table(path / "universe.parquet"),
        signals=read_table(path / "signals.parquet"),
        signal_meta=pd.read_csv(path / "signal_meta.csv"),
        targets=read_table(path / "targets.parquet"),
        states=read_table(path / "states.parquet"),
        cost_inputs=read_table(path / "cost_inputs.parquet"),
        source="synthetic-test",
    )


@pytest.fixture(scope="session")
def small_panel(tmp_path_factory) -> DataBundle:
    """~120 stocks over 1990-2004: large enough to fit models, small enough for fast tests."""
    out = tmp_path_factory.mktemp("panel")
    generate(out, n_stocks=120, start="1990-01-31", end="2004-12-31", seed=11)
    return bundle_from_dir(out)


@pytest.fixture(scope="session")
def truncated_panel(tmp_path_factory) -> DataBundle:
    """Same seed and settings as ``small_panel`` but the raw panel is cut at 2000-12-31."""
    out = tmp_path_factory.mktemp("panel_trunc")
    generate(out, n_stocks=120, start="1990-01-31", end="2004-12-31", seed=11)
    b = bundle_from_dir(out)
    cut = pd.Timestamp("2000-12-31")
    return DataBundle(
        universe=b.universe[b.universe["date"] <= cut].copy(),
        signals=b.signals[b.signals["date"] <= cut].copy(),
        signal_meta=b.signal_meta,
        targets=b.targets[b.targets["date"] <= cut].copy(),
        states=b.states[b.states["date"] <= cut].copy(),
        cost_inputs=b.cost_inputs[b.cost_inputs["date"] <= cut].copy(),
        source="synthetic-test-truncated",
    )
