"""Statistical inference. Each test pins a property a referee would check.

The tests are written so that a *broken* implementation fails loudly rather than returning a
plausible number. That matters more here than anywhere else in the codebase: an inference routine
that silently understates a standard error manufactures significance, and nothing downstream would
notice.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.validation import (benjamini_hochberg, deflated_sharpe, diebold_mariano, hansen_spa,
                                  inference_report, newey_west_se, pbo_cscv, romano_wolf,
                                  sharpe_se, sharpe_test)


def _ar1(n: int, rho: float, sd: float = 0.04, mu: float = 0.0, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    e = rng.normal(0, sd, n)
    x = np.empty(n)
    x[0] = e[0]
    for t in range(1, n):
        x[t] = rho * x[t - 1] + e[t]
    return x + mu


# ------------------------------------------------------------------ standard errors

def test_newey_west_matches_plain_se_when_there_is_no_autocorrelation():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1, 4000)
    plain = x.std(ddof=1) / np.sqrt(len(x))
    assert newey_west_se(x) == pytest.approx(plain, rel=0.15)


def test_newey_west_is_larger_under_positive_autocorrelation():
    """The whole point: iid standard errors understate uncertainty in persistent series."""
    x = _ar1(2000, rho=0.5, seed=1)
    plain = x.std(ddof=1) / np.sqrt(len(x))
    assert newey_west_se(x) > 1.15 * plain


def test_sharpe_se_accounts_for_higher_moments():
    """A left-skewed, fat-tailed series must not get the Gaussian standard error."""
    rng = np.random.default_rng(2)
    normal = rng.normal(0.01, 0.04, 600)
    skewed = np.concatenate([rng.normal(0.015, 0.02, 570), rng.normal(-0.10, 0.05, 30)])
    se_norm = sharpe_se(normal, higher_moments=True, autocorr=False)
    se_skew = sharpe_se(skewed, higher_moments=True, autocorr=False)
    assert np.isfinite(se_norm) and np.isfinite(se_skew)
    assert se_skew > se_norm, "negative skew and fat tails must widen the standard error"


def test_sharpe_test_reports_the_harvey_liu_zhu_hurdle():
    r = _ar1(360, rho=0.0, sd=0.03, mu=0.02, seed=3)
    res = sharpe_test(r)
    assert res.detail["months"] == 360
    assert "harvey_liu_zhu_hurdle_met" in res.detail
    assert res.detail["harvey_liu_zhu_hurdle_met"] == (abs(res.detail["t_stat"]) > 3.0)


def test_a_pure_noise_series_is_not_significant():
    rng = np.random.default_rng(4)
    res = sharpe_test(rng.normal(0, 0.04, 400))
    assert res.p_value > 0.05


# ------------------------------------------------------------------ selection bias

def test_deflated_sharpe_penalises_a_larger_search():
    """The same Sharpe must look worse when it was the best of more attempts."""
    r = _ar1(240, rho=0.0, sd=0.04, mu=0.012, seed=5)
    few = deflated_sharpe(1.0, n_trials=5, returns=r)
    many = deflated_sharpe(1.0, n_trials=5000, returns=r)
    assert few.statistic > many.statistic
    assert many.detail["expected_max_sr_ann"] > few.detail["expected_max_sr_ann"]


def test_deflated_sharpe_kills_a_mediocre_sharpe_found_by_a_big_search():
    r = _ar1(240, rho=0.0, sd=0.04, mu=0.004, seed=6)
    res = deflated_sharpe(0.35, n_trials=10_000, returns=r)
    assert res.statistic < 0.95
    assert "does NOT survive" in res.detail["verdict"]


def test_expected_maximum_grows_with_the_number_of_trials():
    sizes = [10, 100, 1000, 10000]
    maxima = [deflated_sharpe(1.0, n, returns=_ar1(240, 0.0, seed=7)).detail["expected_max_sr_ann"]
              for n in sizes]
    assert all(b > a for a, b in zip(maxima, maxima[1:])), maxima


# ------------------------------------------------------------------ overfitting of the procedure

def test_pbo_is_high_when_strategies_are_pure_noise():
    """If every candidate is noise, the in-sample winner should be a coin flip out of sample."""
    rng = np.random.default_rng(8)
    noise = pd.DataFrame(rng.normal(0, 0.04, (240, 12)),
                         columns=[f"s{i}" for i in range(12)])
    res = pbo_cscv(noise, n_splits=10)
    assert 0.25 < res.statistic <= 1.0, f"PBO={res.statistic} on pure noise"


def test_pbo_is_low_when_one_strategy_is_genuinely_better():
    rng = np.random.default_rng(9)
    M = pd.DataFrame(rng.normal(0, 0.04, (240, 8)), columns=[f"s{i}" for i in range(8)])
    M["winner"] = rng.normal(0.02, 0.04, 240)          # a real, persistent edge
    res = pbo_cscv(M, n_splits=10)
    assert res.statistic < 0.3, f"PBO={res.statistic} despite a genuine winner"


# ------------------------------------------------------------------ many comparisons

def test_romano_wolf_controls_familywise_error_on_pure_noise():
    rng = np.random.default_rng(10)
    noise = pd.DataFrame(rng.normal(0, 0.04, (240, 20)),
                         columns=[f"s{i}" for i in range(20)])
    out = romano_wolf(noise, n_boot=400, seed=0)
    assert out["reject"].sum() <= 1, f"{out['reject'].sum()} false rejections out of 20"


def test_romano_wolf_finds_a_genuine_winner():
    rng = np.random.default_rng(11)
    M = pd.DataFrame(rng.normal(0, 0.03, (300, 10)), columns=[f"s{i}" for i in range(10)])
    M["real"] = rng.normal(0.025, 0.03, 300)
    out = romano_wolf(M, n_boot=400, seed=0).set_index("strategy")
    assert out.loc["real", "reject"], out.head()


def test_romano_wolf_p_values_are_monotone_in_the_statistic():
    rng = np.random.default_rng(12)
    M = pd.DataFrame(rng.normal(0.005, 0.04, (200, 6)), columns=list("abcdef"))
    out = romano_wolf(M, n_boot=300, seed=0).sort_values("t_stat", ascending=False)
    assert out["p_adjusted"].is_monotonic_increasing, out


def test_benjamini_hochberg_is_less_conservative_than_bonferroni():
    p = pd.Series([0.001, 0.008, 0.02, 0.04, 0.2, 0.5, 0.9])
    out = benjamini_hochberg(p, alpha=0.05)
    bonferroni = (p < 0.05 / len(p)).sum()
    assert out["reject"].sum() >= bonferroni
    assert (out["p_adjusted"] >= out["p_value"] - 1e-12).all()


def test_benjamini_hochberg_rejects_nothing_on_uniform_p_values():
    rng = np.random.default_rng(13)
    out = benjamini_hochberg(pd.Series(rng.uniform(0, 1, 200)), alpha=0.05)
    assert out["reject"].sum() <= 10


# ------------------------------------------------------------------ superior predictive ability

def test_spa_does_not_reject_when_no_candidate_beats_the_benchmark():
    rng = np.random.default_rng(14)
    bench = rng.normal(0.008, 0.03, 240)
    cands = pd.DataFrame(rng.normal(0.008, 0.03, (240, 8)),
                         columns=[f"c{i}" for i in range(8)])
    res = hansen_spa(bench, cands, n_boot=300, seed=0)
    assert res.p_value > 0.05, res.detail


def test_spa_rejects_when_a_candidate_genuinely_beats_the_benchmark():
    rng = np.random.default_rng(15)
    bench = rng.normal(0.002, 0.03, 300)
    cands = pd.DataFrame(rng.normal(0.002, 0.03, (300, 6)),
                         columns=[f"c{i}" for i in range(6)])
    cands["good"] = rng.normal(0.030, 0.03, 300)
    res = hansen_spa(bench, cands, n_boot=300, seed=0)
    assert res.p_value < 0.10, res.detail


# ------------------------------------------------------------------ forecast comparison

def test_diebold_mariano_identifies_the_better_forecaster():
    rng = np.random.default_rng(16)
    good = rng.normal(0, 0.5, 400)
    bad = rng.normal(0, 1.5, 400)
    res = diebold_mariano(good, bad)
    assert res.detail["better"] == "a"
    assert res.p_value < 0.05


def test_diebold_mariano_is_indifferent_between_equal_forecasters():
    rng = np.random.default_rng(17)
    res = diebold_mariano(rng.normal(0, 1, 500), rng.normal(0, 1, 500))
    assert res.p_value > 0.05


# ------------------------------------------------------------------ the whole report

def test_inference_report_returns_everything_a_referee_asks_for():
    rng = np.random.default_rng(18)
    M = pd.DataFrame(rng.normal(0.006, 0.035, (240, 5)),
                     columns=[f"cell_{i}" for i in range(5)])
    M["benchmark"] = rng.normal(0.004, 0.035, 240)
    rep = inference_report(M, n_trials=228, benchmark="benchmark")

    assert set(rep) >= {"per_strategy", "romano_wolf", "pbo", "spa", "n_trials"}
    per = rep["per_strategy"]
    assert len(per) == 6
    for col in ("sharpe", "se", "t_stat", "p_value", "hlz_t3_hurdle",
                "deflated_sr_prob", "survives_deflation"):
        assert col in per.columns
    assert rep["n_trials"] == 228
    assert per["se"].notna().all(), "a missing standard error is worse than no table"
