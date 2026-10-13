# Record of Absar Wani's written response: exit-policy ownership, exit ruling, and Amendment 001E positions

**Date received:** 2026-10-13 (written message from Absar Wani to Harshit Kumar, relayed by Harshit and recorded here)
**Status:** RECORD ONLY. This file changes no code, no frozen output, no cost coefficient and no committed result.
Amendment 001E (draft `4bad8e3`) is **not edited** by this record and **remains non-binding**.

## 1. Acceptance of the decision-owner role

Absar Wani accepted the exit-policy decision-owner role "as proposed in
`GOVERNANCE_EXIT_POLICY_OWNERSHIP_PROPOSED_2026-10-12.md`, with [Harshit] as implementing maintainer and Maham as
protocol authority." Per section 2 of that note, the appointment is effective from this written acceptance.

Not yet recorded: Harshit's own acknowledgment and Maham's acknowledgment (see the acceptance table in the governance note).

## 2. Ruling on the exit-policy convention

Absar states the ruling is an **interpretation of the existing frozen-sleeve and no-imputation principles, not an
amendment** and not permission to rewrite previous results.

1. **Alive but uncertified holdings.** Follow the documented C11 frozen-sleeve convention. Preserve existing positions at
   their drifted holdings where valid valuation data exist. They are not sold to zero merely because current spread,
   volatility or ADV is uncertified. No discretionary trades occur until the relevant market inputs are certified again.
2. **Temporarily unpriced holdings.** Preserve position quantities and tax lots; explicitly flag unavailable or stale
   valuation. No zero returns, zero liquidation costs or unsupported price estimates. If an accurate NAV cannot be
   established, the affected observation is **unresolved** until evidence or an approved treatment is available.
3. **Panel leavers and delistings.** Distinguish confirmed delistings or mandatory corporate-action exits from
   securities that merely disappeared from the scored cross-section or C6 table. For genuine exits apply the certified
   terminal-return/delisting convention in C4 and close the position once. Liquidation costs reflect the documented
   transaction mechanism and available evidence; missing costs must not automatically become zero.
4. **Missing exit information.** Fail closed: explicit unresolved status and a reported limitation. Do not fabricate
   transaction costs, prices or returns.

This corresponds to **option 1 (carry)** of `EXIT_POLICY_GATE_2026-10-12.md` section 5, with the unresolved
status of option 4 retained where information is missing.

**Conditions set by the ruling**
- Applying it to the decile evaluation needs **separate implementation, tests and a newly labelled analysis**, delivered
  as a separately reviewed change with no silent modification of frozen outputs.
- The original Phase 2 as-run record stays intact.
- **Maham should review any change affecting confirmatory findings.**

## 3. Positions on Amendment 001E

| Item | Absar's position | Consequence |
|---|---|---|
| D1 Japan TERM | **Supported, conditional.** BOJ FM02 `STRAK_STRACDN2DB04` as explicit successor/proxy from April 2022. The 315-month overlap and correlation 0.9978 are persuasive but do not establish exact equivalence. | Before the lockbox opens, record (a) maturity and level differences, (b) retention of the frozen publication lag, (c) current-vintage revisions, (d) the preregistered TERM = 0 robustness comparison. Conditions are not yet recorded in the amendment. |
| D2 India CREDIT | **Approved.** No bridging across BPLR/Base Rate/MCLR/EBLR. Neutralising the unavailable state at zero is acceptable as a declared modelling limitation, not as an observed CREDIT value. | India-specific conditional-cell limitations must be stated explicitly. |
| D3 Remaining C5 sources | **Not certified.** Absar cannot yet certify that every series is refreshed correctly. | Needs evidence of exact source mappings, complete monthly coverage, appropriate historical publication lags, release-date/vintage/legacy-series checks, and uninterrupted expanding standardisation (ddof = 1, 24-observation rule). |
| New issue: shortability | `UNKNOWN_FAIL_CLOSED` must be reconciled with the dollar-neutral long/short evaluation. A modelled borrow fee is not proof of actual short availability. | The protocol needs an explicit treatment of that distinction before countersignature. |
| Countersignature of 001E | **Not given.** | Remains pending, together with Maham. |
| Cost-calibration (S0/S1/S2) and OOS runs | **Not authorised.** | Remain blocked (B3). |

## 4. Effect on the blocker ledger (as of 2026-10-13)

- **B1:** owner accepted, written ruling issued. **Implementation and Maham's review outstanding**; the ledger row is
  updated in `BLOCKER_LEDGER_2026-10-12.md`.
- **B3:** still blocked; not authorised by this ruling.
- **B4:** still open; Absar withholds countersignature until D1 safeguards, D3 evidence, the shortability reconciliation and
  the remaining exposure checks are closed.
- **B7:** D1 conditionally supported, D2 approved, D3 open.
- **B8:** the exit-policy condition can be met by the recorded ruling once Maham has reviewed it.

## 5. Next actions (none taken by this record)

1. Harshit and Maham acknowledge the governance note (acceptance table).
2. Draft the carry-convention evaluation change as a separate branch with tests, producing a new labelled analysis.
3. Add the D1 safeguards and the shortability treatment to a revised 001E draft **before** the lockbox opens.
4. Assemble D3 evidence (source mappings, release dates, vintages, normalisation check) for each listed series.
5. Maham reviews the ruling and any change affecting confirmatory results.
