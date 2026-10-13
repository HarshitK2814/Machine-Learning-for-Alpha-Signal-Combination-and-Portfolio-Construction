"""Phase B inference audit: synthetic simulations only. Reads NO historical data of any kind.

Every statistic comes from a stated data-generating process (DGP) with a fixed seed. Monte Carlo
uncertainty is reported as the binomial standard error sqrt(p(1-p)/N) for rates and the sampling
sd/sqrt(N) for ratios. Finite simulations do not prove universal validity.

Usage:  python tools/audit_inference_simulations.py [--scale 1.0] [--out results/inference_audit_2026-10-13]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from alphacomb.validation import inference as inf  # noqa: E402
from alphacomb.validation.inference import (_stationary_bootstrap_index, newey_west_se,  # noqa: E402
                                            sharpe_difference_test, mean_difference_test, sharpe_se)

PERIODS = 12


def ar1_t(T, phi, rng, df=5, size=None):
    """AR(1) with unit-variance Student-t(df) innovations scaled to unit marginal variance."""
    n = T + 100
    shape = (n,) if size is None else (n, size)
    e = rng.standard_t(df, shape) * np.sqrt((df - 2) / df)
    x = np.zeros(shape)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + e[t]
    x = x[100:] * np.sqrt(1 - phi ** 2)
    return x


def rate(hits, n):
    p = float(np.mean(hits))
    return {"rate": p, "mc_se": float(np.sqrt(max(p * (1 - p), 1e-12) / n)), "n": int(n)}


def sharpe_se_proposed(r, periods=PERIODS):
    """Proposed replacement for sharpe_se: HAC (Newey-West) SE of the Sharpe influence function.

    Same estimator sharpe_difference_test already uses for a difference; for a single series it is
    the SE of the naively annualised Sharpe ratio sqrt(P) * mean / sd, and it contains the
    Mertens skewness/kurtosis terms automatically through the z^2 term.
    """
    r = np.asarray(r, float)
    r = r[np.isfinite(r)]
    return float(newey_west_se(_infl(r, _sr(r))))


def s_proposed_se(scale):
    out = {}
    reps = int(2000 * scale)
    T = 132
    for phi in (-0.2, 0.0, 0.2, 0.4):
        rng = np.random.default_rng(100 + int(phi * 10))                 # same draws as s_standard_errors
        naive, se_new, t_rej = [], [], []
        for _ in range(reps):
            x = 0.04 * ar1_t(T, phi, rng)
            sr = _sr(x)
            naive.append(sr)
            se_new.append(sharpe_se_proposed(x))
            t_rej.append(abs(sr / se_new[-1]) > 1.96)
        out[f"phi={phi}"] = {"ratio_proposed_se_over_empirical_sd": float(np.mean(se_new) / np.std(naive, ddof=1)),
                             "sharpe_test_size_at_5pct_with_proposed_se": rate(t_rej, reps)}
    return out


# ---------------------------------------------------------------------------- S3 / S4: standard errors
def s_standard_errors(scale):
    out = {}
    reps = int(2000 * scale)
    T = 132
    for phi in (-0.2, 0.0, 0.2, 0.4):
        rng = np.random.default_rng(100 + int(phi * 10))
        naive, se_code, se_noac, nw, mean_hat, t_rej = [], [], [], [], [], []
        for _ in range(reps):
            x = 0.0 + 0.04 * ar1_t(T, phi, rng)                       # true SR = 0
            sr = np.sqrt(PERIODS) * x.mean() / x.std(ddof=1)
            naive.append(sr)
            se_code.append(sharpe_se(x, PERIODS))
            se_noac.append(sharpe_se(x, PERIODS, autocorr=False))
            nw.append(newey_west_se(x))
            mean_hat.append(x.mean())
            t_rej.append(abs(sr / se_code[-1]) > 1.96)
        emp_sr = float(np.std(naive, ddof=1))
        out[f"phi={phi}"] = {
            "empirical_sd_of_annualised_naive_SR": emp_sr,
            "mean_sharpe_se_code": float(np.mean(se_code)),
            "ratio_code_se_over_empirical_sd": float(np.mean(se_code) / emp_sr),
            "ratio_iid_formula_over_empirical_sd": float(np.mean(se_noac) / emp_sr),
            "sharpe_test_size_at_5pct (true SR=0)": rate(t_rej, reps),
            "newey_west_se_over_empirical_sd_of_mean": float(np.mean(nw) / np.std(mean_hat, ddof=1)),
        }
    return out


# ---------------------------------------------------------------------------- bootstrap re-implementations
def _sr(x):
    s = x.std(ddof=1)
    return float(x.mean() / s * np.sqrt(PERIODS)) if s > 0 else np.nan


def _infl(x, sr):
    mu, sg = x.mean(), x.std(ddof=1)
    z = (x - mu) / sg
    return np.sqrt(PERIODS) * (z - 0.5 * sr / np.sqrt(PERIODS) * (z ** 2 - 1.0))


def lw_parts(a, b, B, seed, block=6):
    """The exact computation inside sharpe_difference_test, returning the pieces."""
    T = a.size
    sa, sb = _sr(a), _sr(b)
    diff = sa - sb
    se = float(newey_west_se(_infl(a, sa) - _infl(b, sb)))
    stud = diff / se
    rng = np.random.default_rng(seed)
    bd = np.empty(B)
    bs = np.empty(B)
    for i in range(B):
        idx = _stationary_bootstrap_index(T, block, rng)
        ab, bb = a[idx], b[idx]
        x, y = _sr(ab), _sr(bb)
        d = x - y
        bd[i] = d
        s2 = float(newey_west_se(_infl(ab, x) - _infl(bb, y)))
        bs[i] = (d - diff) / s2 if s2 > 0 else np.nan
    return diff, se, stud, bd, bs


def mean_parts(d, B, seed, block=6):
    T = d.size
    stat = PERIODS * d.mean()
    se = PERIODS * newey_west_se(d)
    stud = stat / se
    rng = np.random.default_rng(seed)
    boot = np.empty(B)
    bs = np.empty(B)
    for i in range(B):
        db = d[_stationary_bootstrap_index(T, block, rng)]
        boot[i] = PERIODS * db.mean()
        s = PERIODS * newey_west_se(db)
        bs[i] = (boot[i] - stat) / s if s > 0 else np.nan
    return stat, se, stud, boot, bs


def ci_pair(stat, se, boot, bs, true):
    pct = np.percentile(boot, [2.5, 97.5])
    q = np.nanpercentile(bs, [2.5, 97.5])
    stu = (stat - q[1] * se, stat - q[0] * se)
    return (pct[0] <= true <= pct[1]), (stu[0] <= true <= stu[1])


def s_sharpe_difference(scale):
    out = {}
    B = 399
    reps = int(400 * scale)
    cases = {
        "T=132,phi=0,corr=.9,equal vol": dict(T=132, phi=0.0, rho=0.9, vol_b=1.0),
        "T=132,phi=.3,corr=.9,equal vol": dict(T=132, phi=0.3, rho=0.9, vol_b=1.0),
        "T=132,phi=.3,corr=.9,vol_b=.5 (equal Sharpe)": dict(T=132, phi=0.3, rho=0.9, vol_b=0.5),
        "T=60,phi=.3,corr=.9,equal vol": dict(T=60, phi=0.3, rho=0.9, vol_b=1.0),
    }
    for name, c in cases.items():
        rng = np.random.default_rng(7)
        rej, cov_pct, cov_stu, p_vals = [], [], [], []
        t0 = time.time()
        for r in range(reps):
            z = ar1_t(c["T"], c["phi"], rng, size=2)
            common, idio = z[:, 0], z[:, 1]
            ea = 0.04 * common
            eb = 0.04 * c["vol_b"] * (c["rho"] * common + np.sqrt(1 - c["rho"] ** 2) * idio)
            mu = 0.004                                                   # SR_ann ~ 0.35 for both
            a, b = mu + ea, mu * c["vol_b"] + eb                          # equal Sharpe by construction
            res = sharpe_difference_test(a, b, n_boot=B, seed=r)
            rej.append(res.p_value < 0.05)
            p_vals.append(res.p_value)
            diff, se, stud, bd, bs = lw_parts(a, b, B, r)
            true = np.sqrt(PERIODS) * mu / (0.04 * 1.0) - np.sqrt(PERIODS) * (mu * c["vol_b"]) / (0.04 * c["vol_b"])
            cp, cs = ci_pair(diff, se, bd, bs, true)
            cov_pct.append(cp)
            cov_stu.append(cs)
            if r == 0:
                fin = np.isfinite(bs)
                assert abs(res.p_value - float((np.abs(bs[fin]) >= abs(stud)).mean())) < 1e-12, "re-implementation differs"
                tq = np.percentile(bs[fin], [2.5, 97.5])
                assert abs(res.detail["ci95_stud_low"] - (diff - tq[1] * se)) < 1e-10, "studentised CI differs"
        out[name] = {"reps": reps, "n_boot": B,
                     "size_at_5pct": rate(rej, reps),
                     "coverage_95_percentile_CI(code)": rate(cov_pct, reps),
                     "coverage_95_studentised_CI(proposed)": rate(cov_stu, reps),
                     "seconds": round(time.time() - t0, 1)}
    return out


def s_mean_difference(scale):
    out = {}
    B = 399
    reps = int(400 * scale)
    for name, (T, phi) in {"T=132,phi=0": (132, 0.0), "T=132,phi=.3": (132, 0.3), "T=60,phi=.3": (60, 0.3)}.items():
        rng = np.random.default_rng(11)
        rej, cp_l, cs_l = [], [], []
        for r in range(reps):
            d = 0.01 * ar1_t(T, phi, rng)                                 # true mean difference 0
            res = mean_difference_test(d, np.zeros(T), n_boot=B, seed=r)
            rej.append(res.p_value < 0.05)
            stat, se, stud, boot, bs = mean_parts(d, B, r)
            cp, cs = ci_pair(stat, se, boot, bs, 0.0)
            if r == 0:
                assert abs(res.detail["ci95_stud_low"] - (stat - np.nanpercentile(bs, 97.5) * se)) < 1e-10
            cp_l.append(cp)
            cs_l.append(cs)
        out[name] = {"reps": reps, "size_at_5pct": rate(rej, reps),
                     "coverage_95_percentile_CI(code)": rate(cp_l, reps),
                     "coverage_95_studentised_CI(proposed)": rate(cs_l, reps)}
    return out


# ---------------------------------------------------------------------------- SPA and Romano-Wolf
def spa_patched(benchmark, candidates, n_boot, block, seed, legacy=False):
    """hansen_spa re-implemented. legacy=True reproduces the pre-2026-10-13 threshold (extra 1/sqrt(T));
    legacy=False is Hansen's units, A_n * se_of_mean, and must equal the library function."""
    rng = np.random.default_rng(seed)
    base = np.asarray(benchmark, float)
    C = candidates
    d = C.to_numpy() - base[:, None]
    T, K = d.shape
    dbar = d.mean(axis=0)
    ses = np.array([newey_west_se(d[:, k]) for k in range(K)])
    ses = np.where(ses > 0, ses, np.inf)
    t_obs = float(np.max(np.sqrt(T) * dbar / ses))
    threshold = -np.sqrt(2.0 * np.log(np.log(max(T, 3)))) * ses / (np.sqrt(T) if legacy else 1.0)
    g = np.where(dbar > threshold, dbar, 0.0)
    boot = np.empty(n_boot)
    for b in range(n_boot):
        idx = _stationary_bootstrap_index(T, block, rng)
        sample = d[idx] - g
        sbar = sample.mean(axis=0)
        sse = np.array([newey_west_se(sample[:, k]) for k in range(K)])
        sse = np.where(sse > 0, sse, np.inf)
        boot[b] = float(np.max(np.sqrt(T) * sbar / sse))
    return float(np.mean(boot >= t_obs))


