# Germany: the first real-data factorial attribution

**Panel:** promoted international C1-C6, Germany. 273,068 security-months, 1990-2020.
**Evaluation window:** 2009-01-31 to 2019-12-31, 132 months, frozen in amendment 001A before any
result was inspected.
**Design:** the pre-registered 2x2x2x2 over nonlinearity (N), state dependence (C), cost-aware
objective (E) and uncertainty shrinkage (U). All 16 cells, 132 months each, zero held months.
**Trial count:** 52 configurations fitted against a registered N = 64 (conservative by 12).
**Reproduce:** `pipelines/02_train_models.py --country DEU --cells all --years 2009 2019 --fast`,
then `pipelines/04_construct_portfolios.py --country DEU --strategies <16 cells>`, then
`tools/dev_backtest.py --country DEU`, then `tools/exp_e29_attribution.py --source real_DEU`.

> **Status.** The C12 engine used here is workstream B's development stand-in, not Absar's contract
> engine. Cost parity is exact across cells because every cell is priced by the same object, so the
> *contrasts* below are sound, but the absolute levels will move when the real engine lands.

---

## 1. Cells, ranked by net-of-cost Sharpe

| cell | N | C | E | U | net p.a. | net Sharpe |
|---|---|---|---|---|---|---|
| `L-S-P-U` | - | - | - | **+** | +0.14% | **+0.335** |
| `N-C-P-U` | **+** | **+** | - | **+** | +0.12% | +0.280 |
| `N-S-P-U` | **+** | - | - | **+** | +0.12% | +0.250 |
| `L-S-P-0` | - | - | - | - | +0.13% | +0.233 |
| `N-C-P-0` | **+** | **+** | - | - | +0.08% | +0.168 |
| `N-S-P-0` | **+** | - | - | - | +0.02% | +0.038 |
| `L-C-P-U` | - | **+** | - | **+** | -0.03% | -0.069 |
| `L-C-P-0` | - | **+** | - | - | -0.11% | -0.187 |
| `N-C-E-0` | **+** | **+** | **+** | - | -0.26% | -0.306 |
| `N-C-E-U` | **+** | **+** | **+** | **+** | -0.41% | -0.502 |
| `L-C-E-0` | - | **+** | **+** | - | -0.48% | -0.568 |
| `L-S-E-0` | - | - | **+** | - | -0.47% | -0.576 |
| `L-C-E-U` | - | **+** | **+** | **+** | -0.46% | -0.593 |
| `N-S-E-0` | **+** | - | **+** | - | -0.55% | -0.658 |
| `L-S-E-U` | - | - | **+** | **+** | -0.58% | -0.675 |
| `N-S-E-U` | **+** | - | **+** | **+** | -0.62% | -0.813 |

**The ranking separates perfectly on one axis.** Every prediction-loss cell (E = -) ranks above
every economic-loss cell (E = +). No other factor comes close to ordering the table.

## 2. Factorial effects, estimated in the time domain

Contrasts are formed month by month and the effect is the mean of the contrast's own return series
with a Newey-West standard error, because the 16 cells share months, universe, optimiser and cost
model and are ~0.9 correlated. A regression on 16 cell statistics would treat them as independent
and understate every standard error.

| term | annualised | t |
|---|---|---|
| **economic** | **-0.0054** | **-3.77** * |
| conditional x economic | +0.0012 | +2.47 * |
| nonlinear x conditional | +0.0011 | +1.81 |
| nonlinear | +0.0004 | +0.31 |
| conditional | +0.0003 | +0.42 |
| uncertainty | -0.0001 | -0.16 |
| economic x uncertainty | -0.0007 | -1.15 |
| *(remaining 8 interactions)* | \|effect\| <= 0.0004 | \|t\| <= 1.19 |

**Shapley attribution** (sums exactly to all-on minus all-off, -0.0054 p.a.):

| factor | p.a. | share of total |
|---|---|---|
| economic | **-0.0055** | **102.0%** |
| uncertainty | -0.0003 | +5.0% |
| nonlinear | +0.0002 | -3.5% |
| conditional | +0.0002 | -3.5% |

Both methods agree: one factor accounts for essentially all of the net-of-cost difference, and it
is the cost-aware objective, acting in the wrong direction.

## 3. Deflation: nothing survives

| | |
|---|---|
| registered trial count N | 64 |
| configurations actually fitted | 52 |
| E[max Sharpe] under the null | **0.717** annualised |
| cells surviving deflation | **0 of 16** |
| best cell (`L-S-P-U`) | Sharpe 0.335, deflated probability 0.104 |

