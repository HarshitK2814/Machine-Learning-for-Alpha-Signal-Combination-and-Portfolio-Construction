# Targeted corrections to live documents (2026-10-14)

Scope: two contradictions listed in `docs/MANUSCRIPT_EVIDENCE_MAP_2026-10-14.md` (L1 and L2, with L3 which is the same near-ruined qualification). Only committed historical evidence was used (`docs/PAPER_2026-10-09_FULL_ACCOUNT.md` section 6.3.3; Phase 2 `results/capacity_return_difference/tierB_*.csv`, `docs/RESULTS_CAPACITY_RETURN_DIFFERENCE_2026-10-10.md`). No statistic was recomputed, no number changed, no manuscript was rewritten. Every edit keeps the earlier wording visible as a dated correction so that the trail is preserved. Internal researcher-led work; not an external review.

## 1. Taxes "decisive for survival" (withdrawn at `PAPER` 6.3.3) - L1

| File | Location | Change |
|---|---|---|
| `docs/PAPER_2026-10-09_FULL_ACCOUNT.md` | section 2.2 closing paragraph | the clause "while showing it is nevertheless decisive for survival" replaced by a dated correction stating that it is withdrawn and that no role for taxes in survival is established |
| same | contribution table row 3 | "decisive for survival" marked as an earlier phrasing, withdrawn, corrected 2026-10-14 |
| `tools/check_withdrawn_claims.py` + `tests/docs_hygiene/test_check_withdrawn_claims.py` | `PATTERNS` "survival framing" | the screen now also catches "decisive for survival" (same line); the regression test lists it. It is a screen, not verification, and does not catch a phrase wrapped across two lines |

## 2. Sharpe-point capacity gains without the near-ruined-comparator qualification - L2, L3

The qualification added in each place: the uncapped comparator's compounded terminal wealth is 7.7e-10 (Germany $100mn), 2.6e-06 (India $30mn), 6.7e-06 (Japan $1bn), and 1.1e-17 at Japan $10bn (Tier B). "Solvent" is the minimal criterion only; the figures are an accounting difference against a near-ruined comparator, not an established economic gain; B(A) is the like-for-like object.

| File | Location | Change |
|---|---|---|
| `PAPER` | abstract, finding 1 (including "Japan's comparison book is solvent through $10bn", L3) | dated bracketed qualification inserted; the numbers and the rest of the sentence are unchanged |
| `PAPER` | section 8.9, after the one-book table | dated qualification block inserted before the "Ordering on one book" paragraph |
| `docs/STATUS.md` | "Capacity channel" bullet | dated qualification inserted in the bullet |
| `docs/FINALIZATION_AUDIT_2026-10-09.md` | verdict row "A binding ADV participation cap improves ..." | status changed from "Established on solvent rungs" to "Qualified 2026-10-14: accounting difference against a near-ruined comparator, not an established economic gain" with the original status quoted |
| `docs/RESULTS_CAPACITY_CHANNEL_2026-10-09.md` | header | dated proviso covering every use of "solvent rung" in the file (lines 17, 34, 44, 99, 125, 308); the body is kept unedited as the record |

## 3. Deliberately not edited

* `docs/handoff/21_FOR_MAHAM_001D_SIGN_FLIP_COUNTERSIGNATURE_2026-10-09.md` (line 11 repeats the unqualified figures). It is a dated document prepared for a counterparty's response; altering it after the fact could be mistaken for altering what was put to them. It is **superseded in this respect** by the qualification above and by this note; any future communication should cite the qualified wording.
* `PAPER` lines 439-440 and 685-686: they already mark the insolvent-rung figures as not interpretable; the abstract and section 8.9 qualifications cover the remaining solvent-rung figures.
* L4 (calibration qualifier on "no mandate size at which it hurts"), L5 (stale dates), L6 (design-axis scope), L7 (stale test count), L8 (specification wording): not part of this task; still open in the evidence map.

## 4. Checks

Documentation hygiene tests, the withdrawn-claims screen and `git diff --check` after the edits are recorded in `docs/PHASE_C_RUN_READINESS_V2_2026-10-14.md`.
