# Manuscript evidence map

**Date:** 2026-10-14. **Branch head when written:** see the overnight work log. Internal researcher-led compilation; **not** external statistical sign-off, and no approval by any other person is implied. The manuscript itself was **not** modified, no historical number was recomputed, and no withdrawn result is restored. Every figure below is quoted from a committed document or artifact; where I could not trace a figure to an artifact I say so.

Status vocabulary: **current** (supported by committed artifacts, wording constraints below apply), **withdrawn** (never to be restated), **superseded** (replaced by a named later analysis), **exploratory** (disclosed, not claimed), **unresolved** (depends on an open item). "Depends on `carry_v1`" means the underlying numbers were produced under the `as_run` exit treatment (`after_tax_backtest` default, commits through `ac669f2`) and the exit ruling of 2026-10-13 (`docs/EXIT_POLICY_RULING_AND_001E_RESPONSE_2026-10-13.md`) may change them; the revised analysis (Phase C) has not been run and does not inherit confirmatory status.

Artifact commit hashes below are the last commit touching the file (`git log -1 -- <path>`).

## 1. How the corpus is organised (what governs what)

* The only prose that resembles a manuscript is `docs/PAPER_2026-10-09_FULL_ACCOUNT.md` (last touched `b8e21ba`). It is an internal full record, not a submission draft, and its abstract and introduction predate Phase 2.
* Authority order for the capacity result: `docs/RESULTS_CAPACITY_RETURN_DIFFERENCE_2026-10-10.md` and `results/capacity_return_difference/` (`ac669f2`, Phase 2) over the Sharpe-point capacity figures in the PAPER, STATUS and RESULTS_CAPACITY_CHANNEL documents.
* Authority order for withdrawn items: `docs/FINALIZATION_AUDIT_2026-10-09.md` section 1.2 and `docs/CONSISTENCY_PASS_CHANGELOG_2026-10-10.md` (`b8e21ba`).
* Inference corrections of 2026-10-13 (`26957cc`, `docs/INFERENCE_AUDIT_2026-10-13.md`) change which statistics would move if re-run (section 4 below).

## 2. Claim table

Columns: ID; claim (as it would appear); supporting artifact; commit / manifest; status; sample, market, book, cost convention; test and multiplicity; limitations and **permitted wording**; depends on `carry_v1`?

### 2.1 Abstract and framing

| ID | Claim | Artifact | Commit / manifest | Status | Scope | Test / family | Limits and permitted wording | `carry_v1` |
|---|---|---|---|---|---|---|---|---|
| A1 | At a $1bn mandate the net-of-cost Sharpe of the optimised book is not distinguishable from zero (t = +0.53 DEU, +0.82 IND, +0.18 JPN). | `FINALIZATION_AUDIT` 1.1; `PAPER` 1 (abstract); produced by `tools/exp_after_tax_inference.py` | `44803e9`, `b8e21ba`; no tracked result table (outputs/ is git-ignored) | **current**, but not re-derivable from tracked results | 2009-2019, 132 months, optimised book, $1bn, registered cost model, `as_run` exit | HAC t of the net Sharpe computed inside `exp_after_tax_inference.py` (own Newey-West on the standardised series, not `sharpe_se`) | Say "not distinguishable from zero at this power". Unaffected by the 2026-10-13 `sharpe_se` correction because that tool does not call `sharpe_se`. Do not say "ML alpha does not exist". | **Yes** (uses `after_tax_backtest`) |
| A2 | The gross decile signals carry real information (gross SR +2.31 / +1.20 / +1.28, t = +7.14 / +3.19 / +4.11). | `FINALIZATION_AUDIT` 1.1 | `44803e9` | **current**; source table not tracked | gross, decile books, 3 markets | per-market t | Gross, before costs; do not combine with executable claims. | No (gross) |
| A3 | Four surviving results are statements about channels and differences, not about a profitable strategy. | `PAPER` 1 | `b8e21ba` | **current framing** | all | n/a | Keep this framing sentence. | Partly |
| A4 | Coverage-asymmetry hazard: a 35-point cost-input coverage asymmetry manufactured a significant t = -6.10 contrast that survived two robustness checks. | `PAPER` 1 and 9-10; `AMENDMENT_001D` retraction header; memory note on coverage asymmetry | `b8e21ba` | **current** (methodological; the t = -6.10 itself is withdrawn as a finding) | DEU vs IND panels | n/a | Quote as a worked failure, never as a result. | No |

### 2.2 Capacity findings

