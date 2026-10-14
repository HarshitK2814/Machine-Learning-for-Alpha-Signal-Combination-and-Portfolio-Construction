# Phase C specification, addendum 2 (eligibility vs support vs exit; metric masks; inference settings; valid-rung rule)

**Date:** 2026-10-14. Addendum to `docs/PHASE_C_REVISED_ANALYSIS_SPEC_2026-10-14.md` (`0a320cb`) and addendum 1 (`d0c1768`). Written **before any revised historical performance outcome exists or has been read**. The settings below are fixed now and are not adjusted in response to any result; a change needs a further dated addendum committed before the affected result is read, stating what was seen. The rulings in section 1 are the researcher's rulings of 2026-10-14 (internal, researcher-led); they are **not** an external or independent review, and no approval by Maham or Absar beyond their documented responses is claimed.

Context (not a premise): census v3 (`results/phase_c_census_v3_2026-10-14`) is outcome-free (membership and presence flags only). Nothing in this addendum depends on what it counted.

## 1. Three different questions, kept apart

| Question | Source | Consequence of "no" |
|---|---|---|
| **Trade eligibility**: may the optimiser buy or sell this name this month? | C1 `in_universe`; a C6 row with certified spread, volatility and ADV | **Held-but-untradeable**, not an exit (below) |
| **Return and valuation support**: can the holding be valued over the month? | C4 row present with usable `ret_next` (and `div_next` for dividends) | Affected account-month is **unresolved** (return) or tax-unsupported (dividend) |
| **Confirmed terminal exit**: did the security leave the investable set permanently, on approved evidence? | an approved terminal-event table (specification section 2); none exists in C1/C4/C6 | Without evidence, a name that has disappeared from C4 stays **unresolved** |

Rules:

1. A previously held position that remains in C4 with usable return and valuation support, but has no certified C6 inputs or is no longer in the C1 universe, is **held-but-untradeable**. The drifted holding is preserved, no discretionary trade is made, and no new position is opened in it until certification returns.
2. The absence of C6 inputs alone creates **no** exit, **no** missing valuation and **no** unsupported transaction cost for a trade that was never made. A cost is unsupported only for a trade that is made (an entry, or a sale that actually executes) and cannot be priced.
3. If a required return or valuation is unavailable, the affected account-month is **unresolved**. It is never filled with zero.
4. A name that has disappeared from C4 is **unresolved** unless approved terminal-event evidence establishes an exit (specification section 2 item 4 admissibility conditions unchanged). The table remains empty.
5. A confirmed exit is processed **exactly once**. A later reappearance of the same name must not close a stale lot at its old value.
6. Missing dividend information remains subject to the frozen primary fail-closed rule (`dividend_missing="unsupported"`, specification section 4).

**Engine consequence, stated so it is not overlooked:** `exit_policy="carry_v1"` as committed (`f201f9c`) takes "no C6 row at the date" as the departure test (`priced_at`) and therefore classifies a C6-lapsed name that is still in C4 as an unresolved exit. That is **not** the rule in 1-5. The corrected rule needs a new, additive, separately versioned exit policy (provisionally `carry_v2`; `as_run` and `carry_v1` and every frozen artifact stay untouched), with synthetic-fixture tests for rules 1-6, before any run. Until then no historical panel can be run under this addendum. This addendum does not itself change any code.

## 2. Metric-specific support masks (extends addendum 1 section 1)

Every month receives three status flags per series: `valuation` (rules 3-4), `cost` (rule 2) and `tax` (rule 6; for the zero-tax regime only a missing dividend can make it unsupported). Each reported metric uses the **union of the months that affect it, counted once**:

| Metric | Mask (months excluded if flagged) |
|---|---|
| Gross return, gross Sharpe, held/frozen-sleeve diagnostics | valuation |
| Net return, net Sharpe, cost drag, capacity return difference B(A) | valuation, cost |
| After-tax return, tax drag, after-tax Sharpe, after-tax comparisons | valuation, cost, tax |
| Paired comparison of two series | union over **both** series |

Unsupported months **make the metric NaN for the whole NAV path from the first affected month** (the `carry_v1` convention is retained); they are never repaired, interpolated or zero-filled. The tier of each metric (addendum 1 section 2, unchanged) is assigned from **that metric's own** union share. A row's tier for one metric does not carry to another. Resolved-only diagnostics stay labelled diagnostic in every tier above 0%.

