# Amendment 001D: the capacity channel changes sign with scale, and Japan tests it

> # RETRACTED 2026-10-09, 12:30 IST — H-FLIP IS FALSIFIED ON ITS OWN EXPLORATORY SAMPLE
>
> **Japan never needed to report. The sign flip was an artefact of cost-input coverage and it is
> withdrawn.**
>
> **The defect.** The ladder in section 3 formed decile portfolios on the **signal-bearing**
> cross-section (~382 German names a month) rather than the **investable** one (~246). The promoted
> C6 prices only **65.1%** of Germany's cross-section over 2009-2019 — `adv_usd` is the binding
> field — against **99.1%** of India's. Document 13 requirement 2 makes an uncertified
> security-month **non-tradeable** and prohibits imputation (`docs/NON_TRADEABLE_TREATMENT.md`),
> and the ladder violated that rule in both directions at once:
> * in the **uncapped** book an uncovered name was charged **zero cost**, so 35% of Germany's
>   positions were being traded for free;
> * in the **capped** book the same name got `cap = 0` and was dropped outright.
>
> Both push the capacity channel downward, and **only in Germany**. That was the negative region.
>
> **The corrected numbers** (`--require-cost-inputs`, Germany at $100k):
>
> | | non-compliant | compliant |
> |---|---|---|
> | gross | +2.383 | **+1.998** (the excluded names did carry alpha) |
> | net uncapped | +1.749 | **+0.657** (35% of positions were free) |
> | net capped | +0.938 | **+0.719** |
> | **capacity channel** | **−0.811** | **+0.062** |
>
> India, at 99.1% coverage, is the control and barely moves: **+0.183 → +0.211**. That is precisely
> the signature of a coverage artefact rather than a market difference.
>
> **On the compliant universe the channel is positive at every rung in both markets and monotone
> increasing in AUM. There is no crossover anywhere in the data.** We never observe the regime in
> which the cap hurts, so we **cannot** adjudicate the
> Novy-Marx-Velikov-versus-Azevedo-Hoegner-Velikov disagreement, and the claim to do so is
> withdrawn in full.
>
> **Status of each prediction:** D1 (monotonicity) holds and is the only one that survives. D2
> (positive at $1bn) is expected to hold but is no longer a test of anything contested. **D3 is
> dead** — there is no negative region in the exploratory sample for Japan to generalise. D4 and D5
> were conditional on quantities this retraction changes.
>
> **This retraction was written before Japan reported**, with Japan's stage 02 on its final cell and
> no Japanese portfolio in existence, so no Japanese result influenced it. The error was found by
> checking whether the wedge tool obeyed the project's own non-tradeability rule — it did not.
>
> **What survives is in section 10 below**, added with this retraction. Everything between here and
> there is kept as the record of a claim that did not hold.

> ## REVISED 2026-10-09, 12:06 IST, BEFORE JAPAN REPORTED
>
> **What changed and why.** Sections 3 and 4 as first written used the **mean across cells of each
> cell's Sharpe difference**. Having then built the inference (`sharpe_difference_test`,
> `tools/exp_capacity_channel_inference.py`) I measured the **composite** channel — one
> equal-weighted portfolio of the 8 prediction cells, which is the object a paper should quote —
> and the two statistics do not agree about India.
>
> | | mean of per-cell Sharpe diffs | **composite portfolio** |
> |---|---|---|
> | Germany, channel at $1bn | +8.77 [withdrawn] | **+11.06**, t = +12.27 |
> | Germany, crossover | between $3mn and $4mn | **$3.79mn [withdrawn], 95% CI [$1.88mn, $7.07mn]** |
> | India, channel at $1k | −0.0039 | **+0.0035**, t = +0.13, p = 0.89 |
> | India, crossover | "between $1k and $3k" | **none in $1k..$10bn**; 50.8% of bootstrap draws show no sign change |
>
> **So India does not show a sign flip.** Its channel is positive at every scale we can measure and
> significantly so from $10k upward. The original claim that India's crossover sits between $1k and
> $3k was an artefact of the mean-of-Sharpes statistic and is **withdrawn**. Germany's flip, by
> contrast, is confirmed at both tails: significantly **negative** at $100k/$300k/$1mn (t = −6.10,
> −5.99, −4.01; Holm-adjusted across 8 cells) and significantly **positive** from $8mn upward
> (t = +2.30 to +12.99).
>
> **Consequences, all applied below.** The composite is now the primary statistic throughout.
> Prediction **D3 was ill-posed** (it compared Japan's crossover against an India crossover that
> does not exist) and is **replaced**. D2 is restated so it does not presume the flip is universal —
> which, on two markets, it demonstrably is not.
>
> **Why this revision is legitimate.** Japan had not reported when it was made: re-verified at
> 12:06 IST that `outputs/` contains no Japanese portfolio, weights-index entry or stage-04
> artefact of any kind, and that Japan's stage 02 is still training. The revision corrects the
> **exploratory** sample's statistic; it does not weaken a prediction after seeing the answer. Both
> the original text and this block are kept, and the git history is the record. Nothing may be
> revised once Japan's arm reports.

