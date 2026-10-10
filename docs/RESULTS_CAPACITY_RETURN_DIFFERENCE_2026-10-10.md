# Capacity in return units: B(A), the annualised net-return difference (audit task P0-2)

**Date:** 2026-10-10. **Status:** results of the approved direct-return analysis, now with Tier B (the
pipeline's own accounting) on **all 35 valid rungs**. **Final text for the Phase 2 commit.**
Specification: `CAPACITY_RETURN_DIFFERENCE_SPEC_2026-10-10.md` (with an addendum on the solvency unit).
Code: `tools/exp_capacity_return_difference.py` (stages `snapshot`, `pipeline`, `tables`) and
`mean_difference_test` in `src/alphacomb/validation/inference.py`. Tracked inputs, outputs and a SHA-256
manifest: `results/capacity_return_difference/` (the `outputs/` tree is git-ignored; nothing in it is tracked).

## Definition (as run)

`B(A) = 12 * (mean monthly net return of the capped book - mean monthly net return of the uncapped
book)`, the research composite (below), same months, **percentage points of NAV per year,
arithmetic**. A rung is valid only if **no cell-month of either book** is at or below -100% (each cell is
an independently simulated full-AUM account; spec section 7). A composite-only rule would admit one more
rung in Germany ($300mn) and one in India ($100mn), each with 1 of 8 cells wiped: reported, not computed.
Inference: paired studentised stationary bootstrap (Newey-West, block 6, 4,000 replications, seed 0),
two-sided p, Holm within country over valid rungs; intervals are unadjusted. Sample 2009-01 to 2019-12
(132 months; India 131). No insolvent rung has a B(A). Tier A = wedge-tool series (its own cost code).
Tier B = `after_tax_backtest` at zero tax on **re-dumped** decile weights. The re-dump reproduces the Tier A
returns **bit for bit** (max abs difference 0 over all 35 rungs x 8 cells x 2 books), so the books are the same.

**The composite.** It is an **equal-weighted research summary across eight independently simulated,
full-AUM prediction variants**: each variant is a complete decile book simulated on its own, with its own costs,
cap and NAV path at the full mandate, and the composite is the monthly arithmetic mean of the eight return
series. It is **not a single investable fund** and not a fund holding the average weights (which would net
trades and face convex impact on the netted trade); no such strategy was implemented or evaluated. Earlier
phrases such as "one equal-weighted book" mean this summary.

**Solvency rule.** Every cell must stay solvent (no net return at or below -100%) over the whole horizon, in
both books. No terminal-wealth threshold is part of the primary analysis. Near-ruined but technically solvent
comparators are **retained and flagged** (terminal wealth is shown for every rung); they are not plausible
investable benchmarks, and B against them is an accounting difference only.

**Inference status.** The full valid-rung results (35 rungs, within-country Holm) are the inferential result and
appear in the side-by-side table. Anything computed on a subset chosen after looking is descriptive.

## Headline reading

1. **Large B is a ruined comparator, in both tiers.** At the valid rungs the uncapped composite's compounded
   terminal wealth is below 0.1 at 6 of 11 German, 7 of 10 Indian and 4 of 14 Japanese rungs (Tier B). The big
   numbers (+100 to +330 points per year) are the cost of a plan that destroys itself, not a return anyone could
   earn. "Solvent" is the approved minimal criterion; near-ruined comparators are retained and flagged, and
   **no wealth cutoff is part of the primary analysis**.
2. **Tier B changes the small-mandate picture, not the large one.** The tiers agree in sign and order of
   magnitude at large rungs, but at Germany $100k and $300k Tier A shows B of +0.64 and +2.63 while Tier B shows
   -0.52 and -0.01 (Holm p 0.86 and 1.00). The Tier B column is the one to quote; there, small-mandate B in
   Germany is not distinguishable from zero.
3. **Post hoc and descriptive only; not confirmatory (a cut made after looking, not a gate; the p-values quoted
   in it are not evidence for anything and the Holm family there is not the pre-specified one):** restricting to rungs where the
   uncapped composite keeps at least half its wealth (Tier B): Germany $100k to $1mn gives -0.52, -0.01, +5.09
   (Holm p 0.86, 1.00, 0.041); India $100k and $300k give +2.88, +5.73 (Holm p 0.070, 0.070); Japan $100k to
   $4mn gives -0.01 to +1.46 (Holm p 0.38 down to 0.055). Mostly not significant after Holm.
4. **B is monotone increasing in AUM across valid rungs in both tiers**, as found, not imposed. The capped
   book's own mean net return is not monotone (Tier B: 8 steps down / 2 up in Germany, 7 / 2 India, 9 / 4 Japan).
5. B is an accounting difference against an infeasible plan. It is not realised performance and not a
   Sharpe-point equivalent; no ratio is claimed.

## Largest valid rung (Tier A) versus the Tier B validation rung

The largest valid Tier A rung is Germany $100mn, India $30mn and **Japan $10bn**. The earlier Tier B
cross-check used Japan $1bn, which is not Japan's largest valid rung; both are shown. Units: points per year.

| | rung | B Tier A | B Tier B | A - B | uncapped net/yr A / B | uncapped wealth A / B |
|---|---|---|---|---|---|---|
| Germany | $100mn | +215.98 | +171.72 | +44.26 | -216.92 / -172.75 | 2e-12 / 7.7e-10 |
| India | $30mn | +111.00 | +103.99 | +7.01 | -114.04 / -107.17 | 1.2e-06 / 2.6e-06 |
| Japan | $10bn | +327.16 | +289.32 | +37.83 | -327.28 / -289.45 | 6.8e-20 / 1.1e-17 |
| Japan (earlier cross-check rung) | $1bn | +101.25 | +101.65 | -0.40 | -102.15 / -102.62 | 7e-06 / 6.7e-06 |

## All 35 valid rungs, side by side (every disagreement preserved)

Columns: B and the uncapped book's mean net return per year (points), the uncapped book's compounded terminal
wealth, and the capped book's own mean net return per year, for Tier A and Tier B; "CI" is the unadjusted 95%
interval of Tier B's B; "p Holm" is Tier B's.

### DEU

| AUM | B Tier A | B Tier B | A-B | CI Tier B (unadj.) | t(B) | p Holm (B) | uncapped net/yr A | B | uncapped wealth A | B | capped net/yr A | B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $100k | +0.64 | -0.52 | +1.16 | [-1.85, +0.55] | -0.78 | 0.8620 | +9.00 | +10.40 | 2.48 | 2.9 | +9.63 | +9.88 |
| $300k | +2.63 | -0.01 | +2.63 | [-2.03, +2.11] | -0.01 | 0.9962 | +3.60 | +6.03 | 1.37 | 1.79 | +6.22 | +6.02 |
| $1mn | +9.90 | +5.09 | +4.80 | [+1.22, +9.03] | +2.46 | 0.0413 | -6.96 | -2.53 | 0.427 | 0.698 | +2.94 | +2.57 |
| $2mn | +17.66 | +11.04 | +6.62 | [+5.75, +16.63] | +4.07 | 0.0000 | -16.62 | -10.36 | 0.145 | 0.292 | +1.04 | +0.68 |
| $3mn | +24.05 | +16.05 | +8.00 | [+9.70, +22.98] | +4.95 | 0.0000 | -24.03 | -16.37 | 0.063 | 0.149 | +0.01 | -0.33 |
| $4mn | +29.74 | +20.58 | +9.17 | [+13.33, +28.69] | +5.62 | 0.0000 | -30.29 | -21.44 | 0.031 | 0.0844 | -0.54 | -0.87 |
| $6mn | +39.55 | +28.42 | +11.13 | [+19.98, +38.23] | +6.61 | 0.0000 | -40.77 | -29.94 | 0.00936 | 0.0322 | -1.23 | -1.52 |
| $8mn | +48.04 | +35.26 | +12.78 | [+25.87, +46.18] | +7.43 | 0.0000 | -49.61 | -37.11 | 0.00338 | 0.0142 | -1.57 | -1.85 |
| $10mn | +55.68 | +41.44 | +14.24 | [+31.39, +53.21] | +8.14 | 0.0000 | -57.40 | -43.42 | 0.00136 | 0.00689 | -1.72 | -1.98 |
| $30mn | +109.87 | +85.51 | +24.36 | [+70.38, +102.95] | +11.75 | 0.0000 | -111.41 | -87.21 | 2.08e-06 | 3.95e-05 | -1.54 | -1.70 |
| $100mn | +215.98 | +171.72 | +44.26 | [+146.06, +199.88] | +14.72 | 0.0000 | -216.92 | -172.75 | 1.97e-12 | 7.74e-10 | -0.94 | -1.02 |

Insolvent comparator, **no B computed** (3 rungs): $300mn (uncapped first exhausts NAV 2009-03-31, 1 of 8 cells wiped; capped net -0.63/yr, Sharpe -0.61, t -2.05); $1bn (uncapped first exhausts NAV 2009-01-31, 8 of 8 cells wiped; capped net -0.22/yr, Sharpe -0.67, t -2.29); $10bn (uncapped first exhausts NAV 2009-01-31, 8 of 8 cells wiped; capped net -0.02/yr, Sharpe -0.67, t -2.29)

### IND

| AUM | B Tier A | B Tier B | A-B | CI Tier B (unadj.) | t(B) | p Holm (B) | uncapped net/yr A | B | uncapped wealth A | B | capped net/yr A | B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $100k | +3.16 | +2.88 | +0.28 | [+0.94, +5.33] | +2.67 | 0.0700 | +0.61 | +0.21 | 0.961 | 0.92 | +3.76 | +3.09 |
| $300k | +6.21 | +5.73 | +0.48 | [+2.31, +9.99] | +3.09 | 0.0700 | -4.53 | -4.60 | 0.544 | 0.54 | +1.68 | +1.13 |
| $1mn | +13.46 | +12.48 | +0.98 | [+6.59, +20.04] | +3.77 | 0.0473 | -14.58 | -14.01 | 0.177 | 0.189 | -1.12 | -1.54 |
| $2mn | +21.49 | +19.99 | +1.50 | [+12.14, +30.03] | +4.49 | 0.0340 | -23.78 | -22.63 | 0.0627 | 0.0712 | -2.29 | -2.64 |
| $3mn | +27.92 | +26.00 | +1.92 | [+16.63, +37.91] | +4.90 | 0.0338 | -30.84 | -29.25 | 0.028 | 0.0335 | -2.93 | -3.25 |
| $4mn | +33.43 | +31.15 | +2.28 | [+20.71, +44.44] | +5.23 | 0.0330 | -36.79 | -34.82 | 0.0142 | 0.0176 | -3.36 | -3.67 |
| $6mn | +42.91 | +40.02 | +2.88 | [+27.84, +55.58] | +5.77 | 0.0245 | -46.78 | -44.17 | 0.00445 | 0.00596 | -3.87 | -4.15 |
| $8mn | +51.24 | +47.85 | +3.39 | [+34.29, +65.03] | +6.21 | 0.0200 | -55.20 | -52.06 | 0.00166 | 0.00236 | -3.96 | -4.21 |
| $10mn | +58.73 | +54.89 | +3.84 | [+40.06, +73.52] | +6.54 | 0.0180 | -62.61 | -59.01 | 0.000689 | 0.00103 | -3.88 | -4.12 |
| $30mn | +111.00 | +103.99 | +7.01 | [+80.96, +132.42] | +8.15 | 0.0100 | -114.04 | -107.17 | 1.23e-06 | 2.61e-06 | -3.04 | -3.19 |

Insolvent comparator, **no B computed** (4 rungs): $100mn (uncapped first exhausts NAV 2011-12-31, 1 of 8 cells wiped; capped net -1.55/yr, Sharpe -0.81, t -2.36); $300mn (uncapped first exhausts NAV 2009-01-31, 8 of 8 cells wiped; capped net -0.50/yr, Sharpe -0.63, t -1.85); $1bn (uncapped first exhausts NAV 2009-01-31, 8 of 8 cells wiped; capped net -0.15/yr, Sharpe -0.62, t -1.80); $10bn (uncapped first exhausts NAV 2009-01-31, 8 of 8 cells wiped; capped net -0.01/yr, Sharpe -0.62, t -1.80)

### JPN

| AUM | B Tier A | B Tier B | A-B | CI Tier B (unadj.) | t(B) | p Holm (B) | uncapped net/yr A | B | uncapped wealth A | B | capped net/yr A | B |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| $100k | -0.01 | -0.01 | -0.00 | [-0.03, +0.00] | -1.10 | 0.3797 | +0.92 | -0.16 | 1.07 | 0.947 | +0.91 | -0.17 |
| $300k | +0.07 | +0.08 | -0.00 | [-0.01, +0.18] | +1.54 | 0.3615 | +0.16 | -0.92 | 0.982 | 0.872 | +0.23 | -0.84 |
| $1mn | +0.34 | +0.35 | -0.01 | [+0.11, +0.65] | +2.72 | 0.1800 | -1.33 | -2.40 | 0.833 | 0.741 | -0.99 | -2.05 |
| $2mn | +0.68 | +0.70 | -0.02 | [+0.31, +1.16] | +3.49 | 0.0920 | -2.69 | -3.76 | 0.717 | 0.638 | -2.01 | -3.05 |
| $3mn | +1.09 | +1.13 | -0.03 | [+0.57, +1.77] | +4.07 | 0.0700 | -3.74 | -4.80 | 0.639 | 0.569 | -2.65 | -3.67 |
| $4mn | +1.42 | +1.46 | -0.04 | [+0.79, +2.24] | +4.41 | 0.0555 | -4.62 | -5.67 | 0.58 | 0.516 | -3.20 | -4.21 |
| $6mn | +2.03 | +2.09 | -0.05 | [+1.23, +3.08] | +5.13 | 0.0385 | -6.10 | -7.14 | 0.493 | 0.439 | -4.07 | -5.06 |
| $8mn | +2.74 | +2.81 | -0.07 | [+1.79, +3.96] | +6.09 | 0.0240 | -7.35 | -8.38 | 0.429 | 0.383 | -4.61 | -5.57 |
| $10mn | +3.40 | +3.50 | -0.10 | [+2.36, +4.78] | +6.84 | 0.0112 | -8.45 | -9.48 | 0.38 | 0.339 | -5.05 | -5.98 |
| $30mn | +9.58 | +9.84 | -0.26 | [+7.89, +11.96] | +10.58 | 0.0000 | -16.07 | -17.05 | 0.163 | 0.146 | -6.49 | -7.21 |
| $100mn | +26.26 | +26.74 | -0.48 | [+22.85, +30.70] | +14.64 | 0.0000 | -30.96 | -31.85 | 0.0305 | 0.0276 | -4.70 | -5.12 |
| $300mn | +52.75 | +53.30 | -0.55 | [+45.99, +60.53] | +16.11 | 0.0000 | -55.06 | -55.81 | 0.00192 | 0.00177 | -2.31 | -2.51 |
| $1bn | +101.25 | +101.65 | -0.40 | [+86.90, +116.62] | +15.66 | 0.0000 | -102.15 | -102.62 | 7e-06 | 6.68e-06 | -0.90 | -0.97 |
| $10bn | +327.16 | +289.32 | +37.83 | [+216.88, +360.45] | +9.73 | 0.0025 | -327.28 | -289.45 | 6.77e-20 | 1.1e-17 | -0.13 | -0.13 |

## Tier A versus Tier B: where they disagree and why (existing accounting outputs only)

* **Gross returns are identical** to 1e-16 in every checked rung and book, so weights, returns and universe are
  the same. Every disagreement is in **costs**.
* **Borrow fee (supported in the one cell checked).** The pipeline charges a flat 1.0% per year on short exposure (`MODELLED_FLAT_BORROW_PROXY_V1`);
  the wedge tool has no borrow term. In one checked cell (Japan $100k, capped) the pipeline's spread plus impact
  equals the wedge cost to 0.0003 per year and the pipeline total exceeds it by the 0.0100 borrow. This
  accounts for the level gap in that cell. That it accounts for the small-rung gaps in all rungs and countries has
  not been checked cell by cell; the claim that it largely cancels in B is an expectation, not a verified result.
* **Germany and India, large rungs: the pipeline's uncapped cost is lower.** In one checked cell (Germany
  $100mn, uncapped) the pipeline's spread plus impact is 1.86 per year against the wedge's 2.30 (monthly
  correlation 0.86), and mean turnover is 0.917 in the pipeline against 0.963 from the weights without drift.
  The pipeline rebalances from drifted, NAV-scaled holdings; the wedge tool charges the trade from the previous
  month's target weights. That is consistent with a drift effect, but it is **not proven** to be the cause, let alone the whole of the gap
  (impact is convex, and a 5% turnover difference would not by itself obviously produce a 20% impact difference).
  The cause is unresolved and no adjustment is applied.
