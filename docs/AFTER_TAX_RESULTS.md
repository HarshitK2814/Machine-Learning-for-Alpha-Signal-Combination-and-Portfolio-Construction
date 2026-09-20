# After-tax results: first full-span run

**Run date:** 20 September 2026 · **Span:** 216 months, 2003-2020 out of sample · **Data:** synthetic
panel · **Construction:** all five strategies solved **216/216 optimal**, zero held, zero inaccurate.

> **These are pipeline rehearsals on synthetic data, not findings about markets.** The synthetic
> generator plants the effects the models then find. What these numbers establish is that the
> machinery works end to end and produces the *kind* of quantity the paper needs - not that any
> particular effect exists in real returns.

> **An earlier version of this run was void.** Two cells had silently degraded into stale
> buy-and-holds (69% and 43% of months) because of an optimiser infeasibility. See
> `docs/SILENT_OPTIMISER_FAILURE.md`. Everything below is from the rebuild.

---

## 1. What the investor keeps

Annualised, HIFO lots, accrual accounting, 2% assumed dividend yield.

| Cell | Gross Sharpe | Net of cost | After tax | Tax as % of gross |
|---|---|---|---|---|
| `N-S-P-0` nonlinear, static | 1.429 | 0.992 | **0.659** | 23.8% |
| `N-C-P-0` nonlinear, conditional | 1.424 | 0.990 | **0.695** | 19.3% |
| `L-S-E-0` linear, economic objective | 1.572 | 0.810 | **0.571** | 14.9% |
| `L-S-E-0_aftertax` same, after-tax objective | 1.564 | 0.725 | **0.505** | 13.9% |
| `L-S-P-0` linear, static | 0.969 | 0.513 | **0.351** | 16.6% |

Under the s475(f) mark-to-market election the same books fall to **0.11-0.40**. Under the offshore
regime (dividend withholding only) they keep **0.43-0.91**. The investor's tax status moves
after-tax Sharpe by more than any model choice in the table.

## 2. The mechanism: turnover does not explain the tax bill

This is the result worth keeping.

| Strategy | Monthly turnover | Long-term share of gains | Tax as % of gross |
|---|---|---|---|
| `L-S-E-0_aftertax` | 0.140 | 0.578 | 13.9% |
| `L-S-E-0` | 0.142 | 0.541 | 14.9% |
| `L-S-P-0` | 0.150 | 0.508 | 16.6% |
| `N-C-P-0` | 0.147 | 0.492 | 19.3% |
| `N-S-P-0` | 0.152 | 0.417 | 23.8% |

Turnover spans **1.09x** across these books. Tax as a share of gross spans **1.71x**. Ranked by
long-term share the ordering is perfectly monotonic: **Spearman -1.000 (n=5)**.

With turnover effectively held constant, holding-period composition orders the tax bill. That is
the channel Israel & Moskowitz (2012) and Krasner & Sosner (2024) identify at the *style* level,
reproduced here at the level of *model design*. Five points is far too few to call it established;
it is a hypothesis now worth testing properly on real data.

**On the ranking reordering.** `N-S-P-0` and `N-C-P-0` do swap rank between net-of-cost and
after-tax. Their pre-tax gap is **0.0017** - they are tied - so the swap is not evidence of
anything. The table above is the claim; the rank flip is not.

## 3. Negative result: the after-tax training objective does not pay

Training the economic policy on net-of-cost-**and-tax** utility (`L-S-E-0_aftertax`) versus the same
policy on net-of-cost utility (`L-S-E-0`):

| | Blind | Tax-aware | Change |
|---|---|---|---|
| Long-term share of gains | 0.541 | **0.578** | +0.037 |
| Tax drag | 43.8 bps | **36.4 bps** | **-7.4 bps** |
| Net-of-cost return | 152 bps | 122 bps | **-30.1 bps** |
| **After-tax Sharpe** | **0.571** | **0.505** | **-0.066** |

**The objective worked and the strategy still lost.** It did exactly what it was designed to do -
deferred gains, raised the long-term share to the highest of any cell, cut the tax bill by 17% -
and gave up four times as much pre-tax return doing it.

Candidate explanations, none tested:
* the differentiable tax term is an average-cost approximation with basis reset at every 12-month
  BPTT boundary, so it understates embedded gains and over-trades against its own estimate;
* `harvest_haircut = 1.0` assumes realised losses are fully usable, which flatters harvesting;
* the tax term may simply be over-weighted relative to alpha at this gamma.

