"""Output-collision guard, second tranche (overnight sprint 2026-10-14).

Infrastructure tests and synthetic fixtures only: no experiment is run. For every newly guarded writer:
(a) ``--overwrite`` is exposed; (b) a pre-existing output of unknown origin stops the run with ``OutputCollision``
BEFORE any computation, leaves that file untouched and fabricates no provenance record for it.
``claim_run_items`` (per-item fingerprints) is tested directly for same-configuration reruns, conflicting
configurations, legacy outputs, validate-before-record and ``--overwrite``.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from alphacomb.output_guard import OutputCollision, claim_run_items, sidecar_path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))


def _load(rel: str):
    spec = importlib.util.spec_from_file_location("guard_ext_" + Path(rel).stem.replace(".", "_"), ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# name: (module, argv builder, legacy file relative to tmp, main takes argv?, directory claim?)
CASES = {
    "matched_book": ("tools/exp_matched_book_accounting.py", lambda t: ["--out", str(t)], "matched_book_1e+09.csv", True, False),
    "theme_liquidity": ("tools/exp_theme_liquidity_terciles.py", lambda t: ["--out", str(t), "--country", "DEU"],
                        "theme_liquidity_DEU.csv", True, False),
    "capacity_channel_inference": ("tools/exp_capacity_channel_inference.py", lambda t: ["--out", str(t), "--country", "DEU"],
                                   "capacity_channel_inference_DEU.csv", True, False),
    "after_tax_inference": ("tools/exp_after_tax_inference.py", lambda t: ["--out", str(t)], "after_tax_inference_1e9.csv", True, False),
    "gate2_power": ("tools/gate2_power.py", lambda t: ["--out", str(t)], "gate2_power_1e+09.csv", True, False),
    "book_characteristics": ("tools/exp_book_characteristics.py", lambda t: ["--out", str(t)], "capacity_DEU.csv", True, False),
    "capacity_dose_response": ("tools/exp_capacity_dose_response.py", lambda t: ["--out", str(t)], "dose_panel_DEU.csv", True, False),
    "factorial_prediction_arm": ("tools/exp_factorial_prediction_arm.py", lambda t: ["--out", str(t)], "factorial_P_DEU.csv", True, False),
    "e02_e03": ("tools/exp_e02_e03_signal_diagnostics.py", lambda t: ["--out", str(t), "--countries", "DEU"],
                "e02_e03_summary.csv", True, False),
    "e29_attribution": ("tools/exp_e29_attribution.py", lambda t: ["--out", str(t)], "e29_cells.csv", True, True),
    "exhibit_provenance": ("tools/exhibit_provenance.py", lambda t: ["--out", str(t / "chain.csv")], "chain.csv", True, False),
    "complexity_tax": ("tools/exp_complexity_tax.py", lambda t: [], "exp_complexity_tax.csv", False, False),
    "dev_backtest": ("tools/dev_backtest.py", lambda t: [], "summary_dev_backtest.csv", False, False),
    "verify_projection_fidelity": ("tools/verify_projection_fidelity.py", lambda t: ["--out", str(t / "fid.csv")], "fid.csv", True, False),
    "verify_workstream_a_receipt": ("tools/verify_workstream_a_receipt.py", lambda t: ["--json", str(t / "receipt.json")],
                                    "receipt.json", True, False),
}


def _run(mod, takes_argv, argv, monkeypatch):
    if takes_argv:
        return mod.main(argv)
    monkeypatch.setattr(sys, "argv", ["tool", *argv])
    return mod.main()


@pytest.mark.parametrize("name", list(CASES))
def test_writer_exposes_overwrite(name, monkeypatch, capsys):
    rel, _, _, takes_argv, _ = CASES[name]
    mod = _load(rel)
    with pytest.raises(SystemExit):
        _run(mod, takes_argv, ["--help"], monkeypatch)
    assert "--overwrite" in capsys.readouterr().out


@pytest.mark.parametrize("name", list(CASES))
def test_unknown_origin_output_is_refused_before_any_work(name, tmp_path, monkeypatch):
    rel, argv_of, legacy, takes_argv, is_dir = CASES[name]
    mod = _load(rel)
    monkeypatch.setenv("ALPHACOMB_OUTPUTS", str(tmp_path))
    f = tmp_path / legacy
    f.write_text("earlier output")
    before = sorted(p.name for p in tmp_path.iterdir())
    with pytest.raises(OutputCollision):
        _run(mod, takes_argv, argv_of(tmp_path), monkeypatch)
    assert f.read_text() == "earlier output"                                  # untouched
    assert sorted(p.name for p in tmp_path.iterdir()) == before               # nothing created, no record fabricated
    assert not sidecar_path(f).exists()
    assert not (tmp_path / ".run.json").exists()


def test_verify_arm_information_refuses_a_legacy_output_before_work(tmp_path, monkeypatch, capsys):
    mod = _load("tools/verify_arm_information.py")
    monkeypatch.setattr(mod, "ROOT", tmp_path)                       # keep the repository's real outputs out of the test
    legacy = tmp_path / "outputs" / "arm_information" / "arm_information_DEU.csv"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("earlier output")
    with pytest.raises(SystemExit):
        mod.main(["--help"])
    assert "--overwrite" in capsys.readouterr().out
    with pytest.raises(OutputCollision):
        mod.main(["--country", "DEU", "--from-weights-index"])
    assert legacy.read_text() == "earlier output" and not sidecar_path(legacy).exists()


# --------------------------------------------------------------------------------------- claim_run_items
def _ns(**kw):
    kw.setdefault("overwrite", False)
    return argparse.Namespace(**kw)


def _items(tmp, countries):
    return [(tmp / f"t_{c}.csv", {"country": c}) for c in countries]


def test_same_configuration_rerun_is_allowed(tmp_path):
    a = _ns(country=["DEU", "IND"], n_boot=100, out=tmp_path)
    claim_run_items(_items(tmp_path, a.country), a)
    for c in a.country:
        (tmp_path / f"t_{c}.csv").write_text("x")
    claim_run_items(_items(tmp_path, a.country), a)                            # identical parameters: proceeds


def test_a_different_country_list_does_not_collide_on_shared_files_but_different_settings_do(tmp_path):
    a = _ns(country=["DEU", "IND"], n_boot=100, out=tmp_path)
    claim_run_items(_items(tmp_path, a.country), a)
    for c in a.country:
        (tmp_path / f"t_{c}.csv").write_text("x")
    claim_run_items(_items(tmp_path, ["IND", "JPN"]), _ns(country=["IND", "JPN"], n_boot=100, out=tmp_path))   # IND same settings
    with pytest.raises(OutputCollision):
        claim_run_items(_items(tmp_path, ["DEU"]), _ns(country=["DEU"], n_boot=500, out=tmp_path))          # same file, other n_boot
    assert (tmp_path / "t_DEU.csv").read_text() == "x"


def test_legacy_output_without_a_record_is_refused_and_not_modified(tmp_path):
    (tmp_path / "t_DEU.csv").write_text("legacy")
    with pytest.raises(OutputCollision):
        claim_run_items(_items(tmp_path, ["DEU"]), _ns(country=["DEU"], out=tmp_path))
    assert (tmp_path / "t_DEU.csv").read_text() == "legacy"
    assert not sidecar_path(tmp_path / "t_DEU.csv").exists()                   # no provenance fabricated


def test_refusal_on_a_later_item_leaves_no_record_for_earlier_items(tmp_path):
    (tmp_path / "t_IND.csv").write_text("legacy")
    with pytest.raises(OutputCollision):
        claim_run_items(_items(tmp_path, ["DEU", "IND"]), _ns(country=["DEU", "IND"], out=tmp_path))
    assert not sidecar_path(tmp_path / "t_DEU.csv").exists()


def test_overwrite_replaces_the_record_and_is_the_only_way_past_a_conflict(tmp_path):
    a = _ns(country=["DEU"], n_boot=100, out=tmp_path)
    claim_run_items(_items(tmp_path, ["DEU"]), a)
    (tmp_path / "t_DEU.csv").write_text("x")
    b = _ns(country=["DEU"], n_boot=900, out=tmp_path)
    with pytest.raises(OutputCollision):
        claim_run_items(_items(tmp_path, ["DEU"]), b)
    claim_run_items(_items(tmp_path, ["DEU"]), _ns(country=["DEU"], n_boot=900, out=tmp_path, overwrite=True))
    rec = json.loads(sidecar_path(tmp_path / "t_DEU.csv").read_text())
    assert rec["params"]["n_boot"] == 900
    claim_run_items(_items(tmp_path, ["DEU"]), b)                              # the new configuration now reruns freely


def test_empty_and_default_tags_are_distinct_parameters(tmp_path):
    claim_run_items([(tmp_path / "o.csv", None)], _ns(tag="", out=tmp_path))
    (tmp_path / "o.csv").write_text("x")
    with pytest.raises(OutputCollision):
        claim_run_items([(tmp_path / "o.csv", None)], _ns(tag="default", out=tmp_path))
