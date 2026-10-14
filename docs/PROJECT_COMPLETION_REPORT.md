# Project completion report (2026-10-14, completion sprint)

Internal researcher-led report; not an external review. No approval by Maham or Absar beyond their documented responses is claimed; Maham's acknowledgement of the exit ruling is outstanding and 001A-001E are not countersigned. Start: HEAD `24e9a4c` (clean). Work branch: `feat/completion-sprint-2026-10-14`.

**Overall state: not submission-ready.** A defensible, narrower as-run manuscript candidate exists, but items below that undermine or can change its claims remain open.

## 1. What is completed

* Claim-evidence audit of the whole claim set: `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md` (41 status entries; 8 supported as run, 17 supported with qualification, 7 withdrawn, 4 blocked, 5 unverifiable).
* Publication-path decision (rule B: narrower, separate candidate): `docs/FINAL_PUBLICATION_PATH.md`.
* Manuscript candidate `submission_candidate_as_run_only/` with a trimmed bibliography, hash-recorded traceability table and a deterministic consistency check.
* Withdrawn-claims screen extended; README corrected; Phase C closeout preserved.

## 2. What was actually changed

| Change | Files |
|---|---|
| Matrix, decision, this report | `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md`, `docs/FINAL_PUBLICATION_PATH.md`, `docs/PROJECT_COMPLETION_REPORT.md` |
| Candidate | `submission_candidate_as_run_only/{manuscript.md, references.bib, TRACEABILITY.csv, README.md}` |
| Consistency check and tests | `tools/check_submission_candidate.py`, `tests/tools/test_check_submission_candidate.py` (8 tests, each injecting a defect) |
| Withdrawn-claims screen | `tools/check_withdrawn_claims.py` (scans the candidate directory; new pattern for the Sharpe-point capacity gains against near-ruined comparators, with "near-ruined" as a label), `tests/docs_hygiene/test_check_withdrawn_claims.py` (3 tests added) |
| README | stale "290 tests" and handoff-era status replaced by a current-state section, data-access section and environment note |

No result was regenerated, no analysis code changed, no historical document was edited, and no data source or external system was accessed.

## 3. Publication path and why

