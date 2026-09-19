"""The economic policy trained on after-tax utility.

The property that makes this arm comparable to the tax-blind one is **nesting**: with zero rates the
tax term must vanish identically, so any difference between the arms is the objective and nothing
else.
"""
from __future__ import annotations

import numpy as np
import pytest

from alphacomb.models.economic import EconomicPolicy, MonthBatch

torch = pytest.importorskip("torch")


def batch(n: int = 40, seed: int = 0) -> MonthBatch:
    import pandas as pd
    rng = np.random.default_rng(seed)
    return MonthBatch(
        date=pd.Timestamp("2015-06-30"), permnos=np.arange(n),
        X=rng.normal(0, 1, (n, 5)).astype("float32"),
        r=rng.normal(0.01, 0.05, n).astype("float32"),
        spread=np.full(n, 0.001, dtype="float32"),
        impact=np.full(n, 0.01, dtype="float32"),
        borrow=np.full(n, 0.0002, dtype="float32"),
        B=rng.normal(0, 1, (n, 3)).astype("float32"),
        L=np.eye(3, dtype="float32") * 0.04,
        d=np.full(n, 0.01, dtype="float32"),
    )


def test_zero_rates_switch_the_tax_term_off():
    assert EconomicPolicy().tax_aware is False
    assert EconomicPolicy(tax_short_rate=0.408, tax_long_rate=0.238).tax_aware is True


def test_selling_an_embedded_gain_is_charged():
    policy = EconomicPolicy(tax_short_rate=0.40, tax_long_rate=0.20)
    n = 4
    w_prev = torch.tensor([0.10, 0.10, 0.10, 0.10])
    w = torch.tensor([0.00, 0.10, 0.05, 0.10])       # fully sold, held, half sold, held
    gain = torch.tensor([0.02, 0.02, 0.02, 0.02])
    age = torch.zeros(n)                              # short-term
    b = batch(n)
    b.r[:] = 0.0
    tax, gain_next, _ = policy._tax(w, w_prev, gain, age, b, torch)
    # 0.02 fully realised + 0.02 half realised = 0.03 of gain, at (essentially) the short-term rate.
    # Not exactly 0.40: the statutory boundary is smoothed with a sigmoid so the policy has a
    # gradient through it, which leaves sigmoid(-12/2) = 0.25% of long-term weight even at age 0.
    assert float(tax) == pytest.approx(0.40 * 0.03, rel=2e-3)
    assert float(gain_next[0]) == pytest.approx(0.0, abs=1e-7)  # nothing left embedded (float32)
    assert float(gain_next[1]) == pytest.approx(0.02)


def test_long_held_positions_get_the_preferential_rate():
    policy = EconomicPolicy(tax_short_rate=0.40, tax_long_rate=0.20, tax_boundary_tau=0.25)
    w_prev, w = torch.tensor([0.10]), torch.tensor([0.0])
    gain = torch.tensor([0.02])
    b = batch(1)
    b.r[:] = 0.0
    short_tax, _, _ = policy._tax(w, w_prev, gain, torch.tensor([0.0]), b, torch)
    long_tax, _, _ = policy._tax(w, w_prev, gain, torch.tensor([24.0]), b, torch)
    assert float(long_tax) < float(short_tax)
    assert float(long_tax) == pytest.approx(0.20 * 0.02, rel=1e-3)


def test_closing_a_short_never_gets_the_preferential_rate():
    """s1233: however long the short was open, the gain is ordinary."""
    policy = EconomicPolicy(tax_short_rate=0.40, tax_long_rate=0.20, tax_boundary_tau=0.25)
    b = batch(1)
    b.r[:] = 0.0
    tax, _, _ = policy._tax(torch.tensor([0.0]), torch.tensor([-0.10]),
                            torch.tensor([0.02]), torch.tensor([36.0]), b, torch)
    assert float(tax) == pytest.approx(0.40 * 0.02, rel=1e-3)


