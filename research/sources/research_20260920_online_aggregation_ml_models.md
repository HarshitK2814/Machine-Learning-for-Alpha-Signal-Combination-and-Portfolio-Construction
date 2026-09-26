# Research lookup: online expert aggregation over ML models for stock strategies

**Date:** 2026-09-20
**Backend used:** built-in web search (`WebSearch`). **NOT** the skill's configured backends —
`parallel-cli` is not installed and neither `PARALLEL_API_KEY` nor `OPENROUTER_API_KEY` is set.
**Treat every entry as `[verify]`.**

**Purpose:** check whether `alphacomb.adaptive` (regret-bounded aggregation over model cells,
scored on realised return) is already published.

---

## THE DIRECT HIT

**Remlinger, Carl; Alasseur, Clémence; Brière, Marie; Mikael, Joseph (2023). "Expert Aggregation for
Financial Forecasting." *The Journal of Finance and Data Science*, November 2023.**

- arXiv: https://arxiv.org/abs/2111.15365 · PDF https://arxiv.org/pdf/2111.15365
- SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4513503
- ScienceDirect: https://www.sciencedirect.com/science/article/pii/S2405918823000247
  (returns HTTP 403 to automated fetch; use the arXiv version)
- Amundi: https://research-center.amundi.com/article/expert-aggregation-financial-forecasting

**What it does — effectively our adaptive layer:**
- Applies **Bernstein Online Aggregation (BOA)** to combine **individual stock return forecasts
  coming from different machine-learning models**.
- Builds **long-short strategies** from the aggregated forecasts.
- Motivation stated as ours is: algorithm accuracy "may be unstable over time", so choosing one
  model ex ante is hard.
- Result: aggregation **outperforms the individual algorithms** — higher portfolio Sharpe, lower
  shortfall, **similar turnover**; works in non-stationary environments. Neural-net experts raise
  average return, Huber-loss OLS experts lower risk.
- Proposes expert and aggregation **specialisations** across a family of portfolio metrics.

> ### IMPACT ON OUR CLAIM — SEVERE
> The adaptive layer cannot be presented as novel in any of these respects:
> * aggregating over **ML models** (not assets) — done;
> * for **stock-level long-short** portfolios — done;
> * with a **regret-bounded online rule** — done, and BOA is a stronger algorithm than plain Hedge;
> * beating **individual members** — done;
> * under **non-stationarity** — done.
>
> Threat level: **HIGH**. Must enter the tracker immediately and be cited in any adaptive section.

**What is left to us (thin, but real, and must be stated as such):**
1. **Costs and taxes.** Their reward is a pre-tax, pre-cost square loss and nothing in the paper
   charges trading costs. Ours is realised **net-of-cost-and-tax** return. This is the largest
   remaining difference and it is substantive: a 120%-turnover book reporting a Sharpe of 2.77 gross
   of costs is not an implementable result.
2. **Experts.** Theirs are 13 arbitrary algorithms (the GKX suite). Ours are the cells of a
   controlled factorial design, so the weight path reads as "which design *ingredient* is currently
   worth paying for" rather than "which algorithm is hot".
3. ~~Equal-weighted benchmark~~ — **RESOLVED AGAINST US.** They do benchmark against it (PtfUNI), and
   they even report a universe where it wins. The "aggregation versus blend" comparison is theirs.

---

## FULL TEXT READ — 2026-09-20. Open questions RESOLVED.

Retrieved the 24-page arXiv PDF (v4, revised 6 July 2023) and extracted it. Facts, not summaries:

**Authors (correct order from the paper itself):** Carl Remlinger, Clémence Alasseur, Marie Brière,
Joseph Mikael. (The arXiv listing page garbles this to "Brière Marie, Alasseur Clémence".)

**Experts: the 13 Gu-Kelly-Xiu models.** OLS+H, OLS3+H, PLS, PCR, ENet+H, GLM+H, RF, GBRT+H,
NN1, NN2, NN3, NN4, NN5.

**Data: the GKX dataset.** WRDS (CRSP + Compustat), >30,000 US stocks, 1957-2017, the **94 standard
firm characteristics used by Gu et al. (2020)**. Expanding training window, rolling 12-year
validation, 30 one-year out-of-sample test years, **test period 1987-2016**.

**Where the aggregation acts:** on **portfolio weights**, not on forecasts — "since the objective is
monthly portfolio performance from any (potentially black-box) strategy and not return forecast
accuracy, the online mixture is applied on portfolio weights." BOA minimises the square loss between
the best possible portfolio returns and the returns of the K=13 expert strategies.

**Algorithm:** BOA (Wintenberger 2017), with the learning rate tuned inside the procedure, regret
rate log(K)/T. EWA (Vovk 1990; Littlestone-Warmuth 1994), ML-Poly (Cesa-Bianchi-Lugosi 2003;
Gaillard et al. 2014), **Fixed Share (Herbster & Warmuth 1998)** and Ridge are discussed in their
literature review as alternatives — so our fixed-share choice is inside their surveyed space too.

### (4) RESOLVED — YES, they benchmark against the equal-weighted blend

`PtfUNI` is exactly that: "A uniform mixture of the K portfolios, called PtfUNI, is used as a
benchmark and assigns a constant weight of 1/K to each expert throughout the test period."

