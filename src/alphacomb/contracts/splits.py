"""Walk-forward split calendar with embargo and lockbox protection. SHARED FILE (contract C8).

Design (PDF 4, Section 9):

* expanding training window from ``train_start``;
* a rolling 60-month validation block immediately before the test year;
* an embargo equal to the target horizon between train/validation and validation/test, so that
  overlapping multi-month labels cannot leak;
* annual refit: one split per test year;
* the lockbox (2021-2025) is refused unless the team has frozen the specification.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .io import freeze_tag, load_config


class LockboxError(RuntimeError):
    """Raised when code tries to touch the held-out period before the specification freeze."""


def _m(ts) -> pd.Timestamp:
    """Month-end timestamp."""
    return pd.Timestamp(ts) + pd.offsets.MonthEnd(0)


def _shift(ts, months: int) -> pd.Timestamp:
    return _m(pd.Timestamp(ts) + pd.DateOffset(months=months))


@dataclass(frozen=True)
class Split:
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    val_start: pd.Timestamp
    val_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    horizon_months: int
    embargo_months: int

    @property
    def test_year(self) -> int:
        return int(self.test_start.year)

    @property
    def label(self) -> str:
        return f"test{self.test_year}"

    def mask(self, dates: pd.Series, part: str) -> pd.Series:
        lo, hi = {
            "train": (self.train_start, self.train_end),
            "val": (self.val_start, self.val_end),
            "test": (self.test_start, self.test_end),
        }[part]
        d = pd.to_datetime(dates)
        return (d >= lo) & (d <= hi)

    def assert_no_leakage(self) -> None:
        gap_tv = (self.val_start.to_period("M") - self.train_end.to_period("M")).n
        gap_vt = (self.test_start.to_period("M") - self.val_end.to_period("M")).n
        if gap_tv <= self.embargo_months or gap_vt <= self.embargo_months:
            raise AssertionError(
                f"embargo violated: train->val gap {gap_tv}m, val->test gap {gap_vt}m, "
                f"need > {self.embargo_months}m for horizon {self.horizon_months}m"
            )

    def as_dict(self) -> dict:
        return {
            "train_start": str(self.train_start.date()), "train_end": str(self.train_end.date()),
            "val_start": str(self.val_start.date()), "val_end": str(self.val_end.date()),
            "test_start": str(self.test_start.date()), "test_end": str(self.test_end.date()),
            "horizon_months": self.horizon_months, "embargo_months": self.embargo_months,
        }


def generate(horizon_months: int = 1, cfg: dict | None = None, *, include_lockbox: bool = False,
             first_test_year: int | None = None, last_test_year: int | None = None) -> list[Split]:
    """Build the annual walk-forward calendar for a given target horizon."""
    cfg = cfg or load_config("base")
    s = cfg["splits"]
    embargo = s.get("embargo_months") or horizon_months
    first = first_test_year or int(s["first_test_year"])
    last = last_test_year or int(s["last_dev_test_year"])
    val_months = int(s["validation_months"])
    rolling = str(s.get("train_window", "expanding")).startswith("rolling")
    rolling_months = 240

    if include_lockbox:
        assert_lockbox_allowed()
        last = int(pd.Timestamp(s["lockbox_end"]).year)

    splits: list[Split] = []
    for year in range(first, last + 1):
        test_start = _m(f"{year}-01-31")
        test_end = _m(f"{year}-12-31")
        val_end = _shift(test_start, -(embargo + 1))
        val_start = _shift(val_end, -(val_months - 1))
        train_end = _shift(val_start, -(embargo + 1))
        train_start = _m(s["train_start"]) if not rolling else _shift(train_end, -(rolling_months - 1))
        split = Split(train_start, train_end, val_start, val_end, test_start, test_end, horizon_months, embargo)
        split.assert_no_leakage()
        splits.append(split)
    return splits


def assert_lockbox_allowed() -> None:
    """The lockbox may be opened only once, after the specification freeze."""
    if not freeze_tag():
        raise LockboxError(
            "Lockbox period is closed. It may be used only after the team freezes the specification "
            "and sets ALPHACOMB_FREEZE_TAG (e.g. ALPHACOMB_FREEZE_TAG=v-freeze). See PDF 4, Section 9."
        )


def assert_not_lockbox(dates, cfg: dict | None = None) -> None:
    """Guard used by model and portfolio code: refuse data inside the lockbox window."""
    cfg = cfg or load_config("base")
    start = _m(cfg["splits"]["lockbox_start"])
    d = pd.to_datetime(pd.Series(list(dates)))
    if (d >= start).any() and not freeze_tag():
        raise LockboxError(
            f"{int((d >= start).sum())} observations fall inside the lockbox window (>= {start.date()}) "
            "and the specification is not frozen. Development runs must stop at the dev test end."
        )
