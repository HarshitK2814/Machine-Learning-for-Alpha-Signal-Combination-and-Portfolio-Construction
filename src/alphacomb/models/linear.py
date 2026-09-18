"""Linear cells: ridge on signals (static) and on signals plus state interactions (conditional)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from .base import grid


class RidgeCell:
    """Ridge regression on standardised features; the linear arm of the factorial design.

    ``n_members`` > 1 fits bootstrap replicas so the cell can also report forecast uncertainty
    (contract C9's ``unc_sd``), which is what the uncertainty factor switches on.
    """

    def __init__(self, alpha: float = 1.0, n_members: int = 1, seed: int = 0):
        self.alpha = float(alpha)
        self.n_members = int(n_members)
        self.seed = int(seed)
        self.models: list[Ridge] = []
        self.mu_: np.ndarray | None = None
        self.sd_: np.ndarray | None = None

    def _standardise(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            self.mu_ = np.nanmean(X, axis=0)
            self.sd_ = np.nanstd(X, axis=0)
            self.sd_[self.sd_ < 1e-8] = 1.0
        Z = (np.nan_to_num(X, nan=0.0) - self.mu_) / self.sd_
        return np.clip(Z, -8, 8)

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str], target: str = "y") -> "RidgeCell":
        X = train[features].to_numpy(dtype="float32")
        y = train[target].to_numpy(dtype="float64")
        Z = self._standardise(X, fit=True)
        rng = np.random.default_rng(self.seed)
        self.models = []
        for m in range(self.n_members):
            if self.n_members == 1:
                idx = np.arange(len(Z))
            else:
                idx = rng.choice(len(Z), size=len(Z), replace=True)
            model = Ridge(alpha=self.alpha, fit_intercept=True, solver="lsqr")
            model.fit(Z[idx], y[idx])
            self.models.append(model)
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        Z = self._standardise(test[features].to_numpy(dtype="float32"))
        preds = np.column_stack([m.predict(Z) for m in self.models])
        out = pd.DataFrame(index=test.index)
        out["score"] = preds.mean(axis=1)
        out["unc_sd"] = preds.std(axis=1, ddof=1) if self.n_members > 1 else np.nan
        return out

    @property
    def coefficients(self) -> np.ndarray:
        return np.mean([m.coef_ for m in self.models], axis=0)


def candidates(models_cfg: dict, conditional: bool, n_members: int = 1, seed: int = 0):
    """(model, params) pairs for the linear arm, honouring the configured grid."""
    key = "conditional_linear" if conditional else "ridge"
    alphas = models_cfg[key]["alpha_grid"]
    for a in grid({"alpha": list(alphas)}):
        params = {"model": "ridge", "conditional": conditional, "n_members": n_members, **a}
        yield RidgeCell(alpha=a["alpha"], n_members=n_members, seed=seed), params
