# Does signal value depend on liquidity? A first test of the "liquidity-conditioned combination" premise

**Date:** 2026-10-09, 18:50 IST
**Status:** exploratory, gross of costs, theme composites rather than ML scores.
**Tool:** `tools/exp_theme_liquidity_terciles.py`. Data: `docs/attachments/THEME_LIQUIDITY_*_2026-10-09.csv`.

## 1. Why this test comes first

The proposed direction ("Which alpha signals survive at scale?") rests on one premise: a signal's
economic value depends on the liquidity of the names it trades, so an allocation rule that
conditions on liquidity can beat one that does not. That premise needs no cost model to test. If a
theme's gross decile-spread return is the same in the most and least liquid tercile there is nothing
for a liquidity-conditioned combination to learn from it.

## 2. Method, fixed before looking

Compliant investable universe (finite spread, volatility, positive ADV), 600-name cap, window
2009-01..2019-12. **Signal orientation is estimated on pre-2009 data only** (sign of mean monthly
rank-IC over 1990-2008; about half the signals in each market flip), so no evaluation information
touches it. Theme score = mean of the oriented signals in the theme, 13 themes. Each month names are
split into ADV terciles within the month; within each tercile the spread is mean(top-decile return)
minus mean(bottom-decile return). Annualised Sharpe with a HAC t statistic, and a paired
`sharpe_difference_test` of illiquid minus liquid, Holm-adjusted across the 13 themes.

## 3. Result

| | themes with illiquid > liquid Sharpe | mean (illiquid − liquid) | significant after Holm | raw p < 0.05 |
|---|---|---|---|---|
| **Germany** | **10 of 13** | +0.50 | **1** (quality, p < 0.001) | 4 |
| **India** | **11 of 13** | +0.45 | 0 | 1 |
| **Japan** | 5 of 13 | −0.03 | 0 | 1 |

Illustrative themes (annualised gross decile-spread Sharpe):

| | all | illiquid tercile | liquid tercile |
|---|---|---|---|
| Germany quality | +1.73 | **+1.83** | +0.18 |
| Germany momentum | +1.06 | +1.47 | +0.38 |
| India momentum | +0.83 | +1.29 | +0.31 |
| India quality | +1.09 | +1.35 | +0.64 |
| Japan low_leverage | +0.60 | +0.04 | **+0.72** |

Of the 11 theme-markets with significant pooled gross alpha (t > 2), 8 have illiquid above liquid.

## 4. Reading

* **The premise has directional support in the two shallow markets and none in Japan.** Germany and
  India together: 21 of 26 themes have illiquid above liquid (one-sided binomial p = 0.0012), but
  themes and markets are correlated, so that p-value is descriptive only.
* **It is not established theme by theme.** Only German quality survives Holm. Within-tercile
  deciles contain roughly 8 names in Germany, so each theme-tercile Sharpe is noisy, and the study
  has low power for exactly the per-theme claim a conditioning model would need.
* **Japan is the opposite or neutral**, and it is the deepest market. That is itself a result: the
  Avramov-Cheng-Metzker pattern (alpha living in hard-to-trade names) shows up where the investable
  universe is small and does not show up where it is large.
* **This is gross and equal-weighted.** Novy-Marx & Velikov argue equal-weighted spreads flatter
  small names, so some of the illiquid-tercile advantage may be the construction rather than the
  signal. A value-weighted version has not been run.

## 5. What it means for the proposed direction

1. **Half of "liquidity-conditioned combination" has already been tested.** The state-conditional
   cells condition on market states including `ILLIQ`, `MKTVOL` and `BEAR`, and the conditioning
   axis was undetectable (0 of 42). The distinction the proposal needs is **stock-level** liquidity
   rather than a **market-wide** state, and that arm has not been built. Whether the existing
   nonlinear models already learn stock-level interactions through the size and low-risk themes is
   unverified.
