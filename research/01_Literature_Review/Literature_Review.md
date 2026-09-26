# Comprehensive Literature Review: Machine Learning for Alpha Signal Combination and Portfolio Construction

## Executive Summary

This review covers the published and working-paper literature on using machine learning (ML) to combine many return-predictive signals into portfolios. The literature universe assembled for this project contains more than 180 entries. About 35 are core papers analysed in detail in the literature matrix, and the rest are foundational, methodological, data and inference references. Every entry carries an evidence label; DOIs were checked against Crossref where available (see 08_References).

Five conclusions organise the rest of this document.

**1. Prediction is largely solved as an engineering problem, but its economic value is not.** Flexible models (trees, neural networks, autoencoders, adversarial SDF estimators) reliably beat linear models on statistical criteria and gross long-short spreads [@GKX2020; @GKX2021; @CPZ2024; @FNW2020]. The most-cited evidence, however, evaluates gross, sort-based portfolios.

**2. The implementability reckoning has arrived.** ML alpha is concentrated in microcaps, distressed and hard-to-arbitrage stocks and in high limits-to-arbitrage states. It deteriorates under realistic trading costs [@ACM2023]. Net performance of common one-month-horizon ML models is near zero after 2004 [@BHHH2023]. The average published anomaly earns only a few basis points per month net and post-publication [@CV2023; @CW2026]. Researcher design choices produce non-standard errors larger than standard errors [@CHK2024; @LAL2025; @MENK2024]. Some sophisticated ML combinations remain profitable after costs [@AHV2023].

**3. The frontier has moved from "predict better" to "learn under the economic objective".** Parametric portfolio policies [@BSCV2009] were extended to transaction costs [@DMNU2020], to neural networks [@SWZ2023], and to ML under an implementable-efficient-frontier criterion [@JKMP2026]. Learning weights directly under a cost-aware objective dominates predict-then-optimise after costs. Any new paper claiming "cost-aware ML signal combination" must be positioned against these papers.

**4. Signal efficacy is time-varying, but evidence of implementable state-dependent combination at the stock level is thin.** Factor returns are timeable [@HKS2020; @NRRZ2024; @KNNV2024; @EL2022]. Anomalies depend on sentiment and market states [@SYY2012; @MPR2026], and momentum crashes are predictable [@DM2016]. A conditional multifactor portfolio survives costs at the factor level [@DMU2024]. Theory says trading speed and allocation should depend on liquidity regimes [@CDS2020]. We found no paper that cleanly measures whether state-dependent signal weights add net-of-cost value at the stock level, separately from nonlinearity and from the cost-aware objective (research inference; see the closest-prior-art tracker).

**5. Uncertainty and non-stationarity are emerging, not settled.** Formal inference for neural-network expected returns and its portfolio use is new [@LMNS2025]. So is joint selection of training windows and complexity [@CHSWZ2025], and meta-learning under regime shifts [@WL2025]. Learning from forecast errors improves optimiser robustness in low dimensions [@BS2022].

The most defensible research opportunity is therefore not another model. It is a rigorous, multiple-testing-robust **attribution of where the net-of-cost value of ML signal combination comes from**: nonlinearity, state dependence, a cost-aware objective and forecast uncertainty, including their interactions. The attribution should come with economic mechanisms. This is developed in the Research Gap report and the Selected Research Design.

## 1. Scope, Search Protocol and Evidence Standards

**Scope.** Cross-sectional equity return prediction with many signals; signal/forecast combination; portfolio construction (mean-variance, risk-based, robust, end-to-end, parametric policies); transaction costs and capacity; factor timing and regimes; backtest integrity and inference; interpretability.

**Sources.** Publisher pages (Oxford Academic, Wiley, Elsevier, INFORMS, Cambridge, Taylor & Francis, Springer), NBER, SSRN, arXiv (only where relevant), authors' repositories, association policy pages, and the Crossref and OpenAlex APIs for bibliographic verification and journal metrics. Blogs and content farms were not used as evidence.

