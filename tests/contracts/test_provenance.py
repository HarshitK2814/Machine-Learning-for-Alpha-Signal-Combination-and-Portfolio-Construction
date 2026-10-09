"""Country provenance must fail loudly, because the silent failure is indistinguishable from success.

``outputs/weights/<strategy>/`` and ``outputs/predictions/<strategy>/`` are shared across
countries and ``paths.latest_run`` resolves by modification time. Four separate consumers were
caught by that in one night: a Germany exhibit resolving to India's book, an IC diagnostic
comparing Japan's scores against India's targets, a book-characteristics table printing India's
leverage under a German heading, and stage 04 itself, which would have built German portfolios from
Japanese predictions.

Every one of those produced a *plausible* number. None of them produced an error. That is why the
resolver raises rather than falling back, and why these tests assert the refusals rather than the
happy path.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from alphacomb.contracts import paths, provenance
from alphacomb.contracts.provenance import MissingProvenance


@pytest.fixture
def outputs(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "outputs_root", lambda: tmp_path)
    return tmp_path


def write_index(root: Path, country: str, rows: list[dict], aum: str = "1e9") -> Path:
    index_dir = root / "weights_index"
    index_dir.mkdir(parents=True, exist_ok=True)
    path = index_dir / f"{country}_{aum}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def make_weights(root: Path, strategy: str, run_id: str) -> Path:
    folder = root / "weights" / strategy
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{run_id}.parquet"
    path.write_bytes(b"not really a parquet, only its existence is checked here")
    return path


# ------------------------------------------------------------------ the refusals

def test_a_missing_index_raises_instead_of_resolving_by_mtime(outputs):
    """The whole point. A fallback here is what scored one country's book in another's panel."""
    with pytest.raises(MissingProvenance, match="no weights index"):
        provenance.country_weights("JPN")


def test_the_error_names_how_to_recover(outputs):
    """An error that does not say what to do gets worked around rather than fixed."""
    with pytest.raises(MissingProvenance) as exc:
        provenance.country_weights("JPN")
    message = str(exc.value)
    assert "modification time" in message
    assert "tools/weights_index.py" in message


def test_an_index_that_omits_a_requested_strategy_raises(outputs):
    p = make_weights(outputs, "cell_L-S-P-0", "pf_a")
    write_index(outputs, "IND", [{"country": "IND", "aum": 1e9, "strategy": "cell_L-S-P-0",
                                  "run_id": "pf_a", "weights": str(p)}])
    with pytest.raises(MissingProvenance, match="does not cover"):
        provenance.country_weights("IND", strategies=["cell_L-S-P-0", "cell_N-C-E-U"])


def test_an_index_naming_a_vanished_file_raises(outputs):
    write_index(outputs, "IND", [{"country": "IND", "aum": 1e9, "strategy": "cell_L-S-P-0",
                                  "run_id": "pf_a", "weights": str(outputs / "gone.parquet")}])
    with pytest.raises(MissingProvenance, match="does not exist"):
        provenance.country_weights("IND")


def test_source_artefacts_refuses_when_the_manifest_has_no_matching_runs(outputs):
    p = make_weights(outputs, "cell_L-S-P-0", "pf_a")
    write_index(outputs, "DEU", [{"country": "DEU", "aum": 1e9, "strategy": "cell_L-S-P-0",
                                  "run_id": "pf_a", "weights": str(p)}])
    pd.DataFrame([{"strategy": "cell_L-S-P-0", "run_id": "pf_SOMETHING_ELSE",
                   "source_artefact": "x.parquet"}]).to_csv(
        outputs / "manifest_portfolios.csv", index=False)
    with pytest.raises(MissingProvenance, match="no rows for the run ids"):
        provenance.country_source_artefacts("DEU")


# ------------------------------------------------------------------ the happy path

def test_resolves_each_strategy_to_the_file_its_own_run_wrote(outputs):
    a = make_weights(outputs, "cell_L-S-P-0", "pf_deu")
    b = make_weights(outputs, "cell_N-C-E-U", "pf_deu2")
    write_index(outputs, "DEU", [
        {"country": "DEU", "aum": 1e9, "strategy": "cell_L-S-P-0", "run_id": "pf_deu",
         "weights": str(a)},
        {"country": "DEU", "aum": 1e9, "strategy": "cell_N-C-E-U", "run_id": "pf_deu2",
         "weights": str(b)},
    ])
    got = provenance.country_weights("DEU")
    assert got == {"cell_L-S-P-0": a, "cell_N-C-E-U": b}


def test_a_newer_file_from_another_country_is_ignored(outputs):
    """The regression this module exists for.

    India writes a newer artefact for the same cell. ``latest_run`` would return India's; the
    resolver must still return Germany's, because that is what Germany's index names.
    """
    german = make_weights(outputs, "cell_L-S-P-0", "pf_deu_older")
    indian = make_weights(outputs, "cell_L-S-P-0", "pf_ind_newer")
    import os
    import time

    now = time.time()
    os.utime(german, (now - 3600, now - 3600))
    os.utime(indian, (now, now))
    assert paths.latest_run("weights", "cell_L-S-P-0") == indian, "fixture precondition"

    write_index(outputs, "DEU", [{"country": "DEU", "aum": 1e9, "strategy": "cell_L-S-P-0",
                                  "run_id": "pf_deu_older", "weights": str(german)}])
    assert provenance.country_weights("DEU")["cell_L-S-P-0"] == german


def test_country_cells_drops_the_comparators(outputs):
    cell = make_weights(outputs, "cell_L-S-P-0", "pf_a")
    base = make_weights(outputs, "baseline_BASE-EW", "pf_b")
    write_index(outputs, "DEU", [
        {"country": "DEU", "aum": 1e9, "strategy": "cell_L-S-P-0", "run_id": "pf_a",
         "weights": str(cell)},
        {"country": "DEU", "aum": 1e9, "strategy": "baseline_BASE-EW", "run_id": "pf_b",
         "weights": str(base)},
    ])
    assert set(provenance.country_cells("DEU")) == {"cell_L-S-P-0"}


def test_different_aum_arms_are_separate_indexes(outputs):
    a = make_weights(outputs, "cell_L-S-P-0", "pf_1e9")
    b = make_weights(outputs, "cell_L-S-P-0", "pf_1e10")
    write_index(outputs, "DEU", [{"country": "DEU", "aum": 1e9, "strategy": "cell_L-S-P-0",
                                  "run_id": "pf_1e9", "weights": str(a)}], aum="1e9")
    write_index(outputs, "DEU", [{"country": "DEU", "aum": 1e10, "strategy": "cell_L-S-P-0",
                                  "run_id": "pf_1e10", "weights": str(b)}], aum="1e10")
    assert provenance.country_weights("DEU", "1e9")["cell_L-S-P-0"] == a
    assert provenance.country_weights("DEU", "1e10")["cell_L-S-P-0"] == b


# ------------------------------------------------------------------ the real repo

def test_the_real_indexes_resolve_if_they_exist():
    """Guards the published exhibits: every index on disk must name files that are still there."""
    root = paths.outputs_root() / "weights_index"
    if not root.exists():
        pytest.skip("no weights indexes in this checkout")
    found = sorted(root.glob("*.csv"))
    if not found:
        pytest.skip("no weights indexes in this checkout")
    for index in found:
        country, aum = index.stem.split("_", 1)
        resolved = provenance.country_weights(country, aum)
        assert resolved, f"{index.name} resolved to nothing"
