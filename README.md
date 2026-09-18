# alphacomb

Research code for the paper **"Where Does Machine-Learning Alpha Come From After Trading Costs?
Nonlinearity, State Dependence and Cost-Aware Learning in Signal Combination."**

The design, hypotheses and experiment register live in the research package
(`../ML_Alpha_Signal_Combination_Research/`), PDF 4 and Workbook 4. The team split is in PDF 6 /
`Team_Coding_Work_Distribution.docx`: three equal workstreams (Absar = data/costs/backtest,
Harshit = models/portfolio/risk/interpretation, Maham = baselines/statistics/reporting).

## Status

| Workstream | Owner | State |
|---|---|---|
| A - data, costs, backtest | Absar | **Not started.** A synthetic stand-in generator lives in `src/alphacomb/synthetic/` so the other workstreams are unblocked. What is needed, by when, and in what format: `docs/HARSHIT_NEEDS_FROM_ABSAR.md`. |
| B - models, portfolio, risk, interpretation | Harshit | **Code complete on synthetic data**: 16 factorial cells (E20-E28), cost-aware optimiser (E33), risk model (C7/E64), published benchmarks (E13), seed stability (E56), interpretation (E60-E62). 53 tests pass. Status and next actions: `docs/STATUS.md`. |
| C - baselines, statistics, reporting | Maham | Not started. Contracts, example outputs and a worked "how to plug a baseline in" snippet are ready: `docs/HARSHIT_PROVIDES.md`. |

No real-data or paper results exist yet, and none can until workstream A delivers contracts C1-C6.
Everything below runs on the synthetic panel.

## Quick start

```bash
python -m pip install -e .
python pipelines/run_all.py --smoke               # generate data, 2 cells, 2 years, end to end
pytest -q                                         # 53 tests

# or stage by stage
python -m alphacomb.synthetic.generate --out data/synthetic          # C1-C6 fixtures + truth.json
python pipelines/02_train_models.py --cells all --years 1995 2020     # C9/C10
python pipelines/02_train_models.py --cells N-S-P-0 --seeds 0 1 2 3 4 # seed dispersion (E56)
python pipelines/02_train_models.py --cells L-S-P-0 --benchmarks gkx_nn3 gkx_gbrt   # E13
python pipelines/04_construct_portfolios.py --strategies all          # C11 weights
python pipelines/04_construct_portfolios.py --strategies all --cost-multiplier 2.0  # cost sensitivity
python tools/dev_backtest.py --strategies all                         # TEMPORARY stand-in for C12
```

Cell codes are `<form>-<conditioning>-<objective>-<uncertainty>`, for example `N-C-E-U` is nonlinear,
state-conditional, economic loss, with uncertainty shrinkage (the full model).

## Repository layout (CODEOWNERS)

```
src/alphacomb/contracts/   SHARED - schemas, paths, io, splits, interfaces (frozen Week 1)
src/alphacomb/synthetic/   ABSAR  - synthetic data generator (currently written by Harshit as a stand-in)
src/alphacomb/data/        ABSAR  - WRDS pulls, PIT panel, signals, states
src/alphacomb/costs/       ABSAR  - spreads, impact, borrow fees
src/alphacomb/backtest/    ABSAR  - P&L engine
src/alphacomb/models/      HARSHIT- 16 factorial cells, uncertainty, benchmarks
src/alphacomb/portfolio/   HARSHIT- TC-aware optimiser, constraints, projection
src/alphacomb/risk/        HARSHIT- structural factor risk model
src/alphacomb/interpret/   HARSHIT- economic feature importance, SHAP, implied weights
src/alphacomb/baselines/   MAHAM  - naive/linear/SDF baselines
src/alphacomb/stats/       MAHAM  - inference and decomposition
src/alphacomb/reporting/   MAHAM  - tables and figures
tools/                     TEMPORARY dev utilities (deleted once workstream A lands)
```

## Branch and merge rules

- `main` is protected in spirit: every change arrives through a `feat/*` branch and is merged with
  `--no-ff` so the feature history stays visible.
- Branch names: `harshit/<topic>`, `absar/<topic>`, `maham/<topic>` for member work;
  `feat/<topic>` for the shared bootstrap done in Week 1.
- Nobody edits another member's folders. Changes to `src/alphacomb/contracts/` are Contract Change
  Requests and need all three members to agree.
- Outputs are keyed by `run_id`, so parallel runs never overwrite each other. `data/` and `outputs/`
  are git-ignored.

## Evidence and integrity rules baked into the code

- Point-in-time only: models never see data after the split's `train_end` (see `contracts/splits.py`).
- The lockbox window (2021-2025) is refused by `Splits.assert_not_lockbox()` unless the environment
  variable `ALPHACOMB_FREEZE_TAG` is set, which happens only after the specification freeze.
- Every fit logs a row to `outputs/trials.csv` (C13) so the deflated Sharpe ratio and PBO can use an
  honest trial count.
