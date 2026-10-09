# Where this paper actually stands, against the goal we set in September

**Date:** 2026-10-09
**Written because:** a day of work produced a new headline, and before building further on it I went
back to `research/03_Research_Gaps/PUBLICATION_READINESS_AUDIT.md` and
`research/02_Journal_Strategy/Journal_Strategy.md` to check it against what we originally set out to
do. It does not clear the bar we wrote down, and the reason is one we diagnosed in September and
have now walked into from the other side.

---

## 1. The goal, as we defined it

From the journal strategy: **primary targets JFQA and Management Science (Finance)** (fit 9,
difficulty 4); RFS/JF/JFE as stretch, and explicitly only *"if the decomposition yields a general
lesson about why ML adds value"*.

From the readiness audit, six blockers. Current status:

| # | Blocker | Sep 20 | Today |
|---|---|---|---|
| 1 | No real data | **Fatal** | **Resolved.** DEU/IND panels complete, JPN partial |
| 2 | No statistical inference | **Fatal** | **Resolved.** Deflated Sharpe, PBO-CSCV, Romano-Wolf, SPA, HAC |
| 3 | No identification argument | **Fatal** | **Changed, not resolved.** See §2 |
| 4 | Contribution contested on four fronts | Severe | **Worse, then better.** Worse on measurement (§3); resolved by moving to the sign flip, which is an open dispute rather than occupied ground (§4 item 2) |
| 5 | No economic mechanism | Severe | **Closed, pending Japan.** `net Sharpe = (alpha_eff − kappa·G^0.5)/sigma` with `kappa ∝ sqrt(AUM/ADV)` predicts a sign change; measured over nine decades of AUM in two markets; pre-registered for Japan in `AMENDMENT_001D` |
| 6 | Dead components | Moderate | Resolved (demoted to appendix) |

## 2. Blocker 3: the identification we designed for failed, and its replacement is different in kind

The audit's answer to "what identifies the effect?" was explicit: *"The cross-country
tax-architecture design is a genuine identification strategy with a dose-response ordering and two
placebos written into law. It is currently framed as an extension. **It should be the paper.**"*

**That design was run and it failed.** The pre-registered statistic returned the wrong sign and was
separately ill-defined; the post-hoc replacement was a between-arm artefact
(`docs/RESULTS_WEDGE_TEST.md` §2, §5). What survives of it is a statutory fact — the holding-period
channel exists only where the law creates a boundary — and a magnitude finding that kills it as a
headline: **costs beat taxes 5x in Germany and 53x in India.**

The capacity finding that replaced it has a *different kind* of identification, and on its own terms
a good one:

> The treatment is AUM, which we set exogenously at $0.1bn / $1bn / $10bn; the cross-sectional
> variation in treatment intensity is market depth, which puts the capacity frontier at $106mn in
> Germany, $55mn in India and $413mn in Japan without anything we chose; and Japan below $413mn is
> a region where the constraint does not bind at all, giving a control.

That is one sentence, it is causal, and it would pass the desk-rejection test the audit names. It is
pre-registered for Japan as of `AMENDMENT_001C`. **So blocker 3 is in better shape than it looks —
but for a different paper than the one we designed.**

## 3. Blocker 4 is now the binding constraint, and it is worse than it was

The audit said of the tax design: *"None of them does cross-country identification of which friction
channel binds. **That is the only uncontested ground we hold.**"* We have moved off that ground onto
much more crowded ground.

> **CORRECTED 2026-10-09.** This section originally said our tracker had *"42 rows and none of these
> in it"*. That is wrong: **@ACM2023 is row 5 and @AHV2023 is row 10.** The real failure was not
> omission but **mis-rating** — both were scored against the *attribution* claim, at Low and Medium
> threat respectively, and nobody re-scored them when the headline moved to frictions. They are now
> High and Severe. What was genuinely absent is the **capacity** literature (@KS2004, @NMV2016,
> @GP2013, @CV2023) and the **international ML** literature (@CFMZ2023, 46 markets, JEDC 2023, which
> means "ML outside the US" is not available to us as a contribution either). All of it is now in
> tracker sections C1–C8, added from **full texts**, not abstracts.

