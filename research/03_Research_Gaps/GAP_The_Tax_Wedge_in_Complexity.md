# The gap: does the virtue of complexity survive taxes?

**Status: [REJECTED on synthetic data], 20 September 2026.** See section 7c. The directional
prediction failed with Spearman +1.000 against it. The international identification strategy in
section 3b does NOT depend on this hypothesis and stands on its own.

**Original status line: [proposal], 20 September 2026.** Found by the second and third research passes; raw
evidence in `sources/research_20260920b_frontier_and_gap_recheck.md` and the searches logged below.

---

## 1. The one-sentence version

> Model complexity and investor tax status interact, because **transaction costs are a level
> penalty on turnover while capital-gains tax is a rate penalty on holding period**. Complex models
> exploit more transient signal, which shifts the holding-period distribution left and pushes
> realisations from the long-term rate to the short-term rate *even at constant turnover*.
> Therefore the optimal model complexity is a decreasing function of the investor's tax rate, and
> there exists a complexity level beyond which net-of-cost performance still rises while after-tax
> performance falls.

## 2. Why this is open

**The virtue-of-complexity literature is entirely pre-tax.**
Kelly, Malamud & Zhou (*JF* 2024) prove and document that out-of-sample performance rises with
parameterisation. "The Virtue of Complexity Everywhere" extends it to US equities, international
equities, bonds, commodities, currencies and interest rates. Didisheim, Ke, Kelly & Malamud (2023)
do factor pricing models; "The Virtue of Sparsity in Complexity" (2026) and the
"Nonstationarity-Complexity Tradeoff" (2025) refine it. **None of them mentions tax.** Verified by
direct search: the literature spans six asset classes and zero tax regimes.

**The obvious extension is already taken, and it is not this one.**
Jensen, Kelly, Malamud & Pedersen, "Machine Learning and the Implementable Efficient Frontier"
(*RFS*) already asks whether complexity survives **trading costs**, and answers yes once costs are
inside the objective. That is our @JKMP2026, tracker row 1, threat High. So "does complexity
survive frictions?" is answered - **for the wrong friction**.

**The tax literature does not do complexity.**
Sialm & Sosner (2018), Israel & Moskowitz (2012), Krasner & Sosner (2024), Berkin & Ye (2003) all
study *given* factor portfolios at a single specification. Huang (2019) puts tax in an RL objective
on an average basis. Pishehvar (2026) builds lot-level tax machinery into a personalised retail RL
system. **None varies model complexity.**

**Nobody is standing in the intersection.** A direct fetch of arXiv q-fin.PM for August 2026 found
zero after-tax portfolio-construction papers and zero attribution papers.

## 3. Why the mechanism is genuinely different from transaction costs

This is the intellectual core, and it is what makes the paper more than "run JKMP again with a tax
line".

| | Transaction cost | Capital-gains tax |
|---|---|---|
| What it scales with | **Turnover** (a quantity) | **Holding period** (a distribution) |
| Functional form | level: `cost ~ k x turnover` | rate: 23.8% vs 40.8% at the s1222 boundary |
| Two books, same turnover | pay the same | can differ by **71% in rate** |
| Remedy in the literature | penalise turnover in the objective | **no remedy proposed** |

The entire cost-aware ML apparatus - putting `|dw|` in the loss - is a **turnover** instrument. It
cannot control a **holding-period** problem except by accident. A model can be made cheap without
being made tax-efficient, and that is precisely the wedge.

### We already have direct evidence for the mechanism

From `docs/AFTER_TAX_RESULTS.md`, five books over 216 months:

* monthly turnover spans **1.09x** (0.140 to 0.152) - essentially constant;
* tax as a share of gross spans **1.71x** (13.9% to 23.8%);
* ranked by long-term share of realised gains, the ordering of the tax burden is **perfectly
  monotonic, Spearman -1.000**.

**Turnover is nearly uninformative about the tax bill; holding-period composition orders it
completely.** That is the seed of this paper, already measured. It is on synthetic data with n=5
and proves nothing yet - but it is the exact quantity the hypothesis is about, and it points the
right way.

## 3b. The identification strategy: cross-country variation in tax ARCHITECTURE

This is the part that decides whether the paper is interesting or desk-rejected.

**The problem.** Inside one country the two channels are confounded. A model that trades more also
holds for less time, so turnover and holding period move together and no amount of care separates
them. A referee will say so immediately.

**The solution.** Tax architectures differ across countries **in kind, not just in level**. That
gives a 2x2 that nature built, not one we constructed:

| | **Low transaction tax** | **High transaction tax** |
|---|---|---|
| **Holding-period wedge** | **United States** - 17 pts at 12m, 0.6 bps statutory round trip | **India** - 7.5 pts at 12m, 21 bps round trip (STT both sides) |
| **Flat / no wedge** | **Germany** 26.375% flat, **Japan** 20.315% flat, **Singapore** zero CGT | **Taiwan** 30 bps sell, **UK** 50 bps buy, **Hong Kong** 21 bps, **China** zero CGT |

Generated live by `alphacomb.tax.identification_table()`.

**What each cell does for us:**

* **United States** - the holding-period channel at maximum strength with the turnover channel
  switched off. Where the effect should be largest.
* **India** - both channels on, and the wedge is less than half the US wedge while the statutory
  transaction tax is roughly 35x larger. If the complexity penalty in India tracks its *wedge*, the
  mechanism is holding-period; if it tracks its *STT*, the mechanism is turnover. This single
  country discriminates between the two hypotheses.
* **Germany and Japan - THE PLACEBO.** A flat rate means there is no boundary to cross, so the
  holding-period channel is **switched off by law**. If our complexity penalty survives in Germany,
  our mechanism is wrong and we say so. Two flat-rate countries in different regions guard against
  the placebo being a European artefact.
* **Singapore and Hong Kong - THE DOUBLE PLACEBO.** Zero capital-gains tax, so net-of-cost
  performance *is* after-tax performance. These rows reproduce exactly what the existing literature
  reports, and anchor the whole comparison.
* **United Kingdom** - flat CGT *plus* a 30-day bed-and-breakfast rule *plus* a buy-side-only
  transaction tax. It **isolates the wash-sale rule from the holding-period wedge**, which the US
  confounds by having both.
* **China A-shares** - zero CGT but a holding-period wedge on **dividends** (broadly exempt above a
  year, 10% from one month to a year, 20% below). Tests whether the mechanism is about
  capital-gains *character* specifically, or about holding-period-dependent taxation in general. No
  other country in the set has this.

**The prediction that makes it publishable.** The complexity penalty should be **ordered by the
wedge, not by the transaction tax**:

    US (17 pts)  >  India (7.5 pts)  >  Germany = Japan = Singapore = Taiwan = HK (0 pts)

while the *turnover* penalty runs the other way. A result with that shape is very hard to explain
as anything but the holding-period channel. A result where Taiwan and the UK look like the US would
falsify us cleanly.

**Why a referee should care.** "We added taxes to a backtest" is a robustness section. "Cross-country
variation in tax architecture identifies which friction channel binds on model complexity" is a
paper: it has a treatment, a dose-response ordering, two independent placebos, and a falsification
condition stated in advance.

**And it is genuinely new.** "The Virtue of Complexity *Everywhere*" covers US equities,
international equities, bonds, commodities, currencies and interest rates - six asset classes and
**zero tax regimes**. Nobody has varied the tax architecture.

## 4. Testable predictions

| # | Prediction | Falsified if |
|---|---|---|
| P1 | As complexity rises, the realised holding-period distribution shifts left (long-term share of gains falls) **at controlled turnover** | LT share is flat in complexity once turnover is held fixed |
| P2 | The effective tax rate on realisations rises with complexity | effective rate flat in complexity |
| P3 | Net-of-cost performance is increasing in complexity (replicating KMZ/JKMP) while after-tax performance is hump-shaped | after-tax performance also monotone increasing |
| P4 | The complexity that maximises after-tax performance is **decreasing in the investor's tax rate**: highest for tax-exempt, lower for taxable, lowest under s475(f) | the argmax is the same across regimes |
| P5 | Putting tax in the *objective* shifts the optimum right (you can afford more complexity if you manage its tax consequence) | tax-aware training does not move the argmax |
| **P6** | **Across countries the complexity penalty is ordered by the holding-period wedge (US > India > flat-rate countries), not by the transaction tax** | the ordering tracks transaction tax instead, or Germany/Japan show the same penalty as the US |
| **P7** | **In Germany, Japan, Singapore, Hong Kong and Taiwan the holding-period component is exactly zero**, because no such boundary exists in law | a non-zero holding-period effect appears where no holding-period rule exists - which would be a bug, not a finding |

P6 and P7 are the identification. P7 is a hard placebo: it predicts *nothing*, which is the most
falsifiable kind of prediction.

P3 is the headline. P4 is the one that makes it *useful*: it says there is no single optimal model,
only an optimal model **for a given investor**.

## 5. Why we are unusually well placed to run it

Already built and tested:

* **A complexity ladder** - random Fourier features (Rahimi-Recht) with dense ridgeless and sparse
  basis-pursuit arms, `alphacomb.models.complexity`, plus the AIPT eigenvalue-spectrum diagnostic.
  This is the standard KMZ instrument for sweeping parameterisation.
