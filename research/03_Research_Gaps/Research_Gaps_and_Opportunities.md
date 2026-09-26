# Research Gap and Opportunity Report

## Executive Summary

A research gap is recorded here only if a systematic comparison of the literature shows that a question is (i) economically important, (ii) not answered by existing papers, and (iii) testable with obtainable data. "Future work" sentences in papers are not treated as gaps. Each gap has a status (Solved / Partially solved / Open / Open but low value) and a pointer to the closest prior art. The closest-prior-art tracker (Closest_Prior_Art_Tracker.md) is a **living document**: it must be re-checked at each project phase and immediately before submission.

The central finding is that the literature has already established three things: ML improves prediction, costs destroy much of ML's gross alpha, and learning under a cost-aware economic objective restores much of it [@GKX2020; @ACM2023; @JKMP2026]. What it has **not** done is identify *which* ingredients of ML signal combination create net-of-cost value, how those ingredients interact, and whether the resulting state dependence is economically interpretable. That decomposition question is where we see a defensible contribution [inference].

## 1. Existing Approaches and Their Weaknesses

| Approach | Representative papers | Strength | Weakness for net investment value |
|---|---|---|---|
| Naive/heuristic combination (equal weight, IC-weight, theme-EW) | @GK2000; @GRIN1989; @RSZ2010 | Robust, low turnover, hard to beat | Ignores interactions, redundancy, costs, states |
| Linear statistical combination (FM, ridge, PLS) | @LEW2015; @LMR2017; @FNW2020 | Transparent, stable | Misses nonlinearity; static; prediction loss |
| Shrunk SDF / mean-variance over signal portfolios | @KNS2020 | Economically grounded | Portfolio-level; turnover at stock level not modelled |
| Nonlinear ML prediction then sort | @GKX2020; @CFMZ2023; @TH2021 | Best statistical accuracy | Gross sorts; microcap/illiquid concentration [@ACM2023] |
| ML prediction then optimiser (predict-then-optimise) | @BLACKROCK2025; Markowitz-ML in @JKMP2026 | Modular, industrial | Loss-objective mismatch; error maximisation; costs only ex post |
| Parametric/economic-objective weight learning | @BSCV2009; @DMNU2020; @SWZ2023; @JKMP2026 | Directly optimises net utility | Mostly static mapping; attribution of gains unclear [inference] |
| End-to-end differentiable optimisation | @BK2023; @CI2023; @ULM2024 | Aligns loss and decision | Small universes; stability; scale |
| Reinforcement learning | @CTWZ2021; @MS2001 | Flexible objectives | Sample inefficiency; overfitting; replication risk |
| Factor timing / conditional factor weights | @HKS2020; @NRRZ2024; @DMU2024 | Captures time-varying efficacy | Factor-level; limited stock-level implementation |
| Regime models | @AB2002; @GT2007; @NML2018; @SYM2025; @CDS2020 | Economic state interpretation | Few regime episodes; low-dimensional; costs rarely central |
| Uncertainty-aware portfolios | @BS2022; @LMNS2025; @GI2003 | Temper noisy alphas | New; interaction with costs untested |

## 2. Gap Taxonomy (status after systematic comparison)

### 2.1 Alpha combination

