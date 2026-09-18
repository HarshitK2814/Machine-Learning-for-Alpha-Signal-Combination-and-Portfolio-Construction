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
| A - data, costs, backtest | Absar | **Not started.** A synthetic stand-in generator lives in `src/alphacomb/synthetic/` so the other workstreams are unblocked (see `docs/HARSHIT_NEEDS_FROM_ABSAR.md`). |
| B - models, portfolio, risk, interpretation | Harshit | In progress (this repo's current work). |
| C - baselines, statistics, reporting | Maham | Not started. Contracts and example outputs are ready (see `docs/HARSHIT_PROVIDES.md`). |

## Quick start

```bash
python -m pip install -e .
python -m alphacomb.synthetic.generate --out data/synthetic      # C1-C6 fixtures
python pipelines/02_train_models.py --cells all --data synthetic  # C9/C10 predictions
python pipelines/04_construct_portfolios.py --strategies all      # C11 weights
python tools/dev_backtest.py --strategies all                     # TEMPORARY stand-in for C12
pytest -q
```

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
