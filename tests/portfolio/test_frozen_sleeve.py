"""Non-tradeable held positions: the frozen sleeve (docs/NON_TRADEABLE_TREATMENT.md).

The bug these cover turned every prediction cell on the real DEU panel into one month of strategy
followed by 131 months of a drifting book, and no test caught it, because every existing test of
this path passes ``w_prev=None`` - a fresh book, the one case in which no held name can be
unpriceable. Each test below therefore starts from a *held* book.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.portfolio import OptimizerConfig, construct, grinold_alpha, project
from alphacomb.portfolio.cost_terms import partition_prior_book, priced_at
from alphacomb.portfolio.optimizer import BREACH_TOL, FrozenSleeve, bound_breach
from alphacomb.portfolio.robust import construct_robust
from alphacomb.risk import StructuralRiskModel

DATE = pd.Timestamp("2000-12-31")


@pytest.fixture(scope="module")
def setup(small_panel):
    risk_provider = StructuralRiskModel(small_panel).prepare()
    risk = risk_provider.load(DATE)
    rng = np.random.default_rng(3)
    scores = pd.Series(rng.normal(size=len(risk.B)), index=risk.B.index)
    alpha = grinold_alpha(scores, risk, ic=0.05)
    cfg = OptimizerConfig.from_files()
    cfg = OptimizerConfig(**{**cfg.__dict__, "gamma": 40.0})
    return small_panel, risk, alpha, cfg


def _book(res_weights: pd.Series, n: int = 20) -> pd.Series:
    """A prior book of the n largest absolute positions."""
    w = res_weights[res_weights.abs() > 0]
    return w.reindex(w.abs().sort_values(ascending=False).index[:n])


def _blank_fields(cost_inputs: pd.DataFrame, date, permnos) -> pd.DataFrame:
    """Keep the C6 row but void its market fields: alive, unpriceable."""
    ci = cost_inputs.copy()
    mask = (ci["date"] == pd.Timestamp(date)) & ci["permno"].isin(list(permnos))
    ci.loc[mask, ["spread", "sigma_d", "adv_usd"]] = np.nan
    return ci


def _drop_rows(cost_inputs: pd.DataFrame, date, permnos) -> pd.DataFrame:
    """Remove the C6 row entirely: the security has left the panel."""
    ci = cost_inputs.copy()
    mask = (ci["date"] == pd.Timestamp(date)) & ci["permno"].isin(list(permnos))
    return ci.loc[~mask].reset_index(drop=True)


# ------------------------------------------------------------------ partition

def test_partition_splits_tradeable_frozen_and_exited(setup):
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 12)
    frozen_names, exited_names = list(book.index[:3]), list(book.index[3:5])
    ci = _blank_fields(panel.cost_inputs, DATE, frozen_names)
    ci = _drop_rows(ci, DATE, exited_names)

    tradeable, frozen, exited = partition_prior_book(DATE, ci, book)
    assert set(frozen) == set(frozen_names)
    assert set(exited) == set(exited_names)
    assert set(tradeable) == set(book.index) - set(frozen_names) - set(exited_names)
    # the three sets partition the held book exactly
    assert len(tradeable) + len(frozen) + len(exited) == len(book)


def test_partition_is_empty_for_a_fresh_book(setup):
    panel, _, _, _ = setup
    tradeable, frozen, exited = partition_prior_book(DATE, panel.cost_inputs, None)
    assert len(tradeable) == len(frozen) == len(exited) == 0


def test_priced_at_distinguishes_blanked_from_removed(setup):
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    names = list(_book(base.weights, 6).index)
    blanked = _blank_fields(panel.cost_inputs, DATE, names[:3])
    assert set(names[:3]) <= set(priced_at(DATE, blanked))
    removed = _drop_rows(panel.cost_inputs, DATE, names[:3])
    assert not set(names[:3]) & set(priced_at(DATE, removed))


# ------------------------------------------- the regression: book keeps trading

@pytest.mark.parametrize("solver", [construct, construct_robust])
def test_one_unpriceable_holding_does_not_freeze_the_whole_book(setup, solver):
    """The actual bug. One blanked name used to return the entire prior book, every month."""
    panel, risk, alpha, cfg = setup
    # cfg must be passed by keyword: construct_robust takes `uncertainty` sixth, not `cfg`.
    base = solver(DATE, alpha, None, risk, panel.cost_inputs, cfg=cfg)
    book = _book(base.weights, 20)
    ci = _blank_fields(panel.cost_inputs, DATE, list(book.index[:1]))

    res = solver(DATE, alpha, book, risk, ci, cfg=cfg)
    assert not res.status.startswith("failed"), res.status
    # The result must not simply be the prior book handed back.
    common = book.index.intersection(res.weights.index)
    assert not np.allclose(res.weights.reindex(common).to_numpy(),
                           book.reindex(common).to_numpy())
    assert res.diagnostics["n_frozen"] == 1


def test_frozen_position_is_carried_at_its_prior_weight(setup):
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 20)
    frozen_names = list(book.index[:3])
    ci = _blank_fields(panel.cost_inputs, DATE, frozen_names)

    res = construct(DATE, alpha, book, risk, ci, cfg)
    for name in frozen_names:
        assert name in res.weights.index
        assert res.weights[name] == pytest.approx(book[name], abs=1e-12)
    assert res.diagnostics["n_frozen"] == 3
    assert res.diagnostics["gross_frozen"] == pytest.approx(book[frozen_names].abs().sum())


def test_exited_position_is_closed_not_frozen(setup):
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 20)
    gone = list(book.index[:2])
    ci = _drop_rows(panel.cost_inputs, DATE, gone)

    res = construct(DATE, alpha, book, risk, ci, cfg)
    assert not set(gone) & set(res.weights.index)
    assert res.diagnostics["n_exited"] == 2
    assert res.diagnostics["n_frozen"] == 0


# ------------------------------------------------- the sleeve consumes budget

def test_gross_budget_counts_the_frozen_sleeve(setup):
    """Traded gross plus the sleeve's gross must still respect gross_max."""
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 25)
    frozen_names = list(book.index[:8])
    ci = _blank_fields(panel.cost_inputs, DATE, frozen_names)

    res = construct(DATE, alpha, book, risk, ci, cfg)
    assert float(res.weights.abs().sum()) <= cfg.gross_max + 1e-4


