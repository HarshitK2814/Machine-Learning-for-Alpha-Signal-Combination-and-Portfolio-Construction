# Project completion report (updated 2026-10-14, after the manuscript-lockdown sprint)

Internal researcher-led report; not an external review. No approval by Maham or Absar beyond their documented responses is claimed; Maham's acknowledgement of the exit ruling is outstanding and 001A-001E are not countersigned. Sprint history on `feat/completion-sprint-2026-10-14`: `24e9a4c` (start) -> `f295d3d` (sprint 1) -> `5f206fd` (sprint 2) -> lockdown sprint (this update).

**Overall state: not submission-ready.** A narrowed, internally consistent, traceable as-run candidate exists. It is blocked from submission by prerequisites that need external access or author decisions (below); passing the available checks does not change that.

## 1. Candidate location and build status

* **Candidate:** `submission_candidate_as_run_only/` (`manuscript.md`, `references.bib`, `BIB_PROVENANCE.csv`, `TRACEABILITY.csv`, `README.md`, `SUBMISSION_PREPARATION.md`). The original paper and every historical document are unchanged.
* **Build status:** **no PDF exists.** No TeX distribution or Pandoc is installed (`pdflatex`, `xelatex`, `latexmk`, `tectonic`, `pandoc` absent; no MiKTeX or TeX Live directory) and no venue template is selected. Nothing was installed. The reproducible check is `python tools/check_submission_candidate.py` (citations, hashes, re-derived numbers, cross-references, disclosures, banned wording); it does not read any converted LaTeX. Exact remaining build steps and an Overleaf workflow are in `submission_candidate_as_run_only/SUBMISSION_PREPARATION.md` section 2.

## 2. What the lockdown sprint did

| Decision applied | Effect |
|---|---|
| Germany's untraceable inference statistic: **not regenerated, excluded** | Excluded from the candidate with any inferential statement about Germany's optimised book (manuscript sections 5.1, 5.3, 7). Traceability record retained and the omission recorded in `docs/FINAL_NUMERICAL_TRACEABILITY_GAPS.md` section 4. Germany's independently traceable stage-06 summary values (net +0.128, after-tax +0.017, turnover 0.0135, tax drag 6.38 bps; cell means, no test statistics) are kept as descriptive values and re-derived by the checker |
| Exit-treatment sensitivity: disclosure retained | Unknown, with no inference about direction or size; exit policy untouched |
| Cost-calibration and finite-unit capacity runs: not run, out of scope | The candidate drops "no mandate size at which the cap hurts" and reports capacity only as B(A), an accounting difference; `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md` shows neither run is essential to a retained central claim (C4 and C9 stay BLOCKED and omitted) |
| Registration terminology audited | `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md` section 6 lists every term, decision and source commit. "Pre-registered", "pre-specified" and "confirmatory" are used for no reported result; the registration history is described with dates, self-filed status and no countersignature; B(A), the design ladder, the tax-channel comparison and the 8-cell restriction are stated as post hoc; **Japan is no longer presented as a confirmation** |
| Phase C | blocked and unrun; no recovery work reopened |

Further manuscript consistency fixes: removed "real" for the gross signal (the gross t-statistics are untraceable); removed an unsupported attribution of the cost-model choice to the capacity literature; stated that the capped-slack remark rests only on a Sharpe-unit ladder not reported; qualified the retraction narrative as recorded in the project note; sourced the statutory rates (`src/alphacomb/tax/jurisdictions.py`) and the breadth cap (amendment 001B) and said neither was independently re-verified; added the provenance and the sensitivity caveats for the Germany and India summaries.

**Finding the authors must see:** amendment 001C required that its five Japan predictions be scored and failures reported prominently. No scoring record exists in the repository. On the committed summaries the second prediction (Japan's net Sharpe at $1bn above Germany's +0.128) does not appear to hold (Japan +0.057). The candidate says so and does not call Japan a confirmation. The earlier sprint's claim that Japan was "a pre-registered out-of-sample confirmation" (and the evidence-map wording behind it) is superseded.

## 3. Prior-art status (`docs/FINAL_PRIOR_ART_REVIEW.md`)

Full texts (some version) read for Azevedo et al., Novy-Marx and Velikov, Korajczyk and Sadka, Jensen et al., Gârleanu and Pedersen, Gu et al., Chen and Velikov (working paper) and Liao et al. **Avramov-Cheng-Metzker's full text was not accessible and was not reviewed**; every statement about it is abstract-level and the candidate says so. Section 7 of the review lists which novelty statements remain **provisional** (those that depend on that comparison and on the abstract-level tax and international sources). No further novelty claim was drafted to work around inaccessible texts. Bibliographic metadata for all 21 candidate entries were verified against Crossref or arXiv where reachable (`BIB_PROVENANCE.csv`); two project-record errors (BY2003 DOI, HUANG2019 arXiv id) were not propagated.

## 4. Is the central contribution defensible?

As a narrow non-US as-run measurement with a methods caution: yes, on the evidence that is traceable, and with the qualifications stated. It adds no mechanism and no method; the AUM dimension is established for the US by Jensen et al.; the capacity object is an accounting difference against an infeasible comparator; the zero long-term share under flat statutes is mechanical; the design null is a low-power bound; and every number carries an unresolved exit-treatment qualification. Whether it is publishable, and where, is an author decision; the central novelty comparison against Avramov-Cheng-Metzker is not done.

