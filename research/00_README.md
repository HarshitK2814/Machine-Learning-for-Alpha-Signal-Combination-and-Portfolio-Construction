# ML Alpha Signal Combination Research Package

**Topic:** Machine Learning for Alpha Signal Combination and Portfolio Construction
**Status:** Pre-empirical research proposal (September 2026). No backtests have been run; expected outcomes are hypotheses.

## Selected paper (proposed)

*Where Does Machine-Learning Alpha Come From After Trading Costs? Nonlinearity, State Dependence and Cost-Aware Learning in Signal Combination.*
A controlled 2x2x2x2 factorial attribution of net-of-cost value to nonlinearity, state-dependent weights, a cost-aware objective and forecast
uncertainty, with data-snooping-robust inference and economic mechanism tests. Primary targets: JFQA, Management Science; stretch: RFS.

## Deliverables

| Deliverable | Path | Contents |
|---|---|---|
| PDF 1 | [09_Reports/PDF1_Comprehensive_Literature_Review.pdf](09_Reports/PDF1_Comprehensive_Literature_Review.pdf) | Executive summary, literature evolution, key papers, methods, findings, gaps, BlackRock AIM analysis, matrix appendices |
| PDF 2 | [09_Reports/PDF2_Journal_Strategy.pdf](09_Reports/PDF2_Journal_Strategy.pdf) | Journal tiers, comparison, fit, expectations, ranking, submission strategy, reviewer checklist |
| PDF 3 | [09_Reports/PDF3_Research_Gap_and_Opportunity_Report.pdf](09_Reports/PDF3_Research_Gap_and_Opportunity_Report.pdf) | Existing approaches, weaknesses, gaps, pipelines A-F, prior-art tracker, 15 ideas, 5 concepts |
| PDF 4 | [09_Reports/PDF4_Proposed_Research_Design.pdf](09_Reports/PDF4_Proposed_Research_Design.pdf) | Research question, hypotheses, architecture, data, ML/portfolio methods, benchmarks, experiments, statistics |
| PDF 5 | [09_Reports/PDF5_Final_Research_Blueprint.pdf](09_Reports/PDF5_Final_Research_Blueprint.pdf) | Consolidated working blueprint (overview + design + framework + checklist + roadmap) |
| Workbook 1 | [09_Reports/Workbook1_Literature_Database.xlsx](09_Reports/Workbook1_Literature_Database.xlsx) | 200 entries; summary formulas; closest prior art; legend |
| Workbook 2 | [09_Reports/Workbook2_Journal_Analysis.xlsx](09_Reports/Workbook2_Journal_Analysis.xlsx) | Journal analysis with priority formulas, role formatting, metrics note |
| Workbook 3 | [09_Reports/Workbook3_Research_Idea_Matrix.xlsx](09_Reports/Workbook3_Research_Idea_Matrix.xlsx) | 15 ideas; editable weights; score and rank formulas; concept selection |
| Workbook 4 | [09_Reports/Workbook4_Experiment_Matrix.xlsx](09_Reports/Workbook4_Experiment_Matrix.xlsx) | Experiment register with status dropdowns, progress summary, factorial contrasts, Gantt, checklist tracker |

## Folder structure

| Folder | Contents |
|---|---|
| [01_Literature_Review](01_Literature_Review) | Literature review (Markdown source), literature matrix CSV |
| [02_Journal_Strategy](02_Journal_Strategy) | Journal strategy, journal analysis CSV, OpenAlex metrics (raw JSON, CSV, pull script) |
| [03_Research_Gaps](03_Research_Gaps) | Gap and opportunity report; **living closest-prior-art tracker** |
| [04_Paper_Concepts](04_Paper_Concepts) | 15 ideas, 5 full concepts, selection; idea matrix CSV |
| [05_Selected_Research_Design](05_Selected_Research_Design) | Selected design (incl. contribution statement and closest-paper tables); blueprint overview |
| [06_Data_Strategy](06_Data_Strategy) | Data sources, bias register, point-in-time rules |
| [07_Experimental_Framework](07_Experimental_Framework) | Implementation spec, YAML config, experiment register, reviewer-proof checklist, roadmap |
| [08_References](08_References) | BibTeX, formatted bibliography, Crossref verification CSV + raw responses + script |
| [09_Reports](09_Reports) | 5 PDFs, 4 Excel workbooks, figures |
| [_build](_build) | Single source of truth (data modules) and build scripts |

## Evidence conventions

- **Verified**: from publisher pages, abstracts, authors' repositories, Crossref/OpenAlex APIs.
- **[inference]**: research-team synthesis. **[verify]**: not confirmed from accessible full text (130 flags across sources); check before citing.
- **Proposed**: our design choice. **Hypothesis**: to be tested; never a result.

## Verification statistics

- Bibliography entries: 200; with DOI: 160; DOI matched/confirmed via Crossref: 157.
- Journal Impact Factors (Clarivate) were **not** verifiable and are not reported; OpenAlex 2-year mean citedness is reported instead.

## Rebuild

```
python _build/build_all.py
```
Requires Python 3.12 with reportlab, openpyxl, matplotlib, fontTools, PyMuPDF; fonts Georgia/Segoe UI/Consolas (Windows).

## Most important habit

Re-run the closest-prior-art search protocol (03_Research_Gaps/Closest_Prior_Art_Tracker.md) at every phase gate and within two weeks of submission.
