"""Baseline signal-combination rules (workstream C, experiments E10-E12).

These are the comparators the ML cells have to beat. Each one is a *rule for combining signals
into a score* and nothing more: the design matrix, split calendar, alpha scaling, optimiser, cost
model and tax ledger are the same objects the factorial cells use.

That is a deliberate constraint, not a convenience. Handoff document 13 requirement 5 says every
comparator must route through the same stage-04 portfolio machinery for cost parity, and
requirement 3 says the shared cost functions must not be reimplemented in a separate baseline path.
The paper's headline claim is a *net-of-cost* attribution, so any asymmetry in how a baseline's
costs are computed would show up as model skill that is really plumbing. The cheapest way to be
wrong here is to give a baseline its own backtest; these classes exist so nobody has to.

The rules
---------
``EqualWeightCell``      average of the z-scored signals. The hardest baseline to beat in the
                         literature and the one referees ask for first.
``ThemeEqualWeightCell`` average of the 13 theme composites, so themes with many signals do not
                         dominate by count. Equal-weight's main weakness is exactly that.
``ICWeightCell``         signals weighted by their trailing rank IC, estimated on the training
                         window only, with negative-IC signals clipped to zero rather than flipped
                         (flipping is a second decision and would need its own pre-registration).
``OLSCell``              pooled OLS of the demeaned target on the signals.
``RidgeBaselineCell``    ridge with the penalty chosen on validation rank IC - the closest linear
                         comparator to the ML cells, and the one that isolates "nonlinearity" as a
                         factorial axis rather than "regularisation".

All five are pre-registered in PLAN_002 as BASE-EW, BASE-THEME-EW, BASE-IC, BASE-OLS, BASE-RIDGE.
Adding a sixth after seeing results would be an unregistered comparator and must be reported as
exploratory.

Interface
---------
Each class exposes ``fit(train, val, features, target="y") -> self`` and
``predict(test, features) -> DataFrame[date, permno, score]``, matching ``RidgeCell`` so the same
runner drives cells and baselines.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .base import rank_ic

SCORE_COLUMNS = ["date", "permno", "score"]


def _standardise_cross_section(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Z-score each column within each date.

    Signals arrive rank-normalised to [-0.5, 0.5] per contract C2, but a simple average still
    over-weights whichever signals happen to have wider realised dispersion in a given month.
    Re-standardising per date makes "equal weight" mean equal weight.
    """
    out = df[cols].astype("float64")
    grouped = out.groupby(df["date"].to_numpy())
    centred = grouped.transform("mean")
    spread = grouped.transform("std").replace(0.0, np.nan)
    return ((out - centred) / spread).fillna(0.0)


def _scores(test: pd.DataFrame, values: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({
        "date": test["date"].to_numpy(),
        "permno": test["permno"].to_numpy(),
        "score": np.asarray(values, dtype="float64"),
    })[SCORE_COLUMNS]


@dataclass
class EqualWeightCell:
    """Equal-weight the z-scored signals. No parameters, nothing fitted."""

    name: str = "BASE-EW"
    _cols: list[str] = field(default_factory=list)

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str],
            target: str = "y") -> "EqualWeightCell":
        self._cols = [c for c in features if c.startswith("sig_")] or list(features)
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        cols = [c for c in (self._cols or features) if c in test.columns]
        if not cols:
            return _scores(test, np.zeros(len(test)))
        return _scores(test, _standardise_cross_section(test, cols).mean(axis=1).to_numpy())


@dataclass
class ThemeEqualWeightCell:
    """Equal-weight the theme composites, so a crowded theme does not win on headcount."""

    name: str = "BASE-THEME-EW"
    _cols: list[str] = field(default_factory=list)

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str],
            target: str = "y") -> "ThemeEqualWeightCell":
        self._cols = [c for c in features if c.startswith("thm_")]
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        cols = [c for c in self._cols if c in test.columns]
        if not cols:
            # No theme composites in this design: fall back to equal-weighting the raw signals
            # rather than returning zeros, so the comparator is still a real strategy.
            cols = [c for c in features if c.startswith("sig_") and c in test.columns]
        if not cols:
            return _scores(test, np.zeros(len(test)))
        return _scores(test, _standardise_cross_section(test, cols).mean(axis=1).to_numpy())


@dataclass
class ICWeightCell:
    """Weight each signal by its trailing rank IC, estimated on the training window only.

    Negative-IC signals are clipped to zero, not sign-flipped. Flipping would assert that the
    in-sample sign reverses out of sample, which is a separate (and much stronger) claim than
    "this signal carries information"; it would need its own pre-registration.
    """

    name: str = "BASE-IC"
    min_abs_ic: float = 0.0
    _weights: dict[str, float] = field(default_factory=dict)

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str],
            target: str = "y") -> "ICWeightCell":
        cols = [c for c in features if c.startswith("sig_")] or list(features)
        frame = train if not train.empty else val
        weights: dict[str, float] = {}
        if not frame.empty and target in frame.columns:
            actual = frame[target].to_numpy()
            dates = frame["date"]
            for col in cols:
                if col not in frame.columns:
                    continue
                ic = rank_ic(frame[col].to_numpy(), actual, dates)
                if np.isfinite(ic) and ic > self.min_abs_ic:
                    weights[col] = float(ic)
        if not weights:  # degenerate window: fall back to equal weight over available signals
            weights = {c: 1.0 for c in cols if c in frame.columns} or {c: 1.0 for c in cols}
        total = sum(weights.values()) or 1.0
        self._weights = {k: v / total for k, v in weights.items()}
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        cols = [c for c in self._weights if c in test.columns]
        if not cols:
            return _scores(test, np.zeros(len(test)))
        z = _standardise_cross_section(test, cols)
        w = np.array([self._weights[c] for c in cols], dtype="float64")
        return _scores(test, z.to_numpy() @ w)


