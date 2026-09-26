# Frontier component validation — 22 September 2026

`PUBLICATION_READINESS_AUDIT.md` flagged three design-v2 components as **built, never validated
against a benchmark**: the attention cell, conformal prediction, and the robust optimiser. The
complexity ladder had been silently broken for weeks while its tests passed, so the standing
instruction was to assume these were too until shown otherwise. This is the result of checking.

The common defect in the old tests is that they assert the component **ran**, not that its output
was **usable**. `test_attention_cell_fits_and_keeps_weights` is the clearest case: it checks that a
fit produces weights. The complexity ladder also produced predictions the whole time it was broken.

---

## 1. Attention cell — works, but is dominated, and had two real defects

Validation rank IC on `N-S-P-0`, 478 train months, 170 features, one split (2018):

| Variant | train IC | val IC |
|---|---|---|
| as shipped | 0.0792 | 0.0391 |
| standardised target | 0.0689 | **0.0491** |
| standardised target, lr 3e-4, 60 epochs | 0.0619 | 0.0419 |
| **attention block ablated** (same net, no cross-stock mixing) | 0.0609 | **0.0511** |
| *linear ridge on 13 theme composites* | — | **0.0562** |

Three things follow, and only the first two are defects.

**(a) The target was not standardised.** Monthly returns have sd ≈ 0.13 while the head, fed by a
`LayerNorm`, emits O(1) at initialisation. Under MSE the early gradients are spent shrinking that
scale mismatch rather than learning the signal, and early stopping fires before it recovers.
Training on a unit target and rescaling at predict time is worth **+26% of the validation IC**
(0.0391 → 0.0491) and costs nothing. Fixed in `attention.py`; rank IC is scale-free so this changes
the fit, not the metric.

**(b) `predict` subsampled the cross-section.** `max_stocks=1000` exists to bound the O(n²)
attention cost during *training*. It was also applied on the prediction path, where every dropped
stock is silently returned as NaN. Our synthetic universe is ~666 names so the cap never binds —
which is precisely why this was invisible. **On a real CRSP universe of ~3000 names it would have
discarded two thirds of every cross-section.** Since the international real-data panels are the next
milestone, this would have fired on first contact with real data. Fixed, with a regression test that
uses a universe larger than the cap.

**(c) Attention does not earn its place, and neither does anything nonlinear.** Ablating the
self-attention block — same depth, same parameters, no cross-stock mixing — *improves* validation IC
from 0.0491 to 0.0511. And plain linear ridge on 13 theme composites beats every variant at 0.0562.

**(c) is not a bug and must not be reported as one.** It is the same result the complexity ladder
gave after recalibration, and it is a statement about **our synthetic data generator**, whose
conditional mean is close to linear by construction. It is not evidence about real markets. What it
does establish is that the nonlinear frontier cannot be evaluated at all on synthetic data — every
rung is dominated by the linear benchmark because the DGP has nothing for them to find. This is an
additional, independent reason the real-data panels are the binding blocker.

## 2. Conformal prediction — passes, with an honest conditional-coverage caveat

Run on the actual 216-month prediction panel (139,644 rows, 2003–2020), not a synthetic fixture.
The existing unit test draws i.i.d. data, which is the exact case the guarantee is proven for, so
passing it showed nothing. Financial panels are not exchangeable.

| Nominal | Adaptive | Realised | Worst year | Coverage sd |
|---|---|---|---|---|
| 80% | off / **on** | 79.9% / **80.1%** | 63.8% / **65.9%** | 0.082 / **0.080** |
| 90% | off / **on** | 89.6% / **90.0%** | 76.4% / **78.3%** | 0.065 / **0.062** |
| 95% | off / **on** | 94.5% / **94.9%** | 85.1% / **86.3%** | 0.047 / **0.044** |

**Marginal coverage holds at every level**, and the adaptive rescaling measurably helps: it moves
realised coverage onto the nominal value and lowers the dispersion at all three levels. This is the
first component of the three that does what it claims.

