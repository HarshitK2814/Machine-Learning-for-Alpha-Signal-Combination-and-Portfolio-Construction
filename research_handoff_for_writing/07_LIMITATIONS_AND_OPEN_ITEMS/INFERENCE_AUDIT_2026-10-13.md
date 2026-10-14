# Phase B: internal inference audit (researcher-led)

**Date:** 2026-10-13. **Status:** findings (sections 1-5) and corrections applied the same day (section 6). No frozen result, committed result table or historical protocol was changed, and no historical statistic has been updated.
This is an internal validation by the project's own author. It is **not** external statistical sign-off and no
approval is claimed. No historical panel or return outcome was loaded; every number below comes from synthetic
data-generating processes (DGPs) or from the aggregate columns already present in committed result tables.

Evidence files: `tests/validation/test_inference_audit.py` (originally 30 tests with 2 strict-xfail documenting the defects; the markers were removed once the corrected assertions passed, see section 6),
`tools/audit_inference_simulations.py` (seeded simulations), `results/inference_audit_2026-10-13/sim_*.json` (raw output).

## 1. Verdicts

| # | Item (file::function) | Reference definition | Verdict |
|---|---|---|---|
| 1 | `sharpe_difference_test` influence-function annualisation | `IF_t = sqrt(P)[z_t - (SR_per/2)(z_t^2 - 1)]`, SE = Newey-West SE of the mean of `IF_a - IF_b`; for iid normals `Var(SR_ann) = P(1+SR_per^2/2)/T` | **Correct.** The `sqrt(P)` placement is right (analytic check within 6% at T=40,000; no factor-`sqrt(12)` error). Closes the "wrong by sqrt(12)" worry in handoff 21. |
| 2 | `newey_west_se` | Bartlett HAC SE of the mean, lags `floor(4(T/100)^(2/9))`, no small-sample correction | **Correct.** Equals statsmodels `HAC(maxlags=L, use_correction=False)` to 1e-10 for L in {0,1,4,8}; lag rule gives 4 at T=132. Slightly small in finite samples (SE/true sd 0.88 at phi=.4, 0.94 at .2, 0.99 at 0, 1.03 at -.2, T=132). Disclose. |
| 3 | `_stationary_bootstrap_index` | Politis-Romano: uniform start, new block w.p. `1/block`, circular | **Correct.** Indices in range and circular; block-break rate 0.1661 vs 0.1653 expected; start index ~uniform. No missing-value handling inside (callers drop pairs first). |
| 4 | `sharpe_difference_test` / `mean_difference_test` studentised bootstrap p | Ledoit-Wolf: `p = P*(|t*| >= |t|)`, `t* = (d* - d)/se*` | **Correct and adequately sized at T=132** (rejection 5.5-6.2% at nominal 5%, Monte Carlo se 1.1-1.2 pts; paired, corr .9, phi up to .3, t(5) innovations). **Oversized at T=60** (8.7-9.0%, se 1.4 pts): disclose for short subsamples. Pairing is preserved (paired SE < 0.3x the shuffled-pair SE in test). |
| 5 | Confidence intervals of both tests (`ci95_low/high`) | Studentised interval `d - q_{.975}(t*) se`, `d - q_{.025}(t*) se` pairs with a studentised p | **Methodological choice that needs disclosure** (see D4). Code reports the *percentile* interval of the uncentred bootstrap statistic, the p-value is studentised. Coverage is slightly worse than the studentised interval, and the two disagree on significance for 2 of 35 solvent Tier B rungs. |
| 6 | `sharpe_se` (autocorrelation branch) | SE of the naively annualised `sqrt(P) mean/sd` must rise with positive autocorrelation | **VERIFIED DEFECT D1** |
| 7 | `romano_wolf` | Romano-Wolf step-down on null-centred, studentised, jointly resampled statistics | **Decisions correct** (FWER 6.0%, se 1.4 pts, 8 correlated null cells). **VERIFIED REPORTING DEFECT D2** in the adjusted p-values. Silent joint row-drop (D3). |
| 8 | `hansen_spa` | Hansen (2005): recentre candidates with `sqrt(n) dbar/omega > -sqrt(2 loglog n)` | **VERIFIED DEVIATION D5** (threshold units). Effect on the one reported SPA is directionally safe (below). |
| 9 | Holm (five local copies in `tools/`) | Step-down `max_i (m-i+1) p_(i)`, capped at 1, running max | **Correct and identical in all five copies**; equals statsmodels `holm` on ties and extreme vectors; NaN p-values are excluded from the family. Disclosure only (D6). |
| 10 | `benjamini_hochberg`, `_expected_max_sharpe` | BH step-up; Bailey-Lopez de Prado expected maximum | **Correct** (match statsmodels / the published formula). `deflated_sharpe` default `trial_sr_sd = 1/sqrt(T-1)` is the sampling sd of one Sharpe, not the dispersion across trials; with correlated trials this overstates the hurdle, i.e. conservative. Disclose. |
| 11 | Seeds, reproducibility, edge cases | | Same seed reproduces exactly; identical series -> diff 0, p = 1; constant paired difference -> exact `P*c`, collapsed interval; zero-variance -> NaN with note; <12 pairs raises; unequal length raises; NaN pairs dropped pairwise and reported in `n_obs`. Every test uses `seed=0` by default, so p-values across tests share bootstrap index paths (common random numbers): no validity issue, but they are not independent Monte Carlo draws. |