| ID | Claim | Artifact | Commit / manifest | Status | Scope | Test / family | Limits and permitted wording | `carry_v1` |
|---|---|---|---|---|---|---|---|---|
| C1 | **B(A)**: the annualised net-return difference between the capped and uncapped decile composites, in percentage points of NAV per year, is monotone increasing in AUM across the 35 valid rungs (DEU 11, IND 10, JPN 14). | `docs/RESULTS_CAPACITY_RETURN_DIFFERENCE_2026-10-10.md`; `results/capacity_return_difference/tierB_*.csv`, `tables.md` | `ac669f2`; `results/capacity_return_difference/MANIFEST.json` (17 SHA-256, `git_dirty_when_written = true`) | **current**; Tier B primary, Tier A shown beside it | 2009-01 to 2019-12; capped vs uncapped decile composites (equal-weighted summary of 8 independently simulated full-AUM variants, not an investable fund); registered cost model, 1% modelled borrow, tax-exempt regime | `mean_difference_test`, 4,000 replications, block 6, seed 0, Holm within country over valid rungs; intervals unadjusted | Large B at large rungs is the cost of a self-destroying uncapped plan: uncapped terminal wealth is below 0.1 at 6/11 DEU, 7/10 IND, 4/14 JPN rungs. Permitted: "an accounting difference against an infeasible comparator", **not** realised performance, **not** a Sharpe-point equivalent. At DEU $100k and $300k Tier B B is -0.52 and -0.01 (Holm p 0.86, 1.00): not distinguishable from zero. Tier A / Tier B costs are not fully explained. | **Yes**, and the Phase C revised analysis is projected not estimable for every rung under the frozen rule (see run-readiness) |
| C2 | Insolvent comparator rungs (DEU 3, IND 4, JPN 0) get no B. | same | `ac669f2` | **current** | rung-level | n/a | Never interpolate or draw a value there. | Yes |
| C3 | "The capacity channel is +6.80 (DEU $100mn), +3.19 (IND $30mn), +6.92 (JPN $1bn) Sharpe points at the largest solvent rung." | `PAPER` 1 (lines 44-55), 8.9 (lines 902-948); `STATUS` CURRENT STATE (lines 20-24); `FINALIZATION_AUDIT` 1.1 (line 22); `RESULTS_CAPACITY_CHANNEL` (lines 17, 34, 44, 99, 125, 308) | `b8e21ba`, `44803e9` | **unresolved - do not quote.** Phase 2 shows the uncapped composites at exactly these rungs are near-ruined (Tier B terminal wealth 7.7e-10, 2.6e-06, 6.7e-06), so a Sharpe-point difference against them is the kind of comparison already withdrawn at $1bn/$10bn | matched-book accounting, Sharpe difference | `sharpe_difference_test`, Holm across 8 cells | Not restorable as a headline. If shown at all, mark as an accounting difference against a near-ruined comparator, next to C1. | Yes |
| C4 | The $1bn and $10bn German and Indian capacity gains (+8.92/+9.26, +5.69/+5.97), the "asymptotic channel", the sign flip and crossover, and `crossover ~ k^-2`. | `FINALIZATION_AUDIT` 1.2 | `44803e9` | **withdrawn** | | | Never restate as findings. | n/a |
| C5 | The cap's effect is zero where slack and increases with how hard it binds ("dose-response in cap slack"). | `RESULTS_CAPACITY_CHANNEL` 2; `PAPER` 6.2.2 | `b8e21ba` | **current as a pattern on solvent rungs**, magnitude wording governed by C1 | 3 markets | per-rung paired tests | Monotone in AUM is "as found, not imposed" (Phase 2 point 4). Use return-unit B(A) for magnitudes. | Yes |
| C6 | "There is no mandate size at which the cap meaningfully hurts, at the registered cost calibration." | `PAPER` 1 (line 54) and 6.2 (line 462); `STATUS` | `b8e21ba` | **unresolved**: a cheaper impact calibration produces a small negative region (RESULTS_CAPACITY_CHANNEL 3g) and the S0/S1/S2 cost-calibration sensitivity is not authorised or run | | | Must carry the calibration qualifier in the same sentence. | Yes (cost conventions) |
| C7 | Japan's capacity result is a pre-registered out-of-sample confirmation (D2). | `AMENDMENT_001D` 11; `PAPER` 1 | `b8e21ba` | **current as a prediction scored by code committed earlier**; D3 passed vacuously (-0.0013, p = 0.370) and D5 failed, both reported | JPN | scorecard | "H-FLIP CONFIRMED" is withdrawn. Say D2 confirmed, D3 vacuous, D5 failed. | Yes |
| C8 | Tier A and Tier B cost accounting differ by convention; closure of the discrepancy is partial. | `results/cost_parity_diagnostic/parity_report.txt`, `parity_summary.csv`; `docs/COST_PARITY_DIAGNOSTIC_SPEC_2026-10-10.md` | `316464d`; MANIFEST | **current** | 12 rung-book pairs | Shapley attribution to three conventions | Report as diagnostic, "not fully explained" stays. | Yes |
| C9 | Implementability frontier $106mn / $55mn / $413mn (DEU / IND / JPN). | `FINALIZATION_AUDIT` 1.1; `outputs/capacity_frontier.csv` (git-ignored) | `44803e9` | **descriptive** | | none | Not comparable with break-even capacities; "10-100x below US" is withdrawn. | No |

