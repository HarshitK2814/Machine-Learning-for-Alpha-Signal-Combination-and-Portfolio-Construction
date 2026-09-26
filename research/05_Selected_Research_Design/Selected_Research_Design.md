# Proposed Research Design: Where Does Machine-Learning Alpha Come From After Trading Costs?

*Working title: "Nonlinearity, State Dependence, and Cost-Aware Learning: Decomposing the Net Value of Machine-Learning Signal Combination".*

Everything in this document is a **proposed** design. Expected outcomes are **hypotheses**, not results.

## 1. Research Question

How much of the net-of-cost investment value of machine-learning signal combination is attributable to (i) **nonlinear** signal interactions, (ii) **state-dependent** signal weights, (iii) a **cost-aware economic training objective**, and (iv) **forecast-uncertainty** shrinkage? Do these ingredients interact? Is the learned state dependence consistent with economic theory?

## 2. Hypotheses (pre-registered)

| ID | Hypothesis | Primary test | Grounding |
|---|---|---|---|
| H1 | Nonlinearity raises gross IC and gross Sharpe relative to linear combination, but at least 50% of the gross Sharpe gain disappears net of costs | Clark-West (IC/R²), LW2008 Sharpe difference gross vs net, factorial contrast | @GKX2020; @ACM2023; @BHHH2023 |
| H2 | State-dependent weights add net value only when costs are internalised in training (positive State × Objective interaction) | Factorial interaction contrast, block bootstrap; SPA | @CDS2020; @GP2013; @DMU2024 |
| H3 | The cost-aware objective is the largest main effect on net utility | Factorial main effects; Shapley attribution | @JKMP2026; @DMNU2020 |
| H4 | Uncertainty shrinkage raises net Sharpe, mainly by reducing turnover | Mediation: turnover change vs gross alpha change | @LMNS2025; @BS2022 |
| H5 | Learned state dependence matches theory: lower momentum weight after market declines with high volatility; stronger short-leg anomaly weights after high sentiment; faster trading in liquid states | Regressions of implied weights / turnover on states | @DM2016; @SYY2012; @CDS2020 |
| H6 | Gross ML gains load on limits-to-arbitrage stocks; cost-aware learning shifts exposure toward liquid stocks | Characteristic tilts of portfolios | @ACM2023 |

**Null results are informative.** If H2 fails, the paper reports that conditioning adds no net value even with costs internalised. That is an important negative finding for practitioners (e.g., for the regime resampling in @BLACKROCK2025).

## 3. Architecture

```text
Point-in-time data (CRSP, Compustat, JKP/OpenAP signals, state variables, cost inputs)
  -> Signal construction (~150 signals, 13 themes) + publication-date flags
  -> Cross-sectional rank normalisation, missing-value indicators
  -> Signal quality & redundancy diagnostics (IC, decay, turnover, clusters)
  -> Walk-forward splits (expanding train, 5y validation, embargo = horizon, annual refit; 2021-2025 lockbox)
  -> 16-cell factorial combination models
       Form:        Linear (L)  | Nonlinear (N)
       Conditioning: Static (S)  | State-conditional (C)
       Objective:   Prediction loss (P) | Economic net-of-cost loss (E)
       Uncertainty: None (0)    | Ensemble-uncertainty shrinkage (U)
  -> P-cells: standardized scores -> common alpha scaling -> common TC-aware optimiser
     E-cells: weights learned under net utility, then projected onto the same constraint set
  -> Risk controls (neutralities, position/trade limits, factor risk model)
  -> Execution & costs (spread + power-law impact; AUM grid; borrow costs)
  -> Backtest -> statistics (SPA/StepM/MCS, LW2008, DSR, PBO, NW alphas)
  -> Factorial & Shapley attribution -> mechanism tests -> robustness & multiverse
```

**Design principle (proposed).** All cells share the signal library, universe, splits, constraint set, risk model, cost model, AUM and evaluation code. The only differences between cells are the four switched ingredients, so differences in net performance can be attributed to them.

## 4. Data