## 2. Defects and the smallest proposed corrections (NOT applied)

### D1. `sharpe_se`: autocorrelation correction points the wrong way (verified)
`sharpe_se` multiplies the iid SE by `sqrt(q)/sqrt(q + 2 sum (q-k) rho_k)`, which is Lo's factor `eta(q)/sqrt(q)`. `eta(q)` deflates the
*point estimate* of the annualised Sharpe; `sharpe_test` does not deflate it (it reports the naive `sqrt(P) mean/sd`). The SE of the naive
estimator should **rise** with positive autocorrelation; the code lowers it, and for negative autocorrelation inflates it.

Simulation (T=132, AR(1) with t(5) innovations, true SR = 0, 2,000 replications, nominal 5% test):

| phi | code SE / empirical sd | iid SE / empirical sd | size of `sharpe_test` | proposed SE / empirical sd | size with proposed SE |
|---|---|---|---|---|---|
| -0.2 | 1.59 | 1.22 | 0.6% | 1.02 | 5.3% |
| 0.0 | 1.09 | 1.00 | 4.3% | 0.98 | 6.1% |
| 0.2 | **0.74** | 0.81 | **16.1%** | 0.93 | 7.9% |
| 0.4 | **0.47** | 0.64 | **34.7%** | 0.85 | 10.3% |

(Monte Carlo se of each rate: 0.2-1.1 points.)

Proposed patch (3 lines, same estimator `sharpe_difference_test` already validates): in the `autocorr` branch return
`newey_west_se(np.sqrt(periods) * (z - 0.5 * sr * (z**2 - 1)))` with `z = (r-mean)/sd`, `sr = mean/sd` (per-period). It carries the Mertens
skew/kurtosis terms through `z**2`, so it also replaces the `higher_moments` branch when `autocorr=True`. Residual HAC under-coverage at
phi=.4 is the finite-sample property in item 2.

**Possibly affected statistics:** only the `se`, `t_stat`, `p_value` and `hlz_t3_hurdle` columns of `inference_report(...)["per_strategy"]`
(called from `tools/exp_e29_attribution.py`), i.e. per-strategy Sharpe t-statistics for the 16/21-strategy exhibits. **Not affected:** deflated-Sharpe
probabilities (`deflated_sharpe` has its own formula), Romano-Wolf, PBO, SPA, every paired test, every capacity/tax result. The published
statements built on those exhibits are null findings (0 of 16 / 0 of 21 survive deflation; Romano-Wolf 0 of 16 reject); a correct SE is larger
when autocorrelation is positive, so it could only strengthen them. The direction is not guaranteed for negative autocorrelation, so the per-strategy
t-statistics (if ever quoted) would need the rerun.

