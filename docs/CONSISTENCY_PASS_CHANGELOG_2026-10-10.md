# Consistency pass (audit task P0-1): changelog

**Date:** 2026-10-10. **Status:** changes made in the working tree, **not committed**, pending review.
**Scope:** documents and one new checker only. No file under `src/`, `pipelines/`, `tests/`,
`configs/`, `data/` or `outputs/` was touched. No result was recomputed. No experiment was run.

## What was done and why

Live passages still presented withdrawn results as current. Each is now either corrected or kept as a
clearly labelled historical record with the reason. Withdrawn values are struck through or marked, not
deleted; every removed line was a heading or sentence replaced by a labelled version (verified by
comparing each removed line against the edited file).

| File | Change |
|---|---|
| `STATUS.md` | New **CURRENT STATE** block at the top. The three time-stamped blocks below it are relabelled "Historical record - superseded where marked", with the withdrawn rows, the "kept" column, the survival finding, the "+12.7 / closes blocker 5" sentence and the stale venue note marked in place |
| `PAPER_2026-10-09_FULL_ACCOUNT.md` | Abstract finding 4 (design null) scoped to the capped decile book in Germany and India, with the Japan conditioning observation disclosed as exploratory. Insolvent rungs marked † in §6.2.1, §6.2.4 and §6.5; solvent-rung significance counts added; §6.2.3 weighting table marked pre-fix; weighting robustness stated as unconfirmed on the compliant universe; §6.4 gains the optimised-book table; §8.7 heading no longer says "unresolved"; §12 statuses corrected and renumbered in order; §13 venue marked superseded; blocker 5 no longer "closed"; retraction counts and test count updated |
| `RESULTS_CAPACITY_CHANNEL_2026-10-09.md` | Correction banner; title and §1 re-stated against solvent rungs; † on insolvent rungs; "tax removes 87%" struck; weighting row of the robustness table marked unconfirmed |
| `RESULTS_TAX_THREE_COUNTRY_2026-10-09.md` | Title and §1/§4 survival framing struck; "within 1% [withdrawn]" softened; "kept" column struck; ladder status updated (Japan run, India not) |
| `RESULTS_DESIGN_IDENTIFIABILITY_2026-10-09.md` | Scope note: decile books, Germany and India only; Japan conditioning observation disclosed |
| `handoff/21_...` | Correction block at the top, listing superseded figures for the person asked to sign off |
| `Closest_Prior_Art_Tracker.md` | §C3 prediction/table and §C5 point 2 marked withdrawn (found by this pass; the audit's number-based search missed them); the 5x/53x claim and the "kills 10-100x" wording corrected |
| `RESULTS_WEDGE_TEST.md`, `handoff/19_...` | 5x / 53x [withdrawn] struck with the correction (all-cell averages; prediction cells 2.70x / 87.4x / 3.7x JPN) |
| `CANDIDATE_REFRAMING_CAPACITY.md`, `RESULTS_CAPACITY_2026-10-09.md`, `PRACTITIONER_GAP.md` | "Superseded in part" banner on older context documents; body untouched |
| `VERIFICATION_PROTOCOL_2026-10-09.md` | Update note: error 4 resolved, list has grown, some early figures corrected |
| `AMENDMENT_001D_...` | Note that the §10 $1bn figures compare against an insolvent book; record otherwise unchanged |
| `tools/check_withdrawn_claims.py` (new) | Checks the P0-1 acceptance criterion by code |

## Evidence

* `python tools/check_withdrawn_claims.py` on the **committed HEAD** documents: **FAIL, 31 hits** in 9
  files (exit 1). On the edited tree: **PASS**, 69 pattern hits all within 10 lines of a retraction
  marker, every record file carrying a header marker (exit 0).
* Full test suite: **464 passed, 0 failed** (same as the audit baseline).
* `git status`: 14 modified documents, 1 new tool, nothing else.

## Limits of this pass

* The checker is **necessary, not sufficient**. It proves a label is adjacent, not that it explains the
  withdrawal. `STATUS.md` passed at HEAD only because unrelated "withdrawn" wording sat within ten lines
  of the stale table, so the checker would not have caught that file; the audit did.
* The checker exempts files carrying the literal banner or a header marker; those documents' bodies are
  not individually checked.
* Not corrected because they were **not re-run** (they need approval): value-weighting on the compliant
  universe, and solvency under the sensitivity cost models. Both are now stated as unconfirmed.
* The older time-stamped blocks in `STATUS.md` remain, as history, below the CURRENT STATE block.

## Review pass (same day): checker rewritten, one missed document found

The first checker accepted any retraction word within ten lines and exempted any file carrying a
banner or header. Rewritten: a hit now needs a label on its own line (or inside a strikethrough), or
within 3 lines in the **same paragraph** (never across a blank line, never from a neighbouring table
row), or a level-2+ retraction heading above it. No file-level exemption of any kind; record files and
bannered files are checked like the rest. Generic words (corrected, historical, artefact, moot, no
longer) are no longer labels. Scope widened to `docs/`, `research/`, `prereg/`, `README.md`.

* New tests: `tests/docs_hygiene/test_check_withdrawn_claims.py`, 14 tests (current claim fails;
  struck / labelled retraction passes; unrelated marker in another paragraph or far away fails; generic
  words fail; banner does not exempt body; title heading does not exempt body; heading label scoped to
  its section; table row needs its own label; the known same-line limitation is pinned).
* On committed HEAD the strict checker finds **69 unlabelled hits in 13 files**. It then found
  `STRATEGIC_ASSESSMENT_2026-10-09.md`, which presented the sign flip, +8.77 and 5x/53x as current and
  which the first checker had passed. That file now has a SUPERSEDED banner; 38 further hits across 11
  files were given an inline `[withdrawn]` tag (text added; nothing deleted or reworded).
* Limits unchanged in kind: same-line labels are trusted, so a line mixing a live and a withdrawn figure
  can pass; stale claims in new wording or new numbers are invisible. PASS is a screen, not verification.
* Full suite: 478 passed (464 + 14 new), 0 failed. `git diff --check`: clean.