| Component | Source | Access | Notes |
|---|---|---|---|
| Returns, prices, volume, shares, delistings | CRSP US Stock (monthly & daily) via WRDS | University subscription | Share codes 10/11; exchanges NYSE/AMEX/NASDAQ; delisting returns applied |
| Fundamentals | Compustat North America (annual & quarterly) via WRDS | Subscription | Lagged availability (see Section 9); CCM link table |
| Characteristics | JKP global characteristics (WRDS; code public) and/or Open Source AP firm-level signals (209 downloadable + 3 from CRSP) | WRDS / free download | JKP factor returns under CC BY-NC 4.0 (jkpfactors.com); OpenAP data through Dec 2024 |
| Factor benchmarks | Ken French data library; q-factors (global-q.org); JKP theme factors | Free | FF5+UMD, q5, JKP themes |
| State variables | FRED (credit/term spreads, CPI, yields), Goyal predictor data, CBOE VIX (from 1990), Baker-Wurgler sentiment, Pastor-Stambaugh liquidity | Free (verify latest update dates) | All lagged one month |
| Trading-cost inputs | Chen-Velikov effective spreads (hf-spreads-all code, TAQ-based); EDGE OHLC estimator [@AGK2024]; Abdi-Ranaldo [@AR2017]; Hasbrouck Gibbs [@HAS2009] | TAQ via WRDS; estimators from CRSP OHLC | Hierarchy: TAQ effective spread (1993+), else EDGE, else AR |
| Borrow costs (optional) | Markit/IHS securities finance via WRDS if licensed (JKMP code references short-selling fees from WRDS) | Institution-dependent | Fallback: institutional-ownership proxy with fee tiers |

## 5. ML Methodology

**Inputs.** For stock i at month-end t: signal vector x_{i,t} (about 150 cross-sectionally rank-normalised to [-0.5, 0.5]; missing set to 0 with 13 theme-level missing indicators); cost features c_{i,t} (log effective spread, log dollar volume, Amihud illiquidity, 60-day volatility); state vector z_t (pre-specified, Section 6).

**Targets.** Prediction cells: cross-sectionally demeaned excess return over horizon h ∈ {1, 3, 6, 12} months (h chosen in validation and counted as a trial), rank-transformed in robustness. Economic cells: realised next-month net portfolio utility.

**Model classes per cell.**
- **L-S-P.** Ridge on x (λ grid 10^-4 to 10^4, 17 points). Elastic net and PLS reported as baselines.
- **L-C-P.** Ridge on [x, x⊗z] with separate penalties for main and interaction blocks.
- **N-S-P.** LightGBM (num_leaves {15, 31, 63}; learning_rate {0.01, 0.05}; min_data_in_leaf {500, 2000}; feature_fraction {0.5, 0.8}; bagging 0.8; L2 {0, 10}; early stopping on validation, up to 2,000 trees) and an NN3 ensemble (32-16-8 ReLU, batch norm, Adam lr 1e-3, L1 {1e-5, 1e-4, 1e-3}, early stopping patience 5, 10 seeds). The pre-specified nonlinear prediction is the equal-weight average of the LightGBM and NN ensembles; each is also reported separately.
- **N-C-P.** As N-S-P with z and x⊗z appended for NN and z appended for LightGBM. Gated mixture-of-experts variant: 3 NN experts, softmax gate on z only (interpretable gate).
- **L-S-E.** Linear parametric portfolio policy with costs [@DMNU2020].
- **L-C-E.** Linear policy with coefficients linear in z (conditional PPP).
- **N-S-E.** NN policy (NN3) mapping (x, c) to weight tilts, trained on net utility [@SWZ2023; @JKMP2026 Portfolio-ML as external benchmark].
- **N-C-E.** NN policy on (x, c, z) with state gate.
- **Uncertainty (U).** For P-cells, the alpha score is shrunk as α_shrunk = α / (1 + κ·s²/s_avg²), where s is the stock's ensemble standard deviation across 10 members, s_avg is its cross-sectional average (seeds for NN, bagged subsamples for LightGBM or ridge) and κ ∈ {0, 0.5, 1, 2, 4} is chosen in validation. For E-cells, a penalty proportional to the ensemble variance of proposed weights is added. A bootstrap-SE variant [@LMNS2025] is used in robustness.

