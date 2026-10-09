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
| 4 | Contribution contested on four fronts | Severe | **Worse.** See §3 |
| 5 | No economic mechanism | Severe | **Partly.** See §4 |
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
much more crowded ground. Our prior-art tracker has **42 rows and none of these in it**, because it
was built for a tax paper:

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

Stated conservatively, after the above:

1. **Non-US capacity frontiers, and they are an order of magnitude below the US estimates.**
   Korajczyk-Sadka put momentum at $2–5bn and later work puts size/value at $50–170bn, all US. We
   measure **$55mn (India), $106mn (Germany), $413mn (Japan)** — **10x to 100x smaller**. That is a
   new fact about where this literature's conclusions do and do not travel, and this literature is
   overwhelmingly US.
2. **The capacity channel has a positive sign, decomposed.** From the same scores: decile-spread
   Sharpe **+2.38** gross, **−9.17** net of costs uncapped, **−0.40** once participation-capped. The
   cap *adds* **8.77 Sharpe points**. Novy-Marx-Velikov's buy/hold result is the closest relative,
   but they frame turnover restriction as a *design choice that helps*; we show the *exogenous
   liquidity constraint you would want relieved* is the thing saving the strategy. Adjacent, and
   sharper.
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

## 6. What to do next, in order

1. **Rebuild the prior-art tracker for the capacity literature.** It is 42 rows of tax papers and
   is now known-incomplete in the dimension that matters. Nothing should be written until the six
   papers in §3 are read properly and the differentiation in §4 is checked against what they
   actually claim rather than against abstracts.
2. **Build the horse-race exhibit** — cost, capacity and tax drag in one table per country, per
   AUM. Every input exists; it has never been assembled in one place.
3. **The mechanism (blocker 5).** The positive capacity channel is derivable: with
   `net Sharpe = (alpha_eff - kappa*G^0.5)/sigma` and a participation cap that bounds both gross
   `G` and per-name turnover, tightening the cap lowers `alpha_eff` linearly but lowers the cost
   term as `G^0.5`, so there is a region where tightening helps. That is a one-page comparative
   static which predicts the monotone net-Sharpe and hump-shaped net-return pattern we measured
   (§5b of `RESULTS_CAPACITY`). Writing it converts the paper from "we measured this" to "theory
   predicts this and we test it" — exactly what the audit asks for and the one blocker still fully
   open.
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
