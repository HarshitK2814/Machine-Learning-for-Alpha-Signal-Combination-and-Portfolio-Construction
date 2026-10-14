"""Review-driven checks for exit_policy='carry_v1' (dividends, borrow, tax lots, isolation).

Synthetic fixtures only. Each test says whether it pins a defect that was found and fixed
('defect') or a deliberate conservative policy choice ('policy').
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import exit_fixtures as fx
from alphacomb.contracts import paths
from exit_fixtures import DATES, build_bundle, build_weights, evidence, run

CARRY = dict(exit_policy="carry_v1")


# ---- defect: a name that was stale before leaving must not be closed at its last mark ------------
def test_defect_stale_name_that_then_leaves_is_unresolved_even_with_evidence():
    # name 2's terminal return (ret_next at month 2) is missing, then the name leaves with evidence
    b, w = build_bundle(unpriced=(2, 2), gone=(2, 3)), build_weights({2: 3})
    f, ledger = run(b, w, exit_evidence=evidence(2, 3), **CARRY)
    assert ledger.position(2) > 2e6
    assert f["n_exit_closed"].sum() == 0
    assert any("stale before the name left" in e.get("reason", "") for e in f.attrs["exit_log"])
    assert (f.loc[2:, "valuation_status"] == "unresolved").all()


# ---- policy: one leaver makes every later month unresolved ---------------------------------------
def test_policy_one_unevidenced_leaver_makes_all_later_months_unresolved_with_a_materiality_trail():
    f, _ = run(build_bundle(gone=(2, 3)), build_weights({2: 3}), **CARRY)
    assert (f.loc[:2, "valuation_status"] == "resolved").all()
    assert (f.loc[3:, "valuation_status"] == "unresolved").all()
    assert f.loc[3:, "nav"].isna().all() and f.loc[:2, "nav"].notna().all()
    # the share at stake is reported every month, so a materiality rule can be applied later
    assert (f.loc[3:, "unresolved_exit_gross"] > 0.2).all()


# ---- defect: borrow on stale/unresolved shorts is not part of the resolved-only diagnostic -------
def test_defect_borrow_is_not_accrued_on_a_stale_short_and_the_gap_is_reported():
    base, _ = run(build_bundle(), build_weights(), **CARRY)
    f, _ = run(build_bundle(unpriced=(3, 3)), build_weights(), **CARRY)
    assert f.loc[4, "cost_borrow"] < 0.65 * base.loc[4, "cost_borrow"]
    assert f.loc[4, "unresolved_short_gross"] > 0.2


def test_policy_unresolved_exit_short_accrues_no_borrow_and_is_reported():
    f, ledger = run(build_bundle(gone=(3, 3)), build_weights({3: 3}), **CARRY)
    assert ledger.position(3) < 0
    assert f.loc[4, "unresolved_short_gross"] > 0.2
    assert "not evidence that a short was available" in f.attrs["short_availability_evidence"]


# ---- defect: s475(f) must not book tax on a stale mark ------------------------------------------
def test_defect_mark_to_market_skips_stale_and_unresolved_lots(monkeypatch):
    monkeypatch.setattr(fx, "DATES", pd.date_range("2020-01-31", periods=12, freq="ME"))
    f, ledger = run(build_bundle(unpriced=(1, 3), gone=(2, 4)), build_weights({2: 4}),
                    regime="475f", **CARRY)
    for permno in (1, 2):      # stale and unresolved: basis was not reset to the stale value
        lots = ledger.lots[permno]
        assert sum(l.basis for l in lots) < 0.99 * sum(l.value for l in lots)
    live = ledger.lots[4]      # an ordinary short was marked on 31 December
    assert sum(l.basis for l in live) == pytest.approx(sum(l.value for l in live), rel=1e-9)


# ---- dividends: missing is missing information, not a known zero --------------------------------
def _with_missing_div(month_idx, permno=1, value=np.nan):
    b = build_bundle()
    b.targets.loc[(b.targets["permno"] == permno) & (b.targets["date"] == DATES[month_idx]), "div_next"] = value
    return b


def test_defect_missing_dividend_on_a_held_name_makes_after_tax_unsupported_not_zero():
    f, _ = run(_with_missing_div(3), build_weights(), **CARRY)
    assert f.loc[3, "tax_status"] == "unsupported" and f.loc[3, "n_div_missing"] == 1
    assert np.isnan(f.loc[3, "after_tax_ret"]) and np.isfinite(f.loc[3, "net_ret"])  # gross/net unaffected
    assert np.isfinite(f.loc[3, "after_tax_ret_diag"])
    assert f.loc[:2, "tax_status"].eq("supported").all() and f.loc[4, "tax_status"] == "supported"
    assert f.loc[3:, "nav"].isna().all()
    out = __import__("alphacomb.tax", fromlist=["summarise_after_tax"]).summarise_after_tax(f)
    assert out["n_unsupported_tax_months"] == 1 and "DIAGNOSTIC" in out["basis"]


def test_a_known_zero_dividend_is_supported():
    f, _ = run(_with_missing_div(3, value=0.0), build_weights(), **CARRY)
    assert f["tax_status"].eq("supported").all() and f["n_div_missing"].eq(0).all()


def test_missing_dividend_on_an_unheld_name_is_irrelevant():
    f, _ = run(_with_missing_div(3, permno=6), build_weights(), **CARRY)
    assert f["tax_status"].eq("supported").all()


def test_policy_flag_only_keeps_the_zero_filled_after_tax_return_but_still_labels_it():
    f, _ = run(_with_missing_div(3), build_weights(), dividend_missing="flag_only", **CARRY)
    assert np.isfinite(f.loc[3, "after_tax_ret"]) and f.loc[3, "tax_status"] == "incomplete_flagged"


def test_as_run_still_zero_fills_missing_dividends_silently():
    f, _ = run(_with_missing_div(3), build_weights())
    assert np.isfinite(f.loc[3, "after_tax_ret"]) and "tax_status" not in f.columns


# ---- tax lots: reappearance after a temporary gap ------------------------------------------------
def test_policy_a_reappearing_name_after_a_gap_keeps_its_old_lot_unresolved_and_untraded():
    b, w = build_bundle(gone=(2, 3), reappear=5), build_weights()      # weights still ask for name 2
    f, ledger = run(b, w, **CARRY)
    assert [g for g in ledger.realised if g.permno == 2 and g.date >= DATES[3]] == []
    cut = w[w["date"] <= DATES[3]]
    _, l_cut = run(build_bundle(gone=(2, 3), reappear=5), cut, **CARRY)
    assert ledger.position(2) == pytest.approx(l_cut.position(2), rel=1e-12)
    assert f.loc[5:, "n_exit_unresolved"].eq(1).all()


# ---- as_run compatibility on the synthetic generator --------------------------------------------
def test_as_run_is_unchanged_on_the_synthetic_bundle_with_and_without_the_new_fields(small_panel):
    from alphacomb.contracts import load_config
    from alphacomb.tax import TaxConfig, after_tax_backtest, get_regime
    from test_backtest import simple_weights

    cfg = load_config("base")
    cfg = {**cfg, "costs": {**cfg["costs"], "aum_usd_2020": 1.0e7}}
    w = simple_weights(small_panel)
    default = after_tax_backtest(w, small_panel, cfg, TaxConfig(regime=get_regime("taxable")))
    explicit = after_tax_backtest(w, small_panel, cfg,
                                  TaxConfig(regime=get_regime("taxable"), exit_policy="as_run"))
    pd.testing.assert_frame_equal(default, explicit, check_exact=True)
    golden = pd.read_parquet(Path(__file__).parent / "golden" / "as_run_synthetic_small_panel.parquet")
    pd.testing.assert_frame_equal(default.reset_index(drop=True), golden, check_exact=False,
                                  rtol=1e-12, atol=0)
    assert "valuation_status" not in default.columns and "exit_policy" not in default.attrs


# ---- pipeline 06 isolation ----------------------------------------------------------------------
@pytest.fixture(scope="module")
def pipe():
    path = Path(__file__).resolve().parents[2] / "pipelines" / "06_after_tax_eval.py"
    spec = importlib.util.spec_from_file_location("pipe06", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(mod)
    return mod


def _call(pipe, monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["06", *argv])
    with pytest.raises(SystemExit) as e:
        pipe.main()
    return str(e.value)


def test_pipeline_refuses_carry_v1_without_an_explicit_out(pipe, monkeypatch):
    assert "requires an explicit --out" in _call(pipe, monkeypatch, "--exit-policy", "carry_v1")


def test_pipeline_refuses_carry_v1_directly_in_outputs(pipe, monkeypatch):
    msg = _call(pipe, monkeypatch, "--exit-policy", "carry_v1", "--out",
                str(paths.outputs_root() / "summary_after_tax.csv"))
    assert "may not sit directly in outputs" in msg


def test_pipeline_refuses_carry_v1_overwrite_and_existing_files(pipe, monkeypatch, tmp_path):
    existing = tmp_path / "phase2_summary.csv"
    existing.write_text("keep me")
    assert "already exists" in _call(pipe, monkeypatch, "--exit-policy", "carry_v1", "--out", str(existing))
    assert "refuses --overwrite" in _call(pipe, monkeypatch, "--exit-policy", "carry_v1", "--overwrite",
                                          "--out", str(tmp_path / "new" / "s.csv"))
    assert existing.read_text() == "keep me"
