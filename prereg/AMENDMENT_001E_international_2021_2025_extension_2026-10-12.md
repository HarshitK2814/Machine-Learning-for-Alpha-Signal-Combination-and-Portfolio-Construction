# Pre-registration amendment 001E: the 2021-2025 international extension

**Amendment date:** 12 October 2026
**Amends:** `PLAN_001_after_tax_attribution.json` (21 September 2026), as amended by 001A-001D
**Parent fingerprint:** `cae8140b7e2b7ee4`, **unchanged**
**Confirmatory trial count:** **N = 64**, **unchanged**
**Status:** `DRAFT_PRE_RESULTS`: **not binding until countersigned** by Maham (protocol owner) and Absar (data and C5 owner)
**Drafted by:** Workstream B

```ini
A2_RETURN_PANELS_INTEGRATED             = NO
A2_OUTCOME_VALUES_INSPECTED_BY_B        = NO     # metadata and non-outcome quality fields only
LOCKBOX_OPENED                          = NO
PARENT_PLAN_OVERWRITTEN                 = NO
TRIAL_COUNT_CHANGED                     = NO
MODELS_TRAINED_OR_BACKTESTED_ON_A2      = NO
```

The lockbox stays sealed until this amendment is **committed and countersigned**, section 2's exposure audit is accepted,
and the two source decisions in section 4 are signed off.

---

## 0. Purpose

The 2009-2019 results were produced under a frozen contract and have been corrected repeatedly since. A forward test on
2021-2025 data is only worth having if its procedure is fixed before any outcome is opened. This amendment fixes it.
It changes **no** part of the search (grid, N) and **no** part of the 2009-2019 results.

## 1. The extension

* **Candidate data:** Workstream A2 Phase-2 isolated candidate (`INTL_OOS_PHASE2_CANDIDATE_BUILD_2026-10`),
  hash-validated by Workstream B on 11 October 2026 (17 of 17 manifest entries; row counts and null fields as reported).
* **Formation months:** 2021-01-31 to 2025-12-31 (60 months) for Germany, India and Japan. The December 2020 formation
  (January 2021 return) lies in neither panel and is not evaluated.
* **Outcomes:** `ret_next` for each formation month. 3-, 6- and 12-month horizons are secondary; late-2025 12-month labels
  are right-censored null and stay null.
* **Pre-tax only.** C14 is not certified for 2021-2025; after-tax evaluation on the extension is **prohibited**.
* **Statistical power:** 60 months against 132 raises the minimum detectable effect by a factor of 1.354 at equal
  standard error. A null on the extension will be reported as low-powered, not as confirmation of a null.

## 2. Exposure audit: what has already touched 2020 and 2021-2025

Audit date 12 October 2026. Method: schema and date-range metadata of every artefact, plus the run manifests; no return
values of the A2 panel were read.

| Question | Finding | Evidence |
|---|---|---|
| Do real-data (DEU, IND, JPN) predictions reach 2020? | **No.** All 39 real prediction artefacts (13 per country) end 2019-12-31. | date range of each artefact, joined to `manifest_models.csv` |
| Do real-data weights reach 2020? | **No.** 201 manifested real weight files (117 DEU, 21 IND, 63 JPN) end before 2020. | same, via `manifest_portfolios.csv` |
| What does reach 2020? | 19 synthetic prediction artefacts, 72 synthetic weight files, 18 backtest-return files from one dev batch (8 Oct; their panel is not confirmed from the manifests), and **three artefacts not in any manifest** (one prediction dated 9 Oct spanning 1996-2020; two `adaptive_hedge` weight files dated 20 Sept). | same |
| Production panels | The promoted panels run **1990-2020** and are loaded in full by every run, including 2020 targets and cost inputs. | bundle date ranges |
| Was 2020 used to fit or evaluate on real data? | The only 2020 outcome inside any real evaluation is **January 2020**, the `ret_next` of the December 2019 formation (evaluation window 2009-01 to 2019-12). Annual refits use data up to the formation date less the embargo, so no real-data fit used 2020 outcomes. | config `splits`, `embargo_months`, window of results documents |
| Was real 2020 or later performance computed or discussed? | No result document reports a real-data statistic for 2020 or later. | text search of `docs/` (limited: absence of mentions is not proof) |
| 2021-2025 exposure | The extension's outcome values have not been read by Workstream B. Count-level QA (non-missing counts per year, row counts) and macro-rate diagnostics have been read. The A2 builder reports results not inspected; that is **self-reported and not independently verified**. | A2 status verdict; this audit |
| Channels not measurable by an audit | Researcher knowledge of 2020-2025 market history; vintage revisions of the risk-free and Compustat return indexes (A2 notes both "may revise"). | n/a |