## 3. Scope: two analysis objects, never mixed

* **Object A: capacity return difference B(A)** (zero tax), configuration recovered in `docs/PHASE_C_CONFIGURATION_RECOVERY_2026-10-14.md`. Net-return mask. Weights: the Tier B re-dumped decile weights.
* **Object B: multi-regime after-tax grid** (statutory regime and `tax_exempt`, HIFO, accrual, 16 cells, three countries, AUM 1e8/1e9/1e10), configuration recovered in `docs/PHASE_C_AFTER_TAX_CONFIGURATION_RECOVERY_2026-10-14.md`, with the DEU 1e9 and IND 1e9 weights labelled "inferred from the index" wherever shown. After-tax mask.

Specification section 1 ("identical to the original Phase 2 invocation") is read as: identical to the recovered configuration of the object concerned. The Phase 2 manifest is the source for Object A only. Results for A and B are reported separately; they enter separate families (section 5).

## 4. Inference settings (fixed)

* **`n_boot = 2000`** for every reported test of the revised analysis (not the as-run 4000 of B(A) and not the 800 cap of the after-tax tables). Seed 0, block length 6, recorded in each manifest. A difference in `n_boot` from the as-run tables is disclosed wherever a revised number is set beside an as-run one.
* **p-values:** the raw bootstrap proportion is reported; **decisions use the add-one form** `(1 + #{|t*| >= |t|}) / (1 + B)`.
* **Intervals:** the studentised interval (`ci95_stud_low/high`) is primary; the percentile interval (`ci95_low/high`) is reported beside it every time. A statement of a difference from zero requires Holm-adjusted add-one p < 0.05 **and** both intervals excluding zero; if the two intervals disagree the result is inconclusive (as in specification section 8).
* Library: the corrected `src/alphacomb/validation/inference.py` at `26957cc`. Remaining limitations carried verbatim from `docs/INFERENCE_AUDIT_2026-10-13.md`.

## 5. Holm family (fixed)

* **Object A:** within country, over the **valid** rungs whose B(A) row is in tier 1 (0% unsupported) for the net mask; one family per country.
* **Object B:** within country x regime x lot method, over all comparator tests whose rows are in tier 1 for the after-tax mask.
* Rows in tiers 2-4, and rungs that are not valid, enter no family; they are counted and listed. Romano-Wolf is a one-sided robustness check; BH secondary; Hansen SPA only for an explicit best-of-many claim (specification section 6, unchanged).

## 6. Source of the valid-rung list (Object A)

The 35-rung list of Phase 2 is **not** imported. Validity is re-derived for the exact Phase C configurations:

1. Support masks and tiers are computed and written to disk first (they use no return value).
2. For each rung that has any tier-1 row, solvency is evaluated with the **frozen rule** of `docs/CAPACITY_RETURN_DIFFERENCE_SPEC_2026-10-10.md` sections 2 and 7, unchanged: a rung is valid only if **no cell-month of either book** (8 cells x 2 books, each a separately funded account at the full AUM) has a net return at or below -100%. Solvency is a property of each cell; the composite-only rule is not used.
3. The derived list is written to a file (with the minimum monthly net return per cell and the rule text) **before any inference test is run**, and is not edited afterwards. Rungs failing the rule get no B(A) ("INSOLVENT COMPARATOR"), as in the frozen specification; no terminal-wealth threshold is added (the solvent-but-nearly-ruined caveat of the Phase 2 specification stands and must be attached to every reported value).
4. Because solvency uses return values, it is an outcome-derived filter; it is applied once, by a rule fixed here, and its inputs are the supported months of tier-1 rows only (an unsupported month is neither solvent nor insolvent evidence).

## 7. Unchanged

Thresholds (0% / up to 5% / up to 25% / above 25%) and their treatment, the outcome rules, the inference families' definitions apart from the scoping above, the dividend policy, the cost convention (S0, k = 1.0) and the output-isolation rules of specification section 7 are unchanged. Researcher-selected reporting cutoffs, not statistically validated thresholds; not changed after outcome inspection.

## 8. Authorised in this step

Documentation only. No historical performance panel, cost sensitivity, re-optimisation, training or A2 evaluation is authorised, and the `carry_v2` policy of section 1 is not yet written.
