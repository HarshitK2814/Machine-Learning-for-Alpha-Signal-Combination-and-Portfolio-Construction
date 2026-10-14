# Developer notes (previous repository README, kept for the team)

Moved here from the repository front page. It holds the workstream split, branch rules, CODEOWNERS layout and the engineering quick start.

# Machine Learning for Alpha Signal Combination and Portfolio Construction (`alphacomb`)

Repository: https://github.com/HarshitK2814/Machine-Learning-for-Alpha-Signal-Combination-and-Portfolio-Construction
(public). The Python package is importable as `alphacomb`.

Research code for the paper **"Where Does Machine-Learning Alpha Come From After Trading Costs?
Nonlinearity, State Dependence and Cost-Aware Learning in Signal Combination."**

The design, hypotheses and experiment register live in the research package
(`../ML_Alpha_Signal_Combination_Research/`), PDF 4 and Workbook 4. The team split is in PDF 6 /
`Team_Coding_Work_Distribution.docx`: three equal workstreams (Absar = data/costs/backtest,
Harshit = models/portfolio/risk/interpretation, Maham = baselines/statistics/reporting).

## At a glance (2026-10-14)

**What this repository is.** Research code, committed result snapshots, a narrowed manuscript candidate and a library of publication figures and tables for a study of how much of a machine-learning equity signal survives three frictions (AUM-indexed trading costs, an ADV participation constraint, statutory capital-gains tax) in **Germany, India and Japan, 2009-2019**.

**What the evidence supports (and no more).** A modest, **as-run, non-US measurement with a methods caution**; no new method, no new mechanism. The gross decile composites look strong before costs; the executable participation-capped decile book is net-negative at a $1bn mandate in all three markets; the optimised book's net Sharpe is not distinguishable from zero where it is traceable; the capacity measure B(A) is an accounting difference against an infeasible comparator (not an investable gain); the statute decides whether a holding-period tax channel exists; no design axis is detectable at the available power. Every number is under the `as_run` exit treatment, and the sensitivity to the later exit ruling is **unknown**.

**What is blocked or withdrawn.** Phase C (the revised analysis) is blocked and **not run**; all 560 required series are not estimable under current rules; Germany's optimised-book after-tax inference statistic is excluded (no artifact); Japan is **not** a confirmation of amendment 001C (P2 not met, P1/P3/P4/P5 not scoreable); several earlier headline claims were withdrawn (`docs/FINALIZATION_AUDIT_2026-10-09.md` section 1.2). The project's amendments are repository commits by the team, not countersigned, in no external registry: nothing here is "pre-registered" or "confirmatory", and no co-author or reviewer approval is claimed.

### Repository map

| Path | Contents |
|---|---|
| `src/alphacomb/` | The package: contracts, models, portfolio construction, risk, tax engine, validation, theory |
| `pipelines/` | Stage scripts (train, construct portfolios, after-tax evaluation) |
| `tools/` | Experiment and audit scripts, the candidate checker, the withdrawn-claims screen, the asset generators |
| `tests/` | Unit and integration tests (`tests/tools`, `tests/validation`, `tests/tax`, ...) |
| `configs/` | Base, portfolio, model and risk configuration |
| `docs/` | Specifications, audits, results write-ups, amendments, the claim-evidence matrix and the completion report |
| `docs/attachments/`, `results/` | Committed result snapshots with hashes recorded in `submission_candidate_as_run_only/TRACEABILITY.csv` |
| `submission_candidate_as_run_only/` | The narrowed manuscript candidate (Markdown), bibliography with provenance, traceability table, submission notes |
| `paper_assets_as_run_only/` | **26 figures and 25 tables** (PDF/SVG/PNG and CSV/LaTeX/Markdown), catalog and manifest |
| `research_handoff_for_writing/` | Writer-friendly copy of the approved material, indexes, collaborator guide and a manifest |

### Quick start

```
python -m pip install -e .                       # Python 3.12
python tools/check_submission_candidate.py       # citations, hashes, every manuscript number re-derived
python tools/check_withdrawn_claims.py           # screen for withdrawn wording
python tools/make_paper_assets.py                # rebuild paper_assets_as_run_only/ from tracked artifacts
python tools/make_paper_assets.py --verify       # verify the folder against its manifest (line-ending tolerant)
python -m pytest tests/tools -o addopts= -p no:cacheprovider -q   # run test directories one at a time
```

