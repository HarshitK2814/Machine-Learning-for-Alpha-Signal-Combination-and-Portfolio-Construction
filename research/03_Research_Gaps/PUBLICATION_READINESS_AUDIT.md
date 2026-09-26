# Publication readiness audit

**Date:** 20 September 2026. **Verdict: NOT publishable at a top journal, and not close.**

This document exists to be uncomfortable. It is written against the actual standard - roughly 85%
of submissions to JF, JFE and RFS are rejected, and about 40% are desk-rejected by an editor without
reaching a referee - rather than against what we would like to be true.

The single most-cited desk-rejection criterion for an empirical paper is this: **a reader of the
first five pages should be able to state, in one sentence, why the estimates can be interpreted
causally.** We currently cannot pass that test. Everything below follows from it.

---

## 1. The blockers, in severity order

| # | Blocker | Severity | Fixable by the code workstream? |
|---|---|---|---|
| 1 | **No real data.** Only `data/synthetic` and `data/null` exist | **Fatal** | No - blocked on contracts C1-C6 |
| 2 | **No statistical inference** on any reported number | **Fatal** | **Yes - done, see section 3** |
| 3 | **No identification argument** in the headline claim | **Fatal** | Partly - by reframing |
| 4 | **Contribution is contested on four fronts** | Severe | Partly |
| 5 | **No economic mechanism or theory** | Severe | No - needs an author decision |
| 6 | Dead components still in the design | Moderate | Yes |

### 1.1 No real data

Every number produced in this project comes from a synthetic generator whose data-generating process
we wrote. The models recover effects we planted. **No top-three finance journal publishes an
empirical asset-pricing paper on simulated data.** Simulation appears in these journals only as a
supplement to real evidence, or in a theory paper where the model is the contribution.

This is not a weakness to be argued around. Until C1-C6 arrive, there is no paper.

What the synthetic work *is* worth: it proves the pipeline runs end to end, and it has already
caught four bugs that would each have produced a plausible, publishable-looking, wrong number. That
is genuine value - but it is infrastructure value, not evidence.

### 1.2 No statistical inference

Until today, every performance figure in this repository was a bare point estimate. No standard
errors, no multiple-testing adjustment, no deflated Sharpe ratio, no probability of backtest
overfitting. We searched over hundreds of specifications and reported the best.

This field is unusually explicit about the standard, because it was burned: Harvey, Liu and Zhu's
t > 3.0 hurdle for new factors; Bailey and Lopez de Prado on deflation and PBO; White's reality
check and Hansen's SPA; Romano and Wolf's stepwise method. A machine-learning paper reporting
Sharpe ratios without any of it is rejected on that ground alone, and correctly so.

**Status: fixed today.** See section 3.

### 1.3 No identification argument

Our current claim is a *decomposition*: how much of net-of-cost value comes from nonlinearity,
conditioning, objective and uncertainty. That is descriptive. It answers "how much" but not "why,
and how do you know it is not something else".

A referee will ask: the four ingredients are correlated with each other and with turnover,
liquidity, and holding period. What identifies the contribution of each?

**We have an answer and it is not in the headline.** The cross-country tax-architecture design
(`03_Research_Gaps/GAP_The_Tax_Wedge_in_Complexity.md`, section 3b) is a genuine identification
strategy with a dose-response ordering and two placebos written into law. It is currently framed as
an extension. **It should be the paper.**

### 1.4 Contested contribution

From the prior-art tracker (42 rows), four papers occupy adjacent ground:

* **Huang (2019)** owns "taxes matter more than trading costs for an ML strategy" - our premise.
* **Pishehvar (2026)** owns lot-level tax machinery inside an ML portfolio system, patent pending.
* **Remlinger et al. (2023)** owns online aggregation over ML models for long/short - our adaptive
  layer, which is now a method we cite rather than a contribution.
* **Krasner & Sosner (2024)** and **Israel & Moskowitz (2012)** own the value-to-momentum tax tilt.

None of them does *cross-country identification of which friction channel binds*. That is the only
uncontested ground we hold.

### 1.5 No economic mechanism

Top journals want a reason, not just a measurement. Why should the holding-period channel matter
more than the turnover channel? A one-period model of a taxable investor facing a realisation-based
capital-gains tax with a holding-period boundary would give a testable comparative static - and
would convert the paper from "we measured this" to "theory predicts this and we test it".

Constantinides (1983, 1984) and Dammon, Spatt & Zhang (2001) supply the machinery. Nobody has taken
it to an ML design-choice setting. **This is an author decision, not a coding task.**

### 1.6 Dead components

* **Adaptive layer** - scored -0.003 against a fixed 1/N blend. Demote to an appendix.
* **Complexity x tax wedge** - rejected, Spearman +1.000 against the prediction. Delete from the
  design; keep the finding that complexity *lengthens* holding periods, which is the interesting
  residue.
