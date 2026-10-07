# Workstream-B receipt, verification and integration — 7 October 2026

**Author:** Harshit (workstream B). **Audience:** Absar (A), Maham (C).

Absar's document 13 declares Workstream A complete and promoted and asks Harshit to run
three validation commands. This records what workstream B actually found, verified and
integrated.

---

## 0. Result

```ini
PROMOTED_BUNDLE_LOCATED    = YES - complete, on Google Drive (not GitHub)
GITHUB_PUSH                = NO  (git fetch: newest remote commit 2026-09-27, all Harshit's)
CODE_DOWNLOADED_AND_HASHED = 14/16 integration files MATCH; 2 are C14 audit files
DOC13_PINNED_DIGESTS       = 5/5 MATCH (including the sole promotion authority)
INTEGRATION_BRANCH         = feat/workstream-a-integration-2026-10-07
TEST_SUITE                 = 290 collected (matches A's count), 289 pass, 1 blocked
OUTSTANDING_BLOCKER        = data/intl_c6/cache/C6_WRDS_DAILY_FX_TO_USD.csv.gz not on Drive
REAL_RESULTS_INSPECTED     = NO
MODELS_RUN_ON_REAL_DATA    = NO (prohibited by doc 13 and frozen decision 6B)
```

## 0.1 Correction — an earlier draft of this document was wrong

An earlier draft stated the Drive `data/` folder was empty and that A's promotion "never
left Absar's machine". **Both were wrong.** The Drive **API** returns an empty result for
every query against this shared tree, and the Drive **web UI search** is equally
unreliable — searching `dated.py` returns only the manifest that *mentions* it, not the
33 KB file sitting in `src/alphacomb/tax/`. Both are search-index lag on a recently
uploaded shared folder.

Those empty responses were mistaken for evidence of absence. The folder had to be walked
directly, directory by directory, before its real contents were visible. **Do not trust
an empty Drive search result for this folder.** Absar's own
`exact_current_authority_manifest_found = False` was recorded against a 2 October
snapshot, before he uploaded.

---

## 1. What was verified

### 1.1 Code — downloaded and hashed

The repository was downloaded from Drive and every manifest-listed integration file
re-hashed against `WORKSTREAM_A_POST_PROMOTION_MANIFEST_2026-10-07.json`:

```
integration files: MATCH=14  DIFFERS=0  MISSING=2 of 16
```

The two "missing" are `data/intl_c14/audit/C14_EVALUATION_SAMPLE_VALIDATION_2026-10-07.json`
and the pre-results amendment, both of which arrived later with the C14 data.
`src/alphacomb/tax/dated.py` (33,994 B) — which doc 13 §6 requires and which had never
existed in our repository — matches exactly.

### 1.2 The five digests pinned in document 13 — all match

| File | Result |
|---|---|
| `FINAL_PRODUCTION_PROMOTION_MANIFEST_2026-10-07.json` (sole authority, `9fe4d029…`) | **MATCH** |
| `WORKSTREAM_A_POST_PROMOTION_VALIDATION_2026-10-07.json` (`37a2b38a…`) | **MATCH** |
| `WORKSTREAM_A_POST_PROMOTION_TESTS_2026-10-07.xml` (`dee50cc7…`) | **MATCH** |
| `data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz` (`bb296e48…`) | **MATCH** |
| `data/intl_c14/production/c14_regime_candidate_source_frozen.csv` (`992a491c…`) | **MATCH** |

`data/intl_c1/production/IND/universe.parquet` was also pulled individually and matches.

### 1.3 `cost_terms.py` — the prohibited behaviour is gone

The open question to Absar is answered by reading his file. `cost_inputs_for` now **fails
closed on all four fields**, not just borrow:

- missing or invalid `spread` / `sigma_d` / `adv_usd` raises `MissingCostInput`; the old
  median imputation survives only behind an explicit
  `allow_synthetic_market_imputation=True` opt-in;
- a missing `borrow_fee` raises unless an explicit `BorrowFeeProxy` is configured — the
  silent `fillna(0.0025)` is gone;
- `borrow_fee` must be finite and non-negative after the policy is applied.

That closes the consumer gate that held C6 at `FAIL_MECHANICAL_PREFLIGHT`.

### 1.4 The duplicate-folder hazard — resolved by Absar mid-session

`data/` briefly held `intl_c6` twice and `intl_c14` three times, and they were **not**
equivalent: only one `intl_c14` had a `production/` subfolder with the correct 11 KB
frozen source. At 19:25 Absar renamed the stale copies to
`_STALE_intl_c6_2026-10-03_DO_NOT_USE` and `_STALE_intl_c14_2026-10-03_DO_NOT_USE_{1,2}`,
leaving exactly one of each. The verified copies in this branch are the current ones.

### 1.5 GitHub is genuinely empty

`git fetch --all` against the configured remote: every branch is authored by Harshit and
the newest remote commit is **2026-09-27**. Drive is the transport Absar used.

---

## 2. What was integrated

Branch `feat/workstream-a-integration-2026-10-07`, built on the 27 September `main`:

- all 16 integration files at their manifest paths;
- both validators plus `promote_workstream_a_from_manifest.py`,
  `final_workstream_a_semantic_preflight.py` and `final_workstream_a_post_promotion_validate.py`;
- `data/intl_c5`, `data/intl_c6`, `data/intl_c14`, `data/workstream_a_closeout`, and
  `data/intl_c1/production/IND/universe.parquet`;
