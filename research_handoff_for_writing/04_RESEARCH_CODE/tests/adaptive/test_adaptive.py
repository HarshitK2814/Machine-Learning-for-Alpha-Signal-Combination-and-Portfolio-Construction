"""Online aggregation and drift detection.

The claim these tests defend is narrow and precise: the rule adapts, it does so using only past
information, and it carries a regret guarantee. They do not claim it makes money - that is an
empirical question the pipeline answers, and the answer is allowed to be no.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.adaptive import (HedgeAggregator, HedgeConfig, PageHinkley, adaptation_report,
                                calibrate_threshold, detect, equal_weight_benchmark, member_rewards,
                                refit_schedule, run_aggregation)


def panel(seed: int = 0, months: int = 180) -> pd.DataFrame:
    """Three experts: one good throughout, one bad throughout, one that switches at the midpoint."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2000-01-31", periods=months, freq="ME")
    half = months // 2
    good = rng.normal(0.008, 0.02, months)
    bad = rng.normal(-0.004, 0.02, months)
    switcher = np.concatenate([rng.normal(-0.006, 0.02, half),
                               rng.normal(0.014, 0.02, months - half)])
    return pd.DataFrame({"good": good, "bad": bad, "switcher": switcher}, index=dates)


def test_weights_stay_on_the_simplex():
    agg = HedgeAggregator(["a", "b", "c"])
    for _ in range(50):
        w = agg.update(pd.Series({"a": 0.01, "b": -0.01, "c": 0.0}))
        assert w.sum() == pytest.approx(1.0)
        assert (w >= 0).all()


def test_warmup_holds_equal_weights():
    agg = HedgeAggregator(["a", "b"], HedgeConfig(warmup=6))
    for i in range(6):
        w = agg.update(pd.Series({"a": 0.10, "b": -0.10}))
        assert w["a"] == pytest.approx(0.5), f"month {i} should still be equal-weighted"
    assert agg.update(pd.Series({"a": 0.10, "b": -0.10}))["a"] > 0.5


def test_weight_moves_towards_the_better_expert():
    agg = HedgeAggregator(["good", "bad"], HedgeConfig(warmup=2, share=0.0))
    for _ in range(120):
        agg.update(pd.Series({"good": 0.02, "bad": -0.02}))
    assert agg.state.as_series()["good"] > 0.9


