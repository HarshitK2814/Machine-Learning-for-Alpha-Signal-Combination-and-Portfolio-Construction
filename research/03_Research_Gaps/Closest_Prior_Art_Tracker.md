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
| 5 | @ACM2023 | MS 2023 | ML under economic restrictions | Motivation; **and the capacity headline directly** | We propose/attribute, not only diagnose; see row C1-C6 and section C3 | **High** (re-rated Oct 2026, was Low) | Oct 2026 |
| 6 | @CHK2024 | SSRN WP | 1,056 ML designs; non-standard errors | Design-grid methodology | Our factors are economic ingredients evaluated net of costs with a common optimiser | Medium | Sep 2026 |
| 7 | @LAL2025 | EFM 2025 | 5,376 portfolios; design choices incl. portfolio construction | Design-grid methodology | Same as above | Medium | Sep 2026 |
| 8 | @NRRZ2024 | SSRN WP | Factor-zoo timing | State-variable predictability | Stock-level implementation with costs | Medium | Sep 2026 |
| 9 | @LMNS2025 | arXiv WP | NN forecast uncertainty; uncertainty-averse portfolios | Uncertainty dimension (iv) | Interaction with costs and conditioning | Medium-High (for iv) | Sep 2026 |
| 10 | @AHV2023 | SSRN WP (= @AHV2025, row C3) | ML strategies net of costs and decay | Net-of-cost evaluation; **opposite sign on turnover reduction** | Cost-aware learning, attribution; scale-dependence of the sign (section C3) | **Severe** (re-rated Oct 2026, was Medium) | Oct 2026 |
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

---

# Capacity and friction literature (added 2026-10-09, read in full text)

**Why this section exists.** The tracker above was built for a tax paper. When the headline moved to
capacity (`docs/CANDIDATE_REFRAMING_CAPACITY.md`, `docs/STRATEGIC_ASSESSMENT_2026-10-09.md`) it
became known-incomplete in the dimension that matters. Rows C1-C6 below were added after obtaining
and reading the **full text** of each paper, not the abstract. Where a claim in the strategic
assessment turned out to be wrong against the actual paper, that is recorded in section C8.

**Provenance of these rows.** Full texts extracted to
`scratchpad/lit_txt/{ks2004,nmv2016,gp_capacity,cv_zoo,ahv_afa,ahv_slides,cv_zeroing}.txt`
from publisher- or author-hosted PDFs. @ACM2023 full text was **not** obtained (INFORMS paywall,
SSRN blocks automated download); its row is still abstract-level and is flagged as such.

## C1. Tracker rows

