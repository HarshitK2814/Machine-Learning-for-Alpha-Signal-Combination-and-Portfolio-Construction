# Experimental Framework and Implementation Specification

This document is written to be handed directly to a quant developer. Parameter values are the **proposed baseline**. Any change after the lockbox specification freeze (end of Phase 7) must be logged as a deviation.

## 1. End-to-End Research Pipeline

| # | Stage | What happens | Key controls | Output artefact |
|---|---|---|---|---|
| 1 | Data | Pull CRSP, Compustat, CCM, TAQ spreads, factors, states | Versioned raw extracts with pull dates | `data/raw/*` + manifest |
| 2 | Point-in-time engineering | Lag accounting data, link identifiers at t, apply delisting returns, build month-end panels | Automated look-ahead unit tests | `panel_pit.parquet` |
| 3 | Feature / signal generation | Compute ~150 JKP/OpenAP signals; publication-year flags | Replication tests vs published t-stats | `signals.parquet` |
| 4 | Signal cleaning | Remove signals with <50% average coverage; handle outliers via ranks | Coverage report by year | `signal_qc.csv` |
| 5 | Normalisation | Cross-sectional rank to [-0.5, 0.5]; missing → 0 + theme missing indicators | Only information at t | `X_t` arrays |
| 6 | Signal quality analysis | IC, rank IC, ICIR by horizon; IC half-life; turnover of signal portfolios | NW t-stats | E02 report |
| 7 | Redundancy analysis | Rank-correlation and return-correlation clustering; effective number of signals | Bootstrap stability | E03 report |
| 8 | Train/validation/test | Expanding train from 1972, 5y validation, embargo = h, annual refit, 1995-2020 test, 2021-2025 lockbox | Split calendar file checked into repo | `splits.yaml` |
| 9 | ML alpha combination | 16 factorial cells + benchmarks | Identical tuning budgets; all trials logged | Model registry |
| 10 | Expected return / ranking | P-cells → standardized scores → IC-scaled alpha; E-cells → weight proposals | Common scaling rule | `alpha_t`, `w_prop_t` |
| 11 | Portfolio construction | TC-aware MVO with constraints; E-cell projection | Solver status logs | `weights_t` |
| 12 | Risk controls | Dollar/beta/industry neutrality; position, trade and participation limits | Constraint-violation checks | Risk report |
| 13 | Transaction costs | Spread + power-law impact + commission + borrow | Cost multipliers; AUM grid | Cost ledger |
| 14 | Execution assumptions | Trade at close of first trading day of t+1; returns from execution price | One-day lag enforced in code | Execution log |
| 15 | Backtesting | Monthly P&L gross/net; drifted weights | Reconciliation: Σ contributions = portfolio return | `returns_cells.parquet` |
| 16 | Statistical tests | NW, LW2008, CW, DM, SPA, StepM, MCS, DSR, PBO | Trial log feeds DSR/PBO | Inference tables |
| 17 | Robustness | Subperiods, universes, costs, AUM, horizons, risk models, placebo, gating, seeds, international | Pre-declared multiverse | Robustness appendix |
| 18 | Economic interpretation | Economic feature importance, SHAP/ALE, implied state-dependent weights, limits-to-arbitrage tilts | Tie each result to hypothesis H1-H6 | Interpretation section |

## 2. Specification Summary (configuration)