The best cell in the design reaches a third of the Sharpe that searching 64 configurations would
be expected to produce by chance. This is the result the deflated Sharpe exists to deliver and it
should be reported as the headline, not buried: **on Germany, net of costs, no configuration in the
pre-registered design is distinguishable from the outcome of the search that produced it.**

### Multiple testing: the same answer from two more directions

| test | result |
|---|---|
| Romano-Wolf StepM, family-wise over 16 cells | **0 of 16 reject** at 5%; best adjusted p = 0.581 (`N-C-P-U`) |
| PBO by CSCV | **0.069** |

Romano-Wolf agrees with the deflation: once the family of 16 is corrected for, nothing is
significant, and it is not close - fifteen of sixteen cells have an adjusted p of 1.000.

PBO deserves care, because 6.9% is a *low* number and low PBO is normally good news. It says the
configuration that wins in sample lands in the bottom half out of sample only 6.9% of the time, so
the selection **procedure** is stable. But stability is not profitability, and here the stability
is largely inherited from the E-vs-P separation in section 1: the gap between prediction-loss and
economic-loss cells is large and persistent, so whichever prediction cell wins in sample is
reliably above median out of sample. The honest summary of the three tests together is: **the
design picks the same winner consistently, and that winner is not good enough to clear the hurdle
its own search creates.**

## 4. Why: capacity binds before the model matters

This is the mechanism, and it is what makes the negative result informative rather than empty.

**The tradeable universe is smaller than the signal-bearing one.** C6 `adv_usd` is non-null for
only 55.3% of DEU rows. Over the evaluation window, the share of each month's cross-section with
certified spread *and* volatility *and* positive ADV averages 65.2% and is never 100% in any month:
~246 tradeable names a month against ~360 carrying a signal.

**The gross budget is unreachable.** At the registered $1bn, the largest gross the universe can
carry is 0.19-0.23 against a pre-registered budget of 2.0, because 97.6% of names are capped by ADV
participation rather than by the 1% position limit. Median ADV is $0.6-1.7m. At $10bn the ceiling is
0.024. Even at $50m - a twentieth of the baseline - 79.5% of names are still capped. **The German
tradeable panel cannot support a 100/100 market-neutral book at 5% participation at any
institutionally meaningful size.**

**So the book expresses liquidity, not the forecast.** On cell `L-C-P-0` over all 132 months:

| diagnostic | value |
|---|---|
| held positions at their position cap | 36.2% mean, 58.6% max |
| rank corr of \|w\| with \|alpha\| | **-0.080** |
| rank corr of \|w\| with the position cap | **+0.871** |

Position size is explained almost entirely by liquidity and is unrelated to the alpha forecast. The
optimiser chooses signs; how much to hold was decided by ADV before the model was consulted.

That resolves what would otherwise look like a contradiction. The signals carry information - E02
finds positive mean rank IC with Newey-West t above 2 for a large share of the library - yet the
books earn ~8bp gross against 10-18bp of costs. Gross alpha is small **not because the forecast is
empty but because it is not being expressed.**

### The reading this supports, and the one it does not

* It is **not** evidence that nonlinearity, state dependence or uncertainty shrinkage fail to
  forecast. Their net-of-cost effects are indistinguishable from zero (\|t\| <= 0.42) because in a
  capacity-bound universe none of them can be acted on.
* It **is** evidence that net-of-cost ML signal-combination value is approximately zero on this
  market at institutional size, and that the binding constraint is implementation capacity rather
  than forecasting skill.

## 5. Why the cost-aware objective *loses* 54bp

The one significant effect runs against its own design intent, so it needs a mechanism rather than
a shrug. The economic cells trade far more and forecast no better:

| group | turnover / month | cost drag p.a. | gross Sharpe |
|---|---|---|---|
| prediction-loss (`*-P-*`) | 0.009 - 0.016 | 10 - 18 bp | +0.14 to +0.60 |
| economic-loss (`*-E-*`) | 0.022 - 0.028 | 34 - 43 bp | -0.27 to +0.15 |

