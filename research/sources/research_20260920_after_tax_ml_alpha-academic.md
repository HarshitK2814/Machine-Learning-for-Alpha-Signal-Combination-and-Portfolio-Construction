# Research lookup: after-tax evaluation of ML signal combination

**Date:** 2026-09-20
**Backend used:** built-in web search (`WebSearch`). **NOT** the skill's configured backends —
`parallel-cli` is not installed on this machine and neither `PARALLEL_API_KEY` nor
`OPENROUTER_API_KEY` is set. Results are therefore general web search, not Perplexity academic mode
or Parallel deep research. **Treat every entry below as `[verify]`** until confirmed against
Crossref or the publisher.

**Purpose:** the Closest Prior Art safeguard. Establish whether the proposed after-tax extension to
the ML signal-combination paper is already published, before any novelty is claimed.

---

## Query 1: "machine learning stock return prediction after-tax returns taxable investor portfolio"

**Finding: the ML asset-pricing literature stops at transaction costs.** Retrieved papers cover
prediction accuracy, portfolio construction, transaction costs and fee-equivalents, but the search
summary explicitly noted that results "don't specifically address after-tax returns or tax
considerations for taxable investors."

Representative retrieved items (all pre-tax):
- Maximizing Portfolio Predictability with Machine Learning — https://arxiv.org/pdf/2311.01985
- The Uncertainty of Machine Learning Predictions in Asset Pricing — https://arxiv.org/pdf/2503.00549
  (= our @LMNS2025; SSRN https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5160731)
- Performance attribution of machine learning methods for stock returns prediction —
  https://www.sciencedirect.com/science/article/pii/S2405918822000022
- Deep Learning for Forecasting Stock Returns in the Cross-Section — https://arxiv.org/pdf/1801.01777

**Implication for us:** supports the premise. The gap between the ML literature and the after-tax
literature is real.

---

## Query 2: "tax-aware machine learning factor investing after-tax alpha long-short wash sale"

**Finding: tax-aware long/short is a very large and very active PRACTITIONER field.**

- Roughly **$150bn** sits in the "tax-aware long-short" category across AQR and competitors; inflows
  of roughly $1bn/week reported.
  https://247wallst.com/personal-finance/2026/08/21/wall-street-calls-it-tax-alpha-its-a-1-trillion-machine-for-beating-the-irs-instead-of-the-market/
- AQR's own research hub on tax-aware long-short:
  https://www.aqr.com/Insights/Research/Tax-Aware-Investing/Our-Research-into-Tax-Aware-Long-Short-Investing-Clarifying-a-Few-Important-Things
- Practitioners explicitly manage the §1091 wash-sale window using correlated proxies to hold
  exposure while avoiding the 61-day window.
  https://icapital.com/insights/investment-market-strategy/the-long-and-short-of-tax-aware-investing/

**Implication for us:** the *mechanics* we implemented (wash sales, harvesting, holding periods) are
industry-standard, not novel. Our contribution cannot be "we modelled taxes carefully."

---

## Query 3: Sialm & Sosner verification

**VERIFIED.** Sialm, Clemens; Sosner, Nathan (2018). "Taxes, Shorting, and Active Management."
*Financial Analysts Journal* **74**(1): 88–107.

- Publisher: https://www.tandfonline.com/doi/full/10.2469/faj.v74.n1.1
- CFA Institute: https://rpc.cfainstitute.org/research/financial-analysts-journal/2017/taxes-shorting-and-active-management
- SSRN: https://www.ssrn.com/abstract=2907195
- AQR: https://www.aqr.com/Insights/Research/Journal-Article/Taxes-Shorting-and-Active-Management
- **DOI: 10.2469/faj.v74.n1.1**

> ### CORRECTION REQUIRED IN OUR BIBLIOGRAPHY
> `_build/lit_tax_online.py` currently records `doi="10.2469/faj.v74.n1.4"` for `SS2018`.
> That is **wrong**. The correct DOI is **10.2469/faj.v74.n1.1**.

**Substance:** short positions create tax benefits because they enhance opportunities to time
capital-gain realisations. Long positions tend to realise net **long-term** gains (low rate); short
positions tend to realise net **short-term losses** (high rate, so valuable as offsets). Strategies
using short selling can therefore generate superior after-tax performance.

**Implication for us:** this is the asymmetry our ledger implements via §1233. It is *their* result.
We cite it; we cannot discover it.

---

## Query 4: Krasner & Sosner and the momentum/value tilt — **THE MOST IMPORTANT FINDING**

Krasner, Stanley; Sosner, Nathan (2024). "Loss Harvesting or Gain Deferral? A Surprising Source of
Tax Benefits of Tax-Aware Long-Short Strategies." *Journal of Wealth Management*, Summer 2024.
- SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4584287
- AQR: https://www.aqr.com/Insights/Research/Journal-Article/Loss-Harvesting-or-Gain-Deferral-A-Surprising-Source-of-Tax-Benefits-of-TaxAware-Long-Short-Strategies

Two findings that bear directly on our proposed claim:

1. **Net capital losses come from gain DEFERRAL, not loss harvesting.** Tax-aware long-short factor
   strategies can realise cumulative net capital losses exceeding **100% of initially invested
   capital within three years**, and the bulk of this arises from systematic deferral of short-term
   gains on long positions rather than elevated loss realisation.

