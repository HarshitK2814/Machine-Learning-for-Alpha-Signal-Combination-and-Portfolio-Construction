# Workstream B status (Harshit)

Updated: 2026-09-20. Synthetic data only. **No real-data or paper results exist.**

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

Total: 117 tests, 116 passing and 1 skipped (a solver-dependent optimiser path).

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
