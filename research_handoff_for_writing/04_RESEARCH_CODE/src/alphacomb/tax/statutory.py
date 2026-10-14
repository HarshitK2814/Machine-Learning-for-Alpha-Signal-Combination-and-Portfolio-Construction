"""Statutory investor regimes for DEU, IND and JPN, built from the frozen C14 schedule.

Why this module exists
----------------------
The paper's identification is cross-country variation in **tax architecture**, not in tax level:

    the friction penalty on a machine-learning design is ordered by each country's statutory
    holding-period wedge, and is identically zero where the law sets a flat capital-gains rate.

So the wedge ``Delta = cgt_short - cgt_long`` is the treatment variable, and it has to come from
the statute rather than from a constant someone typed. Every regime here is therefore *derived*
from ``data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv`` - the same frozen
source Workstream A certified - so a regime cannot silently disagree with the schedule the rest of
the C14 machinery resolves against.

What the schedule says over the frozen 2009-2019 evaluation window
------------------------------------------------------------------
======  ==========================================  =========  ========  =======  ========
country regime                                      cgt_short  cgt_long  wedge    boundary
======  ==========================================  =========  ========  =======  ========
DEU     ABGELTUNGSTEUER (2009-01-01..2020-12-31)      0.26375   0.26375   **0.00**  none
JPN     EXTENDED_LISTED_SHARE_REDUCED (..2013-12-31)  0.10000   0.10000   **0.00**  none
JPN     NORMAL_LISTED_SHARE + RECONSTRUCTION (2014-)  0.20315   0.20315   **0.00**  none
IND     STT125_LTCG_EXEMPT_STCG15 (2009-04..2012-06)  0.15000   0.00000   **0.15**  12 months
IND     STT100_LTCG_EXEMPT_STCG15 (2012-07..2018-03)  0.15000   0.00000   **0.15**  12 months
IND     SECTION_112A_STT100 (2018-04..2020-03)        0.15000   0.10000   **0.05**  12 months
======  ==========================================  =========  ========  =======  ========

Two features of that table are the whole paper:

1. **Germany and Japan are placebos the tax code wrote.** Neither has a holding-period boundary for
   listed shares in the window, so no amount of turnover can move a gain from one rate to another.
   Germany is the sharp case: at 26.375% it is taxed *harder* than India's 15% short-term rate, so
   a "high taxes punish high turnover" story predicts Germany suffers most, while the wedge story
   predicts Germany suffers nothing. The two predictions are opposed, which is what makes the test
   informative rather than confirmatory.
2. **India's wedge falls inside the sample.** Section 112A (2018-04-01) ends the LTCG exemption and
   cuts the wedge from 0.15 to 0.05, giving a within-country event study on top of the
   cross-country ordering. It is also why the frozen mechanism subwindow stops at 2018-03-31: over
   2014-01-01..2018-03-31 all three countries sit on a single constant-rate rule, so a static
   regime is exactly faithful there and no dated machinery is required.

None of these jurisdictions has a s1091 wash-sale rule or a s1211(b) ordinary-income offset, so
those US-specific switches are turned off rather than inherited from the US default.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .regimes import TaxRegime

#: The frozen statutory source Workstream A certified. Not a copy - the same file the dated C14
#: engine resolves against.
FROZEN_SCHEDULE = Path("data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv")

#: Tax year-end month per country (India runs April-March).
YEAR_END_MONTH = {"DEU": 12, "JPN": 12, "IND": 3}

COUNTRIES = ("DEU", "IND", "JPN")

#: No holding-period boundary in the statute is represented by a horizon longer than any sample,
#: so every gain is "short term" at a rate that equals the long-term rate anyway.
NO_BOUNDARY_MONTHS = 10_000


def _repo_root() -> Path:
    from ..contracts import paths
    return Path(paths.REPO_ROOT)


@lru_cache(maxsize=4)
def load_schedule(path: str | None = None) -> pd.DataFrame:
    """The frozen statutory schedule, with parsed effective dates and an explicit wedge column."""
    p = Path(path) if path else _repo_root() / FROZEN_SCHEDULE
    if not p.exists():
        raise FileNotFoundError(
            f"frozen C14 statutory schedule not found at {p}. The statutory regimes are derived "
            "from it rather than hardcoded, so there is no fallback: without the schedule there is "
            "no certified wedge."
        )
    d = pd.read_csv(p)
    d["effective_from"] = pd.to_datetime(d["effective_from"])
    d["effective_to"] = pd.to_datetime(d["effective_to"])
    d["wedge"] = d["cgt_short"] - d["cgt_long"]
    return d


def resolve_rule(country: str, date, path: str | None = None) -> pd.Series:
    """The single statutory rule in force for ``country`` at ``date``."""
    d = load_schedule(path)
    ts = pd.Timestamp(date)
    hit = d[(d["country"] == country) & (d["effective_from"] <= ts) & (d["effective_to"] >= ts)]
    if hit.empty:
        raise KeyError(f"no statutory rule for {country} at {ts.date()} in the frozen schedule")
    if len(hit) > 1:
        raise ValueError(
            f"{country} at {ts.date()} matches {len(hit)} overlapping statutory rules; the frozen "
            "schedule must be a partition in time, not a set of overlapping ranges"
        )
    return hit.iloc[0]


def statutory_regime(country: str, date, path: str | None = None) -> TaxRegime:
    """Build the investor regime in force for ``country`` at ``date``, straight from the statute.

    A missing ``cgt_short`` with a present ``cgt_long`` (or the reverse) is an unresolved rate in
    the schedule, not a zero: those are raised rather than defaulted, because silently taxing at
    zero would manufacture the paper's result in the direction it wants.
    """
    if country not in COUNTRIES:
        raise KeyError(f"unknown country {country!r}; the frozen schedule covers {COUNTRIES}")
    r = resolve_rule(country, date, path)
    short, long = r["cgt_short"], r["cgt_long"]
    if not np.isfinite(short) or not np.isfinite(long):
        raise ValueError(
            f"{country} at {pd.Timestamp(date).date()} ({r['legal_regime']}) has an unresolved "
            f"capital-gains rate (cgt_short={short!r}, cgt_long={long!r}). The frozen schedule "
            f"marks it open; it must not be defaulted to zero. source_status={r['source_status']!r}"
        )
    boundary = r["holding_period_months"]
    months = int(boundary) if np.isfinite(boundary) else NO_BOUNDARY_MONTHS
    div = r["dividend_rate"]
    div = float(div) if np.isfinite(div) else float(short)
    return TaxRegime(
        name=f"{country}_{r['legal_regime']}",
        short_term_rate=float(short),
        long_term_rate=float(long),
        qualified_dividend_rate=div,
        ordinary_dividend_rate=div,
        long_term_months=months,
        # s1091 and s1211(b) are United States law and have no counterpart in these jurisdictions.
        wash_sale_rule=False,
        annual_ordinary_offset=0.0,
        losses_ring_fenced=bool(r.get("losses_ring_fenced", False) is True),
        payment_month=YEAR_END_MONTH[country],
        notes=(f"{country} {r['legal_regime']} in force {r['effective_from'].date()}.."
               f"{r['effective_to'].date()}; wedge={float(short) - float(long):.5f}; "
               f"derived from the frozen C14 schedule, not hardcoded"),
    )


def wedge(country: str, date, path: str | None = None) -> float:
    """``cgt_short - cgt_long``: the treatment variable of the paper."""
    r = statutory_regime(country, date, path)
    return r.rate_spread


def mechanism_window_regimes(path: str | None = None) -> dict[str, TaxRegime]:
    """The three regimes in force across the frozen mechanism subwindow 2014-01-01..2018-03-31.

    Every country sits on one constant rule throughout that span, which is why the subwindow was
    frozen: a static regime per country is exactly faithful and the dated engine is not needed.
    This function asserts that rather than assuming it.
    """
    lo, hi = pd.Timestamp("2014-01-01"), pd.Timestamp("2018-03-31")
    out = {}
    for c in COUNTRIES:
        a, b = statutory_regime(c, lo, path), statutory_regime(c, hi, path)
        if a.name != b.name:
            raise ValueError(
                f"{c} changes statutory regime inside the frozen mechanism subwindow "
                f"({a.name} -> {b.name}); a static regime is not faithful there and the dated C14 "
                "engine must be used instead"
            )
        out[c] = a
    return out
