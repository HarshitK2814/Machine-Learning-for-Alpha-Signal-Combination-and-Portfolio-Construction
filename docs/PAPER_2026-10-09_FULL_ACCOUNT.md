# Where Does Machine-Learning Alpha Go? Costs, Capacity and Taxes in Three Non-US Equity Markets

**A complete account of the project as of 2026-10-09, 17:10 IST**

Workstream B (Harshit) · drafted for internal use and for Absar (workstream A, data) and Maham
(workstream C, statistics)

---

## How to read this document

This is written in the shape of a paper, but it is **not** a submission draft. It is the full
record: what we set out to do, what the literature already owns, exactly what we built, every
result that survived, **every result that did not and why**, and what remains. Section 8 is the
honest ledger of nine retractions and corrections (8.1-8.9), seven of them arising today. Section 12 is what is left to do, why each
item matters, and how each could change the paper.

Numbers are stated with the sample and specification they come from. Where a quantity has been
withdrawn it appears struck through with the reason, rather than deleted, because the record of what
we believed and on what basis is part of the paper's credibility.

---

## 1. Abstract

For an institutional investor in a mid-size equity market, three frictions compete to consume
machine-learning alpha: transaction costs, liquidity capacity, and taxes. We measure all three in
one framework, on one set of signals, across **Germany, India and Japan** — three jurisdictions
chosen because their statutory capital-gains architectures differ in a way that creates a natural
placebo design. We evaluate 16 model cells in a 2×2×2×2 factorial plus five baselines, over a
frozen 132-month window (2009-2019), with a lot-level tax engine, a square-root price-impact cost
model indexed to assets under management, and a full constraint set including an ADV participation
cap.

**The framing fact, which conditions everything below:** at a $1bn mandate **no country's
net-of-cost Sharpe is statistically distinguishable from zero** (t = +0.53 Germany, +0.82 India,
+0.18 Japan). Machine-learning alpha, implemented at institutional scale in these three markets
under a realistic AUM-indexed cost model, is **not demonstrably positive**. That corroborates
@ACM2023 in markets they did not study, and it is the backdrop against which the four results below
must be read: they are statements about **channels and differences**, not about a profitable
strategy.

Four results survive.

1. **The ADV participation constraint improves net risk-adjusted performance, and the improvement
   is monotone in how hard the constraint binds.** Measured at the largest mandate where the
   uncapped comparison book is still solvent (§8.8), and on the pipeline's own accounting of both
   books (§8.9), the capacity channel is **+6.80** (Germany, $100mn), **+3.19** (India, $30mn) and
   **+6.92** (Japan, $1bn) Sharpe points (the wedge tool gave +7.63 / +3.64 / +6.68, with
   inference t = +10.21 / +5.00 / +11.01); Japan's comparison book is solvent through $10bn. Beyond those rungs
   the German and Indian uncapped books are bankrupt, and the larger figures quoted elsewhere are
   not interpretable as performance gains. Japan is a **pre-registered out-of-sample
   confirmation**. The effect is zero where
   the constraint is slack and there is no mandate size at which it meaningfully hurts, at the
   registered cost calibration. It survives a six-fold sweep of the impact
   coefficient (value-weighting was run on the PRE-FIX signal-bearing universe only; the compliant re-run (§12.3) has not been done, so robustness to weighting is unconfirmed on the universe the headline uses), a level-matched switch to the Kyle-linear impact law our closest competitor
   prefers, and familywise correction across cells.

   **What the improvement improves must be stated plainly, because the magnitude invites
   misreading.** The capped book is not good; it is **not catastrophic**. Germany's decile book at
   $1bn goes from a net Sharpe of **−9.597 uncapped to −0.675 capped** — the constraint rescues the
   strategy from disaster, not into profit. On the **optimised** book the level is +0.128, which
   finding 2 shows is **not distinguishable from zero**. So the capacity channel is a large, robust,
   significant **difference between two books, neither of which is significantly profitable**. That
   is the finding; "+8.9 Sharpe points" quoted alone is not.
2. **No strategy is distinguishable from zero net of costs, and the capital-gains statute decides
   whether taxes then measurably erode it further.** At $1bn no country's net Sharpe is
   significant (t = +0.53 Germany, +0.82 India, +0.18 Japan). The **tax channel**, however, is
   significant in both **flat-rate** jurisdictions — Germany **−0.1363 (t = −4.67)**, Japan
   **−0.1373 (t = −4.99)**, 3 of 8 cells under Holm each — and **not** significant under India's
   long-term exemption (−0.0054, t = −1.93, 0 of 8) **on the optimised book**. **On the executable
   decile book the contrast is weaker than that**: Germany −0.070 (t −3.55), Japan −0.170 (t −3.67),
   India −0.009 (t −2.14), so the flat regimes are 8–19× larger in magnitude than India but India
   is itself borderline-significant, and the two placebos differ by a factor of 2.4 rather than
   agreeing to 1% (§8.9). The robust statement is the **magnitude ordering by statute type**, not
   the exact match or the clean insignificance. It is not the rate (Germany's is 30% above
   Japan's); it is whether the law provides a long-term category at all. An investor cannot grow out of it:
   Germany's tax bill falls **25-fold** from $100mn to $10bn while the risk-adjusted drag stays
   flat at −0.11 to −0.16.
3. **The statutory wedge determines whether the holding-period channel can exist at all.**
   `lt_share_of_gains` is **identically 0.0000** under both flat-rate regimes (Germany 26.375%,
   Japan 20.315%) and **0.5928** in India, whose statute creates a long-term category. Two
   independent placebos, one treatment. Given the wedge, the drag *level* is ordered by **turnover,
   not by the rate**: Japan's rate is 23% lower than Germany's and its drag is 80% higher, because
   it turns over 2.1× as fast.
4. **No machine-learning design axis is detectable at this power.** On the **capped decile-spread
   book in Germany and India**, 0 of 42 axis-rungs (14 AUM rungs x 3 axes) are significant in each
   market, with paired HAC inference and Holm correction. The minimum detectable effect at 80% power
   with 132 months is 0.25-0.81 Sharpe points depending on axis and market, so the null excludes only
   effects of roughly a quarter of a Sharpe point or more. **Scope limits:** it was not measured for
   Japan or on the optimised book at every rung. In a single-AUM check on the **optimised** book at
   $1bn, Japan's *conditioning* axis is t = +2.84 (effect +0.515; p = 0.0045 unadjusted, 0.014 after
   Holm within Japan, 0.041 after Bonferroni across the nine axis tests) and the other eight axis
   tests are not significant. That observation is **exploratory, not pre-specified and unreplicated:
   it is disclosed, not claimed** (§6.4). The signals themselves carry information coefficients with
   t up to +10.4.

A fifth result is methodological and arose from our own failure. A **35-percentage-point asymmetry
in cost-input coverage** between two panels of the same study manufactured a highly significant
(t = −6.10), monotone, theoretically coherent cross-country contrast that **survived two robustness
checks**, including satisfying a scaling law the mechanism predicted. We retract it and document the
checks that catch it (§9, §10).

---

## 2. Introduction

### 2.1 The question

Gu, Kelly and Xiu (2020) and successors established that machine learning extracts economically
large predictability from the cross-section of equity returns. A second literature asks whether any
of it is implementable. Those two literatures are overwhelmingly **US** and they mostly measure a
**marginal trader**: costs are effective spreads, invariant to how much money is being run.

An allocator does not face that problem. They face a specific mandate size in a specific market
with specific statutory taxes, and want to know which friction consumes the alpha first. That is
the question here, and it motivates three design choices that distinguish this study:

* **Everything is indexed to AUM.** Costs include a square-root price-impact term that scales with
  mandate size, so every quantity is reported as a function of money managed rather than at an
  unstated scale.
* **Three jurisdictions with genuinely different tax architecture**, which lets statute rather than
  specification do the identifying work for the tax channel.
* **A real lot-level tax engine**, not a flat haircut — HIFO selection, holding-period rules dated
  to the statute, and a reform event (India's §112A, 2018-04-01) spanned by a dated engine.

### 2.2 What we set out to do, and where we ended

The project's original claim (`research/03_Research_Gaps/PUBLICATION_READINESS_AUDIT.md`,
September 2026) was a **cross-country tax-architecture design**: the statutory short-versus-long
wedge Δ = `cgt_short − cgt_long` is 0.000 in Germany and Japan (flat rates) and 0.150 in India
falling to 0.050 at the 2018 reform, giving a dose-response with two placebos written into law. The
audit called this "the only uncontested ground we hold" and said "it should be the paper".

**That design was run and it failed twice** (§8.1, §8.2). What replaced it was a capacity finding,
and the capacity finding then had to be narrowed twice more (§8.3, §8.5). The paper that remains is
the one in §1: a measurement of where ML alpha goes, with the tax machinery serving as the
instrument that *rules the tax channel out as a channel* while showing it is nevertheless decisive
for survival.

We state this history because seven of the nine entries in §8 happened in a single day, and
because the shape of the errors (§9) is itself one of the paper's contributions.

### 2.3 Contributions, stated against what is already published

| contribution | why it is not already owned |
|---|---|
| Capacity channel measured as an **AUM-indexed dose-response** over seven orders of magnitude, in three non-US markets, with standard errors | @NMV2016's price impact is **Kyle-linear**, so their cost is linear in invested dollars, their capacity is a single break-even point and their "SR/$B" is a constant slope. They report one number per strategy. We report the curve and show it is strongly nonlinear |
| **Implementability frontier** — the AUM at which the mandate's target gross becomes infeasible | @KS2004 and @NMV2016 both define capacity where **profit** vanishes. Implementability binds earlier and is what an allocator writing an IMA faces. Nobody reports it |
| Tax channel measured with a **lot-level engine across three statutory regimes**, and shown second-order as a channel but decisive for survival | None of @KS2004, @NMV2016, @GP2013, @CV2023 contains a tax engine. @NMV2016 and @AHV2025 do not mention tax |
| **Turnover, not the statutory rate, orders the cross-country tax drag** | Requires three jurisdictions to separate the two orderings. The tax-aware literature (@SS2018, @IM2012, @HUANG2019) is single-jurisdiction |
| **Design-axis null with power**, across 14 mandate sizes and two books | @CHK2024 and @LAL2025 document design dispersion gross; nobody reports its detectability on an executable book as a function of scale |
| **Coverage-asymmetry hazard**, demonstrated with a worked false positive | New, and specific to non-US work where coverage is never complete |

