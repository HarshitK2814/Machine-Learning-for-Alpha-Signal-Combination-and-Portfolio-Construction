# Cost-accounting parity diagnostic: results (Workstream A)

**Date:** 2026-10-10. **Status:** executed as specified in `COST_PARITY_DIAGNOSTIC_SPEC_2026-10-10.md`; **committed as `316464d`
(reviewed).** Phase 1 (`b8e21ba`) and Phase 2 (`ac669f2`) are untouched. Accounting only: no model, parameter,
cost setting, AUM rung or result was changed. Code: `tools/diag_cost_parity.py`, `tools/diag_dtv_support.py`; tracked
outputs, report and a SHA-256 manifest: `results/cost_parity_diagnostic/`.

## 1. What was done

For the six rungs (Germany $100k, $300k, $100mn; India $30mn; Japan $1bn, $10bn) and both books, the existing cost
function was re-evaluated on the existing weights under all 8 combinations of three conventions: **D** (trade size
measured from the previous *target* weight, Tier A, or from the pipeline ledger's *drifted* holdings, Tier B), **X**
(treatment of names that leave the scored cross-section: Tier A charges `|T(t-1)|` on last month's inputs; Tier B
charges a name only if it is still certified this month, otherwise closes it at no trading cost) and **B** (flat 1%
borrow, Tier B only). The pipeline was instrumented by recording the arguments of `trade_cost_numpy` and
`cost_inputs_for` (wrappers that delegate unchanged).

## 2. Headline

* **Both accountings are reproduced to machine precision in 11 of 12 pairs** (maximum monthly error 3.3e-16), and the
  reconstructed drifted holdings match what the pipeline actually traded (4e-17). The one exception, Japan $10bn
  uncapped, is reproduced only to 3e-3 per month (drift reconstruction 1.2e-2) at an account value of about
  $1e-6; the replicated discrepancy differs from the reported one by 0.032 points (tolerance
  max(0.05, 5% of 37.8) = 1.9), so the pair counts as reconciled, but the residual is **not zero** and the cause (a
  ledger edge at near-zero NAV) was not identified. A first pass had a residual of -10.6 points there; it came from
  my reconstruction missing two ledger rules (the 1e-8 dollar "held" threshold and the 1e-10 dollar lot pruning).
  Both are rules of the existing pipeline, copied into the reconstruction; the pipeline itself was not changed.
* **11 of 12 pairs have a material discrepancy** (|B - A| > 0.05 points); the Japan $10bn capped pair (0.006) does not,
  so no closure is computed for it. **All 12 are reconciled** within the pre-set tolerance.
* **The pre-set dominant-mechanism criterion is NOT met:** a single convention closes at least 90% of the
  discrepancy in 6 of 12 pairs for X, 5 of 12 for B and 2 of 12 for D (none reaches 10). **No common dominant
  explanation is claimed.** The one-at-a-time closure ratios are unstable because the three effects have opposite
  signs, so they are shown beside the order-free Shapley attribution.
* **Partial explanations that the evidence does support:**
  1. *Exit convention (X) is the largest contributor in all 6 uncapped pairs* (Shapley +1.2 to +75.8 points against
     -1.0 for borrow and -0.3 to -36.9 for drift). Tier A charges the full exit of every name that leaves the scored
     cross-section; the pipeline charges none of Tier A's exits in Germany and India, and 0.48 to 0.65 of them in
     Japan.
  2. *Borrow (B)* is a constant -1.00 point in the uncapped books (a 1% fee on gross short exposure of 1.0) and
     -0.01 to -0.93 in the capped books; it explains the capped-book gaps (which are at most 0.25 points) and none of
     the large uncapped gaps.
  3. *Drift / stale holdings (D)* is small and of one sign (the pipeline costs a little more) except at Japan $10bn,
     where interactions between the conventions are large (-90.7 points) and Shapley values should be used.
* **Why exits matter so much in the uncapped book:** its positions are multiples of daily volume (Table 6). Charging
  the exit of such a position through a convex impact term is a very large number; not charging it is a very large
  omission. Switching the exit convention alone moves the cost by 43 points at Germany $100mn; at Japan $10bn its Shapley share is +75.8 points, offset by drift (-36.9) for a net discrepancy of 37.8.

## 3. Tables

### Table 1. The 12 rung-book pairs (annual cost, points of NAV; discrepancy = Tier B - Tier A)

| Rung | Book | cost A | cost B | B - A | replicated B - A | residual R | material | reconciled |
|---|---|---|---|---|---|---|---|---|
| DEU $100k | capped | 14.63 | 14.39 | -0.247 | -0.247 | +0.000 | yes | yes |
| DEU $100k | uncapped | 18.07 | 16.66 | -1.407 | -1.407 | -0.000 | yes | yes |
| DEU $300k | capped | 12.83 | 13.03 | +0.204 | +0.204 | +0.000 | yes | yes |
| DEU $300k | uncapped | 23.47 | 21.04 | -2.429 | -2.429 | +0.000 | yes | yes |
| DEU $100mn | capped | 1.66 | 1.74 | +0.079 | +0.079 | -0.000 | yes | yes |
| DEU $100mn | uncapped | 243.99 | 199.81 | -44.177 | -44.177 | +0.000 | yes | yes |
| IND $30mn | capped | 3.52 | 3.66 | +0.145 | +0.145 | +0.000 | yes | yes |
| IND $30mn | uncapped | 129.48 | 122.62 | -6.861 | -6.861 | +0.000 | yes | yes |
| JPN $1bn | capped | 1.98 | 2.04 | +0.062 | +0.062 | -0.000 | yes | yes |
| JPN $1bn | uncapped | 112.92 | 113.38 | +0.463 | +0.463 | +0.000 | yes | yes |
| JPN $10bn | capped | 0.22 | 0.23 | +0.006 | +0.006 | -0.000 | no | yes |
| JPN $10bn | uncapped | 338.05 | 300.22 | -37.828 | -37.860 | +0.032 | yes | yes |

### Table 2. Attribution to the three conventions (change in cost when switching to the Tier A convention; points)

`e_m`: switch only m, from the Tier B baseline. `Shapley`: average over all six orderings (sums to A - B). `inter`: A - B minus the sum of the three `e_m`. Closure = `e_m` / (A - B) for material pairs only.

| Rung | Book | e_D | e_X | e_B | inter | Shapley D | Shapley X | Shapley B | closure D | closure X | closure B |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEU $100k | capped | -0.32 | +1.31 | -0.92 | +0.18 | -0.23 | +1.40 | -0.92 | -1.28 | +5.29 | -3.74 |
| DEU $100k | uncapped | -0.45 | +2.55 | -1.00 | +0.31 | -0.29 | +2.70 | -1.00 | -0.32 | +1.81 | -0.71 |
| DEU $300k | capped | -0.23 | +0.68 | -0.78 | +0.12 | -0.17 | +0.74 | -0.78 | +1.11 | -3.35 | +3.82 |
| DEU $300k | uncapped | -0.52 | +3.51 | -1.00 | +0.43 | -0.30 | +3.73 | -1.00 | -0.21 | +1.45 | -0.41 |
| DEU $100mn | capped | -0.01 | +0.01 | -0.08 | +0.00 | -0.01 | +0.01 | -0.08 | +0.12 | -0.07 | +0.96 |
| DEU $100mn | uncapped | -3.45 | +42.97 | -1.00 | +5.66 | -0.62 | +45.80 | -1.00 | -0.08 | +0.97 | -0.02 |
| IND $30mn | capped | -0.07 | +0.11 | -0.21 | +0.02 | -0.06 | +0.12 | -0.21 | +0.48 | -0.75 | +1.43 |
| IND $30mn | uncapped | -5.78 | +11.54 | -1.00 | +2.11 | -4.73 | +12.59 | -1.00 | -0.84 | +1.68 | -0.15 |
| JPN $1bn | capped | -0.01 | +0.02 | -0.07 | +0.00 | -0.01 | +0.02 | -0.07 | +0.11 | -0.25 | +1.18 |
| JPN $1bn | uncapped | -0.80 | +1.10 | -1.00 | +0.23 | -0.68 | +1.22 | -1.00 | +1.72 | -2.37 | +2.16 |
| JPN $10bn | capped | -0.00 | +0.00 | -0.01 | +0.00 | -0.00 | +0.00 | -0.01 | n/a | n/a | n/a |
| JPN $10bn | uncapped | +8.40 | +121.13 | -1.00 | -90.67 | -36.94 | +75.80 | -1.00 | +0.22 | +3.20 | -0.03 |

### Table 3. Component split of B - A (points): spread+commission, impact, borrow

| Rung | Book | spread+commission | impact | borrow |
|---|---|---|---|---|
| DEU $100k | capped | -0.584 | -0.588 | +0.925 |
| DEU $100k | uncapped | -1.010 | -1.397 | +1.000 |
| DEU $300k | capped | -0.234 | -0.342 | +0.780 |
| DEU $300k | uncapped | -1.010 | -2.419 | +1.000 |
| DEU $100mn | capped | +0.002 | +0.001 | +0.076 |
| DEU $100mn | uncapped | -1.010 | -44.166 | +1.000 |
| IND $30mn | capped | -0.020 | -0.043 | +0.208 |
| IND $30mn | uncapped | -0.162 | -7.699 | +1.000 |
| JPN $1bn | capped | -0.002 | -0.009 | +0.074 |
| JPN $1bn | uncapped | +0.092 | -0.628 | +1.000 |
| JPN $10bn | capped | -0.000 | -0.001 | +0.008 |
| JPN $10bn | uncapped | -1.438 | -37.421 | +1.000 |

### Table 4. Why Tier A's exits left the scored cross-section, and whether the pipeline charges them

Shares of exit notional (target weights). `charged by B`: share of exiting names the pipeline still prices that month.

| Rung | Book | no C6 row (left the panel) | row but uncertified | certified but unscored | exits per cell-month | charged by B | exit share of trade notional |
|---|---|---|---|---|---|---|---|
| DEU $100k | capped | 0.350 | 0.650 | 0.000 | 3.86 | 0.000 | 0.057 |
| DEU $100k | uncapped | 0.292 | 0.708 | 0.000 | 3.86 | 0.000 | 0.079 |
| DEU $300k | capped | 0.457 | 0.543 | 0.000 | 3.86 | 0.000 | 0.035 |
| DEU $300k | uncapped | 0.292 | 0.708 | 0.000 | 3.86 | 0.000 | 0.079 |
| DEU $100mn | capped | 0.755 | 0.245 | 0.000 | 3.86 | 0.000 | 0.002 |
| DEU $100mn | uncapped | 0.292 | 0.708 | 0.000 | 3.86 | 0.000 | 0.079 |
| IND $30mn | capped | 0.985 | 0.015 | 0.000 | 3.57 | 0.000 | 0.031 |
| IND $30mn | uncapped | 0.977 | 0.023 | 0.000 | 3.57 | 0.000 | 0.060 |
| JPN $1bn | capped | 0.709 | 0.002 | 0.289 | 4.03 | 0.650 | 0.014 |
| JPN $1bn | uncapped | 0.347 | 0.003 | 0.650 | 4.03 | 0.650 | 0.026 |
| JPN $10bn | capped | 0.724 | 0.002 | 0.274 | 4.03 | 0.650 | 0.014 |
| JPN $10bn | uncapped | 0.347 | 0.003 | 0.650 | 4.03 | 0.483 | 0.026 |

### Table 5. Replication checks (maximum absolute monthly error, return units)

| Rung | Book | Tier A replication | Tier B replication | drift reconstruction |
|---|---|---|---|---|
| DEU $100k | capped | 2.1e-16 | 2.0e-16 | 4.2e-17 |
| DEU $100k | uncapped | 2.1e-16 | 2.0e-16 | 2.8e-17 |
| DEU $300k | capped | 2.1e-16 | 2.0e-16 | 2.8e-17 |
| DEU $300k | uncapped | 2.1e-16 | 2.0e-16 | 3.1e-17 |
| DEU $100mn | capped | 2.0e-16 | 2.0e-16 | 2.8e-17 |
| DEU $100mn | uncapped | 3.3e-16 | 2.8e-16 | 4.2e-17 |
| IND $30mn | capped | 2.0e-16 | 2.0e-16 | 4.2e-17 |
| IND $30mn | uncapped | 3.1e-16 | 2.8e-16 | 5.6e-17 |
| JPN $1bn | capped | 2.0e-16 | 2.0e-16 | 1.6e-17 |
| JPN $1bn | uncapped | 2.2e-16 | 2.2e-16 | 2.8e-17 |
| JPN $10bn | capped | 2.0e-16 | 1.7e-16 | 3.5e-18 |
| JPN $10bn | uncapped | 3.3e-16 | 3.1e-03 | 1.2e-02 |

### Table 6. Trade size relative to daily volume (the support of published impact estimates is about 12% of daily volume)

| Rung | Book | notional beyond 12% of ADV | notional beyond 100% of ADV | notional-weighted median trade, % of ADV |
|---|---|---|---|---|
| DEU $100k | uncapped | 4.3% | 0.1% | 0.6 |
| DEU $100k | capped | 0.3% | 0.0% | 0.5 |
| DEU $300k | uncapped | 18.5% | 0.6% | 1.8 |
| DEU $300k | capped | 0.8% | 0.0% | 0.9 |
| DEU $100mn | uncapped | 90.7% | 70.7% | 596.0 |
| DEU $100mn | capped | 0.6% | 0.0% | 4.6 |
| IND $30mn | uncapped | 81.6% | 54.1% | 127.9 |
| IND $30mn | capped | 3.3% | 0.1% | 4.4 |
| JPN $1bn | uncapped | 96.9% | 65.0% | 171.9 |
| JPN $1bn | capped | 0.9% | 0.0% | 5.0 |
| JPN $10bn | uncapped | 100.0% | 97.7% | 1719.3 |
| JPN $10bn | capped | 1.5% | 0.0% | 5.0 |

## 4. Interpretation, at the strength the evidence supports

* **What is established [measured].** The Tier A / Tier B cost gap is fully accounted for, in the replication sense, by
  three conventions; borrow is exactly computable and small; the exit convention dominates the large uncapped gaps;
  the capped books agree to within about 0.25 points a year.
* **Which names exit [measured, Table 4].** In Germany 29-75% of exit notional is names that have no C6 row (they left
  the panel) and 25-71% is names that remain but are uncertified. In India 98% is "no C6 row". In Japan 35-72% is no
  row and 27-65% is certified-but-unscored, which the pipeline does price. So the pipeline's zero-cost exit applies to
  names that left the panel (closed by the delisting return, as the code comment states) and to names that stay
  but have no certified inputs.
* **Cost-input coverage [descriptive only].** The share of exit notional that is *uncertified* is large only in Germany
  (coverage 65%) and negligible in India (99.1%) and Japan (99.8%), which is the direction one would expect. But India's
  X effect is also material (11.5 points of 129 in the uncapped book) with 98% of its exits being names that left the
  panel, so coverage alone does not account for X. Three countries; no causal claim.
* **Which convention is right is not established.** For a name that has left the panel, closing at the delisting
  return is defensible. For a live name with no certified inputs, closing it at zero cost is an imputation of zero,
  which document 13 requirement 2 argues against; charging it on last month's inputs (Tier A) is also an imputation.
  The sign and size of the difference is a modelling choice that matters only where positions are multiples of daily
  volume.
* **Beyond published support [measured, Table 6].** The impact law is calibrated to trades of at most about 12% of daily
  volume. In the uncapped books at the large valid rungs the notional-weighted median trade is 128% (India $30mn), 172%
  (Japan $1bn), 596% (Germany $100mn) and 1,719% (Japan $10bn) of daily volume, and 54-98% of notional exceeds 100%.
  The capped books stay close to the support (median 0.5-5%, at most 3.3% of notional beyond 12%). So the uncapped
  comparator is priced by extrapolation, and large values of B(A) are extrapolations.

## 5. What this does and does not change

* **Does not change** any committed result; Tier B remains the authoritative cost accounting and the capped-book
  results, which are unaffected by X, are robust to the convention at the 0.25-point level.
* **Bears on Phase 2 interpretation:** (i) at five of the six rungs Tier B's B(A) is *lower* than Tier A's (Japan $1bn is the exception, -0.4),
  chiefly because Tier B does not charge the exit of a name that leaves the panel; (ii) the Germany $100k and $300k sign
  differences between tiers (B of +0.64 and +2.63 in Tier A, -0.52 and -0.01 in Tier B) come mainly from the uncapped
  book's lower Tier B cost (1.41 and 2.43 points, chiefly its exit cost: Shapley +2.70 and +3.73, partly offset by
  borrow and drift), with a small capped-book contribution (-0.25 and +0.20);
  (iii) the uncapped comparator is outside published support at the rungs where B is large. These are statements for
  the paper's limitations section, not revisions of the committed documents.
