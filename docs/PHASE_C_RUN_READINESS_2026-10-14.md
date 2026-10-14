# Phase C run-readiness report (2026-10-14)

**Verdict: NOT READY. Do not run the revised historical panel yet.** If it were run exactly as the committed specification prescribes, the census says every rung x book x cell would be **not estimable** (more than 25% of months unresolved), so the run would produce a data-adequacy statement and no performance result. The prerequisites that decide what the run should be are listed in section 7. Nothing here relaxes a threshold or changes a rule.

> **Status note, 2026-10-14 (later):** section 2's explanation (C6 lapses as exits) is corrected by census v3; the verdict is unchanged but its cause is not. See `docs/PHASE_C_RUN_READINESS_V2_2026-10-14.md`. This version is kept as the record.

Internal researcher-led preparation; not external statistical sign-off; no approval by Maham or Absar beyond their documented responses is claimed. No historical performance panel, cost sensitivity, re-optimisation, training or A2 evaluation was run; no return, price, dividend, cost, tax or NAV value was read.

Inputs: specification `0a320cb` + addendum 1 `d0c1768`; configuration recovery (`docs/PHASE_C_CONFIGURATION_RECOVERY_2026-10-14.md`); census v2 (`results/phase_c_census_v2_2026-10-14`, commit `fd4c7b7`; code and 7 whitelist tests in the same commit). Census v1 (`076a6e9`) used the wrong weight set and is superseded.

## 1. Exact configuration to be reused

The frozen Phase 2 object is the capacity return-difference accounting B(A) (commit `ac669f2`): per country, per AUM rung, 8 prediction cells x {capped, uncapped} decile books, `after_tax_backtest` with the `tax_exempt` regime, HIFO, accrual, `initial_nav` = rung AUM, cost multiplier 1.0, `max_names=600`, base config costs with modelled 1.00% borrow, dividends from C4 `div_next`, window 2009-01-31 to 2019-12-31 (132 months; India 131). Weights: `outputs/decile_weights/<C>/tierb/aum_<rung>/{capped,uncapped}_<cell>.parquet` (35 rung directories: DEU 11, IND 10, JPN 14 = 560 country x rung x book x cell series). Inference as run: `mean_difference_test`, 4,000 replications, block 6, seed 0, Holm within country over valid rungs.

Known gaps (not guessed): the exact code tree of the original Tier B run (`git_dirty_when_written = true` at `b8e21ba`), the hashes of the git-ignored weight files at run time (the census manifest records their current hashes), and the valid-rung list (an outcome-derived set; it would have to be taken from the committed `tierA_*.csv`).

## 2. What the census implies for the reporting tiers (identifiers and membership only)

Columns read: C1 `date, permno, in_universe`; C4 `date, permno` (row presence only); C6 `country, date, permno` (row presence only); weights `date, permno, w` (as the test `w != 0`). Not read: any return, price, dividend, cost value, tax result, NAV or performance value. No delisting is inferred from a missing row. Fields scanned in C1, C4 and C6 contain **no terminal-event field**, so exit evidence is unavailable for every exit.

| Quantity (2009-01 to 2019-12) | DEU | IND | JPN |
|---|---|---|---|
| Rung directories | 11 | 10 | 14 |
| Series (rung x 2 books x 8 cells) | 176 | 160 | 224 |
| C4 panel exits of **held** names (present at t, absent at t+1) | 0 | 0 | 0 |
| C6 lapses of held names (no C6 row at t+1), summed over series-months | 26,620 (2.4% of held name-months) | 73,600 (5.3%) | 41,524 (1.2%) |
| Held names with terminal-event evidence | 0 | 0 | 0 |
| First unresolved month if every such lapse is unresolved | 2009-02 (154 series), 2009-03 (22) | 2009-02 (160) | 2009-02 (224) |
| Projected unresolved share of months | 98.5-99.2% | 99.2% | 99.2% |
| Projected tier (by the committed thresholds) | **>25%: not estimable**, all 176 | **>25%**, all 160 | **>25%**, all 224 |

Panel-level flows (entries and exits by month) and coverage counts are in `panel_flows_by_country_month.csv` and `panel_coverage_by_country_month.csv`.

**Why the projection is this extreme.** The engine's rule (`src/alphacomb/portfolio/cost_terms.py::priced_at`, used by `carry_v1` in `src/alphacomb/tax/backtest.py`) treats a held name with no C6 row at a date as having left the panel. C6 membership coincides with the in-universe flag, so these lapses are mostly names leaving the investable universe while remaining in the C4 targets table (zero held C4 exits). Under `carry_v1` with no exit evidence each such name is **unresolved**, and NAV is NaN from the first unresolved month. A typical month has 1-5% of held names lapsing, so the first lapse arrives in the second month and the rest of the path is unresolved. The projection counts only names with a non-zero weight in a scored month, so it is an approximation; it cannot be lower than the real first-lapse month by more than the omission of carried-but-no-longer-targeted positions.

**Consequences, stated plainly.** (i) Under the frozen rule the primary revised statistics are not estimable for any of the 560 series, the Holm family (tier-1 rows only) is empty, and the only reportable content is the unresolved-month counts and the resolved-only diagnostic (the first month). (ii) This is a finding about data adequacy of the exit metadata, not about the strategies. (iii) It will not be tuned away: no threshold, rule or window is changed here.

## 3. Specification versus implementation