### 2.4 What we explicitly do not claim

* Not "first to measure strategy capacity" — @KS2004, @NMV2016, @GP2013.
* Not "first to show ML alpha is fragile to frictions" — **@ACM2023, in Management Science**, one
  of our two original target journals.
* Not "first to show it survives frictions" — @AHV2025, who disagree with @ACM2023.
* Not "first to show turnover reduction can help" — @NMV2016's buy/hold spread; @KS2004's
  liquidity weighting, which moves momentum's break-even fund size from roughly $1mn to over $5bn.
* Not "first to apply ML outside the US" — **@CFMZ2023, 46 markets, JEDC 2023**.
* Not an adjudication of the @NMV2016-versus-@AHV2025 disagreement. **We never observe the regime
  in which the constraint hurts** (§6.2), so we cannot speak to it.

---

## 3. Related work

### 3.1 Capacity and price impact

Read in full text on 2026-10-09; the tracker rows are
`research/03_Research_Gaps/Closest_Prior_Art_Tracker.md` §C1.

**@KS2004 — Korajczyk & Sadka, "Are Momentum Profits Robust to Trading Costs?", JF 59(3) 1039.**
Break-even fund size for momentum under price impact, from intraday data. Two impact models:
Breen-Hodrick-Korajczyk (**exponential, convex**) and Glosten-Harris (**linear**), both scaled by
*shares outstanding / market capitalisation*. Equal-, value- and **liquidity-weighted** variants.
Break-even where alpha = 0: **$4.5–5.0bn**; where significance disappears: **$1.1–2.0bn**; value-
weighted **$3bn**; and for equal-weighted/low-volume variants on the full NYSE/AMEX/Nasdaq sample,
negative alpha at "merely **$1 million**". All figures relative to December-1999 market
capitalisation — $5bn is **0.043%** of NYSE capitalisation, which is the comparable statistic.
**Their range within one paper is a factor of 5,000, driven by the weighting scheme**, i.e. by how
much the strategy tilts toward liquid names. They note explicitly that if true impact is concave,
their results are conservative.

**@NMV2016 — Novy-Marx & Velikov, "A Taxonomy of Anomalies and their Trading Costs", RFS 2016.**
23 anomalies net of effective spreads; capacity from **Kyle's lambda (linear)**; capacity defined as
new capital before the *latest-executing marginal* trader is unprofitable, **one-sided**, stated at
December 2012. The buy/hold spread (enter on decile, exit on quintile) is "the most effective" cost
mitigation. Capacities: size **$20–169bn**, gross profitability **$125–131bn**, value **$21–51bn**,
momentum **$5.2–5.8bn**, PEAD **$0.8–3.0bn**, **high-frequency combination $0.38–0.44bn**, industry
relative reversal **$0.18–0.53bn**. Market capitalisation explains >70% of cross-sectional variation
in log lambda with slope −0.98. Their footnote 9 **argues against concave impact functions** on
endogeneity grounds. They also argue equal-weighted anomaly results are "misleading" net of costs
because they load on small, expensive names.

**@AHV2025 — Azevedo, Hoegner & Velikov, "The Expected Returns on Machine-Learning Strategies",
SSRN 4702406.** ML combination (OLS-Huber, ENET, FFNN, **LSTM**, ensemble) over ~320
Chen-Zimmermann anomalies, net of Chen-Velikov effective spreads, post-publication decay and the
post-decimalisation era. Net returns to **1.42%/month (t = 3.99)** for LSTM1; six-factor net alpha
**1.20% (t = 3.46)**; one-sided turnover **60–70%**; costs only **20–25 bps/month**. They test
@NMV2016's mitigations and find turnover and costs fall but **net performance does not improve**,
because the gross-return loss dominates. **They are a marginal trader: their cost model contains no
AUM term at all.**

**@GP2013 — Gârleanu & Pedersen.** Optimal trading toward a moving aim portfolio under quadratic
costs; capacity as dollar volatility sustainable at a target Sharpe; **Sharpe falls in invested
capital**.

**@CV2023 — Chen & Velikov, "Zeroing in on the Expected Returns of Anomalies", JFQA 58(3) 968.**
Net expected anomaly returns after data-mining and cost corrections; the strongest net ~10bp.

**@ACM2023 — Avramov, Cheng & Metzker, Management Science 69(5) 2587.** ML return predictability
collapses under realistic frictions: high turnover, extreme positions, and restrictions. **Full
text not obtained** (paywall; SSRN blocks automated retrieval) — this row remains abstract-level and
must be read before submission.

### 3.2 The live disagreement, which we engage but do not settle

@NMV2016 and @KS2004 find turnover reduction and liquidity tilting **help**; @AHV2025 find the same
mitigations **do not**. All three are US and all three are internally consistent. Both positions
follow from

    net Sharpe = (alpha_eff - kappa * G^0.5) / sigma ,     kappa ~ sqrt(AUM / ADV)

@AHV2025 sit at `kappa ≈ 0`. Our data lies entirely on the other side: we observe only the regime
where the constraint helps (§6.2), so we **corroborate** @NMV2016 and @KS2004 and are silent on
@AHV2025. An earlier draft of this project claimed to adjudicate; that claim is retracted (§8.3).

### 3.3 International ML, and why "non-US" is not our contribution

**@CFMZ2023 — Cakici, Fieberg, Metko & Zaremba, "Machine Learning Goes Global", JEDC 155:104725.**
ML cross-sectional predictability in **46 markets** with 148 characteristics. Performance depends on
firm size and recent-information availability and varies with the number of listed firms and average
idiosyncratic risk. They do **not** do transaction costs at scale, capacity, AUM, price impact or
taxes. So international ML predictability is theirs; the **friction** measurement is ours.

### 3.4 ML design dispersion

@GKX2020 (macro interactions), @CPZ2024, @DMU2024 (conditional, net of costs), @JKMP2026
(trading-cost-aware learning, RFS 2026), @SWZ2023 (deep parametric policies), @DMNU2020 (linear
PPP), @LMNS2025 (forecast uncertainty), @CHK2024 (1,056 designs, non-standard errors), @LAL2025
(5,376 portfolios; its 2026 EFM revision reports non-standard errors up to 5× standard errors).
Our factorial has **8 prediction cells**, which is the binding power constraint on §6.4.

### 3.5 Tax

@SS2018 (closest after-tax work; long/short factor portfolios, §1233, harvesting supply),
@IM2012 (momentum is tax-inefficient), @BY2003 (HIFO), @KS2024 (gain deferral rather than loss
harvesting; tax awareness tilts toward momentum), @HUANG2019, @PISH2026 (lot-level machinery in the
ML/RL applications literature), @CBLO2020. None of this literature prices capacity.

---

## 4. Data

Supplied by workstream A (Absar), production-promoted, contract-validated.

| | Germany | India | Japan |
|---|---|---|---|
| universe rows (full span 1990-01..2020-12) | 273,068 | 755,806 | 1,254,688 |
| in-universe rows, 2009-2019 | 50,004 | 44,233 | 247,412 |
| **signal-bearing** names/month (median) | 382 | 349 | 1,708 |
| **investable** names/month (median) | **246** | **348** | **1,705** |
| cost-input coverage, 2009-2019 (mean / median / min) | **0.651 / 0.654 / 0.517** | 0.991 / 1.000 / 0.004 | 0.998 / 1.000 / 0.941 |
| statutory short-term rate | 26.375% | 15.0% | 20.315% |
| statutory wedge Δ | **0.000** | **0.150 → 0.050** (2018-04-01) | **0.000** |

**Contracts.** C1 universe, C2 signals (**168 characteristics**), C4 targets, C6 cost inputs
(spread, daily volatility, USD ADV), C14 tax regimes. Evaluation window frozen at
**2009-01-01..2019-12-31, 132 months** (India's tax panel is 131 months; its January-2009
cost-input coverage is 0.004).

**Cost-input coverage is the single most consequential data fact in this document.** `adv_usd` is
the binding field, and Germany carries only **65.1%**. Document 13 requirement 2 makes an
uncertified security-month **non-tradeable** and prohibits imputation
(`docs/NON_TRADEABLE_TREATMENT.md`), so Germany's *investable* universe is 246 names a month, not
382. Germany is the only panel affected; India and Japan are at or above 99%. §8.3 is what happened
when an exhibit ignored this.

**Breadth cap.** `--max-names 600` (amendment 001B), verified bit-identical for Germany and India
(whose worst months are 438 and 546) and binding only on Japan. Declared because Japan's 1,708
names would otherwise make it a different experiment from the other two.

---

## 5. Methodology

### 5.1 Pipeline

```
02_train_models      16 factorial cells + 5 baselines -> scores / weight proposals
04_construct_portfolios   constrained optimisation at a given AUM -> weights
dev_backtest         realised returns, turnover, costs
06_after_tax_eval    lot-level tax engine -> after-tax returns
```

Plus the experiment tools in §13.

### 5.2 The frozen contract

| parameter | value |
|---|---|
| gross exposure | **2.0**, dollar-neutral |
| per-name weight cap | **1%** |
| **ADV participation cap** | **5%** |
| beta / industry caps | 0.05 / 0.02 |
| target annual volatility | 10% |
| commission | 1 bp |
| impact coefficient `k` | **1.0** (Grinold-Kahn) |
| impact power | **1.5** |
| borrow | modelled flat 1% p.a. proxy |
| reference AUM | **$1bn** |
| solver order | CLARABEL, ECOS, SCS |

**Cost model.** Per name, in return units:

    cost_i = (spread_i/2 + commission) * |dw_i|  +  k * sigma_d,i * sqrt(AUM/ADV_i) * |dw_i|^1.5

