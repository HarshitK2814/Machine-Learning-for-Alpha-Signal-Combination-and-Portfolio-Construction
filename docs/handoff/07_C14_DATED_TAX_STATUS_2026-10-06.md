# C14 dated-tax status — 6 October 2026

This handoff records working/audit artifacts only. No C14 production file was
written, Workstream B was not modified, and nothing was committed or pushed.

## Outcome

| Item | Status | Evidence |
|---|---|---|
| Imported Drive C14 package | PASS | 24 regime rows plus source audit and certification restored locally |
| Daily interval coverage | PASS | DEU/IND/JPN, 1990-01-01–2020-12-31, zero gaps/overlaps |
| New primary-source freeze | PASS working | 71 dated facts added to a separate enriched candidate |
| Full field/date inventory | PASS | 306 classified records; blanks remain null |
| Local non-production dated-C12 patch | PASS | all mechanically determined capabilities implemented outside frozen B |
| C14 architecture tests | PASS | 22/22 tests |
| Frozen static-vs-dated C12 gate | BLOCKED | local patch not imported; explicit configurations remain open |
| Workstream-B modification | NOT PERFORMED | genuine legal/design choices remain |
| Existing synthetic-result impact | NO CURRENT IMPACT | current selectable regimes are indefinite and non-ring-fenced |
| C6 borrow integration gate | HARD FAIL AS INTENDED | null borrow fee + implicit 0.0025 consumer fill is rejected |

## C14 artifacts

- Imported candidate: `data/intl_c14/candidate_working/c14_regime_candidate_working.csv`
- Source-frozen working candidate: `data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv`
- Source-freeze ledger: `data/intl_c14/audit/C14_SOURCE_FREEZE_LEDGER.csv`
- Complete field inventory: `data/intl_c14/audit/C14_FIELD_INVENTORY.csv`
- Field inventory summary: `data/intl_c14/audit/C14_FIELD_INVENTORY_SUMMARY.json`
- Working certification: `data/intl_c14/audit/C14_WORKING_CERTIFICATION.json`
- Dated C12 integration design: `data/intl_c14/audit/C14_C12_DATED_INTEGRATION_DESIGN_2026-10-06.md`
- Static compatibility gate: `data/intl_c14/audit/C14_STATIC_DATED_COMPATIBILITY_GATE.json`
- Executable reference semantics: `research/c14_dated_engine_reference.py`
- Local dated-C12 patch: `research/c14_dated_c12_patch.py`
- Local patch gate: `data/intl_c14/audit/C14_LOCAL_DATED_C12_PATCH_GATE.json`
- Local patch implementation note: `data/intl_c14/audit/C14_DATED_C12_LOCAL_PATCH_IMPLEMENTATION_2026-10-06.md`
- Loss-ledger result-impact audit: `data/intl_c14/audit/C14_LOSS_LEDGER_RESULT_IMPACT.json`
- Test status: `data/intl_c14/audit/C14_LOCAL_PATCH_TEST_STATUS.json`
- Architecture freeze: `data/intl_c14/audit/C14_DATED_C12_ARCHITECTURE_FREEZE_2026-10-06.json`
- Human decision sheet: `data/intl_c14/audit/C14_C6_HUMAN_DECISION_SHEET_2026-10-06.md`
- Tests: `tests/c14/test_c14_dated_engine_design.py` and `tests/c14/test_c14_dated_c12_patch.py`

## Source-freeze result

The pass mechanically froze the following without inventing a scalar rate:

- Germany: six-/twelve-month history, old private-sale thresholds and same-year
  loss rule, 2002 half-inclusion metadata, 2009 acquisition cutoff, EUR 801
  capital-income allowance, share-loss bucket, and post-2009 loss restrictions.
- India: eight-year capital-loss horizon from the April-2003 working interval,
  capital-gain ring fencing with ST/LT sub-buckets, and exact §55(2)(ac)
  grandfathered-basis metadata for §112A.
- Japan: exact 1999 transaction-tax abolition boundary and explicit `NONE`
  holding-wedge semantics for the sourced post-2002 listed-share regimes.

The working certification remains `production_ready = false`, correctly.

## Local architecture result and frozen-engine blocker

The opt-in local patch passes `PASS_LOCAL_NONPRODUCTION_ARCHITECTURE`. It implements
event/acquisition/applied rule IDs, grandfathered lots, per-side statutory taxes,
security-specific reference values, asymmetric loss buckets, inclusive expiry,
immutable loss vintages, and local-currency statutory amounts with injected dated FX.
Unresolved rates, allowance allocations, brokerage, and FX never receive defaults.

