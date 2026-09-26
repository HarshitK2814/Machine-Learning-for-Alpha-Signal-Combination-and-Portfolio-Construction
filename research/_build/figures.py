# -*- coding: utf-8 -*-
"""Static figures for the PDF reports. Palette: validated reference categorical slots (light mode),
recessive chrome, thin marks, legends for >=2 series, selective direct labels. No invented data:
every plotted value comes from the project data files (literature, journals, ideas, roadmap)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from common import CORE, OTHER, EXTRA, J, IDEAS, ACADEMIC, FIGS, idea_score

SURFACE = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; MUTED = "#898781"; GRID = "#e1e0d9"; AXIS = "#c3c2b7"
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
SEQ = {"100": "#cde2fb", "200": "#9ec5f4", "300": "#6da7ec", "450": "#2a78d6", "600": "#184f95", "700": "#0d366b"}

plt.rcParams.update({
    "font.family": ["Segoe UI", "Arial", "DejaVu Sans"], "font.size": 9, "axes.edgecolor": AXIS,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False, "legend.frameon": False,
})


def _grid(ax, axis="y"):
    ax.grid(True, axis=axis, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _save(fig, name):
    os.makedirs(FIGS, exist_ok=True)
    p = os.path.join(FIGS, name)
    fig.savefig(p, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return p


GROUPS = [
    ("ML prediction & asset pricing", {"ML asset pricing"}),
    ("Implementability & trading costs", {"ML strategies & implementability", "TC & implementability"}),
    ("Portfolio construction & end-to-end", {"Portfolio construction", "End-to-end / decision-focused"}),
    ("Timing & regimes", {"Factor timing & regimes"}),
    ("Inference, replication, data & methods", {"Statistical inference", "Replication & multiple testing",
                                                "Data & measurement", "ML methods", "Industry"}),
]


def fig_literature_timeline():
    papers = CORE + [o for o in OTHER] + EXTRA
    seen, uniq = set(), []
    for p in papers:
        if p["id"] not in seen:
            seen.add(p["id"]); uniq.append(p)
    buckets = [("<2000", 0, 1999), ("2000-09", 2000, 2009), ("2010-14", 2010, 2014), ("2015-19", 2015, 2019),
               ("2020-22", 2020, 2022), ("2023-26", 2023, 2026)]
    counts = {g: [0] * len(buckets) for g, _ in GROUPS}
    for p in uniq:
        g = next((name for name, cats in GROUPS if p["category"] in cats), GROUPS[-1][0])
        for k, (_, a, b) in enumerate(buckets):
            if a <= p["year"] <= b:
                counts[g][k] += 1
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    bottoms = [0] * len(buckets)
    x = range(len(buckets))
    for (g, _), col in zip(GROUPS, SLOTS):
        ax.bar(x, counts[g], bottom=bottoms, width=0.62, color=col, edgecolor=SURFACE, linewidth=1.5, label=g)
        bottoms = [b + c for b, c in zip(bottoms, counts[g])]
    for k, tot in enumerate(bottoms):
        ax.text(k, tot + 0.8, str(tot), ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xticks(list(x)); ax.set_xticklabels([b[0] for b in buckets])
    ax.set_ylabel("Papers in literature universe"); _grid(ax)
    ax.set_title(f"Literature universe by publication period and strand (n = {len(uniq)})", loc="left", fontsize=10)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=7.5, ncol=3)
    ax.set_ylim(0, max(bottoms) * 1.12)
    return _save(fig, "fig_literature_timeline.png")


def fig_journal_map():
    """Sorted horizontal bars of project fit, coloured by venue class (3 validated slots), role as direct label."""
    cls = lambda t: 0 if t.startswith("Tier 1 -") or t.startswith("Tier 1b") else (1 if t.startswith("Tier 2") else 2)
    names = ["Top finance / top OR (Tier 1, 1b)", "Quantitative, field & OR (Tier 2)", "Practitioner & ML venues"]
    rows = sorted(J, key=lambda j: (j["fit"], -j["difficulty"]))
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    for y, j in enumerate(rows):
        c = cls(j["tier"])
        ax.barh(y, j["fit"], height=0.62, color=SLOTS[c], edgecolor=SURFACE, linewidth=1.5, label=names[c])
        role = j["role"].split(" (")[0]
        ax.text(j["fit"] + 0.12, y, f"{j['fit']}  {role}", va="center", fontsize=6.8, color=INK2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([j["journal"] for j in rows], fontsize=7.2, color=INK)
    ax.set_xlim(0, 13.5); ax.set_xticks(range(0, 11, 2))
    ax.set_xlabel("Project fit score (1-10, team assessment)")
    _grid(ax, "x")
    h, l = ax.get_legend_handles_labels(); uniq = dict(zip(l, h))
    ax.legend([uniq[n] for n in names if n in uniq], [n for n in names if n in uniq], loc="lower right", fontsize=7.4)
    ax.set_title("Journal fit for the selected paper, with recommended role", loc="left", fontsize=10)
    return _save(fig, "fig_journal_map.png")


def fig_opportunity_matrix():
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    best = max(IDEAS, key=idea_score)["id"]
    for i in IDEAS:
        x = i["publication"] + ACADEMIC[i["id"]] * 0.0
        y = (i["data_feas"] + (10 - i["complexity"]) + (10 - i["risk"])) / 3
        sc = idea_score(i)
        col = SLOTS[0] if i["id"] == best else MUTED
        ax.scatter(x, y, s=(sc - 4.5) ** 2 * 70, color=col, alpha=0.9 if i["id"] == best else 0.55,
                   edgecolor=SURFACE, linewidth=1.5, zorder=3)
        ax.annotate(i["id"], (x, y), xytext=(7, -3), textcoords="offset points", fontsize=7.5,
                    color=INK if i["id"] == best else INK2, fontweight="bold" if i["id"] == best else "normal")
    ax.set_xlabel("Publication potential (0-10)")
    ax.set_ylabel("Feasibility = mean(data feasibility, 10 - difficulty, 10 - risk)")
    _grid(ax, "both")
    ax.set_title(f"Opportunity matrix: bubble size = weighted overall score; highlighted = {best} (selected)",
                 loc="left", fontsize=10)
    ax.set_xlim(3.5, 9); ax.set_ylim(3.5, 8)
    return _save(fig, "fig_opportunity_matrix.png")


def _box(ax, x, y, w, h, text, fc, ec=AXIS, tc=INK, fs=7.2, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02", fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, wrap=True,
            fontweight="bold" if bold else "normal")


def fig_pipeline():
    stages = [
        ("Data", "d"), ("Point-in-time\nengineering", "d"), ("Signal\ngeneration", "s"), ("Signal\ncleaning", "s"),
        ("Normalisation", "s"), ("Signal quality\nanalysis", "s"),
        ("Redundancy\nanalysis", "s"), ("Train / valid / test\n+ lockbox", "m"), ("ML alpha\ncombination\n(16 cells)", "m"),
        ("Expected return /\nweight proposal", "m"), ("Portfolio\nconstruction", "p"), ("Risk controls", "p"),
        ("Transaction\ncosts", "p"), ("Execution\nassumptions", "p"), ("Backtesting", "e"), ("Statistical\ntests", "e"),
        ("Robustness\ntests", "e"), ("Economic\ninterpretation", "e"),
    ]
    colors = {"d": SEQ["100"], "s": SEQ["100"], "m": SEQ["300"], "p": SEQ["100"], "e": SEQ["100"]}
    fig, ax = plt.subplots(figsize=(7.4, 4.0)); ax.set_xlim(0, 6); ax.set_ylim(0, 3.2); ax.axis("off")
    w, h = 0.86, 0.62
    for k, (t, g) in enumerate(stages):
        row, col = divmod(k, 6)
        c = col if row % 2 == 0 else 5 - col
        x = 0.07 + c * 0.99; y = 2.35 - row * 1.05
        _box(ax, x, y, w, h, t, colors[g], tc=INK if g != "m" else INK, bold=(g == "m"))
        if k < len(stages) - 1:
            nrow, ncol = divmod(k + 1, 6)
            if nrow == row:
                yc = y + h / 2
                if row % 2 == 0:   # left-to-right row
                    start, end = (x + w, yc), (x + 0.99, yc)
                else:              # right-to-left row
                    start, end = (x, yc), (x - 0.99 + w, yc)
                ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.8))
            else:
                ax.annotate("", xy=(x + w / 2, y - 0.43), xytext=(x + w / 2, y), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.8))
    ax.text(0.07, 3.08, "Empirical research pipeline (shaded stages = factorial ML core)", fontsize=10, color=INK, ha="left")
    return _save(fig, "fig_pipeline.png")


def fig_factorial():
    rows = [("L-S", "Linear, static"), ("L-C", "Linear, state-conditional"), ("N-S", "Nonlinear, static"),
            ("N-C", "Nonlinear, state-conditional")]
    cols = [("P-0", "Prediction loss\nno uncertainty"), ("P-U", "Prediction loss\n+ uncertainty"),
            ("E-0", "Economic loss\nno uncertainty"), ("E-U", "Economic loss\n+ uncertainty")]
    exp = {("L-S", "P"): "E20", ("N-S", "P"): "E21", ("L-C", "P"): "E22", ("N-C", "P"): "E23",
           ("L-S", "E"): "E24", ("N-S", "E"): "E25", ("L-C", "E"): "E26", ("N-C", "E"): "E27"}
    fig, ax = plt.subplots(figsize=(7.4, 3.9)); ax.set_xlim(-1.9, 4.1); ax.set_ylim(-0.25, 4.9); ax.axis("off")
    for c, (code, lab) in enumerate(cols):
        ax.text(c + 0.5, 4.72, lab, ha="center", va="center", fontsize=7.4, color=INK2)
    for r, (code, lab) in enumerate(rows):
        yy = 3.5 - r
        ax.text(-0.1, yy + 0.4, lab, ha="right", va="center", fontsize=7.6, color=INK2)
        for c, (ccode, _) in enumerate(cols):
            obj = ccode[0]
            fc = SEQ["100"] if obj == "P" else SEQ["300"]
            if code == "N-C" and ccode == "E-U":
                fc = SEQ["600"]
            tc = "#ffffff" if fc == SEQ["600"] else INK
            label = f"{code}-{ccode}\n{exp[(code, obj)]}{'' if ccode.endswith('0') else ' + E28'}"
            _box(ax, c + 0.05, yy + 0.05, 0.9, 0.78, label, fc, ec=SURFACE, tc=tc, fs=7.4)
    ax.text(-1.9, -0.15, "Economic loss = net-of-cost utility. All 16 cells share signals, universe, splits, optimiser, risk and cost model.\n"
            "Dark cell = full model; E29 decomposes main effects and interactions.", fontsize=7.0, color=INK2, va="top")
    ax.set_ylim(-0.75, 5.05)
    return _save(fig, "fig_factorial_design.png")


def fig_roadmap():
    phases = [("1 Literature + design", 1, 2), ("2 Data infrastructure", 2, 4), ("3 Signal library", 3, 5),
              ("4 Baseline models", 5, 6), ("5 ML signal combination", 6, 9), ("6 Portfolio construction", 8, 10),
              ("7 Robust backtesting + lockbox", 9, 11), ("8 Robustness + statistics", 11, 13),
              ("9 Paper writing", 12, 15), ("10 Journal submission", 15, 16)]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    for k, (name, a, b) in enumerate(phases):
        y = len(phases) - 1 - k
        ax.barh(y, b - a + 1, left=a - 1, height=0.56, color=SLOTS[0], edgecolor=SURFACE, linewidth=1.5)
        ax.text(-0.2, y, name, ha="right", va="center", fontsize=7.8, color=INK)
    for m, lab in [(2, "Gate 1"), (6, "Gate 2"), (11, "Gate 3: freeze -> lockbox")]:
        ax.axvline(m, color=AXIS, lw=0.8)
        ax.text(m + 0.1, len(phases) - 0.35, lab, fontsize=7, color=INK2, va="bottom")
    ax.set_yticks([]); ax.set_xlim(0, 16.3); ax.set_ylim(-0.6, len(phases) + 0.2)
    ax.set_xticks(range(0, 17, 2)); ax.set_xlabel("Project month (planning estimate)")
    _grid(ax, "x"); ax.spines["left"].set_visible(False)
    ax.set_title("Implementation roadmap (single series: planned phase duration)", loc="left", fontsize=10)
    return _save(fig, "fig_roadmap.png")


def fig_prediction_to_value():
    steps = [("Forecast\nquality", "OOS R2,\nIC, rank IC"), ("Information\ntransfer", "transfer coeff.,\nconstraints"),
             ("Implement-\nability", "turnover, horizon,\nmicrocaps"), ("Trading\ncosts", "spread, impact,\nborrow"),
             ("Integrity\nhaircut", "snooping,\ndecay, NSE"), ("Net investment\nvalue", "net Sharpe,\nalpha, CE")]
    fig, ax = plt.subplots(figsize=(8.2, 2.1)); ax.set_xlim(0, 6); ax.set_ylim(0, 1.25); ax.axis("off")
    for k, (t, sub) in enumerate(steps):
        fc = SEQ["600"] if k == len(steps) - 1 else SEQ["100"]
        tc = "#ffffff" if k == len(steps) - 1 else INK
        _box(ax, k + 0.04, 0.12, 0.84, 0.86, f"{t}\n\n{sub}", fc, ec=SURFACE, tc=tc, fs=6.6)
        if k < len(steps) - 1:
            ax.annotate("", xy=(k + 1.03, 0.55), xytext=(k + 0.89, 0.55), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9))
    ax.text(0.04, 1.12, "Conceptual chain from prediction to investment value (each link is a measured quantity in our design)",
            fontsize=8.5, color=INK)
    return _save(fig, "fig_prediction_to_value.png")


def build_all():
    return [fig_literature_timeline(), fig_journal_map(), fig_opportunity_matrix(), fig_pipeline(), fig_factorial(),
            fig_roadmap(), fig_prediction_to_value()]


if __name__ == "__main__":
    for p in build_all():
        print(p)
