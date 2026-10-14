"""Nonlinear cells: gradient boosting, a neural-network ensemble, and a state-gated mixture of experts."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import grid


class LGBMCell:
    """LightGBM regression on the signal matrix (plus state columns for conditional cells)."""

    def __init__(self, num_leaves: int = 31, learning_rate: float = 0.05, min_data_in_leaf: int = 500,
                 feature_fraction: float = 0.8, bagging_fraction: float = 0.8, lambda_l2: float = 0.0,
                 num_boost_round: int = 500, early_stopping_rounds: int = 50, n_members: int = 1, seed: int = 0):
        self.params = dict(num_leaves=num_leaves, learning_rate=learning_rate, min_data_in_leaf=min_data_in_leaf,
                           feature_fraction=feature_fraction, bagging_fraction=bagging_fraction,
                           lambda_l2=lambda_l2, objective="regression", verbosity=-1, bagging_freq=1)
        self.num_boost_round = int(num_boost_round)
        self.early_stopping_rounds = int(early_stopping_rounds)
        self.n_members = int(n_members)
        self.seed = int(seed)
        self.boosters: list = []
        self.feature_names_: list[str] = []

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str], target: str = "y") -> "LGBMCell":
        import lightgbm as lgb

        self.feature_names_ = list(features)
        self.boosters = []
        Xtr = train[features].to_numpy(dtype="float32")
        ytr = train[target].to_numpy(dtype="float64")
        Xva = val[features].to_numpy(dtype="float32")
        yva = val[target].to_numpy(dtype="float64")
        for m in range(self.n_members):
            params = dict(self.params, seed=self.seed + m, bagging_seed=self.seed + m, feature_fraction_seed=self.seed + m)
            dtrain = lgb.Dataset(Xtr, label=ytr, feature_name=list(features))
            dval = lgb.Dataset(Xva, label=yva, reference=dtrain)
            booster = lgb.train(params, dtrain, num_boost_round=self.num_boost_round, valid_sets=[dval],
                                callbacks=[lgb.early_stopping(self.early_stopping_rounds, verbose=False)])
            self.boosters.append(booster)
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        X = test[features].to_numpy(dtype="float32")
        preds = np.column_stack([b.predict(X, num_iteration=b.best_iteration) for b in self.boosters])
        out = pd.DataFrame(index=test.index)
        out["score"] = preds.mean(axis=1)
        out["unc_sd"] = preds.std(axis=1, ddof=1) if self.n_members > 1 else np.nan
        return out


class NNCell:
    """Feed-forward network ensemble (Gu, Kelly & Xiu style NN3) with early stopping.

    Ensemble members differ by seed; their dispersion is the forecast-uncertainty measure used by
    the uncertainty factor (deep ensembles).
    """

    def __init__(self, layers: tuple[int, ...] = (32, 16, 8), l1: float = 1e-5, learning_rate: float = 1e-3,
                 batch_size: int = 10000, max_epochs: int = 40, patience: int = 5, n_members: int = 3,
                 seed: int = 0, device: str | None = None):
        self.layers = tuple(layers)
        self.l1 = float(l1)
        self.learning_rate = float(learning_rate)
        self.batch_size = int(batch_size)
        self.max_epochs = int(max_epochs)
        self.patience = int(patience)
        self.n_members = int(n_members)
        self.seed = int(seed)
        self.device = device
        self.nets: list = []
        self.mu_: np.ndarray | None = None
        self.sd_: np.ndarray | None = None

    # ------------------------------------------------------------------ utils
    def _prep(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            self.mu_ = np.nanmean(X, axis=0)
            self.sd_ = np.nanstd(X, axis=0)
            self.sd_[self.sd_ < 1e-8] = 1.0
        return np.clip((np.nan_to_num(X, nan=0.0) - self.mu_) / self.sd_, -8, 8).astype("float32")

    def _build(self, n_features: int, seed: int):
        import torch
        from torch import nn

        torch.manual_seed(seed)
        mods: list = []
        prev = n_features
        for width in self.layers:
            mods += [nn.Linear(prev, width), nn.BatchNorm1d(width), nn.ReLU()]
            prev = width
        mods.append(nn.Linear(prev, 1))
        return nn.Sequential(*mods)

    # ------------------------------------------------------------------ api
    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str], target: str = "y") -> "NNCell":
        import torch

        device = torch.device(self.device or ("cuda" if torch.cuda.is_available() else "cpu"))
        Xtr = torch.tensor(self._prep(train[features].to_numpy(dtype="float32"), fit=True), device=device)
        ytr = torch.tensor(train[target].to_numpy(dtype="float32"), device=device).unsqueeze(1)
        Xva = torch.tensor(self._prep(val[features].to_numpy(dtype="float32")), device=device)
        yva = torch.tensor(val[target].to_numpy(dtype="float32"), device=device).unsqueeze(1)

        self.nets = []
        for m in range(self.n_members):
            net = self._build(len(features), self.seed + m).to(device)
            opt = torch.optim.Adam(net.parameters(), lr=self.learning_rate)
            loss_fn = torch.nn.MSELoss()
            best_state, best_loss, bad = None, float("inf"), 0
            n = len(Xtr)
            gen = torch.Generator(device="cpu").manual_seed(self.seed + m)
            for _ in range(self.max_epochs):
                net.train()
                perm = torch.randperm(n, generator=gen).to(device)
                for start in range(0, n, self.batch_size):
                    idx = perm[start:start + self.batch_size]
                    if len(idx) < 8:
                        continue
                    opt.zero_grad()
                    out = net(Xtr[idx])
                    loss = loss_fn(out, ytr[idx])
                    if self.l1:
                        loss = loss + self.l1 * sum(p.abs().sum() for p in net.parameters())
                    loss.backward()
                    opt.step()
                net.eval()
                with torch.no_grad():
                    vloss = float(loss_fn(net(Xva), yva))
                if vloss < best_loss - 1e-9:
                    best_loss, bad = vloss, 0
                    best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
                else:
                    bad += 1
                    if bad >= self.patience:
                        break
            if best_state is not None:
                net.load_state_dict(best_state)
            net.eval()
            self.nets.append(net)
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        import torch

        device = next(self.nets[0].parameters()).device
        X = torch.tensor(self._prep(test[features].to_numpy(dtype="float32")), device=device)
        with torch.no_grad():
            preds = np.column_stack([net(X).cpu().numpy().ravel() for net in self.nets])
        out = pd.DataFrame(index=test.index)
        out["score"] = preds.mean(axis=1)
        out["unc_sd"] = preds.std(axis=1, ddof=1) if self.n_members > 1 else np.nan
        return out


class MoECell:
    """Mixture of experts whose gate sees only the market-state vector.

    This is the interpretable version of state dependence: the gate weights are a function of
    observable states alone, so the fitted gate can be read as "which model runs in which regime"
    (experiment E61). Falls back to a single expert when no state columns are supplied.
    """

    def __init__(self, n_experts: int = 3, expert_layers: tuple[int, ...] = (16, 8), learning_rate: float = 1e-3,
                 batch_months: int = 24, max_epochs: int = 30, patience: int = 5, n_members: int = 1, seed: int = 0,
                 device: str | None = None):
        self.n_experts = int(n_experts)
        self.expert_layers = tuple(expert_layers)
        self.learning_rate = float(learning_rate)
        self.batch_months = int(batch_months)
        self.max_epochs = int(max_epochs)
        self.patience = int(patience)
        self.n_members = int(n_members)
        self.seed = int(seed)
        self.device = device
        self.models: list = []
        self.state_cols_: list[str] = []
        self.feature_cols_: list[str] = []
        self.mu_: np.ndarray | None = None
        self.sd_: np.ndarray | None = None

    def _prep(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            self.mu_ = np.nanmean(X, axis=0)
            self.sd_ = np.nanstd(X, axis=0)
            self.sd_[self.sd_ < 1e-8] = 1.0
        return np.clip((np.nan_to_num(X, nan=0.0) - self.mu_) / self.sd_, -8, 8).astype("float32")

    def _build(self, n_features: int, n_states: int, seed: int):
        import torch
        from torch import nn

        torch.manual_seed(seed)

        class MoE(nn.Module):
            def __init__(self, n_in, n_state, n_experts, layers):
                super().__init__()
                def expert():
                    mods, prev = [], n_in
                    for width in layers:
                        mods += [nn.Linear(prev, width), nn.ReLU()]
                        prev = width
                    mods.append(nn.Linear(prev, 1))
                    return nn.Sequential(*mods)
                self.experts = nn.ModuleList([expert() for _ in range(n_experts)])
                self.gate = nn.Sequential(nn.Linear(max(n_state, 1), 8), nn.Tanh(), nn.Linear(8, n_experts))

            def forward(self, x, s):
                gate = torch.softmax(self.gate(s), dim=1)                    # (B, E)
                outs = torch.cat([e(x) for e in self.experts], dim=1)        # (B, E)
                return (gate * outs).sum(dim=1, keepdim=True), gate

        return MoE(n_features, n_states, self.n_experts, self.expert_layers)

    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str], target: str = "y",
            state_cols: list[str] | None = None) -> "MoECell":
        import torch

        device = torch.device(self.device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.state_cols_ = [c for c in (state_cols or []) if c in train.columns]
        self.feature_cols_ = [c for c in features if c not in self.state_cols_]

        Xtr = torch.tensor(self._prep(train[self.feature_cols_].to_numpy(dtype="float32"), fit=True), device=device)
        Str = torch.tensor(train[self.state_cols_].to_numpy(dtype="float32") if self.state_cols_
                           else np.zeros((len(train), 1), dtype="float32"), device=device)
        ytr = torch.tensor(train[target].to_numpy(dtype="float32"), device=device).unsqueeze(1)
        Xva = torch.tensor(self._prep(val[self.feature_cols_].to_numpy(dtype="float32")), device=device)
        Sva = torch.tensor(val[self.state_cols_].to_numpy(dtype="float32") if self.state_cols_
                           else np.zeros((len(val), 1), dtype="float32"), device=device)
        yva = torch.tensor(val[target].to_numpy(dtype="float32"), device=device).unsqueeze(1)

        self.models = []
        for m in range(self.n_members):
            net = self._build(len(self.feature_cols_), len(self.state_cols_) or 1, self.seed + m).to(device)
            opt = torch.optim.Adam(net.parameters(), lr=self.learning_rate)
            loss_fn = torch.nn.MSELoss()
            best_state, best_loss, bad = None, float("inf"), 0
            n = len(Xtr)
            batch = max(2048, n // 20)
            gen = torch.Generator(device="cpu").manual_seed(self.seed + m)
            for _ in range(self.max_epochs):
                net.train()
                perm = torch.randperm(n, generator=gen).to(device)
                for start in range(0, n, batch):
                    idx = perm[start:start + batch]
                    if len(idx) < 8:
                        continue
                    opt.zero_grad()
                    pred, _ = net(Xtr[idx], Str[idx])
                    loss = loss_fn(pred, ytr[idx])
                    loss.backward()
                    opt.step()
                net.eval()
                with torch.no_grad():
                    pred, _ = net(Xva, Sva)
                    vloss = float(loss_fn(pred, yva))
                if vloss < best_loss - 1e-9:
                    best_loss, bad = vloss, 0
                    best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
                else:
                    bad += 1
                    if bad >= self.patience:
                        break
            if best_state is not None:
                net.load_state_dict(best_state)
            net.eval()
            self.models.append(net)
        return self

    def predict(self, test: pd.DataFrame, features: list[str]) -> pd.DataFrame:
        import torch

        device = next(self.models[0].parameters()).device
        X = torch.tensor(self._prep(test[self.feature_cols_].to_numpy(dtype="float32")), device=device)
        S = torch.tensor(test[self.state_cols_].to_numpy(dtype="float32") if self.state_cols_
                         else np.zeros((len(test), 1), dtype="float32"), device=device)
        preds, gates = [], []
        with torch.no_grad():
            for net in self.models:
                p, g = net(X, S)
                preds.append(p.cpu().numpy().ravel())
                gates.append(g.cpu().numpy())
        stacked = np.column_stack(preds)
        out = pd.DataFrame(index=test.index)
        out["score"] = stacked.mean(axis=1)
        out["unc_sd"] = stacked.std(axis=1, ddof=1) if self.n_members > 1 else np.nan
        self.last_gate_ = np.mean(gates, axis=0)     # kept for interpretation (E61)
        return out


def candidates(models_cfg: dict, conditional: bool, n_members: int = 1, seed: int = 0, fast: bool = False):
    """(model, params) pairs for the nonlinear arm: LightGBM plus a neural network (and MoE if conditional)."""
    lg = models_cfg["lightgbm"]
    lgb_grid = {
        "num_leaves": lg["num_leaves"], "learning_rate": lg["learning_rate"],
        "min_data_in_leaf": lg["min_data_in_leaf"], "feature_fraction": lg["feature_fraction"],
        "lambda_l2": lg["lambda_l2"],
    }
    if fast:
        lgb_grid = {"num_leaves": [31], "learning_rate": [0.05], "min_data_in_leaf": [500],
                    "feature_fraction": [0.8], "lambda_l2": [0.0]}
    for p in grid(lgb_grid):
        params = {"model": "lightgbm", "conditional": conditional, "n_members": n_members, **p}
        yield LGBMCell(num_boost_round=300 if fast else lg["num_boost_round"],
                       early_stopping_rounds=lg["early_stopping_rounds"], n_members=n_members, seed=seed, **p), params

    nn_cfg = models_cfg["neural_net"]
    l1_values = [nn_cfg["l1"][0]] if fast else nn_cfg["l1"]
    for l1 in l1_values:
        params = {"model": "nn", "conditional": conditional, "n_members": n_members, "l1": l1,
                  "layers": list(nn_cfg["layers"])}
        yield NNCell(layers=tuple(nn_cfg["layers"]), l1=l1, learning_rate=nn_cfg["learning_rate"],
                     batch_size=nn_cfg["batch_size"], max_epochs=20 if fast else nn_cfg["max_epochs"],
                     patience=nn_cfg["patience"], n_members=n_members, seed=seed), params
