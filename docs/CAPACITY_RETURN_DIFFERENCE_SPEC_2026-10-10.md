# Capacity measure in return units: specification (audit task P0-2)

**Date:** 2026-10-10. **Status:** specification written **before** any value was computed. Approved by
the user in amended form (the ratio `S = B/D`, its denominator floor and any "Sharpe-point-equivalent"
reading were rejected). Implementation and results are reviewed before anything is committed.

## 1. What is measured

For a country and a mandate size A, the **annualised arithmetic net-return difference**

    B(A) = 12 * ( mean_t r_C,t(A)  -  mean_t r_U,t(A) )          [units: return points per year,
                                                                   i.e. fraction of NAV per year]

where `r_C`, `r_U` are the **monthly net returns of the participation-capped and the uncapped decile
books**, each the *research composite* (defined in section 8) of the 8 prediction cells, over the **same months**. It is a
*difference of arithmetic mean returns*. It is not a Sharpe difference, is not a ratio, has no
denominator and therefore no near-zero-denominator problem.

It is an **accounting diagnostic against a hypothetical uncapped plan**, not an investable
performance. The investable object is the capped book's own return, reported separately for every rung.

## 2. Which rungs are valid

A rung is **valid** for B(A) only if the uncapped comparator is solvent over the whole evaluation
period: in every one of the 8 cells and every month, the uncapped book's net monthly return is
strictly greater than -100% (NAV never reaches zero), and the same holds for the capped book. This is
checked from the monthly series and cross-checked against the committed `uncapped_solvency.csv`.

At every other rung:
* **no B(A) is calculated, extrapolated or imputed**; the row says `INSOLVENT COMPARATOR`;
* the reason is stated: a full-period like-for-like comparison does not exist because the comparison
  account ceases to exist before the horizon ends, and a mean over a truncated or sub-(-100%) return
  series is not a performance;
* the capped book's own mean net return, Sharpe and t are reported separately;
* the month in which the uncapped comparator first exhausts NAV is reported as a fact. A
  pre-insolvency sub-period comparison is **not** computed (it would be a diagnostic only and is not
  needed to answer the question).

"Solvent" is a minimal condition. Rungs that are solvent but nearly ruined (compounded wealth of the
uncapped composite near zero) are flagged with the compounded terminal wealth, because an arithmetic
mean ignores compounding. They are not excluded, since the approved criterion is solvency.

## 3. Decomposition and reconciliation

Per month and book, `gross_t` is the book's gross return, and `cost_t := gross_t - net_t`. Then, as an
identity on the monthly series,

    B = 12 * [ ( mean g_C - mean g_U )  +  ( mean c_U - mean c_C ) ]
        = 12 * ( gross return forgone, negative )  +  12 * ( cost saved )

**Tier A (full ladder).** The committed monthly series `outputs/signal_vs_portfolio/monthly_<C>_cov.csv`
(compliant universe: `--require-cost-inputs`; contract cost model; 2009-2019). Here cost is *defined*
as the residual `g - net`, so the split is exact **by construction** and its agreement with B is a
bookkeeping check only, not independent evidence.

**Tier B (authoritative pipeline).** The pipeline's own `after_tax_backtest`, zero-tax regime, run on
the committed decile weights, for the rungs where weights are committed: Germany $100mn, India $30mn,
Japan $1bn (the largest solvent rung of each). It models NAV compounding, drift and frozen names.
There the cost ledger is read independently of the returns where the table provides it, and:
* `B_pipeline` is compared with `B_tierA` at the same rung (difference reported, not hidden);
* the decomposition is reconciled to `B_pipeline` and the residual is reported. Exact additivity is
  **not** assumed: arithmetic mean returns of a compounding, drifting account are not additive in
  gross, cost and tax.

Tier A at rungs without committed weights is therefore on the wedge tool's cost code, not the pipeline's.
Earlier reconciliation put the two within about 5e-4 per month on the capped book. Extending Tier B to
every rung needs the decile weights re-dumped at each rung (a deterministic re-run, no new model); that
is **not** done here and is listed as an open request.

## 4. Inference

`mean_difference_test` (new, `src/alphacomb/validation/inference.py`): paired, on `d_t = r_C,t - r_U,t`.
* statistic: `12 * mean(d)`; Newey-West HAC standard error (existing `newey_west_se`);
* calibration: **studentised stationary bootstrap** (existing `_stationary_bootstrap_index`), expected
  block 6 months, 4,000 replications, seed 0, centred at the null `B = 0`; two-sided p;
