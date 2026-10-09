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

## 5b. The full dose-response: three AUM arms, and no viable operating point

Germany, prediction arm, 8 cells, 132 months, same stage-02 scores throughout. The $1e10 arm's
constraints were verified against **its own** participation cap before use (0 of ~32,000 trades
over cap on every prediction cell; its 99.2% `optimal_inaccurate` rate is a solver tolerance label,
not a violation):

| AUM | gross Sharpe | **net Sharpe** | gross p.a. | **net p.a.** | turnover | cost drag |
|---|---|---|---|---|---|---|
| **$1e8** | 0.654 | **−0.116** | 97.7 bps | **−19.1 bps** | 0.0521 | 116.8 bps |
| **$1e9** | 0.423 | **+0.128** | 24.3 bps | **+7.1 bps** | 0.0135 | 17.2 bps |
| **$1e10** | 0.469 | **+0.271** | 3.6 bps | **+2.1 bps** | 0.0016 | 1.5 bps |

**Net Sharpe is monotone increasing in AUM** — −0.116 → +0.128 → +0.271. The harder capacity binds,
the better the risk-adjusted net return, because cost drag falls 77-fold (116.8 → 1.5 bps) across
the range while gross Sharpe does not fall nearly as much.

**Net return is hump-shaped**, peaking at $1e9: −19.1 → **+7.1** → +2.1 bps p.a.

Those two facts together are the paper's sharpest statement:

> **There is no AUM in this range at which the strategy delivers both a respectable Sharpe ratio
> and a non-trivial return.** At $100mn it has the best achievable signal (gross Sharpe 0.654) and
> loses money net. At $1bn it earns its highest net return — **7.1 bps a year**, about $710k on
> $1bn, below a management fee. At $10bn it posts its best net Sharpe, 0.271, on a net return of
> **2.1 bps** and a book that is 1.7% invested. Every operating point is unusable, for a different
> reason.

*A correction:* gross Sharpe is **not** monotone in AUM — 0.654 → 0.423 → **0.469**. It falls as
capacity begins to bind and then recovers slightly at $1e10, where the book is 100% ADV-capped and
is close to proportional to ADV times the sign of the signal. So "capacity monotonically suppresses
signal" is true from $1e8 to $1e9 and false from $1e9 to $1e10, and I had asserted the monotone
version. What *is* monotone is the share of names at the cap (83% → 97% → 100%), the cost drag, and
the net Sharpe.

## 6. How much this depends on the cost calibration

Costs enter linearly once weights are fixed, so the crossover solves exactly:

| cost multiplier | $1e9 | $1e8 matched | winner |
|---|---|---|---|
| 0.25 | +0.3453 | **+0.4582** | looser capacity |
| 0.50 | +0.2712 | **+0.2963** | looser capacity |
| **0.5715** | +0.2500 | +0.2500 | tie |
| **1.00** (as calibrated) | **+0.1229** | −0.0276 | tighter capacity |

**The turnover-brake conclusion holds unless transaction costs are overstated by more than 1.75x.**

Resolved further, on the impact term specifically. The cost model is the **canonical square-root
law**: `impact_i = k * sigma_d_i * sqrt(AUM/ADV_i) * |dw_i|^1.5`, which rewritten with traded
dollars `Q_i = |dw_i|*AUM` is `cost_i/|dw_i| = k * sigma_d_i * sqrt(Q_i/ADV_i)`. So `k = 1` means
*trading one day's volume costs one day's volatility* — the Grinold–Kahn rule of thumb, and inside
the range Almgren et al. estimate. It is a standard choice, not an aggressive one.

Decomposed from the C12 engine's own monthly `cost_spread` / `cost_impact` / `cost_borrow`
(reconciled against the published summary: L-S-P-0 gross 0.00294 and cost 20.88 bps against 0.0029
and 20.88):

| | spread | **impact** | borrow | total | impact share |
|---|---|---|---|---|---|
| $1e9, gross 0.132 | 3.15 | **7.47** | 6.59 | **17.21** | 43.4% |
| $1e8, gross 0.130 | 7.17 | **46.23** | 6.49 | **59.89** | **77.2%** |

The looser-capacity arm's cost is impact-dominated, because with the participation cap slack it
takes much larger per-name trades and impact is superlinear in trade size. Solving for the
crossover on `impact_k` alone:

| `impact_k` | $1e9 | $1e8 matched | winner |
|---|---|---|---|
| 0.00 | +0.2516 | **+0.4716** | looser capacity |
| 0.25 | +0.2194 | **+0.3460** | looser capacity |
| 0.50 | +0.1872 | **+0.2204** | looser capacity |
| **0.5888** | — | — | **tie** |
| **1.00** (canonical) | **+0.1229** | −0.0308 | tighter capacity |
| 2.00 | −0.0059 | −0.5333 | tighter capacity |

**The turnover-brake conclusion requires the square-root impact coefficient to be at least 59% of
its canonical value.** That is the honest statement of the dependency: the model's `k = 1` is the
standard calibration, published estimates of this coefficient span roughly 0.3–1.5 across studies
and markets, and a coefficient at the low end of that range would reverse the ordering. So the
result should be reported **with the crossover stated**, and an independent estimate of `k` on
these specific markets would strengthen it materially.

*A correction worth recording:* I first inferred from per-trade medians (median half-spread 29.8 bps
against median impact 11.9 bps per dollar traded) that cost was spread-dominated and `impact_k`
therefore could not matter. That was wrong. Because impact is superlinear, the aggregate annual drag
is dominated by the large trades sitting at the 5% participation cap (p95 participation 4.68%)
rather than by the median trade. Per-trade medians are the wrong statistic for this question.

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
* The curve spans $1e8 to $1e10 at a 5% participation limit; the $1bn point and the limit were
  pre-registered. The $1e10 arm passed `verify_trade_caps --aum 1e10 --strict` (0 of ~32,000 trades
  over cap on every prediction cell), so its numbers are used; the caveat that stood before that
  check is discharged.
* The economic-loss arm is not a competent implementation of its objective
  (`docs/ECONOMIC_ARM_CAPABILITY_GAP.md`): its IC is an order of magnitude below the prediction
  arm's, partly because it is forced to a gross the constraint makes infeasible. The factorial's
  economic main effect should not be read as a property of economic objectives.
* This reframing was arrived at **after** the pre-registered tax hypothesis failed. That failure is
  reported in `docs/RESULTS_WEDGE_TEST.md` §2 and §5, not omitted.