def test_realising_a_loss_is_a_credit_and_the_haircut_scales_it():
    full = EconomicPolicy(tax_short_rate=0.40, tax_harvest_haircut=1.0)
    half = EconomicPolicy(tax_short_rate=0.40, tax_harvest_haircut=0.5)
    none = EconomicPolicy(tax_short_rate=0.40, tax_harvest_haircut=0.0)
    args = (torch.tensor([0.0]), torch.tensor([0.10]), torch.tensor([-0.02]), torch.tensor([0.0]))
    b = batch(1)
    b.r[:] = 0.0
    t_full = float(full._tax(*args, b, torch)[0])
    t_half = float(half._tax(*args, b, torch)[0])
    t_none = float(none._tax(*args, b, torch)[0])
    assert t_full < t_half < 0 or t_full < t_half <= t_none
    assert t_none == pytest.approx(0.0)
    assert t_full == pytest.approx(-0.40 * 0.02, rel=3e-3)   # smoothed boundary, as above


def test_embedded_gain_accumulates_with_the_return():
    policy = EconomicPolicy(tax_short_rate=0.40)
    b = batch(1)
    b.r[:] = 0.10
    w = torch.tensor([0.10])
    _, gain_next, age_next = policy._tax(w, w, torch.tensor([0.0]), torch.tensor([0.0]), b, torch)
    assert float(gain_next[0]) == pytest.approx(0.10 * 0.10, rel=1e-5)
    assert float(age_next[0]) == pytest.approx(1.0, rel=1e-5)


def test_buying_dilutes_the_holding_period():
    policy = EconomicPolicy(tax_short_rate=0.40)
    b = batch(1)
    b.r[:] = 0.0
    # held 0.05 for 12 months, now doubling the position: the average age must roughly halve
    _, _, age_next = policy._tax(torch.tensor([0.10]), torch.tensor([0.05]),
                                 torch.tensor([0.0]), torch.tensor([12.0]), b, torch)
    assert 6.0 < float(age_next[0]) < 7.0


def test_the_tax_term_is_differentiable():
    """It has to produce a gradient, or the policy cannot learn from it."""
    policy = EconomicPolicy(tax_short_rate=0.40, tax_long_rate=0.20)
    w = torch.tensor([0.05, -0.05], requires_grad=True)
    b = batch(2)
    b.r[:] = 0.01
    tax, _, _ = policy._tax(w, torch.tensor([0.10, -0.10]), torch.tensor([0.02, 0.01]),
                            torch.tensor([6.0, 6.0]), b, torch)
    tax.backward()
    assert w.grad is not None
    assert torch.isfinite(w.grad).all()
    assert float(w.grad.abs().sum()) > 0


def test_tax_aware_policy_trains_and_nests_the_blind_one(small_panel):
    """End to end on a few months: both arms fit, and zero rates reproduce the blind utility."""
    import pandas as pd
    from alphacomb.contracts import load_config
    from alphacomb.models.base import build_design
    from alphacomb.models.economic import prepare_months
    from alphacomb.contracts.interfaces import CellSpec
    from alphacomb.risk import RiskCache, StructuralRiskModel

    cfg = load_config("base")
    spec = CellSpec.parse("L-S-E-0")
    df, features = build_design(small_panel, spec, horizon=1)
    risk = RiskCache(StructuralRiskModel(small_panel, cfg))
    kwargs = dict(risk=risk, aum=1.0e7, impact_k=1.0, commission_bps=1.0)
    dates = sorted(df["date"].unique())
    train = df[df["date"].isin(dates[-30:-10])]
    val = df[df["date"].isin(dates[-10:-2])]
    train_m = prepare_months(train, features.all, **kwargs)
    val_m = prepare_months(val, features.all, **kwargs)
    if len(train_m) < 6 or len(val_m) < 2:
        pytest.skip("not enough usable months in the fixture panel")

    blind = EconomicPolicy(nonlinear=False, max_epochs=3, patience=2, seed=0).fit(train_m, val_m)
    taxed = EconomicPolicy(nonlinear=False, max_epochs=3, patience=2, seed=0,
                           tax_short_rate=0.408, tax_long_rate=0.238).fit(train_m, val_m)
    assert np.isfinite(blind.val_utility_)
    assert np.isfinite(taxed.val_utility_)
    # NOTE: we deliberately do NOT assert taxed.val_utility_ <= blind.val_utility_. That ordering
    # only holds if both arms reach their optimum; with a few epochs of SGD the two follow
    # different gradient paths and either can end up ahead on its own objective. Asserting it would
    # be asserting that the optimiser is perfect.

    zero = EconomicPolicy(nonlinear=False, max_epochs=3, patience=2, seed=0,
                          tax_short_rate=0.0, tax_long_rate=0.0).fit(train_m, val_m)
    assert zero.val_utility_ == pytest.approx(blind.val_utility_, rel=1e-9)
