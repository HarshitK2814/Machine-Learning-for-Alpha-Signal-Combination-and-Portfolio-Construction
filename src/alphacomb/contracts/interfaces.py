"""Frozen interfaces between workstreams, and the definition of the 16 factorial cells. SHARED FILE.

Cell code: ``<form>-<conditioning>-<objective>-<uncertainty>``

* form:         L = linear, N = nonlinear
* conditioning: S = static, C = state-conditional
* objective:    P = prediction loss, E = economic net-of-cost loss
* uncertainty:  0 = none, U = ensemble-uncertainty shrinkage

Example: ``N-C-E-U`` is the full model (experiment E27 + E28).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import pandas as pd

FORMS = {"L": "linear", "N": "nonlinear"}
CONDITIONING = {"S": "static", "C": "state"}
OBJECTIVES = {"P": "prediction", "E": "economic"}
UNCERTAINTY = {"0": "none", "U": "ensemble_shrinkage"}

# Experiment IDs from Workbook 4 (the uncertainty variant additionally belongs to E28).
CELL_EXPERIMENTS = {
    ("L", "S", "P"): "E20", ("N", "S", "P"): "E21", ("L", "C", "P"): "E22", ("N", "C", "P"): "E23",
    ("L", "S", "E"): "E24", ("N", "S", "E"): "E25", ("L", "C", "E"): "E26", ("N", "C", "E"): "E27",
}


@dataclass(frozen=True)
class CellSpec:
    form: str          # "L" | "N"
    conditioning: str  # "S" | "C"
    objective: str     # "P" | "E"
    uncertainty: str   # "0" | "U"

    @staticmethod
    def parse(code: str) -> "CellSpec":
        parts = code.strip().upper().split("-")
        if len(parts) != 4 or parts[0] not in FORMS or parts[1] not in CONDITIONING \
                or parts[2] not in OBJECTIVES or parts[3] not in UNCERTAINTY:
            raise ValueError(f"bad cell code '{code}'; expected e.g. 'N-C-E-U'")
        return CellSpec(*parts)

    @property
    def code(self) -> str:
        return f"{self.form}-{self.conditioning}-{self.objective}-{self.uncertainty}"

    @property
    def experiment(self) -> str:
        base = CELL_EXPERIMENTS[(self.form, self.conditioning, self.objective)]
        return base if self.uncertainty == "0" else f"{base}+E28"

    @property
    def is_economic(self) -> bool:
        return self.objective == "E"

    @property
    def is_conditional(self) -> bool:
        return self.conditioning == "C"

    @property
    def is_nonlinear(self) -> bool:
        return self.form == "N"

    @property
    def uses_uncertainty(self) -> bool:
        return self.uncertainty == "U"

    def contrasts(self) -> dict[str, int]:
        """Orthogonal +/-1 coding used by the factorial decomposition (experiment E29)."""
        x_n = 1 if self.is_nonlinear else -1
        x_c = 1 if self.is_conditional else -1
        x_e = 1 if self.is_economic else -1
        x_u = 1 if self.uses_uncertainty else -1
        return {
            "x_nonlinear": x_n, "x_state": x_c, "x_economic": x_e, "x_uncertainty": x_u,
            "state_x_economic": x_c * x_e, "nonlinear_x_economic": x_n * x_e,
            "nonlinear_x_state": x_n * x_c, "uncertainty_x_economic": x_u * x_e,
        }

    def describe(self) -> str:
        return (f"{FORMS[self.form]}, {CONDITIONING[self.conditioning]}, "
                f"{OBJECTIVES[self.objective]} loss, uncertainty={UNCERTAINTY[self.uncertainty]}")


ALL_CELLS: list[CellSpec] = [
    CellSpec(f, c, o, u) for f in "LN" for c in "SC" for o in "PE" for u in ("0", "U")
]


@runtime_checkable
class PredictionModel(Protocol):
    """Prediction-loss cells and baselines (produce contract C9)."""

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str], target: str) -> "PredictionModel": ...

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        """Returns columns ``score`` and optionally ``unc_sd`` aligned to ``test``."""


@runtime_checkable
class WeightPolicy(Protocol):
    """Economic-objective cells (produce contract C10)."""

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str]) -> "WeightPolicy": ...

    def propose(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        """Returns column ``w_prop`` aligned to ``test``."""


@runtime_checkable
class RiskModelProvider(Protocol):
    """Contract C7 (Harshit)."""

    def load(self, date) -> object: ...


@runtime_checkable
class CostModel(Protocol):
    """Contract C6 consumer (Absar owns the implementation)."""

    def trade_cost(self, dw: pd.Series, cost_row: pd.DataFrame, cfg: dict) -> pd.Series: ...
