"""Coverage of the output-collision guard across the fixed-path writers named in the finalization audit (P0-6).

For every guarded writer: (a) ``--overwrite`` is exposed; (b) a pre-existing output of unknown origin makes the run stop with
``OutputCollision`` BEFORE any work, leaving the file untouched. No experiment is run.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pytest

from alphacomb.output_guard import OutputCollision, claim_run, sidecar_path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))


def _load(rel: str):
    spec = importlib.util.spec_from_file_location("guard_cov_" + Path(rel).stem.replace(".", "_"), ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# (module path, argv builder given a tmp dir, existing legacy file relative to that dir, takes argv?)
CASES = {
    "design_identifiability": ("tools/exp_design_identifiability.py",
                               lambda t: ["--out", str(t)], "design_identifiability_DEU.csv", True),
    "friction_horse_race": ("tools/exp_friction_horse_race.py",
                            lambda t: ["--out", str(t)], "horse_race_decile_panel.csv", True),
    "event_study_112a": ("tools/exp_112a_event_study.py",
                         lambda t: ["--out", str(t)], "event_112a.csv", True),
    "wedge_test": ("tools/exp_wedge_test.py",
                   lambda t: ["--inputs", "x", "--out", str(t)], "wedge_test.csv", True),
    "tals_overhang": ("tools/exp_tals_overhang.py", lambda t: [], "exp_tals_overhang.csv", False),
    "adaptive_combine": ("pipelines/07_adaptive_combine.py", lambda t: [], "adaptive_weights.csv", False),
    "after_tax_eval_summary": ("pipelines/06_after_tax_eval.py",
                               lambda t: ["--out", str(t / "summary_after_tax.csv")], "summary_after_tax.csv", False),
}


def _run(mod, takes_argv, argv, monkeypatch):
    if takes_argv:
        return mod.main(argv)
    monkeypatch.setattr(sys, "argv", ["tool", *argv])
    return mod.main()


@pytest.mark.parametrize("name", list(CASES))
def test_writer_exposes_overwrite(name, monkeypatch, capsys):
    rel, _, _, takes_argv = CASES[name]
    mod = _load(rel)
    with pytest.raises(SystemExit):
        _run(mod, takes_argv, ["--help"], monkeypatch)
    assert "--overwrite" in capsys.readouterr().out


@pytest.mark.parametrize("name", list(CASES))
def test_unknown_origin_output_is_refused_before_any_work(name, tmp_path, monkeypatch):
    rel, argv_of, legacy, takes_argv = CASES[name]
    mod = _load(rel)
    monkeypatch.setenv("ALPHACOMB_OUTPUTS", str(tmp_path))
    f = tmp_path / legacy
    f.write_text("earlier output")
    with pytest.raises(OutputCollision):
        _run(mod, takes_argv, argv_of(tmp_path), monkeypatch)
    assert f.read_text() == "earlier output"              # untouched
    assert not sidecar_path(f).exists()                    # and no record was fabricated for it


def test_claim_run_uses_the_parsed_arguments_and_honours_overwrite(tmp_path):
    f = tmp_path / "x.csv"
    a = argparse.Namespace(country=["DEU"], n_boot=1000, overwrite=False, out=tmp_path)
    claim_run([f], a)
    f.write_text("1")
    claim_run([f], argparse.Namespace(country=["DEU"], n_boot=1000, overwrite=False, out=tmp_path))   # same run
    with pytest.raises(OutputCollision):
        claim_run([f], argparse.Namespace(country=["DEU", "IND"], n_boot=1000, overwrite=False, out=tmp_path))
    claim_run([f], argparse.Namespace(country=["DEU", "IND"], n_boot=1000, overwrite=True, out=tmp_path))
