# For Maham (workstream C): the claim has changed twice today. Four amendments need countersigning, and the newest one is already retracted.

> ## UPDATE at 12:35 IST — READ THIS BEFORE ANYTHING ELSE
>
> **I retracted 001D's hypothesis at 12:30, before Japan reported. The sign flip was a cost-input
> coverage artefact.** So **ask B below is moot** — you no longer need to rule on whether my 12:06
> revision was a legitimate pre-registration, because the hypothesis it protected is dead on the
> exploratory sample. What I now need from you is **ask A** (countersign 001A/B/C, and 001D
> *as retracted*), **ask C** (economic arm) and **ask D** (the inference, which is unaffected and
> still carries the surviving result).
>
> **What happened.** The ladder formed decile portfolios on Germany's **signal-bearing**
> cross-section (~382 names a month) instead of its **investable** one (~246). C6 prices **65.1%**
> of Germany's cross-section over 2009-2019 against **99.1%** of India's, and document 13
> requirement 2 makes an uncertified security-month non-tradeable with imputation prohibited. The
> ladder broke that rule twice over: an uncovered name was charged **zero cost** in the uncapped
> book, and given **cap = 0** in the capped book. Both push the capacity channel down, **and only
> in Germany**.
>
> | Germany at $100k | non-compliant | compliant |
> |---|---|---|
> | net uncapped | +1.749 | **+0.657** (35% of positions had been free) |
> | **capacity channel** | **−0.811** (t = −6.10) | **+0.062** |
>
> India, at 99.1% coverage, is the control and moves only **+0.183 → +0.211**. An effect that
> reverses in the 65%-coverage panel and not in the 99%-coverage panel is a coverage effect.
>
> **The one thing I would most like your eye on.** The spurious result was **t = −6.10**, monotone
> across nine decades of AUM, and it **passed both robustness checks I threw at it** — value
> weighting and a six-fold impact-coefficient sweep — including satisfying the mechanism's own
> quantitative prediction that `crossover ∝ k^−2`, to within ±15%. **A wrong result reproduced a
> theoretical scaling law.** I would like to know what you think a reviewer-proof protocol looks
> like when a coverage asymmetry can do that, because my robustness instincts demonstrably did not
> catch it; only enforcing the project's own non-tradeability rule did.
>
> **The surviving result** is in `docs/RESULTS_CAPACITY_CHANNEL_2026-10-09.md`: on the investable
> universe the capacity channel is **positive at every rung in both markets** and monotone in AUM —
> Germany +0.068 at $100k to **+8.92** at $1bn (t = +11.11), India +0.264 to **+5.69** (t = +5.70),
> significant on 13 of 14 and 14 of 14 rungs respectively, 8 of 8 cells under Holm from $1mn. **No
> crossover anywhere** (94.1% / 100% of replications show no sign change). Because we never observe
> the regime where the cap hurts, we **cannot** adjudicate Novy-Marx-Velikov versus
> Azevedo-Hoegner-Velikov and no longer claim to. The contribution is a measurement, not a
> mechanism adjudication.
>
> Everything below was written at 12:35 against the retracted claim and is kept for the record.
> Where it says "the flip", read "the retracted flip".

**From:** Harshit, workstream B
**Date:** 2026-10-09, 12:35 IST
**Reading order:** this document, then `docs/RESULTS_SIGN_FLIP_2026-10-09.md`, then
`docs/AMENDMENT_001D_CAPACITY_CHANNEL_SIGN_FLIP.md`.
**Japan had not reported when this was written.** That is the load-bearing fact in §3.

---

## 1. What you need to do, shortest version

| # | ask | why it is yours |
|---|---|---|
| **A** | **Countersign 001A, 001B, 001C, 001D** (001A/B/C have been waiting; 001D is new) | pre-registration discipline is workstream C's call, not mine |
| **B** | **Rule on whether 001D is still a valid pre-registration** after I revised it at 12:06 — §3 below sets out exactly what I changed and why | I am not a neutral judge of whether my own revision was legitimate |
| **C** | **Rule on the economic arm** (doc 19 §7, still open) — it now also affects the headline numbers, see §5 | unchanged from doc 19 |
| **D** | **Sanity-check the inference** in §4. It is new code and it carries the central claim | this is your speciality and I wrote it against my own hypothesis |

## 2. The claim is no longer about tax, and no longer about magnitude

The tax hypothesis failed (doc 19). The capacity reframing that replaced it was "capacity binds
before alpha", and **that is now also not the claim**, because reading the capacity literature in
full text showed the ground is occupied — Avramov, Cheng & Metzker (Management Science 2023) own
"ML alpha dies under realistic frictions", in one of our two target journals.

What we have instead is narrower and, I think, better:

> The effect of the ADV participation constraint on net Sharpe is **monotone in mandate size and
> changes sign**. Germany: **−0.81** Sharpe points at a $100k mandate, **+11.06** at $1bn, crossing
> zero at **$3.79mn (95% CI $1.88mn–$7.07mn)**.

