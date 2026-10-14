"""E02/E03 signal diagnostics.

Recovery tests again: plant a signal with known information and known persistence, and check the
diagnostics report it. The effective-signal-count test is the one that matters most for the
paper, because that number is the quantitative claim behind "the library is smaller than it
looks".
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.validation import signal_diagnostics as sd


@pytest.fixture()
def panel():
    """sig_good predicts returns; sig_noise does not; sig_dup is a near-copy of sig_good."""
    rng = np.random.default_rng(19)
    dates = pd.date_range("2005-01-31", periods=120, freq="ME")
    permnos = np.arange(1, 61, dtype="int32")
    rows = []
    prev = rng.normal(size=permnos.size)
    for d in dates:
        # Persistent signal: 85% carried over month to month.
        good = 0.85 * prev + np.sqrt(1 - 0.85 ** 2) * rng.normal(size=permnos.size)
        prev = good
        noise = rng.normal(size=permnos.size)
        dup = good + 0.05 * rng.normal(size=permnos.size)
        # Longer horizons dilute the signal with independent noise rather than rescaling it.
        # Rank IC is invariant to a positive monotone transform, so `0.5 * r_1m` would have
        # exactly the same rank IC as `r_1m` and nothing would appear to decay.
        r1 = 0.05 * good + 0.02 * rng.normal(size=permnos.size)
        rows.append(pd.DataFrame({
            "date": d, "permno": permnos,
            "sig_good": good, "sig_noise": noise, "sig_dup": dup,
            "r_1m": r1,
            "r_3m": 0.05 * good + 0.06 * rng.normal(size=permnos.size),
            "r_6m": 0.05 * good + 0.15 * rng.normal(size=permnos.size),
            "r_12m": 0.05 * good + 0.60 * rng.normal(size=permnos.size),
        }))
    return pd.concat(rows, ignore_index=True)


SIGNALS = ["sig_good", "sig_noise", "sig_dup"]


@pytest.fixture()
def meta():
    return pd.DataFrame({
        "signal": SIGNALS,
        "theme": ["momentum", "value", "momentum"],
        "pub_year": [1993, 1992, 1997],
        "source": ["x", "y", "z"],
    })


# --------------------------------------------------------------------- E02

def test_informative_signal_has_positive_significant_ic(panel):
    q = sd.signal_quality(panel, SIGNALS).set_index("signal")
    assert q.loc["sig_good", "mean_ic"] > 0.1
    assert q.loc["sig_good", "nw_t"] > 3
    assert bool(q.loc["sig_good", "significant_5pct"])


def test_noise_signal_carries_far_less_information(panel):
    """The substantive claim, not a single-draw significance flag.

    `sig_noise` is independent of returns by construction, so on any one seed its t-statistic
    clears 1.96 about 5% of the time. Asserting it never does would be testing the random number
    generator; what must hold is that its IC is an order of magnitude below the real signal's.
    """
    q = sd.signal_quality(panel, SIGNALS).set_index("signal")
    assert abs(q.loc["sig_noise", "mean_ic"]) < 0.05
    assert abs(q.loc["sig_noise", "mean_ic"]) < 0.2 * abs(q.loc["sig_good", "mean_ic"])
    assert abs(q.loc["sig_noise", "icir"]) < abs(q.loc["sig_good", "icir"])


def test_persistence_is_recovered(panel):
    """The generator carries 85% of the signal forward; autocorrelation should find it."""
    q = sd.signal_quality(panel, SIGNALS).set_index("signal")
    assert 0.7 < q.loc["sig_good", "autocorr_1m"] < 0.95
    # A persistent signal implies low turnover.
    assert q.loc["sig_good", "implied_turnover"] < 0.3
    # Pure noise refreshes completely, so its implied turnover is near one.
    assert q.loc["sig_noise", "implied_turnover"] > 0.7


def test_ic_decays_across_horizons(panel):
    """r_12m carries a twentieth of r_1m's loading, so IC must fall with horizon."""
    q = sd.signal_quality(panel, SIGNALS).set_index("signal")
    row = q.loc["sig_good"]
    assert row["ic_r_1m"] > row["ic_r_6m"] > 0
    assert np.isfinite(row["ic_half_life_months"])


def test_ranked_output_is_sorted_by_ic(panel):
    q = sd.signal_quality(panel, SIGNALS)
    assert q["mean_ic"].is_monotonic_decreasing
    assert q.iloc[0]["signal"] == "sig_good"


# --------------------------------------------------------------------- E03

def test_effective_signal_count_detects_the_duplicate(panel, meta):
    """Three signals where two are near-identical should count as roughly two, not three.

    This is the number behind the paper's redundancy claim, so it has to be right.
    """
    r = sd.redundancy(panel, SIGNALS, meta)
    assert r["n_signals"] == 3
    assert 1.5 < r["effective_n_signals"] < 2.6


def test_within_theme_correlation_exceeds_cross_theme(panel, meta):
    """E03's hypothesis, stated as a test: themes are where the redundancy lives."""
    r = sd.redundancy(panel, SIGNALS, meta)
    assert r["mean_abs_within_theme_corr"] > r["mean_abs_cross_theme_corr"]


def test_effective_count_equals_n_for_an_uncorrelated_panel():
    rng = np.random.default_rng(3)
    corr = pd.DataFrame(np.eye(10))
    assert sd.effective_number_of_signals(corr) == pytest.approx(10.0)


def test_effective_count_is_one_for_a_perfectly_correlated_panel():
    corr = pd.DataFrame(np.ones((6, 6)))
    assert sd.effective_number_of_signals(corr) == pytest.approx(1.0, abs=1e-6)


def test_per_theme_table_reports_each_multi_signal_theme(panel, meta):
    r = sd.redundancy(panel, SIGNALS, meta)
    # Only 'momentum' has more than one signal here.
    assert list(r["per_theme"].index) == ["momentum"]
    assert r["per_theme"].loc["momentum", "n_signals"] == 2


# --------------------------------------------------------------------- coverage

def test_coverage_reports_a_row_per_year(panel):
    cov = sd.coverage(panel, SIGNALS)
    assert len(cov) == panel["date"].dt.year.nunique()
    assert (cov["mean_signal_coverage"] <= 1.0).all()
    assert (cov["mean_signal_coverage"] > 0.9).all()


def test_missing_values_reduce_coverage(panel):
    holed = panel.copy()
    holed.loc[holed.index[:len(holed) // 2], "sig_noise"] = np.nan
    cov = sd.coverage(holed, SIGNALS)
    assert cov["mean_signal_coverage"].min() < 1.0


def test_empty_signal_is_skipped_rather_than_crashing(panel):
    blank = panel.copy()
    blank["sig_blank"] = np.nan
    q = sd.signal_quality(blank, SIGNALS + ["sig_blank"])
    assert "sig_blank" not in set(q["signal"])
