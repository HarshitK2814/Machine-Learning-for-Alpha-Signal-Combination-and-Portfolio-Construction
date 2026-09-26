# Team Coding Work Distribution

## 1. Purpose and Principles

This document splits the coding work for the selected paper (*Where Does Machine-Learning Alpha Come From After Trading Costs?*) among three team members. **All three are equal partners.** Nobody is a lead, nobody holds extra approval rights, and every member carries the same planned workload. Work runs **in parallel** and merges at the end **without conflicts**. Tasks map to the experiment IDs (E00-E64) in Workbook 4 and the specification in PDF 4. Members are listed alphabetically throughout.

**Team and workstreams**

| Member | Background | Workstream | Planned effort |
|---|---|---|---|
| **Absar** | Data engineering | **Workstream A:** data, transaction costs and backtesting | 100 points (1/3) |
| **Harshit** | ML modelling; portfolio construction; data engineering | **Workstream B:** models and portfolio construction | 100 points (1/3) |
| **Maham** | Statistics & reporting | **Workstream C:** baselines, statistics and reporting | 100 points (1/3) |

**How the split was balanced**
- **Equal effort.** Every task has an effort estimate in planning points (Section 5), and each member's tasks sum to exactly 100. Points are planning estimates. If actual effort in one workstream drifts more than 15% from the others, tasks are rebalanced at the next checkpoint by agreement of all three.
- **Matched to background.** Each workstream fits the member's stated strengths. No workstream is treated as more central than another: the paper needs all three to produce a single result.
- **Shared duties are shared.** The contracts, split calendar, integration script, specification freeze and lockbox run belong to the whole team. The duty of running each integration checkpoint rotates (Section 6).
- **Symmetric review.** Pull requests are reviewed in a circle (Absar reviews Harshit, Harshit reviews Maham, Maham reviews Absar). Changes to shared files need all three approvals.

**Five rules that make parallel work mergeable**

1. **Contracts first.** In Week 1 all three members jointly agree and freeze every data schema, file path and function signature that crosses a workstream boundary (Section 4). Afterwards, contracts change only through a Contract Change Request approved by all three.
2. **Folder ownership.** Each member edits only their workstream's folders (Section 3). Nobody edits another member's files, so Git merge conflicts cannot occur in source code.
3. **Synthetic data from day one.** A synthetic dataset with the exact real schema is available in Week 1. Everyone builds and tests against it, so nobody waits for anybody else.
4. **Run-ID keyed outputs.** Every output file is written under its own `run_id`, so runs never overwrite each other.
5. **Continuous contract tests.** CI validates every output against the frozen schemas on every pull request. Integration problems surface in days, not at the end.

{{PAGEBREAK}}

## 2. Overview Diagrams

{{FIG:fig_team_interfaces.png|Figure 1. Workstream ownership and the artefacts (contracts) that flow between members. Every arrow is a frozen schema validated in CI.}}

{{FIG:fig_team_timeline.png|Figure 2. Parallel work plan by week (planning estimate). Vertical lines mark integration checkpoints; all three lanes run simultaneously.}}

## 3. Repository Layout and Ownership (CODEOWNERS)

```text
alphacomb/
  pyproject.toml, environment.yml, .pre-commit-config.yaml   SHARED (frozen Week 1; changes need 3 approvals)
  configs/base.yaml, configs/splits.yaml                      SHARED
  configs/data.yaml, configs/costs.yaml, configs/backtest.yaml   ABSAR (A)
  configs/models.yaml, configs/portfolio.yaml, configs/risk.yaml HARSHIT (B)
  configs/stats.yaml, configs/robustness/*.yaml               MAHAM (C)
  src/alphacomb/contracts/   schemas.py, io.py, paths.py, splits.py, VERSION   SHARED
  src/alphacomb/synthetic/   synthetic data generator (same schemas)          ABSAR (A)
  src/alphacomb/data/        WRDS pulls, PIT panel, universe, signals, states  ABSAR (A)
  src/alphacomb/costs/       spreads, impact function, borrow fees            ABSAR (A)
  src/alphacomb/backtest/    P&L engine, execution lag, drift, cost ledger    ABSAR (A)
  src/alphacomb/models/      16 factorial cells, uncertainty, published ML    HARSHIT (B)
  src/alphacomb/portfolio/   TC-aware optimiser, constraints, E-cell projection  HARSHIT (B)
  src/alphacomb/risk/        structural factor risk model                      HARSHIT (B)
  src/alphacomb/interpret/   SHAP/ALE, economic feature importance            HARSHIT (B)
  src/alphacomb/baselines/   naive, linear, KNS SDF, linear PPP, banding      MAHAM (C)
  src/alphacomb/stats/       NW, LW2008, CW/DM, SPA, StepM, MCS, DSR, PBO, decomposition  MAHAM (C)
  src/alphacomb/reporting/   tables, figures, LaTeX export                     MAHAM (C)
  pipelines/01_build_data.py, 05_backtest.py                  ABSAR (A)
  pipelines/02_train_models.py, 04_construct_portfolios.py    HARSHIT (B)
  pipelines/03_baselines.py, 06_inference.py, 07_report.py    MAHAM (C)
  pipelines/run_all.py        SHARED (only calls stage scripts; no logic)
  tests/contracts/            SHARED
  tests/data, tests/costs, tests/backtest, tests/synthetic     ABSAR (A)
  tests/models, tests/portfolio, tests/risk, tests/interpret   HARSHIT (B)
  tests/baselines, tests/stats, tests/reporting                MAHAM (C)
  data/  outputs/  mlruns/    git-ignored (never committed)
```

