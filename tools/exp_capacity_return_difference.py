#!/usr/bin/env python
"""Capacity measure in return units: B(A) = 12 * (mean net return capped - mean net return uncapped).

Specification: docs/CAPACITY_RETURN_DIFFERENCE_SPEC_2026-10-10.md.

Three stages, so every reported number can be regenerated from TRACKED files:

  snapshot  copy the untracked wedge-tool monthly series (outputs/, git-ignored) and the solvency
            table into results/capacity_return_difference/inputs/ and write a SHA-256 manifest.
  pipeline  (heavy; needs the frozen data) run the pipeline's own ``after_tax_backtest`` at zero tax
            on the re-dumped decile weights for every valid rung and save the per-cell monthly
            gross / net / cost series to results/.../tierB_monthly_<C>.csv.gz.
  tables    (light; tracked inputs only) compute Tier A, Tier B, the side-by-side reconciliation and
            the markdown tables.

Tier A = wedge-tool series (tag ``cov``); Tier B = pipeline accounting (tag ``tierb`` weights).
A rung is valid only if NO cell-month of either book is at or below -100% (each cell is a separately
funded account at the full AUM; see the spec, section on the accounting unit). Insolvent rungs get no
B(A).

    python tools/exp_capacity_return_difference.py --stage snapshot
    python tools/exp_capacity_return_difference.py --stage pipeline --country DEU
    python tools/exp_capacity_return_difference.py --stage tables
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from alphacomb.validation.inference import mean_difference_test, newey_west_se  # noqa: E402

PERIODS = 12
OUTPUTS = ROOT / "outputs"
RES = ROOT / "results" / "capacity_return_difference"
INP = RES / "inputs"
COUNTRIES = ("DEU", "IND", "JPN")


def holm(p: dict) -> dict:
    items = sorted(((k, v) for k, v in p.items() if np.isfinite(v)), key=lambda kv: kv[1])
    m, run, out = len(items), 0.0, {k: float("nan") for k in p}
    for i, (k, v) in enumerate(items):
        run = max(run, min(1.0, (m - i) * v))
        out[k] = run
    return out


def sharpe(x) -> float:
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    return float(x.mean() / s * np.sqrt(PERIODS)) if s > 0 else float("nan")


def t_nw(x) -> float:
    x = np.asarray(x, float)
    se = newey_west_se(x)
    return float(x.mean() / se) if se > 0 else float("nan")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


# ----------------------------------------------------------------------------- Tier A / shared
def composite_from_cells(g: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    piv = g.pivot_table(index="date", columns="cell", values=cols)
    return pd.DataFrame({c: piv[c].mean(axis=1) for c in cols}).dropna()


def b_row(comp: pd.DataFrame, g_cap: str, g_unc: str, n_cap: str, n_unc: str,
          n_boot: int, block: int, seed: int) -> dict:
    r = mean_difference_test(comp[n_cap], comp[n_unc], periods=PERIODS, n_boot=n_boot,
                             block=block, seed=seed)
    dg = PERIODS * float((comp[g_cap] - comp[g_unc]).mean())
    ds = PERIODS * float(((comp[g_unc] - comp[n_unc]) - (comp[g_cap] - comp[n_cap])).mean())
    geo = lambda x: float(np.prod(1 + x) ** (PERIODS / len(x)) - 1)  # noqa: E731
    return {"B": r.statistic, "B_ci_low": r.detail["ci95_low"], "B_ci_high": r.detail["ci95_high"],
            "se_hac": r.detail["se_hac"], "t_stud": r.detail["studentized"], "p": r.p_value,
            "gross_forgone": dg, "cost_saved": ds, "recon_residual": r.statistic - (dg + ds),
            "uncapped_mean_net_ann": PERIODS * float(comp[n_unc].mean()),
            "geometric_ann_diff": geo(comp[n_cap].to_numpy()) - geo(comp[n_unc].to_numpy())}


def add_holm(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["p_holm"] = np.nan
    adj = holm({i: d.loc[i, "p"] for i in d.index[d["solvent"]]})
    for i, v in adj.items():
        d.loc[i, "p_holm"] = v
    return d


def tier_a(country: str, n_boot: int, block: int, seed: int) -> pd.DataFrame:
    mon = pd.read_csv(INP / f"monthly_{country}_cov.csv", parse_dates=["date"])
    rows = []
    for aum, g in mon.groupby("aum"):
        cols = ["gross_ret", "net_ret_uncapped", "gross_ret_capped", "net_ret_capped"]
        comp = composite_from_cells(g, cols)
        min_u, min_c = float(g["net_ret_uncapped"].min()), float(g["net_ret_capped"].min())
        wiped = g.loc[g["net_ret_uncapped"] <= -1.0]
        cells_wiped = int(wiped["cell"].nunique())
        solvent = (min_u > -1.0) and (min_c > -1.0)
        comp_rule = (comp["net_ret_uncapped"].min() > -1.0) and (comp["net_ret_capped"].min() > -1.0)
        cap = comp["net_ret_capped"].to_numpy()
        row = {"country": country, "aum": float(aum), "months": len(comp), "solvent": solvent,
               "solvent_if_composite_rule": bool(comp_rule), "cells_wiped_of_8": cells_wiped,
               "min_monthly_net_uncapped": min_u, "min_monthly_net_capped": min_c,
               "first_uncapped_wipeout": str(wiped["date"].min().date()) if len(wiped) else "",
               "uncapped_terminal_wealth": float(np.prod(1 + comp["net_ret_uncapped"])),
               "capped_terminal_wealth": float(np.prod(1 + comp["net_ret_capped"])),
               "capped_mean_net_ann": PERIODS * float(cap.mean()),
               "capped_sharpe": sharpe(cap), "capped_t_nw": t_nw(cap)}
        if solvent:
            row.update(b_row(comp, "gross_ret_capped", "gross_ret", "net_ret_capped",
                             "net_ret_uncapped", n_boot, block, seed))
        rows.append(row)
    return add_holm(pd.DataFrame(rows).sort_values("aum").reset_index(drop=True))


# ----------------------------------------------------------------------------- Tier B
def tier_b(country: str, valid_aums: list[float], n_boot: int, block: int, seed: int) -> pd.DataFrame:
    m = pd.read_csv(RES / f"tierB_monthly_{country}.csv.gz", parse_dates=["date"])
    rows = []
    for aum in valid_aums:
        g = m[np.isclose(m["aum"], aum)]
        if g.empty:
            rows.append({"country": country, "aum": aum, "tierB_status": "NOT RUN"})
            continue
        u, c = g[g.book == "uncapped"], g[g.book == "capped"]
        pu = u.pivot_table(index="date", columns="cell", values=["gross_ret", "net_ret", "cost_total"])
        pc = c.pivot_table(index="date", columns="cell", values=["gross_ret", "net_ret", "cost_total"])
        comp = pd.DataFrame({
            "gross_ret": pu["gross_ret"].mean(axis=1), "net_ret_uncapped": pu["net_ret"].mean(axis=1),
            "gross_ret_capped": pc["gross_ret"].mean(axis=1), "net_ret_capped": pc["net_ret"].mean(axis=1),
            "cost_unc": pu["cost_total"].mean(axis=1), "cost_cap": pc["cost_total"].mean(axis=1)}).dropna()
        min_u, min_c = float(u["net_ret"].min()), float(c["net_ret"].min())
        cells_u = u.groupby("cell")["date"].nunique()
        row = {"country": country, "aum": float(aum), "months": len(comp),
               "min_monthly_net_uncapped": min_u, "min_monthly_net_capped": min_c,
               "min_cell_months_uncapped": int(cells_u.min()),
               "pipeline_solvent": bool(min_u > -1.0 and min_c > -1.0
                                        and int(u.groupby("cell")["date"].nunique().min()) >= int(u["dates_expected"].iloc[0])
                                        and int(c.groupby("cell")["date"].nunique().min()) >= int(c["dates_expected"].iloc[0])),
               "capped_mean_net_ann": PERIODS * float(comp["net_ret_capped"].mean()),
               "capped_sharpe": sharpe(comp["net_ret_capped"]),
               "capped_t_nw": t_nw(comp["net_ret_capped"]),
               "uncapped_terminal_wealth": float(np.prod(1 + comp["net_ret_uncapped"]))}
        if row["pipeline_solvent"]:
            row.update(b_row(comp, "gross_ret_capped", "gross_ret", "net_ret_capped",
                             "net_ret_uncapped", n_boot, block, seed))
            row["cost_saved_ledger"] = PERIODS * float((comp["cost_unc"] - comp["cost_cap"]).mean())
            row["recon_residual_ledger"] = row["B"] - (row["gross_forgone"] + row["cost_saved_ledger"])
        rows.append(row)
    d = pd.DataFrame(rows)
    d["solvent"] = d.get("pipeline_solvent", False)
    d = d.sort_values("aum").reset_index(drop=True)
    if "p" in d:
        d = add_holm(d.assign(solvent=d["solvent"].fillna(False).astype(bool)))
    return d


# ----------------------------------------------------------------------------- stages
def stage_snapshot() -> None:
    INP.mkdir(parents=True, exist_ok=True)
    files = [OUTPUTS / "signal_vs_portfolio" / f"monthly_{c}_cov.csv" for c in COUNTRIES]
    files.append(OUTPUTS / "signal_vs_portfolio" / "uncapped_solvency.csv")
    for f in files:
        shutil.copy2(f, INP / f.name)
    write_manifest(note="inputs snapshotted from git-ignored outputs/")
    print("snapshot written to", INP)


def write_manifest(note: str = "") -> None:
    def git(*a):
        try:
            return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
        except Exception:  # noqa: BLE001
            return "unavailable"
    man_path = RES / "MANIFEST.json"
    old = json.loads(man_path.read_text()) if man_path.exists() else {}
    files = {p.relative_to(RES).as_posix(): sha256(p)
             for p in sorted(RES.rglob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    man = {
        "purpose": "Inputs and outputs of the capacity return-difference analysis B(A) "
                   "(docs/CAPACITY_RETURN_DIFFERENCE_SPEC_2026-10-10.md)",
        "note": note or old.get("note", ""),
        "git_head_when_written": git("rev-parse", "HEAD"),
        "git_dirty_when_written": bool(git("status", "--porcelain")),
        "python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__,
        "inference": {"test": "mean_difference_test", "n_boot": 4000, "block": 6, "seed": 0,
                      "holm_family": "valid rungs within country"},
        "regeneration": {
            "wedge_series_cov": "python tools/exp_signal_vs_portfolio_wedge.py --country C --dump-monthly "
                                "--require-cost-inputs --tag cov --aum <14 rungs> (needs frozen data/, "
                                "not in git)",
            "weights_for_tierB": "python tools/exp_signal_vs_portfolio_wedge.py --country C --dump-monthly "
                                 "--dump-weights --require-cost-inputs --tag tierb --aum <valid rungs>",
            "tierB_monthly": "python tools/exp_capacity_return_difference.py --stage pipeline --country C",
            "tables": "python tools/exp_capacity_return_difference.py --stage tables "
                      "(uses only tracked files in this directory)"},
        "not_regenerable_from_git_alone": "inputs/monthly_*_cov.csv and tierB_monthly_*.csv.gz derive "
                                          "from frozen data/ and stage-02 predictions, which are not tracked",
        "sha256": files}
    man_path.write_text(json.dumps(man, indent=2))


def stage_pipeline(countries: list[str]) -> None:
    from alphacomb.contracts import intl, load_config
    from alphacomb.tax import get_regime
    from exp_matched_book_accounting import run_one

    for country in countries:
        a = tier_a(country, n_boot=200, block=6, seed=0)
        valid = [float(x) for x in a.loc[a.solvent, "aum"]]
        cfg0 = load_config("base")
        bundle = intl.load_country_bundle(country, max_names=600)
        zero = get_regime("tax_exempt")
        out = []
        for aum in valid:
            wdir = OUTPUTS / "decile_weights" / country / "tierb" / f"aum_{aum:.0e}"
            cfg = {**cfg0, "costs": {**cfg0["costs"], "aum_usd_2020": float(aum)}}
            for book in ("uncapped", "capped"):
                files = sorted(wdir.glob(f"{book}_*.parquet"))
                if len(files) != 8:
                    print(f"{country} {aum:.0e} {book}: expected 8 weight files, found {len(files)}")
                    continue
                for f in files:
                    w = pd.read_parquet(f)
                    fz = run_one(w, bundle, cfg, zero, aum)
                    n_dates = w["date"].nunique()
                    fz = fz.set_index("date")
                    fz["cost_total"] = (fz["cost_spread"] + fz["cost_impact"] + fz["cost_borrow"]
                                        + fz["cost_transaction_tax"])
                    t = fz[["gross_ret", "net_ret", "cost_total"]].reset_index()
                    t["country"], t["aum"], t["book"] = country, aum, book
                    t["cell"] = f.stem.split("_", 1)[1]
                    t["dates_expected"] = n_dates
                    out.append(t)
            print(f"{country} {aum:.0e} done", flush=True)
            pd.concat(out).to_csv(RES / f"tierB_monthly_{country}.csv.gz", index=False)
    write_manifest()


def fmt_aum(x: float) -> str:
    return f"${x/1e9:g}bn" if x >= 1e9 else (f"${x/1e6:g}mn" if x >= 1e6 else f"${x/1e3:g}k")


def stage_tables(n_boot: int, block: int, seed: int) -> None:
    pct = lambda x: f"{100 * x:+.2f}"  # noqa: E731
    md = []
    side = []
    for c in COUNTRIES:
        a = tier_a(c, n_boot, block, seed)
        a.to_csv(RES / f"tierA_{c}.csv", index=False)
        valid = [float(x) for x in a.loc[a.solvent, "aum"]]
        b = tier_b(c, valid, n_boot, block, seed) if (RES / f"tierB_monthly_{c}.csv.gz").exists() else None
        if b is not None:
            b.to_csv(RES / f"tierB_{c}.csv", index=False)
            j = a[a.solvent].merge(b, on=["country", "aum"], suffixes=("_A", "_B"))
            j["B_diff_A_minus_B"] = j["B_A"] - j["B_B"]
            j.to_csv(RES / f"reconciliation_{c}.csv", index=False)
            side.append(j)
        md.append(f"\n### {c}\n")
        md.append("| AUM | B Tier A | B Tier B | A-B | CI Tier B (unadj.) | t(B) | p Holm (B) | uncapped net/yr A | B | uncapped wealth A | B | capped net/yr A | B |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        if b is not None:
            for _, r in j.iterrows():
                md.append(
                    f"| {fmt_aum(r.aum)} | {pct(r.B_A)} | {pct(r.B_B)} | {100 * r.B_diff_A_minus_B:+.2f} | "
                    f"[{pct(r.B_ci_low_B)}, {pct(r.B_ci_high_B)}] | {r.t_stud_B:+.2f} | {r.p_holm_B:.4f} | "
                    f"{pct(r.uncapped_mean_net_ann_A)} | {pct(r.uncapped_mean_net_ann_B)} | "
                    f"{r.uncapped_terminal_wealth_A:.3g} | {r.uncapped_terminal_wealth_B:.3g} | "
                    f"{pct(r.capped_mean_net_ann_A)} | {pct(r.capped_mean_net_ann_B)} |")
        iv = a[~a.solvent]
        if len(iv):
            md.append(f"\nInsolvent comparator, **no B computed** ({len(iv)} rungs): "
                      + "; ".join(f"{fmt_aum(r.aum)} (uncapped first exhausts NAV {r.first_uncapped_wipeout}, "
                                  f"{int(r.cells_wiped_of_8)} of 8 cells wiped; capped net {pct(r.capped_mean_net_ann)}/yr, "
                                  f"Sharpe {r.capped_sharpe:+.2f}, t {r.capped_t_nw:+.2f})" for _, r in iv.iterrows()))
    (RES / "tables.md").write_text("\n".join(md), encoding="utf-8")
    write_manifest()
    print("\n".join(md))


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["snapshot", "pipeline", "tables"], required=True)
    ap.add_argument("--country", nargs="+", default=list(COUNTRIES))
    ap.add_argument("--n-boot", type=int, default=4000)
    ap.add_argument("--block", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    RES.mkdir(parents=True, exist_ok=True)
    if a.stage == "snapshot":
        stage_snapshot()
    elif a.stage == "pipeline":
        stage_pipeline(a.country)
    else:
        stage_tables(a.n_boot, a.block, a.seed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
