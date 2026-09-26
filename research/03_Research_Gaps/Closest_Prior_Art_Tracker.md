# Closest Prior Art Tracker (living document)

**Purpose.** Prevent the paper from claiming novelty that has already been published. Re-run the search protocol below at the start of every project phase, at each conference submission, and in the final week before journal submission. Record every newly found paper here, even if it seems only tangential.

**Current proposed claim (Concept A).** We provide a controlled, multiple-testing-robust attribution of the net-of-cost value of ML signal combination to (i) nonlinearity, (ii) state-dependent signal weights, (iii) a cost-aware economic training objective, and (iv) forecast-uncertainty shrinkage, including their interactions. We also test whether the learned state dependence matches economic theory.

**Extension under consideration (Sep 2026).** Whether the ranking of ML combination designs is
invariant to the investor's tax status, and whether an ex-ante regret-bounded aggregation rule over
those designs beats an equal-weighted blend of them after tax. Both are [proposal], not results.

**Claims we must NOT make (already published):**
- "First to use ML to combine many characteristics": @GKX2020 and many others.
- "First to incorporate transaction costs into ML portfolios": @JKMP2026; @DMNU2020 (linear); @SWZ2023.
- "First to show ML alpha is fragile to costs/restrictions": @ACM2023; @BHHH2023; @AHV2023.
- "First to condition on market states": @GKX2020 (macro interactions); @CPZ2024 (macro states); @DMU2024 (volatility, net of costs).
- "First to time factors with many predictors": @NRRZ2024; @HKS2020.
- "First to document design-choice dispersion": @CHK2024; @LAL2025; @MENK2024.
- "First uncertainty-aware ML portfolio": @LMNS2025; @BS2022.
- "First to evaluate equity strategies after tax": @JA1993; @ABY2001; @BY2003; @IM2012; @CBLO2020.
- "First to analyse taxes in a long/short book": **@SS2018** - this is the closest after-tax work and
  it already covers long/short factor portfolios, s1233 short treatment and harvesting supply.
- "First to show momentum is tax-inefficient": @IM2012.
- "First to use HIFO / lot selection to improve after-tax returns": @BY2003.
- "First adaptive or regret-bounded portfolio rule": @COVER1991; @BK1999; @LH2014; and for experts
  @VOVK1990; @LW1994; @FS1997; @HW1998.
- "First to detect concept drift in a financial model": @PAGE1954; @GAMA2014.
- "First to aggregate several ML models' stock forecasts online into a long-short strategy":
  **@RABM2023** - Bernstein Online Aggregation over ML stock-return forecasts, beats its members on
  Sharpe and shortfall at similar turnover, including under non-stationarity. Our adaptive layer is
  a method we ADOPT, not a contribution.
- "First to show tax awareness tilts a portfolio toward momentum": @IM2012; **@KS2024**.
- "First to show the tax benefit of a long-short book comes from gain deferral rather than loss
  harvesting": **@KS2024**. Also @SKP2018 for the character-versus-deferral decomposition.

## Search protocol (repeat each phase)

1. SSRN / NBER / arXiv q-fin keyword queries: "machine learning" AND ("transaction costs" OR "implementable") AND ("signal combination" OR "characteristics"); "factor timing" AND "stock level"; "conditional" AND "parametric portfolio"; "decomposition" AND "machine learning" AND "asset pricing"; "uncertainty" AND "machine learning" AND "portfolio".
2. Forward citations (Google Scholar / Semantic Scholar / OpenAlex) of: GKX2020, JKMP2026, DMNU2020, SWZ2023, ACM2023, DMU2024, NRRZ2024, LMNS2025, CHK2024.
3. Programmes: AFA, WFA, EFA, SFS Cavalcade, NBER Asset Pricing / Big Data, SoFiE, Q-Group, INQUIRE, ICAIF.
3b. **After-tax queries (added Sep 2026):** "after-tax" AND ("machine learning" OR "factor"); "tax-aware"
   AND ("optimization" OR "portfolio"); "tax-loss harvesting" AND "direct indexing"; "wash sale" AND
   "backtest"; forward citations of @SS2018, @IM2012, @BY2003, @CBLO2020. Also AQR, Parametric and
   Vanguard research pages, since much of this literature is practitioner-published.
3c. **Online-learning queries:** "online portfolio selection" AND "regret"; "expert advice" AND
   ("asset pricing" OR "factor timing"); "concept drift" AND "financial"; forward citations of
   @COVER1991, @HW1998, @LH2014.
