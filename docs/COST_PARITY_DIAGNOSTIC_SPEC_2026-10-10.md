# Cost-accounting parity diagnostic: specification (written before the run)

**Date:** 2026-10-10. **Status:** specification for Workstream A. Phase 1 (`b8e21ba`) and Phase 2 (`ac669f2`) are
frozen; nothing here modifies them or their manifest. The diagnostic is accounting only: it re-evaluates the
existing cost functions on existing weights. No model is trained, no cost parameter is changed, no AUM rung is
added. Scope: the six rungs (Germany $100k, $300k, $100mn; India $30mn; Japan $1bn, $10bn) x {uncapped, capped}
= **12 rung-book pairs**, each averaged over the 8 prediction cells and the 2009-2019 months.

## 1. The two cost accountings (as implemented)

Cost per month is in return units (fraction of NAV). For a trade of size `q = |dw|` in a name with inputs
`z = (spread s, daily volatility sigma, ADV)`:

    F(q; z) = (s/2 + c) q  +  k sigma sqrt(A/ADV) q^1.5          c = 1 bp commission, k = 1, A = mandate

`F_lin` is the first term (spread plus commission); `F_imp` the second. Both tiers call the same
`trade_cost_numpy`.

**Tier A (wedge tool).** Target weights `T_t`. Let `S_t` be the cross-section at `t`: names with a score and
certified inputs (the `--require-cost-inputs` filter), including names whose target weight is zero.
* Continuing names `i in S_t`: trade `dw_i = T_t(i) - T_{t-1}(i)`, inputs `z_t(i)` (previous target 0 if absent).
* Exits `i in S_{t-1} \ S_t`: trade `|T_{t-1}(i)|`, priced on **last month's** inputs `z_{t-1}(i)` if complete.
* No borrow cost.

**Tier B (pipeline, `after_tax_backtest`, zero tax).** Each month the account holds drifted positions; the
trade is to the target weight. `Dprev_i = T_{t-1}(i) (1 + r_i - q_i) / (1 + gross_{t-1})` is the drifted weight
(price return `r`, dividend `q`, gross portfolio return). Names in the trade universe are
`idx_t = (target names + held names) intersected with priced_at(t)`; only those with certified inputs at `t`
(`cost_idx_t`) are charged:
* every `i in cost_idx_t`: trade `dw_i = T_t(i) - Dprev_i`, inputs `z_t(i)`;
* held names outside `cost_idx_t` are closed for tax purposes **at no trading cost** (unpriced or uncertified);
* borrow: `(1% / 12) x short gross` of the target weights, added to cost.

## 2. The three switchable conventions

| switch | Tier A value | Tier B value |
|---|---|---|
| **D** trade-size basis | from the previous *target* weights | from the previous *drifted* weights |
| **X** treatment of names that leave `S_t` | charged `|T_{t-1}|` at prior-month inputs | charged only if still certified at `t`, current inputs, drifted size; otherwise free |
| **B** borrow | none | flat 1% on shorts |

A cost evaluator `V(d, x, b)` with each switch set to its Tier A or Tier B value is defined for every one of the
8 combinations. **Replication requirements:** `V(A,A,A)` must equal the tracked Tier A cost and `V(B,B,B)` must equal
the pipeline's own spread+impact+borrow, month by month and cell by cell. If either fails the diagnostic stops
and reports the failure; nothing is adjusted to force agreement.

## 3. Quantities reported per rung-book pair (annualised, points of NAV, x12)

* `cost_A`, `cost_B`, discrepancy `G = cost_B - cost_A`; split into spread+commission, impact, borrow.
* `V` for all 8 combinations; one-at-a-time effects from the Tier B baseline,
  `e_m = V(only m switched to Tier A) - V(B,B,B)`, for `m in {D, X, B}`; pairwise and three-way effects;
  interaction `= (V(A,A,A) - V(B,B,B)) - (e_D + e_X + e_B)`; **Shapley averages** over the 6 orderings as the
  order-free attribution.
* Share of annual traded notional in exit names; month counts; exits charged by A and not by B.
* Replication errors (max over cell-months) and the unexplained residual `R = G - (cost_B,rep - cost_A,rep)`.
* Descriptive link to coverage: the country's documented cost-input coverage (Germany 65.1%, India 99.1%,
  Japan 99.8%) next to the measured exit-convention effect. Three countries; association only, no causal claim.

## 4. Pre-set tolerance and decision rules

* **Material discrepancy:** `|G| > 0.05` points per year. A pair at or below that is reported as "no material
  discrepancy" and **no percentage closure is computed** for it.
* **Reconciled:** the replicated discrepancy reproduces the reported one, `|R| <= max(0.05 points, 5% of |G|)`.
* **Closure of mechanism m** (material pairs only): `e_m / (V(A,A,A) - V(B,B,B))` using the one-at-a-time effect;
  the Shapley share is reported beside it.
* **Common dominant mechanism:** one mechanism achieves closure >= 90% in **at least 10 of the 12 pairs**. Pairs
  without a material discrepancy cannot count toward the 10; the rule is applied to all 12 as approved, and the
  count among material pairs is also shown. Failing the rule does not suppress partial explanations, which are
  reported with their measured shares.
* Whatever is found, **no model, parameter or result is adjusted.** The diagnostic changes how the discrepancy is
  described, nothing else.

## 5. Inputs and provenance

Weights: `outputs/decile_weights/{C}/tierb/aum_*/` (git-ignored; the re-dump verified bit-identical to the tracked
Tier A series). Cross-section and inputs: the frozen country bundle and the stage-02 prediction artefacts via
`outputs/source_index/{C}.csv`. Reported Tier A / Tier B costs: tracked files in
`results/capacity_return_difference/`. The pipeline run is instrumented by **recording** the arguments of
`trade_cost_numpy` and `cost_inputs_for` (wrappers that delegate unchanged); it does not alter any computation.