The heavy stages that produced the committed snapshots need licensed vendor-derived panels that are **not** in this repository; they are not rerun by the commands above.

### Where to read next

* `docs/PROJECT_COMPLETION_REPORT.md`: what is done, what blocks submission, validation record, decision register.
* `submission_candidate_as_run_only/manuscript.md`: the manuscript candidate (not submission-ready).
* `paper_assets_as_run_only/ASSET_CATALOG.md`: every figure and table with sources, hashes, captions, limits and the placement map.
* `research_handoff_for_writing/00_START_HERE/README_FOR_COLLABORATOR.md`: the guide for the person writing the paper.
* `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md`, `docs/FINAL_NUMERICAL_TRACEABILITY_GAPS.md`, `docs/FINAL_PRIOR_ART_REVIEW.md`: claim status, traceability gaps, literature status.

### Data, licensing and sharing

This repository is **public**. It contains derived result tables, monthly portfolio-level series and some security-level reference files produced from licensed vendor data (WRDS/Compustat Global lineage); raw vendor extracts are not included. Whether each derived artifact may be redistributed has **not** been verified against the vendor's terms; anyone reusing the data should check. No journal papers are committed. The manuscript candidate is a draft with author fields unfilled.

### Validation record

Candidate checker and withdrawn-claims screen pass. Tests were last run in 13 sequential per-directory batches (715 passed, 0 failed); this is not a single full-suite invocation. Details: `docs/PROJECT_COMPLETION_REPORT.md` sections 7, 8a and 8b.

## Status

| Workstream | Owner | State |
|---|---|---|
| A - data, costs, backtest | Absar | **Complete and production-promoted.** C1-C6 are ready; the dated C14/C12 integration and six frozen human decisions pass semantic preflight. The real-data handoff to Workstream B is complete in `docs/handoff/13_WORKSTREAM_A_PRODUCTION_PROMOTION_AND_WORKSTREAM_B_HANDOFF_2026-10-07.md`. |
| B - models, portfolio, risk, interpretation | Harshit | **Code complete on synthetic data; real-data inputs handed off.** Next: validate the handoff, produce real C11 weights under the frozen experiment, and return those weights to Absar for final C12 accounting. |
| C - baselines, statistics, reporting | Maham | Not started. Contracts, example outputs and a worked "how to plug a baseline in" snippet are ready: `docs/HARSHIT_PROVIDES.md`. |

That sentence block describes the state at the Workstream-A handoff (2026-10-07). It is superseded by
the **current state** section below: real-data as-run experiments have since been run, several results were
withdrawn, and the revised (Phase C) analysis is blocked.

### Frozen Workstream-A boundary

- C1-C6 are ready for the real-data experiment.
- Tax-dependent international evaluation is restricted to 2009-01 through
  2019-12. The clean mechanism window is 2014-01 through 2018-03.
- `MODELLED_FLAT_BORROW_PROXY_V1` is a configuration-layer assumption only.
  Certified C6 `borrow_fee` observations remain null; the legacy implicit 25 bp
  fallback is prohibited.
- Workstream-B must assemble and run one flat bundle per country using a
  separate `ALPHACOMB_DATA` root. C6/C14 are shared lookup sources; they do not
  authorize pooled DEU/IND/JPN ranking or portfolio construction.
- Absar's remaining downstream responsibility is final C12 accounting after
  Harshit supplies real C11 weights.

## Current state (2026-10-14)

* Authoritative records: `docs/PROJECT_COMPLETION_REPORT.md` (what is done, what blocks submission),
  `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md` (status of every claim), `docs/FINAL_PUBLICATION_PATH.md`.
* The as-run experiments (2009-2019, DEU/IND/JPN) exist; several headline results were **withdrawn** and are
  listed in `docs/FINALIZATION_AUDIT_2026-10-09.md` section 1.2. `python tools/check_withdrawn_claims.py` screens
  `docs/`, `research/`, `prereg/`, `submission_candidate_as_run_only/` and this README for them (a screen, not verification).
* **Phase C (the revised analysis under the 2026-10-13 exit ruling) is blocked and has not been run**; see
  `docs/PHASE_C_RUN_READINESS_V2_2026-10-14.md` section 8.
* A narrower manuscript candidate is in `submission_candidate_as_run_only/` (Markdown; no TeX toolchain is
  assumed). Consistency check: `python tools/check_submission_candidate.py`. It checks citations, hashes,
  re-derived numbers and disclosures; it is not scientific validation and the candidate is not submission-ready.
