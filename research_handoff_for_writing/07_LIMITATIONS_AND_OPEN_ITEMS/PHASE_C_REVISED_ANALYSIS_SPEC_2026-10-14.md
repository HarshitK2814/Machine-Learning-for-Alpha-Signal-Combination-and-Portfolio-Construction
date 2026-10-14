# Phase C: specification of the revised 2009-2019 `carry_v1` analysis

**Date:** 2026-10-14. **Status:** DRAFT SPECIFICATION, written and committed BEFORE any revised historical panel is run. **Nothing in this document was informed by a revised-analysis outcome.** No revised panel has been run; none may be run until this specification has been reviewed and the run is explicitly authorised.

**Nature of the work:** internal researcher-led analysis. It is not external statistical sign-off, and no approval, signature or review by any other person is claimed or implied.

**Classification:** REVISED ANALYSIS. It does not inherit the confirmatory status of PLAN_001 (fingerprint cae8140b7e2b7ee4, N=64) automatically. It is not an amendment to PLAN_001. The original as-run Phase 1 / Phase 2 record stays intact and authoritative for what was run. Whether any revised result can be called confirmatory is a question for Maham's review (outstanding), not for this document.

Code under this specification: commit 26957cc (inference corrections) on top of f201f9c (`carry_v1`). The run must record the exact commit hash it executes.

---

## 1. Purpose and scope

Re-evaluate the frozen Phase 2 portfolio weights under (a) the exit treatment ruled on 2026-10-13 (`exit_policy="carry_v1"`) and (b) the corrected inference procedures, so that the headline after-tax comparison no longer depends on the as-run treatment of names that leave the panel.

* **Weights:** the frozen weights only. No re-optimisation, no training, no new strategies, no parameter grids.
* **Strategies, countries, regimes, lot methods, AUM, dividend yield, as-of, sample window:** identical to the original Phase 2 invocation. They are to be copied from the Phase 2 run manifest/command record. Reading that record is a configuration read, not an outcome read. If any value cannot be recovered from the record, the run does not start and the gap is reported instead of guessed.
* **Out of scope:** S0/S1/S2 repricing (Phase D), A2 extension / lockbox (deferred), 001E items D3 and shortability reconciliation (deferred), any cost recalibration.

## 2. Exit evidence (terminal-event requirements)

1. Exit evidence may come only from schema or contract metadata that existed before this analysis. A missing C6 row is **not** confirmation of a delisting or a mandatory corporate-action exit.
2. **Finding already established from the schema (not from outcomes):** C1, C4 and C6 contain no terminal-event field. Therefore the exit-evidence table for this run is **empty**.
3. Consequence, fixed in advance: every name that leaves the priced panel is classified **unresolved** from its first absent month. No terminal return, liquidation, zero return or zero cost is invented for it.
4. A future evidence source is admissible only if all of the following are recorded before it is read into any run: named source; the rule that maps source records to `kind` in {`delisting`, `mandatory_corporate_action_exit`}; event dates; provenance; and, for `liquidation_cost_frac`, a stated basis. Without a stated basis the liquidation cost is **unsupported**, never zero. Adding such a source later creates a new, separately versioned run, not an edit of this one.
5. Terminal return (C4) and liquidation cost are kept separate, as ruled.

## 3. Unresolved-month treatment and reporting rule

Under `carry_v1`, NAV is NaN from the first unresolved or unsupported month; resolved-only values are the `*_diag` columns and are **diagnostics**, labelled as such wherever shown.

Quantities reported for every country x strategy x regime x lot-method row, before any performance number is read:

* `n_months`, `n_unresolved_months`, `n_unsupported_cost_months`, `n_unsupported_tax_months`, and the unresolved share of months;
* first unresolved month;
* materiality of unresolved exposure: `stale_gross` and `unresolved_exit_gross` as a share of NAV (peak and mean over unresolved months).

Predefined reporting tiers, by unresolved share of months in the row (researcher-set thresholds, fixed now, before outcomes):

| Unresolved share | Treatment |
|---|---|
| 0% | Row is fully resolved; performance statistics reported as primary. |
| >0% and <=5% | Resolved-only statistics reported, labelled diagnostic, with the counts above beside them. |
| >5% and <=25% | Resolved-only statistics reported as diagnostic only, with a prominent caveat; **no hypothesis test is reported as a finding** for the row. |
| >25% | Row declared **not estimable** under `carry_v1`. No Sharpe, drag or comparison is reported as a result. |

Because the schema gives no terminal-event field (section 2), it is expected that many rows fall in the upper tiers. That is a finding about data adequacy and will be reported as such. It will not be tuned away by changing thresholds, evidence rules or the window after the fact. Resolved-only diagnostics are never presented as the NAV path, and never as the as-run number.

## 4. Missing-dividend policy

* **Primary:** `dividend_missing="unsupported"` (fail closed). A month with a held name whose dividend is missing is tax-unsupported; the tax-dependent quantities are NaN for that month.
* **Secondary, reported separately and classified exploratory:** `dividend_missing="flag_only"`. It is shown only beside the primary, never replaces it, and never feeds the primary inference family.
* Reported for both: number and share of tax-unsupported months, and the dividend-missing counts.

