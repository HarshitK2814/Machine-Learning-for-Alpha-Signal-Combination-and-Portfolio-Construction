# Research Ideas and Paper Concepts

## 1. Fifteen Candidate Research Directions

Scores (0-10) are the research team's judgement, not empirical results. Overall score = 0.20·Novelty + 0.15·Academic importance + 0.10·Practical importance + 0.20·Publication potential + 0.15·Data feasibility + 0.10·(10 − Implementation difficulty) + 0.10·(10 − Failure risk). Workbook 3 holds all fields (research question, hypothesis, existing literature, what is solved or unsolved, exact novelty, data, signals, ML, portfolio method, benchmark, experiments, metrics, difficulties, target journals), and its weights sheet recomputes scores and ranks with live formulas.

{{IDEA_TABLE}}

## 2. Five Full Paper Concepts

### Concept A (from I01): "Where Does Machine-Learning Alpha Come From After Trading Costs?"

- **Research question.** Which ingredients of ML signal combination create net-of-cost investment value: nonlinearity, state-dependent weights, cost-aware economic training, forecast-uncertainty shrinkage? How do they interact?
- **Main hypothesis.** (H1) Nonlinearity raises gross IC and Sharpe, but at least half of the gain disappears net of costs. (H2) State dependence adds net value only when trading costs are internalised in training. (H3) The cost-aware objective is the largest single source of net value. (H4) Uncertainty shrinkage raises net Sharpe mainly by cutting turnover. (H5) Learned state dependence matches economic theory: momentum crashes, sentiment-driven short legs, liquidity-regime trading speed.
- **Novel contribution (proposed).** A controlled 2×2×2×2 factorial attribution on one public signal library, universe, optimiser and cost model, with data-snooping-robust inference and mechanism tests.
- **Literature positioning.** Builds on GKX2020 (nonlinearity), JKMP2026/DMNU2020/SWZ2023 (economic objective), DMU2024/NRRZ2024 (conditioning), LMNS2025 (uncertainty), ACM2023/BHHH2023/CV2023 (implementability), CHK2024/MENK2024 (non-standard errors).
- **Methodology.** Walk-forward annual refits, 1995-2020 development test, 2021-2025 lockbox; 16 cells; common TC-aware optimiser; factorial and Shapley attribution with block bootstrap.
- **Dataset.** CRSP, Compustat, JKP characteristics (WRDS), OpenAP signals, FF/q factors, FRED and Goyal state variables, spread estimates.
- **Signal library.** About 150 characteristics in 13 JKP themes, with publication-date flags.
- **ML architecture.** Ridge; LightGBM; NN3 deep ensemble; gated mixture-of-experts (state-only gate); economic-loss NN policy.
- **Portfolio optimizer.** Mean-variance with spread + power-law impact costs, dollar/beta/industry neutrality, ADV-based trade limits, factor risk model.
- **Benchmarks.** 1/N, market, EW/theme-EW/IC/ICIR/inverse-vol composites, Lewellen FM, ridge/ENet/PLS, RF/LightGBM/NN, KNS SDF, IPCA, DMNU PPP, JKMP Portfolio-ML, NMV banding, NRRZ-style timing.
- **Experimental design / statistical testing / robustness.** See 05 and 07.
- **Expected results (hypotheses only).** Cost-aware objective > nonlinearity in net terms; positive state × objective interaction; uncertainty reduces turnover.
- **Potential weaknesses.** Overlap perception with JKMP2026/SWZ2023; cost-model dependence; compute; null results on conditioning.
- **Why a reviewer should care.** It tells the field *what to build* and *what not to bother with* in ML portfolio construction, with inference that survives the factor zoo's multiple-testing problem.
- **Suitable journals.** RFS (stretch); JFQA, MS (primary); RAPS, RF, QF (alternatives).
- **Publication difficulty.** High (4/5).
- **What makes it publishable rather than a student project.** Pre-registered hypotheses; lockbox holdout; strongest published benchmarks run from their own code; full trial logs; cost sensitivity and capacity; mechanism tests; replication package.

### Concept B (from I02): "Forecasting Signal Efficacy"

