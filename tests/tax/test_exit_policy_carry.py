"""exit_policy='carry_v1': the 2026-10-13 exit-policy ruling, on synthetic fixtures only.

No historical panel is read. Each test names the ruling clause it checks.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.tax import TaxConfig, get_regime, summarise_after_tax
from alphacomb.tax.backtest import after_tax_backtest
from exit_fixtures import DATES, build_bundle, build_weights, evidence, run, build_cfg

CARRY = dict(exit_policy="carry_v1")


def _late(ledger, permno, first_idx):
    return [g for g in ledger.realised if g.permno == permno and g.date >= DATES[first_idx]]


# ---- ruling 1: alive but uncertified ------------------------------------------------------------
def test_frozen_name_is_carried_not_sold_and_pays_no_cost():
    b, w = build_bundle(frozen=(1, 3)), build_weights({1: 3})
    f, ledger = run(b, w, **CARRY)
    assert ledger.position(1) > 2e6                       # quantity and lots preserved
    assert _late(ledger, 1, 3) == []                      # nothing realised on it
    assert (f["valuation_status"] == "resolved").all()    # valuation exists, so the month is resolved
    assert f.loc[3:, "n_frozen"].eq(1).all() and f.loc[:2, "n_frozen"].eq(0).all()
    base, _ = run(build_bundle(), build_weights(), **CARRY)
    assert f.loc[3, "turnover"] < base.loc[3, "turnover"]
    assert f.loc[3, "gross_ret"] == pytest.approx(0.015, rel=0.01)  # it keeps earning (weights drift)


def test_frozen_name_ignores_a_conflicting_weights_file_weight():
    """The ledger's drifted holding is authoritative, not the optimiser's weight."""
    f_in, l_in = run(build_bundle(frozen=(1, 3)), build_weights(), **CARRY)
    f_out, l_out = run(build_bundle(frozen=(1, 3)), build_weights({1: 3}), **CARRY)
    assert _late(l_in, 1, 3) == [] and _late(l_out, 1, 3) == []
    assert l_in.position(1) == pytest.approx(l_out.position(1), rel=1e-9)
    assert f_in.loc[3:, "n_blocked_trades"].eq(0).all()


def test_no_new_position_is_opened_in_an_uncertified_name():
    b = build_bundle(frozen=(5, 0))                       # name 5 never certified
    w = build_weights()
    extra = pd.DataFrame(dict(date=DATES, permno=np.int32(5), w=0.1))
    f, ledger = run(b, pd.concat([w, extra], ignore_index=True), **CARRY)
    assert ledger.position(5) == 0.0
    assert f["n_blocked_trades"].eq(1).all()


def test_recertified_name_is_traded_again_with_a_normal_cost():
    b, w = build_bundle(frozen=(1, 3, 5)), build_weights({1: 3})
    f, ledger = run(b, w, **CARRY)
    assert ledger.position(1) == 0.0                      # sold once inputs returned
    assert len(_late(ledger, 1, 3)) == len(_late(ledger, 1, 5)) > 0
    assert f.loc[5, "realised_st"] > 0.01
    assert f.loc[5, "cost_spread"] > f.loc[4, "cost_spread"]    # the sale is now charged
    assert f.loc[4, "n_frozen"] == 1 and f.loc[5, "n_frozen"] == 0


# ---- ruling 2: temporarily unpriced -------------------------------------------------------------
def test_unpriced_holding_is_flagged_stale_with_no_imputed_return_and_a_null_month():
    b, w = build_bundle(unpriced=(1, 3)), build_weights()
    f, ledger = run(b, w, **CARRY)
    assert (f.loc[:2, "valuation_status"] == "resolved").all()
    assert (f.loc[3:, "valuation_status"] == "unresolved").all()    # stays unresolved: gap return unknown
    assert f.loc[3:, ["gross_ret", "net_ret", "after_tax_ret", "nav"]].isna().all().all()
    assert f.loc[:2, ["gross_ret", "nav"]].notna().all().all()
    assert len(f) == 8                                              # months retained in the index
    assert f.loc[3, "n_stale"] == 1 and f.loc[3, "stale_gross"] > 0.2
    # resolved-only diagnostic excludes the stale name rather than giving it a 0% "return"
    assert f.loc[3, "gross_ret_diag"] == pytest.approx(0.010)
    assert f["nav_diag"].notna().all()
    # quantity and lots untouched, value frozen at its last mark
    cut = build_weights()
    cut = cut[cut["date"] <= DATES[3]]
    _, ledger_cut = run(build_bundle(unpriced=(1, 3)), cut, **CARRY)
    assert ledger.position(1) == pytest.approx(ledger_cut.position(1), rel=1e-12)
    # month 3's trade happened at a priced date; from month 4 the stale name is never traded
    assert _late(ledger, 1, 4) == []
    assert f.attrs["stale_permnos"] == [1]


# ---- ruling 3 + 4: panel leavers, terminal events, unresolved -----------------------------------
def test_confirmed_delisting_is_closed_exactly_once_and_cost_is_unsupported_not_zero():
    b, w = build_bundle(gone=(2, 3)), build_weights({2: 3})
    f, ledger = run(b, w, exit_evidence=evidence(2, 3), **CARRY)
    assert ledger.position(2) == 0.0 and ledger.lots.get(2, []) == []
    closes = _late(ledger, 2, 3)
    assert len(closes) == 1 and closes[0].date == DATES[3] and abs(closes[0].amount) > 1e5
    assert f["n_exit_closed"].tolist() == [0, 0, 0, 1, 0, 0, 0, 0]
    assert f.loc[3, "cost_status"] == "unsupported" and np.isnan(f.loc[3, "net_ret"])
    assert f.loc[3, "gross_ret"] == pytest.approx(0.010) and f.loc[3, "valuation_status"] == "resolved"
    assert f.loc[4:, "cost_status"].eq("supported").all() and f.loc[4:, "net_ret"].notna().all()
    assert f.loc[3, "cost_exit"] == 0.0                   # not charged, and not claimed as zero:
    assert f.attrs["exit_log"][0]["liquidation_cost"] == "unsupported"
    assert f.loc[3:, "nav"].isna().all() and f["nav_diag"].notna().all()


def test_evidenced_liquidation_cost_is_charged_and_the_month_is_supported():
    b, w = build_bundle(gone=(2, 3)), build_weights({2: 3})
    f, _ = run(b, w, exit_evidence=evidence(2, 3, cost_frac=0.01), **CARRY)
    assert f.loc[3, "cost_status"] == "supported" and f.loc[3, "cost_exit"] > 0.002
    assert f.loc[3, "net_ret"] == pytest.approx(f.loc[3, "net_ret_diag"])
    assert f["nav"].notna().all()


def test_a_terminal_event_is_never_processed_twice_when_the_name_reappears():
    b, w = build_bundle(gone=(2, 3), reappear=6), build_weights({2: 3})
    f, ledger = run(b, w, exit_evidence=evidence(2, 3), **CARRY)
    assert len(_late(ledger, 2, 3)) == 1
    assert f["n_exit_closed"].sum() == 1


def test_disappearance_without_documented_evidence_is_unresolved_and_not_closed():
    b, w = build_bundle(gone=(2, 3)), build_weights({2: 3})
    f, ledger = run(b, w, **CARRY)                        # no exit_evidence at all
    assert ledger.position(2) > 2e6 and _late(ledger, 2, 3) == []
    assert (f.loc[3:, "valuation_status"] == "unresolved").all()
    assert f.loc[3:, "n_exit_unresolved"].eq(1).all()
    assert f.attrs["unresolved_exit_permnos"] == [2]
    cut = build_weights({2: 3})
    cut = cut[cut["date"] <= DATES[3]]
    _, l_cut = run(build_bundle(gone=(2, 3)), cut, **CARRY)
    assert ledger.position(2) == pytest.approx(l_cut.position(2), rel=1e-12)     # no stale valuation drift


def test_evidence_for_another_name_or_an_undocumented_kind_does_not_confirm():
    b, w = build_bundle(gone=(2, 3)), build_weights({2: 3})
    f, ledger = run(b, w, exit_evidence=evidence(5, 3), **CARRY)
    assert ledger.position(2) > 2e6 and f.loc[3, "n_exit_unresolved"] == 1
    with pytest.raises(ValueError, match="not documented terminal events"):
        TaxConfig(regime=get_regime("taxable"), exit_evidence=evidence(2, 3, kind="left_universe"), **CARRY)


def test_a_reappearing_unresolved_leaver_is_not_closed_at_a_stale_value():
    b, w = build_bundle(gone=(2, 3), reappear=6), build_weights({2: 3})
    f, ledger = run(b, w, **CARRY)
    assert _late(ledger, 2, 3) == []                      # as_run realised it late at a stale value
    assert f.loc[6:, "valuation_status"].eq("unresolved").all()


# ---- reporting ----------------------------------------------------------------------------------
def test_summary_is_labelled_a_diagnostic_when_any_month_is_unresolved():
    f, _ = run(build_bundle(unpriced=(1, 3)), build_weights(), **CARRY)
    out = summarise_after_tax(f)
    assert out["basis"] == "RESOLVED_ONLY_DIAGNOSTIC_NOT_FULL_PORTFOLIO_PERFORMANCE"
    assert out["n_unresolved_months"] == 5 and np.isfinite(out["net_sharpe"])


def test_summary_is_full_portfolio_when_every_month_resolves():
    f, _ = run(build_bundle(frozen=(1, 3)), build_weights({1: 3}), **CARRY)
    assert summarise_after_tax(f)["basis"] == "FULL_PORTFOLIO_ALL_MONTHS_RESOLVED"


# ---- shorts: accounting, not implementability ---------------------------------------------------
def test_carried_short_keeps_accruing_borrow_and_short_dividends():
    b = build_bundle(frozen=(3, 3))
    b.targets.loc[b.targets["permno"] == 3, "div_next"] = 0.01
    w = build_weights({3: 3})
    f, ledger = run(b, w, **CARRY)
    assert ledger.position(3) < -2e6                      # the short is carried, not covered
    base, _ = run(build_bundle(), build_weights(), **CARRY)
    assert f.loc[4, "cost_borrow"] == pytest.approx(base.loc[4, "cost_borrow"], rel=0.05)    # the carried short drifts, so not equal
    assert f.loc[4, "div_paid"] > 0.0
    assert "not evidence that a short was available" in f.attrs["short_availability_evidence"]
    as_run, _ = run(b, w)
    assert as_run.loc[4, "cost_borrow"] < f.loc[4, "cost_borrow"] * 0.9    # as_run covered it, free


# ---- accounting identities ----------------------------------------------------------------------
@pytest.mark.parametrize("kw", [
    dict(bundle=dict(), w={}),
    dict(bundle=dict(frozen=(1, 3)), w={1: 3}),
    dict(bundle=dict(unpriced=(1, 3)), w={}),
    dict(bundle=dict(gone=(2, 3)), w={2: 3}),
])
def test_nav_chain_matches_the_diagnostic_after_tax_returns(kw):
    f, _ = run(build_bundle(**kw["bundle"]), build_weights(kw["w"]), **CARRY)
    growth = f["nav_diag"].to_numpy()[1:] / f["nav_diag"].to_numpy()[:-1]
    assert np.allclose(growth, 1.0 + f["after_tax_ret_diag"].to_numpy()[1:], atol=1e-10)
    assert (f["net_ret_diag"] <= f["gross_ret_diag"] + 1e-12).all()


# ---- integration + guards -----------------------------------------------------------------------
def test_all_cases_together_are_deterministic():
    b = build_bundle(frozen=(1, 3), gone=(2, 3), unpriced=(3, 4))
    w = build_weights({1: 3, 2: 3})
    f1, l1 = run(b, w, exit_evidence=evidence(2, 3), **CARRY)
    f2, _ = run(b, w, exit_evidence=evidence(2, 3), **CARRY)
    pd.testing.assert_frame_equal(f1, f2)
    assert f1.loc[3, "n_frozen"] == 1 and f1.loc[3, "n_exit_closed"] == 1
    assert f1.loc[4:, "valuation_status"].eq("unresolved").all()
    assert l1.position(2) == 0.0 and _late(l1, 1, 3) == []


def test_carry_v1_refuses_a_synthetic_bundle_and_unknown_policies():
    b = build_bundle()
    b.source = "synthetic_seed_1"
    with pytest.raises(ValueError, match="real-panel"):
        after_tax_backtest(build_weights(), b, build_cfg(), TaxConfig(regime=get_regime("taxable"), **CARRY))
    with pytest.raises(ValueError, match="exit_policy"):
        TaxConfig(regime=get_regime("taxable"), exit_policy="carry_v2")


# ---- confirmed exit with a -100% terminal return ------------------------------------------------
def _total_loss(**kw):
    """Name 2 returns -100% in month 2 (its last priced month), then leaves with documented evidence."""
    return build_bundle(gone=(2, 3), ret_override={(2, 2): -1.0}, **kw), build_weights({2: 3})


def test_total_loss_exit_is_realised_once_at_the_documented_exit_date():
    b, w = _total_loss()
    cut = w[w["date"] <= DATES[2]]
    _, l_cut = run(build_bundle(gone=(2, 3), ret_override={(2, 2): -1.0}), cut, **CARRY)
    basis = sum(lot.basis for lot in l_cut.lots[2])             # still on the books at end of month 2
    assert basis > 2e6
    f, ledger = run(b, w, exit_evidence=evidence(2, 3), **CARRY)
    assert ledger.position(2) == 0.0 and ledger.lots.get(2, []) == []
    closes = [g for g in ledger.realised if g.permno == 2 and g.date >= DATES[3]]
    assert len(closes) == 1 and closes[0].date == DATES[3]
    assert closes[0].amount == pytest.approx(-basis, rel=1e-6)    # the whole basis is lost, once
    assert f.loc[3, "realised_st"] < -0.2 and f["n_exit_closed"].sum() == 1


def test_total_loss_exit_cannot_be_realised_twice_even_if_the_name_reappears():
    b = build_bundle(gone=(2, 3), reappear=6, ret_override={(2, 2): -1.0})
    f, ledger = run(b, build_weights({2: 3}), exit_evidence=evidence(2, 3), **CARRY)
    assert len([g for g in ledger.realised if g.permno == 2 and g.date >= DATES[3]]) == 1
    f2, _ = run(b, build_weights({2: 3}), exit_evidence=evidence(2, 3), **CARRY)
    pd.testing.assert_frame_equal(f, f2)


def test_total_loss_without_evidence_keeps_the_lot_unresolved_not_silently_dropped():
    b, w = _total_loss()
    f, ledger = run(b, w, **CARRY)
    assert len(ledger.lots.get(2, [])) == 1                      # the lot survives to be reported
    assert f.loc[3:, "n_exit_unresolved"].eq(1).all()
