"""Pre-registration of the design grid. The only honest way to make the trial count small.

Why this module exists
----------------------
On 20 September 2026 the inference layer was run against the project's own results for the first
time. The real trial log held **539** fitted configurations. The expected maximum Sharpe ratio from
a 539-trial search under a no-skill null is **0.727**. The best after-tax Sharpe we had produced was
**0.695**.

Every reported strategy sat *below* what pure specification search would deliver by chance. Nothing
survived deflation. And this was on synthetic data where we planted the effects ourselves.

There are two ways to respond to that. One is to argue the trial count down after seeing the
results - to claim that only some of the 539 were "really" part of selecting the reported strategy.
That is unfalsifiable and every referee has seen it before.

The other is to **fix the grid in advance, publish the count, and be held to it.** Then a small N is
a fact about the design rather than a claim about intentions. That is what this module enforces.

How it works
------------
1. Before the confirmatory run, write a plan: the cells, the hyperparameter grid per cell, the
   selection rule, the primary outcome. ``PreRegistration.save`` hashes it and freezes it.
2. The plan's ``n_planned_trials`` is computed from the grid, not asserted. It is the N that goes
   into the deflated Sharpe ratio.
3. During the run, every fitted configuration is checked against the plan. Anything outside it is
   recorded as an **exploratory** trial, which may be reported but never as a confirmatory result.
4. ``audit`` compares the plan against ``outputs/trials.csv`` after the fact and reports drift.
   If more configurations were fitted than planned, it says so, in the output, with the number.

The point is not bureaucracy. It is that the deflated Sharpe ratio is only meaningful if N is honest,
and N is only honest if it was fixed before anyone saw a result.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import pandas as pd


@dataclass
class PreRegistration:
    """A frozen analysis plan.

    ``grids`` maps a cell code to a dict of hyperparameter name -> list of values. The planned trial
    count is the sum over cells of the product of grid lengths, times ``n_seeds``, times the number
    of walk-forward refits.
    """

    title: str
    primary_outcome: str
    selection_rule: str
    cells: list[str]
    grids: dict[str, dict[str, list]]
    n_seeds: int = 1
    n_refits: int = 1
    lockbox_note: str = ""
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""

    # ------------------------------------------------------------------ counting
    @property
    def n_planned_trials(self) -> int:
        """The N that goes into the deflated Sharpe ratio. Computed, never asserted."""
        total = 0
        for cell in self.cells:
            grid = self.grids.get(cell, self.grids.get("default", {}))
            combos = 1
            for values in grid.values():
                combos *= max(len(values), 1)
            total += combos
        return int(total * max(self.n_seeds, 1) * max(self.n_refits, 1))

    def planned_configurations(self, cell: str) -> list[dict]:
        grid = self.grids.get(cell, self.grids.get("default", {}))
        if not grid:
            return [{}]
        keys = list(grid)
        return [dict(zip(keys, combo)) for combo in product(*(grid[k] for k in keys))]

    def is_planned(self, cell: str, params: dict) -> bool:
        """Is this configuration inside the frozen plan? Anything else is exploratory."""
        grid = self.grids.get(cell, self.grids.get("default"))
        if grid is None:
            return False
        for key, values in grid.items():
            if key not in params:
                return False
            if params[key] not in values:
                return False
        return True

    # ------------------------------------------------------------------ freezing
    @property
    def fingerprint(self) -> str:
        """Stable hash of the plan. Changing any grid value changes this."""
        payload = json.dumps(
            {k: v for k, v in asdict(self).items() if k != "created_utc"},
            sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        if path.exists():
            raise FileExistsError(
                f"{path} already exists. A pre-registration is written once. To change the plan, "
                "write a new file with a new name and explain in the paper why the plan changed - "
                "that disclosure is the whole point.")
        path.parent.mkdir(parents=True, exist_ok=True)
        blob = asdict(self)
        blob["fingerprint"] = self.fingerprint
        blob["n_planned_trials"] = self.n_planned_trials
        path.write_text(json.dumps(blob, indent=2, default=str), encoding="utf-8")
        return path

    @staticmethod
    def load(path: str | Path) -> "PreRegistration":
        blob = json.loads(Path(path).read_text(encoding="utf-8"))
        stored = blob.pop("fingerprint", None)
        blob.pop("n_planned_trials", None)
        plan = PreRegistration(**blob)
        if stored and stored != plan.fingerprint:
            raise ValueError(
                f"pre-registration at {path} has been edited since it was frozen "
                f"(stored {stored}, recomputed {plan.fingerprint}). The trial count it claims "
                "cannot be trusted, and neither can any deflated Sharpe ratio built on it.")
        return plan


def audit(plan: PreRegistration, trials: pd.DataFrame) -> dict:
    """Compare the frozen plan against what was actually fitted.

    Returns the honest N for the deflated Sharpe ratio, and the drift. A run that fitted more
    configurations than it planned has a larger effective search than the plan claims, and the
    report says so rather than quietly using the smaller number.
    """
    actual = len(trials)
    planned = plan.n_planned_trials

    exploratory = 0
    if {"cell", "params_json"}.issubset(trials.columns):
        for _, row in trials.iterrows():
            try:
                params = json.loads(row["params_json"])
            except (TypeError, ValueError):
                exploratory += 1
                continue
            if not plan.is_planned(str(row["cell"]), params):
                exploratory += 1

    confirmatory = actual - exploratory
    drift = actual - planned
    return {
        "fingerprint": plan.fingerprint,
        "planned_trials": planned,
        "actual_trials": actual,
        "confirmatory_trials": confirmatory,
        "exploratory_trials": exploratory,
        "drift": drift,
        # Conservative by construction: if more was fitted than planned, the larger number is the
        # honest N. Shrinking N after seeing results is the failure mode this module prevents.
        "n_for_deflation": int(max(actual, planned)),
        "clean": bool(drift <= 0 and exploratory == 0),
        "verdict": ("plan followed; use the planned count"
                    if drift <= 0 and exploratory == 0 else
                    f"PLAN DRIFT: {actual} fitted vs {planned} planned, {exploratory} outside the "
                    f"grid. Report the larger count and disclose the drift."),
    }


def factorial_plan(cells: list[str], grid: dict[str, list], n_seeds: int = 1,
                   n_refits: int = 1, **kwargs) -> PreRegistration:
    """Convenience constructor for a factorial design where every cell shares one grid."""
    return PreRegistration(cells=cells, grids={"default": grid}, n_seeds=n_seeds,
                           n_refits=n_refits, **kwargs)