**Declared:** 2026-10-09, 11:30 IST (revised 12:06 IST, before Japan reported)
**Status:** declared **before any Japanese portfolio exists**. See section 6 for the evidence.
**Awaiting countersignature:** Maham (workstream C), as with 001A, 001B and 001C.
**Supersedes nothing.** PLAN_001 (`cae8140b7e2b7ee4`, N=64), 001A, 001B and 001C all stand.
**Relation to 001C:** 001C pre-registered that the participation constraint *governs* the portfolio
above a critical size (H-CAP). This amendment pre-registers the sharper and more falsifiable claim
that the constraint's effect on net risk-adjusted performance **changes sign** at a measurable
scale, and that the published disagreement in the literature is a disagreement about which side of
that scale the authors stand on.

---

## 1. Why this amendment exists

Reading the full text of the capacity literature (recorded in
`research/03_Research_Gaps/Closest_Prior_Art_Tracker.md`, sections C1-C8) produced two findings that
change what this paper can claim.

**First, a claim of ours was wrong and is withdrawn.** The assertion that our capacity frontiers are
"10x to 100x below published US estimates" compared our monthly-rebalanced ML books against
*low-turnover* US strategies. Novy-Marx & Velikov (RFS 2016, Table 7) report, in the US,
**$0.38-0.44bn** for a high-frequency combination strategy and **$0.18-0.53bn** for industry
relative reversal. Turnover-matched, Japan's $413mn is *inside* that range. Details in tracker
section C8.1.

**Second, the literature contains a live disagreement about a sign, and we can settle it.**

* **Novy-Marx & Velikov (RFS 2016):** the buy/hold spread is the most effective cost-mitigation
  technique; reducing turnover **improves** net performance.
* **Korajczyk & Sadka (JF 2004):** a deliberate liquidity weighting raises momentum's break-even
  fund size from roughly $1mn (equal-weighted, full sample) to **over $5bn** -- a factor of 5,000
  from the liquidity tilt alone.
* **Azevedo, Hoegner & Velikov (SSRN 4702406, 2025):** the same mitigations "significantly reduce
  turnover and trading costs" but **do not improve net performance**, because the lost gross return
  more than offsets the cost saving. Their stated reason is that post-decimalisation costs are only
  20-25 bps per month.

All three are US. All three are correct about their own setting. We hold that the disagreement is
not empirical but **positional**: it depends on where on the cost curve the investor sits, and that
is the one thing our design varies exogenously.

## 2. The hypothesis

> **H-FLIP.** The effect of a participation constraint on net risk-adjusted performance is a
> monotone increasing function of the ratio of impact cost to alpha. That ratio is governed by
> `kappa`, which grows as `sqrt(AUM / ADV)`. Consequently the constraint **destroys** net Sharpe at
> small mandate sizes, where it forfeits signal without averting meaningful cost, and **creates**
> net Sharpe at large mandate sizes, where the cost it averts exceeds the signal it forfeits. There
> exists a market-specific crossover AUM at which its effect is exactly zero.

