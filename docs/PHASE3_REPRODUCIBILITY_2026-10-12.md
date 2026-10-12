# Phase 3 reproducibility work (audit tasks P0-6 and P0-7)

**Date:** 2026-10-12. Scope: figures from committed snapshots and protection against output collisions. No cost
sensitivity, data extension or model training was run.

## 1. Output-collision protection (P0-6)

**The problem.** `tools/exp_signal_vs_portfolio_wedge.py` names its outputs from a short `--tag`
(`wedge_<C>_<tag>.csv`, `monthly_<C>_<tag>.csv`, `decile_weights/<C>/<tag or 'default'>/`). A run that differs from an
earlier one in anything else (an AUM ladder, the weighting scheme, a cost flag) but reuses the tag silently overwrites it,
and tags `""` and `"default"` share one weights directory. This has happened before.

**The fix (minimal).** `src/alphacomb/output_guard.py`: `claim_output(path, params)` stores a SHA-256 fingerprint of the run
parameters in a sidecar (`<file>.run.json`, or `<dir>/.run.json`). Same parameters: a re-run proceeds. Different
parameters, or an existing output with no record: refused with `OutputCollision`. `--overwrite` discards the earlier
output deliberately. The tag is part of the parameters as given, so `""` and `"default"` collide. It changes nothing a
run computes.

**Where it is applied (actual coverage, 12 October update).**

| Guarded (claim before any work, `--overwrite` to discard) | Outputs |
|---|---|
| `tools/exp_signal_vs_portfolio_wedge.py` | `wedge_<C>_<tag>.csv`, `monthly_<C>_<tag>.csv`, `decile_weights/<C>/<tag or default>/` |
| `tools/exp_design_identifiability.py` | per-country files and `design_identifiability_all.csv` |
| `tools/exp_friction_horse_race.py` | `horse_race_decile_panel.csv`, `horse_race_tax_panel.csv` |
| `tools/exp_112a_event_study.py` | `tax_year_panel.csv`, `event_112a.csv` |
| `tools/exp_wedge_test.py` | `wedge_test.csv` |
| `tools/exp_tals_overhang.py` | `exp_tals_overhang.csv`, `exp_tals_overhang_trajectory.csv` |
| `pipelines/07_adaptive_combine.py` | `adaptive_weights.csv`, `summary_adaptive.csv`, `adaptive_report.json`, `adaptive_refit_schedule.csv` |
| `pipelines/06_after_tax_eval.py` | the `--out` summary, or the default `summary_after_tax.csv` |
| `tools/make_figures.py` | the figure directory |

These are the six fixed-path writers named in the finalization audit (section 1.3, item 5), plus the wedge tool, the
stage 06 summary and the figure tool. Nothing any of them computes changed; none was re-run.

**NOT guarded (still exposed to silent overwrites):** `tools/exp_matched_book_accounting.py` (one `matched_book_<aum>.csv`
for all countries), `tools/exp_theme_liquidity_terciles.py`, `tools/exp_capacity_channel_inference.py`,
`tools/exp_after_tax_inference.py`, `tools/gate1_liquidity.py`, `tools/gate2_power.py`,
`tools/exp_book_characteristics.py`, `tools/exp_capacity_dose_response.py`, `tools/exp_factorial_prediction_arm.py`,
`tools/exp_e02_e03_signal_diagnostics.py`, `tools/exp_e29_attribution.py`, `tools/exp_leverage_matched.py`,
`tools/exp_complexity_tax.py`, `tools/dev_backtest.py`, `tools/exhibit_provenance.py`, the `verify_*` and index tools
(`weights_index.py`, `repair_source_index.py`), `pipelines/02_train_models.py` (its source-index writer merges rather than
overwrites, from an earlier fix) and `pipelines/04_construct_portfolios.py`, and the Phase 2 and diagnostic tools that
write deterministic files into `results/` (`exp_capacity_return_difference.py`, `diag_cost_parity.py`,
`diag_dtv_support.py`; their outputs are tracked in git and so are protected by version control instead). Guard coverage is
therefore **partial**: the audit's named list, not every writer in the repository.

**Consequences to know.** Outputs written before the guard have no record, so re-running the same command into an
existing legacy output now needs `--overwrite` or a new tag. The Phase 2 manifest's regeneration commands for the wedge
series therefore need `--overwrite` if the old files are still on disk. Phase 2 and the diagnostic were **not** modified.

**Tests** (`tests/validation/test_output_guard.py`, 8): first claim recorded; identical re-run allowed; same tag with a
different AUM ladder refused and the file untouched; existing output without a record refused; `--overwrite` replaces the
record; `""` versus `"default"` collide on the shared weights directory; distinct tags to distinct paths do not interfere;
the wedge tool exposes `--overwrite`.

## 2. Figures from committed snapshots (P0-7)

`tools/make_figures.py` reads **only tracked files under `results/`** and writes `results/figures/`:

| Figure | Content |
|---|---|
| 1 | B(A) by mandate, per country, Tier B primary and Tier A beside it |
| 2 | uncapped composite compounded terminal wealth by mandate |
| 3 | Shapley attribution of the Tier A / Tier B cost gap to three conventions |
| 4 | share of traded notional beyond 12% and 100% of daily volume, capped versus uncapped |

**Labelling.** B is drawn only at solvent rungs (no cell-month of either book at or below -100%); insolvent rungs are
shaded and labelled "no B computed" and no value is drawn or interpolated there. Solvent rungs whose uncapped composite
ends with less than 0.1 of its starting value are drawn with hollow markers as **near-ruined comparators**. That
threshold is a display flag only: it is not part of the solvency rule and excludes nothing (tested).

**Traceability.** `results/figures/FIGURE_MANIFEST.json` records the SHA-256 of every input file, of the script and of each
figure, library versions, the solvency rule, the display flag, and the git head and dirty state when written. The
figure directory is itself guarded: regenerating from changed inputs or code is refused without `--overwrite`.

**Tests** (`tests/validation/test_make_figures.py`, 5): inputs are tracked `results/` files only; no B at insolvent
rungs (all three countries); insolvent counts equal Phase 2's (3, 4, 0); the near-ruined flag keeps the rung and its B;
a build writes four figures with a complete manifest, a re-run is allowed and a mismatched record is refused.

**Limits.** PNG bytes depend on the matplotlib version (recorded). The figures inherit every limit of their inputs: B is an
accounting difference against an infeasible plan, Tier A / Tier B costs are not fully explained, and the exit policy is
unresolved (`EXIT_POLICY_GATE_2026-10-12.md`).