### D2. `romano_wolf`: adjusted p-values after the first non-rejection are forced to 1.0 (verified, reporting only)
`p_adj` is initialised to ones and the post-failure loop takes `max(p, p_adj[j]) = 1`. In the 8-cell null simulation 87% of non-rejected
hypotheses were reported with `p_adjusted` exactly 1.0 (deterministic test: t = -0.11 reported as 1.0, step-down value is about 0.5). Rejection decisions
are unaffected and FWER is controlled (6.0%). Patch: delete the `if p > alpha: ... break` branch so the loop assigns every step-down value
(monotone running max already enforced). **Affected:** the printed `p_adjusted` column of any Romano-Wolf table (e.g. DEU "best adjusted p = 0.581" is a
first-failure value and is unaffected; other non-rejected rows are over-stated).

### D3. `romano_wolf` drops incomplete months jointly and silently (verified, disclosure)
`returns.dropna(axis=0, how="any")` contradicts the module claim that nothing is silently dropped, and the dropped count is not returned. Proposed: return
`months_used` / `months_dropped` in the frame attrs. No numerical change for balanced panels.

### D4. Percentile interval beside a studentised p (methodological choice)
Simulated coverage of the nominal-95% interval (400 replications, `n_boot = 399`, corr .9 pairs):

| DGP | size | percentile CI (code) | studentised CI (proposed) |
|---|---|---|---|
| Sharpe diff, T=132, phi=0 | 5.8% | 93.5% | 93.2% |
| Sharpe diff, T=132, phi=.3 | 6.2% | 91.0% | 92.7% |
| Sharpe diff, T=60, phi=.3 | 8.7% | 87.3% | 88.5% |
| Mean diff, T=132, phi=0 | 5.5% | 92.7% | 93.0% |
| Mean diff, T=132, phi=.3 | 6.2% | 91.5% | 92.5% |
| Mean diff, T=60, phi=.3 | 9.0% | 84.3% | 87.3% |

Differences are 0.3-3 points against Monte Carlo se of 1.2-1.8 points: modest evidence, same direction in all six. Both under-cover (finite-sample HAC).
In the committed Tier B capacity table, 2 of 35 solvent rungs have a percentile interval that excludes zero while the studentised p is above 0.05
(India 1e5: B = 2.88 points, p = 0.057; Japan 1e6: B = 0.35 points, p = 0.060). Proposed: report `ci95_*` as the studentised interval
`d - q_{.975}(t*) se, d - q_{.025}(t*) se` (needs `boot_stud`, already computed) and keep the percentile interval as `ci95_pct_*`. **Affected:** every
`ci95_low/high` and `B_ci_*` column; headline p-values and Holm decisions are unchanged.

### D5. `hansen_spa`: recentring threshold in the wrong units (verified)
`newey_west_se` already returns the SE of the mean, but the threshold is `-sqrt(2 loglog T) * ses / sqrt(T)`, a further `1/sqrt(T)` too small (about 11x at
T=132). Hansen's rule is `dbar < -sqrt(2 loglog T) * se_of_mean`. Effect: mildly inferior candidates are classed "poor" and not recentred, which shrinks the
null distribution. Simulation (T=132, K=20, H0 true, 300 replications, nominal 5%): rejection 6.0% (code) vs 3.3% (patched) with 19 candidates at -3 se;
2.3% vs 0.3% with 19 at -1 se; 8.7% vs 6.7% with all 20 at zero (Monte Carlo se 0.3-1.6 points). The patch lowers rejection in all three, so it can
only raise p. **Affected:** the single reported SPA (`p = 0.70` against equal-weight, 0 of 21): a larger p keeps "no candidate beats the benchmark".
Patch: delete `/ np.sqrt(T)` in the threshold line. Both versions over-reject when all nulls sit exactly at the boundary, so the SPA p is approximate.