| # | Paper | Status | What it actually does (full text) | Overlap | Differentiation | Threat | Checked |
|---|---|---|---|---|---|---|---|
| C1 | @KS2004 Korajczyk & Sadka, "Are Momentum Profits Robust to Trading Costs?" | **JF 2004**, 59(3) 1039 | Break-even fund size for momentum under price impact. Impact from Breen-Hodrick-Korajczyk (**exponential, convex**) and Glosten-Harris (**linear**), scaled by *shares outstanding / market cap*, estimated on intraday data. EW/VW plus a derived **liquidity-weighted** strategy. Break-even where alpha = 0: **$4.5-5.0bn**; where *significance* disappears: **$1.1-2.0bn**. All figures stated **relative to Dec-1999 market cap**, = 0.043% of NYSE cap | **High.** Their break-even fund size is the closest published object to our capacity frontier | **Different construct** (see C2) - theirs is where *profit* vanishes, ours where the *mandate becomes infeasible* at target gross. Also: ours is concave (sqrt) impact, theirs convex/linear; ours scaled by **ADV**, theirs by **market cap**; ours non-US | **High** | Oct 2026 |
| C2 | @NMV2016 Novy-Marx & Velikov, "A Taxonomy of Anomalies and their Trading Costs" | **RFS 2016** | 23 anomalies net of effective spreads; capacity from **Kyle's lambda (linear)** price impact; capacity defined as new capital before the *latest-executing marginal* trader is unprofitable, **one-sided**, stated at Dec-2012. Buy/hold spread (enter on decile, exit on quintile) is the most effective mitigation. Capacities: size **$20-169bn**, gross profitability **$125-131bn**, value **$21-51bn**, momentum **$5.2-5.8bn**, PEAD **$0.8-3.0bn**, **high-frequency combo $0.38-0.44bn**, industry relative reversal **$0.18-0.53bn** | **Severe.** Their high-turnover capacities are **$180-530mn** - the same range as our $55/106/413mn | **This kills the "10-100x below US" claim** (C8.1). Surviving differences: definition, impact law, non-US, and that their mitigation is a *design choice* while ours is an *exogenous constraint* | **Severe** | Oct 2026 |
| C3 | @AHV2025 Azevedo, Hoegner & Velikov, "The Expected Returns on Machine-Learning Strategies" | SSRN 4702406 (Nov 2023, rev. Jun 2025); AFA programme | ML anomaly combination (OLS-Huber, ENET, FFNN, **LSTM**, ensemble) on ~320 Chen-Zimmermann anomalies, net of Chen-Velikov effective spreads, post-publication decay, post-decimalisation. Net returns to **1.42%/month (t=3.99)** for LSTM1; FF6 net alpha **1.20% (t=3.46)**; one-sided turnover **60-70%**; costs only **20-25 bps/month**. Tests NMV's mitigations (H2/H3/H4 holding periods, QUINTILE, BHS, universe filters): **turnover and costs fall but net performance does not improve** - the gross-return loss more than offsets the cost saving. Only H2 marginally helps | **Severe, and it is the live counterparty to our capacity channel** | They are a **marginal trader with no price impact** - costs are effective spreads, invariant to AUM. We are an **AUM-indexed trader** with square-root impact. Section C3 argues this is exactly why their sign is negative and ours positive | **Severe** | Oct 2026 |
| C4 | @GP2013 Garleanu & Pedersen, "Dynamic Trading with Predictable Returns and Transaction Costs" and capacity follow-ons | JF 2013 and follow-ons | Optimal trading toward a moving aim portfolio under quadratic costs; capacity expressed as dollar volatility sustainable at a target Sharpe; **Sharpe falls in invested capital** | High on the mechanism (costs vs signal decay trade-off) | They solve for the optimal *policy* given costs; we hold the policy fixed and vary the *constraint*. Their Sharpe-falls-in-scale is the opposite sign to our constrained book's Sharpe-rises-in-scale, which is the fact to explain | **High** | Oct 2026 |
| C5 | @CV2023 Chen & Velikov, "Zeroing in on the Expected Returns of Anomalies" | **JFQA 2023**, 58(3) 968 | Net expected returns of anomalies after data-mining and cost corrections; strongest anomalies net **~10bp** at best | Moderate - sets the bar for what "survives" means | We do not claim new anomalies; we measure where an existing signal's value goes | Moderate | Oct 2026 |
| C6 | @CFMZ2023 Cakici, Fieberg, Metko & Zaremba, "Machine Learning Goes Global" | **JEDC 2023**, 155:104725 | ML cross-sectional predictability in **46 markets**, 148 characteristics. Performance depends on firm size and recent-information availability; varies internationally with **number of listed firms** and **average idiosyncratic risk** | **Severe for the "non-US ML" framing.** They own international ML return predictability | They vary *breadth and arbitrage risk*; they do **not** do transaction costs at scale, capacity, AUM, price impact, or taxes. Our contribution must be the **friction** measurement, never "ML works outside the US" | **Severe (for framing)** | Oct 2026 |

Also updated: **row 5 (@ACM2023)** threat Low to **High**, and **row 10 (@AHV2023)** threat Medium to
**Severe**, because both were rated against the *attribution* claim and the headline has moved to
frictions. @ACM2023 remains abstract-level; obtain the full text before submission.

## C2. Our capacity frontier is not their break-even fund size

This distinction is the single most important thing to come out of reading C1 and C2, and it has to
be stated in the paper in one sentence or a referee will assume we rediscovered @KS2004.

* **@KS2004 and @NMV2016 define capacity where profit vanishes.** Break-even fund size is the AUM at
  which net alpha (KS) or the marginal trader's net profit (NMV) reaches zero.
* **Our frontier is where the mandate becomes infeasible.** `capacity_frontier = AUM_ref *
  ceiling_ref / gross_budget`: the largest AUM at which the **target gross of 2.0 is still
  attainable** under the ADV participation cap. It is an *implementability* bound, independent of
  whether the strategy is profitable there.

The two can be ordered: implementability binds **before** profitability, because a book can still be
profitable while unable to reach its mandated gross. Nobody reports the implementability bound, and
it is the one an allocator writing an investment management agreement actually faces. That is a
conceptual contribution, it is cheap to establish, and it is honest - but it also means **our number
is not comparable to theirs**, and C8.1 is the consequence.

## C3. The @NMV2016 / @AHV2025 dispute is where our mechanism belongs

The literature contains a genuine, unresolved disagreement about the **sign** of turnover reduction:

* **@NMV2016 (RFS):** the buy/hold spread is the most effective cost mitigation technique; reducing
  turnover **improves** net performance.
* **@KS2004 (JF):** liquidity-weighting - a deliberate tilt toward tradeable names - **raises**
  break-even fund size by a large factor.
* **@AHV2025:** the same mitigations significantly reduce turnover and trading costs but **do not
  improve net performance**, because the gross-return loss dominates. Their stated reason is that
  post-decimalisation costs are only 20-25 bps/month.