* Environment: Python 3.12 (`python -m pip install -e .`, then `pytest -q`). Commands elsewhere in this README that
  reference `../ML_Alpha_Signal_Combination_Research/` assume a sibling research folder that is not part of this repository.

### Data access and unavailable sources

* `data/` holds the production C1/C4/C6/C14 tables and audits that were committed or copied locally. The raw
  vendor extracts (the C4 source SAS file and every `data/intl_c6/staging/*` file named in the C6 audits) are **not
  in this repository**, so those audits cannot be re-verified here; vendor (WRDS/Compustat Global) access and the
  vendor's own item documentation are external prerequisites for any further data-recovery work.
* `outputs/` is git-ignored: historical experiment outputs live there only on the original machine. Tracked,
  verbatim snapshots are `docs/attachments/*.csv`; Germany's optimised-book after-tax inference row and the India and
  Germany $1bn after-tax summaries have **no tracked snapshot** (see the claim-evidence matrix, section 1).

## Quick start

```bash
python -m pip install -e .
python pipelines/run_all.py --smoke               # generate data, 2 cells, 2 years, end to end
pytest -q                                         # full suite (count changes; see docs/PROJECT_COMPLETION_REPORT.md)

# or stage by stage
python -m alphacomb.synthetic.generate --out data/synthetic          # C1-C6 fixtures + truth.json
python pipelines/02_train_models.py --cells all --years 1995 2020     # C9/C10
python pipelines/02_train_models.py --cells N-S-P-0 --seeds 0 1 2 3 4 # seed dispersion (E56)
python pipelines/02_train_models.py --cells L-S-P-0 --benchmarks gkx_nn3 gkx_gbrt   # E13
python pipelines/04_construct_portfolios.py --strategies all          # C11 weights
python pipelines/04_construct_portfolios.py --strategies all --cost-multiplier 2.0  # cost sensitivity
python tools/dev_backtest.py --strategies all                         # TEMPORARY stand-in for C12
```

Cell codes are `<form>-<conditioning>-<objective>-<uncertainty>`, for example `N-C-E-U` is nonlinear,
state-conditional, economic loss, with uncertainty shrinkage (the full model).

## Repository layout (CODEOWNERS)

```
src/alphacomb/contracts/   SHARED - schemas, paths, io, splits, interfaces (frozen Week 1)
src/alphacomb/synthetic/   ABSAR  - synthetic data generator (currently written by Harshit as a stand-in)
src/alphacomb/data/        ABSAR  - WRDS pulls, PIT panel, signals, states
src/alphacomb/costs/       ABSAR  - spreads, impact, borrow fees
src/alphacomb/backtest/    ABSAR  - P&L engine
src/alphacomb/models/      HARSHIT- 16 factorial cells, uncertainty, benchmarks
src/alphacomb/portfolio/   HARSHIT- TC-aware optimiser, constraints, projection
src/alphacomb/risk/        HARSHIT- structural factor risk model
src/alphacomb/interpret/   HARSHIT- economic feature importance, SHAP, implied weights
src/alphacomb/baselines/   MAHAM  - naive/linear/SDF baselines
src/alphacomb/stats/       MAHAM  - inference and decomposition
src/alphacomb/reporting/   MAHAM  - tables and figures
tools/                     TEMPORARY dev utilities (deleted once workstream A lands)
```

## Branch and merge rules

- `main` is protected in spirit: every change arrives through a `feat/*` branch and is merged with
  `--no-ff` so the feature history stays visible.
- Branch names: `harshit/<topic>`, `absar/<topic>`, `maham/<topic>` for member work;
  `feat/<topic>` for the shared bootstrap done in Week 1.
- Nobody edits another member's folders. Changes to `src/alphacomb/contracts/` are Contract Change
  Requests and need all three members to agree.
- Outputs are keyed by `run_id`, so parallel runs never overwrite each other. `data/` and `outputs/`
  are git-ignored.

## Evidence and integrity rules baked into the code

- Point-in-time only: models never see data after the split's `train_end` (see `contracts/splits.py`).
- The lockbox window (2021-2025) is refused by `Splits.assert_not_lockbox()` unless the environment
  variable `ALPHACOMB_FREEZE_TAG` is set, which happens only after the specification freeze.
- Every fit logs a row to `outputs/trials.csv` (C13) so the deflated Sharpe ratio and PBO can use an
  honest trial count.