4. Tables of contents (last 24 months): JF, RFS, JFE, JFQA, MS, RAPS, RF, QF, JFEc, JFM, JBF, JEF.

## Tracker

| # | Paper | Status | What it does | Overlap with our claim | Differentiation | Threat level | Last checked |
|---|---|---|---|---|---|---|---|
| 1 | @JKMP2026 | RFS 2026 | ML + trading-cost-aware learning of weights; implementable frontier; economic feature importance | Objective dimension (iii); static nonlinear economic-loss learner | We nest it as a cell; add conditioning, uncertainty, interactions, mechanism tests | **High** | Sep 2026 |
| 2 | @SWZ2023 | MS 2026 (Crossref) | Deep parametric portfolio policies; robust to costs | Nonlinear economic-objective cell | Factorial attribution; state dependence; formal snooping control | **High** | Sep 2026 |
| 3 | @DMNU2020 | RFS 2020 | Linear PPP with TC; netting | Linear economic-loss cell | Nonlinear and conditional cells; netting attribution | Medium | Sep 2026 |
| 4 | @DMU2024 | JF 2024 | Conditional multifactor (volatility) net of costs | Conditioning x costs in low dimension | Stock-level high-dimensional conditioning; many states; mechanism tests | **High** (for G2) | Sep 2026 |
| 5 | @ACM2023 | MS 2023 | ML under economic restrictions | Motivation | We propose/attribute, not only diagnose | Low | Sep 2026 |
| 6 | @CHK2024 | SSRN WP | 1,056 ML designs; non-standard errors | Design-grid methodology | Our factors are economic ingredients evaluated net of costs with a common optimiser | Medium | Sep 2026 |
| 7 | @LAL2025 | EFM 2025 | 5,376 portfolios; design choices incl. portfolio construction | Design-grid methodology | Same as above | Medium | Sep 2026 |
| 8 | @NRRZ2024 | SSRN WP | Factor-zoo timing | State-variable predictability | Stock-level implementation with costs | Medium | Sep 2026 |
| 9 | @LMNS2025 | arXiv WP | NN forecast uncertainty; uncertainty-averse portfolios | Uncertainty dimension (iv) | Interaction with costs and conditioning | Medium-High (for iv) | Sep 2026 |
| 10 | @AHV2023 | SSRN WP | ML strategies net of costs and decay | Net-of-cost evaluation | Cost-aware learning, attribution | Medium | Sep 2026 |
| 11 | @BHHH2023 | JFDS 2023 | Horizon choice and ML alpha net | Horizon/turnover lever | Horizon is a robustness factor | Low-Medium | Sep 2026 |
| 12 | @CTWZ2021 | NBER WP | RL direct construction; transformer | Direct-objective learning | Controlled attribution; costs | Low-Medium | Sep 2026 |
| 13 | @CDS2020 | JFE 2020 | Liquidity-regime theory with costs | Economic prediction we test | We test it empirically | Low (supportive) | Sep 2026 |
| 14 | @CHSWZ2025 | arXiv WP | Non-stationarity vs complexity | Window/complexity choice | Robustness dimension | Low | Sep 2026 |
| 15 | @BLACKROCK2025 | Industry | AIM pipeline | Framing | Public data + inference | Low | Sep 2026 |
| 16 | @FRLUX2025 | arXiv WP (Oct 2025) | Friction-aware, **regime-conditioned** policy optimisation: costs inside the reward, inaction bands, 4 volatility-liquidity regimes, evaluated on a regime x cost grid with bootstrap CIs and multiple-testing corrections | **Direct overlap with gap G2** (conditioning x cost interaction) and with our robustness grid | It proposes one RL method; we identify which of four ingredients creates net value in a ~150-signal stock cross-section, with a nested factorial design. Its regime grid becomes a robustness parameterisation we cite and reuse | **High** | Sep 2026 |
| 17 | @VSC2026 | arXiv WP (Apr 2026) | Sparse (basis pursuit) versus dense ridgeless selection in high-complexity feature spaces; complexity pays through sparse discovery | Our new complexity ladder (levels A2/A3) | We test the claim inside a net-of-cost, implementable setting rather than gross SDF Sharpe | Medium | Sep 2026 |
| 18 | @AIPT2025 | WP (Oct 2025) [verify authors/venue] | Complexity helps only when the factor eigenvalue spectrum is diffuse | Our spectrum diagnostic | We use it as a mechanism test for when the complexity rung should pay | Low-Medium | Sep 2026 |
| 19 | @SPUR2026 | arXiv WP (2026) [verify authors] | Adaptive specification search yields significant backtests under a no-predictability null; proposes a falsification audit and multiplicity-adjusted inflation gap | Our credibility layer | We adopt it as a standard rather than compete with it; it raises the bar every rival submission must now clear | Low (supportive) | Sep 2026 |
| 20 | @LLG2025 | arXiv WP (Dec 2025) | Limits-to-learning gap: empirical fit understates true predictability | How we interpret small R2 and IC | Cited as a caveat; no overlap of claim | Low | Sep 2026 |
| 21 | @SPO2026 | arXiv WP (2026) | Decision-focused (SPO) portfolio learning inflates predictions and turnover; proposes clipping, rescaling, partial adjustment | Our economic-objective cells | We adopt the controls and report inflation as a diagnostic, since the objective axis is precisely what we are testing | Medium | Sep 2026 |
| 22 | @CPPS2024 | arXiv WP (2024, rev. 2025) | Conformal prediction intervals for portfolio selection | Our uncertainty level D2 | We use conformal as a calibrated input to a cost-aware optimiser and compare it against ensemble dispersion inside the factorial design | Medium | Sep 2026 |
| 23 | @SERT2025 | arXiv WP (May 2025) | Transformer variants for US large-cap pricing; high reported out-of-sample R2 | Our attention rung (A4) | Ours is a cross-sectional attention block inside a cost-aware comparison, not a standalone architecture claim | Low-Medium | Sep 2026 |
| 24 | @FMYY2025 | arXiv WP (Dec 2024, rev. 2025) | Cost-aware mean-variance with nonconvex penalties in large universes; S&P 500 and Russell 2000 | Our optimiser stage | Optimisation methodology, not attribution; we can cite it as an alternative cost-aware optimiser | Low-Medium | Sep 2026 |

