"""Model tests (workstream B): design matrix, learners, uncertainty and the cell runner."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from alphacomb.contracts import read_table, validate
from alphacomb.contracts.interfaces import CellSpec
from alphacomb.models import CellRunConfig, RidgeCell, build_design, run_cell, split_frames
from alphacomb.models.economic import EconomicPolicy, prepare_months
from alphacomb.models.nonlinear import LGBMCell, NNCell
from alphacomb.models.uncertainty import proxy_weights
from alphacomb.risk import RiskCache, StructuralRiskModel

STATIC = CellSpec.parse("L-S-P-0")
COND = CellSpec.parse("L-C-P-0")


@pytest.fixture(scope="module")
def design(small_panel):
    df, features = build_design(small_panel, STATIC, horizon=1)
    return df, features


def test_design_matrix_is_clean_and_demeaned(design):
    df, features = design
    assert len(features.signal_cols) > 100 and features.theme_cols
    assert not features.state_cols and not features.interaction_cols   # static cell sees no states
    assert df[features.all].isna().sum().sum() == 0
    per_month_mean = df.dropna(subset=["y"]).groupby("date")["y"].mean().abs().max()
    assert per_month_mean < 1e-8                                        # cross-sectionally demeaned target


def test_conditional_design_adds_states_and_interactions(small_panel):
    _, features = build_design(small_panel, COND, horizon=1)
    assert features.state_cols, "conditional cells must see the state variables"
    assert len(features.interaction_cols) == len(features.theme_cols) * 6
    assert all("_x_" in c for c in features.interaction_cols)


def test_ridge_recovers_the_planted_signal(design):
    df, features = design
    train = df[(df["date"] < "1999-01-31") & df["y"].notna()]
    test = df[(df["date"] >= "1999-01-31") & df["y"].notna()]
    model = RidgeCell(alpha=10.0).fit(train, train, features.all)
    pred = model.predict(test, features.all)["score"].to_numpy()
    ic = pd.DataFrame({"d": test["date"].to_numpy(), "p": pred, "y": test["y"].to_numpy()}) \
        .groupby("d").apply(lambda d: d["p"].corr(d["y"], method="spearman"), include_groups=False).mean()
    assert ic > 0.01, "ridge should recover the planted linear effects out of sample"


def test_bootstrap_members_produce_uncertainty(design):
    df, features = design
    train = df[(df["date"] < "1998-01-31") & df["y"].notna()]
    test = df[df["date"] == "1999-01-31"]
    single = RidgeCell(alpha=10.0, n_members=1).fit(train, train, features.all).predict(test, features.all)
    ensemble = RidgeCell(alpha=10.0, n_members=5, seed=1).fit(train, train, features.all).predict(test, features.all)
    assert single["unc_sd"].isna().all()
    assert (ensemble["unc_sd"] > 0).mean() > 0.9
    assert ensemble["score"].corr(single["score"]) > 0.9


@pytest.mark.parametrize("factory", [
    lambda: LGBMCell(num_boost_round=60, early_stopping_rounds=10, n_members=2, seed=0),
    lambda: NNCell(layers=(8, 4), max_epochs=3, n_members=2, seed=0, batch_size=4096),
])
def test_nonlinear_cells_fit_and_report_uncertainty(design, factory):
    df, features = design
    train = df[(df["date"] < "1997-01-31") & df["y"].notna()]
    val = df[(df["date"] >= "1997-01-31") & (df["date"] < "1998-01-31") & df["y"].notna()]
    test = df[df["date"] == "1999-01-31"]
    out = factory().fit(train, val, features.all).predict(test, features.all)
    assert np.isfinite(out["score"]).all()
    assert (out["unc_sd"] >= 0).all()


def test_economic_policy_learns_feasible_proposals(small_panel):
    spec = CellSpec.parse("L-S-E-0")
    df, features = build_design(small_panel, spec, horizon=1)
    risk = RiskCache(StructuralRiskModel(small_panel))
    train = df[(df["date"] >= "1995-01-31") & (df["date"] < "1999-01-31")]
    val = df[(df["date"] >= "1999-01-31") & (df["date"] < "2000-01-31")]
    test = df[(df["date"] >= "2000-01-31") & (df["date"] < "2000-07-31")]
    kwargs = dict(risk=risk, aum=1e9, impact_k=1.0, commission_bps=1.0)
    tr, va, te = (prepare_months(x, features.all, **kwargs) for x in (train, val, test))
    assert tr and va and te
    policy = EconomicPolicy(nonlinear=False, gamma=25.0, max_epochs=4, patience=2, seed=0).fit(tr, va)
    proposals = policy.propose(te)
    assert np.isfinite(policy.val_utility_)
    by_month = proposals.groupby("date")["w_prop"]
    assert by_month.sum().abs().max() < 1e-4                      # dollar neutral
    assert by_month.apply(lambda w: w.abs().sum()).sub(2.0).abs().max() < 1e-3   # gross budget respected


def test_proxy_weights_respect_cap_and_neutrality(small_panel):
    risk = RiskCache(StructuralRiskModel(small_panel))
    mr = risk.monthly(pd.Timestamp("2000-12-31"))
    alpha = pd.Series(np.random.default_rng(0).normal(size=len(mr.permnos)), index=pd.Index(mr.permnos))
    w = proxy_weights(alpha, mr, gross=2.0, weight_cap=0.01)
    assert abs(w.sum()) < 1e-9
    assert w.abs().max() <= 0.01 + 1e-12
    assert w.abs().sum() <= 2.0 + 1e-9


@pytest.mark.parametrize("code", ["L-S-P-0", "N-S-P-U", "L-S-E-0"])
def test_run_cell_end_to_end_writes_a_valid_contract(small_panel, tmp_path, monkeypatch, code):
    monkeypatch.setenv("ALPHACOMB_OUTPUTS", str(tmp_path))
    spec = CellSpec.parse(code)
    risk = RiskCache(StructuralRiskModel(small_panel))
    cfg = CellRunConfig(horizon=1, first_test_year=2003, last_test_year=2003, fast=True,
                        uncertainty_members=2, kappa_grid=(0.0, 1.0), economic_max_train_months=60,
                        validation_months_for_kappa=3)
    result = run_cell(spec, small_panel, risk, cfg)
    table = read_table(result["artefact"])
    validate(table, result["contract"])
    assert result["rows"] > 0
    assert set(pd.to_datetime(table["date"]).dt.year) == {2003}       # only the test year is predicted
    trials = pd.read_csv(tmp_path / "trials.csv")
    assert len(trials) >= 1 and (trials["cell"] == code).all()
