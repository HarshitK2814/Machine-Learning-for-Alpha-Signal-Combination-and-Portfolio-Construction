#!/usr/bin/env python
"""Where does each signal theme's alpha live: liquid names or illiquid names?

The question
------------
The proposed direction ("Which alpha signals survive at scale?") rests on one premise: that a
signal's economic value depends on the liquidity of the names it trades, so that an allocation rule
which conditions on liquidity can beat one that does not. That premise can be tested **without any
cost model at all**. If a theme's gross decile-spread return is the same in the most liquid and the
least liquid tercile, there is nothing for a liquidity-conditioned combination to learn from that
theme. If it is concentrated in the illiquid tercile, that is the Avramov-Cheng-Metzker mechanism
and conditioning on liquidity has something to say.

Method (kept deliberately simple, and fixed before looking)
-----------------------------------------------------------
* Universe: the compliant investable set (finite spread, daily volatility and positive ADV), the
  600-name breadth cap, evaluation window 2009-01..2019-12.
* **Signal orientation uses only pre-2009 data.** For each of the 166 signals the sign is
  ``sign(mean monthly rank-IC over 1990-2008)``, so no evaluation-window information touches it.
* Theme score = equal-weighted mean of the oriented signals in the theme (13 themes).
* Each month, names are split into ADV terciles **within the month** (ADV is known at the portfolio
  date). Within each tercile, and in the pooled universe, the spread is mean(next-month return of
  the top decile) minus mean(... of the bottom decile) by theme score.
* Annualised Sharpe of each spread series, HAC t statistic, and a **paired** test of
  Sharpe(illiquid) - Sharpe(liquid) with ``sharpe_difference_test``. Holm across the 13 themes.

What this does not do
---------------------
It is gross of costs by construction, equal-weighted within deciles (so it flatters small names, per
Novy-Marx & Velikov), and it uses theme composites rather than the ML models' scores. It tests
whether the *premise* holds, not whether a liquidity-conditioned model would win.

Usage
-----
    python tools/exp_theme_liquidity_terciles.py --country DEU IND JPN
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts import intl  # noqa: E402
from alphacomb.validation.inference import newey_west_se, sharpe_difference_test  # noqa: E402

PERIODS = 12
SIGN_END = pd.Timestamp("2009-01-01")
EVAL_START, EVAL_END = pd.Timestamp("2009-01-01"), pd.Timestamp("2019-12-31")


def holm(p: dict[str, float]) -> dict[str, float]:
    items = sorted(((k, v) for k, v in p.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m = len(items)
    out = {k: float("nan") for k in p}
    run = 0.0
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - i) * v))
        out[k] = run
    return out


def sharpe_t(x) -> tuple[float, float]:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    sd = x.std(ddof=1)
    if x.size < 12 or not sd > 0:
        return float("nan"), float("nan")
    sr = float(x.mean() / sd * np.sqrt(PERIODS))
    se = float(newey_west_se(x / sd)) * np.sqrt(PERIODS)
    return sr, (sr / se if se > 0 else float("nan"))


def monthly_rank_ic(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Mean monthly cross-sectional Spearman IC of each signal against next-month return."""
    out = {c: [] for c in cols}
    for _, g in frame.groupby("date"):
        if len(g) < 30:
            continue
        r = g["ret_next"].rank()
        for c in cols:
            s = g[c]
            ok = s.notna()
            if ok.sum() < 30:
                out[c].append(np.nan)
                continue
            out[c].append(float(np.corrcoef(s[ok].rank(), r[ok])[0, 1]))
    return pd.DataFrame({c: [np.nanmean(v) if len(v) else np.nan] for c, v in out.items()})


def decile_spread(g: pd.DataFrame, score: str, frac: float = 0.10,
                  weight: str | None = None) -> float:
    """Top-decile minus bottom-decile next-month return by ``score``.

    ``weight=None`` is equal-weighted within each leg, which flatters small names. ``weight='me'``
    value-weights each leg by market capitalisation, the construction Novy-Marx & Velikov
    recommend, and is what Gate 1 needs: if the illiquid-tercile advantage is only the influence of
    tiny stocks, it should shrink or vanish here.
    """
    n = len(g)
    k = max(int(np.floor(n * frac)), 1)
    if n < 2 * k + 2:
        return float("nan")
    order = g[score].rank(method="first")
    top_g, bot_g = g.loc[order >= n - k + 1], g.loc[order <= k]
    if weight is None:
        return float(top_g["ret_next"].mean() - bot_g["ret_next"].mean())

    def leg(x: pd.DataFrame) -> float:
        w = pd.to_numeric(x[weight], errors="coerce")
        ok = w.notna() & (w > 0) & x["ret_next"].notna()
        if not ok.any():
            return float("nan")
        return float(np.average(x.loc[ok, "ret_next"], weights=w[ok]))

    return float(leg(top_g) - leg(bot_g))


