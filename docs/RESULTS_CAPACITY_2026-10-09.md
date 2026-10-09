# Results: the participation constraint, not the model, determines the portfolio

**Date:** 2026-10-09
**Panels:** Germany and India, promoted international panel, frozen window 2009-01-01..2019-12-31
(132 months; India 131, one month lost to `too_few_assets`). Japan running.
**Reproduce:** commands in §8.

> This is the ordered, referee-facing version. `docs/CANDIDATE_REFRAMING_CAPACITY.md` is the
> chronological record of how it was arrived at, including three results that died and two
> predictions of mine that were wrong. Both should be kept.

---

## 1. The finding in one paragraph

Machine-learning alpha combination produces **strong, highly significant cross-sectional signal**
in these markets. At institutional scale that signal **does not reach the portfolio**, because the
ADV participation constraint binds on essentially every position. Relaxing the constraint does
**not** fix it: the constraint is simultaneously suppressing signal *and* pinning the book against
turnover, and in this sample the turnover it prevents is worth more than the alpha it blocks. So
across two orders of magnitude of AUM there is no scale at which the design choices this literature
debates produce positive net performance, and relaxing the binding friction makes performance
worse rather than better.

## 2. The signal is real

Rank IC of each prediction-loss cell's scores against realised next-month returns, resolved through
each country's own artefacts (`tools/verify_arm_information.py`):

| | mean IC | range | t-statistics | cells significant |
|---|---|---|---|---|
| **Germany** | **+0.0757** | +0.0709 … +0.0806 | **+8.6 … +10.4** | **8 of 8** |
| **India** | **+0.0368** | +0.0227 … +0.0530 | **+2.8 … +5.4** | **8 of 8** |

By the standard the signal-level literature reports, these are publishable ICs with large
t-statistics in every cell of the design.

## 3. The portfolio does not deliver it

Same cells, same months, after the frozen constraint set:

* **0 of 21** strategies survive deflation at the pre-registered N = 64 (hurdle 0.717)
* **Hansen SPA against equal-weight: p = 0.70** — the family is indistinguishable from `BASE-EW`
* **PBO 0.432** with comparators included

IC t-statistics above +10 coexisting with nothing surviving multiple-testing adjustment **is the
result**. §4 and §5 say why.

## 4. The mechanism: capacity binds on essentially every name

`tools/exp_book_characteristics.py`, pre-registered `adv_participation_max = 0.05`,
`weight_abs_max = 0.01`, `gross_max = 2.0`, AUM $1bn:

| | capacity ceiling | **share of names ADV-capped** | realised gross (P / E) | names held / eligible | median ADV |
|---|---|---|---|---|---|
| **Germany** | 0.189 – 0.233 | **96.8% – 97.6%** | 0.132 / 0.178 | 298–305 / ~253 | $0.63–1.69mn |
| **India** | 0.113 – 0.148 | **99.5% – 100.0%** | 0.056 / 0.097 | 330–335 / ~341 | $0.42–1.49mn |

* Attainable gross is **6–23% of the budget**; India can be at most **11.3% invested**. The risk
  budget never binds in any month.
* The book holds **nearly the entire eligible universe** — the optimiser is not choosing *which*
  names, it is being told *how much* of each by ADV.
* The mechanism is scale against depth: $1bn against a median ADV under $2mn.

Corroborated two further ways, independent of any performance number:

**On the cross-section of weights** (`tools/exp_capacity_dose_response.py`) — the book is
progressively taken over by the constraint as size rises:

| AUM | corr(\|w\|, ADV cap) | corr(w, alpha), signed | share pinned at cap |
|---|---|---|---|
| $1e8 | +0.555 | **+0.497** | 0.519 |
| $1e9 | **+0.854** | +0.321 | 0.670 |

**On the optimiser's own conditioning** — the feasible set collapses until the QP is degenerate:

| AUM | months flagged `optimal_inaccurate` |
|---|---|
| $1e8 | **3.8%** |
| $1e9 | **31.1%** |
| $1e10 | **99.2%** (prediction cells; economic cells solve, being projections only) |

## 5. The dose-response, at matched leverage

Net Sharpe is **not** leverage-neutral: impact cost scales as `gross^1.5` while volatility scales
as `gross`, so `net Sharpe = (a−b)/v − (d/v)·gross^0.5` falls with book size for mechanical reasons.
Arms at different realised gross are therefore not comparable, and **post-hoc rescaling cannot fix
it** — the frozen non-tradeable sleeve is endogenous to the whole book (§7). The comparison must be
made by **re-optimising** at a common gross.

$1e8 capacity (ADV cap 10x looser), re-optimised with gross capped at **0.130**, the level the
$1e9 arm chose for itself. Cap bound in all 132 months; zero held months.

| prediction arm, 8 cells, **both at gross ≈ 0.13** | $1e9 capacity | $1e8 capacity | ratio |
|---|---|---|---|
| **gross** Sharpe | +0.4227 | **+0.6167** | **1.46x** |
| turnover | 0.0135 | **0.0258** | **1.91x** |
| cost drag | 17.21 bps | **59.59 bps** | **3.46x** |
| **net** Sharpe | **+0.1282** | **−0.0250** | worse |
| best single cell, net | +0.3302 | +0.2678 | worse |

