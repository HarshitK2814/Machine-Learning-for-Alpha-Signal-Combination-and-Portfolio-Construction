# Falsification audit: first run (19 September 2026)

Purpose: answer the question a 2026 referee now asks before believing any machine-learning result -
**what does this pipeline report when there is nothing to find?** The standard comes from
"Spurious Predictability in Financial Machine Learning" (arXiv 2604.15531), which shows that
adaptive specification search produces significant backtests under a no-predictability null.

## Setup

* **Planted panel**: the standard synthetic generator (600 stocks, 1972-2025) with its documented
  effects: linear value/quality/investment, a value x quality interaction, a momentum coefficient
  that flips sign in bear plus turbulent states, and reversal alpha confined to small illiquid names.
* **Null panel**: the identical generator with **every planted coefficient set to zero**
  (`alphacomb.validation.zero_predictability_panel`), 400 stocks, 1985-2020. Same signal library,
  same missingness, same cost structure, same universe filters.
* Both runs use the same code path, the same hyperparameter grids and the same walk-forward
  calendar (test years 2018-2019, `--fast` grids).

## Result

Mean rank information coefficient across the two test years:

| Panel | Cell | Validation IC | Test IC |
|---|---|---|---|
| Planted effects | L-S-P-0 (linear, static) | 0.0519 | **0.0572** |
| Planted effects | N-S-P-0 (nonlinear, static) | 0.0509 | **0.0562** |
| Zero-predictability null | L-S-P-0 | -0.0094 | **0.0135** |
| Zero-predictability null | N-S-P-0 | 0.0058 | **0.0093** |

The pipeline recovers 4.2x (linear) and 6.0x (nonlinear) more signal on the panel that contains
signal than on the panel that does not. Validation IC on the null is approximately zero, and in one
case negative, which is the behaviour a correct search should show.

## The honest caveat, and the fix before the paper

**The null is not perfectly null.** Test IC on the zero-alpha panel is about 0.01 rather than 0.000.
The reason is in the generator, not the models: setting the alpha coefficients to zero removes
*direct* predictability, but characteristics still drive factor loadings (size feeds the SMB
exposure, value feeds HML), so a cross-sectional predictor can still pick up a small amount of
factor-driven return variation. That is genuine structure, not a bug, but it is not a clean null.

Required before this audit appears in the paper:

1. Add a **strict null** option that also zeroes the characteristic-to-factor-loading channel, so
   returns are factor structure plus noise that is independent of every signal.
2. Report the **microstructure placebo** (already implemented: signals replaced by
   autocorrelation-matched noise) alongside the strict null, since it holds the cost and turnover
   profile fixed while destroying information.
3. Report the audit in **net-of-cost Sharpe** as well as IC, because a small IC on the null can
   still produce an apparently attractive gross backtest.
4. Compute the **inflation gap** (`validation.inflation_gap`) using the real trial count from
   `outputs/trials.csv` rather than the development count.

## Reproduce

```bash
python -c "from alphacomb.validation import zero_predictability_panel; \
           zero_predictability_panel('data/null', n_stocks=400, start='1985-01-31', end='2020-12-31')"
python pipelines/02_train_models.py --cells L-S-P-0 N-S-P-0 --years 2018 2019 --fast --data null
```
