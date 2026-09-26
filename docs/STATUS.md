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

### The tax-aware optimiser path: broken for most of 21 September, now fixed

Worth recording because it took three attempts and the first two looked like fixes.

The harvesting term was modelled with an auxiliary sell variable constrained by
`s <= prev - w`. With `s >= 0` that implies **`w <= prev`**: every position could only ever shrink.
Restricting `s` to long positions stopped shorts being frozen open and left longs frozen shut -
the failure rate moved from roughly 60% of months to 36%, which looked like progress and was not.

The error was the auxiliary variable itself. **A constraint introduced to model an objective term
must never restrict the decision variable.** The credit `rate * |g| * (prev - w)` is affine in `w`
and needs no variable at all.

Separately, `cp.pos()` was built across all 556 names when the coefficient is non-zero only for
long positions carrying an embedded gain. CVXPY adds an auxiliary variable per element, so the
problem was roughly twice the necessary size.

    before   ~60% of months failed, 98-150 min per 216-month run
    after    36 of 36 months optimal, 311s for 36 months (3x faster)

Two one-line tests now pin it: the tax term must generate **no constraints at all**, and a held
long must still be able to grow. Both test properties of the problem rather than internals of the
implementation - which is the lesson, because three existing tests had to be rewritten after the
fix, and one of them had asserted the bound came from `s <= prev`. That assertion encoded the bug
and would have defended it indefinitely.

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