All three are US. The disagreement is not about data, it is about **where on the cost curve the
investor sits**, and that is what our design varies. With

    net Sharpe = (alpha_eff - kappa * G^0.5) / sigma

a constraint that cuts gross `G` and per-name turnover lowers `alpha_eff` roughly linearly and the
cost term as `G^0.5`. Tightening therefore helps **iff** `kappa` is large relative to alpha - and
`kappa` grows with `sqrt(AUM/ADV)`. @AHV2025 operate at `kappa` near zero (marginal trader, effective
spreads only, no AUM in the cost function at all), so for them mitigation can only destroy alpha.
We operate at large `kappa`, so for us it creates value.

**Our measured capacity channel is monotone in AUM, which is the dose-response this predicts:**

| AUM | Germany cost channel | Germany **capacity channel** |
|---|---|---|
| $100mn | -7.65 | **+4.97** |
| $1bn | -11.56 | **+8.77** |
| $10bn | -12.80 | **+10.02** |

(India at $1bn: cost -5.85, capacity **+4.41**.) The prediction that follows, and the reason for
`AMENDMENT_001D`, is that the capacity channel must **fall toward zero and turn negative** as AUM
drops far below the frontier - recovering @AHV2025's sign inside our own framework. That is the
crossover, and locating it is what makes this a mechanism rather than a measurement.

## C4. Claims we must NOT make (capacity additions)

- "First to measure the capacity of a trading strategy": @KS2004; @NMV2016; @GP2013.
- "First to show ML alpha does not survive realistic frictions": **@ACM2023**, in Management Science,
  one of our two primary target journals.
- "First to show ML alpha *does* survive frictions": @AHV2025 - and note they and @ACM2023 disagree.
- "First to show turnover reduction improves net anomaly performance": **@NMV2016** (buy/hold
  spread); @KS2004 (liquidity weighting). Our contribution is the *sign flip* and its scale
  parameter, never the positive sign itself.
- "First to apply ML to the cross-section outside the US": **@CFMZ2023** (46 markets, JEDC 2023).
- "First to report capacity in the low hundreds of millions for a high-turnover strategy":
  **@NMV2016** reports $180-530mn for its high-turnover strategies, in the US.
- "First to document ML design-choice dispersion": @CHK2024; @LAL2025 (and the 2026 EFM revision
  reports non-standard errors up to 5x standard errors) - relevant to our design-axis null.

## C5. What survives as ours, stated against the full texts

1. **The implementability frontier as a distinct object** (C2), reported for three non-US markets.
2. **The sign of the turnover-reduction effect flips with scale, and we locate the crossover** (C3).
   This adjudicates a live @NMV2016-vs-@AHV2025 disagreement instead of joining one side.
3. **Taxes measured and ruled out as second-order with a real lot-level engine across three
   statutory regimes.** None of C1-C6 contains a tax engine; @NMV2016 and @AHV2025 do not mention
   tax at all. Cost drag beats tax drag 5x (DEU) and 53x (IND).
4. **Three frictions priced in one framework on one set of signals.** C1-C6 each do one.

## C6. Comparisons that must be made turnover- and units-matched

Reading C1 and C2 showed three ways our headline comparison was not like-for-like. Before any
capacity number is published:

* **Match on turnover.** @NMV2016 capacities span $0.18bn to $169bn *within one paper*, ordered by
  turnover. Our strategies rebalance monthly. Compare only against their high-turnover panel.
* **Match on units.** @KS2004 reports Dec-1999 dollars, @NMV2016 Dec-2012 dollars, one-sided. Ours
  are 2009-2019. **Report capacity as a share of total investable market cap** as well as in dollars;
  @KS2004's $5bn is 0.043% of NYSE capitalisation, which is the comparable figure.
* **Match on the impact law.** @KS2004 is exponential-convex, @NMV2016 Kyle-linear, ours
  square-root-concave. @KS2004 state explicitly that if true impact is concave their results are
  conservative because they overestimate large-trade costs. So **our milder law cannot explain a
  smaller frontier** - which protects the finding, and should be said.
* **Match on cost-input coverage, which is ours alone and is a trap.** The promoted C6 prices only
  **65%** of Germany's signal-bearing cross-section over 2009-2019 (`adv_usd` is the binding field)
  against essentially 100% of India's. Document 13 requirement 2 makes an uncertified
  security-month **non-tradeable** and prohibits imputation, so Germany's investable universe is
  ~246 names a month, not the ~382 that carry a signal
  (`docs/NON_TRADEABLE_TREATMENT.md`). Any exhibit that forms portfolios on the *signal-bearing*
  cross-section rather than the *investable* one silently gives uncovered names zero cost in an
  uncapped book and a zero cap in a capped one - **both of which push a capacity channel downward,
  and only in Germany.** That is an alternative explanation for any Germany-versus-India contrast
  and must be controlled before such a contrast is reported. The wedge tool's
  `--require-cost-inputs` flag exists for exactly this and the compliant ladder is the one to
  quote. @KS2004 and @NMV2016 do not face this because US CRSP/TAQ coverage is near-complete; it is
  a hazard specific to non-US work and is worth a methods paragraph of its own.

