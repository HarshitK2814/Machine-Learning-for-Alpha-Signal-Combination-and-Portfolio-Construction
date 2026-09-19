"""Investor tax regimes (workstream B, after-tax evaluation layer).

Almost every published machine-learning asset-pricing paper reports returns gross of tax, because
the implicit investor is a tax-exempt institution. That assumption is not innocuous: for a strategy
that turns over 100%+ per year, the tax bill can exceed the trading cost. Jeffrey and Arnott's
question - "is your alpha big enough to cover its taxes?" - is the one this module lets us answer.

We therefore do not hard-code "the" tax treatment. We define regimes and report the result under
each, so the reader can locate their own investor.

    TAX_EXEMPT   pension, endowment, sovereign fund. The literature's implicit default.
    TAXABLE_US   top-bracket US individual or family office holding the strategy directly.
    TRADER_475F  professional trader who has made the IRC s475(f) mark-to-market election:
                 all gains are ordinary and immediate, the wash-sale rule does not apply,
                 and the short/long holding-period distinction disappears.
    FUND_OFFSHORE offshore feeder paying only US withholding on dividends.

Statutory structure encoded here (US federal, individual):
  * s1(h)      long-term capital gain preferential rate, applies to property held > 12 months
  * s1222      short-term / long-term definitions; the holding period is *strictly* more than a year
  * s1233      gain or loss on closing a short sale is short-term, whatever the elapsed time
  * s1091      wash sale: a loss is disallowed if substantially identical property is acquired
                within 30 days before or after the sale; the loss is added to the new lot's basis
  * s1211(b)   an individual's net capital loss is deductible against ordinary income only up to
                $3,000 per year; the excess carries forward (s1212(b))
  * s1411      3.8% net investment income tax on top of the capital-gains rate
  * s263(h)    substitute dividend payments on a short position held 45 days or less are
                capitalised into the basis of the short rather than deducted currently
  * s1(h)(11)  dividends are "qualified" (and so taxed at the long-term rate) only if the share
                was held more than 60 days in the 121-day window around the ex-dividend date

[verify] The *numeric* rates below are the defaults we report, not a legal position. They must be
re-checked against the rate schedule in force for the sample period and the investor's state before
any number leaves this repository. All of them are overridable per run.
"""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class TaxRegime:
    """A complete description of how one investor is taxed on this strategy."""

    name: str
    short_term_rate: float = 0.0
    long_term_rate: float = 0.0
    qualified_dividend_rate: float = 0.0
    ordinary_dividend_rate: float = 0.0
    # Structural switches, not rates.
    mark_to_market: bool = False          # s475(f): tax unrealised P&L every year, ordinary
    wash_sale_rule: bool = True           # s1091
    wash_sale_window_days: int = 30
    long_term_months: int = 12            # s1222: held MORE than one year
    qualified_dividend_days: int = 61     # s1(h)(11) holding requirement
    short_dividend_deductible: bool = True   # substitute payments; see s263(h)
    short_dividend_capitalise_days: int = 46  # s263(h) threshold
    annual_ordinary_offset: float = 3_000.0  # s1211(b)
    loss_carryforward: bool = True
    payment_month: int = 4                # cash-basis accounting pays in April of the next year
    notes: str = ""

    @property
    def taxable(self) -> bool:
        return max(self.short_term_rate, self.long_term_rate,
                   self.qualified_dividend_rate, self.ordinary_dividend_rate) > 0.0

    @property
    def rate_spread(self) -> float:
        """How much a strategy gains per dollar by converting short-term gains into long-term."""
        return self.short_term_rate - self.long_term_rate

    def with_rates(self, **kwargs) -> "TaxRegime":
        return replace(self, **kwargs)


TAX_EXEMPT = TaxRegime(
    name="tax_exempt",
    notes="Pension, endowment, sovereign fund. The implicit investor in the ML asset-pricing "
          "literature; included so every after-tax number has a zero-tax control.",
)

TAXABLE_US = TaxRegime(
    name="taxable_us_top_bracket",
    short_term_rate=0.408,            # 37% top ordinary + 3.8% s1411 NIIT  [verify]
    long_term_rate=0.238,             # 20% s1(h) + 3.8% s1411 NIIT         [verify]
    qualified_dividend_rate=0.238,    # [verify]
    ordinary_dividend_rate=0.408,     # [verify]
    short_dividend_deductible=False,  # investment-interest limits bite for an individual
    notes="Top-bracket US individual holding the strategy directly, federal only, no state tax.",
)

TRADER_475F = TaxRegime(
    name="trader_475f_mtm",
    short_term_rate=0.408,            # everything is ordinary under the election  [verify]
    long_term_rate=0.408,
    qualified_dividend_rate=0.238,
    ordinary_dividend_rate=0.408,
    mark_to_market=True,
    wash_sale_rule=False,             # the election switches s1091 off
    annual_ordinary_offset=float("inf"),  # s475 losses are ordinary, not capital
    notes="Professional trader with an IRC s475(f) mark-to-market election. Worst case for "
          "deferral (unrealised gains are taxed annually) but immune to wash sales.",
)

FUND_OFFSHORE = TaxRegime(
    name="offshore_fund",
    qualified_dividend_rate=0.30,     # US statutory dividend withholding, treaty-reducible [verify]
    ordinary_dividend_rate=0.30,      # [verify]
    short_dividend_deductible=False,  # withholding is levied on the gross dividend received;
                                      # the substitute payment on the short leg does not offset it
    notes="Offshore feeder: no US tax on capital gains of a non-resident, 30% statutory "
          "withholding on US-source dividends (often reduced by treaty).",
)

REGIMES: dict[str, TaxRegime] = {r.name: r for r in (TAX_EXEMPT, TAXABLE_US, TRADER_475F, FUND_OFFSHORE)}


def get_regime(name: str | TaxRegime) -> TaxRegime:
    if isinstance(name, TaxRegime):
        return name
    key = str(name).lower()
    aliases = {"exempt": "tax_exempt", "none": "tax_exempt", "taxable": "taxable_us_top_bracket",
               "us": "taxable_us_top_bracket", "475f": "trader_475f_mtm", "mtm": "trader_475f_mtm",
               "offshore": "offshore_fund"}
    key = aliases.get(key, key)
    if key not in REGIMES:
        raise KeyError(f"unknown tax regime '{name}'; known: {sorted(REGIMES) + sorted(aliases)}")
    return REGIMES[key]