@dataclass
class OLSCell:
    """Pooled OLS of the cross-sectionally demeaned target on the signals.

    Solved with ``lstsq`` rather than a normal-equation inverse: the signal panel is collinear by
    construction (many signals are near-duplicates within a theme), so an explicit inverse is
    numerically unsound here.
    """

    name: str = "BASE-OLS"
    _cols: list[str] = field(default_factory=list)
    _beta: np.ndarray | None = None

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str],
            target: str = "y") -> "OLSCell":
        self._cols = [c for c in features if c.startswith("sig_")] or list(features)
        self._cols = [c for c in self._cols if c in train.columns]
        frame = train.dropna(subset=[target]) if target in train.columns else train
        if frame.empty or not self._cols:
            self._beta = None
            return self
        X = frame[self._cols].to_numpy(dtype="float64")
        y = frame[target].to_numpy(dtype="float64")
        self._beta = np.linalg.lstsq(X, y, rcond=None)[0]
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        if self._beta is None or not self._cols:
            return _scores(test, np.zeros(len(test)))
        cols = [c for c in self._cols if c in test.columns]
        if len(cols) != len(self._cols):
            return _scores(test, np.zeros(len(test)))
        X = test[cols].to_numpy(dtype="float64")
        return _scores(test, X @ self._beta)


@dataclass
class RidgeBaselineCell:
    """Ridge whose penalty is chosen on validation rank IC.

    This is the comparator that makes the factorial's "nonlinearity" axis mean what it says. Without
    it, a nonlinear cell beating OLS could just as easily be regularisation beating no
    regularisation, and the attribution would be reading a penalty as a functional form.
    """

    name: str = "BASE-RIDGE"
    penalties: tuple[float, ...] = (1.0, 10.0, 100.0, 1000.0)
    _cols: list[str] = field(default_factory=list)
    _beta: np.ndarray | None = None
    chosen_penalty: float | None = None

    def _solve(self, X: np.ndarray, y: np.ndarray, lam: float) -> np.ndarray:
        n_features = X.shape[1]
        A = X.T @ X + lam * np.eye(n_features)
        return np.linalg.solve(A, X.T @ y)

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str],
            target: str = "y") -> "RidgeBaselineCell":
        self._cols = [c for c in features if c.startswith("sig_")] or list(features)
        self._cols = [c for c in self._cols if c in train.columns]
        frame = train.dropna(subset=[target]) if target in train.columns else train
        if frame.empty or not self._cols:
            self._beta, self.chosen_penalty = None, None
            return self
        X = frame[self._cols].to_numpy(dtype="float64")
        y = frame[target].to_numpy(dtype="float64")

        scoring = val if (not val.empty and target in val.columns) else frame
        Xv = scoring[[c for c in self._cols]].to_numpy(dtype="float64")
        yv = scoring[target].to_numpy(dtype="float64")

        best, best_ic = None, -np.inf
        for lam in self.penalties:
            beta = self._solve(X, y, lam)
            ic = rank_ic(Xv @ beta, yv, scoring["date"])
            if np.isfinite(ic) and ic > best_ic:
                best, best_ic, self.chosen_penalty = beta, ic, float(lam)
        self._beta = best if best is not None else self._solve(X, y, self.penalties[0])
        if self.chosen_penalty is None:
            self.chosen_penalty = float(self.penalties[0])
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        if self._beta is None or not self._cols:
            return _scores(test, np.zeros(len(test)))
        cols = [c for c in self._cols if c in test.columns]
        if len(cols) != len(self._cols):
            return _scores(test, np.zeros(len(test)))
        return _scores(test, test[cols].to_numpy(dtype="float64") @ self._beta)


#: Pre-registered baseline set (PLAN_002). Keys are the cell codes used in the plan and in
#: ``outputs/trials.csv``; anything not in this mapping is an exploratory comparator.
BASELINES = {
    "BASE-EW": EqualWeightCell,
    "BASE-THEME-EW": ThemeEqualWeightCell,
    "BASE-IC": ICWeightCell,
    "BASE-OLS": OLSCell,
    "BASE-RIDGE": RidgeBaselineCell,
}


def build(code: str):
    """Instantiate a pre-registered baseline by its PLAN_002 code."""
    if code not in BASELINES:
        raise KeyError(
            f"{code!r} is not a pre-registered baseline. PLAN_002 registers {sorted(BASELINES)}. "
            "A new comparator may be reported, but only as exploratory."
        )
    return BASELINES[code]()
