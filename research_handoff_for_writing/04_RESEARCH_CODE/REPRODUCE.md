# Reproducing what can be reproduced

This folder is a **copy** of code from the Git repository (source of truth), prepared from commit `dfabaac` on branch `feat/completion-sprint-2026-10-14`. Do not edit it; changes belong in the repository.

## What runs from tracked files alone

```
pip install -e .            # from the repository root; needs Python 3.12 with pandas, numpy, matplotlib, pyyaml, pytest
python tools/check_submission_candidate.py     # citations, hashes, every manuscript number re-derived
python tools/check_withdrawn_claims.py         # screen for withdrawn wording
python tools/make_paper_assets.py              # regenerates paper_assets_as_run_only/ (figures and tables)
python tools/make_paper_assets.py --verify     # checks the folder against its manifest
python tools/make_figures.py                   # the candidate's Figures 1 and 2
```

Tests: run one directory at a time to stay within memory, for example `python -m pytest tests/tools -o addopts= -p no:cacheprovider -q`, then `tests/validation`, `tests/tax`, and the other directories under `tests/`. The last validated state was 715 passed across 13 sequential batches (not a single full-suite invocation).

## What needs data that is not in this package

The heavy stages that produced the committed result snapshots (model training, portfolio construction, the lot-level backtest) read licensed vendor-derived panels that are not redistributed. Their outputs are committed as snapshots with hashes. Regenerating the snapshots is not part of the writing task and must not be attempted without the research owner.

Phase C is blocked and must not be run.
