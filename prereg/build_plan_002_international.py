"""Write PLAN_002: the frozen analysis plan for the DEU/IND/JPN after-tax paper.

Why a second plan
-----------------
PLAN_001 was written on 21 September for a United States panel, with a 1995-2020 development
window and a 2021-2025 lockbox. Workstream A's 7 October promotion changed the empirical setting:
the panel is Germany, India and Japan, and the tax-dependent evaluation window is frozen at
2009-01-01 .. 2019-12-31 with a clean mechanism subwindow of 2014-01-01 .. 2018-03-31. PLAN_001's
sample no longer exists, so its trial count cannot be the N that deflates an international Sharpe.

A pre-registration is written once and never edited (``PreRegistration.save`` refuses to overwrite).
So the honest move is a new, separately named plan that says plainly why it supersedes the old one.
That disclosure belongs in the paper.

Why this plan is small
----------------------
The deflated Sharpe ratio is only meaningful if N was fixed before anyone saw a result, and a small
N has to be a fact about the design rather than a claim about intentions. Three choices keep it
small, and each costs something real:

1. **The scenario axes are reported, not searched.** The borrow-fee proxy (five rates) and the cost
   multiplier (four) are *sensitivity dimensions*: every one is reported for the selected
   configuration, and none is used to choose it. They therefore multiply the table count, not the
   trial count. If instead we picked the borrow rate that made the result look best, that would be
   a 20x search and would have to enter N.
2. **One seed.** Seed variation is reported in E56 as a stability diagnostic, not used to select.
3. **Hyperparameters are selected on validation rank IC only** - never on any outcome that appears
   in a results table, and never on anything computed after costs or after tax.

Panel mode
----------
Recorded here as part of the frozen design because it changes what a baseline means and how
standard errors cluster. The choice is ``pooled_fit_separate_construct``: one model trained on the
pooled cross-section, then per-country portfolio construction and per-country tax ledgers.

This is not a preference. C14 tax year-ends differ - Germany and Japan in December, India in March -
so an after-tax ledger spanning the three has no well-defined tax year, and portfolio construction
must be per country regardless. Pooling only the model fit is therefore the option that buys
training data without pretending the tax accounting is unified. If the team overrides this before
the confirmatory run, that is a plan change and needs a new file.

Run ``python prereg/build_plan_002_international.py`` to emit the JSON. It refuses to overwrite.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alphacomb.validation.preregistration import PreRegistration  # noqa: E402

# The 16 factorial cells: Linear/Nonlinear x Static/Conditional x Prediction/Economic loss,
# each with uncertainty shrinkage off ("0") or on ("U").
CELLS = [
    f"{nl}-{st}-{ls}-{un}"
    for nl in ("L", "N")
    for st in ("S", "C")
    for ls in ("P", "E")
    for un in ("0", "U")
]

# Workstream C's baseline comparators. Every one is a *combination rule* fed into the identical
# stage-04 portfolio machinery, so the net-of-cost comparison is not confounded by cost accounting
# (handoff document 13, requirement 5). They are pre-registered so they cannot be added after the
# fact to find a comparator the ML beats.
BASELINES = [
    "BASE-EW",        # equal-weight across signals
    "BASE-IC",        # historical-IC-weighted
    "BASE-OLS",       # pooled OLS of returns on signals
    "BASE-RIDGE",     # ridge, penalty chosen on validation rank IC
    "BASE-THEME-EW",  # equal-weight across the 13 theme composites
]

# Two hyperparameters per cell. Deliberately coarse: a finer grid buys a little fit and a lot of N.
DEFAULT_GRID = {
    "shrinkage": ["low", "high"],
    "capacity": ["small", "large"],
}
# Baselines have no tuning except ridge, whose penalty is the one grid dimension.
BASELINE_GRIDS = {
    "BASE-EW": {},
    "BASE-IC": {},
    "BASE-OLS": {},
    "BASE-RIDGE": {"penalty": ["low", "high"]},
    "BASE-THEME-EW": {},
}

# Reported for the selected configuration; never used to select it.
SENSITIVITY_AXES = {
    "borrow_fee_annual": [0.0030, 0.0060, 0.0100, 0.0430, 0.0700],  # 0.0100 is the baseline
    "cost_multiplier": [0.5, 1.0, 2.0, 3.0],
    "universe": ["all_stocks", "large_only"],
    "panel_mode": ["pooled_fit_separate_construct"],
}

NOTES = """\
Supersedes PLAN_001 (21 September 2026), which pre-registered a United States 1995-2020 panel with
a 2021-2025 lockbox. Workstream A's 7 October promotion replaced that setting with Germany, India
and Japan and froze the tax-dependent evaluation window at 2009-2019. PLAN_001's sample no longer
exists; its trial count cannot deflate an international Sharpe. Both plans are published and the
paper states which one each table uses.

