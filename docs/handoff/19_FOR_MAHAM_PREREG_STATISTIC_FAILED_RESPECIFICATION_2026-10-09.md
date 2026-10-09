# For Maham (workstream C): two tests failed tonight. Please rule on what is left.

**From:** Harshit, workstream B
**Date:** 2026-10-09, 02:10 IST. **Revised 02:35 IST - please read the UPDATE below first.**

---

## UPDATE at 02:35, before you read anything else

When I wrote this at 02:10 I was asking you to rule on a post-hoc statistic (§3) that looked
strong: India's `lt_share_of_gains` falling with turnover, slope -8.78, **t = -4.36**.

**I then ran the obvious robustness check and it does not survive.** Splitting by objective arm:

| sample | n | slope | t | turnover range |
|---|---|---|---|---|
| all 16 cells | 16 | -8.783 | **-4.36** | 0.0043 - 0.0226 |
| prediction-loss arm only | 8 | -5.468 | **-0.86** | 0.0043 - 0.0099 |
| economic-loss arm only | 8 | **+13.095** | +0.75 | 0.0191 - 0.0226 |

The two arms occupy **disjoint** turnover ranges - every economic-loss cell trades faster than
every prediction-loss cell - so a line through all 16 is measuring the gap between two tight
clusters and its effective n is **2, not 16**. Within either cluster there is nothing, and the
high-turnover cluster is the arm that failed to train (see the new §7 below). **The t = -4.36 is
spurious and I am withdrawing §3's claim before you spend time on it.** The tool now prints the
within-arm split above the full-sample slope and refuses the favourable verdict unless the
gradient survives within an arm.

So the question for you is no longer "is this respecification acceptable". It is narrower:

* **What survives** is a cross-country contrast in *levels*: `lt_share` is identically 0.0000 in
  every German cell because Abgeltungsteuer creates no long-term category at all, against
  0.3826-0.6413 in India. That is a statutory fact about which gains can exist, not an estimate,
  and needs no standard error. A tax-LEVEL story cannot produce it - Germany is taxed at 26.375%
  against India's 15% and has no category whatsoever.
* **What does not** is any within-country turnover gradient, in any specification I have tried.
* **Separately, §7 is now the top blocker** and I would value your read on it more than on
  anything else here.

I have kept §1-§6 below as originally written, because the sequence matters and I do not want to
present a tidied-up version of how this went.

---
**Decision needed from you:** whether the respecification in §3 is acceptable, and if so under what
label it may appear in the paper. I have **not** written it up as a passed test. See §5 for the
three options as I see them.

Also still outstanding from before: your countersignature on **amendment 001A**, and now on
**001B** (`docs/AMENDMENT_001B_UNIVERSE_BREADTH_CAP.md`, the Japanese universe cap).

---

## 1. What was registered, and what it returned

The registered test of the wedge claim was the **slope of tax-per-unit-of-gain on turnover**, by
country: predicted zero where the statutory wedge is zero, positive where it is not. 16 factorial
cells per country, HIFO lots, 2009-2019.

| country | wedge | slope | t | significant | predicted |
|---|---|---|---|---|---|
| DEU | 0.000 | −21.99 | −1.44 | no | zero |
| IND | 0.150 | **−4.83** | **−2.59** | **yes** | **positive** |

India is significantly negative — the **wrong sign**. The falsification condition was fixed in
advance and the tool printed it: `PREDICTED ORDERING NOT OBTAINED - the claim as written is not
supported`. I am treating that as binding: as registered, the claim is not supported.

## 2. The statistic is also not well defined on this data, which is the part I want checked

`tax_per_gain = tax_drag / gross_mean_ann`. The denominator is **negative for roughly half the
cells**, because the economic-loss cells lose money over this window:

| country | cells with `gross > 0` | corr(turnover, gross) |
|---|---|---|
| DEU | 10 of 16 | −0.773 |
| IND | 8 of 16 | −0.913 |

So for those cells the statistic is "tax per unit of gain" where there is no gain, and the ratio's
sign is determined by which cells happen to be loss-making rather than by the tax channel. It is
not stable across specification:

| specification | DEU | IND |
|---|---|---|
| as registered, all 16 cells | −21.99 (t −1.44) | −4.83 (t −2.59) |
| same ratio, cells with gains only | **+11.56** (t +0.69) | −1.54 (t −1.75) |
| levels: `tax_bps ~ turnover + gross` | −235.3 (t −1.36) | **+33.4** (t +1.65) |

Germany flips sign between rows 1 and 2; India flips between rows 1 and 3.

**This retracts a result I previously circulated.** I had reported Germany's −21.99 (t = −1.44) as
"the placebo holds." That reading is withdrawn — the number is dominated by the sign-flipping
denominator and the inference from it was not sound. `docs/RESULTS_WEDGE_TEST.md` §2 now records
the retraction.

Note also that **no money-denominated form of this test is well identified here**: turnover and
gross return correlate −0.77 and −0.91 across the 16 cells, because the fastest-trading cells are
the loss-makers. With n = 16 and that collinearity, I do not think any variant of "tax on turnover"
can carry the paper. I would like your view on whether that is right.

## 3. What I did instead, and why I think it is defensible

I measured the mechanism directly rather than its monetary consequence.
`lt_share_of_gains` — the share of realised gains that qualified as long-term — is `1 - Phi(p, H)`
as the lot-level ledger actually realised it, which is the exact object the theory's wedge term
multiplies:

```
tax_drag / gross  ~  theta_L  +  Delta * Phi(p, H)
```

| country | wedge | boundary | `lt_share` range | slope on turnover | t | corr |
|---|---|---|---|---|---|---|
| **DEU** | 0.000 | none | **0.0000 – 0.0000** | no variation at all | — | — |
| **IND** | 0.150 | 12m | **0.3826 – 0.6413** | **−8.783** | **−4.36** | −0.762 |

* Germany's `lt_share` is **identically zero in all 16 cells** — under Abgeltungsteuer there is no
  holding-period boundary for newly acquired listed shares, so no long-term category exists for a
  gain to fall into. The variable the mechanism works through is absent, which is a stronger
  placebo statement than a slope near zero.
* India's falls steeply and significantly: 26 percentage points of realised gains move across the
  12-month boundary between the slowest and fastest cell.
* A tax-**level** account cannot produce this ordering: Germany taxes gains at 26.375% against
  India's 15% short-term rate and shows no channel whatsoever.

**Why I think it is not just a better-looking number:** `lt_share_of_gains` was already a frozen
column of the stage-06 report (`REPORT_COLUMNS`) before any of this, and it is the theory's own
`Phi`, so it is not a variable I went looking for after the fact. What *is* post-hoc is the
decision to **lead** with it.

**Why I am still uneasy, and want you to rule:** within a country, "designs that trade faster
realise fewer long-term gains" is close to arithmetic — turnover is not randomly assigned across
the cells, and the economic-loss axis drives both high turnover and short holding periods. I think
all the non-arithmetic content is in the cross-country contrast (the same arithmetic has a tax
consequence in India and exactly none in Germany, and that is set by statute). But that is a
judgement I should not make alone.

## 4. A magnitude finding that changes the claim regardless

| country | mean tax drag | mean cost drag | ratio |
|---|---|---|---|
| DEU | 5.23 bps p.a. | 27.67 bps p.a. | ~~5x~~ |
| IND | **0.45 bps p.a.** | 24.30 bps p.a. | ~~**53x**~~ |

> **Corrected later the same day:** all-16-cell means including the economic arm. On prediction cells
> the ratios are 2.70x (DEU) and 87.4x (IND); see `PAPER` §8.4.

Transaction costs dominate taxes five to one in Germany and fifty to one in India. India's tax drag
is small *because* its wedge is large in the sheltering direction — LTCG exempt, with 38–64% of
gains long-term, so most Indian gains were taxed at **zero**. Pre-2018 India's wedge is a **reward
for patience that fast trading forfeits**, not a penalty that fast trading incurs.