The impact term is a **square-root (concave) per-unit** law, total cost `~ Q^1.5`. This is the
choice @NMV2016 dispute and @KS2004 endorse; §6.2.4 tests it.

**Participation cap.** `|w_i| <= 0.05 * ADV_i / AUM`. This is the object the paper is about.

### 5.3 The factorial

16 cells, 2×2×2×2:

| axis | levels |
|---|---|
| representation | **L** linear / **N** nonlinear |
| conditioning | **S** static / **C** state-conditional |
| loss | **P** prediction / **E** economic (cost-aware) |
| uncertainty | **0** none / **U** ensemble shrinkage |

**The economic-loss arm is not a competent implementation** and is excluded from every headline.
It trains on net-of-cost utility with a `- cost(w_t - w_{t-1})` term so it should trade *less*;
instead it trades **1.8×** more and has **negative gross Sharpe before any costs**
(`docs/ECONOMIC_ARM_CAPABILITY_GAP.md`). Maham owns the debug-versus-flag ruling
(`docs/handoff/19_...` §7). Until then all headline numbers are **prediction cells only (8)**, and
§8.4 is what happened when they were not.

### 5.4 Pre-registration

PLAN_001, fingerprint `cae8140b7e2b7ee4`, N = 64 scenarios. Amendments:

| amendment | content | status |
|---|---|---|
| 001A | — | awaiting Maham's countersignature |
| 001B | universe breadth cap N = 600 | awaiting countersignature; verified bit-identical for DEU/IND |
| 001C | capacity hypothesis H-CAP, Japan as confirmation sample | awaiting countersignature |
| **001D** | capacity channel sign flip H-FLIP, five predictions for Japan | **RETRACTED same day** (§8.3); awaiting countersignature as retracted |

Japan was held as a genuine confirmation sample: at the time 001C and 001D were declared,
`outputs/` contained **no Japanese portfolio, weights-index entry or stage-04 artefact of any
kind**, verified and recorded in the commit messages. `tools/score_amendment_001d.py`, which scores
the predictions mechanically with every threshold hard-coded, was also committed **before Japan
reported**.

### 5.5 Inference

* **`sharpe_difference_test`** (new, 2026-10-09): Ledoit-Wolf studentized stationary bootstrap for
  a difference of Sharpe ratios on **paired** series. The capacity channel is
  `SR(net capped) − SR(net uncapped)` on the *same* months from the *same* scores, so the series are
  strongly dependent and an unpaired comparison would be badly oversized. Studentized with the
  Lo (2002) influence-function expansion so one Newey-West standard error absorbs both the serial
  and the cross dependence. 12 unit tests, including that the paired SE is strictly smaller than
  treating the series as independent.
* **Holm-Bonferroni** across the 8 cells, not `romano_wolf`: that function studentizes the **mean**
  of each series, so aiming it at return differences would test whether the cap raises mean
  *return* — a different and oppositely signed question, since the cap cuts gross.
* **Crossover intervals**: stationary bootstrap over months, one shared index across AUM rungs to
  preserve cross-rung dependence, zero interpolated in `log10(AUM)`. Replications with no sign
  change are **counted, not dropped**.
* Pre-existing layer: deflated Sharpe (Bailey-López de Prado), PBO-CSCV, Romano-Wolf StepM,
  Hansen SPA, Newey-West HAC, Lo (2002).

### 5.6 The two books, and why both are needed

* **Uncapped decile spread** — rank on the score, long the top decile, short the bottom,
  scaled to gross 2.0. What a signal-level paper reports. Not executable.
* **Participation-capped decile spread** — the same book with `|w_i|` clipped to the ADV cap.
  The first executable object.
* **Optimised book** (stage 04) — full constraint set, risk model, frozen sleeve.

The capacity channel is the difference between the first two. It cannot be measured on the
optimised book, because **the uncapped optimisation cannot be constructed at all** — two backtest
refusals, and the frozen sleeve is endogenous to the whole book
(`docs/RESULTS_CAPACITY_2026-10-09.md`). That limitation is itself a finding and it is why §6.5
compares orders of magnitude rather than a decomposition that sums.

---

## 6. Results

All capacity results are on the **compliant** (investable-universe) ladder,
`--require-cost-inputs`, prediction cells, composite portfolio (one equal-weighted book of the 8
cells), 132 months (India 131).

### 6.1 The capacity frontier (implementability)

`capacity_frontier = AUM_ref × ceiling_ref / gross_budget`: the largest AUM at which the target
gross of 2.0 remains attainable under the ADV cap.

| | eligible names (median) | attainable gross at $1bn | **frontier** | range across months |
|---|---|---|---|---|
| Germany | 246 | 0.213 | **$106.3mn** | $76.5–142.3mn |
| India | 348 | 0.110 | **$55.0mn** | $0.007–98.2mn |
| Japan | 1,705 | 0.825 | **$412.7mn** | $223.3–691.9mn |

This is **not** @KS2004's or @NMV2016's break-even fund size, which is where *profit* vanishes.
Implementability binds earlier and is the constraint an allocator actually writes into a mandate.
The two are not comparable, which is the subject of retraction §8.2.

### 6.2 The capacity channel

#### 6.2.1 Three markets

Channel = `SR(net, capped) − SR(net, uncapped)`, paired studentized bootstrap, 2,000 replications,
block 6.

| AUM | Germany | t | India | t | Japan | t |
|---|---|---|---|---|---|---|
| $100k | +0.068 | +1.22 | **+0.264** | +4.63 | −0.001 | −1.14 |
| $300k | **+0.298** | +2.43 | **+0.478** | +4.36 | +0.009 | +1.48 |
| $1mn | **+0.917** | +3.98 | **+0.880** | +4.40 | +0.042 | +2.72 |
| $3mn | **+1.890** | +5.53 | **+1.536** | +4.66 | **+0.132** | +3.84 |
| $10mn | **+3.646** | +7.05 | **+2.534** | +4.78 | **+0.403** | +6.41 |
| $100mn | **+7.634** | +10.21 | +4.591 † | +5.31 | **+2.693** | +10.40 |
| **$1bn** | +8.922 † | +11.11 | +5.693 † | +5.70 | **+6.681** | **+11.01** |
| $10bn | +9.256 † | +11.43 | +5.967 † | +5.88 | **+7.151** | +7.06 |

* Significant at 5% over all rungs: 13 of 14 German, 14 of 14 Indian, 11 of 14 Japanese. **Over
  solvent rungs only: 10 of 11 German, 10 of 10 Indian, 11 of 14 Japanese** (committed solvency table).
* † **Not interpretable as performance gains**: the uncapped comparison book is insolvent at these
  rungs (Germany from $300mn, India from $100mn; Japan never), see §8.8. The pipeline's own accounting
  of both books gives, at the largest solvent rung, Germany $100mn **+6.80**, India $30mn **+3.19**,
  Japan $1bn **+6.92** (§8.9), which supersede the wedge-tool values in this table for those rungs.
  The t statistics and Holm counts below include † rungs.
* **8 of 8 cells survive Holm** from $1mn (DEU), $300k–$10mn (IND, 8/8) and $8mn (JPN) upward.
* Composite gross decile Sharpe: Germany **+2.305**, India **+1.197**, Japan **+1.278**.

**Japan is the pre-registered out-of-sample confirmation** of `AMENDMENT_001D` prediction D2,
declared and scored by code committed before any Japanese portfolio existed.

#### 6.2.2 What governs the sign: cap slack, not AUM

| country | AUM | cap slack (shortfall of attained gross below 2.0) | channel |
|---|---|---|---|
| Germany | $1k | **0.01%** | **+0.0008** |
| **Japan** | **$100k** | **0.01%** | **−0.0009** |
| Germany | $10k | 0.09% | +0.0086 |
| India | $1k | 0.25% | +0.0175 |
| Japan | $1mn | 0.94% | +0.0313 |
| Germany | $100k | 6.69% | +0.0618 |
| India | $100k | 7.01% | +0.2114 |
| Germany | $1mn | 40.5% | +0.7954 |

> **The constraint's effect is zero when it does not bind and monotonically positive in how much it
> binds. At the registered calibration there is no mandate size at which it meaningfully hurts.**

