# Reviewer-Proof Checklist

Tick every item before submission, and record where the evidence lives (table, figure, appendix or code path). Items are derived from the published critiques and standards cited in this package [@HLZ2016; @HAR2017; @AHM2019; @ACM2023; @CHK2024; @MENK2024; @JKMP2026] and from journal code/data policies (JF, RFS, MS, verified).

## A. Contribution and positioning

- [ ] The research question is stated in one sentence as an economic question, not a model description.
- [ ] The contribution statement names the closest papers (JKMP2026, SWZ2023, DMNU2020, DMU2024, GKX2020, ACM2023, CHK2024, LMNS2025) and says what is new relative to each.
- [ ] The closest-prior-art tracker has been re-run within 2 weeks of submission (SSRN, NBER, arXiv, conference programmes, forward citations).
- [ ] No "first to" claim appears unless the tracker supports it.
- [ ] The hypotheses were pre-registered (dated document or OSF/AEA registry) before the lockbox was opened.
- [ ] Null or negative results are reported, with power discussion.

## B. Data and point-in-time integrity

- [ ] All data sources, pull dates and versions are documented.
- [ ] Accounting variables are lagged by availability (≥ 4 months annual; RDQ quarterly) and unit tests prove it.
- [ ] Universe formed at t from all live securities (no survivorship).
- [ ] CRSP delisting returns are applied; the convention for missing values is documented.
- [ ] Corporate actions are handled via CRSP adjustment factors and total returns.
- [ ] Microcaps are excluded from the main universe; results including them are in robustness.
- [ ] Macro/state variables use real-time (vintage) data or market-based measures; no smoothed regime probabilities.
- [ ] Rebuilt standard factors correlate > 0.95 with the Ken French library.
- [ ] Signal replication statistics versus Chen-Zimmermann/JKP are reported.
- [ ] Missing-data handling is described, with robustness to imputation methods [@BLLP2025; @FHNW2025].

## C. Validation and leakage

- [ ] Walk-forward splits, refit schedule, embargo and purging are documented in a split calendar.
- [ ] No hyperparameter is tuned on test data; the validation windows strictly precede test years.
- [ ] Lockbox period (2021-2025) opened once, after the specification freeze; the freeze date is recorded.
- [ ] Every configuration tried is logged (count reported in the paper).
- [ ] Label overlap for multi-month horizons is purged.
- [ ] NN results report dispersion across ≥ 10 seeds.

## D. Benchmarks

- [ ] Naive composites (EW, theme-EW, IC-weighted, ICIR-weighted, inverse-vol) are included.
- [ ] Linear baselines (Lewellen FM, ridge, ENet, PLS) are included.
- [ ] Strongest published implementable benchmarks are included (JKMP Portfolio-ML from authors' code; DMNU linear PPP).
- [ ] Benchmarks receive the same tuning budget and cost model as proposed cells.
- [ ] 1/N and market portfolios are reported [@DGU2009].
- [ ] Heuristic cost mitigation (banding) is compared [@NMV2016].

## E. Portfolio construction, costs and capacity

- [ ] Net-of-cost results are primary; gross results are secondary.
- [ ] Cost model components (spread, impact, commission, borrow) and calibration sources are stated.
- [ ] Sensitivity to cost multipliers (0.5×-3×) and alternative spread estimators is shown.
- [ ] AUM grid and break-even AUM (capacity) are reported.
- [ ] Turnover, holding period and cost drag are reported for every strategy.
- [ ] Constraint set (neutralities, position/trade/participation limits) is identical across cells.
- [ ] Execution lag (≥ 1 trading day) is enforced.
- [ ] Short-leg contribution and borrow-cost treatment are disclosed.
- [ ] Long-only variant reported.

## F. Statistical inference

- [ ] HAC (Newey-West) t-stats for means and alphas.
- [ ] Sharpe-ratio differences tested with Ledoit-Wolf (2008) bootstrap.
- [ ] Nested forecast comparisons with Clark-West; others with Diebold-Mariano.
- [ ] SPA and Reality Check versus the strongest benchmark; StepM for which cells win; MCS reported.
- [ ] Deflated Sharpe ratio uses the logged trial count; PBO via CSCV reported.
- [ ] Factorial effects and Shapley attributions have bootstrap confidence intervals.
- [ ] Alphas versus FF5+UMD, q5 and JKP themes (net of costs).
- [ ] Multiple theme/signal claims are FDR-controlled.
- [ ] Non-standard errors across the pre-declared multiverse are reported.

## G. Robustness

- [ ] Subperiods, including pre/post decimalisation and post-2008.
- [ ] Universes: all stocks, ex-micro, top-500.
- [ ] Horizons and rebalancing frequency.
- [ ] Risk-model alternatives.
- [ ] Rolling vs expanding windows.
- [ ] Placebo (shuffled) states.
- [ ] Publication-gated signal library.
- [ ] International (developed ex-US) evidence or a stated reason for exclusion.
- [ ] Hyperparameter perturbations.

## H. Economic interpretation

- [ ] Economic feature importance (net utility loss from dropping themes).
- [ ] SHAP/ALE interpretation for prediction cells, with correlated-feature caveats.
- [ ] Implied state-dependent weights are linked to DM2016, SYY2012 and CDS2020 predictions.
- [ ] Limits-to-arbitrage tilts (IVOL, illiquidity, size, distress) by cell.
- [ ] A clear answer to "why does it work (or fail)?" appears in the introduction.

## I. Reproducibility and presentation

- [ ] Replication package: code, environment file, README, pseudo-data for licensed inputs (JF/RFS/MS policies).
- [ ] Figures readable in grayscale; tables have units and sample periods.
- [ ] The abstract states net-of-cost results and the holdout period.
- [ ] Internet appendix contains all robustness tables referenced.
- [ ] Limitations section covers cost-model uncertainty, US focus, and data licences.