The actual gate output is `BLOCKED_STATIC_REGIME_ENGINE` because C12 lacks:

1. event-date rule resolution;
2. acquisition-date transition rules;
3. side-specific statutory transaction taxes;
4. runtime loss ring-fencing;
5. the correct inclusive final carryforward year; and
6. preservation of original loss-vintage years.

The existing `_YearBook` both ignores `losses_ring_fenced` and can refresh the
age of an old loss balance when a new loss occurs. These are correctness issues,
not merely missing international features.

The frozen gate remains blocked by design: `src/alphacomb` does not import the
local patch, and production configuration is incomplete.

The local architecture is now checksum-frozen. Do not extend it unless a
failing dated-C12 integration test demonstrates that the smallest corrective
change is required. Verify the freeze with `python audit_c14_dated_patch_freeze.py`.

## Existing synthetic-result impact

No current default synthetic result is affected by the two loss-ledger defects.
All four regimes selectable through `get_regime` have indefinite carryforward and
`losses_ring_fenced = False`; the India/Germany/Japan `Jurisdiction` objects are
not passed to `after_tax_backtest` by any repository pipeline.

Nothing was rerun. After dated integration, affected stage-06 C12 returns and
`summary_after_tax.csv` must be regenerated. If stage 07 uses those after-tax
rewards, its summary, causal adaptive weights, report, refit schedule, and
adaptive portfolio weights must also be rebuilt, followed by dependent figures.
Stage-04 weights do not need rerunning for the loss-vintage repair alone, although
they will need rebuilding if dated lot rates enter the tax-aware optimiser.

## Blocker ledger

| Blocker | Class | Scope/date | Needed resolution |
|---|---|---|---|
| Representative marginal-rate path | Team research choice | DEU pre-2009; IND pre-2004 | Approve investor income/rate calibration |
| Pre-2003 Japanese CGT route/special rules | Statutory fact | JPN 1990–2002 | Finish primary-source reconstruction |
| 1990 German Börsenumsatzsteuer rate/incidence | Statutory fact | DEU 1990 | Recover primary statute/rate table |
| Old German §10d horizon/carryback details | Statutory fact | DEU 1999–2008 | Date exact rules and cash/refund mechanics |
| Historical dividend schedules | Mixed fact/calibration | JPN all years; DEU pre-2009; selected IND periods | Source law, then approve representative investor rate where required |
| Exchange/regulator/indirect-tax charges | Historical market facts | all countries/dates with blanks | Source venue-specific schedules or remove from C14 scope |
| Brokerage/platform charges | Team research choice | all countries | Approve dated execution-cost calibration or keep outside C14 |
| Threshold currency conversion | Team research choice | DEM/EUR/INR thresholds vs USD NAV | Approve event/payment-date point-in-time FX convention |
| General allowance allocation | Team research choice | especially DEU EUR 801 | Decide full, partial, or zero allocation to the strategy |
| Frozen C12 integration | Mechanical after choices above | all dated regimes | transplant the passing local objects into the existing engine and rerun C12 tests |
| Existing optimiser regression | Pre-existing numerical issue | `test_optimiser_with_tax_awareness_holds_embedded_gains` | tax-aware sales exceed blind sales by 1.32e-6 in the current solver result; not caused by or changed for this patch |
| Actual Abdi–Ranaldo extraction | External access | C6 | Reactivate WRDS Duo, then run the resume command |
| Genuine borrow fee | External data/design | C6 | Obtain lending-fee data or preregister an explicit fallback |

## C6 guardrail added during this pass

`preflight_c5_c6_daily_candidates.py` now treats the combination of certified
missing borrow fees and Workstream B's `fillna(0.0025)` as a hard integration
failure. `audit_c6_consumer_compatibility.py` now reports
`FAIL_HARD_BORROW_FEE_INTEGRATION`. The consumer default itself was not changed.

## Next authorized actions

1. Complete remaining primary-source reconstruction that does not require a
   team choice, especially pre-2003 Japan and Germany 1990/old §10d.
2. Obtain team decisions for the representative-rate, local-currency threshold,
   allowance-allocation, and non-statutory fee questions.
3. Only then transplant the passing local dated objects into the existing
   Workstream-B engine and move the transition tests onto that integrated path.
4. When WRDS Duo is restored, run:

   `.\.venv_wrds\Scripts\python.exe resume_c5_c6_after_wrds.py`

5. Do not promote C6 until the hard borrow-fee integration failure is resolved.
