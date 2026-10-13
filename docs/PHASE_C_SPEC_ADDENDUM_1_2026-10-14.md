# Phase C specification, addendum 1 (support masks; thresholds confirmed)

**Date:** 2026-10-14. Addendum to `docs/PHASE_C_REVISED_ANALYSIS_SPEC_2026-10-14.md` (commit 0a320cb). Written before the census is run and before any revised outcome exists. Internal researcher-led work; no external sign-off is claimed.

## 1. Support mask per metric

Section 3 of the specification is clarified, not loosened. For every reported metric the support mask is built from **all inputs that metric needs**.

* For a primary after-tax comparison, a month is **unsupported** if any of the following required inputs is unsupported for either side of the comparison: valuation/NAV, return, cost, or tax.
* The unsupported share is computed on the **union** of affected months, each month counted once.
* The tier of a metric (section 3 table) is assigned from that metric's own union share, not from the row's best-supported component. A comparison inherits the worse tier of the two sides.
* Resolved-only diagnostics continue to be labelled diagnostic in every tier above 0%.

## 2. Thresholds (unchanged)

| Unsupported share (union) | Treatment |
|---|---|
| 0% | Fully resolved primary statistics may be reported. |
| >0% and <=5% | Diagnostics only. |
| >5% and <=25% | Diagnostics only; no hypothesis test reported as a finding. |
| >25% | Not estimable under `carry_v1`. |

Note: this addendum states the 0-5% tier as diagnostics only. Section 3 of the original specification allowed resolved-only statistics "labelled diagnostic" in that tier; both readings now coincide as diagnostics only, and inferential families (section 6) already admit tier-1 rows only.

These are researcher-selected reporting cutoffs, not statistically validated thresholds. They are not changed after any outcome is inspected.

## 3. Authorised in this step

An outcome-free input census only (identifiers and membership; no returns, prices, dividends, costs, tax results, NAV or performance values). No historical performance panel, cost sensitivity, re-optimisation, training or A2 evaluation is authorised.