**Economic loss (E-cells).** Over training months, maximise the mean of

U_t = w_t'r_{t+1} − (γ/2)·w_t'Σ_t w_t − TC_t(w_t − w⁺_{t−1}) − η·‖w_t‖₁

where w⁺_{t−1} are drifted previous weights. TC is the cost model of Section 7 with a smooth (Huber) approximation of |·| for training. γ is calibrated so the ex-ante volatility of the validation-period portfolio is 10% annualised. Weights are normalised to gross exposure 2 (long 1, short 1) and projected onto the Section 7 constraint set before evaluation. Training uses truncated back-propagation through 12-month sequences so the turnover term is learned.

**Alpha scaling for P-cells (common across models).** score → z-score cross-sectionally → α_{i,t} = IC_v · σ_{i,t} · score_{i,t} (Grinold-Kahn convention), where IC_v is the model's validation-period IC. This prevents a model from "winning" by producing larger forecast magnitudes.

## 6. State Variables (fixed ex ante; all observable at t)

| Variable | Definition | Economic rationale |
|---|---|---|
| MKTVOL | log 21-day realised volatility of CRSP VW index | Momentum crashes; risk prices fall with volatility [@DM2016; @DMU2024] |
| BEAR | 1 if CRSP VW cumulative 24-month return < 0 | Momentum crash state [@DM2016] |
| ILLIQ | VW average Amihud illiquidity, detrended (log deviation from 12-month average) | Liquidity regimes [@CDS2020; @AMI2002] |
| SENT | Baker-Wurgler sentiment (orthogonalised version), last available | Short-leg anomaly strength [@SYY2012; @BW2006] |
| CREDIT | BAA − AAA yield spread | Distress / funding |
| TERM | 10y − 3m Treasury | Business cycle |
| INFL | CPI YoY inflation (lagged for release) | Inflation regime |
| DRATE | 12-month change in 10y yield | Rate regime |
| FMOM_k | Trailing 12-month return of theme-k factor (13 values) | Factor momentum [@EL2022] |
| DISP | Cross-sectional dispersion of composite signal | Opportunity set |

State variables are standardised with expanding-window means and standard deviations. HMM-smoothed regime probabilities are prohibited (look-ahead). Placebo tests replace z with (i) block-shuffled z and (ii) random-walk series.

## 7. Portfolio Methodology

**Optimiser (P-cells and projection step for E-cells).**

max_w α_t'w − (γ/2)·w'Σ_t w − Σ_i TC_i(|w_i − w⁺_{i,t−1}|)

subject to:
- Σ_i w_i = 0 (dollar neutral) and Σ_i |w_i| ≤ 2
- |β_t'w| ≤ 0.05 (beta from the risk model)
- |Σ_{i∈g} w_i| ≤ 0.02 for each Fama-French 49 industry g
- |w_i| ≤ min(1%, 10 × participation cap), with trade size |Δw_i|·AUM ≤ 5% of 20-day ADV_i
- Long-only benchmark-relative variant in robustness: w ≥ 0, Σw = 1, tracking error ≤ 4%

Solved with CVXPY (MOSEK or Clarabel); failures are logged and the portfolio is held.

**Risk model.** Structural factor model Σ = B F B' + D. B is market beta, 13 JKP theme exposures (cross-sectional z-scores) and FF49 industry dummies. Factor returns come from daily cross-sectional WLS (√market-cap weights). F is EWMA with a 126-day half-life and Newey-West adjustment. D is EWMA idiosyncratic variance with Bayesian shrinkage toward size-decile means. Robustness: a 20-factor PCA statistical model and a Ledoit-Wolf-shrunk sample covariance on the top-500 universe [@LW2017].

**Transaction-cost model (per stock, per trade of dollar size Q).**

