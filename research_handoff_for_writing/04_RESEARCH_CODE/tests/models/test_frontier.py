"""Design v2 tests: complexity ladder, conformal uncertainty, attention, robustness, falsification."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.contracts import read_table, validate
from alphacomb.contracts.interfaces import CellSpec
from alphacomb.models import CellRunConfig, build_design, run_cell
from alphacomb.models.attention import AttentionCell
from alphacomb.models.complexity import ComplexityCell, RandomFourierFeatures, spectrum_diagnostic
from alphacomb.models.conformal import coverage_report, split_conformal
from alphacomb.portfolio import OptimizerConfig, construct, construct_robust, grinold_alpha, prediction_inflation
from alphacomb.risk import RiskCache, StructuralRiskModel
from alphacomb.validation import expected_max_of_trials, inflation_gap, microstructure_placebo

SPEC = CellSpec.parse("N-S-P-0")
DATE = pd.Timestamp("2000-12-31")


@pytest.fixture(scope="module")
def design(small_panel):
    return build_design(small_panel, SPEC, horizon=1)


# ---------------------------------------------------------------- complexity ladder
def test_random_features_are_deterministic_and_bounded():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(500, 20))
    a = RandomFourierFeatures(64, seed=7).fit_transform(X)
    b = RandomFourierFeatures(64, seed=7).fit_transform(X)
    np.testing.assert_allclose(a, b)
    assert a.shape == (500, 64)
    assert np.abs(a).max() <= np.sqrt(2 / 64) + 1e-9


def test_dense_and_sparse_arms_share_features_but_differ_in_selection(design):
    df, features = design
    train = df[(df["date"] < "2000-01-31") & df["y"].notna()].head(6000)
    test = df[df["date"] == DATE]
    dense = ComplexityCell(complexity=0.5, penalty="ridge", alpha=1e-6, seed=3).fit(train, train, features.all)
    sparse = ComplexityCell(complexity=0.5, penalty="l1", alpha=1e-4, seed=3).fit(train, train, features.all)
    np.testing.assert_allclose(dense.maps_[0].W_, sparse.maps_[0].W_)          # same feature space
    assert sparse.n_selected_ < dense.n_selected_                              # sparsity actually bites
    for model in (dense, sparse):
        out = model.predict(test, features.all)
        assert np.isfinite(out["score"]).all()


def test_complexity_above_one_is_the_interpolating_regime(design):
    df, features = design
    train = df[(df["date"] < "1996-01-31") & df["y"].notna()].head(1500)
    model = ComplexityCell(complexity=2.0, penalty="ridge", alpha=1e-8, seed=1).fit(train, train, features.all)
    n_features = model.maps_[0].n_features
    assert n_features > len(train)                                             # P > T
    fitted = model.predict(train, features.all)["score"].to_numpy()
    assert np.corrcoef(fitted, train["y"].to_numpy())[0, 1] > 0.5              # near-interpolation in sample


def test_spectrum_diagnostic_distinguishes_concentrated_from_diffuse():
    rng = np.random.default_rng(0)
    n, p = 2000, 30
    factor = rng.normal(size=(n, 1))
    concentrated = pd.DataFrame(factor @ rng.normal(size=(1, p)) + 0.01 * rng.normal(size=(n, p)),
                                columns=[f"f{i}" for i in range(p)])
    concentrated["date"] = pd.Timestamp("2000-01-31")
    diffuse = pd.DataFrame(rng.normal(size=(n, p)), columns=[f"f{i}" for i in range(p)])
    diffuse["date"] = pd.Timestamp("2000-01-31")
    cols = [f"f{i}" for i in range(p)]
    c = spectrum_diagnostic(concentrated, cols)
    d = spectrum_diagnostic(diffuse, cols)
    assert c["top1_share"] > 0.9 and "complexity unlikely" in c["concentration_verdict"]
    assert d["effective_rank"] > c["effective_rank"] * 5
    assert "may pay" in d["concentration_verdict"]


# ---------------------------------------------------------------- conformal uncertainty
def test_conformal_intervals_achieve_their_target_coverage():
    rng = np.random.default_rng(0)
    frames = []
    for k, date in enumerate(pd.date_range("2000-01-31", periods=60, freq="ME")):
        n = 200
        score = rng.normal(size=n)
        y = score + rng.normal(0, 1.0, n)
        frames.append(pd.DataFrame({"date": date, "permno": np.arange(n), "score": score, "y_true": y}))
    result = split_conformal(pd.concat(frames, ignore_index=True), calibration_months=12, alpha=0.1)
    report = coverage_report(result)
    assert 0.85 <= report["mean_coverage"] <= 0.95                      # close to the 90% target
    assert report["months"] > 40


def test_adaptive_conformal_tracks_a_volatility_shift():
    rng = np.random.default_rng(1)
    frames = []
    for k, date in enumerate(pd.date_range("2000-01-31", periods=80, freq="ME")):
        n, sd = 200, (0.5 if k < 40 else 3.0)                            # regime shift halfway
        score = rng.normal(size=n)
        y = score + rng.normal(0, sd, n)
        frames.append(pd.DataFrame({"date": date, "permno": np.arange(n), "score": score, "y_true": y}))
    data = pd.concat(frames, ignore_index=True)
    adaptive = split_conformal(data, calibration_months=12, alpha=0.1, adaptive=True)
    static = split_conformal(data, calibration_months=12, alpha=0.1, adaptive=False)
    late_a = adaptive.coverage.tail(20)["coverage"].mean()
    late_s = static.coverage.tail(20)["coverage"].mean()
    assert late_a >= late_s                                             # adaptation restores coverage
    assert adaptive.coverage["half_width"].iloc[-1] > adaptive.coverage["half_width"].iloc[0]


# ---------------------------------------------------------------- attention
def test_attention_cell_fits_and_keeps_weights(design):
    df, features = design
    cols = features.all[:40]
    train = df[(df["date"] >= "1997-01-31") & (df["date"] < "1999-01-31") & df["y"].notna()]
    val = df[(df["date"] >= "1999-01-31") & (df["date"] < "2000-01-31") & df["y"].notna()]
    test = df[df["date"] == DATE]
    model = AttentionCell(d_model=16, n_heads=2, max_epochs=2, patience=1, seed=0).fit(train, val, cols)
    out = model.predict(test, cols)
    assert np.isfinite(out["score"]).all()
    assert model.last_attention_ is not None


# ---------------------------------------------------------------- robust optimisation
def test_robust_optimiser_is_nested_at_zero_radius(small_panel):
    risk = StructuralRiskModel(small_panel).prepare().load(DATE)
    rng = np.random.default_rng(0)
    scores = pd.Series(rng.normal(size=len(risk.B)), index=risk.B.index)
    alpha = grinold_alpha(scores, risk, ic=0.05)
    cfg = OptimizerConfig(**{**OptimizerConfig.from_files().__dict__, "gamma": 40.0})
    base = construct(DATE, alpha, None, risk, small_panel.cost_inputs, cfg).weights
    nested = construct_robust(DATE, alpha, None, risk, small_panel.cost_inputs, None, 0.0, 0.0, cfg).weights
    np.testing.assert_allclose(base.to_numpy(), nested.to_numpy(), atol=1e-6)


def test_robust_penalty_moves_weight_away_from_uncertain_names(small_panel):
    risk = StructuralRiskModel(small_panel).prepare().load(DATE)
    rng = np.random.default_rng(2)
    scores = pd.Series(rng.normal(size=len(risk.B)), index=risk.B.index)
    alpha = grinold_alpha(scores, risk, ic=0.05)
    unc = pd.Series(np.linspace(0.2, 5.0, len(alpha)), index=alpha.index)     # last names least trusted
    cfg = OptimizerConfig(**{**OptimizerConfig.from_files().__dict__, "gamma": 40.0})
    plain = construct_robust(DATE, alpha, None, risk, small_panel.cost_inputs, unc, 0.0, 0.0, cfg).weights
    robust = construct_robust(DATE, alpha, None, risk, small_panel.cost_inputs, unc, 3.0, 0.0, cfg).weights
    tail = alpha.index[-40:]
    assert robust.loc[tail].abs().sum() < plain.loc[tail].abs().sum()
    assert robust.abs().sum() <= cfg.gross_max + 1e-4


def test_wasserstein_radius_shrinks_concentration(small_panel):
    risk = StructuralRiskModel(small_panel).prepare().load(DATE)
    rng = np.random.default_rng(4)
    alpha = grinold_alpha(pd.Series(rng.normal(size=len(risk.B)), index=risk.B.index), risk, ic=0.05)
    cfg = OptimizerConfig(**{**OptimizerConfig.from_files().__dict__, "gamma": 40.0})
    plain = construct_robust(DATE, alpha, None, risk, small_panel.cost_inputs, None, 0.0, 0.0, cfg).weights
    dro = construct_robust(DATE, alpha, None, risk, small_panel.cost_inputs, None, 0.0, 0.05, cfg).weights
    assert np.sum(dro.to_numpy() ** 2) < np.sum(plain.to_numpy() ** 2)        # more diversified


def test_prediction_inflation_diagnostic():
    idx = pd.Index([1, 2, 3], name="permno")
    alpha = pd.Series([0.05, -0.05, 0.02], index=idx)
    weights = pd.Series([0.5, -0.5, 0.0], index=idx)
    realised = pd.Series([0.01, -0.01, 0.0], index=idx)
    out = prediction_inflation(alpha, weights, realised)
    assert out["inflation_ratio"] == pytest.approx(5.0)
    assert out["effective_names"] == pytest.approx(2.0)


# ---------------------------------------------------------------- falsification audit
def test_expected_max_grows_with_the_number_of_trials():
    assert expected_max_of_trials(1) == 0.0
    assert expected_max_of_trials(10) < expected_max_of_trials(1000)
    assert expected_max_of_trials(100, correlation=0.9) < expected_max_of_trials(100, correlation=0.0)


def test_inflation_gap_verdicts():
    inside = inflation_gap(best_in_sample=2.0, realised_out_of_sample=1.8, n_trials=500, metric_sd=1.0)
    assert "within" in inside.verdict
    outside = inflation_gap(best_in_sample=2.0, realised_out_of_sample=-1.0, n_trials=5, metric_sd=0.2)
    assert "survives" in outside.verdict


def test_microstructure_placebo_destroys_information_but_keeps_shape(small_panel):
    placebo = microstructure_placebo(small_panel, seed=0)
    assert placebo.signals.shape == small_panel.signals.shape
    sig_cols = [c for c in placebo.signals.columns if c.startswith("sig_")]
    block = placebo.signals[sig_cols].to_numpy()
    assert block.min() >= -0.5 - 1e-6 and block.max() <= 0.5 + 1e-6        # contract still holds

    def mean_ic(bundle):
        merged = bundle.signals.merge(bundle.targets[["date", "permno", "r_1m"]], on=["date", "permno"]).dropna()
        col = [c for c in merged.columns if c.startswith("sig_value")][0]
        return merged.groupby("date").apply(lambda d: d[col].corr(d["r_1m"], method="spearman"),
                                            include_groups=False).mean()
    assert abs(mean_ic(placebo)) < abs(mean_ic(small_panel))


@pytest.mark.parametrize("ladder", [("complexity_dense", "complexity_sparse"), ("attention",)])
def test_run_cell_with_frontier_ladder_and_conformal(small_panel, tmp_path, monkeypatch, ladder):
    monkeypatch.setenv("ALPHACOMB_OUTPUTS", str(tmp_path))
    risk = RiskCache(StructuralRiskModel(small_panel))
    cfg = CellRunConfig(horizon=1, first_test_year=2003, last_test_year=2003, fast=True,
                        uncertainty_members=2, kappa_grid=(0.0, 1.0), validation_months_for_kappa=3,
                        form_ladder=ladder, uncertainty_method="conformal", conformal_calibration_months=6)
    result = run_cell(CellSpec.parse("N-S-P-U"), small_panel, risk, cfg)
    table = read_table(result["artefact"])
    validate(table, "predictions")
    assert result["rows"] > 0
    diag = pd.read_csv(result["diagnostics"])
    assert (diag["uncertainty_method"] == "conformal").all()
    assert diag["conformal_coverage"].notna().any()


# --------------------------------------------------------------------------------------------
# Regression tests for the 22 September frontier audit. Each of these failures was invisible to
# the tests that existed: they asserted the component RAN, not that its output was usable.
# --------------------------------------------------------------------------------------------

def test_attention_scores_every_stock_even_past_the_subsample_cap():
    """A capped predict leaves dropped stocks as NaN - two thirds of a real CRSP cross-section.

    The cap exists to bound the O(n^2) attention cost during training. Applying it at prediction
    time is silent data loss: the universe here is deliberately larger than the cap, which the
    synthetic panel (~666 names) never is.
    """
    rng = np.random.default_rng(0)
    n_per_month, cap = 60, 25
    frames = []
    for m, date in enumerate(pd.date_range("2015-01-31", periods=4, freq="ME")):
        x = rng.normal(size=(n_per_month, 3))
        frames.append(pd.DataFrame({
            "date": date, "permno": np.arange(n_per_month) + 1,
            "f0": x[:, 0], "f1": x[:, 1], "f2": x[:, 2],
            "y": x[:, 0] * 0.05 + rng.normal(scale=0.01, size=n_per_month)}))
    panel = pd.concat(frames, ignore_index=True)
    feats = ["f0", "f1", "f2"]
    model = AttentionCell(d_model=8, n_heads=2, ff_hidden=8, max_epochs=2, max_stocks=cap, seed=0)
    model.fit(panel[panel["date"] < "2015-03-01"], panel[panel["date"] >= "2015-03-01"], feats, "y")

    scored = model.predict(panel, feats)
    assert scored["score"].notna().all(), (
        f"{scored['score'].isna().sum()} of {len(scored)} stocks were left unscored; "
        f"the prediction path is subsampling to max_stocks={cap}")


def test_attention_trains_on_a_unit_scale_target():
    """Raw monthly returns (sd ~0.13) against an O(1) head makes the first epochs fight the scale.

    The fitted scale must be stored and reapplied, so the returned score stays on the return scale
    that every other cell emits.
    """
    rng = np.random.default_rng(1)
    frames = []
    for date in pd.date_range("2015-01-31", periods=4, freq="ME"):
        x = rng.normal(size=(40, 2))
        frames.append(pd.DataFrame({"date": date, "permno": np.arange(40) + 1,
                                    "f0": x[:, 0], "f1": x[:, 1],
                                    "y": 0.13 * x[:, 0]}))
    panel = pd.concat(frames, ignore_index=True)
    feats = ["f0", "f1"]
    model = AttentionCell(d_model=8, n_heads=2, ff_hidden=8, max_epochs=2, seed=0)
    model.fit(panel[panel["date"] < "2015-03-01"], panel[panel["date"] >= "2015-03-01"], feats, "y")
    assert model.y_scale_ == pytest.approx(panel[panel["date"] < "2015-03-01"]["y"].std(), rel=1e-6)
    # the caller's frame must not have been mutated by the rescaling
    assert panel["y"].std() == pytest.approx(0.13 * 1.0, rel=0.2)


def test_every_bound_is_feasible_on_an_arbitrarily_drifted_book(small_panel):
    """The feasible set must be non-empty however far the book has drifted, on BOTH paths.

    Two distinct bugs met here. `construct_robust` was a parallel copy that never received the
    21 September feasibility fix - no test caught it because every test passes `w_prev=None`, the
    one case where the constraints cannot conflict. And the fix itself was incomplete: it relaxed
    the position, gross and net bounds to each one's individually-reachable floor, which are not
    jointly attainable, so the infeasibility simply moved into the unrelaxed beta constraint. Both
    are why this asserts feasibility at several drift levels rather than at one.

    `w = prev` is feasible by construction now, so `infeasible` is unreachable by definition; a
    failure here means a bound stopped being anchored at prev.
    """
    risk = StructuralRiskModel(small_panel).prepare().load(DATE)
    rng = np.random.default_rng(5)
    alpha = grinold_alpha(pd.Series(rng.normal(size=len(risk.B)), index=risk.B.index), risk, ic=0.05)
    cfg = OptimizerConfig(**{**OptimizerConfig.from_files().__dict__, "gamma": 40.0})
    for mult in (1.0, 4.0, 10.0):
        drifted = pd.Series(cfg.weight_abs_max * mult, index=alpha.index)
        for name, res in [
            ("construct", construct(DATE, alpha, drifted, risk, small_panel.cost_inputs, cfg)),
            ("construct_robust", construct_robust(DATE, alpha, drifted, risk,
                                                  small_panel.cost_inputs, None, 0.0, 0.0, cfg)),
        ]:
            assert res.status in {"optimal", "optimal_inaccurate"}, (
                f"{name} returned {res.status!r} at drift {mult}x weight_abs_max; a bound is no "
                f"longer relaxed to its value at prev, so the feasible set is empty")
            assert not res.weights.empty


def test_no_bound_is_loosened_on_an_undrifted_book(small_panel):
    """The feasibility machinery must be a no-op when the book is inside its caps.

    This is the property the second failed repair broke: anchoring every bound at `prev` made
    `net_slack` equal `|sum prev|`, so dollar-neutrality quietly stopped binding after any drift.
    Buying feasibility by weakening a property the paper claims is not a repair, so it is asserted.
    """
    risk = StructuralRiskModel(small_panel).prepare().load(DATE)
    rng = np.random.default_rng(11)
    alpha = grinold_alpha(pd.Series(rng.normal(size=len(risk.B)), index=risk.B.index), risk, ic=0.05)
    cfg = OptimizerConfig(**{**OptimizerConfig.from_files().__dict__, "gamma": 40.0})
    res = construct(DATE, alpha, None, risk, small_panel.cost_inputs, cfg)
    assert res.status in {"optimal", "optimal_inaccurate"}
    assert res.diagnostics["n_violated"] == 0, (
        f"bounds were breached on a fresh book: {res.diagnostics['violated']}")
    # the bounds the paper quotes must hold exactly, not approximately
    assert abs(float(res.weights.sum())) < 1e-6, "dollar-neutrality stopped binding"
    assert float(res.weights.abs().sum()) <= cfg.gross_max + 1e-6
    beta = risk.B["beta"].to_numpy(dtype=float)
    assert abs(float(beta @ res.weights.to_numpy())) <= cfg.beta_abs_max + 1e-6


def test_a_breached_bound_is_reported_not_hidden(small_panel):
    """When a bound genuinely cannot be met, the violation must reach the diagnostics.

    The whole point of the soft formulation is that a breach is visible in the manifest instead of
    appearing as a failed solve or as silently relaxed limits.
    """
    risk = StructuralRiskModel(small_panel).prepare().load(DATE)
    rng = np.random.default_rng(12)
    alpha = grinold_alpha(pd.Series(rng.normal(size=len(risk.B)), index=risk.B.index), risk, ic=0.05)
    cfg = OptimizerConfig(**{**OptimizerConfig.from_files().__dict__, "gamma": 40.0})
    drifted = pd.Series(cfg.weight_abs_max * 10.0, index=alpha.index)   # far outside every bound
    res = construct(DATE, alpha, drifted, risk, small_panel.cost_inputs, cfg)
    assert res.status in {"optimal", "optimal_inaccurate"}
    assert res.diagnostics["n_violated"] > 0, (
        "a book at 10x the position cap must breach the gross budget and report it")
    assert res.diagnostics["max_violation"] > 0.0


def test_a_returned_book_never_breaches_its_bounds_unreported(small_panel):
    """The returned weights and the reported violations must agree, at every drift level.

    This catches the worst failure found in the 22 September audit, which the repair itself
    introduced. On a drifted book the hard constraint set is empty, but SCS does not always say
    `infeasible` - it returns `optimal_inaccurate` with a solution breaching the gross budget by
    two orders of magnitude. Because the status was not `failed`, the soft fallback never fired and
    the result was a book at gross 769 against a budget of 2 with nothing recorded anywhere.

    So the invariant is not "the solver was happy". It is: whatever comes back, any bound it
    breaches is in the diagnostics. A solution is measured, never taken on the strength of a label.
    """
    from alphacomb.portfolio.optimizer import BREACH_TOL, bound_breach

    risk = StructuralRiskModel(small_panel).prepare().load(DATE)
    rng = np.random.default_rng(13)
    alpha = grinold_alpha(pd.Series(rng.normal(size=len(risk.B)), index=risk.B.index), risk, ic=0.05)
    cfg = OptimizerConfig(**{**OptimizerConfig.from_files().__dict__, "gamma": 40.0})
    ci = small_panel.cost_inputs

    for mult in (0.0, 1.0, 4.0, 10.0):
        prev = None if mult == 0 else pd.Series(cfg.weight_abs_max * mult, index=alpha.index)
        res = construct(DATE, alpha, prev, risk, ci, cfg)
        assert res.status in {"optimal", "optimal_inaccurate"}, f"failed at drift {mult}"
        prev_arr = (prev.reindex(res.weights.index).fillna(0.0).to_numpy()
                    if prev is not None else np.zeros(len(res.weights)))
        adv_cap, pos_cap = _caps_for(res.weights.index, ci, cfg, prev_arr)
        actual = bound_breach(res.weights.to_numpy(), prev_arr, adv_cap, pos_cap, cfg,
                              risk.align(res.weights.index))
        if actual > BREACH_TOL:
            assert res.diagnostics.get("n_violated", 0) > 0, (
                f"drift {mult}x: the returned book breaches its bounds by {actual:.4g} "
                f"(relative) with nothing in diagnostics - an unreported constraint violation")


def _caps_for(permnos, cost_inputs, cfg, prev):
    """The position and trade caps `construct` builds internally, for independent verification.

    Includes the per-name widening `book_constraints` applies, so the check compares against the
    bounds actually imposed rather than a tighter set the optimiser was never asked to meet.
    """
    from alphacomb.portfolio.cost_terms import cost_inputs_for

    ci = cost_inputs_for(DATE, cost_inputs, permnos)
    adv_cap = np.clip(ci["adv_usd"].to_numpy() * cfg.adv_participation_max / cfg.aum_usd, 1e-6, None)
    pos_cap = np.minimum(cfg.weight_abs_max, np.maximum(adv_cap, 1e-5))
    return adv_cap, np.maximum(pos_cap, np.abs(prev) - adv_cap)