### 2.3 Tax findings

| ID | Claim | Artifact | Commit / manifest | Status | Scope | Test / family | Limits and permitted wording | `carry_v1` |
|---|---|---|---|---|---|---|---|---|
| T1 | `lt_share_of_gains` is exactly 0.0000 under both flat regimes (DEU 26.375%, JPN 20.315%) and 0.5928 in India. | `RESULTS_TAX_THREE_COUNTRY` 1; `PAPER` 1 item 3 | `b8e21ba` | **current** (statutory fact) | prediction cells, $1bn | none (deterministic) | India's 0.5928 comes from the engine; a statute-driven structural zero elsewhere. | Low (an engine ratio) |
| T2 | The tax channel is significant in the flat-rate jurisdictions on the optimised book (DEU -0.1363, t -4.67; JPN -0.1373, t -4.99; 3 of 8 cells under Holm each) and not under India's exemption (-0.0054, t -1.93). | `PAPER` 1 item 2, 6.3 | `b8e21ba` | **current, with the decile-book qualification** | $1bn, optimised book | paired Sharpe difference, Holm across 8 cells | On the executable decile book the contrast is weaker (DEU -0.070, JPN -0.170, IND -0.009, t -2.14): India is itself borderline. The exact "within 1%" match is **withdrawn**. | **Yes** |
| T3 | The magnitude ordering of the tax drag follows statute type, and the drag level follows turnover, not the rate (n = 3, descriptive). | `FINALIZATION_AUDIT` 1.1; `PAPER` 1 item 3 | `44803e9` | **descriptive** | 3 jurisdictions | none | Turnover is endogenous. Do not write "causes". | Yes |
| T4 | "Taxes are second-order as a channel but decisive for survival." | `PAPER` lines 139 and 150 (section 2.2 and the contribution table) | `b8e21ba` | **withdrawn** ("first-order for survival" withdrawn at `PAPER` 6.3.3, line 591, and `FINALIZATION_AUDIT` 1.2) but still live in the introduction | | | See conflict L1 below. Correct to "second-order as a channel". | n/a |

### 2.4 Design-axis conclusions

| ID | Claim | Artifact | Commit / manifest | Status | Scope | Test / family | Limits and permitted wording | `carry_v1` |
|---|---|---|---|---|---|---|---|---|
| D1 | No ML design axis is detectable at this power: 0 of 42 axis-rungs significant in each of Germany and India (14 rungs x 3 axes), capped decile book, minimum detectable effect 0.25-0.81 Sharpe points at 80% power with 132 months. | `RESULTS_DESIGN_IDENTIFIABILITY_2026-10-09`; `PAPER` 1 item 4, 6.4 | `b8e21ba` | **current as a scoped null** | DEU and IND, capped **decile** book only | `sharpe_difference_test` (paired HAC), Holm | Not measured for Japan or on the optimised book at every rung. "Not detectable at this power", never "no effect". | Yes (returns from the backtest) |
| D2 | Japan conditioning axis, optimised book, $1bn: t = +2.84, effect +0.515; p 0.0045 unadjusted, 0.014 Holm within Japan, 0.041 Bonferroni across nine axis tests. | `PAPER` 1 item 4, 6.4 | `b8e21ba` | **exploratory, unreplicated, not pre-specified** | JPN, optimised, $1bn | as stated | "Disclosed, not claimed." The 2021-2025 extension is deferred. | Yes |
| D3 | "Capacity overwrites ML design identifiability." | `PAPER` 8.6 | `b8e21ba` | **withdrawn** | | | India shows the same null unconstrained. | n/a |
| D4 | Stock-level liquidity-conditioned arm. | `RESULTS_THEME_LIQUIDITY_2026-10-09`, `RESULTS_GATE2_POWER_2026-10-09` | `d4bc8aa`, `6f57b8c` | **stopped** (Gate 1 mostly a size effect; Gate 2 MDE is 70-92% of the cost gap) | | | Not a flagship candidate. | No |

### 2.5 Introduction and contribution statement

