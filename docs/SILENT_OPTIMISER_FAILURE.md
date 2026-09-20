# Silent optimiser failure: a bug that would have become a finding

**Date found:** 20 September 2026, while checking a 216-month walk-forward before reporting it.
**Status:** fixed (`2a1b9e9`), four regression tests, all prior long-run results void and redone.

This is written up rather than just committed because the failure mode generalises, and because a
referee is entitled to ask what we do about it. It is the clearest example we have of the project's
own thesis: **the portfolio construction stage can manufacture a conclusion about the model.**

---

## What happened

The 16-cell design was run over 2003-2020. Four cells got the full 216-month span. Two of them had
quietly collapsed:

| Cell | optimal | optimal_inaccurate | **failed_hold** |
|---|---|---|---|
| `cell_L-S-E-0` | 216 | 0 | 0 |
| `cell_L-S-P-0` | 197 | 19 | 0 |
| `cell_N-S-P-0` | 109 | 14 | **93 (43%)** |
| `cell_N-C-P-0` | 50 | 16 | **150 (69%)** |

`failed_hold` is our fallback when the solver cannot return a solution: keep last month's weights.
It is a reasonable fallback for one month. It is a catastrophe for 150.

**Nothing crashed.** The pipeline completed, wrote a contract-valid weights table, and would have
produced a complete monthly return series with a plausible Sharpe ratio. The series would have
described a portfolio that stopped trading in 2004 and drifted, not the model that named the file.

## Why it is worse than an ordinary bug

Three properties make this class of failure dangerous:

1. **It is silent.** The output is well-formed. Every downstream contract check passes. Only the
   status distribution, which nothing was asserting on, records the problem.
2. **It self-reinforces.** Failure causes the caller to hold weights; held weights drift further
   outside the constraint set; the next month is more likely to fail. A single bad month becomes a
   run of them. That is the difference between 43% and 69%.
3. **It is correlated with the treatment.** The cause is the ADV participation cap, which binds
   hardest in small illiquid names. The synthetic panel plants a reversal effect *specifically in
   small illiquid names*. The nonlinear cells are the ones that can find it, so they are the ones
   that trade those names, so they are the ones that break.

Put those together and the pipeline was on course to report:

> Nonlinearity does not add net-of-cost value.

That is a headline-grade result, it is consistent with parts of the literature, it would have
survived peer review, and it would have been **an artefact of the optimiser**.

## Root cause

Three constraints can each become unreachable in a single month once weights drift, because trading
is capped at ADV participation:

| # | Constraint pair | Infeasible when |
|---|---|---|
| 1 | `abs(w_i) <= pos_cap_i` and `abs(w_i - prev_i) <= adv_cap_i` | `abs(prev_i) - adv_cap_i > pos_cap_i` |
| 2 | `norm1(w) <= gross_max` and `abs(dw) <= adv_cap` | `sum(abs(prev)) - sum(adv_cap) > gross_max` |
| 3 | `sum(w) == 0` and `abs(dw) <= adv_cap` | `abs(sum(prev)) > sum(adv_cap)` |

All three are the same mistake: **a bound written as if the portfolio could be rebuilt from scratch
each month, imposed on a problem where it can only be nudged.** A position that appreciates above
its cap cannot always be traded back inside it before the next rebalance.

## Fix

Each bound relaxes to exactly the minimum feasibility requires, and no further:

```
pos_cap_i  ->  max(pos_cap_i, abs(prev_i) - adv_cap_i)
gross_max  ->  max(gross_max, sum(abs(prev)) - sum(adv_cap))
sum(w) == 0  ->  abs(sum(w)) <= max(0, abs(sum(prev)) - sum(adv_cap))
```

The relaxation shrinks by `adv_cap` every month, so an over-cap position is forced back inside the
cap at the participation limit rather than being frozen or expected to teleport. That is what a
desk does. In the normal case - a book already inside its constraints - all three are identical to
the originals, and `net_slack` is exactly zero.

`project()` is deliberately untouched: a weight *proposal* is not a position, so there is no drift
to accommodate and dollar neutrality stays a hard equality.

**Visibility, not just correctness.** `gross_cap`, `net_slack` and `cap_relaxed` are written to
diagnostics. A relaxation that binds is now reported rather than silently changing what the
constraint means.

### Also: solver status escalation

CLARABEL reported `optimal_inaccurate` on this problem's scaling - trade caps near `1e-6` against a
gross budget of 2 - where SCS returns a clean `optimal` with an objective agreeing to five
significant figures. So CLARABEL's *answer* was fine and its *status* was not. `construct()` now
takes the first genuinely optimal solution and falls back to the best inaccurate one, recording
which solver answered. On the worst-affected cell, 30 sampled months went from 23 inaccurate / 7
optimal to 30 optimal (SCS 22, CLARABEL 8).

## What the tests are for

`tests/portfolio/test_cap_feasibility.py`, four tests, including the walk-forward cascade itself.

Writing them is what found causes 2 and 3. The first version of the test still **failed** after the
per-name fix was in; after the gross fix it still **skipped**, because the dollar-neutral equality
was unreachable in the fixture. Each time, the test was reporting that the fix was incomplete. A
skipped test is not a passing test.

## What this changes in the project

1. **An assertion, not an eyeball.** *(done)* Stage 04 counts `optimal / optimal_inaccurate /
   failed_hold` per strategy, writes them to `manifest_portfolios.csv`, and **exits non-zero** when
   the held share exceeds `--max-held-share` (default 2%). The weights are still written, but the
   run fails, so a stale portfolio cannot reach a results table unnoticed.
2. **Report the status distribution.** *(done)* Stage 06 joins `held_share` from the manifest onto
   every row of `summary_after_tax.csv` and warns when a strategy is stale, or when the share is
   unknown because the manifest predates the check. A reader never has to take on trust that the
   optimiser succeeded.
3. **It belongs in the paper.** The credibility layer already argues that the construction stage can
   create apparent alpha (`docs/FALSIFICATION_AUDIT.md`). This is the same argument running the
   other way: the construction stage can also *destroy* apparent alpha, selectively, in the arm that
   trades the hardest names. Any factorial attribution across model families has to demonstrate that
   its optimiser succeeded equally often in every cell, or the attribution is measuring solver
   behaviour. We have not seen that check in any paper in the tracker.

## Reproduce the diagnosis

```bash
# per-month structural infeasibility count, before the fix
python - <<'PY'
# |prev_i| - adv_cap_i > pos_cap_i  =>  the feasible interval for w_i is empty
PY
python -m pytest tests/portfolio/test_cap_feasibility.py -q
python pipelines/04_construct_portfolios.py --strategies cell_N-C-P-0
# statuses must now be {'optimal': 216}
```