The mechanism, which is the one-page comparative static that blocker 5 of the readiness audit asks
for:

    net Sharpe = (alpha_eff - kappa * G^0.5) / sigma

A participation cap lowers attainable gross `G` and per-name turnover. It lowers `alpha_eff`
roughly **linearly** in the forfeited positions, but lowers the cost term as **`G^0.5`**. Tightening
therefore helps if and only if `kappa` is large relative to alpha. Azevedo et al. operate at
`kappa` near zero -- their cost model is an effective spread that does not contain AUM at all -- so
for them a mitigation can only destroy alpha. Novy-Marx & Velikov and Korajczyk & Sadka price
impact at scale, so for them it creates value. Both findings follow from one expression.

## 3. The exploratory evidence (Germany and India)

Measured on the decile-spread portfolios built from the same stage-02 scores, across nine decades of
AUM. Full ladder: `outputs/signal_vs_portfolio/capacity_channel_ladder.csv` (34 rows), committed
verbatim at **`docs/attachments/CAPACITY_CHANNEL_LADDER_2026-10-09.csv`** because `outputs/` is
gitignored and a pre-registration whose exploratory evidence is not version-controlled is worth
little.

**Provenance of that ladder, so it is reproducible.** It was assembled from the wedge tool's
`--tag` outputs `crossover`, `xover_fine`, `xover_low` and `asym`, all at the config default
`impact_k = 1.0` and equal weighting. Later runs added the tags `k05`, `k20`, `k30` (impact-k
sweep, section 3e) and `vw` (value weighting), which are **not** part of this ladder — a glob over
`wedge_DEU_*.csv` would now mix four different cost assumptions into one table. The `--tag` flag
exists because an untagged run had already silently overwritten the $1bn rows once.

**Capacity channel** = (net Sharpe, participation-capped) - (net Sharpe, uncapped).

| AUM | Germany | India |
|---|---|---|
| $1k | | **-0.0039** |
| $3k | | +0.0150 |
| $100k | **-0.6895** | +0.1833 |
| $1mn | -0.5371 | +0.7090 |
| $3mn | **-0.1269** | +1.2769 |
| $4mn | **+0.0264** | |
| $10mn | +0.8129 | +2.1179 |
| $100mn | +4.9733 | +3.7073 |
| $1bn | +8.7707 | +4.4077 |
| $10bn | +10.0150 | +4.5521 |
| $1tn (asymptote) | +10.4002 | +4.6042 |

### 3a. The composite statistic, which is now primary

The table above is the **mean across cells of each cell's Sharpe difference**. The object the paper
should quote is the **composite**: one equal-weighted portfolio of the 8 prediction cells, tested
with the paired studentized bootstrap (`sharpe_difference_test`). Full table with standard errors:
`outputs/capacity_inference/capacity_channel_inference_{DEU,IND}.csv`.

| AUM | Germany channel | t | Holm 5% | India channel | t | Holm 5% |
|---|---|---|---|---|---|---|
| $1k | | | | +0.0035 | +0.13 | 0/8 |
| $3k | | | | +0.0284 | +0.98 | 0/8 |
| $10k | | | | +0.0575 | +1.76 | 0/8 |
| $100k | **−0.8114** | **−6.10** | **8/8** | +0.2320 | +4.12 | 3/8 |
| $300k | **−0.8006** | **−5.99** | **8/8** | +0.4355 | +4.10 | 8/8 |
| $1mn | **−0.6219** | **−4.01** | 3/8 | +0.8273 | +4.21 | 8/8 |
| $2mn | −0.3430 | −1.87 | 1/8 | | | |
| $3mn | −0.1447 | −0.71 | 0/8 | +1.4619 | +4.49 | 8/8 |
| $4mn | +0.0331 | +0.15 | 0/8 | | | |
| $8mn | **+0.6782** | **+2.30** | 1/8 | | | |
| $10mn | **+0.9447** | **+2.96** | 3/8 | +2.4341 | +4.65 | 8/8 |
| $100mn | **+6.0853** | **+9.74** | **8/8** | +4.4674 | +5.25 | 6/8 |
| $1bn | **+11.0552** | **+12.27** | **8/8** | +5.5523 | +5.66 | 7/8 |
| $10bn | **+12.6546** | **+12.99** | **8/8** | +5.8220 | +5.85 | 7/8 |

