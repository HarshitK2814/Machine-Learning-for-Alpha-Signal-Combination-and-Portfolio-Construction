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

#: Columns the shared cell runner consumes. ``unc_sd`` is required even though a fixed
#: combination rule has no ensemble dispersion: the runner reads it unconditionally.
SCORE_COLUMNS = ["date", "permno", "score", "unc_sd"]


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
    """Prediction frame in the shape the shared cell runner consumes.

    Two details are load-bearing and were wrong until 8 October 2026, when these rules were first
    run through ``run_prediction_cell`` rather than called directly in a unit test:

    * **the index must be ``test``'s index**, because the runner selects per month with
      ``pred.loc[group.index]``. A fresh ``RangeIndex`` raises ``KeyError: None of [...] are in
      the [index]`` the moment the design frame is not 0-based, which it never is after filtering.
    * **``unc_sd`` must exist.** The runner reads it unconditionally. A fixed combination rule has
      no ensemble dispersion, so it is NaN - and that is also why the uncertainty axis of the
      factorial does not apply to a baseline.

    ``RidgeCell.predict`` has always done both; these returned neither, which is the hazard of a
    comparator that is tested but never run.
    """
    out = pd.DataFrame(index=test.index)
    out["date"] = test["date"].to_numpy()
    out["permno"] = test["permno"].to_numpy()
    out["score"] = np.asarray(values, dtype="float64")
    out["unc_sd"] = np.nan
    return out


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


def run_baseline(code: str, bundle, risk, cfg=None, base_cfg: dict | None = None,
                 models_cfg: dict | None = None) -> dict:
    """Run one pre-registered baseline through the shared cell runner and write contract C9.

    Deliberately the same mechanism as ``benchmarks.run_benchmark``: substitute a single fixed
    candidate into the cell runner's candidate list, so the baseline gets the identical design
    matrix, split calendar, lockbox assertion, validation IC, alpha scaling and trial logging that
    every factorial cell gets. Handoff document 13 requirement 5 asks for exactly this, and
    requirement 3 forbids a separate baseline cost path.

    Without this the five comparators existed as tested classes that nothing ran, and the exhibit
    answered "which ML ingredient contributes" while leaving "does any of it beat equal-weighting
    net of costs" unanswered - which is the first question a referee asks.

    A baseline is a static, prediction-loss rule with no uncertainty shrinkage, so it is run under
    the ``L-S-P-0`` cell specification: the nonlinearity and state-dependence axes do not apply to
    a fixed combination rule, and pretending otherwise would put a comparator inside the factorial.
    """
    from ..contracts import new_run_id, paths, splits as split_mod, write_table
    from ..contracts.interfaces import CellSpec
    from ..contracts.io import load_config, read_yaml
    from .base import build_design
    from .cells import CellRunConfig, run_prediction_cell
    import alphacomb.models.cells as cells_module

    model = build(code)                     # raises for anything not pre-registered
    cfg = cfg or CellRunConfig()
    base_cfg = base_cfg or load_config("base")
    models_cfg = models_cfg or read_yaml(paths.REPO_ROOT / "configs" / "models.yaml")
    strategy = f"baseline_{code}"
    run_id = new_run_id(strategy)

    spec = CellSpec.parse("L-S-P-0")
    df, features = build_design(bundle, spec, horizon=cfg.horizon)
    calendar = split_mod.generate(horizon_months=cfg.horizon, cfg=base_cfg,
                                 first_test_year=cfg.first_test_year,
                                 last_test_year=cfg.last_test_year)
    df = df[df["date"] <= calendar[-1].test_end].copy()
    split_mod.assert_not_lockbox(df["date"].unique(), base_cfg)
    risk.warm([d for d in sorted(df["date"].unique())
               if pd.Timestamp(d) >= calendar[0].val_start])

    params = {"baseline": code, "rule": type(model).__name__}
    original = cells_module._candidates
    cells_module._candidates = lambda spec_, models_cfg_, features_, cfg_: [(model, params)]
    try:
        table = run_prediction_cell(spec, df, features, calendar, risk, cfg, base_cfg, models_cfg,
                                    run_id, strategy)
    finally:
        cells_module._candidates = original

    out = paths.predictions_path(strategy, run_id)
    write_table(table, out, "predictions")
    return {"baseline": code, "experiment": "E10-E12", "strategy": strategy, "run_id": run_id,
            "artefact": out, "contract": "predictions", "rows": len(table)}
