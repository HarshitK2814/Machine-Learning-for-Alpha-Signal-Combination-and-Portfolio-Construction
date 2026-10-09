# The ADV participation constraint's effect on net performance grows with how hard it binds (measured against an uncapped comparison book that becomes insolvent at scale)

**Date:** 2026-10-09, 12:35 IST
**Supersedes:** `docs/RESULTS_SIGN_FLIP_2026-10-09.md`, whose central claim — a sign flip with a
measurable crossover — **was retracted the same day as a cost-input coverage artefact.** That
document is kept as the record; §6 here explains what happened and why it matters methodologically.
**Status:** exploratory on Germany and India; **Japan is a pre-registered out-of-sample
confirmation** of the positive channel (§3c, `AMENDMENT_001D` D2), reported 12:55 IST.
**Audience:** referee-facing. Every number is reproducible from §7.

> **CORRECTED in the finalization audit (Phase 1), after this document was first written.**
> 1. The **uncapped comparison book is insolvent** at the rungs marked † below (Germany from $300mn,
>    India from $100mn; median monthly net return -55% / -45% at $1bn; Japan never). A Sharpe
>    difference against a bankrupt book is not a performance gain. Quote only unmarked rungs. Reasons
>    and evidence: `PAPER_2026-10-09_FULL_ACCOUNT.md` §8.8.
> 2. The wedge-tool values in the tables are **superseded** by the pipeline's own accounting of both
>    books (§8.9 of the same file): +6.80 (Germany $100mn), +3.19 (India $30mn), +6.92 (Japan $1bn).
> 3. The **"share of what survives" and "tax removes 87%"** passages of §4 are withdrawn: no country's
>    net Sharpe is distinguishable from zero, so there is nothing for tax to decide
>    (`RESULTS_TAX_THREE_COUNTRY` §4b).
> 4. The "cleanest statement of the result" language in §3b applies to the solvent rungs only.
> 5. The title and §1 previously said the constraint "creates" performance. The defensible statement
>    is a **difference against an infeasible comparison book**, whose value lies in the dose-response in
>    how hard the cap binds and in the solvent-rung magnitudes, not in a headline Sharpe gain.

---

## 1. The claim

> For an institutional investor in a mid-size equity market, the ADV participation constraint's
> effect on net risk-adjusted performance is **zero while the constraint does not bind, and
> monotonically positive in how much it binds**. Measured on the pipeline's own accounting of both
> books at the largest mandate where the uncapped comparison book is still solvent, it reaches
> **+6.80** (Germany, $100mn), **+3.19** (India, $30mn) and **+6.92** (Japan, $1bn) Sharpe points,
> from ±0.001 where the cap is slack; beyond those mandates the German and Indian comparison books
> are insolvent and larger figures are not performance gains (`PAPER` §8.8). It pays because it suppresses turnover faster than it suppresses
> signal. **At the registered cost calibration there is no scale at which it meaningfully
> hurts** (see §3g for the calibration dependence). The tax channel, measured with a
> lot-level engine across three statutory regimes, is **two to three orders of magnitude smaller**
> than either the cost or the capacity channel.

