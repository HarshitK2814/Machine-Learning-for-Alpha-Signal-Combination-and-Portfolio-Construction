"""Synthetic stock panel with a known data-generating process (contracts C1-C6).

OWNERSHIP NOTE: workstream A (Absar) owns this module in the final repository. It is written here
as a stand-in so that workstreams B and C are not blocked while the WRDS pipeline is built. When the
real generator lands, this file is replaced; nothing else changes, because everything downstream
reads the contracts rather than this module.

What is deliberately realistic
------------------------------
* entry and exit of firms, including performance-related delistings with a -30% delisting return;
* a lognormal size distribution with a market-wide drift, so the universe filter bites;
* a factor structure (market, size, value) with persistent volatility regimes;
* ~150 signals grouped into 13 themes, where signals inside a theme are noisy variants of the same
  latent attribute (so redundancy analysis has something to find);
* signals that decay at different speeds: value/quality are slow, momentum medium, reversal fast;
* staggered coverage: some signals only start in the 1980s/1990s, and missingness is higher for
  small firms (missing values are set to 0 with a theme-level missing indicator, as per the contract);
* spreads that fall after decimalisation and rise for small, volatile firms; ADV tied to size;
* borrow fees that are punitive for the smallest, most illiquid decile.

The planted truth
-----------------
Expected returns are built from latent theme scores, not from the observed noisy signals, so a model
has to work to recover them. The truth includes:

* a static linear effect (value, quality);
* a nonlinear interaction (value x quality) that only nonlinear models can capture;
* a state-dependent momentum coefficient that turns negative after bear markets with high
  volatility (the momentum-crash channel);
* a fast reversal effect concentrated in small, illiquid stocks (high gross alpha, expensive to trade).

Everything is written to ``truth.json`` so that the decomposition (E29) and the mechanism tests
(E61-E63) can be validated against known answers before they are used on real data.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..contracts import paths, write_table

THEMES = [
    "value", "quality", "profitability", "investment", "momentum", "short_term_reversal",
    "low_risk", "size", "liquidity", "accruals", "debt_issuance", "profit_growth", "seasonality",
]
SIGNALS_PER_THEME = {
    "value": 14, "quality": 13, "profitability": 12, "investment": 12, "momentum": 13,
    "short_term_reversal": 8, "low_risk": 12, "size": 8, "liquidity": 12, "accruals": 10,
    "debt_issuance": 10, "profit_growth": 11, "seasonality": 9,
}
# Year from which each theme's signals are treated as "published" (used by the gated-library
# robustness check, E54). Values are plausible placeholders for the synthetic world.
THEME_PUB_YEAR = {
    "value": 1992, "quality": 1996, "profitability": 2013, "investment": 2004, "momentum": 1993,
    "short_term_reversal": 1990, "low_risk": 2006, "size": 1981, "liquidity": 2002,
    "accruals": 1996, "debt_issuance": 1995, "profit_growth": 2006, "seasonality": 2008,
}


@dataclass
class Truth:
    """Planted coefficients; the answer key for validating inference code."""

    b_value: float = 0.0045
    b_quality: float = 0.0030
    b_value_x_quality: float = 0.0035       # nonlinear interaction
    b_momentum_normal: float = 0.0055
    b_momentum_crash: float = -0.0070       # state-dependent: bear market + high volatility
    b_reversal_small_illiquid: float = 0.0090   # fast, expensive alpha
    b_investment: float = -0.0020
    noise_signal_to_theme: float = 1.6      # per-signal noise relative to theme score
    monthly_idio_vol_small: float = 0.16
    monthly_idio_vol_large: float = 0.075
    notes: str = (
        "Expected returns are linear in value/quality/investment, nonlinear in value x quality, "
        "state-dependent in momentum, and concentrated in small illiquid names for reversal."
    )


def _month_ends(start: str, end: str) -> pd.DatetimeIndex:
    return pd.date_range(start, end, freq="ME")


def _xs_rank(values: np.ndarray) -> np.ndarray:
    """Cross-sectional rank transform to [-0.5, 0.5] (NaNs preserved)."""
    out = np.full_like(values, np.nan, dtype="float64")
    ok = ~np.isnan(values)
    n = int(ok.sum())
    if n == 0:
        return out
    order = np.argsort(np.argsort(values[ok]))
    out[ok] = order / max(n - 1, 1) - 0.5
    return out


def _xs_z(values: np.ndarray) -> np.ndarray:
    ok = ~np.isnan(values)
    out = np.zeros_like(values, dtype="float64")
    if ok.sum() < 2:
        return out
    mu, sd = np.nanmean(values[ok]), np.nanstd(values[ok])
    out[ok] = (values[ok] - mu) / (sd if sd > 1e-12 else 1.0)
    return np.clip(out, -4, 4)


def generate(out_dir: Path | str, n_stocks: int = 600, start: str = "1972-01-31",
             end: str = "2025-12-31", seed: int = 20260919, truth: Truth | None = None) -> dict[str, Path]:
    """Generate the full synthetic panel and write contracts C1-C6 plus ``truth.json``."""
    rng = np.random.default_rng(seed)
    truth = truth or Truth()
    out_dir = Path(out_dir)
    dates = _month_ends(start, end)
    T, N = len(dates), n_stocks

    # ---------------- market regimes and factor returns ----------------
    vol_state = np.zeros(T, dtype=int)          # 0 = calm, 1 = turbulent
    p_stay = np.array([0.97, 0.90])
    for t in range(1, T):
        stay = rng.random() < p_stay[vol_state[t - 1]]
        vol_state[t] = vol_state[t - 1] if stay else 1 - vol_state[t - 1]
    mkt_vol = np.where(vol_state == 1, 0.075, 0.035)
    mkt = rng.normal(0.006, mkt_vol)
    smb = rng.normal(0.001, 0.028, T)
    hml = rng.normal(0.002, 0.030, T)
    rf = np.clip(0.004 + 0.0015 * np.sin(np.arange(T) / 40) + rng.normal(0, 0.0005, T), 0.0, None)

    # slow-moving macro states (used for the state-dependent truth)
    def ar1(phi: float, sd: float, mean: float = 0.0) -> np.ndarray:
        x = np.zeros(T)
        x[0] = mean
        for t in range(1, T):
            x[t] = mean + phi * (x[t - 1] - mean) + rng.normal(0, sd)
        return x

    sentiment = ar1(0.94, 0.30)
    credit = np.clip(ar1(0.95, 0.12, mean=1.0) + 1.5 * (vol_state == 1), 0.2, None)
    term = ar1(0.96, 0.25, mean=1.6)
    infl = np.clip(ar1(0.97, 0.25, mean=3.0), -2, 15)
    drate = ar1(0.85, 0.35)

    # ---------------- firm entry, exit and attributes ----------------
    permnos = np.arange(10001, 10001 + N * 8, dtype="int64")  # pool allows replacement of delisted firms
    alive = np.zeros(len(permnos), dtype=bool)
    alive[:N] = True
    next_free = N

    log_me = np.full(len(permnos), np.nan)
    log_me[:N] = rng.normal(6.0, 1.8, N)                 # log $m market cap
    price = np.full(len(permnos), np.nan)
    price[:N] = np.exp(rng.normal(2.9, 0.9, N))
    exchcd = np.full(len(permnos), 3, dtype=int)
    exchcd[:N] = rng.choice([1, 2, 3], N, p=[0.35, 0.10, 0.55])
    ff49 = np.full(len(permnos), 1, dtype=int)
    ff49[:N] = rng.integers(1, 13, N)
    beta = np.full(len(permnos), np.nan)
    beta[:N] = np.clip(rng.normal(1.0, 0.35, N), 0.2, 2.5)

    attrs = {k: np.full(len(permnos), np.nan) for k in
             ["value", "quality", "profitability", "investment", "accruals", "debt_issuance",
              "profit_growth", "seasonality", "liquidity_lat"]}
    for k in attrs:
        attrs[k][:N] = rng.normal(0, 1, N)

    ret_hist: list[np.ndarray] = []
    rows_universe, rows_targets, rows_costs, rows_signals = [], [], [], []
    theme_factor_returns = {th: np.zeros(T) for th in THEMES}
    market_illiquidity = np.zeros(T)
    dispersion = np.zeros(T)

    signal_names: list[str] = []
    signal_theme: list[str] = []
    for th in THEMES:
        for k in range(SIGNALS_PER_THEME[th]):
            signal_names.append(f"sig_{th}_{k:02d}")
            signal_theme.append(th)
    n_signals = len(signal_names)
    signal_noise_seed = rng.normal(0, 1, (n_signals,))  # per-signal noise scaling variation
    signal_noise_scale = truth.noise_signal_to_theme * np.exp(0.25 * signal_noise_seed)
    signal_start_year = np.array([THEME_PUB_YEAR[t] - rng.integers(5, 20) for t in signal_theme])

    prev_ret = np.zeros(len(permnos))
    for t, date in enumerate(dates):
        idx = np.where(alive)[0]
        n_alive = len(idx)

        # --- latent attribute dynamics (slow AR with shocks) ---
        for k, phi in [("value", 0.985), ("quality", 0.99), ("profitability", 0.99),
                       ("investment", 0.97), ("accruals", 0.9), ("debt_issuance", 0.93),
                       ("profit_growth", 0.94), ("seasonality", 0.6), ("liquidity_lat", 0.97)]:
            attrs[k][idx] = phi * attrs[k][idx] + rng.normal(0, np.sqrt(1 - phi ** 2), n_alive)

        size_z = _xs_z(log_me[idx])
        value_z = _xs_z(attrs["value"][idx])
        quality_z = _xs_z(attrs["quality"][idx])
        invest_z = _xs_z(attrs["investment"][idx])

        if len(ret_hist) >= 12:
            past = np.array(ret_hist[-12:])[:, idx]
            mom_raw = np.nansum(past[:-1], axis=0)          # 12-1 momentum
        else:
            mom_raw = np.zeros(n_alive)
        mom_z = _xs_z(mom_raw)
        rev_z = _xs_z(-prev_ret[idx])
        if len(ret_hist) >= 24:
            vol24 = np.nanstd(np.array(ret_hist[-24:])[:, idx], axis=0)
        else:
            vol24 = np.full(n_alive, 0.10)
        lowrisk_z = _xs_z(-vol24)
        liquidity_z = _xs_z(attrs["liquidity_lat"][idx] + 0.6 * size_z)

        # --- state-dependent coefficients (the planted truth) ---
        bear = 1.0 if (t >= 24 and np.nansum([np.nanmean(r) for r in ret_hist[-24:]]) < 0) else 0.0
        turbulent = float(vol_state[t] == 1)
        crash_state = bear * turbulent
        b_mom = truth.b_momentum_normal * (1 - crash_state) + truth.b_momentum_crash * crash_state
        small_illiquid = ((size_z < -0.5) & (liquidity_z < -0.5)).astype(float)

        mu = (truth.b_value * value_z
              + truth.b_quality * quality_z
              + truth.b_investment * invest_z
              + truth.b_value_x_quality * value_z * quality_z
              + b_mom * mom_z
              + truth.b_reversal_small_illiquid * rev_z * small_illiquid)

        idio_vol = np.interp(size_z, [-3, 3], [truth.monthly_idio_vol_small, truth.monthly_idio_vol_large])
        idio_vol = idio_vol * (1.0 + 0.6 * turbulent)
        ret = (rf[t] + mu + beta[idx] * mkt[t] - 0.3 * size_z * smb[t] + 0.3 * value_z * hml[t]
               + rng.normal(0, idio_vol))

        # --- costs and liquidity ---
        me_usd = np.exp(log_me[idx]) * 1e6
        decimalisation = 1.0 if date.year < 2001 else 0.45
        spread = np.clip(decimalisation * (0.0035 * np.exp(-0.45 * size_z) + 0.0006 * (1 + turbulent))
                         + rng.normal(0, 0.0002, n_alive), 0.0002, 0.08)
        adv = np.clip(me_usd * np.exp(0.9 * liquidity_z) * 0.004, 5e4, None)
        sigma_d = np.clip(idio_vol / np.sqrt(21), 0.002, 0.25)
        illiquid_decile = liquidity_z < np.quantile(liquidity_z, 0.10)
        borrow = np.where(illiquid_decile & (size_z < -0.5), 0.05, 0.0025)

        # --- delisting and entry ---
        stress = (ret < -0.5) | (price[idx] < 1.0)
        delist = stress & (rng.random(n_alive) < 0.35)
        delist |= rng.random(n_alive) < 0.0015
        ret = np.where(delist, np.minimum(ret, 0.0) - 0.30, ret)  # -30% delisting return convention

        # --- signals: theme score + per-signal noise, ranked cross-sectionally ---
        theme_scores = {
            "value": value_z, "quality": quality_z, "profitability": _xs_z(attrs["profitability"][idx]),
            "investment": invest_z, "momentum": mom_z, "short_term_reversal": rev_z,
            "low_risk": lowrisk_z, "size": -size_z, "liquidity": -liquidity_z,
            "accruals": _xs_z(attrs["accruals"][idx]), "debt_issuance": _xs_z(attrs["debt_issuance"][idx]),
            "profit_growth": _xs_z(attrs["profit_growth"][idx]), "seasonality": _xs_z(attrs["seasonality"][idx]),
        }
        sig_block = np.empty((n_alive, n_signals), dtype="float32")
        miss_block = {th: np.zeros(n_alive, dtype="int8") for th in THEMES}
        for j, (name, th) in enumerate(zip(signal_names, signal_theme)):
            raw = theme_scores[th] + signal_noise_scale[j] * rng.normal(0, 1, n_alive)
            if date.year < signal_start_year[j]:
                raw = np.full(n_alive, np.nan)                       # staggered coverage
            miss_p = np.clip(0.02 + 0.10 * (size_z < -1.0), 0, 1)     # small firms miss more often
            raw = np.where(rng.random(n_alive) < miss_p, np.nan, raw)
            ranked = _xs_rank(raw)
            missing = np.isnan(ranked)
            miss_block[th] += missing.astype("int8")
            sig_block[:, j] = np.nan_to_num(ranked, nan=0.0).astype("float32")

        # theme factor returns (used for the FMOM_* state variables)
        for th, score in theme_scores.items():
            hi, lo = score > np.quantile(score, 0.7), score < np.quantile(score, 0.3)
            if hi.any() and lo.any():
                theme_factor_returns[th][t] = float(ret[hi].mean() - ret[lo].mean())
        market_illiquidity[t] = float(np.mean(spread))
        dispersion[t] = float(np.std(value_z + quality_z + mom_z))

        # --- assemble rows ---
        nyse = exchcd[idx] == 1
        nyse_cut = np.quantile(me_usd[nyse], np.linspace(0, 1, 101)) if nyse.sum() > 10 else np.quantile(me_usd, np.linspace(0, 1, 101))
        nyse_pct = np.searchsorted(nyse_cut, me_usd).astype("float64")
        in_universe = (price[idx] >= 5.0) & (nyse_pct >= 20) & (t >= 12)

        rows_universe.append(pd.DataFrame({
            "date": date, "permno": permnos[idx].astype("int32"), "in_universe": in_universe,
            "me": me_usd, "price": price[idx], "exchcd": exchcd[idx].astype("int32"),
            "ff49": ff49[idx].astype("int32"), "nyse_size_pct": np.clip(nyse_pct, 0, 100),
        }))
        rows_costs.append(pd.DataFrame({
            "date": date, "permno": permnos[idx].astype("int32"), "spread": spread,
            "sigma_d": sigma_d, "adv_usd": adv, "borrow_fee": borrow,
        }))
        sig_df = pd.DataFrame(sig_block, columns=signal_names)
        sig_df.insert(0, "permno", permnos[idx].astype("int32"))
        sig_df.insert(0, "date", date)
        for th in THEMES:
            sig_df[f"miss_{th}"] = miss_block[th]
        rows_signals.append(sig_df)
        rows_targets.append(pd.DataFrame({
            "date": date, "permno": permnos[idx].astype("int32"),
            "ret": ret, "excess": ret - rf[t], "mu_true": mu,
        }))

        # --- roll state forward ---
        full_ret = np.full(len(permnos), np.nan)
        full_ret[idx] = ret
        ret_hist.append(full_ret)
        prev_ret[:] = 0.0
        prev_ret[idx] = ret
        log_me[idx] = log_me[idx] + np.log1p(np.clip(ret, -0.9, None)) + 0.002
        price[idx] = np.clip(price[idx] * (1 + np.clip(ret, -0.9, None)), 0.2, None)
        attrs["value"][idx] -= 0.35 * np.clip(ret, -0.9, 0.9)   # winners get expensive

        dead = idx[delist]
        alive[dead] = False
        n_new = len(dead) + max(0, int(rng.normal(1.0, 1.0)))
        for _ in range(n_new):
            if next_free >= len(permnos):
                break
            j = next_free
            next_free += 1
            alive[j] = True
            log_me[j] = rng.normal(4.8, 1.2)
            price[j] = float(np.exp(rng.normal(2.6, 0.8)))
            exchcd[j] = int(rng.choice([1, 2, 3], p=[0.2, 0.1, 0.7]))
            ff49[j] = int(rng.integers(1, 13))
            beta[j] = float(np.clip(rng.normal(1.1, 0.4), 0.2, 2.5))
            for k in attrs:
                attrs[k][j] = float(rng.normal(0, 1))

    # ---------------- stack and derive forward targets ----------------
    universe = pd.concat(rows_universe, ignore_index=True)
    costs = pd.concat(rows_costs, ignore_index=True)
    signals = pd.concat(rows_signals, ignore_index=True).fillna(0.0)
    raw_targets = pd.concat(rows_targets, ignore_index=True).sort_values(["permno", "date"])

    grp = raw_targets.groupby("permno", sort=False)
    targets = raw_targets[["date", "permno"]].copy()
    targets["ret_next"] = grp["ret"].shift(-1).to_numpy()          # next-month total return (for the backtest)
    targets["r_1m"] = grp["excess"].shift(-1).to_numpy()           # next-month excess return
    cum = grp["excess"].cumsum()
    for h in (3, 6, 12):
        # sum of excess returns over t+1 ... t+h, per firm; NaN when the firm's history is too short
        fwd = grp["excess"].transform(lambda s: s.cumsum().shift(-h) - s.cumsum())
        targets[f"r_{h}m"] = fwd.to_numpy()
    del cum
    targets = targets.sort_values(["date", "permno"]).reset_index(drop=True)

    # ---------------- states (lagged one month, expanding standardisation) ----------------
    states = pd.DataFrame({"date": dates})
    realised_vol = pd.Series(mkt).rolling(6, min_periods=2).std().to_numpy()
    cum24 = pd.Series(mkt).rolling(24, min_periods=6).sum().to_numpy()
    states["MKTVOL"] = np.log(np.nan_to_num(realised_vol, nan=0.04) + 1e-4)
    states["BEAR"] = (np.nan_to_num(cum24, nan=0.0) < 0).astype(float)
    states["ILLIQ"] = np.log(market_illiquidity + 1e-6)
    states["SENT"] = sentiment
    states["CREDIT"] = credit
    states["TERM"] = term
    states["INFL"] = infl
    states["DRATE"] = drate
    states["DISP"] = dispersion
    for th in THEMES:
        states[f"FMOM_{th}"] = pd.Series(theme_factor_returns[th]).rolling(12, min_periods=6).sum().fillna(0.0)
    value_cols = [c for c in states.columns if c != "date"]
    states[value_cols] = states[value_cols].shift(1).bfill()              # observable at t
    binary = {"BEAR"}
    for c in value_cols:                                                  # expanding standardisation (PIT)
        if c in binary:
            continue
        s = states[c]
        states[c] = ((s - s.expanding(min_periods=24).mean()) / s.expanding(min_periods=24).std()).fillna(0.0)
    states[value_cols] = states[value_cols].replace([np.inf, -np.inf], 0.0).clip(-5, 5)

    placebo = states.copy()
    block = 24
    order = np.random.default_rng(seed + 1).permutation(int(np.ceil(len(states) / block)))
    shuffled = np.concatenate([np.arange(b * block, min((b + 1) * block, len(states))) for b in order])
    placebo[value_cols] = states.loc[shuffled, value_cols].to_numpy()

    # ---------------- signal metadata ----------------
    signal_meta = pd.DataFrame({
        "signal": signal_names,
        "theme": signal_theme,
        "pub_year": [int(THEME_PUB_YEAR[t]) for t in signal_theme],
        "source": "synthetic",
    })

    # ---------------- write ----------------
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {
        "universe": write_table(universe, out_dir / "universe.parquet", "universe"),
        "signals": write_table(signals, out_dir / "signals.parquet", "signals"),
        "targets": write_table(targets, out_dir / "targets.parquet", "targets"),
        "states": write_table(states, out_dir / "states.parquet", "states"),
        "states_placebo": write_table(placebo, out_dir / "states_placebo.parquet", "states"),
        "cost_inputs": write_table(costs, out_dir / "cost_inputs.parquet", "cost_inputs"),
    }
    signal_meta.to_csv(out_dir / "signal_meta.csv", index=False)
    written["signal_meta"] = out_dir / "signal_meta.csv"

    truth_payload = {
        "coefficients": asdict(truth),
        "themes": THEMES,
        "signals_per_theme": SIGNALS_PER_THEME,
        "n_signals": n_signals,
        "n_months": int(T),
        "n_stock_months": int(len(universe)),
        "date_range": [str(dates[0].date()), str(dates[-1].date())],
        "seed": seed,
        "planted_effects": {
            "linear": ["value", "quality", "investment"],
            "nonlinear_interaction": "value x quality",
            "state_dependent": "momentum coefficient flips sign in bear + turbulent states",
            "limits_to_arbitrage": "reversal alpha only in small and illiquid stocks",
        },
    }
    (out_dir / "truth.json").write_text(json.dumps(truth_payload, indent=2), encoding="utf-8")
    written["truth"] = out_dir / "truth.json"
    return written


def main() -> None:
    p = argparse.ArgumentParser(description="Generate the synthetic panel (contracts C1-C6).")
    p.add_argument("--out", default=str(paths.processed_dir("synthetic")))
    p.add_argument("--n-stocks", type=int, default=600)
    p.add_argument("--start", default="1972-01-31")
    p.add_argument("--end", default="2025-12-31")
    p.add_argument("--seed", type=int, default=20260919)
    p.add_argument("--quick", action="store_true", help="small panel for tests (120 stocks, 1990-2005)")
    a = p.parse_args()
    if a.quick:
        a.n_stocks, a.start, a.end = 120, "1990-01-31", "2005-12-31"
    written = generate(a.out, n_stocks=a.n_stocks, start=a.start, end=a.end, seed=a.seed)
    for k, v in written.items():
        print(f"{k:16s} {v}")


if __name__ == "__main__":
    main()
