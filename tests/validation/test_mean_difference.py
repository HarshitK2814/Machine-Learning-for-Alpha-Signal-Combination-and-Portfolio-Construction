"""Tests for the paired annualised mean-return difference test (capacity measure B(A), P0-2)."""
from __future__ import annotations

import numpy as np
import pytest

from alphacomb.validation.inference import mean_difference_test


def _pair(T=132, shift=0.0, seed=1):
    rng = np.random.default_rng(seed)
    b = rng.normal(0.0, 0.03, T)
    a = b + shift + rng.normal(0.0, 0.01, T)
    return a, b


def test_statistic_is_annualised_mean_difference_exactly():
    a, b = _pair(shift=0.004)
    r = mean_difference_test(a, b, n_boot=200)
    assert r.statistic == pytest.approx(12 * (a.mean() - b.mean()), abs=1e-12)
    assert r.detail["mean_a"] == pytest.approx(a.mean())


def test_antisymmetric_in_the_two_series():
    a, b = _pair(shift=0.004)
    assert mean_difference_test(a, b, n_boot=200).statistic == pytest.approx(
        -mean_difference_test(b, a, n_boot=200).statistic)


def test_detects_real_shift_and_not_a_null():
    a, b = _pair(shift=0.01)
    assert mean_difference_test(a, b, n_boot=500).p_value < 0.01
    a0, b0 = _pair(shift=0.0, seed=3)
    assert mean_difference_test(a0, b0, n_boot=500).p_value > 0.05


def test_interval_contains_estimate_and_is_reproducible():
    a, b = _pair(shift=0.004)
    r1 = mean_difference_test(a, b, n_boot=500, seed=7)
    r2 = mean_difference_test(a, b, n_boot=500, seed=7)
    assert r1.detail["ci95_low"] <= r1.statistic <= r1.detail["ci95_high"]
    assert r1.p_value == r2.p_value and r1.detail["ci95_low"] == r2.detail["ci95_low"]


def test_nonfinite_months_dropped_pairwise_and_length_mismatch_rejected():
    a, b = _pair()
    a2 = a.copy(); a2[5] = np.nan
    r = mean_difference_test(a2, b, n_boot=100)
    assert r.detail["n_obs"] == len(a) - 1
    with pytest.raises(ValueError):
        mean_difference_test(a[:-1], b, n_boot=100)
    with pytest.raises(ValueError):
        mean_difference_test(a[:6], b[:6], n_boot=100)