2. **The ceiling is the same as for the tax optimiser.** On the optimised book the gross-to-net gap
   is 0.295 (Germany), 0.329 (India) and 0.380 (Japan) Sharpe points. Any implementation-side
   improvement, whether tax-aware, cost-aware or liquidity-conditioned, can recover at most that.
   Design-axis effects on the executable book have had standard errors of about 0.1, so recovering
   30% of the gap (about 0.1) is roughly t = 1.
3. **Cross-market transfer is feasible**, and the infrastructure anticipates pooling
   (`intl.py` asserts permno-disjoint panels across countries). It is the most original piece and
   also the most compute-heavy: stage 02 took about ten hours for Japan alone.

## 6. Verdict

Worth a bounded test, not a thesis. The premise survives its first check in two of three markets,
the third contradicts it, and nothing is individually significant after correction. A stock-level
liquidity-conditioned arm should be built as an experiment with a pre-agreed stopping rule: it is
promoted only if it beats both the existing static and state-conditional cells on an untouched
period by an amount a paired test can detect.

---

# Addendum, 22:35 IST: Gate 1 result, and the arm is stopped

The Gate 1 criterion was committed before any variant ran (`2b23610`): in each of three variants the
mean illiquid-minus-liquid gap must keep at least 50% of the market's baseline gap and at least 8 of
13 themes must still point the same way; the arm proceeds only if Germany **and** India both pass.

| | baseline (ew, raw ADV) | vw, raw ADV | ew, size-neutral | vw, size-neutral | Gate 1 |
|---|---|---|---|---|---|
| **Germany** gap (themes) | +0.496 (10/13) | +0.558, 113% (11/13) PASS | **+0.194, 39% (7/13) FAIL** | **+0.195, 39% (8/13) FAIL** | **FAIL** |
| **India** gap (themes) | +0.450 (11/13) | +0.357, 79% (11/13) PASS | +0.246, 55% (9/13) PASS | **-0.007, -2% (6/13) FAIL** | **FAIL** |
| Japan (not gated) | -0.026 (5/13) | +0.018 (8/13) | -0.027 (6/13) | -0.051 (6/13) | n/a |

Size-neutral liquidity is the month-by-month residual of log ADV on log market cap. Its Spearman
correlation with market cap is +0.113 (Germany), +0.016 (India), +0.027 (Japan), so size is largely
but not perfectly partialled out in Germany.

## What this does and does not show

* **Value-weighting alone does not remove the pattern.** Germany's gap is 113% of baseline and
  India's 79%. So the alternative "tiny stocks dominate each equal-weighted decile" is not the main
  explanation.
* **Partialling out size does.** Germany keeps 39% and India 55% then -2% as the controls stack. The
  accurate reading is that most of the apparent liquidity effect is a **size** effect: alpha
  concentrated in small names, not in names that are illiquid *for their size*.
* **Germany is partial, not zero.** 39% survives with 7-8 of 13 themes pointing the same way, and its
  size control is imperfect (+0.113). The frozen rule says FAIL and I am applying it as written; a
  reader should still know it is a miss by 11 points on one criterion, not a clean null.
* No theme is significant after Holm in any size-neutral variant in either gated market.

## Decision

Both gates fail: **Gate 1** (the premise is largely a size effect) and **Gate 2**
(`RESULTS_GATE2_POWER_2026-10-09.md`: the minimum detectable effect is 70-92% of the entire
gross-to-net gap even for a close variant). Either alone stops the stock-level liquidity arm as a
flagship candidate. It is retained as a **descriptive diagnostic** and nothing is trained.

The two failures are independent. Gate 1 says the mechanism is mostly size; Gate 2 says that even a
real mechanism could not be detected with this design. Passing Gate 1 would not have rescued it.

Data: `docs/attachments/THEME_LIQUIDITY_*_{VW_ADV,EW_ADV_RESID,VW_ADV_RESID}_2026-10-09.csv`.