## 4. Interface Contracts (agreed jointly and frozen in Week 1)

All tables are Parquet, keyed by `date` (month-end, `datetime64[ns]`) and `permno` (`int32`). Schemas are enforced with `pandera` in `src/alphacomb/contracts/schemas.py`. Paths are generated only by `contracts/paths.py`; nobody hard-codes file paths.

| # | Artefact (path) | Produced by | Used by | Required columns | First version |
|---|---|---|---|---|---|
| C1 | `data/processed/universe.parquet` | Absar | All | date, permno, in_universe (bool), me, price, exchcd, ff49, nyse_size_pct | Synthetic W1; real W9 |
| C2 | `data/processed/signals.parquet` | Absar | Harshit, Maham | date, permno, sig_* (float32 in [-0.5, 0.5]), miss_<theme> (int8) | Synthetic W1; real W9 |
| C3 | `data/processed/signal_meta.csv` | Absar | Harshit, Maham | signal, theme, pub_year, source | W1 |
| C4 | `data/processed/targets.parquet` | Absar | Harshit, Maham | date, permno, r_1m, r_3m, r_6m, r_12m (excess, delisting-adjusted), ret_next | Synthetic W1; real W9 |
| C5 | `data/processed/states.parquet` | Absar | Harshit, Maham | date, MKTVOL, BEAR, ILLIQ, SENT, CREDIT, TERM, INFL, DRATE, FMOM_<theme>, DISP | Synthetic W1; real W10 |
| C6 | `data/processed/cost_inputs.parquet` | Absar | Harshit, Maham | date, permno, spread, sigma_d, adv_usd, borrow_fee | Synthetic W1; real W12 |
| C7 | `risk.load(date) -> RiskModel(B, F, D)` | Harshit | Harshit, Maham | B: permno × factor DataFrame; F: factor covariance; D: specific variance Series | Synthetic W2; real W12 |
| C8 | `configs/splits.yaml` + `contracts/splits.py` | All (Week 1 sprint) | All | train/validation/test/lockbox calendar, embargo rule | W1 |
| C9 | `outputs/predictions/{strategy}/{run_id}.parquet` | Harshit (cells), Maham (baselines) | Harshit, Maham | date, permno, score, alpha, unc_sd (nullable) | Synthetic W5 |
| C10 | `outputs/weight_proposals/{strategy}/{run_id}.parquet` | Harshit (E-cells), Maham (linear PPP) | Harshit | date, permno, w_prop | Synthetic W8 |
| C11 | `outputs/weights/{strategy}/{run_id}.parquet` | Harshit (optimiser), Maham (banding) | Absar, Harshit, Maham | date, permno, w | Synthetic W6 |
| C12 | `outputs/returns/{strategy}/{run_id}.parquet` | Absar (backtest) | Harshit, Maham | date, gross_ret, net_ret, turnover, cost_spread, cost_impact, cost_borrow, long_ret, short_ret | Synthetic W6 |
| C13 | `outputs/trials.csv` (append-only via `contracts/io.log_trial`) | Everyone who trains or tunes | Maham (DSR, PBO, SPA) | run_id, strategy, cell, params_json, seed, train_end, val_metric, git_sha, timestamp | W1 |

**Function signatures (frozen).**