def run_country(country: str, n_boot: int, seed: int, weighting: str = "ew",
                liquidity: str = "adv") -> pd.DataFrame:
    """``weighting``: 'ew' or 'vw'. ``liquidity``: 'adv' (raw dollar ADV) or 'adv_resid'.

    ``adv_resid`` is the month-by-month residual of log ADV on log market cap, i.e. liquidity with
    size partialled out. Terciles on it ask whether a name is illiquid *for its size*, so any
    illiquid-tercile advantage that survives is not merely a small-cap effect.
    """
    b = intl.load_country_bundle(country, max_names=600)
    sig_cols = list(b.signal_columns)
    meta = b.signal_meta.set_index("signal")
    themes = {t: [s for s in g.index if s in sig_cols] for t, g in meta.groupby("theme")}

    uni = b.universe[["date", "permno", "in_universe", "me"]].copy()
    uni["date"] = pd.to_datetime(uni["date"])
    uni = uni[uni.in_universe.astype(bool)][["date", "permno", "me"]]
    tg = b.targets[["date", "permno", "ret_next"]].copy()
    tg["date"] = pd.to_datetime(tg["date"])
    ci = b.cost_inputs[["date", "permno", "spread", "sigma_d", "adv_usd"]].copy()
    ci["date"] = pd.to_datetime(ci["date"])
    sg = b.signals[["date", "permno"] + sig_cols].copy()
    sg["date"] = pd.to_datetime(sg["date"])

    d = uni.merge(tg, on=["date", "permno"], how="inner").merge(sg, on=["date", "permno"], how="left")
    d = d.dropna(subset=["ret_next"])

    # --- orientation from pre-evaluation data only --------------------------------------------
    pre = d[d.date < SIGN_END]
    ic = monthly_rank_ic(pre, sig_cols).iloc[0]
    sign = np.sign(ic).replace(0, 1.0).fillna(1.0)
    print(f"  {country}: orientation from {pre.date.nunique()} pre-2009 months; "
          f"{int((sign < 0).sum())} of {len(sig_cols)} signals flipped")

    # --- evaluation panel, compliant universe -------------------------------------------------
    ev = d[(d.date >= EVAL_START) & (d.date <= EVAL_END)].merge(ci, on=["date", "permno"], how="left")
    ok = (np.isfinite(ev.adv_usd) & (ev.adv_usd > 0) & np.isfinite(ev.spread)
          & np.isfinite(ev.sigma_d))
    cov = float(ok.mean())
    ev = ev.loc[ok].copy()
    print(f"  {country}: evaluation rows {len(ev):,} (cost-input coverage kept {cov:.3f}); "
          f"names/month median {ev.groupby('date').permno.nunique().median():.0f}")

    oriented = ev[sig_cols].mul(sign.to_numpy(), axis=1)
    for t, cols in themes.items():
        ev[f"th_{t}"] = oriented[cols].mean(axis=1, skipna=True)
    def _terciles(s: pd.Series) -> pd.Series:
        # A tercile split of a handful of names is meaningless, and in a month with almost no
        # investable names qcut raises on duplicate bin edges (India's sparse early months did
        # exactly that). Such months simply contribute no tercile observation.
        if len(s) < 30:
            return pd.Series(np.nan, index=s.index)
        return pd.qcut(s.rank(method="first"), 3, labels=[0, 1, 2]).astype(float)

    if liquidity == "adv_resid":
        def _resid(g: pd.DataFrame) -> pd.Series:
            ok = (g["me"] > 0) & (g["adv_usd"] > 0)
            out = pd.Series(np.nan, index=g.index)
            if ok.sum() < 30:
                return out
            x, y = np.log(g.loc[ok, "me"].to_numpy(float)), np.log(g.loc[ok, "adv_usd"].to_numpy(float))
            slope, icpt = np.polyfit(x, y, 1)
            out.loc[ok] = y - (icpt + slope * x)
            return out

        ev["liq"] = ev.groupby("date", group_keys=False).apply(_resid)
    elif liquidity == "adv":
        ev["liq"] = ev["adv_usd"]
    else:
        raise SystemExit(f"unknown liquidity measure {liquidity!r}")
    if liquidity == "adv_resid":
        rho = ev.groupby("date").apply(
            lambda g: g[["liq", "me"]].dropna().corr(method="spearman").iloc[0, 1]).mean()
        print(f"  {country}: mean monthly Spearman(size-neutral liquidity, market cap) = {rho:+.3f}"
              f"  (raw ADV vs size is far higher; ~0 confirms size is partialled out)")
    ev["tercile"] = ev.groupby("date")["liq"].transform(_terciles)

    rows = []
    for t in themes:
        sc = f"th_{t}"
        series = {}
        for name, mask in (("all", slice(None)), ("illiquid", 0.0), ("mid", 1.0), ("liquid", 2.0)):
            vals = {}
            for date, g in ev.groupby("date"):
                gg = g if name == "all" else g[g.tercile == mask]
                vals[date] = decile_spread(gg.dropna(subset=[sc]), sc,
                                           weight="me" if weighting == "vw" else None)
            series[name] = pd.Series(vals).sort_index()
        rr = {}
        for name, s in series.items():
            sr, tt = sharpe_t(s.to_numpy())
            rr[f"sr_{name}"], rr[f"t_{name}"] = sr, tt
        idx = series["illiquid"].dropna().index.intersection(series["liquid"].dropna().index)
        if len(idx) >= 24:
            dd = sharpe_difference_test(series["illiquid"].loc[idx].to_numpy(),
                                        series["liquid"].loc[idx].to_numpy(), periods=PERIODS,
                                        n_boot=n_boot, block=6, seed=seed)
            rr.update({"diff_illiq_minus_liq": dd.statistic, "diff_t": dd.detail["studentized"],
                       "diff_p": dd.p_value})
        else:
            rr.update({"diff_illiq_minus_liq": np.nan, "diff_t": np.nan, "diff_p": np.nan})
        rows.append({"country": country, "theme": t, "n_signals": len(themes[t]), **rr})
    out = pd.DataFrame(rows)
    adj = holm({r.theme: r.diff_p for r in out.itertuples()})
    out["diff_p_holm"] = out.theme.map(adj)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", nargs="+", default=["DEU", "IND", "JPN"])
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--weighting", choices=["ew", "vw"], default="ew")
    ap.add_argument("--liquidity", choices=["adv", "adv_resid"], default="adv")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "theme_liquidity")
    ap.add_argument("--overwrite", action="store_true",
        help="discard an earlier output written by a different run (or of unknown origin); by default such a collision is refused (alphacomb.output_guard)")
    a = ap.parse_args(argv)
    from alphacomb.output_guard import claim_run_items
    _sfx = "" if (a.weighting, a.liquidity) == ("ew", "adv") else f"_{a.weighting}_{a.liquidity}"
    claim_run_items([(a.out / f"theme_liquidity_{c}{_sfx}.csv", {"country": c}) for c in a.country], a)
    a.out.mkdir(parents=True, exist_ok=True)

    allr = []
    for c in a.country:
        print(f"\n{'='*100}\n{c}\n{'='*100}")
        t = run_country(c, a.n_boot, a.seed, a.weighting, a.liquidity)
        allr.append(t)
        # The default (ew, adv) keeps its original filename; variants carry a suffix so a Gate 1
        # run can never overwrite the baseline it is being compared against.
        sfx = "" if (a.weighting, a.liquidity) == ("ew", "adv") else f"_{a.weighting}_{a.liquidity}"
        t.to_csv(a.out / f"theme_liquidity_{c}{sfx}.csv", index=False)
        show = t.sort_values("sr_all", ascending=False)
        print(f"\n  {'theme':<20}{'#':>3} | {'ALL':>6} {'t':>6} | {'illiq':>6} {'t':>6} | "
              f"{'mid':>6} | {'liquid':>6} {'t':>6} | {'illiq-liq':>9} {'t':>6} {'p(Holm)':>8}")
        for r in show.itertuples():
            star = "*" if r.diff_p_holm < 0.05 else " "
            print(f"  {r.theme:<20}{r.n_signals:>3} | {r.sr_all:>+6.2f} {r.t_all:>+6.1f} | "
                  f"{r.sr_illiquid:>+6.2f} {r.t_illiquid:>+6.1f} | {r.sr_mid:>+6.2f} | "
                  f"{r.sr_liquid:>+6.2f} {r.t_liquid:>+6.1f} | {r.diff_illiq_minus_liq:>+9.2f} "
                  f"{r.diff_t:>+6.1f} {r.diff_p_holm:>8.3f}{star}")
        n_sig = int((t.diff_p_holm < 0.05).sum())
        n_more = int((t.sr_illiquid > t.sr_liquid).sum())
        print(f"\n  themes with illiquid > liquid Sharpe: {n_more} of {len(t)};  "
              f"significant after Holm: {n_sig} of {len(t)}")
    # Deliberately no combined file: concurrent single-country runs would all write the same fixed
    # path and the last to finish would win, which is the failure that bit the source index and
    # stage 06 earlier. Per-country files are written above and are the only outputs.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