def s_spa(scale):
    import pandas as pd
    out = {}
    T, K, B = 132, 20, 299
    reps = int(300 * scale)
    sd = 0.04
    se_mean = sd / np.sqrt(T)
    for name, mus in {"1 candidate at 0, 19 at -1 se": [0.0] + [-1 * se_mean] * 19,
                      "all 20 at 0": [0.0] * 20,
                      "1 at 0, 19 at -3 se": [0.0] + [-3 * se_mean] * 19}.items():
        rng = np.random.default_rng(21)
        rej_code, rej_fix = [], []
        for r in range(reps):
            bench = np.zeros(T)
            cand = pd.DataFrame(np.array(mus) + sd * ar1_t(T, 0.0, rng, size=K))
            p_code = inf.hansen_spa(bench, cand, n_boot=B, seed=r).p_value
            p_leg = spa_patched(bench, cand, B, 6, r, legacy=True)
            if r < 3:
                assert abs(p_code - spa_patched(bench, cand, B, 6, r)) < 1e-12, "library differs from reference"
            rej_code.append(p_code < 0.05)
            rej_fix.append(p_leg < 0.05)
        out[name] = {"reps": reps, "rejection_rate_corrected_library (H0 true)": rate(rej_code, reps),
                     "rejection_rate_legacy_threshold": rate(rej_fix, reps)}
    return out


