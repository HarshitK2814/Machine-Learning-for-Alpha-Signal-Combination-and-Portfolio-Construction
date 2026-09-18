"""Economic-objective cells: learn portfolio weights directly from net-of-cost utility.

This is the ``E`` arm of the factorial design. Instead of minimising prediction error, the network
maps signals (and, for conditional cells, market states) to portfolio weights and is trained on

    U_t = w_t'r_{t+1} - (gamma/2) w_t'Sigma_t w_t - cost(w_t - w_{t-1}) - borrow(w_t)

with the turnover term linking consecutive months, so the model learns to avoid trades it cannot
pay for. Training uses truncated back-propagation through 12-month sequences. The proposal is then
projected onto the shared constraint set (``portfolio.project``), so prediction-loss cells and
economic cells face identical limits and the comparison isolates the objective.

Linear variant  = a single linear layer (the analogue of a parametric portfolio policy).
Nonlinear variant = a small MLP.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..portfolio.cost_terms import impact_coefficient
from ..risk.cache import RiskCache


@dataclass
class MonthBatch:
    date: pd.Timestamp
    permnos: np.ndarray
    X: np.ndarray            # n x p features
    r: np.ndarray            # n realised next-month excess returns
    spread: np.ndarray
    impact: np.ndarray       # coefficient on |dw|^1.5
    borrow: np.ndarray
    B: np.ndarray
    L: np.ndarray
    d: np.ndarray


def prepare_months(df: pd.DataFrame, features: list[str], risk: RiskCache, aum: float, impact_k: float,
                   commission_bps: float, max_months: int | None = None) -> list[MonthBatch]:
    """Build the per-month tensors the policy trains on (most recent ``max_months`` months)."""
    out: list[MonthBatch] = []
    dates = sorted(df["date"].unique())
    if max_months:
        dates = dates[-max_months:]
    for date in dates:
        d = df[(df["date"] == date) & df["ret_next"].notna()]
        if len(d) < 30:
            continue
        mr = risk.monthly(date)
        pos = pd.Index(mr.permnos).get_indexer(d["permno"].to_numpy())
        keep = pos >= 0
        if keep.sum() < 30:
            continue
        d = d.iloc[keep]
        pos = pos[keep]
        spread = d["spread"].to_numpy(dtype=float)
        lin = 0.5 * spread + commission_bps / 10_000.0
        out.append(MonthBatch(
            date=pd.Timestamp(date), permnos=d["permno"].to_numpy(),
            X=np.nan_to_num(d[features].to_numpy(dtype="float32"), nan=0.0),
            r=d["ret_next"].to_numpy(dtype="float32"),
            spread=lin.astype("float32"),
            impact=impact_coefficient(d["sigma_d"].to_numpy(), d["adv_usd"].to_numpy(), aum, impact_k).astype("float32"),
            borrow=(d["borrow_fee"].to_numpy(dtype=float) / 12.0).astype("float32"),
            B=mr.B[pos].astype("float32"), L=mr.L.astype("float32"), d=mr.d[pos].astype("float32"),
        ))
    return out


class EconomicPolicy:
    """Weight policy trained on net-of-cost utility."""

    def __init__(self, nonlinear: bool = True, hidden: tuple[int, ...] = (16, 8), gamma: float = 25.0,
                 gross: float = 2.0, learning_rate: float = 5e-3, max_epochs: int = 40, patience: int = 5,
                 bptt_months: int = 12, seed: int = 0, device: str | None = None, n_members: int = 1):
        self.nonlinear = bool(nonlinear)
        self.hidden = tuple(hidden)
        self.gamma = float(gamma)
        self.gross = float(gross)
        self.learning_rate = float(learning_rate)
        self.max_epochs = int(max_epochs)
        self.patience = int(patience)
        self.bptt_months = int(bptt_months)
        self.seed = int(seed)
        self.device = device
        self.n_members = int(n_members)
        self.nets: list = []
        self.mu_: np.ndarray | None = None
        self.sd_: np.ndarray | None = None
        self.val_utility_: float = float("nan")

    # ------------------------------------------------------------------ helpers
    def _standardise(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            self.mu_ = np.nanmean(X, axis=0)
            self.sd_ = np.nanstd(X, axis=0)
            self.sd_[self.sd_ < 1e-8] = 1.0
        return np.clip((np.nan_to_num(X, nan=0.0) - self.mu_) / self.sd_, -8, 8).astype("float32")

    def _build(self, p: int, seed: int):
        import torch
        from torch import nn

        torch.manual_seed(seed)
        if not self.nonlinear:
            return nn.Linear(p, 1, bias=False)
        mods, prev = [], p
        for width in self.hidden:
            mods += [nn.Linear(prev, width), nn.ReLU()]
            prev = width
        mods.append(nn.Linear(prev, 1))
        return nn.Sequential(*mods)

    @staticmethod
    def _weights(raw, gross: float):
        """Dollar-neutral weights scaled to the gross budget (differentiable)."""
        import torch

        centred = raw - raw.mean()
        denom = centred.abs().sum() + 1e-8
        return gross * centred / denom

    def _utility(self, w, w_prev, batch, torch):
        r = torch.tensor(batch.r, device=w.device)
        dw = w - w_prev
        lin = torch.tensor(batch.spread, device=w.device)
        imp = torch.tensor(batch.impact, device=w.device)
        borrow = torch.tensor(batch.borrow, device=w.device)
        B = torch.tensor(batch.B, device=w.device)
        L = torch.tensor(batch.L, device=w.device)
        dvec = torch.tensor(batch.d, device=w.device)
        fx = L.T @ (B.T @ w)
        risk = (fx * fx).sum() + (dvec * w * w).sum()
        cost = (lin * dw.abs()).sum() + (imp * dw.abs().clamp(min=1e-12) ** 1.5).sum()
        short = torch.clamp(-w, min=0.0)
        return (w * r).sum() - 0.5 * self.gamma * risk - cost - (borrow * short).sum()

    def _run_epoch(self, net, months: list[MonthBatch], torch, optimiser=None) -> float:
        total, count = 0.0, 0
        device = next(net.parameters()).device
        chunks = [months[i:i + self.bptt_months] for i in range(0, len(months), self.bptt_months)]
        for chunk in chunks:
            prev_w = None
            prev_permnos = None
            if optimiser is not None:
                optimiser.zero_grad()
            chunk_utility = 0.0
            for batch in chunk:
                X = torch.tensor(self._standardise(batch.X), device=device)
                raw = net(X).squeeze(-1)
                w = self._weights(raw, self.gross)
                if prev_w is None:
                    w_prev = torch.zeros_like(w)
                else:
                    aligned = pd.Index(prev_permnos).get_indexer(batch.permnos)
                    mask = torch.tensor((aligned >= 0).astype("float32"), device=device)
                    safe = np.clip(aligned, 0, None)
                    w_prev = prev_w[torch.tensor(safe, device=device)] * mask
                utility = self._utility(w, w_prev, batch, torch)
                chunk_utility = chunk_utility + utility
                prev_w, prev_permnos = w, batch.permnos
                total += float(utility.detach())
                count += 1
            if optimiser is not None and count:
                (-chunk_utility / max(len(chunk), 1)).backward()
                torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0)
                optimiser.step()
                prev_w = prev_w.detach() if prev_w is not None else None
        return total / max(count, 1)

    # ------------------------------------------------------------------ api
    def fit(self, train_months: list[MonthBatch], val_months: list[MonthBatch]) -> "EconomicPolicy":
        import torch

        if not train_months or not val_months:
            raise ValueError("economic policy needs both training and validation months")
        device = torch.device(self.device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self._standardise(np.concatenate([b.X for b in train_months[-24:]], axis=0), fit=True)
        p = train_months[0].X.shape[1]
        self.nets = []
        best_overall = -np.inf
        for m in range(self.n_members):
            net = self._build(p, self.seed + m).to(device)
            opt = torch.optim.Adam(net.parameters(), lr=self.learning_rate)
            best_state, best_val, bad = None, -np.inf, 0
            for _ in range(self.max_epochs):
                net.train()
                self._run_epoch(net, train_months, torch, optimiser=opt)
                net.eval()
                with torch.no_grad():
                    val_u = self._run_epoch(net, val_months, torch)
                if val_u > best_val + 1e-9:
                    best_val, bad = val_u, 0
                    best_state = {k: v.detach().clone() for k, v in net.state_dict().items()}
                else:
                    bad += 1
                    if bad >= self.patience:
                        break
            if best_state is not None:
                net.load_state_dict(best_state)
            net.eval()
            self.nets.append(net)
            best_overall = max(best_overall, best_val)
        self.val_utility_ = float(best_overall)
        return self

    def propose(self, months: list[MonthBatch]) -> pd.DataFrame:
        """Sequential weight proposals for the test months (contract C10)."""
        import torch

        device = next(self.nets[0].parameters()).device
        rows = []
        for batch in months:
            X = torch.tensor(self._standardise(batch.X), device=device)
            with torch.no_grad():
                raws = [net(X).squeeze(-1) for net in self.nets]
                raw = torch.stack(raws).mean(dim=0)
                w = self._weights(raw, self.gross).cpu().numpy()
                spread = None
                if len(raws) > 1:
                    members = torch.stack([self._weights(r, self.gross) for r in raws])
                    spread = members.std(dim=0).cpu().numpy()
            frame = pd.DataFrame({"date": batch.date, "permno": batch.permnos.astype("int32"), "w_prop": w})
            if spread is not None:
                frame["w_prop_sd"] = spread
            rows.append(frame)
        return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["date", "permno", "w_prop"])


def candidates(models_cfg: dict, nonlinear: bool, gamma: float, seed: int = 0, n_members: int = 1, fast: bool = False):
    """(policy, params) pairs for the economic arm."""
    cfg = models_cfg["economic_policy"]
    hidden_options = [tuple(cfg["hidden"])] if not fast else [tuple(cfg["hidden"])]
    lrs = [cfg["learning_rate"]] if fast else [cfg["learning_rate"], cfg["learning_rate"] * 2]
    for hidden in hidden_options:
        for lr in lrs:
            params = {"model": "economic_policy", "nonlinear": nonlinear, "hidden": list(hidden),
                      "learning_rate": lr, "n_members": n_members}
            yield EconomicPolicy(nonlinear=nonlinear, hidden=hidden, gamma=gamma, learning_rate=lr,
                                 max_epochs=12 if fast else cfg["max_epochs"], patience=cfg["patience"],
                                 bptt_months=cfg["bptt_months"], seed=seed, n_members=n_members), params
