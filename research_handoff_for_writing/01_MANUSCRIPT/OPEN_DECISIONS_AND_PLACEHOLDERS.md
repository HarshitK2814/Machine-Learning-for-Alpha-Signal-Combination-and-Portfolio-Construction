# Open author decisions and placeholders

Extracted from `submission_candidate_as_run_only/SUBMISSION_PREPARATION.md`. Nothing here is decided and no author detail may be invented; the writer leaves these as placeholders for the authors.

The manuscript candidate itself states that authors, affiliations and acknowledgements are not filled in, that it is not submission-ready, that venue selection is open and that amendments are not countersigned.

## 3. Fields requiring author confirmation (none is filled or inferred)

| Field | State |
|---|---|
| Author names, order, affiliations, corresponding author, ORCIDs | not set; do not infer from repository activity or from the workstream owners named in project documents |
| Author contributions (e.g. CRediT roles) | not set |
| Acknowledgements and funding | not set; the data workstream and statistical review are named in internal documents, but no one has agreed to be acknowledged |
| Competing interests / conflicts | not set |
| Preregistration statement | see section 5 of this document |
| Data availability statement | draft below, needs authors' and data-licence confirmation |
| Code availability statement | draft below, needs authors' confirmation |
| Ethics / AI-use / preprint-server statements | depend on the chosen venue's policies; not assessed |
| Co-author acknowledgement of the exit ruling and of the narrowed framing | outstanding; not claimed |


## 4. Draft availability wording (conservative; to be confirmed, not asserted)

**Data (draft).** "The empirical panels (security universe, signals, forward returns, cost inputs and tax-regime tables for Germany, India and Japan) were built by a separate data workstream from licensed commercial data and are not distributed with the code. The raw vendor extracts and intermediate staging files are not held in the project repository. Verbatim copies of the derived result tables used in this paper are in the repository under `docs/attachments/` and `results/`, with SHA-256 hashes in `submission_candidate_as_run_only/TRACEABILITY.csv`." **[Authors must confirm (a) the licence terms for the derived tables, (b) whether any of them may be redistributed, (c) the access route for the underlying data.]**

**Code (draft).** "The analysis code is in the project's Git repository (remote: `HarshitK2814/Machine-Learning-for-Alpha-Signal-Combination-and-Portfolio-Construction` on GitHub; the repository's README describes it as public, which we have not verified). The results reported here were produced by earlier commits of this repository under settings recorded in the project documentation; run-time hashes of the code and of some weight files were not recorded, so exact reproduction from the repository alone is not guaranteed (see Section 7 of the manuscript)." **[Authors must confirm (a) that the repository is public and may remain so, (b) a licence (the repository currently has no LICENSE file), (c) a release tag or archive DOI if the venue requires one.]** Do not state that code or data "will be made available" until the permissions and the distribution plan are confirmed.


## 6. Author decision register (2026-10-14)

Statuses: `AUTHOR DECISION REQUIRED`, `EXTERNAL DEPENDENCY`, `COMPLETE`. Nothing below has been decided for the authors and no author detail is invented. The same register is kept in `docs/PROJECT_COMPLETION_REPORT.md`.

| # | Item | Status | What is needed |
|---|---|---|---|
| 1 | Venue selection | AUTHOR DECISION REQUIRED | Section 1; read the live instructions of the chosen journal |
| 2 | Author list, order, affiliations, corresponding author, contributions | AUTHOR DECISION REQUIRED | Not set; not inferred from repository activity |
| 3 | Acknowledgements, funding, conflicts of interest | AUTHOR DECISION REQUIRED | No one has agreed to be acknowledged |
| 4 | Data availability: vendor-licence terms and which derived tables may be shared | AUTHOR DECISION REQUIRED / EXTERNAL DEPENDENCY | Licence terms are with the data vendor and the data workstream |
| 5 | Code availability: repository visibility, licence file, permission of every contributor | AUTHOR DECISION REQUIRED | The repository's public status was not verified |
| 6 | Accept the permanently qualified exit-treatment disclosure (sensitivity unknown; Phase C blocked) | AUTHOR DECISION REQUIRED | Alternative is vendor access and a dated addendum (external) |
| 7 | Submit the narrowed manuscript despite its modest contribution, or first read the remaining tax and international papers | AUTHOR DECISION REQUIRED | Eight cited works remain unread (`docs/FINAL_PRIOR_ART_REVIEW.md` section 8) |
| 8 | Seek reviewer or coauthor comments; request countersignature or acknowledgement of amendments 001A-001E and of the exit ruling | AUTHOR DECISION REQUIRED | None exists; none is claimed |
| 9 | Any separate authorisation for a narrowly defined descriptive calculation scoring 001C's P1, P3, P4 or P5 (definitions fixed in writing first) | AUTHOR DECISION REQUIRED | Otherwise they stay `NOT_SCOREABLE` |
| 10 | Library or publisher access to the unread papers | EXTERNAL DEPENDENCY | Section 3 of the prior-art review |
| 11 | LaTeX environment (Overleaf or local TeX) and the venue template | EXTERNAL DEPENDENCY | Section 2; no PDF exists |
| 12 | Vendor access and documentation for the Phase C month-level flag query | EXTERNAL DEPENDENCY | Phase C stays blocked and unrun |
| 13 | 001C Japan scorecard recorded and reported in the manuscript (P2 not met; P1, P3, P4, P5 not scoreable) | COMPLETE | `docs/AMENDMENT_001C_JAPAN_PREDICTION_SCORECARD.md` |
| 14 | ACM full-text comparison and candidate wording check | COMPLETE | `docs/FINAL_PRIOR_ART_REVIEW.md` section 1 |
| 15 | Follow-up literature search (five more works read; eight unreadable) | COMPLETE | Section 8 of the prior-art review |
| 16 | Venue comparison from official sources (via search summary; direct fetch blocked) | COMPLETE as far as accessible | Section 1 |

