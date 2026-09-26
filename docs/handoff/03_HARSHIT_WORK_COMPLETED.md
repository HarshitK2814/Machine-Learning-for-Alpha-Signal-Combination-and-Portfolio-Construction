# What Harshit has built — workstream B inventory

**22 September 2026.** What exists, what is verified, and what is not. Written so Absar and Maham can
build against real files rather than descriptions, and so a reviewer can see the state honestly.

**The standing caveat, stated once and applying to everything below: this all runs on a synthetic
panel we wrote ourselves. No real-data result exists.**

---

## 1. Test inventory

| Area | Tests |
|---|---|
| `tests/models` | 52 |
| `tests/tax` | 37 |
| `tests/validation` | 31 |
| `tests/portfolio` | 30 |
| `tests/theory` | 16 |
| `tests/adaptive` | 15 |
| `tests/contracts` | 15 |
| `tests/risk` | 6 |
| `tests/interpret` | 5 |
| `tests/synthetic` | 5 |
| **Total** | **231 collected** |

Last full green run: **231 collected, 231 passing, 0 failures** (22 September, run dir-by-dir with
`OMP/OPENBLAS/MKL_NUM_THREADS=1` to keep peak memory low). This includes the feasibility-based solver
selection and the updated `test_cap_feasibility.py` assertions, so nothing is unverified.

---

## 2. Models — `src/alphacomb/models/`

| Module | What it is | State |
|---|---|---|
| `cells.py`, `base.py` | The 16-cell factorial design, design-matrix construction, rank IC | Done, tested |
| `linear.py`, `nonlinear.py` | Linear and nonlinear rungs | Done, tested |
| `economic.py` | Economic-objective cells (E-cells) producing C10 weight proposals | Done, tested |
| `uncertainty.py` | Ensemble dispersion, validation-tuned κ shrinkage, nested at κ=0 | Done, tested |
| `stability.py` | Cross-split stability diagnostics | Done, tested |
| `benchmarks.py` | Internal reference models | Done, tested |
| `complexity.py` | Random Fourier features, virtue-of-complexity ladder | Done — **recalibrated after a silent failure**, see §7 |
| `conformal.py` | Split conformal with time-ordered calibration + adaptive rescaling | Done — **validated on the real panel**, see §7 |
| `attention.py` | Cross-sectional attention over stocks within a month | Done — **two defects fixed 22 Sep**, see §7 |

## 3. Portfolio — `src/alphacomb/portfolio/`

| Module | What it is |
|---|---|
| `optimizer.py` | Cost-aware mean-variance, contract C11. Dollar-neutral, gross ≤ 2, beta and industry neutrality, position and ADV participation caps. Two-stage solve: hard bounds first, breachable bounds only on infeasibility, with the returned solution **measured** against every bound rather than trusted on its status |
| `cost_terms.py` | The convex cost term and `trade_cost_numpy`, the reference implementation Absar's engine must match |
| `tax_terms.py` | Tax consequence of a trade, inside the objective. Affine in `w`, generates **no constraints** — that property is pinned by a test, because violating it caused a 60%-of-months failure |
| `alpha_scaling.py` | Grinold scaling (IC × σ × z) so cells are comparable |
| `robust.py` | Ellipsoidal (Goldfarb-Iyengar) and Wasserstein DRO uncertainty penalties; nested at radius 0 |

## 4. Tax — `src/alphacomb/tax/` (the distinctive contribution)

| Module | What it is |
|---|---|
| `lots.py` | Lot-level ledger. Exact §1222 twelve-month anniversaries (not month-fractions — a leap year broke this once), §1233 short-sale rule, bidirectional §1091 wash sales with basis adjustment and §1223(3) holding-period tacking, four lot-selection methods (FIFO/LIFO/HIFO/TAX_OPTIMAL) |
| `regimes.py` | Four investor regimes: tax-exempt, taxable US top bracket (40.8%/23.8%), §475(f) trader mark-to-market, offshore fund |
| `jurisdictions.py` | Nine jurisdictions across two independent architectural dimensions — the **holding-period wedge** (θ_S − θ_L) and **loss-relief breadth** (ring-fencing, carryforward life). Produces the 2×2 identification table |
| `backtest.py` | After-tax backtest in dollars with real NAV, splitting total return into price and dividend components, with vintage-tracked carryforward expiry |
| `overhang.py` | Deferral overhang: pre-liquidation vs mark-to-liquidation, trajectory, harvesting decomposition |

**Independent validation worth noting:** the ledger reproduced Sialm–Sosner without being tuned to —
realised short-term gains negative (−64 bps/yr), long-term positive (+190 bps/yr).

## 5. Everything else

| Module | What it is |
|---|---|
| `risk/structural.py`, `cache.py` | Structural factor risk model (C7). Verified point-in-time: rebuilding from a truncated panel reproduces it exactly |
| `adaptive/hedge.py`, `drift.py`, `meta.py` | Online expert aggregation (Hedge/EWA with Herbster-Warmuth fixed share), Page-Hinkley drift detection, and a **like-for-like** equal-weight-alpha benchmark |
| `validation/inference.py` | NW, Lo/Mertens Sharpe SEs, deflated Sharpe, PBO/CSCV, Romano-Wolf, Hansen SPA, BH, DM — **see `02_NEEDS_FROM_MAHAM.md` §1, this overlaps workstream C and the ownership needs settling** |
| `validation/preregistration.py` | Write-once pre-registration with fingerprint hashing, separating configuration count (the DSR N) from fit count |
| `validation/falsification.py` | Zero-predictability null, microstructure placebo, inflation gap |
| `theory/tax_model.py` | The one-period model: closed-form short-term share Φ(p,H), after-tax return R(p) = g(1−θ_L) − κp − g·Δ·Φ(p,H), channel decomposition, comparative static in the wedge |
| `contracts/` | C1–C13 frozen at v1.1.0, validator, path generation, split calendar, lockbox guard |

