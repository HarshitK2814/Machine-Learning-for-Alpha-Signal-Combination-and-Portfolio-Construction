# Project completion report (updated 2026-10-14, after the technical research-completion and publication-assets sprint)

Internal researcher-led report; not an external review. No approval by Maham or Absar beyond their documented responses is claimed; Maham's acknowledgement of the exit ruling is outstanding and 001A-001E are not countersigned. Sprint history on `feat/completion-sprint-2026-10-14`: `24e9a4c` (start) -> `f295d3d` (sprint 1) -> `5f206fd` (sprint 2) -> `8ad2f3c` (lockdown) -> novelty-gate and 001C-scorecard sprint (`53a04b3`) -> bounded submission sprint (`807fb3a`: follow-up literature search, venue comparison, decision register) -> technical sprint (this update: Gate 1 coding-readiness audit, `paper_assets_as_run_only/`).

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

**Update (novelty-gate sprint): amendment 001C scorecard** (`docs/AMENDMENT_001C_JAPAN_PREDICTION_SCORECARD.md`). Of the five Japan predictions, **P2 is `NOT_MET`** (Japan's net Sharpe at $1bn, cell mean 0.0568 and composite 0.0550, against the amendment's fixed threshold of +0.128; descriptive, no test); **P1, P3, P4 and P5 are `NOT_SCOREABLE`** from committed artifacts (incomplete definitions and diagnostics that were never committed; no substitution was made). Of the amendment's own whole-hypothesis falsification conditions, a non-monotone Japanese net Sharpe across $100mn, $1bn and $10bn is met, rising cost drag is not met, and the joint P2-and-P4 condition is indeterminate. The candidate reports this and does not call Japan a confirmation. The earlier claim that Japan was "a pre-registered out-of-sample confirmation" remains superseded.

## 3. Prior-art status (`docs/FINAL_PRIOR_ART_REVIEW.md`)

Full texts (some version) read for Azevedo et al., Novy-Marx and Velikov, Korajczyk and Sadka, Jensen et al., Gârleanu and Pedersen, Gu et al., Chen and Velikov (working paper), Liao et al., and, since the novelty-gate sprint, **Avramov-Cheng-Metzker (the published article from the author-hosted PDF, accessed 2026-10-14; the PDF is not committed and the online appendix was not accessed)**. The detailed comparison and per-statement statuses (`SUPPORTED_BY_COMPARISON`, `NARROW_REQUIRED`, `UNRESOLVED_PRIOR_ART`, `REMOVE`) are in `docs/FINAL_PRIOR_ART_REVIEW.md` section 1: that paper has no AUM-indexed cost, capacity, participation constraint, tax or non-US analysis, but a new geography is a difference in coverage, not a method, and the candidate's novelty wording was narrowed accordingly. Statements that depend on the unread tax and international papers remain `UNRESOLVED_PRIOR_ART`. Bibliographic metadata for all 21 candidate entries were verified against Crossref or arXiv where reachable (`BIB_PROVENANCE.csv`); two project-record errors (BY2003 DOI, HUANG2019 arXiv id) were not propagated.

**Follow-up search (bounded submission sprint, 2026-10-14; detail in `docs/FINAL_PRIOR_ART_REVIEW.md` section 8).** Read in full: Choi-Jiang-Zhang (international ML, 32 markets incl. Japan and India; March 2023 working paper; gross of costs; no capacity or tax; the published RAPS article was not read), Israel-Moskowitz, Krasner-Sosner (published article), Moehle et al. (2021 author version; lot-level tax-aware construction, so the lot-level engine is a tool, not a contribution) and Huang. **Still unreadable:** Cakici et al. (CAPTCHA, not bypassed), Chen-Hanauer-Kalsbach (SSRN 403), Lalwani et al. (403), Novy-Marx-Velikov 2019, Sialm-Sosner and Berkin-Ye (publisher-restricted), Chaudhuri et al. (empty response), Dai et al. (bot protection). The candidate now says exactly this; its novelty wording was not strengthened. Choi et al. was added to the bibliography (22 entries).