It matters because **the literature disagrees about this sign in print**: Novy-Marx & Velikov
(RFS 2016) and Korajczyk & Sadka (JF 2004) find turnover reduction and liquidity tilting help,
while Azevedo, Hoegner & Velikov (2025) find the same mitigations do not. All three are US and all
three are right about their own setting. Both fall out of
`net Sharpe = (alpha_eff − kappa·G^0.5)/sigma` with `kappa ∝ sqrt(AUM/ADV)`, and AHV sit at
`kappa ≈ 0`. We recover their regime inside our own data and walk it up nine decades.

**Three of my own claims were withdrawn today**, all the same error — a quantity computed correctly
and compared against the wrong benchmark. They are listed in `docs/STATUS.md` and in tracker §C8.
The one you should know about for your own writing: **"costs beat taxes 5x in Germany and 53x in
India" are all-16-cell averages**. On prediction cells only they are **2.70x** and **87.4x**.

## 3. Ask B: is 001D still a pre-registration? Here is exactly what I did

This is the part I most need an outside judgement on.

**11:30 IST.** Declared 001D with five predictions for Japan, using the statistic I had: the
**mean across cells of each cell's Sharpe difference**.

**12:06 IST.** Having then built the inference, I measured the **composite** channel — one
equal-weighted portfolio of the 8 prediction cells — and the two statistics disagree about India:

| | mean of per-cell Sharpe diffs | composite |
|---|---|---|
| Germany at $1bn | +8.77 | **+11.06**, t = +12.27 |
| Germany crossover | $3–4mn | **$3.79mn [1.88, 7.07]** |
| India at $1k | **−0.0039** | **+0.0035**, t = +0.13, p = 0.89 |
| India crossover | "between $1k and $3k" | **none detectable** |

So I revised 001D: made the composite primary, **withdrew** the claim that India has a crossover,
and **replaced prediction D3**, which had compared Japan's crossover against an India crossover
that does not exist and was therefore ill-posed. The replacement D3 is **conditional** on Japan's
gross Sharpe exceeding India's.

**My own view, for you to accept or reject.** I think the revision is legitimate, because:
* Japan had not reported. I re-verified at 12:06 that `outputs/` held no Japanese portfolio, no
  weights-index entry and no stage-04 artefact of any kind, and that Japan's stage 02 was still
  training. The verification commands and their output are in the commit message of `0e80485`.
* It corrects the **exploratory** sample's statistic. It does not change a threshold after seeing
  the answer.
* The replacement D3 is **weaker and harder to pass** than the original, not easier: it can come
  out void, and if it does, the sign flip rests on **Germany alone** and must be reported that way.
* Both versions are in the document and in git history.

**What would make me wrong.** If you judge that choosing the composite statistic was itself
influenced by it giving a cleaner Germany result, then 001D is contaminated and Japan is not a
confirmation sample. I do not believe that is what happened — I built the composite because a
difference of Sharpe ratios needs a paired test and the test needs one return series, not eight —
but I cannot certify my own motives and the order of events is in the git log for you to check.

**If you rule it contaminated**, the fallback is clean and I will take it without argument: report
Germany and India as exploratory on two markets, and treat Japan as a third exploratory market
rather than a confirmation. The sign flip survives either way; what we lose is the right to the
phrase "pre-registered out-of-sample test".

**To make this checkable rather than a matter of trust**, `tools/score_amendment_001d.py` was
written and committed **before Japan reported** and scores D1–D5 mechanically, with every threshold
and every exploratory reference value hard-coded. Run it yourself when Japan lands.

## 4. Ask D: please sanity-check the inference

New code, and it carries the central claim.

**`sharpe_difference_test`** (`src/alphacomb/validation/inference.py`) — Ledoit-Wolf studentized
stationary bootstrap for a difference of Sharpe ratios on **paired** series. Paired because the
capped and uncapped books are the same months from the same scores. Studentized with the Lo (2002)
influence-function expansion, so one Newey-West standard error absorbs both the serial dependence
and the cross-dependence of the pair.

Specific things I would like you to attack:

1. **The influence function.** I use
   `sqrt(P)·(z − (SR/(2·sqrt(P)))·(z² − 1))` with `z = (r − mu)/sigma`, differenced across the two
   series, then a Newey-West SE of its mean. Is that the right annualisation? I convinced myself
   the `sqrt(P)` placement is right because `psi` is mean-zero and its SE-of-mean is the SE of the
   annualised difference, but it is the kind of thing that is wrong by a factor of `sqrt(12)`
   without anything looking odd.