## 5. Submission-dependency checklist

### Work completed and evidenced

* Claim-evidence matrix with a registration-terminology audit; publication-path decision and reassessment; numerical traceability audit with verbatim snapshots; prior-art review with a provisional-claims table; candidate with 21-entry verified bibliography, traceability hashes and a consistency check (11 tests that inject defects); venue shortlist and build notes (`SUBMISSION_PREPARATION.md`); withdrawn-claims screen covering the candidate.

### MUST_FINISH_BEFORE_SUBMISSION

| # | Task | State |
|---|---|---|
| 1 | Obtain and read Avramov-Cheng-Metzker's full text; re-check every provisional novelty statement (review section 7) | blocked on access |
| 2 | Read the abstract-level works and the tax papers in full; replace abstract-level wording | open (some need library access) |
| 3 | Authors score amendment 001C's five Japan predictions formally and decide how the manuscript reports the outcome | open (finding in section 2) |
| 4 | Convert the Markdown to the chosen venue's template and compile; check cross-references in the converted file | blocked: no TeX/Pandoc, no template chosen |
| 5 | Fill author, affiliation, contribution, acknowledgement, funding, conflict, data/code availability and any venue-required statements | author decisions |
| 6 | Re-run the candidate check, screens and tests on the final text | done for the current text; repeat after any edit |

### AUTHOR_DECISION_REQUIRED

| ID | Decision |
|---|---|
| A | Journal and template. Shortlist with evidence status: `SUBMISSION_PREPARATION.md` section 1 (official author instructions were not retrievable: HTTP 403; verify on each journal's site) |
| B | Author list, order, affiliations, contributions, acknowledgements, funding, conflicts of interest |
| C | Data and code availability: licence terms for the derived tables, whether the repository is public and may remain so, a licence (none exists), a release tag or archive. Draft conservative wording and the confirmations it needs: `SUBMISSION_PREPARATION.md` section 4. Nothing may be stated as "will be made available" until confirmed |
| D | Whether to submit now or only after items 1-3 above |
| E | Whether to accept the "exit-treatment sensitivity unknown" disclosure permanently, or to rule on a different treatment (a different ruling needs its own addendum and is not implied here) |
| F | Whether a future reproduction of Germany's historical statistic is ever wanted (conditions are recorded in the traceability document; currently declined) |
| G | Whether the cost-calibration or finite-unit capacity runs should ever be added; they would be needed only for a stronger capacity claim than the candidate makes |

### EXTERNAL_DEPENDENCY

* Library or publisher access to the closest prior art; Maham's acknowledgement of the exit ruling's consequence and the countersignatures of 001A-001D (001E draft status); journal author instructions that were not retrievable; a TeX distribution or Overleaf account for the build; vendor access and documentation for any data-recovery work.

### OPTIONAL_IMPROVEMENT

* Remaining evidence-map conflicts L5-L8 in the historical documents; `handoff/21` still quotes superseded figures; extending `research/_build` so the generated project bibliography includes the corrected entries; borrow-fee sweep and compliant value-weighting re-run (each a new run, not authorised).

### BLOCKED_UNDER_CURRENT_DATA

* Phase C revised analysis (560 series not estimable; vendor coverage `unknown`).

## 6. Exact condition for reopening Phase C

All of: (1) external vendor access by someone entitled to it, with the vendor's own documentation for `prcstd`/`r_prc_stat`, `trfd`, `ajexdi` and the corporate-action and terminal-event fields stored in the repository; (2) a month-level, aggregate-only, value-free flag query for the gap months whose result shows genuine observations; (3) written authorisation from the ruling owners; (4) a dated addendum, committed before any reconstruction rule is adopted or any revised result is read. A ruling to liquidate departing holdings at a certified cost is a different route and needs its own addendum. See `docs/PHASE_C_RUN_READINESS_V2_2026-10-14.md` section 8.

## 7. Tests and validation (actual commands and results)

| Check | Command | Result |
|---|---|---|
| Candidate checker | `python tools/check_submission_candidate.py` | PASS (consistency only) |
| Withdrawn-claims screen | `python tools/check_withdrawn_claims.py` | PASS (a screen, not verification) |
| Focused tests | `python -m pytest tests/tools tests/docs_hygiene -q` | 53 passed |
| Full suite | `python -m pytest tests -o addopts="" -p no:cacheprovider -q -rfE` | **684 passed, 0 failed, 337 warnings, 230 s**; log `C:/Temp/claude/full_suite_lockdown_2026-10-14.log` |
| Whitespace | `git diff --check` | clean apart from CRLF warnings |
| Manuscript build | none possible | no TeX/Pandoc, no template |

## 8. Final validation record

The full suite ran on the tree after all code, test and candidate edits; the report's final wording and the commits are documentation-only. Passing tests show that code and checks behave as written; they do not validate any scientific claim or establish reproducibility.

## 9. Outstanding limitations affecting validity

Unknown sensitivity of every as-run number to the exit treatment; a comparator that is infeasible or near-ruined; low design power (8 cells, 132 months); endogenous turnover and n = 3 jurisdictions; modelled borrow; cost-calibration sensitivity not run; amendments not countersigned and 001C unscored; the closest prior art unread; Germany's optimised-book inference excluded; weight identities for the Germany and India $1bn summaries inferred and no run-time hashes; no external review; raw vendor and staging files unavailable.