| Paper | Venue | What it owns | Overlap |
|---|---|---|---|
| **Avramov, Cheng & Metzker** | **Management Science 2023** | ML return predictability collapses under realistic frictions: high turnover, extreme positions, and restrictions (microcaps, no credit rating, distress) cut returns by more than half | **Severe.** This is our finding, and it is published in **one of our two primary target journals** |
| **Novy-Marx & Velikov** | RFS 2016 | Taxonomy of anomalies and their trading costs; capacity each can absorb; turnover is the main driver; **buy/hold spreads are the most effective mitigation** | **Severe.** The buy/hold result is adjacent to our positive capacity channel |
| **Korajczyk & Sadka** | JF 2004 | Break-even fund size under price impact; $2–5bn for momentum | **High.** Their break-even fund size *is* our capacity frontier |
| **Gârleanu & Pedersen** | Capacity of trading strategies | Sharpe falls as invested capital grows; capacity as dollar volatility at a target Sharpe | **High**, and note the sign: they find Sharpe *falling* in scale |
| **Chen & Velikov** | Accounting for the anomaly zoo | Trading-cost perspective on the anomaly zoo | Moderate |
| **Azevedo, Hoegner & Velikov** | SSRN / AFA | **Counter-argument:** value-weighting plus falling costs leave ML strategies profitable | Severe — an active dispute we would be entering |

**Assessment: "ML alpha does not survive frictions" is occupied, and occupied in our target journal.**
Submitting the capacity finding as the headline to Management Science would be read as incremental
to a paper they published two years ago.

## 4. What is genuinely ours

> **CORRECTED 2026-10-09, later the same day.** Items 1 and 2 below were written against search
> summaries and abstracts. I then obtained and read the full texts. **Item 1 is wrong and is
> withdrawn** — see the strikethrough and `AMENDMENT_001D` section 1, and tracker section C8.1.
> **Item 2 was understated**, and its corrected form is now the paper's headline — see
> `AMENDMENT_001D` and tracker section C3. Items 3 and 4 stand. The original text is kept rather
> than deleted, because the record of what we believed on abstracts versus on full texts is itself
> the argument for reading the papers.

1. ~~**Non-US capacity frontiers, and they are an order of magnitude below the US estimates.**
   Korajczyk-Sadka put momentum at $2–5bn and later work puts size/value at $50–170bn, all US. We
   measure **$55mn (India), $106mn (Germany), $413mn (Japan)** — **10x to 100x smaller**.~~
   **WITHDRAWN.** The comparison was not turnover-matched. Novy-Marx & Velikov (RFS 2016, Table 7)
   report, *in the US*, **$0.38–0.44bn** for a high-frequency combination strategy and
   **$0.18–0.53bn** for industry relative reversal. Their capacities span $0.18bn to $169bn *within
   one paper*, ordered by turnover. Our monthly-rebalanced ML books belong in the high-turnover
   panel, where **Japan's $413mn is inside the US range**, Germany's $106mn is ~2–4x below it and
   India's $55mn ~3–10x below it. Three further mismatches (definition, impact law, dollar vintage)
   confound even that residual gap; tracker section C6 lists what must be matched before any
   capacity number is published. One of @NMV2016's authors co-authors @AHV2025, so a referee who
   owns this is likely.