### D6. Disclosure items (not defects)
* **p-value resolution.** Bootstrap p has no `+1` correction: `p = 0` is reported when no replication reaches the observed statistic (12 of 35 solvent Tier B rungs). Report `p < 1/(B+1)` or use `(1 + #)/(1 + B)`; Holm decisions do not change.
* **Convention drift.** `exp_after_tax_inference.py` runs the per-cell tests with `n_boot = min(n_boot, 800)` while pooled tests use the CLI value; all callers use `block = 6` and `PERIODS = 12`. The per-cell p-values therefore have coarser resolution (1/800).
* **Holm families.** Five local copies (correct, identical). Families differ by tool (8 cells per rung; valid rungs within country). In `exp_capacity_return_difference.py` the family is the *solvent* rungs, a filter defined on outcomes of the uncapped book, so the family size is data-dependent. State it with the table.
* **Short samples.** Size is 8.7-9.0% at T=60; do not read sub-sample or short-window p-values at face value.

## 3. Simulation specification (reproducible)

`python tools/audit_inference_simulations.py --scale 1.0` (seeds fixed; about 9 minutes). DGP: AR(1) with Student-t(5) innovations scaled to unit
marginal variance, 100-observation burn-in. Sharpe-difference size/coverage: monthly mean 0.004, sd 0.04 (SR about 0.35 annualised), cross-correlation .9,
second series scaled to equal Sharpe (volatility ratio 1 and .5), T in {132, 60}, 400 replications of 399 bootstrap draws. SE study: 2,000 replications,
true SR = 0. SPA: K = 20, iid candidates, benchmark 0, 300 replications of 299 draws. Romano-Wolf: K = 8, cross-correlation .5, phi = .2, all means 0,
300 replications of 299 draws. Finite simulations do not prove universal validity; they show the stated behaviour under the stated assumptions.

## 4. Historical claims by method (read-only trace; nothing re-run)

| Method | Claims that depend on it | Status after this audit |
|---|---|---|
| `mean_difference_test` | Capacity return difference B(A), Tier A/B tables | Test and p-values sound; interval wording to be changed (D4); Holm correct |
| `sharpe_difference_test` | Capacity channel, design identifiability, tax channel, matched-book, theme x liquidity, gate-2 power | Test sound at T=132; short-sample oversize; interval wording (D4) |
| `newey_west_se` | Factorial effects, IC t-statistics, `t_nw` columns, after-tax Sharpe t | Sound; slightly small SE at high persistence |
| `sharpe_se` via `inference_report` | Per-strategy Sharpe t / p / HLZ hurdle (E29 exhibits) | **Affected (D1)**; rerun needed before quoting |
| `deflated_sharpe`, PBO | "0 of 16 / 0 of 21 survive deflation" | Not affected by D1; assumptions disclosed (item 10) |
| `romano_wolf` | "0 of 16 reject at 5%" | Decision unaffected; adjusted p column over-stated (D2) |
| `hansen_spa` | "SPA p = 0.70, 0 of 21" | Deviation D5; correction can only raise p |

Items that cannot be resolved without a later approved rerun: the corrected per-strategy `sharpe_se` columns (D1), the studentised-interval columns (D4),
and the corrected Romano-Wolf `p_adjusted` (D2). None changes a preregistered headline test.

## 5. Proposed patch order (awaiting review)
1. D1 `sharpe_se` (3 lines) + remove the matching `xfail` in `test_inference_audit.py`.
2. D2 Romano-Wolf loop (delete the early `break` branch) + remove its `xfail`.
3. D5 SPA threshold (`/ np.sqrt(T)` removed).
4. D4 report both intervals; D6 `(1+#)/(1+B)` as an opt-in `p_floor` flag so existing results stay reproducible.

## 6. Corrections applied (2026-10-13, reviewed before commit)

Scope: D1, D2, D5 and the primary confidence-interval convention only. Historical statistics are **not** updated.