| ID | Claim | Artifact | Status | Limits and permitted wording |
|---|---|---|---|---|
| I1 | Capacity measured as an AUM-indexed dose-response in three non-US markets. | `PAPER` 2.3 row 1 | **current as a measurement contribution**; the magnitude of the response is C1 | State it in return units (B) with the comparator caveat. Do not claim "seven orders of magnitude" for the *interpretable* range: insolvent rungs have no B. |
| I2 | Implementability frontier as a new quantity. | `PAPER` 2.3 row 2 | **descriptive** | "Nobody reports it" is a literature claim resting on the prior-art tracker; the full text of @ACM2023 and others is not read (`PAPER` 12.6). Soften to "to our knowledge". |
| I3 | Tax channel by lot-level engine across three regimes, "decisive for survival". | `PAPER` 2.3 row 3 | partly **withdrawn** | See T4 / L1. |
| I4 | Turnover, not the rate, orders the tax drag. | `PAPER` 2.3 row 4 | **descriptive, n = 3** | Do not present as identified. |
| I5 | Design-axis null with power. | `PAPER` 2.3 row 5 | **current as scoped (D1)** | "across 14 mandate sizes and two books" - the two books claim must be checked against D1's scope (decile only). |
| I6 | Not claimed: first on capacity, fragility, survival of frictions, turnover reduction, non-US ML, or adjudicating @NMV2016 vs @AHV2025. | `PAPER` 2.4 | **current** | Keep verbatim. |

### 2.6 Methodology section

| ID | Claim | Artifact | Commit / manifest | Status | Limits and permitted wording | `carry_v1` |
|---|---|---|---|---|---|---|
| M1 | Frozen contract, 2x2x2x2 factorial plus five baselines, 132-month window 2009-2019. | `PAPER` 5.1-5.3; `prereg/AMENDMENT_001A...` | `b8e21ba` | **current** | PLAN_001 fingerprint `cae8140b7e2b7ee4`, N = 64 unchanged. | No |
| M2 | Pre-registration status. | `prereg/`, amendments 001A-001D, 001E draft | | **001E is a draft, non-binding; countersignature withheld by Absar; Maham's review outstanding** | Do not describe 001E as signed. Revised (`carry_v1`) analyses are not confirmatory. | n/a |
| M3 | Inference layer: paired studentised stationary bootstrap for differences; Holm within family; Romano-Wolf, Hansen SPA, DSR, PBO. | `PAPER` 5.5; `INFERENCE_AUDIT_2026-10-13` | `26957cc` | **current after the three corrections**; residual limits listed in the audit (HAC `sharpe_se` over-rejects 10.2% at phi 0.4; SPA over-rejects 6.7% on a boundary; RW one-sided; T = 60 oversize ~9%; A_n form from the library docstring) | Intervals are approximate (2-8 points under-coverage). Studentised CI primary, percentile beside it. Describe as an internal validation. | Not applicable |
| M4 | Exit treatment. | `EXIT_POLICY_GATE_2026-10-12`, `EXIT_POLICY_RULING...2026-10-13`, `EXIT_POLICY_CARRY_V1_SPEC_2026-10-13` | `56f7155`, `f201f9c` | **open**: `as_run` drops a -100% lot without realising the loss and treats a missing C6 row as a closed position by the targets table's delisting return | The paper must state the exit treatment of the reported numbers and that `carry_v1` is implemented but not yet run on the history. | n/a |
| M5 | Two books and why both are needed; the capacity channel cannot be measured on the optimised book. | `PAPER` 5.6 | `b8e21ba` | **current** | | No |

## 3. Statistics that the 2026-10-13 inference corrections would change if re-run (not re-run)

Per `docs/INFERENCE_AUDIT_2026-10-13.md` section 6: per-strategy Sharpe SE / t / p / HLZ columns of `inference_report` (used by `tools/exp_e29_attribution.py`), non-rejected Romano-Wolf `p_adjusted`, the Hansen SPA p-value (can only rise), and interval columns where the studentised interval is adopted. Capacity, tax, matched-book, identifiability and theme results use `sharpe_difference_test` / `mean_difference_test` p-values and do not use the corrected functions; the headline net-Sharpe t-statistics (A1) come from the tool's own Newey-West and are also unaffected. Any manuscript table sourced from `inference_report` (e29 outputs) must be flagged as pre-correction.

## 4. Conflicts between documents, with proposed corrections

None of these has been edited.