2. > **RETRACTED 2026-10-09, 12:30 IST — THIRD PASS. The sign flip was a cost-input coverage
   > artefact and is withdrawn in full.** See `AMENDMENT_001D` retraction header and §10. In one
   > line: the ladder formed deciles on Germany's **signal-bearing** cross-section (~382 names)
   > rather than its **investable** one (~246), because the promoted C6 prices only 65.1% of
   > Germany against 99.1% of India. An uncovered name was charged **zero cost** in the uncapped
   > book and given **cap = 0** in the capped book — both pushing the channel down, and only in
   > Germany. Enforcing the project's own non-tradeability rule reverses the sign at $100k from
   > **−0.811 to +0.062**, while India (the 99.1%-coverage control) moves only +0.183 → +0.211.
   > **On the compliant universe the channel is positive at every rung in both markets**, so we
   > never observe the regime where the cap hurts and **cannot** adjudicate
   > @NMV2016-versus-@AHV2025. The surviving claim is item 2' below.
   >
   > The spurious result was **t = −6.10**, and it survived a value-weighting robustness check and
   > a six-fold impact-coefficient sweep. Only the coverage rule killed it. That is the third time
   > today a correctly-computed quantity met the wrong benchmark, and the second time one of my own
   > robustness checks failed to catch it.

   **2'. The surviving claim: the capacity channel is positive, monotone in AUM, and large.**
   On the compliant universe the ADV participation constraint **creates** risk-adjusted
   performance at every scale measured, rising monotonically to **+8.05** (Germany) and **+4.51**
   (India) Sharpe points at $1bn. Robust to equal- versus value-weighting, to the impact
   coefficient over `k ∈ {0.5, 1, 2, 3}`, and to the coverage treatment. This is the
   @NMV2016/@KS2004 side of the literature confirmed in non-US markets at AUM-indexed scale — a
   measurement, not an adjudication, and weaker than what §5 and item 2 claimed before 12:30.

   ~~**The capacity channel changes sign with scale, and the crossover is measurable.** This is the
   corrected and much stronger form of what item 2 originally said.~~ Measured over **nine decades of
   AUM** on the German and Indian scores, the capacity channel is **monotone increasing in AUM** and
   **crosses zero**: Germany between **$3mn and $4mn**, India between **$1k and $3k**. Below the
   crossover the participation cap **destroys** net Sharpe (Germany −0.69 at $100k); above it the cap
   **creates** net Sharpe (+8.77 at $1bn, asymptote **+10.40**). That matters because the literature
   disagrees about this sign in print: @NMV2016 (RFS) and @KS2004 (JF) find turnover reduction and
   liquidity tilting help — @KS2004 get a **5,000x** break-even range from the tilt alone — while
   @AHV2025 find the same mitigations do **not** improve net performance, because post-decimalisation
   costs are only 20–25bp/month. All three are US and all three are right about their own setting.
   Both positions fall out of `net Sharpe = (alpha_eff − kappa·G^0.5)/sigma` with
   `kappa ∝ sqrt(AUM/ADV)`: @AHV2025 sit at `kappa ≈ 0`, where a cap can only forfeit alpha. **We
   reproduce their regime inside our own data** — at $100k India's uncapped decile spread has a
   *positive* net Sharpe (+0.07) — and then walk it up nine decades to where the cap is worth +10
   Sharpe points. The crossover is **not** a fixed multiple of the capacity frontier (3.6e-2 vs
   3.3e-5 in frontier units against a frontier ratio of 1.9x), which is an open question we report
   rather than paper over. Pre-registered for Japan in `AMENDMENT_001D`, declared before any
   Japanese portfolio existed.
3. **Taxes ruled out as second-order, with a real tax engine rather than an assumption.** Lot-level
   HIFO, three genuine statutory regimes, a dated engine spanning a real reform. Cost drag beats tax
   drag **5x** (Germany) and **53x** (India). The tax-aware-investing literature
   (Sialm-Sosner, Israel-Moskowitz, Huang 2019) is second-order at institutional scale in these
   markets. **Nobody has both machines on non-US data**, which is why nobody has said this.
4. **The design-axis null.** With the broken economic arm removed, no factorial axis is detectable
   (t = +0.48, −1.20, +1.53) while the signals themselves carry IC t up to +10.4. Avramov et al.
   show ML *degrades*; they do not show that the *choice among ML designs* becomes undetectable.
   That is a distinct and useful message for the design literature (Gu-Kelly-Xiu and successors).

## 5. The framing I think is strongest

