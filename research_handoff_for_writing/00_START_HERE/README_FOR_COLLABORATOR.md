# Start here: writing the paper from this research package

This package lets you write the manuscript without needing to run any code. The research owner keeps responsibility for the code, the analysis, the tables and the figures. Prepared 2026-10-14 from Git commit `dfabaac` (branch `feat/completion-sprint-2026-10-14`). The Git repository is the source of truth for code; this package is the writing copy.

## 1. What the project investigates

Machine-learning signals for stock returns often look strong before trading costs. We ask how much of a signal survives three real-world frictions in **Germany, India and Japan, 2009-2019**: trading costs that grow with the size of the mandate (AUM), a cap on how much of a stock's daily volume the portfolio may trade, and capital-gains tax under each country's statute (a lot-level tax engine).

## 2. The actual, narrowed contribution

A modest, **as-run, non-US measurement** with a methods caution. It is not a new method and not a new mechanism. The US literature already established that implementable performance falls with AUM; what is different here is the coverage (three non-US markets, statute-specific tax, an ADV participation constraint on one book). Say exactly that. The four supported statements are in the abstract of the manuscript candidate; do not add to them.

## 3. Which manuscript draft to use

`01_MANUSCRIPT/manuscript.md` (title: "Costs, capacity and capital-gains tax for machine-learning equity strategies in Germany, India and Japan: an as-run measurement"). It is **not submission-ready**: authors, affiliations, acknowledgements, funding, conflicts, data and code availability are open author decisions (see `01_MANUSCRIPT/OPEN_DECISIONS_AND_PLACEHOLDERS.md`). Every number in it is re-derived from committed artifacts by a checker (`python tools/check_submission_candidate.py`); if you change a number, the checker will say so. Do not use `docs/PAPER_2026-10-09_FULL_ACCOUNT.md` (the original full account): it contains claims that were later withdrawn, and it is deliberately not in this package.

## 4. Figures and tables: IDs, placement, eligibility

Refer to every figure and table by its **stable asset ID** (for example `FIG_M4_capacity_B_tierB`, `TAB_M2_matched_book_outcomes`) so nothing breaks when numbering changes. Indexes with captions, intended manuscript locations, sources and limitations: `02_FIGURES/FIGURE_INDEX.md` and `03_TABLES/TABLE_INDEX.md`.

* **Main text:** 4 figures (`FIG_M1` pipeline schematic, `FIG_M2` cost-input coverage, `FIG_M3` Sharpe ladder and channels, `FIG_M4` capacity B(A)) and 4 tables (`TAB_M1` markets and coverage, `TAB_M2` matched-book outcomes, `TAB_M3` tax regimes, `TAB_M4` construction and friction specification). A journal article will not hold more; choose within these.
* **Supplement:** 17 more figures and 18 more tables (coverage audits, capacity details, solvency ledger, per-cell results, provenance registers, blocked-items inventory).
* **Diagnostic only** (supplement or an internal record, **never the main text**): 5 figures and 3 tables (`FIG_S4`, `FIG_S16`, `FIG_S17`, `FIG_S19`, `FIG_S21`; `TAB_S15`, `TAB_S16`, `TAB_S19`).
* The candidate's existing exhibits map as: Table 1 = `TAB_M2`; Table 2 = `TAB_S2` (all rungs); Figure 1 = `FIG_M4`; Figure 2 = `FIG_S1`.

Each figure is in three formats (PDF, SVG, PNG) and each table in three (CSV, LaTeX, Markdown); the three formats are one asset. Use the vector PDF or SVG for print and the CSV or LaTeX table for typesetting.

## 5. Claims that are withdrawn or blocked (never restate as findings)

* Sharpe-point capacity "gains", the capacity sign flip, its crossover and scaling law, "taxes decide viability", and the other items in manuscript Appendix A.
* **B(A) is an accounting difference against an infeasible, often near-ruined comparator. It is not an investable performance gain and cannot be converted to Sharpe points.**
* Germany's after-tax inference statistic: it exists in no artifact and is excluded; do not quote it.
* Japan is **not** a confirmation of the original prediction: of the five predictions in amendment 001C, one (P2) is scored and **not met**; four are not scoreable (`07_LIMITATIONS_AND_OPEN_ITEMS/AMENDMENT_001C_JAPAN_PREDICTION_SCORECARD.md`).
* Phase C (the revised exit treatment, carry-forward) was **not run and is blocked**. All 560 required series are not estimable under the current rules. The sensitivity of every number to the exit treatment is **unknown**.
* The project's amendments (001A to 001E) are repository commits by the project team: not countersigned, not in an external registry. Do not call anything "pre-registered" or "confirmatory". No co-author or reviewer approval exists or may be implied.

