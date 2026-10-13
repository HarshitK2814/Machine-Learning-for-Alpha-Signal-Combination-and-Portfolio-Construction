# Output-collision audit (overnight sprint, 2026-10-14)

Scope: every remaining unguarded writer named in `docs/PHASE3_REPRODUCIBILITY_2026-10-12.md` section 1 and `docs/BLOCKER_LEDGER_2026-10-12.md` (W5). **No experiment was run.** Evidence is the source of each writer (default output paths, write mode, argument handling) and infrastructure tests on synthetic fixtures.

## 1. Guard design (unchanged semantics, one additive helper)

`alphacomb.output_guard.claim_output` records a SHA-256 fingerprint of the run parameters in a sidecar. Same fingerprint: rerun proceeds. Different fingerprint, or an existing output with no record: `OutputCollision`. `--overwrite` replaces the record. The tag is part of the parameters as given, so `""` and `"default"` differ. A claim is made **after argument parsing and before any data load or computation**.

New this sprint: `claim_run_items(items, args)`, for writers that emit one file per country (or similar). Each file gets its own fingerprint (the arguments minus the per-item key, plus that key), so a later run over a different country list does not collide on files whose settings are identical, but the same file under different settings does. All claims are validated before any record is written, so a refusal part-way leaves no stray records. A legacy output is never given fabricated metadata: it is refused unless `--overwrite` is passed.

Known limits shared by every guard: the fingerprint covers command-line arguments, not input data content (a rerun with the same arguments but different upstream data is treated as the same job); a run that fails after claiming leaves a record, so a later differently-parameterised run needs `--overwrite` even though no output exists.

## 2. Coverage matrix

| Writer | Default / fixed outputs | Write mode | Concurrent differently-tagged runs | Missing manifest | Status |
|---|---|---|---|---|---|
| `tools/exp_matched_book_accounting.py` | `outputs/matched_book/matched_book_<aum>.csv` (all countries in one file) | truncate | collide: `--tag` and `--country` do not enter the name | detected (refused) | **guarded 2026-10-14**, whole-argument fingerprint |
| `tools/exp_theme_liquidity_terciles.py` | `outputs/theme_liquidity/theme_liquidity_<C><sfx>.csv` | truncate | weighting/liquidity variants have suffixes; same variant collides | detected | **guarded**, per-country fingerprints |
| `tools/exp_capacity_channel_inference.py` | `capacity_channel_inference_<C><sfx>.csv`, `crossover_intervals<sfx>.csv` | truncate | suffix carries the tag | detected | **guarded**, per-country + shared summary |
| `tools/exp_after_tax_inference.py` | `after_tax_inference_<aum>.csv` | truncate | one file per AUM; countries share it | detected | **guarded** |
| `tools/gate2_power.py` | `outputs/gate2/gate2_power_<aum>.csv` | truncate | same as above | detected | **guarded** |
| `tools/exp_book_characteristics.py` | `capacity_<C>.csv`, `realised_books_<C>.csv` | truncate | AUM list and dates not in name | detected | **guarded** |
| `tools/exp_capacity_dose_response.py` | `dose_panel_<C>.csv`, `dose_summary_<C>.csv` | truncate | AUM list not in name | detected | **guarded** |
| `tools/exp_factorial_prediction_arm.py` | `factorial_P_<C><suffix>.csv` | truncate | `--column` not in name | detected | **guarded** |
| `tools/exp_e02_e03_signal_diagnostics.py` | `e02_e03_summary.csv`, `provenance.json`, three files per country | truncate | `--max-signals` not in name | detected | **guarded**, per-country + summary |
| `tools/exp_e29_attribution.py` | `outputs/e29/e29_*.csv` (file set depends on the data), `e29_inference.csv`, `e29_provenance.json` | truncate | `--column`, `--source` not in names | detected | **guarded as a directory** (`outputs/e29/.run.json`) |
| `tools/exhibit_provenance.py` | `outputs/e29/e29_artefact_chain.csv` | truncate | n/a | detected | **guarded** (file) |
| `tools/exp_complexity_tax.py` | `outputs/exp_complexity_tax.csv` | truncate | all arguments absent from name | detected | **guarded** |
| `tools/dev_backtest.py` | `outputs/summary_dev_backtest.csv` (plus unique-run-id returns files) | truncate | `--country`, `--strategies` absent from name | detected | **guarded** (summary; run-id files cannot collide) |
| `tools/verify_arm_information.py` | `outputs/arm_information/arm_information_<C>.csv` | truncate | n/a | detected | **guarded** |
| `tools/verify_projection_fidelity.py` | `--out` file when given | truncate | n/a | detected | **guarded** when `--out` is set |
| `tools/verify_workstream_a_receipt.py` | `--json` report when given | truncate | n/a | detected | **guarded** when `--json` is set |
| `tools/gate1_liquidity.py` | none (reads and prints only) | no writes | n/a | n/a | no guard needed (verified by grep: no write call) |
| `tools/exp_leverage_matched.py` | `outputs/weights_index/<C>_<tag><suffix>.csv`; weights get new run ids | truncate (index), unique (weights) | index file collides if tag and suffix repeat | not detected | **NOT guarded: proposal below** |
| `tools/weights_index.py` | `outputs/weights_index/<C>_<aum>.csv` or `--out` | truncate | collides with stage-04 index of the same name | not detected | **NOT guarded: proposal below** |
| `tools/repair_source_index.py` | `outputs/source_index/<C>.csv` | rebuilt from manifests, truncate | single file per country | not detected | **NOT guarded: proposal below** |
| `pipelines/02_train_models.py` | `outputs/source_index/<C>.csv` (merge), `seed_stability_<code>.csv`, `manifest_models.csv` or `--manifest` | merge / truncate / rewritten | merges by design | not detected | **NOT guarded: proposal below** |
| `pipelines/04_construct_portfolios.py` | `manifest_portfolios.csv` (append), `weights_index/<C>_<tag><suffix>.csv` (truncate) | append / truncate | append interleaves; index collides | not detected | **NOT guarded: proposal below** |
| `tools/exp_capacity_return_difference.py`, `diag_cost_parity.py`, `diag_dtv_support.py`, `make_figures.py` | files under `results/` | deterministic, tracked in git | n/a | tracked: git reveals changes; figures already guarded | protected by version control, unchanged |
| `tools/phase_c_input_census.py` (new) | `--out` directory | refuses existing path | distinct dirs | n/a | refuses by construction |