They are worse **gross**, not merely net, so this is not simply "they pay more costs". The
explanation consistent with section 4: the economic objective optimises a net-of-cost utility at a
gross exposure the market cannot absorb. Its proposals ask for the full gross budget of 2.0; the
realised book is capped near 0.16. It is therefore optimising a utility it can never realise, and
the trades it selects to chase that utility are calibrated to a regime 12x larger than the one it
executes in. A cost-aware objective calibrated to an unconstrained gross is **mis-specified when
capacity binds** - which is a sharper claim than "decision-focused learning did not help", and it
is testable by re-running the objective with the capacity ceiling inside its own utility.

**This is the first thing to do next**, and it is a modelling change, not a scenario choice: the
economic cells should optimise subject to the same attainable gross the optimiser will enforce.

### It is not an artefact of the projection

The economic cells reach C11 as proposals that `project()` maps onto the constraint set, and that
projection is code written on 8 October. If it did not carry the proposal, this whole section would
be measuring the projection. Checked, across all eight economic cells
(`tools/verify_projection_fidelity.py`):

| measure | range |
|---|---|
| sign agreement, top quintile of \|w_prop\| | 99.1% - 99.7% |
| sign agreement, gross-weighted | 88.8% - 95.8% |
| sign agreement, unweighted | 75.6% - 87.3% |

The unweighted figure looks alarming and is not the right measure: a proposal carries a long tail of
near-zero positions whose sign holds no information. Weighted by position size, the projection is
faithful on the positions that constitute the book.

## 6. What had to be fixed before any of this could be believed

The first real-data run of this design completed successfully, wrote contract-valid output, and was
entirely wrong. Four faults, each acting on one axis rather than on all cells, so each would have
read as a treatment effect (`docs/NON_TRADEABLE_TREATMENT.md`, commits `36e839a`..`e1bfd38`):

1. **All eight prediction cells held a drifting 2009 book for 131 of 132 months.** `construct` held
   the entire prior book whenever any held name lost its cost inputs - self-reinforcing, because the
   book then never changed and never regained eligibility. Replaced with a frozen sleeve.
2. **The guard built to catch that was blind to it**, matching `failed_hold` where the status was
   `failed_hold_missing_cost`, so 131 held months scored as zero against a 2% threshold.
3. **`project` never applied the per-name trade cap**, so economic cells made trades up to 24x the
   ADV participation limit on 15.4% of name-months - on exactly the axis that is now the headline
   effect. Post-fix: 0.16%.
4. **`factorial_effects` silently dropped unbalanced months** while its docstring promised a raise.

Plus: the five pre-registered comparators had 24 passing tests but no driver had ever run them, and
running them raised `KeyError` inside the shared runner immediately.

Current state of the quality gates on this exhibit:

| gate | result |
|---|---|
| cells with any held month | **0 of 16** |
| months per cell | 132, balanced |
| trades over the ADV cap | <= 0.16% per cell, worst 5.2x, cumulative excess gross 1e-4 |
| dollar neutrality | \|net\| <= 1.6e-7 |
| frozen sleeve | plateaus at 55-65 names, <= 1.44% of gross |
| projection fidelity | >= 99.1% on the top quintile |
| provenance | `outputs/e29/e29_artefact_chain.csv`, sha256 per artefact per cell |

## 7. Limitations to state in the paper

1. **Both registered AUM levels are capacity-bound**, so the design may have little power to detect
   the four effects on Germany. That is a property of the market, not of the scenario grid: there is
   no plausible AUM at which the constraint stops binding (section 4).
2. **The economic-objective effect is confounded with leverage.** Economic cells ride the capacity
   ceiling (gross 0.161-0.197) while prediction cells sit at an interior optimum (0.030-0.140). A
   pure rescaling cannot change a Sharpe ratio, but market impact is superlinear while returns are
   linear, so net-of-cost Sharpe does depend on scale and the two groups are not on the same point
   of that curve. The volatility-matched variant that would separate objective from leverage is
   **not yet run**.
3. **One country.** India and Japan are local and resolve, but have not been run. Amendment 001A
   freezes them as separate runs, so neither borrows power from this one.
4. **The C12 engine is a development stand-in.** Contrasts are sound, levels will move.
5. **`optimal_inaccurate` is common** (98-117 of 132 months in prediction cells). Verified feasible
   rather than trusted: realised constraint violations are at conic-residue scale. It reflects the
   solver's convergence label on a tightly-constrained problem, not an infeasible book.
6. **C6 ADV coverage is unexplained.** Whether 55% is the source data or a promotion gap is an open
   question to Absar (`docs/handoff/18_...`). If recoverable, the tradeable universe grows and every
   number here changes.