Rule B. Phase C was a robustness revision, not the source of the findings, so its block does not remove the as-run evidence; but the original headline set is partly withdrawn (Sharpe-point capacity gains, the cap "improves performance", the clean placebo match, the survival framing) and partly untraceable (Germany's net-Sharpe and optimised-book tax numbers). The candidate is therefore a **measurement and cautionary-methods paper**: capacity in B(A) units only, tax as statute-determined channel existence plus an ordering of magnitudes on the executable decile book, a scoped design-axis null, and the coverage-asymmetry worked failure. Full reasoning and the list of what changed relative to the original framing: `docs/FINAL_PUBLICATION_PATH.md` section 4.

## 4. Status of the major claims (details in the matrix)

| Claim | Status |
|---|---|
| Net Sharpe of the optimised book not distinguishable from zero at $1bn | India and Japan supported with qualification; **Germany unverifiable** |
| Gross signal real; executable capped decile book negative net | Supported with qualification (matched-book attachments) |
| Capacity, B(A) monotone across 35 valid rungs | Supported with qualification (near-ruined comparator; dirty-tree manifest; Tier A/B not fully explained) |
| Sharpe-point capacity gains; "cap never hurts" | **Withdrawn** / **blocked** |
| `lt_share` zero under flat regimes | Supported as run (80 rows); India's 0.5928 from an untracked local file |
| Tax channel ordered by statute type (decile book, all three countries) | Supported with qualification; optimised-book match and turnover ordering not usable |
| Design axes undetectable at this power (0/42 capped DEU and IND) | Supported as run; Japan's conditioning axis exploratory |
| Coverage-asymmetry failure | Supported as a worked failure (the result itself retracted) |
| Revised (Phase C) analysis | **Blocked**, not run, no revised number exists |

Traceability defects found by this audit (new): Germany's after-tax inference row exists in no artifact; the `HORSE_RACE_DECILE_PANEL*` attachments (including the one named `_COV`) both contain the non-compliant ladder; the gross-signal t-statistics and section 6.2.5 capped-book t-statistics have no committed table; no tracked India or Germany $1bn after-tax summary; the paper cites `AHV2025` while the bibliography key is `AHV2023`; tax-literature records are missing from the bibliography.

## 5. Manuscript candidate

`submission_candidate_as_run_only/manuscript.md`. **Build status:** no TeX or pandoc toolchain exists in this environment, so no PDF was compiled and no journal template applied. `python tools/check_submission_candidate.py` passes (citations resolve to bibliography entries identical to the project's; artifact hashes match; headline numbers re-derive from committed CSVs; Table/Figure references and figure files resolve; required disclosures present; banned wording absent). This is a consistency check, not scientific validation.

## 6. Remaining mandatory tasks, ordered by dependency and importance

| # | Task | Class |
|---|---|---|
| 1 | Decide how the as-run exit treatment is to be disclosed or bounded, given the revised analysis cannot run | AUTHOR_DECISION_REQUIRED |
| 2 | Resolve Germany's headline: authorise a tracked, hashed regeneration of the after-tax inference output (a regeneration of historical statistics; not done here), or leave Germany out | AUTHOR_DECISION_REQUIRED |
| 3 | Obtain tracked snapshots for India's `lt_share` and the optimised-book summaries currently only in git-ignored `outputs/` | MUST_FINISH_BEFORE_SUBMISSION |
| 4 | Read Avramov-Cheng-Metzker (Management Science 2023) and other abstract-level rows in full; add verified bibliography records for the tax literature | MUST_FINISH_BEFORE_SUBMISSION (external access to the papers) |
| 5 | Countersignatures of 001A-001D, the status of 001E, and Maham's acknowledgement of the exit ruling's consequences | EXTERNAL_DEPENDENCY |
| 6 | Choose journal and format; apply template; authors, affiliations, data-availability statement, abstract length; compile a PDF | MUST_FINISH_BEFORE_SUBMISSION |
| 7 | Cost-calibration sensitivity (S0/S1/S2), borrow-fee sweep, compliant value-weighting re-run, finite-unit capacity reformulation | AUTHOR_DECISION_REQUIRED (each is a new run; none was authorised) |
| 8 | Phase C revised analysis | BLOCKED_UNDER_CURRENT_DATA |
| 9 | Remaining evidence-map conflicts L5-L8 in the historical documents; `handoff/21` still quotes superseded figures | OPTIONAL_IMPROVEMENT (internal records; the candidate does not depend on them) |
| 10 | Contribution strength: even narrowed, the paper corroborates published work; venue order is an author call | AUTHOR_DECISION_REQUIRED |

## 7. External dependencies and author decisions

* Decisions: (a) exit-treatment disclosure (item 1); (b) whether to authorise the Germany regeneration (item 2); (c) which new runs, if any, to authorise (item 7); (d) venue and framing (item 10).
* External: Maham's acknowledgement and countersignatures; vendor access and documentation for any data-recovery work; full texts of the closest prior art.

## 8. Tests and validation (actual commands and results)

| Check | Command | Result |
|---|---|---|
| Full suite | `python -m pytest tests -o addopts="" -p no:cacheprovider -q -rfE` on the working tree after the candidate, tools, tests and README changes and before this report was added | **681 passed, 0 failed, 337 warnings, 485 s**; log `C:/Temp/claude/full_suite_completion_2026-10-14.log` |
| Focused | `python -m pytest tests/tools tests/docs_hygiene -q` after the final edits | **50 passed** (tests/tools plus tests/docs_hygiene), run after the final edits including this report |
| Withdrawn-claims screen | `python tools/check_withdrawn_claims.py` | PASS after the final edits (a screen, not verification) |
| Candidate check | `python tools/check_submission_candidate.py` | PASS |
| Whitespace | `git diff --check` | clean apart from CRLF warnings |

Passing tests establish that the code and checks behave as written; they do not validate any scientific claim and do not establish reproducibility.

## 9. Outstanding limitations affecting validity

Unknown sensitivity of every as-run number to the exit treatment; a comparator that is infeasible or near-ruined; low design power (8 cells, 132 months); endogenous turnover and n = 3 jurisdictions; modelled borrow; cost-calibration sensitivity not run; amendments not countersigned; some numbers resting on untracked or missing artifacts (listed in the matrix); no external review; raw vendor and staging files are not available, so upstream audits cannot be re-verified.

## 10. Exact condition for reopening Phase C

All of: (1) external vendor access by someone entitled to it, with the vendor's own documentation for `prcstd`/`r_prc_stat`, `trfd`, `ajexdi` and corporate-action and terminal-event fields stored in the repository; (2) a month-level, aggregate-only, value-free flag query for the gap months (counts by status class and month-end flag) whose result shows genuine observations for the gap months; (3) written authorisation from the ruling owners for that query; (4) a dated addendum, committed before any reconstruction rule is adopted or any revised result is read. A ruling to liquidate departing holdings at a certified cost is a different route and needs its own addendum. See `docs/PHASE_C_RUN_READINESS_V2_2026-10-14.md` section 8.