Already guarded before this sprint (not re-audited): wedge tool, `exp_design_identifiability`, `exp_friction_horse_race`, `exp_112a_event_study`, `exp_wedge_test`, `exp_tals_overhang`, `pipelines/06`, `pipelines/07`, `make_figures`.

## 3. Writers left unprotected, and why

These write **indexes or manifests whose merge or append semantics other tools depend on**. A guard that refused on a differing fingerprint would change behaviour that is deliberate (the stage-02 source index is merged precisely so that split invocations accumulate). No protection scheme was improvised.

### 3.1 Proposal for index and manifest writers

1. **Do not fingerprint merge targets.** For `source_index/<C>.csv`, `manifest_models*.csv` and `manifest_portfolios.csv` the contract is "append or merge by key". Replace the unguarded read-modify-write with an atomic one: write to a temporary file in the same directory, `os.replace`, under an exclusive lock file (`<name>.lock`, created with `O_EXCL`). Concurrent writers then serialise instead of interleaving. Merge semantics stay as they are.
2. **Row-level provenance, not file-level refusal.** Add `written_by` (script, git head, argument fingerprint, UTC time) columns to appended manifest rows. Existing consumers select named columns, and a header-drift check already exists (`manifest_portfolios.csv` parser warning), so the added columns must be added **at the end** and the drift check extended in the same change.
3. **Truncating index writers** (`weights_index.py`, `exp_leverage_matched.py`, the stage-04 `weights_index` write): use `claim_output` on the index file with the parameters (country, AUM tag, suffix, source manifest hash). Refuse a conflicting rewrite; allow an identical one. `weights_index.py` should refuse to write over an index whose record names a different source manifest.
4. **`repair_source_index.py`**: it is a rebuild from manifests and has `--dry-run`. Guard with `claim_output` keyed on the manifest set hash, so a repair from a different manifest set is explicit.

### 3.2 Regression plan for that change (not implemented)

* Characterisation tests first: the current merge result for a fixed pair of synthetic invocations (keep='last' on `country, strategy, kind`) must be reproduced byte for byte after the change.
* Two concurrent appenders on a synthetic manifest produce a complete file with all rows once (spawned subprocesses, tmp directory).
* A killed writer leaves either the old file or the new file, never a partial one.
* Header-drift: a manifest with the extra trailing columns is still read by `provenance.py`, `06_after_tax_eval.construction_quality` and `weights_index` consumers.
* Legacy file without a record is accepted for merge targets (record created on first merge) and refused for truncating index writers unless `--overwrite`.

## 4. Tests

`tests/validation/test_output_guard_extended.py` (37 tests): `--overwrite` exposed for each newly guarded writer; for each, a pre-existing output of unknown origin raises `OutputCollision` before any work, the file is unchanged, and no sidecar or other file is created; `claim_run_items`: same-configuration rerun allowed, a different country list does not collide on shared files while different settings on the same file do, legacy outputs refused and not modified, refusal leaves no record for earlier items, `--overwrite` replaces the record and the new configuration then reruns freely, empty and `default` tags are distinct. The existing 8 + 15 guard tests still pass (55 total in the guard group at the time of writing the first tranche).

## 5. Not verified

Whether the full repository suite still passes after these changes is reported in the work log (final-tree run). The guards were exercised only up to the point of refusal; the success path of each tool (claim recorded, run proceeds, outputs written) was not executed because that would run an experiment.