**Evidence labels used throughout the package.**

| Label | Meaning |
|---|---|
| Verified | Stated in the paper abstract, publisher page, authors' repository, or confirmed via Crossref/OpenAlex |
| [inference] | Our reading or synthesis; not a claim made by the cited authors |
| [verify] | Detail we could not confirm from an accessible primary source; check full text before citing |
| Proposed | Our own research idea or design choice |
| Hypothesis | A pre-registered expectation to be tested, not a result |

**Limits of this review.** Many full texts sit behind paywalls, so some design details (exact sample splits, cost calibrations) are marked [verify]. Journal Impact Factors from Clarivate could not be verified and are not reported as facts. OpenAlex citation metrics are reported instead, with their date.

## 2. Evolution of the Literature

### 2.1 Wave 1: The factor zoo and the multiplicity problem (1990s to 2016)

The characteristic-based literature produced hundreds of predictors. Cochrane's "zoo" framing [@COC2011] set the question of which characteristics provide independent information. Multiple-testing hurdles rose [@HLZ2016]. Many anomalies failed stricter replication with NYSE breakpoints and value weighting [@HXZ2020], while open replication showed most clearly significant predictors do reproduce [@CZ2022; @JKP2023]. Returns decline out of sample and after publication [@MP2016], and fewer characteristics provide independent information after 2003 [@GHZ2017]. This wave supplies both the **signal library** and the **integrity constraints** a modern paper must respect.

### 2.2 Wave 2: Linear aggregation and shrinkage

Before ML, the canonical combination was the Fama-MacBeth regression with historically averaged slopes [@FM1973; @LEW2015]. Alternatives included latent-variable/PLS aggregation [@LMR2017] and SDF estimation with economically motivated shrinkage over many anomaly portfolios [@KNS2020]. Nonparametric selection showed nonlinearity matters and that many predictors are redundant [@FNW2020]. In time series, simple forecast combination beats individual models under instability [@RSZ2010], a result that makes naive combinations dangerous benchmarks for any "dynamic weighting" claim.

### 2.3 Wave 3: The ML prediction wave (2018 to present)

@GKX2020 set the standard design: a pooled panel of stock characteristics, macro interactions and industry dummies; a battery of methods from penalised regressions to neural networks; out-of-sample R² and decile spreads. Trees and neural networks won because they capture nonlinear interactions. Extensions added conditional latent factors [@GKX2021; @KPS2019], adversarial no-arbitrage SDFs with macro states [@CPZ2024], trees that build test assets [@BPZ2025; @CFHH2025], principal portfolios using cross-asset signals [@KMP2023], image-based signals [@JKX2023], and transformers inside the SDF [@KKMX2025]. A theoretical "virtue of complexity" argues that heavily parameterised models improve out-of-sample performance [@KMZ2024; @DKKM2023]. International evidence confirms broad predictability and the usefulness of combining models [@CFMZ2023; @TH2021], with market structure mattering [@LWZ2022].

### 2.4 Wave 4: The implementability reckoning (2016 to present)

Trading-cost research showed that turnover determines which anomalies survive, and that buy/hold spreads mitigate costs [@NMV2016; @NMV2019]. Ignoring costs biases model comparisons [@DNMV2023]. Applied to ML, @ACM2023 showed profitability concentrates where arbitrage is hardest, and @BHHH2023 showed the horizon of the training target is a first-order lever for net returns. @CV2023 and @CW2026 set a sobering prior for single-signal alpha. Meta-scientific work on non-standard errors [@MENK2024] was extended to ML design choices [@CHK2024; @LAL2025]. Cost calibration is itself uncertain: live institutional execution costs are "an order of magnitude smaller" than earlier estimates [@FIM2018], while fund-based implementation costs appear substantial [@PW2020]. A credible paper must therefore treat the cost model as a sensitivity dimension, not a fixed assumption.