## 4. Is the central contribution defensible?

As a narrow non-US as-run measurement with a methods caution: yes, on the evidence that is traceable, and with the qualifications stated. It adds no mechanism and no method; the AUM dimension is established for the US by Jensen et al.; the capacity object is an accounting difference against an infeasible comparator; the zero long-term share under flat statutes is mechanical; the design null is a low-power bound; and every number carries an unresolved exit-treatment qualification. Whether it is publishable, and where, is an author decision. The comparison against Avramov-Cheng-Metzker is done and no overlap was found in AUM, capacity, tax or non-US scope; no methodological novelty remains, and eight cited works are still unread.

## 5. Submission-dependency checklist

### Work completed and evidenced

* Claim-evidence matrix with a registration-terminology audit; publication-path decision and reassessment; numerical traceability audit with verbatim snapshots; prior-art review with a provisional-claims table; candidate with 21-entry verified bibliography, traceability hashes and a consistency check (11 tests that inject defects); venue shortlist and build notes (`SUBMISSION_PREPARATION.md`); withdrawn-claims screen covering the candidate.

### MUST_FINISH_BEFORE_SUBMISSION

| # | Task | State |
|---|---|---|
| 1 | ~~Obtain and read Avramov-Cheng-Metzker's full text~~ **done 2026-10-14** (online appendix not accessed). Remaining: read the abstract-level works and tax papers (item 2) and re-check statements 3, 4, 9 and 11 of the review | partly done |
| 2 | Read the abstract-level works and the tax papers in full; replace abstract-level wording | open (some need library access) |
| 3 | Authors decide the scoring of 001C's four unscored Japan predictions (P1, P3, P4, P5) and how the manuscript reports the outcome; P2 is scored `NOT_MET` | open (scorecard decisions below) |
| 4 | Convert the Markdown to the chosen venue's template and compile; check cross-references in the converted file | blocked: no TeX/Pandoc, no template chosen |
| 5 | Fill author, affiliation, contribution, acknowledgement, funding, conflict, data/code availability and any venue-required statements | author decisions |
| 6 | Re-run the candidate check, screens and tests on the final text | done for the current text; repeat after any edit |

### Author decision register (single source: the same table is in `submission_candidate_as_run_only/SUBMISSION_PREPARATION.md` section 6)

Statuses: `AUTHOR DECISION REQUIRED`, `EXTERNAL DEPENDENCY`, `COMPLETE`. Nothing is decided for the authors; no author detail is invented.