## 5. Cost convention

* Cost convention is exactly the as-run one: `--cost-multiplier 1.0`, unchanged AUM and impact scaling, unchanged cost inputs. This is the S0 convention (k = 1.0). No recalibration is done in Phase C.
* Under `carry_v1`, a month's cost is NaN (unsupported), never zero, wherever a trade or borrow cannot be priced (stale or unresolved names).
* S1 (k ~ 0.51) and S2 (k ~ 0.95) belong to Phase D and need their own authorisation and specification note.

## 6. Inference methods

All from the corrected library at 26957cc:

* Sharpe standard error: HAC (Newey-West on the Sharpe influence function). Paired differences: Ledoit-Wolf studentised stationary bootstrap, block length 6 (the library default), Politis-Romano indices.
* **Primary interval:** studentised (percentile-t) `ci95_stud_low/high`. The percentile interval `ci95_low/high` is reported beside it every time an interval is quoted. Intervals are described as approximate; the audit shows 2-8 points of under-coverage.
* **Bootstrap draws:** `n_boot = 2000` for every reported test, including after-tax per-cell tests (the as-run 800 cap is not used). Fixed seed recorded in the manifest.
* **p-values:** the raw bootstrap p is reported, and so is the add-one form `(1 + #{|t*| >= |t|}) / (1 + B)`, which cannot be exactly zero. Decisions use the add-one form. This is a revised convention versus the as-run tables, where 12/35 solvent Tier B raw p-values were exactly 0.
* **Multiplicity:** Holm over a family fixed here: all after-tax-versus-comparator paired tests that fall in rows with 0% unresolved months (tier 1) within one country x regime x lot-method block, solvent rungs only (insolvent rungs excluded and counted). Romano-Wolf step-down reported as a robustness check; it is one-sided and is labelled so. BH is reported only as secondary. Hansen SPA is reported only if an explicit "best-of-many" claim is made, with the disclosed 6.7% boundary over-rejection.
* Rows in tiers 2-4 (section 3) enter no inferential family.
* Known remaining limitations carried verbatim from the audit (section 6 of `docs/INFERENCE_AUDIT_2026-10-13.md`): HAC `sharpe_se` still over-rejects at high persistence (10.2% at phi = 0.4); T = 60 oversize about 8.7-9%; SPA boundary over-rejection; `A_n` form taken from the library docstring, not checked against the paper.

## 7. Output isolation and provenance

* Output root: `results/revised_2009_2019_carry_v1_<run-date>/<country>/`, a new versioned directory. `carry_v1` already refuses a missing `--out`, an `--out` directly in the outputs root, `--overwrite`, and any existing path.
* Phase 1 / Phase 2 artifacts, `results/capacity_return_difference`, `results/cost_parity_diagnostic`, `results/figures`, `outputs/`, `data/` and prereg files are read-only for this analysis. The staged-diff frozen-path check is repeated before committing outputs.
* Every output directory carries a manifest: commit hash, the full command line, config values, input file hashes, seed, `n_boot`, the evidence-table state (empty), and the label "REVISED ANALYSIS - not confirmatory".
* Each summary file carries the basis label (resolved-only diagnostic vs full) and `exit_policy`.
* The run is executed twice into two fresh directories; outputs must match exactly or the discrepancy is reported before anything is interpreted.

## 8. Acceptance criteria

*Run validity* (necessary before any number is read):

1. Tree clean at the recorded commit; full test suite passing at that commit.
2. The configuration equals the Phase 2 configuration except the declared changes (`exit_policy`, inference corrections, `n_boot`, p-value convention).
3. Output isolation checks pass; the two-run reproducibility check matches.
4. Section 3 counts are produced and the tier of every row is assigned before performance columns are inspected.

*Statistical statement* (what may be written in the manuscript from a row):

* A row in tier 1 may support the statement "differs from zero / from the comparator" only if the Holm-adjusted add-one p < 0.05 **and** both the studentised and percentile intervals exclude zero. If the two intervals disagree, the result is reported as inconclusive.
* Direction and size are compared with the as-run result and the difference is reported in either direction. A revised result that is weaker, reversed or not estimable is reported as such.
* No capacity gain withdrawn earlier is revived. No threshold, tier, family or convention in this document is changed after any revised result has been seen. Any change requires a dated addendum, committed before the affected result is read, stating what was seen.

## 9. Deliberately unspecified until authorised

Running anything. The first authorised step would be an outcome-free input census (counts of names leaving the panel per country and window, no returns or performance read) to confirm the tier mechanics are meaningful; it needs its own go-ahead.

## 10. Governance ledger (excerpt)

* *Independent technical work done:* `carry_v1` (f201f9c); inference audit and corrections (26957cc); this specification.
* *Outstanding approvals:* Maham acknowledgement/review of the exit ruling and of any change to confirmatory results; 001E countersignatures; B2/B3/B5/B6/B9.
* *Reclassified:* all Phase C outputs = revised analysis; the `flag_only` dividend variant = exploratory.
* *Deferred:* A2 extension; 001E D3; shortability reconciliation; external statistical review.
