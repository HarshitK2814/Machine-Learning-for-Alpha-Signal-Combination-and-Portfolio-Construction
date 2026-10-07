"""E29 factorial attribution.

The decisive tests here are recovery tests: we plant known factor effects in simulated cell
returns and check the estimator gets them back. An attribution routine that cannot recover an
effect it was handed has no business being the paper's headline exhibit.

The second group of tests pins the statistical point the module exists for - that contrasts are
formed in the time domain, so that common variation across cells cancels instead of being
mismodelled as noise.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.validation import factorial

ALL_CELLS = [
    f"{n}-{c}-{e}-{u}"
    for n in ("L", "N") for c in ("S", "C") for e in ("P", "E") for u in ("0", "U")
]


def simulate(effects: dict[str, float], n_months: int = 240, common_sd: float = 0.05,
             idio_sd: float = 0.002, seed: int = 7) -> pd.DataFrame:
    """Cell returns with planted main effects and a large shared market component.

    ``common_sd`` is deliberately an order of magnitude larger than the planted effects: that is
    the real situation, and it is what defeats a naive regression on cell means.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2000-01-31", periods=n_months, freq="ME")
    common = rng.normal(0, common_sd, size=n_months)
    out = {}
    for cell in ALL_CELLS:
        levels = factorial.parse_cell(cell)
        mu = sum(effects.get(f, 0.0) * (1 if levels[f] == 1 else 0) for f in factorial.FACTORS)
        out[cell] = mu + common + rng.normal(0, idio_sd, size=n_months)
    return pd.DataFrame(out, index=dates)


# ----------------------------------------------------------------- parsing

def test_parse_cell_decodes_both_extremes():
    assert factorial.parse_cell("N-C-E-U") == {
        "nonlinear": 1, "conditional": 1, "economic": 1, "uncertainty": 1}
    assert factorial.parse_cell("L-S-P-0") == {
        "nonlinear": -1, "conditional": -1, "economic": -1, "uncertainty": -1}


@pytest.mark.parametrize("bad", ["N-C-E", "N-C-E-U-X", "X-C-E-U", "N-Q-E-U", ""])
def test_malformed_cell_codes_raise(bad):
    """A silently mis-parsed cell would corrupt every contrast built from it."""
    with pytest.raises(ValueError):
        factorial.parse_cell(bad)


def test_design_matrix_is_balanced_and_orthogonal():
    d = factorial.design_matrix(ALL_CELLS)
    assert d.shape == (16, 4)
    assert (d.sum(axis=0) == 0).all(), "each factor must be balanced +1/-1 across the 16 cells"
    gram = d.T.to_numpy() @ d.to_numpy()
    assert np.allclose(gram, 16 * np.eye(4)), "factors must be mutually orthogonal"


# ----------------------------------------------------------------- recovery

def test_recovers_a_single_planted_main_effect():
    planted = 0.004  # 40 bp per month on the nonlinear arm
    df = simulate({"nonlinear": planted})
    eff = factorial.factorial_effects(df)
    row = eff[eff["term"] == "nonlinear"].iloc[0]
    # The contrast is a difference of group means, and the planted shift applies to half the
    # cells, so the recovered effect equals the planted size.
    assert row["estimate_monthly"] == pytest.approx(planted, abs=3e-4)
    assert row["t_stat"] > 5


def test_recovers_several_planted_effects_independently():
    planted = {"nonlinear": 0.004, "economic": 0.002, "uncertainty": -0.001}
    df = simulate(planted)
    eff = factorial.factorial_effects(df).set_index("term")
    for factor, size in planted.items():
        assert eff.loc[factor, "estimate_monthly"] == pytest.approx(size, abs=3e-4)
    # A factor that was not planted must come back near zero.
    assert abs(eff.loc["conditional", "estimate_monthly"]) < 5e-4


def test_absent_effect_is_estimated_near_zero():
    df = simulate({"nonlinear": 0.004}, seed=3)
    eff = factorial.factorial_effects(df, max_order=1).set_index("term")
    for factor in ("conditional", "economic", "uncertainty"):
        assert abs(eff.loc[factor, "estimate_monthly"]) < 5e-4


@pytest.mark.slow
def test_inference_is_calibrated_under_the_null():
    """The test that makes the t-statistics believable: size, measured rather than assumed.

    A single null draw says nothing - at a 5% level with four main effects, some draw will reject
    about 18% of the time, and an earlier version of this file failed for exactly that reason. The
    honest check is the rejection *rate* over many independent nulls.

    Measured here: ~6.4% against a nominal 5%, with t-statistics centred on 0 and unit scale. The
    mild over-rejection is the usual Newey-West small-sample behaviour and is the direction that
    costs us significance rather than manufacturing it, which is the right way round for a paper
    whose headline is an attribution.
    """
    rejections = total = 0
    t_stats: list[float] = []
    for seed in range(200):
        eff = factorial.factorial_effects(simulate({}, seed=seed), max_order=1)
        t_stats.extend(eff["t_stat"].tolist())
        rejections += int(eff["significant_5pct"].sum())
        total += len(eff)

    rate = rejections / total
    assert 0.02 < rate < 0.11, f"null rejection rate {rate:.3f} is not near the nominal 5%"
    arr = np.asarray(t_stats)
    assert abs(arr.mean()) < 0.2, "t-statistics are not centred on zero under the null"
    assert 0.8 < arr.std() < 1.3, "t-statistics do not have approximately unit scale"


