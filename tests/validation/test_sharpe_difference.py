"""Tests for the paired Sharpe-difference test.

The capacity channel - the paper's central number - is a difference of two Sharpe ratios computed
on the same months from the same scores. Every property asserted here is one the capacity-channel
result depends on, so a failure anywhere in this file invalidates the headline rather than merely
a utility function.
"""
from __future__ import annotations

import numpy as np
import pytest

from alphacomb.validation.inference import sharpe_difference_test


def _ar1(T: int, phi: float, mu: float, sd: float, rng) -> np.ndarray:
    """An AR(1) return series, so the HAC machinery is actually exercised."""
    e = rng.normal(0.0, sd * np.sqrt(1 - phi**2), T)
    x = np.empty(T)
    x[0] = mu + e[0]
    for t in range(1, T):
        x[t] = mu + phi * (x[t - 1] - mu) + e[t]
    return x


def test_identical_series_give_zero_difference_and_no_rejection():
    rng = np.random.default_rng(1)
    x = rng.normal(0.01, 0.04, 132)
    r = sharpe_difference_test(x, x)
    assert r.statistic == pytest.approx(0.0, abs=1e-12)
    assert r.p_value > 0.99
    assert r.detail["sharpe_a"] == pytest.approx(r.detail["sharpe_b"])


def test_sign_convention_matches_the_capacity_channel():
    """``a`` minus ``b``: passing the capped series first must give a positive channel."""
    rng = np.random.default_rng(2)
    worse = rng.normal(0.002, 0.04, 132)
    better = worse + 0.004
    assert sharpe_difference_test(better, worse).statistic > 0
    assert sharpe_difference_test(worse, better).statistic < 0


def test_antisymmetry_in_the_arguments():
    rng = np.random.default_rng(3)
    a = rng.normal(0.01, 0.05, 150)
    b = rng.normal(0.004, 0.03, 150)
    ab = sharpe_difference_test(a, b, seed=7)
    ba = sharpe_difference_test(b, a, seed=7)
    assert ab.statistic == pytest.approx(-ba.statistic, rel=1e-12)
    assert ab.detail["se_hac"] == pytest.approx(ba.detail["se_hac"], rel=1e-12)


def test_detects_a_real_difference_in_dependent_series():
    rng = np.random.default_rng(4)
    base = _ar1(240, 0.3, 0.001, 0.04, rng)
    good = base + 0.006
    r = sharpe_difference_test(good, base, n_boot=1500, seed=0)
    assert r.statistic > 0
    assert r.p_value < 0.05
    assert r.detail["ci95_low"] > 0


def test_no_false_rejection_when_only_scale_differs():
    """A Sharpe ratio is scale free, so doubling a series must not move the statistic."""
    rng = np.random.default_rng(5)
    x = _ar1(200, 0.2, 0.004, 0.05, rng)
    r = sharpe_difference_test(2.0 * x, x, n_boot=1200, seed=0)
    assert r.statistic == pytest.approx(0.0, abs=1e-10)
    assert r.p_value > 0.5


def test_confidence_interval_brackets_the_point_estimate():
    rng = np.random.default_rng(6)
    a = _ar1(180, 0.25, 0.005, 0.04, rng)
    b = _ar1(180, 0.25, 0.001, 0.04, rng)
    r = sharpe_difference_test(a, b, n_boot=1500, seed=1)
    assert r.detail["ci95_low"] <= r.statistic <= r.detail["ci95_high"]


def test_paired_se_is_smaller_than_treating_the_series_as_independent():
    """The whole reason for a paired test: shared shocks must shrink the standard error."""
    rng = np.random.default_rng(7)
    common = _ar1(240, 0.3, 0.003, 0.045, rng)
    a = common + rng.normal(0.0, 0.002, 240)
    b = common + rng.normal(0.0, 0.002, 240)
    paired = sharpe_difference_test(a, b, n_boot=1000, seed=0).detail["se_hac"]

    # Independent-series SE of a Sharpe difference, i.i.d. approximation.
    def naive_se(x):
        sr = x.mean() / x.std(ddof=1) * np.sqrt(12)
        return np.sqrt((1 + 0.5 * sr**2) / x.size) * np.sqrt(12)

    assert paired < np.hypot(naive_se(a), naive_se(b))


def test_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="same length"):
        sharpe_difference_test(np.zeros(50), np.zeros(49))


def test_rejects_too_few_observations():
    rng = np.random.default_rng(8)
    with pytest.raises(ValueError, match="at least 12"):
        sharpe_difference_test(rng.normal(size=8), rng.normal(size=8))


def test_non_finite_pairs_are_dropped_pairwise():
    rng = np.random.default_rng(9)
    a = rng.normal(0.01, 0.04, 100)
    b = rng.normal(0.01, 0.04, 100)
    a2, b2 = a.copy(), b.copy()
    a2[5] = np.nan
    b2[77] = np.inf
    r = sharpe_difference_test(a2, b2, n_boot=500, seed=0)
    assert r.detail["n_obs"] == 98


def test_zero_variance_series_is_reported_not_raised():
    rng = np.random.default_rng(10)
    r = sharpe_difference_test(np.zeros(60), rng.normal(0.01, 0.04, 60), n_boot=200)
    assert not np.isfinite(r.statistic)
    assert "note" in r.detail


def test_seed_makes_the_bootstrap_reproducible():
    rng = np.random.default_rng(11)
    a = _ar1(150, 0.2, 0.004, 0.04, rng)
    b = _ar1(150, 0.2, 0.001, 0.04, rng)
    one = sharpe_difference_test(a, b, n_boot=800, seed=42)
    two = sharpe_difference_test(a, b, n_boot=800, seed=42)
    assert one.p_value == two.p_value
    assert one.detail["ci95_low"] == two.detail["ci95_low"]
