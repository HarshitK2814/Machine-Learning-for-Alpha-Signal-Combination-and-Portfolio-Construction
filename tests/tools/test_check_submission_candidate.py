"""The candidate consistency check must pass on the committed candidate and fail on each injected defect."""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools" / "check_submission_candidate.py"
spec = importlib.util.spec_from_file_location("check_submission_candidate", TOOL)
mod = importlib.util.module_from_spec(spec)
sys.modules["check_submission_candidate"] = mod
spec.loader.exec_module(mod)


@pytest.fixture()
def cand(tmp_path, monkeypatch):
    dst = tmp_path / "cand"
    shutil.copytree(mod.CAND, dst)
    monkeypatch.setattr(mod, "CAND", dst)
    return dst


def _edit(cand, old, new):
    p = cand / "manuscript.md"
    s = p.read_text(encoding="utf-8")
    assert old in s, old
    p.write_text(s.replace(old, new, 1), encoding="utf-8")


def test_committed_candidate_passes(cand):
    assert mod.check() == []


def test_altered_headline_number_fails(cand):
    _edit(cand, "| Germany | -0.709 |", "| Germany | -0.309 |")
    assert any("table1_DEU" in e for e in mod.check())


def test_altered_capacity_row_fails(cand):
    _edit(cand, "+5.09 | [+1.22, +9.03]", "+9.09 | [+1.22, +9.03]")
    assert any("table2_DEU_$1mn" in e for e in mod.check())


def test_unknown_citation_fails(cand):
    _edit(cand, "[@GKX2020]", "[@NOSUCHKEY2099]")
    errs = mod.check()
    assert any("NOSUCHKEY2099" in e for e in errs)


def test_tampered_artifact_hash_fails(cand):
    p = cand / "TRACEABILITY.csv"
    lines = p.read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1][:-8] + "deadbeef" if lines[1].endswith("yes") is False else lines[1].replace(lines[1].split(",")[2], "0" * 64)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert any("hash mismatch" in e for e in mod.check())


def test_undefined_table_reference_fails(cand):
    _edit(cand, "(Figure 1; Table 2)", "(Figure 1; Table 9)")
    assert any("Table 9" in e for e in mod.check())


def test_missing_disclosure_fails(cand):
    _edit(cand, "has **not been run**", "was skipped")
    assert any("required disclosure" in e for e in mod.check())


def test_approval_claim_is_banned(cand):
    _edit(cand, "## 8. Conclusion", "## 8. Conclusion\n\nMaham approved this analysis.")
    assert any("banned wording" in e for e in mod.check())


def test_bib_entry_without_provenance_fails(cand):
    p = cand / "BIB_PROVENANCE.csv"
    lines = [l for l in p.read_text(encoding="utf-8").splitlines() if not l.startswith("SS2018,")]
    p.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
    assert any("SS2018" in e and "PROVENANCE" in e for e in mod.check())


def test_preregistration_language_is_banned(cand):
    _edit(cand, "## 8. Conclusion", "## 8. Conclusion" + chr(10) * 2 + "This pre-registered analysis shows the result.")
    assert any("banned wording" in e for e in mod.check())


def test_japan_net_sharpe_statement_must_match_artifacts(cand):
    _edit(cand, "Japan's is +0.057 against Germany's +0.128", "Japan's is +0.157 against Germany's +0.128")
    assert any("p2" in e for e in mod.check())


def test_japan_rung_values_must_match_artifacts(cand):
    _edit(cand, "(-0.088, +0.057, -0.100)", "(-0.088, +0.157, -0.100)")
    assert any("jpn_rungs" in e for e in mod.check())