### 2.5 Wave 5: Learning under the economic objective

Modelling weights directly as functions of characteristics [@BSCV2009] was extended to transaction costs, where trade netting makes more characteristics jointly useful [@DMNU2020]. It was generalised to neural networks [@SWZ2023] and to ML designed for the implementable efficient frontier [@JKMP2026], where learning portfolio weights under a cost-aware objective beats Markowitz-with-ML-forecasts after costs. In OR and ML, decision-focused losses [@EG2022], differentiable optimisation layers [@AK2017; @AAB2019] and end-to-end portfolio models [@BK2023; @CI2023; @ULM2024; @ZZR2020] follow the same logic, but mostly on small asset universes. Reinforcement-learning direct construction reports very high Sharpe ratios in US equities [@CTWZ2021]; independent replication under strict cost assumptions is advisable [inference].

### 2.6 Parallel strands: timing, regimes, uncertainty, non-stationarity

- **Timing and regimes.** Factor timing [@HKS2020; @NRRZ2024; @KNNV2024], factor momentum [@EL2022], volatility management [@MM2017; @COWY2020; @DMU2024], sentiment-conditional anomalies [@SYY2012], momentum crashes [@DM2016; @BSC2015], state-dependent anomaly performance [@MPR2026], regime-switching allocation [@AB2002; @GT2007; @NML2018; @SYM2025], and liquidity regimes with costs [@CDS2020].
- **Uncertainty.** Learning from out-of-sample forecast errors [@BS2022]; forecast confidence intervals for neural-network expected returns [@LMNS2025]; robust optimisation [@GI2003; @BCZ2022]; estimation-risk-aware rules [@KZ2007].
- **Non-stationarity.** Joint window/complexity selection [@CHSWZ2025]; meta-learning [@WL2025; @DA2023].

## 3. Key Papers at a Glance

| Paper | Core question | Key verified finding | What it leaves open |
|---|---|---|---|
| @GKX2020 | Which ML measures risk premia best? | Trees and NNs win via nonlinear interactions | Net-of-cost value; implementability |
| @ACM2023 | Does ML survive economic restrictions? | Profits concentrate in hard-to-arbitrage stocks/states; costs erode them | Implementable-by-design combinations |
| @JKMP2026 | How to use ML for the net frontier? | Learning weights under cost-aware objective dominates | Attribution across nonlinearity, states, uncertainty [inference] |
| @DMNU2020 | How do costs change useful characteristics? | 6 to 15 significant characteristics due to netting | Nonlinear/conditional versions |
| @SWZ2023 | Do NN policies beat linear PPP? | 75-276 bps/month higher CE, robust to costs | State dependence; decomposition [inference] |
| @BHHH2023 | Does ML alpha survive costs? | Near-zero net after 2004 for 1-month models; longer horizons help | Signal/state-specific horizons |
| @AHV2023 | Expected returns of ML strategies? | Up to 1.42%/month net; LSTM net alpha 1.20% (t=3.46) | Cost-aware learning |
| @CHK2024 | Do design choices matter? | 1,056 models; returns 0.13%-1.98%/month; NSE 59% above SE | Which choices create net value |
| @NRRZ2024 | Can the factor zoo be timed? | Timing improves nearly all factor groups; +20% return for multifactor | Stock-level implementation with costs |
| @DMU2024 | Do conditional multifactor weights survive costs? | Yes, out of sample and net of costs | High-dimensional stock-level conditioning |
| @CDS2020 | Optimal allocation under liquidity regimes? | Trading speed higher in persistent, risky, liquid states | Large-scale empirical test |
| @LMNS2025 | How uncertain are NN return forecasts? | Closed-form SEs; uncertainty-averse portfolios improve OOS | Interaction with costs |
| @CV2023 | Expected anomaly returns net? | About 4 bps/month average net and post-publication | Whether combination rescues value |
| @BLACKROCK2025 | Industrial ML alpha pipeline | Predict-then-optimise with regime resampling and SHAP attribution; no statistical evidence | Everything requiring inference |

