# Exit-policy gate: positions that become uncertified, unpriced or leave the price panel

**Date:** 2026-10-12. **Status: UNRESOLVED. The ruling has not been obtained.** This document states the question, the
evidence and the options, and records the outcome as unresolved until the pipeline owner rules. Nothing has been
changed: Phase 2 (`ac669f2`) remains the as-run record, Tier A is not substituted for Tier B, and no value is
invented. Cost sensitivities stay blocked behind this gate (`COST_CALIBRATION_SENSITIVITY_PROPOSAL_2026-10-10.md`).

## 1. The question

When a held position's name stops having certified spread, volatility and positive ADV in a month, or has no row in the
cost-input table at all, what does the evaluation do with that position, and what does it charge?

**Principle stated by the review:** zero-cost liquidation must not be the default merely because cost inputs are
unavailable.

## 2. What the repository already says

| Source | Statement |
|---|---|
| `NON_TRADEABLE_TREATMENT.md` (8 Oct, layer C11, the optimiser) | Three sets. **Tradeable:** certified inputs, optimised normally. **Frozen:** no certified inputs but C6 has a row (alive, unpriceable): "carried at its drifted weight; not traded". **Exited:** no C6 row at all (left the panel): "closed by the delisting return already in C4". |
| Document 13, requirement 2 | An uncertified security-month is non-tradeable; imputing a spread or ADV to restore it is prohibited. |
| `NON_TRADEABLE_TREATMENT.md`, rationale | "Selling a position you cannot price is an unpriced liquidation." |

So the documented policy for the optimiser is **carry, do not liquidate** for alive-but-uncertified names, and
delisting-return closure for names that left the panel.

## 3. What the evaluations actually do (measured in the parity diagnostic)

The decile-book evaluation does not use the optimiser's treatment. Its weight files list only the names in the current
scored, certified cross-section.

| | Alive, no certified inputs | Left the panel (no C6 row) |
|---|---|---|
| **Optimiser path (documented)** | carried at drifted weight, not traded | closed by delisting return |
| **Tier B (pipeline on decile weights, as run)** | **sold to zero at no trading cost** (the ledger trades the name to its zero target; the cost routine is not given the name) | closed at no trading cost |
| **Tier A (wedge tool, as run)** | charged `\|last target weight\|` on last month's inputs (an imputation of inputs) | same |

So, for alive-but-uncertified names, **Tier B's behaviour is the one the principle rules out as a default, and it
differs from the documented optimiser convention.** Tier A's behaviour is an imputation, which requirement 2 also argues
against. Neither tier follows the carry convention.

## 4. Size of the effect (existing results, `COST_PARITY_DIAGNOSTIC_RESULTS_2026-10-10.md`)

* Exit convention is the largest contributor to the Tier A / Tier B cost gap in all 6 uncapped pairs (Shapley +1.2 to
  +75.8 points a year); it is negligible in the capped books (at most 1.4 points, usually under 0.2).
* Germany: 25-71% of exit notional is names that remain in the panel without certified inputs (the case in question)
  and 29-75% is names with no C6 row. India: 98% have no row. Japan: 27-65% are certified but unscored (priced by both
  tiers) and 35-72% have no row.
* The uncapped positions are multiples of daily volume (median trade 128% to 1,719% of ADV), so any exit price there is an
  extrapolation whichever convention is chosen.
* The headline optimised-book net Sharpe at $1bn is **not** examined by this diagnostic; that path uses the documented
  frozen-sleeve treatment.

## 5. Options for the ruling

1. **Carry (documented optimiser convention) applied to the decile-book evaluation:** alive-but-uncertified names are held
   at their drifted weight, earn their return, and are liquidated, with cost, only when certified inputs return; names
   that leave the panel are closed by the delisting return. Needs a code change in the evaluation (not made), and the
   Phase 2 numbers would be re-run as a *new, labelled* analysis, not substituted.
2. **Charge at last certified inputs (Tier A):** an explicit, labelled imputation. Requires an approved convention that
   overrides requirement 2 for exits only.
3. **Zero cost (Tier B as run):** acceptable only as a labelled as-run limitation, not as a default.
4. **Unresolved:** keep both tiers, report the gap as the measured sensitivity to the convention, and state the
   limitation. No sensitivity run proceeds.

## 6. Ruling record

| Field | Value |
|---|---|
| Ruling owner | **Absar Wani, PROPOSED and not yet accepted** (see `GOVERNANCE_EXIT_POLICY_OWNERSHIP_PROPOSED_2026-10-12.md`); implementing maintainer Harshit; Maham reviews if a preregistered or confirmatory result changes. Until written acceptance is recorded the owner is unresolved. |
| Ruling | **NOT OBTAINED** |
| Date | n/a |
| Outcome recorded here | **UNRESOLVED** |
| Effect on committed work | none; Phase 1 and Phase 2 stay as-run |
| Effect on planned work | cost sensitivities blocked; Phase 2 limitations text must carry this item |

If liquidation or marking cannot be supported by the available data and an approved convention, the outcome stays
"unresolved" and the limitation is stated in the paper. No value is to be fabricated for positions that cannot be priced.
