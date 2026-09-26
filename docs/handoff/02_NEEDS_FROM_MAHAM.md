# What Harshit needs from Maham — workstream C → B

**22 September 2026.**

---

## 0. The short answer

**Workstream B is not blocked on Maham.** Unlike the data dependency, nothing here stops development.
But there is **one decision that needs settling this week**, and it is not a small one.

---

## 1. The decision that has to be made first: who owns the statistics

**There are now two inference implementations in this project, and that is one too many.**

While workstream C's `src/alphacomb/stats/` was being built, I built
`src/alphacomb/validation/inference.py` — because the after-tax and overhang work needed standard
errors immediately and could not wait. It currently contains:

| Function | What it does |
|---|---|
| `newey_west_se` | HAC standard errors |
| `sharpe_se`, `sharpe_test` | Lo (2002) autocorrelation + Mertens/Christie higher-moment corrections |
| `deflated_sharpe` | Bailey & López de Prado, with the trial count from the pre-registration |
| `pbo_cscv` | probability of backtest overfitting via CSCV |
| `romano_wolf` | StepM with a stationary bootstrap |
| `benjamini_hochberg` | FDR control |
| `hansen_spa` | SPA with recentring |
| `diebold_mariano` | forecast comparison |
| `inference_report` | assembles the above into one table |

That overlaps workstream C's remit almost exactly (NW, LW2008, CW/DM, SPA, StepM, MCS, DSR, PBO).

**I am not arguing that mine should win.** Statistics is your workstream and you should own it. What
cannot happen is two implementations producing two numbers for the same quantity in the same paper —
a referee who finds that has found a reason to reject. Three ways to resolve it, in my order of
preference:

1. **You own it; mine is deleted and its call sites repointed at yours.** Cleanest. I would ask only
   that your versions cover the list above, since the tax work depends on all of them, and that we
   check your implementation and mine agree on the same input before mine is removed — if they
   disagree, that disagreement is itself worth understanding before either is trusted.
2. **You own it; mine survives as a test oracle only**, never called in the pipeline, used to
   cross-check yours. Some value, more clutter.
3. **I keep the tax-specific ones, you own everything else**, with a hard boundary written down.
   Least clean; I would only take this if you would rather not absorb the tax-side requirements.

**Please pick one.** I will do the work of whichever you choose — including deleting my own module.

---

## 2. Baselines — what I need, and the one rule that matters

**The rule: write your baselines as contract C9 and pass them through stage 04.** Do not build a
separate portfolio construction path.

```python
from alphacomb.portfolio import grinold_alpha            # the same scaling the cells use
from alphacomb.contracts import paths, write_table
write_table(frame, paths.predictions_path("baseline_ew", run_id), "predictions")
# then: python pipelines/04_construct_portfolios.py --strategies baseline_ew
```

The reason is comparability, and it is the thing most likely to be got wrong. If a baseline gets its
own portfolio construction, then any difference in net performance between a baseline and a cell is
a mixture of *model* and *portfolio machinery*, and the paper's central comparison becomes
uninterpretable. Same optimiser, same risk model, same cost model, same constraints — only the alpha
differs. I have made the equivalent mistake myself on the adaptive layer (I compared an
alpha-blend-then-optimise against a mean of separately-optimised returns, which was not a
like-for-like benchmark and inverted the conclusion), so this is a warning from experience rather
than pedantry.

Baselines the design calls for: naive equal-weight, linear, KNS SDF, linear PPP, banding.

## 3. Statistics I need run on workstream B's outputs

Whoever ends up owning §1, these are the numbers the tax and frontier work needs:

| # | What | On what | Why it matters |
|---|---|---|---|
| 1 | **Deflated Sharpe** with the honest trial count | every cell and baseline | At the naive N (539) nothing survives — expected max 0.727 against a best of 0.695. With the pre-registered N (64) the hurdle falls to 0.465. **The trial count must come from `prereg/PLAN_001`, not from counting fits**, and the distinction needs stating in the text. |
| 2 | **PBO** via CSCV | the full cell set | The reviewer-facing answer to "you tried sixteen cells" |
| 3 | **Romano-Wolf StepM** | the cell family | Family-wise error across the factorial |
| 4 | **Hansen SPA**, recentred | cells vs the best baseline | "Is the best cell better than the best baseline, allowing for selection" |
| 5 | **NW and Lo/Mertens Sharpe SEs** | after-tax NAV series | Every after-tax Sharpe must be computed on the NAV series that actually paid the tax, not on a pre-tax series with a tax number subtracted |
| 6 | **Diebold-Mariano** | cell vs baseline forecasts | Forecast-level comparison |

**One request specific to the tax work:** the inference must run on the **after-tax** series, and the
after-tax series is non-Gaussian in a way that matters — loss harvesting truncates the left tail and
the §1211(b) ordinary-offset cap puts a kink in it. The higher-moment Sharpe correction is not
optional here.

## 4. Reporting

| Artefact | Note |
|---|---|
| Tables and LaTeX export | Workstream C owns these |
| Figures | I have built the after-tax figures in `_build/figures_aftertax.py` with a validated palette (`_build/validate_figure_palettes.py` enforces contrast and colourblind separation). Please either use that palette or tell me yours so the paper is visually consistent — mixed palettes across a paper read as careless. |
| The closest-prior-art table | **Please keep this maintained.** It is the standing defence against claiming published novelty, and it needs to survive to submission rather than being a one-off. |

## 5. What Maham should not have to do

Re-implement alpha scaling, the optimiser, the risk model, the tax ledger or the trial log. If a
statistic needs something extra out of a model, ask me rather than re-fitting it — a re-fit with
different hyperparameters silently becomes a different model and a different trial.

## 6. What I owe Maham

Listed properly in `03_HARSHIT_WORK_COMPLETED.md` and `04_WHO_DOES_WHAT_NEXT.md`. In brief: C9
predictions, C10 weight proposals, C11 weights, C13 trial log, per-split diagnostics, the after-tax
ledger outputs, and the adaptive panel with its benchmarks.

**One caveat to carry:** the C13 trial log is the denominator for the deflated Sharpe. It is
append-only via `contracts/io.log_trial`, and it was corrupted once by a concurrent-append bug
(fixed 21 September, 23 rows recovered). If a DSR number ever looks implausible, check the trial log
row count first.
