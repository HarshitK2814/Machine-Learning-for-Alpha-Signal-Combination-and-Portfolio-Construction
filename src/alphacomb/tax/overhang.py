"""Deferral overhang: the gap between what tax-aware strategies report and what investors own.

The live dispute this answers
-----------------------------
Tax-aware long/short is now a **$100bn+** business, pioneered by AQR and rapidly copied. It is also
publicly contested. A short-biased manager, Nate Koppikar of Orso Partners, put the criticism this
way: the product's true alpha "is simply extreme tax avoidance ... the mechanical goal of the fund
is to aggressively realize net capital losses on the short side while perpetually deferring the
realization of gains on the long side", and he compared it to the options-basket trade that ended
in a multi-billion-dollar IRS settlement. Fidelity and Schwab have withdrawn from offering these
accounts, citing operational and regulatory tail risk; Goldman and BNY Pershing have stepped in.

AQR's answer is that the objective is **pre-tax alpha**, and the tax treatment is incidental.

**That is an empirical question, and nobody has published the decomposition.**

The measurement gap
-------------------
"Perpetually deferring the realisation of gains" does not make the tax disappear. It accumulates an
embedded unrealised gain - a **deferred tax liability** the investor owns but does not see on a
realised-basis performance report.

The USIPC After-Tax Performance Standards and the SEC require mutual funds to report **both** a
pre-liquidation and a mark-to-liquidation figure, precisely so that this liability is visible:

    liquidation value = market value - tax rate * (market value - cost basis)

Tax-aware long/short is generally sold through separately managed accounts and private funds, not
mutual funds, so that dual-reporting requirement does not bite in the same way. The industry
standard is the pre-liquidation number.

This module computes both from the lot-level ledger, and the **overhang** between them:

    overhang = pre-liquidation return - mark-to-liquidation return

It is the portion of reported performance that is a deferred liability rather than a realised gain.
A strategy whose advantage is genuine pre-tax alpha has a small overhang. A strategy whose advantage
is deferral has a large and growing one. **That distinction is the entire dispute, and it is
measurable.**

The sign matters and runs both ways. A book carrying embedded **losses** has a *negative* overhang:
liquidating would realise a tax credit, so the realised-basis report **understates** what the
investor owns. Only a book carrying embedded **gains** is flattered by realised-basis reporting.

What this module does NOT claim
-------------------------------
It does not say deferral is illegitimate. Deferring tax is valuable - money kept today compounds,
and the liability may be stepped up at death or offset by later losses. The USIPC standards
themselves note that mark-to-liquidation penalises a deferring manager who is in fact adding value.

The claim is narrower and harder to argue with: **both numbers should be shown, because they can
diverge a long way, and only one of them is currently reported.**
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .backtest import TaxConfig, after_tax_backtest
from .lots import TaxLotLedger
from .regimes import TaxRegime, get_regime


@dataclass
class OverhangResult:
    """Pre-liquidation versus mark-to-liquidation, and the gap between them."""

    months: int
    pre_liquidation_ann: float        # what a realised-basis report shows
    liquidation_ann: float            # what the investor would keep on exit today
    overhang_ann: float               # pre-liq minus liq. POSITIVE = deferred liability,
                                      # NEGATIVE = deferred tax ASSET from embedded losses
    overhang_share: float             # overhang as a share of reported performance
    terminal_embedded_gain: float     # unrealised gain at the end, as a share of NAV
    terminal_deferred_tax: float      # tax owed on it, as a share of NAV
    embedded_gain_path: pd.Series
    verdict: str

    def summary(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not isinstance(v, pd.Series)}


def deferral_overhang(weights: pd.DataFrame, bundle, cfg: dict,
                      regime: str | TaxRegime = "taxable_us_top_bracket",
                      periods: int = 12, **tax_kwargs) -> OverhangResult:
    """Decompose reported after-tax performance into realised gain and deferred liability.

    Runs the lot-level ledger once, then reports the same strategy two ways:

    * **pre-liquidation** - tax on what was actually realised. The industry standard.
    * **mark-to-liquidation** - as if every open position were sold on the final date, so the
      embedded gain is taxed. Required of mutual funds by the USIPC standards and the SEC.

    The gap is the deferral overhang.
    """
    tc = TaxConfig(regime=get_regime(regime), liquidate_at_end=True,
                   initial_nav=float(cfg["costs"]["aum_usd_2020"]), **tax_kwargs)
    frame = after_tax_backtest(weights, bundle, cfg, tc)
    if frame.empty:
        raise ValueError("no months produced; check the weights table")

    months = len(frame)
    years = months / periods
    pre = float(frame["after_tax_ret"].mean() * periods)

    deferred = float(frame.attrs.get("deferred_tax_ret", 0.0))
    liquidation = pre - deferred / max(years, 1e-9)
    overhang = pre - liquidation
    share = overhang / abs(pre) if abs(pre) > 1e-12 else float("nan")

    embedded = frame.set_index("date")["unrealised"]
    terminal_gain = float(embedded.iloc[-1])

    if overhang < 0:
        # Embedded LOSSES, not gains. Liquidating would realise them and generate a tax credit, so
        # the liquidation figure is HIGHER than the realised-basis one. The strategy carries a
        # deferred tax ASSET. A first version of this module asserted that liquidation can only
        # reduce the reported figure; that is true only when the embedded position is a net gain,
        # and a test caught it.
        verdict = ("NEGATIVE overhang: the book carries embedded LOSSES, so liquidation would "
                   "realise a tax credit. The realised-basis report UNDERSTATES what the investor "
                   "owns - the opposite of the criticism levelled at tax-aware long/short")
    elif abs(share) < 0.10:
        verdict = ("small overhang: reported performance is substantially realised, consistent "
                   "with a pre-tax-alpha explanation")
    elif abs(share) < 0.30:
        verdict = ("material overhang: a meaningful minority of reported performance is a deferred "
                   "liability and both figures should be shown")
    else:
        verdict = ("LARGE overhang: most of the reported advantage is deferral, not realised gain. "
                   "A realised-basis report materially overstates what the investor owns")

    return OverhangResult(
        months=months, pre_liquidation_ann=pre, liquidation_ann=liquidation,
        overhang_ann=overhang, overhang_share=share,
        terminal_embedded_gain=terminal_gain, terminal_deferred_tax=deferred,
        embedded_gain_path=embedded, verdict=verdict)


def overhang_trajectory(weights: pd.DataFrame, bundle, cfg: dict,
                        regime: str | TaxRegime = "taxable_us_top_bracket",
                        checkpoints=(36, 60, 120, 180, 216), periods: int = 12,
                        **tax_kwargs) -> pd.DataFrame:
    """Does the overhang grow, stabilise, or decay as the strategy ages?

    This is the crux of the criticism. If deferral compounds indefinitely, the liability grows
    without bound and the reported number drifts ever further from what the investor owns. If it
    stabilises - because losses eventually have to be realised, or because basis refreshes - the
    criticism is weaker.

    Related and independently documented: Arnott, Berkin & Ye (2001) show the value of loss
    harvesting **decays** as a portfolio's basis falls. The same mechanism should cap the overhang.
    We measure it rather than assuming either way.
    """
    rows = []
    dates = sorted(weights["date"].unique())
    for k in checkpoints:
        if k > len(dates):
            continue
        cut = weights[weights["date"].isin(dates[:k])]
        res = deferral_overhang(cut, bundle, cfg, regime, periods, **tax_kwargs)
        rows.append({
            "months": k, "years": round(k / periods, 1),
            "pre_liquidation_ann": res.pre_liquidation_ann,
            "liquidation_ann": res.liquidation_ann,
            "overhang_ann": res.overhang_ann,
            "overhang_share": res.overhang_share,
            "embedded_gain_pct_nav": res.terminal_embedded_gain,
            "deferred_tax_pct_nav": res.terminal_deferred_tax,
        })
    return pd.DataFrame(rows)


def harvesting_decomposition(weights: pd.DataFrame, bundle, cfg: dict,
                             regime: str | TaxRegime = "taxable_us_top_bracket",
                             periods: int = 12, **tax_kwargs) -> dict:
    """Where does the after-tax advantage actually come from?

    Splits the gap between a tax-exempt investor's net-of-cost return and a taxable investor's
    after-tax return into its parts, so the "pre-tax alpha or tax avoidance?" question has an
    arithmetic answer rather than a rhetorical one:

    * **gross alpha** - the return before any friction, which is what AQR says the product is for
    * **cost drag** - trading costs, identical for both investors
    * **tax on realised gains** - actually paid
    * **harvesting credit** - value of realised losses, net of what s1091 disallows
    * **wash-disallowed** - harvested losses the rule refuses, a pure deadweight cost
    * **deferral overhang** - the liability accrued but not paid

    Krasner & Sosner (2024) report that the net capital losses of a tax-aware long/short book come
    mainly from **deferral of short-term gains**, not from elevated loss realisation. This function
    tests that claim directly on any strategy the pipeline produces.
    """
    exempt = after_tax_backtest(weights, bundle, cfg,
                                TaxConfig(regime=get_regime("tax_exempt"),
                                          initial_nav=float(cfg["costs"]["aum_usd_2020"]),
                                          **tax_kwargs))
    res = deferral_overhang(weights, bundle, cfg, regime, periods, **tax_kwargs)
    taxed = after_tax_backtest(weights, bundle, cfg,
                               TaxConfig(regime=get_regime(regime), liquidate_at_end=True,
                                         initial_nav=float(cfg["costs"]["aum_usd_2020"]),
                                         **tax_kwargs))

    gross = float(exempt["gross_ret"].mean() * periods)
    cost = float((exempt["gross_ret"] - exempt["net_ret"]).mean() * periods)
    tax_paid = float(taxed["tax_ret"].mean() * periods)
    realised_st = float(taxed["realised_st"].mean() * periods)
    realised_lt = float(taxed["realised_lt"].mean() * periods)
    wash = float(taxed["wash_disallowed"].mean() * periods)

    total_gain = realised_st + realised_lt
    deferral_share = (res.terminal_embedded_gain /
                      (abs(total_gain) * res.months / periods + abs(res.terminal_embedded_gain))
                      if (total_gain or res.terminal_embedded_gain) else float("nan"))

    return {
        "gross_alpha_ann": gross,
        "cost_drag_ann": -cost,
        "tax_paid_ann": -tax_paid,
        "pre_liquidation_ann": res.pre_liquidation_ann,
        "liquidation_ann": res.liquidation_ann,
        "deferral_overhang_ann": res.overhang_ann,
        "overhang_share_of_reported": res.overhang_share,
        "realised_short_term_ann": realised_st,
        "realised_long_term_ann": realised_lt,
        "wash_disallowed_ann": wash,
        "embedded_gain_pct_nav": res.terminal_embedded_gain,
        "deferred_tax_pct_nav": res.terminal_deferred_tax,
        "unrealised_share_of_total_gains": deferral_share,
        "verdict": res.verdict,
    }
