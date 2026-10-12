# Blocker ledger

**Date:** 2026-10-12. State at the finalization checkpoint. Frozen commits: `b8e21ba`, `ac669f2`, `316464d`, `082ca0c`,
`3d062c8`, `7ce1308`, `a560e19`, `4bad8e3`, `0d2437a`, `3ea8342`, `21fffb6`, `bd9c8f7`. Nothing below is executed or
decided by this document; it records who must decide what, and what unblocks each workstream.

**Owners.** *Pipeline owner*: the owner of the evaluation pipeline, **not yet named by the team** (naming one is itself
outstanding). *Maham*: protocol and statistics owner (workstream C). *Absar*: data and C5/C6 owner (workstream A).
*Harshit*: workstream B.

## 1. Workstream status

| # | Workstream | Status | Blocked by |
|---|---|---|---|
| W1 | Cost-calibration sensitivity (S0, S1, S2 repricing of frozen weights) | **Blocked.** S1 (k about 0.51) and S2 (k about 0.95) approved in principle as proxy scenarios; S0 frozen. Not authorised to run. | B1, B3 |
| W2 | G multiplier grid and R borrow grid | **Not adopted.** Not described as preregistered or countersigned. | B2 |
| W3 | A2 2021-2025 outcome lockbox, integration, training, backtesting | **Sealed and prohibited.** | B4, B5, B6, B7, B8 |
| W4 | Phase 2 as-run record and diagnostic | **Frozen.** No silent update. Open item: Japan $10bn uncapped replicated only to 3e-3 per month (residual 0.032 points). | none (carried as a limitation) |
| W5 | Output-collision guard | **Partial coverage** (audit-named writers plus wedge, stage 06 and figure tools). | none; see section 3 |
| W6 | Statistical and amendment sign-offs | **Open.** | B9 |

## 2. Blockers

| ID | Owner | Exact outstanding decision | Condition for unblocking | Unblocks |
|---|---|---|---|---|
| **B1** | Pipeline owner (to be named) | A **written ruling** on how the evaluation treats (a) live-but-uncertified names, (b) temporarily unpriced holdings, (c) panel leavers (no price-panel row). Zero-cost liquidation must not be the default merely because inputs are unavailable. Options: carry at drifted weight (documented optimiser convention), charge at last certified inputs (labelled imputation), zero cost (labelled as-run limitation only), or unresolved. | The ruling is recorded in `EXIT_POLICY_GATE_2026-10-12.md` (section 6), or the team records an explicit decision to proceed with it unresolved and labelled. If the carry convention is chosen, the evaluation change is a separate reviewed task and its results a **new, labelled** analysis; Phase 2 is not updated. | W1 (and the exit-policy condition for W3) |
| **B2** | Maham | Check the cost-multiplier grid {0.5, 1, 2, 3} and the borrow grid {0.3, 0.6, 1, 4.3, 7}% against the **signed protocol**. The values appear in `configs/base.yaml`, the withdrawn PLAN_002 builder and `workstream_a_frozen_decisions.json` (6B), but whether they are countersigned is unverified. | A written statement of which values, if any, are in the signed protocol. Until then neither grid is run or described as preregistered or countersigned. | W2 |
| **B3** | Harshit, on explicit authorisation | **Authorisation to execute** the S0/S1/S2 repricing. Approval in principle is not authorisation. | B1 cleared; an explicit instruction to run; `sigma_ref(c)` and the resulting `k` values computed from inputs and written to a read-only registry before any outcome; the five pre-run tests written and passing (registry equals the approved settings; S0 reproduces committed numbers bit for bit; separate directories cannot overwrite each other; bisection fails loudly if monotonicity fails; the `k` formula). | W1 |
| **B4** | Maham and Absar | **Countersign amendment 001E** (draft `4bad8e3`; parent fingerprint and N = 64 unchanged). | Both countersignatures recorded; any edits made in the amendment before the lockbox opens, not after. | W3 |
| **B5** | Harshit (decision by Maham) | **Accept the 2020 exposure audit.** Finding: all 39 real prediction files and 201 real weight files end before 2020; 2020 is classified development-period. | Maham accepts the audit and classification, or amends them in 001E. | W3 |
| **B6** | Harshit | **Resolve three unclassified artefacts**: one prediction file dated 9 Oct spanning 1996-2020, and two `adaptive_hedge` weight files dated 20 Sept. Panel and origin cannot be established from the manifests. | Each is classified from its run record, or removed from `outputs/`, and the result is recorded in 001E section 2. | W3 |
| **B7** | Absar (with Maham) | **Record the source decisions.** D1 Japan TERM: draft adopts BOJ `FM02 STRAK_STRACDN2DB04` from 2022-04, rejects JBA TIBOR, default no splice. D2 India CREDIT: no extension, no bridging. D3: written confirmation that Germany CREDIT, the OECD inflation dataflow, India DRATE and TERM, and Japan CREDIT are refreshed on the frozen normalisation. | Both decisions signed off or their stated defaults accepted in writing; D3 confirmed in writing by Absar. | W3 |
| **B8** | Maham and the team | The exit-policy condition for the extension: record the B1 ruling, or an explicit decision to proceed unresolved and labelled. | As B1. | W3 |
| **B9** | Maham | Remaining sign-offs: countersign 001A-001D as retracted; the economic-arm ruling; `sharpe_difference_test` and `mean_difference_test` (the influence-function annualisation), Holm versus a max-statistic bootstrap, and the studentised-versus-percentile question. | Written sign-off or amendments for each item. | W6 |

## 3. Output-collision guard coverage (W5)

**Guarded:** the wedge tool; `exp_design_identifiability`; `exp_friction_horse_race`; `exp_112a_event_study`;
`exp_wedge_test`; `exp_tals_overhang`; `pipelines/07_adaptive_combine`; `pipelines/06_after_tax_eval` summary; the figure
tool. **Not guarded:** the other writers listed in `PHASE3_REPRODUCIBILITY_2026-10-12.md`. Coverage is the audit's named list,
not every writer. Extending it needs no approval and no experiment; it is housekeeping to do when those tools are next touched.

## 4. Prohibited until further approval

No cost-calibration sensitivity execution; no multiplier or borrow-grid sweep; no opening or integrating A2 outcome
data; no training or backtesting on the 2021-2025 extension; no re-optimisation, change to frozen research settings, or
silent update to Phase 2 results.