The full matrix (all fields requested: data, universe, frequency, features, ML, combination, portfolio, benchmark, metrics, period, costs, turnover, risk controls, result, contribution, limitation, what was not solved, extension) is in Workbook 1 (Literature Database).

## 4. Machine-Learning Methods: Where They Add Economic Value

| Method family | Evidence of predictive value | Evidence of net economic value | Assessment for our problem |
|---|---|---|---|
| Penalised linear (ridge, lasso, elastic net, PLS) | Solid, modest [@GKX2020; @LMR2017] | Low turnover; strong under costs when used in PPP [@DMNU2020] | Mandatory baseline; often hard to beat net |
| Random forests / GBDT (XGBoost, LightGBM) | Strong, capture interactions [@GKX2020; @LLMSS2021] | Mixed; gains shrink in large caps and after costs [@ACM2023; @BHHH2023] | Main nonlinear workhorse; cheap, interpretable via TreeSHAP |
| Feed-forward NNs / ensembles | Strong in US panel [@GKX2020]; large NN portfolios [@SWZ2023] | Positive when trained on economic objective [@SWZ2023; @JKMP2026] | Include as ensemble with seeds; report dispersion |
| Random features / high complexity | Theory and evidence for complexity [@KMZ2024; @DKKM2023] | JKMP uses random-feature regressions inside a cost-aware design [@JKMP2026] | Useful for economic-loss learner |
| Autoencoders / latent factors (IPCA, CA) | Good pricing performance [@KPS2019; @GKX2021] | Weakened under restrictions [@ACM2023] | Risk-model / benchmark role |
| RNN / LSTM | Useful for sequences and macro states [@CPZ2024; @AHV2023] | LSTM combination profitable net in one study [@AHV2023] | Optional; high tuning burden |
| CNN (images) | Price-pattern signals [@JKX2023] | Signal generation, fast decay likely [inference] | Out of scope (signal generation) |
| Transformers / attention | Cross-asset information sharing [@KKMX2025; @CTWZ2021] | Unproven under strict costs [inference] | Robustness extension only |
| Reinforcement learning | Direct construction [@CTWZ2021; @MS2001] | Claims large; replication risk | Not a primary method; high overfitting risk |
| Mixture-of-experts / gating | Classic architecture [@JJNH1991] | Little finance evidence net of costs [inference] | Natural way to parameterise state dependence |
| Meta-/online learning | Regime adaptation [@WL2025; @DA2023] | Net value untested [inference] | Robustness dimension |
| Bayesian / uncertainty-aware | Forecast SEs [@LMNS2025]; deep ensembles [@LPB2017] | Emerging [@LMNS2025; @BS2022] | One factor in our design |
| Graph neural networks | Economic links predict returns [@CF2008] | Data/PIT hard; unproven net [inference] | Out of scope for main paper |

**Assessment [inference].** The binding constraint on economic value is not model expressiveness but the mapping from forecasts to trades: turnover, concentration in illiquid names, and misalignment between the training loss and the investor objective. Additional architectural complexity is justified only if it survives the cost-aware objective and data-snooping corrections.

## 5. Portfolio Construction: What the Evidence Says

