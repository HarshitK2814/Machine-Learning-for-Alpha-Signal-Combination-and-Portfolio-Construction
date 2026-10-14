"""Second tranche of publication assets (figures and tables) for ``tools/make_paper_assets.py``.

Everything here is a deterministic transformation of tracked artifacts: no model is trained, no portfolio is optimised, no cost
engine or backtest is run and no statistic is estimated. Where a quantity is derived (a composite, a compounded wealth path, a
share, a mean over cells) the derivation is stated in the asset's notes and is checked against a published column in the tests.

``register(base)`` is called by the base module's ``build()``; the base module owns the style, the source registry and the catalog.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

B = None   # the base module, set by register()
COUNTRIES = ("DEU", "IND", "JPN")


# ----------------------------------------------------------------------------------------------------------------
# registration
# ----------------------------------------------------------------------------------------------------------------
def register(base) -> None:
    global B
    if B is base:
        return
    B = base
    base.SOURCES.update(EXTRA_SOURCES)
    base.FIGS.extend(FIGS)
    base.TABLES.extend(TABLES)
    base.REVIEW.update(REVIEW)
    base.NOT_BUILT.extend(NOT_BUILT)


EXTRA_SOURCES = {
    **{f"tierB_monthly_{c}": f"results/capacity_return_difference/tierB_monthly_{c}.csv.gz" for c in COUNTRIES},
    **{f"reconciliation_{c}": f"results/capacity_return_difference/reconciliation_{c}.csv" for c in COUNTRIES},
    "parity_summary": "results/cost_parity_diagnostic/parity_summary.csv",
    "dtv_support": "results/cost_parity_diagnostic/dtv_support.csv",
    "flag_crosstab": "results/phase_c_census_v3_2026-10-14/c4_support_flag_crosstab.csv",
    "after_tax_arms": "results/phase_c_after_tax_config_recovery_2026-10-14/after_tax_arms.csv",
    "after_tax_weight_identity": "results/phase_c_after_tax_config_recovery_2026-10-14/after_tax_weight_identity.csv",
    "config_base": "configs/base.yaml",
    "config_portfolio": "configs/portfolio.yaml",
    "jurisdictions": "src/alphacomb/tax/jurisdictions.py",
}
TIERB_KEYS = [f"tierB_{c}" for c in COUNTRIES]
TIERA_KEYS = [f"tierA_{c}" for c in COUNTRIES]
MONTHLY_KEYS = [f"tierB_monthly_{c}" for c in COUNTRIES]
RECON_KEYS = [f"reconciliation_{c}" for c in COUNTRIES]
STAGE6_ALL = ["sum_deu_1e8", "sum_deu_1e9", "sum_deu_1e10", "sum_ind_1e9", "sum_jpn_1e8", "sum_jpn_1e9", "sum_jpn_1e10"]


# ----------------------------------------------------------------------------------------------------------------
# data layer
# ----------------------------------------------------------------------------------------------------------------
def monthly(country: str) -> pd.DataFrame:
    if country not in COUNTRIES:
        raise ValueError(f"unsupported country {country!r}")
    return pd.read_csv(B.src(f"tierB_monthly_{country}"), parse_dates=["date"])


def all_months() -> pd.DatetimeIndex:
    """Month-ends from the earliest to the latest month in any committed Tier B series; a market that lacks a month keeps a NaN there."""
    lo = min(monthly(c)["date"].min() for c in COUNTRIES)
    hi = max(monthly(c)["date"].max() for c in COUNTRIES)
    return pd.date_range(lo, hi, freq="ME")


def missing_months(country: str) -> list[str]:
    have = set(monthly(country)["date"].unique())
    return [d.strftime("%Y-%m") for d in all_months() if d not in have]


def gap_note(bars: bool = False, plain: bool = False) -> str:
    if plain:
        parts = [f"{B.NAMES[c]} has no Tier B return for {', '.join(m)}: lines are broken there" for c in COUNTRIES if (m := missing_months(c))]
        return ("; ".join(parts) + ". ") if parts else ""
    if bars:
        parts = [f"{B.NAMES[c]} has no Tier B return for {', '.join(m)}, so that calendar year compounds the months that exist" for c in COUNTRIES if (m := missing_months(c))]
        return ("; ".join(parts) + ". ") if parts else ""
    parts = [f"{B.NAMES[c]} has no Tier B return for {', '.join(m)}" for c in COUNTRIES if (m := missing_months(c))]
    return ("; ".join(parts) + ": lines are broken there and wealth compounds over the months that exist (the convention behind the published terminal wealth). ") if parts else ""


def monthly_rungs(country: str) -> list[float]:
    return sorted(monthly(country)["aum"].unique())


def common_rungs() -> list[float]:
    sets = [set(np.round(monthly_rungs(c), 2)) for c in COUNTRIES]
    return sorted(set.intersection(*sets))


def composite(country: str, aum: float, book: str, col: str) -> pd.Series:
    """Equal-weighted mean over the 8 prediction cells of a monthly column of the Tier B pipeline series (the same
    composite the capacity measure B(A) is defined on). Raises for a rung or book the artifact does not hold."""
    d = monthly(country)
    sub = d[np.isclose(d["aum"], aum) & (d["book"] == book)]
    if sub.empty:
        raise ValueError(f"no {book} series for {country} at {aum:g} in the committed Tier B monthly file")
    n = sub.groupby("date")["cell"].nunique()
    if not (n == 8).all():
        raise ValueError("a month with fewer than 8 cells would be averaged silently; refusing")
    return sub.groupby("date")[col].mean().sort_index().reindex(all_months())


def wealth(country: str, aum: float, book: str) -> pd.Series:
    r = composite(country, aum, book, "net_ret")
    return (1.0 + r).cumprod()   # NaN months stay NaN and are skipped by the product


def drawdown(w: pd.Series) -> pd.Series:
    return w / w.cummax() - 1.0


def pick_rungs() -> list[float]:
    c = common_rungs()
    return [c[2], c[-2], c[-1]]


def s6_full(key: str) -> pd.DataFrame:
    d = pd.read_csv(B.src(key))
    d["arm"] = d["strategy"].str.extract(r"-([PE])-")[0]
    d["cell4"] = d["strategy"].str.replace("cell_", "", regex=False)
    return d


def s6_cells(key: str) -> pd.DataFrame:
    """One row per prediction-loss cell with zero-tax and statutory-regime columns side by side."""
    d = s6_full(key)
    d = d[d["arm"] == "P"]
    ex = d[d["regime"] == "tax_exempt"].set_index("cell4")
    st = d[d["regime"] != "tax_exempt"].set_index("cell4")
    out = pd.DataFrame({
        "gross_sharpe": ex["gross_sharpe"], "net_sharpe": ex["net_sharpe"], "after_tax_sharpe": st["after_tax_sharpe"],
        "cost_drag_bps": ex["cost_drag_ann_bps"], "tax_drag_bps": st["tax_drag_ann_bps"], "turnover": ex["turnover_mean"],
        "max_dd_zero_tax": ex["max_drawdown"], "max_dd_statutory": st["max_drawdown"],
        "terminal_nav_zero_tax": ex["terminal_nav_multiple"], "terminal_nav_statutory": st["terminal_nav_multiple"]})
    out["country"] = d["country"].iloc[0]
    return out.reset_index().rename(columns={"cell4": "cell"})


def coverage_funnel() -> pd.DataFrame:
    x = pd.read_csv(B.src("flag_crosstab"))
    cat = np.select(
        [~x["in_c1_universe"], x["in_c1_universe"] & ~x["c6_certified"], x["c6_certified"] & ~(x["ret_ok"] & x["div_ok"])],
        ["not in the C1 universe", "in universe, no certified cost inputs", "in universe, certified, return or dividend unusable"],
        default="in universe, certified, return and dividend usable")
    g = x.assign(category=cat).groupby(["country", "category"], sort=False)["n_c4_rows"].sum().reset_index()
    tot = g.groupby("country")["n_c4_rows"].transform("sum")
    g["share"] = g["n_c4_rows"] / tot
    return g


FUNNEL_ORDER = ["not in the C1 universe", "in universe, no certified cost inputs",
                "in universe, certified, return or dividend unusable", "in universe, certified, return and dividend usable"]


def coverage_audit() -> pd.DataFrame:
    cv = B.coverage_monthly()
    rows = []
    for c in COUNTRIES:
        s = cv[cv["country"] == c]
        lo = s.loc[s["share"].idxmin()]
        rows.append({
            "country": c, "months": len(s), "mean_of_monthly_shares": s["share"].mean(),
            "pooled_share": s["c4_with_certified_c6"].sum() / s["c4_in_c1_universe"].sum(),
            "median_monthly_share": s["share"].median(), "lowest_month": lo["month"].strftime("%Y-%m"), "lowest_share": lo["share"],
            "lowest_certified": int(lo["c4_with_certified_c6"]), "lowest_in_universe": int(lo["c4_in_c1_universe"]),
            "mean_excluding_lowest_month": s.drop(index=s["share"].idxmin())["share"].mean(),
            "months_below_0_5": int((s["share"] < 0.5).sum()), "months_below_0_9": int((s["share"] < 0.9).sum()),
            "months_below_0_95": int((s["share"] < 0.95).sum())})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------------------------------------------
# figures
# ----------------------------------------------------------------------------------------------------------------
def dodge(vals, min_gap, log=False):
    """Nudge end-of-line label positions apart (positions only; plotted data are untouched)."""
    vals = list(map(float, vals))
    order = np.argsort(vals)
    out = list(vals)
    prev = None
    for i in order:
        v = vals[i]
        if prev is not None:
            lo = prev * min_gap if log else prev + min_gap
            if v < lo:
                v = lo
        out[i] = v
        prev = v
    return out


def tier_gap_stats() -> dict:
    out = {}
    for c in COUNTRIES:
        r = pd.read_csv(B.src(f"reconciliation_{c}")).dropna(subset=["B_B", "B_A"])
        d = (r["B_A"] - r["B_B"]) * 100
        out[c] = {"max_abs_points": float(d.abs().max()), "at_aum": float(r.loc[d.abs().idxmax(), "aum"]), "rungs": len(r)}
    return out


def fig_cov_heatmap():
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    cv = B.coverage_monthly()
    p = cv.pivot(index="country", columns="month", values="share").loc[list(COUNTRIES)]
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    x = mdates.date2num(p.columns.to_pydatetime())
    half = (x[1] - x[0]) / 2
    im = ax.imshow(p.to_numpy(), aspect="auto", cmap="viridis", vmin=0, vmax=1, interpolation="nearest",
                   extent=(x[0] - half, x[-1] + half, len(p) - 0.5, -0.5))
    ax.xaxis_date()
    ax.set_yticks(range(len(p)))
    ax.set_yticklabels([B.NAMES[c] for c in p.index])
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlabel("month")
    cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.04)
    cb.set_label("share certified")
    cb.outline.set_linewidth(0.4)
    ax.set_title("Where cost inputs are certified: share of in-universe securities, by market and month", loc="left")
    bot = B.foot(fig, "Each cell is one month. Share = securities with a certified spread, daily volatility and USD ADV divided by in-universe securities (outcome-free support census). "
                 "No cell is smoothed or interpolated; India's single dark cell is 2009-10.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_funnel():
    import matplotlib.pyplot as plt
    g = coverage_funnel()
    cols = ["#BDBDBD", "#E69F00", "#56B4E9", "#0072B2"]
    fig, ax = plt.subplots(figsize=(7.0, 3.1))
    for i, c in enumerate(reversed(COUNTRIES)):
        s_ = g[g["country"] == c].set_index("category")
        left = 0.0
        for cat, col in zip(FUNNEL_ORDER, cols):
            v = float(s_["share"].get(cat, 0.0))
            ax.barh(i, v, left=left, color=col, height=0.6, edgecolor="white", linewidth=0.5)
            if v > 0.06:
                ax.text(left + v / 2, i, f"{v*100:.0f}%", ha="center", va="center", fontsize=6.5, color="black" if col != "#0072B2" else "white")
            left += v
    ax.set_yticks(range(3))
    ax.set_yticklabels([B.NAMES[c] for c in reversed(COUNTRIES)])
    ax.set_xlim(0, 1)
    ax.set_xlabel("share of all C4 target rows, 2009-01 to 2019-12")
    ax.set_title("From target rows to tradeable, certified rows", loc="left")
    from matplotlib.patches import Patch
    fig.legend([Patch(color=c) for c in cols], FUNNEL_ORDER, loc="lower center", bbox_to_anchor=(0.5, 0.115), ncol=2, frameon=False, fontsize=6.3)
    bot = B.foot(fig, "Counts of C4 rows by presence flags from the support census; values were reduced to flags at load time. Shares are within market; a row can fail certification "
                 "or sit outside the universe without any performance consequence being measured here.")
    fig.tight_layout(rect=(0, bot + 0.16, 1, 1))
    return fig


def fig_india_audit():
    import matplotlib.pyplot as plt
    cv = B.coverage_monthly()
    au = coverage_audit().set_index("country")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.0), gridspec_kw={"width_ratios": [1.5, 1]})
    s_ = cv[cv["country"] == "IND"]
    a.plot(s_["month"], s_["c4_in_c1_universe"], color=B.COL["IND"], lw=1.3, label="in-universe securities")
    a.plot(s_["month"], s_["c4_with_certified_c6"], color=B.GREY, lw=1.3, ls="--", label="with certified cost inputs")
    lo = au.loc["IND"]
    m = pd.Timestamp(lo["lowest_month"] + "-01")
    a.annotate(f"{lo['lowest_month']}: {lo['lowest_certified']} of {lo['lowest_in_universe']} certified", xy=(m, lo["lowest_certified"]),
               xytext=(m + pd.Timedelta(days=330), 40), fontsize=6.5, arrowprops=dict(arrowstyle="-", lw=0.6, color=B.DARK))
    a.set_ylabel("securities per month")
    a.set_xlabel("month")
    a.set_ylim(-15, None)
    a.set_title("(a) India: counts behind the monthly share", loc="left")
    a.legend(frameon=False, loc="upper left", fontsize=6.5)
    conv = [("mean of monthly shares\n(the Section 3 convention)", "mean_of_monthly_shares"), ("pooled share\n(sum certified / sum in-universe)", "pooled_share"),
            ("mean excluding the\nlowest month", "mean_excluding_lowest_month")]
    for j, (lab, col) in enumerate(conv):
        for c in COUNTRIES:
            b.plot(au.loc[c, col], len(conv) - 1 - j + {"DEU": 0.18, "IND": 0.0, "JPN": -0.18}[c], "o", color=B.COL[c], ms=4.6)
    b.set_yticks(range(len(conv)))
    b.set_yticklabels([c[0] for c in reversed(conv)], fontsize=6.3)
    b.set_xlim(0.6, 1.005)
    b.set_xlabel("share certified")
    b.set_title("(b) Three aggregations", loc="left")
    from matplotlib.lines import Line2D
    b.legend([Line2D([], [], marker="o", ls="", color=B.COL[c]) for c in COUNTRIES], [B.NAMES[c] for c in COUNTRIES], frameon=False, loc="center left", bbox_to_anchor=(0.2, 0.5), fontsize=6.3)
    gap = missing_months("IND")
    link = (f" India's Tier B monthly series has no return for {', '.join(gap)}" + (", the same month." if gap == [lo["lowest_month"]] else ".")) if gap else ""
    bot = B.foot(fig, "Source: input_coverage_by_country_month.csv. The census keeps only presence flags, so it shows that India's lowest month had a C6 row for every in-universe security but almost none "
                 "passed the certification test; it cannot say which component (spread, volatility or ADV) failed." + link + " Project documents of 2026-10-09 place India's minimum in January 2009; the committed census and series place it here.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def _wealth_panels(books_by_panel):
    pass


def fig_wealth_paths():
    import matplotlib.pyplot as plt
    rungs = pick_rungs()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9), sharey=True)
    for ax, c in zip(axes, COUNTRIES):
        paths = [wealth(c, r, "capped") for r in rungs]
        ends = dodge([w.dropna().values[-1] for w in paths], 1.12, log=True)
        for k, (r, w) in enumerate(zip(rungs, paths)):
            ax.plot(w.index, w.values, color=B.COL[c], alpha={0: 0.45, 1: 0.7, 2: 1.0}[k], lw=1.2)
            ax.text(w.index[-1] + pd.Timedelta(days=40), ends[k], B.aum_label(r), fontsize=6.3, color=B.COL[c], va="center")
        ax.axhline(1.0, color=B.DARK, lw=0.5)
        ax.set_yscale("log")
        ax.set_yticks([0.3, 0.5, 1, 2])
        ax.set_yticklabels(["0.3", "0.5", "1", "2"])
        ax.minorticks_off()
        ax.set_ylim(0.25, 2.2)
        ax.set_title(B.NAMES[c], color=B.COL[c], loc="left")
        ax.set_xlim(paths[0].index[0], paths[0].index[-1] + pd.Timedelta(days=330))
        ax.tick_params(axis="x", rotation=45)
        for t in ax.get_xticklabels():
            t.set_ha("right")
    axes[0].set_ylabel("wealth of the capped composite\n(start = 1; log)")
    bot = B.foot(fig, "Capped decile composite (equal-weighted mean of 8 prediction cells), net of costs and before tax, Tier B pipeline series, at the three largest rungs that exist in all three "
                 "markets. " + gap_note() + "Nothing is interpolated. Descriptive paths, not a forecast.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_capped_vs_uncapped():
    import matplotlib.pyplot as plt
    r = pick_rungs()[1]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9), sharey=True)
    for ax, c in zip(axes, COUNTRIES):
        wc, wu = wealth(c, r, "capped"), wealth(c, r, "uncapped")
        ax.plot(wc.index, wc.values, color=B.COL[c], lw=1.3, label="capped")
        ax.plot(wu.index, wu.values, color=B.COL[c], lw=1.3, ls=":", label="uncapped (infeasible)")
        ax.axhline(1.0, color=B.DARK, lw=0.5)
        ax.set_yscale("log")
        ax.set_title(B.NAMES[c], color=B.COL[c], loc="left")
        ax.tick_params(axis="x", rotation=45)
        for t in ax.get_xticklabels():
            t.set_ha("right")
    axes[0].legend(frameon=False, loc="lower left", fontsize=6.3)
    axes[0].set_ylabel("compounded wealth (start = 1; log)")
    bot = B.foot(fig, f"Same composite at {B.aum_label(r)} for the capped book and for the uncapped comparator, which trades beyond the participation limit. The uncapped path is shown to make "
                 "the infeasibility visible; it is not an alternative strategy. " + gap_note())
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_drawdowns():
    import matplotlib.pyplot as plt
    rungs = pick_rungs()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.8), sharey=True)
    for ax, c in zip(axes, COUNTRIES):
        ds = [drawdown(wealth(c, r, "capped")) for r in rungs]
        ends = dodge([d.dropna().values[-1] * 100 for d in ds], 4.5)
        for k, (r, d) in enumerate(zip(rungs, ds)):
            ax.plot(d.index, d.values * 100, color=B.COL[c], alpha={0: 0.45, 1: 0.7, 2: 1.0}[k], lw=1.1)
            ax.text(d.index[-1] + pd.Timedelta(days=40), ends[k], B.aum_label(r), fontsize=6, color=B.COL[c], va="center")
        ax.axhline(0, color=B.DARK, lw=0.5)
        ax.set_xlim(ds[0].index[0], ds[0].index[-1] + pd.Timedelta(days=330))
        ax.set_title(B.NAMES[c], color=B.COL[c], loc="left")
        ax.tick_params(axis="x", rotation=45)
        for t in ax.get_xticklabels():
            t.set_ha("right")
    axes[0].set_ylabel("drawdown of the capped composite (%)")
    bot = B.foot(fig, "Drawdown = wealth divided by its running maximum minus one, from the compounded net-of-cost, pre-tax capped composite (Tier B). Same rungs as the wealth-path figure. " + gap_note())
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_monthly_cost():
    import matplotlib.pyplot as plt
    r = pick_rungs()[1]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9), sharey=True)
    for ax, c in zip(axes, COUNTRIES):
        for book, ls in (("capped", "-"), ("uncapped", ":")):
            s = composite(c, r, book, "cost_total") * 1e4
            ax.plot(s.index, s.values, color=B.COL[c], ls=ls, lw=1.1, label=book)
        ax.set_yscale("log")
        ax.set_title(B.NAMES[c], color=B.COL[c], loc="left")
        ax.tick_params(axis="x", rotation=45)
        for t in ax.get_xticklabels():
            t.set_ha("right")
    axes[0].legend(frameon=False, loc="upper left", fontsize=6.3)
    axes[0].set_ylabel("cost charged (bp of NAV\nper month; log)")
    bot = B.foot(fig, f"Monthly cost_total of the Tier B pipeline accounting (spread, commission, impact and borrow as configured), mean over the 8 prediction cells at {B.aum_label(r)}. "
                 "Capped book (solid) versus uncapped comparator (dotted). " + gap_note(plain=True))
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_annual_returns():
    import matplotlib.pyplot as plt
    r = pick_rungs()[1]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9), sharey=True)
    for ax, c in zip(axes, COUNTRIES):
        s = composite(c, r, "capped", "net_ret")
        g = composite(c, r, "capped", "gross_ret")
        yr = (1 + s).groupby(s.index.year).prod() - 1
        yg = (1 + g).groupby(g.index.year).prod() - 1
        x = np.arange(len(yr))
        ax.bar(x - 0.2, yg.values * 100, 0.4, color=B.COL[c], alpha=0.45, label="gross")
        ax.bar(x + 0.2, yr.values * 100, 0.4, color=B.COL[c], label="net of costs")
        ax.axhline(0, color=B.DARK, lw=0.5)
        ax.set_xticks(x[::2])
        ax.set_xticklabels([str(int(v)) for v in yr.index[::2]], rotation=45, ha="right")
        ax.set_title(B.NAMES[c], color=B.COL[c], loc="left")
    axes[0].legend(frameon=False, fontsize=6.3, loc="lower left")
    axes[0].set_ylabel("calendar-year return of the capped\ncomposite (% of NAV)")
    bot = B.foot(fig, f"Compounded calendar-year gross and net-of-cost returns of the capped composite at {B.aum_label(r)}, before tax (Tier B). " + gap_note(bars=True) + "Descriptive; no inference.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_trade_size():
    import matplotlib.pyplot as plt
    d = pd.read_csv(B.src("dtv_support"))
    d["label"] = d["country"].map(B.NAMES) + " " + d["aum"].map(B.aum_label)
    order = d.drop_duplicates(["country", "aum"]).sort_values(["country", "aum"]).reset_index(drop=True)
    order["country"] = pd.Categorical(order["country"], COUNTRIES)
    order = order.sort_values(["country", "aum"]).reset_index(drop=True)
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)
    for i, r in order.iterrows():
        for book, mk, fc in (("uncapped", "o", "white"), ("capped", "o", B.COL[r["country"]])):
            q = d[(d["country"] == r["country"]) & np.isclose(d["aum"], r["aum"]) & (d["book"] == book)].iloc[0]
            a.plot(q["share_notional_gt12pct_ADV"], len(order) - 1 - i, mk, mfc=fc, mec=B.COL[r["country"]], ms=5.5, mew=1.0)
            b.plot(q["notional_weighted_median_trade_pct_ADV"], len(order) - 1 - i, mk, mfc=fc, mec=B.COL[r["country"]], ms=5.5, mew=1.0)
    a.set_yticks(range(len(order)))
    a.set_yticklabels(list(reversed(order["label"])))
    a.set_xlim(-0.02, 1.02)
    a.set_xlabel("share of traded notional in trades above 12% of ADV")
    a.set_title("(a) Large trades", loc="left")
    b.set_xscale("log")
    b.set_xlabel("median trade size (% of ADV; log)")
    b.set_title("(b) Notional-weighted median trade", loc="left")
    from matplotlib.lines import Line2D
    a.legend([Line2D([], [], marker="o", ls="", mfc="0.3", mec="0.3"), Line2D([], [], marker="o", ls="", mfc="white", mec="0.3")], ["capped", "uncapped"],
             frameon=False, loc="center", bbox_to_anchor=(0.55, 0.45), fontsize=6.5)
    bot = B.foot(fig, "Rungs are those present in the cost-parity diagnostic. The capped book keeps trades small relative to ADV by construction; the uncapped comparator trades far beyond it.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_gross_attained():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.0, 3.5))
    last = {}
    for c, k in (("DEU", "design_deu"), ("IND", "design_ind")):
        d = pd.read_csv(B.src(k))
        d = d[d["book"] == "capped"].drop_duplicates("aum").sort_values("aum")
        gross = 2.0 * (1.0 - d["cap_slack"])
        ax.plot(d["aum"], gross, "o-", color=B.COL[c], ms=3.8, lw=1.2)
        last[c] = (d["aum"].iloc[-1], gross.iloc[-1], list(d["aum"]))
    xs = last["DEU"][2]
    ax.set_xscale("log")
    ax.set_xlim(min(xs) / 1.3, max(xs) * 3.2)
    ax.set_ylim(0, 2.3)
    ax.axhline(2.0, color=B.DARK, lw=0.7, ls="--")
    ax.text(min(xs) / 1.2, 2.04, "gross ceiling 2.0", fontsize=6.3, va="bottom")
    ax.text(last["DEU"][0] * 1.2, last["DEU"][1] + 0.07, B.NAMES["DEU"], color=B.COL["DEU"], fontsize=7, va="center")
    ax.text(last["IND"][0] * 1.2, last["IND"][1] - 0.07, B.NAMES["IND"], color=B.COL["IND"], fontsize=7, va="center")
    ax.set_xlabel("mandate size (AUM)")
    ax.set_ylabel("mean gross exposure attained by the\ncapped decile book (ceiling 2.0)")
    ax.set_xticks(xs[::2])
    ax.set_xticklabels([B.aum_label(x) for x in xs[::2]], rotation=45, ha="right")
    ax.set_title("How far the participation limit shrinks the book as mandates grow", loc="left")
    bot = B.foot(fig, "From the design-identifiability tables: gross exposure = 2 x (1 - cap_slack), the capped book's mean attained gross over months. Germany and India only; no committed Japanese table holds this quantity.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_solvency_heatmap():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    rows = []
    for c in COUNTRIES:
        a = pd.read_csv(B.src(f"tierA_{c}")).sort_values("aum")
        rows.append(a.set_index("aum")["cells_wiped_of_8"])
    m = pd.concat(rows, axis=1, keys=COUNTRIES).T
    im = ax.imshow(m.to_numpy(float), cmap="Reds", vmin=0, vmax=8, aspect="auto")
    ax.grid(False)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            v = m.iloc[i, j]
            ax.text(j, i, "n/a" if pd.isna(v) else f"{int(v)}", ha="center", va="center", fontsize=7, color="white" if v >= 5 else "black")
    ax.set_xticks(range(m.shape[1]))
    ax.set_xticklabels([B.aum_label(x) for x in m.columns], rotation=45, ha="right")
    ax.set_yticks(range(3))
    ax.set_yticklabels([B.NAMES[c] for c in COUNTRIES])
    cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.03)
    cb.set_label("cells wiped out (of 8)")
    ax.set_title("Uncapped comparator: how many of the 8 cells reach -100% in some month", loc="left")
    bot = B.foot(fig, "A cell is wiped out if any of its months has a net return at or below -100% (Tier A solvency ledger). A rung with any wiped-out cell is insolvent and receives no B(A). Counts, not performance.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_tierA_vs_B():
    import matplotlib.pyplot as plt
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.3))
    lim = 0
    for c in COUNTRIES:
        r = pd.read_csv(B.src(f"reconciliation_{c}")).dropna(subset=["B_B", "B_A"])
        x, y = r["B_B"] * 100, r["B_A"] * 100
        lim = max(lim, float(max(x.max(), y.max())))
        a.plot(x, y, "o", color=B.COL[c], ms=3.8, label=B.NAMES[c])
        b.plot(r["aum"], (r["B_A"] - r["B_B"]) * 100, "o-", color=B.COL[c], ms=3.4, lw=1.0)
    a.plot([-1, lim * 1.2], [-1, lim * 1.2], color=B.DARK, lw=0.6, ls="--")
    a.set_xscale("symlog", linthresh=1.0)
    a.set_yscale("symlog", linthresh=1.0)
    for ax_ in (a,):
        plain_ticks = [0, 1, 10, 100]
        ax_.set_xticks(plain_ticks)
        ax_.set_xticklabels([str(t) for t in plain_ticks])
        ax_.set_yticks(plain_ticks)
        ax_.set_yticklabels([str(t) for t in plain_ticks])
        ax_.minorticks_off()
    a.set_xlabel("B(A), Tier B pipeline accounting (points/yr)")
    a.set_ylabel("B(A), Tier A wedge tool (points/yr)")
    a.legend(frameon=False, loc="upper left", fontsize=6.5)
    a.set_title("(a) Two accountings of B(A)", loc="left")
    b.set_xscale("log")
    b.axhline(0, color=B.DARK, lw=0.6)
    b.set_xlabel("mandate size (AUM)")
    b.set_ylabel("Tier A minus Tier B (points/yr)")
    b.set_title("(b) Difference by rung", loc="left")
    st = tier_gap_stats()
    big = st["DEU"]
    bot = B.foot(fig, "Rungs where both tiers have a B(A) (the pipeline accounting covers solvent rungs only). They are close in relative terms at large B(A) but not equal: the largest absolute gap in "
                 f"Germany is {big['max_abs_points']:.0f} points at {B.aum_label(big['at_aum'])}, and gaps grow with mandate size. Tier B is primary; the cost-parity figure shows which conventions differ. "
                 "Agreement of the tiers would not be confirmation of the capacity effect.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_cost_parity():
    import matplotlib.pyplot as plt
    d = pd.read_csv(B.src("parity_summary"))
    d["country"] = pd.Categorical(d["country"], COUNTRIES)
    d = d.sort_values(["country", "aum", "book"]).reset_index(drop=True)
    d["label"] = d["country"].astype(str).map(B.NAMES) + " " + d["aum"].map(B.aum_label) + " " + d["book"].str[:3] + "."
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 4.4), sharey=True, gridspec_kw={"width_ratios": [1, 1.25]})
    y = np.arange(len(d))[::-1]
    a.plot(d["cost_A"], y, "o", color="0.45", ms=4.5, label="Tier A convention")
    a.plot(d["cost_B"], y, "s", color=B.DARK, ms=4, label="Tier B convention")
    a.set_xscale("log")
    a.set_yticks(y)
    a.set_yticklabels(d["label"], fontsize=6.3)
    a.set_xlabel("annual cost (points of NAV; log)")
    a.set_title("(a) Cost under each accounting", loc="left")
    comps = [("e_D", "trade-size basis", "#E69F00"), ("e_X", "exit convention", "#56B4E9"), ("e_B", "borrow", "#CC79A7"), ("interaction", "interaction", "#999999")]
    pos = np.zeros(len(d))
    neg = np.zeros(len(d))
    for col, lab, colr in comps:
        v = d[col].to_numpy()
        base = np.where(v >= 0, pos, neg)
        b.barh(y, v, left=base, color=colr, height=0.62, label=lab, edgecolor="white", linewidth=0.3)
        pos = pos + np.where(v >= 0, v, 0)
        neg = neg + np.where(v < 0, v, 0)
    b.plot(-d["replicated_B_minus_A"], y, "k|", ms=8, mew=1.4, label="total (replicated A minus B)")
    b.axvline(0, color=B.DARK, lw=0.6)
    b.set_xscale("symlog", linthresh=1.0)
    lo, hi = float(neg.min()) * 1.3, float(pos.max()) * 1.3
    b.set_xlim(lo, hi)
    ticks = [t for t in (-100, -10, -1, 0, 1, 10, 100) if lo <= t <= hi]
    b.set_xticks(ticks)
    b.set_xticklabels([f"{t:g}" for t in ticks])
    b.minorticks_off()
    b.set_xlabel("effect of switching one convention to Tier A\n(points per year; symlog)")
    b.set_title("(b) What the difference is made of", loc="left")
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    hs = [Line2D([], [], marker="o", ls="", color="0.45"), Line2D([], [], marker="s", ls="", color=B.DARK)] + [Patch(color=c) for _, _, c in comps] + [Line2D([], [], color="k", marker="|", ls="", ms=8)]
    ls = ["Tier A convention", "Tier B convention"] + [l for _, l, _ in comps] + ["total (replicated A minus B)"]
    fig.legend(hs, ls, loc="lower center", bbox_to_anchor=(0.5, 0.125), ncol=4, frameon=False, fontsize=6.3)
    bot = B.foot(fig, "Cost parity diagnostic: the existing cost function re-evaluated on existing weights under each combination of three accounting conventions. Effects sum, with the interaction, to the "
                 "replicated difference, which differs from the recorded one by a small replication residual. This is accounting reconciliation only; it is not the sensitivity of any result to the exit treatment, which remains unknown.")
    fig.subplots_adjust(left=0.2, right=0.98, top=0.93, bottom=bot + 0.255, wspace=0.08)
    return fig


def fig_cells_strip():
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.0), sharey=True)
    for ax, c in zip(axes, COUNTRIES):
        d = s6_cells(f"sum_{c.lower()}_1e9")
        cols = ["gross_sharpe", "net_sharpe", "after_tax_sharpe"]
        for _, r in d.iterrows():
            ax.plot([0, 1, 2], [r[k] for k in cols], "-", color=B.COL[c], alpha=0.25, lw=0.8)
        for j, k in enumerate(cols):
            jit = np.linspace(-0.1, 0.1, len(d))
            ax.plot(j + jit, d[k].to_numpy(), "o", color=B.COL[c], ms=3.4, alpha=0.85)
            ax.plot([j - 0.22, j + 0.22], [d[k].mean()] * 2, color=B.DARK, lw=1.4)
        ax.axhline(0, color=B.DARK, lw=0.5)
        ax.set_xticks(range(3))
        ax.set_xticklabels(["gross", "net", "after tax"])
        ax.set_xlim(-0.5, 2.5)
        ax.set_title(B.NAMES[c], color=B.COL[c], loc="left")
    axes[0].set_ylabel("annualised Sharpe ratio\n(optimised book, $1bn)")
    bot = B.foot(fig, "One dot per prediction-loss cell (8 per market); thin lines join a cell's gross, net and after-tax values; bars are means. Net comes from the zero-tax regime and after-tax from the "
                 "statutory regime of the same stage-06 summary. Heterogeneity across cells, with no inference.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_tax_turnover():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    for c in COUNTRIES:
        d = s6_cells(f"sum_{c.lower()}_1e9")
        ax.plot(d["turnover"], d["tax_drag_bps"], "o", color=B.COL[c], ms=5, alpha=0.85, label=B.NAMES[c])
    ax.set_xlabel("mean monthly turnover of the optimised book")
    ax.set_ylabel("tax drag (basis points per year)")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Tax drag against turnover, by prediction cell, at $1bn", loc="left")
    bot = B.foot(fig, "Statutory-regime rows of the stage-06 summaries, one point per cell. Turnover is endogenous and the three markets differ in rate and wedge together, so the pattern is descriptive; "
                 "it does not separate the statutory rate from trading intensity.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_tax_turnover_aum():
    import matplotlib.pyplot as plt
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.0))
    for c in COUNTRIES:
        pts = [(au, s6_cells(k)) for (cc, au), k in sorted(B.RUNG_KEYS.items()) if cc == c]
        xs = [p[0] for p in pts]
        mk = "o-" if len(pts) > 1 else "o"
        a.plot(xs, [p[1]["tax_drag_bps"].mean() for p in pts], mk, color=B.COL[c], ms=4.5, label=B.NAMES[c])
        b.plot(xs, [p[1]["turnover"].mean() for p in pts], mk, color=B.COL[c], ms=4.5)
    for ax in (a, b):
        ax.set_xscale("log")
        ax.set_xticks([1e8, 1e9, 1e10])
        ax.set_xticklabels(["$100mn", "$1bn", "$10bn"])
        ax.set_xlabel("mandate size (AUM)")
    a.set_ylabel("tax drag (basis points per year)")
    a.legend(frameon=False)
    a.set_title("(a) Tax drag", loc="left")
    b.set_ylabel("mean monthly turnover")
    b.set_title("(b) Turnover", loc="left")
    bot = B.foot(fig, "Means over the 8 prediction cells of the optimised book (statutory regime for tax drag). India has one rung. Germany's snapshots come from an earlier script version. Descriptive, no inference.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_arm_contrast():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    for c in COUNTRIES:
        d = s6_full(f"sum_{c.lower()}_1e9")
        d = d[d["regime"] == "tax_exempt"]
        key = d["cell4"].str.replace("-P-", "-x-").str.replace("-E-", "-x-")
        p = d[d["arm"] == "P"].assign(k=key).set_index("k")["net_sharpe"]
        e = d[d["arm"] == "E"].assign(k=key).set_index("k")["net_sharpe"]
        ax.plot(p.loc[e.index], e, "o", color=B.COL[c], ms=5, alpha=0.85, label=B.NAMES[c])
    lim = [min(ax.get_xlim()[0], ax.get_ylim()[0]), max(ax.get_xlim()[1], ax.get_ylim()[1])]
    ax.plot(lim, lim, color=B.DARK, lw=0.6, ls="--")
    ax.set_xlabel("net Sharpe, prediction-loss cell")
    ax.set_ylabel("net Sharpe, matching economic-loss cell")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Prediction-loss versus economic-loss arm, optimised book at $1bn (diagnostic)", loc="left")
    bot = B.foot(fig, "Why the economic-loss arm is outside the headline results: matched cells differ in loss only (representation, conditioning and uncertainty levels equal). The restriction to the 8 prediction "
                 "cells was made after the arm's behaviour was observed and is a post hoc deviation. Diagnostic only.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_design_heat():
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(7.0, 4.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[40, 1], left=0.2, right=0.93, top=0.93, bottom=0.2, hspace=0.9, wspace=0.03)
    axes = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0])]
    cax = fig.add_subplot(gs[:, 1])
    im = None
    for ax, (c, k) in zip(axes, (("DEU", "design_deu"), ("IND", "design_ind"))):
        d = pd.read_csv(B.src(k))
        rows = [(bk, ax_) for bk in ("capped", "uncapped") for ax_ in ("representation", "conditioning", "uncertainty")]
        rungs = sorted(d["aum"].unique())
        t = np.full((len(rows), len(rungs)), np.nan)
        sig = np.zeros_like(t, dtype=bool)
        miss = np.zeros_like(t, dtype=bool)
        for i, (bk, a_) in enumerate(rows):
            for j, r in enumerate(rungs):
                q = d[(d["book"] == bk) & (d["axis"] == a_) & np.isclose(d["aum"], r)]
                if len(q):
                    t[i, j] = q["t"].iloc[0]
                    ph = q["p_holm"].iloc[0]
                    miss[i, j] = pd.isna(ph)
                    sig[i, j] = (not pd.isna(ph)) and ph < 0.05
        im = ax.imshow(t, cmap="RdBu_r", vmin=-4, vmax=4, aspect="auto")
        ax.grid(False)
        for i in range(t.shape[0]):
            for j in range(t.shape[1]):
                if sig[i, j]:
                    ax.text(j, i, "*", ha="center", va="center", fontsize=9, color="black")
                elif miss[i, j]:
                    ax.text(j, i, "-", ha="center", va="center", fontsize=8, color="0.4")
        ax.set_xticks(range(len(rungs)))
        ax.set_xticklabels([B.aum_label(x) for x in rungs], rotation=45, ha="right", fontsize=6)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([f"{b_[:3]}. {a_}" for b_, a_ in rows], fontsize=6.3)
        ax.set_title(B.NAMES[c], color=B.COL[c], loc="left")
    cb = fig.colorbar(im, cax=cax)
    cb.set_label("t-statistic of the axis contrast")
    B.foot(fig, "Decile composites, 14 mandate sizes. * = significant after Holm adjustment across axes within the rung; - = no Holm-adjusted value in the source (the rung was not testable); unmarked cells are "
           "not significant. Colour saturates at |t| = 4.")
    return fig


FIGS = [
    ("FIG_S5_coverage_heatmap", fig_cov_heatmap, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["coverage"],
     "Heatmap of the monthly share of in-universe securities with certified cost inputs, by market, 2009-01 to 2019-12. It shows where, not only how much, the required inputs are certified: Germany sits well below one throughout, "
     "India and Japan are near one apart from India's one-month collapse."),
    ("FIG_S6_coverage_funnel", fig_funnel, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["flag_crosstab"],
     "Decomposition of all C4 target rows into outside-the-universe, uncertified, certified-but-unusable and fully usable rows, by market. This is the denominator view behind the coverage ratio."),
    ("FIG_S7_india_coverage_audit", fig_india_audit, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["coverage"],
     "Audit of India's input coverage: monthly counts and three aggregations of the same data. One month, 2009-10, has 1 of 274 in-universe securities certified. The headline mean of 0.989 includes that month; "
     "the figure shows what the other aggregations give. It describes the flags, not any performance consequence."),
    ("FIG_S8_capped_wealth_paths", fig_wealth_paths, "supplementary", "SUPPLEMENTARY_ELIGIBLE", MONTHLY_KEYS,
     "Compounded wealth of the executable capped decile composite at three mandate sizes common to all markets."),
    ("FIG_S9_capped_vs_uncapped_path", fig_capped_vs_uncapped, "supplementary", "SUPPLEMENTARY_ELIGIBLE", MONTHLY_KEYS,
     "Wealth path of the capped book against the infeasible uncapped comparator at one mandate size, making the comparator's ruin visible over time."),
    ("FIG_S10_capped_drawdowns", fig_drawdowns, "supplementary", "SUPPLEMENTARY_ELIGIBLE", MONTHLY_KEYS,
     "Drawdowns of the capped composite at the same three mandate sizes."),
    ("FIG_S11_monthly_cost_charged", fig_monthly_cost, "supplementary", "SUPPLEMENTARY_ELIGIBLE", MONTHLY_KEYS,
     "Monthly cost charged to the capped and uncapped books at one mandate size, showing when costs are incurred."),
    ("FIG_S12_calendar_year_returns", fig_annual_returns, "supplementary", "SUPPLEMENTARY_ELIGIBLE", MONTHLY_KEYS,
     "Calendar-year gross and net-of-cost returns of the capped composite at one mandate size."),
    ("FIG_S13_trade_size_support", fig_trade_size, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["dtv_support"],
     "Trade size relative to average daily volume for the capped and uncapped books at the rungs of the cost-parity diagnostic."),
    ("FIG_S14_attained_gross_exposure", fig_gross_attained, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["design_deu", "design_ind"],
     "Mean gross exposure the capped decile book attains as mandates grow (Germany and India)."),
    ("FIG_S15_uncapped_solvency_counts", fig_solvency_heatmap, "supplementary", "SUPPLEMENTARY_ELIGIBLE", TIERA_KEYS,
     "Number of the 8 cells whose uncapped comparator reaches a net return of -100% or worse, by market and mandate size."),
    ("FIG_S16_tierA_vs_tierB_B", fig_tierA_vs_B, "supplementary", "DIAGNOSTIC_ONLY", RECON_KEYS,
     "Comparison of the two accountings of B(A) (wedge tool versus pipeline) on the rungs where both exist: close in relative terms at large B(A), but with absolute differences that grow with mandate size."),
    ("FIG_S17_cost_parity_decomposition", fig_cost_parity, "supplementary", "DIAGNOSTIC_ONLY", ["parity_summary"],
     "Cost-parity diagnostic: cost under each accounting convention and the decomposition of their difference into trade-size basis, exit convention, borrow and interaction."),
    ("FIG_S18_cell_dispersion_gross_net_aftertax", fig_cells_strip, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["sum_deu_1e9", "sum_ind_1e9", "sum_jpn_1e9"],
     "Cell-level dispersion of gross, net and after-tax Sharpe ratios of the optimised book at $1bn, by market."),
    ("FIG_S19_tax_drag_vs_turnover", fig_tax_turnover, "supplementary", "DIAGNOSTIC_ONLY", ["sum_deu_1e9", "sum_ind_1e9", "sum_jpn_1e9"],
     "Tax drag against turnover across prediction cells at $1bn, by market."),
    ("FIG_S20_tax_drag_turnover_by_aum", fig_tax_turnover_aum, "supplementary", "SUPPLEMENTARY_ELIGIBLE", STAGE6_ALL,
     "Tax drag and turnover of the optimised book across the mandate sizes that exist per market."),
    ("FIG_S21_prediction_vs_economic_arm", fig_arm_contrast, "supplementary", "DIAGNOSTIC_ONLY", ["sum_deu_1e9", "sum_ind_1e9", "sum_jpn_1e9"],
     "Net Sharpe of each prediction-loss cell against its economic-loss counterpart: the contrast behind the disclosed post hoc restriction to 8 of 16 cells."),
    ("FIG_S22_design_axis_t_heatmaps", fig_design_heat, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["design_deu", "design_ind"],
     "t-statistics of the three design-axis contrasts at every mandate size on the capped and uncapped decile books, Germany and India, with Holm-significant cells marked."),
]

REVIEW = {
    "FIG_S5_coverage_heatmap": "Answers: where in time certification fails. One definition for all markets; no smoothing. Placement: supplement.",
    "FIG_S6_coverage_funnel": "Answers: what the coverage denominator contains. Row-level flags, within-market shares; no performance implied. Placement: supplement.",
    "FIG_S7_india_coverage_audit": "Answers: whether the 0.989 headline is sensitive to one month and how it was aggregated. Uses only source counts. States what the flags cannot establish. Placement: supplement; the finding should also be disclosed in the text.",
    "FIG_S8_capped_wealth_paths": "Answers: how the executable book's wealth evolves at common mandate sizes. A deterministic compounding of the tracked monthly series; reproduces the published uncapped terminal wealth in tests for the uncapped counterpart. Placement: supplement.",
    "FIG_S9_capped_vs_uncapped_path": "Answers: when the infeasible comparator is ruined. Same series, same rung. Placement: supplement.",
    "FIG_S10_capped_drawdowns": "Answers: depth of losses of the executable book. No inference. Placement: supplement.",
    "FIG_S11_monthly_cost_charged": "Answers: timing and size of the cost charged. Units stated. Placement: supplement.",
    "FIG_S12_calendar_year_returns": "Answers: whether results are concentrated in a few years. Descriptive. Placement: supplement.",
    "FIG_S13_trade_size_support": "Answers: whether the capped book respects the participation limit while the comparator does not. Source columns only. Placement: supplement.",
    "FIG_S14_attained_gross_exposure": "Answers: how binding the constraint is. Derived as 2 x (1 - cap_slack); Germany and India only, Japan absent from the source and not substituted. Placement: supplement.",
    "FIG_S15_uncapped_solvency_counts": "Answers: where the comparator fails the solvency test. Counts from the ledger. Placement: supplement.",
    "FIG_S16_tierA_vs_tierB_B": "Answers: how far two accountings of the same quantity differ. They are not equal; the figure shows where and by how much and does not present the closeness at large B(A) as confirmation. Diagnostic only.",
    "FIG_S17_cost_parity_decomposition": "Answers: why two cost accountings differ. Accounting reconciliation only, explicitly not the exit-treatment sensitivity. Diagnostic only.",
    "FIG_S18_cell_dispersion_gross_net_aftertax": "Answers: how much cells differ. Same rung and book across markets. No inference. Placement: supplement.",
    "FIG_S19_tax_drag_vs_turnover": "Answers: how tax drag relates to turnover. Endogeneity and confounding by statute are stated; diagnostic only.",
    "FIG_S20_tax_drag_turnover_by_aum": "Answers: how tax drag and turnover change with mandate size where rungs exist. India single point. Placement: supplement.",
    "FIG_S21_prediction_vs_economic_arm": "Answers: why the economic arm is outside the headline. A documentation of a post hoc exclusion; not evidence for any claim. Diagnostic only.",
    "FIG_S22_design_axis_t_heatmaps": "Answers: whether any design axis is detectable at any rung. Holm marks come from the source; missing adjusted values are marked, not filled. Placement: supplement.",
}


# ----------------------------------------------------------------------------------------------------------------
# tables
# ----------------------------------------------------------------------------------------------------------------
def _tbl(raw, fmt, title, notes, srcs):
    return raw, fmt, title, notes, srcs


def table_definitions():
    rows = [
        ("Capped decile spread", "Long the top decile and short the bottom decile by signal, gross exposure 2.0, with weights clipped to the participation limit |w| <= 5% of ADV / AUM; the first executable object.", "manuscript Section 4.1"),
        ("Uncapped decile spread", "The same spread without the participation clip. Not executable; used only as the comparator in B(A).", "manuscript Section 4.1"),
        ("Optimised book", "The full-constraint optimised portfolio; breadth capped at 600 names.", "manuscript Section 4.1, amendment 001B"),
        ("Prediction cells", "The 8 prediction-loss cells of the 2x2x2x2 factorial (representation, conditioning, loss, uncertainty) used for headline results.", "manuscript Section 4.1"),
        ("Composite", "Equal-weighted mean over the 8 cells of a monthly series.", "tools/exp_capacity_return_difference.py"),
        ("Gross, net, after-tax Sharpe", "Annualised Sharpe ratios of the monthly return before costs, after costs, and after costs and tax.", "stage-06 summaries"),
        ("Cost channel", "Net minus gross Sharpe, in Sharpe points.", "tools/exp_matched_book_accounting.py"),
        ("Tax channel", "After-tax minus net Sharpe, in Sharpe points; the paired block-bootstrap statistic of the matched-book tool.", "tools/exp_matched_book_accounting.py"),
        ("Cost drag, tax drag", "Annualised mean return lost to costs, respectively to tax, in basis points per year.", "stage-06 summaries"),
        ("Long-term share of gains", "Share of realised gains in the long-term category; exactly zero under a flat statute.", "stage-06 summaries"),
        ("B(A)", "Annualised mean net-return difference between the capped and uncapped decile composites at mandate size A, in points of NAV per year. An accounting difference against an infeasible comparator, not an investable gain.", "manuscript Section 4.2"),
        ("Solvent rung", "No cell-month of either book has a net return at or below -100% over the horizon. Insolvent rungs receive no B(A).", "manuscript Section 4.2"),
        ("Near-ruined", "Display flag for a solvent rung whose uncapped terminal wealth is below the flag threshold. Not an exclusion rule.", "tools/make_figures.py"),
        ("Cost-input coverage", "In a month, securities with a certified spread, daily volatility and USD ADV divided by in-universe securities.", "coverage census"),
        ("Minimum detectable effect", "2.8016 x the paired standard error (5% two-sided, 80% power).", "tools/gate2_power.py"),
        ("Tier A, Tier B", "Tier A: wedge-tool monthly series; Tier B: pipeline accounting. Tier B is primary.", "tools/exp_capacity_return_difference.py"),
    ]
    raw = pd.DataFrame(rows, columns=["term", "definition", "source"])
    fmt = raw.rename(columns={"term": "Term", "definition": "Definition as used here", "source": "Where defined"})
    return _tbl(raw, fmt, "Table S6. Terms and accounting conventions", "Definitions restate the manuscript and the named tool documentation; the multiplier 2.8016 equals 1.96 + 0.8416 as in the tool. No value is computed.", [])


def _yaml(key):
    return yaml.safe_load(open(B.src(key), encoding="utf-8"))


def table_spec():
    base, port = _yaml("config_base"), _yaml("config_portfolio")
    p, c = base["portfolio"], base["costs"]
    rows = [
        ("Gross exposure limit", p["gross_max"], "configs/base.yaml portfolio.gross_max"),
        ("Per-name weight cap", p["weight_abs_max"], "portfolio.weight_abs_max"),
        ("ADV participation limit", p["adv_participation_max"], "portfolio.adv_participation_max"),
        ("Target volatility (annual)", p["target_vol_annual"], "portfolio.target_vol_annual"),
        ("Dollar neutral", p["dollar_neutral"], "portfolio.dollar_neutral"),
        ("Beta limit (absolute)", p["beta_abs_max"], "portfolio.beta_abs_max"),
        ("Industry limit (absolute)", p["industry_abs_max"], "portfolio.industry_abs_max"),
        ("Commission (basis points)", c["commission_bps"], "costs.commission_bps"),
        ("Impact coefficient k", c["impact_k"], "costs.impact_k"),
        ("Impact exponent", c["impact_power"], "costs.impact_power"),
        ("Flat borrow rate (annual)", c["borrow_fee_model"]["annual_rate"], "costs.borrow_fee_model.annual_rate"),
        ("Risk aversion gamma", port["risk_aversion_gamma"], "configs/portfolio.yaml risk_aversion_gamma"),
        ("Objective", port["objective"], "configs/portfolio.yaml objective"),
    ]
    raw = pd.DataFrame(rows, columns=["parameter", "value", "config_key"])
    raw["value"] = raw["value"].astype(str)
    fmt = raw.rename(columns={"parameter": "Parameter", "value": "Value", "config_key": "Key in the committed configuration"})
    notes = ("Read from the committed configuration files; the manuscript states the same gross, cap, volatility, commission, impact and borrow values (Section 4.1). Run-time hashes of the "
             "configuration used on 2026-10-09 were not recorded, so this is the configuration as committed, not a certified record of the runs. Amendment 001A records the contract parameters as frozen by the project team, "
             "an attestation that has not been countersigned. Impact is k x sigma x sqrt(AUM/ADV) |dw|^1.5 as stated in the manuscript.")
    return _tbl(raw, fmt, "Table 4. Portfolio construction and friction specification as committed", notes, ["config_base", "config_portfolio"])


REGISTRY_SCRIPTS = {
    "after_tax_inference": "tools/exp_after_tax_inference.py", "matched_1e9": "tools/exp_matched_book_accounting.py", "matched_1e8": "tools/exp_matched_book_accounting.py",
    "matched_3e7": "tools/exp_matched_book_accounting.py", "gate2": "tools/gate2_power.py", "design_deu": "tools/exp_design_identifiability.py", "design_ind": "tools/exp_design_identifiability.py",
    "capinf_deu_noncompliant": "tools/exp_capacity_channel_inference.py", "capinf_deu_cov": "tools/exp_capacity_channel_inference.py", "coverage": "tools/phase_c_input_census_v3.py",
    "tier_counts": "tools/phase_c_input_census_v3.py", "flag_crosstab": "tools/phase_c_input_census_v3.py", "parity_summary": "tools/diag_cost_parity.py", "dtv_support": "tools/diag_cost_parity.py",
    "after_tax_arms": "tools/phase_c_recover_after_tax_config.py", "after_tax_weight_identity": "tools/phase_c_recover_after_tax_config.py", "config_base": "(configuration)",
    "config_portfolio": "(configuration)", "jurisdictions": "(configuration)", "fig1": "tools/make_figures.py", "fig2": "tools/make_figures.py",
}
USED_BY_ASSETS = ["coverage", "matched_1e9", "gate2", "design_deu", "design_ind", "tier_counts", "flag_crosstab", "parity_summary", "dtv_support", "after_tax_arms", "after_tax_weight_identity",
                  "config_base", "config_portfolio", "jurisdictions"] + TIERB_KEYS + TIERA_KEYS + MONTHLY_KEYS + RECON_KEYS + STAGE6_ALL + ["matched_1e8", "matched_3e7"]


def table_registry():
    rows = []
    trace = {r["key"] for r in __import__("csv").DictReader(open(B.TRACE, encoding="utf-8"))}
    for k in USED_BY_ASSETS:
        script = REGISTRY_SCRIPTS.get(k)
        if script is None:
            script = ("pipelines/06_after_tax_eval.py (verbatim snapshot)" if k.startswith("sum_") else
                      "tools/exp_capacity_return_difference.py" if k.startswith(("tier", "reconciliation")) else "")
        rows.append({"key": k, "path": B.SOURCES[k], "sha256": B.sha256_portable(B.src(k)), "recorded_in_TRACEABILITY": "yes" if k in trace else "no (hash recorded by the asset pipeline)", "producing_code": script})
    raw = pd.DataFrame(rows)
    fmt = pd.DataFrame({"Key": raw["key"], "Path": raw["path"], "SHA-256 (first 16)": raw["sha256"].str[:16], "In TRACEABILITY.csv": raw["recorded_in_TRACEABILITY"].str.split(" ").str[0], "Producing code": raw["producing_code"]})
    notes = ("Every source the publication assets read, with its hash (full hash in the CSV) and the tracked code that produced it. Hashes of files listed in TRACEABILITY.csv are verified against it before any asset "
             "is built; the others are recorded here at build time. The heavy producing stages need untracked licensed data and are not rerun by the asset pipeline.")
    return _tbl(raw, fmt, "Table S7. Source artifact and provenance registry for the publication assets", notes, [])


def table_provenance():
    arms = pd.read_csv(B.src("after_tax_arms"))
    wi = pd.read_csv(B.src("after_tax_weight_identity"))
    wi_s = wi.groupby(["country", "aum_label"]).agg(strategies=("strategy", "count"), indexed_run_exists=("exists", "sum"),
                                                   index_equals_latest=("index_equals_latest_by_mtime_today", "sum"), predates_summary=("indexed_run_predates_summary", "sum")).reset_index()
    d = arms.merge(wi_s, on=["country", "aum_label"], how="left")
    d["country"] = pd.Categorical(d["country"], COUNTRIES)
    d = d.sort_values(["country", "aum_label"]).reset_index(drop=True)
    raw = d[["country", "aum_label", "months", "dated_column", "tracked_snapshot", "snapshot_sha256_equals_live_file", "index_written_before_summary", "strategies", "indexed_run_exists", "index_equals_latest", "predates_summary", "summary_sha256"]].copy()
    fmt = pd.DataFrame({"Market": raw["country"].astype(str).map(B.NAMES), "AUM": raw["aum_label"].map(B.aum_label), "Months": raw["months"].astype(str),
                        "Dated column": raw["dated_column"].astype(str), "Snapshot = live file": raw["snapshot_sha256_equals_live_file"].map(lambda x: "n/a (no snapshot at the time)" if pd.isna(x) else str(x)),
                        "Weights index written before summary": raw["index_written_before_summary"].astype(str), "Strategies": raw["strategies"].astype(int).astype(str),
                        "Indexed run exists": raw["indexed_run_exists"].astype(int).astype(str), "Index = latest run": raw["index_equals_latest"].astype(int).astype(str),
                        "Indexed run predates summary": raw["predates_summary"].astype(int).astype(str), "Summary SHA-256 (16)": raw["summary_sha256"].str[:16]})
    notes = ("Recovery record for the seven stage-06 summaries (2026-10-14): which weights each summary most plausibly used. 'Index = latest run' counts strategies whose indexed run is also the newest by modification time today; "
             "zero means later runs exist, so the weight identity rests on the weights index and on modification-time ordering, not on a run-time hash. Run-time hashes of code and weights were not recorded.")
    return _tbl(raw, fmt, "Table S8. Provenance of the stage-06 summaries and the weights they used", notes, ["after_tax_arms", "after_tax_weight_identity"])


def table_funnel():
    g = coverage_funnel()
    wide = g.pivot(index="country", columns="category", values="n_c4_rows").loc[list(COUNTRIES), FUNNEL_ORDER].fillna(0).astype(int)
    share = g.pivot(index="country", columns="category", values="share").loc[list(COUNTRIES), FUNNEL_ORDER].fillna(0)
    raw = wide.copy()
    raw.columns = [c + " (rows)" for c in FUNNEL_ORDER]
    for c in FUNNEL_ORDER:
        raw[c + " (share)"] = share[c]
    raw.insert(0, "total_c4_rows", wide.sum(axis=1))
    raw = raw.reset_index()
    fmt = pd.DataFrame({"Market": raw["country"].map(B.NAMES), "C4 rows": raw["total_c4_rows"].map(lambda x: f"{x:,}")})
    for c in FUNNEL_ORDER:
        fmt[c] = [f"{n:,} ({s*100:.1f}%)" for n, s in zip(raw[c + " (rows)"], raw[c + " (share)"])]
    notes = ("All C4 target rows, 2009-01 to 2019-12, by presence flags from the support census (values were reduced to flags at load time). Certified means the cost-input predicate of the engine: spread and volatility "
             "present and non-negative, ADV positive. The census does not retain which component fails.")
    return _tbl(raw, fmt, "Table S9. Composition of the C4 target rows by certification and usability", notes, ["flag_crosstab"])


def table_cov_year():
    cv = B.coverage_monthly()
    cv["year"] = cv["month"].dt.year
    g = cv.groupby(["year", "country"])["share"].mean().unstack().loc[:, list(COUNTRIES)]
    mn = cv.groupby(["year", "country"])["share"].min().unstack().loc[:, list(COUNTRIES)]
    raw = g.join(mn, lsuffix="_mean", rsuffix="_min").reset_index()
    fmt = pd.DataFrame({"Year": raw["year"].astype(str)})
    for c in COUNTRIES:
        fmt[f"{B.NAMES[c]} mean"] = raw[f"{c}_mean"].map(lambda x: f"{x:.3f}")
        fmt[f"{B.NAMES[c]} lowest month"] = raw[f"{c}_min"].map(lambda x: f"{x:.3f}")
    notes = "Mean and lowest monthly share of in-universe securities with certified cost inputs, by calendar year. Same definition as the coverage table; no month is omitted."
    return _tbl(raw, fmt, "Table S10. Cost-input coverage by calendar year", notes, ["coverage"])


def table_cov_audit():
    a = coverage_audit()
    raw = a.copy()
    fmt = pd.DataFrame({"Market": raw["country"].map(B.NAMES), "Months": raw["months"].astype(str), "Mean of monthly shares": raw["mean_of_monthly_shares"].map(fnum3),
                        "Pooled share": raw["pooled_share"].map(fnum3), "Median month": raw["median_monthly_share"].map(fnum3),
                        "Lowest month": raw["lowest_month"] + ": " + raw["lowest_certified"].astype(str) + " of " + raw["lowest_in_universe"].astype(str),
                        "Mean excluding lowest": raw["mean_excluding_lowest_month"].map(fnum3), "Months < 0.5": raw["months_below_0_5"].astype(str),
                        "Months < 0.9": raw["months_below_0_9"].astype(str), "Months < 0.95": raw["months_below_0_95"].astype(str)})
    notes = ("The manuscript's coverage statistic (Section 3) is the mean over months of certified over in-universe securities, applied identically to all three markets; this table recomputes it and three alternatives from the same "
             "counts. India's lowest month is included in its 0.989. The census retains presence flags only, so it cannot show which certification component failed in that month, nor whether the as-run engine's treatment of uncertified "
             "security-months interacts with it; answering that needs the monthly cost series and is outside this audit. "
             + ("India's committed Tier B monthly series has no return for " + ", ".join(missing_months("IND")) + ("; this is the lowest-coverage month. " if missing_months("IND") == [a.set_index("country").loc["IND", "lowest_month"]] else ". ")
                if missing_months("IND") else "")
             + "Project documents of 2026-10-09 (the full account and the capacity-channel results) say India's 0.004 minimum is a single month, January 2009, and the reason for its 131 months; the committed census and series show 2009-10 instead.")
    return _tbl(raw, fmt, "Table S11. Aggregation audit of the cost-input coverage statistic", notes, ["coverage"])


def fnum3(x):
    return f"{x:.3f}"


def table_matched_aum():
    parts = []
    for k in ("matched_3e7", "matched_1e8", "matched_1e9"):
        parts.append(pd.read_csv(B.src(k)))
    raw = pd.concat(parts, ignore_index=True)
    raw["country"] = pd.Categorical(raw["country"], COUNTRIES)
    raw = raw.sort_values(["aum", "country", "book"]).reset_index(drop=True)
    fmt = pd.DataFrame({"AUM": raw["aum"].map(B.aum_label), "Market": raw["country"].astype(str).map(B.NAMES), "Book": raw["book"], "Gross": raw["sharpe_gross"].map(fnum3),
                        "Net": raw["sharpe_net"].map(fnum3), "After tax": raw["sharpe_after_tax"].map(fnum3), "Cost channel": raw["cost_channel"].map(lambda x: f"{x:+.3f}"),
                        "Tax channel": raw["tax_channel"].map(lambda x: f"{x:+.3f}"), "Tax p": raw["tax_p"].map(fnum3), "Months": raw["months"].astype(int).astype(str)})
    notes = ("Every matched-book snapshot that exists (3e7 for India, 1e8 for Germany, 1e9 for all). Matched-book outputs were produced only for these market-by-rung pairs; the others are not available and are not interpolated. "
             "The uncapped book is the non-executable comparator.")
    return _tbl(raw, fmt, "Table S12. Matched-book outcomes at every committed mandate size", notes, ["matched_3e7", "matched_1e8", "matched_1e9"])


def table_cells():
    rows = []
    for c in COUNTRIES:
        d = s6_cells(f"sum_{c.lower()}_1e9")
        rows.append(d)
    raw = pd.concat(rows, ignore_index=True)[["country", "cell", "gross_sharpe", "net_sharpe", "after_tax_sharpe", "cost_drag_bps", "tax_drag_bps", "turnover"]]
    fmt = pd.DataFrame({"Market": raw["country"].map(B.NAMES), "Cell": raw["cell"], "Gross": raw["gross_sharpe"].map(fnum3), "Net": raw["net_sharpe"].map(fnum3), "After tax": raw["after_tax_sharpe"].map(fnum3),
                        "Cost drag (bp/yr)": raw["cost_drag_bps"].map(lambda x: f"{x:.2f}"), "Tax drag (bp/yr)": raw["tax_drag_bps"].map(lambda x: f"{x:.2f}"), "Turnover": raw["turnover"].map(lambda x: f"{x:.4f}")})
    notes = ("Optimised book at $1bn, one row per prediction-loss cell. Cell codes are representation (L or N), conditioning (S or C), loss (P) and uncertainty (0 or U) as named in the stage-06 summaries. Net, cost drag and turnover from the "
             "zero-tax regime rows; after-tax and tax drag from the statutory-regime rows. No inference is attached; Germany's and India's snapshots are verbatim copies of earlier outputs.")
    return _tbl(raw, fmt, "Table S13. Optimised-book results by prediction cell at $1bn", notes, ["sum_deu_1e9", "sum_ind_1e9", "sum_jpn_1e9"])


def table_aum_rungs():
    rows = []
    for (c, au), k in sorted(B.RUNG_KEYS.items()):
        d = s6_cells(k)
        rows.append({"country": c, "aum": au, "cells": len(d), "gross_sharpe": d["gross_sharpe"].mean(), "net_sharpe": d["net_sharpe"].mean(), "after_tax_sharpe": d["after_tax_sharpe"].mean(),
                     "cost_drag_bps": d["cost_drag_bps"].mean(), "tax_drag_bps": d["tax_drag_bps"].mean(), "turnover": d["turnover"].mean(), "max_dd_statutory": d["max_dd_statutory"].mean()})
    raw = pd.DataFrame(rows)
    raw["country"] = pd.Categorical(raw["country"], COUNTRIES)
    raw = raw.sort_values(["country", "aum"]).reset_index(drop=True)
    fmt = pd.DataFrame({"Market": raw["country"].astype(str).map(B.NAMES), "AUM": raw["aum"].map(B.aum_label), "Gross": raw["gross_sharpe"].map(fnum3), "Net": raw["net_sharpe"].map(fnum3),
                        "After tax": raw["after_tax_sharpe"].map(fnum3), "Cost drag (bp/yr)": raw["cost_drag_bps"].map(lambda x: f"{x:.2f}"), "Tax drag (bp/yr)": raw["tax_drag_bps"].map(lambda x: f"{x:.2f}"),
                        "Turnover": raw["turnover"].map(lambda x: f"{x:.4f}"), "Mean max drawdown": raw["max_dd_statutory"].map(lambda x: f"{x*100:.1f}%")})
    notes = ("Means over the 8 prediction cells for every stage-06 summary that exists: Germany and Japan at 1e8, 1e9, 1e10, India at 1e9 only. Absent rungs are not shown or interpolated. Descriptive; no inference; Germany's "
             "$1bn snapshot is from an older script version (24 columns).")
    return _tbl(raw, fmt, "Table S14. Optimised-book summary at every committed mandate size", notes, STAGE6_ALL)


def table_arm():
    rows = []
    for c in COUNTRIES:
        d = s6_full(f"sum_{c.lower()}_1e9")
        d = d[d["regime"] == "tax_exempt"]
        for arm in ("P", "E"):
            q = d[d["arm"] == arm]
            rows.append({"country": c, "arm": arm, "cells": len(q), "gross_sharpe": q["gross_sharpe"].mean(), "net_sharpe": q["net_sharpe"].mean(), "cost_drag_bps": q["cost_drag_ann_bps"].mean(),
                         "turnover": q["turnover_mean"].mean(), "min_net_sharpe": q["net_sharpe"].min(), "max_net_sharpe": q["net_sharpe"].max()})
    raw = pd.DataFrame(rows)
    fmt = pd.DataFrame({"Market": raw["country"].map(B.NAMES), "Arm": raw["arm"].map({"P": "prediction loss (headline)", "E": "economic loss (excluded)"}), "Cells": raw["cells"].astype(str),
                        "Gross": raw["gross_sharpe"].map(fnum3), "Net": raw["net_sharpe"].map(fnum3), "Net range": [f"[{a:.3f}, {b:.3f}]" for a, b in zip(raw["min_net_sharpe"], raw["max_net_sharpe"])],
                        "Cost drag (bp/yr)": raw["cost_drag_bps"].map(lambda x: f"{x:.2f}"), "Turnover": raw["turnover"].map(lambda x: f"{x:.4f}")})
    notes = ("Zero-tax regime, optimised book at $1bn, means over each arm's 8 cells. The restriction of headline results to the prediction-loss arm was made after the economic arm's behaviour was observed (a post hoc deviation); "
             "this table documents the contrast and is not evidence for any claim. Diagnostic only.")
    return _tbl(raw, fmt, "Table S15. Prediction-loss and economic-loss arms at $1bn (diagnostic)", notes, ["sum_deu_1e9", "sum_ind_1e9", "sum_jpn_1e9"])


def table_recon():
    rows = []
    for c in COUNTRIES:
        r = pd.read_csv(B.src(f"reconciliation_{c}"))
        for _, q in r.iterrows():
            rows.append({"country": c, "aum": q["aum"], "B_A_points": q["B_A"] * 100 if pd.notna(q["B_A"]) else np.nan, "B_B_points": q["B_B"] * 100 if pd.notna(q["B_B"]) else np.nan,
                         "diff_A_minus_B_points": q["B_diff_A_minus_B"] * 100 if pd.notna(q["B_diff_A_minus_B"]) else np.nan, "solvent_A": bool(q["solvent_A"]),
                         "solvent_B": q["solvent_B"] if pd.notna(q["solvent_B"]) else np.nan})
    raw = pd.DataFrame(rows)
    fmt = pd.DataFrame({"Market": raw["country"].map(B.NAMES), "AUM": raw["aum"].map(B.aum_label), "B(A), Tier A": raw["B_A_points"].map(lambda x: "n/a" if np.isnan(x) else f"{x:+.2f}"),
                        "B(A), Tier B": raw["B_B_points"].map(lambda x: "n/a" if np.isnan(x) else f"{x:+.2f}"), "A minus B": raw["diff_A_minus_B_points"].map(lambda x: "n/a" if np.isnan(x) else f"{x:+.3f}"),
                        "Solvent (Tier A)": raw["solvent_A"].map(lambda x: "yes" if x else "no"), "Solvent (Tier B)": raw["solvent_B"].map(lambda x: "not run" if pd.isna(x) else ("yes" if x else "no"))})
    st = tier_gap_stats()
    gaps = "; ".join(f"{B.NAMES[c]} up to {v['max_abs_points']:.1f} points at {B.aum_label(v['at_aum'])}" for c, v in st.items())
    notes = ("Points of NAV per year. The reconciliation files hold only the rungs where Tier B was run (solvent comparator); insolvent rungs are not listed here and appear in the solvency ledger. The two accountings are not equal; the largest absolute gaps are " + gaps + ". "
             "Tier B is primary. Closeness at large B(A) would not be independent confirmation of the capacity effect, and B(A) remains an accounting difference against an infeasible comparator.")
    return _tbl(raw, fmt, "Table S16. Reconciliation of the two accountings of B(A), by rung", notes, RECON_KEYS)


def table_solvency():
    rows = []
    for c in COUNTRIES:
        a = pd.read_csv(B.src(f"tierA_{c}"))
        for _, q in a.iterrows():
            rows.append({"country": c, "aum": q["aum"], "solvent": bool(q["solvent"]), "cells_wiped_of_8": int(q["cells_wiped_of_8"]), "min_monthly_net_uncapped": q["min_monthly_net_uncapped"],
                         "min_monthly_net_capped": q["min_monthly_net_capped"], "first_uncapped_wipeout": q["first_uncapped_wipeout"] if pd.notna(q["first_uncapped_wipeout"]) else ""})
    raw = pd.DataFrame(rows)
    fmt = pd.DataFrame({"Market": raw["country"].map(B.NAMES), "AUM": raw["aum"].map(B.aum_label), "Solvent": raw["solvent"].map(lambda x: "yes" if x else "no"), "Cells wiped (of 8)": raw["cells_wiped_of_8"].astype(str),
                        "Worst month, uncapped": raw["min_monthly_net_uncapped"].map(lambda x: f"{x*100:.1f}%"), "Worst month, capped": raw["min_monthly_net_capped"].map(lambda x: f"{x*100:.1f}%"),
                        "First uncapped wipe-out": raw["first_uncapped_wipeout"].replace("", "none")})
    notes = ("Tier A solvency ledger for every rung. A rung is solvent only if no cell-month of either book is at or below -100%. A worst month below -100% means the comparator's account would be negative; such rungs get no B(A). "
             "Worst months are single-month net returns of the worst cell, not averages.")
    return _tbl(raw, fmt, "Table S17. Solvency ledger of the uncapped comparator and the capped book", notes, TIERA_KEYS)


def table_trade_size():
    d = pd.read_csv(B.src("dtv_support"))
    d["country"] = pd.Categorical(d["country"], COUNTRIES)
    raw = d.sort_values(["country", "aum", "book"]).reset_index(drop=True)
    fmt = pd.DataFrame({"Market": raw["country"].astype(str).map(B.NAMES), "AUM": raw["aum"].map(B.aum_label), "Book": raw["book"], "Notional in trades > 12% ADV": raw["share_notional_gt12pct_ADV"].map(lambda x: f"{x*100:.2f}%"),
                        "Notional in trades > 100% ADV": raw["share_notional_gt100pct_ADV"].map(lambda x: f"{x*100:.3f}%"), "Median trade (% ADV)": raw["notional_weighted_median_trade_pct_ADV"].map(lambda x: f"{x:.2f}")})
    notes = "From the cost-parity diagnostic: the share of traded notional in trades larger than 12% (respectively 100%) of the name's ADV, and the notional-weighted median trade as a percentage of ADV, for the rungs the diagnostic covers."
    return _tbl(raw, fmt, "Table S18. Trade size relative to ADV by book and mandate size", notes, ["dtv_support"])


def table_parity():
    d = pd.read_csv(B.src("parity_summary"))
    d["country"] = pd.Categorical(d["country"], COUNTRIES)
    raw = d.sort_values(["country", "aum", "book"]).reset_index(drop=True)
    fmt = pd.DataFrame({"Market": raw["country"].astype(str).map(B.NAMES), "AUM": raw["aum"].map(B.aum_label), "Book": raw["book"], "Cost, Tier A": raw["cost_A"].map(lambda x: f"{x:.2f}"),
                        "Cost, Tier B": raw["cost_B"].map(lambda x: f"{x:.2f}"), "A minus B": (raw["cost_A"] - raw["cost_B"]).map(lambda x: f"{x:+.2f}"), "Trade size": raw["e_D"].map(lambda x: f"{x:+.2f}"),
                        "Exit": raw["e_X"].map(lambda x: f"{x:+.2f}"), "Borrow": raw["e_B"].map(lambda x: f"{x:+.2f}"), "Interaction": raw["interaction"].map(lambda x: f"{x:+.2f}"),
                        "Residual": raw["residual_R"].map(lambda x: f"{x:+.3f}"), "Material": raw["material"].map(lambda x: "yes" if x else "no"), "Reconciled": raw["reconciled"].map(lambda x: "yes" if x else "no")})
    notes = ("Points of NAV per year. Each effect is the change in cost from switching one accounting convention from Tier B to Tier A (trade-size basis, exit treatment, borrow); effects plus interaction sum to the replicated difference; the residual is the recorded difference minus the replicated one. "
             "Material: the discrepancy exceeds 0.05 points; reconciled: the replication residual is within tolerance. This is accounting reconciliation of the cost function on existing weights, not the sensitivity of results to the exit treatment.")
    return _tbl(raw, fmt, "Table S19. Cost-parity reconciliation between the two accountings", notes, ["parity_summary"])


def table_design_counts():
    rows = []
    for c, k in (("DEU", "design_deu"), ("IND", "design_ind")):
        d = pd.read_csv(B.src(k))
        for bk in ("capped", "uncapped"):
            for ax in ("representation", "conditioning", "uncertainty"):
                q = d[(d["book"] == bk) & (d["axis"] == ax)]
                rows.append({"country": c, "book": bk, "axis": ax, "rungs": len(q), "holm_adjusted_available": int(q["p_holm"].notna().sum()), "holm_significant_5pct": int((q["p_holm"] < 0.05).sum()),
                             "unadjusted_p_below_5pct": int((q["p"] < 0.05).sum()), "largest_abs_t": float(q["t"].abs().max())})
    raw = pd.DataFrame(rows)
    fmt = pd.DataFrame({"Market": raw["country"].map(B.NAMES), "Book": raw["book"], "Axis": raw["axis"], "Rungs": raw["rungs"].astype(str), "Holm-adjusted p available": raw["holm_adjusted_available"].astype(str),
                        "Holm-significant at 5%": raw["holm_significant_5pct"].astype(str), "Unadjusted p < 5%": raw["unadjusted_p_below_5pct"].astype(str), "Largest |t|": raw["largest_abs_t"].map(lambda x: f"{x:.2f}")})
    notes = ("Counts over the mandate sizes of the design-identifiability tables. Holm adjustment is across the three axes within a rung; rungs without an adjusted value in the source are counted as unavailable, not as non-significant. "
             "Unadjusted counts are shown for transparency and carry no multiplicity control. Compare with the manuscript's 0 of 42 capped-book axis-rungs in each of Germany and India.")
    return _tbl(raw, fmt, "Table S20. Design-axis significance counts by market, book and axis", notes, ["design_deu", "design_ind"])


def table_not_built():
    rows = [(a, b, c) for a, b, c in B.NOT_BUILT]
    raw = pd.DataFrame(rows, columns=["candidate", "status", "reason"])
    fmt = raw.rename(columns={"candidate": "Candidate asset or comparison", "status": "Status", "reason": "Why it was not generated"})
    notes = "Assets and comparisons considered and not generated, with the reason; what would be needed (data or a separately authorised analysis) is stated where applicable. Nothing in this table was computed."
    return _tbl(raw, fmt, "Table S21. Inventory of blocked, unsupported and excluded assets", notes, [])


TABLES = [
    ("TAB_M4_construction_friction_spec", table_spec, "main_text", "MAIN_TEXT_ELIGIBLE", "tab:spec"),
    ("TAB_S6_terms_and_conventions", table_definitions, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s6"),
    ("TAB_S7_source_provenance_registry", table_registry, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s7"),
    ("TAB_S8_stage06_weight_provenance", table_provenance, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s8"),
    ("TAB_S9_c4_row_composition", table_funnel, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s9"),
    ("TAB_S10_coverage_by_year", table_cov_year, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s10"),
    ("TAB_S11_coverage_aggregation_audit", table_cov_audit, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s11"),
    ("TAB_S12_matched_book_all_rungs", table_matched_aum, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s12"),
    ("TAB_S13_cell_level_results_1bn", table_cells, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s13"),
    ("TAB_S14_optimised_book_all_rungs", table_aum_rungs, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s14"),
    ("TAB_S15_prediction_vs_economic_arm", table_arm, "supplementary", "DIAGNOSTIC_ONLY", "tab:s15"),
    ("TAB_S16_tierA_tierB_reconciliation", table_recon, "supplementary", "DIAGNOSTIC_ONLY", "tab:s16"),
    ("TAB_S17_solvency_ledger", table_solvency, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s17"),
    ("TAB_S18_trade_size_vs_adv", table_trade_size, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s18"),
    ("TAB_S19_cost_parity_reconciliation", table_parity, "supplementary", "DIAGNOSTIC_ONLY", "tab:s19"),
    ("TAB_S20_design_axis_significance_counts", table_design_counts, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s20"),
    ("TAB_S21_blocked_and_excluded_inventory", table_not_built, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s21"),
]

REVIEW.update({
    "TAB_M4_construction_friction_spec": "Answers: what the portfolios and frictions were. Read from the committed configuration and checked against the manuscript; the provenance caveat is in the notes. Placement: main text (the paper has no parameter table).",
    "TAB_S6_terms_and_conventions": "Answers: what each term means. No numbers computed. Placement: supplement.",
    "TAB_S7_source_provenance_registry": "Answers: where every number came from and whether its hash is verified. Placement: supplement (reproducibility record).",
    "TAB_S8_stage06_weight_provenance": "Answers: how firmly each stage-06 summary is tied to its weights. States the limits of modification-time identity. Placement: supplement.",
    "TAB_S9_c4_row_composition": "Answers: what the coverage denominator is made of. Row counts from flags. Placement: supplement.",
    "TAB_S10_coverage_by_year": "Answers: how coverage varies by year. Placement: supplement.",
    "TAB_S11_coverage_aggregation_audit": "Answers: how the 0.989 statistic is computed and how sensitive it is. Source counts only; says what cannot be established. Placement: supplement.",
    "TAB_S12_matched_book_all_rungs": "Answers: what matched-book results exist beyond $1bn. Absent rungs are not filled. Placement: supplement.",
    "TAB_S13_cell_level_results_1bn": "Answers: how results differ across the 8 cells. Placement: supplement.",
    "TAB_S14_optimised_book_all_rungs": "Answers: optimised-book summary at every committed rung. Placement: supplement.",
    "TAB_S15_prediction_vs_economic_arm": "Answers: why the economic arm is outside the headline. Diagnostic only.",
    "TAB_S16_tierA_tierB_reconciliation": "Answers: how the two B(A) accountings differ rung by rung. Diagnostic only.",
    "TAB_S17_solvency_ledger": "Answers: where and when the uncapped comparator fails. Placement: supplement.",
    "TAB_S18_trade_size_vs_adv": "Answers: trade size against liquidity by book. Placement: supplement.",
    "TAB_S19_cost_parity_reconciliation": "Answers: why two cost accountings differ. Explicitly not the exit-treatment sensitivity. Diagnostic only.",
    "TAB_S20_design_axis_significance_counts": "Answers: how many axis contrasts are significant. Unavailable adjusted values counted separately. Placement: supplement.",
    "TAB_S21_blocked_and_excluded_inventory": "Answers: what is not available and why. Placement: supplement.",
})

NOT_BUILT = [
    ("Drawdown and terminal-NAV strip by prediction cell", "EXCLUDED_WITH_REASON", "Adds little beyond the cell-level dispersion figure and the mean drawdown column of the all-rungs table."),
    ("Calendar-year returns as a table", "EXCLUDED_WITH_REASON", "Duplicates the calendar-year figure's data; the figure answers the question."),
    ("Capacity-channel Sharpe ladders and the capacity-channel inference attachments (all markets)", "EXCLUDED_WITH_REASON", "They express capacity in Sharpe points, the framing withdrawn in the candidate; several are non-compliant ladders."),
    ("Coverage-asymmetry worked failure (the retracted t = -6.098)", "EXCLUDED_WITH_REASON", "A retracted artefact; no approved committed data series supports a plot, and drawing it could be read as a result."),
    ("Projected unresolved-share and per-month unresolved counts from the support census", "EXCLUDED_WITH_REASON", "They visualise the blocked revised exit policy and could be read as Phase C progress."),
    ("India section 112A reference-value inventory (the 456 missing values)", "NOT_SUPPORTED_BY_AVAILABLE_ARTIFACTS", "The tracked bound files hold the supplied reference values; no tracked artifact lists the missing ones."),
    ("Japan trade-size or gross-exposure view of the capped decile book", "NOT_SUPPORTED_BY_AVAILABLE_ARTIFACTS", "No committed Japanese table holds attained gross exposure; the trade-size diagnostic covers only the rungs it lists."),
    ("Gross-to-net cost decomposition by component (spread, impact, borrow) for every rung", "NOT_SUPPORTED_BY_AVAILABLE_ARTIFACTS", "Component monthly series exist only for the six parity-diagnostic rungs; extending them needs the frozen data and weights."),
    ("Impact-coefficient (k) sensitivity plots", "EXCLUDED_WITH_REASON", "A cost-sensitivity result outside the authorised as-run set; the committed attachment is not in the traceability set."),
    ("Liquidity-tercile and theme-level performance panels", "EXCLUDED_WITH_REASON", "Not in the candidate's traceability set; several variants are older or non-compliant."),
]
