"""Interpretation tests (workstream B): importance, implied weights and mechanism regressions."""
from __future__ import annotations

import numpy as np
import pandas as pd

from alphacomb.contracts.interfaces import CellSpec
from alphacomb.interpret import (economic_feature_importance, implied_theme_weights,
                                 limits_to_arbitrage_tilts, state_dependence, statistical_importance)
from alphacomb.models import RidgeCell, build_design
from alphacomb.risk import RiskCache, StructuralRiskModel

SPEC = CellSpec.parse("L-S-P-0")


def test_economic_importance_finds_the_planted_themes(small_panel):
    df, features = build_design(small_panel, SPEC, horizon=1)
    train = df[(df["date"] < "2001-01-31") & df["y"].notna()]
    test = df[(df["date"] >= "2001-01-31") & (df["date"] < "2002-01-31") & df["ret_next"].notna()]
    model = RidgeCell(alpha=10.0).fit(train, train, features.all)
    risk = RiskCache(StructuralRiskModel(small_panel))
    imp = economic_feature_importance(model, test, features.all, small_panel.signal_meta, risk, ic=0.03,
                                      aum=1e9, impact_k=1.0, commission_bps=1.0)
    assert set(imp.columns) >= {"theme", "economic_importance"}
    assert len(imp) >= 10
    planted = {"value", "quality", "momentum"}
    top = set(imp.head(6)["theme"])
    assert planted & top, f"at least one planted theme should rank highly, got {list(imp.head(6)['theme'])}"


def test_statistical_importance_for_linear_model(small_panel):
    df, features = build_design(small_panel, SPEC, horizon=1)
    train = df[df["y"].notna()]
    model = RidgeCell(alpha=1.0).fit(train, train, features.all)
    imp = statistical_importance(model, train.head(2000), features.all, small_panel.signal_meta)
    assert (imp["statistical_importance"] >= 0).all()
    assert len(imp) > 5


def test_implied_theme_weights_recover_a_known_tilt(small_panel):
    df, features = build_design(small_panel, SPEC, horizon=1)
    sample = df[df["date"].between("2001-01-31", "2001-12-31")]
    theme = features.theme_cols[0]
    weights = sample[["date", "permno", theme]].rename(columns={theme: "w"})
    weights["w"] = weights.groupby("date")["w"].transform(lambda s: 0.01 * (s - s.mean()) / (s.std() + 1e-9))
    implied = implied_theme_weights(weights, sample, features.theme_cols)
    assert len(implied) == sample["date"].nunique()
    assert implied[theme].mean() > 0            # the portfolio is built to hold that theme
    others = [c for c in features.theme_cols if c != theme]
    assert implied[theme].mean() > implied[others].mean().max()


def test_state_dependence_regression_returns_t_stats(small_panel):
    rng = np.random.default_rng(0)
    dates = pd.date_range("1995-01-31", periods=120, freq="ME")
    states = pd.DataFrame({"date": dates, "MKTVOL": rng.normal(size=120), "BEAR": rng.integers(0, 2, 120).astype(float)})
    implied = pd.DataFrame({"date": dates,
                            "thm_momentum": 0.01 - 0.02 * states["MKTVOL"] + rng.normal(0, 0.001, 120),
                            "thm_value": rng.normal(0, 0.001, 120)})
    out = state_dependence(implied, states, ["thm_momentum", "thm_value"], ["MKTVOL", "BEAR"])
    mom = out[(out["theme"] == "thm_momentum") & (out["state"] == "MKTVOL")].iloc[0]
    assert mom["coefficient"] < 0 and mom["t_stat"] < -5      # planted negative relationship recovered
    val = out[(out["theme"] == "thm_value") & (out["state"] == "MKTVOL")].iloc[0]
    assert abs(val["t_stat"]) < 5


def test_limits_to_arbitrage_tilts(small_panel):
    df, _ = build_design(small_panel, SPEC, horizon=1)
    sample = df[df["date"] == "2001-06-30"].copy()
    weights = sample[["date", "permno"]].copy()
    small = sample["me"] < sample["me"].median()
    weights["w"] = np.where(small, 0.01, -0.01)               # long small, short large by construction
    tilts = limits_to_arbitrage_tilts(weights, sample)
    assert tilts["size_tilt"].iloc[0] < 0                     # long leg is smaller than the short leg
    assert np.isfinite(tilts["spread_tilt"].iloc[0])
