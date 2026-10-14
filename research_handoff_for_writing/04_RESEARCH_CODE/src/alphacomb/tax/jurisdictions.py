"""Country tax and transaction-cost architectures - the identification strategy, not a detail.

Why this module is the most important idea in the project
---------------------------------------------------------
The hypothesis in ``03_Research_Gaps/GAP_The_Tax_Wedge_in_Complexity.md`` is that model complexity
carries an after-tax penalty through a **holding-period** channel, distinct from the **turnover**
channel that the cost-aware machine-learning literature already handles.

Inside one country those two channels are hopelessly confounded: a model that trades more also
holds for less time. You cannot separate them.

Across countries they come apart, because **tax architectures differ in kind, not just in level**:

* The **United States** has a large holding-period wedge (40.8% vs 23.8%, a 17-point gap at exactly
  twelve months) and **no transaction tax at all**.
* **India** has a moderate holding-period wedge (20% vs 12.5%, 7.5 points, also at twelve months)
  but a **large transaction tax** - STT on both sides of a delivery trade, plus stamp duty, plus
  GST on brokerage.
* **Germany** and **Japan** have a **flat** capital-gains rate with **no holding-period
  distinction whatsoever**, and negligible transaction taxes.
* **Taiwan**, **Hong Kong**, **China** and the **United Kingdom** have material transaction taxes
  with a flat or zero capital-gains rate.
* **Singapore** and **Hong Kong** tax capital gains at **zero** for most investors.

That gives a 2x2 that nature built for us:

                        |  low transaction tax  |  high transaction tax
    ------------------- | --------------------- | ---------------------
    holding-period wedge|  United States        |  India
    flat / no wedge     |  Germany, Japan       |  Taiwan, UK, China

**Germany and Japan are the placebo.** They have no holding-period wedge, so if the complexity
penalty is really a holding-period phenomenon it must *vanish* there while the turnover penalty
persists. **Singapore and Hong Kong are the double placebo**: no capital-gains tax at all, so only
the transaction channel can operate.

A result that holds in the US, weakens in India, and disappears in Germany is very hard to explain
as anything other than the holding-period channel. That is an identification argument, and it is
what turns "we added taxes to a backtest" into a paper.

Status and honesty
------------------
**Every numeric rate below is `[verify]`.** Tax law changes, varies by investor type and residency,
and several of these were checked against secondary sources rather than statute. They are encoded
as *defaults for a sensitivity analysis*, not as tax advice or a legal position. Before any number
leaves this repository each regime must be checked against the rate schedule in force for the
sample period. Where a rule is genuinely uncertain it is marked in ``notes``.

The point of the module does not depend on the third decimal place. It depends on the *architecture*
- whether a holding-period boundary exists at all, and whether a transaction tax exists at all -
and those structural facts are robust.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from .regimes import TaxRegime


@dataclass(frozen=True)
class TransactionTaxes:
    """Statutory transaction charges, as fractions of traded value, per side.

    These are *taxes and levies*, separate from the market-impact and spread costs already modelled
    in ``alphacomb.portfolio.cost_terms``. They are deterministic and known in advance, which is
    exactly what makes them a clean instrument: unlike impact, they do not depend on the trade.
    """

    buy: float = 0.0                 # securities transaction tax / stamp duty on purchases
    sell: float = 0.0                # ditto on sales
    gst_on_brokerage: float = 0.0    # indirect tax applied to brokerage, not to the trade value
    brokerage: float = 0.0           # broker commission as a fraction of value
    platform_fee_annual: float = 0.0  # flat annual platform/custody fee, as a fraction of NAV
    exchange_fee: float = 0.0        # exchange turnover charge per side
    regulator_fee: float = 0.0       # e.g. SEBI turnover fee, SEC Section 31 fee
    notes: str = ""

    def cost_per_side(self, side: str) -> float:
        """Total statutory + brokerage cost of trading one unit of value on the given side."""
        statutory = (self.buy if side == "buy" else self.sell) + self.exchange_fee + self.regulator_fee
        return statutory + self.brokerage * (1.0 + self.gst_on_brokerage)

    @property
    def round_trip(self) -> float:
        """Everything: statutory charges plus brokerage."""
        return self.cost_per_side("buy") + self.cost_per_side("sell")

    @property
    def statutory_round_trip(self) -> float:
        """Transaction TAXES and levies only, excluding brokerage.

        The identification argument is about what the *state* charges for trading, not what a
        broker charges. Brokerage is a negotiated commercial rate that varies by client and is
        already partly captured by the cost model; lumping it in here would classify Singapore -
        which has no transaction tax at all - as a high-transaction-tax country purely because its
        brokers charge more. That mistake was in the first version of this module.
        """
        return self.buy + self.sell + 2 * (self.exchange_fee + self.regulator_fee)


@dataclass(frozen=True)
class LossRelief:
    """How broadly a realised capital loss can be used. The SECOND architectural dimension.

    Added 21 September 2026 after checking the model against industry practice, and it corrected a
    mistaken assumption of ours.

    We had assumed the feature that makes US tax-aware long/short work is the **holding-period
    wedge** - the 17-point gap at twelve months. The industry says otherwise. The roughly $70bn AQR
    runs in tax-aware long/short rests on the unusual breadth of US **loss relief**: capital losses
    offset capital gains without ring-fencing, plus up to $3,000 of ordinary income a year, carried
    forward indefinitely. Elsewhere relief is narrower:

    * **Germany** - losses on shares may offset gains on shares only, ring-fenced away from
      interest and dividends.
    * **Japan** - listed and unlisted share losses cannot be netted against each other.
    * **United Kingdom** - losses offset gains only, never other income.
    * **India** - short-term losses offset both short- and long-term gains, long-term losses offset
      long-term gains only. Eight-year carryforward.

    These two dimensions - the wedge and loss-relief breadth - vary **independently** across
    countries, which is better for us than one dimension would be: they identify two different
    channels. The wedge governs the *rate* applied to gains; relief breadth governs whether
    harvesting losses is worth anything at all.

    Our own framing had the wrong primary mechanism relative to practice. Recorded here rather than
    quietly corrected.
    """

    offsets_same_asset_gains: bool = True      # losses against gains in the same asset class
    offsets_other_capital_gains: bool = True   # losses against gains in OTHER asset classes
    ordinary_income_offset: float = 0.0        # annual amount deductible against ordinary income
    carryforward_years: float = float("inf")   # 0 = none, inf = indefinite
    ring_fenced: bool = False                  # relief confined to one bucket
    notes: str = ""

    @property
    def breadth(self) -> float:
        """A crude 0-1 index of how usable a realised loss is. Ordinal, not cardinal."""
        score = 0.0
        if self.offsets_same_asset_gains:
            score += 0.4
        if self.offsets_other_capital_gains:
            score += 0.3
        if self.ordinary_income_offset > 0:
            score += 0.2
        if self.carryforward_years == float("inf"):
            score += 0.1
        elif self.carryforward_years >= 5:
            score += 0.05
        return round(score, 3)


@dataclass(frozen=True)
class Jurisdiction:
    """A country's complete architecture: how gains are taxed AND how trading is taxed."""

    name: str
    code: str
    currency: str
    regime: TaxRegime
    transaction: TransactionTaxes = field(default_factory=TransactionTaxes)
    loss_relief: LossRelief = field(default_factory=LossRelief)
    annual_exempt_local: float = 0.0   # annual capital-gains exemption in local currency
    notes: str = ""

    @property
    def has_holding_period_wedge(self) -> bool:
        """Does this country reward holding past a boundary? The treatment variable."""
        return abs(self.regime.short_term_rate - self.regime.long_term_rate) > 1e-9

    @property
    def wedge(self) -> float:
        """Size of the holding-period wedge in rate points. Zero means a flat regime."""
        return self.regime.short_term_rate - self.regime.long_term_rate

    @property
    def cell(self) -> str:
        """Which cell of the identification 2x2 this country occupies."""
        hp = "wedge" if self.has_holding_period_wedge else "flat"
        tt = "high_ttax" if self.transaction.statutory_round_trip > 0.0005 else "low_ttax"
        return f"{hp}/{tt}"

    @property
    def harvesting_viable(self) -> bool:
        """Is systematic loss harvesting worth doing here at all?

        It needs a positive rate **on capital gains** to shelter against AND relief broad enough to
        use the losses. This is the industry's binding constraint, and it is what confines tax-aware
        long/short to the United States.

        Testing ``regime.taxable`` here was wrong: that is true whenever any rate is positive,
        including dividends, which marked Taiwan and China as viable when neither taxes capital
        gains on listed shares at all. Harvesting a capital loss is worthless where capital gains
        are untaxed.
        """
        taxes_gains = max(self.regime.short_term_rate, self.regime.long_term_rate) > 0
        return taxes_gains and self.loss_relief.breadth >= 0.7


