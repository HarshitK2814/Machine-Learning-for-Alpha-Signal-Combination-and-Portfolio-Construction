"""The statutory wedge is the paper's treatment variable, so it is pinned to the statute.

If these numbers move, the identification moves with them, and every cross-country claim in the
paper changes meaning. They are asserted against the frozen C14 schedule rather than against
constants typed here, so a drift in the schedule fails loudly instead of quietly re-defining the
treatment.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.tax.statutory import (COUNTRIES, NO_BOUNDARY_MONTHS, load_schedule,
                                     mechanism_window_regimes, resolve_rule, statutory_regime,
                                     wedge)

WINDOW = ("2009-01-01", "2019-12-31")
MECHANISM = ("2014-01-01", "2018-03-31")


def test_schedule_covers_the_three_countries():
    d = load_schedule()
    assert set(d["country"].unique()) == set(COUNTRIES)


def test_schedule_is_a_partition_in_time_per_country():
    """Overlapping rules would make 'the rate in force' ambiguous, and resolve() would be a guess."""
    d = load_schedule()
    for country, g in d.groupby("country"):
        g = g.sort_values("effective_from")
        starts, ends = g["effective_from"].to_numpy(), g["effective_to"].to_numpy()
        assert (starts[1:] > ends[:-1]).all(), f"{country} has overlapping statutory rules"


# ------------------------------------------------- the identification, stated as assertions

@pytest.mark.parametrize("country", ["DEU", "JPN"])
def test_flat_rate_countries_have_exactly_zero_wedge(country):
    """Germany and Japan are the placebos. Not approximately zero - exactly, by statute."""
    for date in pd.date_range(*MECHANISM, freq="YE"):
        r = statutory_regime(country, date)
        assert r.short_term_rate == r.long_term_rate
        assert r.rate_spread == 0.0
        assert r.long_term_months == NO_BOUNDARY_MONTHS, (
            "a flat-rate country must carry no holding-period boundary; if the schedule grows one, "
            "the placebo is gone and the design needs rethinking")


def test_india_carries_a_positive_wedge_and_a_twelve_month_boundary():
    r = statutory_regime("IND", "2016-06-30")
    assert r.rate_spread == pytest.approx(0.15)
    assert r.long_term_months == 12
    assert r.long_term_rate == 0.0, "LTCG was exempt before section 112A"


def test_germany_is_taxed_harder_than_india_yet_has_no_wedge():
    """The two stories make opposite predictions, which is what makes the test informative.

    A 'high tax rates punish high turnover' account predicts Germany suffers most of the three.
    The wedge account predicts Germany suffers nothing. They cannot both be right.
    """
    deu, ind = statutory_regime("DEU", "2016-06-30"), statutory_regime("IND", "2016-06-30")
    assert deu.short_term_rate > ind.short_term_rate
    assert deu.rate_spread == 0.0 < ind.rate_spread


def test_section_112A_cuts_the_indian_wedge_inside_the_sample():
    """The within-country event study: 0.15 -> 0.05 on 2018-04-01."""
    assert wedge("IND", "2018-03-31") == pytest.approx(0.15)
    assert wedge("IND", "2018-04-01") == pytest.approx(0.05)


def test_wedge_ordering_across_countries_is_the_predicted_one():
    w = {c: wedge(c, "2016-06-30") for c in COUNTRIES}
    assert w["IND"] > w["DEU"] == w["JPN"] == 0.0


# --------------------------------------------------------------- the mechanism subwindow

def test_every_country_is_on_one_constant_rule_across_the_mechanism_subwindow():
    """This is why 2014-01-01..2018-03-31 was frozen; a static regime is faithful only if true."""
    regimes = mechanism_window_regimes()
    assert set(regimes) == set(COUNTRIES)
    for country, r in regimes.items():
        first = statutory_regime(country, MECHANISM[0])
        last = statutory_regime(country, MECHANISM[1])
        assert first.name == last.name == r.name


def test_mechanism_window_regimes_would_refuse_a_regime_change():
    """The guard has to fire, otherwise it is decoration.

    2018-04-01 is inside India's section 112A change, so a window spanning it is not constant.
    """
    from alphacomb.tax import statutory as st

    assert st.statutory_regime("IND", "2018-03-31").name != st.statutory_regime("IND", "2018-06-30").name


# --------------------------------------------------------------- refusing to invent a rate

def test_an_unresolved_rate_raises_rather_than_defaulting_to_zero(tmp_path):
    """A silent zero would manufacture the paper's result in the direction it wants."""
    d = load_schedule().copy()
    row = d[(d["country"] == "DEU") & (d["effective_from"] <= pd.Timestamp("2016-06-30"))
            & (d["effective_to"] >= pd.Timestamp("2016-06-30"))].index[0]
    d.loc[row, "cgt_short"] = np.nan
    p = tmp_path / "broken_schedule.csv"
    d.to_csv(p, index=False)
    load_schedule.cache_clear()
    with pytest.raises(ValueError, match="unresolved"):
        statutory_regime("DEU", "2016-06-30", path=str(p))
    load_schedule.cache_clear()


def test_unknown_country_is_refused():
    with pytest.raises(KeyError, match="USA"):
        statutory_regime("USA", "2016-06-30")


def test_us_specific_switches_are_off_for_these_jurisdictions():
    """s1091 wash sales and the s1211(b) offset are United States law with no counterpart here."""
    for c in COUNTRIES:
        r = statutory_regime(c, "2016-06-30")
        assert r.wash_sale_rule is False
        assert r.annual_ordinary_offset == 0.0


def test_india_runs_an_april_march_tax_year():
    assert statutory_regime("IND", "2016-06-30").payment_month == 3
    assert statutory_regime("DEU", "2016-06-30").payment_month == 12
    assert statutory_regime("JPN", "2016-06-30").payment_month == 12


def test_resolve_rule_reports_the_named_legal_regime():
    r = resolve_rule("DEU", "2016-06-30")
    assert r["legal_regime"] == "ABGELTUNGSTEUER"
    assert statutory_regime("IND", "2016-06-30").name.endswith("STT100_LTCG_EXEMPT_STCG15")