> **SUPERSEDED 2026-10-09, later the same day.** The horse race below is still the right *structure*
> for the paper, but it is not the right *claim*, because a horse race is a measurement and
> measurements in this literature are occupied. The claim is now **the sign flip** (section 4 item 2,
> `AMENDMENT_001D`):
>
> > **When does a liquidity constraint help a machine-learning strategy?** The literature disagrees
> > in print. Novy-Marx & Velikov (RFS 2016) find turnover reduction is the most effective cost
> > mitigation available; Korajczyk & Sadka (JF 2004) obtain a 5,000-fold range in break-even fund
> > size from a liquidity tilt alone; Azevedo, Hoegner & Velikov (2025) find the same mitigations do
> > not improve net performance at all. We show these are not competing findings but the two limits
> > of one expression. The effect of a participation constraint on net Sharpe is monotone in
> > `kappa ∝ sqrt(AUM/ADV)` and **changes sign** at a measurable mandate size — $3–4mn in Germany,
> > $1–3k in India — destroying 0.69 Sharpe points below it and creating 10.40 above it. We locate
> > the crossover in three jurisdictions, show it is not a fixed multiple of the capacity frontier,
> > and rule out the tax channel as second-order with a lot-level engine spanning three statutory
> > regimes and a real reform.
>
> The horse race becomes the paper's **second table**: having established the scale parameter, it
> prices all three frictions on the same signals and shows capacity dominates costs and taxes. Keep
> everything below; it is the structure, not the headline.

Not "capacity kills ML alpha" — that is taken. Instead a **friction horse race**, which is the one
thing our machinery can do that nobody else's can:

> **Where does machine-learning alpha go?** For an institutional investor in a mid-size equity
> market, three frictions compete: transaction costs, liquidity capacity, and taxes. We measure all
> three in one framework, on the same signals, across three jurisdictions chosen for genuine
> statutory tax variation. Capacity dominates by one to two orders of magnitude; the tax channel
> that a decade of tax-aware-investing research is built on is **undetectable** at institutional
> scale; and the capacity constraint, counterintuitively, *improves* net performance because it
> suppresses turnover faster than it suppresses signal. The capacity frontier is $55mn–$413mn,
> an order of magnitude below published US estimates.

This keeps the tax machinery as the **measuring instrument that rules the tax channel out** — which
is what `REFRAMED_CLAIM.md` always said the ledger was — rather than as a failed headline. It uses
every asset we have. And the horse race is novel because the three literatures do not talk to each
other and nobody has all three instruments on one dataset.

**Realistic venue: JFQA primary** (Management Science is compromised by Avramov et al.), with
Review of Asset Pricing Studies and Journal of Financial Markets as strong alternatives. **Not
JF/JFE/RFS** — the audit's own condition for tier 1 was a general lesson about *why* ML adds value,
and our lesson is about why it does not arrive, in markets the field does not study. That is a good
field-journal paper, not a top-three paper, and saying otherwise would waste a year.

> **REVISED 2026-10-09, later the same day.** With the sign flip as the claim, the venue judgement
> improves but does not reach tier 1. **JFQA remains the primary target** and is now a *better* fit,
> because the paper adjudicates a disagreement between an RFS paper and a JF paper and their
> successor, which is squarely what JFQA publishes. **RFS becomes a defensible stretch** rather than
> a fantasy: the mechanism is a general lesson about when a liquidity constraint helps, not a
> country study, and @NMV2016 is an RFS paper. I would still submit to JFQA first — the lesson is
> about when ML alpha *fails to arrive*, the effect is identified off a cost model rather than off
> an experiment, and Japan's confirmation is not in yet. Management Science stays compromised.

## 6. What to do next, in order

> **Progress 2026-10-09, later the same day:** items 1 and 3 are **done**, and doing item 1 is what
> forced the corrections above. Item 3 turned out to be the headline rather than a supporting
> section. Items 2, 4 and 5 are open and are now the whole remaining critical path.

1. ~~**Rebuild the prior-art tracker for the capacity literature.**~~ **DONE** — tracker sections
   C1–C8, six papers plus @CFMZ2023, from full texts. It produced the withdrawal in §4.1, the
   re-rating in §3, and the discovery of the @NMV2016-vs-@AHV2025 dispute that became the claim.
2. **Build the horse-race exhibit** — cost, capacity and tax drag in one table per country, per
   AUM. Every input exists; it has never been assembled in one place.