```python
# contracts/interfaces.py  (SHARED, frozen Week 1)
def fit_predict(cell: CellSpec, split: Split, data: DataBundle,
                cfg: dict) -> pd.DataFrame: ...          # Harshit/Maham -> C9 rows
def construct(date, alpha: pd.Series, w_prev: pd.Series, risk: RiskModel,
              costs: pd.DataFrame, cfg: dict) -> pd.Series: ...   # Harshit -> C11
def trade_cost(dq_usd: pd.Series, cost_row: pd.DataFrame,
               cfg: dict) -> pd.Series: ...              # Absar; used by all
def backtest(weights: pd.DataFrame, targets: pd.DataFrame,
             costs: pd.DataFrame, cfg: dict) -> pd.DataFrame: ...  # Absar -> C12
def run_tests(returns: dict[str, pd.DataFrame], trials: pd.DataFrame,
              cfg: dict) -> dict[str, pd.DataFrame]: ...  # Maham -> tables
```

**Contract Change Request (CCR).** A CCR is a pull request that edits only `contracts/` or `tests/contracts/`. It bumps `contracts/VERSION`, describes the migration, and needs approval from all three members. Each member then updates their own modules in separate PRs. Additive changes, such as a new nullable column, are preferred over renames.

## 5. Work Assignment by Member (equal effort: 100 points each)

Planning points are relative effort estimates, not hours or importance. Every member also carries the same 10 points of shared duties: the Week 1 contracts sprint (4), one rotating integration checkpoint (3) and peer review (3).

### 5.1 Absar: Workstream A (data, transaction costs, backtesting)

| Area | Tasks | Exp. IDs | Deliverables | Acceptance criteria | Points |
|---|---|---|---|---|---|
| Synthetic data | Generator producing C1-C6 with realistic shapes (e.g., 500 stocks × 300 months), planted effects, missingness, delistings, cost ranges | - | `synthetic/generate.py`, `data/synthetic/*` | Passes all contract tests; used by everyone from Week 2 | 10 |
| WRDS extraction & PIT panel | CRSP monthly/daily, delistings, Compustat + CCM, accounting lags, universe filters | E00 | `data/wrds_pull.py`, `data/pit_panel.py`, C1, C4 | Rebuilt FF factors correlate > 0.95 with Ken French; zero look-ahead test failures | 18 |
| Signal library | ~150 JKP/OpenAP signals, rank normalisation, missing indicators, publication years, gated-library flags | E01 | `data/signals/*`, C2, C3 | Replication slope/R² vs Chen-Zimmermann reported | 16 |
| State variables | MKTVOL, BEAR, ILLIQ, SENT, CREDIT, TERM, INFL, DRATE, FMOM, DISP; placebo versions | - | `data/states.py`, C5, `states_placebo.parquet` | No future information (tests); placebo files for E53 | 6 |
| Transaction-cost model | Spread hierarchy (TAQ/EDGE/Abdi-Ranaldo), ADV, volatility, borrow fees; `trade_cost()` | E31 | `costs/*`, C6 | Spread-estimator correlation with TAQ reported; 0.5×-3× multipliers configurable | 14 |
| Backtest engine | Execution lag, drifted weights, gross/net P&L, cost ledger, AUM scaling, reconciliation; frontier and capacity runs | E30, E32 | `backtest/engine.py`, C12 | Contributions reconcile to portfolio return (tolerance 1e-8); AUM grid and capacity outputs | 20 |
| International data | JKP developed ex-US panel in the same schemas | supports E55 | `data/international/*` | Contract-valid files | 6 |
| Shared duties | Contracts sprint; runs checkpoint **IC1**; peer review of Harshit's PRs | - | IC1 report | IC1 passes | 10 |
| **Total** | | | | | **100** |

### 5.2 Harshit: Workstream B (models, portfolio construction)

