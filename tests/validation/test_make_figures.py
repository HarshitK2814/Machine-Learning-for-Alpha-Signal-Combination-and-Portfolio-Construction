"""Figures come from committed snapshots, label solvent versus insolvent comparisons, and are traceable (audit task P0-7)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import make_figures as mf  # noqa: E402
from alphacomb.output_guard import OutputCollision  # noqa: E402


def test_inputs_are_tracked_results_files_only():
    for p in mf.INPUTS:
        assert p.exists(), p
        assert "outputs" not in p.relative_to(ROOT).parts and p.relative_to(ROOT).parts[0] == "results"


@pytest.mark.parametrize("country", mf.COUNTRIES)
def test_no_b_is_drawn_at_an_insolvent_rung(country):
    d = mf.b_series(country)
    ins = d[d.status == "insolvent"]
    assert ins[["B_A", "B_B"]].isna().all().all()                     # never plotted, never interpolated
    sol = d[d.status == "solvent"]
    assert sol[["B_A", "B_B"]].notna().all().all()


def test_insolvent_rungs_match_the_phase2_counts():
    counts = {c: int((mf.b_series(c).status == "insolvent").sum()) for c in mf.COUNTRIES}
    assert counts == {"DEU": 3, "IND": 4, "JPN": 0}


def test_near_ruined_is_a_flag_on_solvent_rungs_not_an_exclusion():
    d = mf.b_series("DEU")
    assert d["near_ruined"].any()                                      # the flag fires for ruined-but-solvent rungs
    flagged = d[d.near_ruined]
    assert (flagged.status == "solvent").all() and flagged["B_B"].notna().all()   # still carries its B value
    assert (flagged.wealth_B < mf.NEAR_RUINED_WEALTH).all()


def test_build_writes_traceable_figures_and_refuses_a_collision(tmp_path):
    out = tmp_path / "figs"
    m = mf.build(out)
    assert len(m["figures"]) == 4 and all((out / n).stat().st_size > 5000 for n in m["figures"])
    man = json.loads((out / "FIGURE_MANIFEST.json").read_text())
    assert set(man["inputs_sha256"]) == {p.relative_to(ROOT).as_posix() for p in mf.INPUTS}
    assert man["script_sha256"] and man["matplotlib"] and man["solvency_rule"]
    assert all(len(v["sha256"]) == 64 for v in man["figures"].values())
    mf.build(out)                                                      # same inputs and code: a re-run is allowed
    # a differently parameterised run into the same directory is refused
    sidecar = out / ".run.json"
    rec = json.loads(sidecar.read_text())
    rec["fingerprint"] = "0" * 64
    sidecar.write_text(json.dumps(rec))
    with pytest.raises(OutputCollision):
        mf.build(out)