**The caveat the paper must state.** Worst-year coverage is 63.8% against a nominal 80%. Marginal
coverage holds; **conditional coverage fails in crisis years**, and adaptive rescaling narrows the
gap without closing it. This is the known limitation of split conformal under distribution shift and
a referee will ask about it, so it is reported rather than buried — and it is the honest reason the
intervals should not be described as a "guarantee" in the text without qualification.

## 3. Robust optimiser — a parallel copy, and an incomplete fix underneath it

Two separate defects, and the second is the more serious of the two.

### 3.1 The divergence

`portfolio/robust.py` implemented the same constrained problem as `portfolio/optimizer.py`
**separately**. When the silent-infeasibility bug was repaired on 21 September, the fix landed only
in `optimizer.py`; `construct_robust` kept the unrelaxed constraint set and, separately, never got
the solver-escalation logic either.

**No test caught it** because `construct_robust` is called from tests only and *every* call passes
`w_prev=None`. A fresh book is the single case in which a drifted position cannot make the
constraints conflict — the tests exercised the one configuration where the bug is unreachable.

**How much damage: none realised.** A 36-month walk on `cell_N-C-P-0` through the *unfixed* robust
path produced **zero** failures — the book runs at gross 0.63 against a budget of 2.0 and never
drifts far enough to trap itself. The missing relaxations were latent risk, not a live failure, and
the earlier draft of this document overstated them. What the walk *did* show is the escalation gap:
32 optimal / 4 `optimal_inaccurate` against 36 / 0 for `construct`.

### 3.2 The 21 September fix was itself incomplete — the important finding

Probing feasibility directly on a book drifted to 1× `weight_abs_max` and beyond:

| Drift | pre-21 Sep | 21 Sep fix | now |
|---|---|---|---|
| 0× | optimal | optimal | optimal |
| 1× | infeasible | **infeasible** | optimal |
| 4× | infeasible | **infeasible** | optimal |
| 10× | infeasible | **infeasible** | optimal |

The September repair relaxed the position, gross and net bounds to each one's *individually
reachable* floor, and left `beta` and the industry exposures untouched. Two things were wrong:

1. **The exposure bounds are the same trap.** `|g'w| ≤ bound` is unreachable whenever the book has
   already drifted outside it, because `|w − prev| ≤ adv_cap` pins `w` near `prev`.
2. **Individually-reachable floors are not jointly attainable.** Minimising `‖w‖₁` and neutralising
   `β'w` call for different trades, so relaxing each bound to its own floor still leaves an empty
   intersection. Relaxing three of five bounds that way simply *moved* the infeasibility into beta —
   which is exactly why the first repair looked complete and passed its tests.

**Four attempts, three of which looked correct.** Recorded in full because the pattern in the
failures is more useful than the final answer.

| # | Approach | Feasible when drifted? | Bounds intact? | Breach visible? |
|---|---|---|---|---|
| 1 | 21 Sep: each bound to its own reachable floor | **no** — moved into beta | yes | n/a |
| 2 | anchor every bound at `prev` | yes | **no** — neutrality stopped binding | n/a |
| 3 | soft bounds everywhere | yes | yes | **no** — status trusted |
| 4 | hard, with a verified soft fallback | yes | yes | yes |

**Attempt 2** does guarantee feasibility — `w = prev` satisfies everything at once. But it silently
loosens the book: `net_slack` becomes `|sum prev|` instead of zero, so dollar-neutrality stops
binding after any drift at all. Buying feasibility by weakening a property the paper claims converts
a loud failure into a quiet misspecification, which is strictly worse.

**Attempt 3** is the one worth dwelling on, because it was *this repair that introduced the worst
failure found in the whole audit*. The design was right — hard trade and position caps forming a
non-empty box, with gross, neutrality and the factor exposures made breachable at a price — but the
fallback was triggered on `status == "failed"`. On a drifted book the hard set is genuinely empty
and **SCS does not reliably report `infeasible`**: it returns `optimal_inaccurate` with a solution
breaching the gross budget by two orders of magnitude. The fallback never fired, and the optimiser
returned a book at **gross 769.9 against a budget of 2.0 with zero violations reported**. The bug it
replaced at least failed loudly. This one returns a confident, well-formed, catastrophically wrong
book — and it would have propagated into every downstream table without a single warning.

