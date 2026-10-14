"""Phase B inference audit: deterministic synthetic checks of src/alphacomb/validation/inference.py.

Internal researcher-led validation, NOT external statistical sign-off. No historical data is read.
The D1 (``sharpe_se``), D2 (``romano_wolf`` step-down) and D5 (``hansen_spa`` threshold) defects found in
docs/INFERENCE_AUDIT_2026-10-13.md were corrected on 2026-10-13; the strict-xfail markers that documented
them were removed once the corrected assertions passed. Simulation evidence lives in
tools/audit_inference_simulations.py.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from alphacomb.validation import inference as inf
from alphacomb.validation.inference import (_expected_max_sharpe, _stationary_bootstrap_index, hansen_spa,
                                            benjamini_hochberg, mean_difference_test, newey_west_se,
                                            romano_wolf, sharpe_difference_test, sharpe_se)

TOOLS = Path(__file__).resolve().parents[2] / "tools"


def _ar1(T, phi, seed, scale=1.0):
    rng = np.random.default_rng(seed)
    e = rng.standard_normal(T + 200)
    x = np.zeros(T + 200)
    for t in range(1, T + 200):
        x[t] = phi * x[t - 1] + e[t]
    return scale * x[200:] * np.sqrt(1 - phi ** 2)


# ------------------------------------------------------------------ Newey-West
@pytest.mark.parametrize("lags", [0, 1, 4, 8])
def test_newey_west_matches_statsmodels_bartlett_hac(lags):
    import statsmodels.api as sm
    x = _ar1(200, 0.3, 1) + 0.1
    ref = sm.OLS(x, np.ones_like(x)).fit(cov_type="HAC", cov_kwds={"maxlags": lags, "use_correction": False}).bse[0]
    assert newey_west_se(x, lags=lags) == pytest.approx(ref, rel=1e-10)


def test_newey_west_default_lag_rule_is_floor_4_T_over_100_to_2_over_9():
    x = _ar1(132, 0.2, 2)
    assert newey_west_se(x) == pytest.approx(newey_west_se(x, lags=int(np.floor(4 * (132 / 100) ** (2 / 9)))))
    assert int(np.floor(4 * (132 / 100) ** (2 / 9))) == 4


def test_newey_west_iid_equals_classical_se_up_to_the_bartlett_cross_terms():
    x = np.random.default_rng(0).standard_normal(5000)
    assert newey_west_se(x, lags=0) == pytest.approx(x.std(ddof=0) / np.sqrt(len(x)), rel=1e-12)


# ------------------------------------------------------------------ stationary bootstrap indices
def test_bootstrap_indices_in_range_and_circular():
    T = 50
    idx = _stationary_bootstrap_index(T, 10 ** 9, np.random.default_rng(3))      # p ~ 0: one long block
    assert idx.min() >= 0 and idx.max() < T and len(idx) == T
    assert np.array_equal(idx, (idx[0] + np.arange(T)) % T)                       # wraps around, no truncation


def test_bootstrap_block_length_and_first_index_are_as_documented():
    T, block, reps = 120, 6, 3000
    rng = np.random.default_rng(4)
    breaks = n = 0
    firsts = np.zeros(T)
    for _ in range(reps):
        i = _stationary_bootstrap_index(T, block, rng)
        breaks += int((np.diff(i) % T != 1).sum())
        n += T - 1
        firsts[i[0]] += 1
    assert breaks / n == pytest.approx(1 / block * (1 - 1 / T), abs=0.006)        # P(new block) = 1/6
    assert firsts.max() / (reps / T) < 1.9                                         # start index ~ uniform


def test_bootstrap_with_block_1_is_iid():
    idx = _stationary_bootstrap_index(10000, 1, np.random.default_rng(5))
    assert abs(np.mean(np.diff(idx) % 10000 == 1) - 1 / 10000) < 0.002


# ------------------------------------------------------------------ sharpe_difference_test
def test_identical_series_give_zero_difference_and_p_one():
    x = _ar1(132, 0.2, 6, 0.04) + 0.01
    r = sharpe_difference_test(x, x.copy(), n_boot=300)
    assert r.statistic == 0.0 and r.p_value == 1.0 and r.detail["se_hac"] == 0.0


def test_missing_observations_are_dropped_pairwise_and_reported():
    x = _ar1(132, 0.2, 7, 0.04) + 0.01
    y = x + _ar1(132, 0.0, 8, 0.01)
    y2 = y.copy()
    y2[[5, 40, 41]] = np.nan
    r = sharpe_difference_test(x, y2, n_boot=200)
    assert r.detail["n_obs"] == 129
    with pytest.raises(ValueError):
        sharpe_difference_test(x, y[:100], n_boot=100)


def test_zero_variance_and_tiny_samples_are_handled_not_silent():
    x = _ar1(132, 0.2, 9, 0.04)
    r = sharpe_difference_test(np.zeros(132), x, n_boot=100)
    assert np.isnan(r.statistic) and "zero variance" in r.detail["note"]
    with pytest.raises(ValueError, match="at least 12"):
        sharpe_difference_test(x[:11], x[:11] + 1e-3, n_boot=100)
    near = sharpe_difference_test(x, x + 1e-13 * np.random.default_rng(1).standard_normal(132), n_boot=100)
    assert np.isfinite(near.p_value) or np.isnan(near.p_value)                    # no exception, no inf


def test_sharpe_difference_se_matches_the_analytic_delta_method_for_independent_iid_normals():
    """Reference: Var(SR_hat_ann) = P (1 + SR^2/2) / T for iid normals; independent pair -> sum."""
    T, P = 40000, 12
    rng = np.random.default_rng(10)
    a = 0.004 + 0.04 * rng.standard_normal(T)
    b = 0.002 + 0.03 * rng.standard_normal(T)
    sa, sb = a.mean() / a.std(ddof=1), b.mean() / b.std(ddof=1)
    ref = np.sqrt(P / T * ((1 + sa ** 2 / 2) + (1 + sb ** 2 / 2)))
    got = sharpe_difference_test(a, b, n_boot=100).detail["se_hac"]
    assert got == pytest.approx(ref, rel=0.06)


def test_pairing_is_preserved_in_the_bootstrap_and_in_the_se():
    rng = np.random.default_rng(11)
    common = 0.04 * rng.standard_normal(132)
    a = 0.005 + common
    b = 0.004 + common + 0.004 * rng.standard_normal(132)
    paired = sharpe_difference_test(a, b, n_boot=300).detail["se_hac"]
    shuffled = sharpe_difference_test(a, rng.permutation(b), n_boot=300).detail["se_hac"]
    assert paired < 0.3 * shuffled


def test_same_seed_reproduces_exactly_and_different_seed_changes_the_bootstrap():
    rng = np.random.default_rng(12)
    a, b = 0.04 * rng.standard_normal(132), 0.04 * rng.standard_normal(132)
    r1, r2, r3 = (sharpe_difference_test(a, b, n_boot=300, seed=s) for s in (5, 5, 6))
    assert r1.p_value == r2.p_value and r1.detail == r2.detail
    assert (r1.p_value, r1.detail["ci95_low"]) != (r3.p_value, r3.detail["ci95_low"])


def test_two_sided_p_is_symmetric_under_swapping_the_series():
    rng = np.random.default_rng(13)
    a, b = 0.005 + 0.04 * rng.standard_normal(132), 0.04 * rng.standard_normal(132)
    p_ab = sharpe_difference_test(a, b, n_boot=500, seed=1).p_value
    p_ba = sharpe_difference_test(b, a, n_boot=500, seed=1).p_value
    assert abs(p_ab - p_ba) < 1e-9 or abs(p_ab - p_ba) < 0.02


# ------------------------------------------------------------------ mean_difference_test
def test_mean_difference_constant_paired_difference_is_exact():
    c = 0.002
    x = _ar1(132, 0.2, 14, 0.04)
    r = mean_difference_test(x + c, x, n_boot=300)
    assert r.statistic == pytest.approx(12 * c, rel=1e-12)
    assert r.detail["ci95_low"] == pytest.approx(12 * c, abs=1e-10) == pytest.approx(r.detail["ci95_high"], abs=1e-10)
    assert r.p_value == 0.0                              # note: bootstrap p has no +1 correction (see report)


def test_mean_difference_se_is_annualised_hac_se_of_the_mean():
    d = _ar1(132, 0.3, 15, 0.01)
    r = mean_difference_test(d, np.zeros(132), n_boot=100)
    assert r.detail["se_hac"] == pytest.approx(12 * newey_west_se(d), rel=1e-12)
    assert r.statistic == pytest.approx(12 * d.mean(), rel=1e-12)


def test_mean_difference_symmetric_in_sign():
    d = _ar1(132, 0.3, 16, 0.01) + 0.002
    a = mean_difference_test(d, np.zeros(132), n_boot=400, seed=2)
    b = mean_difference_test(np.zeros(132), d, n_boot=400, seed=2)
    assert a.statistic == pytest.approx(-b.statistic, rel=1e-12)
    assert a.detail["se_hac"] == pytest.approx(b.detail["se_hac"], rel=1e-12)


# ------------------------------------------------------------------ Holm (five local copies in tools/)
def _load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    sys.path.insert(0, str(TOOLS))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HOLM_MODULES = ["exp_capacity_return_difference", "exp_capacity_channel_inference", "exp_after_tax_inference",
                "exp_design_identifiability", "exp_theme_liquidity_terciles"]


@pytest.mark.parametrize("module", HOLM_MODULES)
def test_every_local_holm_matches_statsmodels_including_ties_and_nan(module):
    from statsmodels.stats.multitest import multipletests
    holm = _load(module).holm
    vectors = [[0.01, 0.04, 0.03, 0.005], [0.2, 0.2, 0.2], [0.001], [0.5, 0.01, 0.01, 0.9, 0.03],
               [0.0, 1.0, 0.049, 0.0125]]
    for v in vectors:
        got = holm({str(i): p for i, p in enumerate(v)})
        ref = multipletests(v, method="holm")[1]
        assert [got[str(i)] for i in range(len(v))] == pytest.approx(list(ref), abs=1e-12), (module, v)
    got = holm({"a": 0.01, "b": float("nan"), "c": 0.02})            # NaN is outside the family
    assert np.isnan(got["b"]) and got["a"] == pytest.approx(0.02) and got["c"] == pytest.approx(0.02)
    assert (np.array([got["a"], got["c"]]) >= np.array([0.01, 0.02])).all()      # adjusted >= raw


def test_holm_known_values():
    holm = _load("exp_capacity_return_difference").holm
    got = holm({"a": 0.01, "b": 0.04, "c": 0.03, "d": 0.005})
    assert got == pytest.approx({"a": 0.03, "b": 0.06, "c": 0.06, "d": 0.02})


# ------------------------------------------------------------------ BH, DSR building block
def test_benjamini_hochberg_known_vector():
    p = pd.Series([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216])
    from statsmodels.stats.multitest import multipletests
    ref = multipletests(p.to_numpy(), method="fdr_bh")[1]
    assert benjamini_hochberg(p)["p_adjusted"].to_numpy() == pytest.approx(ref, abs=1e-12)


def test_expected_max_sharpe_follows_bailey_lopez_de_prado():
    from scipy.stats import norm
    g, n, sd = 0.5772156649, 64, 0.1
    ref = sd * ((1 - g) * norm.ppf(1 - 1 / n) + g * norm.ppf(1 - 1 / (n * np.e)))
    assert _expected_max_sharpe(n, sd) == pytest.approx(ref, rel=1e-12)
    assert _expected_max_sharpe(1, sd) == 0.0
    assert _expected_max_sharpe(128, sd) > _expected_max_sharpe(64, sd)


# ------------------------------------------------------------------ corrected defects (regression tests)
def test_D1_sharpe_se_is_not_smaller_than_the_iid_se_under_positive_autocorrelation():
    x = 0.04 * _ar1(6000, 0.4, 20)
    assert sharpe_se(x, 12) >= sharpe_se(x, 12, autocorr=False)


def test_D2_romano_wolf_adjusted_p_after_first_non_rejection_is_not_forced_to_one():
    rng = np.random.default_rng(30)
    X = pd.DataFrame(0.04 * rng.standard_normal((132, 4)))
    X[0] += 0.02                                          # one strong, three nulls
    res = romano_wolf(X, n_boot=400, seed=1)
    non = res.loc[~res["reject"], "p_adjusted"]
    assert len(non) == 3 and not (non == 1.0).any()      # t = -0.11 has a step-down p near 0.5, not 1.0


def test_D3_documented_not_fixed_romano_wolf_silently_drops_incomplete_months():
    """Disclosure item (policy): rows with any NaN are removed jointly, contradicting 'nothing silently dropped'."""
    rng = np.random.default_rng(31)
    X = pd.DataFrame(0.04 * rng.standard_normal((60, 3)))
    X.iloc[3, 1] = np.nan
    res = romano_wolf(X, n_boot=50, seed=1)
    assert len(res) == 3                                   # runs; the dropped month is not reported anywhere


# ---- D1 regression: reference formulas ----------------------------------------------------------
def _psi(x, periods=12):
    sd = x.std(ddof=1)
    sr = x.mean() / sd
    z = (x - x.mean()) / sd
    return np.sqrt(periods) * (z - 0.5 * sr * (z ** 2 - 1.0))


def test_D1_sharpe_se_is_the_hac_se_of_the_sharpe_influence_function():
    x = 0.04 * _ar1(132, 0.3, 40) + 0.004
    assert sharpe_se(x, 12) == pytest.approx(newey_west_se(_psi(x)), rel=1e-12)


@pytest.mark.parametrize("phi", [0.4, -0.4])
def test_D1_se_tracks_the_long_run_variance_of_an_ar1(phi):
    """Reference: for AR(1) with true SR = 0, Var(sqrt(P) mean/sd) = P (1+phi)/(1-phi) / T."""
    T = 120000
    x = 0.04 * _ar1(T, phi, 41)
    ref = np.sqrt(12 * (1 + phi) / (1 - phi) / T)
    assert sharpe_se(x, 12) == pytest.approx(ref, rel=0.08)


def test_D1_negative_autocorrelation_gives_a_smaller_se_than_iid_and_positive_a_larger():
    base = {phi: 0.04 * _ar1(20000, phi, 42) for phi in (-0.3, 0.0, 0.3)}
    se = {phi: sharpe_se(x, 12) for phi, x in base.items()}
    assert se[-0.3] < se[0.0] < se[0.3]


def test_D1_iid_normal_case_agrees_with_the_iid_formula_and_skew_is_retained():
    rng = np.random.default_rng(43)
    x = 0.004 + 0.04 * rng.standard_normal(40000)
    assert sharpe_se(x, 12) == pytest.approx(sharpe_se(x, 12, autocorr=False), rel=0.04)
    y = 0.004 + 0.04 * (rng.exponential(1.0, 40000) - 1.0)              # iid, strongly right-skewed
    assert sharpe_se(y, 12) == pytest.approx(sharpe_se(y, 12, autocorr=False), rel=0.06)
    assert sharpe_se(y, 12, autocorr=False) != pytest.approx(
        sharpe_se(y, 12, autocorr=False, higher_moments=False), rel=1e-3)


# ---- D2 regression: step-down logic -------------------------------------------------------------
def _legacy_romano_wolf_p(boot_max, t_obs, alpha=0.05):
    """The pre-2026-10-13 loop, kept here only as a reference for the equivalence test."""
    K = len(t_obs)
    order = np.argsort(-t_obs)
    p_adj = np.ones(K)
    remaining = list(order)
    prev = 0.0
    while remaining:
        k = remaining[0]
        p = max(float(np.mean(boot_max[:, remaining].max(axis=1) >= t_obs[k])), prev)
        p_adj[k] = p
        prev = p
        if p > alpha:
            for j in remaining[1:]:
                p_adj[j] = max(p, p_adj[j])
            break
        remaining = remaining[1:]
    return p_adj


def test_D2_step_down_matches_legacy_on_decisions_and_through_the_first_non_rejection():
    rng = np.random.default_rng(50)
    X = pd.DataFrame(0.04 * rng.standard_normal((132, 6)))
    X[0] += 0.02
    X[1] += 0.008
    new = romano_wolf(X, n_boot=400, seed=3)
    # rebuild the same bootstrap draws to get the legacy answer
    rng2 = np.random.default_rng(3)
    means = X.mean().to_numpy()
    ses = np.array([newey_west_se(X[c].to_numpy()) for c in X.columns])
    t_obs = means / ses
    centred = X.to_numpy() - means
    boot_max = np.empty((400, 6))
    for b in range(400):
        idx = _stationary_bootstrap_index(132, 6, rng2)
        smp = centred[idx]
        bse = np.array([newey_west_se(smp[:, k]) for k in range(6)])
        boot_max[b] = smp.mean(axis=0) / bse
    legacy = _legacy_romano_wolf_p(boot_max, t_obs)
    got = new.set_index("strategy")["p_adjusted"].reindex(range(6)).to_numpy()
    order = np.argsort(-t_obs)
    first_fail = next(i for i, k in enumerate(order) if legacy[k] > 0.05)
    for k in order[: first_fail + 1]:
        assert got[k] == pytest.approx(legacy[k], abs=1e-12)           # identical through the first failure
    assert ((got < 0.05) == (legacy < 0.05)).all()                     # identical decisions
    after = list(order[first_fail + 1:])
    assert all(got[k] <= legacy[k] + 1e-12 for k in after)             # legacy over-stated the rest
    assert any(legacy[k] == 1.0 and got[k] < 1.0 for k in after)
    gs = [got[k] for k in order]
    assert all(b >= a - 1e-12 for a, b in zip(gs, gs[1:]))             # monotone along the step-down


def test_D2_single_hypothesis_is_the_one_sided_bootstrap_p():
    rng = np.random.default_rng(51)
    X = pd.DataFrame({"a": 0.04 * rng.standard_normal(132) + 0.004})
    out = romano_wolf(X, n_boot=300, seed=1)
    assert len(out) == 1 and 0 <= out["p_adjusted"].iloc[0] <= 1
    assert bool(out["reject"].iloc[0]) == (out["p_adjusted"].iloc[0] < 0.05)


# ---- D5 regression: Hansen threshold --------------------------------------------------------------
def test_D5_threshold_is_minus_A_n_standard_errors_of_the_mean():
    from alphacomb.validation.inference import _spa_recentre
    T = 132
    A = np.sqrt(2 * np.log(np.log(T)))
    se = np.array([0.01, 0.02, 0.01, 0.01])
    dbar = np.array([-1.0 * 0.01, -(A + 0.05) * 0.02, -(A - 0.05) * 0.01, 0.003])
    g = _spa_recentre(dbar, se, T)
    assert g[0] == dbar[0]             # -1 se: not clearly inferior, centred at zero
    assert g[1] == 0.0                 # below -A_n se: clearly inferior, keeps its negative mean
    assert g[2] == dbar[2]             # just above the threshold: centred
    assert g[3] == dbar[3]             # positive: centred
    assert 1.5 < A < 2.0               # A_n = sqrt(2 log log 132) = 1.77, not 1.77/sqrt(132) = 0.15


def test_D5_end_to_end_spa_still_detects_a_real_winner_and_accepts_noise():
    rng = np.random.default_rng(52)
    bench = np.zeros(132)
    noise = pd.DataFrame(0.04 * rng.standard_normal((132, 10)))
    assert hansen_spa(bench, noise, n_boot=300, seed=0).p_value > 0.05
    win = noise.copy()
    win[3] += 0.03
    assert hansen_spa(bench, win, n_boot=300, seed=0).p_value < 0.05


# ---- CI convention: studentised interval is reported beside the percentile one -------------------
def test_CI_studentised_interval_matches_an_independent_reconstruction():
    d = 0.004 + 0.01 * _ar1(132, 0.3, 61)
    r = mean_difference_test(d, np.zeros(132), n_boot=400, seed=4)
    T = 132
    stat, se = 12 * d.mean(), 12 * newey_west_se(d)
    gen = np.random.default_rng(4)
    ts = []
    for _ in range(400):
        db = d[_stationary_bootstrap_index(T, 6, gen)]
        ts.append((12 * db.mean() - stat) / (12 * newey_west_se(db)))
    q = np.percentile(np.array(ts), [2.5, 97.5])
    assert r.detail["ci95_stud_low"] == pytest.approx(stat - q[1] * se, rel=1e-10)
    assert r.detail["ci95_stud_high"] == pytest.approx(stat - q[0] * se, rel=1e-10)
    assert r.detail["ci95_low"] <= r.statistic <= r.detail["ci95_high"]       # percentile keys unchanged


def test_CI_sharpe_difference_reports_both_intervals():
    rng = np.random.default_rng(62)
    a = 0.005 + 0.04 * rng.standard_normal(132)
    b = 0.003 + 0.04 * rng.standard_normal(132)
    r = sharpe_difference_test(a, b, n_boot=400, seed=2)
    assert r.detail["ci95_stud_low"] < r.detail["ci95_stud_high"]
    assert r.detail["ci95_low"] < r.detail["ci95_high"]
