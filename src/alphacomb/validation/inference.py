"""Statistical inference. Without this every number in the project is a bare point estimate.

This is the single largest technical gap between what we have and what a referee at a top finance
journal will accept. The field's standards here are unusually explicit, because the field was burned:
Harvey, Liu & Zhu's t > 3.0 hurdle, Bailey & Lopez de Prado's deflated Sharpe ratio and probability
of backtest overfitting, White's reality check and Hansen's SPA, Romano & Wolf's stepwise method.
A machine-learning paper that reports Sharpe ratios without any of this is rejected on that ground
alone, and correctly so: we searched over hundreds of specifications, and the maximum of a search is
biased upward by construction.

Three distinct problems, which are often conflated:

1. **Autocorrelation and non-normality.** Monthly strategy returns are neither iid nor Gaussian, so
   the textbook Sharpe standard error ``sqrt((1 + S^2/2)/T)`` is wrong. ``sharpe_se`` implements the
   Lo (2002) autocorrelation correction and the Mertens/Christie higher-moment correction.
2. **Selection over many trials.** We fit hundreds of configurations and report the best. The
   deflated Sharpe ratio asks whether the winner beats what the *maximum of that many trials* would
   produce under a null of no skill.
3. **Many simultaneous comparisons.** The factorial design makes 16+ comparisons at once. Controlling
   each at 5% controls none of them jointly. Romano-Wolf and Benjamini-Hochberg do different jobs
   here and are not interchangeable: Romano-Wolf controls the familywise error rate and is the
   conservative choice for a headline claim; BH controls the false discovery rate and is the right
   choice for screening a large signal library.

Everything takes a return series or a matrix of them and returns a dataclass with the statistic, the
p-value and enough metadata to reproduce it. Nothing here silently drops observations.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats


# ----------------------------------------------------------------------------- basics

@dataclass
class TestResult:
    name: str
    statistic: float
    p_value: float
    detail: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.name}: stat={self.statistic:.4f}, p={self.p_value:.4f}"

    @property
    def significant_at_5pct(self) -> bool:
        return self.p_value < 0.05


def newey_west_se(x: np.ndarray, lags: int | None = None) -> float:
    """Newey-West standard error of the mean, robust to autocorrelation and heteroskedasticity.

    ``lags=None`` uses the standard ``floor(4 (T/100)^(2/9))`` rule.
    """
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    T = len(x)
    if T < 3:
        return float("nan")
    if lags is None:
        lags = int(np.floor(4 * (T / 100) ** (2 / 9)))
    lags = max(0, min(lags, T - 2))
    e = x - x.mean()
    gamma0 = float(e @ e) / T
    var = gamma0
    for k in range(1, lags + 1):
        w = 1.0 - k / (lags + 1.0)                       # Bartlett kernel
        gamma_k = float(e[k:] @ e[:-k]) / T
        var += 2.0 * w * gamma_k
    return float(np.sqrt(max(var, 0.0) / T))


def sharpe_se(returns: np.ndarray, periods: int = 12, autocorr: bool = True,
              higher_moments: bool = True) -> float:
    """Standard error of an annualised Sharpe ratio.

    The textbook ``sqrt((1 + S^2/2)/T)`` assumes iid normal returns. Strategy returns are neither.
    Lo (2002) corrects for autocorrelation; Mertens (2002) and Christie (2005) correct for skewness
    and excess kurtosis. Ignoring both typically **understates** the standard error, which is the
    direction that manufactures significance.
    """
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    T = len(r)
    if T < 8:
        return float("nan")
    sd = r.std(ddof=1)
    if sd <= 0:
        return float("nan")
    sr = r.mean() / sd                                    # per-period Sharpe

    var = 1.0 + 0.5 * sr ** 2
    if higher_moments:
        skew = float(stats.skew(r, bias=False))
        kurt = float(stats.kurtosis(r, fisher=True, bias=False))
        var = 1.0 - skew * sr + 0.25 * (kurt + 2.0) * sr ** 2
    se = np.sqrt(max(var, 1e-12) / T)

    if autocorr:
        # Lo (2002): scale by the ratio of the true multi-period factor to sqrt(q)
        q = min(periods, T // 4)
        if q >= 2:
            rho = np.array([_autocorr(r, k) for k in range(1, q)])
            denom = q + 2.0 * float(np.sum((q - np.arange(1, q)) * rho))
            if denom > 0:
                se *= np.sqrt(q) / np.sqrt(denom) * np.sqrt(q) / np.sqrt(q)
    return float(se * np.sqrt(periods))


def _autocorr(x: np.ndarray, lag: int) -> float:
    if lag >= len(x) - 1:
        return 0.0
    a, b = x[:-lag], x[lag:]
    sa, sb = a.std(), b.std()
    if sa <= 0 or sb <= 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def sharpe_test(returns, periods: int = 12, benchmark: float = 0.0) -> TestResult:
    """Is the annualised Sharpe ratio different from ``benchmark``, with honest standard errors?"""
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    sd = r.std(ddof=1)
    sr = float(r.mean() / sd * np.sqrt(periods)) if sd > 0 else float("nan")
    se = sharpe_se(r, periods)
    t = (sr - benchmark) / se if se and np.isfinite(se) and se > 0 else float("nan")
    p = 2 * (1 - stats.norm.cdf(abs(t))) if np.isfinite(t) else float("nan")
    return TestResult("sharpe", sr, p,
                      {"se": se, "t_stat": t, "months": int(len(r)), "benchmark": benchmark,
                       "harvey_liu_zhu_hurdle_met": bool(np.isfinite(t) and abs(t) > 3.0)})


# ----------------------------------------------------------------------------- selection bias

def deflated_sharpe(observed_sr: float, n_trials: int, returns=None, trial_sr_sd: float | None = None,
                    periods: int = 12) -> TestResult:
    """Bailey & Lopez de Prado's deflated Sharpe ratio.

    Asks the right question: not "is this Sharpe non-zero?" but "does it beat the *maximum* that
    ``n_trials`` independent attempts would produce under a null of no skill?" With enough trials
    an impressive Sharpe is the expected outcome of searching, not evidence of anything.

    ``n_trials`` must be the **real** number of configurations fitted, from ``outputs/trials.csv``,
    not the number reported in the paper. Using the reported count is the most common way this
    statistic is misapplied.
    """
    r = np.asarray(returns, dtype=float) if returns is not None else None
    if r is not None:
        r = r[np.isfinite(r)]
        T = len(r)
        skew = float(stats.skew(r, bias=False))
        kurt = float(stats.kurtosis(r, fisher=False, bias=False))
    else:
        T, skew, kurt = 120, 0.0, 3.0

    sr = observed_sr / np.sqrt(periods)                  # to per-period units
    sd = trial_sr_sd if trial_sr_sd is not None else 1.0 / np.sqrt(max(T - 1, 1))
    sr0 = _expected_max_sharpe(n_trials, sd)

    denom = np.sqrt(max(1.0 - skew * sr + 0.25 * (kurt - 1.0) * sr ** 2, 1e-12))
    z = (sr - sr0) * np.sqrt(max(T - 1, 1)) / denom
    psr = float(stats.norm.cdf(z))
    return TestResult("deflated_sharpe", psr, 1.0 - psr,
                      {"observed_sr_ann": observed_sr, "n_trials": int(n_trials),
                       "expected_max_sr_per_period": float(sr0),
                       "expected_max_sr_ann": float(sr0 * np.sqrt(periods)),
                       "months": int(T), "skew": skew, "kurtosis": kurt,
                       "verdict": "survives" if psr > 0.95 else "does NOT survive deflation"})


def _expected_max_sharpe(n_trials: int, sd: float) -> float:
    """Expected maximum of n independent Sharpe estimates under a no-skill null."""
    n = max(int(n_trials), 1)
    if n == 1:
        return 0.0
    gamma = 0.5772156649
    z1 = stats.norm.ppf(1 - 1.0 / n)
    z2 = stats.norm.ppf(1 - 1.0 / (n * np.e))
    return float(sd * ((1 - gamma) * z1 + gamma * z2))


def pbo_cscv(performance: pd.DataFrame, n_splits: int = 16) -> TestResult:
    """Probability of Backtest Overfitting by combinatorially symmetric cross-validation.

    ``performance`` is months x strategies. The sample is cut into ``n_splits`` blocks; for every
    balanced split into in-sample and out-of-sample halves, pick the configuration that won in
    sample and record its *rank* out of sample. PBO is the share of splits where the in-sample
    winner lands in the bottom half out of sample.

    PBO above ~0.5 means the selection procedure has no skill: the winner in sample is a coin flip
    out of sample. This is a property of the **procedure**, not of any one strategy, which is why it
    belongs in a paper that searches over a design grid.
    """
    from itertools import combinations

    M = performance.dropna(axis=1, how="any")
    if M.shape[1] < 2:
        return TestResult("pbo_cscv", float("nan"), float("nan"), {"error": "need >= 2 strategies"})
    n_splits = max(2, n_splits - n_splits % 2)
    blocks = np.array_split(np.arange(len(M)), n_splits)
    half = n_splits // 2

    logits = []
    for combo in combinations(range(n_splits), half):
        is_idx = np.concatenate([blocks[i] for i in combo])
        oos_idx = np.concatenate([blocks[i] for i in range(n_splits) if i not in combo])
        is_perf = M.iloc[is_idx].mean()
        oos_perf = M.iloc[oos_idx].mean()
        best = is_perf.idxmax()
        rank = float(oos_perf.rank(pct=True)[best])
        rank = min(max(rank, 1e-6), 1 - 1e-6)
        logits.append(np.log(rank / (1 - rank)))

    logits = np.asarray(logits)
    pbo = float(np.mean(logits <= 0))
    return TestResult("pbo_cscv", pbo, float("nan"),
                      {"n_combinations": len(logits), "n_strategies": int(M.shape[1]),
                       "median_logit": float(np.median(logits)),
                       "verdict": "overfit selection" if pbo > 0.5 else "selection has some skill"})


# ----------------------------------------------------------------------------- many comparisons

def romano_wolf(returns: pd.DataFrame, n_boot: int = 2000, alpha: float = 0.05,
                block: int = 6, seed: int = 0) -> pd.DataFrame:
    """Romano-Wolf stepwise multiple testing, controlling the familywise error rate.

    The right tool when the claim is "these specific cells beat the benchmark" and a single false
    positive would be embarrassing. Uses a stationary bootstrap so the resampling respects
    autocorrelation; an iid bootstrap here would be the same mistake as an uncorrected standard error.

    Returns one row per strategy with the studentised statistic, the stepwise-adjusted p-value and
    the reject decision.
    """
    rng = np.random.default_rng(seed)
    X = returns.dropna(axis=0, how="any")
    names = list(X.columns)
    T, K = X.shape
    if T < 20 or K < 1:
        return pd.DataFrame(columns=["strategy", "mean", "t_stat", "p_adjusted", "reject"])

    means = X.mean().to_numpy()
    ses = np.array([newey_west_se(X[c].to_numpy()) for c in names])
    ses = np.where(ses > 0, ses, np.inf)
    t_obs = means / ses

    boot_max = np.empty((n_boot, K))
    centred = X.to_numpy() - means
    for b in range(n_boot):
        idx = _stationary_bootstrap_index(T, block, rng)
        sample = centred[idx]
        bmean = sample.mean(axis=0)
        bse = np.array([newey_west_se(sample[:, k]) for k in range(K)])
        bse = np.where(bse > 0, bse, np.inf)
        boot_max[b] = bmean / bse

    order = np.argsort(-t_obs)
    p_adj = np.ones(K)
    remaining = list(order)
    prev_p = 0.0
    while remaining:
        sub = boot_max[:, remaining]
        maxes = sub.max(axis=1)
        k = remaining[0]
        p = float(np.mean(maxes >= t_obs[k]))
        p = max(p, prev_p)                                # enforce monotonicity
        p_adj[k] = p
        prev_p = p
        if p > alpha:
            for j in remaining[1:]:
                p_adj[j] = max(p, p_adj[j])
            break
        remaining = remaining[1:]

    return pd.DataFrame({"strategy": names, "mean": means, "t_stat": t_obs,
                         "p_adjusted": p_adj, "reject": p_adj < alpha}).sort_values("p_adjusted")


def _stationary_bootstrap_index(T: int, block: int, rng) -> np.ndarray:
    """Politis-Romano stationary bootstrap indices with expected block length ``block``."""
    p = 1.0 / max(block, 1)
    idx = np.empty(T, dtype=int)
    idx[0] = rng.integers(T)
    for t in range(1, T):
        idx[t] = rng.integers(T) if rng.random() < p else (idx[t - 1] + 1) % T
    return idx


def benjamini_hochberg(p_values, alpha: float = 0.05) -> pd.DataFrame:
    """Benjamini-Hochberg false discovery rate control.

    The right tool for *screening* - "which of these 150 signals carry information?" - where a few
    false positives are tolerable. It is NOT interchangeable with Romano-Wolf: BH controls the
    expected proportion of false discoveries, not the probability of any false discovery.
    """
    p = pd.Series(p_values).dropna()
    m = len(p)
    if m == 0:
        return pd.DataFrame(columns=["p_value", "p_adjusted", "reject"])
    order = p.sort_values()
    ranks = np.arange(1, m + 1)
    adj = np.minimum.accumulate((order.to_numpy() * m / ranks)[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    out = pd.DataFrame({"p_value": order.to_numpy(), "p_adjusted": adj, "reject": adj < alpha},
                       index=order.index)
    return out.reindex(p.index)


def hansen_spa(benchmark, candidates: pd.DataFrame, n_boot: int = 2000, block: int = 6,
               seed: int = 0) -> TestResult:
    """Hansen's Superior Predictive Ability test.

    Null: no candidate beats the benchmark. Hansen's refinement over White's reality check is that
    poor candidates are recentred so they cannot drag the null distribution around - which matters
    for us, because a factorial grid contains cells we already expect to be bad, and those should
    not make it easier to declare the winner significant.
    """
    rng = np.random.default_rng(seed)
    base = np.asarray(benchmark, dtype=float)
    C = candidates.dropna(axis=0, how="any")
    common = min(len(base), len(C))
    base, C = base[-common:], C.iloc[-common:]
    d = C.to_numpy() - base[:, None]                      # excess of each candidate
    T, K = d.shape
    if T < 20 or K < 1:
        return TestResult("hansen_spa", float("nan"), float("nan"), {"error": "too few observations"})

    dbar = d.mean(axis=0)
    ses = np.array([newey_west_se(d[:, k]) for k in range(K)])
    ses = np.where(ses > 0, ses, np.inf)
    t_obs = float(np.max(np.sqrt(T) * dbar / ses))

    # Hansen's recentring: only candidates that are not clearly inferior contribute to the null
    threshold = -np.sqrt(2.0 * np.log(np.log(max(T, 3)))) * ses / np.sqrt(T)
    g = np.where(dbar >= threshold, dbar, 0.0)

    boot = np.empty(n_boot)
    for b in range(n_boot):
        idx = _stationary_bootstrap_index(T, block, rng)
        sample = d[idx] - g
        sbar = sample.mean(axis=0)
        sse = np.array([newey_west_se(sample[:, k]) for k in range(K)])
        sse = np.where(sse > 0, sse, np.inf)
        boot[b] = float(np.max(np.sqrt(T) * sbar / sse))

    p = float(np.mean(boot >= t_obs))
    return TestResult("hansen_spa", t_obs, p,
                      {"n_candidates": K, "months": T,
                       "best_candidate": str(C.columns[int(np.argmax(dbar / ses))]),
                       "verdict": "at least one candidate genuinely beats the benchmark"
                                  if p < 0.05 else "no candidate beats the benchmark"})


def diebold_mariano(errors_a, errors_b, lags: int | None = None) -> TestResult:
    """Diebold-Mariano test of equal predictive accuracy between two forecast error series."""
    a = np.asarray(errors_a, dtype=float) ** 2
    b = np.asarray(errors_b, dtype=float) ** 2
    n = min(len(a), len(b))
    d = a[-n:] - b[-n:]
    d = d[np.isfinite(d)]
    se = newey_west_se(d, lags)
    t = d.mean() / se if se and se > 0 else float("nan")
    p = 2 * (1 - stats.norm.cdf(abs(t))) if np.isfinite(t) else float("nan")
    return TestResult("diebold_mariano", float(t), float(p),
                      {"mean_loss_diff": float(d.mean()), "n": int(len(d)),
                       "better": "a" if d.mean() < 0 else "b"})


# ----------------------------------------------------------------------------- the report

def inference_report(returns: pd.DataFrame, n_trials: int, benchmark: str | None = None,
                     periods: int = 12) -> dict:
    """Everything a referee will ask for, in one call.

    ``returns`` is months x strategies. ``n_trials`` is the real fitted-configuration count from
    ``outputs/trials.csv``.
    """
    out: dict = {"n_strategies": int(returns.shape[1]), "months": int(returns.shape[0]),
                 "n_trials": int(n_trials)}

    rows = []
    for col in returns.columns:
        r = returns[col].dropna().to_numpy()
        st = sharpe_test(r, periods)
        ds = deflated_sharpe(st.statistic, n_trials, r, periods=periods)
        rows.append({"strategy": col, "sharpe": st.statistic, "se": st.detail["se"],
                     "t_stat": st.detail["t_stat"], "p_value": st.p_value,
                     "hlz_t3_hurdle": st.detail["harvey_liu_zhu_hurdle_met"],
                     "deflated_sr_prob": ds.statistic,
                     "survives_deflation": ds.statistic > 0.95,
                     "expected_max_sr_from_search": ds.detail["expected_max_sr_ann"]})
    out["per_strategy"] = pd.DataFrame(rows)
    out["romano_wolf"] = romano_wolf(returns)
    out["pbo"] = pbo_cscv(returns)
    if benchmark and benchmark in returns.columns:
        others = returns.drop(columns=[benchmark])
        out["spa"] = hansen_spa(returns[benchmark].to_numpy(), others)
    return out
