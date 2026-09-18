# Design v2: frontier methods, and the credibility layer top journals now require

Written 2026-09-19 after a targeted search of what has actually been accepted or circulated in
2025-2026. This document says what we add, what we deliberately refuse to add, and why each choice
helps rather than hurts the paper's chances at Quantitative Finance, JFQA, Management Science, RFS.

## 0. The rule that governs every addition

A method enters the paper only if it is a **level on one of the four design axes** (form,
conditioning, objective, uncertainty) or a **credibility instrument** referees now demand. Anything
that is neither is decoration: it inflates the trial count, weakens the deflated Sharpe ratio, and
invites the "kitchen sink" rejection. Every added level is pre-registered, logged in `trials.csv`,
and included in the multiple-testing correction.

## 1. What the 2025-2026 literature changed

| Finding | Source | What it does to our design |
|---|---|---|
| Friction-aware, **regime-conditioned** policy optimisation with costs in the reward, evaluated on regime x cost grids with bootstrap CIs and multiple-testing corrections | FR-LUX (Zhang 2025, arXiv 2510.02986) | **Closest new prior art for gap G2.** We must cite it, and differentiate: it proposes one RL method in a small asset space; we identify *which ingredient* creates net value in a ~150-signal stock cross-section. Its regime grid becomes a robustness parameterisation of our conditioning axis |
| Complexity pays only through **sparse discovery** in a rich feature space; dense ridgeless plateaus | The Virtue of Sparsity in Complexity (Afsharhajari & Li 2026, arXiv 2604.17166) | The form axis gains a complexity ladder with a dense arm (ridgeless RFF) and a sparse arm (basis pursuit), instead of a single "nonlinear" level |
| Complexity helps only when the factor eigenvalue spectrum is diffuse | APT or "AIPT"? (Kelly et al. 2025) | Adds a spectrum diagnostic that predicts *when* our complexity level should pay: a mechanism test, not a horse race |
| Adaptive specification search produces significant backtests under a no-predictability null; referees should expect a falsification audit | Spurious Predictability in Financial ML (2026, arXiv 2604.15531) | New **credibility layer**: zero-predictability synthetic null, microstructure placebo, multiplicity-adjusted inflation gap |
| Empirical fit systematically understates true predictability (limits-to-learning gap) | Chen, Kelly & Malamud (2025, arXiv 2512.12735) | We report our R2 and IC with the LLG caveat, and avoid interpreting small R2 as "no signal" |
| Decision-focused (SPO-style) learning inflates predictions and turnover | Wang & Hasuike (2026, arXiv 2605.01176) | Our economic-objective cells adopt their controls (output clipping, partial adjustment) and we *report* prediction inflation as a diagnostic, since it is exactly the mechanism our objective axis is testing |
| Conformal prediction gives distribution-free, finite-sample intervals for portfolio choice | Kato (2024/25, arXiv 2410.16333); Conformal Prediction for Reliable Stock Selections (PMLR 2025) | The uncertainty axis is upgraded from ensemble dispersion to conformal intervals, with ensemble dispersion kept as the comparison level |
| Transformers with cross-asset attention improve SDF estimation | Kelly, Kuznetsov, Malamud & Xu (2025, NBER w33351); Lai (2025, arXiv 2505.01575) | Cross-sectional attention becomes the top rung of the form ladder, since it is the current state of the art for *combining* information across stocks |

## 2. The upgraded design

The spine is unchanged: one signal library, one universe, one optimiser, one cost model, one
inference framework, and an attribution of net-of-cost value. What changes is that two axes become
**ladders** and the credibility layer becomes a first-class part of the paper.

### Axis A - functional form (was: linear vs nonlinear)

