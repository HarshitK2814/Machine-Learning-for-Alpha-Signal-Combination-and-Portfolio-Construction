# PLAN_002 — withdrawn, unused

**Written:** 8 October 2026, workstream B
**Withdrawn:** 8 October 2026, same day, before any use
**Superseded by:** `AMENDMENT_001A_international_scenario_freeze_2026-10-08.md`

## Status

```ini
RESULTS_PRODUCED_UNDER_THIS_PLAN = NONE
RUNS_EXECUTED                    = NONE
WITHDRAWN_BEFORE_ANY_INSPECTION  = YES
```

`PLAN_002_international_after_tax.json` is retained on disk. A pre-registration is never deleted,
even an unused one — the record of what was contemplated is part of what makes the surviving plan
credible.

## Why it was written

PLAN_001 pre-registered a United States 1995-2020 panel with a 2021-2025 lockbox. Workstream A's
7 October promotion replaced that setting with Germany, India and Japan and froze the
tax-dependent window at 2009-2019. Reading PLAN_001's sample as no longer existing, workstream B
wrote a fresh plan for the new setting, with **N = 70**.

## Why it was withdrawn

Workstream A specified the amendment route instead: keep PLAN_001's grid, keep its fingerprint
`cae8140b7e2b7ee4`, keep **N = 64**, and freeze only the empirical setting the plan never pinned
down. That is the better call, for a reason worth recording:

**The grid did not change.** PLAN_002 would have reset the deflation hurdle on the basis of a
change to the *setting*, not to the *search*. N exists to price how much specification search
produced the reported number, and no extra searching happened. A new, smaller-hurdle N would have
been unearned.

## The one substantive disagreement, preserved

PLAN_002 counted the five workstream-C baselines into the trial count (64 + 6 = 70). Amendment 001A
does not.

Both positions are defensible and the distinction is real:

- **PLAN_002's view:** N in Bailey and López de Prado counts strategies that *could have been
  reported*. Twenty-one strategies were run; twenty-one could have been reported.
- **Amendment 001A's view (adopted):** the baselines are reported *unconditionally*, whatever they
  show. They are not competing for "best strategy" status, so they do not contribute selection bias
  to the ML result. Only the 64 ML configurations are selected among.

001A adopts the second and discloses the edge case the first was right about: `BASE-RIDGE` chooses
its penalty on validation, so the ridge comparator is itself selected and its own deflation should
use N = 2.

This file exists so the choice is visible to a referee rather than invisible in a diff.