At ~0.01% slack the channel is ±0.001 **with arbitrary sign** — Germany +0.0008 against Japan
−0.0009 **on the same cost model**. Those are noise around zero, not two regimes. Any bootstrap
"crossover" (Japan's point estimate is $115,532, CI [$101k, $349k], 90.8% of draws crossing) is
simply **the point at which the cap begins to bind**, and carries no economic content. Germany and
India show no crossover at all down to $1,000 (94.1% and 100% of draws with no sign change).

This also explains @AHV2025 without claiming to adjudicate them: their cost model has **no AUM
term**, so they sit permanently at zero slack, where this channel is zero by construction.

#### 6.2.3 Weighting

| | gross decile Sharpe | channel at $1bn | t |
|---|---|---|---|
| Germany, equal-weighted ‡ | +2.763 | ~~+11.06~~ ‡ | +12.27 |
| Germany, **value-weighted** ‡ | **+0.473** | ~~+4.15~~ ‡ | **+10.21** |
| India, equal-weighted ‡ | +1.209 | ~~+5.55~~ ‡ | +5.66 |
| India, **value-weighted** ‡ | **+0.215** | ~~+4.73~~ ‡ | **+5.61** |

‡ **Pre-fix signal-bearing universe** (the coverage-artefact ladder, §8.3), and the $1bn German and
Indian uncapped comparison books are insolvent under the contract cost model (§8.8; solvency was not
assessed for the value-weighted book). The channel entries are **withdrawn as quotable gains**. The
gross decile Sharpes are on the same pre-fix universe (the compliant equal-weighted values are
+2.305 / +1.197 / +1.278).

**Value weighting cuts the gross decile Sharpe by about 80%.** That is @NMV2016's critique of
equal-weighted anomaly results landing on **our own** gross numbers, and every gross Sharpe we
quote must carry it. The channel itself survives: positive and strongly significant at scale under
both schemes, in both markets. **[Unconfirmed on the compliant universe.** These are on the
signal-bearing ladder, measured before the coverage fix; the qualitative conclusion is probably
unchanged but is not established until the compliant re-run (§12.3) is done.**]**

#### 6.2.4 Impact coefficient and curvature

Impact coefficient, Germany, compliant ladder:

| `k` | channel at $100k | $1mn | $6mn |
|---|---|---|---|
| 0.5 | **−0.0142** | +0.1894 | +0.9220 |
| **1.0** (contract) | +0.0618 | +0.9174 | +2.4784 |
| 2.0 | +0.2113 | +1.8736 | +4.4578 |
| 3.0 | +0.3540 | +2.7097 | +5.3278 |

Positive at scale at every `k`. Only `k = 0.5` produces any negative region at all, and it is
−0.014 — economically nothing.

**Curvature.** @NMV2016 use Kyle-linear impact (total cost `~ Q^2`); we use square-root
(`~ Q^1.5`). For portfolio weights `|dw| < 1`, so raising the exponent at the same coefficient makes
impact *uniformly cheaper* — it moves the level as well as the curvature. Level-matching
`k' = Σ c·dw^1.5 / Σ c·dw²` on the uncapped book at $1bn preserves aggregate impact cost and
isolates curvature: `k' = 4.88` (Germany), `3.74` (India).

| Germany | $100k | $1mn | $3mn | $1bn | $10bn |
|---|---|---|---|---|---|
| 1.5, k=1 (contract) | +0.062 | +0.795 | +1.653 | +8.922 † | +9.256 † |
| 2.0, k=1 (uncalibrated) | **−0.054** | **−0.160** | **−0.193** | +5.618 | +7.600 |
| **2.0, level-matched** | **+0.087** | **+0.879** | **+1.729** | **+7.740** | **+8.103** |

| India | $100k | $1mn | $1bn | $10bn |
|---|---|---|---|---|
| 1.5, k=1 | +0.211 | +0.751 | +5.693 † | +5.967 † |
| 2.0, k=1 | +0.079 | +0.058 | +3.016 | +3.660 |
| **2.0, level-matched** | **+0.182** | **+0.560** | **+3.643** | **+3.837** |

† Under the contract cost model the uncapped comparison book is insolvent at these German and Indian
rungs (§8.8). Solvency was assessed **only under the contract cost model**, not under the sensitivity
cost models, so the $1bn and $10bn entries in every row should be read the same way until it is
assessed. The informative columns are $100k-$3mn.

**The channel is robust to curvature** (at the columns where the comparison is interpretable). A referee preferring Kyle-linear impact gets the same
paper. The negative region in the uncalibrated row is a **level** artefact and vanishes when the
level is restored — but it is also what the comparative static predicts, so the honest statement is
that the sign at small mandates depends on the cost **calibration**, and ours is Grinold-Kahn.

### 6.2.5 Inference on the signal-to-portfolio ladder (added 17:30 IST)

The decile-spread Sharpes that anchor the ladder previously had no standard errors. HAC t statistics
on the composite of the 8 prediction cells, $1bn, compliant universe:

| | gross SR | t | p | net uncapped | **net capped** | t | p |
|---|---|---|---|---|---|---|---|
| Germany | **+2.305** | +7.14 | <0.0001 | -9.597 | **-0.675** | **-2.29** | 0.022 |
| India | **+1.197** | +3.19 | 0.0014 | -6.315 | **-0.623** | -1.80 | 0.071 |
| Japan | **+1.278** | +4.11 | <0.0001 | -7.456 | **-0.775** | **-2.56** | 0.011 |

The signal is real (gross significant everywhere); the uncapped book is destroyed by cost; and the
**executable capped decile book is significantly negative in Germany and Japan**. That is the
signal-to-portfolio wedge with inference, and it is the cleanest single-sentence statement of the
Avramov-Cheng-Metzker result in our three markets.

**Caveat that prevents over-reading.** The capped decile book attains a gross of only ~0.03 of its
2.0 target at $1bn, so its Sharpe is a ratio of two tiny quantities, dominated by the fixed spread
cost on a very small book. The negative t statistics are statements about a nearly-empty executable
decile portfolio, not about the optimised book, whose net Sharpe (+0.128 Germany) is insignificant
(section 6.3.3). Quote both together or neither.

### 6.3 Taxes across three statutory regimes

Optimised book, $1bn, prediction cells, taxable regime, HIFO.

| | rate | **lt_share of gains** | turnover | tax bps | cost bps | SR gross | SR net | **SR after tax** | kept |
|---|---|---|---|---|---|---|---|---|---|
| **Germany** | 26.375% | **0.0000** | 0.0135 | 6.38 | 17.21 | +0.423 | +0.128 | **+0.018** | **14%** |
| **India** | 15.000% | **0.5928** | 0.0067 | 0.11 | 9.96 | +0.534 | +0.205 | **+0.201** | **98%** |
| **Japan** | 20.315% | **0.0000** | 0.0290 | 11.49 | 42.31 | — | +0.057 | **−0.049** | **negative** |

**6.3.1 The statutory wedge determines whether the holding-period channel can exist.** `lt_share`
is identically **0.0000** in Germany *and* identically **0.0000** in Japan, against **0.5928** in
India. Neither flat regime creates a long-term category, so no realised gain can fall into one at
any turnover under any model. **Japan is a second, independent placebo reproducing Germany's exact
zero.** A tax-*level* story cannot produce that: the three rates all differ (26.4% / 20.3% / 15.0%)
and the two flat regimes give the same exact zero. This is the one pre-registered tax claim that
survived (§8.1), now confirmed out of sample.

**6.3.2 Given the wedge, drag is ordered by turnover, not by the rate.**

| ordering | sequence |
|---|---|
| statutory short rate | DEU > JPN > IND |
| **tax drag** | **JPN > DEU > IND** |
| **turnover** | **JPN > DEU > IND** |

Germany's rate is 30% higher than Japan's, yet Japan's tax drag is **80% higher**, because Japan
turns over **2.1×** as fast. Normalising, tax drag per unit turnover is **473** (Germany) and
**396** (Japan) — the two flat regimes, close as they should be for rates of 26.4% and 20.3% —
against **17** for India, 25× lower because it shelters most gains in an exempt long-term category.
**The third jurisdiction was required to separate the rate and turnover orderings at all.**

**6.3.3 Second-order as a channel; and the "survival" framing is withdrawn.** The tax channel is
−0.004 (India), −0.106 (Japan), −0.111 (Germany) Sharpe points against cost channels of −7.5 to
−11.9 and capacity channels of +3.6 to +8.9. Two orders of magnitude.

An earlier version of this section claimed taxes are "first-order for survival" because India keeps
98% of its net Sharpe, Germany 14%, and Japan's goes negative. **That is withdrawn.** Testing the
net Sharpe against zero (`tools/exp_after_tax_inference.py`):

| | net Sharpe | t | p | after-tax Sharpe | t | **tax channel** | **t** | **p** | Holm |
|---|---|---|---|---|---|---|---|---|---|
| **Germany** (flat 26.375%) | +0.152 | +0.53 | 0.595 | +0.016 | +0.06 | **−0.1363** | **−4.67** | **<0.0001** | **3/8** |
| **India** (wedge 0.150) | +0.271 | +0.82 | 0.413 | +0.265 | +0.80 | −0.0054 | −1.93 | 0.096 | **0/8** |
| **Japan** (flat 20.315%) | +0.055 | +0.18 | 0.861 | −0.082 | −0.27 | **−0.1373** | **−4.99** | **0.0010** | **3/8** |

**No country's net Sharpe is distinguishable from zero**, and neither is any after-tax Sharpe
including Japan's negative one. So "tax turns a viable strategy unviable" is not available — nothing
survives to be decided, and the 98% / 14% / negative retention figures are arithmetic on quantities
that are each indistinguishable from zero.

**What replaces it is better identified.** The tax channel's *significance* tracks the statute:
significant in **both flat-rate** jurisdictions (which have no long-term category,
`lt_share` = 0.0000 exactly) and an order of magnitude smaller under India's exemption — **on the
optimised book**, where the placebos happen to match (−0.1363, −0.1373) and India is not
significant (−0.0054, 0 of 8 cells). **That precision does not survive a change of book (§8.9):**
on the decile book the placebos are −0.070 and −0.170, and India is −0.009 with t = −2.14. What
does survive is the **ordering of magnitudes by statute type** (flat regimes 8–19× larger than
India) and `lt_share`, which needs no estimation. It is not the rate — Germany's is 30% above
Japan's and the ordering is not by rate.

This still retires the magnitude argument for dropping the tax machinery: the engine is what
produces the statutory contrast in (ii), which no cost model could.

**6.3.4 You cannot grow out of it.** Germany, prediction cells:

| AUM | turnover | cost bps | **tax bps** | SR net | SR after tax | **tax channel** |
|---|---|---|---|---|---|---|
| **$100mn** | 0.0522 | 60.47 | **23.28** | +0.255 | +0.100 | **−0.155** |
| **$1bn** | 0.0135 | 17.21 | **6.38** | +0.128 | +0.018 | **−0.111** |
| **$10bn** | 0.0017 | 2.20 | **0.94** | +0.186 | +0.063 | **−0.122** |

The tax bill falls **25-fold** as the cap suppresses turnover **31-fold**, and the risk-adjusted
drag is **flat at −0.11 to −0.16**. The cap cuts the tax bill by cutting trading and cuts gross
return in the same motion. A $10bn fund looks almost untaxed at 0.94 bps and is not, in the units
that matter. `lt_share` is 0.0000 at all three rungs, as the statutory argument requires.

### 6.4 ML design choice is not detectable at this power (decile books, Germany and India)

Three axes (representation, conditioning, uncertainty) on the 8 prediction cells; at each AUM rung
the equal-weighted composite of the 4 cells at each level, tested with the same paired bootstrap,
Holm-corrected across axes.

| | capped (executable) | uncapped |
|---|---|---|
| **Germany** | **0 of 42** | 5 of 42 |
| **India** | **0 of 42** | **0 of 42** |

14 AUM rungs × 3 axes per decile book per country. **Scope: the capped and uncapped decile-spread
books, Germany and India only.** The null was previously one test on one book at one AUM; it is now 42
per book per country across five orders of magnitude with paired HAC inference and familywise
correction, and it does not break anywhere on the capped decile book in either market.

**The optimised book, Japan, and one exploratory observation.** The same three contrasts were computed
on the **optimised** book at $1bn in all three markets (`tools/gate2_power.py`), effect (paired SE, t):

| | representation | conditioning | uncertainty |
|---|---|---|---|
| Germany | +0.134 (0.289, +0.46) | -0.177 (0.152, -1.17) | +0.159 (0.089, +1.80) |
| India | +0.007 (0.279, +0.03) | -0.263 (0.285, -0.92) | +0.154 (0.101, +1.54) |
| Japan | -0.418 (0.249, -1.68) | **+0.515 (0.182, +2.84)** | +0.125 (0.092, +1.35) |

Japan's conditioning contrast is the only one of nine that is significant: p = 0.0045 unadjusted, 0.014
after Holm across the three axes within Japan, 0.041 after Bonferroni across all nine. It is
**exploratory, was not pre-specified, was found during an audit, rests on a single AUM, and is
unreplicated**; it is disclosed here and must not be cited as evidence that conditioning helps.
Minimum detectable effect at 80% power with 132 months: 0.25-0.28 (uncertainty), 0.43-0.80
(conditioning), 0.70-0.81 (representation) Sharpe points.

**The mechanism we hoped for is not supported** (§8.6). Caveat that limits the null's reach: 8
cells and 132 months is low power for a 3-factor design, and the standard errors rather than the
effects are binding. The defensible framing is "**not detectable at this power**", with the power
stated — @CHK2024 use 1,056 designs and @LAL2025 5,376 against our 8.

### 6.5 The friction horse race

Compliant ladder, $1bn, prediction cells.

| channel, Sharpe points | Germany | India |
|---|---|---|
| cost (gross → net uncapped) | −11.90 † | −7.51 † |
| **capacity** (net uncapped → net capped) | +8.92 † | +5.69 † |
| tax (net → after tax, optimised book) | **−0.111** | **−0.004** |

† Both legs use the **insolvent** uncapped comparison book at $1bn (§8.8), so these German and Indian
cost and capacity entries are not quotable. The like-for-like ladder at the largest **solvent** rung is
in §8.9: Germany $100mn cost -9.62 / capacity +6.80 / tax (capped book) -0.098; India $30mn -5.18 /
+3.19 / -0.005; Japan $1bn -9.02 / +6.92 / -0.170.

| annualised bps, optimised book | Germany | India | Japan |
|---|---|---|---|
| cost drag | 17.21 | 9.96 | 42.31 |
| tax drag | 6.38 | 0.114 | 11.49 |
| **cost / tax** | **2.70×** | **87.4×** | **3.7×** |

**Ordering: capacity ≫ cost ≫ tax**, with tax two to three orders of magnitude below the other two
in scale-invariant Sharpe units.

**Limitation, stated not buried.** Cost and capacity drags are measured on the **decile-spread**
book, the only one with an uncapped counterfactual; tax drag on the **optimised** book, because the
lot-level engine runs on realised weights. Two different books, so this compares **orders of
magnitude, not a decomposition that sums**. It is not fixable by arithmetic (§5.6). The bias favours
the tax channel — measured on the lower-turnover, constrained book — and it still loses.

---

## 7. The mechanism

    net Sharpe = (alpha_eff - kappa * G^0.5) / sigma ,     kappa ~ sqrt(AUM / ADV)

A participation cap lowers attainable gross `G` and per-name turnover. It lowers `alpha_eff` roughly
**linearly** in the positions it forfeits but lowers the cost term as **`G^0.5`**, so it pays
whenever `kappa` is large relative to alpha. Since `kappa` grows as `sqrt(AUM/ADV)`, the benefit
must grow with mandate size — which §6.2.1 measures over seven orders of magnitude, and §6.2.2
refines: the governing variable is not AUM but **how much the cap actually binds**.

The expression also implies a small-AUM regime where the cap costs more alpha than it saves. **We
searched for it down to a $1,000 mandate and at the registered calibration it is not there** — the
channel decays to zero from above rather than crossing. It appears only under a materially cheaper
impact calibration (§6.2.4), which is the mechanism working, not an instability: the cap pays only
when there is cost worth avoiding.

This closes blocker 5 of the September readiness audit (no economic mechanism), with the caveat
that the comparative static is a one-page argument rather than a derived model.

---

## 8. Retractions and corrections, in full

Nine entries (8.1-8.9); seven arose today. Each is in the git history with the evidence.

### 8.1 The pre-registered tax-wedge statistic — WITHDRAWN (earlier)

India returned slope −4.83, t = −2.59: **significantly the wrong sign**. The statistic also divides
tax by mean gross return, which is **negative for 6 of 16 German and 8 of 16 Indian cells**, so it
is ill-defined; its sign flips with specification (Germany −21.99 on all cells, **+11.56** on cells
with gains). An earlier report that Germany's −21.99 "showed the placebo holds" was retracted.
**What survives is §6.3.1**, which is a statutory fact rather than an estimate.
`docs/RESULTS_WEDGE_TEST.md` §2.

### 8.2 The post-hoc turnover gradient (t = −4.36) — WITHDRAWN (earlier)

A promoted gradient in `lt_share_of_gains` against turnover (India, slope −8.78, **t = −4.36**) does
not survive splitting by objective arm. The two arms occupy **disjoint** turnover ranges, so a line
through all 16 cells measures the gap between two tight clusters and its **effective n is 2, not
16**. Within the prediction arm t = **−0.86**; the economic arm has the wrong sign (+13.1).
**Do not quote t = −4.36.**

### 8.3 The capacity-channel sign flip — RETRACTED TODAY, and it would have been the headline

**The claim.** The channel changes sign: Germany **−0.811** Sharpe points at a $100k mandate
(**t = −6.10**) rising to **+11.06** at $1bn, crossing zero at **$3.79mn, 95% CI
[$1.88mn, $7.07mn]**, 0 of 2,000 bootstrap replications failing to show a sign change. It
reconciled @NMV2016/@KS2004 with @AHV2025 as two limits of one expression.

**The defect.** The ladder formed deciles on Germany's **signal-bearing** cross-section (~382 names)
instead of its **investable** one (~246). C6 prices **65.1%** of Germany against **99.1%** of India,
and document 13 requirement 2 makes an uncertified security-month non-tradeable. The ladder broke
that rule in **both directions at once**: an uncovered name was charged **zero cost** in the
uncapped book, and given **cap = 0** in the capped book. Both push the channel downward, **and only
in Germany**.

| Germany at $100k | non-compliant | compliant |
|---|---|---|
| gross | +2.383 | +1.998 |
| net uncapped | +1.749 | **+0.657** (35% of positions had been free) |
| net capped | +0.938 | +0.719 |
| **channel** | **−0.811** | **+0.062** |

India, at 99.1% coverage, is the control and moves only **+0.183 → +0.211**. An effect that reverses
in the 65%-coverage panel and not in the 99%-coverage panel is a coverage effect.

**Why this is the most important entry in this section.** The spurious result was **t = −6.10**,
monotone across nine decades of AUM, and it **survived a value-weighting robustness check and a
six-fold impact-coefficient sweep** — including satisfying the mechanism's own
`crossover ∝ k^(−2)` prediction to within ±15%. **A wrong result reproduced a theoretical scaling
law.** Both checks varied parameters *within* the mis-specified universe and therefore inherited the
defect. Only enforcing the project's own non-tradeability rule killed it.

**Blast radius, audited.** Only one tool was affected. Every other consumer routes through the
optimiser, which has called `eligible_cost_input_permnos` at both construct sites plus
`partition_prior_book` since 8 October. **The capacity frontier, the dose-response correlations
(+0.555 → +0.854), book characteristics, the tax ledger and every stage-04/06 number are
unaffected.** The frontier was already computed on eligible names — Germany's 246, not 382 — which
is why it was internally consistent and why the ladder disagreeing with it was the clue worth
following.

### 8.4 "Costs beat taxes 5× (Germany) / 53× (India)" — CORRECTED TODAY

Those are **all-16-cell averages** including the incompetent economic arm, which trades 1.8× faster.
On prediction cells alone: **2.70×** and **87.4×**. **Germany's margin is one order of magnitude,
not two.**

### 8.5 "Our frontiers are 10–100× below published US estimates" — WITHDRAWN TODAY

Not turnover-matched. @NMV2016's capacities span **$0.18bn to $169bn within one paper**, ordered by
turnover; its **high-turnover** panel is **$0.18–0.53bn**. Our monthly-rebalanced ML books belong
there, where **Japan's $413mn is inside the US range**, Germany's $106mn is ~2–4× below it and
India's $55mn ~3–10× below. Three further mismatches confound even that residual gap (§10 C4).
**The non-US frontiers are no longer a contribution.**

Related correction: the claim that "our 42-row prior-art tracker contains none of these papers" was
**wrong** — @ACM2023 is row 5 and @AHV2023 row 10. The failure was **mis-rating** them (Low and
Medium threat, scored against the old attribution claim) and never re-scoring when the headline
moved. They are now High and Severe.

### 8.6 "Capacity overwrites ML design identifiability" — NOT SUPPORTED TODAY

The hypothesis would have turned §6.4's bare null into a mechanism. Prediction written before
looking: capped axis effects shrink as cap slack falls, uncapped effects do not. Three things go
against it:

1. **India shows the same null on the unconstrained book** (0 of 42). Removing the cap does not
   restore detectability.
2. **Germany's capped effects do not shrink** — mean |effect| *grows* 0.087 → 0.138. The standard
   errors grow faster, so it is lost **power**, not shrinkage. The prediction was about the effect.
3. **Germany's 5 of 42 is within multiple-testing expectation** (~2 expected; four of the five are
   one axis at adjacent, highly correlated rungs, so roughly two independent observations).

