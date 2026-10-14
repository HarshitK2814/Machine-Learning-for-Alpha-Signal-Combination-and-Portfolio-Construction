# Phase C run-readiness report, version 2 (2026-10-14)

**Verdict: NOT READY. Do not run the revised historical panel.** The corrected classification (census v3) removes the reason given in version 1 for the 560 "not estimable" series, but the projection does not change: every series is still above the 25% unresolved threshold under the rules ruled on 2026-10-14. The new cause is different and is a data-support fact, not a classification artefact (section 2). Version 1 (`docs/PHASE_C_RUN_READINESS_2026-10-14.md`) is kept as the historical record; its section 2 attributes the result to C6 lapses, which is the classification this version corrects.

Internal researcher-led preparation; not external sign-off; no approval by Maham or Absar beyond their documented responses is claimed. **No historical performance panel, cost sensitivity, re-optimisation, training or A2 evaluation was run.** No numerical return, price, dividend, cost, tax or performance value was read, printed or summarised: the census reduces `ret_next`, `div_next` and the C6 certification fields to booleans at load time.

## 1. Deliverables of this step

| Deliverable | Where | Commit |
|---|---|---|
| Census v3 (script, 15 synthetic tests, outputs, manifest); v1 and v2 untouched | `tools/phase_c_input_census_v3.py`, `tests/tools/test_phase_c_input_census_v3.py`, `results/phase_c_census_v3_2026-10-14/` | `e6e5d16`, `ae8b058` |
| Recovered multi-regime after-tax configuration, with provenance and gaps | `docs/PHASE_C_AFTER_TAX_CONFIGURATION_RECOVERY_2026-10-14.md`, `tools/phase_c_recover_after_tax_config.py`, `results/phase_c_after_tax_config_recovery_2026-10-14/` | `132396a` |
| Specification addendum 2 | `docs/PHASE_C_SPEC_ADDENDUM_2_2026-10-14.md` | `14fd8ae` |
| Targeted corrections to live documents | `docs/LIVE_DOCUMENT_CORRECTIONS_2026-10-14.md` and the files it lists | `b7b26b8` |
| This report | `docs/PHASE_C_RUN_READINESS_V2_2026-10-14.md` | next commit |

## 2. Census v3: what it counted (membership and flags only)