## C7. Search protocol additions

4. Forward citations of **@KS2004**, **@NMV2016**, **@GP2013**, **@ACM2023**, **@CFMZ2023**.
5. Queries: "capacity" AND ("anomaly" OR "factor") AND ("price impact" OR "break-even fund size");
   "participation constraint" AND portfolio; "ADV" AND capacity AND backtest; "machine learning"
   AND capacity AND ("international" OR "non-US"); "turnover reduction" AND "net performance".
6. Author pages: Velikov (he has three papers in this space and is a co-author on the strongest
   counter-argument), Novy-Marx, Korajczyk, Zaremba, Avramov.

## C8. Corrections to the strategic assessment forced by these full texts

**C8.1 - the "10-100x below US estimates" claim is wrong and must be withdrawn.**
`STRATEGIC_ASSESSMENT_2026-10-09.md` section 4.1 says our $55mn/$106mn/$413mn frontiers are "10x to
100x smaller" than published US estimates, citing @KS2004's $2-5bn for momentum and $50-170bn for
size/value. Those are **low-turnover** strategies. @NMV2016 Table 7 reports, in the US, **$0.38-0.44bn
for a high-frequency combination** and **$0.18-0.53bn for industry relative reversal**. Our
monthly-rebalanced ML books belong in that panel. Turnover-matched, **Japan's $413mn is inside the US
range**, Germany's $106mn is roughly 2-4x below it and India's $55mn roughly 3-10x below it - and even
that gap is confounded by the three mismatches in C6. The claim as written would not survive a
referee who owns @NMV2016, and one of its authors is a co-author of @AHV2025.

**C8.2 - "our 42-row tracker contains none of them" is wrong.**
@ACM2023 is row 5 and @AHV2023 is row 10. What was missing is the **capacity** literature
(@KS2004, @NMV2016, @GP2013, @CV2023) and the **international ML** literature (@CFMZ2023). The
real failure was not absence but **mis-rating**: both were scored against the attribution claim at
Low and Medium threat, and nobody re-scored them when the headline moved.

**C8.3 - what gets stronger.** The @NMV2016-vs-@AHV2025 disagreement (C3) is a better home for our
mechanism than "capacity binds" ever was, because it is an open question with named parties rather
than occupied ground, our comparative static answers it in one line, and our design already contains
the dose-response that identifies the answer.

## C9. Tax-timing and tax-aware construction (added 2026-10-09, ABSTRACT-LEVEL ONLY)

Both rows below were confirmed from abstracts and publisher listings, not full text. Read before
submission.

| # | Paper | Status | What it does | Overlap | Differentiation | Threat |
|---|---|---|---|---|---|---|
| C7 | @DLLY2026 Dai, Lei, Liu & Yang, "Optimal Tax Timing with Transaction Costs" | **Management Science**, online Feb 2026, DOI 10.1287/mnsc.2023.03118 | Dynamic portfolio model combining capital-gains tax, transaction costs and **year-end taxation**. Tiny transaction costs substantially delay loss realisation, far more than gain realisation; offered as an explanation for the disposition effect. Earlier working paper NUS RMI 2020-04; same group's RFS 2015 paper handles asymmetric long/short-term rates | **High on the joint-friction idea.** Combining taxes and transaction costs, even dynamically, is not a novelty claim | Theory of one investor's timing problem. Ours is an empirical evaluation of ML signals under dated, jurisdiction-specific statutes and an AUM-indexed impact model; they do not price market capacity | **High** |
| C8 | @MKBA2021 Moehle, Kochenderfer, Boyd & Ang, "Tax-Aware Portfolio Construction via Convex Optimization" | **J. Optimization Theory and Applications** 189(2) 364-383, May 2021; arXiv 2008.04985 | Adds tax liability to Markowitz construction and outputs a trade list that includes **which tax lots to sell**; handles wash sales; the problem is nonconvex but convex once buy/sell is fixed per asset, solved by a custom relaxation | **High on the optimiser.** Tax-lot-aware convex construction is prior art | Our `tax_aware` optimiser is a **tool**, not a contribution. It is myopic and static-ledger; theirs handles the buy/sell nonconvexity | **High** |

**Consequence.** The framing "tax-aware implementable frontier" cannot rest on the optimiser being
new. If a tax-aware arm is built it is a bounded experiment with a pre-agreed stopping rule, and the
paper's contribution stays the empirical, statute-specific, multi-jurisdiction evaluation.