**Unclassified artefacts (three).** Their panel and date range cannot be established from the manifests. They are listed
here and are **not** relied on; they are to be classified or removed from `outputs/` before the lockbox opens.

**Classification adopted.**
* **2020 calendar year: development-period, not confirmatory.** The repository config names 2020 the last development
  test year (`last_dev_test_year: 2020`) and January 2020 has been inside an evaluation window. No 2020 formation month is
  evaluated in the extension.
* **2021-2025 formation months: unexposed at the outcome level**, subject to the two unmeasurable channels above.
* **Design exposure:** the contract, universe rules, 600-name breadth cap, cost model and the withdrawals documented in
  `PAPER` section 8 were set or corrected after seeing 2009-2019 results. The extension tests that frozen design out of
  time; it does not make the design choices blind.

## 3. Frozen evaluation procedure

* **Design and models:** the 16-cell grid, unchanged. No hyperparameter, architecture, feature, theme or signal-set
  change. All 153 signals are retained.
* **Training:** the existing annual expanding-window refit with the model's embargo, using real data to the refit date.
  No re-tuning on any 2021-2025 outcome.
* **Cost contract:** the frozen contract is the **primary** specification: impact `k = 1.0`, exponent 1.5, certified C6
  spreads, 1 bp commission, the 1% modelled borrow proxy (`MODELLED_FLAT_BORROW_PROXY_V1`, **kept out of C6**),
  the 600-name breadth cap and the ADV participation cap. **`--require-cost-inputs` is mandatory** for every capacity or
  decile exhibit. Shortability is `UNKNOWN_FAIL_CLOSED`; no short-side eligibility is inferred.
* **Cost sensitivities** (calibration proposal) are secondary, labelled, and run only after the exit-policy gate is
  resolved and they are separately approved.
* **Exit and uncertified-position policy:** whatever the exit-policy ruling (`EXIT_POLICY_GATE_2026-10-12.md`) decides is
  applied identically to the extension; until it is ruled on, the extension reports both the as-run Tier B convention and
  the Tier A convention and labels the gap, and no extension result is described as final.
* **Primary statistics:** optimised-book net Sharpe at the $1bn mandate with Newey-West t, per country; gross decile
  Sharpe and t; the capped decile book; the capacity return difference B(A) on solvent rungs (cell-level solvency rule,
  no wealth threshold). Reported per country with the Phase 2 tables beside them.
* **Missing data:** the frozen missing-signal treatment is unchanged and **no signal or theme is dropped after seeing
  outcomes**. Known data conditions are declared now (section 5).
* **Decision rule:** all pre-specified tables are reported whether or not they support the earlier conclusions. A
  conclusion that changes is reported as changed. Nothing is re-specified after the lockbox opens.

## 4. Source decisions (explicit; binding on countersignature)

These are drafted so that a decision exists before the lockbox opens. **If a countersignature is not obtained, the stated
default applies and no splice is made.**

**Fail-closed semantics, stated precisely.** The existing pipeline fills a missing state variable with 0.0 (the
standardised mean) in conditional cells (`models/base.py`, `df[state_cols].fillna(0.0)`). "Fail-closed" for TERM or CREDIT
therefore means the state is neutral (0), which removes that state's interaction effect rather than signalling an error.
It affects only conditional (C = +) cells.

