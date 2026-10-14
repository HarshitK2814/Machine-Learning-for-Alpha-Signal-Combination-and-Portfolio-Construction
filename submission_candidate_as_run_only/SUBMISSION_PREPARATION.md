# Submission preparation (2026-10-14): venues, build, author fields, availability wording

Internal preparation material for the authors. It selects nothing: venue, authorship, permissions and every statement that needs someone's confirmation are author decisions. Nothing here asserts that code or data will be public. Evidence status is stated for each fact: **retrieved** (read from the named page today), **secondary** (a third-party or search-result description), or **not retrieved** (the official page returned HTTP 403 or was not found).

## 1. Venue comparison for the narrowed contribution (at most three; not a recommendation)

The contribution (see `docs/FINAL_PUBLICATION_PATH.md` section 7): a narrow, as-run, non-US measurement with a methods caution; no new method or mechanism; a permanently qualified exit-treatment disclosure; and a prior-art comparison that is complete for the US capacity literature and the closest ML-cost paper but still provisional for four tax papers and several international papers (`docs/FINAL_PRIOR_ART_REVIEW.md`). Fit notes are about subject matter only; none estimates the chance of acceptance.

**Evidence status, applied to every row.** Access date for all rows: **2026-10-14**. Direct fetches of the official ScienceDirect and Taylor & Francis pages returned **HTTP 403**, so no official page was read directly. The quoted facts below are the official pages' text **as summarised by a web-search tool restricted to the publishers' own domains** (labelled *official, via search summary*), which is stronger than a third-party description but is not a direct read and can be stale. Facts the search did not return are marked *not verified*.

| | *Journal of Empirical Finance* (Elsevier) | *International Review of Financial Analysis* (Elsevier) | *Quantitative Finance* (Taylor & Francis) |
|---|---|---|---|
| Aims and scope | Financial economics; empirical finance read broadly, covering financial econometrics and theory with clear empirical implications; welcomes all fields of finance including asset pricing and international finance (official, via search summary) | Non-affiliated refereed journal for high-quality financial research, open to a diversity of topics and "not limited to U.S. centric topics" (official, via search summary) | Original research on quantitative methods in finance, theoretical and empirical, interdisciplinary; topics include portfolio management, market microstructure and financial econometrics; fast publication (official, via search summary) |
| Fit with the candidate | Plausible for applied empirical finance; the guide reportedly warns that about 85% of submissions are rejected and advises being conservative about where to submit, so a modest measurement paper is at risk | Plausible: international scope stated; no stated fit test beyond screening for aims and scope | Plausible if the work is framed as a quantitative implementation measurement; the candidate claims no method, which may fit a methods-oriented journal poorly |
| Article type, length | not verified | not verified | not verified |
| Template and format | Elsevier `elsarticle` class (Elsevier LaTeX page, retrieved earlier: all files in one folder, no subfolders). The Guide for Authors itself was **not read** | `elsarticle`, same note | T&F `interact` class is a common option; whether the journal requires it is **not verified** |
| Fees and open access | Submission fee US$175, non-refundable, including on desk rejection (official, via search summary). Open-access APC listed as USD 3,410 on one page and USD 3,200 on another (excluding taxes; personalised at submission); subscription route available, 24-month self-archiving embargo | Submission fee US$175, non-refundable (official, via search summary). Open-access APC listed as USD 3,920 on one page and USD 3,580 on two others (excluding taxes; personalised at submission) | Hybrid (Open Select). The search returned no figure for a submission fee and no journal-specific APC; the APC is stated to vary by journal and to be paid after acceptance. **Not verified** |
| Source URLs | https://www.sciencedirect.com/journal/journal-of-empirical-finance/publish/guide-for-authors ; https://www.sciencedirect.com/science/journal/09275398/publish/open-access-options ; https://shop.elsevier.com/journals/journal-of-empirical-finance/0927-5398 | https://www.sciencedirect.com/journal/international-review-of-financial-analysis/publish/guide-for-authors ; https://www.sciencedirect.com/journal/international-review-of-financial-analysis/publish/open-access-options | https://www.tandfonline.com/journals/rquf20/about-this-journal ; https://authorservices.taylorandfrancis.com/choose-open/publishing-open-access/open-access-cost-finder/ |

**Dropped from the earlier shortlist.** *Finance Research Letters* (a letters-length limit reported only by Wikipedia would force a drastic cut and the loss of the traceability apparatus; not verified). *Journal of International Financial Markets, Institutions & Money* and *Review of Asset Pricing Studies* (earlier notes: banking and FX weighting; poor fit for a corroborating measurement; neither re-verified). Dropping them is a fit judgement, not a finding.

**Not done, by instruction.** No journal was selected for the authors and no template was applied. Before choosing, the authors must read each journal's current instructions on its own site (article types and length, submission fee, APC, data and code policy, AI-use policy, preprint policy), which could not be retrieved here.

**Exact author choice needed.** (1) Choose one venue, or a different one, after reading its live Guide for Authors; (2) confirm the authors will pay a non-refundable submission fee if the venue charges one, and the open-access route, if any; (3) only then should the template be applied and the Section 2 build steps run.

## 2. Build readiness

* **Environment checked:** no `pdflatex`, `xelatex`, `latexmk`, `tectonic` or `pandoc` is installed on the machine that produced the candidate, and nothing was installed (a TeX distribution is a large install and no template is chosen). **No PDF exists.** Nothing below has been executed.
* **Other tools found:** Docker is installed (a TeX Live image would be a multi-gigabyte download and was not pulled without authorisation); the Python packages `markdown`, `weasyprint` and `reportlab` are installed, which could render a plain review copy of the Markdown, but that would not be a journal-formatted build and none was made. No MiKTeX, TeX Live or Pandoc directory exists in the usual install locations.
* **What a compiled version needs:** (1) a chosen venue and its class (`elsarticle` or the T&F `interact` class); (2) conversion of `manuscript.md` to LaTeX, by `pandoc` with citeproc or `--natbib`, or by hand; (3) `references.bib` (22 entries; journal volume and pages are inside the `journal` field following the project convention, so a LaTeX bibliography style will print them as part of the journal name unless the entries are reformatted); (4) the two figures `results/figures/fig1_capacity_return_difference_B.png` and `fig2_uncapped_terminal_wealth.png` copied into the submission folder (Elsevier requires a flat folder); (5) a TeX distribution (MiKTeX or TeX Live) with `bibtex`/`biber`, or an online editor.
* **Overleaf workflow (practical, not tested here):** create a project from the venue's template; upload `references.bib` and the two figures; paste the converted text; fix table widths (the Markdown pipe tables are wide); compile; then check every `Table n`/`Figure n` reference and bibliography entry. The abstract-level wording in Section 2 and the Section 7 disclosures must survive the conversion. Before uploading anything, confirm that using a third-party hosting service is acceptable for unpublished work with licensed-data provenance.
* **After compiling, re-run** `python tools/check_submission_candidate.py` on the Markdown source (it does not read the LaTeX) and compare the PDF's numbers with it manually; there is no automated check of the converted file.

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

## 5. Terminology rule for registration language

Audit performed on 2026-10-14 (`docs/FINAL_CLAIM_EVIDENCE_MATRIX.md` section 6 lists every term, source and decision). The manuscript uses "pre-registered", "pre-specified" and "confirmatory" for no reported result. It describes the project's repository-committed plan and amendments as such, with dates and commit hashes, and states that they are not countersigned, not in any external registry, and not the basis of any reported analysis. A venue-required preregistration statement should say the same: no preregistered analysis is reported.

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