### 8.7 The §112A bounding exercise — INVALID TWICE, then RESOLVED

Intended to discharge Absar's dependency: re-run the event study with the 456 missing reference
values at both tax extremes; if the bounds agree, the missing data cannot change the conclusion.

**Version 1.** Both bounds returned **bit-identical** results and I was one step from reporting
Absar unblocked. The engine consumes `close_value_local × (fmv/close)`, so **the ratio is the only
lever**, and both files set `fmv = close` on the 456 rows — **ratio 1.0 in both**. The two runs were
the same run.

**Version 2.** Corrected to vary the ratio (1e−6 vs 1e6), leaving the 546 real rows untouched.
**Output is still bit-identical**, and `tools/verify_bound_is_live.py` correctly returns exit 2,
"BOUND DID NOT BIND".

**RESOLVED 17:20 IST — the engine is correct and the 456 values cannot change the result.**

422 of the 456 names are materially held and 75 are held post-reform, so the possibility of a bug
in the dated engine was live and serious. It is excluded, end to end at the unit level. For a
**perturbed** permno, a long lot acquired 2017-01-31 at basis 100 and sold 2018-06-30 at 200:

| bound | ratio | statutory reference | tax basis | **taxable gain** |
|---|---|---|---|---|
| MAXTAX | 1e−6 | 0.0001 | 100 (actual cost) | **100** (full gain taxed) |
| MINTAX | 1e6 | 1e8 | 200 (sale value) | **0** (fully sheltered) |

