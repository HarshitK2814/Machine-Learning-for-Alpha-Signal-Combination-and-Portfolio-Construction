#!/usr/bin/env python
"""Publication tables and figures for the as-run-only manuscript, built from COMMITTED artifacts only.

This is a deterministic presentation layer. It reads tracked CSVs (the snapshots listed in
``submission_candidate_as_run_only/TRACEABILITY.csv`` plus two tracked census and capacity tables), verifies their SHA-256
against that file where a hash is recorded, and writes figures, tables, captions and a catalog. It trains nothing, runs no
backtest, optimises nothing and computes no new statistic: every plotted or tabulated value is either a column of a tracked
artifact, a mean of such a column over the 8 prediction cells (the same aggregation the candidate checker uses), or a
ratio or product of tracked columns whose definition is stated in the table notes.

Excluded by construction: Germany's after-tax inference statistic (no committed artifact holds it; this script never reads
``after_tax_inference`` for Germany), any Phase C quantity, any B(A) expressed as a Sharpe-point gain, and any Japan result
described as a confirmation.

    python tools/make_paper_assets.py                       # writes paper_assets_as_run_only/
    python tools/make_paper_assets.py --out some/other/dir  # used by the determinism test
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
DEFAULT_OUT = ROOT / "paper_assets_as_run_only"
TRACE = ROOT / "submission_candidate_as_run_only" / "TRACEABILITY.csv"
COUNTRIES = ("DEU", "IND", "JPN")
NAMES = {"DEU": "Germany", "IND": "India", "JPN": "Japan"}
# Okabe-Ito colours: distinguishable under the common colour-vision deficiencies.
COL = {"DEU": "#0072B2", "IND": "#D55E00", "JPN": "#009E73"}
GREY, DARK = "#9A9A9A", "#222222"
EXTRA = {
    "tier_counts": "results/phase_c_census_v3_2026-10-14/tier_counts_by_metric.csv",
    "tierA_DEU": "results/capacity_return_difference/tierA_DEU.csv",
    "tierA_IND": "results/capacity_return_difference/tierA_IND.csv",
    "tierA_JPN": "results/capacity_return_difference/tierA_JPN.csv",
}
MDE_Z = 1.96 + 0.8416  # the multiplier used by tools/gate2_power.py for 5% two-sided, 80% power


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CHK = _load("check_submission_candidate_for_assets", ROOT / "tools" / "check_submission_candidate.py")
MKF = _load("make_figures_for_assets", ROOT / "tools" / "make_figures.py")
SOURCES = {**CHK.ARTIFACTS, **EXTRA}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def src(key: str) -> Path:
    return ROOT / SOURCES[key]


def verify_sources() -> dict[str, str]:
    """Hash every source; fail if a hash recorded in TRACEABILITY.csv differs. Returns key -> sha256."""
    recorded = {r["key"]: r["sha256"] for r in csv.DictReader(open(TRACE, encoding="utf-8"))}
    out = {}
    for key in SOURCES:
        h = sha256(src(key))
        if key in recorded and recorded[key] != h:
            raise SystemExit(f"source {key} ({SOURCES[key]}) does not match its recorded SHA-256")
        out[key] = h
    return out


# ----------------------------------------------------------------------------------------------------------------
# data layer: deterministic transformations of tracked columns
# ----------------------------------------------------------------------------------------------------------------
def coverage_monthly() -> pd.DataFrame:
    d = pd.read_csv(src("coverage"))
    d["month"] = pd.to_datetime(d["month"] + "-01")
    d["share"] = d["c4_with_certified_c6"] / d["c4_in_c1_universe"]
    return d.sort_values(["country", "month"]).reset_index(drop=True)


def stage6(key: str) -> pd.DataFrame:
    """Stage-06 summary rows for the 8 prediction cells, one row per (cell, regime)."""
    d = pd.read_csv(src(key))
    return d[d["strategy"].str.contains("-P-")].copy()


def stage6_means(key: str) -> dict:
    d = stage6(key)
    ex = d[d["regime"] == "tax_exempt"]
    st = d[d["regime"] != "tax_exempt"]
    regimes = sorted(st["regime"].unique())
    assert len(regimes) == 1, (key, regimes)
    return {
        "cells": int(ex["strategy"].nunique()), "months": int(ex["months"].iloc[0]), "regime_label": regimes[0],
        "gross_sharpe": ex["gross_sharpe"].mean(), "net_sharpe": ex["net_sharpe"].mean(),
        "after_tax_sharpe": st["after_tax_sharpe"].mean(), "cost_drag_bps": ex["cost_drag_ann_bps"].mean(),
        "tax_drag_bps": st["tax_drag_ann_bps"].mean(), "turnover": ex["turnover_mean"].mean(),
        "lt_share": st["lt_share_of_gains"].mean(), "wash_bps": st["wash_disallowed_ann_bps"].mean(),
    }


RUNG_KEYS = {("DEU", 1e8): "sum_deu_1e8", ("DEU", 1e9): "sum_deu_1e9", ("DEU", 1e10): "sum_deu_1e10",
             ("IND", 1e9): "sum_ind_1e9",
             ("JPN", 1e8): "sum_jpn_1e8", ("JPN", 1e9): "sum_jpn_1e9", ("JPN", 1e10): "sum_jpn_1e10"}


def matched_book() -> pd.DataFrame:
    return pd.read_csv(src("matched_1e9"))


def b_frames() -> dict:
    cap = ROOT / "results" / "capacity_return_difference"
    return {c: MKF.b_series(c, cap) for c in COUNTRIES}


def tierb_full(country: str) -> pd.DataFrame:
    return pd.read_csv(src(f"tierB_{country}"))


# ----------------------------------------------------------------------------------------------------------------
# style
# ----------------------------------------------------------------------------------------------------------------
def set_style():
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams.update({
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "font.family": "DejaVu Sans", "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#E6E6E6",
        "grid.linewidth": 0.5, "grid.linestyle": "-", "axes.axisbelow": True, "lines.linewidth": 1.2,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "path", "svg.hashsalt": "paper_assets_as_run_only",
        "figure.dpi": 100, "savefig.dpi": 300,
    })


def aum_label(x: float) -> str:
    return f"${x/1e9:g}bn" if x >= 1e9 else (f"${x/1e6:g}mn" if x >= 1e6 else f"${x/1e3:g}k")


def save_fig(fig, base: Path):
    base.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(base.with_suffix(".pdf"), metadata={"Creator": None, "Producer": None, "CreationDate": None, "ModDate": None})
    fig.savefig(base.with_suffix(".svg"), metadata={"Date": None, "Creator": None})
    fig.savefig(base.with_suffix(".png"), dpi=300, metadata={"Software": None})
    import matplotlib.pyplot as plt
    plt.close(fig)


def foot(fig, text, size=5.8, width=150):
    """Wrapped source/limitation note at the bottom of a figure; returns the bottom margin (figure fraction) to reserve."""
    import textwrap
    lines = textwrap.wrap(text, width)
    fig.text(0.01, 0.008, "\n".join(lines), fontsize=size, color="#444444", va="bottom", ha="left")
    h = fig.get_size_inches()[1]
    return (len(lines) * size * 1.4 / 72 + 0.14) / h


def plain_symlog_ticks(ax, top, bottom=0.0):
    """Explicit tick labels (-10, -1, 0, 1, 10, 100) instead of the 10^k notation, which reads oddly for negative values."""
    cand = [-100, -10, -1, 0, 1, 10, 100, 1000]
    ticks = [t for t in cand if bottom * 1.6 <= t <= max(top * 1.6, 1)] if bottom < 0 else [t for t in cand if 0 <= t <= max(top * 1.6, 1)]
    ax.set_yticks(ticks)
    ax.set_yticklabels([f"{t:g}" for t in ticks])
    ax.minorticks_off()


def panel_letter(ax, s):
    ax.text(-0.02, 1.04, s, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="right")


# ----------------------------------------------------------------------------------------------------------------
# figures: each builder returns a matplotlib Figure (testable) and is saved by the driver
# ----------------------------------------------------------------------------------------------------------------
def fig_pipeline():
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 64)
    ax.axis("off")

    def box(x, y, w, h, title, body, fc="#F2F6FA", ec="#4A6FA5", fs=6.2):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.0", fc=fc, ec=ec, lw=0.9))
        ax.text(x + w / 2, y + h - 1.6, title, ha="center", va="top", fontsize=7.2, fontweight="bold", color=DARK, linespacing=1.15)
        ax.text(x + w / 2, y + h - 8.0, body, ha="center", va="top", fontsize=fs, color=DARK, linespacing=1.4)

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=0.9, color=DARK, shrinkA=0, shrinkB=0))

    y0, h = 34, 26
    box(0.5, y0, 17.5, h, "Certified panels", "from a separate data\nworkstream:\nC1 universe\nC2 signals\nC4 targets\nC6 cost inputs\nC14 tax regimes")
    box(21, y0, 18.5, h, "Stage 02", "models and signals:\n2x2x2x2 factorial\n(representation,\nconditioning, loss,\nuncertainty); the 8\nprediction-loss cells\nare used")
    box(42.5, y0, 19.5, h, "Stage 04", "portfolio books:\nuncapped decile spread\n(not executable)\ncapped decile spread\n(participation cap)\noptimised book\n(full constraints)")
    box(65, y0, 17.5, h, "Stage 06", "lot-level backtest of\nthe same weights:\nzero-tax control and\nstatutory regime;\ngross, net,\nafter-tax")
    box(85.5, y0, 14, h, "Committed\nsnapshots", "docs/attachments\nresults/\nhashes in\nTRACEABILITY.csv", fc="#F4F4F4", ec="#6E6E6E")
    for x0, x1 in ((18.3, 20.7), (39.8, 42.2), (62.3, 64.7), (82.8, 85.2)):
        arrow(x0, y0 + h / 2, x1, y0 + h / 2)
    box(21, 2, 41, 24, "Frictions applied to every book", "spread, 1 bp commission, square-root\nimpact scaled to AUM, 1% flat borrow;\nparticipation cap |w| <= 5% of ADV / AUM;\nlot-level capital-gains tax (Germany and\nJapan flat; India as configured)", fc="#FBF6EC", ec="#B58A2B")
    box(65, 2, 34.5, 24, "Not run, not used, unknown", "Phase C: blocked, unrun\nGermany's after-tax inference\nstatistic: excluded, no artifact\nexit-treatment sensitivity: unknown\nB(A): accounting unit, not a return", fc="#FAF0F0", ec="#A04040")
    arrow(41, 26.6, 52, y0 - 0.6)
    ax.set_title("Research design and as-run analysis pipeline (schematic; no data are plotted)", fontsize=9, loc="left")
    return fig


def fig_coverage():
    import matplotlib.pyplot as plt
    d = coverage_monthly()
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    ypos = {"DEU": None, "IND": 0.90, "JPN": 1.0}
    for c in COUNTRIES:
        s = d[d["country"] == c]
        ax.plot(s["month"], s["share"], color=COL[c], lw=1.3)
        y = s["share"].iloc[-1] if ypos[c] is None else ypos[c]
        ax.text(s["month"].iloc[-1] + pd.Timedelta(days=45), y, f"{NAMES[c]} (mean {s['share'].mean():.3f})", color=COL[c], va="center", fontsize=7.5)
    low = d[d["share"] < 0.5]
    low = low[low["country"] != "DEU"]
    for r in low.itertuples():
        ax.annotate(f"{NAMES[r.country]} {r.month:%Y-%m}:\n{int(r.c4_with_certified_c6)} of {int(r.c4_in_c1_universe)}\ncertified", xy=(r.month, r.share),
                    xytext=(r.month + pd.Timedelta(days=200), 0.28), fontsize=6.3, color=COL[r.country],
                    arrowprops=dict(arrowstyle="-", lw=0.6, color=COL[r.country]))
    ax.set_ylim(0, 1.05)
    ax.set_xlim(d["month"].min(), d["month"].max() + pd.Timedelta(days=560))
    ax.set_ylabel("share of in-universe securities with\ncertified cost inputs")
    ax.set_xlabel("month (evaluation window 2009-01 to 2019-12)")
    ax.set_title("Cost-input coverage of the investable universe, by month", loc="left")
    fig.text(0.01, 0.012, "Share = securities with a certified spread, daily volatility and USD ADV divided by in-universe securities, per month (outcome-free support census).\n"
             "An uncertified security-month is non-tradeable; none is imputed.", fontsize=6, color="#444444", va="bottom")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    return fig


def fig_ladder():
    import matplotlib.pyplot as plt
    mb = matched_book()
    cap = mb[mb["book"] == "capped"].set_index("country")
    unc = mb[mb["book"] == "uncapped"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.3), gridspec_kw={"width_ratios": [1.15, 1]})
    ys = {c: i for i, c in enumerate(reversed(COUNTRIES))}
    for c in COUNTRIES:
        r = cap.loc[c]
        y = ys[c]
        xs = [r.sharpe_gross, r.sharpe_net, r.sharpe_after_tax]
        a.plot(xs, [y] * 3, "-", color=COL[c], lw=1.0, alpha=0.7, zorder=2)
        for x, m, lab in zip(xs, ("o", "s", "D"), ("gross", "net of costs", "after tax")):
            a.plot([x], [y], m, color=COL[c], ms=5.5, zorder=3)
            dy = {"gross": 0.22, "net of costs": 0.22, "after tax": -0.30}[lab]
            a.text(x, y + dy, f"{x:+.2f}", ha="center", va="center", fontsize=6.3, color=DARK)
    a.axvline(0, color=DARK, lw=0.7)
    a.set_yticks(list(ys.values()))
    a.set_yticklabels([NAMES[c] for c in ys])
    a.set_ylim(-0.6, 2.9)
    a.set_xlabel("annualised Sharpe ratio, capped decile composite")
    from matplotlib.lines import Line2D
    a.legend([Line2D([], [], marker=m, color="0.35", ls="", ms=5) for m in ("o", "s", "D")], ["gross", "net of costs", "after tax"],
             loc="upper left", frameon=False, handletextpad=0.3, ncol=3, columnspacing=1.0, bbox_to_anchor=(0.0, 1.0))
    a.set_title("(a) Gross, net and after-tax Sharpe at $1bn", loc="left")
    # channels
    w = 0.34
    for i, c in enumerate(COUNTRIES):
        r = cap.loc[c]
        b.bar(i - w / 2, r.cost_channel, w, color=COL[c], alpha=0.95)
        b.bar(i + w / 2, r.tax_channel, w, color=COL[c], alpha=0.5, hatch="///", edgecolor="white", lw=0)
        b.text(i - w / 2, r.cost_channel - 0.04, f"{r.cost_channel:+.2f}", ha="center", va="top", fontsize=6.3)
        b.text(i + w / 2, r.tax_channel - 0.04, f"{r.tax_channel:+.2f}", ha="center", va="top", fontsize=6.3)
    b.axhline(0, color=DARK, lw=0.7)
    b.set_xticks(range(3))
    b.set_xticklabels([NAMES[c] for c in COUNTRIES])
    b.set_ylim(min(cap.cost_channel.min(), cap.tax_channel.min()) - 0.25, 0.12)
    b.set_ylabel("Sharpe points")
    b.set_title("(b) Cost (solid), tax (hatched)", loc="left")
    n_unc = len(unc)
    note = (f"Capped decile composite, {int(cap.months.max())} months, 8 prediction cells. "
            f"The uncapped comparator for Japan ({unc.iloc[0].sharpe_net:+.2f} net) is not executable and is not plotted. "
            "No intervals are drawn: the source holds no interval for these Sharpe ratios.") if n_unc else ""
    bot = foot(fig, note)
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_capacity_B():
    import matplotlib.pyplot as plt
    frames = b_frames()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.1))
    for ax, c in zip(axes, COUNTRIES):
        d = frames[c]
        t = tierb_full(c).set_index("aum")
        s = d[d["status"] == "solvent"].copy()
        s["lo"] = t.loc[s["aum"], "B_ci_low"].to_numpy() * 100
        s["hi"] = t.loc[s["aum"], "B_ci_high"].to_numpy() * 100
        y = s["B_B"].to_numpy() * 100
        ax.set_xscale("log")
        ax.set_yscale("symlog", linthresh=1.0)
        ax.errorbar(s["aum"], y, yerr=[y - s["lo"], s["hi"] - y], fmt="none", ecolor=COL[c], elinewidth=0.6, alpha=0.6, capsize=0)
        ax.plot(s["aum"], y, "-", color=COL[c], lw=1.0)
        solid, hollow = s[~s["near_ruined"]], s[s["near_ruined"]]
        ax.plot(solid["aum"], solid["B_B"] * 100, "o", color=COL[c], ms=3.6)
        ax.plot(hollow["aum"], hollow["B_B"] * 100, "o", mfc="white", mec=COL[c], ms=4.2, mew=0.9)
        ax.axhline(0, color=DARK, lw=0.6)
        xs = list(d["aum"])
        ax.set_xlim(min(xs) / 1.5, max(xs) * 1.5)
        ax.set_xticks(xs[::3])
        ax.set_xticklabels([aum_label(x) for x in xs[::3]], rotation=45, ha="right")
        ins = d[d["status"] == "insolvent"]
        if len(ins):
            ax.axvspan(ins["aum"].min() / 1.25, max(xs) * 1.5, color="#E4E4E4", zorder=0)
            ax.text(ins["aum"].min(), 0.96, "comparator insolvent:\nno B(A) computed", transform=ax.get_xaxis_transform(),
                    fontsize=6, va="top", ha="left", color="#444444")
        ax.set_title(NAMES[c], color=COL[c], loc="left")
        ax.set_xlabel("mandate size (AUM)")
        plain_symlog_ticks(ax, float(np.nanmax(s["hi"])), float(np.nanmin(s["lo"])))
    axes[0].set_ylabel("B(A), points of NAV per year (symlog)")
    bot = foot(fig, "B(A) = capped minus uncapped mean net return of the decile composites, Tier B (pipeline accounting), solvent rungs only; bars: unadjusted 95% "
             "studentised-bootstrap intervals. Hollow markers: solvent but near-ruined comparator (terminal wealth < "
             f"{MKF.NEAR_RUINED_WEALTH:g}). B(A) is an accounting difference against an infeasible plan, not realised or investable performance.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_wealth():
    import matplotlib.pyplot as plt
    frames = b_frames()
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9))
    for ax, c in zip(axes, COUNTRIES):
        d = frames[c]
        s = d[d["status"] == "solvent"]
        ax.set_xscale("log")
        ax.set_yscale("log")
        floor = 1e-6
        y = s["wealth_B"].clip(lower=floor)
        ax.plot(s["aum"], y, "o-", color=COL[c], ms=3.4)
        clipped = s[s["wealth_B"] < floor]
        if len(clipped):
            ax.plot(clipped["aum"], [floor] * len(clipped), "v", color=COL[c], ms=4)
        ax.axhline(1.0, color=DARK, lw=0.6)
        ax.axhline(MKF.NEAR_RUINED_WEALTH, color="#A04040", lw=0.8, ls="--")
        ax.set_ylim(floor / 2, 1e1)
        xs = list(d["aum"])
        ax.set_xlim(min(xs) / 1.5, max(xs) * 1.5)
        ax.set_xticks(xs[::3])
        ax.set_xticklabels([aum_label(x) for x in xs[::3]], rotation=45, ha="right")
        ins = d[d["status"] == "insolvent"]
        if len(ins):
            ax.axvspan(ins["aum"].min() / 1.25, max(xs) * 1.5, color="#E4E4E4", zorder=0)
        ax.set_title(NAMES[c], color=COL[c], loc="left")
        ax.set_xlabel("mandate size (AUM)")
    axes[0].set_ylabel("uncapped comparator: compounded\nterminal wealth (start = 1; log)")
    bot = foot(fig, "Tier B uncapped composite, solvent rungs. Dashed line: the display flag for near-ruin used in the B(A) figure (not an exclusion rule). Triangles: below the "
             "axis floor of 1e-6. Grey: comparator insolvent, nothing plotted.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_rungs():
    import matplotlib.pyplot as plt
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.0))
    for c in COUNTRIES:
        pts = [(au, stage6_means(k)) for (cc, au), k in sorted(RUNG_KEYS.items()) if cc == c]
        xs = [p[0] for p in pts]
        a.plot(xs, [p[1]["net_sharpe"] for p in pts], "o-" if len(pts) > 1 else "o", color=COL[c], ms=4.5, label=NAMES[c])
        b.plot(xs, [p[1]["cost_drag_bps"] for p in pts], "o-" if len(pts) > 1 else "o", color=COL[c], ms=4.5)
    for ax in (a, b):
        ax.set_xscale("log")
        ax.set_xticks([1e8, 1e9, 1e10])
        ax.set_xticklabels(["$100mn", "$1bn", "$10bn"])
        ax.set_xlabel("mandate size (AUM)")
    a.axhline(0, color=DARK, lw=0.7)
    a.set_ylabel("net Sharpe, optimised book\n(mean of 8 prediction cells)")
    a.legend(frameon=False, loc="best")
    a.set_title("(a) Net Sharpe", loc="left")
    b.set_yscale("log")
    b.set_ylabel("cost drag, basis points per year (log)")
    b.set_title("(b) Cost drag", loc="left")
    bot = foot(fig, "Zero-tax regime, stage-06 summaries. India has a committed summary at $1bn only; no other India rung exists and none is interpolated. "
             "Descriptive point estimates, no inference. The German snapshots come from an earlier script version.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_design_axes():
    import matplotlib.pyplot as plt
    g = pd.read_csv(src("gate2"))
    axes_order = ["representation", "conditioning", "uncertainty"]
    mm = g.groupby("country")["months"].first()
    months_txt = ", ".join(f"{NAMES[c]} {int(mm[c])}" for c in COUNTRIES)
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)
    off = {"DEU": -0.22, "IND": 0.0, "JPN": 0.22}
    for c in COUNTRIES:
        s = g[g["country"] == c].set_index("axis").loc[axes_order]
        ys = np.arange(3) + off[c]
        a.plot(s["t"], ys, "o", color=COL[c], ms=4.8, label=NAMES[c])
        b.plot(s["effect"].abs(), ys, "o", color=COL[c], ms=4.8)
        b.plot(MDE_Z * s["se"], ys, "|", color=COL[c], ms=9, mew=1.6)
    a.axvline(0, color=DARK, lw=0.6)
    for z in (-1.96, 1.96):
        a.axvline(z, color=GREY, lw=0.8, ls="--")
    a.set_yticks(range(3))
    a.set_yticklabels(axes_order)
    a.set_ylim(-0.6, 2.6)
    a.set_xlabel("t-statistic of the axis contrast (unadjusted)")
    a.set_title("(a) Observed contrasts at $1bn", loc="left")
    a.legend(frameon=False, loc="lower right")
    a.text(2.03, 2.52, "unadjusted 5%\nreference (dashed)", fontsize=6, ha="left", va="top", color="#555555")
    b.set_xlabel("Sharpe points (dot: |effect|; bar: MDE)")
    b.set_title("(b) Observed size vs detectability", loc="left")
    bot = foot(fig, f"Optimised book at $1bn, {months_txt} months. MDE = {MDE_Z:.4f} x paired standard error (5% two-sided, 80% power; tools/gate2_power.py). "
             "Japan's conditioning contrast is exploratory and unadjusted; it is disclosed, not claimed. Diagnostic only.")
    fig.tight_layout(rect=(0, bot, 1, 1))
    return fig


def fig_B_components():
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9))
    for ax, c in zip(axes, COUNTRIES):
        t = tierb_full(c)
        t = t[t["solvent"]]
        ax.set_xscale("log")
        ax.set_yscale("symlog", linthresh=1.0)
        ax.plot(t["aum"], t["cost_saved"] * 100, "-", color=COL[c], lw=1.2, label="cost saved by capping")
        ax.plot(t["aum"], t["gross_forgone"] * 100, "--", color=COL[c], lw=1.2, label="gross return forgone")
        ax.plot(t["aum"], t["B"] * 100, ":", color=DARK, lw=1.4, label="B(A) = sum")
        ax.axhline(0, color=DARK, lw=0.6)
        xs = list(t["aum"])
        ax.set_xticks(xs[::3])
        ax.set_xticklabels([aum_label(x) for x in xs[::3]], rotation=45, ha="right")
        ax.set_title(NAMES[c], color=COL[c], loc="left", pad=12)
        ax.set_xlabel("mandate size (AUM)")
        plain_symlog_ticks(ax, float(t["cost_saved"].max() * 100), float(t["gross_forgone"].min() * 100))
    axes[0].set_ylabel("points of NAV per year (symlog)")
    from matplotlib.lines import Line2D
    fig.legend([Line2D([], [], color="0.2", ls="-"), Line2D([], [], color="0.2", ls="--"), Line2D([], [], color="0.2", ls=":", lw=1.6)],
               ["cost saved by capping", "gross return forgone", "B(A) = sum"], loc="upper center", ncol=3, frameon=False, fontsize=6.5,
               bbox_to_anchor=(0.5, 1.0))
    bot = foot(fig, "Tier B, solvent rungs only. B(A) equals gross forgone plus cost saved (the source reconciliation residual is zero to rounding). "
             "Most of B(A) is the cost the uncapped comparator would pay, i.e. an accounting identity against an infeasible plan.")
    fig.tight_layout(rect=(0, bot, 1, 0.92))
    return fig


# ----------------------------------------------------------------------------------------------------------------
# tables
# ----------------------------------------------------------------------------------------------------------------
def fnum(x, nd=3, sign=False):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def tex_escape(s: str) -> str:
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("$", "\\$"), ("#", "\\#"), ("_", "\\_"), ("{", "\\{"), ("}", "\\}"), ("~", "\\textasciitilde{}"), ("^", "\\textasciicircum{}")):
        s = s.replace(a, b)
    return s


def write_table(base: Path, raw: pd.DataFrame, fmt: pd.DataFrame, caption: str, notes: str, label: str):
    base.parent.mkdir(parents=True, exist_ok=True)
    raw.to_csv(base.with_suffix(".csv"), index=False, lineterminator="\n")
    cols = list(fmt.columns)
    md = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    md += ["| " + " | ".join(str(v) for v in row) + " |" for row in fmt.itertuples(index=False)]
    base.with_suffix(".md").write_text(f"**{caption}**\n\n" + "\n".join(md) + f"\n\n*Notes.* {notes}\n", encoding="utf-8", newline="\n")
    spec = "l" + "r" * (len(cols) - 1)
    body = ["\\begin{table}[t]", "\\centering", "\\small", f"\\caption{{{tex_escape(caption)}}}", f"\\label{{{label}}}", f"\\begin{{tabular}}{{{spec}}}", "\\toprule",
            " & ".join(tex_escape(c) for c in cols) + " \\\\", "\\midrule"]
    body += [" & ".join(tex_escape(str(v)) for v in row) + " \\\\" for row in fmt.itertuples(index=False)]
    body += ["\\bottomrule", "\\end{tabular}", "\\par\\vspace{2pt}", f"\\parbox{{\\textwidth}}{{\\footnotesize {tex_escape(notes)}}}", "\\end{table}"]
    base.with_suffix(".tex").write_text("\n".join(body) + "\n", encoding="utf-8", newline="\n")


def table_market() -> tuple:
    cv = coverage_monthly()
    rows = []
    for c in COUNTRIES:
        s = cv[cv["country"] == c]
        rows.append({"country": NAMES[c], "first_month": s["month"].min().strftime("%Y-%m"), "last_month": s["month"].max().strftime("%Y-%m"),
                     "months": len(s), "in_universe_names_mean": s["c4_in_c1_universe"].mean(),
                     "certified_cost_input_names_mean": s["c4_with_certified_c6"].mean(),
                     "coverage_mean": s["share"].mean(), "coverage_min": s["share"].min(), "coverage_max": s["share"].max()})
    raw = pd.DataFrame(rows)
    fmt = pd.DataFrame({"Market": raw["country"], "Window": raw["first_month"] + " to " + raw["last_month"], "Months": raw["months"].astype(str),
                        "In-universe names (mean)": raw["in_universe_names_mean"].map(lambda x: fnum(x, 0)),
                        "With certified cost inputs (mean)": raw["certified_cost_input_names_mean"].map(lambda x: fnum(x, 0)),
                        "Coverage, mean": raw["coverage_mean"].map(fnum), "min": raw["coverage_min"].map(fnum), "max": raw["coverage_max"].map(fnum)})
    lows = []
    for c in COUNTRIES:
        s_ = cv[cv["country"] == c]
        r_ = s_.loc[s_["share"].idxmin()]
        lows.append(f"{NAMES[c]} {r_['month']:%Y-%m}: {int(r_['c4_with_certified_c6'])} of {int(r_['c4_in_c1_universe'])}")
    notes = ("Coverage = security-months with a certified spread, daily volatility and USD ADV divided by in-universe security-months, per month. Counts are means over months. "
             "An uncertified security-month is non-tradeable and is not imputed. Lowest month by market (certified of in-universe): " + "; ".join(lows) + ". "
             "India's tax panel has 131 months in the stage-06 summaries. Source: outcome-free support census; it is a description of inputs, not a result.")
    return raw, fmt, "Table 1. Markets, evaluation window and cost-input coverage", notes, ["coverage"]


def table_outcomes() -> tuple:
    mb = matched_book()
    mb = mb.assign(order=mb["book"].map({"capped": 0, "uncapped": 1})).sort_values(["country", "order"])
    mb["country"] = pd.Categorical(mb["country"], COUNTRIES)
    mb = mb.sort_values(["country", "order"]).drop(columns="order")
    raw = mb.reset_index(drop=True)
    fmt = pd.DataFrame({"Market": raw["country"].map(NAMES), "Book": raw["book"], "Gross Sharpe": raw["sharpe_gross"].map(fnum),
                        "Net Sharpe": raw["sharpe_net"].map(fnum), "After-tax Sharpe": raw["sharpe_after_tax"].map(fnum),
                        "Cost channel": raw["cost_channel"].map(lambda x: fnum(x, 3, True)), "Tax channel": raw["tax_channel"].map(lambda x: fnum(x, 3, True)),
                        "Tax t": raw["tax_t"].map(lambda x: fnum(x, 2, True)), "Tax p": raw["tax_p"].map(fnum),
                        "Net t vs 0": raw["net_t_vs_zero"].map(lambda x: fnum(x, 2, True)), "Months": raw["months"].astype(int).astype(str)})
    notes = ("Decile composites at $1bn, matched-book accounting (same weights, zero-tax control and statutory regime). Channels are differences in Sharpe points (cost: net minus gross; tax: "
             "after-tax minus net). The uncapped book is not executable and is shown only as the comparator; its Japanese net Sharpe reflects near-ruin. No net Sharpe is significantly positive. "
             "Tax t and p are the source's paired block-bootstrap values for the after-tax minus net Sharpe difference (block 6), unadjusted for multiplicity; net t is a Newey-West t-statistic against zero. Germany's optimised-book inference statistic is not reported: no committed artifact holds it.")
    return raw, fmt, "Table 2. Matched-book outcomes at $1bn by market", notes, ["matched_1e9"]


def table_statutes() -> tuple:
    from alphacomb.tax.jurisdictions import get_jurisdiction
    rows = []
    for c in COUNTRIES:
        m = stage6_means(RUNG_KEYS[(c, 1e9)])
        r = {"country": NAMES[c], "as_run_regime_label": m["regime_label"], "lt_share_of_gains_mean": m["lt_share"], "wash_disallowed_bps_mean": m["wash_bps"]}
        if c in ("DEU", "JPN"):
            j = get_jurisdiction(c)
            r["short_term_rate"], r["long_term_rate"] = j.regime.short_term_rate, j.regime.long_term_rate
        else:
            r["short_term_rate"], r["long_term_rate"] = float("nan"), float("nan")
        rows.append(r)
    raw = pd.DataFrame(rows)
    fmt = pd.DataFrame({"Market": raw["country"], "Regime label in the stage-06 summary": raw["as_run_regime_label"],
                        "Short-term rate": raw["short_term_rate"].map(lambda x: "see label" if np.isnan(x) else f"{x*100:.3f}%"),
                        "Long-term rate": raw["long_term_rate"].map(lambda x: "see label" if np.isnan(x) else f"{x*100:.3f}%"),
                        "Long-term share of gains": raw["lt_share_of_gains_mean"].map(lambda x: fnum(x, 4)),
                        "Wash-sale disallowed (bp/yr)": raw["wash_disallowed_bps_mean"].map(lambda x: fnum(x, 2))})
    notes = ("Rates for Germany and Japan are the configured values in src/alphacomb/tax/jurisdictions.py (flat; every numeric rate in that file is marked as unverified by the project and this is "
             "not a legal review). India's rates are not restated here: the regime label as run in stage 06 is shown verbatim. The long-term share is exactly zero under flat statutes by "
             "construction, a mechanical consequence and not an estimate. Means over the 8 prediction cells at $1bn, statutory regime rows.")
    return raw, fmt, "Table 3. Tax regimes as run", notes, ["sum_deu_1e9", "sum_ind_1e9", "sum_jpn_1e9"]


def table_cost_accounting() -> tuple:
    rows = []
    for c in COUNTRIES:
        m = stage6_means(RUNG_KEYS[(c, 1e9)])
        rows.append({"country": NAMES[c], "cells": m["cells"], "months": m["months"], "gross_sharpe": m["gross_sharpe"], "net_sharpe": m["net_sharpe"],
                     "after_tax_sharpe": m["after_tax_sharpe"], "cost_drag_bps": m["cost_drag_bps"], "tax_drag_bps": m["tax_drag_bps"], "turnover": m["turnover"]})
    raw = pd.DataFrame(rows)
    fmt = pd.DataFrame({"Market": raw["country"], "Cells": raw["cells"].astype(str), "Months": raw["months"].astype(str), "Gross Sharpe": raw["gross_sharpe"].map(fnum),
                        "Net Sharpe": raw["net_sharpe"].map(fnum), "After-tax Sharpe": raw["after_tax_sharpe"].map(fnum), "Cost drag (bp/yr)": raw["cost_drag_bps"].map(lambda x: fnum(x, 2)),
                        "Tax drag (bp/yr)": raw["tax_drag_bps"].map(lambda x: fnum(x, 2)), "Turnover (mean monthly)": raw["turnover"].map(lambda x: fnum(x, 4))})
    notes = ("Optimised book at $1bn, stage-06 summaries, means over the 8 prediction cells. Net Sharpe and cost drag are from the zero-tax regime rows; after-tax Sharpe and tax drag from the "
             "statutory-regime rows. Germany's and India's summaries are verbatim snapshots of earlier untracked outputs (the German one from an older script version with 24 columns); the "
             "weight identity was recovered from the weights index. Turnover is endogenous, so the ordering of tax drag by turnover is descriptive and does not separate rate from wedge. "
             "No inference is attached.")
    return raw, fmt, "Table S1. Cost, tax and turnover accounting on the optimised book at $1bn", notes, ["sum_deu_1e9", "sum_ind_1e9", "sum_jpn_1e9"]


def table_capacity_full() -> tuple:
    frames = b_frames()
    rows = []
    for c in COUNTRIES:
        d = frames[c]
        t = tierb_full(c).set_index("aum")
        for _, r in d.iterrows():
            row = {"country": NAMES[c], "aum": r["aum"], "status": r["status"]}
            if r["status"] == "solvent":
                tr = t.loc[r["aum"]]
                row.update({"B_points_nav_per_year": tr["B"] * 100, "ci95_low": tr["B_ci_low"] * 100, "ci95_high": tr["B_ci_high"] * 100,
                            "p_holm": tr["p_holm"], "uncapped_terminal_wealth": tr["uncapped_terminal_wealth"], "near_ruined": bool(r["near_ruined"])})
            else:
                row.update({"B_points_nav_per_year": np.nan, "ci95_low": np.nan, "ci95_high": np.nan, "p_holm": np.nan,
                            "uncapped_terminal_wealth": np.nan, "near_ruined": np.nan})
            rows.append(row)
    raw = pd.DataFrame(rows)

    def wealth(x):
        return "n/a" if np.isnan(x) else (f"{x:.3g}" if x >= 1e-3 else f"{x:.1e}")
    fmt = pd.DataFrame({"Market": raw["country"], "AUM": raw["aum"].map(aum_label), "Status": raw["status"].map({"solvent": "solvent", "insolvent": "comparator insolvent: no B(A)"}),
                        "B(A)": raw["B_points_nav_per_year"].map(lambda x: fnum(x, 2, True)),
                        "95% interval": [("n/a" if np.isnan(a) else f"[{a:+.2f}, {b:+.2f}]") for a, b in zip(raw["ci95_low"], raw["ci95_high"])],
                        "Holm p": raw["p_holm"].map(lambda x: "n/a" if np.isnan(x) else ("<0.0001" if x < 5e-5 else f"{x:.4f}")), "Uncapped terminal wealth": raw["uncapped_terminal_wealth"].map(wealth),
                        "Near-ruined": raw["near_ruined"].map(lambda x: "n/a" if pd.isna(x) else ("yes" if x else "no"))})
    notes = ("B(A) is the annualised mean net-return difference between the capped and uncapped decile composites (equal-weighted over 8 independently simulated full-AUM variants), in points of NAV "
             "per year, Tier B pipeline accounting. It is an accounting difference against an infeasible comparator and is not an investable performance gain; it is not convertible to Sharpe points. "
             "A rung is solvent only if no cell-month of either book is at or below -100% net return; insolvent rungs have no B(A) and are listed, not dropped. Intervals are unadjusted studentised "
             "stationary-bootstrap intervals; Holm p is adjusted within country across valid rungs. Near-ruined: uncapped terminal wealth below the display flag, not an exclusion rule.")
    return raw, fmt, "Table S2. Capacity accounting B(A) at every rung, with insolvent rungs shown", notes, ["tierB_DEU", "tierB_IND", "tierB_JPN", "tierA_DEU", "tierA_IND", "tierA_JPN"]


def table_design() -> tuple:
    g = pd.read_csv(src("gate2"))
    raw = g.copy()
    raw["mde_80pct_power"] = MDE_Z * raw["se"]
    raw["abs_effect_below_mde"] = raw["effect"].abs() < raw["mde_80pct_power"]
    fmt = pd.DataFrame({"Market": raw["country"].map(NAMES), "Axis": raw["axis"], "Effect (Sharpe pts)": raw["effect"].map(lambda x: fnum(x, 3, True)),
                        "SE": raw["se"].map(fnum), "t": raw["t"].map(lambda x: fnum(x, 2, True)), "MDE (80% power)": raw["mde_80pct_power"].map(fnum),
                        "Months": raw["months"].astype(int).astype(str)})
    over = raw[raw["t"].abs() > 1.96]
    which = "; ".join(f"{NAMES[r.country]} {r.axis}" for r in over.itertuples())
    notes = (f"Optimised book at $1bn: paired effect of each design axis with its standard error from the source. MDE = {MDE_Z:.4f} x SE (5% two-sided, 80% power, the multiplier used in "
             f"tools/gate2_power.py). The t-statistics are unadjusted. {len(over)} of {len(raw)} contrasts have |t| above 1.96 ({which}); it was not specified in advance and is disclosed but "
             "not claimed (Japan's conditioning contrast is exploratory). A null here excludes only effects of roughly the MDE or larger.")
    return raw, fmt, "Table S3. Design-axis contrasts at $1bn and their minimum detectable effects", notes, ["gate2"]


def table_estimability() -> tuple:
    d = pd.read_csv(src("tier_counts"))
    short = {"tier_gross_valuation": "gross (valuation)", "tier_net_valuation_or_cost": "net (valuation or cost)",
             "tier_after_tax_valuation_cost_or_tax": "after-tax (valuation, cost or tax)"}
    tiers = ["0%", "<=5%", "<=25%", ">25%"]
    rows = []
    for c in COUNTRIES:
        for m in ("tier_gross_valuation", "tier_net_valuation_or_cost", "tier_after_tax_valuation_cost_or_tax"):
            sub = d[(d["country"] == c) & (d["metric"] == m)].set_index("tier")["n_series"]
            row = {"country": NAMES[c], "metric": short[m], "series": int(sub.sum())}
            for t in tiers:
                row[t] = int(sub.get(t, 0))
            rows.append(row)
    raw = pd.DataFrame(rows)
    fmt = pd.DataFrame({"Market": raw["country"], "Metric": raw["metric"], "Weight series": raw["series"].astype(str), **{f"Tier {t}": raw[t].astype(str) for t in tiers}})
    all_top = bool((raw[">25%"] == raw["series"]).all())
    per_country = raw.groupby("country", sort=False)["series"].first()
    total = int(per_country.sum())
    notes = (f"Outcome-free support census (version 3). A series is one saved weight series (mandate rung x book x factorial cell), {total} in all across the three markets. Each is assigned to an "
             "estimability tier by the share of months lacking a usable input; the thresholds are 0% / at most 5% / at most 25% / above 25%. "
             + ("Every series under every metric sits in the highest tier, so none is estimable under the census rule. " if all_top else "Tier counts are as listed. ")
             + "This table describes input support only: it is not a result and it does not show that the revised (carry-forward) analysis, Phase C, was run. That analysis is blocked.")
    return raw, fmt, "Table S4. Input-support (estimability) census of the series required by the revised analysis", notes, ["tier_counts"]


def design_sig_counts() -> dict:
    """Capped-book axis-rungs significant after Holm adjustment, from the two committed design tables."""
    out = {}
    for c, k in (("DEU", "design_deu"), ("IND", "design_ind")):
        d = pd.read_csv(src(k))
        d = d[d["book"] == "capped"]
        out[c] = (int((d["p_holm"] < 0.05).sum()), len(d))
    return out


def table_register() -> tuple:
    sig = design_sig_counts()
    rows = [
        ("Germany: optimised-book after-tax inference statistic", "excluded", "No committed artifact holds it and it was not regenerated; the German values shown elsewhere are descriptive stage-06 means without inference."),
        ("Phase C (revised exit treatment, carry-forward)", "blocked, not run", "Needs vendor documentation and a month-level flag query, written authorisation and a dated addendum; Table S4 counts input support only."),
        ("Exit-treatment sensitivity of every as-run number", "unknown", "All results use the as_run treatment; the size of the effect of a different treatment has not been measured."),
        ("Amendment 001C Japan predictions P1, P3, P4, P5", "not scoreable", "Definitions incomplete or diagnostics never committed; nothing was substituted."),
        ("Amendment 001C Japan prediction P2 (net Sharpe above Germany's at $1bn)", "not met", "Descriptive comparison against the amendment's fixed threshold; no test attached; Japan is not presented as a confirmation."),
        ("Economic-loss arm (8 of 16 cells)", "excluded after the fact", "The restriction to the 8 prediction cells was made after the arm's behaviour was observed; it is a post hoc deviation."),
        ("Capacity Sharpe-point gains", "withdrawn", "B(A) is an accounting difference against an infeasible comparator and is not convertible to Sharpe points."),
        ("Design-axis effects", "not detectable at this power", f"Capped book, Holm-adjusted: {sig['DEU'][0]} of {sig['DEU'][1]} axis-rungs significant in Germany and {sig['IND'][0]} of {sig['IND'][1]} in India; Table S3 gives the minimum detectable effects."),
    ]
    raw = pd.DataFrame(rows, columns=["item", "status", "basis"])
    fmt = raw.rename(columns={"item": "Item", "status": "Status", "basis": "Basis"})
    notes = "Register of results that are withheld, withdrawn, excluded or unresolved, so that their absence from the figures and tables is visible. Statuses restate the project's documents; no value is computed here."
    return raw, fmt, "Table S5. What is not reported, and why", notes, []


# ----------------------------------------------------------------------------------------------------------------
# registry and driver
# ----------------------------------------------------------------------------------------------------------------
FIGS = [
    ("FIG_M1_pipeline", fig_pipeline, "main_text", "MAIN_TEXT_ELIGIBLE", [],
     "Research design and as-run analysis pipeline. Certified panels from a separate data workstream feed the 2x2x2x2 model factorial, three portfolio books and a lot-level backtest under a zero-tax control and a statutory regime; "
     "committed snapshots are the only inputs to the tables and figures. Schematic: no data are plotted. The unrun and unknown items in the lower right are part of the design record."),
    ("FIG_M2_cost_input_coverage", fig_coverage, "main_text", "MAIN_TEXT_ELIGIBLE", ["coverage"],
     "Share of in-universe security-months with certified cost inputs, by month, 2009-01 to 2019-12. Germany's investable universe is smaller than its signal-bearing one because uncertified security-months are non-tradeable and not imputed. "
     "This describes input support; it is not a performance result."),
    ("FIG_M3_sharpe_ladder_channels", fig_ladder, "main_text", "MAIN_TEXT_ELIGIBLE", ["matched_1e9"],
     "Capped decile composite at $1bn. (a) Gross, net and after-tax annualised Sharpe ratios by market. (b) Cost channel (net minus gross) and tax channel (after-tax minus net) in Sharpe points. Comparisons use matched books and identical definitions in "
     "all three markets. No interval is drawn because the source holds none; no net Sharpe is significantly positive. The non-executable uncapped Japanese comparator is not plotted."),
    ("FIG_M4_capacity_B_tierB", fig_capacity_B, "main_text", "MAIN_TEXT_ELIGIBLE", ["tierB_DEU", "tierB_IND", "tierB_JPN", "tierA_DEU", "tierA_IND", "tierA_JPN"],
     "B(A), the annualised mean net-return difference between capped and uncapped decile composites (Tier B), by mandate size, solvent rungs only, with unadjusted 95% bootstrap intervals. B(A) is an accounting difference against an infeasible, "
     "often near-ruined comparator; it is not realised performance, not investable, and not convertible to Sharpe points. Insolvent rungs are shaded and carry no B(A)."),
    ("FIG_S1_uncapped_terminal_wealth", fig_wealth, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["tierB_DEU", "tierB_IND", "tierB_JPN", "tierA_DEU", "tierA_IND", "tierA_JPN"],
     "Compounded terminal wealth of the uncapped comparator at solvent rungs. Where wealth is far below one the comparator is near-ruined, which is why B(A) at those rungs measures an accounting gap against an infeasible plan."),
    ("FIG_S2_B_components", fig_B_components, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["tierB_DEU", "tierB_IND", "tierB_JPN"],
     "Decomposition of B(A) into gross return forgone by capping and cost saved by capping, Tier B, solvent rungs. The cost the uncapped comparator would pay dominates at large mandates."),
    ("FIG_S3_net_sharpe_cost_drag_by_aum", fig_rungs, "supplementary", "SUPPLEMENTARY_ELIGIBLE", ["sum_deu_1e8", "sum_deu_1e9", "sum_deu_1e10", "sum_ind_1e9", "sum_jpn_1e8", "sum_jpn_1e9", "sum_jpn_1e10"],
     "Net Sharpe and cost drag of the optimised book at $100mn, $1bn and $10bn (zero-tax regime, means over 8 prediction cells). Japan's net Sharpe is not monotone in AUM while its cost drag falls. India has one rung. "
     "Descriptive; this is not presented as confirming any prediction (amendment 001C: P2 not met, four predictions not scoreable)."),
    ("FIG_S4_design_axes_gate2", fig_design_axes, "supplementary", "DIAGNOSTIC_ONLY", ["gate2"],
     "Design-axis contrasts on the optimised book at $1bn: unadjusted t-statistics and observed size against the minimum detectable effect. The contrasts are mostly small relative to what the design could detect. Japan's conditioning contrast is exploratory "
     "and not claimed. Diagnostic only; not for the main text."),
]
TABLES = [
    ("TAB_M1_markets_coverage", table_market, "main_text", "MAIN_TEXT_ELIGIBLE", "tab:markets"),
    ("TAB_M2_matched_book_outcomes", table_outcomes, "main_text", "MAIN_TEXT_ELIGIBLE", "tab:outcomes"),
    ("TAB_M3_tax_regimes", table_statutes, "main_text", "MAIN_TEXT_ELIGIBLE", "tab:tax"),
    ("TAB_S1_cost_tax_turnover", table_cost_accounting, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s1"),
    ("TAB_S2_capacity_all_rungs", table_capacity_full, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s2"),
    ("TAB_S3_design_axes_mde", table_design, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s3"),
    ("TAB_S4_estimability_census", table_estimability, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s4"),
    ("TAB_S5_not_reported_register", table_register, "supplementary", "SUPPLEMENTARY_ELIGIBLE", "tab:s5"),
]
TABLE_SOURCES = {fn.__name__: None for _, fn, *_ in TABLES}

# Scientific review of each asset (question answered; comparability; uncertainty; placement). Written after inspecting the rendered files.
REVIEW = {
    "FIG_M1_pipeline": "Answers: what was run and what was not. No values, so nothing to trace. Placement: main text as a design record; it must not be read as a result.",
    "FIG_M2_cost_input_coverage": "Answers: how much of the universe is tradeable on certified inputs. Definition identical across markets (certified over in-universe, per month). No uncertainty needed: a count ratio. The one-month India collapse is annotated from the data, not smoothed. Placement: main text.",
    "FIG_M3_sharpe_ladder_channels": "Answers: where gross predictability goes under costs and tax. Same book (capped decile composite), same AUM, same definitions in all three markets. No interval is drawn because none is in the source; the figure does not claim significance. The executable and the non-executable books are not mixed. Placement: main text.",
    "FIG_M4_capacity_B_tierB": "Answers: how the capped-minus-uncapped accounting difference grows with mandate size. Intervals are the source's unadjusted bootstrap intervals; insolvent rungs are shaded and unplotted; near-ruined comparators are hollow. Caption states B(A) is not investable performance. Placement: main text (already Figure 1 of the candidate, restyled), as an accounting illustration.",
    "FIG_S1_uncapped_terminal_wealth": "Answers: how infeasible the uncapped comparator is. Values are source terminal-wealth columns; floor-clipped points are marked. Placement: supplement.",
    "FIG_S2_B_components": "Answers: what B(A) is made of (cost saved versus gross forgone), to prevent reading it as alpha. Placement: supplement.",
    "FIG_S3_net_sharpe_cost_drag_by_aum": "Answers: how net Sharpe and cost drag move across the three AUM rungs that exist. Germany and Japan only for a line; India is a single point. Descriptive point estimates; German snapshots come from an older script version; not a confirmation of any prediction. Placement: supplement.",
    "FIG_S4_design_axes_gate2": "Answers: whether the design could have detected the contrasts it observed. Unadjusted t-statistics and MDE from the source; the single |t| above 1.96 is exploratory. Placement: supplement, diagnostic only; not eligible for the main text.",
    "TAB_M1_markets_coverage": "Same definitions in all markets; counts and ratios only. Placement: main text.",
    "TAB_M2_matched_book_outcomes": "Same books, AUM and accounting in all markets; the uncapped comparator is labelled. Inference columns come from the source and are unadjusted. Germany's optimised-book inference is absent by design. Placement: main text.",
    "TAB_M3_tax_regimes": "States the statute inputs as configured and as run, with no legal claim. Placement: main text.",
    "TAB_S1_cost_tax_turnover": "Optimised-book cost, tax and turnover means; provenance caveats for the German and Indian snapshots are in the notes. Placement: supplement.",
    "TAB_S2_capacity_all_rungs": "Every rung is listed, including insolvent ones, so exclusions are visible. Placement: supplement.",
    "TAB_S3_design_axes_mde": "Observed contrasts and detectability; unadjusted. Placement: supplement.",
    "TAB_S4_estimability_census": "Input-support counts only; no outcome is shown and Phase C is not implied to have run. Placement: supplement.",
    "TAB_S5_not_reported_register": "Makes withheld, withdrawn and unresolved items visible. Statuses restate project documents; no value is computed except the two Holm counts. Placement: supplement.",
}

NOT_BUILT = [
    ("Germany after-tax inference figure or table", "NOT_SUPPORTED_BY_AVAILABLE_ARTIFACTS", "No committed artifact holds the statistic and regeneration is not authorised."),
    ("Any Phase C or revised-exit-treatment result, or a chart implying the 560 series were resolved", "NOT_SUPPORTED_BY_AVAILABLE_ARTIFACTS", "Phase C is blocked and unrun; Table S4 shows only input-support counts."),
    ("India net Sharpe or cost drag across AUM rungs", "NOT_SUPPORTED_BY_AVAILABLE_ARTIFACTS", "Only the $1bn India summary is committed; a line would require interpolation."),
    ("Japan optimised-book realised gross, cap share, weight correlations, $100mn axis contrasts (001C P1, P3, P4, P5)", "NOT_SUPPORTED_BY_AVAILABLE_ARTIFACTS", "The diagnostics were never committed; scoring them needs a separate authorisation."),
    ("Long-term share of gains by statute (figure)", "EXCLUDED_WITH_REASON", "Zero under flat statutes by construction; fully carried by Table 3, a plot would add nothing."),
    ("001C scorecard chart", "EXCLUDED_WITH_REASON", "One of five predictions is scoreable; a chart would imply more evidence than exists. Rows are in Table S5 and the scorecard document."),
    ("Liquidity-tercile, theme and wedge-tool panels in docs/attachments", "EXCLUDED_WITH_REASON", "Not in the candidate's traceability set, several are non-compliant ladders or older versions; not approved for result plots."),
    ("Sharpe-point conversion of B(A)", "EXCLUDED_WITH_REASON", "Withdrawn: B(A) is an accounting difference against an infeasible comparator."),
    ("Second restyled copy of any figure", "EXCLUDED_WITH_REASON", "Duplicated evidence is not added to raise the figure count."),
]


def build(out: Path) -> list[dict]:
    set_style()
    hashes = verify_sources()
    out = Path(out)
    records = []
    for aid, fn, sect, status, srcs, cap in FIGS:
        fig = fn()
        base = out / "figures" / sect / aid
        save_fig(fig, base)
        records.append({"id": aid, "kind": "figure", "section": sect, "status": status, "sources": srcs, "script": fn.__name__, "caption": cap,
                        "files": [f"figures/{sect}/{aid}.{e}" for e in ("pdf", "svg", "png")]})
    for aid, fn, sect, status, label in TABLES:
        raw, fmt, title, notes, srcs = fn()
        base = out / "tables" / sect / aid
        write_table(base, raw, fmt, title, notes, label)
        records.append({"id": aid, "kind": "table", "section": sect, "status": status, "sources": srcs, "script": fn.__name__, "caption": title + ". " + notes,
                        "files": [f"tables/{sect}/{aid}.{e}" for e in ("csv", "tex", "md")]})
    write_catalog(out, records, hashes)
    return records


def write_catalog(out: Path, records: list[dict], hashes: dict[str, str]):
    me = sha256(Path(__file__))
    lines = ["# Asset catalog: `paper_assets_as_run_only/`", "",
             "Generated by `tools/make_paper_assets.py` (do not edit by hand; rerun the script). Every value is a deterministic transformation of committed artifacts; nothing was trained, optimised or newly estimated. "
             "This folder holds outputs only. The figures and tables are presentation of existing as-run evidence under the `as_run` exit-treatment (sensitivity unknown); Phase C is blocked and unrun; Germany's after-tax inference statistic is excluded; "
             "Japan is not presented as a confirmation (amendment 001C: P2 not met, P1/P3/P4/P5 not scoreable); the paper claims no new method. A figure or table is not evidence of statistical validity or novelty.", "",
             f"Script SHA-256: `{me}`. Environment: Python {platform.python_version()}, pandas {pd.__version__}, numpy {np.__version__}, matplotlib {__import__('matplotlib').__version__}.", "",
             "Formats: figures as vector PDF and SVG plus 300-dpi PNG for review; tables as CSV (full precision), LaTeX (booktabs; add `\\usepackage{booktabs}`) and Markdown. Colours are the Okabe-Ito palette. "
             "Widths are 7.0 in (full page) and fonts 6-9 pt at that width. None of the source files is copied here.", "",
             "## Index", "", "| ID | Kind | Section | Status | Files |", "|---|---|---|---|---|"]
    for r in records:
        lines.append(f"| {r['id']} | {r['kind']} | {r['section']} | `{r['status']}` | " + ", ".join(f"`{f}`" for f in r["files"]) + " |")
    lines += ["", "## Per-asset record", ""]
    for r in records:
        lines += [f"### {r['id']}", "", f"* Status: `{r['status']}`; placement: {r['section']}.", f"* Builder: `{r['script']}` in `tools/make_paper_assets.py`.",
                  f"* Caption: {r['caption']}", f"* Review: {REVIEW[r['id']]}", "* Sources (path, SHA-256):"]
        if r["sources"]:
            for k in r["sources"]:
                lines.append(f"  * `{SOURCES[k]}` `{hashes[k]}`")
        else:
            lines.append("  * none (schematic or register; no numerical source)")
        lines.append("")
    lines += ["## Candidates not built", "", "| Candidate | Status | Reason |", "|---|---|---|"]
    lines += [f"| {a} | `{b}` | {c} |" for a, b, c in NOT_BUILT]
    lines += ["", "## Output hashes", "", "See `ASSET_MANIFEST.csv` (SHA-256 of every generated file, used by the determinism test).", ""]
    (out / "ASSET_CATALOG.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
    rows = []
    for r in records:
        for f in r["files"]:
            rows.append((f, sha256(out / f)))
    rows.append(("ASSET_CATALOG.md", sha256(out / "ASSET_CATALOG.md")))
    with open(out / "ASSET_MANIFEST.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["file", "sha256"])
        w.writerows(sorted(rows))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a = ap.parse_args()
    recs = build(a.out)
    print(f"wrote {sum(r['kind'] == 'figure' for r in recs)} figures and {sum(r['kind'] == 'table' for r in recs)} tables to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