TC_i(Q) = (s_i/2)·|Q| + k·σ_i·|Q|^{1.5} / ADV_i^{0.5} + commission·|Q|

- s_i: effective spread (TAQ-based where available; EDGE or AR estimator otherwise).
- σ_i: daily volatility; ADV_i: 20-day average dollar volume.
- k = 1 baseline, with 0.5×, 2× and 3× sensitivity. The 3/2 total-cost power corresponds to square-root impact; @ATHL2005 report a concave impact exponent near 3/5 [verify], and the functional form is a sensitivity dimension.
- commission = 1 bp.
- Short positions pay 25 bps per year (general collateral). Stocks in the bottom institutional-ownership decile pay 5% per year, or Markit fees where licensed.
- AUM baseline $1bn (Dec-2020 dollars, scaled by total CRSP market capitalisation), grid {$0.1bn, $1bn, $10bn}.

Bounds: live institutional costs may be lower [@FIM2018]; fund-implied costs may be higher [@PW2020].

**Execution assumption.** Signals are formed with information available at month-end t. Trades are assumed executed at the close of the first trading day of month t+1 (one-day implementation lag), with returns accrued from that price. A same-day-close variant is reported only as a sensitivity.

## 8. Benchmarks

| Group | Benchmarks |
|---|---|
| Naive | 1/N universe; VW market; EW z-score composite; theme-EW composite; IC-weighted (rolling 60m); ICIR-weighted; inverse-volatility of signal portfolios |
| Linear statistical | Lewellen FM rolling slopes [@LEW2015]; ridge; lasso; elastic net; PLS [@LMR2017] |
| Portfolio-level | KNS shrunk SDF over signal portfolios [@KNS2020]; NRRZ-style PLS factor timing [@NRRZ2024] |
| Nonlinear ML | Random forest; LightGBM; GKX NN3 [@GKX2020]; IPCA expected returns [@KPS2019] |
| Economic objective | DMNU linear PPP with TC [@DMNU2020]; JKMP Portfolio-ML using authors' public code [@JKMP2026]; deep PPP [@SWZ2023] if code obtainable |
| Cost mitigation | NMV buy/hold banding applied to the EW composite [@NMV2016] |
| Factor models (alpha) | FF5 + UMD; q5; JKP 13 themes; DNMV net-of-cost model comparison logic [@DNMV2023] |

Every benchmark receives the **same** tuning budget per refit as the corresponding factorial cell, and all hyperparameter grids are published.

## 9. Validation Framework

- **Walk-forward.** Initial training Jan 1972 to Dec 1989; validation Jan 1990 to Dec 1994; first test year 1995. Each January: expanding training window, rolling 5-year validation immediately before the test year, embargo gap equal to the target horizon h between training/validation and validation/test (labels overlapping the next split are purged) [@LDP2018]. Refit annually.
- **Lockbox.** Jan 2021 to Dec 2025 remains untouched until all design choices are frozen and pre-registered. It is opened once.
- **Rolling-window robustness.** A 20-year rolling training window.
- **No k-fold shuffling** of time. Purged grouped cross-validation is used only inside the training window for early-stopping diagnostics.
- **Point-in-time rules.** Annual Compustat items are used ≥ 4 months after fiscal year-end; quarterly items after RDQ, or ≥ 4 months after quarter-end if RDQ is missing. Market equity is at t. Signals whose original publication year is after t are flagged, and a gated library is used in robustness [@MP2016]. The CRSP-Compustat link is valid at t. Survivorship: the universe is formed at t from all securities alive at t. Delisting returns come from CRSP; missing performance-delisting returns are set to −30% [@SHU1997; verify convention].

## 10. Evaluation Metrics