That is `max(actual_cost, min(fmv, sale_value))` working exactly as §55(2)(ac) requires, with the
perturbation flowing through **maximally**. So the reference value is threaded.

**Therefore the identical aggregate output has one remaining explanation:** none of the 456 names
is ever realised as a **grandfathered long-term gain on a pre-February-2018 lot sold after
2018-04-01** in any of the 16 cells. Had even one been, its taxable gain would have differed by the
entire gain between bounds, which must have moved `mean_tax_per_gain_post` — and that is identical
to sixteen significant figures (0.0408371359251255).

The deduction is only valid while the plumbing is known good, so it is pinned by **six tests** in
`tests/tax/test_112a_reference_threading.py`, including one asserting the exact mistake: moving
`fmv` and `close` together is a no-op. **Absar's lookup is no longer a blocker** — it would be nice
for completeness and nothing waits on it. `docs/handoff/20_...` records the resolution and the fact
that the 02:45 escalation was too strong, because I had not checked whether the affected names were
in the binding set before escalating.

---

### 8.8 The $1bn capacity numbers for Germany and India are differences against an insolvent book — CORRECTED

Found while running the decile weights through the tax engine. `after_tax_backtest` stopped after
**one month** on the uncapped books, because it halts when NAV reaches zero. That is the engine
correctly refusing to continue a bankrupt account, and it exposed that the uncapped Sharpe the
capacity channel is measured against is computed on a return series no investor could have had.

Uncapped decile book, composite of the 8 prediction cells, compliant universe
(`outputs/signal_vs_portfolio/uncapped_solvency.csv`):

| | solvent up to | channel at that rung | at $1bn |
|---|---|---|---|
| **Germany** | **$100mn** | **+7.63** (t +10.21) | **median monthly net return −54.7%; 7.9% of cell-months below −100%; 7 composite months below −100%** |
| **India** | **$30mn** | **+3.64** (t +5.00) | **median −44.6%; 11.2% of cell-months below −100%; 11 composite months** |
| **Japan** | **every rung through $10bn** | **+6.68 at $1bn** (t +11.01) | median −7.9%, no month below −100% |

At $10bn, 93.7% (Germany) and 80.1% (India) of cell-months are below −100%. A monthly return below
−100% is impossible for a real account. The cumulative product of (1+r) is exactly zero in Germany
and India at $1bn.

**What stands.** The effect is large and significant on **solvent** rungs: Germany +7.63 at $100mn,
India +3.64 at $30mn, Japan +6.68 at $1bn and +7.15 at $10bn with no insolvency anywhere. The
direction, the monotonicity in how hard the cap binds, and Japan's pre-registered confirmation are
unaffected, and Japan is the cleanest case because its counterfactual is feasible throughout.

**What is withdrawn.** The German and Indian **$1bn and $10bn** figures (+8.92 / +9.26 and
+5.69 / +5.97) as quotable Sharpe-point gains. They are arithmetic on a bankrupt counterfactual.
Quote the largest solvent rung per market, and flag the rest.

**Consequence for two earlier claims.** (i) The "asymptotic channel [withdrawn]" (+10.4 Germany, +4.6 India) and
the cross-market regularity built on it (D4: 4.58 vs 4.82) were produced by **Sharpe saturation**:
the uncapped Sharpe plateaus (−9.60 at $1bn, −9.93 at $10bn) while the cost it contains rises
threefold, because mean and standard deviation of the return series scale together. It is not an
economic limit. D4 is withdrawn as a regularity. (ii) The **units audit** the team's reviewer asked
for was warranted: the headline magnitude was a ratio statistic on a degenerate series.

**What it means for the paper.** Sharpe points are the wrong unit for the capacity channel once the
uncapped leg is insolvent. A better-posed quantity is the **cost avoided as a share of gross alpha**
or the net return in basis points, both of which stay finite. That reformulation is open work
(§12.12).

### 8.9 Matched-book accounting: the one-book ladder, and the tax-channel match was a coincidence of the book — CORRECTED

Step 1 of the revised plan: the saved decile weights (capped and uncapped) go through the **same**
`after_tax_backtest` under the zero-tax control and the country's statutory regime, on identical
dates and the identical investable universe (`tools/exp_matched_book_accounting.py`).

**Cost, capacity and tax on one book, at the largest solvent rung** (prediction cells, composite):

| | AUM | gross SR | net SR uncapped | net SR capped | **cost ch** | **capacity ch** | **tax ch (capped)** | t |
|---|---|---|---|---|---|---|---|---|
| Germany | $100mn | +2.305 | −7.312 | −0.510 | **−9.618** | **+6.802** | **−0.098** | −3.90 |
| India | $30mn | +1.197 | −3.987 | −0.801 | **−5.184** | **+3.186** | **−0.005** | −2.13 |
| Japan | $1bn | +1.278 | −7.745 | −0.828 | **−9.023** | **+6.917** | **−0.170** | −3.67 |

At $1bn the engine itself reports the German and Indian uncapped books insolvent (NAV exhausted
after **1 of 132** months in all 8 cells), independently confirming §8.8.

**Ordering on one book: capacity (+3.2 to +6.9) and cost (−5.2 to −9.6) are two orders of magnitude
above tax (−0.005 to −0.170).** That is now a like-for-like comparison, and it retires the
horse-race limitation of §6.5 for the solvent rungs.

**Three corrections that come out of it.**

1. **The capacity channel is smaller on the pipeline's accounting than on my wedge tool's.**
   Germany **+6.80 versus +7.63**, India **+3.19 versus +3.64**, Japan **+6.92 versus +6.68**. The
   executable (capped) book reconciles between the two to about **5e−4** per month, so the cost
   code is consistent. The *uncapped* book does not (max monthly difference up to 0.27 at Germany
   $100mn): the pipeline compounds NAV and charges costs on drifted positions, the wedge tool
   treats each month independently at fixed AUM. The pipeline is the more faithful account of a
   real portfolio, so **the matched-book figures supersede the wedge-tool figures** wherever both
   exist.
2. **The executable decile book's net Sharpe is negative or borderline everywhere:** Germany −0.510
   (t −1.83), India −0.801 (t −2.28), Japan −0.828 (t −2.74) at the solvent rungs. This is the
   signal-to-portfolio wedge on a single book. The caveat of §6.2.5 stands: that book attains only a
   few percent of its target gross, so its Sharpe is a ratio of small numbers.
3. **The tax-channel "match within 1% [withdrawn]" was a property of the optimised book, not of the statutes.**
   On the optimised book Germany and Japan gave −0.1363 and −0.1373. On the executable decile book
   they are **−0.070 (t −3.55) and −0.170 (t −3.67)** at $1bn, a factor of **2.4** apart, and India
   is **−0.009 with t = −2.14**, i.e. borderline significant where the optimised book gave
   t = −1.93. What survives is the **ordering of magnitudes by statute type** — the flat regimes
   are **8–19×** India's — and the exact `lt_share` contrast. The clean "two placebos agree,
   treatment insignificant" statement is **withdrawn**; it was a coincidence of one book.

   A side observation: on Japan's uncapped book the tax channel is **positive** (+0.078, t +1.51).
   A book that loses money every month realises losses, and realised losses earn tax credits, so
   the sign of the tax channel depends on whether the book has gains to tax. That is correct
   behaviour of the engine and a reason not to read the sign as a property of the statute.

## 9. The shape of the errors

Six of the nine entries in §8 (8.3, 8.4, 8.5, 8.7, 8.8, 8.9), plus three infrastructure bugs, share one shape: **a quantity computed
correctly, then compared against or constructed under the wrong thing.** The pipeline is not this
project's risk. The framing of the comparison is.

| # | computed correctly | wrong frame |
|---|---|---|
| 8.5 | frontiers $55/106/413mn | compared to **low-turnover** US capacities |
| 8.4 | cost/tax ratios | averaged over a cell set containing a **broken arm** |
| 8.3 | capacity channel | formed on the **signal-bearing** rather than investable universe |
| 8.7 | §112A bounds | varied a column the consumer **does not read** |
| infra | source index | **fixed path**, so two runs overwrote each other |
| infra | stage 06 summary | **fixed path**, same failure |
| infra | horse race | read the **non-compliant** ladder |

**Robustness checks did not catch any of them**, because robustness checks vary parameters *inside*
the frame.

---

## 10. Verification protocol (methods contribution)

`docs/VERIFICATION_PROTOCOL_2026-10-09.md`. Seven checks, each costing roughly nothing against the
three hours §8.3 consumed.

