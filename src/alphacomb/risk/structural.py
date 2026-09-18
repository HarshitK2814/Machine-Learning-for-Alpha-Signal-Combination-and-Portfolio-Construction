"""Structural factor risk model (contract C7, workstream B).

Sigma_t = B_t F_t B_t' + D_t

* ``B_t``: exposures known at t - market beta (rolling regression), 13 theme composites built from
  the signal library, and industry dummies.
* ``F_t``: EWMA covariance of factor returns estimated by monthly cross-sectional WLS regressions
  of realised returns on the *previous* month's exposures.
* ``D_t``: EWMA specific variance, shrunk towards the size-decile mean.

Point-in-time by construction: the factor return of month s uses exposures from s-1 and returns of
month s, and ``load(t)`` only ever consumes factor returns dated <= t. ``test_risk_model.py``
verifies this by rebuilding the model from a truncated panel and comparing outputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd

from ..contracts import DataBundle, load_config
from ..contracts.io import read_yaml
from ..contracts import paths


@dataclass
class RiskModel:
    """Risk model for one month: exposures, factor covariance and specific variances."""

    date: pd.Timestamp
    B: pd.DataFrame          # stocks x factors
    F: pd.DataFrame          # factors x factors (monthly covariance)
    D: pd.Series             # stocks, specific variance (monthly)

    @property
    def permnos(self) -> pd.Index:
        return self.B.index

    def align(self, permnos: pd.Index) -> "RiskModel":
        idx = pd.Index(permnos)
        B = self.B.reindex(idx).fillna(0.0)
        D = self.D.reindex(idx)
        D = D.fillna(D.median() if np.isfinite(D.median()) else 0.01)
        return RiskModel(self.date, B, self.F, D)

    def variance(self, w: pd.Series | np.ndarray) -> float:
        w = self._vec(w)
        fx = self.B.to_numpy().T @ w
        return float(fx @ self.F.to_numpy() @ fx + np.sum(self.D.to_numpy() * w ** 2))

    def volatility(self, w, annualised: bool = True) -> float:
        v = np.sqrt(max(self.variance(w), 0.0))
        return float(v * np.sqrt(12) if annualised else v)

    def factor_exposure(self, w, factor: str) -> float:
        return float(self.B[factor].to_numpy() @ self._vec(w))

    def _vec(self, w) -> np.ndarray:
        if isinstance(w, pd.Series):
            return w.reindex(self.B.index).fillna(0.0).to_numpy()
        arr = np.asarray(w, dtype=float)
        if arr.shape[0] != len(self.B):
            raise ValueError(f"weight vector has {arr.shape[0]} entries, risk model has {len(self.B)} stocks")
        return arr


def _ewma_cov(x: np.ndarray, halflife: float, ridge: float = 0.0) -> np.ndarray:
    n = len(x)
    lam = 0.5 ** (1.0 / halflife)
    w = lam ** np.arange(n - 1, -1, -1)
    w /= w.sum()
    xc = x - np.average(x, axis=0, weights=w)
    cov = (xc * w[:, None]).T @ xc
    if ridge:
        cov = cov + ridge * np.eye(cov.shape[0])
    return cov


def _ewma_var(x: np.ndarray, halflife: float) -> np.ndarray:
    n = x.shape[0]
    lam = 0.5 ** (1.0 / halflife)
    w = lam ** np.arange(n - 1, -1, -1)
    w = w / w.sum()
    mean = np.nansum(x * w[:, None], axis=0)
    dev = np.where(np.isnan(x), 0.0, x - mean)
    mask = (~np.isnan(x)).astype(float) * w[:, None]
    denom = np.clip(mask.sum(axis=0), 1e-6, None)
    return (dev ** 2 * mask).sum(axis=0) / denom


class StructuralRiskModel:
    """Builds and caches monthly risk models from a data bundle (contract C7 provider)."""

    def __init__(self, bundle: DataBundle, cfg: dict | None = None, risk_cfg: dict | None = None):
        self.bundle = bundle
        self.cfg = cfg or load_config("base")
        self.risk_cfg = risk_cfg or read_yaml(paths.REPO_ROOT / "configs" / "risk.yaml")
        self._prepared = False

    # ---------------------------------------------------------------- exposures
    def _theme_composites(self) -> pd.DataFrame:
        meta = self.bundle.signal_meta
        sig = self.bundle.signals
        out = sig[["date", "permno"]].copy()
        for theme, group in meta.groupby("theme"):
            cols = [c for c in group["signal"] if c in sig.columns]
            if cols:
                out[f"thm_{theme}"] = sig[cols].mean(axis=1).astype("float32")
        return out

    def prepare(self) -> "StructuralRiskModel":
        if self._prepared:
            return self
        cfg = self.risk_cfg["estimation"]
        bundle = self.bundle

        panel = bundle.universe[["date", "permno", "me", "ff49"]].merge(
            bundle.targets[["date", "permno", "r_1m"]], on=["date", "permno"], how="left")
        panel = panel.merge(self._theme_composites(), on=["date", "permno"], how="left")
        panel = panel.sort_values(["date", "permno"]).reset_index(drop=True)

        theme_cols = [c for c in panel.columns if c.startswith("thm_")]
        panel[theme_cols] = panel[theme_cols].fillna(0.0)

        # market return per month (value-weighted realised next-month return)
        mkt = panel.dropna(subset=["r_1m"]).groupby("date").apply(
            lambda d: np.average(d["r_1m"], weights=np.clip(d["me"], 1e-6, None)), include_groups=False)
        mkt.name = "mkt"

        # rolling market beta per stock (36m, PIT: uses returns up to the current month)
        rets = panel.pivot_table(index="date", columns="permno", values="r_1m")
        mkt_aligned = mkt.reindex(rets.index)
        window = int(cfg["beta_window_months"])
        cov = rets.rolling(window, min_periods=int(cfg["min_obs"])).cov(mkt_aligned)
        var = mkt_aligned.rolling(window, min_periods=int(cfg["min_obs"])).var()
        beta = cov.div(var, axis=0).shift(1).clip(-1.5, 3.5)  # shift: beta known at the start of t
        beta_long = beta.stack(future_stack=True).rename("beta").reset_index()
        panel = panel.merge(beta_long, on=["date", "permno"], how="left")
        panel["beta"] = panel["beta"].fillna(1.0)

        ind = pd.get_dummies(panel["ff49"].astype(int), prefix="ind", dtype=float)
        self.industry_cols = list(ind.columns)
        panel = pd.concat([panel, ind], axis=1)

        self.factor_cols = ["beta"] + theme_cols + self.industry_cols
        self.panel = panel

        # ---- factor returns: cross-sectional WLS of month-t return on exposures known at t ----
        frets, resid_rows = [], []
        for date, d in panel.groupby("date", sort=True):
            d = d.dropna(subset=["r_1m"])
            if len(d) < len(self.factor_cols) + 10:
                continue
            X = d[self.factor_cols].to_numpy(dtype=float)
            y = d["r_1m"].to_numpy(dtype=float)
            wgt = np.sqrt(np.clip(d["me"].to_numpy(dtype=float), 1e-6, None))
            wgt = wgt / wgt.mean()
            Xw, yw = X * wgt[:, None], y * wgt
            coef, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
            frets.append(pd.Series(coef, index=self.factor_cols, name=date))
            resid_rows.append(pd.DataFrame({"date": date, "permno": d["permno"].to_numpy(),
                                            "resid": y - X @ coef}))
        self.factor_returns = pd.DataFrame(frets).sort_index()
        self.residuals = pd.concat(resid_rows, ignore_index=True)
        self.resid_wide = self.residuals.pivot_table(index="date", columns="permno", values="resid")
        self._prepared = True
        return self

    # ---------------------------------------------------------------- per-date model
    def load(self, date) -> RiskModel:
        """Risk model usable for trading at ``date`` (uses information up to and including ``date``)."""
        self.prepare()
        date = pd.Timestamp(date)
        cfg = self.risk_cfg["estimation"]
        min_obs = int(cfg["min_obs"])

        hist = self.factor_returns.loc[self.factor_returns.index <= date]
        if len(hist) < min_obs:
            hist = self.factor_returns.iloc[: max(min_obs, len(hist))]
        F = _ewma_cov(hist.to_numpy(dtype=float), float(cfg["factor_cov_halflife_months"]),
                      ridge=float(cfg.get("ridge_on_factor_cov", 0.0)))
        F = pd.DataFrame(F, index=self.factor_returns.columns, columns=self.factor_returns.columns)

        cross = self.panel[self.panel["date"] == date]
        if cross.empty:
            raise KeyError(f"no cross-section for {date.date()}")
        B = cross.set_index("permno")[self.factor_cols].astype(float)

        r_hist = self.resid_wide.loc[self.resid_wide.index <= date].tail(120)
        cols = [p for p in B.index if p in r_hist.columns]
        spec = pd.Series(0.0, index=B.index, dtype=float)
        if cols:
            var = _ewma_var(r_hist[cols].to_numpy(dtype=float), float(cfg["specific_halflife_months"]))
            spec.loc[cols] = var
        spec = spec.replace(0.0, np.nan)

        me = cross.set_index("permno")["me"]
        decile = pd.qcut(me.rank(method="first"), 10, labels=False, duplicates="drop")
        group_mean = spec.groupby(decile).transform("median")
        shrink = float(cfg["specific_shrink_to_size_decile"])
        spec = (1 - shrink) * spec.fillna(group_mean) + shrink * group_mean.fillna(spec.median())
        spec = spec.fillna(spec.median() if np.isfinite(spec.median()) else 0.01)
        spec = spec.clip(lower=1e-6)
        return RiskModel(date=date, B=B, F=F, D=spec)

    @lru_cache(maxsize=64)
    def _cached(self, date_str: str) -> RiskModel:  # pragma: no cover - thin cache wrapper
        return self.load(pd.Timestamp(date_str))

    def load_cached(self, date) -> RiskModel:
        return self._cached(str(pd.Timestamp(date).date()))


def bias_statistic(realised_returns: pd.Series, predicted_vol: pd.Series) -> float:
    """Bias statistic for experiment E64: mean squared standardised return.

    A well-calibrated risk model gives a value near 1. Values above 1 mean risk was underestimated,
    which is what factor-alignment problems (Ceria, Saxena & Stubbs 2012) predict for optimised
    portfolios whose alpha model is richer than the risk model.
    """
    z = realised_returns.to_numpy(dtype=float) / np.clip(predicted_vol.to_numpy(dtype=float), 1e-12, None)
    z = z[np.isfinite(z)]
    return float(np.sqrt(np.mean(z ** 2))) if len(z) else float("nan")