| Defect | Reference formula (stated before editing) | Change |
|---|---|---|
| D1 `sharpe_se` | SE of `sqrt(P) mean/sd` = Newey-West SE of the mean of `psi_t = sqrt(P)[z_t - (S/2)(z_t^2 - 1)]`; AR(1), true SR 0: `sqrt(P (1+phi)/(1-phi) / T)` | `autocorr=True` returns that HAC SE; `autocorr=False` unchanged |
| D2 `romano_wolf` | Romano-Wolf (2005) step-down: each hypothesis compared with the bootstrap maximum over the hypotheses still remaining, p made monotone | Early `break` removed; every hypothesis gets its own step-down value; decisions identical (`p_adjusted < alpha`) |
| D5 `hansen_spa` | Hansen (2005): recentre unless `sqrt(n) dbar / omega <= -A_n`, `A_n = sqrt(2 log log n)`; `omega/sqrt(n)` is the SE of the mean, so the test is `dbar <= -A_n * se` | Threshold `-A_n * ses` (extra `1/sqrt(T)` removed), factored into `_spa_recentre`; `>` replaces `>=` at the boundary, per the definition |

The `A_n = sqrt(2 log log n)` form is the library docstring's own rule; I could not consult the paper in this environment, so only the unit (the standard-error-of-the-mean factor) is derived from the definition of the standardised statistic, not the form of `A_n`.

**Primary confidence-interval convention (resolved for Phase C):** the studentised (percentile-t) interval
`[d - q_{.975}(t*) se, d - q_{.025}(t*) se]` is primary because it is built from the same studentised bootstrap distribution as the p-value. The
percentile interval stays available as `ci95_low/high` (unchanged) and the studentised one is added as `ci95_stud_low/high` in both
`sharpe_difference_test` and `mean_difference_test` (additive keys; no existing key or value changed). Coverage evidence (nominal 95%, same draws for both
intervals, Monte Carlo se 1.2-1.8 points): studentised vs percentile were 93.2/93.5 (Sharpe diff, T=132, phi 0), 92.7/91.0 (phi .3), 88.5/87.3 (T=60),
93.0/92.7, 92.5/91.5 and 87.3/84.3 (mean diff). The studentised interval is at least as good in 5 of 6 and ahead by 0.3-3.0 points in most, but
individual differences are within Monte Carlo error; both under-cover by 2-8 points, so intervals must be described as approximate. Both are reported
side by side whenever an interval is quoted.

**Post-patch simulations** (`results/inference_audit_2026-10-13/post_patch/`, pre-patch copies in `pre_patch/`, same seeds, DGPs and replication counts
as section 3; the library and an independent re-implementation agree to 1e-12 on the SPA and on the studentised interval):

| Check | Before | After | Monte Carlo se |
|---|---|---|---|
| `sharpe_se`/empirical sd, phi = -0.2 / 0 / 0.2 / 0.4 | 1.59 / 1.09 / 0.74 / 0.47 | 1.02 / 0.98 / 0.93 / 0.85 | ratio of means over 2,000 draws |
| `sharpe_test` size at 5%, same phi | 0.6 / 4.3 / 16.1 / 34.7% | 5.2 / 6.1 / 7.9 / 10.2% | 0.5-0.7 pts |
| Romano-Wolf family-wise rejection, 8 correlated null cells | 6.0% | 6.0% (same draws, identical decisions) | 1.4 pts |
| Non-rejected hypotheses reported at exactly 1.0 | 87.4% | 5.1% | |
| SPA rejection, 19 candidates at -1 se / all 20 at zero / 19 at -3 se | 2.3 / 8.7 / 6.0% | 0.3 / 6.7 / 3.3% | 0.3-1.6 pts |

Remaining behaviour to disclose: the HAC-based `sharpe_se` still under-covers at high persistence (phi = .4 rejects 10.2%, Newey-West small-sample bias);
the SPA still over-rejects when every null is exactly on the boundary (6.7%, se 1.4); Romano-Wolf is one-sided (tests mean > 0).

**Affected inference functions:** `sharpe_se` (and through it `sharpe_test`, `inference_report`), `romano_wolf`, `hansen_spa`,
`sharpe_difference_test` and `mean_difference_test` (additive keys only). **Statistics that would change if re-run (not re-run):** per-strategy Sharpe
SE/t/p/HLZ columns of `inference_report`; non-rejected Romano-Wolf `p_adjusted`; the SPA p (can only rise); interval columns where the studentised
interval is adopted. Capacity, tax, matched-book, identifiability and theme results use only the unchanged paired-test p-values and are unchanged.
