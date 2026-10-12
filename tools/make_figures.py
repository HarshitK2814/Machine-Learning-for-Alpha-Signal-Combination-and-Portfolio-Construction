#!/usr/bin/env python
"""Figures from COMMITTED snapshots only (audit task P0-7).

Reads only tracked files under ``results/`` and writes figures plus a manifest recording the SHA-256 of every input,
of this script, library versions and git state. No frozen data, no model output and no ``outputs/`` file is read, so a
clean checkout reproduces the figures.

What the figures show and how comparisons are labelled
* The capacity return difference B(A) is drawn **only at solvent rungs** (no cell-month of either book at or below
  -100%). Rungs where the uncapped comparator is insolvent are shaded and labelled; **no B is drawn or interpolated there**.
* Solvent rungs whose uncapped composite ends with less than ``NEAR_RUINED_WEALTH`` of its starting value are drawn with
  hollow markers: **near-ruined but technically solvent** comparators. The threshold is a *descriptive flag for display
  only*. It is not part of the solvency rule and no rung is excluded by it.
* Tier B (the pipeline accounting) is primary; Tier A is drawn lighter.

    python tools/make_figures.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CAP = ROOT / "results" / "capacity_return_difference"
PAR = ROOT / "results" / "cost_parity_diagnostic"
OUT = ROOT / "results" / "figures"
COUNTRIES = ("DEU", "IND", "JPN")
NAMES = {"DEU": "Germany", "IND": "India", "JPN": "Japan"}
NEAR_RUINED_WEALTH = 0.1           # display flag only
SOLVENCY_RULE = "no cell-month of either book at or below -100% net return, over the whole horizon"
INPUTS = ([CAP / f"tierA_{c}.csv" for c in COUNTRIES] + [CAP / f"tierB_{c}.csv" for c in COUNTRIES]
          + [PAR / "parity_summary.csv", PAR / "dtv_support.csv"])


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def b_series(country: str, cap_dir: Path = CAP) -> pd.DataFrame:
    """One row per mandate rung with B for Tier A and Tier B and an explicit status.

    ``status`` is ``solvent`` or ``insolvent``. B is NaN at insolvent rungs by construction (Tier A computes none);
    ``near_ruined`` flags solvent rungs whose uncapped terminal wealth is below the display threshold.
    """
    a = pd.read_csv(cap_dir / f"tierA_{country}.csv")
    b = pd.read_csv(cap_dir / f"tierB_{country}.csv")
    d = a[["aum", "solvent", "B", "uncapped_terminal_wealth", "first_uncapped_wipeout"]].rename(
        columns={"B": "B_A", "uncapped_terminal_wealth": "wealth_A"})
    d = d.merge(b[["aum", "B", "uncapped_terminal_wealth"]].rename(columns={"B": "B_B", "uncapped_terminal_wealth": "wealth_B"}),
                on="aum", how="left")
    d["status"] = np.where(d["solvent"], "solvent", "insolvent")
    d.loc[d["status"] == "insolvent", ["B_A", "B_B", "wealth_B"]] = np.nan
    d["near_ruined"] = (d["status"] == "solvent") & (d["wealth_B"] < NEAR_RUINED_WEALTH)
    d["country"] = country
    return d.sort_values("aum").reset_index(drop=True)


def _aum_label(x: float) -> str:
    return f"${x/1e9:g}bn" if x >= 1e9 else (f"${x/1e6:g}mn" if x >= 1e6 else f"${x/1e3:g}k")


def _shade_insolvent(ax, d: pd.DataFrame) -> None:
    ins = d[d["status"] == "insolvent"]
    if len(ins):
        ax.axvspan(ins["aum"].min() / 1.3, ax.get_xlim()[1] if ax.get_xlim()[1] > ins["aum"].max() else ins["aum"].max() * 1.3,
                   color="0.85", zorder=0)
        ax.text(ins["aum"].min(), 0.97, "uncapped comparator insolvent:\nno B computed", transform=ax.get_xaxis_transform(),
                fontsize=7, va="top", ha="left", color="0.25")


def fig_b(frames: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=False)
    for ax, c in zip(axes, COUNTRIES):
        d = frames[c]
        s = d[d.status == "solvent"]
        ax.set_xscale("log")
        ax.set_yscale("symlog", linthresh=1.0)
        for col, lab, colr, z in (("B_A", "Tier A (wedge tool)", "tab:orange", 2), ("B_B", "Tier B (pipeline, primary)", "tab:blue", 3)):
            ax.plot(s["aum"], s[col], "-", color=colr, alpha=0.6 if col == "B_A" else 0.9, lw=1.2, zorder=z, label=lab)
            solid, hollow = s[~s.near_ruined], s[s.near_ruined]
            ax.plot(solid["aum"], solid[col], "o", color=colr, ms=4.5, zorder=z)
            ax.plot(hollow["aum"], hollow[col], "o", mfc="white", mec=colr, ms=5, zorder=z)
        ax.axhline(0, color="k", lw=0.5)
        top = float(np.nanmax(s[["B_A", "B_B"]].to_numpy()))
        ticks = [t for t in (0, 1, 10, 100, 1000) if t <= max(top * 1.5, 1)]
        ax.set_yticks(ticks)
        ax.set_yticklabels([str(t) for t in ticks], fontsize=7)
        ax.set_title(NAMES[c])
        ax.set_xlabel("mandate (AUM)")
        xs = list(d["aum"])
        ax.set_xticks(xs[::2])
        ax.set_xticklabels([_aum_label(x) for x in xs[::2]], rotation=45, fontsize=7)
        ax.set_xlim(min(xs) / 1.5, max(xs) * 1.5)
        _shade_insolvent(ax, d)
    axes[0].set_ylabel("B(A): capped minus uncapped mean net return\n(points of NAV per year; symlog)")
    axes[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("Capacity return difference B(A), solvent rungs only", fontsize=11)
    fig.text(0.5, 0.005, f"Hollow markers: solvent but near-ruined comparator (uncapped terminal wealth < {NEAR_RUINED_WEALTH}; display flag, "
             "not an exclusion). Grey: insolvent comparator, B not computed. B is an accounting difference against an infeasible plan, "
             "not realised performance.", ha="center", fontsize=6.5, wrap=True)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_wealth(frames: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.0))
    for ax, c in zip(axes, COUNTRIES):
        d = frames[c]
        s = d[d.status == "solvent"]
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.plot(s["aum"], s["wealth_A"], "o-", color="tab:orange", alpha=0.6, ms=4, label="Tier A")
        ax.plot(s["aum"], s["wealth_B"], "o-", color="tab:blue", ms=4, label="Tier B (primary)")
        ax.axhline(1.0, color="k", lw=0.6)
        ax.axhline(NEAR_RUINED_WEALTH, color="tab:red", lw=0.8, ls="--")
        ax.set_ylim(1e-22, 1e2)
        xs = list(d["aum"])
        ax.set_xticks(xs[::2])
        ax.set_xticklabels([_aum_label(x) for x in xs[::2]], rotation=45, fontsize=7)
        ax.set_xlim(min(xs) / 1.5, max(xs) * 1.5)
        ax.set_title(NAMES[c])
        _shade_insolvent(ax, d)
    axes[0].set_ylabel("uncapped composite: compounded terminal wealth\n(starting value = 1)")
    axes[0].legend(fontsize=7, loc="lower left")
    fig.suptitle("The uncapped comparator at solvent rungs: compounded terminal wealth", fontsize=11)
    fig.text(0.5, 0.005, f"Dashed line: {NEAR_RUINED_WEALTH} (display flag for near-ruined, not an exclusion). "
             "Grey: insolvent comparator, no value computed.", ha="center", fontsize=6.5)
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_parity(path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = pd.read_csv(PAR / "parity_summary.csv")
    d["label"] = [f"{r.country} {_aum_label(r.aum)}\n{r.book}" for r in d.itertuples()]
    fig, ax = plt.subplots(figsize=(12, 4.4))
    x = np.arange(len(d))
    w = 0.26
    for i, (col, lab, colr) in enumerate((("shap_D", "D: drifted vs target trade basis", "tab:green"),
                                           ("shap_X", "X: exit treatment", "tab:purple"),
                                           ("shap_B", "B: borrow fee", "tab:gray"))):
        ax.bar(x + (i - 1) * w, d[col], w, label=lab, color=colr)
    ax.set_yscale("symlog", linthresh=1.0)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(d["label"], fontsize=7)
    ax.set_ylabel("Shapley attribution of Tier A minus Tier B cost\n(points of NAV per year; symlog)")
    ax.legend(fontsize=7)
    fig.suptitle("Why Tier A and Tier B costs differ: attribution to three accounting conventions", fontsize=11)
    fig.text(0.5, 0.005, "Positive: switching that convention to Tier A raises cost. No single mechanism meets the pre-set "
             "dominance criterion (X 6/12, B 5/12, D 2/12). Replication error <= 3.3e-16 in 11 of 12 pairs.",
             ha="center", fontsize=6.5)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def fig_support(path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = pd.read_csv(PAR / "dtv_support.csv")
    d["label"] = [f"{r.country} {_aum_label(r.aum)}" for r in d.itertuples()]
    rungs = list(dict.fromkeys(d["label"]))
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for ax, thr, col in zip(axes, ("12% of daily volume", "100% of daily volume"),
                             ("share_notional_gt12pct_ADV", "share_notional_gt100pct_ADV")):
        for i, book in enumerate(("uncapped", "capped")):
            v = [float(d[(d.label == r) & (d.book == book)][col].iloc[0]) for r in rungs]
            ax.bar(np.arange(len(rungs)) + (i - 0.5) * 0.38, v, 0.38, label=book, color="tab:red" if book == "uncapped" else "tab:blue")
        ax.set_xticks(np.arange(len(rungs)))
        ax.set_xticklabels(rungs, rotation=30, fontsize=7)
        ax.set_title(f"share of traded notional beyond {thr}")
        ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("share of traded notional")
    axes[0].legend(fontsize=7)
    fig.suptitle("Trade size relative to daily volume: published live-trade impact estimates end near 12%", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(path, dpi=160)
    plt.close(fig)


def git(*a: str) -> str:
    try:
        return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return "unavailable"


def build(out: Path, overwrite: bool = False) -> dict:
    import matplotlib
    from alphacomb.output_guard import claim_output

    script = Path(__file__).resolve()
    params = {"inputs": {p.relative_to(ROOT).as_posix(): sha256(p) for p in INPUTS},
              "script": sha256(script), "near_ruined_wealth": NEAR_RUINED_WEALTH, "solvency_rule": SOLVENCY_RULE}
    claim_output(out, params, is_dir=True, overwrite=overwrite)
    frames = {c: b_series(c) for c in COUNTRIES}
    figs = {"fig1_capacity_return_difference_B.png": lambda p: fig_b(frames, p),
            "fig2_uncapped_terminal_wealth.png": lambda p: fig_wealth(frames, p),
            "fig3_tierA_tierB_attribution.png": fig_parity,
            "fig4_trade_size_vs_daily_volume.png": fig_support}
    for name, fn in figs.items():
        fn(out / name)
    manifest = {
        "purpose": "figures regenerated from committed snapshots only",
        "git_head_when_written": git("rev-parse", "HEAD"), "git_dirty_when_written": bool(git("status", "--porcelain")),
        "python": sys.version.split()[0], "matplotlib": matplotlib.__version__, "pandas": pd.__version__, "numpy": np.__version__,
        "solvency_rule": SOLVENCY_RULE,
        "near_ruined_display_flag": f"uncapped terminal wealth < {NEAR_RUINED_WEALTH}; display only, no exclusion",
        "inputs_sha256": params["inputs"], "script": script.relative_to(ROOT).as_posix(), "script_sha256": params["script"],
        "regenerate": "python tools/make_figures.py   (tracked inputs only)",
        "figures": {n: {"sha256": sha256(out / n), "inputs": ("all capacity tierA/tierB files" if n.startswith(("fig1", "fig2"))
                                                              else "results/cost_parity_diagnostic/" + ("parity_summary.csv" if "attribution" in n else "dtv_support.csv"))}
                    for n in figs},
        "note": "PNG bytes depend on the matplotlib version; the manifest records it. B is an accounting difference against an "
                "infeasible plan, not realised performance."}
    (out / "FIGURE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--overwrite", action="store_true", help="replace figures from different inputs or code")
    a = ap.parse_args(argv)
    m = build(a.out, a.overwrite)
    print("wrote", len(m["figures"]), "figures to", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