def test_dollar_neutrality_counts_the_frozen_sleeve(setup):
    panel, risk, alpha, cfg = setup
    if not (cfg.dollar_neutral and not cfg.long_only):
        pytest.skip("configuration is not dollar-neutral")
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 25)
    ci = _blank_fields(panel.cost_inputs, DATE, list(book.index[:8]))

    res = construct(DATE, alpha, book, risk, ci, cfg)
    # The whole book is neutral, which is only possible if the optimiser offset the sleeve.
    assert abs(float(res.weights.sum())) < 1e-3


def test_sleeve_build_reports_committed_exposure(setup):
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 10)
    frozen = pd.Index(book.index[:4])
    sleeve = FrozenSleeve.build(frozen, book, risk)
    assert not sleeve.empty
    assert sleeve.gross == pytest.approx(book[frozen].abs().sum())
    assert sleeve.net == pytest.approx(book[frozen].sum())
    expected_beta = float(risk.B.reindex(frozen)["beta"].to_numpy() @ book[frozen].to_numpy())
    assert sleeve.beta == pytest.approx(expected_beta)
    assert sleeve.factor_exposure.shape == (risk.B.shape[1],)


def test_empty_sleeve_reproduces_the_base_optimiser(setup):
    """Nesting: with nothing frozen the result must be identical to the unmodified path."""
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 20)
    a = construct(DATE, alpha, book, risk, panel.cost_inputs, cfg)
    assert a.diagnostics["n_frozen"] == 0
    assert a.diagnostics["n_exited"] == 0
    sleeve = FrozenSleeve.build(pd.Index([]), book, risk)
    assert sleeve.empty
    assert sleeve.gross == 0.0 and sleeve.net == 0.0
    assert np.allclose(sleeve.factor_exposure, 0.0)


# -------------------------------------------- the breach measure sees the sleeve

