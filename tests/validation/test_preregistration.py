"""Pre-registration. The trial count is only honest if it was fixed before anyone saw a result."""
from __future__ import annotations

import json

import pandas as pd
import pytest

from alphacomb.validation.preregistration import PreRegistration, audit, factorial_plan


def _plan(**kw) -> PreRegistration:
    return factorial_plan(
        cells=["L-S-P-0", "N-S-P-0"],
        grid={"alpha": [0.1, 1.0, 10.0], "depth": [2, 4]},
        title="test", primary_outcome="after-tax Sharpe",
        selection_rule="best validation rank IC", **kw)


def test_planned_count_is_computed_from_the_grid_not_asserted():
    plan = _plan()
    assert plan.n_planned_trials == 2 * 3 * 2            # cells x alpha x depth
    assert _plan(n_seeds=5).n_planned_trials == 2 * 3 * 2 * 5
    assert _plan(n_refits=4).n_planned_trials == 2 * 3 * 2 * 4


def test_configurations_inside_the_grid_are_planned_and_others_are_not():
    plan = _plan()
    assert plan.is_planned("L-S-P-0", {"alpha": 1.0, "depth": 4})
    assert not plan.is_planned("L-S-P-0", {"alpha": 7.0, "depth": 4}), "value outside the grid"
    assert not plan.is_planned("L-S-P-0", {"alpha": 1.0}), "missing a planned dimension"


def test_fingerprint_changes_when_the_grid_changes():
    a = _plan().fingerprint
    b = factorial_plan(cells=["L-S-P-0", "N-S-P-0"],
                       grid={"alpha": [0.1, 1.0, 10.0, 100.0], "depth": [2, 4]},
                       title="test", primary_outcome="after-tax Sharpe",
                       selection_rule="best validation rank IC").fingerprint
    assert a != b


def test_a_plan_is_written_once(tmp_path):
    path = tmp_path / "plan.json"
    _plan().save(path)
    with pytest.raises(FileExistsError, match="written once"):
        _plan().save(path)


def test_round_trip_preserves_the_plan(tmp_path):
    path = tmp_path / "plan.json"
    original = _plan(n_seeds=3)
    original.save(path)
    loaded = PreRegistration.load(path)
    assert loaded.fingerprint == original.fingerprint
    assert loaded.n_planned_trials == original.n_planned_trials


def test_editing_a_frozen_plan_is_detected(tmp_path):
    """The failure this guards: quietly widening the grid after seeing results."""
    path = tmp_path / "plan.json"
    _plan().save(path)
    blob = json.loads(path.read_text(encoding="utf-8"))
    blob["grids"]["default"]["alpha"] = [0.1, 1.0, 10.0, 100.0, 1000.0]
    path.write_text(json.dumps(blob), encoding="utf-8")

    with pytest.raises(ValueError, match="edited since it was frozen"):
        PreRegistration.load(path)


def _trials(rows):
    return pd.DataFrame([{"cell": c, "params_json": json.dumps(p)} for c, p in rows])


def test_audit_reports_a_clean_run():
    plan = _plan()
    rows = [(c, {"alpha": a, "depth": d})
            for c in plan.cells for a in [0.1, 1.0, 10.0] for d in [2, 4]]
    out = audit(plan, _trials(rows))
    assert out["clean"]
    assert out["exploratory_trials"] == 0
    assert out["drift"] == 0
    assert out["n_for_deflation"] == plan.n_planned_trials


def test_audit_catches_configurations_outside_the_plan():
    plan = _plan()
    rows = [("L-S-P-0", {"alpha": 1.0, "depth": 2}),
            ("L-S-P-0", {"alpha": 999.0, "depth": 2}),      # outside the grid
            ("N-S-P-0", {"alpha": 0.1, "depth": 4})]
    out = audit(plan, _trials(rows))
    assert out["exploratory_trials"] == 1
    assert not out["clean"]
    assert "PLAN DRIFT" in out["verdict"]


def test_deflation_count_never_shrinks_below_what_was_actually_fitted():
    """The core protection: you cannot argue N down after seeing the results."""
    plan = _plan()                                          # plans 12
    rows = [("L-S-P-0", {"alpha": a, "depth": d})
            for a in [0.1, 1.0, 10.0, 100.0, 1000.0] for d in [2, 4, 8]]   # fits 15
    out = audit(plan, _trials(rows))
    assert out["actual_trials"] == 15
    assert out["planned_trials"] == 12
    assert out["n_for_deflation"] == 15, "the larger, more conservative count must win"
    assert out["drift"] == 3


def test_unparseable_trial_rows_count_as_exploratory_not_ignored():
    plan = _plan()
    frame = pd.DataFrame([{"cell": "L-S-P-0", "params_json": "not json"}])
    out = audit(plan, frame)
    assert out["exploratory_trials"] == 1