2. **Tax awareness shifts factor exposure away from value and toward momentum** — because deferring
   gains means holding recent winners and accelerating losses means selling recent losers, which is
   mechanically a momentum tilt. They attribute the observation to Israel & Moskowitz (2012).

> ### THIS PRE-EMPTS THE NAIVE VERSION OF OUR MECHANISM CLAIM
> Our proposed claim was: *the after-tax ranking of designs reorders relative to the net-of-cost
> ranking, driven by holding-period composition.* Krasner & Sosner (2024) and Israel & Moskowitz
> (2012) have already established the reordering direction at the **factor/style** level.
> We must not present the reordering itself as a discovery.

Related, retrieved in the same search:
- Sosner, N.; Krasner, S.; Pyne, T. "The Tax Benefits of Relaxing the Long-Only Constraint: Do They
  Come from Character or Deferral?" — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3264213
- Liberman, J.; Krasner, S.; Sosner, N.; Freitas, P. "Beyond Direct Indexing: Dynamic Direct
  Long-Short Investing." — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4437402
- Krasner, S.; Liberman, J.; Sosner, N.; Brenner, S. "Levering Up to Do Good: Direct Long-Short
  Investing and Charitable Giving." — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4804911
- "A guide to 130/30 loss harvesting." *Journal of Asset Management* (2024) 25:445–459 —
  https://link.springer.com/article/10.1057/s41260-024-00374-z  (DOI 10.1057/s41260-024-00374-z)
- AQR white paper, Understanding the Tax Efficiency of Market Neutral Equity Strategies —
  https://www.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Understanding-the-Tax-Efficiency-of-EMN-Equity-Strategies.pdf

---

## Query 5: the academic ML × after-tax intersection

**Finding: no academic paper found that evaluates high-dimensional ML signal combination after
tax.** Searches across SSRN/arXiv 2025–2026 returned ML asset-pricing work on one side (Limits to
Machine Learning, AI Asset Pricing Models NBER w33351, Deep Learning in Asset Pricing, attention
models) and tax-compliance ML on the other, with nothing bridging them.

- Limits To (Machine) Learning — https://arxiv.org/pdf/2512.12735 (= our @LLG2025)
- Artificial Intelligence Asset Pricing Models, NBER w33351 —
  https://www.nber.org/system/files/working_papers/w33351/w33351.pdf
- Deep Learning in Asset Pricing (Chen, Pelger, Zhu) —
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3350138

**Caveat on this negative result.** Absence of evidence from four web searches is weak evidence of
absence. This must be re-run against Google Scholar, SSRN full-text and the AQR/Parametric
publication lists before the claim is committed to, because much of this field is
practitioner-published and poorly indexed by general web search.

---

## Net assessment for the Closest Prior Art tracker

| Component of the proposed claim | Status after this search |
|---|---|
| Taxes matter for high-turnover active equity | **Long settled.** Jeffrey & Arnott (1993) onward. Not claimable. |
| Long/short shorting creates tax benefits via §1233 character | **Settled by @SS2018.** Not claimable. |
| Net losses come from gain deferral, not harvesting | **Settled by Krasner & Sosner (2024).** Not claimable. |
| Tax awareness tilts exposure value → momentum | **Settled by @IM2012 and Krasner & Sosner (2024).** Not claimable. |
| Careful lot/wash-sale modelling | **Industry standard.** Not claimable. |
| After-tax evaluation of *high-dimensional ML signal combination* | **No prior work found.** Still open, pending a deeper search. |
| After-tax *attribution across ML design ingredients* (our factorial) | **No prior work found.** Still open, pending a deeper search. |

**Surviving formulation.** The defensible claim is narrower than what was written in
`docs/AFTER_TAX_AND_ADAPTATION.md`:

> Given that tax awareness is known to tilt factor exposures toward momentum (Israel & Moskowitz
> 2012; Krasner & Sosner 2024), does the same mechanism change which *machine-learning combination
> design ingredient* is worth paying for? Specifically: does the net-of-cost attribution across
> nonlinearity, conditioning, economic objective and uncertainty survive after tax, or does the
> ranking reorder?

The reordering at the style level is prior art and must be cited as our *prior*, not our finding.

## Sources

- https://arxiv.org/pdf/2311.01985
- https://arxiv.org/pdf/2503.00549
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5160731
- https://www.sciencedirect.com/science/article/pii/S2405918822000022
- https://arxiv.org/pdf/1801.01777
- https://247wallst.com/personal-finance/2026/08/21/wall-street-calls-it-tax-alpha-its-a-1-trillion-machine-for-beating-the-irs-instead-of-the-market/
- https://www.aqr.com/Insights/Research/Tax-Aware-Investing/Our-Research-into-Tax-Aware-Long-Short-Investing-Clarifying-a-Few-Important-Things
- https://icapital.com/insights/investment-market-strategy/the-long-and-short-of-tax-aware-investing/
- https://www.tandfonline.com/doi/full/10.2469/faj.v74.n1.1
- https://rpc.cfainstitute.org/research/financial-analysts-journal/2017/taxes-shorting-and-active-management
- https://www.ssrn.com/abstract=2907195
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4584287
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3264213
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4437402
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4804911
- https://link.springer.com/article/10.1057/s41260-024-00374-z
- https://www.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Understanding-the-Tax-Efficiency-of-EMN-Equity-Strategies.pdf
- https://arxiv.org/pdf/2512.12735
- https://www.nber.org/system/files/working_papers/w33351/w33351.pdf
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3350138
