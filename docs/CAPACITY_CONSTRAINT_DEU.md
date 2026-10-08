# Capacity binds before the risk budget does (Germany)

**Date:** 8 October 2026
**Status:** empirical finding from the promoted DEU panel, frozen 2009-2019 evaluation window.
**Reproduce:** `python tools/exp_book_characteristics.py --country DEU`

---

## The finding

The pre-registered gross budget is `gross_max = 2.0` (i.e. 100% long / 100% short). On the German
panel at the baseline AUM of $1bn, **that budget is unreachable by an order of magnitude.** The
per-name position cap is

```
pos_cap_i = min(weight_abs_max, adv_usd_i * adv_participation_max / AUM)
          = min(0.01, adv_usd_i * 0.05 / 1e9)
```

and the largest gross the universe can carry is `sum_i pos_cap_i`:

| AUM | date | eligible names | max attainable gross | share of names ADV-capped | median ADV |
|---|---|---|---|---|---|
| $1bn | 2009-06-30 | 219 | **0.189** | 96.8% | $0.63m |
| $1bn | 2014-06-30 | 253 | **0.202** | 97.6% | $0.84m |
| $1bn | 2019-06-30 | 252 | **0.233** | 97.6% | $1.69m |
| $10bn | 2009-06-30 | 219 | **0.023** | 100% | $0.63m |
| $10bn | 2014-06-30 | 253 | **0.024** | 100% | $0.84m |
| $10bn | 2019-06-30 | 252 | **0.026** | 100% | $1.69m |

So at $1bn the book can be at most ~20% invested, and at $10bn ~2.4%. For 97% of names the binding
cap is ADV participation, not the 1% per-name position limit. The reason is visible in the last
column: the tradeable German panel is a small/mid-cap panel, with median ADV between $0.6m and
$1.7m. Five percent of $0.8m is $42,000, which against $1bn is a weight of 0.00004.

This is not a constraint mis-specification. It is the capacity statement the design was built to
make, and amendment 001A already froze AUM as a scenario axis at {1e9, 1e10}. What the numbers add
is that **the lower end of that axis is already capacity-bound**: the interesting variation in this
market is not between a comfortable book and a constrained one, it is between constrained and
essentially uninvestable.

It also sharpens the paper's central claim. A net-of-cost attribution is only interesting where
costs bite, and here they bite through the participation limit before they bite through the spread.

## Consequence for the factorial: the two objectives do not choose the same leverage

Realised gross differs systematically by objective, on real DEU data over the 132 evaluation
months:

| cell group | mean gross | mean names held |
|---|---|---|
| economic-loss cells (`*-E-*`) | 0.161 - 0.197 | 246.5 |
| prediction-loss cells (`*-P-*`) | 0.030 - 0.140 | 128.6 - 157.9 |

The raw C10 proposals from the economic-loss cells have gross **exactly 2.0** - they ask for the
whole budget - and `project()` minimises squared distance to that request, so the projected book
lands on the capacity ceiling. The prediction-loss cells go through `construct()`, which solves a
mean-variance problem at `gamma = 25`; with monthly alphas of the size this signal library
produces, its interior optimum sits well below the ceiling.

**This is a confound and it is reported as one.** The economic-objective axis of the design changes
two things at once: the objective being optimised, and the leverage the book ends up carrying. A
net-of-cost Sharpe difference between the two groups is therefore not purely an objective effect:

* a pure rescaling of weights leaves the Sharpe ratio unchanged, so leverage is not *mechanically*
  responsible for a Sharpe difference;
* but market-impact cost is superlinear in trade size while returns are linear in it, so
  **net-of-cost** Sharpe does depend on scale. The two groups are not on the same point of that
  curve.

Two honest readings coexist and the paper should state both: riding the capacity ceiling is part of
what a cost-aware economic objective *does* (it knows the cap and spends up to it), and it is also
a leverage difference that a reader is entitled to see separated from the objective itself.

The exhibit therefore reports mean gross and mean names held per cell alongside every performance
number, so the asymmetry is on the face of the table rather than buried in the construction code.

## What would settle it

A volatility-matched variant: rescale every cell's book to a common ex-ante volatility before
pricing, and re-run the attribution. The objective effect that survives matching is the part that
is genuinely about the objective. This is a clean, cheap robustness check and is **not yet run** -
it is the first thing to add to the DEU exhibit, and it requires no new data.

Until it is run, the economic-objective main effect should be read as "objective plus the leverage
the objective selects", and described that way in the text.