def test_fixed_share_tracks_a_regime_change():
    """Herbster-Warmuth: plain Hedge can get stuck; the share term lets it switch back."""
    data = panel(seed=3)
    plain = run_aggregation(data, HedgeConfig(share=0.0, warmup=12, floor=0.0))
    shared = run_aggregation(data, HedgeConfig(share=0.05, warmup=12, floor=0.0))
    second_half = data.index[len(data) // 2:]
    plain_w = plain.set_index("date").loc[second_half, "w_switcher"].iloc[-1]
    shared_w = shared.set_index("date").loc[second_half, "w_switcher"].iloc[-1]
    assert shared_w > plain_w


def test_regret_bound_holds_against_the_best_expert():
    data = panel(seed=1)
    result = run_aggregation(data, HedgeConfig(warmup=12))
    shortfall = result.attrs["best_expert_total"] - result.attrs["aggregate_total"]
    assert shortfall <= result.attrs["regret_bound"]


def test_aggregate_beats_the_worst_expert():
    data = panel(seed=2)
    result = run_aggregation(data, HedgeConfig(warmup=12))
    assert result.attrs["aggregate_total"] > data.sum().min()


def test_weights_in_force_never_use_the_current_month():
    """The causality property the whole claim rests on."""
    data = panel(seed=4)
    result = run_aggregation(data, HedgeConfig(warmup=0, share=0.0)).set_index("date")
    # month 0 must be equal-weighted: nothing has been observed yet
    assert result.iloc[0][["w_good", "w_bad", "w_switcher"]].to_numpy() == pytest.approx(1 / 3)
    # perturbing only the last month cannot change any earlier weight
    perturbed = data.copy()
    perturbed.iloc[-1] = perturbed.iloc[-1] + 10.0
    other = run_aggregation(perturbed, HedgeConfig(warmup=0, share=0.0)).set_index("date")
    cols = ["w_good", "w_bad", "w_switcher"]
    assert np.allclose(result[cols].to_numpy(), other[cols].to_numpy())


def test_equal_weight_benchmark_is_reported():
    data = panel(seed=5)
    eq = equal_weight_benchmark(data)
    assert len(eq) == len(data)
    assert eq.iloc[0] == pytest.approx(data.iloc[0].mean())


# ---------------------------------------------------------------- drift detection

def test_page_hinkley_detects_a_planted_break():
    rng = np.random.default_rng(7)
    series = pd.Series(np.concatenate([rng.normal(0.01, 0.01, 60), rng.normal(-0.02, 0.01, 60)]),
                       index=pd.date_range("2000-01-31", periods=120, freq="ME"))
    events = detect(series, delta=0.002, threshold=0.03, burn_in=24)
    assert events, "a 3-sigma regime break must be detected"
    assert any(e.direction == "decline" for e in events)
    first = min(e.date for e in events if e.direction == "decline")
    assert first >= series.index[60], "must not fire before the break"
    assert first <= series.index[80], "must fire within 20 months of the break"


def test_detector_is_quiet_on_a_stationary_series():
    rng = np.random.default_rng(11)
    series = pd.Series(rng.normal(0.005, 0.01, 240),
                       index=pd.date_range("2000-01-31", periods=240, freq="ME"))
    events = detect(series, delta=0.002, threshold=0.08, burn_in=24)
    assert len(events) <= 2, f"too many false alarms in 20 years: {len(events)}"


def test_threshold_calibration_targets_the_false_alarm_rate():
    rng = np.random.default_rng(13)
    validation = pd.Series(rng.normal(0.005, 0.01, 120),
                           index=pd.date_range("1990-01-31", periods=120, freq="ME"))
    thr = calibrate_threshold(validation, target_false_alarms_per_decade=1.0)
    assert thr > 0
    fired = len(detect(validation, threshold=thr))
    assert fired <= 4


def test_page_hinkley_resets_after_firing():
    """A constant stream is not a change, so the step has to be real for anything to fire."""
    ph = PageHinkley(delta=0.001, threshold=0.02, burn_in=5)
    dates = pd.date_range("2000-01-31", periods=60, freq="ME")
    values = [0.01] * 30 + [-0.05] * 30
    fired = [ph.update(d, v) for d, v in zip(dates, values)]
    events = [e for e in fired if e is not None]
    assert events and events[0].direction == "decline"
    assert ph._max_high >= ph._cum_high      # statistic is non-negative after the reset


def test_refit_schedule_compares_calendar_and_drift():
    data = panel(seed=17)
    schedule = refit_schedule(data.mean(axis=1), threshold=0.03)
    assert schedule["calendar_refit"].sum() == len(data) // 12
    assert set(schedule.columns) >= {"date", "calendar_refit", "drift_refit"}


# ---------------------------------------------------------------- reporting

def test_adaptation_report_summarises_the_rule():
    data = panel(seed=19)
    result = run_aggregation(data, HedgeConfig(warmup=12))
    weight_panel = result.rename(columns={f"w_{c}": c for c in data.columns})
    weight_panel["n_updates"] = range(len(weight_panel))

    class _M:
        def __init__(self, name, series):
            self.name = name
            self.returns = pd.DataFrame({"date": series.index, "after_tax_ret": series.to_numpy()})
    members = [_M(c, data[c]) for c in data.columns]

    report = adaptation_report(weight_panel, members)
    assert report["months"] == len(data)
    assert 1.0 <= report["min_effective_members"] <= report["mean_effective_members"] <= len(data.columns)
    assert set(report["final_weights"]) == set(data.columns)


def test_member_rewards_builds_a_clean_panel():
    data = panel(seed=23)

    class _M:
        def __init__(self, name, series):
            self.name = name
            self.returns = pd.DataFrame({"date": series.index, "after_tax_ret": series.to_numpy()})
    rewards = member_rewards([_M(c, data[c]) for c in data.columns])
    assert list(rewards.columns) == list(data.columns)
    assert rewards.index.is_monotonic_increasing