# ---------------------------------------------------------------------------------------------
# The jurisdictions. All rates [verify].
# ---------------------------------------------------------------------------------------------

UNITED_STATES = Jurisdiction(
    name="United States", code="US", currency="USD",
    regime=TaxRegime(
        name="us_top_bracket", short_term_rate=0.408, long_term_rate=0.238,
        qualified_dividend_rate=0.238, ordinary_dividend_rate=0.408,
        long_term_months=12, wash_sale_rule=True, short_dividend_deductible=False,
        notes="37% top ordinary + 3.8% NIIT; 20% s1(h) + 3.8% NIIT. [verify]"),
    transaction=TransactionTaxes(
        brokerage=0.0002, regulator_fee=0.0000278,   # SEC Section 31 fee, sell side [verify]
        notes="No securities transaction tax. SEC fee is tiny and sell-side only."),
    loss_relief=LossRelief(
        offsets_same_asset_gains=True, offsets_other_capital_gains=True,
        ordinary_income_offset=3_000.0, carryforward_years=float("inf"), ring_fenced=False,
        notes="The broadest relief in this set, and the reason tax-aware long/short is a US "
              "product: losses net freely against gains, plus $3,000 of ordinary income a "
              "year, carried forward indefinitely. [verify]"),
    notes="LARGE holding-period wedge (17 points at exactly 12 months), NO transaction tax. "
          "The cell where the holding-period channel should be strongest and cleanest.",
)

