"""Workstream-C baseline comparators (E10-E12).

These tests pin properties rather than implementations: that each rule is a genuine strategy, that
it degrades safely instead of silently returning zeros, that IC weighting actually prefers the
informative signal, and - the one that protects the paper's headline claim - that every baseline
emits the same contract shape the factorial cells do, so stage 04 can price them all through the
identical cost path.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.models import baselines


@pytest.fixture()
def panel():
    """A small panel where sig_good carries the signal and sig_noise does not."""
    rng = np.random.default_rng(11)
    dates = pd.date_range("2015-01-31", periods=24, freq="ME")
    permnos = np.arange(1, 41, dtype="int32")
    rows = []
    for d in dates:
        good = rng.normal(size=permnos.size)
        noise = rng.normal(size=permnos.size)
        # y is driven by sig_good only, cross-sectionally demeaned.
        y = 0.04 * good + 0.01 * rng.normal(size=permnos.size)
        rows.append(pd.DataFrame({
            "date": d, "permno": permnos,
            "sig_good": good, "sig_noise": noise,
            "thm_value": good, "thm_mom": noise,
            "y": y - y.mean(),
        }))
    return pd.concat(rows, ignore_index=True)


FEATURES = ["sig_good", "sig_noise"]
THEME_FEATURES = ["sig_good", "sig_noise", "thm_value", "thm_mom"]
ALL_CODES = sorted(baselines.BASELINES)


def _split(panel):
    train = panel[panel["date"] < "2016-01-31"]
    val = panel[(panel["date"] >= "2016-01-31") & (panel["date"] < "2016-07-31")]
    test = panel[panel["date"] >= "2016-07-31"]
    return train, val, test


@pytest.mark.parametrize("code", ALL_CODES)
def test_every_baseline_emits_the_contract_shape(panel, code):
    """Stage 04 prices cells and baselines with the same machinery, so the output shape must match.

    This is the test that protects cost parity: if a baseline emitted something stage 04 could not
    consume, the temptation would be to give it its own backtest, and the net-of-cost comparison
    would quietly stop being like-for-like.
    """
    train, val, test = _split(panel)
    model = baselines.build(code).fit(train, val, THEME_FEATURES)
    out = model.predict(test, THEME_FEATURES)

    assert list(out.columns) == baselines.SCORE_COLUMNS
    assert len(out) == len(test)
    # What the runner actually requires, and what this test asserted the wrong version of until
    # 8 October 2026: it selects per month with `pred.loc[group.index]` and reads `unc_sd`
    # unconditionally. A frame carrying the right column names but a fresh RangeIndex passes a
    # shape check and then raises inside the runner, which is exactly what happened the first
    # time a baseline was run rather than unit-tested.
    assert out.index.equals(test.index), "the runner selects by test's index, not position"
    assert "unc_sd" in out.columns and out["unc_sd"].isna().all()
    assert out["score"].notna().all()
    assert np.isfinite(out["score"]).all()
    assert out["permno"].to_numpy().tolist() == test["permno"].to_numpy().tolist()


@pytest.mark.parametrize("code", ALL_CODES)
def test_baselines_produce_cross_sectional_variation(panel, code):
    """A rule that returns a constant is not a strategy - the optimiser would see no signal."""
    train, val, test = _split(panel)
    out = baselines.build(code).fit(train, val, THEME_FEATURES).predict(test, THEME_FEATURES)
    per_date_spread = out.groupby("date")["score"].std()
    assert (per_date_spread > 0).all(), f"{code} produced a flat cross-section"


def test_ic_weighting_prefers_the_informative_signal(panel):
    train, val, _ = _split(panel)
    model = baselines.ICWeightCell().fit(train, val, FEATURES)
    assert model._weights["sig_good"] > model._weights.get("sig_noise", 0.0)


def test_ic_weighting_clips_negative_ic_rather_than_flipping_it(panel):
    """A negative-IC signal gets zero weight, never a reversed sign.

    Flipping asserts the in-sample sign reverses out of sample, which is a far stronger claim than
    "this signal carries information" and would need separate pre-registration.
    """
    flipped = panel.copy()
    flipped["sig_noise"] = -flipped["y"] * 10.0  # strongly negative IC against y
    train, val, _ = _split(flipped)
    model = baselines.ICWeightCell().fit(train, val, FEATURES)
    assert model._weights.get("sig_noise", 0.0) == 0.0


def test_ridge_selects_a_penalty_from_its_grid(panel):
    train, val, _ = _split(panel)
    model = baselines.RidgeBaselineCell().fit(train, val, FEATURES)
    assert model.chosen_penalty in model.penalties


def test_ridge_and_ols_recover_the_informative_signal(panel):
    """Both linear baselines should load positively on sig_good, which generated y."""
    train, val, test = _split(panel)
    for cls in (baselines.OLSCell, baselines.RidgeBaselineCell):
        model = cls().fit(train, val, FEATURES)
        idx = model._cols.index("sig_good")
        assert model._beta[idx] > 0, f"{cls.__name__} did not load on the informative signal"


def test_theme_equal_weight_uses_theme_columns_when_present(panel):
    train, val, test = _split(panel)
    model = baselines.ThemeEqualWeightCell().fit(train, val, THEME_FEATURES)
    assert model._cols == ["thm_value", "thm_mom"]


def test_theme_equal_weight_falls_back_to_signals_when_no_themes(panel):
    """A design with no theme composites must still yield a real strategy, not zeros."""
    train, val, test = _split(panel)
    model = baselines.ThemeEqualWeightCell().fit(train, val, FEATURES)
    out = model.predict(test, FEATURES)
    assert out.groupby("date")["score"].std().gt(0).all()


def test_equal_weight_is_invariant_to_signal_rescaling(panel):
    """Per-date standardisation is what makes 'equal weight' actually equal.

    Without it, multiplying one signal by 100 would silently make it dominate the average.
    """
    train, val, test = _split(panel)
    base = baselines.EqualWeightCell().fit(train, val, FEATURES).predict(test, FEATURES)

    scaled_test = test.copy()
    scaled_test["sig_noise"] = scaled_test["sig_noise"] * 100.0
    scaled = baselines.EqualWeightCell().fit(train, val, FEATURES).predict(scaled_test, FEATURES)

    corr = np.corrcoef(base["score"], scaled["score"])[0, 1]
    assert corr > 0.999


@pytest.mark.parametrize("code", ALL_CODES)
def test_degenerate_training_window_does_not_raise(panel, code):
    """An empty train split must degrade gracefully; the walk-forward hits thin windows early on."""
    _, val, test = _split(panel)
    empty = panel.iloc[0:0]
    out = baselines.build(code).fit(empty, val, THEME_FEATURES).predict(test, THEME_FEATURES)
    assert len(out) == len(test)
    assert np.isfinite(out["score"]).all()


def test_unregistered_comparator_is_refused():
    """PLAN_002 fixes the comparator set; a new one may be reported, but only as exploratory."""
    with pytest.raises(KeyError, match="exploratory"):
        baselines.build("BASE-WHATEVER")


def test_registered_codes_match_the_preregistration():
    """The code must not drift from the frozen plan without the plan changing."""
    import json
    from pathlib import Path

    plan_path = Path(__file__).resolve().parents[2] / "prereg" / "PLAN_002_international_after_tax.json"
    if not plan_path.exists():
        pytest.skip("PLAN_002 not present in this checkout")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    registered = {c for c in plan["cells"] if c.startswith("BASE-")}
    assert registered == set(baselines.BASELINES), (
        "baselines.BASELINES and PLAN_002 disagree; changing the comparator set requires a new "
        "pre-registration file, not an edit"
    )


# ------------------------------------------------------- the runner (E10-E12)

def test_baseline_runs_through_the_shared_cell_runner(small_panel, tmp_path, monkeypatch):
    """A comparator must produce contract C9 by the same route a cell does.

    Document 13 requirement 5 asks for cost parity through the shared stage-04 path, and
    requirement 3 forbids a second cost implementation. The check that matters is that the run
    lands in C9 *and* logs a trial, because that is what proves it went through the cell runner
    rather than around it.
    """
    from alphacomb.contracts import read_table
    from alphacomb.contracts.schemas import validate
    from alphacomb.models import CellRunConfig, run_baseline
    from alphacomb.risk import RiskCache, StructuralRiskModel
    import pandas as pd

    monkeypatch.setenv("ALPHACOMB_OUTPUTS", str(tmp_path))
    risk = RiskCache(StructuralRiskModel(small_panel))
    cfg = CellRunConfig(horizon=1, first_test_year=2003, last_test_year=2003, fast=True)
    result = run_baseline("BASE-EW", small_panel, risk, cfg)

    table = read_table(result["artefact"])
    validate(table, "predictions")
    assert result["experiment"] == "E10-E12"
    assert result["strategy"] == "baseline_BASE-EW"
    assert set(pd.to_datetime(table["date"]).dt.year) == {2003}
    trials = pd.read_csv(tmp_path / "trials.csv")
    assert (trials["strategy"] == "baseline_BASE-EW").any(), (
        "a baseline that does not log a trial has bypassed the shared runner")


def test_baseline_runner_refuses_an_unregistered_comparator(small_panel):
    from alphacomb.models import run_baseline
    from alphacomb.risk import RiskCache, StructuralRiskModel

    risk = RiskCache(StructuralRiskModel(small_panel))
    with pytest.raises(KeyError, match="exploratory"):
        run_baseline("BASE-NOT-REGISTERED", small_panel, risk)
