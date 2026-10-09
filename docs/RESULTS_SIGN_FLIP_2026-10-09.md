# When does a liquidity constraint help a machine-learning strategy?

**Date:** 2026-10-09
**Status:** exploratory on Germany and India. Japan is the pre-registered confirmation sample
(`AMENDMENT_001D`, declared and revised before any Japanese portfolio existed) and **has not
reported**.
**Audience:** referee-facing. Every number here is reproducible from the tools named in section 7.

---

## 1. The claim

> The effect of an ADV participation constraint on net risk-adjusted performance is **monotone in
> mandate size and changes sign**. In Germany the constraint **destroys** 0.81 Sharpe points at a
> $100k mandate and **creates** 11.06 at $1bn, crossing zero at **$3.79mn (95% CI $1.88mn–$7.07mn)**.
> Both tails are significant at 5% under a paired test with Holm correction across eight cells. In
> India no crossover exists at any measurable scale: the constraint helps everywhere.

This matters because the literature disagrees about this sign **in print**, and all parties are US:

| | finding | our reading |
|---|---|---|
| Novy-Marx & Velikov, **RFS 2016** | the buy/hold spread is "the most effective" cost mitigation; cutting turnover **helps** | they price impact at scale: large `kappa` |
| Korajczyk & Sadka, **JF 2004** | liquidity weighting raises momentum's break-even fund size from ~$1mn (equal-weighted) to **>$5bn** — a factor of 5,000 from the tilt alone | same: large `kappa` |
| Azevedo, Hoegner & Velikov, **2025** | the same mitigations cut turnover and cost but **do not improve** net performance; costs are only 20–25bp/month post-decimalisation | marginal trader: `kappa ≈ 0` |

All three are right about their own setting. The disagreement is not empirical, it is **positional**.

## 2. The mechanism, in one line

    net Sharpe = (alpha_eff - kappa * G^0.5) / sigma ,      kappa ∝ sqrt(AUM / ADV)

A participation cap lowers attainable gross `G` and per-name turnover. It lowers `alpha_eff`
roughly **linearly** in the positions it forfeits, but lowers the cost term as **`G^0.5`**.
Tightening therefore helps **iff `kappa` is large relative to alpha**. Azevedo et al.'s cost model
contains no AUM term at all, so for them a cap can only forfeit alpha; Novy-Marx & Velikov and
Korajczyk & Sadka are at the other end. One expression, both published findings.

**The prediction this makes, and that we test:** there is a crossover, it is market-specific, and
the channel is monotone in AUM on either side of it.

## 3. The result

Composite portfolio: one equal-weighted book of the eight prediction cells, built from the same
stage-02 scores, 132 months, 2009-01..2019-12. Channel = `SR(net, capped) − SR(net, uncapped)`,
tested with the paired Ledoit-Wolf studentized stationary bootstrap (2,000 replications, block 6).

### 3a. Germany — the sign flips, and both tails are significant

| AUM | SR capped | SR uncapped | **channel** | HAC se | t | p | Holm 5% |
|---|---|---|---|---|---|---|---|
| $100k | +0.938 | +1.749 | **−0.811** | 0.133 | **−6.10** | 0.0000 | **8/8** |
| $300k | +0.704 | +1.505 | **−0.801** | 0.134 | **−5.99** | 0.0000 | **8/8** |
| $1mn | +0.406 | +1.028 | **−0.622** | 0.155 | **−4.01** | 0.0005 | 3/8 |
| $2mn | +0.252 | +0.595 | −0.343 | 0.184 | −1.87 | 0.072 | 1/8 |
| $3mn | +0.120 | +0.265 | −0.145 | 0.204 | −0.71 | 0.495 | 0/8 |
| **$3.79mn** | | | **0 (crossover)** | | | | |
| $4mn | +0.022 | −0.012 | +0.033 | 0.227 | +0.15 | 0.892 | 0/8 |
| $8mn | −0.171 | −0.849 | **+0.678** | 0.294 | **+2.30** | 0.029 | 1/8 |
| $10mn | −0.234 | −1.179 | **+0.945** | 0.319 | **+2.96** | 0.008 | 3/8 |
| $100mn | −0.396 | −6.481 | **+6.085** | 0.625 | **+9.74** | 0.0000 | **8/8** |
| $1bn | −0.580 | −11.635 | **+11.055** | 0.901 | **+12.27** | 0.0000 | **8/8** |
| $10bn | −0.586 | −13.240 | **+12.655** | 0.975 | **+12.99** | 0.0000 | **8/8** |

**Crossover $3,791,348, 95% bootstrap CI [$1,879,622, $7,074,104].** Zero of 2,000 replications
failed to show a sign change. The insignificant band ($2mn–$7mn) is the crossover region, which is
what one should expect: the channel is near zero there by construction.

### 3b. India — no crossover; the cap helps everywhere