| 25 | @SS2018 | FAJ 2018 | After-tax long/short factor investing: s1233 makes short gains ordinary, but shorting also supplies harvestable losses continuously, so a long/short book can be more tax efficient than its turnover implies | **Direct overlap with the whole after-tax layer** | It analyses given factor portfolios. Our object is whether the after-tax ranking of *learned combination designs* differs from the net-of-cost ranking, attributed across our four ingredients. If we cannot show the reordering, we have no after-tax contribution and should cite them and stop | **High** | Sep 2026 |
| 26 | @IM2012 | WP (Booth/NBER) | After-tax returns of value, momentum, size; momentum's short holding period is heavily penalised | Our proposed mechanism (holding-period composition) | They show it across *styles*; we test whether the same mechanism reorders *ML design choices*. Their result is our prior, and we must cite it as such rather than presenting it as a discovery | **High** (for the mechanism) | Sep 2026 |
| 27 | @BY2003 | FAJ 2003 | HIFO vs FIFO lot accounting materially changes after-tax outcomes | Our lot-method axis | We do not claim lot selection matters - they established that. We use it as a controlled axis and report whether it interacts with the model design | Medium | Sep 2026 |
| 28 | @ABY2001 | JWM 2001 | Value of systematic loss harvesting; the benefit decays as basis falls | Our harvesting results | The decay means a short sample overstates harvesting value. Constrains how we report: full-sample and by-subperiod, never a single annualised number | Medium | Sep 2026 |
| 29 | @CBLO2020 | FAJ 2020 | Tax-loss-harvesting alpha is highly state-dependent, concentrated in volatile down markets | Interacts with our conditioning axis | Suggests a genuine interaction (conditioning x tax) we can test; also a warning that a benign sample inflates it | Medium-High | Sep 2026 |
| 30 | @CON1983, @CON1984 | Econometrica 1983; JFE 1984 | Optimal realisation policy: realise losses, defer gains; short/long incentives | Our TAX_OPTIMAL lot rule and deferral term | Theory we implement, not a result we claim | Low (supportive) | Sep 2026 |
| 31 | @DSZ2001 | RFS 2001 | Capital-gains lock-in distorts optimal rebalancing | Our optimiser's embedded-gain penalty | Lifecycle consumption setting; the mechanism is theirs, the cross-sectional measurement is ours | Low-Medium | Sep 2026 |
| 32 | @COVER1991, @BK1999, @LH2014 | Math. Finance 1991; ML 1999; CSUR 2014 | Universal portfolios and online portfolio selection, with and without transaction costs | Our adaptive layer | These aggregate over **assets**. We aggregate over **models**, scored on after-tax return. If a paper appears that aggregates over models with a tax-aware reward, the adaptive contribution is gone | Medium | Sep 2026 |
| 33 | @HW1998, @FS1997, @LW1994, @VOVK1990 | ML/JCSS/I&C | Regret bounds for prediction with expert advice; fixed share tracks the best sequence | The rule we use | Cited, never claimed. Our contribution cannot be the algorithm | Low (supportive) | Sep 2026 |
| 34 | @PAGE1954, @GAMA2014 | Biometrika 1954; CSUR 2014 | CUSUM change detection; concept-drift adaptation with false-alarm control | Our drift-triggered refit | Cited, never claimed. The question we can own is whether drift-triggered refitting beats annual refitting *after tax* | Low (supportive) | Sep 2026 |