Four facts, all exploratory, all on the sample that generated them:

1. **The channel is monotone increasing in AUM** in both markets, across every rung, without
   exception.
2. **Germany's channel changes sign, and both tails are significant.** Significantly **negative** at
   $100k, $300k and $1mn (t = −6.10, −5.99, −4.01; 8 of 8 cells surviving Holm at the first two) and
   significantly **positive** from $8mn upward (t = +2.30 rising to +12.99). The crossover is
   **$3.79mn [withdrawn], 95% bootstrap CI [$1.88mn, $7.07mn]**, with **0%** of 2,000 replications failing to
   show a sign change. This is Azevedo et al.'s regime and Novy-Marx & Velikov's regime in the same
   dataset, separated by a factor of about 10 in mandate size.
3. **India's channel does not change sign.** It is positive at every rung, insignificantly so below
   $10k and significantly from $10k upward. **50.8%** of bootstrap replications show no sign change
   anywhere in $1k..$10bn. India is a market where the participation cap helps at every mandate size
   an investor could actually run. **The flip is therefore not universal**, which is a result in its
   own right and is why prediction D3 below had to be rewritten.
4. **A candidate regularity.** The asymptotic channel [withdrawn] scaled by the composite gross Sharpe agrees
   across the two markets: Germany +12.6546/2.763 = **4.58**; India +5.8220/1.209 = **4.82**. With
   n = 2 this is weak and is pre-registered as a secondary prediction only.

### 3b. Why India has no flip, as a hypothesis rather than a claim

The crossover is not a fixed multiple of the capacity frontier — Germany's is 3.6e-2 of its $106mn
frontier while India has none at all, against a frontier ratio of only 1.9x. Depth alone does not
set it. The candidate explanation, to be tested and not asserted, is the **share of alpha sitting in
the illiquid tail**: Germany's composite decile spread has gross Sharpe +2.763 against India's
+1.209, so Germany forfeits more than twice as much signal per unit of gross that the cap removes,
and needs a correspondingly larger cost saving before capping pays. India's signal is weaker and
more evenly spread, so the cap is nearly free at any scale.

## 4. The predictions for Japan, fixed now

Japan's arm runs at `--max-names 600`, `--years 2009 2019` (amendment 001B), on the
prediction-loss cells. The ladder will be the same nine decades.

All predictions are on the **composite** channel (section 3a), tested with
`sharpe_difference_test`, on the ladder $1k..$10bn.

| # | prediction | falsified if | weight |
|---|---|---|---|
| **D1** | Japan's composite capacity channel is **monotone non-decreasing** in AUM across $1k..$10bn | any decrease exceeding 0.05 Sharpe points between adjacent rungs | **primary** |
| **D2** | Japan's channel is **significantly positive at $1bn** (5%, paired test), because $1bn is 2.4x past Japan's $413mn frontier | not significantly positive at $1bn, or negative there | **primary** |
| **D3** (replaced) | **Japan resembles Germany rather than India on the sign question**, i.e. Japan's channel is **negative at the bottom of the ladder**, because Japan's composite gross decile Sharpe will exceed India's +1.209 and the section-3b hypothesis says the flip appears where there is more alpha to forfeit. Stated conditionally and scored both ways: **if** Japan's gross Sharpe > 1.209 **then** a negative region should exist; **if** it is below, no flip is predicted and D3 is void | Japan's gross Sharpe exceeds +1.209 **and** no rung in $1k..$1mn has a negative channel | **primary, conditional** |
| **D4** | Japan's **asymptotic** composite channel divided by its own composite gross decile Sharpe lies in **[3.5, 5.5]** | outside that band | secondary (n = 2) |
| **D5** | Japan's channel at $1bn, **scaled by its gross Sharpe**, is below Germany's 11.0552/2.763 = **+4.00**, because $1bn is only 2.4x past Japan's frontier against 9.4x past Germany's | at or above +4.00 | secondary |