* **Does not establish** the effect of the exit convention on the optimised-book net Sharpe at $1bn (the headline), which
  uses the C11 optimiser's frozen-sleeve treatment, a different exit mechanism. That is not examined here.

## 6. Unresolved

* Japan $10bn uncapped: Tier B replicated to 3e-3 per month, not to machine precision (residual 0.032 points). Cause
  not identified.
* Whether the zero-cost exit of uncertified-but-alive names should stand: a decision for the owners of the pipeline,
  not for this diagnostic.
* Coverage association rests on three countries.

## 7. Provenance and checks

* `results/cost_parity_diagnostic/parity_monthly_*.csv.gz` (per cell-month, all 8 variants split into spread+commission,
  impact and borrow, plus exit classification), `parity_summary.csv`, `parity_report.txt`, `tables.md`,
  `dtv_support.csv`, `MANIFEST.json` (SHA-256, git state, versions, regeneration commands).
* `--stage summarize` regenerates the summary and report from the tracked monthly files and `results/capacity_return_difference/`.
  `--stage run` and `diag_dtv_support.py` need the frozen data, stage-02 predictions and the git-ignored decile weights.
* Tests: `tests/validation/test_cost_parity_attribution.py` (attribution is efficient and exact for additive effects;
  the cost split is exact).
