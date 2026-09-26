# Journal Strategy Report

## Executive Summary

The paper should be written for a **finance** audience first, with ML and optimisation rigor as supporting strengths. The realistic primary targets are the **Journal of Financial and Quantitative Analysis** and **Management Science (Finance)**. The stretch target is the **Review of Financial Studies**, which has published the closest precedents [@GKX2020; @DMNU2020; @JKMP2026]. Strong alternatives are the Review of Asset Pricing Studies, Review of Finance and Quantitative Finance. Backups are the Journal of Financial Markets, Journal of Banking & Finance and Journal of Empirical Finance. A shorter practitioner version could go to the Financial Analysts Journal or the Journal of Financial Data Science after the main paper is on SSRN.

**Metrics note.** Clarivate Journal Impact Factors could not be verified from an accessible primary source and are not reported as facts. Instead we report OpenAlex 2-year mean citedness and h-index (pulled from the OpenAlex API, September 2026). This is a transparent, reproducible proxy, not the JIF. Chartered ABS AJG and ABDC grades must be checked on the official lists before use in any internal assessment.

## 1. Four Kinds of Venue (why Impact Factor alone misleads)

| Category | Examples | What they reward | What gets a paper rejected | Implication for us |
|---|---|---|---|---|
| 1. Prestigious general finance | JF, RFS, JFE | A general economic insight that changes how the field thinks; mechanism; very broad robustness | "Better backtest" without economic content; incremental method; weak baselines | Only if the decomposition yields a general lesson about *why* ML adds value |
| 2. Top field / quantitative finance | JFQA, MS-Finance, RAPS, Review of Finance; QF, JFEc | Rigorous methods with clear financial relevance; narrower contribution acceptable | Snooping, missing costs, poor positioning versus closest papers | **Best fit** for our design |
| 3. Interdisciplinary ML/OR/forecasting | MS (other departments), OR, EJOR, IJF, JoE, JBES; ICAIF, NeurIPS/ICML workshops | Methodological novelty (often theory or algorithms), finance as application | Weak economic evaluation, especially costs, for finance-facing claims; lack of theory for OR/econometrics | Fits spin-offs (differentiable optimiser; inference methods) |
| 4. Accessible but respectable | JBF, JEF, JFM, JEDC, CFR, FAJ, JPM, JFDS, AOR | Solid execution, practical relevance, clarity | Sloppy integrity; overstated claims | Backups and practitioner dissemination |

Impact factor misleads here because high-volume applied-AI journals (e.g., Expert Systems with Applications, OpenAlex 2-yr mean citedness about 7.5) out-cite most specialist finance journals (e.g., JFQA about 3.4) yet carry far less weight with finance hiring and tenure committees and with finance reviewers [inference based on field norms].

## 2. Journal Comparison

| Journal | Tier | OpenAlex 2y cit. / h | Fit (1-10) | Difficulty (1-5) | Role | Code/data policy |
|---|---|---|---|---|---|---|
| Review of Financial Studies | 1 | 11.8 / 397 | 8 | 5 | Stretch | Verified: Data Editors; reproducibility package (conditional acceptances from 1 Oct 2025) |
| Journal of Finance | 1 | 13.2 / 664 | 7 | 5 | Stretch | Verified: AFA Data and Code Sharing Policy (2024) |
| Journal of Financial Economics | 1 | 12.4 / 557 | 6 | 5 | Stretch (lower fit) | Policy page exists |
| JFQA | 1b | 3.4 / 255 | 9 | 4 | **Primary target** | Verified: code sharing policy page |
| Management Science (Finance) | 1b | 6.2 / 480 | 9 | 4 | **Primary target** | Verified: Code and Data Disclosure Policy with Data Editor (2019) |
| Review of Asset Pricing Studies | 1b | 4.3 / 49 | 8 | 4 | Target | SFS journal (verify) |
| Review of Finance | 1b | n/a (verify) | 7 | 4 | Target | Verified: policy page exists |
| Quantitative Finance | 2 | 2.5 / 113 | 9 | 3 | Target | Verify |
| Journal of Financial Econometrics | 2 | 1.2 / 77 | 7 | 4 | Target (inference variant) | Verify |
| International Journal of Forecasting | 2 | 3.8 / 188 | 7 | 3 | Target (combination variant) | Verify |
| Journal of Financial Markets | 2 | 2.1 / 104 | 8 | 3 | Backup | Verify |
| Journal of Banking & Finance | 2 | 4.4 / 309 | 8 | 3 | Backup | Verify |
| Journal of Empirical Finance | 2 | 2.8 / 133 | 8 | 3 | Backup | Verify |
| European Journal of Operational Research | 2 | 5.9 / 407 | 7 | 3 | Backup (optimisation variant) | Verify |
| Critical Finance Review | 2 | 3.7 / 32 | 7 | 3 | Backup (critical re-assessment) | Verify |
| Operations Research | 1b (OR) | 3.5 / 304 | 5 | 5 | Method spin-off only | Verify |
| Financial Analysts Journal | 3 | 2.7 / 168 | 7 | 3 | Practitioner version | Verify |
| Journal of Financial Data Science | 3 | 0.7 / 21 | 6 | 2 | Practitioner ML version | None known |
| Journal of Portfolio Management | 3 | 0.8 / 116 | 6 | 2 | Practitioner | None known |
| Mathematical Finance | 2 | 1.6 / 129 | 2 | 5 | Not recommended | - |
| Journal of Computational Finance | 2 | 0.7 / 57 | 4 | 3 | Not recommended (except numerical variant) | - |
| ACM ICAIF | ML | n/a | 5 | 2 | Early feedback on ML components | Varies |

