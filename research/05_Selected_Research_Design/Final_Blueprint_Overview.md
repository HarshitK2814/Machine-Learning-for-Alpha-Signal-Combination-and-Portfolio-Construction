# Final Research Blueprint: Overview

## 1. Executive Summary

**Topic.** Machine learning for alpha signal combination and portfolio construction.

**Bottom line.** The literature has already shown that ML predicts cross-sectional returns better than linear models [@GKX2020]. It has shown that ML portfolios are fragile to economic restrictions and trading costs [@ACM2023; @BHHH2023], and that learning portfolio weights under a cost-aware objective substantially improves net-of-cost outcomes [@JKMP2026; @DMNU2020; @SWZ2023]. Another model will not be a defensible contribution.

**Selected research direction (proposed).** *"Where does machine-learning alpha come from after trading costs?"* A controlled 2×2×2×2 factorial design switches four ingredients on and off: nonlinearity, state-dependent signal weights, a cost-aware economic training objective, and forecast-uncertainty shrinkage. Signal library, universe, optimiser, cost model and inference stay fixed. Net-of-cost value is attributed to each ingredient and their interactions using data-snooping-robust tests. Mechanism tests check whether the learned state dependence matches economic theory [@DM2016; @SYY2012; @CDS2020].

**Why this is the right bet.** The contribution does not depend on beating a benchmark. It survives the closest prior art by nesting those papers as benchmark cells. It uses university-obtainable data. It answers *why*, not only *whether*.

**Primary targets.** JFQA and Management Science (Finance). **Stretch:** RFS. **Alternatives:** RAPS, Review of Finance, Quantitative Finance. **Backups:** JFM, JBF, JEF.

**Timeline.** About 16 months to a submitted working paper, with a 2021-2025 lockbox holdout opened once.

## 2. State of the Literature

Five waves (detail in PDF 1):
1. The factor zoo and multiple testing [@COC2011; @HLZ2016; @HXZ2020; @JKP2023; @CZ2022; @MP2016].
2. Linear aggregation and shrinkage [@LEW2015; @LMR2017; @KNS2020; @FNW2020].
3. The ML prediction wave [@GKX2020; @GKX2021; @KPS2019; @CPZ2024; @BPZ2025; @KMZ2024].
4. The implementability reckoning [@NMV2016; @ACM2023; @BHHH2023; @CV2023; @AHV2023; @CHK2024; @CW2026].
5. Learning under the economic objective [@BSCV2009; @DMNU2020; @SWZ2023; @JKMP2026; @BK2023; @CTWZ2021].

Parallel strands: factor timing and regimes [@HKS2020; @NRRZ2024; @DMU2024; @CDS2020], uncertainty [@BS2022; @LMNS2025], and non-stationarity [@CHSWZ2025; @WL2025].

## 3. What Has Already Been Solved

- ML beats linear models on prediction and gross spreads, via nonlinear interactions.
- Trading costs and turnover are first-order. Horizon choice and banding help.
- Cost-aware learning of weights beats predict-then-optimise net of costs.
- Factor returns are timeable at the factor level. A conditional multifactor portfolio survives costs.
- Tools for backtest integrity exist: DSR, PBO, SPA, MCS, FDR.

## 4. What Remains Unsolved

- Which ingredient of an ML pipeline creates net value, and how the ingredients interact [inference; re-verify before submission].
- Whether state dependence helps only when costs are internalised.
- Whether learned state dependence is economically interpretable.
- How forecast uncertainty interacts with costs.

## 5. Most Important Research Gaps

| Gap | Statement | Closest prior art |
|---|---|---|
| G1 | No controlled attribution of net ML value across nonlinearity, conditioning, objective, uncertainty | JKMP2026; SWZ2023; GKX2020; CHK2024 |
| G2 | Conditioning × cost-internalisation interaction untested at stock level | DMU2024; CDS2020 |
| G3 | Economic interpretation of learned state dependence | DM2016; SYY2012; CPZ2024 |
| G4 | Uncertainty shrinkage and turnover channel under costs | LMNS2025; BS2022 |
| G5 | Stock-level implementation of factor-timing information | NRRZ2024; HKS2020 |

## 6. Fifteen Possible Project Ideas (ranked by weighted score)

{{IDEA_TABLE}}

## 7. Top Five Paper Concepts

| Concept | Title | Core question | Target journals | Difficulty |
|---|---|---|---|---|
| A | Where Does ML Alpha Come From After Trading Costs? | Attribution of net value to four ingredients | RFS (stretch); JFQA, MS | High |
| B | Forecasting Signal Efficacy | Can signal-level meta-features time signals at stock level after netting? | RAPS, JFQA; JBF, JEF | Medium-high |
| C | Uncertainty-Aware Alpha Combination | Does forecast uncertainty improve net portfolios via turnover? | QF, JFEc | Medium |
| D | Differentiable Cost-Aware Portfolio Layers at Scale | Does end-to-end training scale and help net? | MS, OR, EJOR | High |
| E | Regime-Gated Mixture-of-Experts | Do interpretable state gates add net value? | QF, JBF, JEF | Medium |

## 8. Best Final Research Idea

**Concept A.** It scored highest on novelty, academic contribution, rigor, reproducibility, mechanism and journal fit (mean 8.2/10 vs 7.5 for the runner-up). It nests Concepts B, C and E. Its closest competitors become benchmark cells, and its value holds whatever the empirical outcome.

