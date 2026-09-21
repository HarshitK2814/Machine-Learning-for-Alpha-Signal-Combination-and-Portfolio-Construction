"""Deferral overhang: the gap between reported and owned.

These tests pin the arithmetic behind a live public dispute about a $100bn industry, so they are
written to fail loudly rather than return a plausible number.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.tax import (deferral_overhang, harvesting_decomposition, overhang_trajectory)

def simple_weights(bundle, n_per_side: int = 15) -> pd.DataFrame:
    """A crude dollar-neutral signal portfolio, used only to exercise the accounting."""
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
    from alphacomb.contracts import load_config
    base = load_config("base")
    return {**base, "costs": {**base["costs"], "aum_usd_2020": 1.0e7}}


def test_overhang_sign_follows_the_sign_of_the_embedded_position(small_panel, weights, cfg):
    """Embedded GAINS flatter a realised-basis report; embedded LOSSES understate it.

    The first version of this test asserted that liquidation can only reduce the reported figure.
    That is true only for a book carrying net embedded gains. A book carrying embedded losses would
    realise a tax credit on liquidation, so its liquidation figure is higher. The test caught the
    error in the module's own docstring.
    """
    r = deferral_overhang(weights, small_panel, cfg)
    if r.terminal_embedded_gain > 0:
        assert r.liquidation_ann <= r.pre_liquidation_ann + 1e-12
        assert r.overhang_ann >= -1e-12
    else:
        assert r.liquidation_ann >= r.pre_liquidation_ann - 1e-12
        assert "NEGATIVE overhang" in r.verdict


def test_a_tax_exempt_investor_has_no_overhang(small_panel, weights, cfg):
    """With no tax there is no deferred liability, so both bases must coincide exactly."""
    r = deferral_overhang(weights, small_panel, cfg, regime="tax_exempt")
    assert r.overhang_ann == pytest.approx(0.0, abs=1e-12)
    assert r.terminal_deferred_tax == pytest.approx(0.0, abs=1e-12)


def test_mark_to_market_regime_cannot_defer(small_panel, weights, cfg):
    """s475(f) taxes unrealised gains annually, so by construction nothing can be deferred."""
    r = deferral_overhang(weights, small_panel, cfg, regime="trader_475f_mtm")
    assert abs(r.overhang_ann) < 1e-6, r.summary()


def test_a_higher_tax_rate_produces_a_larger_overhang(small_panel, weights, cfg):
    """The liability scales with the rate applied to the same embedded gain."""
    low = deferral_overhang(weights, small_panel, cfg, regime="offshore_fund")
    high = deferral_overhang(weights, small_panel, cfg, regime="taxable_us_top_bracket")
    assert high.overhang_ann >= low.overhang_ann - 1e-12


def test_the_embedded_gain_path_is_reported_not_just_its_endpoint(small_panel, weights, cfg):
    """A referee will ask whether the liability grows; the trajectory has to be available."""
    r = deferral_overhang(weights, small_panel, cfg)
    assert isinstance(r.embedded_gain_path, pd.Series)
    assert len(r.embedded_gain_path) == r.months
    assert r.embedded_gain_path.notna().all()


def test_trajectory_covers_several_horizons(small_panel, weights, cfg):
    out = overhang_trajectory(weights, small_panel, cfg, checkpoints=(24, 48, 72))
    assert len(out) >= 2
    assert out["months"].is_monotonic_increasing
    for col in ("pre_liquidation_ann", "liquidation_ann", "overhang_ann", "overhang_share"):
        assert col in out.columns
    # sign of the gap must track the sign of the embedded position at every horizon
    gains = out["embedded_gain_pct_nav"]
    gap = out["pre_liquidation_ann"] - out["liquidation_ann"]
    assert ((gains > 0) == (gap > -1e-12)).all() or (gains.abs() < 1e-9).all(), out


def test_verdict_covers_every_regime_the_arithmetic_can_produce(small_panel, weights, cfg):
    """Five outcomes are possible and the verdict must name the right one.

    An earlier version fired the "embedded losses" branch on an overhang of -1e-9 - floating-point
    zero - and so mislabelled a strategy whose embedded gains were simply sheltered by an
    accumulated loss carryforward. The branch now needs a tolerance, and the zero case
    distinguishes "nothing deferred" from "liability cancelled by a deferred tax asset".
    """
    r = deferral_overhang(weights, small_panel, cfg)
    assert any(word in r.verdict for word in
               ("small", "material", "LARGE", "NEGATIVE", "ZERO", "zero")), r.verdict


def test_carryforward_is_reported_so_the_netting_is_auditable(small_panel, weights, cfg):
    """A deferred tax liability can be cancelled by a deferred tax asset; both must be visible."""
    r = deferral_overhang(weights, small_panel, cfg)
    assert hasattr(r, "terminal_carryforward")
    assert np.isfinite(r.terminal_carryforward)
    assert r.terminal_carryforward >= -1e-12, "a carryforward is a non-negative loss balance"


def test_tiny_floating_point_overhang_is_not_called_embedded_losses(small_panel, weights, cfg):
    """The exact bug: -1e-9 is zero, not evidence of an embedded loss position."""
    r = deferral_overhang(weights, small_panel, cfg, regime="trader_475f_mtm")
    assert abs(r.overhang_ann) < 1e-6
    assert "NEGATIVE overhang" not in r.verdict, r.verdict


def test_decomposition_accounts_for_every_component(small_panel, weights, cfg):
    """The parts a referee will ask to see separately."""
    d = harvesting_decomposition(weights, small_panel, cfg)
    for key in ("gross_alpha_ann", "cost_drag_ann", "tax_paid_ann", "pre_liquidation_ann",
                "liquidation_ann", "deferral_overhang_ann", "realised_short_term_ann",
                "realised_long_term_ann", "wash_disallowed_ann", "embedded_gain_pct_nav"):
        assert key in d, key
        assert np.isfinite(d[key]), f"{key} is not finite: {d[key]}"


def test_cost_drag_is_reported_as_a_negative_contribution(small_panel, weights, cfg):
    d = harvesting_decomposition(weights, small_panel, cfg)
    assert d["cost_drag_ann"] <= 0, "trading costs must reduce, never add"


def test_liquidation_figure_matches_between_the_two_entry_points(small_panel, weights, cfg):
    """deferral_overhang and harvesting_decomposition must not disagree with each other."""
    r = deferral_overhang(weights, small_panel, cfg)
    d = harvesting_decomposition(weights, small_panel, cfg)
    assert d["liquidation_ann"] == pytest.approx(r.liquidation_ann, rel=1e-9)
    assert d["pre_liquidation_ann"] == pytest.approx(r.pre_liquidation_ann, rel=1e-9)
