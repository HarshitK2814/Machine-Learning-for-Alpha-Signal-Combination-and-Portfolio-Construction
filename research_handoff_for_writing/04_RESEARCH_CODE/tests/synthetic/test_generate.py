"""The synthetic panel must satisfy every contract and contain the effects it claims to plant."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from alphacomb.contracts import read_table, validate
from alphacomb.synthetic import generate


@pytest.fixture(scope="module")
def panel(tmp_path_factory):
    out = tmp_path_factory.mktemp("syn")
    written = generate(out, n_stocks=90, start="1990-01-31", end="2000-12-31", seed=7)
    return out, written


def test_all_contracts_validate(panel):
    out, _ = panel
    for name, file in [("universe", "universe.parquet"), ("signals", "signals.parquet"),
                       ("targets", "targets.parquet"), ("states", "states.parquet"),
                       ("cost_inputs", "cost_inputs.parquet")]:
        validate(read_table(out / file), name)
    meta = pd.read_csv(out / "signal_meta.csv")
    validate(meta, "signal_meta")
    signals = read_table(out / "signals.parquet")
    assert set(meta["signal"]) <= set(signals.columns)


def test_panel_is_realistic(panel):
    out, _ = panel
    universe = read_table(out / "universe.parquet")
    costs = read_table(out / "cost_inputs.parquet")
    targets = read_table(out / "targets.parquet")

    assert universe["in_universe"].mean() > 0.3          # a usable universe survives the filters
    assert universe.groupby("date")["permno"].nunique().std() > 0  # entry and exit happen
    assert universe["permno"].nunique() > 90             # firms are replaced over time

    merged = universe.merge(costs, on=["date", "permno"])
    small = merged["me"] < merged["me"].median()
    assert merged.loc[small, "spread"].mean() > merged.loc[~small, "spread"].mean()  # small = costlier
    late = merged["date"].dt.year >= 2001
    if late.any():
        assert merged.loc[late, "spread"].mean() < merged.loc[~late, "spread"].mean()  # decimalisation

    r = targets["r_1m"].dropna()
    assert 0.03 < r.std() < 0.35 and abs(r.mean()) < 0.05
    assert targets["r_1m"].isna().mean() < 0.2           # only the tail of each firm's life is NaN


def test_signals_are_informative_but_noisy(panel):
    out, _ = panel
    signals = read_table(out / "signals.parquet")
    targets = read_table(out / "targets.parquet")
    df = signals.merge(targets, on=["date", "permno"]).dropna(subset=["r_1m"])
    value_cols = [c for c in signals.columns if c.startswith("sig_value")]
    ic = df.groupby("date").apply(lambda d: d[value_cols[0]].corr(d["r_1m"]), include_groups=False)
    assert 0.0 < ic.mean() < 0.15, "a single noisy signal should have a small positive IC"

    composite = df[value_cols].mean(axis=1)
    ic_theme = df.assign(c=composite).groupby("date").apply(lambda d: d["c"].corr(d["r_1m"]), include_groups=False)
    assert ic_theme.mean() > ic.mean(), "averaging signals inside a theme must raise IC (redundancy)"


def test_truth_file_documents_the_planted_effects(panel):
    out, _ = panel
    truth = json.loads((out / "truth.json").read_text())
    assert truth["coefficients"]["b_value_x_quality"] != 0
    assert truth["coefficients"]["b_momentum_crash"] < 0 < truth["coefficients"]["b_momentum_normal"]
    assert truth["n_signals"] > 100


def test_states_are_lagged_and_standardised(panel):
    out, _ = panel
    states = read_table(out / "states.parquet")
    cols = [c for c in states.columns if c not in {"date", "BEAR"}]
    assert states["date"].is_monotonic_increasing
    assert np.isfinite(states[cols].to_numpy()).all()
    tail = states[cols].iloc[60:]
    assert tail.abs().to_numpy().max() <= 5.0            # clipped standardised values
    assert set(states["BEAR"].unique()) <= {0.0, 1.0}