| Item | Specification | Implementation (`f201f9c`) | Agree? |
|---|---|---|---|
| Unresolved NAV | NaN from first unresolved month; resolved-only diagnostics labelled | `nav` NaN from first unresolved/unsupported month; `nav_diag`/`*_diag`; `summarise_after_tax` stamps the basis label | Yes |
| Exit evidence | empty table; no inference from missing C6 row | `exit_evidence` optional table validated; none supplied -> unresolved | Yes |
| Missing dividends | `unsupported` primary, `flag_only` exploratory | `dividend_missing` default `unsupported`; C4 defines `div_next` for every row, so missing counts arise only for names with no C4 row | Yes |
| Unsupported costs | NaN, never zero | `cost_status`; costs NaN where a trade cannot be priced | Yes |
| Tax status | per-month status | `tax_status` supported / incomplete_flagged / unsupported; zero-tax regime so only dividends can make it unsupported | Yes |
| Support mask per metric (addendum 1) | union of affected months, counted once | statuses are per month; the union per metric must be computed by the analysis script, which does not exist yet | **Not yet implemented** |
| Regimes and lot methods (spec section 1) | written as if multi-regime after-tax grid | Phase 2 is zero-tax HIFO | **Spec wording to be corrected by addendum** (L8) |
| `n_boot` | 2000 | as-run 4000 | **Decision needed** |
| Bootstrap p-value | add-one form for decisions | library returns the raw proportion; add-one must be computed by the analysis script | **Not yet implemented** |

## 4. Future run: structure (commands are templates; flags marked * do not exist yet)

The Phase 2 runner `tools/exp_capacity_return_difference.py` has no exit-policy option and writes into the tracked `results/capacity_return_difference/`. It must not be used for the revised analysis. A new runner is required and needs its own synthetic-fixture tests before any real use:

```
# P-1 (to be written, tested on synthetic panels only): tools/phase_c_capacity_revised.py
python tools/phase_c_capacity_revised.py --stage pipeline --country DEU IND JPN \
    --exit-policy carry_v1 --dividend-missing unsupported \
    --out results/revised_2009_2019_carry_v1_<YYYYMMDD>_run1          # *--out, *--stage names are proposals
python tools/phase_c_capacity_revised.py --stage pipeline ... --out results/revised_2009_2019_carry_v1_<YYYYMMDD>_run2
python tools/phase_c_capacity_revised.py --stage support-masks --run results/..._run1      # tiers before any performance column
python tools/phase_c_capacity_revised.py --stage tables --run results/..._run1             # only for tier-1 rows
```

Requirements for the runner: refuse any output under `results/capacity_return_difference`, `results/cost_parity_diagnostic`, `results/figures`, `outputs/` or an existing path; claim the output before computation (`output_guard`); read weights only from the census-hashed list and refuse if a hash differs from `results/phase_c_census_v2_2026-10-14/MANIFEST.json`; write `exit_policy`, `dividend_missing`, commit hash, command line, seeds, `n_boot`, library versions, input and output SHA-256 and the label "REVISED ANALYSIS - not confirmatory" into a manifest; compute per-metric union support masks and assign tiers before reading any performance column.

## 5. Validation sequence and objective stop conditions

1. Tree clean at a recorded commit; full suite run serially with the final summary line visible; docs-hygiene and withdrawn-claims screens pass.
2. Census manifest weight hashes equal the current weight-file hashes. **Stop** on any mismatch.
3. Run 1 into a fresh directory. **Stop** on collision, exception, non-finite configuration, or memory pressure (do not restart unattended).
4. Assign tiers from the support masks; write them to disk **before** any performance column is read.
5. Run 2 into a second fresh directory; outputs must be byte-identical (or numerically identical with the difference reported) before interpretation. **Stop** otherwise.
6. If a series is tier >25%: report "not estimable", stop for that series, no test. If tiers 0-25%: apply the committed reporting rules.
7. Confirm no frozen path changed (`git status`, hashes), record everything in the work log.

## 6. What the report on the run would contain under the frozen rule

Unresolved-month counts and shares per series, first unresolved month, the number of distinct lapsing names, `stale_gross` / `unresolved_exit_gross` materiality, and "not estimable" labels. No Sharpe, drag or B.

## 7. Prerequisites before any run (decisions and work)

1. **Classification question (blocking).** Held names that drop out of C6 but stay in C4 are universe exclusions, not demonstrated delistings. The ruling says stale or unpriced positions are flagged and left unresolved, and that a missing C6 row is not confirmation of a delisting; the implementation therefore makes them unresolved. Whether such a name should instead be classified as alive and uncertified (carried at drifted holdings and sold under a stated rule) is a policy question for the people who own the exit ruling. It changes the expected tiers radically. I have not decided it and have not implemented any variant.
2. Spec addendum 2, before any run, fixing: the primary object is the zero-tax capacity B(A) comparison; `n_boot` (2000 vs as-run 4000); the add-one p convention; the source of the valid-rung list; the set of series that enter any family.
3. The runner P-1 with synthetic tests (section 4).
4. Support-mask utility (union per metric) with tests.
5. Review of this report and the census by the user; acknowledgement by Maham of the ruling's consequence for confirmatory results remains outstanding.
6. Cost-calibration sensitivity (S0/S1/S2) and A2 stay unauthorised and out of scope.

## 8. Not verified here

The success path of every step above was not executed (that would run the analysis). The census approximates the engine's leaver rule from membership and counts only names with a weight in the scored month. Weight-file hashes establish present state, not equality with 2026-10-10.
