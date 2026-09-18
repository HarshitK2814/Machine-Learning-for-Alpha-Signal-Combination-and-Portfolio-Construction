"""Per-month risk-model cache (workstream B).

Building the structural model for every month in a long training window is the slowest part of the
economic-objective cells, and every cell needs the same models. ``RiskCache`` builds them once and
serves numpy views that torch and cvxpy can consume directly.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .structural import RiskModel, StructuralRiskModel


@dataclass
class MonthlyRisk:
    date: pd.Timestamp
    permnos: pd.Index
    B: np.ndarray      # n x k exposures
    L: np.ndarray      # k x k factor covariance factor (F = L L')
    d: np.ndarray      # n specific variances

    def variance(self, w: np.ndarray) -> float:
        fx = self.L.T @ (self.B.T @ w)
        return float(fx @ fx + np.sum(self.d * w ** 2))

    def stock_vol(self) -> np.ndarray:
        common = np.einsum("ij,jk,ik->i", self.B, self.L @ self.L.T, self.B)
        return np.sqrt(np.clip(common + self.d, 1e-12, None))


class RiskCache:
    """Lazily builds and stores monthly risk models."""

    def __init__(self, provider: StructuralRiskModel):
        self.provider = provider.prepare()
        self._models: dict[pd.Timestamp, RiskModel] = {}
        self._monthly: dict[pd.Timestamp, MonthlyRisk] = {}

    def model(self, date) -> RiskModel:
        date = pd.Timestamp(date)
        if date not in self._models:
            self._models[date] = self.provider.load(date)
        return self._models[date]

    def monthly(self, date) -> MonthlyRisk:
        date = pd.Timestamp(date)
        if date not in self._monthly:
            rm = self.model(date)
            F = rm.F.to_numpy(dtype=float)
            vals, vecs = np.linalg.eigh((F + F.T) / 2)
            L = vecs @ np.diag(np.sqrt(np.clip(vals, 0.0, None)))
            self._monthly[date] = MonthlyRisk(date, rm.B.index, rm.B.to_numpy(dtype=float), L,
                                              rm.D.to_numpy(dtype=float))
        return self._monthly[date]

    def warm(self, dates) -> "RiskCache":
        for d in pd.DatetimeIndex(sorted(pd.to_datetime(list(dates)).unique())):
            self.monthly(d)
        return self

    def __len__(self) -> int:
        return len(self._monthly)
