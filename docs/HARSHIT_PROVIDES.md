# What Harshit hands over (workstream B -> A and C)

Everything below already exists in the repository and runs on synthetic data today, so Absar and
Maham can build against real files rather than descriptions.

## 1. To Maham (workstream C: baselines, statistics, reporting)

| # | Artefact | Path pattern | Columns | Notes |
|---|---|---|---|---|
| C9 | Predictions and scaled alphas | `outputs/predictions/cell_<CODE>/<run_id>.parquet` | `date, permno, score, alpha, unc_sd` | One file per cell run. `alpha` is already Grinold-scaled (IC x sigma x z) using validation-period IC, so cells are comparable. `unc_sd` is the ensemble dispersion and is `NaN` for non-uncertainty cells |
| C10 | Raw weight proposals | `outputs/weight_proposals/cell_<CODE>/<run_id>.parquet` | `date, permno, w_prop` | Economic-objective cells only; dollar-neutral, gross 2 |
| C11 | Implementable weights | `outputs/weights/<strategy>/<run_id>.parquet` | `date, permno, w` | Produced by the shared optimiser. **Maham's baselines should be written as C9 and passed through the same stage 04 script**, so no baseline gets an unfair portfolio |
| C13 | Trial log | `outputs/trials.csv` | `run_id, strategy, cell, params_json, seed, train_end, val_metric, git_sha, timestamp` | Every fitted candidate, including losers and the kappa search. This is the denominator for the deflated Sharpe ratio and PBO |
| - | Per-split diagnostics | `outputs/models/cell_<CODE>/<run_id>/diagnostics.csv` | `cell, split, val_rank_ic, test_rank_ic, kappa, params` | Useful for the prediction-vs-value table and for spotting a cell that failed a year |
| - | Manifests | `outputs/manifest_models.csv`, `outputs/manifest_portfolios.csv` | run metadata | Maps run IDs to cells, cost multipliers and AUM |
| - | Cell contrast coding | `alphacomb.contracts.interfaces.CellSpec.contrasts()` | +/-1 coding and interactions | Feeds the factorial decomposition (E29) directly; already verified orthogonal |
| - | Interpretation outputs | `alphacomb.interpret` functions | economic importance, implied theme weights, state-dependence regressions, limits-to-arbitrage tilts | E60-E62 inputs |

**How to run a baseline through the same machinery**

```python
# write your baseline scores as contract C9, then:
#   python pipelines/04_construct_portfolios.py --strategies baseline_ew
from alphacomb.portfolio import grinold_alpha            # same scaling as the cells
from alphacomb.contracts import paths, write_table
write_table(frame, paths.predictions_path("baseline_ew", run_id), "predictions")
```

**What Maham should not have to do:** re-implement alpha scaling, the optimiser, the risk model or
the trial log. If a statistic needs something extra from a model, ask rather than re-fitting it.

## 2. To Absar (workstream A: data, costs, backtest)

| Artefact | What it is | Why Absar needs it |
|---|---|---|
| C11 weights | `outputs/weights/<strategy>/<run_id>.parquet` | The input to the real backtest engine. Already feasible: dollar-neutral, gross <= 2, position and ADV caps respected |
| C7 risk model | `alphacomb.risk.StructuralRiskModel(bundle).load(date)` | Available if the backtest wants predicted volatility for reporting; also the source of the bias statistic for E64 |
| Reference cost implementation | `alphacomb.portfolio.cost_terms.trade_cost_numpy` | The formula the optimiser assumes; Absar's engine must match it |
| Synthetic generator | `src/alphacomb/synthetic/generate.py` | Written as a stand-in; replace or keep as the fixture generator for CI. Please keep the schemas and the `truth.json` idea |

## 3. Interfaces Harshit owns and will not change without a Contract Change Request

* `fit_predict`-style cells: `fit(train, val, features, target)` and `predict(test, features) -> score, unc_sd`
* `construct(date, alpha, w_prev, risk, cost_inputs, cfg) -> weights` (C11)
* `project(date, w_prop, risk, cost_inputs, cfg) -> weights` (C11 from C10)
* `RiskModel.variance(w)`, `.volatility(w)`, `.factor_exposure(w, factor)` (C7)

## 4. Current state (synthetic data, development only)

* 16 factorial cells implemented; three of them (`L-S-P-0`, `N-S-P-U`, `L-S-E-0`) have end-to-end
  tests that write contract-valid artefacts.
* Optimiser and projection verified against every constraint, with cost-awareness demonstrated
  (higher costs reduce turnover).
* Risk model verified point-in-time: rebuilding it from a truncated panel reproduces it exactly.
* Lockbox guard active: any attempt to use 2021-2025 data raises `LockboxError` until the team sets
  `ALPHACOMB_FREEZE_TAG`.
* **No real-data results exist yet, and none will until workstream A delivers C1-C6.**
