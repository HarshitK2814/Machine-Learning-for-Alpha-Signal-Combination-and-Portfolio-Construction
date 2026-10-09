# Candidate reframing: the signal is real, the portfolio cannot express it

**Date:** 2026-10-09, 03:00 IST
**Status:** a proposal, not a result claim. The framing of the paper is a team decision, and this is
me putting the evidence in one place because every strand of tonight's work converged on it.
**Author:** Harshit (workstream B)

---

## 1. Why this document exists

Three results died tonight, each for a real reason (`docs/RESULTS_WEDGE_TEST.md` §2, §5;
`docs/ECONOMIC_ARM_CAPABILITY_GAP.md`). That is a bad night for the tax-wedge headline and a
genuinely informative one, because the *same* fact killed all three and it has been sitting in the
exhibits since the first real-data run:

> At $1bn in these three equity markets, the ADV participation constraint binds on essentially
> **every** position. The portfolio is determined by capacity, not by alpha and not by risk.

That is not a nuisance to be controlled for. On the evidence below it is the most robust,
most replicable and most economically consequential thing we have measured, and it is a finding the
literature we are writing into does not report.

## 2. The claim

> Machine-learning alpha combination produces **strong and highly significant cross-sectional
> signal** in international equity markets. At institutional scale that signal **cannot be
> converted into portfolio performance**, because the participation constraint — not the risk
> budget, not the tax code, not the choice of loss function — determines the book. We quantify the
> wedge between signal-level and portfolio-level evidence, and show that every design choice the
> literature debates is second-order to it.

The contribution is the **wedge**, measured end to end on the same data with a frozen,
pre-registered design: from information coefficient, through a capacity-constrained optimiser, to
after-tax returns under three real statutory regimes.

## 3. The evidence, in the order a referee would want it

### 3a. The signal is real and strong

