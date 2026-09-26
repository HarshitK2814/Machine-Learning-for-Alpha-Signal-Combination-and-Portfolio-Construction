# -*- coding: utf-8 -*-
"""Figures for the after-tax evaluation layer and the adaptive combination.

Same conventions as figures.py: validated categorical slots, recessive chrome, thin marks, no
invented data. Every plotted value is read from a file the pipeline actually wrote
(``alphacomb/outputs/summary_after_tax.csv``, ``summary_adaptive.csv``, ``adaptive_weights.csv``)
or from a published table quoted with its source. Nothing here is illustrative.

If a required output file is missing, the corresponding figure is SKIPPED rather than drawn from
placeholder numbers. A missing figure is a visible gap; a fabricated one is a false result.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGS
from figures import AXIS, GRID, INK, INK2, MUTED, SEQ, SLOTS, SURFACE, _grid, _save

# The research folder now lives inside the alphacomb repository (research/), so the repo root is
# two levels up from _build/ rather than a sibling directory three levels up. Resolved by walking
# up until a directory containing src/alphacomb is found, so neither layout breaks it again.
def _repo_root(start: str) -> str:
    d = os.path.dirname(os.path.abspath(start))
    for _ in range(6):
        if os.path.isdir(os.path.join(d, "src", "alphacomb")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    raise RuntimeError("could not locate the alphacomb repository root from " + start)


REPO = _repo_root(__file__)
OUTPUTS = os.path.join(REPO, "outputs")

REGIME_LABEL = {
    "tax_exempt": "Tax-exempt\n(pension, endowment)",
    "taxable_us_top_bracket": "Taxable US\ntop bracket",
    "trader_475f_mtm": "Trader, s475(f)\nmark-to-market",
    "offshore_fund": "Offshore fund\n(dividend withholding)",
}
REGIME_ORDER = ["tax_exempt", "offshore_fund", "taxable_us_top_bracket", "trader_475f_mtm"]
LOT_LABEL = {"hifo": "HIFO", "fifo": "FIFO", "lifo": "LIFO", "tax_optimal": "Tax-optimal"}


def _load(name: str) -> pd.DataFrame | None:
    path = os.path.join(OUTPUTS, name)
    if not os.path.exists(path):
        print(f"  SKIP: {name} not found - run the pipeline that writes it")
        return None
    frame = pd.read_csv(path)
    return frame if len(frame) else None


def _provenance(ax, text: str, y: float = -0.19, width: int = 132) -> None:
    """Every figure states where its numbers came from, on the figure itself.

    The text is wrapped. An unwrapped long caption combined with ``bbox_inches="tight"`` widens the
    saved canvas to fit the caption and squashes the plot to a sliver - which is exactly what
    happened to this figure before the wrap was added.
    """
    import textwrap

    ax.text(0, y, textwrap.fill(text, width=width),
            transform=ax.transAxes, fontsize=6.2, color=MUTED, va="top", linespacing=1.5)


# ----------------------------------------------------------------------- after-tax

def fig_tax_waterfall():
    """Gross -> net of cost -> after tax, for one strategy, one bar per regime.

    This is the headline: the distance between the tax-exempt bar (what the literature reports)
    and the taxable bar (what the investor keeps).
    """
    df = _load("summary_after_tax.csv")
    if df is None:
        return None
    df = df[df["lot_method"] == "hifo"]
    strategy = sorted(df["strategy"].unique())[0]
    d = df[df["strategy"] == strategy].set_index("regime")
    regimes = [r for r in REGIME_ORDER if r in d.index]
    if not regimes:
        return None

    gross = d.loc[regimes, "gross_mean_ann"].to_numpy() * 100
    net = d.loc[regimes, "net_mean_ann"].to_numpy() * 100
    after = d.loc[regimes, "after_tax_mean_ann"].to_numpy() * 100

    fig, ax = plt.subplots(figsize=(7.6, 3.8), constrained_layout=True)
    x = np.arange(len(regimes))
    # Ordinal ramp 300/450/700, not 100/300/600: the validator rejected the lighter ramp because
    # its light end sat at 1.29:1 against the surface, below the 2:1 floor - the "gross" band was
    # effectively invisible. This ramp passes monotonicity, step gaps, single hue and light-end
    # contrast (scripts/validate_palette.js --ordinal).
    ax.bar(x, gross, width=0.62, color=SEQ["300"], label="Gross return")
    ax.bar(x, net, width=0.62, color=SEQ["450"], label="Net of trading cost")
    ax.bar(x, after, width=0.62, color=SEQ["700"], label="After tax")
    top = float(gross.max())
    ax.set_ylim(0, top * 1.30)                      # headroom so the drag labels are not clipped
    for k in range(len(regimes)):
        ax.text(x[k], after[k] + top * 0.015, f"{after[k]:.2f}%", ha="center", fontsize=7.6,
                color="#ffffff" if after[k] > top * 0.25 else INK, va="top" if after[k] > top * 0.25 else "bottom")
        if net[k] - after[k] > top * 0.05:          # only label the middle band when it is visible
            # sits on the mid ramp step, so it needs primary ink rather than secondary
            ax.text(x[k], net[k] + top * 0.015, f"{net[k]:.2f}%", ha="center", fontsize=6.8, color=INK)
        ax.text(x[k], gross[k] + top * 0.045, f"-{gross[k] - after[k]:.2f} pts", ha="center",
                fontsize=7.0, color=MUTED)
    ax.set_xticks(x)
    ax.set_xticklabels([REGIME_LABEL.get(r, r) for r in regimes], fontsize=7.2)
    ax.set_ylabel("Annualised return (%)")
    ax.set_title(f"What the investor keeps: {strategy}", fontsize=9.5, loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, fontsize=7.4)
    _grid(ax)
    _provenance(ax, f"Source: alphacomb/outputs/summary_after_tax.csv, HIFO lots, {int(d.loc[regimes[0], 'months'])} months, "
                    "synthetic panel. Rehearsal, not a result.", y=-0.34)
    return _save(fig, "fig_tax_waterfall.png")


def fig_tax_drag_decomposition():
    """Cost drag vs tax drag, in basis points, across strategies under the taxable regime.

    The point of the figure: tax is the same order of magnitude as trading cost, and the literature
    reports only the left-hand bar.
    """
    df = _load("summary_after_tax.csv")
    if df is None:
        return None
    d = df[(df["regime"] == "taxable_us_top_bracket") & (df["lot_method"] == "hifo")]
    if d.empty:
        return None
    d = d.sort_values("total_drag_ann_bps", ascending=True)
    names = [s.replace("cell_", "") for s in d["strategy"]]
    y = np.arange(len(d))

    fig, ax = plt.subplots(figsize=(7.4, max(2.8, 0.44 * len(d) + 1.9)), constrained_layout=True)
    ax.barh(y, d["cost_drag_ann_bps"], height=0.6, color=SEQ["300"], label="Trading cost drag")
    ax.barh(y, d["tax_drag_ann_bps"], height=0.6, left=d["cost_drag_ann_bps"],
            color=SLOTS[1], label="Tax drag")
    for k, (c, t) in enumerate(zip(d["cost_drag_ann_bps"], d["tax_drag_ann_bps"])):
        ax.text(c + t + 4, k, f"{c:.0f} + {t:.0f} = {c + t:.0f} bps", va="center", fontsize=7, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7.6)
    ax.set_xlabel("Annual drag on gross return (basis points)")
    ax.set_title("Trading cost is reported in the literature. Tax is not.", fontsize=9.5, loc="left")
    # two series only: the top-right of the plot area is empty, so the legend goes inside
    ax.legend(loc="lower right", fontsize=7.4)
    ax.set_xlim(0, float((d["cost_drag_ann_bps"] + d["tax_drag_ann_bps"]).max()) * 1.40)
    _grid(ax, axis="x")
    _provenance(ax, "Source: alphacomb/outputs/summary_after_tax.csv, taxable US top bracket, HIFO lots, synthetic panel.",
                y=-0.13 if len(d) > 4 else -0.30)
    return _save(fig, "fig_tax_drag_decomposition.png")


def fig_lot_method_matters():
    """After-tax Sharpe by lot-selection method: an accounting choice, not a modelling one.

    Pre-tax P&L is identical across these bars by construction (a test pins it), so the whole spread
    is the accounting rule.
    """
    df = _load("summary_after_tax.csv")
    if df is None:
        return None
    d = df[df["regime"] == "taxable_us_top_bracket"]
    if d.empty or d["lot_method"].nunique() < 2:
        print("  SKIP: fig_lot_method_matters needs >= 2 lot methods")
        return None
    pivot = d.pivot_table(index="strategy", columns="lot_method", values="after_tax_sharpe")
    methods = [m for m in ["fifo", "lifo", "hifo", "tax_optimal"] if m in pivot.columns]
    strategies = list(pivot.index)

    fig, ax = plt.subplots(figsize=(7.4, 3.4), constrained_layout=True)
    x = np.arange(len(strategies))
    width = 0.8 / len(methods)
    for k, m in enumerate(methods):
        offset = (k - (len(methods) - 1) / 2) * width
        ax.bar(x + offset, pivot[m], width=width * 0.92, color=SLOTS[k % len(SLOTS)],
               label=LOT_LABEL.get(m, m))
    net = d.groupby("strategy")["net_sharpe"].first().reindex(strategies)
    ax.plot(x, net, linestyle="none", marker="_", markersize=30, color=INK,
            markeredgewidth=1.6, label="Net of cost, before tax")
    for k, v in enumerate(net):
        ax.text(x[k], v + 0.025, f"{v:.2f}", ha="center", fontsize=7.0, color=INK)
    ax.set_ylim(0, max(float(net.max()), float(pivot[methods].to_numpy().max())) * 1.22)
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace("cell_", "") for s in strategies], fontsize=7.6)
    ax.set_ylabel("Sharpe ratio")
    ax.set_title("Lot selection moves after-tax Sharpe without touching pre-tax P&L",
                 fontsize=9.5, loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=len(methods) + 1, fontsize=7.2)
    _grid(ax)
    _provenance(ax, "Source: alphacomb/outputs/summary_after_tax.csv, taxable US top bracket. Gross return is identical "
                    "across lot methods by construction (tests/tax/test_backtest.py).", y=-0.30)
    return _save(fig, "fig_lot_method_matters.png")


def fig_wash_sale_bite():
    """How much of the harvested loss s1091 disallows, against the tax actually paid."""
    df = _load("summary_after_tax.csv")
    if df is None:
        return None
    d = df[(df["regime"] == "taxable_us_top_bracket") & (df["lot_method"] == "hifo")]
    if d.empty:
        return None
    names = [s.replace("cell_", "") for s in d["strategy"]]
    x = np.arange(len(d))

    fig, ax = plt.subplots(figsize=(7.2, 3.2), constrained_layout=True)
    ax.bar(x - 0.19, d["wash_disallowed_ann_bps"], width=0.36, color=SLOTS[1],
           label="Loss disallowed by s1091 (bps/yr)")
    ax.bar(x + 0.19, d["tax_drag_ann_bps"], width=0.36, color=SEQ["600"],
           label="Tax actually paid (bps/yr)")
    top = float(d["wash_disallowed_ann_bps"].max())
    ax.set_ylim(0, top * 1.16)
    for k, (w, t) in enumerate(zip(d["wash_disallowed_ann_bps"], d["tax_drag_ann_bps"])):
        ax.text(x[k] - 0.19, w + top * 0.02, f"{w:.0f}", ha="center", fontsize=7.2, color=INK)
        ax.text(x[k] + 0.19, t + top * 0.02, f"{t:.0f}", ha="center", fontsize=7.2, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=7.6)
    ax.set_ylabel("Basis points per year")
    ax.set_title("The wash-sale rule disallows more than the strategy pays in tax",
                 fontsize=9.5, loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, fontsize=7.4)
    _grid(ax)
    _provenance(ax, "Source: alphacomb/outputs/summary_after_tax.csv. Month-end wash-sale window (conservative reading): "
                    "a sale followed by a next-month repurchase counts as a wash.", y=-0.28)
    return _save(fig, "fig_wash_sale_bite.png")


# ----------------------------------------------------------------------- adaptive

def fig_adaptive_weights():
    """Combination weight on each member over time, with drift events marked."""
    frame = _load("adaptive_weights.csv")
    if frame is None:
        return None
    frame["date"] = pd.to_datetime(frame["date"])
    members = [c for c in frame.columns if c not in {"date", "n_updates", "n_effective"}
               and not c.startswith("w_")]
    if not members:
        members = [c[2:] for c in frame.columns if c.startswith("w_")]
        for m in members:
            frame[m] = frame[f"w_{m}"]
    if len(members) < 2:
        return None

    fig, ax = plt.subplots(figsize=(7.8, 3.3), constrained_layout=True)
    ax.stackplot(frame["date"], [frame[m] for m in members],
                 labels=[m.replace("cell_", "") for m in members],
                 colors=SLOTS[:len(members)], edgecolor=SURFACE, linewidth=0.4)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Weight on member")
    ax.set_title("The combination re-weights itself on realised after-tax return",
                 fontsize=9.5, loc="left")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=min(len(members), 4), fontsize=7.2)
    _grid(ax)
    _provenance(ax, "Source: alphacomb/outputs/adaptive_weights.csv. Weights in force at month t are produced by "
                    "updates on months up to t-1 (alphacomb.adaptive.assert_causal).", y=-0.30)
    return _save(fig, "fig_adaptive_weights.png")


def fig_adaptive_vs_benchmarks():
    """The honest comparison: adaptive against the blend and the best member in hindsight."""
    frame = _load("summary_adaptive.csv")
    if frame is None:
        return None
    order = {"member": 0, "benchmark": 1, "adaptive": 2, "not_implementable": 3,
             "not_like_for_like": 4}
    frame = frame.sort_values(["kind", "after_tax_sharpe"], key=lambda c: c.map(order) if c.name == "kind" else c)
    # Validated set: SEQ200 failed the lightness band and the chroma floor, and SLOTS[2] green
    # collided with the blue under tritanopia (deltaE 4.7). #6da7ec / #eb6834 / #184f95 passes.
    # The infeasible oracle stays deliberately recessive grey - it is chrome, not a series, so it
    # is hatched as well as greyed and is excluded from the categorical check.
    colour = {"member": SEQ["300"], "benchmark": SLOTS[1], "adaptive": SEQ["600"],
              "not_implementable": MUTED, "not_like_for_like": MUTED}
    y = np.arange(len(frame))

    fig, ax = plt.subplots(figsize=(7.8, max(3.4, 0.46 * len(frame) + 2.3)), constrained_layout=True)
    ax.barh(y, frame["after_tax_sharpe"], height=0.62,
            color=[colour.get(k, MUTED) for k in frame["kind"]],
            hatch=["//" if k in {"not_implementable", "not_like_for_like"} else ""
                   for k in frame["kind"]],
            edgecolor=SURFACE, linewidth=0.8)
    for k, v in enumerate(frame["after_tax_sharpe"]):
        ax.text(v + 0.012, k, f"{v:.3f}", va="center", fontsize=7.2, color=INK2)
    ax.set_yticks(y)
    ax.set_yticklabels([s.replace("cell_", "") for s in frame["strategy"]], fontsize=7.4)
    ax.set_xlabel("After-tax Sharpe ratio")
    ax.set_title("Adaptation versus fixing the weights at 1/N", fontsize=9.5, loc="left")
    kinds = ["member", "benchmark", "adaptive", "not_implementable", "not_like_for_like"]
    names = {"member": "Single member",
             "benchmark": "Fixed 1/N alpha blend",
             "adaptive": "Adaptive (Hedge)",
             "not_implementable": "Best in hindsight (infeasible)",
             "not_like_for_like": "Return blend (not comparable)"}
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=colour[k],
                             hatch="//" if k in {"not_implementable", "not_like_for_like"} else None)
               for k in kinds if k in set(frame["kind"])]
    labels = [names[k] for k in kinds if k in set(frame["kind"])]
    ax.set_xlim(0, float(frame["after_tax_sharpe"].max()) * 1.16)
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, fontsize=6.8)
    _grid(ax, axis="x")
    _provenance(ax, "Source: alphacomb/outputs/summary_adaptive.csv. The hatched 'return blend' averages three "
                    "separately optimised books and is NOT comparable; the fixed 1/N alpha blend is, because it "
                    "differs from the adaptive arm only in the weights. Remlinger et al. (2023) report a universe "
                    "where the uniform mixture beats their online rule.",
                y=-0.30 if len(frame) > 4 else -0.40)
    return _save(fig, "fig_adaptive_vs_benchmarks.png")


def fig_prior_art_positioning():
    """Where the literatures sit on two axes, and the corner nobody occupies.

    The vertical axis is how far the evaluation goes: gross, net of trading cost, net of cost AND
    tax. The horizontal axis is how many signals are combined. Positions are editorial judgements
    from the Closest Prior Art Tracker, not measurements, and the figure says so.
    """
    fig, ax = plt.subplots(figsize=(7.8, 4.4), constrained_layout=True)
    ax.set_xlim(0, 10)
    ax.set_ylim(0.2, 10)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    ax.set_yticks([2.0, 5.2, 8.3])
    ax.set_yticklabels(["Gross of\neverything", "Net of\ntrading cost", "Net of cost\nAND tax"], fontsize=7.4)
    ax.set_xticks([2.4, 7.3])
    ax.set_xticklabels(["A few factors\nor styles", "High-dimensional\nML combination"], fontsize=7.4)
    ax.set_xlabel("How many signals are combined", fontsize=8, labelpad=4)
    ax.set_ylabel("How far the evaluation goes", fontsize=8, labelpad=4)
    _grid(ax, axis="both")

    entries = [
        # Amber, not the green slot: #1baf7a against #6da7ec separates by only 4.7 under
        # tritanopia, below the 6-8 floor. #eda100 lifts the worst tritan pair to 26.1.
        (7.3, 2.0, "Online aggregation\nRemlinger et al. 2023\n13 ML models, no cost model,\nzero mentions of tax",
         SLOTS[3], INK),
        (7.3, 5.2, "ML asset pricing\nGKX 2020, JKMP 2026,\nSWZ 2023, DMU 2024\nnet of cost, gross of tax",
         SEQ["300"], INK),
        (2.4, 8.3, "After-tax investing\nJeffrey-Arnott 1993,\nSialm-Sosner 2018,\nKrasner-Sosner 2024",
         SLOTS[1], "#ffffff"),
        (7.3, 8.3, "THIS PROJECT\nafter-tax attribution across\nML design ingredients",
         SEQ["600"], "#ffffff"),
    ]
    for x, y, label, fc, tc in entries:
        ax.add_patch(plt.Rectangle((x - 2.05, y - 1.05), 4.1, 2.1, facecolor=fc,
                                   edgecolor=SURFACE, linewidth=1.4, zorder=3))
        ax.text(x, y, label.replace("\n", "\n"), ha="center", va="center", fontsize=6.9,
                color=tc, zorder=4)

    ax.annotate("", xy=(7.3, 7.15), xytext=(7.3, 6.3),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.0), zorder=2)
    ax.annotate("", xy=(5.15, 8.3), xytext=(4.55, 8.3),
                arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.0), zorder=2)

    ax.set_title("Two mature literatures. The top-right corner is the opening we are testing.",
                 fontsize=9.5, loc="left")
    _provenance(ax, "Positions are editorial judgements recorded in 03_Research_Gaps/Closest_Prior_Art_Tracker.md, "
                    "not measurements. [inference]", y=-0.20)
    return _save(fig, "fig_prior_art_positioning.png")


def build_all():
    made = []
    for fn in (fig_tax_waterfall, fig_tax_drag_decomposition, fig_lot_method_matters, fig_wash_sale_bite,
               fig_adaptive_weights, fig_adaptive_vs_benchmarks, fig_prior_art_positioning):
        path = fn()
        if path:
            made.append(path)
    return made


if __name__ == "__main__":
    os.makedirs(FIGS, exist_ok=True)
    for p in build_all():
        print("wrote", p)
