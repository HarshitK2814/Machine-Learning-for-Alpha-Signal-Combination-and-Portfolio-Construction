# submission_candidate_as_run_only

A **narrowed, as-run-only manuscript candidate**. Not submission-ready. The original full-account paper (`docs/PAPER_2026-10-09_FULL_ACCOUNT.md`) and every historical document are untouched. Why this scope and what it omits: `docs/FINAL_PUBLICATION_PATH.md`. Status of every claim: `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md`.

| File | Purpose |
|---|---|
| `manuscript.md` | the candidate (pandoc-style `[@key]` citations; format of the project's existing paper) |
| `references.bib` | the 13 cited entries, copied verbatim from `research/08_References/references.bib` |
| `TRACEABILITY.csv` | each artifact behind a quoted number, with SHA-256 |
| figures | referenced from `results/figures/` (not duplicated) |

## Build status

No TeX or pandoc toolchain is installed in the environment that produced this candidate, so **no PDF was compiled** and no journal template was applied. The reproducible check is

```
python tools/check_submission_candidate.py
```

It verifies that citations resolve against an identical bibliography entry, that every artifact exists with the recorded hash, that the quoted headline numbers re-derive from the committed CSVs, that Table/Figure references are defined and the figure files exist, that the required disclosures (Phase C blocked and not run, `as_run` exit, amendments not countersigned, exploratory observation labelled) are present, and that banned wording is absent. Its tests (`tests/tools/test_check_submission_candidate.py`) inject each defect and require failure. It is a consistency check, **not** scientific validation.

## Known gaps before this can be submitted (see the completion report for ordering)

* Germany's optimised-book net-Sharpe and tax-channel figures are not in any artifact and are omitted.
* India's `lt_share` (0.5928) rests on an untracked local file; it needs a tracked snapshot.
* Tax-literature references have no records in the bibliography (`[CITATION PENDING]`): SS2018, IM2012, BY2003, KS2024, HUANG2019, PISH2026, CBLO2020, Dai-Lei-Liu-Yang (2026) and Moehle-Kochenderfer-Boyd-Ang (2021) as named in the project's documents. `ACM2023` was read at abstract level only.
* Authors, affiliations, journal template, abstract length and data-availability statement are not set (author decision).
* Exit-treatment sensitivity is unknown; the revised analysis is blocked (Section 7 of the manuscript).