* 95% interval: percentile interval of the bootstrap distribution of the (uncentred) statistic;
* same conventions as `sharpe_difference_test`, which it mirrors.

**Multiplicity.** A formal claim "B differs from zero" is made per country across its valid rungs, so
p-values are **Holm-adjusted within country over the valid rungs**. Intervals are not adjusted and are
labelled as unadjusted. The mandate rungs are strongly dependent (same scores), so Holm is conservative.

## 5. What is not done

No sensitivity sweep, no value-weighting rerun, no borrow-fee sweep, no cost-model variant, no new
data, no model training, no change to the frozen cost contract, the 600-name cap or the 2009-2019
window. No monotonicity is imposed or tested for; the sequence of B over rungs is reported as found,
with non-monotonic steps listed. No Sharpe-point equivalence or ratio is claimed.

## 6. Existing components used

| Need | Component |
|---|---|
| monthly series, capped/uncapped/gross, 8 cells, 14 rungs | `outputs/signal_vs_portfolio/monthly_{DEU,IND,JPN}_cov.csv` (wedge tool, tag `cov`) |
| solvency cross-check | `outputs/signal_vs_portfolio/uncapped_solvency.csv` |
| authoritative accounting | `alphacomb.tax.after_tax_backtest`, `get_regime("tax_exempt")`, `intl.load_country_bundle(max_names=600)`, `tools/exp_matched_book_accounting.run_one` |
| committed weights | `outputs/decile_weights/{DEU/matched8/aum_1e+08, IND/matched7/aum_3e+07, JPN/matched/aum_1e+09}` |
| HAC SE, bootstrap indices | `newey_west_se`, `_stationary_bootstrap_index` |

## 7. Addendum (same day): the accounting unit behind the solvency rule

**Question.** Why does the rule test all 8 cells' monthly returns, not just the composite's?

**What the code does** (`tools/exp_signal_vs_portfolio_wedge.py`, `tools/exp_matched_book_accounting.py`,
`alphacomb.tax.after_tax_backtest`):
* The 8 cells are the 2x2x2 prediction variants (L/N x S/C x 0/U), i.e. **alternative model designs on
  the same universe**, not parts of one allocation.
* **Every cell is run as its own account at the full mandate A.** Costs and the participation cap
  both use `aum = A` for each cell; `after_tax_backtest` starts each cell with NAV = A and **stops that
  cell the moment its NAV reaches zero**.
* The composite is the **month-by-month arithmetic mean of the 8 cells' returns**. It is not a
  single account: it does not net trades across cells and no cell is funded at A/8.

**Consequence.** A cell with a monthly net return <= -100% is an account that no longer exists. Averaging
its (impossible) return with seven solvent cells produces a composite that looks solvent but is not
the return of any feasible portfolio, so solvency is a property of each cell. The composite-only rule
would admit one more rung in Germany ($300mn: 1 of 8 cells wiped, composite worst month -74%) and one
more in India ($100mn: 1 of 8 wiped, composite worst month -77%); Japan is unaffected. The cell rule is
the stricter one and the one consistent with how the pipeline itself stops a bankrupt cell.

**Resolved (section 8).** The composite is a research summary, not a fund. The rule stays cell-level.

## 8. Definition of the composite (resolved by the user, 2026-10-10)

The **composite** used throughout this analysis, and in the earlier capacity-channel results documents
that call it "one equal-weighted book of the eight prediction cells", is an **equal-weighted research
summary across eight independently simulated, full-AUM prediction variants**: the month-by-month
arithmetic mean of eight return series, each produced by a separate simulation of a complete decile book
at the full mandate A with its own costs, its own participation cap and its own NAV path.

It is **not** a single investable fund. In particular it is not a fund holding the average of the eight
cells' weights: such a fund would net trades across variants, face convex impact on the netted trade and
hold one NAV. No such strategy has been implemented or evaluated here, and doing so would need a separate
proposal and explicit approval. Phrases such as "one book" or "one equal-weighted book" in earlier
documents mean this summary and must not be read as a single account.

**Solvency rule (unchanged).** Every one of the eight cells must remain solvent (no month at or below
-100% net return) over the complete evaluation horizon, in both the capped and the uncapped book. No
terminal-wealth threshold is part of the primary analysis. Solvent comparators that nevertheless lose
nearly all of their value are **retained and flagged** with their compounded terminal wealth; they are
not treated as plausible investable benchmarks, and B(A) against them is an accounting difference only.