| AUM | **channel** | t | p | Holm 5% |
|---|---|---|---|---|
| $1k | +0.004 | +0.13 | 0.893 | 0/8 |
| $3k | +0.028 | +0.98 | 0.284 | 0/8 |
| $10k | +0.058 | +1.76 | 0.036 | 0/8 |
| $100k | +0.232 | +4.12 | 0.0000 | 3/8 |
| $1mn | +0.827 | +4.21 | 0.0005 | 8/8 |
| $10mn | +2.434 | +4.65 | 0.0075 | 8/8 |
| $1bn | +5.552 | +5.66 | 0.0030 | 7/8 |
| $10bn | +5.822 | +5.85 | 0.0015 | 7/8 |

The point estimate is **no crossover in range**, and **50.8% of replications show no sign change**
anywhere in $1k..$10bn.

**The precise statement, which is weaker than "India has no crossover".** India's channel at the
bottom of the ladder is **indistinguishable from zero** (+0.004, t = +0.13, p = 0.89 at $1k), not
reliably positive. Roughly half the bootstrap replications do cross zero somewhere; the other half
do not. So the honest claim is **"no crossover is detectable in India, and if one exists it is
below the scale at which the constraint does anything measurable"** — not that India's constraint
is provably never harmful. What *is* established for India is the positive half: significantly
positive from $10k upward, 8 of 8 cells under Holm from $300k to $10mn.

**Either way the flip is not universal**, and that is what matters for the claim: Germany's
crossover is a real, bounded quantity and India's is not, so the existence of a negative region
cannot be read off market depth. That is why `AMENDMENT_001D` D3 had to be made conditional.

### 3c. Why the two markets differ — hypothesis, not claim

The crossover is **not** a fixed multiple of the capacity frontier: Germany's is 3.6e-2 of its
$106mn frontier, India has none at all, and the frontier ratio is only 1.9x. Depth alone does not
set it.

The candidate explanation is the **share of alpha in the illiquid tail**. Germany's composite gross
decile Sharpe is **+2.763** against India's **+1.209**, so Germany forfeits more than twice as much
signal per unit of gross the cap removes and needs a correspondingly larger cost saving before
capping pays. This is testable, it is what `AMENDMENT_001D` D3 now tests on Japan, and it is
labelled a hypothesis throughout.

### 3d. A candidate regularity

The asymptotic channel scaled by the composite gross Sharpe: Germany 12.655/2.763 = **4.58**, India
5.822/1.209 = **4.82**. Agreement within 5% on n = 2. Pre-registered as a secondary prediction
(D4) only; it should not be leaned on.

## 3e. The impact coefficient: the mechanism predicts its own sensitivity, and is confirmed

`k = 1` is Grinold-Kahn and is an assumption, not an estimate. Because the channel's sign depends
on `kappa ∝ k·sqrt(AUM/ADV)`, the crossover must move with `k` — and the mechanism says exactly
how. The crossover sits where `kappa` reaches a critical value, so `k·sqrt(AUM)` is constant there
and therefore

> **crossover AUM ∝ k^(−2).**

That is a quantitative, falsifiable prediction about a nuisance parameter. Germany, composite
channel, `k` swept over a six-fold range:

| k | crossover | crossover × k² | min channel below $1mn | channel at $1bn |
|---|---|---|---|---|
| 0.5 | **$16.56mn** | 4.14mn | −0.909 | +8.62 |
| **1.0** | **$3.79mn** | **3.79mn** | −0.811 | +11.06 |
| 2.0 | **$1.06mn** | 4.24mn | −0.802 | +11.84 |
| 3.0 | **$0.55mn** | 4.97mn | −0.791 | +11.76 |

Three things follow, and they matter more than the point estimate did.

1. **The sign flip exists at every `k` tested.** Every column has a negative region below $1mn and
   a strongly positive channel at $1bn. The *existence* of the flip does not depend on the impact
   coefficient at all; only its location does.
2. **`crossover × k²` is constant to within about ±15% for `k ≤ 2`**, drifting mildly at `k = 3`.
   The mechanism's own prediction about how the crossover scales with the cost coefficient is
   confirmed over a six-fold range. This is internal validation of the comparative static that does
   **not** depend on Japan.
3. **The depth of the negative region is almost invariant to `k`** (−0.79 to −0.91). That is what
   the mechanism implies: at small mandates the cap's damage is nearly pure alpha forfeiture, which
   has no `k` in it, while the cost saving it buys is negligible.

So section 6's warning that `k` was "the largest unquantified sensitivity" is **discharged**: the
qualitative claim is robust to `k`, and the quantitative claim about the crossover's location
should be quoted as **$3.79mn at `k = 1`, moving as `k^(−2)`**, with the CI in section 3a
conditional on `k = 1`. A referee who prefers `k = 2` gets $1.06mn and the same paper.

Data: `outputs/signal_vs_portfolio/impact_k_sensitivity_DEU.csv`.

## 4. The friction horse race

Capacity against cost against tax, same signals. **The ordering is capacity >> cost >> tax in both
markets**, and in scale-invariant Sharpe points the tax channel is two to three orders of magnitude
below the other two.

| channel (Sharpe points, $1bn) | Germany | India |
|---|---|---|
| cost (gross -> net uncapped) | **−14.40** | **−7.38** |
| capacity (net uncapped -> net capped) | **+11.06** | **+5.55** |
| tax (net -> after tax, optimised book) | **−0.111** | **−0.004** |

