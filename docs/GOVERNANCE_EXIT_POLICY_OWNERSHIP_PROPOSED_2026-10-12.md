# Proposed governance note: ownership of exit and liquidation accounting

**Status:** Proposed, pending written acceptance and required approvals
**Scope:** Exit treatment for uncertified holdings, temporarily unpriced securities and panel leavers in realised portfolio accounting
**Related components:** `src/alphacomb/tax/backtest.py`, `pipelines/06_after_tax_eval.py`, `NON_TRADEABLE_TREATMENT.md`

> **Record note (2026-10-12).** The text below was supplied by the project owner and is recorded unchanged. It is a
> **proposal**: no appointment is in effect. The evidence behind it (authorship by `git blame`, the documented assignments
> of final C12 accounting and of the six frozen accounting decisions to Absar) is summarised in the read-only ownership
> review of the same date. The acceptance record in section 6 is **blank on purpose**.

## 1. Why this appointment is needed

The repository does not currently assign formal ownership of exit-policy decisions.

The documented non-tradeability policy says that a security that remains alive but becomes uncertified is carried at its drifted weight and not traded, while panel leavers are closed using the applicable delisting return.

The current after-tax pipeline instead charges no trading cost when certain held positions are closed because current cost inputs are unavailable. The wedge-tool accounting uses a different convention, charging exits using the previous month's inputs where available.

The cost-parity diagnostic shows that this difference is a material contributor to discrepancies between the two accounting implementations. Neither implementation should be presumed correct merely because it produces a particular result.

## 2. Proposed responsibilities

### Decision owner: Absar Wani, proposed, pending acceptance

Absar is proposed as the decision owner for the exit and liquidation accounting policy, given the documented assignment of final C12 accounting and his recorded approval of existing accounting conventions.

The proposed responsibility is to review the available evidence, consult the relevant maintainers, and issue a written ruling on the operational treatment of exits. This appointment does not imply that Absar authored or previously approved the current exit behaviour.

**This appointment becomes effective only after Absar explicitly accepts it in writing.**

### Implementing maintainer: Harshit Kumar

Harshit is responsible for documenting the current implementation, identifying the code paths affected by the ruling, implementing an approved change, and adding tests for the selected convention.

Because Harshit authored both the documented frozen-sleeve policy and the current exit behaviour, he will not be the sole approver of the accounting convention he implemented.

### Protocol authority: Maham

Maham will review the ruling if it changes a preregistered or confirmatory result.

If the ruling constitutes a change to the frozen research contract, the existing three-party approval requirement applies. No contract change becomes effective without the required approvals from Harshit, Absar and Maham.

## 3. Decisions that the policy must cover

The written ruling must distinguish these cases:

1. **Alive but uncertified:** how a held position is carried at its drifted weight while its cost inputs remain uncertified, and when it may be traded again.
2. **Temporarily unpriced:** how the position is valued during the missing-price period and what conditions permit a subsequent trade.
3. **Panel leaver or delisting:** which final-return or delisting convention applies, how the position is closed, and how liquidation costs are treated when inputs are unavailable.
4. **Missing liquidation information:** which cases remain unresolved rather than receiving an unsupported zero-cost or zero-return imputation.

The ruling must identify whether it interprets the existing contract or amends it. Any amendment must follow the applicable approval requirements and be reflected in the relevant documentation and tests.

## 4. Research-record safeguards

The committed Phase 2 analysis remains the historical record of the accounting actually executed. It must not be silently rewritten to match the eventual ruling.

Any future rerun must record the selected convention, its approval status, the relevant code and configuration versions, and the effect on affected results.

Cost-calibration sensitivity remains blocked until the exit-policy decision is documented and the required approvals have been obtained. No cost coefficients, frozen portfolio weights or research results may be changed as part of appointing the decision owner.

## 5. Acceptance and effective date

The proposed decision owner must explicitly accept the responsibility. The record must then identify the ruling, required countersignatures, effective date, and any changes to the frozen contract.

Until acceptance and required approvals are recorded, the exit-policy ownership decision remains unresolved.

## 6. Acceptance record (to be completed by the named people, in writing)

| Item | Recorded value |
|---|---|
| Decision owner accepts (Absar Wani) | **ACCEPTED in writing, 2026-10-13** (`EXIT_POLICY_RULING_AND_001E_RESPONSE_2026-10-13.md`) |
| Implementing maintainer acknowledges (Harshit Kumar) | **NOT RECORDED** |
| Protocol authority acknowledges (Maham) | **NOT RECORDED** |
| Ruling (document and date) | **ISSUED 2026-10-13** by Absar, recorded in `EXIT_POLICY_RULING_AND_001E_RESPONSE_2026-10-13.md`; implementation and Maham's review outstanding |
| Interprets or amends the existing contract | **Interprets** (per Absar); Maham to confirm |
| Required countersignatures | Maham review required if a confirmatory result changes; not yet given |
| Effective date | n/a |
| Changes to the frozen contract | none recorded |

Status of the exit-policy ownership decision: **OWNER ACCEPTED, RULING ISSUED; acknowledgments by Harshit and Maham, and Maham's review, NOT YET RECORDED.** Updated 2026-10-13.
