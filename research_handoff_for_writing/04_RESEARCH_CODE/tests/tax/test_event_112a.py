"""The section 112A event study rests on two things that fail silently if they are wrong.

The first is India's April-March tax year. Label it as a calendar year and the treatment date lands
in the wrong bucket, which moves observations across the pre/post boundary and changes the answer
without changing anything visible in the output.

The second is which country's weights were loaded. ``outputs/weights/<strategy>/`` is shared across
countries and resolves by modification time, so running Germany's exhibit after India's stage 04
would quietly score India's book against German prices and report it as Germany.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "exp_112a_event_study", ROOT / "tools" / "exp_112a_event_study.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


e112a = _load()


# --------------------------------------------------------------- the April-March tax year

def test_india_tax_year_runs_april_to_march():
    """FY2018-19 is April 2018 .. March 2019 and is labelled by the year it ends in."""
    dates = pd.Series(pd.to_datetime(
        ["2018-03-31", "2018-04-01", "2018-12-31", "2019-03-31", "2019-04-01"]))
    assert list(e112a.tax_year(dates, 3)) == [2018, 2019, 2019, 2019, 2020]


def test_german_tax_year_is_the_calendar_year():
    dates = pd.Series(pd.to_datetime(["2018-01-31", "2018-12-31", "2019-01-31"]))
    assert list(e112a.tax_year(dates, 12)) == [2018, 2018, 2019]


def test_the_treatment_date_is_the_first_day_of_an_indian_tax_year():
    """Section 112A takes effect on 2018-04-01, so no Indian tax year straddles it.

    If it did, that year would be partly taxed under each regime and could not be assigned to
    either side of the event.
    """
    assert e112a.SECTION_112A == pd.Timestamp("2018-04-01")
    before = e112a.tax_year(pd.Series([e112a.SECTION_112A - pd.Timedelta(days=1)]), 3)[0]
    after = e112a.tax_year(pd.Series([e112a.SECTION_112A]), 3)[0]
    assert after == before + 1


# ------------------------------------------------------------------- the pre/post assignment

@pytest.mark.parametrize("country,end_month,first_post", [("IND", 3, 2019), ("DEU", 12, 2018)])
def test_first_post_year_matches_each_country_year_end(country, end_month, first_post):
    """The same calendar instant falls in a differently-labelled tax year in each country."""
    computed = e112a.SECTION_112A.year + (1 if e112a.SECTION_112A.month > end_month else 0)
    assert computed == first_post
    assert e112a.TAX_YEAR_END_MONTH[country] == end_month


# ------------------------------------------------------------------- the statute actually moves

def test_only_india_changes_rule_across_the_event_date():
    """Germany and Japan are the controls precisely because their law does not move that day."""
    from alphacomb.tax.dated import DatedC12Patch

    engine = DatedC12Patch.from_frozen_evaluation_artifacts(ROOT)
    before = {c: engine.schedule.resolve(c, "2018-03-31") for c in ("IND", "DEU", "JPN")}
    after = {c: engine.schedule.resolve(c, "2018-04-01") for c in ("IND", "DEU", "JPN")}

    assert before["IND"].legal_regime != after["IND"].legal_regime
    assert before["IND"].cgt_long == 0.0 and after["IND"].cgt_long == pytest.approx(0.10)
    # The short rate and the boundary must NOT move, or the event is not a clean wedge change.
    assert before["IND"].cgt_short == after["IND"].cgt_short == pytest.approx(0.15)
    assert before["IND"].holding_period_months == after["IND"].holding_period_months == 12
    assert before["IND"].stt_sell == after["IND"].stt_sell

    for control in ("DEU", "JPN"):
        assert before[control].legal_regime == after[control].legal_regime
        assert before[control].cgt_short == after[control].cgt_short
        assert before[control].cgt_long == after[control].cgt_long


def test_the_dated_schedule_covers_the_window_without_gaps():
    from alphacomb.tax.dated import DatedC12Patch

    engine = DatedC12Patch.from_frozen_evaluation_artifacts(ROOT)
    coverage = engine.schedule.validate(*e112a.WINDOW)
    assert coverage["gaps"] == 0 and coverage["overlaps"] == 0
    assert coverage["countries"] == 3


# ------------------------------------------------------------------- weights provenance

def test_resolve_weights_refuses_when_the_country_index_is_absent(tmp_path, monkeypatch):
    """It must fail loudly rather than fall back to 'the most recently modified file'.

    That fallback is what would silently score one country's book in another country's panel.
    """
    from alphacomb.contracts import paths

    monkeypatch.setattr(paths, "outputs_root", lambda: tmp_path)
    with pytest.raises(SystemExit, match="no weights index"):
        e112a.resolve_weights("JPN", ["cell_L-S-P-0"], "1e9")


def test_resolve_weights_refuses_an_index_that_omits_a_requested_cell(tmp_path, monkeypatch):
    from alphacomb.contracts import paths

    monkeypatch.setattr(paths, "outputs_root", lambda: tmp_path)
    index = tmp_path / "weights_index"
    index.mkdir()
    pd.DataFrame([{"country": "IND", "aum": 1e9, "strategy": "cell_L-S-P-0",
                   "run_id": "pf_x", "weights": str(tmp_path / "x.parquet")}]
                 ).to_csv(index / "IND_1e9.csv", index=False)
    with pytest.raises(SystemExit, match="does not cover"):
        e112a.resolve_weights("IND", ["cell_L-S-P-0", "cell_N-C-E-U"], "1e9")


def test_resolve_weights_refuses_an_index_naming_a_missing_file(tmp_path, monkeypatch):
    from alphacomb.contracts import paths

    monkeypatch.setattr(paths, "outputs_root", lambda: tmp_path)
    index = tmp_path / "weights_index"
    index.mkdir()
    pd.DataFrame([{"country": "IND", "aum": 1e9, "strategy": "cell_L-S-P-0",
                   "run_id": "pf_x", "weights": str(tmp_path / "gone.parquet")}]
                 ).to_csv(index / "IND_1e9.csv", index=False)
    with pytest.raises(SystemExit, match="missing file"):
        e112a.resolve_weights("IND", ["cell_L-S-P-0"], "1e9")


def test_the_real_germany_index_resolves_to_files_that_exist():
    """Guards the published Germany exhibit: its 21 run ids must still be on disk."""
    index = ROOT / "outputs" / "weights_index" / "DEU_1e9.csv"
    if not index.exists():
        pytest.skip("no DEU index in this checkout")
    frame = pd.read_csv(index)
    assert len(frame) == 21
    missing = [p for p in frame["weights"] if not Path(p).exists()]
    assert not missing, f"{len(missing)} Germany weights files have gone: {missing[:3]}"


# ------------------------------------------------------------------- the estimator

def test_interaction_is_recovered_on_a_panel_built_to_contain_one():
    """A cell whose tax bill falls in proportion to its turnover after the event.

    Constructed so the true post x turnover interaction is -0.5; the estimator has to find it
    through the cell and year fixed effects rather than soaking it up into them.
    """
    rows = []
    for cell_i in range(8):
        turnover = 0.1 + 0.05 * cell_i
        for year in range(2012, 2021):
            post = 1.0 if year >= 2019 else 0.0
            tax_per_gain = 0.2 + 0.01 * cell_i + 0.002 * (year - 2012) - 0.5 * post * turnover
            rows.append({"country": "IND", "cell": f"c{cell_i}", "tax_year": year,
                         "turnover": turnover, "post": post, "months": 12, "full_year": True,
                         "gross_ret": 1.0, "tax_ret": tax_per_gain,
                         "realised_st": 1.0, "realised_lt": 0.0, "lt_share": 0.0})
    out = e112a.did(pd.DataFrame(rows), "IND", include_truncated=False)
    assert out["interaction_post_x_turnover"] == pytest.approx(-0.5, abs=1e-6)
    assert out["n_post_years"] == 2


def test_did_reports_an_error_rather_than_a_number_without_post_variation():
    rows = [{"country": "DEU", "cell": "c0", "tax_year": y, "turnover": 0.2, "post": 0.0,
             "months": 12, "full_year": True, "gross_ret": 1.0, "tax_ret": 0.1,
             "realised_st": 1.0, "realised_lt": 0.0, "lt_share": 0.0}
            for y in range(2012, 2018)]
    out = e112a.did(pd.DataFrame(rows), "DEU", include_truncated=False)
    assert "error" in out and "pre/post" in out["error"]