def s_romano_wolf(scale):
    import pandas as pd
    T, K, B = 132, 8, 299
    reps = int(300 * scale)
    rng = np.random.default_rng(31)
    any_rej, stuck_one, nonrej = [], 0, 0
    for r in range(reps):
        z = ar1_t(T, 0.2, rng, size=K + 1)
        X = 0.04 * (np.sqrt(0.5) * z[:, [0]] + np.sqrt(0.5) * z[:, 1:])      # corr .5, mean 0
        res = inf.romano_wolf(pd.DataFrame(X), n_boot=B, seed=r)
        any_rej.append(bool(res["reject"].any()))
        ne = res.loc[~res["reject"], "p_adjusted"]
        nonrej += len(ne)
        stuck_one += int((ne == 1.0).sum())
    return {"reps": reps, "familywise_rejection_rate (all nulls true, K=8)": rate(any_rej, reps),
            "share_of_non_rejected_hypotheses_with_reported_p_adjusted_exactly_1.0": stuck_one / max(nonrej, 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--out", default="results/inference_audit_2026-10-13")
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = {"proposed_se": s_proposed_se, "standard_errors": s_standard_errors, "sharpe_difference": s_sharpe_difference,
            "mean_difference": s_mean_difference, "hansen_spa": s_spa, "romano_wolf": s_romano_wolf}
    for k, f in jobs.items():
        if a.only and k not in a.only:
            continue
        t0 = time.time()
        res = f(a.scale)
        (out / f"sim_{k}.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"[{k}] done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
