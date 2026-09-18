"""Runner for the 16 factorial cells (workstream B).

For every walk-forward split a cell:

1. builds its design matrix (signals, plus states and interactions when conditional);
2. fits every hyperparameter candidate on the training window, scores them on validation, and logs
   *all* of them to the trial file (C13);
3. keeps the best candidate and applies it to the test year;
4. prediction cells write scores and Grinold-scaled alphas (C9); economic cells write raw weight
   proposals (C10).

Nothing in this module ever reads test-period data before predicting it, and the split calendar
refuses lockbox dates unless the team has frozen the specification.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..contracts import DataBundle, Split, log_trial, new_run_id, paths, splits as split_mod, write_table
from ..contracts.interfaces import CellSpec
from ..contracts.io import load_config, read_yaml
from ..portfolio.alpha_scaling import grinold_alpha, shrink_by_uncertainty
from ..risk.cache import RiskCache
from . import attention, complexity, economic, linear, nonlinear
from .base import build_design, rank_ic, select_by_validation, split_frames
from .conformal import per_stock_uncertainty, split_conformal
from .uncertainty import select_kappa

log = logging.getLogger(__name__)


@dataclass
class CellRunConfig:
    horizon: int = 1
    first_test_year: int | None = None
    last_test_year: int | None = None
    fast: bool = False
    seed: int = 0
    uncertainty_members: int = 5
    kappa_grid: tuple[float, ...] = (0.0, 0.5, 1.0, 2.0, 4.0)
    economic_max_train_months: int = 240
    validation_months_for_kappa: int = 12
    gamma: float = 25.0
    # design v2: rungs of the functional-form ladder used inside the nonlinear arm
    # options: "gbdt_nn" (A1), "complexity_dense" (A2), "complexity_sparse" (A3), "attention" (A4)
    form_ladder: tuple[str, ...] = ("gbdt_nn",)
    # design v2: "ensemble" dispersion (D1) or calibrated "conformal" intervals (D2)
    uncertainty_method: str = "ensemble"
    conformal_alpha: float = 0.1
    conformal_calibration_months: int = 24
    diagnostics: list = field(default_factory=list)


class _MoEAdapter:
    """Gives the mixture-of-experts the same fit signature as the other prediction cells."""

    def __init__(self, inner: nonlinear.MoECell, state_cols: list[str]):
        self.inner, self.state_cols = inner, state_cols

    def fit(self, train, val, features, target="y"):
        self.inner.fit(train, val, features, target, state_cols=self.state_cols)
        return self

    def predict(self, test, features):
        return self.inner.predict(test, features)


def _candidates(spec: CellSpec, models_cfg: dict, features, cfg: CellRunConfig):
    members = cfg.uncertainty_members if spec.uses_uncertainty else 1
    if spec.is_nonlinear:
        ladder = tuple(cfg.form_ladder or ("gbdt_nn",))
        if "gbdt_nn" in ladder:
            yield from nonlinear.candidates(models_cfg, spec.is_conditional, n_members=members, seed=cfg.seed,
                                            fast=cfg.fast)
        arms = tuple(a for a, key in (("dense", "complexity_dense"), ("sparse", "complexity_sparse"))
                     if key in ladder)
        if arms:
            yield from complexity.candidates(n_members=members, seed=cfg.seed, fast=cfg.fast, arms=arms)
        if "attention" in ladder:
            yield from attention.candidates(n_members=members, seed=cfg.seed, fast=cfg.fast)
        if spec.is_conditional and features.state_cols:
            moe_cfg = models_cfg["mixture_of_experts"]
            inner = nonlinear.MoECell(n_experts=int(moe_cfg["experts"]),
                                      expert_layers=tuple(moe_cfg["expert_layers"]),
                                      max_epochs=12 if cfg.fast else 30, n_members=members, seed=cfg.seed)
            yield _MoEAdapter(inner, features.state_cols), {"model": "moe", "conditional": True,
                                                            "experts": int(moe_cfg["experts"]),
                                                            "n_members": members}
    else:
        yield from linear.candidates(models_cfg, spec.is_conditional, n_members=members, seed=cfg.seed)


def _month_maps(frame: pd.DataFrame, cols: list[str]) -> dict:
    return {pd.Timestamp(d): g.set_index("permno")[cols] for d, g in frame.groupby("date")}


def run_prediction_cell(spec: CellSpec, df: pd.DataFrame, features, calendar: list[Split], risk: RiskCache,
                        cfg: CellRunConfig, base_cfg: dict, models_cfg: dict, run_id: str, strategy: str) -> pd.DataFrame:
    rows, diagnostics = [], []
    costs_cfg = base_cfg["costs"]
    for split in calendar:
        train, val, test = split_frames(df, split)
        if len(train) < 2000 or val.empty or test.empty:
            log.warning("%s %s: insufficient data (train=%d, val=%d, test=%d)", spec.code, split.label,
                        len(train), len(val), len(test))
            continue
        best, val_ic, params = select_by_validation(
            list(_candidates(spec, models_cfg, features, cfg)), train, val, features.all,
            run_id, strategy, spec.code, split, seed=cfg.seed)

        kappa = 0.0
        if spec.uses_uncertainty:
            val_pred = best.predict(val, features.all)
            tail = sorted(val["date"].unique())[-cfg.validation_months_for_kappa:]
            val_alphas, val_unc, val_costs, val_rets = {}, {}, {}, {}
            for date in tail:
                mask = val["date"] == date
                sub = val.loc[mask]
                rm = risk.model(date)
                scores = pd.Series(val_pred.loc[mask, "score"].to_numpy(), index=sub["permno"].to_numpy())
                val_alphas[pd.Timestamp(date)] = grinold_alpha(scores, rm, ic=max(val_ic, 0.005))
                unc_series = pd.Series(val_pred.loc[mask, "unc_sd"].to_numpy(), index=sub["permno"].to_numpy())
                val_unc[pd.Timestamp(date)] = unc_series
                val_costs[pd.Timestamp(date)] = sub.set_index("permno")[["spread", "sigma_d", "adv_usd", "borrow_fee"]]
                val_rets[pd.Timestamp(date)] = sub.set_index("permno")["ret_next"]
            kappa, kappa_scores = select_kappa(val_alphas, val_costs, val_rets, risk, cfg.kappa_grid, val_unc,
                                               float(costs_cfg["aum_usd_2020"]), float(costs_cfg["impact_k"]),
                                               float(costs_cfg["commission_bps"]))
            log_trial(run_id, strategy, spec.code, {"kappa_selection": kappa_scores, "chosen_kappa": kappa},
                      cfg.seed, split.train_end, float(max(kappa_scores.values()) if kappa_scores else 0.0))

        pred = best.predict(test, features.all)
        conformal_report = None
        if spec.uses_uncertainty and cfg.uncertainty_method == "conformal":
            # calibrate on validation months (strictly before the test year), then apply to the test
            val_pred_for_cal = best.predict(val, features.all)
            frame = pd.concat([
                pd.DataFrame({"date": val["date"].to_numpy(), "permno": val["permno"].to_numpy(),
                              "score": val_pred_for_cal["score"].to_numpy(), "y_true": val["y"].to_numpy(),
                              "unc_sd_ensemble": val_pred_for_cal["unc_sd"].to_numpy()}),
                pd.DataFrame({"date": test["date"].to_numpy(), "permno": test["permno"].to_numpy(),
                              "score": pred["score"].to_numpy(), "y_true": np.nan,
                              "unc_sd_ensemble": pred["unc_sd"].to_numpy()}),
            ], ignore_index=True)
            result = split_conformal(frame, calibration_months=cfg.conformal_calibration_months,
                                     alpha=cfg.conformal_alpha)
            calibrated = per_stock_uncertainty(frame, result)
            frame["unc_calibrated"] = calibrated.to_numpy()
            lookup = frame.set_index(["date", "permno"])["unc_calibrated"]
            keys = pd.MultiIndex.from_arrays([test["date"].to_numpy(), test["permno"].to_numpy()])
            pred = pred.copy()
            pred["unc_sd"] = lookup.reindex(keys).to_numpy()
            conformal_report = {"mean_coverage": result.mean_coverage, "target": result.target_coverage}

        for date, group in test.groupby("date"):
            rm = risk.model(date)
            idx = group["permno"].to_numpy()
            scores = pd.Series(pred.loc[group.index, "score"].to_numpy(), index=idx)
            alpha = grinold_alpha(scores, rm, ic=max(val_ic, 0.005))
            unc = pd.Series(pred.loc[group.index, "unc_sd"].to_numpy(), index=idx)
            if spec.uses_uncertainty and kappa > 0:
                alpha = shrink_by_uncertainty(alpha, unc, kappa)
            keep = alpha.index
            rows.append(pd.DataFrame({
                "date": pd.Timestamp(date), "permno": keep.astype("int32"),
                "score": scores.reindex(keep).to_numpy(), "alpha": alpha.to_numpy(),
                "unc_sd": unc.reindex(keep).to_numpy(),
            }))
        test_ic = rank_ic(pred["score"].to_numpy(), test["y"].to_numpy(), test["date"])
        diagnostics.append({"cell": spec.code, "split": split.label, "val_rank_ic": val_ic,
                            "test_rank_ic": test_ic, "kappa": kappa, "params": params,
                            "uncertainty_method": cfg.uncertainty_method if spec.uses_uncertainty else "none",
                            "conformal_coverage": (conformal_report or {}).get("mean_coverage")})
        log.info("%s %s: val IC %.4f, test IC %.4f, kappa %.2f", spec.code, split.label, val_ic, test_ic, kappa)
    cfg.diagnostics.extend(diagnostics)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["date", "permno", "score", "alpha", "unc_sd"])


def run_economic_cell(spec: CellSpec, df: pd.DataFrame, features, calendar: list[Split], risk: RiskCache,
                      cfg: CellRunConfig, base_cfg: dict, models_cfg: dict, run_id: str, strategy: str) -> pd.DataFrame:
    rows, diagnostics = [], []
    costs_cfg = base_cfg["costs"]
    members = cfg.uncertainty_members if spec.uses_uncertainty else 1
    for split in calendar:
        train, val, test = split_frames(df, split)
        if train.empty or val.empty or test.empty:
            continue
        kwargs = dict(risk=risk, aum=float(costs_cfg["aum_usd_2020"]), impact_k=float(costs_cfg["impact_k"]),
                      commission_bps=float(costs_cfg["commission_bps"]))
        train_months = economic.prepare_months(train, features.all, max_months=cfg.economic_max_train_months, **kwargs)
        val_months = economic.prepare_months(val, features.all, **kwargs)
        test_months = economic.prepare_months(test, features.all, **kwargs)
        if not train_months or not val_months or not test_months:
            log.warning("%s %s: no usable months for the economic policy", spec.code, split.label)
            continue

        best, best_val, best_params = None, -np.inf, None
        for policy, params in economic.candidates(models_cfg, spec.is_nonlinear, gamma=cfg.gamma, seed=cfg.seed,
                                                  n_members=members, fast=cfg.fast):
            policy.fit(train_months, val_months)
            log_trial(run_id, strategy, spec.code, params, cfg.seed, split.train_end, policy.val_utility_)
            if policy.val_utility_ > best_val:
                best, best_val, best_params = policy, policy.val_utility_, params
        if best is None:  # pragma: no cover
            continue
        proposals = best.propose(test_months)
        rows.append(proposals[["date", "permno", "w_prop"]])
        diagnostics.append({"cell": spec.code, "split": split.label, "val_utility": best_val, "params": best_params})
        log.info("%s %s: validation utility %.5f", spec.code, split.label, best_val)
    cfg.diagnostics.extend(diagnostics)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["date", "permno", "w_prop"])


def run_cell(spec: CellSpec | str, bundle: DataBundle, risk: RiskCache, cfg: CellRunConfig | None = None,
             base_cfg: dict | None = None, models_cfg: dict | None = None, run_id: str | None = None) -> dict:
    """Run one factorial cell across the walk-forward calendar and write its contract artefact."""
    spec = CellSpec.parse(spec) if isinstance(spec, str) else spec
    cfg = cfg or CellRunConfig()
    base_cfg = base_cfg or load_config("base")
    models_cfg = models_cfg or read_yaml(paths.REPO_ROOT / "configs" / "models.yaml")
    run_id = run_id or new_run_id(f"cell_{spec.code}")
    strategy = f"cell_{spec.code}"

    df, features = build_design(bundle, spec, horizon=cfg.horizon,
                               interaction_states=models_cfg["conditional_linear"]["interaction_states"])
    calendar = split_mod.generate(horizon_months=cfg.horizon, cfg=base_cfg,
                                  first_test_year=cfg.first_test_year, last_test_year=cfg.last_test_year)
    # keep only the window the calendar actually uses, then prove that window excludes the lockbox
    df = df[df["date"] <= calendar[-1].test_end].copy()
    split_mod.assert_not_lockbox(df["date"].unique(), base_cfg)

    needed = df.loc[df["date"].between(calendar[0].train_start, calendar[-1].test_end), "date"].unique()
    risk.warm(sorted(needed)[-(cfg.economic_max_train_months + 400):] if spec.is_economic else
              [d for d in sorted(needed) if pd.Timestamp(d) >= calendar[0].val_start])

    if spec.is_economic:
        table = run_economic_cell(spec, df, features, calendar, risk, cfg, base_cfg, models_cfg, run_id, strategy)
        out = paths.weight_proposals_path(strategy, run_id)
        contract = "weight_proposals"
    else:
        table = run_prediction_cell(spec, df, features, calendar, risk, cfg, base_cfg, models_cfg, run_id, strategy)
        out = paths.predictions_path(strategy, run_id)
        contract = "predictions"
    if table.empty:
        raise RuntimeError(f"cell {spec.code} produced no output; check the split calendar and data coverage")
    write_table(table, out, contract)

    diag = pd.DataFrame(cfg.diagnostics)
    diag_path = paths.models_dir(strategy, run_id) / "diagnostics.csv"
    diag_path.parent.mkdir(parents=True, exist_ok=True)
    diag.to_csv(diag_path, index=False)
    return {"cell": spec.code, "experiment": spec.experiment, "strategy": strategy, "run_id": run_id,
            "artefact": out, "contract": contract, "rows": len(table), "diagnostics": diag_path}
