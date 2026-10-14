"""E02 / E03: signal quality, decay and redundancy on the real international panel.

Why these are runnable before the scenario grid is countersigned
----------------------------------------------------------------
Frozen decision 6B blocks inspecting *results* before scenarios are fixed. What it protects
against is specification search: choosing the configuration that looks best and reporting it
without paying for the search in the deflation. That hazard attaches to **strategy performance** -
C11 weights and C12 returns - because those are what a configuration is selected on.

E02 and E03 are not that. They are descriptive properties of the **signal panel itself**:

* the information coefficient of each individual signal, and how fast it decays;
* how much of the panel is redundant.

No strategy is formed, no configuration is selected, nothing here can be deflated, and none of it
depends on the grid. The experiment register places them in Phase 3 - before the baselines in
Phase 4 and the factorial in Phase 5 - precisely because they characterise the data a model will
later be fitted to. Every paper of this kind reports them in its data section.

One hazard is real and worth naming: knowing which signals carry information could in principle
influence modelling choices later. It does not here, because the cells consume the whole signal
panel rather than a selected subset, and the hyperparameter grid is frozen independently in
amendment 001A. Nothing in this module feeds selection.

What is measured
----------------
**E02.** Per signal: mean monthly rank IC, its Newey-West t-statistic, ICIR, the autocorrelation
of the cross-sectional signal (a proxy for how fast a position in it must be traded), and IC at
1/3/6/12-month horizons with the implied decay half-life.

**E03.** Within-theme versus cross-theme correlation, and the **effective number of independent
signals** - computed from the eigenvalue spectrum of the signal correlation matrix as
``(sum l)^2 / sum(l^2)``, the participation ratio. A panel of 150 signals whose effective number
is 15 is a panel of 15 signals with 135 near-duplicates, and that gap is itself a finding: it is
the quantitative statement of why naive equal-weighting over-weights crowded themes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .inference import newey_west_se


def _rank_ic_series(df: pd.DataFrame, signal: str, target: str) -> pd.Series:
    """Monthly cross-sectional Spearman correlation between one signal and realised returns."""
    sub = df[["date", signal, target]].dropna()
    if sub.empty:
        return pd.Series(dtype="float64")
    return sub.groupby("date").apply(
        lambda d: d[signal].corr(d[target], method="spearman") if len(d) > 5 else np.nan,
        include_groups=False,
    ).dropna()


def signal_quality(panel: pd.DataFrame, signals: list[str], target: str = "r_1m",
                   horizons: tuple[str, ...] = ("r_1m", "r_3m", "r_6m", "r_12m"),
                   periods: int = 12) -> pd.DataFrame:
    """E02: per-signal IC, ICIR, Newey-West t, persistence and decay across horizons.

    The t-statistic is Newey-West rather than iid: monthly ICs are autocorrelated, and treating
    them as independent would overstate significance for exactly the slow-moving signals whose
    IC persistence is the thing being measured.
    """
    rows = []
    for sig in signals:
        ic = _rank_ic_series(panel, sig, target)
        if ic.empty:
            continue
        mean = float(ic.mean())
        sd = float(ic.std())
        se = float(newey_west_se(ic.to_numpy()))
        row = {
            "signal": sig,
            "n_months": int(len(ic)),
            "mean_ic": mean,
            "ic_sd": sd,
            "icir": float(mean / sd * np.sqrt(periods)) if sd > 0 else np.nan,
            "nw_t": float(mean / se) if se > 0 else np.nan,
        }
        # Persistence of the signal itself: how similar is the cross-section month to month.
        wide = panel.pivot_table(index="date", columns="permno", values=sig, aggfunc="first")
        if len(wide) > 2:
            lagged = wide.shift(1)
            corrs = wide.corrwith(lagged, axis=1, method="spearman").dropna()
            row["autocorr_1m"] = float(corrs.mean()) if len(corrs) else np.nan
            # A signal that fully refreshes each month must be traded in full each month.
            row["implied_turnover"] = float(1.0 - row["autocorr_1m"]) if np.isfinite(
                row.get("autocorr_1m", np.nan)) else np.nan
        for h in horizons:
            if h in panel.columns:
                ich = _rank_ic_series(panel, sig, h)
                row[f"ic_{h}"] = float(ich.mean()) if len(ich) else np.nan
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # Decay half-life from the 1m -> 12m IC profile, where the profile is monotone and positive.
    def half_life(r):
        pts = [(1, r.get("ic_r_1m")), (3, r.get("ic_r_3m")), (6, r.get("ic_r_6m")), (12, r.get("ic_r_12m"))]
        pts = [(h, v) for h, v in pts if v is not None and np.isfinite(v) and v > 0]
        if len(pts) < 2 or pts[0][1] <= 0:
            return np.nan
        h0, v0 = pts[0]
        for h, v in pts[1:]:
            if v <= v0 / 2:
                return float(h)
        return np.nan  # has not halved within 12 months
    out["ic_half_life_months"] = out.apply(half_life, axis=1)
    out["significant_5pct"] = out["nw_t"].abs() > 1.96
    return out.sort_values("mean_ic", ascending=False).reset_index(drop=True)


def effective_number_of_signals(corr: pd.DataFrame) -> float:
    """Participation ratio of the correlation eigenvalue spectrum: ``(sum l)^2 / sum(l^2)``.

    Equals N for a perfectly uncorrelated panel and 1 for a panel that is one signal repeated.
    The honest headline number for "how many independent bets does this library actually contain".
    """
    vals = np.linalg.eigvalsh(corr.to_numpy())
    vals = vals[vals > 1e-10]
    if vals.size == 0:
        return float("nan")
    return float(vals.sum() ** 2 / (vals ** 2).sum())


def redundancy(panel: pd.DataFrame, signals: list[str], meta: pd.DataFrame) -> dict:
    """E03: within- versus cross-theme correlation and the effective signal count."""
    present = [s for s in signals if s in panel.columns]
    corr = panel[present].corr(method="spearman").fillna(0.0)

    theme_of = dict(zip(meta["signal"], meta["theme"]))
    within, cross = [], []
    for i, a in enumerate(present):
        for b in present[i + 1:]:
            v = corr.loc[a, b]
            if not np.isfinite(v):
                continue
            (within if theme_of.get(a) == theme_of.get(b) else cross).append(abs(v))

    per_theme = {}
    for theme, group in meta.groupby("theme"):
        cols = [c for c in group["signal"] if c in present]
        if len(cols) > 1:
            per_theme[theme] = {
                "n_signals": len(cols),
                "effective_n": effective_number_of_signals(corr.loc[cols, cols]),
                "mean_abs_corr": float(np.abs(corr.loc[cols, cols].to_numpy()[
                    np.triu_indices(len(cols), 1)]).mean()),
            }

    return {
        "n_signals": len(present),
        "effective_n_signals": effective_number_of_signals(corr),
        "mean_abs_within_theme_corr": float(np.mean(within)) if within else np.nan,
        "mean_abs_cross_theme_corr": float(np.mean(cross)) if cross else np.nan,
        "n_themes": int(meta["theme"].nunique()),
        "per_theme": pd.DataFrame(per_theme).T.sort_values("n_signals", ascending=False),
        "correlation": corr,
    }


def coverage(panel: pd.DataFrame, signals: list[str]) -> pd.DataFrame:
    """Non-missing share per signal per year — the other half of a credible data section."""
    present = [s for s in signals if s in panel.columns]
    by_year = panel.assign(year=pd.to_datetime(panel["date"]).dt.year)
    return by_year.groupby("year")[present].apply(lambda d: d.notna().mean().mean()).rename(
        "mean_signal_coverage").to_frame()