Full detail (scope, typical methodology, empirical/theory/data expectations, related papers, notes) is in Workbook 2.

## 3. What Differentiates Papers That Get In

Based on the precedents in our literature matrix [inference from reading the published papers against working papers and practitioner outlets]:

1. **An economic question, not a model.** GKX2020 asked where ML gains come from (nonlinear interactions). ACM2023 asked whether ML survives economic restrictions. JKMP2026 asked what the right evaluation criterion is (the implementable frontier). DMNU2020 asked why many characteristics matter under costs (netting).
2. **A controlled comparison.** The same data, universe and evaluation across methods, with strong linear and naive baselines.
3. **Implementability.** Costs, turnover, capacity and universe restrictions are now baseline expectations for investment claims [@NMV2016; @DNMV2023; @JKMP2026].
4. **Integrity.** Transparent trial counts, out-of-sample discipline, multiple-testing awareness [@HLZ2016; @HAR2017], and increasingly reproducibility packages (JF, RFS, MS policies verified above).
5. **Interpretation.** An explanation of which signals and states drive results, tied to known economics (limits to arbitrage, sentiment, liquidity).
6. **Positioning.** Explicit statements of what is new relative to the closest papers, with no over-claiming.

## 4. Reviewer Expectations by Dimension

| Dimension | Top-3 finance | JFQA / MS / RAPS | QF / JFM / JBF / JEF |
|---|---|---|---|
| Novelty | Conceptual contribution to finance | Clear methodological or empirical advance | Solid incremental contribution acceptable |
| Theory | Mechanism strongly preferred | Economic motivation; formal theory optional | Optional |
| Economic interpretation | Essential | Essential | Expected |
| Robustness | Very extensive (subperiods, universes, international, alternative specs) | Extensive | Moderate-extensive |
| Transaction costs | Essential for investment claims | Essential | Expected |
| Out-of-sample | Essential, with genuine holdout | Essential | Essential |
| Data | CRSP/Compustat full history; international a plus | Same | Same or narrower |
| Code/data | Required at acceptance | Required (MS Data Editor) | Journal-specific |

## 5. Submission Strategy (proposed)

1. **Pre-submission (months 12-15).** Post an SSRN working paper with the replication code structure described. Submit to AFA, WFA, EFA, SFS Cavalcade, NBER Asset Pricing / Big Data and ML, SoFiE, FMA, and practitioner forums (Q-Group, INQUIRE). Present ML components at ICAIF for feedback. Incorporate discussant comments before journal submission.
2. **First journal submission.** RFS if the attribution yields a clear, general economic lesson, for example that cost-aware learning, not model complexity, drives net value and that state dependence matters only with costs internalised, backed by mechanism evidence. Otherwise go directly to **JFQA** or **Management Science**.
3. **After rejection.** Revise using reports, re-run the closest-prior-art check, then JFQA ↔ MS, RAPS or Review of Finance, then Quantitative Finance, JFM, JBF or JEF.
4. **Spin-offs** (only after the main paper is public): a practitioner FAJ/JFDS article on "what matters net of costs"; a methods paper (differentiable cost-aware layers) for MS/OR/EJOR; an inference note (factorial attribution with SPA/MCS) for JFEc.
5. **Cover letter.** Name the closest papers explicitly (JKMP2026, SWZ2023, DMNU2020, DMU2024, ACM2023, CHK2024) and state the incremental contribution in one sentence each.

## 6. What Makes a Quantitative Finance Paper Publishable or Rejectable

**Publishable:** a sharply posed economic question; a design that isolates the answer; strong baselines including naive and linear; net-of-cost and capacity evidence; out-of-sample holdout; data-snooping controls; interpretation tied to economic theory; honest limits; a reproducible package.

**Common rejection reasons [inference from field norms and the published critiques in @HLZ2016; @HAR2017; @ACM2023; @CHK2024]:**
- Gross-of-cost results or unrealistic costs.
- Look-ahead bias: accounting data not lagged, survivorship, unadjusted delistings [@SHU1997], smoothed regime labels.
- Hyperparameter tuning on the test period; undisclosed trial counts.
- Weak benchmarks, or benchmarks under-tuned relative to the proposed model.
- Microcap-driven results with equal weighting [@HXZ2020].
- "Black box" with no economic interpretation.
- Over-claimed novelty relative to closest papers.
- Short samples or a single market regime.
- Statistical significance claims without HAC errors, Sharpe-difference tests or multiple-testing corrections.

## 7. Reviewer-Proof Checklist

The full checklist is maintained in 07_Experimental_Framework/Reviewer_Proof_Checklist.md and reproduced in the Final Blueprint PDF.