- **Estimation error dominates naive optimisation.** None of 14 sample-based rules consistently beat 1/N out of sample [@DGU2009]. Constraints act as shrinkage [@JM2003]; shrinkage covariance estimators help in high dimensions [@LW2004; @LW2017]. Hierarchical risk parity avoids inversion [@LDP2016].
- **Risk-based portfolios** (minimum variance, risk parity, maximum diversification, HRP) are useful risk baselines [@MRT2010; @CC2008] but ignore alpha. For a signal-combination paper they belong in the risk-model comparison, not as alpha benchmarks [inference].
- **Blending forecasts with confidence.** Black-Litterman [@BL1992] and robust/DRO formulations [@GI2003; @DY2010; @BCZ2022] offer principled ways to temper ML alphas by their uncertainty.
- **Transaction-cost-aware dynamic trading.** Aim portfolios with partial adjustment [@GP2013], regime-dependent trading speed [@CDS2020], and utility-maximising parametric policies with costs [@DMNU2020; @JKMP2026] are the state of the art. Heuristic mitigation (buy/hold bands) is a strong simple benchmark [@NMV2016].
- **Alignment.** Differences between the alpha model, risk model and constraints create unintended exposures and underestimated risk [@CSS2012; @LS2008]. This is likely worse for nonlinear ML alphas [hypothesis].
- **End-to-end and decision-focused learning** reduces the gap between loss and objective [@EG2022; @BK2023], but evidence at stock-universe scale with realistic constraints remains limited, except for parametric/economic-loss approaches [@SWZ2023; @JKMP2026].

## 6. Prediction Is Not Investment Value

Many ML finance papers report strong predictive statistics but weak tradable performance. The mechanisms documented in the literature are:

1. **Tiny R², concentrated where it cannot be traded.** Monthly stock-level R² is fractions of a percent, even for the best models [@GKX2020]. The predictive content concentrates in microcaps, distressed and high-idiosyncratic-volatility stocks [@ACM2023]. Equal-weighted sorts amplify it [@HXZ2020].
2. **Loss/objective mismatch.** MSE weights all stocks and errors equally; the investor cares about ranking at the extremes, covariance, and trade costs. Decision-focused and economic-objective learning exist precisely because of this gap [@EG2022; @JKMP2026].
3. **Turnover.** One-month-horizon forecasts from fast signals such as reversal, short-term momentum and liquidity shocks create high turnover. Anomalies with more than 50% monthly turnover rarely survive [@NMV2016], and longer training horizons restore net alpha [@BHHH2023].
4. **The IC-to-IR chain.** The fundamental law links IR to IC and breadth [@GRIN1989]. Constraints reduce the transfer coefficient, so a higher IC can translate into little additional IR [@CST2002].
5. **Short-leg dependence.** A large share of anomaly profits comes from the short side and bad states [@SYY2012; @MPR2026], where borrow costs and constraints bind.
6. **Error maximisation.** Plugging noisy ML alphas into mean-variance optimisers amplifies errors [@MICH1989; @DGU2009].
7. **Decay and publication.** Returns fall out of sample and after publication [@MP2016]. Recent net alpha of published anomalies is near zero [@CW2026].
8. **Researcher degrees of freedom.** Non-standard errors from design choices rival or exceed standard errors [@CHK2024; @LAL2025; @MENK2024]. Multiple testing inflates backtests [@HLZ2016; @BLDP2014; @BBLZ2017].
9. **Non-stationarity.** Relationships shift; longer windows help complex models but include stale regimes [@CHSWZ2025].

**Implication for our research.** Every experiment must report prediction metrics (OOS R², IC, rank IC, ICIR), portfolio metrics (gross and net Sharpe, Sortino, drawdown, turnover, alpha, capacity), and the **conversion rates** between them. These are, for example, net Sharpe per unit of IC and cost drag per unit of turnover. This makes "prediction vs. investment value" a measured result rather than a caveat.

## 7. What Is Solved and What Remains Open

**Largely solved (do not claim novelty here):**
- ML beats linear models on statistical accuracy and gross spreads in US and global equities.
- Trees and NNs capture nonlinear interactions; price-trend, liquidity and volatility characteristics dominate predictions.
- Costs matter first-order; turnover and horizon are key levers; simple mitigation helps.
- Learning portfolio weights under a cost-aware economic objective beats predict-then-optimise net of costs (JKMP2026; DMNU2020 linear; SWZ2023 nonlinear).
- Factor returns are timeable at the factor-portfolio level.
- Backtest-integrity tools exist (DSR, PBO, SPA, MCS, FDR).