2. **Holm rather than Romano-Wolf for the across-cell multiplicity.** I did *not* use our
   `romano_wolf`, because it studentizes the **mean** of each series, so aiming it at the return
   differences would test whether the cap raises mean *return* — a different and oppositely-signed
   question, since the cap cuts gross. Holm on the Sharpe-difference p-values is conservative but
   about the right statistic. If you would rather have a proper max-statistic bootstrap over the
   per-cell studentized Sharpe differences, say so and I will write it.
3. **The crossover interval.** Stationary bootstrap over months; each replication recomputes the
   composite channel at every rung with **one shared index** across rungs (to preserve the
   cross-rung dependence) and interpolates the zero in `log10(AUM)`. Replications with no sign
   change are **counted, not dropped** — Germany 0%, India 50.8%. Is percentile-on-the-zero
   defensible, or do you want it inverted from the studentized statistic?
4. **The 12 tests** in `tests/validation/test_sharpe_difference.py`, particularly
   `test_paired_se_is_smaller_than_treating_the_series_as_independent`, which is the one that would
   catch me having silently lost the pairing.

Full suite: **450 tests, 0 failures.**

## 5. Ask C: the economic arm now also distorts the headline

Doc 19 §7 asked you to rule on debug-versus-flag. That is still open and it now matters more,
because the horse race showed the published cost-over-tax ratios were formed by averaging the
broken arm into them:

| | cost drag | tax drag | cost/tax |
|---|---|---|---|
| Germany, all 16 cells | 27.67 bps | 5.23 | **5.3x** (as published) |
| Germany, prediction 8 | 17.21 | 6.38 | **2.70x** |
| Germany, economic 8 | 38.12 | 4.07 | 9.38x |
| India, all 16 | 24.30 | 0.455 | **53.5x** (as published) |
| India, prediction 8 | 9.96 | 0.114 | **87.4x** |

The economic arm trades 1.8x faster than the prediction arm and drives the all-cell average. Until
you rule, **every headline number should be quoted on the prediction cells only**, which is what
`RESULTS_SIGN_FLIP` and `AMENDMENT_001D` now do.

## 6. One result you may want for your own section

Two robustness checks landed today and both are yours to use.

**The impact coefficient predicts its own sensitivity.** `k = 1` is Grinold-Kahn and is an
assumption. The mechanism says the crossover sits where `kappa` is critical, so
`crossover ∝ k^(−2)`. Measured on Germany over `k ∈ {0.5, 1, 2, 3}`: `crossover × k²` = 4.14, 3.79,
4.24, 4.97 (mn) — constant to within ±15% for `k ≤ 2`. **The sign flip exists at every `k`.** This
is internal validation that does not depend on Japan.

**Value weighting cuts our gross Sharpes by ~80%** (Germany +2.38 → +0.47, India +1.00 → +0.21),
which is Novy-Marx & Velikov's critique of equal-weighted anomaly results landing on our own
numbers, and it must be reported.

**On the flip itself, value weighting is bad news and I want to be blunt about it**, because I
briefly got this wrong. Reading the point estimates off the per-cell ladder, both markets appeared
to flip — Germany's crossover moving to ~$1.1mn and one *appearing* in India at ~$107k. Running the
composite inference says otherwise:

| | Germany EW | Germany VW | India EW | India VW |
|---|---|---|---|---|
| channel at the bottom rung | **−0.811** | −0.179 | +0.004 | −0.002 |
| t | **−6.10** | **−1.65** | +0.13 | −0.06 |
| p | **0.0000** | **0.117** | 0.893 | 0.959 |
| crossover point estimate | **$3.79mn** | $1.11mn | none | $107k |
| draws with no sign change | **0.0%** | 2.1% | 50.8% | **51.8%** |

**The negative region is statistically established in exactly one place: Germany under equal
weighting.** Under value weighting Germany's negative side is t = −1.65, p = 0.117 — the point
estimate is negative and the crossover is still there on 97.9% of draws, but it is not significant.
India's negative side is nil under both weightings.

So the defensible claim is: **the positive side is robust everywhere** (both markets, both
weightings, t = +5.3 to +12.3 at scale, 8 of 8 cells under Holm from $30mn upward), while **the
sign change itself rests on Germany under equal weighting**, with value weighting giving a
consistent but insignificant point estimate. My earlier wording "the flip survives in Germany and
appears in India" was an overstatement from point estimates and I have corrected it in
`RESULTS_SIGN_FLIP` §3f.

One thing for you specifically: at Germany VW $100k the **percentile CI on the difference excludes
zero** ([−0.424, −0.0085]) while the **studentized p is 0.117**. I report the studentized p as
primary, per Ledoit-Wolf. Please confirm that is the right call, because it is the difference
between a significant and an insignificant negative region.

## 7. What I am not asking you for

Nothing about Japan. Its stage 02 is on its final cell and I will run the pre-registered scorecard
and report the result whichever way it goes, with the same prominence as the two failures in
`RESULTS_WEDGE_TEST.md`. If D3 comes out void, I will say the flip rests on Germany alone.
