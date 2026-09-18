# What Harshit needs from Absar (workstream A -> B)

Workstream B is code-complete against **synthetic** data. Everything below is what has to arrive
from workstream A for the same code to run on real data. Nothing else changes: the models, optimiser
and interpretation read contracts, never Absar's internals.

Status legend: **BLOCKING** = workstream B cannot produce real-data results without it;
**NEEDED LATER** = required before the frozen run, not before development continues.

## 1. Data artefacts (contracts C1-C6)

| # | Artefact | Columns Harshit's code reads | Why it matters to workstream B | Status | Wanted by |
|---|---|---|---|---|---|
| C1 | `data/real/universe.parquet` | `date, permno, in_universe, me, price, exchcd, ff49, nyse_size_pct` | Defines the cross-section each month; `ff49` drives the optimiser's industry constraints; `me` drives specific-risk shrinkage by size decile | **BLOCKING** | Week 9 |
| C2 | `data/real/signals.parquet` | `date, permno, sig_*` in [-0.5, 0.5], `miss_<theme>` | The model features. Must already be cross-sectionally rank-normalised with missing values set to 0 and flagged | **BLOCKING** | Week 9 |
| C3 | `data/real/signal_meta.csv` | `signal, theme, pub_year, source` | Theme composites (13) drive the risk model, the conditional interactions and every interpretation output | **BLOCKING** | Week 9 |
| C4 | `data/real/targets.parquet` | `date, permno, r_1m, r_3m, r_6m, r_12m, ret_next` | `r_*` are training targets; `ret_next` is what the economic cells maximise and what weight drift uses | **BLOCKING** | Week 9 |
| C5 | `data/real/states.parquet` | `date, MKTVOL, BEAR, ILLIQ, SENT, CREDIT, TERM, INFL, DRATE, DISP, FMOM_<theme>` | The conditioning factor of the design. Must be lagged and standardised with an expanding window only | **BLOCKING** | Week 10 |
| C6 | `data/real/cost_inputs.parquet` | `date, permno, spread, sigma_d, adv_usd, borrow_fee` | Enters the optimiser objective, the position/trade caps and the economic cells' training loss | **BLOCKING** | Week 12 |
| - | `data/real/states_placebo.parquet` | same as C5 | Placebo test E53 (shuffled states must destroy the conditioning gain) | NEEDED LATER | Week 14 |
| - | Gated signal list | `signal, pub_year` | Publication-gated robustness E54 | NEEDED LATER | Week 16 |
| - | International panel | C1-C6 for developed ex-US | Robustness E55 | NEEDED LATER | Week 20 |

## 2. Properties the data must have (not just the columns)

1. **No look-ahead.** Accounting items lagged to availability, states observable at t, signals using
   only information up to t. Workstream B's tests assume this; they cannot detect it for you.
2. **Delisting returns applied** in `ret_next`, with the convention documented.
3. **Universe already filtered** (price >= $5, above the NYSE 20th size percentile, >= 12 months of
   history), with `in_universe` as the switch so robustness universes can be produced by changing
   one column rather than the pipeline.
4. **`permno` is `int32`, `date` is a month-end timestamp**, and the pairs are unique. The contract
   test enforces this; a silent duplicate would corrupt every cross-sectional operation.
5. **`spread` is a fraction, not basis points** (0.0025 = 25 bp). The optimiser multiplies it by 0.5
   for the half-spread. Please keep this unit; a units mistake here changes the paper's conclusion.
6. **`adv_usd` in dollars**, because participation caps are computed as `adv_usd * 5% / AUM`.
7. **Coverage from 1972** (or the earliest year you can support) so the expanding training window has
   enough history before the first test year, 1995.

## 3. The cost function must agree exactly

The optimiser embeds this formula as a convex term, and `alphacomb.costs.trade_cost` must return the
same number for the same trade:

```
cost_i(dw) = 0.5 * spread_i * |dw_i| + (commission_bps / 10000) * |dw_i|
           + k * sigma_d_i * sqrt(AUM / adv_usd_i) * |dw_i|^1.5
borrow_i(w) = (borrow_fee_i / 12) * max(-w_i, 0)
```

`alphacomb.portfolio.cost_terms.trade_cost_numpy` is the reference implementation, and
`tests/portfolio/test_optimizer.py::test_cvx_cost_matches_numpy_formula` pins it. Please write a
matching test on your side; if the two ever disagree, the net-of-cost attribution is meaningless.

## 4. The backtest engine (contract C12)

Workstream B currently uses `tools/dev_backtest.py`, a deliberately simple stand-in. Your engine
should replace it and add what the stand-in skips: the one-day implementation lag, delisting-month
handling, and hard-to-borrow escalation. Weights arrive as C11 (`date, permno, w`), already
constraint-feasible. Please keep the C12 column set unchanged so the statistics code does not move.

## 5. Questions that need an answer before Week 12

1. Which spread estimator is primary for each era (TAQ 1993+, EDGE or Abdi-Ranaldo before)?
2. Are Markit borrow fees licensed? If not, workstream B will keep the institutional-ownership
   fee tiers currently used in the synthetic data, and the paper must say so.
3. Confirm the `ff49` industry mapping (the synthetic data uses 12 codes; the optimiser scales to any
   number, but the constraint count changes).
4. Will `r_3m`, `r_6m` and `r_12m` be cumulative excess returns over t+1..t+h? The horizon comparison
   (E52) assumes so.