| Level | Method | Why it is here |
|---|---|---|
| A0 | Ridge on signals | The baseline nobody can dismiss |
| A1 | LightGBM / NN3 ensemble | The 2020-era standard (GKX) |
| A2 | **Ridgeless random Fourier features**, complexity c = P/T on a grid | Tests the virtue of complexity in *our* net-of-cost setting |
| A3 | **Sparse-in-complexity**: basis pursuit / lasso on the same RFF space | Tests the 2026 claim that complexity pays through sparsity |
| A4 | **Cross-sectional attention** (one encoder block over stocks within a month) | Current state of the art for cross-asset information sharing |

The factorial attribution still uses the binary contrast (linear vs nonlinear) for the headline
decomposition; A2-A4 enter as a pre-registered ladder inside the nonlinear arm, so the headline test
keeps its power while the paper still speaks to the complexity debate.

### Axis B - conditioning (was: static vs state-conditional)

Unchanged in structure; gains two robustness parameterisations: the FR-LUX 2x2
volatility-liquidity regime grid, and a gate restricted to two states for interpretability.

### Axis C - objective (was: prediction loss vs economic loss)

Economic cells gain the SPO-critique controls: output clipping, partial adjustment towards the
target (a Garleanu-Pedersen-style trading rate), and a reported **prediction-inflation diagnostic**
(the ratio of implied expected return to realised). A differentiable-optimiser variant
(cvxpylayers) is available but is *not* in the headline design: it changes the constraint handling
and would confound the objective comparison.

### Axis D - uncertainty (was: ensemble dispersion)

| Level | Method | Why |
|---|---|---|
| D0 | None | Nested at kappa = 0 |
| D1 | Ensemble dispersion shrinkage | What most ML papers do |
| D2 | **Split/adaptive conformal intervals** with per-month recalibration | Distribution-free coverage; current frontier; gives a *calibrated* quantity rather than an arbitrary spread |
| D3 | Conformal interval -> **robust optimisation budget** (ellipsoidal / Wasserstein DRO) | Connects uncertainty to the decision, which is the economically interesting claim |

### Credibility layer (new, and non-negotiable)

1. **Falsification audit.** Re-run the entire pipeline on (i) a zero-predictability synthetic panel
   (all planted coefficients set to zero), (ii) block-shuffled states, (iii) a microstructure
   placebo where signals are replaced by lagged noise with the same autocorrelation. Report the
   inflation gap between in-sample optimised evidence and disjoint walk-forward realisations,
   adjusted for effective multiplicity.
2. **Spectrum diagnostic.** Eigenvalue concentration of the signal-return covariance, and whether
   the complexity ladder pays where the AIPT logic says it should.
3. **Limits-to-learning caveat.** Report R2 and IC alongside the LLG argument, so small numbers are
   not misread as absence of signal.
4. Existing tools stay: deflated Sharpe, PBO, SPA/StepM/MCS, non-standard errors multiverse,
   lockbox, full trial logging.

## 3. What we deliberately do NOT add

| Tempting addition | Why it is excluded |
|---|---|
| Deep reinforcement learning portfolio agent | Sample-inefficient, hard to replicate, and FR-LUX already occupies that space. Our contribution is identification, not a new agent |
| Graph neural networks on supply-chain links | Requires licensed relationship data; point-in-time integrity is hard to defend; orthogonal to the question |
| LLM-generated signals | Training-data look-ahead is currently unresolvable for pre-cutoff periods; would contaminate a paper whose selling point is integrity. Reserve for a follow-up with a strict post-cutoff window |
| Diffusion models for return distributions | No accepted finance precedent yet; adds trials without touching the four axes |
| Every published ML architecture as a horse-race row | Exactly the behaviour that gets ML-finance papers rejected; each extra arm weakens the deflated Sharpe ratio of the winner |

## 4. What this buys us with referees

* The paper is no longer "another ML horse race": it answers *which ingredient* pays after costs,
  and it does so with 2026-current levels on each axis, so no referee can say the methods are dated.
* It engages directly with the live debates (complexity vs sparsity, decision-focused learning's
  turnover pathology, uncertainty calibration) instead of ignoring them.
* It pre-empts the three standard rejection routes: costs, snooping, and interpretability.
* The falsification audit is something most submissions still do not have.
