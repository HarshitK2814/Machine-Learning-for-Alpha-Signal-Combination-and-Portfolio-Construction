# submission_candidate_as_run_only

A **narrowed, as-run-only manuscript candidate**. Not submission-ready. The original full-account paper (`docs/PAPER_2026-10-09_FULL_ACCOUNT.md`) and every historical document are untouched. Why this scope and what it omits: `docs/FINAL_PUBLICATION_PATH.md`. Status of every claim: `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md`.

| File | Purpose |
|---|---|
| `manuscript.md` | the candidate (pandoc-style `[@key]` citations; format of the project's existing paper) |
| `references.bib` | the 21 cited entries: 11 copied verbatim from the generated project bibliography, 2 updated notes (`JKMP2026`, `AHV2023`), 8 tax-literature entries added from verified records |
| `BIB_PROVENANCE.csv` | verification source and full-text status for every entry that differs from the project bibliography |
| `TRACEABILITY.csv` | each artifact behind a quoted number, with SHA-256 |
| figures | referenced from `results/figures/` (not duplicated) |

## Build status

No TeX or pandoc toolchain is installed in the environment that produced this candidate, so **no PDF was compiled** and no journal template was applied. The reproducible check is

```
python tools/check_submission_candidate.py
```

It verifies that every citation resolves to a bibliography entry that is identical to the project's or has a provenance row, that every artifact exists with the recorded hash, that the quoted headline numbers re-derive from the committed CSVs, that Table/Figure references are defined and the figure files exist, that the required disclosures (Phase C blocked and not run, `as_run` exit, amendments not countersigned, exploratory observation labelled) are present, and that banned wording is absent. Its tests (`tests/tools/test_check_submission_candidate.py`) inject each defect and require failure. It is a consistency check, **not** scientific validation.

## Known gaps before this can be submitted (see `docs/PROJECT_COMPLETION_REPORT.md` for ordering)

* Germany's optimised-book net-Sharpe and tax-channel inference figures exist in no artifact and are omitted (regeneration conditions are in `docs/FINAL_NUMERICAL_TRACEABILITY_GAPS.md`; not authorised, not run).
* Germany and India $1bn after-tax summaries are verbatim snapshots of untracked historical outputs with partly inferred provenance (disclosed in manuscript Section 7).
* `ACM2023` (the closest prior art) was read in full (published article; online appendix not accessed) and compared in `docs/FINAL_PRIOR_ART_REVIEW.md` section 1. Since the follow-up search of 2026-10-14, Choi et al., Israel and Moskowitz, Krasner and Sosner, Moehle et al. and Huang were also read (versions in `BIB_PROVENANCE.csv`); Cakici et al., Chen et al., Lalwani et al., Novy-Marx and Velikov (2019), Sialm and Sosner, Berkin and Ye, Chaudhuri et al. and Dai et al. remain unread, so novelty statements about those literatures stay provisional.
* Amendment 001C's Japan predictions: P2 not met, four not scoreable from committed artifacts (`docs/AMENDMENT_001C_JAPAN_PREDICTION_SCORECARD.md`); the authors must decide whether to approve any further descriptive scoring.
* Authors, affiliations, journal template, abstract length, data and code availability statement are not set (author decisions).
* Exit-treatment sensitivity is unknown; the revised analysis is blocked (Section 7 of the manuscript).

## Publication assets

`paper_assets_as_run_only/` (at the repository root) holds generated figures and tables with a catalog (`ASSET_CATALOG.md`); regenerate with `python tools/make_paper_assets.py`. They are presentation of the committed artifacts listed in `TRACEABILITY.csv` and are not part of the checked manuscript text.

Mapping of the manuscript's exhibits to the asset library (full placement map in `paper_assets_as_run_only/ASSET_CATALOG.md`): Table 1 = `TAB_M2_matched_book_outcomes`; Table 2 = `TAB_S2_capacity_all_rungs` (all rungs); Figure 1 = `FIG_M4_capacity_B_tierB`; Figure 2 = `FIG_S1_uncapped_terminal_wealth`. The manuscript text was not changed to cite the other assets; Section 3 gained one disclosure (India's 2009-10 month) that `FIG_S7_india_coverage_audit` and `TAB_S11_coverage_aggregation_audit` document.
