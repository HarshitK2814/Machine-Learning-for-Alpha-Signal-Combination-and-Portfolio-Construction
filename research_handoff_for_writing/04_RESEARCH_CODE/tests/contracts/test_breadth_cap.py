"""The breadth cap of amendment 001B decides which names the Japanese arm is built from.

Two properties carry the amendment. The cap must keep the *largest* names deterministically, and it
must be **slack** for Germany and India - because that is the whole argument for it being one
uniform rule rather than a restriction written for the one country it bites on. If it ever stops
being slack there, two completed arms have silently changed and the published Germany result no
longer describes the portfolio that produced it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.contracts.intl import apply_breadth_cap


def panel(sizes_by_month: dict[str, list[float]], live: bool = True) -> pd.DataFrame:
    rows = []
    for date, sizes in sizes_by_month.items():
        for i, me in enumerate(sizes):
            rows.append({"date": pd.Timestamp(date), "permno": 1000 + i, "me": me,
                         "in_universe": live})
    return pd.DataFrame(rows)


def live_permnos(frame: pd.DataFrame, date: str) -> set[int]:
    d = frame[(frame["date"] == pd.Timestamp(date)) & frame["in_universe"].astype(bool)]
    return set(d["permno"])


# --------------------------------------------------------------------- it keeps the largest

def test_keeps_exactly_the_n_largest_names():
    frame = panel({"2015-01-31": [5.0, 1.0, 4.0, 2.0, 3.0]})
    out = apply_breadth_cap(frame, 2)
    # me 5.0 is permno 1000 and me 4.0 is permno 1002
    assert live_permnos(out, "2015-01-31") == {1000, 1002}


def test_a_month_already_under_the_cap_is_untouched():
    frame = panel({"2015-01-31": [3.0, 2.0, 1.0]})
    out = apply_breadth_cap(frame, 10)
    assert out["in_universe"].astype(bool).all()
    assert out["in_universe"].astype(bool).equals(frame["in_universe"].astype(bool))


def test_the_cap_is_applied_within_each_month_not_across_the_panel():
    """A name small in a big month can be large in a small one; the ranking is monthly."""
    frame = panel({"2015-01-31": [10.0, 9.0, 8.0], "2015-02-28": [1.0, 0.5, 0.2]})
    out = apply_breadth_cap(frame, 2)
    assert live_permnos(out, "2015-01-31") == {1000, 1001}
    assert live_permnos(out, "2015-02-28") == {1000, 1001}


def test_ties_are_broken_by_permno_so_the_selection_is_reproducible():
    frame = panel({"2015-01-31": [1.0, 1.0, 1.0, 1.0]})
    first = apply_breadth_cap(frame, 2)
    second = apply_breadth_cap(frame.sample(frac=1.0, random_state=7), 2)
    assert live_permnos(first, "2015-01-31") == {1000, 1001}
    assert live_permnos(second, "2015-01-31") == {1000, 1001}


# --------------------------------------------------------------------- what it must not do

def test_rows_are_never_dropped_only_the_flag_narrows():
    """Dropping rows would desynchronise signals from targets, which are aligned on (date, permno)."""
    frame = panel({"2015-01-31": [5.0, 4.0, 3.0, 2.0, 1.0]})
    out = apply_breadth_cap(frame, 2)
    assert len(out) == len(frame)
    assert list(out["permno"]) == list(frame["permno"])
    assert int(out["in_universe"].astype(bool).sum()) == 2


def test_a_name_outside_the_universe_is_never_promoted_into_it():
    """The cap only ever removes. A dead name that happens to be large must stay dead."""
    frame = pd.concat([
        panel({"2015-01-31": [1.0, 0.9]}, live=True),
        pd.DataFrame([{"date": pd.Timestamp("2015-01-31"), "permno": 99,
                       "me": 1e9, "in_universe": False}]),
    ], ignore_index=True)
    out = apply_breadth_cap(frame, 10)
    assert 99 not in live_permnos(out, "2015-01-31")
    assert live_permnos(out, "2015-01-31") == {1000, 1001}


def test_a_name_with_no_market_cap_cannot_be_ranked_and_is_excluded():
    """Sorting NaN to either end would make the cap depend on pandas' ordering of missing values."""
    frame = panel({"2015-01-31": [5.0, np.nan, 4.0]})
    out = apply_breadth_cap(frame, 3)
    assert 1001 not in live_permnos(out, "2015-01-31")
    assert live_permnos(out, "2015-01-31") == {1000, 1002}


def test_a_universe_without_market_caps_is_refused_rather_than_ranked_arbitrarily():
    frame = panel({"2015-01-31": [1.0, 2.0]}).drop(columns=["me"])
    with pytest.raises(ValueError, match="market-cap"):
        apply_breadth_cap(frame, 1)


def test_an_empty_universe_is_handled_without_error():
    frame = panel({"2015-01-31": [1.0, 2.0]}, live=False)
    out = apply_breadth_cap(frame, 1)
    assert not out["in_universe"].astype(bool).any()


# --------------------------------------------------------------------- the amendment's claim

@pytest.mark.parametrize("country", ["DEU", "IND"])
def test_the_600_cap_is_slack_for_the_completed_arms(country):
    """Amendment 001B's load-bearing claim, asserted against the real promoted panel.

    If this fails, the cap has started to bite on an arm whose results are already published, and
    docs/RESULTS_DEU_2026-10-08.md and docs/RESULTS_WEDGE_TEST.md no longer describe the portfolios
    that produced them.
    """
    from alphacomb.contracts import intl

    try:
        base = intl.load_country_bundle(country).universe
    except Exception as exc:  # pragma: no cover - panel absent in a bare checkout
        pytest.skip(f"promoted {country} panel unavailable: {exc}")
    capped = intl.load_country_bundle(country, max_names=600).universe
    assert base["in_universe"].astype(bool).equals(capped["in_universe"].astype(bool)), (
        f"the 600-name cap is no longer slack for {country}; amendment 001B says it must be")


def test_the_600_cap_binds_on_japan():
    """The other half: if it did not bind, the amendment would be doing nothing."""
    from alphacomb.contracts import intl

    try:
        base = intl.load_country_bundle("JPN").universe
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"promoted JPN panel unavailable: {exc}")
    capped = intl.load_country_bundle("JPN", max_names=600).universe
    live = capped["in_universe"].astype(bool)
    assert live.sum() < base["in_universe"].astype(bool).sum()
    per_month = capped.loc[live].groupby("date").size()
    assert per_month.max() <= 600