| Area | Tasks | Exp. IDs | Deliverables | Acceptance criteria | Points |
|---|---|---|---|---|---|
| Factorial ML cells | 16 cells: linear/nonlinear × static/state × prediction/economic loss; gated mixture-of-experts; economic-loss NN policy | E20-E27 | `models/cells/*`, `configs/models.yaml` | Every cell runs on synthetic (IC1) and real data (IC3); all trials logged to C13 | 28 |
| Uncertainty | Deep ensembles and bagging, κ-shrinkage, bootstrap-SE variant | E28 | `models/uncertainty/*` | `unc_sd` populated; κ chosen on validation only | 7 |
| Published ML benchmarks | GKX-style NN3 and LightGBM; JKMP Portfolio-ML replication from authors' code | E13 | `models/benchmarks/*` producing C9/C10 | Directional replication documented | 9 |
| Portfolio optimiser | CVXPY TC-aware mean-variance; neutralities, position/trade/ADV limits; E-cell projection; long-only variant | E33 | `portfolio/*`, `configs/portfolio.yaml` | Constraint violations < 0.1% of months; solver failures logged | 18 |
| Risk model | Structural factor model (beta, 13 themes, FF49); EWMA factor/specific risk; PCA alternative; alignment diagnostics | E64 | `risk/*`, C7 | Bias statistics reported; `risk.load(date)` < 2 s per month | 14 |
| Seeds & stability | 10+ seeds; ±1 grid-step perturbations | E56 | Seed-dispersion outputs | Dispersion table shared with the team | 5 |
| Interpretation | Economic feature importance (leave-theme-out), TreeSHAP/deep SHAP, ALE | E60 | `interpret/*`, figure-ready CSVs | Results tied to hypothesis H3 | 9 |
| Shared duties | Contracts sprint; runs checkpoint **IC2**; peer review of Maham's PRs | - | IC2 report | IC2 passes | 10 |
| **Total** | | | | | **100** |

### 5.3 Maham: Workstream C (baselines, statistics, reporting)

| Area | Tasks | Exp. IDs | Deliverables | Acceptance criteria | Points |
|---|---|---|---|---|---|
| Statistics library | Newey-West, Ledoit-Wolf Sharpe tests, Clark-West, Diebold-Mariano, Hansen SPA, White RC, Romano-Wolf StepM, MCS, DSR, PBO, Harvey-Liu haircut, BH-FDR, Bai-Perron | - | `stats/*` with unit tests on simulated series | Known size/power reproduced on simulations | 17 |
| Signal diagnostics | IC, rank IC, ICIR, IC half-life, turnover; redundancy clustering | E02, E03 | `baselines/diagnostics.py`, tables | Synthetic by W6, real by W11 | 7 |
| Baselines | EW/theme-EW/IC/ICIR/inverse-vol composites; Lewellen FM, ridge, lasso, ENet, PLS; KNS shrunk SDF; linear PPP with costs (DMNU); NMV buy/hold banding | E10, E11, E12, E14, E34 | `baselines/*` producing C9/C10/C11 | Same tuning budget as model cells; contract tests pass | 17 |
| Factorial decomposition | Orthogonal-contrast regressions, Shapley attribution, block-bootstrap CIs | E29 | `stats/decomposition.py` | Recovers planted effects on synthetic data | 8 |
| Inference | SPA/StepM/MCS, DSR/PBO over C13, factor alphas, multiverse non-standard errors | E40-E43 | `pipelines/06_inference.py`, tables | Every pre-registered test reported | 14 |
| Robustness orchestration | Config grids for subperiods, universes, horizons, placebo states, gated library, international | E50-E55 | `configs/robustness/*.yaml`, appendix tables | All runs reproducible from configs alone | 11 |
| Mechanisms & implied weights | Implied state-dependent weights; limits-to-arbitrage tilts; trading speed vs liquidity state | E61, E62, E63 | Regression tables | Linked to hypotheses H5/H6 | 7 |
| Reporting | Publication tables and figures, LaTeX export, experiment-status dashboard | - | `reporting/*`, `pipelines/07_report.py` | One command regenerates all paper tables | 9 |
| Shared duties | Contracts sprint; runs checkpoint **IC3**; peer review of Absar's PRs | - | IC3 report | IC3 passes | 10 |
| **Total** | | | | | **100** |

#### Workload check

| Member | Own tasks | Shared duties | Total | Share |
|---|---|---|---|---|
| Absar | 90 | 10 | 100 | 33.3% |
| Harshit | 90 | 10 | 100 | 33.3% |
| Maham | 90 | 10 | 100 | 33.3% |

## 6. Parallel Timeline and Integration Checkpoints (weeks, planning estimate)