Japan is a **pre-registered out-of-sample confirmation** (`AMENDMENT_001D` D2, declared and scored
by committed code before any Japanese portfolio existed): +6.68 at $1bn on the wedge tool (t = +11.01;
+6.92 on the pipeline's accounting), 8 of 8 cells surviving Holm from $8mn upward.

**What this is not.** It is not a sign flip, not an economically meaningful crossover, and not an
adjudication of the published disagreement about whether turnover reduction helps. The only
negative readings anywhere in the compliant data are **±0.001 at ~0.01% cap slack, with arbitrary
sign** — Germany +0.0008 against Japan −0.0009 on the same cost model (§3d). Those are noise around
zero, not a regime. An earlier draft of this project claimed a sign flip with a measurable
crossover; it was a cost-input coverage artefact and is retracted in §6.

## 2. The mechanism

    net Sharpe = (alpha_eff - kappa * G^0.5) / sigma ,      kappa ∝ sqrt(AUM / ADV)

A participation cap lowers attainable gross `G` and per-name turnover. It lowers `alpha_eff`
roughly linearly in the positions it forfeits but lowers the cost term as `G^0.5`, so it pays
whenever `kappa` is large relative to alpha. Since `kappa` grows as `sqrt(AUM/ADV)`, the benefit
must grow with mandate size — which is what §3 measures, over five decades.

The same expression says there should exist a small-AUM regime where the cap costs more alpha than
it saves in cost. **We looked for it down to a $1,000 mandate and it is not there** — see §3d. The
channel decays to zero from above rather than crossing, so at the registered cost model that regime
is not reachable in our data at all.

## 3. The result

Composite portfolio: one equal-weighted book of the eight prediction cells, built from the same
stage-02 scores, on the **investable** universe (names carrying certified spread, volatility and
positive ADV — document 13 requirement 2; see §6). 132 months, 2009-01..2019-12. Channel =
`SR(net, capped) − SR(net, uncapped)`, paired Ledoit-Wolf studentized stationary bootstrap, 2,000
replications, block 6.

### 3a. Germany

| AUM | SR capped | SR uncapped | **channel** | HAC se | t | p | Holm 5% (of 8) |
|---|---|---|---|---|---|---|---|
| $100k | +0.825 | +0.758 | +0.068 | 0.055 | +1.22 | 0.178 | 0 |
| $300k | +0.599 | +0.301 | **+0.298** | 0.123 | +2.43 | 0.029 | 0 |
| $1mn | +0.347 | −0.571 | **+0.917** | 0.230 | +3.98 | 0.001 | **8** |
| $2mn | +0.139 | −1.333 | **+1.472** | 0.293 | +5.03 | 0.0000 | **8** |
| $3mn | +0.002 | −1.888 | **+1.890** | 0.342 | +5.53 | 0.0000 | **8** |
| $4mn | −0.089 | −2.333 | **+2.245** | 0.381 | +5.90 | 0.0000 | **8** |
| $6mn | −0.225 | −3.031 | **+2.806** | 0.442 | +6.36 | 0.0000 | **8** |
| $8mn | −0.312 | −3.569 | **+3.258** | 0.484 | +6.74 | 0.0000 | **8** |
| $10mn | −0.361 | −4.007 | **+3.646** | 0.517 | +7.05 | 0.0000 | **8** |
| $30mn | −0.468 | −6.210 | **+5.742** | 0.664 | +8.65 | 0.0000 | **8** |
| $100mn | −0.471 | −8.105 | **+7.634** | 0.748 | +10.21 | 0.0000 | **8** |
| $300mn | −0.611 | −9.083 | +8.471 † | 0.794 | +10.66 | 0.0000 | **8** |
| **$1bn** | −0.675 | −9.597 † | +8.922 † | 0.803 | +11.11 | 0.0000 | **8** |
| $10bn | −0.675 | −9.931 † | +9.256 † | 0.810 | +11.43 | 0.0000 | **8** |

**Significant at 5% on 13 of 14 rungs; 8 of 8 cells survive Holm at every rung from $1mn upward.**
**No crossover: 94.1% of replications show no sign change anywhere in $100k..$10bn.**

† Uncapped comparison book insolvent (Germany from $300mn): not interpretable as a performance gain.
Over the 11 solvent rungs, 10 of 11 are significant. Wedge-tool values; the pipeline's accounting at
the largest solvent rung ($100mn) is +6.80.

### 3b. India — the same shape, and cleaner

| AUM | SR capped | SR uncapped | **channel** | HAC se | t | p | Holm 5% (of 8) |
|---|---|---|---|---|---|---|---|
| $100k | +0.309 | +0.045 | **+0.264** | 0.057 | +4.63 | 0.0000 | 7 |
| $300k | +0.150 | −0.328 | **+0.478** | 0.110 | +4.36 | 0.0005 | **8** |
| $1mn | −0.119 | −0.999 | **+0.880** | 0.200 | +4.40 | 0.0005 | **8** |
| $2mn | −0.276 | −1.546 | **+1.271** | 0.274 | +4.64 | 0.0000 | **8** |
| $3mn | −0.386 | −1.923 | **+1.536** | 0.329 | +4.66 | 0.0000 | **8** |
| $4mn | −0.474 | −2.213 | **+1.739** | 0.371 | +4.68 | 0.0000 | **8** |
| $6mn | −0.598 | −2.647 | **+2.049** | 0.435 | +4.71 | 0.0005 | **8** |
| $8mn | −0.654 | −2.968 | **+2.314** | 0.488 | +4.74 | 0.0010 | **8** |
| $10mn | −0.686 | −3.221 | **+2.534** | 0.530 | +4.78 | 0.0025 | **8** |
| $30mn | −0.767 | −4.411 | **+3.644** | 0.729 | +5.00 | 0.0130 | 6 |
| $100mn | −0.814 | −5.405 † | +4.591 † | 0.865 | +5.31 | 0.0075 | 6 |
| $300mn | −0.634 | −5.969 † | +5.335 † | 0.972 | +5.49 | 0.0055 | 7 |
| **$1bn** | −0.623 | −6.315 † | +5.693 † | 0.998 | +5.70 | 0.0035 | 7 |
| $10bn | −0.623 | −6.589 † | +5.967 † | 1.015 | +5.88 | 0.0025 | 7 |

**Significant at 5% on all 14 rungs** (10 of 10 solvent rungs), 7–8 of 8 cells surviving Holm at every
rung. **100% of replications show no sign change** — on the solvent rungs ($100k-$30mn) India is the
cleanest statement of the result in the study.

† Uncapped comparison book insolvent (India from $100mn): not interpretable as a performance gain.
Wedge-tool values; the pipeline's accounting at the largest solvent rung ($30mn) is +3.19.

Monotone, positive throughout, the same shape as Germany at roughly two-thirds the magnitude,
consistent with India's weaker signal (composite gross decile Sharpe **+1.197** against Germany's
**+2.305**, both on the investable universe).