3. ~~**The mechanism (blocker 5).**~~ **DONE, and it became the paper.** The comparative static is
   as sketched: `net Sharpe = (alpha_eff - kappa*G^0.5)/sigma`, tightening lowers `alpha_eff`
   linearly and the cost term as `G^0.5`, so there is a region where tightening helps. What was not
   anticipated is that it also predicts a **region where tightening hurts**, and that both regions
   are observable in our own data. Measured over nine decades of AUM: Germany's capacity channel
   runs −0.69 → +10.40 with a zero at **$3–4mn**; India's −0.004 → +4.61 with a zero at **$1–3k**.
   Pre-registered for Japan as `AMENDMENT_001D`, declared before any Japanese portfolio existed.
   Ladder: `docs/attachments/CAPACITY_CHANNEL_LADDER_2026-10-09.csv`.
4. **Inference on the new central numbers.** The decile-spread Sharpes (+2.38, +1.00) have no
   standard errors yet, and the +2.38 → +0.128 wedge has no formal test. The inference layer
   exists; it has not been pointed at these.
5. **Japan's confirmation**, per `AMENDMENT_001C`. Its capacity frontier is already in; its model
   arm is still training.

## 7. The uncomfortable summary

We set out to own *cross-country identification of which friction channel binds*. We built the
machinery, ran it, and **the channel we expected to bind does not** — it is 5 to 53 times too small
to matter. The channel that does bind is one other people have studied, in a market we do not study.

The honest paper that comes out of that is still a good paper, because we can measure all three
frictions at once and nobody else can, and because the non-US frontiers are genuinely new and
genuinely small. But it is a JFQA paper about where ML alpha goes, not a top-three paper about tax
architecture. The sooner the framing moves, the less of the remaining time is spent defending a
headline that the data has already refused twice.

---

## 8. Addendum, same day: reading the papers changed the answer

Everything above §4 was written against abstracts and search summaries. I then obtained the full
texts. Three things happened, in this order, and the order matters.

**One claim died.** "Our frontiers are 10–100x below US estimates" compared our high-turnover books
against low-turnover US strategies. @NMV2016 reports $0.18–0.53bn for *its* high-turnover
strategies, in the US. Turnover-matched, Japan is inside the US range. That was the lead item in
§4, and it is gone. **The non-US frontiers are no longer a contribution.**

**One claim was understated.** The "+8.77 Sharpe points" was one point on a curve. The curve runs
nine decades, is monotone, and **crosses zero** — which means the participation cap sometimes
*hurts*, something neither §4 nor `AMENDMENT_001C` anticipated. That is a strictly stronger result
than a positive sign, because a sign that flips has a mechanism and a positive sign is just a fact.

**The literature turned out to be arguing about exactly that sign.** @NMV2016 (RFS) and @KS2004 (JF)
on one side, @AHV2025 on the other, all US, all internally consistent. Occupied ground became an
open question with named parties, and our design already contained the dose-response that answers
it. **This is the first time in this project that the prior art helped rather than threatened.**

The lesson for the remaining work is narrow and practical: **this project has now been wrong twice
in the same way** — the pre-registered tax statistic, and the frontier comparison — and both times
the error was a quantity computed correctly and then compared against the wrong benchmark. The
pipeline is not the risk. The benchmark is. Tracker §C6 lists the three matchings (turnover, units,
impact law) that any capacity number must pass before it is published, and that list should be run
against every headline number, not only the capacity ones.

**What is still genuinely open, and what the paper's credibility now rests on:**

* **Inference on the crossover.** The crossover AUMs ($3–4mn, $1–3k) are point estimates from a
  ladder with no standard errors, and the capacity channel has no formal test anywhere. This is now
  the single largest gap, because the crossover *is* the claim. The inference layer exists
  (deflated Sharpe, Romano-Wolf, SPA, HAC) and has never been pointed at these quantities.
* **Japan**, per `AMENDMENT_001D` D2 and D3.
* **Why the crossover is not a fixed multiple of the frontier** (3.6e-2 vs 3.3e-5 in frontier units
  against a frontier ratio of 1.9x). Reported as open; the candidate explanation is the share of
  alpha sitting in the illiquid tail, and it is testable with what we have.
* **The horse-race exhibit** (§6 item 2), which is now table 2 rather than the headline.