**Contribution statement (draft, not overclaiming).**

> Existing literature shows ML improves return prediction and that cost-aware learning improves the implementable frontier. However, it compares bundled pipelines on differing data, costs and criteria. We propose a factorial attribution that isolates nonlinearity, state dependence, the economic objective and uncertainty within one controlled environment. This lets us test whether state dependence helps only when costs are internalised, and whether uncertainty works through turnover. We will report evidence across US equities 1995-2025 (with a 2021-2025 lockbox), three AUM levels, cost perturbations and developed international markets. Implications will be stated only after the lockbox is opened.

## 9. Exact Methodology (summary; full specification in Part II)

- **Universe.** CRSP common stocks (share codes 10/11) on NYSE/AMEX/NASDAQ; main filter excludes price < $5 and stocks below the NYSE 20th size percentile.
- **Frequency.** Monthly signals and rebalancing; daily data for risk and costs.
- **Periods.** Training from 1972 (expanding); 5-year rolling validation; walk-forward test 1995-2020; lockbox 2021-2025; annual refit; embargo equal to the horizon.
- **Signals.** About 150 JKP characteristics in 13 themes, rank-normalised, with missing indicators and publication flags.
- **Cells.** {Linear, Nonlinear} × {Static, State-conditional} × {Prediction loss, Economic net-of-cost loss} × {No uncertainty, Ensemble shrinkage}.
- **Models.** Ridge; LightGBM + NN3 ensembles; gated mixture-of-experts; linear and NN parametric policies with costs.
- **Portfolio.** Mean-variance minus costs; dollar/beta/industry neutral; position, trade and ADV limits; structural factor risk model.
- **Costs.** Half effective spread + k·σ·|Q|^1.5/ADV^0.5 + 1 bp; borrow fees; AUM $0.1bn/$1bn/$10bn; k ∈ {0.5, 1, 2, 3}.

## 10. Data Requirements

CRSP (monthly/daily, delistings), Compustat + CCM, JKP characteristics (WRDS) with OpenAP cross-checks, TAQ effective spreads (1993+) and EDGE/Abdi-Ranaldo estimators, Ken French/q/JKP factors, and FRED, Goyal, VIX, Baker-Wurgler and Pastor-Stambaugh state variables. Optional: IBES, 13F, short interest, Markit borrow fees, JKP international. Bias register in Part II and PDF 4.

## 11. Experimental Design

Forty experiments across eight blocks (E00-E64). Data integrity → signal library → baselines → 16-cell factorial core with decomposition → portfolio and costs → inference → robustness → interpretation. Every configuration is logged. A specification freeze precedes a single lockbox evaluation.

## 12. Benchmark Framework

Naive composites (EW, theme-EW, IC/ICIR-weighted, inverse-vol); linear (Lewellen FM, ridge, ENet, PLS); portfolio-level (KNS SDF; NRRZ-style timing); nonlinear ML (RF, LightGBM, GKX NN3, IPCA); economic objective (DMNU linear PPP, JKMP Portfolio-ML from authors' code, deep PPP); cost mitigation (NMV banding); 1/N and market; factor-model alphas (FF5+UMD, q5, JKP themes). All benchmarks get equal tuning budgets and the same costs.

## 13. Statistical Framework

Newey-West t-stats; Ledoit-Wolf Sharpe-difference bootstrap; Clark-West and Diebold-Mariano; Hansen SPA, White Reality Check, Romano-Wolf StepM, Model Confidence Set; Deflated Sharpe and PBO over the full trial log; Harvey-Liu haircuts; factorial contrasts and Shapley attribution with block-bootstrap CIs; Bai-Perron stability; BH-FDR; non-standard errors across a pre-declared multiverse.

## 14. Robustness Framework

Subperiods; universes (all, ex-micro, top-500); horizons and rebalancing; cost multipliers and spread estimators; AUM grid; risk models; rolling vs expanding windows; publication-gated signals; placebo states; NN seeds and grid perturbations; long-only; international developed markets; alternative uncertainty estimators.

## 15. Journal Strategy

Write for finance reviewers. Present at AFA, WFA, EFA, SFS Cavalcade, NBER, SoFiE and ICAIF before submission. Submit to RFS only if the attribution yields a general lesson backed by mechanisms; otherwise JFQA or MS first; then RAPS or Review of Finance, then QF, JFM, JBF or JEF. Practitioner spin-off in FAJ or JFDS after SSRN posting. Detail in PDF 2.

## 16. Target Journal List

| Role | Journals |
|---|---|
| Stretch | Review of Financial Studies; Journal of Finance |
| Primary targets | Journal of Financial and Quantitative Analysis; Management Science (Finance) |
| Strong alternatives | Review of Asset Pricing Studies; Review of Finance; Quantitative Finance |
| Backups | Journal of Financial Markets; Journal of Banking & Finance; Journal of Empirical Finance |
| Spin-offs | FAJ / JFDS (practitioner); MS/OR/EJOR (optimiser methods); JFEc (inference) |

## 17-18. Reviewer-Proof Checklist and Implementation Roadmap

See Parts IV and V of this blueprint.

## 19. Citations

All in-text citations resolve to the reference list at the end of this document. The full bibliography (BibTeX and formatted), with Crossref verification status for every DOI, is in 08_References.

## 20-21. Generated Reports and Workbooks

{{FILE_INDEX}}