* **C1 — did the knob I turned move the model's input?** A bounding or sensitivity run whose output
  is unchanged is a null result **about the plumbing** until proven otherwise. Assert the **derived**
  quantity the consumer reads, not the column you edited. **Executable:**
  `tools/verify_bound_is_live.py`, which refuses a bounding claim whose bound did not bind (exit 3
  when `--derived` exposes an identical transform, exit 2 when outputs match). It caught §8.7 both
  times.
* **C2 — is my universe the same universe as the thing I compare against?** §8.3's clue was
  available before any result was interpreted: 382 German names against the frontier's 246.
  Reconcile every new exhibit's name count against `capacity_frontier.csv`. They now match in all
  three countries (246 / 348.5 / 1705).
* **C3 — does the aggregate contain a component already declared broken?** §8.4. Every mean over
  cells must state its cell set; default to prediction cells.
* **C4 — is the comparator matched on the dimension that drives the quantity?** §8.5. Capacity
  numbers must match on **turnover, units (dollar vintage, one- vs two-sided), impact law, and
  cost-input coverage**.
* **C5 — would this effect appear in a panel where the mechanism cannot operate?** Coverage
  65/99/99.8 across Germany/India/Japan settled §8.3 in one line.
* **C6 — robustness checks inside a wrong frame are not evidence.** A suite must vary the **frame**
  (universe, eligibility rule, cell set, comparator), not only the parameters.
* **C7 — every pre-registered prediction needs a magnitude floor, not only a sign.**
  `AMENDMENT_001D` D3 asked for the *existence* of a negative channel with no magnitude floor and no
  significance requirement, and Japan passed it on **−0.0013 with p = 0.370**. A test that a −0.0013
  reading passes is not a test.

### 10.1 Japan's scorecard, and why we do not report its verdict

`tools/score_amendment_001d.py`, committed before Japan reported, returned:

| prediction | verdict | deciding number |
|---|---|---|
| D1 monotone | **PASS** | largest adjacent change +0.0102 (no decrease) |
| D2 positive at $1bn | **PASS** | **+6.6813, t = +11.01, p < 0.0001** |
| D3 negative region exists | **PASS** | gross Sharpe +1.278 > India's +1.209; a negative channel exists below $1mn |
| D4 asymptotic ratio [withdrawn] in [3.5, 5.5] | FAIL | 7.1511/1.278 = **5.596** |
| D5 scaled channel at $1bn < 4.00 | FAIL | **5.228** |

Its verdict line reads "H-FLIP CONFIRMED". **We do not report that.** D3's pass is vacuous (C7):
the negative reading is **−0.0013, t = −1.14, p = 0.370**, CI containing zero, four orders of
magnitude below the retracted German −0.811. And H-FLIP's retraction is independent of Japan — §8.3
withdrew its evidential basis, so Japan cannot resurrect it. **D2 is the real confirmation** and it
is clean.

**D5's failure is substantive and informative.** We predicted Japan's scaled channel would be
*below* Germany's because $1bn is only 2.4× past Japan's $413mn frontier against 9.4× past
Germany's $106mn. It came out **higher**. At $1bn Japan's attained gross is 0.162 of 2.0 — the cap
binds hard despite the nearer frontier, because Japan's **1,705-name breadth** puts far more
positions at the cap. **Distance past the capacity frontier is not a sufficient statistic for how
hard the constraint bites.**

---

## 11. Threats to validity

1. **Low power on the factorial.** 8 prediction cells, 132 months. §6.4's null is "not detectable at
   this power". The standard errors bind, not the effects.
2. **Germany's 65% cost-input coverage.** Handled by restricting to the investable universe, but it
   means Germany's investable panel is 246 names — thin for a cross-sectional strategy — and the
   excluded names demonstrably carried alpha (gross Sharpe +2.383 → +1.998).
3. **Turnover is endogenous.** §6.3.2's ordering is descriptive, not identified. Japan trades 2.1×
   Germany because of its universe and signal, not its tax code. Only §6.3.1's existence claim has
   an exogenous statutory instrument.
4. **n = 3 jurisdictions**, and India differs from the other two on both rate and wedge at once.
5. **Two books in the horse race** (§6.5). Not fixable by arithmetic.
6. **The economic arm is broken** and excluded. Whether to debug or flag is Maham's ruling. If it is
   repaired, the factorial's one significant main effect may change and §6.4 must be re-run.
7. **Borrow fee is a modelled flat 1% proxy**, not certified data. Sensitivity rates
   {0.3%, 0.6%, 4.3%, 7%} exist in config and have not been swept for the capacity channel.
8. **The frozen sleeve** makes the uncapped optimised book unconstructible, so the capacity channel
   is only measurable on the decile book.
9. **Survivorship and listing conventions** in the non-US panels are workstream A's certification;
   we have not independently audited them.

---

## 12. What is left to do, why it matters, and how it could change the paper

Ordered by how much each could move the paper.

### 12.1 ~~Resolve §8.7 — is the §112A reference value threaded into the tax engine?~~ **DONE**

**Resolved 17:20 IST.** The engine is correct (unit-tested end to end, maximal flow-through), so the
identical bound output means the 456 names are never realised as grandfathered long-term gains in
the post-reform window. **The §112A result stands as written and Absar's lookup is discharged.**
Pinned by six tests. See §8.7.

### 12.2 Japan's tax ladder **[DONE, all three rungs]**

Prediction cells, taxable regime, optimised book:

| AUM | turnover | cost bps | tax bps | SR net | **SR after tax** | **tax channel** | lt_share |
|---|---|---|---|---|---|---|---|
| **$100mn** | 0.1402 | 166.51 | 35.17 | −0.088 | **−0.205** | **−0.116** | 0.0000 |
| **$1bn** | 0.0290 | 42.31 | 11.49 | +0.057 | **−0.049** | **−0.106** | 0.0000 |
| **$10bn** | 0.0036 | 5.48 | 1.35 | −0.100 | **−0.177** | **−0.077** | 0.0000 |

After-tax Sharpe is negative at all three rungs and `lt_share` is exactly 0 at all three. Germany's
ladder, for comparison, is −0.155 / −0.111 / −0.122.

**Reading it correctly, because the tool's own printed verdict overreaches.** The script printed
"Japan's book is unviable after tax at EVERY mandate size tested". That is the "survival" framing
withdrawn in §6.3.3. Japan's **pre-tax** net Sharpe is −0.088 / +0.057 / −0.100: negative at two of
three rungs before any tax, and not distinguishable from zero at $1bn (t = +0.18). Taxes make a
non-viable book more negative; they do not turn a viable one non-viable.

**Correction to "scale-invariant".** Germany's tax channel is roughly flat across the ladder
(−0.155 / −0.111 / −0.122). Japan's is not: it **shrinks by about a third** at $10bn (−0.116 →
−0.077), because at that scale turnover has fallen to 0.0036 and the tax bill with it. So the
claim "you cannot grow out of the tax channel" holds for Germany and only partly for Japan, and
§6.3.4 should say so.

### 12.3 Re-run the value-weighting check on the compliant ladder **[NOT DONE - needs approval]**

**Why.** §6.2.3's figures were measured **before** the coverage fix, on the signal-bearing universe.
The conclusion (channel survives value-weighting) is very likely unchanged, but the numbers quoted
are from the defective universe and must not be published as they stand.

**How it changes the paper.** Probably not at all, but it is a published-number correctness issue of
exactly the kind §9 catalogues, and leaving it would be inconsistent with C2.

### 12.4 Inference on the design-axis null, and a power calculation **[PARTLY DONE: minimum detectable effects derived from the committed paired SEs (audit §1.4); Gate 2 covers a new arm]**

**Why.** §6.4 reports 0 of 42 but no **minimum detectable effect**. A null without a power statement
is weak evidence of absence, and @CHK2024/@LAL2025 have 100× our design count.

**How it changes the paper.** With an MDE, §6.4 becomes "design dispersion below X Sharpe points is
undetectable on an executable book at this power", which is publishable as a bound. Without one it
is an absence of evidence and a referee will say so.

### 12.5 Capacity frontier as a share of market capitalisation **[NOT DONE]**

**Why.** @KS2004 reports $5bn as **0.043% of NYSE capitalisation** — that is the comparable
statistic across eras and countries, and we report only dollars. §10 C4 requires it.

**How it changes the paper.** It is the only way to make any cross-country or cross-era capacity
comparison legitimate after §8.5. It may restore a weaker version of the withdrawn claim, or
confirm it should stay withdrawn. Cheap: market cap is in C1 `me`.

### 12.6 Read @ACM2023 in full text **[NOT DONE; also JKMP final, Nechvátalová, Dai et al., Moehle et al. remain abstract-level]**

**Why.** It is the closest competitor, it is in Management Science, and our row is still
abstract-level. We do not know precisely what it does and does not claim.

**How it changes the paper.** Could sharpen or puncture §2.3. Required before submission regardless.

### 12.7 Borrow-fee sensitivity for the capacity channel **[NOT DONE - needs approval]**

**Why.** Borrow is a modelled 1% flat proxy, and the config carries sensitivity rates up to 7%. A
long/short book at gross 2.0 pays borrow on the whole short side, so a 7× borrow rate is not a small
perturbation.

**How it changes the paper.** If the capacity channel is sensitive to borrow, the headline needs a
band. The sweep is cheap and has not been run.

### 12.8 Japan's optimised-book capacity dose-response **[NOT DONE - needs approval; the diagnostic exists for Germany only, and realised_books_JPN/IND.csv are empty stubs]**

**Why.** The weight-cross-section diagnostics (`corr(|w|, adv_cap)` +0.555 → +0.854,
`corr(w, alpha)` +0.497 → +0.321) exist for Germany only. Japan's book now exists.

**How it changes the paper.** Gives the mechanism a third independent confirmation on the
**optimised** book rather than the decile book, which is the book an investor runs.

### 12.9 Maham's rulings **[blocked on her]**

