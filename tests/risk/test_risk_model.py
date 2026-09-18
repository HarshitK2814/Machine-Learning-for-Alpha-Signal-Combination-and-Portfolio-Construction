"""Risk model tests (workstream B): shape, positive semi-definiteness, diversification and PIT."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.risk import StructuralRiskModel, bias_statistic

DATE = pd.Timestamp("2000-12-31")


@pytest.fixture(scope="module")
def model(small_panel):
    return StructuralRiskModel(small_panel).prepare()


def test_shapes_and_positive_semidefinite(model):
    rm = model.load(DATE)
    assert rm.B.shape[0] > 30 and rm.B.shape[1] == rm.F.shape[0] == rm.F.shape[1]
    assert (rm.D > 0).all()
    F = rm.F.to_numpy()
    assert np.allclose(F, F.T, atol=1e-12)
    assert np.linalg.eigvalsh(F).min() > -1e-10


def test_diversification_reduces_predicted_risk(model):
    rm = model.load(DATE)
    n = len(rm.B)
    equal = pd.Series(np.ones(n) / n, index=rm.B.index)
    single = pd.Series(np.zeros(n), index=rm.B.index)
    single.iloc[0] = 1.0
    assert rm.volatility(equal) < rm.volatility(single)
    assert 0.02 < rm.volatility(equal) < 1.5   # plausible annualised volatility


def test_long_short_portfolio_has_lower_risk_than_long_only(model):
    rm = model.load(DATE)
    n = len(rm.B)
    idx = rm.B.index
    long_only = pd.Series(np.ones(n) / n, index=idx)
    ls = pd.Series(np.where(np.arange(n) < n // 2, 1.0, -1.0), index=idx)
    ls = ls / ls.abs().sum()
    assert rm.volatility(ls) < rm.volatility(long_only)


def test_factor_exposure_matches_manual_calculation(model):
    rm = model.load(DATE)
    w = pd.Series(np.linspace(-1, 1, len(rm.B)), index=rm.B.index)
    w = w / w.abs().sum()
    manual = float((rm.B["beta"] * w).sum())
    assert rm.factor_exposure(w, "beta") == pytest.approx(manual)


def test_point_in_time_truncating_future_data_changes_nothing(small_panel, truncated_panel):
    full = StructuralRiskModel(small_panel).prepare().load(DATE)
    trunc = StructuralRiskModel(truncated_panel).prepare().load(DATE)
    common = full.B.index.intersection(trunc.B.index)
    assert len(common) > 30
    np.testing.assert_allclose(full.F.to_numpy(), trunc.F.to_numpy(), rtol=1e-8, atol=1e-12)
    np.testing.assert_allclose(full.D.loc[common].to_numpy(), trunc.D.loc[common].to_numpy(), rtol=1e-6, atol=1e-12)


def test_bias_statistic_is_about_one_for_a_correct_model():
    rng = np.random.default_rng(0)
    vol = pd.Series(np.full(5000, 0.05))
    realised = pd.Series(rng.normal(0, 0.05, 5000))
    assert bias_statistic(realised, vol) == pytest.approx(1.0, abs=0.05)
    assert bias_statistic(realised * 2, vol) > 1.5   # underestimated risk is detected
