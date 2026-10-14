# Non-tradeable security-months: the frozen sleeve

**Date:** 8 October 2026
**Layer:** C11 (portfolio construction). No contract, no frozen hyperparameter and no
pre-registered scenario changes. Applies identically to all 16 cells and to every comparator.
**Code:** `alphacomb.portfolio.cost_terms.partition_prior_book`,
`alphacomb.portfolio.optimizer.FrozenSleeve`.

---

## The data fact

The promoted international C6 does not price every security-month. On Germany:

| field | non-null |
|---|---|
| `spread` | 85.5% |
| `sigma_d` | 97.1% |
| `adv_usd` | **55.3%** |
| `borrow_fee` | 0% (by certification; the modelled proxy is injected at the consumer layer) |

`adv_usd` binds. Over the frozen 2009-2019 evaluation window, the share of each month's alpha
cross-section carrying certified spread **and** volatility **and** positive USD ADV is:

| statistic | value |
|---|---|
| mean | 65.2% |
| median | 65.4% |
| min / max | 51.7% / 75.5% |
| months at 100% | **0 of 132** |

So the investable Germany universe is about 246 names a month, not the ~360 that carry a signal.
That is a finding about the data, and it is reported rather than engineered away: document 13
requirement 2 makes an uncertified security-month **non-tradeable**, and imputing a spread or an
ADV to restore it is prohibited.

Coverage is not static at the name level. Month over month, among names held and priceable last
month, an average of **16.1** (median 15, max 48) lose eligibility - 6.6% of the book, and never
zero in any of the 131 month pairs. Of those, ~12.4 are still in the universe and ~3.7 have left it.

## What went wrong

`construct` and `construct_robust` held the **entire** prior book whenever any held name lost its
cost inputs:

```python
held_without_costs = ineligible_held_permnos(date, cost_inputs, w_prev)
if len(held_without_costs):
    return OptimizationResult(w_prev.copy(), "failed_hold_missing_cost", ...)
```

The reasoning was sound - selling a position you cannot price is an unpriced liquidation - but the
remedy is self-reinforcing. Once the book is held it does not change, so the offending name is
still in it next month, and the book is held again. On real DEU data every prediction cell returned:

```
132 months, statuses {'failed_hold_missing_cost': 131, 'optimal_inaccurate': 1}
```

One month of strategy, then 131 months of a drifting 2009 portfolio. This is the same class of
failure as `SILENT_OPTIMISER_FAILURE.md`, and it reached a results-bearing pipeline for two reasons:

1. **The guard that exists to catch it was keyed to the wrong string.** Stage 04 computed
   `held = counts.get("failed_hold", 0)` and compared it to `--max-held-share`. The status here is
   `failed_hold_missing_cost`, so the count was zero and 131 held months passed the 2% threshold
   unnoticed. The guard now counts every status beginning `failed_hold`.
2. **The economic-loss cells did not fail.** They reach C11 through `project()`, which takes no
   prior book at all ("a proposal is not a position"), so the guard was unreachable on that path.
   The design's cost-objective axis was therefore comparing optimised portfolios against a frozen
   one - the contrast would have loaded almost entirely onto this bug.

## The treatment

Partition last month's book at each date into three sets:

| set | test | treatment |
|---|---|---|
| tradeable | certified spread, volatility, positive ADV | optimised normally |
| **frozen** | no certified inputs, **but C6 has a row** - alive, unpriceable | carried at its drifted weight; not traded |
| exited | no C6 row at all - left the panel | closed by the delisting return already in C4 |

The alive/exited split uses presence of a C6 row rather than a universe join, because `construct`
receives no universe. That identity was verified on the promoted DEU panel: across **2,106**
held-name observations that lost eligibility, "C6 has a row" agreed with "in universe" in
**2,106** cases and disagreed in none.

The frozen names leave the optimisation vector - there is no admissible trade for them - but they
remain *in the book*, so every aggregate limit is written on the whole book:

* gross: `||w||_1 + gross_frozen <= gross_max`
* dollar neutrality: `sum(w) + net_frozen == 0`
* beta and each industry: the sleeve's committed exposure is added to the constrained expression
* factor risk: the risk term minimises `||L'(B'w + B_f' w_f)||^2`, the whole book's factor variance

Omitting any of these would let the optimiser spend a budget the portfolio has already committed,
and the reported exposures would not be the exposures held.

### How large the sleeve actually gets

I first asserted that the sleeve "does not accumulate, ~12 names and about 5% of gross". Measured
over the 132 real DEU months of cell `L-C-P-0`, that was wrong in both directions:

| | value |
|---|---|
| frozen names, first month | 0 |
| frozen names, median | **56** |
| frozen names, max | 84 |
| trend | +1.4 names per year |
| frozen share of gross, mean | **0.45%** |
| frozen share of gross, max | 1.44% |

It **does** accumulate, because a name that never regains certified inputs is never traded out of:
eligibility being re-tested monthly lets a name *leave* the sleeve, but does not stop the sleeve
from filling. It plateaus at 55-65 rather than growing without bound because ADV coverage churns in
both directions and delisted names are dropped, so inflow and outflow balance.

What stays negligible is its **weight**, not its headcount: under 1.5% of gross in every month.
That is not a coincidence - the positions that lose pricing are the illiquid ones whose ADV
participation cap made them tiny in the first place. So the sleeve is a long tail of near-zero
positions rather than a meaningful block of frozen risk, and the treatment costs the strategy very
little gross budget.

Reported anyway, every month: `n_frozen`, `gross_frozen` and `n_exited` are in the optimiser
diagnostics, so a reader can see how much of the book could not be traded rather than having to
trust that it was small. Reproduce with `python tools/verify_trade_caps.py --country DEU`.

The backtest drops exited names from the cost base for the same reason - the position no longer
exists, and keeping it there would halt the fail-closed cost consumer on a phantom holding.

## Why this is not a pre-registration event

It is a universe/implementation rule, not a hyperparameter: it does not depend on any cell's
treatment and is applied identically to all 16 cells and every comparator. It cannot favour a cell,
because it is a function of C6 coverage alone. Nothing about the frozen grid, the trial count
`N = 64`, or the scenario freeze in amendment 001A is touched.

It does change the universe the paper reports on, and that is stated as a result: **the tradeable
German universe over 2009-2019 is ~246 names a month, 65% of the signal-bearing cross-section.**