* **A lot-level after-tax ledger** with exact s1222 anniversaries, s1233, bidirectional s1091 with
  basis adjustment and holding-period tacking, four lot methods and four investor regimes.
* **A differentiable after-tax training objective** for P5.
* **A common cost-aware optimiser**, so complexity is the only thing that varies.
* **A trial log and multiplicity machinery**, so the complexity sweep is not a fishing expedition.
* **A falsification audit and a stale-portfolio guard**, so a null is credible and a solver failure
  cannot masquerade as a complexity effect (`docs/SILENT_OPTIMISER_FAILURE.md`).

The experiment is roughly: sweep P (number of random features) over the KMZ range; at each P,
record net-of-cost performance, the holding-period distribution, the effective tax rate and
after-tax performance, for each of four investor regimes; then repeat with the after-tax objective
switched on.

## 6. Honest risks

1. **Kelly and Malamud can write this themselves**, quickly, and they have the data and the
   platform. This is the main risk. It argues for moving fast and for the international/robustness
   extensions being ours rather than the core claim.
2. **The null is plausible.** If complexity mostly adds cross-sectional resolution rather than
   shortening holding periods, P1 fails and the paper becomes "complexity is tax-neutral" - still
   publishable as a robustness note, but not a headline.
3. **It needs real data.** The synthetic panel's holding-period distribution is an artefact of the
   generator. Nothing here can be established before workstream A delivers C1-C6.
4. **The complexity ladder must actually produce a gradient.** If our RFF implementation does not
   reproduce the KMZ complexity effect pre-tax, we cannot test what happens to it after tax. **This
   is the first thing to check**, and it is cheap.
5. **Taxes are investor-specific and jurisdictional.** The result is conditional on a regime, which
   referees at general-interest journals may read as narrowness. The four-regime table is the
   defence.

## 7. Relation to what we already have

This does not discard the existing design; it **reorients** it.

* The factorial attribution across four ingredients becomes the **mechanism section**: it is how we
  show the effect is holding-period composition rather than turnover.
* The after-tax ledger becomes the **measurement instrument** rather than the contribution.
* The adaptive layer drops to a robustness appendix, where it already belonged after @RABM2023.
* The complexity ladder is promoted from a design-v2 robustness rung to **the treatment variable**.

## 7b. First falsification attempt: INCONCLUSIVE, and why that matters

**Run 20 September 2026** (`tools/exp_complexity_tax.py`, synthetic panel, test years 2016-2020,
P swept 50 to 4000 with training subsampled to T = 2,000 so that c = P/T crossed 1).

The verdict printed "P1 NOT SUPPORTED", Spearman +0.086 (p=0.87). **That is not a rejection of the
hypothesis. It is a failed experiment**, and the diagnostics say so unambiguously:

| | This run | Working pipeline |
|---|---|---|
| Validation rank IC | **-0.003 to +0.004** | 0.040 to 0.052 |
| Monthly turnover | **0.1% to 0.9%** | ~15% |
| Gross Sharpe | **sign-flipped, 4 of 6 negative** | stable positive |

Subsampling training to 2,000 rows destroyed the signal. With IC at zero, Grinold scaling produces
alpha at zero, the optimiser builds almost no book, and the measured "holding-period distribution"
is noise. **There was no strategy whose holding period could be measured.**

### The design tension this exposes, which is worth recording

* The virtue-of-complexity literature defines complexity as `c = P/T` and cares about `c > 1`.
* In Kelly, Malamud & Zhou, `T` is the number of **months** (about 1,000), so `c > 1` is reachable.
* On a **panel**, `T` is stock-months (about 300,000), so reaching `c > 1` needs 300k random
  features - a design matrix of roughly 700 GB.
* Shrinking `T` to make `c > 1` reachable destroys exactly the signal the test needs.

**The two requirements are in direct conflict on a raw panel, and that is a property of the
problem, not of our code.**

### The correct design, which is how the literature actually does it

Didisheim, Ke, Kelly & Malamud work with **characteristic-managed portfolios**: project the panel
onto signal-weighted portfolio *returns*, which collapses `T` to the number of months while keeping
the cross-sectional information. That makes `c > 1` reachable *and* keeps the signal. Any serious
version of this test has to be built on managed portfolios, not on the raw stock-month panel.

An intermediate test - larger `T`, so the models actually predict, at the cost of staying below
`c = 1` - is running now. It can show whether **capacity** shortens holding periods even outside
the interpolating regime, which is the mechanism question. It cannot speak to the interpolating
regime itself.

**Status of the hypothesis: untested.** Not supported, not rejected. Anyone reading this file should
not treat the first run as evidence in either direction.

