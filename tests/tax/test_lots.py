"""Tax-lot rules. Each test pins one statutory rule, so a regression names the rule it broke."""
from __future__ import annotations

import pandas as pd
import pytest

from alphacomb.tax import LotMethod, TaxLotLedger, get_regime


@pytest.fixture
def taxable():
    return get_regime("taxable_us_top_bracket")


def test_partial_sale_realises_proportional_basis(taxable):
    led = TaxLotLedger(taxable)
    led.buy(1, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: 0.10}))          # value 110, basis 100
    gains = led.sell(1, "2020-02-29", 55.0)
    assert len(gains) == 1
    assert gains[0].amount == pytest.approx(5.0)       # half the lot, half the gain
    assert led.position(1) == pytest.approx(55.0)


def test_holding_period_boundary_is_strictly_more_than_twelve_months(taxable):
    """s1222: 'more than one year'. Twelve months exactly is short-term."""
    short = TaxLotLedger(taxable)
    short.buy(1, "2020-01-31", 100.0)
    assert short.sell(1, "2021-01-31", 100.0)[0].long_term is False

    long = TaxLotLedger(taxable)
    long.buy(1, "2020-01-31", 100.0)
    assert long.sell(1, "2021-03-31", 100.0)[0].long_term is True


def test_closing_a_short_is_always_short_term(taxable):
    """s1233, regardless of how long the short was open."""
    led = TaxLotLedger(taxable)
    led.short(1, "2018-01-31", 100.0)
    led.accrue_returns(pd.Series({1: -0.10}))
    gain = led.sell(1, "2023-06-30", 90.0, side=-1)[0]
    assert gain.amount == pytest.approx(10.0)          # price fell, the short profits
    assert gain.long_term is False


def test_wash_sale_forward_disallows_the_loss_and_lifts_the_new_basis(taxable):
    """s1091 looking forward: repurchase within 30 days after the loss sale."""
    led = TaxLotLedger(taxable)
    led.buy(1, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: -0.20}))
    loss = led.sell(1, "2020-02-29", 80.0)[0]
    lot = led.buy(1, "2020-03-05", 80.0)
    assert loss.amount == pytest.approx(-20.0)
    assert loss.disallowed == pytest.approx(20.0)
    assert loss.allowed == pytest.approx(0.0)
    assert lot.basis == pytest.approx(100.0)           # 80 paid + 20 disallowed loss
    assert lot.washed_from is not None                 # s1223(3) tacking


def test_wash_sale_backward_also_bites(taxable):
    """s1091 looking back: a purchase in the 30 days *before* the loss sale."""
    led = TaxLotLedger(taxable)
    led.buy(1, "2020-01-01", 100.0)
    led.buy(1, "2020-02-20", 50.0)                     # replacement bought first
    led.accrue_returns(pd.Series({1: -0.20}))
    gains = led.sell(1, "2020-02-29", 80.0, side=1)
    assert sum(g.disallowed for g in gains) > 0


def test_wash_sale_outside_the_window_is_allowed(taxable):
    led = TaxLotLedger(taxable)
    led.buy(1, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: -0.20}))
    loss = led.sell(1, "2020-02-29", 80.0)[0]
    led.expire_wash_window("2020-06-30")
    led.buy(1, "2020-06-30", 80.0)
    assert loss.disallowed == pytest.approx(0.0)
    assert loss.allowed == pytest.approx(-20.0)


def test_mark_to_market_election_switches_the_wash_rule_off():
    led = TaxLotLedger(get_regime("trader_475f_mtm"))
    led.buy(1, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: -0.20}))
    loss = led.sell(1, "2020-02-29", 80.0)[0]
    led.buy(1, "2020-03-05", 80.0)
    assert loss.disallowed == pytest.approx(0.0)       # s475(f) turns s1091 off
    assert loss.long_term is False


def test_mark_to_market_realises_unrealised_gains():
    led = TaxLotLedger(get_regime("trader_475f_mtm"))
    led.buy(1, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: 0.25}))
    assert led.mark_to_market("2020-12-31") == pytest.approx(25.0)
    assert led.unrealised_total() == pytest.approx(0.0)  # basis reset to market


def test_hifo_realises_less_gain_than_fifo(taxable):
    def run(method):
        led = TaxLotLedger(taxable, method)
        led.buy(1, "2020-01-31", 100.0)
        led.accrue_returns(pd.Series({1: 1.0}))        # first lot doubles: basis 100, value 200
        led.buy(1, "2020-02-29", 200.0)                # second lot at the higher price
        return sum(g.amount for g in led.sell(1, "2020-03-31", 200.0))

    assert run(LotMethod.HIFO) < run(LotMethod.FIFO)
    assert run(LotMethod.HIFO) == pytest.approx(0.0)   # sells the at-cost lot, no gain


def test_tax_optimal_takes_losses_first(taxable):
    led = TaxLotLedger(taxable, LotMethod.TAX_OPTIMAL)
    led.buy(1, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: 0.50}))           # winner: basis 100, value 150
    led.buy(1, "2020-02-29", 100.0)
    led.accrue_returns(pd.Series({1: -0.40}))          # both fall; lot 2 is now a loser
    gains = led.sell(1, "2020-03-31", 60.0)
    assert gains[0].amount < 0                          # the loss is realised first


def test_crossing_zero_closes_then_reopens(taxable):
    led = TaxLotLedger(taxable)
    led.buy(1, "2020-01-31", 100.0)
    gains = led.trade_to(1, "2020-02-29", -50.0)
    assert len(gains) == 1                              # the long was fully closed
    assert led.position(1) == pytest.approx(-50.0)


def test_embedded_gain_rate_reports_what_selling_would_cost(taxable):
    led = TaxLotLedger(taxable)
    led.buy(1, "2020-01-31", 100.0)
    led.accrue_returns(pd.Series({1: 0.25}))
    g, rate = led.embedded_gain_rate(1, "2020-02-29")
    assert g == pytest.approx(25.0 / 125.0)
    assert rate == pytest.approx(taxable.short_term_rate)
    assert led.embedded_gain_rate(999, "2020-02-29") == (0.0, 0.0)
