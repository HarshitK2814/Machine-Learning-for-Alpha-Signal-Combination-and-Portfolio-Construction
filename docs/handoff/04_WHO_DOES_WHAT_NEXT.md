# Who does what next, building on workstream B

**22 September 2026.** Companion to `03_HARSHIT_WORK_COMPLETED.md`. That document says what exists;
this one says what each person does with it.

---

## 0. The critical path, in one picture

```
  Absar: feasibility note (Priority 0)        <- THIS WEEK, gates everything
            |
            v
  Absar: C1-C6 + C14 per country              <- the only fatal blocker
            |
            +---> Harshit: run the frozen pipeline on real data
            |             |
            |             +---> C9 predictions, C11 weights, C13 trials
            |                        |
            |                        v
            |             Maham: baselines through the SAME stage 04,
            |                    then DSR / PBO / SPA / StepM on everything
            |                        |
            +---> Absar: C12 backtest from OUR after-tax engine, not parallel to it
                                     |
                                     v
                          Maham: tables, figures, LaTeX -> the paper
```

Everything below the first box is blocked until it is answered. Nothing below it is blocked by
anything *other* than it.

---

## 1. Absar — what to do with workstream B's work

### 1.1 Do not rebuild these

| Thing | Where it already is | Why it matters |
|---|---|---|
| The C12 backtest engine | `alphacomb.tax.after_tax_backtest` — already writes a contract-valid C12 with additive tax columns | Two independent engines **will** disagree. This has already happened once in this project with the optimiser and cost a day. Start from ours; add the one-day lag, delisting-month handling and hard-to-borrow escalation |
| The cost formula | `alphacomb.portfolio.cost_terms.trade_cost_numpy` | This is the reference. Your `alphacomb.costs.trade_cost` must return the same number for the same trade |
| The synthetic generator | `src/alphacomb/synthetic/generate.py` | Keep it as the CI fixture generator even after real data lands. Please preserve the schemas and the `truth.json` idea |

### 1.2 Write these

1. **A test that your cost function matches ours**, on the same inputs. Not agreement by inspection —
   an actual test. If the two ever disagree, the net-of-cost attribution is meaningless, and that
   attribution is the paper's headline.
2. **`alphacomb.contracts.validate` run over every file before handing it over.** It catches dtype,
   key-uniqueness and range violations. A silent duplicate `(date, permno)` corrupts every
   cross-sectional operation and no downstream test will find it.

### 1.3 Consume these

| Artefact | Path | What it is |
|---|---|---|
| C11 weights | `outputs/weights/<strategy>/<run_id>.parquet` | The input to your backtest. Already constraint-feasible: dollar-neutral, gross ≤ 2, position and ADV caps respected — **and as of 22 September that is verified by measurement rather than assumed from the solver's status** |
| C7 risk model | `alphacomb.risk.StructuralRiskModel(bundle).load(date)` | If the backtest wants predicted volatility for reporting; also the source of the E64 bias statistic |

### 1.4 The one thing only Absar can guarantee

**No look-ahead.** Our tests assume it and cannot detect it. Accounting items lagged to availability,
states observable at t, signals using only information up to t, expanding-window standardisation
only. This is the single assumption of the entire project that rests wholly on workstream A.

---

## 2. Maham — what to do with workstream B's work

### 2.1 Settle the statistics ownership first

See `02_NEEDS_FROM_MAHAM.md` §1. There are two inference implementations
(`src/alphacomb/validation/inference.py` and `src/alphacomb/stats/`) and one has to go or be clearly
subordinated. **I will do the work of whichever resolution you pick, including deleting mine.** What
cannot survive to submission is two numbers for the same quantity.

### 2.2 The one rule for baselines

**Write baselines as C9 and pass them through stage 04.** Do not build a separate portfolio path.

```python
from alphacomb.portfolio import grinold_alpha
from alphacomb.contracts import paths, write_table
write_table(frame, paths.predictions_path("baseline_ew", run_id), "predictions")
# python pipelines/04_construct_portfolios.py --strategies baseline_ew
```

If a baseline gets its own construction, any performance difference between a baseline and a cell is
a mixture of model and machinery, and the paper's central comparison stops meaning anything. I made
exactly this mistake on the adaptive layer and it inverted the conclusion.

### 2.3 Consume these