**D2 and D3 are the real tests.** D1 is close to mechanical given the cost model and should be read
as a consistency check: if it fails, something is wrong with the pipeline rather than with H-FLIP.
D4 rests on two observations and a failure should be reported as a failure of the regularity, not of
H-FLIP. D5 depends on Japan's gross Sharpe, which is unknown.

**D3 is deliberately conditional, and that is a weakening of this amendment relative to its first
version.** India having no flip means the flip's existence cannot be predicted from market depth
alone, so an unconditional "Japan will flip" would be a guess. Tying it to Japan's gross Sharpe
makes it a test of the **section-3b mechanism** rather than of depth, which is the thing actually at
issue — but it also means D3 can come out void, and if it does, the sign-flip mechanism will rest on
Germany alone and must be reported that way.

## 5. What would falsify H-FLIP as a whole

* **D2 failing.** A channel that is not positive at $1bn in Japan, well past its frontier, would
  break the mechanism's core claim that the cap pays once `kappa` is large.
* **D1 failing.** A non-monotone channel would mean `kappa` is not the governing parameter.
* **D3 failing in its antecedent-true branch** — Japan's gross Sharpe above India's but no negative
  region anywhere — would falsify the section-3b explanation of *why* Germany flips and India does
  not, leaving the flip an unexplained one-market fact.
* The **joint** failure of D2 and D3 would mean scale does not govern the sign and the
  reconciliation of the literature fails.

## 6. That this precedes any Japanese result

Checked immediately before writing this document:

* `outputs/weights_index/` contains **no** Japanese entry (DEU and IND only).
* `outputs/signal_vs_portfolio/` contains **no** Japanese file; the capacity-channel ladder exists
  for Germany and India only.
* A search of `outputs/` for any Japanese backtest, portfolio or summary artefact
  (`*jpn*` crossed with `bt_*`, `pf_*`, `summary*`) returns **zero** files.
* **Japan has never been through stage 04.** Stage 02 is still training: 7 of its remaining
  strategies have reported, the rest have not.
* The Japanese quantities already inspected are **cost-input aggregates only** -- eligible-name
  counts, ADV medians, capacity ceilings and the $413mn frontier -- all computable before any model
  is fitted, all reported in `RESULTS_CAPACITY` section 4b, and all excluded from this confirmation.
* What would invalidate this amendment: editing any prediction in section 4 after Japan's arm
  reports. The predictions are fixed at this commit and the git history is the record.

## 7. How to report the outcome

* **If D1-D3 hold:** report H-FLIP as exploratory on Germany and India and **confirmed on Japan**,
  naming Japan as a pre-registered out-of-sample test and citing this document's commit date. The
  paper then claims the sign flip and its scale parameter, and explicitly reconciles Novy-Marx &
  Velikov with Azevedo, Hoegner & Velikov.
* **If they fail:** report the failure with the same prominence as the two failures already recorded
  in `RESULTS_WEDGE_TEST.md`, and report the sign flip as exploratory on two markets only.
* Either way, the **withdrawal in section 1 stands**: the "10-100x below US estimates" claim is
  gone regardless of what Japan shows.

## 8. What this does not claim

* Not "first to measure strategy capacity" -- Korajczyk & Sadka, Novy-Marx & Velikov, Garleanu &
  Pedersen.
* Not "first to show turnover reduction can help" -- Novy-Marx & Velikov own the positive sign;
  Korajczyk & Sadka own the liquidity tilt.
