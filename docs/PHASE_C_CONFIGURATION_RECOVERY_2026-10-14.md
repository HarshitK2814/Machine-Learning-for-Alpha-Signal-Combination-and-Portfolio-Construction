# Phase C: recovered configuration of the frozen Phase 2 run

**Date:** 2026-10-14. Configuration and provenance fields only. No performance summary, return, price, dividend, cost value or tax outcome was read to produce this document. Internal researcher-led work; no external sign-off.

## 1. What "Phase 2" is

Phase 2 (commit `ac669f2`, 2026-10-10) is the **capacity return-difference accounting** `B(A) = 12 * (mean net return capped - mean net return uncapped)` of `docs/CAPACITY_RETURN_DIFFERENCE_SPEC_2026-10-10.md`, with **Tier B** (the pipeline's own `after_tax_backtest` at zero tax on re-dumped decile weights) as the primary tier. It is **not** the multi-regime after-tax grid of `pipelines/06_after_tax_eval.py`. The first census (`results/phase_c_census_2026-10-14`, commit 076a6e9) used the after-tax `weights_index` sets and is therefore the wrong object. It is superseded by `results/phase_c_census_v2_2026-10-14` (fd4c7b7); the older directory is left in place unchanged.

Consequence for `docs/PHASE_C_REVISED_ANALYSIS_SPEC_2026-10-14.md`: wherever it speaks of regimes, lot methods and "after-tax comparisons", the revised-analysis object is the zero-tax capacity comparison B(A) (tax-exempt regime), so the "tax" input of a month's support mask is trivially supported there unless dividends are missing. No threshold, tier or family is changed by this observation.

## 2. Recovered fields and their sources

| Field | Value | Source |
|---|---|---|
| Entry point | `tools/exp_capacity_return_difference.py --stage pipeline --country C`, then `--stage tables` | script docstring; `stage_pipeline`, `main` |
| Evaluation window | monthly dates 2009-01-31 to 2019-12-31 (132 month-ends); ledger cold-starts 2009-01-01 | `prereg/AMENDMENT_001A_international_scenario_freeze_2026-10-08.md` section 2; date range of the Tier B weight files (date column only) |
| Countries | DEU, IND, JPN | `COUNTRIES` constant |
| Weights (frozen inputs) | `outputs/decile_weights/<C>/tierb/aum_<rung>/{capped,uncapped}_<cell>.parquet`, 8 cells x 2 books per rung, columns `date, permno, w` | `stage_pipeline`; 35 rung directories present (DEU 11, IND 10, JPN 14), matching the "35 valid rungs" of the commit message |
| Strategy cells | 8 per rung, `L-C-P-0`, `L-C-P-U`, `L-S-P-0`, ... (file stems) | weight file names |
| Books | `capped` (decile book with the participation cap) and `uncapped` | spec, `stage_pipeline` |
| AUM rungs | per directory name, e.g. 1e5, 3e5, 1e6, 2e6, 3e6, 4e6, 6e6, 8e6, 1e7, 3e7, 1e8 (DEU); IND to 3e7; JPN additionally 3e8, 1e9, 1e10. Set of "valid" (solvent) rungs is determined from Tier A solvency, an outcome-derived list, and was deliberately not re-derived here | directory listing; `stage_pipeline` |
| Tax regime | `get_regime("tax_exempt")` (zero tax) | `exp_matched_book_accounting.run_one` |
| Lot method / accounting | HIFO / `accrual` | `run_one` |
| Dividend source | `TaxConfig.dividend_yield_annual = 0.02` is passed, but the engine uses C4 `div_next` whenever the targets table carries that column (`dividend_source = targets.div_next`); the 2% flat yield is only the fallback. C4 has `div_next`, so the observed series is the source | `run_one`; `backtest.py` lines 317-320 and 680 |
| Initial NAV | equals the rung AUM | `run_one` |
| Cost multiplier | 1.0 | `after_tax_backtest(..., 1.0)` in `run_one` |
| Costs config | `configs/base.yaml`: commission 1.0 bp, `impact_k` 1.0, `impact_power` 1.5, `aum_usd_2020` overridden per rung, modelled flat borrow proxy 1.00% (MODELLED_FLAT_BORROW_PROXY_V1) | `configs/base.yaml`, `stage_pipeline` |
| Universe cap | `max_names=600` in `load_country_bundle` | `stage_pipeline` |
| Exit policy | `as_run` (the default at that time) | code at ac669f2 |
| Inference | `mean_difference_test`, `n_boot` 4000, block 6, seed 0, Holm within country over valid rungs; solvency pre-test inside `--stage pipeline` used `n_boot=200`, block 6, seed 0 | `write_manifest`, `stage_tables`, `stage_pipeline` |
| Runtime versions | Python 3.12.6, pandas 2.2.3, numpy 2.3.5 | `results/capacity_return_difference/MANIFEST.json` |
| Recorded input hashes | 17 SHA-256 entries (Tier A monthly inputs and Tier B snapshots) | same MANIFEST |

## 3. Gaps (not guessed)

1. **Code state of the original Tier B run.** The MANIFEST records `git_head_when_written = b8e21ba` with `git_dirty_when_written = true`, and states that the monthly files derive from git-ignored data and predictions. The exact tree that produced `tierB_monthly_*.csv.gz` is therefore not reproducible from git alone. The script at `ac669f2` is the best available reference.
2. **Hashes of the frozen decile-weight files.** The weight files are git-ignored and are not in the MANIFEST's hash list. The census manifest records their hashes now (so that future runs can check they are unchanged), but this does not prove they equal the weights used on 2026-10-10.
3. **The valid-rung list** is not recorded as configuration; it is a function of Tier A solvency (an outcome). A run that reuses it must take it from the committed `results/capacity_return_difference/tierA_*.csv` and disclose that choice.
4. **Seeds for the Tier B accounting itself.** The accounting is deterministic given weights; only the bootstrap uses seed 0.
5. **Window boundaries inside the engine.** The window is carried by the weight files' own dates (2009-01-31 to 2019-12-31) rather than by a command-line flag; no `--as-of` applies to the zero-tax regime.

## 4. Items for reviewer decision (specification reconciliation, nothing changed here)

* Specification section 6 prescribes `n_boot = 2000`; the as-run Phase 2 used 4000. Raising or matching is a pre-outcome choice that needs an explicit decision recorded before any run.
* Dividends: Phase 2 took dividends from C4 `div_next` (flat 2% only as an unused fallback). The `dividend_missing` switch therefore applies as specified; the dividend-missing counts are part of the support mask. (An earlier draft of this note said the opposite; it was wrong and is corrected here.)