INDIA = Jurisdiction(
    name="India", code="IN", currency="INR",
    regime=TaxRegime(
        name="india_resident", short_term_rate=0.20, long_term_rate=0.125,
        qualified_dividend_rate=0.30, ordinary_dividend_rate=0.30,
        long_term_months=12, wash_sale_rule=False,
        annual_ordinary_offset=0.0, loss_carryforward=True,
        notes="Post-Budget-2024 equity rates: STCG 20%, LTCG 12.5% above a Rs 1.25 lakh annual "
              "exemption, both at a 12-month boundary. Dividends taxed at slab rate for residents; "
              "30% used as the top-slab default. No wash-sale rule in Indian law. [verify]"),
    transaction=TransactionTaxes(
        buy=0.001,          # STT 0.1% on delivery purchases [verify]
        sell=0.001,         # STT 0.1% on delivery sales [verify]
        gst_on_brokerage=0.18,
        brokerage=0.0003,
        exchange_fee=0.0000297,   # NSE equity delivery transaction charge [verify]
        regulator_fee=0.000001,   # SEBI turnover fee, Rs 10 per crore [verify]
        notes="Plus stamp duty 0.015% on the buy side, folded into `buy`. DP charges are a flat "
              "per-scrip amount on sells and are not modelled. [verify]"),
    loss_relief=LossRelief(
        offsets_same_asset_gains=True, offsets_other_capital_gains=True,
        ordinary_income_offset=0.0, carryforward_years=8, ring_fenced=False,
        notes="Short-term losses offset both STCG and LTCG; long-term losses offset LTCG "
              "only. No relief against ordinary income. Eight-year carryforward. [verify]"),
    annual_exempt_local=125_000.0,
    notes="MODERATE holding-period wedge (7.5 points, 12-month boundary) AND a LARGE round-trip "
          "transaction tax. The cell that separates the two channels: if complexity hurts here "
          "much more than the wedge alone predicts, the turnover channel is doing the work.",
)

GERMANY = Jurisdiction(
    name="Germany", code="DE", currency="EUR",
    regime=TaxRegime(
        name="germany_abgeltungsteuer", short_term_rate=0.26375, long_term_rate=0.26375,
        qualified_dividend_rate=0.26375, ordinary_dividend_rate=0.26375,
        long_term_months=0, wash_sale_rule=False,
        notes="Abgeltungsteuer 25% + 5.5% solidarity surcharge = 26.375%, FLAT, with NO "
              "holding-period distinction. Church tax excluded. [verify]"),
    transaction=TransactionTaxes(brokerage=0.0005, notes="No financial transaction tax. [verify]"),
    loss_relief=LossRelief(
        offsets_same_asset_gains=True, offsets_other_capital_gains=False,
        ordinary_income_offset=0.0, carryforward_years=float("inf"), ring_fenced=True,
        notes="RING-FENCED: share losses offset share gains only, not interest or dividends. "
              "This, not the flat rate, is why US-style harvesting does not transfer. [verify]"),
    annual_exempt_local=1_000.0,   # Sparer-Pauschbetrag [verify]
    notes="PLACEBO. A flat rate means there is no holding-period boundary to cross, so the "
          "holding-period channel is switched off by law. Any complexity penalty observed here "
          "must run through turnover. If the US effect survives in Germany, our mechanism is wrong.",
)