## 6. What is traceable and what must be disclosed

* Traceable: every table and figure number is built from a committed artifact whose SHA-256 is recorded (`05_RESULTS_AND_PROVENANCE/`).
* Disclose (all are already in the manuscript Section 7): the unknown exit-treatment sensitivity; the infeasible comparator; low design power (8 cells, 132 months); endogenous turnover and only three jurisdictions; the German and Indian $1bn summaries are verbatim snapshots of earlier outputs with weight identity recovered from file times, not run-time hashes; the 8-of-16-cell restriction was made after the economic arm's behaviour was seen.
* New disclosure from the asset build: India's cost-input coverage collapses in 2009-10 (1 of 274 in-universe securities certified) and its Tier B series has no return for that month; earlier project notes placing this in January 2009 are not supported by the committed artifacts. The manuscript Section 3 states it.
* The two accountings of B(A) (Tier A and Tier B) differ by up to 44 points of NAV a year in Germany; the manuscript uses Tier B only. Do not describe the tiers as agreeing.

## 7. Literature status

Read in full (some version; versions are in `06_LITERATURE/BIB_PROVENANCE.csv`): Avramov-Cheng-Metzker (published article), Azevedo-Hoegner-Velikov, Novy-Marx-Velikov 2016, Korajczyk-Sadka, Jensen et al., Gârleanu-Pedersen, Gu-Kelly-Xiu, Chen-Velikov (working paper), Liao et al., Choi-Jiang-Zhang (working paper), Israel-Moskowitz, Krasner-Sosner, Moehle et al., Huang. **Not read at full-text level** (metadata verified only; do not describe their contents): Cakici et al., Chen-Hanauer-Kalsbach, Lalwani et al., Novy-Marx-Velikov 2019, Sialm-Sosner, Berkin-Ye, Chaudhuri et al., Dai et al. Keep any statement about them marked "abstract level" or remove it. No copyrighted paper is included here.

## 8. What you can do on your own

Prose, structure, signposting and tightening; the introduction and related-work narrative within the stated limits; figure and table placement and captions within the asset indexes; consistent terminology (use the terms in `03_TABLES/` table `TAB_S6_terms_and_conventions`); the abstract's wording as long as the four supported statements and the caveats stay; bibliography formatting once a venue is chosen.

## 9. What you must not decide or change unilaterally

The research claim; any number, sign or threshold; removing a caveat; describing an unrun analysis as done; the venue choice and fees; author list, order, affiliations, contributions, acknowledgements and funding; data and code availability and licensing; whether to submit given the modest contribution; whether to seek co-author or reviewer countersignature; any new analysis (including scoring Japan predictions P1, P3, P4, P5, regenerating Germany's statistic, reopening Phase C, cost-sensitivity or capacity runs). Ask the research owner.

## 10. Recommended writing order

1. **Introduction and research question** (manuscript Section 1): frame as measurement, not method; end with the narrow contribution sentence as written.
2. **Related work** (Section 2): follow the read/unread status above; keep the Avramov et al. summary faithful to what the paper says (including its caution that findings do not imply unprofitability for all traders).
3. **Data and market definitions** (Section 3): `TAB_M1`, `FIG_M2`; keep the India 2009-10 disclosure; coverage supplements `FIG_S5`-`FIG_S7`, `TAB_S9`-`TAB_S11`.
4. **Portfolio construction and accounting** (Section 4): `FIG_M1`, `TAB_M4`, definitions `TAB_S6`.
5. **Results** (Section 5): 5.1 `TAB_M2`, `FIG_M3`; 5.2 `FIG_M4`, `TAB_S2`, `FIG_S1`, `FIG_S2`, solvency `FIG_S15`, `TAB_S17`; 5.3 `TAB_M3`, `TAB_S1`, `TAB_S14`; 5.4 design axes `TAB_S3`, `TAB_S20`, `FIG_S22`. Quote values from the tables, not from memory.
6. **Limitations and reproducibility** (Sections 6-7, Appendix B): `07_LIMITATIONS_AND_OPEN_ITEMS/`, `TAB_S7`, `TAB_S8`, `TAB_S21`.
7. **Conclusion and contribution statement** (Section 8): consistent with the abstract; "measurements consistent with published work, not a new mechanism".

If anything here conflicts with a number or statement in a table, the table and the checker win; tell the research owner.
