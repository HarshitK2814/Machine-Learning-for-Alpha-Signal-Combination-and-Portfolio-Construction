# Submission preparation (2026-10-14): venues, build, author fields, availability wording

Internal preparation material for the authors. It selects nothing: venue, authorship, permissions and every statement that needs someone's confirmation are author decisions. Nothing here asserts that code or data will be public. Evidence status is stated for each fact: **retrieved** (read from the named page today), **secondary** (a third-party or search-result description), or **not retrieved** (the official page returned HTTP 403 or was not found).

## 1. Venue shortlist for the narrowed contribution (not a recommendation)

The contribution (see `docs/FINAL_PUBLICATION_PATH.md` section 7): a modest non-US as-run measurement with a methods caution, no new method or mechanism, an unresolved exit-treatment qualification, and an unfinished novelty comparison against the closest prior art. Fit notes below are about subject matter and length only; none estimates the chance of acceptance.

| Option | Official aims and scope | Article type and length | Template and build dependency | Evidence status |
|---|---|---|---|---|
| *Journal of Empirical Finance* (Elsevier) | Empirical financial economics and financial econometrics, all fields of finance including international finance and asset pricing (Elsevier shop listing) | Regular articles; the listing reports about 85% of submissions rejected, about 40% without review, with "topic too narrow" and "analysis below standard" among the common reasons | Elsevier `elsarticle` class; Elsevier's LaTeX page states all files must sit in one folder with no subfolders (`.tex`, `.bbl`, `.bst`, `.bib`, images as figure items) | Shop listing **secondary-retrieved**; Elsevier LaTeX page **retrieved**; the journal's own Guide for Authors **not retrieved** (403) |
| *Quantitative Finance* (Taylor & Francis) | Theoretical and empirical work on quantitative methods in finance, researchers and practitioners (aggregator description) | not verified | T&F generic `interact` class with reference styles (Overleaf hosts T&F templates); whether the journal requires a specific class is not verified | **Secondary** only; T&F pages **not retrieved** (403) |
| *International Review of Financial Analysis* (Elsevier) | Refereed outlet open to research from anywhere in the world, not US-centric (secondary summaries of the ScienceDirect aims page) | not verified | `elsarticle`, as above | **Secondary** only; Guide for Authors **not retrieved** |
| *Finance Research Letters* (Elsevier) | All areas of finance (Wikipedia) | Letters; a 2,500-word limit is reported by Wikipedia citing the Guide for Authors, **not confirmed**. The candidate is far longer, so this option would mean a drastic cut and loss of the traceability apparatus | `elsarticle` | **Secondary** only; Guide **not retrieved** |

Carried from the earlier audit and **not re-verified**: *Journal of International Financial Markets, Institutions & Money* (international securities markets; weighted to FX and banking topics) and *Review of Asset Pricing Studies* (noted as unlikely to fit a corroborating measurement). Before choosing, the authors must read each journal's current instructions on its own site (aims, article types, length, submission fee, data and code policy, AI-use policy, preprint policy), which could not be retrieved here.

## 2. Build readiness

* **Environment checked:** no `pdflatex`, `xelatex`, `latexmk`, `tectonic` or `pandoc` is installed on the machine that produced the candidate, and nothing was installed (a TeX distribution is a large install and no template is chosen). **No PDF exists.** Nothing below has been executed.
* **Other tools found:** Docker is installed (a TeX Live image would be a multi-gigabyte download and was not pulled without authorisation); the Python packages `markdown`, `weasyprint` and `reportlab` are installed, which could render a plain review copy of the Markdown, but that would not be a journal-formatted build and none was made. No MiKTeX, TeX Live or Pandoc directory exists in the usual install locations.
* **What a compiled version needs:** (1) a chosen venue and its class (`elsarticle` or the T&F `interact` class); (2) conversion of `manuscript.md` to LaTeX, by `pandoc` with citeproc or `--natbib`, or by hand; (3) `references.bib` (21 entries; journal volume and pages are inside the `journal` field following the project convention, so a LaTeX bibliography style will print them as part of the journal name unless the entries are reformatted); (4) the two figures `results/figures/fig1_capacity_return_difference_B.png` and `fig2_uncapped_terminal_wealth.png` copied into the submission folder (Elsevier requires a flat folder); (5) a TeX distribution (MiKTeX or TeX Live) with `bibtex`/`biber`, or an online editor.
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