| Topic | Status | Evidence | Gap statement |
|---|---|---|---|
| Combining heterogeneous signals | Solved (prediction); Partially (net) | @GKX2020; @DMNU2020; @JKMP2026 | Net value of heterogeneity through netting is shown linearly; nonlinear netting benefits unmeasured |
| Dynamic signal weighting | Partially solved | @NRRZ2024; @DMU2024; @HKS2020 | Stock-level, high-dimensional, cost-aware conditional weights untested |
| Nonlinear signal interactions | Solved (prediction) | @GKX2020; @BPZ2025 | Net-of-cost value of interactions vs their turnover cost unmeasured |
| Cross-sectional vs time-series prediction | Largely solved | @GKX2020; @DLRZ2022 | Low marginal value as stand-alone topic |
| Regime-dependent efficacy | Partially solved (descriptive) | @SYY2012; @DM2016; @MPR2026 | Exploiting it implementably at stock level is open |
| Signal decay | Solved (descriptive) | @MP2016; @CV2023; @CW2026 | Decay-aware combination partially addressed via horizons [@BHHH2023; @JKMP2026] |
| Signal redundancy | Solved (linear) | @GHZ2017; @FNW2020; @JKP2023 | Low novelty |
| Correlated alpha signals | Solved (shrinkage) | @KNS2020 | Low novelty |
| Alpha crowding | Open but measurement-limited | (limited peer-reviewed evidence; one withdrawn arXiv paper) | Data constraints on crowding proxies |
| Meta-learning for alpha weighting | Open (early) | @WL2025; @DA2023 | Net value untested; risk of overfitting |
| Uncertainty-aware combination | Partially solved | @LMNS2025; @BS2022 | Cost interaction untested |

### 2.2 Machine learning (value vs complexity)

Summary of the methods table in the Literature Review. Tree ensembles and NN ensembles are justified. Transformers, RL, GNNs and meta-learning are justified only as robustness or extension cells unless they survive cost-aware objectives and snooping corrections [inference].

### 2.3 Portfolio construction

| Topic | Status | Gap relevant to us |
|---|---|---|
| Mean-variance with shrinkage | Solved | Use as default optimiser with NL shrinkage [@LW2017] |
| Risk parity / min variance / max diversification / HRP | Solved (risk baselines) | Not alpha benchmarks |
| Black-Litterman | Solved | Possible uncertainty-blending cell |
| CVaR / robust / DRO | Solved (methods) | Robust budgets driven by ML uncertainty: partially open |
| ML-driven optimisation / end-to-end | Partially solved | Scale + realistic constraints open [@BK2023; @CI2023] |
| Transaction-cost-aware optimisation | Solved (theory and linear/ML) | [@GP2013; @DMNU2020; @JKMP2026] |
| Turnover-constrained | Solved | Benchmark variant |
| Dynamic / regime-dependent trading speed | Theory solved; empirics open | [@CDS2020] prediction untested in ML setting |

## 3. The Real Research Gaps (ranked)

**G1: Attribution of net-of-cost ML value (highest).** Existing papers compare *bundles*. GKX2020 compares model classes under prediction loss. JKMP2026 compares predict-then-optimise with economic-objective learners. DMU2024 shows conditioning in low dimension. SWZ2023 compares linear and nonlinear policies. No paper we found holds the signal library, universe, optimiser, cost model and inference fixed while switching nonlinearity, conditioning, objective and uncertainty on and off in a factorial design. Without that, the field cannot say *why* a given ML pipeline adds net value [inference; re-verify].

**G2: The conditioning × cost interaction.** Theory [@CDS2020; @GP2013] implies conditioning should be valuable when trading speed and aim portfolios adapt to states. Prediction-loss models that condition on states can instead increase turnover. Whether state dependence helps only when costs are internalised is a sharp, testable hypothesis [inference].

**G3: Economic interpretability of learned state dependence.** Do learned weights move the way theory predicts? Examples: momentum down-weighted after market declines in high volatility [@DM2016]; short-leg anomalies stronger after high sentiment [@SYY2012]; faster trading in liquid states [@CDS2020]. This moves the paper from "does it work" to "why it works".

**G4: Uncertainty in a cost-aware combination.** Whether uncertainty shrinkage mainly works by cutting turnover (hypothesis) is untested [@LMNS2025].

**G5: Stock-level implementation of factor-timing information.** Open; lower priority because it is partly nested in G1/G2 through state variables such as factor momentum and valuation spreads.

## 4. Open Questions for Reviewers to Probe (and our planned answers)