| Group | Metrics |
|---|---|
| Prediction | Pooled OOS R² vs zero [@GKX2020]; MSE; IC, rank IC, ICIR, IC t-stat (NW); top-minus-bottom decile spread (VW) |
| Portfolio (gross & net) | Annualised mean, volatility, Sharpe, Sortino, max drawdown, Calmar, skewness, kurtosis, CVaR(5%) |
| Implementation | One-way monthly turnover; average holding period; cost drag (bps/month); share of costs from spread vs impact; short-leg share of returns; microcap/illiquid exposure |
| Economic | Certainty-equivalent return; net alpha vs FF5+UMD, q5, JKP themes (NW t); implementable efficient frontier [@JKMP2026]; break-even AUM; break-even cost multiplier |
| Conversion rates (novel reporting) | Net Sharpe per unit IC; cost drag per unit turnover; transfer coefficient (correlation of scores with implemented weights) [@CST2002] |

## 11. Statistical Framework

1. **Mean returns and alphas.** Newey-West HAC t-statistics (12 lags) [@NW1987].
2. **Sharpe differences.** Ledoit-Wolf studentised circular block bootstrap (block lengths 4, 6, 12; 5,000 reps) [@LW2008]; Lo's serial-correlation adjustment for reporting [@LO2002].
3. **Forecast comparisons.** Clark-West for nested models [@CW2007]; Diebold-Mariano on cross-sectional average errors [@DM1995].
4. **Data snooping.** Every configuration is logged (MLflow). Hansen SPA versus the strongest benchmark (stationary bootstrap, mean block 6, 10,000 reps) [@HAN2005; @PR1994]; White Reality Check [@WHI2000]; Romano-Wolf StepM to identify which cells beat the benchmark [@RW2005]; Model Confidence Set at 10% [@HLN2011].
5. **Backtest overfitting.** Deflated Sharpe ratio using the logged number of trials and their correlation [@BLDP2014]; probability of backtest overfitting via CSCV with 16 blocks [@BBLZ2017]; Harvey-Liu haircut Sharpe [@HL2015].
6. **Factorial attribution.** Monthly net returns of the 16 cells regressed on ±1-coded factors and all interactions (orthogonal contrasts). Shapley decomposition of net Sharpe and CE across the four ingredients. Confidence intervals by month-block bootstrap, which preserves cross-cell dependence.
7. **Stability.** Bai-Perron structural breaks in rolling cell differences [@BP1998]; subperiod tests.
8. **Multiple signal/theme claims.** Benjamini-Hochberg FDR [@BH1995]; t > 3 hurdle for any new-signal-type claim [@HLZ2016].
9. **Non-standard errors.** Distribution of main-effect estimates across a pre-declared multiverse (window type, universe, horizon, target transform, cost estimator, risk model) [@MENK2024; @CHK2024].

## 12. Robustness Framework

Subperiods (1995-2000, 2001-2008, 2009-2019, 2020-2025; pre/post decimalisation). Universes (all stocks incl. microcaps; ex-microcaps (main); NYSE top 500). Weighting and constraints (long-only; no industry constraint). Horizons (1, 3, 6, 12m) and quarterly rebalancing. Cost multipliers 0.5-3× and alternative spread estimators. AUM grid. Risk models (structural, PCA, LW shrinkage). Rolling vs expanding windows. Publication-gated signal library. Placebo states. NN seeds (≥10) and ±1 grid-step perturbations. International out-of-sample (JKP developed ex-US). Alternative uncertainty estimators (bootstrap SE, MC dropout, conformal).

## 13. Economic Interpretation Plan

- **Economic feature importance.** Change in net utility when a theme is removed and the model refit [@JKMP2026]. TreeSHAP and deep SHAP by theme for P-cells [@LL2017]. ALE plots, given correlated signals [@AZ2020].
- **Interaction analysis.** Friedman H-statistics for the top theme pairs; comparison of gross vs net importance.
- **State dependence.** Implied signal-theme weights (cross-sectional regression of implemented weights on theme scores) regressed on z_t, with tests of H5.
- **Portfolio attribution.** Returns decomposed into theme exposures, industry, market and residual; cost attribution by theme.
- **Limits to arbitrage.** Portfolio tilts on idiosyncratic volatility, illiquidity, size and distress by cell (H6) [@ACM2023].
- **Alignment.** Ex-ante vs ex-post risk bias statistics by cell [@CSS2012].

## 14. Contribution Statement (draft)