They also report two further ensembles and an oracle:
* best fixed convex combination calibrated on the last validation year;
* best one-year **rolling** convex combination;
* **oracle** = best convex mixture over the test period, infeasible in practice.

Headline numbers, equally weighted portfolios, test 1987-2016 (annual Sharpe):

| Strategy | SR | Max DD | Max monthly loss | Turnover |
|---|---|---|---|---|
| Best expert (NN2) | 2.74 | 0.17 | 0.16 | 1.23 |
| **PtfUNI (equal-weight blend)** | **2.56** | 0.24 | 0.18 | 1.22 |
| Best convex combination (fixed) | 2.28 | 0.25 | 0.13 | 1.26 |
| One-year rolling convex | 2.60 | 0.17 | 0.16 | 1.22 |
| **PtfBOA** | **2.77** | **0.08** | **0.08** | 1.23 |
| Oracle (infeasible) | 2.92 | 0.07 | 0.07 | 1.24 |

So BOA beats the uniform blend on Sharpe (2.77 vs 2.56), and its real advantage is tail risk —
max drawdown 8% versus 24%, max monthly loss 8% versus 18%.

**But — the caveat we independently built into `compare()` is in their own results.** On the bottom
1000 stocks by market cap: "The naive constant weighting PtfUNI provides the highest SR for small
stocks (3.07)" — the equal-weighted blend **beats BOA** there. This is exactly why our pipeline
prints the equal-weight row and says in words when the adaptive rule loses.

### (5) RESOLVED — transaction costs are NOT in the loss, and NOT charged at all

A full-text scan for "cost", "net of", "transaction cost" finds only two incidental uses ("costs and
tends to stabilise return estimates", "cost of higher volatility"). **Turnover of ~120-126% a year is
reported but never charged.** There is no cost model anywhere in the paper.

This is a material and legitimate differentiator: their Sharpe ratios of 2.5-2.9 are **gross of
trading costs** on a book turning over ~120% a year. Our framework charges spread, impact and borrow
inside the optimiser before anything is reported.

### (6) RESOLVED — taxes: **zero occurrences** of "tax" in the entire paper.

### Their own novelty claim

"To our knowledge, this paper provides the first application of online expert aggregation for
financial strategies." We must not contest this, and must not restate it as ours.

---

## Supporting / algorithmic prior art (cite, never claim)

| Work | Link | Role |
|---|---|---|
| Wintenberger, Optimal learning with Bernstein Online Aggregation | https://www.researchgate.net/publication/261404792_Optimal_learning_with_Bernstein_Online_Aggregation | The BOA algorithm itself |
| Online Mixture of Experts: No-Regret Learning for Optimal Collective Decision-Making (NeurIPS 2025) | https://arxiv.org/abs/2510.21788 · https://neurips.cc/virtual/2025/poster/117331 | Current frontier of no-regret expert mixing |
| Online Aggregation of Unbounded Losses Using Shifting Experts with Confidence | https://arxiv.org/pdf/1808.00741 | Shifting-expert regret — the same territory as our Herbster-Warmuth fixed share |
| Haddad, Kozak, Santosh — Factor Timing (NBER w26708) | https://www.nber.org/system/files/working_papers/w26708/w26708.pdf | Factor timing benchmark |
| Factor Timing with Portfolio Characteristics, *RAPS* 14(1):84 | https://academic.oup.com/raps/article/14/1/84/7191017 | Factor timing benchmark |
| Dynamic Factor Allocation Leveraging Regime-Switching Signals | https://arxiv.org/pdf/2410.14841 | Regime-conditioned allocation |
| Selecting and Testing Asset Pricing Models: A Stepwise Approach | https://arxiv.org/pdf/2601.10279 | Model-selection inference |
| Reinforcement Learning in Economics and Finance | https://arxiv.org/pdf/2003.10014 | Survey context |

---

## Revised position on the adaptive layer

The adaptive layer should be **demoted from a contribution to a method**, unless the full text of
Remlinger et al. shows a gap we genuinely fill. Recommended framing:

> We adopt online expert aggregation (Remlinger et al. 2023, who apply Bernstein Online Aggregation
> to ML stock-return forecasts) and change one thing: the rule is scored on realised **after-tax**
> net return rather than pre-tax performance. We report whether that change alters which design
> ingredient receives weight.

That is a legitimate, small, honest increment. It is not a headline.

## Sources

- https://arxiv.org/abs/2111.15365
- https://arxiv.org/pdf/2111.15365
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4513503
- https://www.sciencedirect.com/science/article/pii/S2405918823000247
- https://research-center.amundi.com/article/expert-aggregation-financial-forecasting
- https://www.researchgate.net/publication/261404792_Optimal_learning_with_Bernstein_Online_Aggregation
- https://arxiv.org/abs/2510.21788
- https://neurips.cc/virtual/2025/poster/117331
- https://arxiv.org/pdf/1808.00741
- https://www.nber.org/system/files/working_papers/w26708/w26708.pdf
- https://academic.oup.com/raps/article/14/1/84/7191017
- https://arxiv.org/pdf/2410.14841
- https://arxiv.org/pdf/2601.10279
- https://arxiv.org/pdf/2003.10014
