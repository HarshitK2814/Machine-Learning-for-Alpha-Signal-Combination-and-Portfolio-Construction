# The economic-loss arm extracts an order of magnitude less information than the prediction arm

**Date:** 2026-10-09, 02:45 IST
**Reproduce:** `python tools/verify_arm_information.py --country DEU --from-weights-index`
**Bears on:** the factorial's only significant main effect, and the withdrawn turnover gradient in
`docs/RESULTS_WEDGE_TEST.md` §5.

---

## 1. Why this had to be checked

The factorial's one significant main effect is the **economic** one, and it is negative: the
economic-loss cells lose to the prediction-loss cells by **0.0054 p.a. (t = −3.77)** in Germany and
**0.0063 p.a. (81.6% of the total effect)** in India. It replicates across two countries, which is
why it was the most robust-looking finding in the project.

But that is a statement about *objectives* only if both arms are competent implementations. If one
arm barely learns, the "main effect" measures an implementation gap wearing the label of a design
axis. Three symptoms made that worth testing:

1. The economic cells trade **3.3x more** than the prediction cells (India: turnover 0.0214 against
   0.0066), although their objective contains an explicit `- cost(w_t - w_{t-1})` term that exists
   precisely to make them trade less.
2. They have **negative gross Sharpe — before any cost is charged** (India: −0.272 against +0.534;
   all 8 E cells negative, all 8 P cells positive).
3. Their cost drag is **4x** higher (39.2 bps against 9.6 bps).

An objective that prices turnover, churns anyway, and earns negative gross alpha has more likely
failed to optimise than discovered something about economics.

## 2. The measurement

Rank correlation between each cell's stage-02 output and the realised next-month return, by month,
then averaged. A prediction cell emits a score; an economic cell emits a proposed weight. Either
way, a cell with skill should rank next month's winners above its losers. The statistic is
**scale-free**, so it is unaffected by the leverage problem in §4.

| | **Germany** mean IC | cells with IC t > 1.96 | **India** mean IC | cells with IC t > 1.96 |
|---|---|---|---|---|
| prediction-loss (P) | **+0.0757** | **8 of 8** (t = +8.6 … +10.4) | **+0.0368** | **8 of 8** (t = +2.8 … +5.4) |
| economic-loss (E) | +0.0072 | **2 of 8** | **−0.0061** | **0 of 8** |

Per cell, Germany:

```
L-C-E-0  E  -0.00890  t -0.92      L-C-P-0  P  +0.07086  t  +8.59
L-C-E-U  E  +0.00311  t +0.31      L-C-P-U  P  +0.07085  t  +8.84
L-S-E-0  E  +0.00041  t +0.05      L-S-P-0  P  +0.07619  t +10.15
L-S-E-U  E  +0.00545  t +0.60      L-S-P-U  P  +0.07726  t +10.40
N-C-E-0  E  +0.02094  t +3.18      N-C-P-0  P  +0.07558  t  +9.34
N-C-E-U  E  +0.02523  t +3.60      N-C-P-U  P  +0.08059  t  +9.76
N-S-E-0  E  +0.00289  t +0.39      N-S-P-0  P  +0.07709  t  +9.73
N-S-E-U  E  +0.00850  t +1.19      N-S-P-U  P  +0.07719  t  +8.98
```

**Stated precisely, and not more strongly than that.** In Germany the economic arm is **10.5x
weaker** than the prediction arm but not uniformly dead — the two nonlinear-conditional cells do
learn something (t = +3.18, +3.60). In India it carries **no information at all** (7 of 8 negative,
none significant). So the claim is *not* "the economic arm never learns"; it is:

> The economic-loss implementation extracts an order of magnitude less information from the same
> signals as the prediction-loss implementation, in both countries, and none at all in one of them.

## 3. What that does to the main effect