* Countersign 001A, 001B, 001C, and 001D-as-retracted.
* **Rule on the economic arm** — debug or flag. Affects §5.3, §6.4 and every all-cell average.
* **Sanity-check `sharpe_difference_test`** — the influence-function annualisation in particular,
  which is the kind of thing that is wrong by `sqrt(12)` without looking odd; and whether Holm or a
  proper max-statistic bootstrap is the right multiplicity control.
* **Adjudicate the studentized-versus-percentile discrepancy** at Germany VW $100k, where the
  percentile CI excludes zero and the studentized p is 0.117.
* Opinion on §9/§10: what a reviewer-proof protocol looks like when a coverage asymmetry can
  produce a t = −6.10 result that passes two robustness checks.

### 12.10 ~~Absar's lookup~~ **DISCHARGED — there is no longer any external blocker**

The 456 missing §112A reference values **cannot change the event study** (§8.7, §12.1). Obtaining
them remains desirable for completeness and nothing waits on them.

**As of 17:20 IST this project has no blocker that only another person can clear.** Everything
outstanding is either our own compute (§12.2–12.8) or Maham's judgement on work already done
(§12.9), and none of §12.9 blocks a result — it blocks sign-off.

### 12.11 Not worth doing

* **A properly calibrated Kyle replication.** §6.2.4's level-matched run already answers the
  curvature objection; a full recalibration is a large job for a robustness row.
* **Reviving the sign flip at a cheaper calibration.** It exists at `k = 0.5` and at uncalibrated
  exponent 2.0, but §6.2.2 shows those negative readings sit where the cap is essentially
  non-binding. Pursuing it would be fitting the artefact's ghost.
* **Pivoting the paper onto §9/§10.** The coverage-asymmetry finding is genuinely novel and worth a
  methods section, but building a paper on our own bug is a weak foundation and a referee would say
  so. It is a section, not a thesis.

### 12.12 Restate the capacity channel in a unit that survives an insolvent comparison book **[NOT DONE - audit task P0-2; the definition must be fixed before any value is computed]**

**Why.** §8.8: Sharpe points are ill-posed once the uncapped leg is bankrupt, and the uncapped
Sharpe saturates rather than measuring cost. Quote-able alternatives that stay finite: cost avoided
as a share of gross alpha; net return in basis points; terminal wealth with explicit ruin.

**How it changes the paper.** It replaces the headline unit. The qualitative result survives (it is
confirmed on solvent rungs and in Japan throughout), but a referee will ask for exactly this, and
the unit decides whether the number is believable. Cheap: every input exists in the monthly dumps.

### 12.13 Matched-book accounting and the two new literature rows **[DONE: see §8.9 and tracker C7/C8]**

Decile weights saved (`--dump-weights`) and run through `after_tax_backtest` on one book
(`tools/exp_matched_book_accounting.py`); the tracker gains **Dai-Lei-Liu-Yang (Management Science
2026, "Optimal Tax Timing with Transaction Costs")** and **Moehle-Kochenderfer-Boyd-Ang (JOTA 2021,
"Tax-Aware Portfolio Construction via Convex Optimization")**, both confirmed at abstract level only.
The second means a tax-lot-aware convex optimiser is prior art, so ours is a tool and not a
contribution.

---

## 13. Venue assessment, honestly

The September strategy named **JFQA and Management Science (Finance)** as primary (fit 9, difficulty
4), with RFS/JF/JFE as a stretch conditional on "a general lesson about why ML **adds** value".

**Judgement at the time of writing: JFQA primary. SUPERSEDED** by `FINALIZATION_AUDIT_2026-10-09.md`
section 4 (Journal of Empirical Finance first, Quantitative Finance second, JIFMIM third, Review of
Asset Pricing Studies not a default), which was set after the withdrawals in §8 and uses the
publishers' official scope pages. The bullets below are kept as the earlier reasoning.

* **Management Science is compromised** by having published @ACM2023.
* **Not JF/JFE/RFS.** Our lesson is about why ML alpha *fails to arrive*, and the direction of the
  main result corroborates @NMV2016 and @KS2004 rather than overturning them. We add scale-indexing,
  three non-US markets, a tax engine and inference — not a new mechanism.
* **RFS is a defensible stretch rather than a fantasy**, because the paper engages an RFS paper and
  a JF paper with new machinery, and because §6.3's three-jurisdiction placebo design is genuinely
  not available to anyone else. But submitting there first would cost a year on a paper whose main
  effect is a confirmation.
* **Alternatives:** Review of Asset Pricing Studies, Journal of Financial Markets.

The blocker status against the September audit:

| # | blocker | Sep 20 | now |
|---|---|---|---|
| 1 | no real data | Fatal | **Resolved** — three complete panels |
| 2 | no inference | Fatal | **Resolved** — deflated Sharpe, PBO, Romano-Wolf, SPA, HAC, plus the new paired Sharpe test |
| 3 | no identification | Fatal | **Changed.** The designed tax identification failed (§8.1). What identifies the capacity result is that AUM is set exogenously and market depth varies without our choosing it; §6.3.1 has a genuine statutory instrument |
| 4 | contested contribution | Severe | **Narrowed and honest.** §2.3 and §2.4 |
| 5 | no mechanism | Severe | **Not closed by evidence.** §7 is a one-page comparative static; its predicted small-AUM sign change was not observed at the registered calibration, so it explains the monotone dose-response but has no independent confirmation |
| 6 | dead components | Moderate | Resolved (demoted) |

---

## 14. Reproduction

```bash
# compliant capacity ladder (--require-cost-inputs is MANDATORY for any capacity exhibit)
python tools/exp_signal_vs_portfolio_wedge.py --country DEU --dump-monthly \
    --require-cost-inputs --tag cov \
    --aum 1e5 3e5 1e6 2e6 3e6 4e6 6e6 8e6 1e7 3e7 1e8 3e8 1e9 1e10

python tools/exp_capacity_channel_inference.py --country DEU IND JPN --tag cov --n-boot 2000
python tools/exp_friction_horse_race.py  --country DEU IND JPN          # defaults to --tag cov
python tools/exp_design_identifiability.py --country DEU IND
python tools/score_amendment_001d.py --country JPN --tag cov
python tools/verify_bound_is_live.py --inputs A B --outputs X Y --derived NUM/DEN
python tools/repair_source_index.py --country JPN
```

**Test suite: 464 tests, 0 failures** (re-run for the finalization audit; 438 pre-existing +
12 `test_sharpe_difference` + 8 `test_cost_input_coverage_rule` + 6 `test_112a_reference_threading`).

### 14.1 Document index

| document | content |
|---|---|
| `RESULTS_CAPACITY_CHANNEL_2026-10-09.md` | the capacity result, robustness, and §8.3's retraction |
| `RESULTS_TAX_THREE_COUNTRY_2026-10-09.md` | §6.3, including the AUM ladder |
| `RESULTS_DESIGN_IDENTIFIABILITY_2026-10-09.md` | §6.4 and §8.6 |
| `RESULTS_SIGN_FLIP_2026-10-09.md` | **retracted**; kept with a retraction header as the record |
| `AMENDMENT_001D_CAPACITY_CHANNEL_SIGN_FLIP.md` | pre-registration, its revision, its retraction, and Japan's result in §11 |
| `VERIFICATION_PROTOCOL_2026-10-09.md` | §9, §10 |
| `STRATEGIC_ASSESSMENT_2026-10-09.md` | the day's framing decisions, with corrections marked in place |
| `RESULTS_WEDGE_TEST.md` | §8.1, §8.2 |
| `ECONOMIC_ARM_CAPABILITY_GAP.md` | §5.3 |
| `NON_TRADEABLE_TREATMENT.md` | the rule §8.3 broke |
| `Closest_Prior_Art_Tracker.md` §C1–C8 | §3, from full texts |
| `handoff/20_FOR_ABSAR_...` | §12.10 |
| `handoff/21_FOR_MAHAM_...` | §12.9 |
| `docs/attachments/*.csv` | every table above, committed verbatim because `outputs/` is gitignored |

---

## 15. One-paragraph summary

At a $1bn mandate in Germany, India or Japan, a machine-learning equity strategy's net-of-cost
Sharpe ratio is **not statistically distinguishable from zero** (t = +0.53, +0.82, +0.18), which
corroborates Avramov, Cheng & Metzker in markets they did not study. Against that backdrop three
channels can be measured and two of them are significant. A **binding ADV participation constraint
improves** risk-adjusted performance by **+6.8 / +3.2 / +6.9** Sharpe points at the largest mandate
where the uncapped comparison book is still solvent ($100mn Germany, $30mn India, $1bn Japan) — and
beyond that the German and Indian uncapped books are bankrupt, so larger figures are not
performance gains. The constraint rescues the strategy from disaster rather than into profit. The
effect is zero where the constraint is slack,
monotone in how hard it binds, confirmed out of sample in Japan against a pre-registered prediction,
and robust to impact curvature, the impact coefficient and cost-input coverage (the weighting check
is unconfirmed on the compliant universe, §12.3). The
**tax channel** is two orders of magnitude smaller but **significant in exactly the two
jurisdictions whose statute provides no long-term category** — Germany −0.1363 (t = −4.67) and
Japan −0.1373 (t = −4.99) on the optimised book — and **insignificant** under India's long-term
exemption (−0.0054, t = −1.93). That contrast is not robust to the choice of book: on the
executable decile book the flat regimes are 8–19× larger than India, but India is
borderline-significant and the two placebos differ by 2.4× (§8.9), so only the magnitude ordering
by statute type should be quoted. No
machine-learning **design axis** is detectable at this power on the capped decile book in Germany and
India (0 of 42 in each; minimum detectable effect 0.25-0.81 Sharpe points), with one exploratory,
unreplicated exception on the optimised book (Japan's conditioning axis, t = +2.84, p = 0.041 after
Bonferroni across nine tests), though the signals carry information coefficients with t up to +10.4. The
paper's most uncomfortable contribution is that a 35-percentage-point cost-input coverage asymmetry
between two of its own panels manufactured a t = −6.10, monotone, theoretically coherent
cross-country contrast that survived two robustness checks before being caught — a warning the
international asset-pricing literature should probably hear.
