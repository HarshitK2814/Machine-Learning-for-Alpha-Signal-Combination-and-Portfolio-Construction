"""Manifest appends must survive the schema changing.

The obvious implementation - ``to_csv(mode="a", header=not path.exists())`` - writes the header once
and never revisits it. The day a column is added, new rows have more fields than the header
promises and the file becomes unparseable. That happened here: a column added in one pipeline broke
a *different* pipeline weeks later, and the failure surfaced as a pandas ParserError in the middle
of a results run rather than at the point of the change.
"""
from __future__ import annotations

import pandas as pd
import pytest

from alphacomb.contracts import append_manifest
from alphacomb.contracts.io import _recover_csv


def test_append_to_a_missing_file_writes_a_header(tmp_path):
    path = tmp_path / "m.csv"
    append_manifest(pd.DataFrame([{"strategy": "a", "months": 12}]), path)
    out = pd.read_csv(path)
    assert list(out.columns) == ["strategy", "months"]
    assert len(out) == 1


def test_appending_the_same_schema_accumulates_rows(tmp_path):
    path = tmp_path / "m.csv"
    append_manifest(pd.DataFrame([{"strategy": "a", "months": 12}]), path)
    append_manifest(pd.DataFrame([{"strategy": "b", "months": 24}]), path)
    out = pd.read_csv(path)
    assert len(out) == 2
    assert list(out["strategy"]) == ["a", "b"]


def test_a_new_column_does_not_corrupt_the_file(tmp_path):
    """The regression: the second write has a column the first did not."""
    path = tmp_path / "m.csv"
    append_manifest(pd.DataFrame([{"strategy": "a", "months": 12}]), path)
    append_manifest(pd.DataFrame([{"strategy": "b", "months": 24, "held_share": 0.0}]), path)

    out = pd.read_csv(path)                      # must not raise ParserError
    assert len(out) == 2
    assert "held_share" in out.columns
    assert pd.isna(out.loc[0, "held_share"])     # the old row has no value, not a shifted one
    assert out.loc[1, "held_share"] == 0.0
    assert out.loc[0, "strategy"] == "a"         # fields did not slide across columns


def test_a_removed_column_keeps_the_old_rows_intact(tmp_path):
    path = tmp_path / "m.csv"
    append_manifest(pd.DataFrame([{"strategy": "a", "months": 12, "gamma": 25.0}]), path)
    append_manifest(pd.DataFrame([{"strategy": "b", "months": 24}]), path)
    out = pd.read_csv(path)
    assert len(out) == 2
    assert out.loc[0, "gamma"] == 25.0
    assert pd.isna(out.loc[1, "gamma"])


def test_recovery_of_a_file_already_damaged_by_the_old_writer(tmp_path):
    """Files written by the previous implementation still exist; they must be recoverable."""
    path = tmp_path / "m.csv"
    path.write_text(
        "strategy,months\n"          # stale two-column header
        "a,12\n"
        "b,24,0.5\n"                 # a row written after a column was added
        "c,36,0.0\n",
        encoding="utf-8")
    with pytest.raises(pd.errors.ParserError):
        pd.read_csv(path)

    recovered = _recover_csv(path)
    assert len(recovered) == 3
    assert list(recovered["strategy"]) == ["a", "b", "c"]
    assert len(recovered.columns) == 3           # header padded to the widest row

    # and an append onto the damaged file repairs it rather than failing
    append_manifest(pd.DataFrame([{"strategy": "d", "months": 48}]), path)
    out = pd.read_csv(path)
    assert len(out) == 4
    assert list(out["strategy"]) == ["a", "b", "c", "d"]