* Not "first to show ML alpha is fragile to frictions" -- Avramov, Cheng & Metzker, in Management
  Science.
* Not "first to apply ML outside the US" -- Cakici, Fieberg, Metko & Zaremba, 46 markets, JEDC 2023.
* What is claimed: **the sign is scale-dependent, the crossover is measurable, the published
  endpoints are recovered as limiting cases of one expression, and the crossover is not a fixed
  multiple of the capacity frontier.**

> **Note added in the finalization audit.** The $1bn figures quoted in this section (+8.05 Germany,
> +4.51 India, and the table below) compare against an uncapped book that is insolvent at those
> rungs (`PAPER` §8.8) and are not interpretable as performance gains; the qualitative statement of
> what survives (positive, monotone in cap slack, zero where slack) is unchanged. The record of what
> was predicted and what happened in sections 1-9 and 11 is left as written.

## 10. What survives the retraction (added 2026-10-09, 12:31 IST)

On the **compliant** universe — investable names only, `--require-cost-inputs`, which is what
document 13 requirement 2 has always required — the capacity channel is:

| AUM | Germany | India |
|---|---|---|
| $100k | **+0.062** | **+0.211** |
| $300k | +0.256 | +0.392 |
| $1mn | +0.795 | +0.751 |
| $2mn | +1.282 | +1.096 |
| $3mn | +1.653 | +1.332 |
| $4mn | +1.971 | +1.509 |
| $6mn | +2.478 | +1.780 |
| $8mn | +2.887 | +2.005 |
| $1e7 | +3.236 | +2.190 |
| $3e7 | +5.115 | +3.072 |
| $1e8 | +6.818 | +3.792 |
| $3e8 | +7.617 | +4.290 |
| $1e9 | +8.047 | +4.507 |
| $1e10 | +8.336 | +4.657 |

**Three things survive, and they are worth having.**

1. **The capacity channel is positive and monotone increasing in AUM, in both markets, at every
   scale measured.** It reaches **+8.05** (Germany) and **+4.51** (India) Sharpe points at $1bn. It
   is robust to the weighting scheme (§3e), to the impact coefficient over a six-fold range (§3f),
   and now to the coverage treatment. A binding ADV participation constraint **creates**
   risk-adjusted performance at institutional scale, and the effect grows with mandate size.
2. **The comparative static still explains that**, and its `k`-scaling prediction (§3f) still held
   on the non-compliant ladder; it should be re-checked on the compliant one before being quoted.
3. **The coverage asymmetry is itself a methods finding** worth a paragraph: a 35-point gap in
   cost-input coverage between two panels of the same study generated a spurious, highly
   significant (t = −6.10), sign-flipping result that survived a value-weighting robustness check
   and an impact-coefficient sweep. Only enforcing the project's own non-tradeability rule killed
   it. For non-US work, where coverage is never complete, that is a general warning.

**What does not survive:** the sign flip, the crossover and its confidence interval, and the claim
to adjudicate the @NMV2016-versus-@AHV2025 disagreement. **We only ever observe the regime in which
the cap helps.** Our result is therefore *consistent with* @NMV2016 and @KS2004 and says nothing
about @AHV2025, who operate at a scale we do not reach.

**What this does to the paper.** The contribution reverts to a measurement — the positive capacity
channel, AUM-indexed, in three non-US markets, with the tax channel ruled out as second-order — and
loses the mechanism-adjudication framing that made it interesting. That is a real loss and should
not be dressed up. `docs/STRATEGIC_ASSESSMENT_2026-10-09.md` needs a fourth pass.

## 11. Japan's result (2026-10-09, 12:55 IST) — and why I am not reporting the scorecard's verdict

