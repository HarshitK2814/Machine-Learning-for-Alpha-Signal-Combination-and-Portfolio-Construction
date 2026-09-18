"""Complexity ladder: random Fourier features, ridgeless regression and sparsity-in-complexity.

Implements levels A2 and A3 of design v2 (see ``docs/DESIGN_V2_FRONTIER.md``).

* **A2, dense**: random Fourier features (Rahimi & Recht 2007) with ridge/ridgeless regression, the
  construction behind the "virtue of complexity" results (Kelly, Malamud & Zhou 2024; Didisheim,
  Ke, Kelly & Malamud 2023). Complexity is indexed by ``c = P / T`` (features per observation);
  c > 1 is the interpolating regime.
* **A3, sparse**: the same feature space with an L1 (basis-pursuit style) selection, testing the
  2026 claim that complexity pays through *sparse discovery* rather than density
  (Afsharhajari & Li 2026).

Both arms share the random feature map, so the dense/sparse comparison is clean: only the penalty
changes. The ridge parameter and the L1 strength are chosen on validation like every other
hyperparameter, and every fitted configuration is logged as a trial.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, Ridge

from .base import grid


class RandomFourierFeatures:
    """Fixed random feature map x -> sqrt(2/P) * cos(W x * gamma + b).

    The map is drawn once per fit with a fixed seed, so the feature space is identical across the
    dense and sparse arms and across hyperparameter values.
    """

    def __init__(self, n_features: int, gamma: float = 1.0, seed: int = 0):
        self.n_features = int(n_features)
        self.gamma = float(gamma)
        self.seed = int(seed)
        self.W_: np.ndarray | None = None
        self.b_: np.ndarray | None = None
        self.mu_: np.ndarray | None = None
        self.sd_: np.ndarray | None = None

    def fit(self, X: np.ndarray) -> "RandomFourierFeatures":
        rng = np.random.default_rng(self.seed)
        self.mu_ = np.nanmean(X, axis=0)
        self.sd_ = np.nanstd(X, axis=0)
        self.sd_[self.sd_ < 1e-8] = 1.0
        d = X.shape[1]
        self.W_ = rng.normal(0.0, np.sqrt(2.0 * self.gamma), size=(d, self.n_features))
        self.b_ = rng.uniform(0, 2 * np.pi, size=self.n_features)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        Z = np.clip((np.nan_to_num(X, nan=0.0) - self.mu_) / self.sd_, -8, 8)
        proj = Z @ self.W_ + self.b_
        return np.sqrt(2.0 / self.n_features) * np.cos(proj)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)


class ComplexityCell:
    """Random-feature regression with either a dense (ridge/ridgeless) or sparse (L1) penalty.

    Parameters
    ----------
    complexity:
        Target ratio of features to training rows, ``c = P / T``. ``c >= 1`` puts the model in the
        interpolating regime that the virtue-of-complexity literature studies.
    penalty:
        ``"ridge"`` for the dense arm (``alpha`` near zero is ridgeless) or ``"l1"`` for the sparse
        arm (basis-pursuit style selection).
    """

    def __init__(self, complexity: float = 1.0, penalty: str = "ridge", alpha: float = 1e-6,
                 gamma: float = 1.0, max_features: int = 6000, n_members: int = 1, seed: int = 0):
        if penalty not in {"ridge", "l1"}:
            raise ValueError("penalty must be 'ridge' or 'l1'")
        self.complexity = float(complexity)
        self.penalty = penalty
        self.alpha = float(alpha)
        self.gamma = float(gamma)
        self.max_features = int(max_features)
        self.n_members = int(n_members)
        self.seed = int(seed)
        self.maps_: list[RandomFourierFeatures] = []
        self.models_: list = []
        self.n_selected_: int | None = None

    def _n_features(self, n_rows: int) -> int:
        return int(np.clip(round(self.complexity * n_rows), 16, self.max_features))

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str], target: str = "y") -> "ComplexityCell":
        X = train[features].to_numpy(dtype="float32")
        y = train[target].to_numpy(dtype="float64")
        p = self._n_features(len(X))
        self.maps_, self.models_ = [], []
        rng = np.random.default_rng(self.seed)
        for m in range(self.n_members):
            rff = RandomFourierFeatures(p, gamma=self.gamma, seed=self.seed + m)
            Z = rff.fit_transform(X)
            if self.n_members > 1:
                idx = rng.choice(len(Z), size=len(Z), replace=True)
                Z, yy = Z[idx], y[idx]
            else:
                yy = y
            if self.penalty == "ridge":
                model = Ridge(alpha=max(self.alpha, 1e-10), fit_intercept=True, solver="lsqr")
            else:
                model = Lasso(alpha=max(self.alpha, 1e-8), fit_intercept=True, max_iter=3000, selection="random",
                              random_state=self.seed + m)
            model.fit(Z, yy)
            self.maps_.append(rff)
            self.models_.append(model)
        if self.penalty == "l1":
            self.n_selected_ = int(np.mean([(np.abs(m.coef_) > 1e-12).sum() for m in self.models_]))
        else:
            self.n_selected_ = p
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        X = test[features].to_numpy(dtype="float32")
        preds = np.column_stack([model.predict(rff.transform(X)) for rff, model in zip(self.maps_, self.models_)])
        out = pd.DataFrame(index=test.index)
        out["score"] = preds.mean(axis=1)
        out["unc_sd"] = preds.std(axis=1, ddof=1) if self.n_members > 1 else np.nan
        return out

    @property
    def effective_complexity(self) -> float:
        """Selected features per observation; equals ``complexity`` for the dense arm."""
        if not self.maps_:
            return float("nan")
        return float(self.n_selected_) / max(len(self.models_[0].coef_), 1) * self.complexity


def candidates(complexity_grid=(0.25, 1.0, 4.0), ridge_alphas=(1e-8, 1e-4, 1e-2),
               l1_alphas=(1e-5, 1e-4), gamma: float = 1.0, n_members: int = 1, seed: int = 0,
               fast: bool = False, arms=("dense", "sparse")):
    """(model, params) pairs for the complexity ladder.

    The dense and sparse arms share the same random feature map for a given complexity and seed, so
    a difference between them is attributable to the penalty rather than to the feature draw.
    """
    if fast:
        complexity_grid, ridge_alphas, l1_alphas = (0.5, 2.0), (1e-6,), (1e-4,)
    for c in complexity_grid:
        if "dense" in arms:
            for a in ridge_alphas:
                params = {"model": "rff_dense", "complexity": c, "alpha": a, "gamma": gamma,
                          "n_members": n_members}
                yield ComplexityCell(complexity=c, penalty="ridge", alpha=a, gamma=gamma,
                                     n_members=n_members, seed=seed), params
        if "sparse" in arms:
            for a in l1_alphas:
                params = {"model": "rff_sparse", "complexity": c, "alpha": a, "gamma": gamma,
                          "n_members": n_members}
                yield ComplexityCell(complexity=c, penalty="l1", alpha=a, gamma=gamma,
                                     n_members=n_members, seed=seed), params


def spectrum_diagnostic(panel: pd.DataFrame, feature_cols: list[str], max_months: int | None = None) -> dict:
    """Eigenvalue concentration of the feature covariance (the AIPT diagnostic).

    Kelly et al. (2025) argue that complexity pays only when the factor structure is *not*
    concentrated in a few dominant eigenvalues. We report the share of variance in the top
    eigenvalues and the effective rank, so the paper can say when the complexity ladder should help
    rather than only whether it did.
    """
    dates = sorted(panel["date"].unique())
    if max_months:
        dates = dates[-max_months:]
    sub = panel[panel["date"].isin(dates)]
    X = sub[feature_cols].to_numpy(dtype="float64")
    X = X - X.mean(axis=0, keepdims=True)
    cov = np.cov(X, rowvar=False)
    vals = np.clip(np.linalg.eigvalsh(cov)[::-1], 0, None)
    total = vals.sum()
    if total <= 0:
        return {"effective_rank": float("nan"), "top1_share": float("nan"), "top5_share": float("nan")}
    share = vals / total
    entropy = -np.sum(np.where(share > 0, share * np.log(share), 0.0))
    return {
        "n_features": len(feature_cols), "n_obs": int(len(X)),
        "top1_share": float(share[0]), "top5_share": float(share[:5].sum()),
        "top10_share": float(share[:10].sum()), "effective_rank": float(np.exp(entropy)),
        "concentration_verdict": ("concentrated - complexity unlikely to pay"
                                  if share[:5].sum() > 0.8 else
                                  "diffuse - complexity may pay (AIPT logic)"),
    }