---

## 6. Substantive findings so far (all synthetic — none are paper claims)

| Finding | Status |
|---|---|
| The complexity × tax hypothesis is **rejected** — Spearman +1.000, wrong direction | Measured |
| Complexity **lengthens** holding periods: turnover −40%, long-term share +19 points | Measured |
| Tax-aware books accumulate 22–39% of NAV in embedded gain; tax-blind stay at ~3.6% | Measured |
| The loss carryforward **does not** cancel it — covers only 4–25%, leaving ~5.9% of NAV in unreported deferred tax | Measured; **reverses an earlier conclusion** that was an artefact of testing an unlevered tax-blind book |
| At the naive trial count (N=539) **nothing survives** deflation; with the pre-registered N=64 the hurdle falls to 0.465 | Measured |
| **Every nonlinear rung is dominated by plain linear ridge** (attention 0.0491, attention-ablated 0.0511, ridge 0.0562) | Measured — and this is a property of a near-linear synthetic DGP, **not** a claim about markets |
| USIPC mandates pre-liquidation reporting and the unrealised-gain percentage, but **neither the deferred tax nor the offsetting carryforward** — so the disclosure cannot distinguish a sheltered embedded gain from an unsheltered one | Verified against the primary 44-page standard |

The last row is the practitioner gap the paper is aimed at.

---

## 7. Silent failures found and fixed — the honest record

Eleven, and the pattern in them is the useful part. Full detail in
`docs/SILENT_OPTIMISER_FAILURE.md` and `docs/FRONTIER_VALIDATION.md`.

| # | Failure | Why it was invisible |
|---|---|---|
| 1 | Leap-year holding-period boundary classed a 12-month hold as long-term | Month-fraction arithmetic, 366/30.4375 = 12.02 |
| 2 | Page-Hinkley δ on the wrong branch — false alarms on stationary data by construction | Statistic grew linearly in T |
| 3 | Qualified-dividend **fraction** used as a boolean | Type coercion |
| 4 | Offshore regime netted away its own withholding | Wrong default flag |
| 5 | **Optimiser infeasibility death spiral** — 150/216 months `failed_hold`, **correlated with treatment** because it bites hardest in small illiquid names | Status checked, solution never measured |
| 6 | Manifest corruption from concurrent append | `to_csv(mode="a")` race |
| 7 | Adaptive benchmark not like-for-like — inverted the conclusion | Compared alpha-blend-then-optimise against mean of separately-optimised |
| 8 | Complexity ladder inverted: γ ≈350× too large, ridge grid 5–9 orders too small | IC *fell* in P and nobody checked the direction |
| 9 | Unbounded gain rate → −112,000%/yr | `gain/value` for a position down 99.99% |
| 10 | Tax term froze every position (3 attempts; the first two looked like fixes) | A constraint introduced to model an *objective* restricted the decision variable |
| 11 | **Solver selection chose infeasible books on every month** — SCS `optimal` with 139/827 names over their position cap, preferred over CLARABEL `optimal_inaccurate` with none | The two objectives agreed to five significant figures, so the objective was compared and the constraints never were |

**The pattern, which is worth a paragraph in the paper rather than a changelog entry: every one of
these was validated on a label rather than on output.** `test_attention_cell_fits_and_keeps_weights`
checked that a fit returns weights. `failed_hold` checked solver status. The September optimiser
repair checked solvability. The escalation rule checked the objective value. In each case the
question that actually mattered — *is the returned thing correct?* — was never asked until a function
existed to ask it.

---

## 8. Known open items on my side

1. ~~Verification of the last two changes~~ **closed 22 September**: 231 tests green including both.
2. ~~Impact of finding #11 on the synthetic results~~ **measured 22 September — immaterial.** A
   12-month walk on `cell_N-C-P-0` under both selection rules:

   | rule | solvers chosen | ann ret | Sharpe |
   |---|---|---|---|
   | status-first (as published) | CLARABEL 7, SCS 5 | 4.72% | 2.88 |
   | feasibility-first (fixed) | CLARABEL 8, SCS 4 | 4.74% | 2.65 |

   Annualised difference **−0.0149%** (~1.5 bps/yr); mean monthly difference −1.2e-5; worst single
   month 20 bps. **A footnote, not a re-run.** The infeasible books differed from the feasible ones
   in constraint satisfaction far more than in realised return, because the breaches sat in tiny
   illiquid positions contributing almost nothing to P&L. That is a more useful claim for the paper
   than either "no bug" or "results invalid", and it should be stated rather than omitted.

   Two caveats on that measurement, kept because they bound what it shows. The window is 12 months
   and one cell, so the Sharpe move (2.88 → 2.65) is noise at n=12 and nothing should be read into
   it. And SCS still wins 4 of 12 months, which is correct: the new rule rejects it only where its
   solution is *measurably* infeasible, so the choice changed in one or two months rather than all
   of them — which is itself why the return impact is small.
3. **Four falsification-audit fixes** outstanding (`docs/FALSIFICATION_AUDIT.md`), strict null among
   them.
4. **The theory model's paper-facing exposition** — the module exists, the paper section does not.
5. **Every tax rate carries `[verify]`** and needs checking against statute per sample period.
6. `docs/STATUS.md` is stale (says 130 tests).
