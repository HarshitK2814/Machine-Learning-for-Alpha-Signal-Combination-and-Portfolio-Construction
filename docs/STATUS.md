# Workstream B status (Harshit)

Updated: 2026-09-21. Synthetic data only. **No real-data or paper results exist.**

## Done

| Area | Experiment IDs | State | Evidence |
|---|---|---|---|
| Contracts C1-C13, split calendar, lockbox guard | - | Done (shared, frozen v1.0.0) | `tests/contracts` (12 tests) |
| Synthetic stand-in data (workstream A placeholder) | - | Done | `tests/synthetic` (5 tests) |
| Structural risk model | E64 input | Done | `tests/risk` (6 tests), point-in-time proof |
| Cost-aware optimiser, projection, alpha scaling | E33 | Done | `tests/portfolio` (9 tests) |
| 16 factorial cells: linear, nonlinear, conditional, economic | E20-E27 | Done | `tests/models` (11 tests) |
| Uncertainty shrinkage with validation-tuned kappa | E28 | Done | nested at kappa = 0 |
| Interpretation: economic importance, implied weights, state dependence, LTA tilts | E60-E62 | Done | `tests/interpret` (5 tests) |
| Pipelines 02 and 04, temporary dev backtest | - | Done | smoke run on the full synthetic panel |
| Design v2 frontier: complexity ladder, conformal, attention, robust optimisation | E65-E68 | Done | `tests/models/test_frontier.py` (16 tests) |
| Falsification audit: zero-predictability null, placebo, inflation gap | E69 | Done, 4 fixes open | `docs/FALSIFICATION_AUDIT.md` |
| **After-tax ledger: lots, wash sales, holding periods, 4 investor regimes** | **E70-E72 (new)** | **Done** | `tests/tax` (22 tests) |
| **Tax terms inside the optimiser, with the s1091 block** | **E73 (new)** | **Done** | `tests/portfolio/test_tax_terms.py` (11 tests) |
| **Self-adapting combination: Hedge with fixed share, drift detection** | **E74-E75 (new)** | **Done** | `tests/adaptive` (15 tests) |
| Pipelines 06 (after-tax) and 07 (adaptive) | - | Done | run on the 2003-2020 synthetic span |

| **Optimiser feasibility under drifted weights** | **fix** | **Done** | `tests/portfolio/test_cap_feasibility.py` (4 tests) |
| Stale-portfolio guard in stage 04, construction quality in stage 06 | - | Done | `--max-held-share`, `held_share` column |

Total: **130 tests, all passing, none skipped.**

### KNOWN BROKEN: the tax-aware optimiser path

`--tax-aware` construction does **not** work. Two bugs were found and fixed on 21 September - an
unbounded embedded gain rate producing 4000x phantom harvesting credits, and a harvesting
constraint that forbade covering short positions - and it is **still** failing on roughly half of
all months (128 of 216 at gross 2, 102 of 216 at gross 4). It is also extremely slow: 98 to 150
minutes per 216-month run against 6 minutes for the tax-blind path.

**Do not report any result from the tax-aware optimiser arm.** The evaluation ledger
(`alphacomb.tax`) is unaffected and every after-tax number in `docs/AFTER_TAX_RESULTS.md` and
`docs/PRACTITIONER_GAP.md` stands, because the ledger never builds the optimiser's tax term.

Next diagnostic step: the auxiliary harvesting variable plus the cap-relaxation constraints are
probably jointly infeasible in some months. Instrument `construct()` to report which constraint
set is binding when it fails, rather than guessing a third time.

### A bug worth knowing about before reading any number in this repo

The first 216-month walk-forward was **void**. Two cells had silently degraded into stale
buy-and-holds (`cell_N-C-P-0` held weights on 69% of months, `cell_N-S-P-0` on 43%) because three
optimiser constraints become infeasible once weights drift past what ADV-capped trading can unwind.
Nothing crashed; the output was contract-valid the whole way through. The failure was correlated
with the treatment - it hit the cells that trade small illiquid names - so it was on course to
produce "nonlinearity adds no net value" as an artefact of the solver.

Fixed, guarded and written up in `docs/SILENT_OPTIMISER_FAILURE.md`. Every strategy now reports its
held-weight share, and stage 04 exits non-zero above 2%. After the fix all five full-span
strategies solve 216/216 optimal.

Contracts bumped to **v1.1.0**, additively: optional `targets.div_next` (the dividend part of
`ret_next`) and optional tax columns on `returns` (C12). Nothing existing breaks.

## Verified on the synthetic panel (development check, not a result)

* `L-S-P-0` over test years 2018-2019: validation rank IC 0.054, test rank IC 0.060, so the linear
  cell recovers the planted effects out of sample.
* `L-S-E-0` trains its economic policy and produces feasible proposals.
* Every configuration tried is logged to `outputs/trials.csv`.

## Not started or blocked

| Item | Why | Owner |
|---|---|---|
| Real-data runs | Contracts C1-C6 not yet available | Absar |
| Published ML benchmarks E13 (GKX NN3 config, JKMP Portfolio-ML replication) | Needs the real signal library; the code path exists | Harshit |
| Seed dispersion E56 | Cheap to run once the real data lands | Harshit |
| Gamma calibration on validation dates | `portfolio.calibrate_gamma` exists; run it in Phase 6 | Harshit |
| Full 16-cell walk-forward 1995-2020 | Compute; run once the data is real | Harshit |
| Backtest engine C12 | Stand-in only | Absar |
| Baselines, statistics, robustness, reporting | Contracts ready | Maham |

## Next actions for Harshit

1. Run the full 16 cells on synthetic data over 1995-2020 as a compute rehearsal and to give Maham
   realistic files for the decomposition.
2. Add the published-benchmark presets (E13) behind the same interface.
3. Re-run `calibrate_gamma` and freeze the value in `configs/portfolio.yaml`.
4. Review Absar's first C1-C6 delivery against `docs/HARSHIT_NEEDS_FROM_ABSAR.md`.
5. Close the four falsification-audit fixes in `docs/FALSIFICATION_AUDIT.md`, starting with the
   strict null.
6. Run the three-arm tax-aware construction comparison (tax-blind / tax-aware / tax-aware +
   wash-block). The code path exists; it has not been measured over the full span.
7. Ask Absar for `div_next` (CRSP `RET` minus `RETX`). Until it arrives, dividend tax is an
   assumption, not a measurement.