> Existing literature shows that machine-learning combinations of firm characteristics improve return prediction [@GKX2020], that the resulting portfolios are fragile to economic restrictions and trading costs [@ACM2023; @BHHH2023], and that learning portfolio weights under a cost-aware objective substantially improves the implementable efficient frontier [@JKMP2026; @DMNU2020; @SWZ2023].
>
> However, these studies compare bundled pipelines. They largely assume that the sources of ML's value (flexible functional form, time-varying signal efficacy, the training objective and forecast uncertainty) can be assessed one at a time, on different data, costs and evaluation criteria.
>
> We propose a controlled factorial design that switches each ingredient on and off within one signal library, universe, optimiser, cost model and inference framework, and we attribute net-of-cost performance to the ingredients and their interactions with data-snooping-robust tests.
>
> This allows us to test whether nonlinearity creates value beyond its trading costs, whether state-dependent signal weights help only when costs are internalised, and whether uncertainty shrinkage works through turnover.
>
> We demonstrate [results to be determined] across US equities from 1995 to 2025, including an untouched 2021-2025 holdout, three AUM levels, cost-model perturbations and developed international markets.
>
> The results imply [to be determined; stated only after the lockbox is opened].

**What we explicitly do not claim.** We are not the first to use ML for signal combination, the first to include transaction costs, the first to condition on market states, or the first to quantify design-choice dispersion (see the closest-prior-art tracker).

## 15. Comparison Tables Against the Closest Papers

### 15.1 Ten closest papers

| Paper | What it does | What we use | What we improve | Why ours is different |
|---|---|---|---|---|
| @JKMP2026 | Cost-aware ML weight learning; implementable frontier | Frontier evaluation; Portfolio-ML as benchmark; public code | Isolate the objective effect from nonlinearity, conditioning and uncertainty | Attribution and interaction tests, not a single pipeline |
| @SWZ2023 | NN parametric portfolio policies vs linear | Nonlinear economic-loss cell | Common cost model/optimiser; conditioning; snooping control | Decomposition and mechanisms |
| @DMNU2020 | Linear PPP with TC; netting | Linear economic-loss cell | Nonlinear and conditional extensions | Measures netting benefits of nonlinear/conditional combination |
| @DMU2024 | Conditional multifactor weights net of costs | Conditioning-with-costs logic | Stock-level, many states, nonlinear | Tests the conditioning × cost interaction at scale |
| @GKX2020 | ML prediction horse race | Model classes and OOS R² design | Net-of-cost evaluation in a common optimiser | Economic rather than statistical attribution |
| @ACM2023 | ML under economic restrictions | Universe restrictions; limits-to-arbitrage tests | Constructive design | Explains which ingredient causes fragility |
| @NRRZ2024 | High-dimensional factor timing | State variables; PLS timing benchmark | Stock-level implementation with netting and costs | Timing information inside cost-aware combination |
| @CHK2024 | ML design choices; non-standard errors | Multiverse reporting | Economic ingredients; net of costs; common optimiser | Attribution of net value, not dispersion |
| @LMNS2025 | NN forecast uncertainty; uncertainty-averse portfolios | Bootstrap SE variant | Cost interaction; turnover channel | Uncertainty as one factor in the factorial design |
| @BHHH2023 | Horizon and net ML alpha | Horizon grid | Horizon chosen in validation and counted as trials | Horizon as a controlled design factor |

### 15.2 Five strongest methodological precedents

| Paper | What it does | What we use | What we improve | Why ours is different |
|---|---|---|---|---|
| @HAN2005 | SPA test | Snooping control over cells | Applied to factorial cells | Cell-level inference |
| @RW2005 | StepM | Identify cells beating benchmark | - | - |
| @BBLZ2017 | PBO via CSCV | Overfitting probability of chosen configuration | Report for full trial log | Transparency |
| @MENK2024 | Non-standard errors | Multiverse design | Economic ingredients | Attribution |
| @LW2008 | Robust Sharpe tests | Pairwise Sharpe inference | Gross vs net | Conversion rates |