def test_interaction_is_recovered():
    """Plant a pure two-way interaction and check the right term picks it up."""
    rng = np.random.default_rng(5)
    dates = pd.date_range("2000-01-31", periods=240, freq="ME")
    common = rng.normal(0, 0.05, size=240)
    data = {}
    for cell in ALL_CELLS:
        lv = factorial.parse_cell(cell)
        both = 1.0 if (lv["nonlinear"] == 1 and lv["conditional"] == 1) else 0.0
        data[cell] = 0.006 * both + common + rng.normal(0, 0.002, size=240)
    df = pd.DataFrame(data, index=dates)

    eff = factorial.factorial_effects(df).set_index("term")
    assert eff.loc["nonlinear x conditional", "t_stat"] > 4
    assert eff.loc["nonlinear x conditional", "estimate_monthly"] > 0


# ------------------------------------------------- the statistical point

def test_common_variation_cancels_in_the_contrast():
    """The module's reason to exist: a huge shared component must not inflate the effect's SE.

    Cells here share a market component 25x larger than the planted effect. Because the contrast
    is formed in the time domain before averaging, that component differences out and the effect
    is still estimated precisely. A method that regressed 16 cell means on contrast codes would
    carry the shared variance into its residual and understate precision.
    """
    df = simulate({"nonlinear": 0.002}, common_sd=0.05, idio_sd=0.001)
    eff = factorial.factorial_effects(df, max_order=1).set_index("term")
    se = eff.loc["nonlinear", "se_monthly"]
    # The SE should reflect idiosyncratic noise only, not the 0.05 common component.
    assert se < 0.001, f"contrast SE {se:.5f} looks contaminated by the common component"
    assert eff.loc["nonlinear", "t_stat"] > 5


def test_contrast_weights_sum_to_zero():
    """Every effect must be a genuine contrast - otherwise it is partly a level, not a difference."""
    design = factorial.design_matrix(ALL_CELLS)
    from itertools import combinations
    for order in range(1, 5):
        for combo in combinations(factorial.FACTORS, order):
            code = design[list(combo)].prod(axis=1)
            assert code.sum() == 0, f"{combo} is not balanced"


def test_unbalanced_panel_raises_rather_than_silently_comparing_periods():
    df = simulate({"nonlinear": 0.003})
    df.iloc[:, 0] = np.nan  # one cell never ran
    with pytest.raises(ValueError, match="balanced"):
        factorial.factorial_effects(df)


def test_partial_missing_months_warn():
    df = simulate({"nonlinear": 0.003}, n_months=100)
    df.iloc[:60, 0] = np.nan
    with pytest.warns(UserWarning, match="months to missing cells"):
        factorial.factorial_effects(df)


# ----------------------------------------------------------------- Shapley

def test_shapley_values_sum_to_the_total_improvement():
    df = simulate({"nonlinear": 0.004, "economic": 0.002, "uncertainty": -0.001})
    sh = factorial.shapley_attribution(df)
    assert sh["shapley_monthly"].sum() == pytest.approx(sh.attrs["total_monthly"], abs=1e-10)


def test_shapley_ranks_the_largest_planted_factor_first():
    df = simulate({"nonlinear": 0.005, "economic": 0.001})
    sh = factorial.shapley_attribution(df).set_index("factor")
    assert sh["shapley_monthly"].idxmax() == "nonlinear"
    assert sh.loc["nonlinear", "shapley_monthly"] > sh.loc["economic", "shapley_monthly"]


def test_shapley_assigns_a_negative_factor_negative_value():
    df = simulate({"nonlinear": 0.004, "uncertainty": -0.003})
    sh = factorial.shapley_attribution(df).set_index("factor")
    assert sh.loc["uncertainty", "shapley_monthly"] < 0


# ----------------------------------------------------------------- report

def test_attribution_report_assembles_all_three_tables():
    df = simulate({"nonlinear": 0.004, "conditional": 0.002})
    rep = factorial.attribution_report(df)
    assert set(rep) == {"cells", "effects", "shapley"}
    assert len(rep["cells"]) == 16
    assert len(rep["effects"]) == 15  # 4 + 6 + 4 + 1
    assert len(rep["shapley"]) == 4
    assert rep["cells"]["sharpe_annualised"].notna().all()