def test_breach_measure_accounts_for_the_sleeve(setup):
    """A correct sleeve solution must not be scored as a violation.

    The aggregate bounds are written on the whole book, so a correct solution has a deliberately
    non-zero traded-only net: ``sum(w) == -net_frozen``. A breach measure that compares
    ``|sum(w)|`` to zero therefore reports a violation of order one for every correct month, sends
    each one down the soft-constraint path, and doubles the solve cost. On the real DEU panel that
    showed up as "relative breach=1.04" on every single month.
    """
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 25)
    frozen_names = list(book.index[:8])
    ci = _blank_fields(panel.cost_inputs, DATE, frozen_names)

    res = construct(DATE, alpha, book, risk, ci, cfg)
    sleeve = FrozenSleeve.build(pd.Index(frozen_names), book, risk)
    traded = res.weights.drop(index=frozen_names)

    prev_arr = book.reindex(traded.index).fillna(0.0).to_numpy()
    rm = risk.align(traded.index)
    from alphacomb.portfolio.cost_terms import cost_inputs_for
    cinfo = cost_inputs_for(DATE, ci, traded.index, borrow_fee_proxy=cfg.borrow_fee_proxy(),
                            allow_synthetic_market_imputation=True)
    adv_cap = np.clip(cinfo["adv_usd"].to_numpy() * cfg.adv_participation_max / cfg.aum_usd,
                      1e-6, None)
    pos_cap = np.minimum(cfg.weight_abs_max, np.maximum(adv_cap, 1e-5))

    with_sleeve = bound_breach(traded.to_numpy(), prev_arr, adv_cap, pos_cap, cfg, rm,
                               frozen=sleeve)
    without = bound_breach(traded.to_numpy(), prev_arr, adv_cap, pos_cap, cfg, rm)
    assert with_sleeve <= BREACH_TOL, f"correct solution scored as breach {with_sleeve}"
    assert without > with_sleeve, "ignoring the sleeve should look worse, not better"


# ------------------------------- project() faces the same trade cap as construct()

def test_projection_respects_the_per_name_trade_cap(setup):
    """The economic-loss path must not be allowed trades the prediction path cannot make.

    Before 8 October 2026 ``project`` built its own constraint list with no prior book, so it
    applied the position cap but never ``|w - prev| <= adv_cap``. On the real DEU panel one
    name-month trade in six exceeded the participation limit, by up to 20x, in exactly the
    ``*-E-*`` half of the factorial.
    """
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 30)
    # A proposal that asks for the whole budget, i.e. the opposite book: every name wants to move.
    proposal = -np.sign(book) * cfg.weight_abs_max
    res = project(DATE, proposal, risk, panel.cost_inputs, cfg, w_prev=book)
    assert not res.status.startswith("failed"), res.status

    from alphacomb.portfolio.cost_terms import cost_inputs_for
    traded = res.weights.reindex(book.index).dropna()
    ci = cost_inputs_for(DATE, panel.cost_inputs, traded.index,
                         borrow_fee_proxy=cfg.borrow_fee_proxy(),
                         allow_synthetic_market_imputation=True)
    adv_cap = np.clip(ci["adv_usd"].to_numpy() * cfg.adv_participation_max / cfg.aum_usd,
                      1e-6, None)
    moved = np.abs(traded.to_numpy() - book.reindex(traded.index).to_numpy())
    # Allow the widened cap book_constraints uses for an already-drifted position.
    assert np.all(moved <= adv_cap * 1.01 + 1e-9), (
        f"{int((moved > adv_cap * 1.01).sum())} of {len(moved)} trades exceed adv_cap")


def test_projection_reports_the_same_diagnostics_as_construct(setup):
    """Both C11 paths must expose the sleeve, so the exhibit can report it for all 16 cells."""
    panel, risk, alpha, cfg = setup
    base = construct(DATE, alpha, None, risk, panel.cost_inputs, cfg)
    book = _book(base.weights, 20)
    proposal = -np.sign(book) * cfg.weight_abs_max
    ci = _blank_fields(panel.cost_inputs, DATE, list(book.index[:3]))
    res = project(DATE, proposal, risk, ci, cfg, w_prev=book)
    for key in ("n_assets", "n_frozen", "gross_frozen", "n_exited", "gross", "net"):
        assert key in res.diagnostics, key
    assert res.diagnostics["n_frozen"] == 3