So I think the claim has to be restated whatever you decide on §3:

* **Supported:** the holding-period composition channel is created and bounded by statute, and is
  identically absent where the law sets a flat rate.
* **Not supported:** *the friction penalty is ordered by the wedge.* The penalty is dominated by
  transaction costs in every jurisdiction measured.

## 5. The options, as I see them

1. **Report §1–2 as the registered result (failed) and §3 as clearly-labelled exploratory**, with
   the reframed claim from §4. This is what the repo currently says. Honest, and the paper's
   headline becomes the reframing rather than the original claim.
2. **Re-register §3 as a primary hypothesis and confirm it out of sample** before the paper leans
   on it. The obvious out-of-sample is Japan (running now) — a second flat-rate country at a
   *different* level, 20.315% vs Germany's 26.375%, where `lt_share` must also be identically zero.
   Slower, much stronger. My preference, if the timeline allows.
3. **Drop the cross-sectional test and lead with the section 112A event study instead**
   (`tools/exp_112a_event_study.py`). India's wedge falls 0.15 → 0.05 on 2018-04-01 *inside* the
   sample while Germany's and Japan's law does not move, so the treatment is a **date** rather than
   a design axis and none of §2's collinearity applies. Both arms are running as I write. This may
   be the cleanest identification in the project and I would like your read on it before I write it
   up. Caveat already in the tool's docstring: the cells are not tax-aware, so it measures the
   incidence of the statute on a fixed portfolio, not a behavioural response.

I lean 2-plus-3. I have not written any of §3 into the paper as a passed test and will not until
you have ruled.

## 6. Where to look

* `docs/RESULTS_WEDGE_TEST.md` — full write-up, §2 is the failure and the retraction
* `tools/exp_wedge_test.py` — reports all four specifications, pre-registered one first, and prints
  a warning when it is not well defined, so it cannot be read selectively
* `tools/exp_112a_event_study.py` — the event study, with both clusterings reported
* `outputs/wedge_test/wedge_test.csv` — the numbers
* `docs/AMENDMENT_001B_UNIVERSE_BREADTH_CAP.md` — the Japanese universe cap, needs countersignature


---

## 7. ADDED 02:35 - the economic-loss arm looks broken, which undercuts the factorial too

The economic-loss cells train on net-of-cost utility including a `- cost(w_t - w_{t-1})` term, so
they should trade LESS than the prediction-loss cells. They trade more, and they have **negative
gross Sharpe - before any costs are charged**:

| India, by arm | gross Sharpe | net Sharpe | gross mean p.a. | turnover | cost drag |
|---|---|---|---|---|---|
| prediction-loss (P) | **+0.534** | +0.217 | +0.00158 | 0.0066 | 9.6 bps |
| economic-loss (E) | **-0.272** | -0.912 | -0.00161 | 0.0214 | 39.2 bps |

All 8 E cells negative, all 8 P cells positive, and the same pattern on the German panel. An
objective that prices turnover, trades 3.3x more and earns negative gross alpha has most likely
failed to train rather than discovered that economic objectives are worse.

**Why this is the top blocker:** the factorial's one significant main effect IS the economic one
(DEU -0.0054, t = -3.77; IND -0.0063, 81.6% of total). If the E arm is misconfigured, that effect
measures a training failure and not a design trade-off - and it is currently the most robust
finding in the project, replicating across two countries. It also supplies all the turnover
variation that §3/§5 depended on.

I have not debugged it yet. Candidates, in the order I would check them: the cost term's scale
relative to the return term in training; whether `w_{t-1}` in the truncated 12-month sequences is
the drifted prior book or a reset to zero (the same drift trap that invalidated the first
real-data run); and whether the policy is simply undertrained at these cross-section sizes.

**Question for you:** is the right move to debug the E arm, or to report the factorial with the E
arm explicitly flagged as not-fit-for-purpose and lean the paper on the P arm plus the
cross-country tax contrast? I can argue either. I would rather you decide than have me pick the
one that makes the results look better.
