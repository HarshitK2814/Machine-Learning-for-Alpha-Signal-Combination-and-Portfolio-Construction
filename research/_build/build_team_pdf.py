# -*- coding: utf-8 -*-
"""Builds PDF6: team coding work distribution (figures + PDF). Members are equal; listed alphabetically."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, REPORTS, load_refs
from figures import plt, SURFACE, INK, INK2, MUTED, AXIS, SLOTS, _grid, _save, _box
from render_pdf import build_pdf

OWNER = {"Absar": SLOTS[0], "Harshit": SLOTS[1], "Maham": SLOTS[2]}
TINT = {"Absar": "#cde2fb", "Harshit": "#fbd9c9", "Maham": "#c9eedd"}


def fig_team_timeline():
    tasks = [
        ("Absar", "Contracts sprint + synthetic data", 1, 1), ("Absar", "WRDS pulls, PIT panel, E00", 2, 6),
        ("Absar", "Signals, states, cost model", 7, 12), ("Absar", "Backtests, frontier, costs, capacity", 13, 20),
        ("Absar", "Lockbox backtests", 22, 22), ("Absar", "International data, capacity reports", 23, 28),
        ("Harshit", "Contracts sprint + interfaces", 1, 1), ("Harshit", "Cells LS-P, NS-P + optimiser v1", 2, 6),
        ("Harshit", "Conditional/economic cells, uncertainty, risk", 7, 12), ("Harshit", "16 cells walk-forward, E13, E64", 13, 20),
        ("Harshit", "Lockbox model runs", 22, 22), ("Harshit", "Seeds, interpretation, E33", 23, 28),
        ("Maham", "Contracts sprint + stats design", 1, 1), ("Maham", "Stats library + baselines (synthetic)", 2, 6),
        ("Maham", "Diagnostics, real baselines, decomposition", 7, 12), ("Maham", "Inference, E29, report templates", 13, 20),
        ("Maham", "Lockbox inference", 22, 22), ("Maham", "Robustness, mechanisms, final tables", 23, 28),
    ]
    fig, ax = plt.subplots(figsize=(7.6, 5.4))
    n = len(tasks)
    for k, (who, name, a, b) in enumerate(tasks):
        y = n - 1 - k
        ax.barh(y, b - a + 1, left=a - 0.5, height=0.62, color=OWNER[who], edgecolor=SURFACE, linewidth=1.5, label=who)
        ax.text(0.1, y, name, ha="right", va="center", fontsize=7.2, color=INK)
    for w, lab in [(1.5, "Contracts\nfrozen (all)"), (6.5, "IC1\n(Absar)"), (12.5, "IC2\n(Harshit)"), (20.5, "IC3\n(Maham)"),
                   (21.5, "Freeze +\nlockbox (all)")]:
        ax.axvline(w, color=AXIS, lw=0.8)
        left = lab.startswith("IC3")
        ax.text(w - 0.15 if left else w + 0.15, n - 0.2, lab, fontsize=6.4, color=INK2, va="bottom",
                ha="right" if left else "left")
    ax.set_yticks([]); ax.set_xlim(0, 28.8); ax.set_ylim(-0.7, n + 1.4)
    ax.set_xticks([1, 4, 8, 12, 16, 20, 24, 28]); ax.set_xlabel("Project week (planning estimate)")
    _grid(ax, "x"); ax.spines["left"].set_visible(False)
    h, l = ax.get_legend_handles_labels(); u = dict(zip(l, h))
    ax.legend([u[k] for k in OWNER], [f"{k} (100 pts)" for k in OWNER], loc="upper center", bbox_to_anchor=(0.5, -0.1),
              fontsize=7.5, ncol=3)
    ax.set_title("Parallel work plan: three equal lanes, shared checkpoints", loc="left", fontsize=10)
    return _save(fig, "fig_team_timeline.png")


def fig_team_interfaces():
    fig, ax = plt.subplots(figsize=(7.6, 4.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 6.2); ax.axis("off")
    boxes = [
        ("Absar", 0.2, 3.9, 2.3, 1.5, "Data layer\nPIT panel, signals,\nstates, targets\n(+ synthetic data)"),
        ("Absar", 0.2, 2.2, 2.3, 1.1, "Transaction-cost\nmodel"),
        ("Harshit", 0.2, 0.5, 2.3, 1.1, "Risk model"),
        ("Harshit", 3.4, 4.5, 2.4, 1.2, "Factorial ML cells\n+ uncertainty"),
        ("Maham", 3.4, 2.9, 2.4, 1.1, "Baselines\n(naive, linear, SDF, PPP)"),
        ("Harshit", 3.4, 0.6, 2.4, 1.3, "TC-aware optimiser\n+ E-cell projection"),
        ("Absar", 6.6, 0.6, 1.6, 1.3, "Backtest\nengine"),
        ("Maham", 6.6, 3.6, 3.2, 1.4, "Statistics, decomposition,\nrobustness, reporting"),
        ("Harshit", 8.4, 0.6, 1.4, 1.3, "Interpret-\nation"),
    ]
    for who, x, y, w, h, t in boxes:
        _box(ax, x, y, w, h, t, TINT[who], ec=OWNER[who], tc=INK, fs=7.2)

    def arrow(p, q, lab, tx, ty):
        ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=0.9))
        if lab:
            ax.text(tx, ty, lab, fontsize=6.4, color=INK2, ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec="none"))
    arrow((2.5, 5.1), (3.4, 5.1), "C1-C5", 2.95, 5.35)
    arrow((2.5, 4.2), (3.4, 3.45), "C2, C4, C5", 2.95, 4.05)
    arrow((2.5, 2.75), (3.4, 1.55), "C6", 2.95, 2.3)
    arrow((2.5, 1.05), (3.4, 1.05), "C7", 2.95, 0.85)
    arrow((4.6, 4.5), (4.6, 4.0), "C9", 4.95, 4.25)
    arrow((4.6, 2.9), (4.6, 1.9), "C9-C11 (baselines)", 5.4, 2.4)
    arrow((5.8, 1.25), (6.6, 1.25), "C11", 6.2, 1.5)
    arrow((7.4, 1.9), (7.8, 3.6), "C12", 7.3, 2.75)
    arrow((5.8, 5.1), (6.6, 4.6), "C9, C13", 6.2, 5.2)
    arrow((8.2, 1.25), (8.4, 1.25), "", 0, 0)
    for k, who in enumerate(OWNER):
        ax.add_patch(plt.Rectangle((0.2 + k * 1.7, 5.85), 0.25, 0.22, color=OWNER[who]))
        ax.text(0.52 + k * 1.7, 5.96, who, fontsize=7.6, color=INK, va="center")
    ax.text(5.3, 5.96, "Arrows = jointly frozen contracts (Section 4)", fontsize=7.2, color=INK2, va="center")
    return _save(fig, "fig_team_interfaces.png")


def main():
    fig_team_timeline(); fig_team_interfaces()
    refs = load_refs()
    md = open(os.path.join(ROOT, "07_Experimental_Framework", "Team_Coding_Work_Distribution.md"), encoding="utf-8").read()
    out = os.path.join(REPORTS, "PDF6_Team_Coding_Work_Distribution.pdf")
    build_pdf(out, dict(kicker="Team plan | Coding work distribution", title="Team Coding Work Distribution",
                        subtitle="Absar, Harshit and Maham: three equal workstreams, frozen interface contracts and a conflict-free merge plan",
                        blurb="All three members are equal partners with the same planned workload (100 points each). "
                              "Work proceeds in parallel against synthetic data and jointly frozen contracts, with rotating "
                              "integration checkpoints, so the final merge is a formality rather than a risk.",
                        short="PDF 6 - Team Coding Work Distribution", report_no="Team plan"), [("md", md)], refs)
    import fitz
    d = fitz.open(out); print(out, d.page_count, "pages")


if __name__ == "__main__":
    main()
