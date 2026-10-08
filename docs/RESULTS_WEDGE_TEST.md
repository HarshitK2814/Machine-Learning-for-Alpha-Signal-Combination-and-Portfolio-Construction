# The wedge test: which friction channel binds on a machine-learning design?

**Status:** Germany and India complete. Japan running (amendment 001B settings).
**Reproduce:** `python tools/exp_wedge_test.py --inputs outputs/summary_after_tax_DEU_1e9.csv
outputs/summary_after_tax_IND_1e9.csv`

> **Read §2 first.** The pre-registered statistic **failed**, and separately turned out to be
> **ill-defined on this data**. The result reported here rests on a different statistic, promoted
> after that failure. That sequence is the most important thing on this page.

---

## 1. The claim being tested

From `research/05_Selected_Research_Design/REFRAMED_CLAIM.md`:

> Machine-learning portfolio research controls frictions by penalising turnover. For a taxable
> investor the binding friction is not turnover but **holding-period composition**. The friction
> penalty on a machine-learning design is ordered by each country's statutory **holding-period
> wedge**, not by its transaction tax, and is **identically zero** in jurisdictions whose law sets
> a flat capital-gains rate.

Theory (`alphacomb.theory.tax_model`), at turnover `p`, boundary `H`, wedge `Delta`:

```
R(p) = g(1 - theta_L) - kappa*p - g * Delta * Phi(p, H)

tax_drag / gross  ~  theta_L   +   Delta * Phi(p, H)
                     level         holding-period channel, PROPORTIONAL TO THE WEDGE
```

`Phi(p, H)` is the share of gains pushed across the boundary by trading at rate `p`.

## 2. The pre-registered statistic failed, and was not well defined

The registered test was the **slope of tax-per-unit-of-gain on turnover**, predicted zero where the
wedge is zero and positive where it is not. Run as registered, on 16 cells per country:

| country | wedge | slope | t | significant | predicted sign |
|---|---|---|---|---|---|
| DEU | 0.000 | −21.99 | −1.44 | no | zero |
| IND | 0.150 | **−4.83** | **−2.59** | **yes** | **positive** |

India's slope is **significantly negative — the opposite of the prediction**. The tool printed
`PREDICTED ORDERING NOT OBTAINED - the claim as written is not supported`, which was the
falsification condition fixed in advance. **As pre-registered, the claim is not supported.**

Diagnosing that failure found the statistic is not a valid measurement here. It divides tax paid by
*mean gross return*, and in both countries roughly half the cells have a **negative** mean gross
return — the economic-loss cells lose money:

| country | cells with `gross > 0` | corr(turnover, gross) |
|---|---|---|
| DEU | 10 of 16 | −0.773 |
| IND | 8 of 16 | −0.913 |

So the denominator changes sign across the sample, and for those cells the statistic is "tax per
unit of gain" computed where there are no gains. Its sign is therefore an artefact of which cells
happen to be loss-making, and it is not stable:

| specification | DEU | IND |
|---|---|---|
| pre-registered, all 16 cells | −21.99 (t −1.44) | −4.83 (t −2.59) |
| same ratio, cells with gains only | **+11.56** (t +0.69) | −1.54 (t −1.75) |
| levels: `tax_bps ~ turnover + gross` | −235.3 (t −1.36) | **+33.4** (t +1.65) |

Germany's slope flips sign between the first two rows; India's flips between the first and third.
**This also retracts the earlier reading of the German placebo.** The previous version of this
document reported Germany's −21.99 (t = −1.44) as "the placebo holds." That number is not evidence
of anything: it is dominated by the same sign-flipping denominator, and the conclusion drawn from
it was luck rather than inference. The German placebo does hold, but for the reason in §4, not that
one.

The levels specification is no rescue either. Turnover and gross return are nearly collinear across
the 16 cells (−0.77, −0.91) because the cells that trade fastest are the ones that lose money, so
with n = 16 the tax-on-turnover slope is weakly identified in every money-denominated form.

## 3. The statutory variation (frozen C14 schedule, not assumed)

Regimes are **derived** from `data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv`
by `alphacomb.tax.statutory`, so they cannot drift from what the dated engine resolves against.

| country | legal regime | cgt_short | cgt_long | **wedge** | boundary | STT |
|---|---|---|---|---|---|---|
| **DEU** | Abgeltungsteuer | 0.26375 | 0.26375 | **0.000** | none | 0 |
| **JPN** | normal listed + reconstruction | 0.20315 | 0.20315 | **0.000** | none | 0 |
| **IND** | STT100 / LTCG exempt | 0.15000 | 0.00000 | **0.150** | 12 months | 0.0010 |
| **IND** | Section 112A (from 2018-04-01) | 0.15000 | 0.10000 | **0.050** | 12 months | 0.0010 |

Germany and Japan are **placebos the tax code wrote**, not placebos we constructed, and Germany is
taxed *harder* than India (26.375% against a 15% short-term rate) — so a tax-level account and a
wedge account make opposed predictions for Germany.

## 4. The mechanism, measured directly — and this is post-hoc

Rather than the monetary consequence, measure the channel itself. `lt_share_of_gains` is the share
of realised gains that qualified as long-term: it is `1 - Phi(p, H)` as the lot-level ledger
actually realised it, and it is the object the theory's wedge term multiplies.

