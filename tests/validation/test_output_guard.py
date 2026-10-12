"""Output-collision protection (audit task P0-6): differently tagged or parameterised runs cannot overwrite each other."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from alphacomb.output_guard import OutputCollision, claim_output, fingerprint, sidecar_path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

BASE = {"country": "DEU", "aum": [1e5, 1e6], "weighting": "ew", "tag": "cov"}


def test_first_claim_is_recorded(tmp_path):
    f = tmp_path / "wedge_DEU_cov.csv"
    fp = claim_output(f, BASE)
    rec = json.loads(sidecar_path(f).read_text(encoding="utf-8"))
    assert rec["fingerprint"] == fp == fingerprint(BASE) and rec["params"]["tag"] == "cov"


def test_rerun_of_the_same_job_is_allowed(tmp_path):
    f = tmp_path / "out.csv"
    claim_output(f, BASE)
    f.write_text("x")
    claim_output(f, dict(BASE))                       # identical parameters: a re-run


def test_different_parameters_with_the_same_tag_are_refused(tmp_path):
    f = tmp_path / "out.csv"
    claim_output(f, BASE)
    f.write_text("x")
    with pytest.raises(OutputCollision):
        claim_output(f, {**BASE, "aum": [1e5, 1e6, 1e7]})   # a different AUM ladder under the same tag
    assert f.read_text() == "x"


def test_existing_output_without_a_record_is_refused(tmp_path):
    f = tmp_path / "legacy.csv"
    f.write_text("legacy")
    with pytest.raises(OutputCollision):
        claim_output(f, BASE)


def test_overwrite_flag_replaces_the_record(tmp_path):
    f = tmp_path / "out.csv"
    claim_output(f, BASE)
    f.write_text("x")
    new = {**BASE, "weighting": "vw"}
    fp = claim_output(f, new, overwrite=True)
    assert json.loads(sidecar_path(f).read_text())["fingerprint"] == fp == fingerprint(new)


def test_empty_tag_and_default_tag_collide_on_the_shared_weights_directory(tmp_path):
    # the wedge tool maps tag "" and tag "default" to the same weights directory
    d = tmp_path / "decile_weights" / "DEU" / "default" / "aum_1e+05"
    claim_output(d, {**BASE, "tag": ""}, is_dir=True)
    (d / "uncapped_L-S-P-0.parquet").write_bytes(b"w")
    with pytest.raises(OutputCollision):
        claim_output(d, {**BASE, "tag": "default"}, is_dir=True)


def test_differently_tagged_runs_with_distinct_paths_do_not_interfere(tmp_path):
    a, b = tmp_path / "wedge_DEU_a.csv", tmp_path / "wedge_DEU_b.csv"
    claim_output(a, {**BASE, "tag": "a"})
    claim_output(b, {**BASE, "tag": "b"})
    assert fingerprint({**BASE, "tag": "a"}) != fingerprint({**BASE, "tag": "b"})


def test_wedge_tool_exposes_the_overwrite_flag(capsys):
    import exp_signal_vs_portfolio_wedge as w
    with pytest.raises(SystemExit):
        w.main(["--help"])
    assert "--overwrite" in capsys.readouterr().out