Until one of those is shown to be the cause, the honest statement is that **tax-aware training did
not pay in this implementation**, and the tax-aware *optimiser* arm (which has not yet been run over
the full span) is the more promising route because it does not disturb the fitted model at all.

## 4. Negative result: adaptation adds nothing over fixed 1/N weights

| Strategy | Kind | After-tax Sharpe | Turnover |
|---|---|---|---|
| `L-S-P-0` | member | 0.351 | 0.150 |
| `N-S-P-0` | member | 0.659 | 0.152 |
| `N-C-P-0` | member | 0.695 | 0.147 |
| best in hindsight | infeasible | 0.695 | - |
| **`equal_weight_alpha`** | **benchmark** | **0.854** | 0.109 |
| `adaptive_hedge` | adaptive | **0.851** | 0.111 |

**Adaptive minus the fixed 1/N alpha blend: -0.003.** The online rule is very slightly *worse* than
not adapting at all.

The Hedge weights end at 0.308 / 0.339 / 0.353 with 2.94 effective members out of 3 and 1.8% monthly
weight turnover. The rule barely moves, so of course it matches uniform weighting.

**What the 0.851 actually measures.** Blending three forecasts and optimising once beats any single
forecast (0.851 vs 0.695) and cuts turnover from ~0.15 to ~0.11. That is forecast averaging, a
result from the 1960s, and it has nothing to do with online learning. Our first version of this
table compared the adaptive arm against the mean of the members' *realised returns* (0.673) and so
credited all of that to adaptation. That comparison is now labelled `not_like_for_like` and kept
only so nobody re-derives it.

This is consistent with Remlinger et al. (2023), who report a universe - small-cap stocks - where
their uniform mixture beats their online rule.

## 5. The number to distrust

Wash sales disallow **403-443 bps/yr**, against **32-77 bps** of tax actually paid - a factor of
**8.4x**. It is also suspiciously uniform across cells.

That is an artefact of the conservative choice, not a measurement. Trades settle at month end, so
the s1091 window is evaluated on month-end dates 28-31 days apart, and essentially *every*
repurchase lands inside it. Practitioners step around the rule with correlated proxies. **Treat this
as an upper bound on the s1091 penalty.** Doing better needs either daily trade dates or an explicit
proxy-substitution rule, and is an open item.

## 6. Everything here that is not yet trustworthy

1. **Synthetic data.** Real C1-C6 from workstream A changes every number.
2. **n = 5 cells.** The monotonic relationship in section 2 rests on five points.
3. **One seed, one AUM, one cost multiplier.** No dispersion, no sensitivity.
4. **No statistical testing.** No Deflated Sharpe, no PBO, no Romano-Wolf. Every comparison above is
   a point estimate, and several gaps (0.0017, 0.003) are plainly inside the noise.
5. **Dividend yield is a flat 2% assumption**, not data. `targets.div_next` is specified but not yet
   supplied.
6. **Tax rates are constant** across 2003-2020, which is false in fact.
7. **`held_share` is blank** in `summary_after_tax.csv` because the manifest predates that column.
   Construction quality here comes from the stage-04 log (216/216 optimal, verified) rather than the
   results table. Re-run stage 04 to populate it properly.
8. **The tax-aware optimiser arm has not been run** over the full span, nor the wash-block arm. The
   three-way comparison in `docs/AFTER_TAX_AND_ADAPTATION.md` section 2 is implemented, not measured.

## Reproduce

```bash
python pipelines/02_train_models.py --cells L-S-P-0 N-S-P-0 N-C-P-0 L-S-E-0 --years 2003 2020 --fast
python pipelines/02_train_models.py --cells L-S-E-0 --years 2003 2020 --fast \
    --after-tax-objective taxable_us_top_bracket --suffix _aftertax
python pipelines/04_construct_portfolios.py --strategies cell_L-S-P-0 cell_N-S-P-0 cell_N-C-P-0 \
    cell_L-S-E-0 cell_L-S-E-0_aftertax
python pipelines/06_after_tax_eval.py --strategies <same> --lot-methods hifo
python pipelines/07_adaptive_combine.py --members cell_L-S-P-0 cell_N-S-P-0 cell_N-C-P-0 --share 0.05
```

Figures: `python _build/figures_aftertax.py` in the research package, then
`python _build/validate_figure_palettes.py`.
