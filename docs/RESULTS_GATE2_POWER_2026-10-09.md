# Gate 2 pre-estimate: the stock-level liquidity arm cannot be detected, even if it recovers most of the cost gap

**Date:** 2026-10-09, 22:30 IST
**Status:** a pre-estimate from the 2009-2019 sample. It is the stopping-rule calculation requested
before committing about ten hours of training. It does not use the 2020-2025 extension (not yet
delivered), and says why that is not expected to change the answer.
**Tool:** `tools/gate2_power.py`. Data: `docs/attachments/GATE2_POWER_1E9_2026-10-09.csv`.

## 1. The question

If a stock-level liquidity-conditioned model improved on the existing models, could a paired test on
an untouched 2020-2025 window (about 72 months) detect it? The proposal estimated yes if the paired
standard error is about 0.10 Sharpe points, but noted that figure was an assumption.

## 2. What was measured

On the **optimised book** at $1bn (the book an investor runs, not the near-empty decile book), the
weights of the 8 prediction cells go through the pipeline's own `after_tax_backtest` under the
zero-tax control. For each design axis, the equal-weighted composite of the 4 cells at one level is
compared with the 4 at the other using the same paired studentised bootstrap used throughout.

| | gross SR | net SR | **gross-to-net gap** | representation SE | conditioning SE | uncertainty SE |
|---|---|---|---|---|---|---|
| Germany | +0.519 | +0.152 | **0.367** | 0.289 | 0.152 | **0.089** |
| India | +0.725 | +0.271 | **0.454** | 0.279 | 0.285 | **0.101** |
| Japan | +0.559 | +0.055 | **0.504** | 0.249 | 0.182 | **0.092** |

The gap is the most any implementation-side improvement can recover without improving gross alpha.
The standard errors differ by axis because the two arms of the **uncertainty** axis are close
variants of the same model and so are highly correlated, which shrinks the paired SE. That is the
right analogue for a liquidity-conditioned model that is a modification of an existing one.

## 3. Detectability at 72 months

SE scales as the square root of the number of months, so 72 months multiplies the 132-month SE by
1.354. Minimum detectable effect at 80% power is 2.80 SE.

| | gap | MDE, typical SE | share of the **whole gap** needed | MDE, close-variant SE | share of the **whole gap** needed | 30% of gap |
|---|---|---|---|---|---|---|
| Germany | 0.367 | 0.576 | **157%** | 0.337 | **92%** | 0.110 |
| India | 0.454 | 1.058 | **233%** | 0.382 | **84%** | 0.136 |
| Japan | 0.504 | 0.689 | **137%** | 0.350 | **70%** | 0.151 |

## 4. Verdict

**Gate 2 fails in all three markets under both assumptions.**

* With a typical paired SE the minimum detectable effect **exceeds the entire gross-to-net gap**
  (137-233%): even a model that eliminated every basis point of implementation cost could not be
  detected.
* With the most favourable SE, the one for a close variant of an existing model, a new arm must
  still recover **70-92% of the whole gap** to be detected. Spread, commission and price impact are
  not removable, so recovering most of the gap is not an economically plausible planning case. The
  planning figure of 30% (0.11-0.15 Sharpe points) is **2.5-3.5 times below** the best-case MDE.
* The proposal's assumed SE of 0.10 is correct for a close variant (measured 0.089-0.101) and wrong
  for anything less correlated with its comparator. Even at 0.10 the conclusion does not change.

## 5. Why the 2020-2025 extension is not expected to rescue it

It supplies about 72 months, fewer than the 132 already analysed, so it makes the standard error
larger, not smaller. It is valuable as an **untouched** sample and for the section 112A
post-reform window, but it cannot manufacture the power the design lacks. A longer history
(pre-2009 with the same models) would, and that is a different, much larger exercise.

## 6. Recommendation

Do **not** launch the full training run for the stock-level liquidity arm as a flagship candidate.
Retain the theme-by-liquidity diagnostic (`RESULTS_THEME_LIQUIDITY_2026-10-09.md`) as a descriptive
result. This is the outcome the stopping rule was written to produce, and it saved about ten hours
of training that could not have produced a detectable result.

What could change it: an arm expected to recover far more of the gap than a liquidity interaction
can (for example, one that raises *gross* alpha rather than trimming cost), or a design with many
more independent evaluation units than eight cells and 132 months.

## 7. Caveats

* The SEs are for **axis contrasts between composites** of 4 cells, which is the available analogue
  for a new arm versus a comparator; the true SE for a specific new model could be smaller if it is
  more tightly coupled to its comparator than the uncertainty axis is.
* The gap is measured on the composite at $1bn only; at smaller AUM the gap is larger (costs are
  higher in Sharpe terms at $100mn for Japan), which would relax the constraint somewhat.
* This calculation is itself exploratory and has not been through Maham's sign-off.