**Partially solved:**
- State-conditional combination net of costs: shown for low-dimensional factor sets (DMU2024), not stock-level high-dimensional signals.
- Uncertainty-aware ML portfolios: new working-paper evidence (LMNS2025), interaction with costs untested.
- Design-choice robustness: documented (CHK2024, LAL2025), but the economic sources of dispersion are not identified.

**Open (to the best of our search; re-check before submission):**
- A unified attribution of net-of-cost ML value to nonlinearity, state dependence, economic objective and uncertainty, including their interactions.
- Whether conditioning helps only when costs are internalised (the interaction), and whether the realised state dependence matches economic theory (DM2016, SYY2012, CDS2020).
- Whether conclusions survive formal data-snooping control across all tried configurations.

## 8. The BlackRock "Augmented Investment Management" Framework

**What it proposes (verified from the white paper, BlackRock Systematic, November 2025, professional-investor material).** AIM, started in 2014, reframes signal combination as forecasting excess returns ("alpha forecasts") from a large signal library, which BlackRock's Figure 1 shows growing to roughly 1,200 stock-selection signals by 2025. The pipeline has four stages: feature processing (outliers, imputation, time-series transforms, optional risk-factor neutralisation); ML training (regularised linear models, gradient-boosting ensembles, neural networks, proprietary variants) chosen by a large-scale configuration search with cross-validation; prediction post-processing; and a separate optimiser and simulator that accounts for transaction costs, borrow costs and fund constraints. Model parameters are tuned to maximise a metric such as the information ratio. Training data typically span 10-20 years. Interpretability uses Shapley-regression additive attribution. Regime-awareness is achieved by resampling so that negative regimes are over-represented. The illustrative defensive model had better drawdown behaviour but about a 20% overall performance haircut. The authors list non-stationarity (signal decay, cyclical shifts) as ongoing research, pointing to adaptive/online learning, transfer learning and domain adaptation.

**Assumptions [inference].** (i) Separation of forecasting from portfolio construction is acceptable, with costs handled only in the optimiser and simulator. (ii) Cross-validation on financial time series controls overfitting, although standard k-fold without purging/embargo can leak. (iii) Regime robustness can be induced by reweighting history rather than by conditioning on observable states. (iv) Tuning on backtest IR across a large configuration search does not create selection bias.

**What later academic research improves.** Cost-aware learning of weights instead of pure predict-then-optimise [@JKMP2026; @DMNU2020; @SWZ2023]. Purged/embargoed validation [@LDP2018]. Deflated Sharpe and PBO for configuration search [@BLDP2014; @BBLZ2017]. State-conditional combination that survives costs [@DMU2024]. Forecast uncertainty [@LMNS2025]. Horizon choice [@BHHH2023].

**What remains unanswered.** The white paper provides no out-of-sample statistical tests, no net-of-cost performance tables, no turnover or capacity figures, and no attribution of value to its components. Its data are proprietary.

**What we do differently (proposed).** We treat each AIM design component as a factor in a controlled experiment on public, reproducible data: nonlinearity, conditioning (versus resampling), cost-awareness in training (versus only in the optimiser), and uncertainty. We use one optimiser and one cost model with sensitivity analysis, log every configuration for data-snooping control, and test whether the realised state dependence matches economic theory.

## 9. Research Opportunities (summary)

1. Attribution of net-of-cost ML value across nonlinearity, conditioning, objective and uncertainty (selected; see 05).
2. Forecasting signal efficacy with signal-level meta-features and implementing it at stock level with netting.
3. Uncertainty-aware alpha combination and robust cost-aware optimisation.
4. Scalable differentiable cost-aware optimisation layers.
5. Regime-gated mixture-of-experts combination with economically interpretable gates.

The full 15-idea matrix and five concept proposals are in 04_Paper_Concepts and Workbook 3.