**D1. Japan TERM.**
* *Evidence (non-outcome, macro rate series):* the frozen OECD 3-month CD series ends 2022-03. Candidate A, BOJ
  `FM02 STRAK_STRACDN2DB04` (new-issue CDs, 90-179 days): 315 months of overlap with the frozen series (1996-01 to
  2022-03), correlation 0.9978, mean difference -0.026 pp, standard deviation 0.018 pp, maximum absolute difference 0.079 pp.
  Candidate B, JBA JPY TIBOR 3M: 15 overlap months, correlation 0.44, a different defined object. The audit itself states
  a level and correlation match cannot establish semantic equivalence.
* *Decision:* **candidate B is rejected.** Candidate A is **adopted as the primary Japan TERM successor from 2022-04,
  with its definitional difference (maturity bucket, level gap) disclosed**, subject to Absar's sign-off that the series is
  an acceptable continuation. A **pre-specified robustness run** reports Japan's conditional cells with TERM held at 0
  from 2022-04.
* *Default if unsigned:* TERM = 0 for Japan from 2022-04 (no splice).

**D2. India CREDIT.**
* *Evidence:* the frozen proxy crosses BPLR, Base Rate, MCLR and EBLR regimes and is not a stable statutory series; scalar
  substitution is prohibited by the source audit.
* *Decision:* **no extension and no bridging.** India's CREDIT state is held at 0 for months after the last frozen
  observation. India's conditional-cell results on the extension are therefore reported with this limitation stated and
  are not pooled with Germany and Japan for any conclusion about state dependence.
* *Default:* the same.

**D3. Other C5 states.** Germany CREDIT (definition break, denominator refresh), the OECD inflation dataflow migration and
the India DRATE / India TERM / Japan CREDIT vintage rechecks are listed by the data owner as "recheck required". They are
**conditions to lockbox opening**: Absar confirms in writing that each series is refreshed on the frozen normalisation
(expanding z, ddof 1, 24 minimum observations, no 2021 restart).

## 5. Data conditions declared before outcomes

* **Germany:** certified-complete C6 market inputs cover about 69-71% of investible rows each year against 99.7-100% in
  India and Japan, so the cost-input coverage asymmetry of 2009-2019 persists. `--require-cost-inputs` is therefore
  decisive for Germany.
* **India:** investible rows are about 12% of all rows (39,341 of 316,285); the 600-name breadth cap is unchanged (it binds from 2023: about 620-820 investible names a month).
* **Japan signals:** in the investible universe, 9 quarterly-earnings-based signals are 98-99% missing and 2 signals
  (`ivol_hxz4_21d`, `iskew_hxz4_21d`) are 100% missing; 11 of 153 signals exceed 50% missing. Whole-theme completeness in
  Japan is near zero for several themes (e.g. investment, profitability, quality about 1%). Whether this also held in
  2009-2019 has not been compared and is a pre-declared limitation. No signal is dropped.
* **C2 point-in-time lineage:** conditional (`PASS_CANDIDATE_CONDITIONAL_PROVIDER_PIT_LINEAGE`); the provider's
  accounting-vintage construction cannot be independently reconstructed.
* **C6 borrow fee:** null in every row by certification; shortability `UNKNOWN_FAIL_CLOSED`.

## 6. Conditions for opening the lockbox

All of: (1) this amendment committed and countersigned (Maham, Absar); (2) the exposure audit accepted and the three
unclassified artefacts classified or removed; (3) D1-D3 signed off or their defaults accepted in writing; (4) the
exit-policy ruling recorded, or an explicit decision to proceed with it unresolved and labelled; (5) the A2 candidate data
integrated by a separate, reviewed step after (1)-(4). Until then no model is trained, no backtest is run and no outcome
column of the extension is read by anyone on this workstream.

## 7. What this amendment does not do

It does not integrate any A2 data, change any 2009-2019 result, alter the cost contract, certify C14 for 2021-2025,
authorise after-tax evaluation, or establish that the extension is out-of-sample evidence. That status follows only from
the conditions in section 6 being met.
