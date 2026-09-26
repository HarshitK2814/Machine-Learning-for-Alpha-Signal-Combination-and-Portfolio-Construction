# Second research pass: is the gap still there, and where has the field moved?

**Date:** 2026-09-20 (second pass, same day)
**Backend:** built-in web search + direct arXiv listing fetch. Still **not** the configured research
backends (`parallel-cli` absent, no API keys). Everything `[verify]`.
**Trigger:** the claim table showed "No prior work found / Low-moderate confidence" on the only two
rows that are ours. That is not good enough to build a paper on.

---

## 1. NEW THREATS FOUND TODAY — the after-tax ML space is no longer empty

### 1a. Huang (2019), "Taxable Stock Trading with Deep Reinforcement Learning"
arXiv **1907.12093**

* RL trading agent that optimises **after-tax** returns using an **average tax basis**.
* Headline: **"tax ignorance could induce more than 62% loss on average portfolio returns"**, and
  taxes are "much higher compared to transaction costs".

> **This is our premise, published in 2019.** "Taxes matter more than trading costs for an ML
> trading strategy" is not ours to claim and never was. We must cite it in the motivation.

**What it is not:** average tax basis, not lot-level (no HIFO, no §1091, no holding-period
boundary); single-asset trading, not a cross-section; an RL agent, not signal combination; no
attribution across design choices.

### 1b. Pishehvar (2026), "A Three-Phase Foundation Model for Tax-Aware Personalized Portfolio Management"
arXiv **2606.30997** · companion arXiv **2608.05255** · **U.S. Provisional Patent 64/101,198**

The closest existing work to our tax layer. It has:
* **position-level tax-lot tracking**;
* **wash-sale constraints**;
* a **tax-aware expert head** in a Mixture-of-Experts actor-critic trained with PPO;
* tax-loss harvesting as one of six sampled objectives;
* a Chronos (T5) time-series **foundation-model** encoder, ticker-identity-free;
* LoRA personalisation from real brokerage transaction history.

> **Threat: HIGH for the tax machinery.** We can no longer say lot-level tax modelling inside an ML
> portfolio system is novel. It is built, it is patent-pending, and it is more elaborate than ours.

**What it is not:** a *personalised retail* product, driven by individual objectives and brokerage
history. Not a cross-sectional signal-combination problem, not ~150 characteristics, not an
attribution of where net-of-tax value comes from, and no multiple-testing control.

---

## 2. WHAT THE CURRENT STREAM ACTUALLY CONTAINS

Direct fetch of **arXiv q-fin.PM, August 2026**, categorised against our four interests:

| Interest | Papers found |
|---|---|
| After-tax / tax-aware portfolio construction | **ZERO** |
| Attribution / decomposition of portfolio value | **ZERO** |
| ML signal or factor combination | 4 (KellyBoost; end-to-end neural shrinkage; factor-graph diversification; axiomatic trader) |
| Transaction-cost-aware / implementable | 1 (Robustness or Crowding: experimental design for strategy capacity) |

Dominant themes: RL, LLM/foundation models, alternative risk measures (CVaR, EVaR), quantum,
lifecycle/DC pensions, AMMs and DeFi.

**Reading:** tax-aware ML lives in the *applications / RL* literature, not the *asset-pricing*
literature. The asset-pricing channel we are targeting still has nobody in it. That is a real but
narrower gap than "nobody does after-tax ML".

---

## 3. WHERE THE FIELD HAS MOVED (things to be current with)

* **LLM agents for asset pricing.** "Empirical Asset Pricing with Large Language Model Agents"
  (arXiv 2409.17266); "Exploring the Synergy of Quantitative Factors and Newsflow Representations
  from LLMs" (arXiv 2510.15691); "CrossAlpha" annual-report benchmark with LLM agents (2605.29286);
  "Generative AI for Stock Selection" (2602.00196).
* **Time-series foundation models.** "Re(Visiting) Time Series Foundation Models in Finance"
  (2511.18578) - scaling TSFMs and asking how parameterisation affects asset-pricing performance.
  Pishehvar uses Chronos as a frozen branch.