**Capacity was doing two things at once:**

1. it **suppresses signal** — at matched leverage, gross Sharpe is **46% lower** when it binds; and
2. it **pins the book** — with the cap binding on ~97% of names there is no room to rebalance, so
   turnover is roughly **halved** and costs cut by about **two thirds**.

**The second effect is worth more than the first costs.** The constraint, on net, *helps*. That is
why $1bn sits near the net-optimal scale — not a convenient parameter choice but a consequence of
the brake.

## 6. How much this depends on the cost calibration

Costs enter linearly once weights are fixed, so the crossover solves exactly:

| cost multiplier | $1e9 | $1e8 matched | winner |
|---|---|---|---|
| 0.25 | +0.3453 | **+0.4582** | looser capacity |
| 0.50 | +0.2712 | **+0.2963** | looser capacity |
| **0.5715** | +0.2500 | +0.2500 | tie |
| **1.00** (as calibrated) | **+0.1229** | −0.0276 | tighter capacity |

**The turnover-brake conclusion holds unless transaction costs are overstated by more than 1.75x.**
Not knife-edge (it tolerates a 43% overstatement), not bulletproof (2x would flip it). `impact_k`
is therefore the most load-bearing single parameter in the paper and was **inherited rather than
estimated here** — it needs an independent calibration check before submission.

**Independent of the calibration:** §2's ICs, §4's constraint-binding shares and weight
correlations, §4's conditioning curve, and §5's *gross* Sharpe comparison. Lead with those if the
cost model cannot be defended.

## 7. A constraint on any reweighting anyone tries next

A frozen position — a name with no certified market inputs that month — cannot be traded, only
carried. Two attempts to leverage-match post hoc were both refused by the backtest:

1. uniform rescaling moves frozen positions: *"87 unpriceable names moved by 2.04e-05 (budget
   1.6e-05). A frozen position must be carried, not traded."*
2. scaling only tradeable names and carrying frozen weights verbatim **also** fails, structurally:
   the drifted prior book is `w(1+r)/(1+port_ret)`, so changing the tradeable weights changes the
   portfolio return and therefore what the frozen weight *would have drifted to*.

**The frozen sleeve is endogenous to the whole book.** No post-hoc reweighting — leverage matching,
volatility matching, risk-parity overlay — is available. Re-optimise under different constraints
instead (`--gross-max`).

## 8. Reproduce

```
# signal level
python tools/verify_arm_information.py --country DEU --from-weights-index
python tools/verify_arm_information.py --country IND --log <ind_stage02.log>

# the mechanism
python tools/exp_book_characteristics.py --country DEU --aum 1e9
python tools/exp_capacity_dose_response.py --country DEU --aum 1e8 1e9

# the matched-leverage arm
python pipelines/04_construct_portfolios.py --country DEU --aum 1e8 \
    --gross-max 0.13 --suffix _g013 --strategies <16 cells>
python tools/dev_backtest.py --country DEU --strategies <16 cells with _g013>
```

Every consumer resolves artefacts through `outputs/weights_index/<C>_<aum>.csv` and
`outputs/source_index/<C>.csv`, never by modification time — see §9.

## 9. A provenance hazard that affected four consumers

`outputs/weights/<strategy>/` and `outputs/predictions/<strategy>/` carry **no country in the
path**, and `paths.latest_run` resolves by modification time. Once a second country has run a
stage, "the latest artefact" silently means that other country's. Four consumers were caught in one
night — a Germany exhibit resolving to India's book, an IC diagnostic comparing Japan's scores to
India's targets, a book-characteristics table printing India's leverage under a German heading, and
stage 04 itself. **Every one produced a plausible number; none produced an error.**

Closed on both sides: stage 04 writes a weights index, stage 02 writes a source index,
`contracts.provenance` resolves through them and raises rather than falling back, and 10 tests
assert the refusals. **Any number computed before commit `2fb32db` should be re-checked against its
index.**

## 10. Limits

* Two countries complete, Japan running. Every slope rests on 16 cells.
* Conditional on $1bn and a 5% participation limit, both pre-registered. The $1e10 arm completes
  the curve but is 99.2% solver-degenerate and **its performance numbers must not be quoted until
  `verify_trade_caps --strict` passes**; if it fails, "not solvable at this scale" is the honest
  result.
* The economic-loss arm is not a competent implementation of its objective
  (`docs/ECONOMIC_ARM_CAPABILITY_GAP.md`): its IC is an order of magnitude below the prediction
  arm's, partly because it is forced to a gross the constraint makes infeasible. The factorial's
  economic main effect should not be read as a property of economic objectives.
* This reframing was arrived at **after** the pre-registered tax hypothesis failed. That failure is
  reported in `docs/RESULTS_WEDGE_TEST.md` §2 and §5, not omitted.