### 3c. Japan — the pre-registered out-of-sample confirmation

Japan's coverage is **99.8%**, so it was never exposed to §6's artefact. Its arm was declared in
`AMENDMENT_001D` and scored by `tools/score_amendment_001d.py`, both committed **before any
Japanese portfolio existed**.

| AUM | **channel** | HAC se | t | p | Holm 5% (of 8) |
|---|---|---|---|---|---|
| $100k | **−0.0013** | 0.0012 | −1.14 | 0.370 | 0 |
| $300k | +0.0088 | 0.0059 | +1.48 | 0.184 | 0 |
| $1mn | +0.0416 | 0.0153 | +2.72 | 0.052 | 0 |
| $2mn | +0.0821 | 0.0239 | +3.43 | 0.021 | 0 |
| $3mn | +0.1317 | 0.0343 | +3.84 | 0.010 | 0 |
| $6mn | +0.2433 | 0.0515 | +4.72 | 0.005 | 1 |
| $8mn | +0.3274 | 0.0576 | +5.68 | 0.002 | **8** |
| $10mn | +0.4033 | 0.0629 | +6.41 | 0.001 | **8** |
| $30mn | +1.0297 | 0.1191 | +8.64 | 0.0000 | **8** |
| $100mn | +2.6933 | 0.2591 | +10.40 | 0.0000 | **8** |
| $300mn | +4.9600 | 0.3701 | +13.40 | 0.0000 | **8** |
| **$1bn** | **+6.6813** | 0.6071 | **+11.01** | 0.0000 | **8** |
| $10bn | +7.1511 | 1.0123 | +7.06 | 0.0000 | **8** |