Fields and predicates accessed (full list in `MANIFEST.json`): C1 `date, permno, in_universe`; C4 `date, permno` and flags `ret_next` finite, `div_next` finite; C6 `country, date, permno` and the certification flag (spread, sigma_d, adv_usd finite with spread >= 0, sigma_d >= 0, adv_usd > 0, the engine's own predicate); weights `date, permno, w` as `w != 0`. Not read: price levels, market equity, borrow fee, FX, `r_1m`..`r_12m`, any cost, tax, NAV or performance value. No terminal-event field exists in C1, C4 or C6.

Method: a membership and flag simulation of each of the 560 weight series (35 rung directories x 2 books x 8 cells; DEU 176, IND 160, JPN 224), not the engine. Held-but-untradeable names are carried at drift; a name is unresolved if it has no C4 row or its `ret_next` flag is false; unresolved is sticky (the `carry_v1` convention).

| Quantity | DEU | IND | JPN |
|---|---|---|---|
| Series | 176 | 160 | 224 |
| Series in tier >25% for gross, net and after-tax masks | 176 | 160 | 224 |
| Unsupported share of months (min to max over series) | 0.894 to 0.992 | 0.893 to 0.992 | 0.902 to 0.992 |
| First unresolved month (range over series) | 2009-02 to 2010-03 | 2010-03 to 2010-04 | 2009-02 to 2010-02 |
| Held or target names that **disappear from C4** (no row) | **0** | **0** | **0** |
| Unresolved because `ret_next` is unusable | all | all | all |
| Most names held-but-untradeable at one time (no C6 row or not in C1 / uncertified) | 48 / 35 | 140 / 3 | 27 / 1 |
| Months with an **entry** lacking certified cost inputs | 0 | 0 | 0 |
| Months with a missing `div_next` on an exposed name | 2019-12 only (132 of 176 series) | none | 2012-02 only (84 of 224 series) |
| Unresolved names that later reappear in C4 | 0 | 0 | 0 |

Support flags over **all** C4 rows in the window (`c4_support_flag_crosstab.csv`): a C4 row with unusable `ret_next` is rare in the universe and common outside it.

| | In-universe rows | Rows outside C1 universe |
|---|---|---|
| DEU | 201 of 50,004 unusable (0.40%) | 8,698 of 75,799 (11.5%) |
| IND | 29 of 44,233 (0.07%) | 113,467 of 471,168 (24.1%) |
| JPN | 32 of 247,412 (0.01%) | 22,197 of 263,186 (8.4%) |

Position of the unusable rows in a name's C4 life (`c4_unusable_ret_next_position.csv`; positions only, **not** interpreted as delistings): most are interior with a later usable return (DEU 6,360, IND 91,195, JPN 19,340), fewer are interior with no later usable return (1,880 / 21,665 / 2,031), and only 659 / 636 / 858 are a name's final C4 row.

**What this means.** The correction removes the exit classification question for held names: **no held name leaves C4**, no entry lacks cost inputs, and a C6 lapse alone does not make a month unresolved. What remains is that a held-but-untradeable name is mostly one that left the universe, and C4 supplies no usable return for it in a minority of its months (about 8-24% of its out-of-universe rows). Under the rule that a missing return makes the account-month unresolved, and under the carried-over `carry_v1` convention that unresolved status persists (spec `docs/EXIT_POLICY_CARRY_V1_SPEC_2026-10-13.md` rows on stale names), a few months after start every series has at least one such name and is above 25%. It is not an artefact of classification. It is an input-support limit.

Limitations of the census (also in the manifest): it is a membership simulation and does not replicate the optimiser's trades; it assumes a tradeable non-target carried name is sold and a frozen one is carried; `ret_next` usability is a finiteness flag, so a present but wrong terminal return would not be detected.

## 3. Specification and implementation: agreement now

| Item | Specification (with addenda 1 and 2) | Implementation | Agree? |
|---|---|---|---|
| Unresolved NAV, tier thresholds, dividends fail-closed | as before | `carry_v1` (`f201f9c`) | yes |
| **Departure test** | held-but-untradeable if the name is still in C4 with usable return; unresolved only if it disappears from C4 or the return is unusable | `carry_v1` uses "no C6 row" (`priced_at`) and treats a C6 lapse as an unresolved exit | **No. A new additive policy (provisionally `carry_v2`) with tests is required before any run** |
| Exactly-once exit; no closing a stale lot on reappearance | addendum 2 rule 5 | `_confirmed_event` / `used_events`, `unresolved_exit` excluded permanently | yes for `carry_v1`; to be re-tested in `carry_v2` |
| Per-metric union support masks | addendum 2 section 2 | statuses exist per month; the union per metric is computed only by the census, not by an analysis script | **not implemented as a reusable utility** |
| `n_boot` 2000; add-one p; studentised primary + percentile | addendum 2 section 4 | library returns the raw proportion; runner must compute add-one | **not implemented** (runner does not exist) |
| Valid-rung list re-derived before inference | addendum 2 section 6 | no tool | **not implemented** |
| Two objects (B(A) and the after-tax grid) | addendum 2 section 3 | runners: Phase 2 tool has no exit policy and writes into tracked `results/`; stage 06 has `--exit-policy carry_v1` | **a new runner and tests are required** |

## 4. Run-readiness checklist

| # | Item | Status |
|---|---|---|
| 1 | Specification, addendum 1 and addendum 2 committed before any outcome | **done** |
| 2 | Outcome-free support census with tests and manifest | **done** (v3) |
| 3 | Configuration recovery for **B(A)** | **done** (with gaps: original Tier B code tree not recoverable, no run-time weight hashes) |
| 4 | Configuration recovery for the **after-tax grid** | **done**; DEU 1e9 and IND 1e9 weights inferred, all seven run commands from the session record only |
| 5 | Live-document contradictions (survival; near-ruined comparators) | **done** (dated qualifications); `handoff/21` unedited by design; L4-L8 open |
| 6 | `carry_v2` exit policy (held-but-untradeable vs unresolved) with synthetic tests | **blocker, not written** |
| 7 | Per-metric support-mask utility with tests | **blocker, not written** |
| 8 | New runner(s) with output isolation (`output_guard`), manifest, two-run reproducibility, add-one p, `n_boot` 2000, valid-rung derivation | **blocker, not written** |
| 9 | Decision on the stickiness convention and on names whose C4 return is unusable | **blocker, decision needed (section 5)** |
| 10 | Reviewer acknowledgement (Maham) of the exit ruling's consequence for confirmatory results | **outstanding** (external; not claimed) |
| 11 | Full suite, hygiene and withdrawn-claims screens on the final tree | see section 6 |
| 12 | Authorisation to run any historical panel | **not given** |

## 5. Decisions needed from the people who own the ruling (not taken here)

1. **Stickiness.** `carry_v1` makes an unresolved or stale name unresolved for every later month (NAV is NaN from the first affected month). The 2026-10-14 ruling says the affected account/month is unresolved. Whether one unusable return month should invalidate the whole remaining path (the `carry_v1` convention, adopted in addendum 2) or only the affected month changes the tiers materially. It cannot be decided from outcomes and I did not compute the alternative, to avoid choosing a rule after seeing counts. If a different convention is chosen it needs an addendum before any run.
2. **What a missing C4 `ret_next` for a held name means.** C4 gives 8-24% unusable returns outside the universe, mostly in the interior of a name's life. Neither "no return" nor "return of zero" is supportable; the open question is whether the policy should instead require liquidating a name that leaves the universe at a stated, certified cost, which would be a different ruling from the one recorded.
3. **Scope.** Object A (B(A)) and Object B (after-tax grid) both, or one first.

## 6. Validation of this step

Recorded in the work log entry for this step (`docs/OVERNIGHT_WORK_LOG_2026-10-14.md`, second section) after the final-tree run.

## 7. Not verified here

The success path of every future run step; the census approximates the engine; the weight-file hashes are present-state, not run-time; no reviewer has checked this report.