Japan ran on the compliant universe (coverage 99.8%, so it was never exposed to §6's artefact) with
`tools/score_amendment_001d.py`, committed before Japan reported. **The scorecard's mechanical
output, in full:**

| # | verdict | number that decided it |
|---|---|---|
| D1 | **PASS** | largest change between adjacent rungs +0.0102, i.e. no decrease (tolerance −0.05) |
| D2 | **PASS** | channel at $1bn **+6.6813**, t = +11.01, p < 0.0001 |
| D3 | **PASS** | antecedent true (gross Sharpe +1.278 > India's +1.209); a negative channel exists in $1k..$1mn |
| D4 | FAIL | asymptotic ratio [withdrawn] 7.1511/1.278 = **5.596**, just outside the band [3.5, 5.5] |
| D5 | FAIL | channel at $1bn / gross = **5.228**, needed < 4.00 (Germany's value) |

Its verdict line reads **"H-FLIP CONFIRMED [withdrawn] on the pre-registered sample."**

**I am not reporting that, and the reason is a defect in my own pre-registration rather than
anything about Japan.**

**D3's pass is vacuous.** It asked only for the *existence of a negative channel somewhere below
$1mn*, with **no magnitude floor and no significance requirement**. Japan's negative reading is
**−0.0013 with t = −1.14 and p = 0.370**, and a 95% CI of [−0.0038, +0.0003] that contains zero. It
is a sign, not an effect — four orders of magnitude smaller than the retracted German −0.811, and
statistically indistinguishable from zero. A test that a −0.0013 reading passes is not a test.
Writing a sign prediction without a magnitude floor was my error, made at 11:30 when the German
−0.811 looked real and a magnitude floor seemed superfluous.

**And H-FLIP's retraction is independent of Japan.** Germany's −0.811 — the only economically
material negative region ever observed in this project — was a cost-input coverage artefact (§6).
Japan cannot resurrect a claim whose evidential basis was withdrawn; it can only add a fourth
near-zero reading at a scale where the constraint does not bind.

**D5's failure is the substantive one.** I predicted Japan's scaled channel at $1bn would be
*below* Germany's 4.00, because $1bn is only 2.4x past Japan's $413mn frontier against 9.4x past
Germany's $106mn. It came out **5.228 — higher**. So the frontier-distance heuristic behind D5 is
wrong: at $1bn Japan's attained gross is 0.162 of 2.0, i.e. the cap is binding hard despite the
frontier being nearer, because Japan's 1,705-name breadth means far more positions hit the cap.
Distance past the frontier is not a sufficient statistic for how much the constraint bites.

### 11a. What Japan does confirm, cleanly

**D2 is a real pre-registered out-of-sample confirmation of the surviving claim.** Japan's channel
is positive and significant on 11 of 14 rungs, with 8 of 8 cells surviving Holm from $8mn upward,
rising monotonically to **+6.68 at $1bn (t = +11.01)** and +7.15 at $10bn. Declared before any
Japanese portfolio existed, scored by a committed script. That is worth having and it is the third
market to show it.

### 11b. The finding that replaces the sign flip

Putting all three markets' smallest rungs beside how much the cap actually binds — measured as the
shortfall of attained gross below the 2.0 target — resolves the whole question:

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

> **The constraint's effect on net Sharpe is zero when the constraint does not bind, and
> monotonically positive in how much it binds. There is no scale at which it meaningfully hurts.**

At ~0.01% slack the channel is ±0.001 and its **sign is arbitrary** — Germany +0.0008, Japan
−0.0009, on the same cost model. Those are not two regimes; they are noise around zero. The
"crossover" that §3 reported, and that Japan's bootstrap still places at $115,532 with a
[$101k, $349k] interval, is nothing more than **the point at which the cap begins to bind at all**,
which is where a non-binding constraint must stop having no effect. It carries no economic content.

This also says, without claiming to adjudicate anyone, why @AHV2025 find no benefit from turnover
reduction: their cost model contains **no AUM term at all**, so they sit permanently at zero slack,
where this channel is zero by construction.

## 9. Countersignature

Maham to countersign, as with 001A, 001B and 001C. Her outstanding decision on the economic arm
(`docs/handoff/19_FOR_MAHAM_...` section 7) is independent and does not block this: every prediction
above concerns the prediction-loss cells.