| 35 | @KS2024 | JWM Summer 2024 (SSRN 4584287) | Tax-aware long-short factor strategies realise cumulative net capital losses over 100% of initial capital within three years; the losses come mainly from **deferral of short-term gains on longs**, not elevated harvesting. Tax awareness shifts exposure **away from value and toward momentum** | **Pre-empts the naive form of our after-tax mechanism claim** | The value-to-momentum reordering under tax awareness is theirs (and @IM2012's) at the style level. We may only ask whether the same mechanism reorders **ML design ingredients** - nonlinearity, conditioning, objective, uncertainty. Must be cited as our prior, never presented as a finding | **High** | Sep 2026 |
| 36 | **@RABM2023** | J. Finance and Data Science 2023 (arXiv 2111.15365 v4) | **FULL TEXT READ 20 Sep 2026.** BOA over the **13 Gu-Kelly-Xiu models** (OLS+H, OLS3+H, PLS, PCR, ENet+H, GLM+H, RF, GBRT+H, NN1-NN5) on the **GKX dataset** (CRSP+Compustat, >30k US stocks, 94 characteristics, 1957-2017), aggregating **portfolio weights**, test 1987-2016. Benchmarks: best expert NN2 (SR 2.74), **uniform blend PtfUNI (2.56)**, fixed convex (2.28), rolling convex (2.60), PtfBOA (2.77), oracle (2.92). BOA's real edge is tail risk: max DD 8% vs 24% | **Nearly the whole adaptive layer.** They even benchmark the equal-weighted blend, and report a universe (bottom-1000 caps) where **PtfUNI beats BOA, SR 3.07**. Their claim: "first application of online expert aggregation for financial strategies" | **Two differences survive, and only two.** (1) **They never charge transaction costs** - zero occurrences of a cost model; turnover ~120%/yr is reported but not charged, so SR 2.77 is a gross number. (2) **Zero occurrences of "tax" in the paper.** Our reward is realised net-of-cost-and-tax return, and our experts are factorial cells rather than 13 arbitrary algorithms. We adopt their method and cite their result; the increment is the implementability of the reward | **High** | Sep 2026 (full text) |
| 37 | @SKP2018 | WP (SSRN 3264213) | Decomposes the tax benefit of relaxing long-only into **character** (s1233) and **deferral** components | Our after-tax decomposition | The decomposition we would otherwise have invented. Cite and reuse their vocabulary | Medium-High | Sep 2026 |
| 38 | @WINT2017 | Machine Learning 2017 [verify] | Bernstein Online Aggregation: second-order refinement of exponential weighting with improved regret | Our HedgeAggregator | BOA is **stronger** than the plain Hedge we implemented. Either adopt it or justify the simpler rule | Low (supportive) | Sep 2026 |
| 39 | Industry: AQR tax-aware long-short (~$150bn AUM) | Practitioner | Wash-sale-aware harvesting with correlated proxies, gain deferral, relaxed-constraint books | The **mechanics** of our tax layer | Industry standard. Our contribution can never be "we modelled taxes carefully" | n/a (context) | Sep 2026 |

| 40 | @HUANG2019 | arXiv 1907.12085 [verify: 1907.12093] (2019) | RL stock trading optimising **after-tax** return on an average tax basis; reports that **ignoring tax costs more than 62% of average portfolio return**, and that tax exceeds transaction cost in magnitude | **Owns our motivating premise.** "Taxes matter more than trading costs for an ML strategy" was published in 2019 | Average basis, not lot level - no HIFO, no s1091, no holding-period boundary; single-asset RL, not a cross-section; no attribution. We cite it in the motivation and never restate it as a finding | **High** (for the premise) | Sep 2026 |
| 41 | @PISH2026 | arXiv 2606.30997 + 2608.05255 (2026), **US Provisional Patent 64/101,198** | Three-phase foundation model for **tax-aware personalised** portfolio management: MoE actor-critic (PPO) with a tax-aware expert head, **position-level tax-lot tracking**, **wash-sale constraints**, tax-loss harvesting as a sampled objective, Chronos TSFM encoder, LoRA personalisation from brokerage history | **Owns the lot-level tax machinery inside an ML portfolio system.** More elaborate than ours | A personalised **retail product** driven by individual objectives and transaction history. Not cross-sectional signal combination, not ~150 characteristics, no attribution, no multiple-testing control. We cannot claim lot-level tax modelling in ML portfolios is novel | **High** | Sep 2026 |
| 42 | @CBFRC2026 | arXiv 2604.07880 (2026) | "The Corporate Bond Factor Replication Crisis": **18,128** factor series from **168 constructions per signal**; average non-standard error **0.31%/month vs a 0.22%/month premium** - methodology-induced spread exceeds the point estimate | Carries the NSE/multiverse method into a new asset class | **This is the template for the strongest reframing available to us** (see decision rule four). It is entirely **pre-tax**; nobody has run an NSE study after tax | Medium (as prior art) / **High as a model to follow** | Sep 2026 |

**Decision rule.** If a newly found paper performs a factorial attribution across at least two of our four ingredients, net of costs, on stock-level data, pause and re-scope: shift the contribution to G2/G3 (interaction + mechanism) or to international and uncertainty extensions.

**Second decision rule (after-tax layer, added Sep 2026).** If a paper is found that evaluates ML
signal combination after tax at the lot level, the after-tax contribution collapses to a robustness
section and the paper's claim reverts to the net-of-cost attribution. Check @SS2018 forward citations
before every submission. The after-tax layer is an *extension* of the claim, never a substitute for
it: if the net-of-cost attribution does not stand on its own, adding tax does not rescue it.

**Third decision rule (adaptive layer, added Sep 2026 after finding @RABM2023).** The adaptive layer
is now a **method section, not a contribution**. It may be described only as: "we adopt online expert
aggregation (@RABM2023, @HW1998) and change one thing - the rule is scored on realised after-tax net
return." Any sentence claiming novelty for online aggregation over ML models, or for beating the
individual members, is false and must be removed. Before the adaptive section is written, someone
**RESOLVED 20 Sep 2026: they do.** `PtfUNI`, a constant 1/K mixture, is an explicit benchmark, and on
small-cap stocks it beats BOA (SR 3.07 vs BOA). So the "aggregation versus equal-weighted blend"
comparison is theirs, not ours, and our pipeline printing that row is good practice rather than a
contribution. What survives: they charge **no transaction costs at all** and mention **taxes zero
times**, so "online aggregation scored on a reward the investor could actually keep" is still open.

**Fourth decision rule (framing, added Sep 2026 after the second research pass).** The after-tax
angle has narrowed: @HUANG2019 owns the premise and @PISH2026 owns the lot-level machinery, both in
the ML/RL applications literature rather than the asset-pricing literature. A direct fetch of the
arXiv q-fin.PM August 2026 listing found **zero** after-tax papers and **zero** attribution papers,
so our cell is still empty - but it is narrower than "nobody does after-tax ML".

The stronger available framing, and the one to test before committing, is the **after-tax
non-standard error**: given @CBFRC2026 shows methodology-induced spread can exceed the premium
itself pre-tax, does the spread across defensible *after-tax* design choices - lot method,
wash-sale treatment, harvest usability, investor regime, accounting basis, on top of the four model
ingredients - swamp the after-tax premium? That question is unoccupied, methodologically current,
uses the grid we have already built, and cannot be scooped by any single new method, because the
claim is about the distribution of results rather than about one model winning.

**Search backend caveat (Sep 2026).** The searches behind rows 35-39 were run with general web
search, not Perplexity academic mode or Parallel deep research (`parallel-cli` is not installed and
no API keys are configured on this machine). The negative result - "no academic paper evaluates
high-dimensional ML signal combination after tax" - rests on four general searches and is therefore
**weak**. It must be re-run against Google Scholar, SSRN full text, and the AQR/Parametric/Vanguard
publication lists before any novelty claim is committed to, because much of this field is
practitioner-published and poorly indexed. Raw results: `sources/research_20260920_*.md`.