| # | Location | Conflict | Proposed correction |
|---|---|---|---|
| L1 | `docs/PAPER_2026-10-09_FULL_ACCOUNT.md` lines 139 and 150 | "shown second-order as a channel but decisive for survival" repeats the withdrawn survival framing that `PAPER` line 591 (6.3.3), `STATUS.md` line 43 and `FINALIZATION_AUDIT` 1.2 withdraw. `tools/check_withdrawn_claims.py` does not catch it (screen, not verification) | Replace with "second-order as a channel"; consider extending the checker with the phrase "decisive for survival" |
| L2 | `PAPER` lines 44-55 (abstract finding 1), 439-440, 685-686, 912-926; `STATUS.md` lines 20-24; `FINALIZATION_AUDIT` line 22; `RESULTS_CAPACITY_CHANNEL` lines 17, 34, 44, 99, 125, 308; `handoff/21` line 11 | Sharpe-point capacity gains (+6.80 / +3.19 / +6.92) are called "established on solvent rungs". Phase 2 (`RESULTS_CAPACITY_RETURN_DIFFERENCE`, `ac669f2`) shows the uncapped comparators at those rungs are near-ruined (Tier B terminal wealth 7.7e-10 DEU $100mn, 2.6e-06 IND $30mn, 6.7e-06 JPN $1bn) | Restate the capacity result in B(A) units with the near-ruined flag; demote the Sharpe-point figures to a clearly labelled accounting difference against a near-ruined comparator, or drop |
| L3 | `PAPER` line 50 | "Japan's comparison book is solvent through $10bn" - technically true (Phase 2 lists JPN as 0 insolvent rungs) but the Japan $10bn uncapped composite has terminal wealth 1.1e-17 (Tier B) | Add the near-ruined flag; do not use "solvent" as an indicator of a plausible comparator |
| L4 | `PAPER` line 54 and line 462; `STATUS` current state | "No mandate size at which it meaningfully hurts" is stated against the registered calibration, but the calibration sensitivity (S0/S1/S2) has not been run and the exit policy is open | Keep the qualifier in the same sentence and add "pending the cost-calibration sensitivity" |
| L5 | `STATUS.md` header "Updated: 2026-10-09 (13:50 IST)" and `PAPER` title block "as of 2026-10-09, 17:10 IST" | Neither mentions Phase 2, the cost-parity diagnostic, the figures, the exit ruling, the inference corrections or the Phase C specification | Add a pointer block or regenerate the status from the later records |
| L6 | `PAPER` 2.3 row 5 ("across 14 mandate sizes and two books") vs `RESULTS_DESIGN_IDENTIFIABILITY` / `PAPER` 6.4 (decile book, Germany and India) | Scope of the design-axis null differs between the contribution table and the results section | Make the contribution row state the DEU/IND decile-book scope |
| L7 | `PAPER` 5.5 "12 unit tests" for `sharpe_difference_test` | Stale count; the suite now has more tests on the inference module | Remove numeric test counts from prose |
| L8 | `docs/PHASE_C_REVISED_ANALYSIS_SPEC_2026-10-14.md` section 1 (regimes, lot methods) vs `docs/PHASE_C_CONFIGURATION_RECOVERY_2026-10-14.md` | The spec was written as if the frozen Phase 2 were the multi-regime after-tax grid; the recovered configuration shows it is the zero-tax capacity comparison | Resolved by a spec addendum before any run (see run-readiness report); not a manuscript conflict |

## 5. Items with no traceable artifact

* The headline net-Sharpe t-statistics (A1) and the gross SRs (A2) are quoted from `FINALIZATION_AUDIT` / `PAPER`; the tool outputs are in git-ignored `outputs/`. Tracked snapshots do not exist for them. A manuscript table needs a tracked, hashed snapshot made with explicit authorisation (it is a regeneration of historical statistics).
* `results/capacity_return_difference/MANIFEST.json` records `git_dirty_when_written = true` at head `b8e21ba`; the exact tree that produced Tier B is not recoverable from git alone (see the configuration recovery).

## 6. Wording that is permitted now

1. The optimised book's net Sharpe is not distinguishable from zero at $1bn in all three markets (as run, `as_run` exit).
2. The participation cap's effect, measured as the annualised net-return difference B(A) against an uncapped plan, is monotone in AUM on valid rungs; at large rungs the comparator is near-ruined and B is an accounting difference, not a gain.
3. Statute determines whether a holding-period channel exists (`lt_share` 0 vs 0.5928); drag ordering by statute type is descriptive.
4. Design axes are not detectable at this power on the capped decile book in DEU and IND; Japan's conditioning observation is exploratory.
5. A coverage asymmetry can manufacture a significant cross-country contrast; here is the worked case and the check that catches it.

Nothing in this map relies on, or restores, a withdrawn Sharpe-point capacity gain.