| annualised bps, optimised book, $1bn, prediction cells | Germany | India |
|---|---|---|
| cost drag | 17.21 | 9.96 |
| tax drag | 6.38 | 0.114 |
| **cost / tax** | **2.70x** | **87.4x** |

### 4a. Two corrections this exhibit forced

**The published "costs beat taxes 5x in Germany and 53x in India" are all-16-cell averages** that
include the economic arm, which is not a competent implementation
(`docs/ECONOMIC_ARM_CAPABILITY_GAP.md`) and over-trades at the wrong gross. On the prediction cells
alone — the only cells whose scores carry signal, and the only cells 001C and 001D concern — the
ratios are **2.70x** and **87.4x**. Germany's margin is **one** order of magnitude, not two.

**"Taxes are second-order" needs splitting in two**, and the honest version is more interesting:

* **As a channel magnitude: yes, decisively.** 0.111 Sharpe points against 11–14.
* **As a share of what survives: no.** Germany's optimised book nets **+0.128** Sharpe and keeps
  **+0.017** after tax — tax removes **87%** of the surviving risk-adjusted return. India's nets
  +0.205 and keeps +0.201, so there the answer is yes on both readings.

So the tax machinery is not vindicated as a headline and is not dismissed either: once cost and
capacity have done their work, what is left in Germany is small enough that a 26.375% flat rate
takes most of it. That is worth a paragraph, not a paper.

### 4b. The limitation, stated rather than buried

Cost and capacity drags are measured on the **decile-spread book**, because that is the only book
for which an uncapped counterfactual exists. Tax drag is measured on the **optimised book**, because
the lot-level engine runs on realised weights. These are two different books, so the table compares
**orders of magnitude, not a decomposition that sums**. It is not fixable by arithmetic: the
uncapped *optimised* book cannot be constructed at all, which is itself a finding of this project
(two backtest refusals, `docs/RESULTS_CAPACITY_2026-10-09.md`). The direction of the bias favours
the tax channel — it is measured on the lower-turnover, constrained book — and it still loses.

## 5. What is ours and what is not

**Not ours.** Measuring strategy capacity (@KS2004, @NMV2016, @GP2013). Showing ML alpha is fragile
to frictions (@ACM2023, *Management Science*). Showing it survives (@AHV2025). Showing turnover
reduction can help (@NMV2016, @KS2004). Applying ML to the cross-section outside the US
(@CFMZ2023, 46 markets, JEDC 2023). Reporting capacity in the low hundreds of millions for a
high-turnover strategy (@NMV2016 reports $0.18–0.53bn, in the US).

**Ours.** That the sign is **scale-dependent**, that the crossover is **measurable with a
confidence interval**, that the published endpoints are **limiting cases of one expression**, that
the crossover is **not a fixed multiple of the capacity frontier**, and that the tax channel is
**two to three orders below** the other two with a real lot-level engine across three statutory
regimes. Plus the **implementability frontier** as an object distinct from the profitability
break-even every prior paper reports (tracker §C2).

**Withdrawn.** "Our frontiers are 10–100x below published US estimates." Not turnover-matched; see
tracker §C8.1.

## 6. What would change the conclusion

* **Japan**, per `AMENDMENT_001D` D1–D5. D2 (channel significantly positive at $1bn) and D3
  (conditional: Japan resembles Germany if its gross Sharpe exceeds India's) are the real tests.
  D3 can come out void, and then the flip rests on **Germany alone** and must be reported so.
* ~~**The impact coefficient.**~~ **DISCHARGED, see §3e.** Swept over `k ∈ {0.5, 1, 2, 3}`: the
  sign flip exists at every value, `crossover × k²` is constant to within ±15% for `k ≤ 2` exactly
  as the mechanism predicts, and the depth of the negative region is almost invariant to `k`. The
  crossover CI in §3a remains conditional on `k = 1`, and that conditioning must be stated.
* **Decile-spread construction.** Equal-weighted within decile. @NMV2016 show equal-weighting
  flatters small illiquid names and is "misleading" net of costs; that is precisely the alpha our
  cap removes in Germany, so the flip's location is sensitive to this choice. A value-weighted
  ladder is the obvious robustness check and has not been run.

## 7. Reproduction

```
python tools/exp_signal_vs_portfolio_wedge.py --country DEU --dump-monthly \
    --aum 1e5 3e5 1e6 2e6 3e6 4e6 5e6 6e6 7e6 8e6 1e7 3e7 1e8 1e9 1e10 --tag infer
python tools/exp_capacity_channel_inference.py --country DEU IND --n-boot 2000
python tools/exp_friction_horse_race.py --country DEU IND
```

Committed evidence: `docs/attachments/CAPACITY_CHANNEL_LADDER_2026-10-09.csv`,
`CAPACITY_CHANNEL_INFERENCE_{DEU,IND}_2026-10-09.csv`, `CROSSOVER_INTERVALS_2026-10-09.csv`.
Test: `tests/validation/test_sharpe_difference.py` (12 tests).