| Artefact | Path | Note |
|---|---|---|
| C9 predictions | `outputs/predictions/cell_<CODE>/<run_id>.parquet` | `alpha` is already Grinold-scaled using validation-period IC, so cells are comparable. `unc_sd` is `NaN` for non-uncertainty cells |
| C10 weight proposals | `outputs/weight_proposals/cell_<CODE>/<run_id>.parquet` | E-cells only |
| C11 weights | `outputs/weights/<strategy>/<run_id>.parquet` | From the shared optimiser |
| C13 trial log | `outputs/trials.csv` | **The DSR denominator.** Includes losers and the κ search. Append-only via `contracts/io.log_trial` |
| Per-split diagnostics | `outputs/models/cell_<CODE>/<run_id>/diagnostics.csv` | For the prediction-vs-value table and for spotting a cell that failed a year |
| After-tax ledger | `outputs/summary_after_tax.csv` + C12 with extra columns | Additive columns, optional in v1.1.0 — **your existing statistics code keeps working unchanged** |
| Adaptive panel | `outputs/summary_adaptive.csv`, `adaptive_report.json` | Contains the benchmarks the adaptive row must be shown against. **Please report all of them together** — the adaptation is worth −0.003 against the like-for-like benchmark, and that has to be visible, not buried |
| Cell contrast coding | `CellSpec.contrasts()` | ±1 coding and interactions for the factorial decomposition, already verified orthogonal |

### 2.4 Two things to be careful about

1. **The DSR trial count must come from `prereg/PLAN_001`** (64 configurations, fingerprint
   `cae8140b7e2b7ee4`), **not from counting rows in the trial log.** At the naive N=539 nothing
   survives — expected max 0.727 against a best of 0.695. At N=64 the hurdle is 0.465. The
   difference between those two numbers is the difference between a paper and no paper, so the
   choice has to be pre-registered and stated in the text, not discovered afterwards.
2. **Inference runs on the after-tax NAV series**, not on a pre-tax series with a tax figure
   subtracted. The after-tax series is non-Gaussian in a way that matters: harvesting truncates the
   left tail and the §1211(b) ordinary-offset cap puts a kink in it. The higher-moment Sharpe
   correction is required here, not optional.

---

## 3. Harshit — what I do next

**Blocked on data (cannot start):** real-data C1–C6 runs, the international comparison, every
empirical claim in the paper.

**Not blocked (doing now, in order):**

1. Verify the last two optimiser changes — last green run was 228 tests, before them.
2. **Measure whether finding #11 (infeasible solver selection) moves the synthetic results.** Until
   this is done I do not know whether the after-tax and overhang numbers need re-running or a
   footnote, and I will not guess.
3. The four falsification-audit fixes, strict null first.
4. Write the theory model's paper-facing section — the module exists, the exposition does not.
5. Run the inference layer on the TALS overhang results.
6. Refresh `docs/STATUS.md`, which is stale.

**Owed to the others:** the C11/C9/C13 artefacts above, and the reference cost implementation, all of
which exist today on synthetic data.

---

## 4. Shared, and genuinely shared

| Item | Note |
|---|---|
| Contracts C1–C13, and **C14 (statutory charges), which is new and unowned** | Contract changes need all three approvals. C14 is specified in `01_NEEDS_FROM_ABSAR.md` §3.6 but nobody has formally taken it |
| The split calendar and lockbox | Any use of 2021–2025 data raises `LockboxError` until the team sets `ALPHACOMB_FREEZE_TAG` |
| The closest-prior-art table | Must be maintained to submission, not written once. It is the standing defence against claiming published novelty |
| Pre-registration | Frozen. Changing it after seeing results is the one thing that would make the deflation argument worthless |

## 5. The decisions that need making, with owners

| # | Decision | Owner | By when |
|---|---|---|---|
| 1 | Which countries are actually sourceable | **Absar** | This week — gates everything |
| 2 | Who owns the statistics layer | **Maham** | This week — two implementations cannot both survive |
| 3 | Who owns contract C14 (statutory charges) | **All three** | Before data work starts |
| 4 | Whether C12 starts from our after-tax engine or is rebuilt | **Absar**, with my strong preference on record | Before week 12 |
| 5 | Figure palette — mine or Maham's | **Maham** | Before the first figure goes in the draft |