**Pre-registered prediction D2 — the channel is significantly positive at $1bn — is confirmed**,
with 11 of 14 rungs significant and 8 of 8 cells surviving Holm from $8mn upward. Composite gross
decile Sharpe +1.278.

**Two pre-registered predictions failed and one passed vacuously; all three are reported in
`AMENDMENT_001D` §11.** In short: **D3 passed on a −0.0013 reading with p = 0.370**, because I wrote
a sign prediction with no magnitude floor — a defect in my pre-registration, not evidence. **D5
failed substantively**: I predicted Japan's scaled channel at $1bn would be below Germany's because
$1bn is only 2.4x past Japan's $413mn frontier, and it came out *higher* (5.228 vs 4.00). Distance
past the frontier is **not** a sufficient statistic for how hard the constraint bites — Japan's
1,705-name breadth means far more positions hit the cap, leaving attained gross at 0.162 of 2.0.

### 3d. The unifying statement: the channel tracks how much the cap binds

All three markets at their smallest rungs, against cap slack (the shortfall of attained gross below
the 2.0 target):

| country | AUM | cap slack | channel |
|---|---|---|---|
| Germany | $1k | **0.01%** | **+0.0008** |
| **Japan** | **$100k** | **0.01%** | **−0.0009** |
| Germany | $10k | 0.09% | +0.0086 |
| India | $1k | 0.25% | +0.0175 |
| Japan | $1mn | 0.94% | +0.0313 |
| Germany | $100k | 6.69% | +0.0618 |
| India | $100k | 7.01% | +0.2114 |
| Germany | $1mn | 40.5% | +0.7954 |

> **The constraint's effect on net Sharpe is zero when it does not bind, and monotonically positive
> in how much it binds. At the registered calibration there is no scale at which it meaningfully
> hurts** - though §3g shows that a materially cheaper impact calibration would create one.

