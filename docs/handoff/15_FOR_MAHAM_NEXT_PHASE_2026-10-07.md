# For Maham — workstream C, next phase

**7 October 2026.** From Harshit (workstream B).

Read [`14_WORKSTREAM_B_RECEIPT_AND_INTEGRATION_2026-10-07.md`](14_WORKSTREAM_B_RECEIPT_AND_INTEGRATION_2026-10-07.md)
first for the data situation, then this.

**Status as of this writing:** Absar's complete promoted bundle is on the shared Google
Drive folder, uploaded 7 October between ~13:00 and 17:09 — code, configs, tests, both
validators, closeout artefacts and data. It was never pushed to GitHub. Workstream B is
downloading and verifying it now. Nothing below depends on that landing first.

---

## 0. The short answer

**You are not blocked, but five things about the project changed in the last three weeks
and they change what your deliverables have to look like.** Workstream A finished and
froze its decisions on 7 October. Those decisions reach into statistics, robustness and
reporting — your remit — and some of them invalidate assumptions baked into the current
`configs/base.yaml`.

Nobody has inspected a real result. Everything below is pre-results work, and it needs
to stay that way: frozen decision 6B explicitly requires that
`results_must_not_be_inspected_before_scenarios_are_fixed`. Fixing those scenarios is
largely your job, and it is the critical path.

### 0.1 Eleven files are frozen and arriving from Absar — do not edit them

Absar's manifest pins each of these to a SHA-256, and his versions are on Drive waiting
to be pulled into the repo.
Editing any of them here creates a second divergent copy of a frozen file, and
reconciling two independent edits to the same cost or tax path is exactly the silent
inconsistency the frozen-contract discipline exists to prevent. Workstream B has already
declined to touch them for this reason.

```
configs/base.yaml                                    src/alphacomb/tax/dated.py
src/alphacomb/portfolio/cost_terms.py                src/alphacomb/tax/backtest.py
src/alphacomb/portfolio/optimizer.py                 src/alphacomb/tax/__init__.py
src/alphacomb/portfolio/robust.py                    tests/portfolio/test_borrow_fee_policy.py
src/alphacomb/models/economic.py                     tests/c14/test_c14_dated_production_integration.py
src/alphacomb/models/cells.py
```

**Everything else is fair game**, including `pipelines/04_construct_portfolios.py`,
`src/alphacomb/validation/inference.py`, `prereg/`, and any new module you create. If a
change you need lands inside a frozen file, write it up and we apply it after Absar's
push rather than editing around him.

---

## 1. The five changes

### 1.1 The paper is DEU / IND / JPN, not the United States

Workstream A's production contracts are Germany, India and Japan
(`data/intl_c*/production/{DEU,IND,JPN}/`). Every baseline, every table and every
robustness cut now has a country dimension that the current pipelines do not have.

**Open question neither A nor B has settled:** are the three countries pooled into one
panel, or run as three panels and aggregated? This changes what a "baseline" even means
and how standard errors cluster. It needs an answer before you build comparator tables.
B has asked A; flagging it to you so the three of us settle it together.

### 1.2 The tax-dependent evaluation window is frozen at 2009–2019

From A's pre-results amendment, for tax-dependent international evaluation only:

- Primary after-tax window: **2009-01-01 → 2019-12-31**
- Clean mechanism subwindow: **2014-01-01 → 2018-03-31**, inheriting tax state from the
  2009 ledger inception
- Cold-start ledger at 2009-01-01, no opening lots, no pre-2009 acquisitions
- 1990–2008 remains available for *training and feature construction*, but may not seed
  tax lots or tax state

This was imposed because the window is complete under the frozen C14 source record, and
was declared before any result was seen. It must be reported that way — it is a
pre-registered sample restriction, not a chosen one.

**Conflict to resolve:** `configs/base.yaml` still declares `first_test_year: 1995`,
`last_dev_test_year: 2020` and a `2021-2025` lockbox. Those are the old US settings. The
after-tax international results cannot use them. Someone has to decide whether `base.yaml`
grows a separate international block or the splits are overridden per experiment, and the
answer belongs in the pre-registration before any run.

**Do not edit `configs/base.yaml` to fix this — see §0.1.** Absar's version on Drive is
1,637 bytes to our 1,314 (modified 16:29 on 7 Oct) and may already settle it. Draft the
intended splits in the pre-registration instead, and apply them once his file is merged.

### 1.3 Borrow cost is now a modelled proxy with pre-registered sensitivities

A could not source genuine borrow-fee data. The certified C6 `borrow_fee` column stays
**null**, and a modelled proxy is injected only at the C11/experiment consumer layer:

| Role | Annual rate |
|---|---|
| Baseline | 1.00% |
| Pre-registered sensitivities | 0.30%, 0.60%, 4.30%, 7.00% |

Classification: `MODELLED_PREREGISTERED_PROXY_NOT_OBSERVED`. The legacy 25 bp fallback is
prohibited, and verified unshortable security-months stay ineligible rather than being
priced.