| country | wedge | boundary | `lt_share` range | slope on turnover | t | corr |
|---|---|---|---|---|---|---|
| **DEU** | 0.000 | none | **0.0000 – 0.0000** | — | — | — |
| **IND** | 0.150 | 12m | **0.3826 – 0.6413** | **−8.783** | **−4.36** | −0.762 |

* **Germany: `lt_share` is identically 0.0000 in all 16 cells.** This is the placebo in its
  strongest possible form. Not a slope near zero with wide error bars — *no variation at all*,
  because under Abgeltungsteuer no holding-period boundary exists for newly acquired listed shares,
  so there is no long-term category for a gain to fall into. The variable the mechanism operates
  through does not exist.
* **India: `lt_share` falls steeply and significantly with turnover**, from 0.64 in the
  slowest-trading cell to 0.38 in the fastest. The design choice moves **26 percentage points of
  realised gains across the 12-month boundary** — from a 0% rate to a 15% one, under the
  pre-2018 exemption.

This is the predicted cross-country ordering, and a tax-level story cannot produce it: Germany taxes
gains harder than India and shows no holding-period channel whatsoever.

**It is post-hoc, and that must travel with the number.** `lt_share_of_gains` is not newly invented
— it is a frozen column of the stage-06 report and is the theory's own `Phi` — but the decision to
lead with it was taken *after* the registered statistic failed. Anyone reading this should treat §4
as a strong descriptive finding and a hypothesis for confirmation, not as a pre-registered test
that passed. The honest status is: **the registered test failed; the mechanism it was supposed to
proxy for shows the predicted pattern when measured directly.**

A caveat on what the slope means. Turnover is not randomly assigned across the 16 cells — the
economic-loss axis drives both high turnover and short holding periods — so "faster designs realise
fewer long-term gains" is close to arithmetic within a country. The non-arithmetic content is
entirely in the **cross-country contrast**: the same arithmetic has a tax consequence in India and
exactly none in Germany, and that difference is set by statute rather than by us.

## 5. Magnitudes, before anyone calls this large

| country | mean tax drag | mean cost drag | ratio |
|---|---|---|---|
| DEU | 5.23 bps p.a. | 27.67 bps p.a. | **5x** |
| IND | **0.45 bps p.a.** | 24.30 bps p.a. | **53x** |

The holding-period channel is real, and statutorily ordered, and **economically second-order in
this sample**. Transaction costs dominate taxes five to one in Germany and fifty to one in India.

India's tax drag is tiny *because* its wedge is large in the sheltering direction: with LTCG exempt
and 38–64% of gains qualifying as long-term, most Indian gains were taxed at **zero**. The wedge in
pre-2018 India therefore operates as a **reward for patience that fast trading forfeits**, not as a
penalty that fast trading incurs, and the size of the reward is bounded by how much gain there is
to shelter — which in this sample is small.

That reframes the paper's claim rather than confirming it as written. Supported: *the
holding-period composition channel is created and bounded by statute, and is identically absent
where the law sets a flat rate.* Not supported: *the friction penalty is ordered by the wedge* — the
penalty is dominated by transaction costs in all three jurisdictions.

## 6. Germany and India: the net-of-cost factorial replicates

Independently of the tax question, the economic-loss main effect reproduces across countries:

| country | economic main effect | share of total | months |
|---|---|---|---|
| DEU | −0.0054 p.a. (t = −3.77) | — | 132 |
| IND | **−0.0063 p.a.** | **81.6%** | 131 |

India loses one month to `too_few_assets`, so 131 rather than 132. India's prediction cells report
`optimal_inaccurate` on 120–127 of 132 months against Germany's 59–71; `tools/verify_trade_caps.py`
puts 0.02–0.22% of India's trades over the ADV cap with cumulative excess gross at most 0.76% and
no cell near the 1% threshold, so the status is a solver-tolerance label rather than a constraint
violation.

## 7. Japan, and what would strengthen this

**Japan is running** under amendment 001B: `--years 2009 2019` (its panel starts in 1996, and
without this it would be evaluated over 300 months against the others' 132) and `--max-names 600`
(verified bit-identical for Germany and India; binds only on Japan). Japan is the strongest
available replication of §4's Germany result, because it is flat-rate at a **different level**
(20.315% against 26.375%). Two flat-rate countries at different rates both showing `lt_share`
identically zero is much harder for a tax-level story to accommodate than one.

Also outstanding:

* **The section 112A event study** (`tools/exp_112a_event_study.py`, Germany arm run, India arm
  pending). India's wedge falls 0.15 → 0.05 on 2018-04-01 *inside* the sample while Germany's and
  Japan's law does not move, which gives a within-country test that does not depend on the
  cross-sectional turnover ranking at all. This is the most valuable thing left, because it is the
  one design here whose treatment is a date rather than a design axis.
* **A pre-registered re-test of §4.** The mechanism result should be re-registered as a primary
  hypothesis and confirmed out of sample before the paper leans on it.

## 8. What this does and does not establish

Three countries, 16 cells each, so every slope is estimated on 16 points and the cross-country
degrees of freedom are three. The claim rests on an *ordering across jurisdictions that statute
fixes in advance*, which is the design's strength — the treatment is assigned by tax law rather
than by us — and also its limit.

The test can **falsify** cleanly: a non-zero `lt_share` gradient in a flat-rate country would do
it, and the registered money-denominated test did in fact return the wrong sign, which is recorded
in §2 rather than buried. It can **confirm** only as far as three jurisdictions, one sample period,
one AUM level, and a post-hoc choice of statistic allow.