At ~0.01% slack the channel is ±0.001 and its **sign is arbitrary** — Germany +0.0008 against
Japan −0.0009 on the same cost model. Those are not two regimes, they are noise around zero. Any
"crossover" a bootstrap locates (Japan's is $115,532, CI [$101k, $349k]) is simply **the point at
which the cap begins to bind at all**, and carries no economic content.

This also explains, without claiming to adjudicate anyone, why @AHV2025 find no benefit from
turnover reduction: their cost model contains **no AUM term**, so they sit permanently at zero
slack, where this channel is zero by construction.

### 3e. Robustness

| dimension | tested | survives |
|---|---|---|
| **weighting** | equal vs value-weighted deciles | **unconfirmed on the compliant universe.** Positive and significant at scale under both on the *pre-fix* universe (t = +5.6 to +12.3 at $1bn, where the German and Indian comparison books are insolvent); the compliant re-run has not been done (`PAPER` §12.3) |
| **impact coefficient** | `k ∈ {0.5, 1, 2, 3}` (k=1 is Grinold-Kahn), on the compliant universe | **yes** — positive at scale at every k, magnitudes rising with k as the mechanism requires. See §3d: only at `k = 0.5` is there any negative region at all, and it is −0.014 |
| **impact curvature** | Kyle-linear (`exponent 2.0`) level-matched against our square-root contract - the law @NMV2016 argue for against ours | **yes** - positive at every rung in both markets, +7.74 / +3.64 at $1bn (§3g) |
| **cost-input coverage** | signal-bearing vs investable universe | **yes for the positive channel.** This is what killed the retracted sign flip, so it is the check that matters — see §6 |
| **cells** | 8 prediction cells, Holm-corrected | **yes** — 8 of 8 from $1mn upward |

Note that value weighting cuts the composite **gross** decile Sharpe by about 80% (Germany
+2.763 → +0.473, measured on the signal-bearing universe before the coverage fix), which is Novy-Marx & Velikov's critique of
equal-weighted anomaly results landing on our own gross numbers. Every gross Sharpe we quote must
carry it.

### 3f. The small-AUM limit: the channel decays to zero, it does not cross

§2 says the mechanism also implies a small-AUM regime where the cap forfeits more alpha than it
saves in cost. **We looked for it on the compliant universe and it is not there.** Germany, down to
a $1,000 mandate:

| AUM | $1k | $3k | $10k | $20k | $30k | $50k | $100k |
|---|---|---|---|---|---|---|---|
| channel | +0.0008 | +0.0021 | +0.0086 | +0.0117 | +0.0181 | +0.0189 | +0.0618 |

**Positive at every rung across seven orders of magnitude of mandate size ($1k to $10bn.)** The
channel decays smoothly to zero *from above* as AUM falls; it never crosses. So at the registered
cost model the regime in which a participation cap destroys risk-adjusted performance is **not
reachable in our data**, and we cannot claim to have observed @AHV2025's side of the literature.

**The sign is weakly `k`-dependent at the very bottom, and this is where the retracted claim's last
piece dies.** Re-running the impact-coefficient sweep on the *compliant* universe:

| k | channel at $100k | channel at $1mn | channel at $6mn |
|---|---|---|---|
| 0.5 | **−0.0142** | +0.1894 | +0.9220 |
| **1.0** | +0.0618 | +0.9174 | +2.4784 |
| 2.0 | +0.2113 | +1.8736 | +4.4578 |
| 3.0 | +0.3540 | +2.7097 | +5.3278 |

Only at `k = 0.5` does a negative region appear at all, and it is **−0.014** — economically
nothing. Its implied crossover is about $170k, and the `crossover ∝ k^(−2)` law would then put the
`k = 1` crossover near $40k. **We measured $20k, $30k and $50k directly and all three are
positive.** So the `k^(−2)` scaling that the retracted ladder appeared to confirm to within ±15%
**was a property of the artefact, not of the mechanism**, and that confirmation is withdrawn along
with it.

What survives of the `k` analysis is only the monotone and unsurprising part: the channel's
magnitude rises with `k` at every AUM, as a larger cost coefficient must make cost avoidance worth
more. The sign does not turn over anywhere an institution would operate.

### 3g. Impact curvature — the one modelling choice our closest competitor disputes

@NMV2016 use a **Kyle-linear** price impact, so their cost is linear in invested dollars, their
capacity is a single break-even point, and their "SR/$B" column is a constant slope. **Their
footnote 9 argues explicitly against concave impact functions on endogeneity grounds** — and
concave (square-root) impact is exactly our frozen contract. @KS2004 take the opposite side,
stating that concave true impact would make their convex-impact results conservative. So the
curvature of our cost law is contested by the paper closest to ours, and a referee who owns
@NMV2016 will raise it.

Total cost under our contract is `∝ Q^1.5`; Kyle-linear impact gives `∝ Q^2`. Two runs, because
the naive one is not a fair test:

| | Germany $100k | $1mn | $3mn | $1bn | $10bn |
|---|---|---|---|---|---|
| **1.5, k=1 (contract)** | +0.062 | +0.795 | +1.653 | +8.922 † | +9.256 † |
| **2.0, k=1 (uncalibrated)** | **−0.054** | **−0.160** | **−0.193** | +5.618 | +7.600 |
| **2.0, level-matched (k=4.88)** | **+0.087** | **+0.879** | **+1.729** | **+7.740** | **+8.103** |

| | India $100k | $1mn | $3mn | $1bn | $10bn |
|---|---|---|---|---|---|
| **1.5, k=1 (contract)** | +0.211 | +0.751 | +1.332 | +5.693 † | +5.967 † |
| **2.0, k=1 (uncalibrated)** | +0.079 | +0.058 | +0.079 | +3.016 | +3.660 |
| **2.0, level-matched (k=3.74)** | +0.182 | +0.560 | +0.955 | +3.643 | +3.837 |

† Under the contract cost model the uncapped book is insolvent at these German and Indian rungs. Solvency
was assessed **only under the contract cost model**, not under the sensitivity cost models, so the
$1bn and $10bn entries in every row should be read the same way until it is assessed. The
informative columns are $100k-$3mn.

**Why two runs.** For portfolio weights, `|dw| < 1`, so raising the exponent from 1.5 to 2.0 at the
same coefficient makes impact **uniformly cheaper** — it changes the cost *level* as well as its
curvature, and a cheaper cost model flatters nothing but does weaken the thing the cap is paying
for. The level-matched run fixes that: `k' = Σ c·dw^1.5 / Σ c·dw²` on the uncapped book at $1bn
preserves **aggregate impact cost** while changing only curvature, giving `k' = 4.88` (Germany) and
`3.74` (India).

**Two conclusions, and they separate cleanly.**

1. **The positive channel is robust to curvature.** Level-matched, both markets are positive at
   every rung and monotone, reaching +7.74 (Germany) and +3.64 (India) at $1bn. **A referee
   preferring Kyle-linear impact gets the same paper.**
2. **The sign at small mandates depends on the cost *level*, not its curvature.** The negative
   region in the uncalibrated row ($100k–$3mn in Germany) disappears once the level is restored, so
   it was a level artefact. But it is also exactly what §2 predicts: the cap pays only when there
   is cost worth avoiding, so a materially cheaper calibration than Grinold-Kahn `k = 1` would
   produce a region where it does not pay. **That region is a property of the cost calibration, and
   we should say so rather than claim the cap can never hurt.**

Point 2 qualifies §1 and §3d: "no scale at which it meaningfully hurts" holds **at the registered
calibration**, over $1k–$10bn, in all three markets. It is not a claim about every calibration.

## 4. The friction horse race

Capacity against cost against tax, same signals. **Capacity >> cost >> tax in both markets.**

| channel (Sharpe points, $1bn) | Germany | India |
|---|---|---|
| cost (gross → net uncapped) | −11.90 † | −7.51 † |
| **capacity** (net uncapped → net capped) | +8.92 † | +5.69 † |
| tax (net → after tax, optimised book) | **−0.111** | **−0.004** |

† Both legs use the insolvent uncapped book at $1bn: not quotable. The like-for-like ladder at the largest
solvent rung (`PAPER` §8.9): Germany $100mn cost -9.62 / capacity +6.80 / tax (capped book) -0.098;
India $30mn -5.18 / +3.19 / -0.005; Japan $1bn -9.02 / +6.92 / -0.170.

| annualised bps, optimised book, $1bn, prediction cells | Germany | India |
|---|---|---|
| cost drag | 17.21 | 9.96 |
| tax drag | 6.38 | 0.114 |
| **cost / tax** | **2.70x** | **87.4x** |

**Two corrections this exhibit forced, both standing.** The published "costs beat taxes 5x in
Germany and 53x [withdrawn] in India" are **all-16-cell** averages including the economic arm, which is not a
competent implementation; on prediction cells the ratios are **2.70x** and **87.4x**, so Germany's
margin is one order of magnitude, not two. ~~And "taxes are second-order" splits in two: true as a
channel magnitude, false as a share of what survives: Germany's book nets +0.128 and keeps +0.017
after tax, so tax removes 87% of the remaining risk-adjusted return.~~ **[WITHDRAWN: the "share of
what survives" half. Germany's +0.128 is itself indistinguishable from zero (t = +0.53), so there is
nothing for tax to remove or to decide. What stands is the channel-magnitude half: the tax channel is
two orders of magnitude below cost and capacity. See `RESULTS_TAX_THREE_COUNTRY` §4b.]**

**Limitation, stated not buried.** Cost and capacity drags are measured on the decile-spread book,
the only book with an uncapped counterfactual; tax drag on the optimised book, because the
lot-level engine runs on realised weights. Two books, so this compares orders of magnitude, not a
decomposition that sums. The bias favours the tax channel (measured on the lower-turnover book) and
it still loses. **Partly superseded:** matched-book accounting (`PAPER` §8.9) now puts cost,
capacity and tax on one book at the largest solvent rung of each market.

## 5. What is ours and what is not

**Not ours.** Measuring strategy capacity (@KS2004, @NMV2016, @GP2013). ML alpha being fragile to
frictions (@ACM2023, *Management Science*) or surviving them (@AHV2025). Turnover reduction helping
(@NMV2016 buy/hold, @KS2004 liquidity weighting). ML outside the US (@CFMZ2023, 46 markets, JEDC
2023). Capacity in the low hundreds of millions for a high-turnover strategy (@NMV2016 reports
$0.18–0.53bn, in the US).

**Ours.** The **AUM-indexed dose-response**: the capacity channel measured over five decades of
mandate size, in two non-US markets, with standard errors, and shown monotone — @NMV2016 and
@KS2004 establish that a liquidity tilt helps, but at a single scale and as a design choice, not as
a function of mandate size under an exogenous constraint. The **implementability frontier** as an
object distinct from the profitability break-even (tracker §C2). The **tax channel ruled out as
second-order** with a real lot-level engine across three statutory regimes — none of the capacity
papers has a tax engine and @NMV2016/@AHV2025 do not mention tax. And §6's **coverage-asymmetry
warning**, which is a methods contribution for non-US work.

**Withdrawn today.** The sign flip and its crossover (§6). "Frontiers 10–100x below US estimates"
(not turnover-matched; tracker §C8.1). The 5x/53x cost-over-tax ratios (all-cell averages).

## 6. The retraction, and why it is itself a result

The claim this document replaces was that the capacity channel **changes sign** — destroying 0.81
Sharpe points at a $100k German mandate and creating 11.06 at $1bn, crossing zero at
$3.79mn (95% CI $1.88–7.07mn), with both tails significant and **t = −6.10** on the negative side.

**It was an artefact of cost-input coverage.** The ladder formed deciles on the **signal-bearing**
cross-section (~382 German names a month) instead of the **investable** one (~246). The promoted C6
prices only **65.1%** of Germany's cross-section over 2009-2019 — `adv_usd` binds — against
**99.1%** of India's. Document 13 requirement 2 makes an uncertified security-month non-tradeable
and prohibits imputation (`docs/NON_TRADEABLE_TREATMENT.md`), and the ladder broke that rule in
both directions at once:

* in the **uncapped** book an uncovered name was charged **zero cost** — 35% of Germany's positions
  were traded for free, flattering the uncapped book at small AUM;
* in the **capped** book the same name received `cap = 0` and was dropped, costing the capped book
  its alpha.

Both push the channel downward and **only in Germany**. Enforcing the rule:

| Germany at $100k | non-compliant | compliant |
|---|---|---|
| gross | +2.383 | +1.998 |
| net uncapped | +1.749 | **+0.657** |
| net capped | +0.938 | +0.719 |
| **channel** | **−0.811** | **+0.062** |

India, at 99.1% coverage, is the control and barely moves: **+0.183 → +0.211**. An effect that
reverses in the 65%-coverage panel and not in the 99%-coverage panel is a coverage effect.

**Why this is worth a methods paragraph rather than a footnote.** The spurious result was
**t = −6.10**, it was monotone across nine decades of AUM, and it **survived a value-weighting
robustness check and a six-fold impact-coefficient sweep** — including a quantitative prediction
(`crossover ∝ k^−2`) that the artefact satisfied to within ±15%. A wrong result reproduced a
theoretical scaling law. Only enforcing the study's own non-tradeability rule killed it. For
cross-country work, where cost-input coverage is never complete and differs between panels, **a
coverage asymmetry can manufacture a significant, theoretically coherent, robustness-passing
cross-country contrast.** Tracker §C6 now lists coverage matching alongside turnover, units and
impact law as requirements any capacity comparison must meet.

### 6a. How far the defect spread: audited, and it is confined to one tool

Because the same mistake elsewhere would invalidate more than this exhibit, every tool and pipeline
stage that loads a country bundle was checked for whether it builds portfolio weights directly from
scores, and if so whether it enforces cost-input eligibility first.

| consumer | builds weights from scores? | eligibility enforced |
|---|---|---|
| `exp_signal_vs_portfolio_wedge.py` | **yes** | **this was the defect**; now via `--require-cost-inputs` |
| `pipelines/04_construct_portfolios.py` | yes, via the optimiser | **yes** — `optimizer.py` calls `eligible_cost_input_permnos` at both construct sites (lines 461, 611) and `partition_prior_book` for the frozen sleeve |
| `exp_capacity_dose_response.py` | no — reads optimised weights via `provenance.country_weights` | yes, inherited, and masks on finite ADV |
| `exp_book_characteristics.py`, `verify_trade_caps.py`, `exp_leverage_matched.py`, `dev_backtest.py` | no — all consume the optimised book | yes, inherited |
| `exp_112a_event_study.py`, `06_after_tax_eval.py` | no — consume realised weights | yes, inherited |

**So the capacity frontier ($106mn / $55mn / $413mn), the dose-response correlations
(+0.555 → +0.854), the book characteristics, the tax ledger and every stage-04 and stage-06 number
are unaffected**, because they all route through the optimiser, which has enforced eligibility
since the frozen-sleeve work of 8 October. The frontier in particular was already computed on
eligible names — Germany's 246, not 382 — which is why it was internally consistent and why the
non-compliant ladder's inconsistency with it was the clue worth following.

Only the one tool written today was wrong, and only for one day.

### 6b. Coverage across all three panels, and a verification worth having

| country | cost-input coverage over 2009-2019 (mean / median / min) | signal-bearing names, median | **investable names, median** | frontier's `eligible_names_median` |
|---|---|---|---|---|
| **Germany** | **0.651 / 0.654 / 0.517** | 381.5 | **246.0** | **246** |
| India | 0.991 / 1.000 / 0.004 | 349.0 | 348.5 | 348 |
| **Japan** | **0.998 / 1.000 / 0.941** | 1707.5 | 1705.0 | 1705 |

Two things follow.

**Germany is the only panel with a coverage problem.** India and Japan are both at or above 99%. So
the artefact in §6 could only ever have arisen in Germany, which is exactly where it arose, and
Japan's forthcoming test is not exposed to it. India's 0.004 minimum is a single month
(January 2009) and is the reason its ladder reports 131 months rather than 132.

**The investable counts reproduce the capacity frontier's own universe exactly** — 246 / 348.5 /
1705 against the frontier's 246 / 348 / 1705. That is a useful verification in both directions: it
confirms `--require-cost-inputs` implements the same eligibility rule the frontier was computed
under, and it confirms the frontier was right all along. It is also the clue that should have been
followed sooner: a ladder running on 382 German names while the frontier it was being compared
against ran on 246 was internally inconsistent before any result was interpreted.

## 7. Reproduction

```
python tools/exp_signal_vs_portfolio_wedge.py --country DEU --dump-monthly \
    --require-cost-inputs --tag cov \
    --aum 1e5 3e5 1e6 2e6 3e6 4e6 6e6 8e6 1e7 3e7 1e8 3e8 1e9 1e10
python tools/exp_capacity_channel_inference.py --country DEU --tag cov --n-boot 2000
python tools/exp_friction_horse_race.py --country DEU IND
```

**`--require-cost-inputs` is mandatory for any capacity exhibit.** Without it the universe is the
signal-bearing cross-section and the result is not compliant with document 13 requirement 2.

Committed evidence: `docs/attachments/WEDGE_DEU_COV_2026-10-09.csv`,
`WEDGE_IND_COV_2026-10-09.csv`, and the non-compliant ladders retained for comparison.
Test: `tests/validation/test_sharpe_difference.py` (12 tests). Suite: 450 tests, 0 failures.
