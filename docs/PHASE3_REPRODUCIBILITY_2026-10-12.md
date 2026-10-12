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

**Where it is applied.** The wedge tool (all three outputs) and the figure tool. **Not yet applied** to the other
fixed-path writers named in the audit (stage 06 summaries, theme-liquidity, matched-book accounting); those remain as
before and should be wrapped the same way when next touched.

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