Written BEFORE any real-data result was inspected. At the time of writing, the repository contains
no real-data output of any kind: frozen decision 6B requires that scenarios be fixed before results
are inspected, and that condition is what this file discharges.

The borrow-fee axis is a MODELLED proxy, not an observation. Workstream A could not source genuine
borrow-fee data; certified C6 borrow_fee is null and MODELLED_FLAT_BORROW_PROXY_V1 is injected only
at the C11/experiment layer. The paper must report the full five-rate band in the main results, not
an appendix, and must state that the short leg's cost is an assumption. If the headline conclusion
does not survive 7.00% p.a., that is the finding.

Pre-2009 observations remain available for model training and feature construction. They may not
seed tax lots or tax state: the dated ledger cold-starts on 2009-01-01 with no opening lots.

India's TERM state is provisional. Workstream A's RBI 91-day evidence audit passed as evidence but
requires an independent production rebuild; until that lands, any robustness cut conditioned on
TERM for India is exploratory, not confirmatory.
"""

plan = PreRegistration(
    title=(
        "Net-of-cost, after-tax attribution of ML signal combination across Germany, India and "
        "Japan: nonlinearity, state dependence, cost-aware objective and uncertainty"
    ),
    primary_outcome=(
        "After-tax net return per month of a dollar-neutral long/short book, per country, under "
        "the dated C12 ledger with statutory local-currency tax and point-in-time FX; aggregated "
        "across DEU/IND/JPN by equal country weight. Evaluation window 2009-01-01..2019-12-31."
    ),
    selection_rule=(
        "Within each cell, the configuration with the highest validation rank IC on the expanding "
        "validation window ending one year before each test year. Selection uses rank IC only - "
        "never a net-of-cost, after-tax, or any other quantity that appears in a results table, "
        "and never a sensitivity-axis value."
    ),
    cells=CELLS + BASELINES,
    grids={**{c: DEFAULT_GRID for c in CELLS}, **BASELINE_GRIDS, "default": DEFAULT_GRID},
    n_seeds=1,
    n_refits=11,  # annual refit across the 2009-2019 evaluation window
    lockbox_note=(
        "There is no sealed lockbox in the international design. The 2009-2019 window is the whole "
        "tax-dependent evaluation sample and was frozen by Workstream A on 7 October 2026 because "
        "it is the span the C14 source record covers completely - not because of anything observed "
        "in strategy performance (WORKSTREAM_A_PRE_RESULTS_SAMPLE_AMENDMENT_2026-10-07.md). The "
        "clean mechanism subwindow 2014-01-01..2018-03-31 inherits tax state from the 2009 "
        "inception and is reported separately, not used to select."
    ),
    notes=NOTES,
)


def main() -> int:
    out = Path(__file__).resolve().parent / "PLAN_002_international_after_tax.json"
    saved = plan.save(out)
    print(f"wrote {saved}")
    print(f"  fingerprint      : {plan.fingerprint}")
    print(f"  cells            : {len(plan.cells)}  ({len(CELLS)} factorial + {len(BASELINES)} baselines)")
    print(f"  configurations N : {plan.n_configurations}")
    print(f"  fits             : {plan.n_fits}")
    print()
    print("  sensitivity axes (reported, NOT searched - they do not enter N):")
    for axis, values in SENSITIVITY_AXES.items():
        print(f"    {axis:<20} {values}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