* ~~**Attention rung, conformal, robust optimisation** - built, never validated against a
  benchmark.~~ **Done 22 September**, see `alphacomb/docs/FRONTIER_VALIDATION.md`. The suspicion was
  justified: two of the three had real defects.
  * *Attention* - target was never standardised (worth +26% of its validation IC), and `predict`
    subsampled the cross-section, which on a real ~3000-name CRSP universe would have returned two
    thirds of every month as NaN. Invisible here only because our synthetic universe is ~666 names.
  * *Conformal* - **passes**. Marginal coverage holds at 80/90/95% on the real 216-month panel and
    adaptive rescaling measurably helps. Conditional coverage does not: worst-year 63.8% against a
    nominal 80%, which the paper must state rather than call the intervals a guarantee.
  * *Robust optimiser* - a parallel copy of `construct` that never received the 21 September
    feasibility fix or the solver escalation. No test caught it because every test passes
    `w_prev=None`, the one case where the constraints cannot conflict. Empirically it never failed
    (36-month walk: zero failures), so this was latent risk rather than a live failure.
  * **The 21 September feasibility fix was itself incomplete**, which is the finding that matters.
    It relaxed three of five bounds to each one's *individually reachable* floor and left `beta` and
    the industry exposures alone. Those floors are not jointly attainable, so a drifted book was
    still infeasible - the symptom had merely moved into beta. Both paths now anchor every bound at
    its value at `prev`, which makes `w = prev` feasible by construction and the empty feasible set
    unreachable. Verified optimal at 1x, 4x and 10x `weight_abs_max` drift where the September
    version was infeasible at all three. Constraint set and escalation now shared via
    `optimizer.book_constraints` / `optimizer.solve_escalating`. Nothing published used either path.
  * The substantive residue: **every nonlinear rung is dominated by linear ridge on our synthetic
    data** (attention 0.0491, attention-ablated 0.0511, ridge 0.0562). That is a property of a DGP
    whose conditional mean is near-linear by construction, not a finding about markets - and it is
    an independent reason the frontier claim cannot be settled without the real panels.

---

## 2. Where a referee will attack, and what we say

| Objection | Our answer today | Good enough? |
|---|---|---|
| "This is simulated data." | Nothing. | **No. Fatal until C1-C6.** |
| "You searched hundreds of specs and showed the winner." | Trial log + deflated Sharpe + PBO + Romano-Wolf, all computed on the real trial count | **Yes, as of today** |
| "What identifies the effect?" | Cross-country tax architecture: dose-response US > India > flat-rate, with Germany/Japan as placebos written into law | **Yes, if it becomes the headline** |
| "Isn't this just turnover?" | Turnover spans 1.09x while tax share spans 1.71x; Spearman -1.000 with long-term share | **Strong, needs real data** |
| "Sialm-Sosner / Krasner-Sosner did this." | They analyse given factor portfolios; we vary the ML design and identify the channel across tax architectures | **Adequate** |
| "Your tax rates are wrong." | Every rate flagged `[verify]`, four investor regimes, nine jurisdictions, sensitivity by construction | **Adequate** |
| "Why should I believe your optimiser?" | Stale-portfolio guard, held-share reported per strategy, falsification audit, 4 documented silent failures | **Strong - this is a differentiator** |
| "Where is the economics?" | Nothing. | **No. Needs a model.** |
| "Does it survive out of sample?" | Lockbox 2021-2025 frozen and gated | **Yes, if genuinely untouched** |

---

## 3. What was fixed today

**`alphacomb.validation.inference`** - the inference layer, 20 tests.

* `newey_west_se` - autocorrelation- and heteroskedasticity-robust standard errors.
* `sharpe_se`, `sharpe_test` - Lo (2002) autocorrelation correction plus Mertens/Christie
  higher-moment correction. Reports whether the Harvey-Liu-Zhu t > 3 hurdle is met.
* `deflated_sharpe` - Bailey & Lopez de Prado. Takes the **real** trial count from
  `outputs/trials.csv`, not the count we would like to report.
* `pbo_cscv` - probability of backtest overfitting by combinatorially symmetric cross-validation.
  Tests the *selection procedure*, which is what a design-grid paper needs.
* `romano_wolf` - stepwise familywise error control with a stationary bootstrap.
* `benjamini_hochberg` - FDR control for screening, documented as **not** interchangeable with
  Romano-Wolf.
* `hansen_spa` - superior predictive ability with Hansen's recentring, so that deliberately weak
  cells in the factorial grid cannot make the winner look significant.
* `diebold_mariano` - equal predictive accuracy.
* `inference_report` - everything in one call.

The tests are adversarial rather than confirmatory: PBO must be high on pure noise and low when a
genuine winner exists; Romano-Wolf must reject at most one of twenty noise series; the deflated
Sharpe must fall as the search grows; a skewed fat-tailed series must receive a *wider* standard
error than a Gaussian one.

### 3.1 What the inference layer said the moment it was run

Run against the project's own 216-month after-tax results, taxable US top bracket:

| Strategy | Sharpe | t | HLZ t>3 | Deflated SR prob | Survives |
|---|---|---|---|---|---|
| N-C-P-0 | 0.695 | 2.47 | no | 0.447 | **no** |
| N-S-P-0 | 0.659 | 2.99 | no | 0.389 | **no** |
| L-S-E-0 | 0.571 | 2.05 | no | 0.262 | **no** |
| L-S-E-0_aftertax | 0.505 | 2.10 | no | 0.178 | **no** |
| L-S-P-0 | 0.351 | 1.67 | no | 0.060 | **no** |

**Real trial count: 539. Expected maximum Sharpe from a 539-trial search under a no-skill null:
0.727. Our best result: 0.695.**

**Every reported Sharpe sits below what pure specification search delivers by chance. Nothing
survives deflation. Nothing meets the t > 3 hurdle.** Romano-Wolf rejects four of five, but it tests
whether the mean is non-zero, not whether the result beats the search - it does not see the 539
trials. PBO is 0.086, which is genuinely reassuring, but computed on five strategies rather than the
full grid.

This is on **synthetic data where we planted the effects ourselves**. Failing deflation where the
signal is known to exist is a serious warning about real data.

Yesterday these numbers read "after-tax Sharpe 0.69, the nonlinear cells win". A referee would have
run this calculation in ten minutes and desk-rejected the paper. We would not have known.

**One caveat that runs in our favour, and the reason it is not a licence.** 539 is the *global*
trial log - every configuration ever fitted in this repository, including complexity sweeps and
null-data runs. Bailey and Lopez de Prado's N is the number of trials used to select *the reported
strategy*, which for an ex-ante factorial design is smaller. But shrinking N after seeing the
results is precisely the move that makes the statistic meaningless. The fix is not to argue the
count down; it is to **fix the grid in advance so a small count is a fact rather than a claim**.

### 3.2 The fix: pre-registration

`alphacomb.validation.preregistration`, 10 tests. Write the plan - cells, grid, selection rule,
primary outcome - before the confirmatory run. The planned trial count is **computed from the grid,
never asserted**. The plan is hashed and can be written only once; editing a frozen plan raises on
load. `prereg_audit` compares the plan against `outputs/trials.csv` afterwards and, critically,
**`n_for_deflation` takes the larger of planned and actual**, so a run that fitted more than it
planned cannot quietly use the smaller number.

A test pins exactly that: plan 12, fit 15, and the deflation count must be 15.

---

## 4. The recommended reframing

**Current framing** (descriptive, no identification, contested):

> We decompose the net-of-cost value of ML signal combination into nonlinearity, conditioning,
> objective and uncertainty.

**Recommended framing** (identified, uncontested, uses what we built):

> Machine-learning portfolio research controls frictions by penalising turnover. We show that for a
> taxable investor the binding friction is not turnover but **holding-period composition**, and we
> identify this using cross-country variation in tax architecture: the penalty is ordered by each
> country's holding-period wedge (US 17 points > India 7.5 > flat-rate countries 0) and not by its
> transaction tax, and it vanishes in Germany and Japan where no holding-period boundary exists in
> law.

Why this clears the bar:
1. **One-sentence causal statement** - the placebo countries are the identification.
2. **Uncontested** - nobody has varied tax architecture; "Virtue of Complexity Everywhere" spans six
   asset classes and zero tax regimes.
3. **Uses what exists** - nine jurisdictions, lot-level ledger, factorial grid, inference layer.
4. **Survives being scooped** on any single method, because the claim is about a channel.
5. **Has a policy reading** - transaction taxes and capital-gains architecture have different
   effects on what quantitative strategies are viable. That widens the audience beyond asset
   pricing, which matters for a general-interest journal.

---

## 5. Honest probability assessment

| Target | Probability as things stand | With real data + the reframing + a model |
|---|---|---|
| JF / JFE / RFS | **~0%** | 10-15% |
| JFQA / Management Science / RAPS | ~0% | 25-35% |
| Journal of Financial Econometrics / RF | ~0% | 35-45% |
| Journal of Banking & Finance / JEF | ~0% | 55-70% |
| Quantitative Finance / JFDS / FAJ | ~2% | 70-85% |

These are judgements, not measurements. The pattern is what matters: **no realistic target is
reachable without real data**, and the gap between the top row and the bottom row is mostly
identification and economics, not empirics.

## 6. Critical path

0. **Pre-register the confirmatory grid before the real-data run.** Non-negotiable, and it has to
   happen *before* step 1 produces anything, or the trial count is contaminated from the first fit.
   Nothing we have currently survives deflation at N = 539.
1. **Real data (C1-C6).** Nothing else counts until this lands. Escalate.
2. **Reframe around the cross-country identification.** Rewrite the claim; demote the factorial
   decomposition to the mechanism section.
3. **Write the one-period model.** A taxable investor, realisation-based tax, holding-period
   boundary, and a comparative static in the wedge. This is what converts measurement into economics.
4. **Run the inference layer on everything** and report it whether or not it is flattering.
5. ~~**Validate the remaining frontier rungs**~~ **done 22 September**
   (`alphacomb/docs/FRONTIER_VALIDATION.md`): two of three had defects, all fixed, with regression
   tests that fail on the old behaviour. No published result moves.
6. **Verify every tax rate against statute** for the sample period.
