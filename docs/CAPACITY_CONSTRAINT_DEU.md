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

---

## The consequence: the book expresses liquidity, not the forecast

Added 8 October 2026, after the first two real cells cleared C12. This is the most important
interpretive result so far and it should shape how the factorial is read.

Measured on cell `L-C-P-0` over all 132 evaluation months:

| diagnostic | value |
|---|---|
| held positions at their position cap (within 1%) | **36.2%** mean, 10.9% min, 58.6% max |
| rank correlation of \|w\| with \|alpha\| | **-0.080** |
| rank correlation of \|w\| with the position cap | **+0.871** |

Position *size* is almost perfectly explained by the ADV participation cap and essentially
unrelated to the alpha forecast. The optimiser is choosing signs and little else: how much to hold
of each name has already been decided by its liquidity before the model is consulted.

That resolves what otherwise looks like a contradiction in the results. The signals carry
information - E02 reports positive mean rank IC with Newey-West t-statistics above 2 for a large
share of the library - and yet the realised books earn almost nothing gross. The first two cells
priced on real data:

| cell | gross Sharpe | net Sharpe | gross p.a. | net p.a. | cost drag |
|---|---|---|---|---|---|
| `cell_L-C-P-0` | +0.138 | **-0.187** | +0.08% | -0.11% | 18.3 bp |
| `cell_L-C-E-0` | -0.157 | **-0.568** | -0.13% | -0.48% | 34.5 bp |

Gross alpha of roughly 8 basis points a year cannot survive 18 basis points of cost. But the
reason gross alpha is 8bp rather than something worth trading is not that the forecast is empty -
it is that the forecast is not being expressed. A book whose weights correlate +0.87 with ADV and
-0.08 with alpha is a liquidity-weighted portfolio with alpha-determined signs.

**What this means for the paper's question.** The thesis is the net-of-cost value of ML signal
combination. On Germany at the registered baseline AUM the answer is "approximately zero, and
negative after costs" - but the mechanism matters enormously for how that is reported:

* it is **not** evidence that nonlinearity, state dependence, cost-aware objectives or uncertainty
  shrinkage fail to add forecasting value;
* it **is** evidence that in a capacity-constrained universe none of them can be acted on, so
  their net-of-cost value is zero regardless of their forecasting value.

That is a sharper and more interesting claim than "ML does not help", and it is exactly the kind of
implementation-versus-forecast distinction the design was built to separate. It also predicts the
sign of the AUM axis: at $10bn, where the attainable gross falls to 0.023, the effects should
compress further toward zero.

**A limitation to state plainly.** Amendment 001A froze capacity at AUM {1e9, 1e10}, and both
levels are capacity-bound for this universe. The registered design may therefore have no power to
detect the four factorial effects on Germany at all - not because the effects are absent, but
because the constraint set dominates at both registered scenarios. Establishing that requires
running an AUM small enough that the participation cap stops binding (on these numbers, of order
$100m), which is **not** a registered scenario.

Such a run is legitimate as a labelled diagnostic of *why* the registered effects are near zero. It
is not legitimate as a replacement headline, and choosing an AUM because its results look better is
precisely the specification search frozen decision 6B exists to prevent. If it is run, it is
reported as exploratory, alongside the registered scenarios, never instead of them.

### How small would AUM have to be for the cap to stop binding?

Cheap to answer, and it carries no selection risk: the capacity ceiling is a property of the
universe, computed from ADV alone, with no strategy formed and no performance involved. At
2014-06-30 (253 eligible names, median ADV $0.84m):

| AUM | max attainable gross | share of names ADV-capped |
|---|---|---|
| $50m | 0.841 | 79.5% |
| $100m | 0.622 | 87.4% |
| $250m | 0.414 | 91.3% |
| $500m | 0.297 | 93.7% |
| **$1bn (registered)** | **0.202** | **97.6%** |
| **$10bn (registered)** | **0.024** | **100.0%** |

The constraint never fully relaxes anywhere near a plausible AUM. Even at $50m - a twentieth of the
registered baseline - four names in five are still capped and the attainable gross is 0.84 against
a budget of 2.0. Reaching the full budget would need an AUM of order $20m, which is not a fund.

So the earlier framing needs tightening: this is not "the registered AUM happens to be too large".
**The German tradeable panel cannot support a 100/100 market-neutral book at 5% participation at
any institutionally meaningful size.** The capacity result is a statement about the market, not
about the choice of scenario, and the registered {1e9, 1e10} grid is bracketing a universe that was
already constrained before the grid was written.

That makes the exploratory small-AUM diagnostic less interesting than it first appeared - it cannot
produce an unconstrained benchmark, only a less constrained one - and makes the capacity finding
itself more central to the paper.

### Side effect worth recording: the held books were not dollar neutral

The stale pre-fix weights show mean |net| of 0.021-0.026 against gross of 0.060-0.140 - up to 35%
net exposure in a design that claims dollar neutrality. Holding a drifting book abandons the
neutrality constraint along with everything else, because nothing is re-solved. The refreshed cells
report mean |net| of exactly 0.0000. Another reason a held month is not comparable to a solved one,
beyond the staleness itself.