JAPAN = Jurisdiction(
    name="Japan", code="JP", currency="JPY",
    regime=TaxRegime(
        name="japan_flat", short_term_rate=0.20315, long_term_rate=0.20315,
        qualified_dividend_rate=0.20315, ordinary_dividend_rate=0.20315,
        long_term_months=0, wash_sale_rule=False,
        notes="15% national + 0.315% reconstruction surtax + 5% local = 20.315%, FLAT. [verify]"),
    transaction=TransactionTaxes(brokerage=0.0005, notes="No transaction tax. [verify]"),
    loss_relief=LossRelief(
        offsets_same_asset_gains=True, offsets_other_capital_gains=False,
        ordinary_income_offset=0.0, carryforward_years=3, ring_fenced=True,
        notes="RING-FENCED between listed and unlisted shares; three-year carryforward. [verify]"),
    notes="Second PLACEBO, independent of Germany. Two flat-rate countries in different regions "
          "guard against the placebo result being a European artefact.",
)

UNITED_KINGDOM = Jurisdiction(
    name="United Kingdom", code="GB", currency="GBP",
    regime=TaxRegime(
        name="uk_cgt", short_term_rate=0.24, long_term_rate=0.24,
        qualified_dividend_rate=0.3935, ordinary_dividend_rate=0.3935,
        long_term_months=0, wash_sale_rule=True, wash_sale_window_days=30,
        notes="CGT is FLAT with no holding-period distinction, but the 30-day 'bed and breakfast' "
              "rule is a genuine analogue of s1091 - so the UK has a wash rule WITHOUT a "
              "holding-period wedge, which no other country here does. [verify]"),
    transaction=TransactionTaxes(
        buy=0.005,      # stamp duty reserve tax, BUY SIDE ONLY [verify]
        brokerage=0.0005,
        notes="SDRT 0.5% on purchases only - an asymmetric transaction tax, unlike India's "
              "symmetric STT. [verify]"),
    loss_relief=LossRelief(
        offsets_same_asset_gains=True, offsets_other_capital_gains=True,
        ordinary_income_offset=0.0, carryforward_years=float("inf"), ring_fenced=False,
        notes="Losses offset gains only, never other income. Indefinite carryforward. [verify]"),
    annual_exempt_local=3_000.0,   # [verify]
    notes="A third architecture: flat CGT + a wash-sale rule + a BUY-SIDE-ONLY transaction tax. "
          "Isolates the wash-sale rule from the holding-period wedge, which the US confounds.",
)

SINGAPORE = Jurisdiction(
    name="Singapore", code="SG", currency="SGD",
    regime=TaxRegime(
        name="singapore_no_cgt", short_term_rate=0.0, long_term_rate=0.0,
        qualified_dividend_rate=0.0, ordinary_dividend_rate=0.0,
        long_term_months=0, wash_sale_rule=False,
        notes="No capital gains tax for investors; no dividend tax for residents. Trading income "
              "can be taxed if the taxpayer is held to be trading rather than investing. [verify]"),
    transaction=TransactionTaxes(
        brokerage=0.0008, exchange_fee=0.0000325,
        notes="Clearing and SGX access fees; no transaction tax. [verify]"),
    notes="DOUBLE PLACEBO: no capital-gains tax at all. Net-of-cost performance IS after-tax "
          "performance here, so this row reproduces exactly what the existing literature reports "
          "and anchors the whole cross-country comparison.",
)

TAIWAN = Jurisdiction(
    name="Taiwan", code="TW", currency="TWD",
    regime=TaxRegime(
        name="taiwan_no_cgt_securities", short_term_rate=0.0, long_term_rate=0.0,
        qualified_dividend_rate=0.21, ordinary_dividend_rate=0.21,
        long_term_months=0, wash_sale_rule=False,
        notes="Securities transaction income tax on listed shares is suspended for individuals; "
              "the transaction tax does the work instead. [verify]"),
    transaction=TransactionTaxes(
        sell=0.003,     # securities transaction tax 0.3%, SELL SIDE [verify]
        brokerage=0.001425,
        notes="0.3% on sales is among the highest equity transaction taxes in the world. [verify]"),
    notes="The extreme of the turnover channel with the holding-period channel switched off "
          "entirely. If complexity is penalised anywhere, it is penalised here - and purely "
          "through turnover.",
)