```yaml
universe:
  source: CRSP
  share_codes: [10, 11]
  exchanges: [NYSE, AMEX, NASDAQ]
  main_filter: {min_price: 5, exclude_below_nyse_size_pct: 20}
  robustness_universes: [all_stocks, nyse_top500]
frequency: {signals: monthly, rebalancing: monthly, risk_and_costs: daily}
periods:
  initial_train: [1972-01, 1989-12]
  initial_validation: [1990-01, 1994-12]
  walk_forward_test: [1995-01, 2020-12]
  lockbox: [2021-01, 2025-12]
  refit: annual_january
  train_window: expanding   # robustness: rolling_240m
  validation_window: 60m_rolling
  embargo_months: horizon_h
signals:
  library: JKP_characteristics   # cross-check: OpenAP
  themes: 13
  normalisation: cross_sectional_rank_[-0.5,0.5]
  missing: zero_plus_theme_indicators
  publication_gating: robustness_only
states: [MKTVOL, BEAR, ILLIQ, SENT, CREDIT, TERM, INFL, DRATE, FMOM_theme, DISP]
targets: {prediction_horizons: [1, 3, 6, 12], choose_in_validation: true}
factorial:
  form: [linear, nonlinear]
  conditioning: [static, state]
  objective: [prediction, economic]
  uncertainty: [none, ensemble_shrinkage]
models:
  ridge: {lambda_grid: logspace(-4, 4, 17)}
  lightgbm: {num_leaves: [15, 31, 63], learning_rate: [0.01, 0.05], min_data_in_leaf: [500, 2000],
             feature_fraction: [0.5, 0.8], bagging_fraction: 0.8, lambda_l2: [0, 10],
             max_trees: 2000, early_stopping: validation}
  nn3: {layers: [32, 16, 8], activation: relu, batch_norm: true, optimizer: adam, lr: 0.001,
        l1: [1e-5, 1e-4, 1e-3], early_stopping_patience: 5, ensemble_seeds: 10}
  moe: {experts: 3, gate_inputs: states_only}
  economic_policy: {net: nn3, bptt_months: 12, gamma: calibrate_to_10pct_vol, huber_delta: 1e-4}
  uncertainty: {members: 10, kappa_grid: [0, 0.5, 1, 2, 4]}
portfolio:
  objective: mean_variance_minus_tc
  constraints: {dollar_neutral: true, gross_max: 2.0, beta_abs_max: 0.05,
                industry_ff49_abs_max: 0.02, weight_abs_max: 0.01, adv_participation_max: 0.05}
  long_only_variant: {tracking_error_max: 0.04}
  solver: [MOSEK, CLARABEL]
risk_model:
  type: structural
  factors: [market_beta, jkp_13_themes, ff49_industries]
  factor_cov: {ewma_halflife_days: 126, newey_west: true}
  specific: {ewma_halflife_days: 126, bayesian_shrink: size_deciles}
  robustness: [pca_20, ledoit_wolf_top500]
costs:
  spread: {primary: taq_effective_spread, fallback: [edge_ohlc, abdi_ranaldo]}
  impact: {form: "k * sigma_daily * |Q|^1.5 / ADV^0.5", k: 1.0, sensitivity: [0.5, 2.0, 3.0]}
  commission_bps: 1
  borrow: {general_collateral_bps_pa: 25, hard_to_borrow_pa: 0.05, htb_proxy: bottom_decile_inst_ownership}
  aum_usd_2020: [1.0e8, 1.0e9, 1.0e10]
  aum_scaling: total_crsp_market_cap
execution: {lag_days: 1, price: close}
inference:
  nw_lags: 12
  lw2008_blocks: [4, 6, 12]
  spa: {bootstrap: stationary, mean_block: 6, reps: 10000}
  mcs_alpha: 0.10
  pbo_cscv_blocks: 16
  bootstrap_reps: 5000
logging: {tracker: mlflow, log_every_trial: true}
```

## 3. Experiment Register

The experiment register (IDs E00-E64: hypothesis, model, dataset, benchmark, metrics, statistical test, expected outcome, status) is in Workbook 4. Summary by block:

| Block | Experiments | Purpose |
|---|---|---|
| Data integrity | E00 | PIT audit and factor replication |
| Signal library | E01-E03 | Replication, quality/decay, redundancy |
| Baselines | E10-E14 | Naive, linear, portfolio-level, published ML, linear cost-aware |
| Factorial core | E20-E29 | 16 cells + decomposition |
| Portfolio & costs | E30-E34 | Frontier, cost sensitivity, capacity, constraints, heuristics |
| Inference | E40-E43 | SPA/StepM/MCS, DSR/PBO, alphas, multiverse |
| Robustness | E50-E56 | Subperiods, universes, horizons, placebo, gating, international, seeds |
| Interpretation | E60-E64 | Economic importance, state-dependent weights, limits to arbitrage, trading speed, alignment |

## 4. Bias Controls Matrix

| Bias | Where it enters | Control in this design |
|---|---|---|
| Look-ahead | Accounting lags; regime labels; standardisation; hyperparameters | PIT rules; filtered states only; cross-sectional ranks; validation-only tuning; unit tests |
| Survivorship | Universe construction | Universe at t from all live securities; delisting returns |
| Selection bias | Choosing signals, periods, universes after seeing results | Signal library fixed from JKP/OpenAP before modelling; pre-registration; lockbox |
| Data snooping / multiple testing | Many cells and configurations | Full trial logging; SPA, StepM, MCS; DSR; PBO; haircuts |
| Overfitting | Complex models | Early stopping; ensembles; validation windows; PBO |
| Leakage | Overlapping multi-month labels | Purging and embargo equal to horizon |
| Rebalancing assumptions | Same-close trading | One-day execution lag; drifted weights |
| Delisting bias | Missing delisting returns | CRSP dlret with convention for missing values |
| Corporate actions | Price/share adjustments | CRSP adjustment factors; total returns |
| Point-in-time information | Restatements; macro revisions | Lags; Snapshot robustness; ALFRED or market-based states |

## 5. Validation Approaches: Which Are Appropriate

| Approach | Appropriate here? | Reason |
|---|---|---|
| Walk-forward with expanding windows | **Yes (main)** | Mimics real-time research; maximises data for complex models |
| Rolling windows | Yes (robustness) | Addresses non-stationarity [@CHSWZ2025] |
| Nested cross-validation (time-ordered) | Yes, for hyperparameters within the training window | Outer loop = walk-forward; inner loop = validation block |
| Purged k-fold with embargo | Yes, inside training for early-stopping diagnostics | Required with overlapping labels [@LDP2018] |
| Standard shuffled k-fold | **No** | Leaks temporal and cross-sectional dependence |
| Combinatorial purged CV (CSCV) | Yes, for PBO estimation only | [@BBLZ2017] |
| Single lockbox holdout | **Yes (final)** | Only credible defence against iterative snooping |

## 6. Reviewer-Proof Checklist (summary)

See Reviewer_Proof_Checklist.md for the full list with owners and evidence locations.

## 7. Implementation Roadmap (summary)

See Research_Roadmap.md.
