# Research Roadmap (staged implementation plan)

Durations are planning estimates for a small team (1-2 researchers plus part-time developer support), in months from project start. They are not commitments. Journal review times vary widely and are not included in the 16-month build.

| Phase | Months | Tasks | Dependencies | Deliverables | Key risks | Acceptance criteria |
|---|---|---|---|---|---|---|
| 1. Literature + research design | 1-2 | Finalise closest-prior-art search; pre-register hypotheses H1-H6; freeze factorial design and benchmark list; confirm data licences | This package | Pre-registration document; updated tracker; design spec v1.0 | Newly published overlapping paper | Tracker re-run; no overlap triggering the re-scope rule; co-author sign-off |
| 2. Data infrastructure | 2-4 | WRDS extracts (CRSP, Compustat, CCM, TAQ spreads); PIT engineering; delisting handling; state variables; unit tests | Phase 1 licences | Versioned PIT panel; data manifest; test suite | Licence gaps (TAQ, Markit); PIT errors | E00 passes: factor correlations > 0.95; zero look-ahead test failures |
| 3. Alpha signal library | 3-5 | Build ~150 signals (JKP code / OpenAP); publication flags; quality, decay, redundancy diagnostics | Phase 2 | Signal panel; E01-E03 reports | Signal definition mismatches | Replication slope/R² close to CZ2022 benchmarks; coverage report |
| 4. Baseline models | 5-6 | Naive, linear, KNS SDF, published ML, DMNU PPP, JKMP Portfolio-ML replication | Phase 3 | E10-E14 results; benchmark registry | JKMP code compute burden | Directional replication of published benchmarks documented |
| 5. ML signal combination | 6-9 | Implement 16 factorial cells; uncertainty ensembles; trial logging (MLflow) | Phases 3-4 | Model registry; E20-E29 development results | Compute; unstable NN economic-loss training | All cells run end-to-end on the 1995-2020 walk-forward; seeds logged |
| 6. Portfolio construction | 8-10 | Risk model; TC-aware optimiser; constraints; cost model; AUM grid; E-cell projection | Phases 2, 5 | Optimiser module; E30-E34 | Solver failures; cost calibration disputes | Constraint-violation rate < 0.1% of months; cost sensitivity grid complete |
| 7. Robust backtesting | 9-11 | Execution lag; reconciliation; multiverse runs; **specification freeze**; then **open the lockbox once** | Phases 5-6 | Frozen spec (dated); lockbox results | Temptation to iterate after lockbox | Freeze date precedes lockbox run in logs |
| 8. Robustness + statistical testing | 11-13 | SPA/StepM/MCS, DSR, PBO, factorial & Shapley attribution, E40-E56; interpretation E60-E64 | Phase 7 | Inference tables; robustness appendix; interpretation figures | Weak power for interactions | All pre-registered tests reported; checklist sections C-H complete |
| 9. Paper writing | 12-15 | Draft introduction and contribution; results; internet appendix; replication package; internal review; SSRN posting; conference submissions | Phase 8 | Working paper; replication package; slides | Over-claiming; unclear narrative | Reviewer-proof checklist 100% ticked; two external readers' comments addressed |
| 10. Journal submission | 15-16 (+ review cycles) | Final prior-art check; journal choice (RFS stretch vs JFQA/MS); cover letter; respond to referees | Phase 9 | Submission; response letters | Desk rejection; long review | Submission package meets journal policy; tracker re-run within 2 weeks |

## Critical path

Data licences → PIT panel → signal library → factorial cells → optimiser/costs → specification freeze → lockbox → inference → writing.

## Go / no-go gates

1. **End of Phase 1.** If a newly found paper performs the same factorial attribution, re-scope to G2/G3 (conditioning × cost interaction and mechanisms) or to the uncertainty and international extensions.
2. **End of Phase 4.** If JKMP Portfolio-ML cannot be run, substitute DMNU PPP and a deep PPP as the economic-objective benchmarks, and disclose this.
3. **End of Phase 7.** Whatever the lockbox shows, the paper proceeds. The narrative adapts; the design does not.