- **RQ.** Can signal-level meta-features predict each signal's next-period net contribution, and does implementing those forecasts at stock level (with netting) beat static combination?
- **Hypothesis.** Efficacy is predictable (factor momentum, valuation spread, volatility), but net benefit concentrates in low-turnover themes.
- **Novelty.** Two-level model from signal-month panel forecasts to a stock-level cost-aware portfolio; timing information evaluated after netting.
- **Positioning.** NRRZ2024, HKS2020, KNNV2024, EL2022 (timing); MP2016, CV2023 (decay); DMNU2020 (netting).
- **Methodology / data / signals.** Signal-month panel (about 150 signals × 360 months); GBDT/ridge meta-model with hierarchical shrinkage; same stock universe, optimiser and costs as Concept A.
- **Benchmarks.** Static composites; NRRZ PLS timing at factor level; factor momentum.
- **Tests.** Clark-West for efficacy forecasts; LW2008 and SPA for portfolios; placebo meta-features.
- **Weaknesses.** Few independent time-series observations; overlap with the factor-timing literature.
- **Journals.** RAPS, JFQA (target); JBF, JEF, IJF (backup). **Difficulty:** 3.5/5.

### Concept C (from I03): "Uncertainty-Aware Alpha Combination"

- **RQ.** Does stock-level forecast uncertainty improve cost-aware portfolios, and through which channel: turnover, concentration or tail risk?
- **Hypothesis.** Uncertainty shrinkage cuts turnover more than gross alpha.
- **Novelty.** Uncertainty estimators (deep ensembles, bootstrap SEs, conformal) × optimiser types (shrinkage, robust ellipsoid, Black-Litterman) under costs.
- **Positioning.** LMNS2025 (closest), BS2022, GI2003, LPB2017, KZ2007.
- **Risks.** LMNS2025 could absorb much of the novelty; must emphasise the cost interaction and calibration.
- **Journals.** QF, JFEc (target); JEF, EJOR (backup). **Difficulty:** 3/5.

### Concept D (from I04): "Differentiable Cost-Aware Portfolio Layers at Scale"

- **RQ.** Can end-to-end training through a constrained, cost-aware QP scale to 1,000+ stocks and beat two-stage pipelines net of costs?
- **Novelty.** Implicit differentiation with factor-structured covariance and power-law costs at stock-universe scale.
- **Positioning.** BK2023, CI2023, ULM2024, EG2022, AAB2019; JKMP2026 as economic benchmark.
- **Risks.** Compute, gradient instability, marginal gains over JKMP-style learners.
- **Journals.** MS, OR, INFORMS JOC (target); QF, EJOR (backup). **Difficulty:** 4/5.

### Concept E (from I05): "Regime-Gated Mixture-of-Experts Combination"

- **RQ.** Do experts gated by observable market states beat global models net of costs, and are the gates economically interpretable?
- **Novelty.** Gates restricted to economically motivated state variables, with gate-level interpretation and placebo gates.
- **Positioning.** CPZ2024, DM2016, SYY2012, CDS2020, SYM2025, JJNH1991.
- **Risks.** Few regime episodes; this concept is largely nested in Concept A's conditional cells.
- **Journals.** QF, JBF, JEF. **Difficulty:** 3/5.

## 3. Selection of the Best Paper Idea

| Criterion | A | B | C | D | E |
|---|---|---|---|---|---|
| Novelty | 8 | 7 | 6 | 7 | 6 |
| Academic contribution | 9 | 7 | 6 | 6 | 5 |
| Practical significance | 9 | 9 | 8 | 7 | 8 |
| Data feasibility | 8 | 8 | 8 | 8 | 8 |
| Implementation feasibility | 6 | 7 | 7 | 4 | 6 |
| Statistical rigor achievable | 9 | 7 | 8 | 7 | 6 |
| Reproducibility | 9 | 9 | 9 | 7 | 8 |
| Potential performance (not required to "win") | 7 | 7 | 6 | 6 | 6 |
| Causal/mechanistic insight | 8 | 6 | 6 | 4 | 6 |
| Journal fit (finance) | 9 | 8 | 7 | 6 | 6 |
| **Mean** | **8.2** | **7.5** | **7.1** | **6.2** | **6.5** |

**Why Concept A is superior.**
1. **Its contribution does not depend on "winning" a backtest.** Whatever the result (nonlinearity helps or not, conditioning helps or not), the attribution is informative and publishable if the design is rigorous. That lowers the failure risk that sinks most ML-finance projects.
2. **It is protected against the closest prior art.** JKMP2026, SWZ2023 and DMNU2020 become benchmark cells rather than competitors.
3. **It nests Concepts B, C and E** as factors or extensions, so the pipeline built for A supports follow-up papers.
4. **Data are obtainable** through WRDS plus open datasets.
5. **It answers "why",** via mechanism tests tied to published theory (DM2016, SYY2012, CDS2020, ACM2023).
