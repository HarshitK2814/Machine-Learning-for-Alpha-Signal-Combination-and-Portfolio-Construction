"""After-tax backtest: the controls that have to hold before any after-tax number is believable."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.tax import LotMethod, TaxConfig, after_tax_backtest, get_regime, summarise_after_tax


def simple_weights(bundle, n_per_side: int = 15) -> pd.DataFrame:
    """A crude dollar-neutral signal portfolio, used only to exercise the tax accounting."""
    col = next(c for c in bundle.signals.columns if c.startswith("sig_"))
    sig = bundle.signals[["date", "permno", col]].dropna()
    rows = []
    for date, group in sig.groupby("date"):
        if len(group) < 2 * n_per_side:
            continue
        ranked = group.sort_values(col)
        short = ranked.head(n_per_side)["permno"].to_numpy()
        long = ranked.tail(n_per_side)["permno"].to_numpy()
        w = 0.5 / n_per_side
        rows.append(pd.DataFrame({"date": date, "permno": np.concatenate([long, short]),
                                  "w": np.concatenate([np.full(n_per_side, w),
                                                       np.full(n_per_side, -w)])}))
    out = pd.concat(rows, ignore_index=True)
    out["permno"] = out["permno"].astype("int32")
    return out


@pytest.fixture(scope="module")
def weights(small_panel):
    return simple_weights(small_panel)


@pytest.fixture(scope="module")
def cfg():
    """Base config with the AUM scaled to the test panel.

    The 120-stock fixture cannot absorb a billion dollars: 15 names a side means 3.3% positions,
    and the square-root impact term then charges more than the strategy earns. $10m is the right
    order for a panel this size and keeps the test about tax rather than about market impact.
    """
    from alphacomb.contracts import load_config
    base = load_config("base")
    base = {**base, "costs": {**base["costs"], "aum_usd_2020": 1.0e7}}
    return base


def test_tax_exempt_after_tax_equals_net(small_panel, weights, cfg):
    """The control: with no tax, the after-tax series must be the net-of-cost series exactly."""
    frame = after_tax_backtest(weights, small_panel, cfg, TaxConfig(regime=get_regime("tax_exempt")))
    assert np.allclose(frame["after_tax_ret"], frame["net_ret"])
    assert frame["tax_ret"].abs().max() == 0.0


def test_costs_never_add_and_tax_follows_the_sign_of_realised_gains(small_panel, weights, cfg):
    """Costs are always a drag. Tax is a drag only when there are net gains to tax.

    A strategy that realises net losses generates a tax *benefit* (s1211(b) and the carryforward),
    so asserting that tax always reduces the return would be asserting something false.
    """
    frame = after_tax_backtest(weights, small_panel, cfg, TaxConfig(regime=get_regime("taxable")))
    assert (frame["net_ret"] <= frame["gross_ret"] + 1e-12).all()
    summary = summarise_after_tax(frame)
    realised = summary["realised_st_ann"] + summary["realised_lt_ann"]
    if realised > 0:
        assert summary["tax_drag_ann_bps"] > 0
        assert summary["after_tax_mean_ann"] < summary["net_mean_ann"]


def test_taxable_investor_keeps_less_than_a_tax_exempt_one(small_panel, weights, cfg):
    exempt = summarise_after_tax(after_tax_backtest(weights, small_panel, cfg,
                                                    TaxConfig(regime=get_regime("tax_exempt"))))
    taxed = summarise_after_tax(after_tax_backtest(weights, small_panel, cfg,
                                                   TaxConfig(regime=get_regime("taxable"))))
    assert taxed["after_tax_mean_ann"] < exempt["after_tax_mean_ann"]
    # Not exactly equal: tax is paid out of capital, so the taxable investor's NAV path - and
    # therefore the weights it drifts from next month - differ slightly. The coupling is real and
    # we keep it rather than reporting a return the investor did not experience.
    assert taxed["net_mean_ann"] == pytest.approx(exempt["net_mean_ann"], rel=0.02)


def test_lot_method_changes_the_tax_bill_but_not_the_pre_tax_return(small_panel, weights, cfg):
    """Lot selection is an accounting choice: it must not move pre-tax P&L."""
    hifo = after_tax_backtest(weights, small_panel, cfg,
                              TaxConfig(regime=get_regime("taxable"), lot_method=LotMethod.HIFO))
    fifo = after_tax_backtest(weights, small_panel, cfg,
                              TaxConfig(regime=get_regime("taxable"), lot_method=LotMethod.FIFO))
    assert np.allclose(hifo["gross_ret"], fifo["gross_ret"], atol=1e-10)
    assert summarise_after_tax(hifo)["tax_drag_ann_bps"] != summarise_after_tax(fifo)["tax_drag_ann_bps"]


def test_mark_to_market_regime_reports_no_wash_sales(small_panel, weights, cfg):
    frame = after_tax_backtest(weights, small_panel, cfg, TaxConfig(regime=get_regime("475f")))
    assert frame["wash_disallowed"].abs().max() == pytest.approx(0.0)
    assert summarise_after_tax(frame)["lt_share_of_gains"] != summarise_after_tax(frame)["lt_share_of_gains"] \
        or summarise_after_tax(frame)["realised_lt_ann"] == pytest.approx(0.0)


def test_wash_sale_rule_disallows_some_losses(small_panel, weights, cfg):
    """A monthly-rebalanced book re-buys names constantly, so s1091 must bite somewhere."""
    frame = after_tax_backtest(weights, small_panel, cfg, TaxConfig(regime=get_regime("taxable")))
    assert frame["wash_disallowed"].sum() > 0


def test_accounting_basis_changes_timing_not_the_total(small_panel, weights, cfg):
    accrual = after_tax_backtest(weights, small_panel, cfg,
                                 TaxConfig(regime=get_regime("taxable"), accounting="accrual"))
    year_end = after_tax_backtest(weights, small_panel, cfg,
                                  TaxConfig(regime=get_regime("taxable"), accounting="year_end"))
    assert accrual["tax_dollars"].sum() == pytest.approx(year_end["tax_dollars"].sum(), rel=0.05)
    assert accrual["tax_ret"].std() < year_end["tax_ret"].std()   # accrual is smoother


def test_deferred_tax_is_reported_and_reduces_the_liquidation_figure(small_panel, weights, cfg):
    frame = after_tax_backtest(weights, small_panel, cfg, TaxConfig(regime=get_regime("taxable")))
    summary = summarise_after_tax(frame)
    assert "deferred_tax_ret" in summary
    assert summary["after_tax_liq_mean_ann"] <= summary["after_tax_mean_ann"] + 1e-12


def test_nav_reconciles_with_the_reported_returns(small_panel, weights, cfg):
    """NAV is the ledger of record; the reported after-tax return must rebuild it."""
    frame = after_tax_backtest(weights, small_panel, cfg, TaxConfig(regime=get_regime("taxable")))
    rebuilt = 1e9 * (1 + frame["after_tax_ret"]).cumprod()
    assert np.allclose(rebuilt.to_numpy(), frame["nav"].to_numpy(), rtol=1e-8)


def test_extended_table_still_satisfies_contract_c12(small_panel, weights, cfg):
    """The tax columns are additive: Maham's statistics code must keep working unchanged."""
    from alphacomb.contracts.schemas import validate
    frame = after_tax_backtest(weights, small_panel, cfg, TaxConfig(regime=get_regime("taxable")))
    validate(frame, "returns")
