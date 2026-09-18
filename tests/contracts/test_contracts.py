"""Contract tests: schemas, split calendar, lockbox guard and cell definitions. SHARED."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from alphacomb.contracts import schemas, splits
from alphacomb.contracts.interfaces import ALL_CELLS, CellSpec


def _signals(n: int = 20) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    dates = pd.to_datetime(["2000-01-31"] * n)
    df = pd.DataFrame({"date": dates, "permno": np.arange(n, dtype="int32")})
    for k in range(12):
        df[f"sig_{k}"] = rng.uniform(-0.5, 0.5, n)
    df["miss_value"] = np.zeros(n, dtype="int8")
    return df


def test_signal_schema_accepts_valid_frame():
    schemas.validate(_signals(), "signals")


def test_signal_schema_rejects_out_of_range_values():
    df = _signals()
    df.loc[0, "sig_0"] = 1.5
    with pytest.raises(schemas.SchemaError, match=r"\[-0.5, 0.5\]"):
        schemas.validate(df, "signals")


def test_schema_rejects_duplicate_keys():
    df = _signals()
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    with pytest.raises(schemas.SchemaError, match="duplicated"):
        schemas.validate(df, "signals")


def test_schema_rejects_missing_column():
    df = _signals().drop(columns=["permno"])
    with pytest.raises(schemas.SchemaError, match="missing required columns"):
        schemas.validate(df, "signals")


def test_schema_allows_extra_columns_additive_change():
    df = _signals()
    df["new_optional_column"] = 1.0
    schemas.validate(df, "signals")


@pytest.mark.parametrize("horizon", [1, 3, 12])
def test_splits_have_embargo_and_are_ordered(horizon):
    calendar = splits.generate(horizon_months=horizon)
    assert len(calendar) == 26  # 1995-2020 development test years
    for s in calendar:
        s.assert_no_leakage()
        assert s.train_start < s.train_end < s.val_start < s.val_end < s.test_start < s.test_end
        gap = (s.test_start.to_period("M") - s.val_end.to_period("M")).n
        assert gap > horizon


def test_splits_never_reach_into_the_lockbox():
    for s in splits.generate(horizon_months=12):
        assert s.test_end < pd.Timestamp("2021-01-31")


def test_lockbox_requires_freeze_tag(monkeypatch):
    monkeypatch.delenv("ALPHACOMB_FREEZE_TAG", raising=False)
    with pytest.raises(splits.LockboxError):
        splits.assert_not_lockbox(pd.to_datetime(["2022-06-30"]))
    with pytest.raises(splits.LockboxError):
        splits.generate(include_lockbox=True)
    monkeypatch.setenv("ALPHACOMB_FREEZE_TAG", "v-freeze")
    splits.assert_not_lockbox(pd.to_datetime(["2022-06-30"]))  # allowed after the freeze
    assert splits.generate(include_lockbox=True)[-1].test_year == 2025
    os.environ.pop("ALPHACOMB_FREEZE_TAG", None)


def test_sixteen_cells_with_unique_codes_and_balanced_contrasts():
    assert len(ALL_CELLS) == 16
    assert len({c.code for c in ALL_CELLS}) == 16
    frame = pd.DataFrame([c.contrasts() for c in ALL_CELLS])
    assert (frame.sum() == 0).all(), "contrast coding must be orthogonal (each column sums to zero)"


def test_cell_round_trip_and_experiment_ids():
    spec = CellSpec.parse("n-c-e-u")
    assert spec.code == "N-C-E-U"
    assert spec.experiment == "E27+E28"
    assert CellSpec.parse("L-S-P-0").experiment == "E20"
    with pytest.raises(ValueError):
        CellSpec.parse("X-S-P-0")