- Absar's handoff documents 06–13, which had not reached us before.

**Numbering collision fixed.** Absar's own documents are 06–13, which clashed with the
06/07/08 this workstream had drafted. Workstream-B's are renumbered **14, 15, 16**.

### Test suite

**290 tests collect — exactly Absar's count — with zero collection errors.** 289 pass.
The single failure is `tests/c14/test_c14_dated_production_integration.py::test_frozen_sample_materializes_complete_engine`,
and it is a missing input, not a defect (see §4).

> A note for whoever runs this next: do **not** invoke pytest with `python -I`. Isolated
> mode drops the working directory from `sys.path`, and `tests/c14/` imports the
> `research` package, so the suite reports two spurious collection errors. Plain
> `python -m pytest` is correct.

---

## 3. New workstream-B work: the country-aware contract resolver

`src/alphacomb/contracts/intl.py`, with 11 tests in
`tests/contracts/test_intl_resolver.py` (all passing).

Doc 13 freezes the handoff at `data/intl_c{1,2,4,5,6,14}/...` and prohibits materialising
`data/real`, but every existing reader — `contracts.paths`, `contracts.io.load_bundle`,
pipelines 02/04/06/07 — resolves a flat `data/<source>/<artefact>.parquet` with no country
dimension. This module is the bridge. It reads the frozen layout **in place** and never
writes a derived bundle.

**Panel mode is left open as configuration, not hard-coded**, because how DEU/IND/JPN
combine is a research decision that was still unsettled:

| Mode | Meaning |
|---|---|
| `separate` | fit, optimise and evaluate each country independently |
| `pooled` | one cross-section per month spanning all three |
| `pooled_fit_separate_construct` *(default)* | one model on the pooled cross-section, then per-country portfolios and per-country tax ledgers |

The default is the third for a reason that is not a preference: **C14 tax year-ends
differ** (DEU and JPN December, India March), so an after-tax ledger spanning the three
has no well-defined tax year. Portfolio construction must be per-country regardless, so
pooling only the model fit is the option that buys training data without pretending the
tax accounting is unified. Whichever mode the team settles on must be recorded in the
pre-registration; changing it is a one-line config change.

Two safeguards worth knowing about:

- **`permno` is only unique within a country here.** Pooling on `(date, permno)` would
  silently merge unrelated securities, so pooled frames carry a `country` column and a
  `gid` composite key, and `assert_permno_disjoint` checks the assumption rather than
  trusting it.
- **`gate_evaluation_frame` enforces the frozen 2009–2019 window** (and the
  2014-01-01..2018-03-31 mechanism subwindow) at the workstream-B input gate, reading the
  bounds from `configs/workstream_a_c14_evaluation_sample_2026-10-07.json` rather than
  hard-coding them. It is an explicit call, not something `load_panel` does implicitly,
  because pre-2009 data remains legitimate for training and feature construction — it
  just may not seed tax lots.

---

## 4. The one outstanding blocker

**`data/intl_c6/cache/C6_WRDS_DAILY_FX_TO_USD.csv.gz` is not on Drive.**

The live `intl_c6` folder contains `audit`, `candidate`, `candidate_working`,
`production` and `reference` — there is **no `cache` directory**. The file is the frozen
point-in-time FX cache, SHA-256 `c59b3be69e32150e51780a259e8e3401a0b7176d0aba66417b97ac03884d47bf`,
listed in the pre-results amendment's integrity block and referenced by
`configs/workstream_a_c14_evaluation_sample_2026-10-07.json`.

It blocks two things, independently confirmed:

1. `validate_c14_evaluation_sample.py` — which otherwise passes the C14 schedule checks
   and the India section 112A checks before failing at `PointInTimeFXStore.from_validated_csv`;
2. the one failing test, which needs the same file.

**Absar: please upload `data/intl_c6/cache/`.** It is the last thing standing between this
branch and a clean 290/290 plus a green C14 validator.

### Also still to transfer

The bulk C1/C2/C4 parquet (~1.04 GB) has not been pulled. Drive's folder-zip downloads
failed repeatedly for anything above ~90 MB, while **single-file downloads worked
reliably** — that is the route to use for the remaining files. Note that the promotion
left C1/C2/C3/C4 unchanged (`VERIFIED_IN_PLACE_NO_COPY_NO_TRANSFORMATION`), and
cross-checking `FINAL_WORKING_MANIFEST` against the promotion manifest shows **14 of 15
artefacts byte-identical** to the promoted versions, so the 2 October upload dates on
those folders are not a staleness problem.

`validate_workstream_a_post_promotion_2026_10_07.py` was not run, because it verifies the
full promotion including the C1/C2/C4 data that is not yet local.

---

## 5. What was deliberately not done

No model was fitted on real data and no result was inspected. Document 13 states the
promotion "deliberately does not authorize ... starting a results run", and frozen
decision 6B requires that `results_must_not_be_inspected_before_scenarios_are_fixed`.
Locking the scenario grid is workstream C's critical path, and it gates everyone.

`configs/base.yaml` was not hand-edited to resolve the stale US splits
(`first_test_year: 1995`, a 2021–2025 lockbox, `borrow_gc_bps_pa: 25.0`): it is a
manifest-pinned file, and Absar's promoted version replaced it wholesale in this branch.
Any remaining splits conflict belongs in the pre-registration.

Nothing was committed to `main` and nothing was pushed.
