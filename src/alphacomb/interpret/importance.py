"""Economic feature importance and signal attribution (workstream B, experiments E60-E61).

Three complementary views, all reported per *theme* rather than per signal, because the signals
inside a theme are near-duplicates:

1. **Economic feature importance** - the drop in net-of-cost utility when a theme is switched off at
   prediction time (the theme's signals are set to their cross-sectional median, i.e. no view).
   This is the net-of-cost analogue of a permutation importance and is what the paper reports.
2. **Statistical importance** - mean absolute SHAP value (tree models) or absolute standardised
   coefficient (linear models), for comparison with the usual ML importance plots.
3. **Implied theme weights** - regressing the implemented portfolio weights on theme scores month by
   month gives a time series of "how much of each theme the portfolio is actually holding", which is
   what the state-dependence tests (E61) regress on market states.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..models.uncertainty import proxy_net_return, proxy_weights
from ..portfolio.alpha_scaling import grinold_alpha
from ..risk.cache import RiskCache


def theme_columns(signal_meta: pd.DataFrame) -> dict[str, list[str]]:
    return {theme: list(group["signal"]) for theme, group in signal_meta.groupby("theme")}


def economic_feature_importance(model, test: pd.DataFrame, features: list[str], signal_meta: pd.DataFrame,
                                risk: RiskCache, ic: float, aum: float, impact_k: float, commission_bps: float,
                                gross: float = 2.0, weight_cap: float = 0.01) -> pd.DataFrame:
    """Net-of-cost utility lost when each theme is neutralised at prediction time (E60).

    The proxy portfolio is used so the calculation is linear in the number of months; the ranking is
    what matters, and it is reported alongside the full-optimiser results for the chosen model.
    """
    themes = theme_columns(signal_meta)

    def net_return_of(frame: pd.DataFrame) -> float:
        pred = model.predict(frame, features)["score"]
        prev, total = None, 0.0
        for date, group in frame.groupby("date"):
            mr = risk.monthly(date)
            scores = pd.Series(pred.loc[group.index].to_numpy(), index=group["permno"].to_numpy())
            alpha = grinold_alpha(scores, risk.model(date), ic=ic)
            w = proxy_weights(alpha, mr, gross=gross, weight_cap=weight_cap)
            costs = group.set_index("permno")[["spread", "sigma_d", "adv_usd", "borrow_fee"]]
            realised = group.set_index("permno")["ret_next"]
            total += proxy_net_return(w, prev, realised, costs, aum, impact_k, commission_bps)
            prev = w
        return total

    base = net_return_of(test)
    rows = []
    for theme, cols in themes.items():
        present = [c for c in cols if c in test.columns]
        related = present + [c for c in features if c.startswith(f"thm_{theme}")]
        if not related:
            continue
        muted = test.copy()
        for col in related:
            muted[col] = muted.groupby("date")[col].transform("median")
        rows.append({"theme": theme, "n_signals": len(present), "net_return_without_theme": net_return_of(muted),
                     "net_return_full": base})
    out = pd.DataFrame(rows)
    out["economic_importance"] = out["net_return_full"] - out["net_return_without_theme"]
    return out.sort_values("economic_importance", ascending=False).reset_index(drop=True)


def statistical_importance(model, sample: pd.DataFrame, features: list[str], signal_meta: pd.DataFrame,
                           max_rows: int = 20000) -> pd.DataFrame:
    """Mean absolute SHAP value per theme for tree models, or absolute coefficients for linear ones."""
    themes = theme_columns(signal_meta)
    lookup = {}
    for theme, cols in themes.items():
        for c in cols:
            lookup[c] = theme
    values: pd.Series
    if hasattr(model, "boosters") and model.boosters:
        import shap

        sub = sample.sample(min(len(sample), max_rows), random_state=0)
        explainer = shap.TreeExplainer(model.boosters[0])
        sv = explainer.shap_values(sub[features].to_numpy(dtype="float32"))
        values = pd.Series(np.abs(sv).mean(axis=0), index=features)
    elif hasattr(model, "coefficients"):
        values = pd.Series(np.abs(model.coefficients), index=features)
    else:
        return pd.DataFrame(columns=["theme", "statistical_importance"])
    frame = pd.DataFrame({"feature": values.index, "value": values.to_numpy()})
    frame["theme"] = frame["feature"].map(lambda f: lookup.get(f, f.split("_x_")[0].replace("thm_", "")
                                                               if f.startswith("thm_") else "other"))
    out = frame.groupby("theme", as_index=False)["value"].sum().rename(columns={"value": "statistical_importance"})
    return out.sort_values("statistical_importance", ascending=False).reset_index(drop=True)


def implied_theme_weights(weights: pd.DataFrame, design: pd.DataFrame, theme_cols: list[str]) -> pd.DataFrame:
    """Month-by-month regression of implemented weights on theme scores (E61 input).

    Coefficients answer "how much of each theme is the portfolio actually holding this month?".
    """
    merged = weights.merge(design[["date", "permno", *theme_cols]], on=["date", "permno"], how="inner")
    rows = []
    for date, group in merged.groupby("date"):
        X = np.column_stack([np.ones(len(group)), group[theme_cols].to_numpy(dtype=float)])
        y = group["w"].to_numpy(dtype=float)
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        rows.append({"date": pd.Timestamp(date), **dict(zip(theme_cols, coef[1:]))})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


def state_dependence(implied: pd.DataFrame, states: pd.DataFrame, theme_cols: list[str],
                     state_cols: list[str]) -> pd.DataFrame:
    """Regress implied theme weights on market states (hypothesis H5).

    A negative MKTVOL or BEAR coefficient on the momentum theme is the momentum-crash prediction of
    Daniel and Moskowitz (2016); a positive SENT coefficient on short-leg-heavy themes matches
    Stambaugh, Yu and Yuan (2012).
    """
    df = implied.merge(states, on="date", how="left").dropna()
    rows = []
    for theme in theme_cols:
        X = np.column_stack([np.ones(len(df)), df[state_cols].to_numpy(dtype=float)])
        y = df[theme].to_numpy(dtype=float)
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ coef
        dof = max(len(df) - X.shape[1], 1)
        sigma2 = float(resid @ resid / dof)
        xtx_inv = np.linalg.pinv(X.T @ X)
        se = np.sqrt(np.clip(np.diag(sigma2 * xtx_inv), 0, None))
        for k, state in enumerate(state_cols, start=1):
            rows.append({"theme": theme, "state": state, "coefficient": coef[k],
                         "t_stat": coef[k] / se[k] if se[k] > 0 else np.nan})
    return pd.DataFrame(rows)


def limits_to_arbitrage_tilts(weights: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    """Weighted-average characteristics of the long and short legs (hypothesis H6).

    Reports size, spread and ADV tilts: the channel by which gross ML alpha tends to live in stocks
    that are expensive to trade (Avramov, Cheng & Metzker 2023).
    """
    merged = weights.merge(panel[["date", "permno", "me", "spread", "adv_usd"]], on=["date", "permno"], how="left")
    merged["log_me"] = np.log(merged["me"].clip(lower=1.0))
    rows = []
    for date, g in merged.groupby("date"):
        long_w = g["w"].clip(lower=0)
        short_w = (-g["w"]).clip(lower=0)
        def wavg(col, weight):
            s = weight.sum()
            return float((g[col] * weight).sum() / s) if s > 1e-12 else np.nan
        rows.append({"date": pd.Timestamp(date),
                     "long_log_me": wavg("log_me", long_w), "short_log_me": wavg("log_me", short_w),
                     "long_spread": wavg("spread", long_w), "short_spread": wavg("spread", short_w),
                     "long_adv": wavg("adv_usd", long_w), "short_adv": wavg("adv_usd", short_w)})
    out = pd.DataFrame(rows)
    out["size_tilt"] = out["long_log_me"] - out["short_log_me"]
    out["spread_tilt"] = out["long_spread"] - out["short_spread"]
    return out