**What this means for you:** the short leg's cost is an assumption, not a measurement, and
the paper has to say so plainly. A five-point sensitivity band belongs in the main results,
not an appendix — if the headline conclusion does not survive 7.00% p.a., that is the
finding. Note that `configs/base.yaml` still carries `borrow_gc_bps_pa: 25.0`; it is stale.

### 1.4 Every comparator must route through the same portfolio machinery

Document 13 §5: preserve the frozen dollar-neutral C11 construction (`gross_max = 2`, beta
and industry neutrality) and **route every comparator through the same stage-04 portfolio
machinery for cost parity**. §3 adds: use the shared cost functions in
`src/alphacomb/portfolio/cost_terms.py`; do not reimplement them in a separate baseline
path.

This is a hard constraint on workstream C's baselines. A simpler baseline implemented with
its own cost accounting would make the net-of-cost comparison meaningless — the headline
claim of the paper is a *net-of-cost* attribution, so any cost asymmetry between the ML
combination and its comparators is a direct confound. Baselines must be alternative
*signal-combination rules* fed into the identical optimiser, not alternative pipelines.

### 1.5 India TERM has an unresolved source question

A's India TERM evidence audit passed the RBI 91-day T-bill auction series as semantically
admissible, but required an independent production rebuild before use. Under the frozen
lag and warm-up, the preview series would activate 235 months earlier than the current
2018-03-31 activation. If that rebuild lands, India's usable state history grows
substantially — which changes the IND panel's effective sample and any robustness cut
conditioned on `TERM`. Treat the IND state history as provisional until A confirms.

---

## 2. The ownership decision from document 02, still open

`docs/handoff/02_NEEDS_FROM_MAHAM.md` §1 flagged that there are two inference
implementations. As of today, `src/alphacomb/stats/` **does not exist in this repository** —
only `src/alphacomb/validation/inference.py` (B's) is here, carrying `newey_west_se`,
`sharpe_se`/`sharpe_test`, `deflated_sharpe`, `pbo_cscv`, `romano_wolf`,
`benjamini_hochberg`, `hansen_spa`, `diebold_mariano` and `inference_report`.

B's position is unchanged and simple: **statistics is workstream C's remit.** B wrote that
module only because the after-tax work needed standard errors immediately. The proposal is
that you take ownership of it as-is, move it to `src/alphacomb/stats/` if you prefer that
home, and B stops touching it. What B needs back is a stable public API and the guarantee
that the trial count feeding `deflated_sharpe` comes from the pre-registration rather than
from however many runs we happen to do.

If you would rather start fresh, say so and B will delete its copy rather than leave two.
Either answer is fine; two implementations is the only unacceptable outcome.

---

## 3. What you can run today

The synthetic and null panels are present and the environment is complete — numpy, pandas,
cvxpy, scikit-learn, scipy, pyarrow, torch, pytest, pyyaml all resolve on system Python
3.12.6. No `.venv` is needed in this checkout. Verified on 7 October: the local suite
collects **240 tests and all 240 pass**, no skips. (A's tree reports 290 — the difference
is A's additions, which haven't reached this checkout.)

```powershell
python -m pytest -q                      # full local suite
python pipelines/02_train_models.py      # 16 factorial cells
python pipelines/04_construct_portfolios.py
python pipelines/06_after_tax_eval.py
python pipelines/07_adaptive_combine.py
```

`data/null/` is the zero-predictability panel used by the falsification audit (E69) — any
method that produces a positive Sharpe there is broken, and that is the cheapest
correctness check available to you.

Concrete pre-results work that needs no real data:

1. **Settle the pooled-vs-three-panels question** (§1.1) and write the clustering scheme
   that follows from it.
2. **Fix the scenario grid before results exist** (§1.3) — the five borrow rates, the cost
   multipliers, the universe cuts — and get it into `prereg/`. This gates everything.
3. **Write the baseline comparator set** as combination rules inside stage 04 (§1.4):
   equal-weight, IC-weighted, OLS, ridge, and whatever else the design calls for. These can
   be built and tested on synthetic data today and will run unchanged on real data.
4. **Resolve the splits conflict** (§1.2) — in the pre-registration, *not* in
   `configs/base.yaml`, which is frozen and incoming (§0.1).
5. **Decide the inference ownership** (§2).
6. **Draft the table and figure skeletons** against synthetic numbers, clearly watermarked,
   so that when real data arrives the reporting path is already tested.

---

## 4. Status of the three workstreams

| Workstream | Owner | State |
|---|---|---|
| A — data, costs, backtest engine | Absar | Complete and promoted on A's machine. Not yet transported to B. |
| B — ML models, optimiser, risk, interpretation | Harshit | Code-complete on synthetic data. Real-data integration blocked on receipt of A's bundle. |
| C — baselines, statistics, robustness, reporting | Maham | Not blocked. Six items above are on the critical path. |

```ini
REAL_RESULTS_INSPECTED = NO
PRODUCTION_PROMOTED    = YES (on A's machine only)
RECEIVED_BY_B          = NO
GITHUB_WRITTEN         = NO
```
