"""The complexity ladder must be calibrated, or it measures the opposite of what it claims.

Two defaults were wrong and both inverted the result:

* ``gamma=1.0`` on a 170-dimensional standardised design. For an RBF kernel exp(-gamma ||x-y||^2)
  the typical squared distance between standardised rows is about 2d, so gamma belonged near
  1/(2*170) = 0.003. At gamma=1 the kernel is effectively a delta function and every random
  feature is noise.
* a ridge grid of ``(1e-8, 1e-4, 1e-2)`` - effectively ridgeless. In a random-features regression
  the penalty has to be large enough to control a P-dimensional fit; at that grid every rung sat in
  the noise-fitting regime.

Measured together, validation IC *fell* with parameterisation - 0.0232 at P=200 down to 0.0003 at
P=4000 - which is the virtue of complexity running backwards. Nothing raised an error. A test that
only checks "does it fit and predict" would have passed throughout.

These tests check the thing that actually matters: that more parameterisation does not destroy the
signal, and that the ladder is not dominated by a plain linear model.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.models.base import rank_ic
from alphacomb.models.complexity import ComplexityCell, RandomFourierFeatures, candidates


def _panel(n: int = 4000, d: int = 20, seed: int = 0):
    """A panel with a genuinely learnable signal: two linear terms and one interaction."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d))
    y = 0.6 * X[:, 0] + 0.4 * X[:, 1] + 0.5 * X[:, 0] * X[:, 1] + rng.normal(0, 1.0, n)
    cols = [f"sig_{i:02d}" for i in range(d)]
    frame = pd.DataFrame(X, columns=cols)
    frame["y"] = y
    frame["date"] = pd.to_datetime("2020-01-31") + pd.to_timedelta(rng.integers(0, 24, n) * 30, unit="D")
    frame["permno"] = np.arange(n)
    return frame, cols


def test_default_bandwidth_is_the_median_heuristic_not_one():
    """gamma=None must resolve to ~1/(2d) at fit time, not to the old hard-coded 1.0."""
    rff = RandomFourierFeatures(n_features=64, gamma=None, seed=0)
    rff.fit(np.random.default_rng(0).normal(size=(500, 170)))
    assert rff.gamma == pytest.approx(1.0 / (2 * 170))
    assert rff.gamma < 0.01, "a bandwidth near 1.0 degenerates the kernel on a wide design"


def test_default_ridge_is_not_effectively_ridgeless():
    """The old default of 1e-6 put every rung in the noise-fitting regime."""
    assert ComplexityCell().alpha >= 1.0
    grid = sorted({p["alpha"] for _, p in candidates(arms=("dense",))})
    assert max(grid) >= 1e3, f"ridge grid tops out too low to control a large P: {grid}"


def test_more_features_does_not_destroy_the_signal():
    """The regression: at the shipped defaults, IC must not collapse as P grows.

    This is deliberately weak - it does not assert that complexity *helps*, only that it does not
    invert. Asserting a virtue of complexity on a small synthetic panel would be asserting someone
    else's empirical result.
    """
    frame, cols = _panel()
    train, val = frame.iloc[:3000], frame.iloc[3000:]
    ics = []
    for P in (64, 256, 1024):
        model = ComplexityCell(complexity=P / len(train), max_features=P, seed=0)
        model.fit(train, val, cols, "y")
        pred = model.predict(val, cols)["score"].to_numpy()
        ics.append(rank_ic(pred, val["y"].to_numpy(), val["date"]))

    assert all(np.isfinite(ics)), ics
    assert ics[-1] > 0, f"the largest rung has no signal at all: {ics}"
    assert ics[-1] > 0.5 * max(ics), f"IC collapsed as P grew, the calibration bug is back: {ics}"


def test_ladder_is_not_dominated_by_plain_linear_ridge():
    """If a linear ridge beats every rung, the ladder is not measuring complexity."""
    from sklearn.linear_model import Ridge

    frame, cols = _panel()
    train, val = frame.iloc[:3000], frame.iloc[3000:]
    linear = Ridge(alpha=1.0).fit(train[cols].to_numpy(), train["y"].to_numpy())
    base = rank_ic(linear.predict(val[cols].to_numpy()), val["y"].to_numpy(), val["date"])

    best = max(
        rank_ic(ComplexityCell(complexity=P / len(train), max_features=P, seed=0)
                .fit(train, val, cols, "y").predict(val, cols)["score"].to_numpy(),
                val["y"].to_numpy(), val["date"])
        for P in (256, 1024)
    )
    # the panel has a real interaction, so the random-feature model should at least match linear
    assert best > 0.8 * base, f"ladder best {best:.4f} vs linear ridge {base:.4f}"


def test_bandwidth_is_recorded_after_fit_for_reproducibility():
    frame, cols = _panel(n=800, d=10)
    model = ComplexityCell(complexity=0.2, max_features=64, seed=0)
    model.fit(frame.iloc[:600], frame.iloc[600:], cols, "y")
    assert model.maps_, "no feature map was fitted"
    assert model.maps_[0].gamma == pytest.approx(1.0 / (2 * len(cols)))
