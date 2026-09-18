"""Cross-sectional attention cell (design v2, form level A4).

The modern way to *combine* information is to let stocks attend to each other within a month, which
is what the transformer-based pricing models do (Kelly, Kuznetsov, Malamud & Xu 2025; Lai 2025).
This is a deliberately small encoder: one multi-head self-attention block over the cross-section,
followed by a feed-forward head that outputs one score per stock.

Two design choices keep it honest:

* attention is **within a month only**; there is no sequence over time, so no information can leak
  from the future through the attention weights;
* the model is trained on the same cross-sectionally demeaned target and validated the same way as
  every other cell, so its place on the form ladder is comparable.

Attention weights are retained after prediction (``last_attention_``) because "which stocks does the
model look at" is an interpretable output for the paper (analogous to the gate of the
mixture-of-experts cell).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class AttentionCell:
    """One-block cross-sectional transformer encoder over stocks within each month."""

    def __init__(self, d_model: int = 32, n_heads: int = 4, ff_hidden: int = 64, dropout: float = 0.1,
                 learning_rate: float = 1e-3, max_epochs: int = 30, patience: int = 5, n_members: int = 1,
                 max_stocks: int = 1000, seed: int = 0, device: str | None = None):
        self.d_model = int(d_model)
        self.n_heads = int(n_heads)
        self.ff_hidden = int(ff_hidden)
        self.dropout = float(dropout)
        self.learning_rate = float(learning_rate)
        self.max_epochs = int(max_epochs)
        self.patience = int(patience)
        self.n_members = int(n_members)
        self.max_stocks = int(max_stocks)
        self.seed = int(seed)
        self.device = device
        self.nets: list = []
        self.mu_: np.ndarray | None = None
        self.sd_: np.ndarray | None = None
        self.last_attention_: np.ndarray | None = None

    # ------------------------------------------------------------------ helpers
    def _prep(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        if fit:
            self.mu_ = np.nanmean(X, axis=0)
            self.sd_ = np.nanstd(X, axis=0)
            self.sd_[self.sd_ < 1e-8] = 1.0
        return np.clip((np.nan_to_num(X, nan=0.0) - self.mu_) / self.sd_, -8, 8).astype("float32")

    def _build(self, p: int, seed: int):
        import torch
        from torch import nn

        torch.manual_seed(seed)

        class CrossSectionAttention(nn.Module):
            def __init__(self, n_in, d_model, n_heads, ff_hidden, dropout):
                super().__init__()
                self.embed = nn.Sequential(nn.Linear(n_in, d_model), nn.LayerNorm(d_model))
                self.attn = nn.MultiheadAttention(d_model, n_heads, dropout=dropout, batch_first=True)
                self.norm1 = nn.LayerNorm(d_model)
                self.ff = nn.Sequential(nn.Linear(d_model, ff_hidden), nn.ReLU(), nn.Dropout(dropout),
                                        nn.Linear(ff_hidden, d_model))
                self.norm2 = nn.LayerNorm(d_model)
                self.head = nn.Linear(d_model, 1)

            def forward(self, x, need_weights: bool = False):
                # x: (1, n_stocks, n_features) - one month at a time
                h = self.embed(x)
                attended, weights = self.attn(h, h, h, need_weights=need_weights, average_attn_weights=True)
                h = self.norm1(h + attended)
                h = self.norm2(h + self.ff(h))
                return self.head(h).squeeze(-1), weights

        return CrossSectionAttention(p, self.d_model, self.n_heads, self.ff_hidden, self.dropout)

    @staticmethod
    def _months(frame: pd.DataFrame, features: list[str], target: str | None, prep, max_stocks: int):
        out = []
        for date, group in frame.groupby("date"):
            if len(group) > max_stocks:
                group = group.sample(max_stocks, random_state=0)
            X = prep(group[features].to_numpy(dtype="float32"))
            y = group[target].to_numpy(dtype="float32") if target else None
            out.append((pd.Timestamp(date), group.index.to_numpy(), X, y))
        return out

    # ------------------------------------------------------------------ api
    def fit(self, train: pd.DataFrame, val: pd.DataFrame, features: list[str], target: str = "y") -> "AttentionCell":
        import torch

        device = torch.device(self.device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self._prep(train[features].to_numpy(dtype="float32"), fit=True)
        tr = self._months(train.dropna(subset=[target]), features, target, self._prep, self.max_stocks)
        va = self._months(val.dropna(subset=[target]), features, target, self._prep, self.max_stocks)
        if not tr or not va:
            raise ValueError("attention cell needs at least one training and one validation month")

        self.nets = []
        for m in range(self.n_members):
            net = self._build(len(features), self.seed + m).to(device)
            opt = torch.optim.Adam(net.parameters(), lr=self.learning_rate)
            loss_fn = torch.nn.MSELoss()
            best_state, best_loss, bad = None, float("inf"), 0
            order = np.arange(len(tr))
            rng = np.random.default_rng(self.seed + m)
            for _ in range(self.max_epochs):
                net.train()
                rng.shuffle(order)
                for i in order:
                    _, _, X, y = tr[i]
                    xb = torch.tensor(X, device=device).unsqueeze(0)
                    yb = torch.tensor(y, device=device).unsqueeze(0)
                    opt.zero_grad()
                    pred, _ = net(xb)
                    loss = loss_fn(pred, yb)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(net.parameters(), 5.0)
                    opt.step()
                net.eval()
                with torch.no_grad():
                    vloss = float(np.mean([
                        float(loss_fn(net(torch.tensor(X, device=device).unsqueeze(0))[0],
                                      torch.tensor(y, device=device).unsqueeze(0)))
                        for _, _, X, y in va]))
                if vloss < best_loss - 1e-12:
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
        out = pd.DataFrame(index=test.index, columns=["score", "unc_sd"], dtype=float)
        attentions = []
        for date, idx, X, _ in self._months(test, features, None, self._prep, self.max_stocks):
            xb = torch.tensor(X, device=device).unsqueeze(0)
            member_scores = []
            with torch.no_grad():
                for net in self.nets:
                    pred, weights = net(xb, need_weights=True)
                    member_scores.append(pred.squeeze(0).cpu().numpy())
                    if weights is not None and len(attentions) < 24:
                        attentions.append(weights.squeeze(0).cpu().numpy().mean(axis=0))
            stacked = np.column_stack(member_scores)
            out.loc[idx, "score"] = stacked.mean(axis=1)
            out.loc[idx, "unc_sd"] = stacked.std(axis=1, ddof=1) if self.n_members > 1 else np.nan
        self.last_attention_ = np.array(attentions, dtype=object) if attentions else None
        return out.astype(float)


def candidates(n_members: int = 1, seed: int = 0, fast: bool = False):
    """(model, params) pairs for the attention rung of the form ladder."""
    grids = [(32, 4)] if fast else [(32, 4), (64, 4)]
    for d_model, heads in grids:
        params = {"model": "attention", "d_model": d_model, "n_heads": heads, "n_members": n_members}
        yield AttentionCell(d_model=d_model, n_heads=heads, max_epochs=8 if fast else 30,
                            n_members=n_members, seed=seed), params