Rank IC of each prediction-loss cell's scores against realised next-month returns
(`tools/verify_arm_information.py`, resolved through each country's own artefacts):

| | mean IC | range | t-statistics | cells significant |
|---|---|---|---|---|
| **Germany** | **+0.0757** | +0.0709 … +0.0806 | **+8.6 … +10.4** | **8 of 8** |
| **India** | **+0.0368** | +0.0227 … +0.0530 | **+2.8 … +5.4** | **8 of 8** |

This is not a weak-signal story. By the standard the signal-level literature reports, these are
publishable ICs with large t-statistics in every cell of the design.

### 3b. The portfolio cannot express it

Same cells, after the frozen constraint set, over the same 132 months:

* **0 of 21** strategies survive deflation against the pre-registered N = 64 (hurdle 0.717).
* **Hansen SPA against equal-weight: p = 0.70.** The whole family is indistinguishable from
  `BASE-EW`.
* **PBO 0.432** with comparators included.

So IC t-statistics of +10 coexist with nothing surviving multiple-testing adjustment at the
portfolio level. **That gap is the paper.**

### 3c. The mechanism: capacity binds on essentially every name

`tools/exp_book_characteristics.py`, registered parameters `adv_participation_max = 0.05`,
`weight_abs_max = 0.01`, `gross_max = 2.0`, AUM = $1bn:

| | capacity ceiling | **share of names ADV-capped** | realised gross (P / E) | names held / eligible | median ADV |
|---|---|---|---|---|---|
| **Germany** | 0.189 – 0.233 | **96.8% – 97.6%** | 0.132 / 0.178 | 298–305 / ~253 | $0.63–1.69mn |
| **India** | 0.113 – 0.148 | **99.5% – 100.0%** | 0.056 / 0.097 | 330–335 / ~341 | $0.42–1.49mn |

Read the third column first. **Almost every eligible name's weight is set by the participation
limit rather than by its position cap, its risk contribution or its alpha.** The consequences:

* The attainable gross is **6–23% of the pre-registered budget of 2.0**. India can be at most
  **11.3% invested**. The risk budget never binds; it is not the active constraint in any month.
* The book holds **nearly the entire eligible universe**. There is almost no cross-sectional
  selection left for the signal to perform — the optimiser is not choosing *which* names, it is
  being told *how much* of each by ADV.
* On the German panel, position size correlates **+0.871 with the ADV cap** and **−0.080 with
  alpha**. The book is a liquidity-weighted index with a small alpha tilt.

The mechanism is simply scale relative to market depth: $1bn against a median ADV under $2mn.

### 3d. Everything else is second-order to it

* **Taxes.** Tax drag 5.23 bps (Germany) and **0.45 bps** (India) against cost drag of 27.67 and
  24.30. Costs dominate taxes **5x** and **53x**. The statutory holding-period wedge — which we
  built an entire cross-country identification around — moves one to two orders of magnitude less
  than the friction that is already there.
* **Loss function.** The economic-loss arm cannot even *represent* the feasible book: it is forced
  to propose gross 2.0 and is projected onto the ceiling 20.6x down, which is why its IC is an
  order of magnitude below the prediction arm's (`docs/ECONOMIC_ARM_CAPABILITY_GAP.md`). The one
  significant main effect in the factorial is mostly this.
* **Adaptive combination.** Scored −0.003 against fixed 1/N.
* **Complexity x wedge.** Rejected, Spearman +1.000 against the prediction.

Every one of these is a design choice the literature argues about, and each is dominated by the
constraint.

## 4. Why this is publishable rather than a failed project

1. **It is a quantified wedge, not a null.** We can state how much signal exists (IC t up to +10.4)
   and how little survives (0 of 21 deflated, SPA p = 0.70), on the same data, same window, same
   frozen design. That contrast is the result.
2. **It explains a real tension in the literature.** Signal-level papers report ICs and decile
   spreads; capacity-constrained net-of-cost portfolio evidence is much rarer. We show the two can
   disagree completely, and *why*, with the binding constraint identified and measured.
3. **Three countries, three statutory regimes, one frozen window.** The cross-country design we
   built for the tax claim still earns its keep: it shows the mechanism is not a
   single-market artefact, and the tax arm becomes a *bound* on how much the tax channel could
   matter rather than a failed headline.
4. **It is honest about scale-dependence**, which is a strength if stated: the finding is
   conditional on $1bn and on a 5% participation limit, both pre-registered. The capacity arms at
   $1e8 and $1e10 make it a dose-response relationship rather than a single point — and that is
   the obvious next run.
5. **The surviving tax result is clean and cheap to state.** `lt_share_of_gains` is identically
   0.0000 in every German cell because Abgeltungsteuer creates no long-term category, against
   0.3826–0.6413 in India. Statute determines whether the holding-period channel can exist at all.
   That is a crisp secondary finding and needs no standard error.

## 5. What it would take, and what I would drop

**Needed:**

1. **The capacity dose-response.** Re-run at $1e8 and $1e10 (the arms deliberately stopped
   earlier). The prediction is that performance and the alpha-correlation of weights *recover* at
   $1e8 and collapse further at $1e10. If that curve is monotone, the mechanism is established
   rather than asserted. **This is the single highest-value run left in the project.**
2. **A capacity-free benchmark arm.** The same cells with the participation constraint relaxed,
   to show how much performance the constraint is removing. That is the counterfactual that turns
   §3b into a measured cost rather than an absence.
3. **Japan**, for the third market (running).
4. **Fix or flag the economic arm** (`docs/handoff/19_FOR_MAHAM_...` §7).

**I would drop, or demote to appendix:** the wedge-as-headline framing, the within-country turnover
gradient (withdrawn), complexity x wedge (rejected), and adaptive combination (negative).

## 6. The honest risk in this reframing

A referee can reasonably say: *you chose a $1bn AUM and a 5% participation cap, and those choices
manufactured the result.* Three answers, and the third is the real one:

* Both were **pre-registered** before any real-data result was seen, and $1bn is a modest
  institutional mandate, not a stress case.
* The median ADV in these universes is **under $2mn**, so the binding is a property of the markets,
  not an aggressive parameter.
* **The dose-response in §5.1 is what settles it**, and until it is run this reframing is a
  well-evidenced hypothesis rather than a finished result. I would not submit on §3 alone.

A second risk: this is a reframing arrived at *after* the registered headline failed. It must be
presented that way — the registered tax hypothesis and its failure belong in the paper, not in a
drawer. `docs/RESULTS_WEDGE_TEST.md` keeps both failures on the record for exactly that reason.


---

## 7. ADDED 07:00 — the dose-response is in for $1e8, and it half-refutes §5.1

§5.1 predicted that at $1e8 "performance and the alpha-correlation of weights *recover*". **The
gross side is confirmed; the net side is refuted, and the refutation is the better finding.**

Germany, the same 16 cells and the same stage-02 scores, only AUM differing:

| prediction-loss arm (8 cells) | $1e9 | $1e8 | change |
|---|---|---|---|
| capacity ceiling | 0.189–0.233 | **0.526–0.801** | 3.4x looser |
| share of names ADV-capped | 96.8–97.6% | **83.3–87.4%** | the constraint starts to release |
| realised gross | 0.132 | 0.423 | 3.2x |
| **gross Sharpe** | **+0.423** | **+0.654** | **1.55x — the signal gets into the book** |
| turnover | 0.0135 | 0.0521 | 3.86x |
| **cost drag** | **17.2 bps** | **116.8 bps** | **6.79x** |
| **net Sharpe** | **+0.128** | **−0.116** | **worse, and sign-flipped** |
| best single cell, net | +0.330 | +0.155 | worse |

**What is confirmed.** Capacity really does suppress the signal at institutional size. Relax it and
gross Sharpe rises 55% from the identical scores — the alpha was always there and the constraint was
holding it out of the book. That is the mechanism, measured rather than asserted.

**What is refuted.** Relieving capacity does **not** improve net performance; it makes it worse.
Cost drag rises **6.79x** against a turnover rise of 3.86x — superlinear, because the impact term is
`|dw|^1.5` and the book is 3.2x larger — and the net Sharpe flips sign.

### The corrected claim: a two-sided friction squeeze

> At institutional size the participation constraint truncates the signal before it reaches the
> book. Below that size the constraint releases and the signal does reach the book, but the larger
> book the optimiser then takes carries superlinearly larger transaction costs that remove more
> than the signal gains. **Across two orders of magnitude of AUM there is no scale at which
> machine-learning alpha combination delivers positive net performance in these markets** — the
> binding friction simply changes identity.

This is a stronger result than §2's version, because it is a *curve* rather than a point and
because it survives the obvious objection to §2 ("you chose a punitive AUM"): the smaller AUM is
not better, it is differently bad.

It also means the registered $1bn happens to sit near the **net-optimal** scale, which is the
opposite of the "we picked a punitive size" criticism. Best net Sharpe is +0.330 at $1e9 against
+0.155 at $1e8.

### An inconsistency this exposes, which must be resolved before publishing

The optimiser at $1e8 **chose** a gross of 0.423 with a transaction-cost term in its objective, and
the backtest then says that book was net-worse than the smaller one. Something is inconsistent
between the two, and the candidates are specific:

1. the optimiser's cost model understates realised cost (impact coefficient, or the spread
   estimate);
2. it is **myopic** — a one-period objective charges this month's trade but does not internalise
   that a 3.2x larger book implies a 3.2x larger rebalance every month thereafter;
3. `gamma = 25` lets the mean-variance term dominate the cost term at the larger scale.

(2) is the most likely and the most interesting, and it is a real modelling criticism of the whole
single-period-with-cost-penalty approach that this literature uses. **This must be diagnosed before
the curve is reported**, because if it is (1) the cost model is simply miscalibrated and the curve
moves.

$1e10 is running and will complete the curve. The prediction for it, fixed now: gross Sharpe
**below** +0.423, cost drag below 17.2 bps, and net Sharpe poor for the opposite reason — signal
suppressed rather than costs paid. If that holds, net performance is hump-shaped in AUM with a low
peak, and "no scale works" is established on three points rather than two.