### 15.3 Five strongest portfolio-construction precedents

| Paper | What it does | What we use | What we improve | Why ours is different |
|---|---|---|---|---|
| @GP2013 | Dynamic trading with costs; aim portfolio | Partial adjustment logic | Learned signal weights | Empirical ML setting |
| @CDS2020 | Liquidity-regime allocation with costs | H5 trading-speed prediction | Empirical test at stock level | Theory test |
| @BSCV2009 | Parametric portfolio policies | Economic-loss parameterisation | Nonlinear, conditional, cost-aware | Nested cells |
| @LW2017 | Nonlinear shrinkage covariance | Robustness risk model | - | - |
| @NMV2016 | Anomaly costs and mitigation | Banding benchmark; spread measures | Optimised mitigation | Optimiser vs heuristic |

### 15.4 Design v2: what changed after the 2025-2026 frontier search (September 2026)

A targeted search of what these journals have accepted or circulated in 2025-2026 produced four
changes. Each is a **level on an existing axis** or a **credibility instrument**; nothing was added
as decoration, because every extra arm weakens the deflated Sharpe ratio of the eventual winner.

| Change | What it is | Why it is now necessary |
|---|---|---|
| Form ladder A2-A4 | Ridgeless random Fourier features on a complexity grid (c = P/T), a sparse basis-pursuit arm on the same feature map, and a cross-sectional attention block | The complexity debate moved on: @VSC2026 shows complexity pays through sparse discovery while dense ridgeless plateaus, and @AIPT2025 shows it pays only when the factor spectrum is diffuse. Attention is the current state of the art for cross-asset combination [@KKMX2025; @SERT2025] |
| Uncertainty ladder D2-D3 | Time-ordered split conformal intervals with adaptive recalibration, feeding an ellipsoidal or Wasserstein robust objective | Ensemble dispersion has no coverage guarantee; conformal does [@CPPS2024], and connecting it to the decision is the economically interesting claim |
| Economic-objective controls | Output clipping, partial adjustment and a reported prediction-inflation diagnostic | @SPO2026 shows decision-focused learning inflates signals and turnover, which is exactly the pathology our objective axis tests |
| Credibility layer | Zero-predictability synthetic null, microstructure placebo, multiplicity-adjusted inflation gap, spectrum diagnostic, limits-to-learning caveat | @SPUR2026 shows adaptive specification search produces significant backtests under a no-predictability null; @LLG2025 shows empirical fit understates true predictability |

**New closest prior art.** @FRLUX2025 (October 2025) performs friction-aware, regime-conditioned
policy optimisation with costs inside the reward and a regime x cost evaluation grid. It is the
nearest neighbour to gap G2 and must be cited in the introduction. The differentiation is
structural: it proposes a single reinforcement-learning method in a small asset space, whereas this
paper identifies *which ingredient* produces net-of-cost value in a ~150-signal stock cross-section
under a nested factorial design with data-snooping-robust inference.

**Deliberately excluded**, with reasons recorded so referees see the choice was made rather than
missed: deep reinforcement-learning agents (occupied by @FRLUX2025; replication risk), graph neural
networks on licensed relationship data (point-in-time integrity), LLM-generated signals (training
data covers our sample, so look-ahead is unresolvable before a strict post-cutoff window), and
diffusion models for return distributions (no finance precedent; adds trials without touching an
axis).

### 15.5 Five strongest ML-finance precedents

| Paper | What it does | What we use | What we improve | Why ours is different |
|---|---|---|---|---|
| @GKX2020 | ML prediction benchmark | NN3/GBDT designs | Net evaluation | Attribution |
| @CPZ2024 | State-dependent deep SDF | Macro-state conditioning idea | Costs; interpretable fixed states | Implementable conditioning |
| @KPS2019 | IPCA | Benchmark expected returns | - | - |
| @AHV2023 | ML strategies net of costs | Net evaluation conventions | Cost-aware learning | Attribution |
| @CTWZ2021 | RL/transformer direct construction | Direct-objective idea | Controlled comparison under strict costs | Replicability focus |