**Attempt 4**, which is what ships:

* **stage 1 — hard bounds, no slack variables.** Numerically identical to the formulation every
  existing result was computed with, so nothing published can move.
* **verification, not trust.** `bound_breach()` measures the returned solution against every
  configured bound. Stage 2 fires on `status == "failed"` **or** a relative breach above
  `BREACH_TOL = 1e-4`.
* **stage 2 — breachable bounds.** Gross, dollar-neutrality and every factor exposure carry a slack
  priced at `violation_penalty = 1e4` against objective terms of order 1e-3. The bound is breached
  by the least amount available and **reported in `diagnostics["violated"]`**.

The breach measure is **relative to each bound**, not absolute, because the bounds span six orders
of magnitude: `adv_cap` floors at 1e-6 while `gross_max` is 2. An absolute tolerance tight enough to
catch a real gross breach treats ordinary conic residue on a 1e-6 trade cap as a violation — which
sent every *undrifted* month down the soft path and cost it a clean `optimal`. That was caught by
noticing the fresh book's gross had moved from 0.389 to 0.384.

The invariant the tests now pin is not "the solver was happy". It is: **whatever comes back, any
bound it breaches is in the diagnostics.** A solution is measured, never taken on the strength of a
label — which is the same lesson as `test_attention_cell_fits_and_keeps_weights`, where this audit
started.

The constraint set and the solver escalation now each live once, in `optimizer.book_constraints` and
`optimizer.solve_escalating`, and both paths call them.

## What this changes

Nothing that has been published moves. Two of the three components had real defects and one
(attention `predict`) would have failed on first contact with real international data. The honest
summary for the paper is that **the nonlinear/robust frontier remains unvalidated as a source of
economic value**, because our synthetic DGP cannot discriminate between its rungs — not because the
code is broken. That claim can only be tested on the real panels.

**Method note.** The first measurement in this audit put the attention cell at 0.0125 val IC. That
was taken on a 20,000-row training subsample and is not representative; on the full training set the
shipped cell gets 0.0391. The subsample was mine, not the model's. Recorded because the audit exists
to stop exactly this kind of error from reaching a table.

---

## 5. Addendum, 22 September evening — the solver-selection finding quantified

Found while chasing why an undrifted book kept falling onto the soft path: `solve_escalating`
preferred the first solver reporting `optimal` over one reporting `optimal_inaccurate`, justified by
the two objectives agreeing to five significant figures. They do. The solutions do not — SCS returned
`optimal` with 139 of 827 names over their position cap (worst 3.54x) while CLARABEL returned
`optimal_inaccurate` with none. The objective had been compared; the constraints never were. Selection
is now made on measured feasibility with the status only breaking ties.

**This is the only finding in the audit that reached results already in the repository**, so it was
measured rather than assumed. A 12-month walk on `cell_N-C-P-0` under both rules:

| rule | solvers chosen | ann ret | Sharpe |
|---|---|---|---|
| status-first (as published) | CLARABEL 7, SCS 5 | 4.72% | 2.88 |
| feasibility-first (fixed) | CLARABEL 8, SCS 4 | 4.74% | 2.65 |

Annualised difference **−0.0149%**, mean monthly −1.2e-5, worst month 20 bps. The breaches sat in
tiny illiquid positions contributing almost nothing to P&L, so the books differed in constraint
satisfaction far more than in return. **A footnote, not a re-run** — and worth stating in the paper,
because "real bug, immaterial to the point estimates" is a stronger and more honest claim than
either alternative.

Bounds on that conclusion: 12 months and one cell, so the Sharpe move is noise at n=12. SCS still
wins 4 of 12 months, correctly — the new rule rejects it only where its solution is measurably
infeasible. A separate diagnostic in the same run compared `|w|` against `pos_cap` *without* the
lawful per-name relaxation and therefore counted drifted positions as breaches; that column was
discarded rather than reported.

Full suite after all four audit fixes: **231 tests, 231 passing.**