## 7c. THE HYPOTHESIS IS REJECTED

**Third run, 20 September 2026, the first valid one** (calibrated ladder, T = 20,000, ridge 1e3,
P swept 100-4000, test years 2016-2020, synthetic panel).

The run is valid this time: validation IC 0.038 to 0.050 (the working pipeline gets 0.040-0.052),
turnover 11-19% monthly, gross Sharpe positive and stable. The instrument works.

| P | val IC | turnover | **LT share of gains** | net Sharpe |
|---|---|---|---|---|
| 100 | 0.0378 | 0.189 | **0.376** | 0.050 |
| 400 | 0.0406 | 0.153 | **0.404** | 0.549 |
| 1500 | 0.0471 | 0.131 | **0.462** | 1.216 |
| 4000 | 0.0495 | 0.113 | **0.568** | 0.866 |

**P1 predicted the long-term share of gains would FALL with complexity. It rises, Spearman +1.000
(p < 0.001).** Turnover falls monotonically too, Spearman -1.000. The tax share of gross falls,
Spearman -0.800.

**Every directional prediction is backwards.** The tax-wedge mechanism as written is dead. Do not
build on it.

### Why it is backwards, in hindsight

More parameters give a better-estimated, more stable signal. Estimation noise is what drives
spurious month-to-month churn, so reducing it *lengthens* holding periods. Complexity buys
stability, and stability is tax-efficient. The folk intuition that complex models churn more is
the opposite of what happens when the extra parameters are actually being used to estimate a
stable signal better.

### The one caveat that is a real limitation, not an excuse

**The synthetic generator has stationary planted effects.** The hypothesised mechanism requires
complexity to fit *transient* signal that does not persist. Our panel contains no such signal to
fit, so the experiment is structurally incapable of producing the effect. This is the precise
subject of "The Nonstationarity-Complexity Tradeoff in Return Prediction" (arXiv 2512.23596).

So the honest status is: **rejected on the available evidence, and the evidence available cannot
test it properly.** A fair test needs non-stationary signal - real data, or a generator with
regime-switching or decaying effects. That is a real experiment someone could run, but it is not
this project's critical path and we should not pretend the current result is neutral. It is not.
It points the other way.

### The positive finding that fell out, which is worth more than the dead hypothesis

**Complexity reduced turnover by 40% and raised the long-term share of gains by 19 points.** If
that survives on real data it inverts a widely held practitioner belief and makes complex models
*more* attractive to taxable investors, not less. That is a cleaner, more useful claim than the one
we set out to test - and it is the opposite claim.

It also validates the calibration fix: with the corrected bandwidth and ridge, validation IC now
**rises** monotonically in P (0.0378 to 0.0495), which is the virtue of complexity appearing in our
data for the first time.

## 8. Immediate next step, before committing

Run the cheap falsification of our own premise: sweep the complexity ladder on the synthetic panel
and check whether **long-term share of realised gains declines in P at controlled turnover** (P1).
If it does not move, the hypothesis is dead on our own data and we should know that this week
rather than after a real-data build.

## Sources checked for this gap

- Kelly, Malamud & Zhou, "The Virtue of Complexity in Return Prediction", *JF* 2024 - https://onlinelibrary.wiley.com/doi/10.1111/jofi.13298 · NBER w30217
- Kelly, Malamud & Zhou, "The Virtue of Complexity Everywhere" - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4166368
- Jensen, Kelly, Malamud & Pedersen, "Machine Learning and the Implementable Efficient Frontier", *RFS* - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4187217
- Buncic, "Simplified: A Closer Look at the Virtue of Complexity" - https://papers.ssrn.com/sol3/Delivery.cfm/5239006.pdf
- "The Virtue of Sparsity in Complexity" - https://arxiv.org/pdf/2604.17166
- "The Nonstationarity-Complexity Tradeoff in Return Prediction" - https://arxiv.org/pdf/2512.23596
- Huang, "Taxable Stock Trading with Deep Reinforcement Learning" - https://arxiv.org/abs/1907.12093
- Pishehvar, "A Three-Phase Foundation Model for Tax-Aware Personalized Portfolio Management" - https://arxiv.org/abs/2606.30997
- Shackelford & Verrecchia, intertemporal tax discontinuity - https://ideas.repec.org/p/nbr/nberwo/7451.html
- Ivkovic, Poterba & Weisbenner, "Tax-Motivated Trading by Individual Investors" - https://economics.mit.edu/sites/default/files/publications/Tax-Motivated%20Trading%20by%20Individual%20Investors.pdf
- arXiv q-fin.PM August 2026 listing - https://arxiv.org/list/q-fin.PM/2026-08
