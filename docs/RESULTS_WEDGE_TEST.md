# The wedge test: which friction channel binds on a machine-learning design?

**Status:** Germany and India complete. Japan running (amendment 001B settings).
**Reproduce:** `python tools/exp_wedge_test.py --inputs outputs/summary_after_tax_DEU_1e9.csv
outputs/summary_after_tax_IND_1e9.csv`

> **Two tests have now failed, in this order, and both failures are recorded below.**
>
> 1. The **pre-registered** statistic returned the wrong sign, and was then found to be
>    ill-defined on this data (§2).
> 2. The **post-hoc replacement** I promoted after that — a turnover gradient in
>    `lt_share_of_gains` — looked strong (t = −4.36) and **does not survive** the obvious
>    robustness check (§5). It is a between-arm artefact.
>
> What survives is narrower than either: a **cross-country contrast in levels** that is a
> statutory fact rather than an estimate (§4), and a magnitude finding that reframes the claim
> (§6). Do not quote the t = −4.36.

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
tax_drag / gross  ~  theta_L   +   Delta * Phi(p, H)
                     level         holding-period channel, PROPORTIONAL TO THE WEDGE
```

`Phi(p, H)` is the share of gains pushed across the boundary by trading at rate `p`.

## 2. The pre-registered statistic failed, and was not well defined

Registered test: **slope of tax-per-unit-of-gain on turnover**, predicted zero where the wedge is
zero, positive where it is not. 16 cells per country.

| country | wedge | slope | t | significant | predicted |
|---|---|---|---|---|---|
| DEU | 0.000 | −21.99 | −1.44 | no | zero |
| IND | 0.150 | **−4.83** | **−2.59** | **yes** | **positive** |

India is **significantly the wrong sign**. The tool printed the falsification condition fixed in
advance: `PREDICTED ORDERING NOT OBTAINED`. **As pre-registered, the claim is not supported.**

The statistic is also not a valid measurement here. It divides tax paid by *mean gross return*, and
in both countries about half the cells have **negative** mean gross return:

| country | cells with `gross > 0` | corr(turnover, gross) |
|---|---|---|
| DEU | 10 of 16 | −0.773 |
| IND | 8 of 16 | −0.913 |

So for those cells it computes "tax per unit of gain" where there is no gain, and its sign tracks
which cells happen to be loss-making. It is not stable:

| specification | DEU | IND |
|---|---|---|
| as registered, all 16 cells | −21.99 (t −1.44) | −4.83 (t −2.59) |
| same ratio, cells with gains only | **+11.56** (t +0.69) | −1.54 (t −1.75) |
| levels: `tax_bps ~ turnover + gross` | −235.3 (t −1.36) | **+33.4** (t +1.65) |

**Retraction.** An earlier version of this document reported Germany's −21.99 (t = −1.44) as "the
placebo holds." That is withdrawn: the number is dominated by the sign-flipping denominator and the
inference from it was not sound.

No money-denominated form rescues this. Turnover and gross return correlate −0.77 and −0.91 across
the 16 cells because the fastest-trading cells are the loss-makers, so with n = 16 every
"tax on turnover" variant is weakly identified.

## 3. The statutory variation (frozen C14 schedule, not assumed)

Derived from `data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv` by
`alphacomb.tax.statutory`, so it cannot drift from what the dated engine resolves against.

| country | legal regime | cgt_short | cgt_long | **wedge** | boundary | STT |
|---|---|---|---|---|---|---|
| **DEU** | Abgeltungsteuer | 0.26375 | 0.26375 | **0.000** | none | 0 |
| **JPN** | normal listed + reconstruction | 0.20315 | 0.20315 | **0.000** | none | 0 |
| **IND** | STT100 / LTCG exempt | 0.15000 | 0.00000 | **0.150** | 12 months | 0.0010 |
| **IND** | Section 112A (from 2018-04-01) | 0.15000 | 0.10000 | **0.050** | 12 months | 0.0010 |

Germany and Japan are **placebos the tax code wrote**. Germany is taxed *harder* than India
(26.375% against a 15% short-term rate), so a tax-level account and a wedge account make opposed
predictions for Germany.

## 4. What stands: a cross-country contrast in levels

`lt_share_of_gains` is the share of realised gains that qualified as long-term — `1 - Phi(p, H)` as
the lot-level ledger realised it, and the object the theory's wedge term multiplies.

| country | wedge | boundary | `lt_share` across all 16 cells |
|---|---|---|---|
| **DEU** | 0.000 | none | **0.0000 — identically, in every cell** |
| **IND** | 0.150 | 12 months | **0.3826 – 0.6413** |

Germany's zero is not a small estimate with wide error bars. Under Abgeltungsteuer **no
holding-period boundary exists** for newly acquired listed shares, so there is no long-term category
for a gain to fall into: the variable the mechanism operates through does not exist. That is a fact
about which gains the statute permits, not a regression result, and it needs no standard error.

India's statute creates the category and 38–64% of realised gains land in it. **A tax-level story
cannot produce this contrast**: Germany taxes gains harder than India and has no holding-period
category whatsoever.

This is the part of the original claim that the data supports, and it is weaker than the claim.
It establishes that *statute determines whether the channel can exist*. It does **not** establish
that the channel orders the friction penalty — see §5 and §6.

## 5. What does not stand: the within-country turnover gradient

Across all 16 Indian cells, `lt_share` falls steeply with turnover: slope **−8.783, t = −4.36**,
corr −0.762. I promoted this to the primary result earlier tonight. **It does not survive splitting
by objective arm**, which is the first check it should have been given:

| sample | n | slope | t | turnover range |
|---|---|---|---|---|
| all 16 cells | 16 | −8.783 | **−4.36** | 0.0043 – 0.0226 |
| prediction-loss arm only | 8 | −5.468 | **−0.86** | 0.0043 – 0.0099 |
| economic-loss arm only | 8 | **+13.095** | +0.75 | 0.0191 – 0.0226 |

Three things kill it:

1. **The arms do not overlap in turnover at all** (`arms_turnover_overlap = False`). Every
   economic-loss cell trades faster than every prediction-loss cell. A line fitted through two
   disjoint clusters measures the gap between the clusters, so its effective n is **2, not 16**,
   and the t = −4.36 is spurious precision.
2. **Within each cluster there is nothing.** t = −0.86 in the healthy arm, and the wrong sign in
   the other.
3. **The high-turnover cluster is the arm that failed to train** (§7). So the one contrast doing
   all the work is a comparison with a broken arm.

`tools/exp_wedge_test.py` now prints the within-arm split directly above the full-sample slope and
refuses the "consistent with the channel" verdict unless the gradient survives within an arm, so
this number cannot be read in isolation again.

## 6. Magnitudes, which reframe the claim regardless

| country | mean tax drag | mean cost drag | ratio |
|---|---|---|---|
| DEU | 5.23 bps p.a. | 27.67 bps p.a. | **5x** |
| IND | **0.45 bps p.a.** | 24.30 bps p.a. | **53x** |

Transaction costs dominate taxes five to one in Germany and fifty to one in India. India's tax drag
is small *because* its wedge is large in the sheltering direction: with LTCG exempt and 38–64% of
gains long-term, most Indian gains were taxed at **zero**. Pre-2018 India's wedge is a **reward for
patience that fast trading forfeits**, not a penalty that fast trading incurs, and the reward is
bounded by how much gain there is to shelter — here, very little.

* **Supported:** the holding-period composition channel is created and bounded by statute, and is
  identically absent where the law sets a flat rate.
* **Not supported:** *the friction penalty is ordered by the wedge.* The penalty is dominated by
  transaction costs in every jurisdiction measured, by one to two orders of magnitude.

## 7. A problem with the economic-loss arm that affects the factorial too

The economic-loss cells are supposed to learn weights from net-of-cost utility, including a
`- cost(w_t - w_{t-1})` term that should make them trade *less*. In both countries they do the
opposite, and they have **negative gross Sharpe — before any costs**:

| India, by arm | gross Sharpe | net Sharpe | gross mean p.a. | turnover | cost drag |
|---|---|---|---|---|---|
| prediction-loss (P) | **+0.534** | +0.217 | +0.00158 | 0.0066 | 9.6 bps |
| economic-loss (E) | **−0.272** | −0.912 | −0.00161 | 0.0214 | 39.2 bps |

All 8 E cells have negative gross Sharpe; all 8 P cells are positive. The same pattern holds on the
German panel. An objective that prices turnover, trades 3.3x more, and earns negative gross alpha
has most likely **failed to train** rather than discovered that economic objectives are worse.

That matters beyond this page: the factorial's one significant main effect is the economic one
(DEU −0.0054, t = −3.77; IND −0.0063, 81.6% of total). If the E arm is misconfigured, that effect
measures a training failure, not a design trade-off. **This needs resolving before the factorial is
reported as a finding**, and it is the top open item.

## 8. Germany and India: what does replicate

| country | economic main effect | share of total | months |
|---|---|---|---|
| DEU | −0.0054 p.a. (t = −3.77) | — | 132 |
| IND | −0.0063 p.a. | 81.6% | 131 |

It replicates cleanly across countries — subject entirely to §7. India loses one month to
`too_few_assets`. India's prediction cells report `optimal_inaccurate` on 120–127 of 132 months
against Germany's 59–71; `tools/verify_trade_caps.py` puts 0.02–0.22% of India's trades over the
ADV cap with cumulative excess gross at most 0.76% and no cell near the 1% threshold, so that
status is a solver-tolerance label rather than a constraint violation.

## 9. Japan, and what would actually settle this

**Japan is running** under amendment 001B: `--years 2009 2019` (its panel starts in 1996; without
this it would be evaluated over 300 months against the others' 132) and `--max-names 600` (verified
bit-identical for Germany and India, binds only on Japan). Japan tests §4's contrast at a
*different* flat rate (20.315% against 26.375%): two flat-rate countries at different levels both
showing `lt_share` identically zero is much harder for a tax-level story to accommodate than one.

Outstanding, in priority order:

1. **Resolve §7.** Until the E arm is either fixed or declared broken, both the factorial's main
   effect and the turnover variation in §5 rest on it.
2. **The section 112A event study** (`tools/exp_112a_event_study.py`). India's wedge falls
   0.15 → 0.05 on 2018-04-01 *inside* the sample while Germany's and Japan's law does not move, so
   the treatment is a **date** rather than a design axis and none of §5's clustering problem
   applies. Germany's control arm is run; **it is not clean** — the levels outcome gives −0.0282
   with t = −1.24 year-clustered but **t = −2.18 cell-clustered**, a borderline-significant gradient
   in a country where no law changed, which caps what India's arm can claim. India's arm is
   running. The India-minus-Germany difference is the statistic that survives, not India's level.
3. **Turnover variation that is not the E/P axis.** §5 failed because the design's only large
   turnover variation is confounded with the broken arm. A turnover sweep *within* the
   prediction-loss arm (varying the cost multiplier or the turnover penalty) would give overlapping
   support and a real gradient test.

## 10. What this does and does not establish

Three countries, 16 cells each, and — after §5 — effectively two turnover clusters per country. The
surviving claim rests on an *ordering across jurisdictions that statute fixes in advance*, which is
the design's strength, and on nothing within-country.

The test has **falsified** twice tonight, cleanly and on the record: the registered
money-denominated test returned the wrong sign (§2), and the post-hoc mechanism gradient did not
survive its first robustness check (§5). Both are reported here rather than buried, which is the
only reason the surviving §4 contrast is worth anything.
