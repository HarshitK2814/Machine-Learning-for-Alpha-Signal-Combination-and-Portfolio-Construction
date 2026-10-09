# The ADV participation constraint creates risk-adjusted performance, and the effect grows with mandate size

**Date:** 2026-10-09, 12:35 IST
**Supersedes:** `docs/RESULTS_SIGN_FLIP_2026-10-09.md`, whose central claim — a sign flip with a
measurable crossover — **was retracted the same day as a cost-input coverage artefact.** That
document is kept as the record; §6 here explains what happened and why it matters methodologically.
**Status:** exploratory on Germany and India. Japan's stage 02 is on its final cell and **has not
reported**.
**Audience:** referee-facing. Every number is reproducible from §7.

---

## 1. The claim

> For an institutional investor in a mid-size equity market, the ADV participation constraint
> **improves** net risk-adjusted performance at every mandate size we can measure, and the
> improvement **grows monotonically with AUM**: from +0.07 Sharpe points at a $100k mandate to
> **+8.92** at $1bn in Germany, and +0.26 to **+5.69** in India. It does so because it suppresses
> turnover faster than it suppresses signal. The tax channel, measured with a lot-level engine
> across three statutory regimes, is **two to three orders of magnitude smaller** than either the
> cost or the capacity channel.

**What this is not.** It is not a sign flip, not a crossover, and not an adjudication of the
disagreement in the literature about whether turnover reduction helps. We **never observe** the
regime in which the constraint hurts, so we cannot speak to it. See §6.

## 2. The mechanism

    net Sharpe = (alpha_eff - kappa * G^0.5) / sigma ,      kappa ∝ sqrt(AUM / ADV)

A participation cap lowers attainable gross `G` and per-name turnover. It lowers `alpha_eff`
roughly linearly in the positions it forfeits but lowers the cost term as `G^0.5`, so it pays
whenever `kappa` is large relative to alpha. Since `kappa` grows as `sqrt(AUM/ADV)`, the benefit
must grow with mandate size — which is what §3 measures, over five decades.

The same expression says there should exist a small-AUM regime where the cap costs more alpha than
it saves in cost. **We do not reach it.** At our smallest measurable mandate ($100k) the channel is
already positive, though insignificantly so (Germany t = +1.22, p = 0.178). The honest reading is
that the regime exists in theory and lies below the scale at which our data can resolve it.

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
| $300mn | −0.611 | −9.083 | **+8.471** | 0.794 | +10.66 | 0.0000 | **8** |
| **$1bn** | **−0.675** | **−9.597** | **+8.922** | 0.803 | **+11.11** | 0.0000 | **8** |
| $10bn | −0.675 | −9.931 | **+9.256** | 0.810 | +11.43 | 0.0000 | **8** |

**Significant at 5% on 13 of 14 rungs; 8 of 8 cells survive Holm at every rung from $1mn upward.**
**No crossover: 94.1% of replications show no sign change anywhere in $100k..$10bn.**

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
| $100mn | −0.814 | −5.405 | **+4.591** | 0.865 | +5.31 | 0.0075 | 6 |
| $300mn | −0.634 | −5.969 | **+5.335** | 0.972 | +5.49 | 0.0055 | 7 |
| **$1bn** | **−0.623** | **−6.315** | **+5.693** | 0.998 | **+5.70** | 0.0035 | 7 |
| $10bn | −0.623 | −6.589 | **+5.967** | 1.015 | +5.88 | 0.0025 | 7 |

**Significant at 5% on all 14 rungs**, 7–8 of 8 cells surviving Holm at every rung. **100% of
replications show no sign change** — India is the cleanest statement of the result in the study.

Monotone, positive throughout, the same shape as Germany at roughly two-thirds the magnitude,
consistent with India's weaker signal (composite gross decile Sharpe **+1.197** against Germany's
**+2.305**, both on the investable universe).

### 3c. Robustness

| dimension | tested | survives |
|---|---|---|
| **weighting** | equal vs value-weighted deciles | **yes** — positive and significant at scale in both markets under both (t = +5.6 to +12.3 at $1bn) |
| **impact coefficient** | `k ∈ {0.5, 1, 2, 3}` (k=1 is Grinold-Kahn) | **yes** — positive at scale at every k; magnitudes rise with k as the mechanism requires |
| **cost-input coverage** | signal-bearing vs investable universe | **yes for the positive channel.** This is what killed the retracted sign flip, so it is the check that matters — see §6 |
| **cells** | 8 prediction cells, Holm-corrected | **yes** — 8 of 8 from $1mn upward |

Note that value weighting cuts the composite **gross** decile Sharpe by about 80% (Germany
+2.763 → +0.473, measured on the signal-bearing universe before the coverage fix), which is Novy-Marx & Velikov's critique of
equal-weighted anomaly results landing on our own gross numbers. Every gross Sharpe we quote must
carry it.

## 4. The friction horse race

Capacity against cost against tax, same signals. **Capacity >> cost >> tax in both markets.**

| channel (Sharpe points, $1bn) | Germany | India |
|---|---|---|
| cost (gross → net uncapped) | −11.90 | −7.51 |
| **capacity** (net uncapped → net capped) | **+8.92** | **+5.69** |
| tax (net → after tax, optimised book) | **−0.111** | **−0.004** |

| annualised bps, optimised book, $1bn, prediction cells | Germany | India |
|---|---|---|
| cost drag | 17.21 | 9.96 |
| tax drag | 6.38 | 0.114 |
| **cost / tax** | **2.70x** | **87.4x** |

**Two corrections this exhibit forced, both standing.** The published "costs beat taxes 5x in
Germany and 53x in India" are **all-16-cell** averages including the economic arm, which is not a
competent implementation; on prediction cells the ratios are **2.70x** and **87.4x**, so Germany's
margin is one order of magnitude, not two. And "taxes are second-order" splits in two: true as a
**channel magnitude** (0.111 against 8.9–11.6), false as a **share of what survives** — Germany's
book nets +0.128 and keeps **+0.017** after tax, so tax removes **87%** of the remaining
risk-adjusted return.

**Limitation, stated not buried.** Cost and capacity drags are measured on the decile-spread book,
the only book with an uncapped counterfactual; tax drag on the optimised book, because the
lot-level engine runs on realised weights. Two books, so this compares orders of magnitude, not a
decomposition that sums. The bias favours the tax channel (measured on the lower-turnover book) and
it still loses.

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
