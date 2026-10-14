"""Drift detection: when should a model refit itself, rather than on a calendar?

Every ML asset-pricing paper we track refits on a fixed schedule - annually, almost always. That is
a modelling choice nobody justifies, and it has an obvious failure mode: if the relationship breaks
in February, an annually refit model spends eleven months trading a stale mapping.

The alternative is to let the data decide. These are sequential change detectors with explicit
false-alarm control, not "refit when performance looks bad", and the threshold is fixed before the
out-of-sample period:

* **Page-Hinkley** (Page 1954; Hinkley 1971) - the classical CUSUM for a change in mean. Detects a
  sustained decline in realised performance with a controllable expected time between false alarms.
* **Two-sided CUSUM** - the same statistic run on both tails, so an *improvement* also triggers a
  refit (the model is leaving money on the table, not just losing it).
* **Rank-IC decay** - a detector on the forecasting signal itself rather than on realised P&L,
  which reacts sooner because it does not wait for the portfolio to lose money.

A detector that fires is not a licence to search. It triggers exactly one action: refit the current
specification on data up to that month. The specification itself is never re-chosen, so this adds
no trials to the multiple-testing count.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class DriftEvent:
    date: pd.Timestamp
    statistic: float
    threshold: float
    direction: str          # "decline" | "improvement"
    detector: str


@dataclass
class PageHinkley:
    """Sequential test for a change in the mean of a stream.

    ``delta`` is the smallest change worth reacting to (a tolerance band) and ``threshold`` sets the
    false-alarm rate. Both are fixed ex ante; we set them on validation months only.
    """

    delta: float = 0.002
    threshold: float = 0.05
    burn_in: int = 24
    two_sided: bool = True
    _n: int = 0
    _mean: float = 0.0
    _cum_low: float = 0.0
    _min_low: float = 0.0
    _cum_high: float = 0.0
    _max_high: float = 0.0
    events: list[DriftEvent] = field(default_factory=list)

    def reset(self) -> None:
        self._cum_low = self._min_low = self._cum_high = self._max_high = 0.0

    def update(self, date, value: float) -> DriftEvent | None:
        value = float(value)
        self._n += 1
        self._mean += (value - self._mean) / self._n
        if self._n <= self.burn_in:
            return None

        # Decrease branch: accumulate (x - mean + delta) and watch how far it falls below its peak.
        # The +delta matters: under no change the sum drifts gently *upward*, so the running maximum
        # keeps pace and the statistic stays near zero. Putting delta on the other branch makes the
        # statistic grow linearly in T and the detector fires on stationary data by construction.
        self._cum_high += value - self._mean + self.delta
        self._max_high = max(self._max_high, self._cum_high)
        stat_down = self._max_high - self._cum_high

        # Increase branch: accumulate (x - mean - delta) and watch how far it rises above its trough.
        self._cum_low += value - self._mean - self.delta
        self._min_low = min(self._min_low, self._cum_low)
        stat_up = self._cum_low - self._min_low

        if stat_down > self.threshold:
            event = DriftEvent(pd.Timestamp(date), stat_down, self.threshold, "decline", "page_hinkley")
            self.events.append(event)
            self.reset()
            return event
        if self.two_sided and stat_up > self.threshold:
            event = DriftEvent(pd.Timestamp(date), stat_up, self.threshold, "improvement", "page_hinkley")
            self.events.append(event)
            self.reset()
            return event
        return None


def detect(series: pd.Series, delta: float = 0.002, threshold: float = 0.05, burn_in: int = 24,
           two_sided: bool = True) -> list[DriftEvent]:
    """Run the detector over a monthly series and return every change point it flags."""
    ph = PageHinkley(delta=delta, threshold=threshold, burn_in=burn_in, two_sided=two_sided)
    out = []
    for date, value in series.sort_index().items():
        if pd.isna(value):
            continue
        event = ph.update(date, value)
        if event is not None:
            out.append(event)
    return out


def calibrate_threshold(validation: pd.Series, target_false_alarms_per_decade: float = 1.0,
                        delta: float = 0.002, grid: tuple[float, ...] = (0.01, 0.02, 0.03, 0.05,
                                                                          0.08, 0.12, 0.20)) -> float:
    """Pick the threshold on *validation* data so the detector fires about as often as we allow.

    Calibrating the false-alarm rate on validation months and then freezing it is what separates a
    detector from a fishing expedition.
    """
    years = max(len(validation) / 12.0, 1e-9)
    best, best_gap = grid[-1], np.inf
    for thr in grid:
        n = len(detect(validation, delta=delta, threshold=thr, burn_in=min(24, len(validation) // 3)))
        rate = n / years * 10.0
        gap = abs(rate - target_false_alarms_per_decade)
        if gap < best_gap:
            best, best_gap = thr, gap
    return float(best)


def refit_schedule(series: pd.Series, annual_months: tuple[int, ...] = (12,), **kwargs) -> pd.DataFrame:
    """Compare the calendar refit schedule with the drift-triggered one on the same series."""
    events = {e.date: e for e in detect(series, **kwargs)}
    rows = []
    for date in series.sort_index().index:
        date = pd.Timestamp(date)
        event = events.get(date)
        rows.append({"date": date,
                     "calendar_refit": date.month in annual_months,
                     "drift_refit": event is not None,
                     "direction": event.direction if event else "",
                     "statistic": event.statistic if event else np.nan})
    return pd.DataFrame(rows)