* **Surveys marking the transition.** "From Econometrics to Machine Learning: Transforming Empirical
  Asset Pricing", *Journal of Economic Surveys* 2026 (doi 10.1111/joes.70002).
* **The multiverse / non-standard-errors method is spreading to new asset classes.**
  **"The Corporate Bond Factor Replication Crisis"** (arXiv **2604.07880**, 2026): **18,128** factor
  return series from **168 economically distinct constructions per signal**; average non-standard
  error **0.31%/month against an average premium of 0.22%/month** - the methodology-induced
  interquartile range *exceeds the point estimate*.
  Also "Mind Your Sorts" (Soebhag & van Vliet) on factor-construction degrees of freedom.

---

## 4. HONEST RE-SCORING OF OUR TWO REMAINING CLAIMS

| Claim | Status after this pass |
|---|---|
| "After-tax evaluation of high-dimensional ML combination" | **Weakened.** Huang (2019) owns the premise; Pishehvar (2026) owns the lot-level machinery. What survives is the *cross-sectional signal-combination* setting and the absence of any such paper in the asset-pricing stream. Confidence: still low-moderate, and for a narrower claim than before. |
| "Factorial attribution across the four ingredients, net of cost" | **Holds, and is the stronger of the two.** Zero attribution/decomposition papers in the current q-fin.PM stream. Everyone proposes methods; almost nobody decomposes where the value came from. Confidence: moderate. |

---

## 5. THE OPENING THIS PASS ACTUALLY REVEALED

Put two facts side by side:

1. The corporate-bond paper shows **non-standard errors can exceed the premium itself** when you
   enumerate construction choices, and that methodology is actively being carried into new asset
   classes in 2026.
2. **Nobody has run it after tax.** Zero after-tax papers in the stream; the NSE literature is
   entirely pre-tax.

That yields a sharper question than the one we have been asking:

> **Is the non-standard error of an ML equity strategy's *after-tax* performance larger than its
> after-tax premium?** Equivalently: once you enumerate the defensible design choices - model form,
> conditioning, objective, uncertainty treatment, *and* the tax choices nobody reports (lot method,
> wash-sale treatment, harvest usability, investor regime, accounting basis) - does the spread in
> after-tax outcomes swamp the thing being measured?

Why this is better than our current framing:
* It is **methodologically current** (NSE/multiverse is live and spreading right now).
* It is **genuinely unoccupied** - the NSE literature is pre-tax, the tax literature is
  single-specification.
* It **plays to what we have already built**: a controlled factorial grid, a common optimiser, a
  rigorous lot-level ledger, a trial log, and multiplicity machinery.
* It turns our own bugs into evidence. The silent optimiser failure
  (`docs/SILENT_OPTIMISER_FAILURE.md`) is a *researcher degree of freedom nobody reports*, and it
  was **correlated with the treatment**. So is the wash-sale granularity choice, which moved the
  disallowed-loss number by an order of magnitude.
* It survives being scooped on any single method, because the claim is about the *distribution* of
  results, not about one model winning.

**Risk:** this is a "replication crisis" genre paper. It is publishable (the bond version is
evidence) but it is a critique, not a discovery, and it needs the design grid to be defensible
rather than exhaustive - the multiverse guidance is explicit that maximal combinatorial scope is a
weakness, not a strength.

## Sources

- https://arxiv.org/abs/1907.12093
- https://arxiv.org/abs/2606.30997
- https://arxiv.org/abs/2608.05255
- https://arxiv.org/list/q-fin.PM/2026-08
- https://arxiv.org/pdf/2604.07880
- https://onlinelibrary.wiley.com/doi/10.1111/joes.70002
- https://arxiv.org/pdf/2409.17266
- https://arxiv.org/pdf/2510.15691
- https://arxiv.org/pdf/2605.29286
- https://arxiv.org/pdf/2602.00196
- https://arxiv.org/html/2511.18578v1
- https://arxiv.org/pdf/2605.19745
- https://wp.lancs.ac.uk/fofi2022/files/2022/08/FoFI-2022-124-Bart-van-Vliet.pdf
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3545001