* **Size of the gap.** Large where the uncapped book is near-ruined (Germany $100mn: 44 points; Japan $10bn: 38
  points) and under 1 point for Japan up to $1bn. Tier B (the pipeline) is the primary result; Tier A is shown
  alongside and every discrepancy is preserved. **The Tier A / Tier B cost differences are not fully explained.**
  Two candidate mechanisms (borrow fee; drifted holdings) are supported only by the single cells examined; they
  are not shown to account for the gaps in the other 34 rungs.
* **Decomposition.** B = gross forgone + cost saved holds to <= 1.4e-15 in both tiers, by construction (cost is
  `gross - net`, or the pipeline ledger, which is itself subtracted from gross). It is bookkeeping, not
  independent confirmation. Compounding breaks additivity: the compounded annual difference
  (`geometric_ann_diff` in the CSVs) is well below the arithmetic B at ruined rungs.

## Artifacts and what regenerates what

* **From tracked snapshots only:** `python tools/exp_capacity_return_difference.py --stage tables` rebuilds Tier A, Tier B,
  the reconciliation files and `tables.md` from `results/capacity_return_difference/inputs/` and
  `tierB_monthly_*.csv.gz`; the bootstrap is seeded, so the outputs are identical. The manifest records SHA-256
  hashes of every file.
* **From upstream, needs the frozen `data/` and stage-02 predictions (not in git):** the `inputs/monthly_*_cov.csv`
  series (wedge tool, tag `cov`) and `tierB_monthly_*.csv.gz` (wedge tool re-dump with `--dump-weights`, tag `tierb`,
  then `--stage pipeline`). Their provenance is the commands in the manifest, not content in git.
* `outputs/` is git-ignored in full; nothing under it is tracked.

## Limits

* The solvency rule admits near-ruined comparators. They are retained and flagged, not filtered; no materiality
  condition is applied.
* The composite is a research summary, not a fund (resolved above). A single-fund average-weight strategy has not
  been implemented; it would need a separate proposal and explicit approval.
* The drift explanation of the Tier A / Tier B cost gap is partial. Resolving it needs per-component cost series
  for all rungs; the saved Tier B file keeps total cost only.
* Intervals are unadjusted; rungs share the same scores and are strongly dependent.