HONG_KONG = Jurisdiction(
    name="Hong Kong", code="HK", currency="HKD",
    regime=TaxRegime(
        name="hong_kong_no_cgt", short_term_rate=0.0, long_term_rate=0.0,
        qualified_dividend_rate=0.0, ordinary_dividend_rate=0.0,
        long_term_months=0, wash_sale_rule=False,
        notes="No capital gains tax, no dividend withholding for residents. [verify]"),
    transaction=TransactionTaxes(
        buy=0.001, sell=0.001,   # stamp duty both sides [verify]
        brokerage=0.0008, regulator_fee=0.000027,
        notes="Stamp duty on both sides plus SFC transaction levy and FRC levy. [verify]"),
    notes="No CGT, symmetric transaction tax. Pairs with Taiwan (sell-side only) to test whether "
          "the *symmetry* of a transaction tax matters as well as its level.",
)

CHINA_A = Jurisdiction(
    name="China (A-shares)", code="CN", currency="CNY",
    regime=TaxRegime(
        name="china_a_individual", short_term_rate=0.0, long_term_rate=0.0,
        qualified_dividend_rate=0.10, ordinary_dividend_rate=0.20,
        long_term_months=12, wash_sale_rule=False,
        notes="Individuals are exempt from capital gains tax on listed A-shares. Dividend tax is "
              "itself holding-period dependent: broadly exempt above one year, 10% for one month "
              "to one year, 20% under one month - a holding-period wedge on DIVIDENDS rather than "
              "on gains, which exists nowhere else in this set. [verify]"),
    transaction=TransactionTaxes(
        sell=0.0005,    # stamp duty, sell side [verify]
        brokerage=0.0003, exchange_fee=0.0000487,
        notes="Stamp duty 0.05% on sales; transfer fee on the Shanghai exchange. [verify]"),
    notes="A genuinely unusual architecture: zero CGT but a holding-period wedge on dividend "
          "income. Tests whether the mechanism is about capital-gains character specifically or "
          "about holding-period-dependent taxation in general.",
)

JURISDICTIONS: dict[str, Jurisdiction] = {
    j.code: j for j in (UNITED_STATES, INDIA, GERMANY, JAPAN, UNITED_KINGDOM,
                        SINGAPORE, TAIWAN, HONG_KONG, CHINA_A)
}


def get_jurisdiction(code: str | Jurisdiction) -> Jurisdiction:
    if isinstance(code, Jurisdiction):
        return code
    key = str(code).upper()
    aliases = {"USA": "US", "IND": "IN", "GER": "DE", "DEU": "DE", "JPN": "JP", "UK": "GB",
               "SGP": "SG", "TWN": "TW", "HKG": "HK", "CHN": "CN"}
    key = aliases.get(key, key)
    if key not in JURISDICTIONS:
        raise KeyError(f"unknown jurisdiction '{code}'; known: {sorted(JURISDICTIONS)}")
    return JURISDICTIONS[key]


def identification_table() -> "object":
    """The 2x2 that makes this an identification strategy rather than a robustness table."""
    import pandas as pd

    rows = []
    for j in JURISDICTIONS.values():
        rows.append({
            "code": j.code, "country": j.name,
            "short_term_rate": j.regime.short_term_rate,
            "long_term_rate": j.regime.long_term_rate,
            "wedge_points": round(100 * j.wedge, 2),
            "boundary_months": j.regime.long_term_months,
            "wash_rule": j.regime.wash_sale_rule,
            "loss_breadth": j.loss_relief.breadth,
            "ring_fenced": j.loss_relief.ring_fenced,
            "harvesting_viable": j.harvesting_viable,
            "ttax_buy_bps": round(1e4 * j.transaction.buy, 1),
            "ttax_sell_bps": round(1e4 * j.transaction.sell, 1),
            "statutory_rt_bps": round(1e4 * j.transaction.statutory_round_trip, 2),
            "all_in_rt_bps": round(1e4 * j.transaction.round_trip, 1),
            "cell": j.cell,
        })
    return pd.DataFrame(rows).sort_values(["cell", "code"]).reset_index(drop=True)