| Weeks | Absar | Harshit | Maham | Checkpoint (run by) |
|---|---|---|---|---|
| 1 | Contracts sprint (all together); synthetic data generator | Contracts sprint (all together); model and optimiser interfaces | Contracts sprint (all together); stats-library design | **Contracts v1.0 frozen** by all three |
| 2-6 | WRDS pulls; PIT panel; universe; E00 | Cells LS-P, NS-P on synthetic; optimiser v1 | Stats library + tests; naive/linear baselines on synthetic | **IC1 (W6): full synthetic end-to-end** (run by Absar) |
| 7-12 | Signals E01, states, cost model; real data v1 (W9) and v2 (W12) | Conditional cells, MoE, economic-loss learners, uncertainty; risk model | Diagnostics E02/E03; baselines and E14 on real data; decomposition code | **IC2 (W12): real-data end-to-end** (run by Harshit) |
| 13-20 | Backtest runs; frontier E30; cost sensitivity E31; capacity E32 | All 16 cells walk-forward; benchmarks E13; alignment E64 | Inference E40-E42; decomposition E29; report templates | **IC3 (W20): complete development results** (run by Maham) |
| 21 | Specification freeze (all three sign) | Specification freeze (all three sign) | Specification freeze (all three sign) | **Freeze tag `v-freeze`** (joint) |
| 22 | Lockbox backtests | Lockbox model and portfolio runs | Lockbox inference | **Lockbox opened once, together** |
| 23-28 | International data; capacity reports | Seeds E56; interpretation E60; optimiser variants E33 | Robustness E50-E55; multiverse E43; mechanisms E61-E63; final tables | **Final merge & release tag `v-paper`** (joint) |

**Nobody is blocked.** Before real data exists, everyone uses the synthetic C1-C6. When real data arrives, the only change is a flag in `configs/base.yaml` (`data_source: synthetic | real`).

## 7. Git Workflow (conflict-free merging)

1. **Branches.** `main` is protected. Work branches are `absar/<topic>`, `harshit/<topic>` and `maham/<topic>`, short-lived (≤ 1 week) and rebased on `main` daily.
2. **Pull requests.** A PR touches only its author's owned paths; CI rejects PRs that modify another member's files (CODEOWNERS plus a path check). Review is circular and equal: Absar reviews Harshit, Harshit reviews Maham, Maham reviews Absar. Shared files need all three approvals.
3. **CI on every PR.** Formatting (ruff/black via pinned pre-commit), unit tests, **contract tests on synthetic data**, and a 5-minute smoke run of the whole pipeline on a tiny synthetic sample.
4. **No shared mutable state.** Outputs are written under `run_id`. The trial log is append-only through `contracts/io.log_trial` with a file lock. Nothing in `data/` or `outputs/` is committed.
5. **Dependencies.** `environment.yml` is pinned. Adding a package is a small shared PR approved by all three.
6. **Configs over code.** Robustness variants, cost multipliers and AUM levels are configuration files, so grids run over any workstream's code without editing it.
7. **Reproducibility.** Every run records `git_sha`, config hash, seed and data version. Checkpoints create tags (`ic1`, `ic2`, `ic3`, `v-freeze`, `v-paper`).
8. **Weekly 30-minute sync.** Facilitation rotates weekly among the three members. Review the contract-test dashboard, blockers and effort points; any contract concern becomes a CCR within 48 hours.

## 8. Definition of Done (same for every member)

- Code sits only in the owner's folders, with docstrings and type hints.
- Unit tests pass, and contract tests pass on synthetic data (and on real data after IC2).
- Behaviour is driven by a config file with no hard-coded paths, dates or parameters.
- Every training or tuning run is logged to `outputs/trials.csv`.
- Outputs regenerate from a single pipeline command.
- The PR is reviewed by the circular reviewer, and the experiment status and spent effort points are updated in Workbook 4.

## 9. Risks to Parallel Work and Mitigations

| Risk | Impact | Mitigation | Handled by |
|---|---|---|---|
| Workloads drift apart | Unequal effort | Effort points tracked weekly; rebalance at checkpoints if any workstream differs by more than 15% | All |
| Synthetic data too unrealistic | Code breaks on real data | Realistic missingness, delistings, fat tails and cost ranges; 2-week buffer before IC2 | Absar |
| Contract changes mid-project | Rework | Additive-only changes; CCR with 3 approvals; version bump | All |
| WRDS/TAQ access delays | Real data late | Synthetic pipeline continues; OpenAP/JKP public files as interim real signals | Absar |
| Model compute bottleneck | IC3 slips | LightGBM cells first; NN cells on GPU; reduced development grid | Harshit |
| Inference bugs found late | Wrong conclusions | Statistics library validated on simulations before real results exist | Maham |
| Hidden test-period tuning | Invalid lockbox | Split calendar enforced in shared code; lockbox dates blocked until `v-freeze` exists | All |
| One member unavailable | Delays | Circular reviewers know neighbouring modules; docs and tests allow hand-over | All |