| # | Item | Status |
|---|---|---|
| 1 | Venue selection (three-venue comparison, `SUBMISSION_PREPARATION.md` section 1; each journal's live instructions must be read first) | AUTHOR DECISION REQUIRED |
| 2 | Author list, order, affiliations, corresponding author, contributions | AUTHOR DECISION REQUIRED |
| 3 | Acknowledgements, funding, conflicts of interest | AUTHOR DECISION REQUIRED |
| 4 | Data availability (vendor-licence terms; which derived tables may be shared) | AUTHOR DECISION REQUIRED and EXTERNAL DEPENDENCY |
| 5 | Code availability (repository visibility, licence file, permissions) | AUTHOR DECISION REQUIRED |
| 6 | Accept the permanently qualified exit-treatment disclosure | AUTHOR DECISION REQUIRED |
| 7 | Submit the narrowed manuscript despite its modest contribution, or first read the eight unread works | AUTHOR DECISION REQUIRED |
| 8 | Reviewer or coauthor comments; countersignature or acknowledgement of 001A-001E and of the exit ruling (none exists; none claimed) | AUTHOR DECISION REQUIRED |
| 9 | Separate authorisation, with definitions fixed in writing first, for a narrowly defined descriptive calculation scoring any of 001C's P1, P3, P4, P5 | AUTHOR DECISION REQUIRED |
| 10 | Whether Germany's historical statistic is ever regenerated (currently declined); whether cost-calibration or finite-unit runs are ever added | AUTHOR DECISION REQUIRED |
| 11 | Library or publisher access to the unread works | EXTERNAL DEPENDENCY |
| 12 | TeX or Overleaf environment and the chosen venue's template (no PDF exists) | EXTERNAL DEPENDENCY |
| 13 | Vendor access and documentation for Phase C (blocked, unrun) | EXTERNAL DEPENDENCY |
| 14 | 001C Japan scorecard recorded and reported (P2 `NOT_MET`; P1, P3, P4, P5 `NOT_SCOREABLE`; whole-hypothesis conditions reported separately; wording verified verbatim against the amendment) | COMPLETE |
| 15 | ACM full-text comparison and candidate-wording check | COMPLETE |
| 16 | Follow-up literature search and venue comparison, to the extent accessible | COMPLETE (limits recorded) |

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
| Focused tests | `python -m pytest tests/tools tests/docs_hygiene -o addopts="" -p no:cacheprovider -q` | 69 passed (tools 55, docs_hygiene 14), run again this sprint |
| Full suite (single invocation) | `python -m pytest tests -o addopts="" -p no:cacheprovider -q -rfE` | **not run this sprint** (the last attempt was stopped for memory); replaced by the sequential batches in section 8a: 699 passed across 13 directories |
| Whitespace | `git diff --check` | clean apart from CRLF warnings |
| Manuscript build | none possible | no TeX/Pandoc, no template |

## 8. Final validation record

The full suite ran on the tree after all code, test and candidate edits; the report's final wording and the commits are documentation-only. Passing tests show that code and checks behave as written; they do not validate any scientific claim or establish reproducibility.

## 8a. Technical sprint: Gate 1 coding-readiness result and publication assets

**Gate 1 result: PASSED for the currently authorised as-run outputs, with explicit limits.** No experiment, training, A2, cost sensitivity, capacity, optimisation or Phase C step was run; no scientific method, threshold or result-generation logic was changed.

*Retained outputs, their producing code, inputs and tests.*

| Retained output (candidate) | Tracked artifact | Producing code | Upstream inputs | Tests / checks |
|---|---|---|---|---|
| Cost-input coverage (Section 3), 560-series input-support counts | `results/phase_c_census_v3_2026-10-14/` | `tools/phase_c_input_census_v3.py` | frozen C1/C4/C6 panels and weight files (untracked, licensed) | `tests/tools/test_phase_c_input_census_v3.py` |
| Matched-book outcomes and channels (Table 1) | `docs/attachments/MATCHED_BOOK_*` | `tools/exp_matched_book_accounting.py` | saved decile weights (untracked `outputs/`) | candidate checker re-derivation; `tests/validation/test_output_guard_extended.py` |
| B(A), solvency, terminal wealth (Table 2, Figures 1-2) | `results/capacity_return_difference/` (Tier A, Tier B, monthly series, manifest) | `tools/exp_capacity_return_difference.py` (stages snapshot, pipeline, tables), `tools/make_figures.py` | wedge-tool series snapshotted into the tracked folder; pipeline stage needs frozen data | `tests/validation/test_capacity_return_difference.py`, `test_make_figures.py`; figures regenerate byte-identically from tracked inputs (checked this sprint) |
| Design axes and power (Section 5.4) | `docs/attachments/DESIGN_IDENTIFIABILITY_*`, `GATE2_POWER_*` | `tools/exp_design_identifiability.py`, `tools/gate2_power.py` | untracked cell series | `tests/validation/test_inference_audit.py`, `test_output_guard_*` |
| Stage-06 summaries, lt share, Japan rungs (Sections 5.2-5.3) | `docs/attachments/SUMMARY_AFTER_TAX_*` (verbatim snapshots) | `pipelines/06_after_tax_eval.py` | saved weights (untracked) | `tests/tax/`; candidate checker re-derivation |
| Japan after-tax composite inference | `docs/attachments/AFTER_TAX_INFERENCE_1E9_*` | `tools/exp_after_tax_inference.py` | summaries and weights | `tests/validation/test_inference_audit.py` |
| Statute rates for Germany and Japan | `src/alphacomb/tax/jurisdictions.py` | (configuration) | none | `tests/tax/` |

*Static audit.* No TODO, FIXME, NotImplemented or XXX marker in `src/`, `tools/` or `pipelines/`. A static check that every column of each retained artifact is produced by its named script found no mismatch; the German stage-06 snapshot has 24 columns against 25 for the others because an older script version produced it (documented earlier; not a defect to fix).

*Defect found and fixed.* `tests/tax/exit_fixtures.py` defined a configuration helper named `test_cfg`, which pytest collected as a test (it returned a dict and raised `PytestReturnNotNoneWarning`; under `-W error` it failed). It was renamed `build_cfg` in the fixture module and its two callers. No assertion was lost: it asserted nothing. This removes one phantom test from the count.

*Limits that remain (not coding defects).* (1) The heavy stages need untracked, licensed data, so the as-run CSVs cannot be regenerated from a clean checkout; what a clean checkout can regenerate is the checker, `tools/make_figures.py` and `tools/make_paper_assets.py`. (2) Run-time hashes of code and weights were not recorded for the 2026-10-09 outputs, and the German and Indian summary snapshots rest on weight identity recovered from the weights index. (3) Phase C, the 560 non-estimable series, the Germany inference statistic and the exit-treatment sensitivity remain blocked or unknown; none is a coding task.

*New code this sprint.* `tools/make_paper_assets.py` (presentation layer; verifies source hashes against `TRACEABILITY.csv`, uses only tracked CSVs, hardcodes no result values) and `tests/tools/test_make_paper_assets.py` (15 tests: byte-identical double build, manifest coverage, hash mismatch refusal, PNG dimensions, solvent-only plotting, insolvent rungs listed as n/a, no interpolation of India's single rung, banned-claim scan, 560 series with no estimable tier). `tools/check_withdrawn_claims.py` now also scans `paper_assets_as_run_only/`.

**Gates 2-5: `paper_assets_as_run_only/` created** (Gate 1 passed first). 8 figures (4 main text, 4 supplementary; PDF, SVG and 300-dpi PNG each) and 8 tables (3 main text, 5 supplementary; CSV, LaTeX and Markdown each), catalogued with source paths, SHA-256 hashes, captions, limitations and a scientific-review note in `paper_assets_as_run_only/ASSET_CATALOG.md`; output hashes in `ASSET_MANIFEST.csv`. Two consecutive builds into different folders produced identical manifests. Every rendered PNG was inspected directly and corrected (overlapping labels, clipped notes, unreadable symlog ticks, legend collisions). Candidates not built (Germany inference, anything Phase C, India across AUM, Japan P1/P3/P4/P5 diagnostics, long-term-share plot, scorecard chart, unapproved attachments, duplicate restyles) are listed with reasons. Findings worth the authors' notice: India's cost-input coverage collapses in 2009-10 (1 of 274 in-universe securities certified), which is inside the mean of 0.989 quoted in Section 3 and is now annotated; `FIG_S4` is `DIAGNOSTIC_ONLY`.

*Validation this sprint.* Sequential, non-overlapping batches over every test directory (`python -m pytest <dir> -o addopts="" -p no:cacheprovider -q -rfE`, one directory at a time, no parallel workers): tools 55, docs_hygiene 14, validation 210, tax 117, portfolio 50, risk 6, theory 33, models 78, interpret 5, contracts 76, adaptive 15, synthetic 5, c14 35 = **699 passed, 0 failed** (the previous 685 minus the one phantom test, plus 15 new asset tests); log `C:/Temp/claude/batches_2026-10-14.log`. These batches together cover every test file under `tests/`; they are reported as batches, not as a single full-suite invocation.

## 9. Outstanding limitations affecting validity

Unknown sensitivity of every as-run number to the exit treatment; a comparator that is infeasible or near-ruined; low design power (8 cells, 132 months); endogenous turnover and n = 3 jurisdictions; modelled borrow; cost-calibration sensitivity not run; amendments not countersigned and 001C unscored; the closest prior art unread; Germany's optimised-book inference excluded; weight identities for the Germany and India $1bn summaries inferred and no run-time hashes; no external review; raw vendor and staging files unavailable.