| Likely reviewer question | Planned answer |
|---|---|
| "Isn't this JKMP2026 with extra steps?" | JKMP is a benchmark cell; our contribution is the factorial attribution, interaction test and mechanism tests. We replicate JKMP's Portfolio-ML with their public code. |
| "Are gains just microcaps?" | Main universe excludes microcaps (NYSE 20th percentile); microcaps only in robustness [@HXZ2020; @ACM2023]. |
| "How many configurations did you try?" | Every configuration is logged; DSR, PBO, SPA and MCS computed over the full log. |
| "Is your cost model realistic?" | Spread estimators [@AGK2024; @AR2017; @HAS2009] plus square-root impact; 0.5x-3x sensitivity; AUM grid; FIM2018 and PW2020 as bounds. |
| "Are states just data-mined?" | States fixed ex ante from theory; placebo/shuffled-state tests. |
| "Does it work outside the US?" | JKP developed-markets robustness. |

## 5. Pipeline Architectures A-F: Academic and Practical Comparison

| Pipeline | Description | Academic novelty today | Practical value | Main risk | Role in our design |
|---|---|---|---|---|---|
| A | Signals, normalise, ML combination, expected returns, optimiser | Low (GKX2020, AIM) | High (industry standard) | Loss/objective mismatch; turnover | Prediction-loss cells (P) |
| B | Meta-model learns signal weights, dynamic weights, construction | Moderate | High | Few effective time-series observations | Conditional linear cells; Idea I02 |
| C | Regime detection, regime-specific weights, optimiser | Low-moderate | Moderate | Few regime episodes; look-ahead in regime labels | Gated conditional cells with pre-specified states |
| D | Ensemble, uncertainty estimation, risk-aware optimisation | Moderate (emerging) | High | Uncertainty miscalibration | Uncertainty factor (U) |
| E | Signals + regime + volatility + liquidity, ML, joint alpha, TC-aware optimiser | Moderate | High | Conflates conditioning with nonlinearity | Decomposed explicitly in factorial design |
| F | Learned interaction, differentiable optimiser, direct net objective | Moderate (JKMP/SWZ nearby) | Moderate-high | Instability; scale; overfitting | Economic-loss cells (E); differentiable variant is Idea I04 |

**Recommendation [proposed].** Do not pick one pipeline. Nest A, B/C, D, E and F inside one factorial design so that the paper *measures* which architectural ingredient matters. That is the contribution a reviewer cannot get from existing papers.

## 6. Regime Dependence: What to Test

- **Candidate states (pre-specified, observable at t).** Realised market volatility, e.g. 1-month S&P 500 realised volatility or VIX from 1990. Aggregate illiquidity [@AMI2002] or @PS2003 liquidity. Sentiment [@BW2006]. Market drawdown/bear indicator (cumulative 24-month market return below 0, as in @DM2016). Credit spread (BAA-AAA) and term spread. Inflation and rate-change regimes (CPI YoY, 10y yield change). Factor momentum of each theme [@EL2022]. Cross-sectional signal dispersion.
- **Parameterisations.** (i) Signal × state interactions (linear conditional). (ii) Gated mixture-of-experts with 2-4 experts. (iii) State-dependent risk aversion/trading speed in the optimiser.
- **Integrity.** States enter only with information available at t. Regime labels from smoothed HMM probabilities are forbidden (look-ahead); only filtered probabilities or observable thresholds are allowed. Placebo tests use shuffled state series.

## 7. Opportunity Matrix

| Idea | Novelty | Publication potential | Data feasibility | Risk | Overall (weighted) |
|---|---|---|---|---|---|
| I01 Attribution of net ML value | 8 | 8 | 8 | 4 | Highest |
| I02 Signal-efficacy meta-model | 7 | 7 | 8 | 6 | High |
| I03 Uncertainty-aware combination | 6 | 6 | 8 | 5 | Medium-high |
| I04 Differentiable cost-aware layers | 7 | 6 | 8 | 7 | Medium |
| I05 Regime-gated MoE | 6 | 6 | 8 | 7 | Medium |

(Weighted scores computed with formulas in Workbook 3; figure in PDF 3.)