The economic main effect is therefore **not a clean test of prediction loss versus economic loss**.
It is dominated by a capability gap in the economic implementation. It cannot be reported as
"economic objectives underperform" — on this evidence the right statement is "our economic-policy
implementation underperforms", which is a much weaker and much less interesting claim.

It also removes the foundation of the withdrawn result in `RESULTS_WEDGE_TEST.md` §5: that turnover
gradient was driven entirely by the gap between the two arms' turnover clusters, and the
high-turnover cluster is this arm.

## 4. The most likely cause: a fixed gross budget that capacity makes infeasible

`EconomicPolicy._weights` normalises every proposal to **exactly** `gross`, which defaults to 2.0 to
match `configs/base.yaml: gross_max: 2.0`. But at $1bn AUM in these universes the ADV participation
cap binds long before the gross budget, so the attainable gross is about 0.1–0.23. Measured on
India's 1e9 run:

| arm | proposed gross | final gross after projection | vs P arm |
|---|---|---|---|
| economic (E) | **2.0000**, every month of every cell | 0.0972 | **1.74x** |
| prediction (P) | — (the optimiser chooses) | 0.0558 | 1.00x |

Two consequences, and the second is the serious one:

* **A 20.6x compression.** Whatever optimality the proposal had at gross 2.0 does not survive
  projection onto a feasible set 20x smaller.
* **The policy cannot represent the optimum.** The optimiser is free to choose its gross and
  chooses 0.056 because costs make a bigger book not worth it. The policy is *hard-coded* to 2.0
  and so can never learn that a small book is better. Its utility is evaluated at a leverage it
  will never run at, where the impact term `|dw|^1.5` — which is **not** scale-invariant — has a
  completely different weight relative to the return term than it does at gross 0.1. The module's
  own docstring claims both arms "face identical limits"; they do not.

A side effect: the E arm ends up at **1.74x the P arm's gross**, so the comparison is not even
leverage-matched. That is the "E-vs-P leverage confound" that was on the todo list as unmeasured;
it is now measured.

The sign convention was checked and is correct (`(-chunk_utility).backward()` maximises utility),
so this is not a flipped objective.

## 5. What to do about it — open, for Maham to rule on

1. **Minimal fix:** pass the attainable gross (or the realised optimiser gross) into
   `EconomicPolicy` so it trains at the scale it will be run at. One-line plumbing plus a stage-02
   re-run of the 8 E cells per country. Cheap enough to do tonight for India.
2. **Correct fix:** put the projection inside the training loop so the policy optimises
   post-projection utility, or make the gross budget learnable. Larger change.
3. **Report-as-is with the arm flagged** not fit for purpose, lean the paper on the prediction arm
   plus the cross-country tax contrast, and present §2 as a methodological finding in its own right
   — that a parametric-portfolio-policy implementation at a fixed gross budget fails when capacity
   rather than risk is the binding constraint. That is arguably a publishable observation about
   end-to-end portfolio learning at realistic scale.

`docs/handoff/19_FOR_MAHAM_...` §7 asks her to choose between debugging and flagging. I can argue
either and would rather not pick the one that flatters the results.

## 6. A note on the diagnostic itself

The first version of `tools/verify_arm_information.py` announced that **both** Germany arms had
failed to learn — on **zero** observations. It had resolved artefacts from a stale 8 October log
whose files no longer exist on disk, every merge came back empty, and it read an empty mean as a
negative finding. It now refuses to judge any cell with no overlapping months, names them, and
exits non-zero if every cell is empty.

It also has a `--from-weights-index` route, used for the Germany numbers above, which resolves
artefacts through the portfolio manifest's `source_artefact` for the pinned run. That names exactly
the stage-02 outputs the published portfolios consumed, rather than whatever a log happened to
write — the same mtime hazard that
`docs/AMENDMENT_001B_UNIVERSE_BREADTH_CAP.md` and the weights index exist to close, and which
caught this diagnostic too before it was fixed.
