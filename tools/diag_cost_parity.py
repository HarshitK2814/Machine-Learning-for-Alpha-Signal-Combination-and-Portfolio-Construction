#!/usr/bin/env python
"""Component-level cost parity diagnostic: Tier A (wedge tool) versus Tier B (pipeline).

Specification (written before the run): docs/COST_PARITY_DIAGNOSTIC_SPEC_2026-10-10.md.
Accounting only: re-evaluates the existing cost function on the existing weights under every combination of
three conventions (D trade-size basis, X exit treatment, B borrow). Changes no model, parameter or result.

Stages
  run        (heavy; needs the frozen data and git-ignored weights) one process per country.
  summarize  (light; tracked files only) tables, replication checks and decision rules.

    python tools/diag_cost_parity.py --stage run --country DEU
    python tools/diag_cost_parity.py --stage summarize
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

OUTPUTS = ROOT / "outputs"
CAP = ROOT / "results" / "capacity_return_difference"
RES = ROOT / "results" / "cost_parity_diagnostic"
RUNGS = [("DEU", 1e5), ("DEU", 3e5), ("DEU", 1e8), ("IND", 3e7), ("JPN", 1e9), ("JPN", 1e10)]
CELLS = [f"{a}-{b}-P-{d}" for a in "LN" for b in "SC" for d in ("0", "U")]
COMBOS = ["".join(c) for c in itertools.product("AB", repeat=3)]      # D, X, B
BORROW_RATE = 0.01
TOL_ABS, TOL_REL, MATERIAL = 0.05, 0.05, 0.05                          # points per year


def _parts(dw, sp, sd, ad, aum, k, comm):
    from alphacomb.portfolio.cost_terms import trade_cost_numpy
    dw = np.asarray(dw, float)
    if dw.size == 0:
        return 0.0, 0.0
    lin = float(trade_cost_numpy(dw, sp, sd, ad, aum, 0.0, comm).sum())
    tot = float(trade_cost_numpy(dw, sp, sd, ad, aum, k, comm).sum())
    return lin, tot - lin


def cross_sections(country, bundle, cell):
    """S_t per date: names with a score and certified inputs (the wedge tool's --require-cost-inputs rule)."""
    from alphacomb.contracts import paths, read_table
    index = pd.read_csv(paths.outputs_root() / "source_index" / f"{country}.csv")
    src = dict(zip(index["strategy"].astype(str), index["artefact"].astype(str)))
    f = read_table(Path(src[f"cell_{cell}"]), "predictions")
    col = "score" if "score" in f.columns else [c for c in f.columns
                                                if c not in ("date", "permno", "unc_sd")][0]
    d = f[["date", "permno", col]].rename(columns={col: "score"}).copy()
    d["date"] = pd.to_datetime(d["date"])
    tg = bundle.targets[["date", "permno", "ret_next"]].copy()
    tg["date"] = pd.to_datetime(tg["date"])
    ci = bundle.cost_inputs[["date", "permno", "spread", "sigma_d", "adv_usd"]].copy()
    ci["date"] = pd.to_datetime(ci["date"])
    d = d.merge(tg, on=["date", "permno"], how="inner").merge(ci, on=["date", "permno"], how="left")
    good = (np.isfinite(d["adv_usd"]) & (d["adv_usd"] > 0) & np.isfinite(d["spread"])
            & np.isfinite(d["sigma_d"]))
    d = d.loc[good]
    return {pd.Timestamp(dt): g.set_index("permno")[["spread", "sigma_d", "adv_usd"]]
            for dt, g in d.groupby("date")}


def run_cell(country, aum, book, cell, bundle, cfg, zero, rets, divs):
    import alphacomb.tax.backtest as bt
    from exp_matched_book_accounting import run_one

    k = float(cfg["costs"]["impact_k"])
    comm = float(cfg["costs"]["commission_bps"])
    wdir = OUTPUTS / "decile_weights" / country / "tierb" / f"aum_{aum:.0e}"
    w = pd.read_parquet(wdir / f"{book}_{cell}.parquet")
    w["date"] = pd.to_datetime(w["date"])
    Tmap = {pd.Timestamp(dt): g.set_index("permno")["w"] for dt, g in w.groupby("date")}

    rec = {"date": [], "idx": [], "dw": [], "sp": [], "sd": [], "ad": []}
    o_ci, o_tc = bt.cost_inputs_for, bt.trade_cost_numpy

    def ci_wrap(date, cost_inputs, permnos, **kw):
        rec["date"].append(pd.Timestamp(date))
        rec["idx"].append(pd.Index(permnos))
        return o_ci(date, cost_inputs, permnos, **kw)

    def tc_wrap(dw, spread, sigma_d, adv_usd, *a, **kw):
        rec["dw"].append(np.array(dw, float))
        rec["sp"].append(np.array(spread, float))
        rec["sd"].append(np.array(sigma_d, float))
        rec["ad"].append(np.array(adv_usd, float))
        return o_tc(dw, spread, sigma_d, adv_usd, *a, **kw)

    bt.cost_inputs_for, bt.trade_cost_numpy = ci_wrap, tc_wrap
    try:
        fz = run_one(w, bundle, cfg, zero, aum)
    finally:
        bt.cost_inputs_for, bt.trade_cost_numpy = o_ci, o_tc
    assert len(rec["date"]) == len(rec["dw"]) == len(fz), (len(rec["date"]), len(rec["dw"]), len(fz))
    fz = fz.set_index("date")

    S = cross_sections(country, bundle, cell)
    dates = rec["date"]
    priced = {pd.Timestamp(dt): set(g["permno"]) for dt, g in bundle.cost_inputs.groupby("date")}
    cinp = bundle.cost_inputs
    okmask = (cinp[["spread", "sigma_d", "adv_usd"]].notna().all(axis=1)
              & np.isfinite(cinp[["spread", "sigma_d", "adv_usd"]]).all(axis=1)
              & (cinp["spread"] >= 0) & (cinp["sigma_d"] >= 0) & (cinp["adv_usd"] > 0))
    certified = {pd.Timestamp(dt): set(g["permno"]) for dt, g in cinp[okmask].groupby("date")}
    # Dprev is the pipeline ledger's holding of EVERY name as a fraction of NAV, including positions in
    # names that left the priced panel and were never traded out (they sit unchanged until re-priced).
    nav_start = np.concatenate([[float(aum)], fz["nav"].to_numpy(float)[:-1]])   # dollars at the start of each month
    out, Dprev = [], pd.Series(dtype=float)
    for j, date in enumerate(dates):
        Tcur = Tmap[date]
        Tprev = Tmap[dates[j - 1]] if j > 0 else pd.Series(dtype=float)
        St = S.get(date, pd.DataFrame(columns=["spread", "sigma_d", "adv_usd"]))
        Sp = S.get(dates[j - 1], pd.DataFrame(columns=["spread", "sigma_d", "adv_usd"])) if j > 0 else None
        idx, dw_rec = rec["idx"][j], rec["dw"][j]
        sp, sd, ad = rec["sp"][j], rec["sd"][j], rec["ad"][j]

        # reconstruction check of the drifted holdings against what the pipeline actually traded
        recon = Tcur.reindex(idx).fillna(0.0).to_numpy() - Dprev.reindex(idx).fillna(0.0).to_numpy()
        recon_err = float(np.max(np.abs(recon - dw_rec))) if dw_rec.size else 0.0

        row = {"country": country, "aum": aum, "book": book, "cell": cell, "date": date,
               "recon_drift_err": recon_err,
               "B_spread": float(fz.loc[date, "cost_spread"]), "B_impact": float(fz.loc[date, "cost_impact"]),
               "B_borrow": float(fz.loc[date, "cost_borrow"])}
        for d_, x_, b_ in itertools.product("AB", repeat=3):
            basis = Tprev if d_ == "A" else Dprev
            if x_ == "B":
                dw = Tcur.reindex(idx).fillna(0.0).to_numpy() - basis.reindex(idx).fillna(0.0).to_numpy()
                lin, imp = _parts(dw, sp, sd, ad, row.get("aum", aum), k, comm)
            else:
                names = St.index.intersection(Tcur.index.union(basis.index))
                dw = Tcur.reindex(names).fillna(0.0).to_numpy() - basis.reindex(names).fillna(0.0).to_numpy()
                z = St.loc[names]
                lin, imp = _parts(dw, z["spread"].to_numpy(), z["sigma_d"].to_numpy(),
                                  z["adv_usd"].to_numpy(), aum, k, comm)
                exits = Tprev.index.difference(St.index)          # Tier A's exit set: last month's targets
                if len(exits) and Sp is not None:
                    pin = Sp.reindex(exits)
                    okm = pin.notna().all(axis=1) & (pin["adv_usd"] > 0)
                    if okm.any():
                        l2, i2 = _parts(basis.reindex(exits).fillna(0.0)[okm].abs().to_numpy(), pin.loc[okm, "spread"].to_numpy(),
                                        pin.loc[okm, "sigma_d"].to_numpy(), pin.loc[okm, "adv_usd"].to_numpy(),
                                        aum, k, comm)
                        lin, imp = lin + l2, imp + i2
            bor = (BORROW_RATE / 12.0) * float(np.clip(-Tcur.to_numpy(), 0, None).sum()) if b_ == "B" else 0.0
            row[f"V{d_}{x_}{b_}_lin"], row[f"V{d_}{x_}{b_}_imp"], row[f"V{d_}{x_}{b_}_bor"] = lin, imp, bor
        # exit statistics (target-weight notional, Tier A's definition of an exit)
        exits_a = Tprev.index.difference(St.index)
        row["exit_notional_A"] = float(Tprev.reindex(exits_a).abs().sum())
        row["trade_notional_A"] = float((Tcur.reindex(Tcur.index.union(Tprev.index)).fillna(0.0)
                                         - Tprev.reindex(Tcur.index.union(Tprev.index)).fillna(0.0)).abs().sum())
        # why each Tier-A exit left the scored cross-section (target-weight notional)
        ex_abs = Tprev.reindex(exits_a).abs()
        cert_t, priced_t = certified.get(date, set()), priced.get(date, set())
        reason_norow = [p for p in exits_a if p not in priced_t]
        reason_uncert = [p for p in exits_a if p in priced_t and p not in cert_t]
        reason_elig = [p for p in exits_a if p in cert_t]
        row["exit_notional_norow"] = float(ex_abs.reindex(reason_norow).sum())
        row["exit_notional_uncertified"] = float(ex_abs.reindex(reason_uncert).sum())
        row["exit_notional_certified_unscored"] = float(ex_abs.reindex(reason_elig).sum())
        row["n_exits_A"] = int(len(exits_a))
        row["n_exits_charged_B"] = int(sum(1 for p in exits_a if p in set(idx)))
        out.append(row)

        # advance the ledger exactly as the pipeline does: names that are held or targeted AND priced are
        # traded to target and accrue (price return - dividend); unpriced held names are left untouched;
        # then every position is divided by (1 + gross), i.e. scaled by nav_next / (nav (1 + gross)).
        nav0 = nav_start[j]
        held = Dprev.index[Dprev.abs() * nav0 > 1e-8]           # the ledger's dollar threshold for "held"
        ia = pd.Index([p for p in Tcur.index.union(held) if p in priced.get(date, ())])
        ret = rets.reindex(pd.MultiIndex.from_product([[date], ia])).fillna(0.0).to_numpy()
        if divs is not None:
            dv = divs.reindex(pd.MultiIndex.from_product([[date], ia])).fillna(0.0).clip(lower=0.0).to_numpy()
        else:
            dv = np.full(len(ia), 0.02 / 12.0)
        fac = np.maximum(1.0 + ret - dv, 0.0)
        traded = pd.Series(Tcur.reindex(ia).fillna(0.0).to_numpy() * fac, index=ia)
        new = pd.concat([Dprev.drop(ia, errors="ignore"), traded])
        new = new[new.abs() * nav0 > 1e-10]                     # lots at or below 1e-10 dollars are pruned
        gross = float(fz.loc[date, "gross_ret"])
        Dprev = new / (1.0 + gross)
    return pd.DataFrame(out)


def stage_run(countries):
    from alphacomb.contracts import intl, load_config
    from alphacomb.tax import get_regime

    RES.mkdir(parents=True, exist_ok=True)
    cfg0 = load_config("base")
    zero = get_regime("tax_exempt")
    for country in countries:
        bundle = intl.load_country_bundle(country, max_names=600)
        tg = bundle.targets.set_index(["date", "permno"])
        tg.index = tg.index.set_levels(pd.to_datetime(tg.index.levels[0]), level=0)
        rets = tg["ret_next"]
        divs = tg["div_next"] if "div_next" in tg.columns else None
        frames = []
        for c, aum in [r for r in RUNGS if r[0] == country]:
            cfg = {**cfg0, "costs": {**cfg0["costs"], "aum_usd_2020": float(aum)}}
            for book in ("uncapped", "capped"):
                for cell in CELLS:
                    frames.append(run_cell(country, aum, book, cell, bundle, cfg, zero, rets, divs))
                print(f"{country} {aum:.0e} {book} done", flush=True)
                pd.concat(frames).to_csv(RES / f"parity_monthly_{country}.csv.gz", index=False)


def attribute(v):
    """Attribution of the Tier A -> Tier B cost change over the three switches D, X, B.

    ``v`` maps 'DXB' strings over {A,B} to the cost under that combination ('A' = Tier A convention).
    Returns (full, e, shapley, interaction): ``full = V(AAA) - V(BBB)``; ``e[m]`` the one-at-a-time effect of
    switching only m from B to A; the Shapley value of each switch over all 6 orderings (sums to ``full``);
    ``interaction = full - sum(e)``.
    """
    names = "DXB"
    full = v["AAA"] - v["BBB"]
    e = {m: v["".join("A" if n == m else "B" for n in names)] - v["BBB"] for m in names}
    sh = {}
    for m in names:
        tot = 0.0
        for perm in itertools.permutations(names):
            pre = perm[:perm.index(m)]
            s0 = "".join("A" if n in pre else "B" for n in names)
            s1 = "".join("A" if (n in pre or n == m) else "B" for n in names)
            tot += v[s1] - v[s0]
        sh[m] = tot / 6.0
    return full, e, sh, full - sum(e.values())


def annual(df, col):
    return 1200.0 * df.groupby("cell")[col].mean().mean()         # points per year (x12 x100), mean over cells


def stage_summarize():
    mon = pd.concat([pd.read_csv(RES / f"parity_monthly_{c}.csv.gz", parse_dates=["date"])
                     for c in ("DEU", "IND", "JPN") if (RES / f"parity_monthly_{c}.csv.gz").exists()])
    A = {c: pd.read_csv(CAP / "inputs" / f"monthly_{c}_cov.csv", parse_dates=["date"]) for c in ("DEU", "IND", "JPN")}
    B = {c: pd.read_csv(CAP / f"tierB_monthly_{c}.csv.gz", parse_dates=["date"]) for c in ("DEU", "IND", "JPN")}
    cov = {"DEU": 65.1, "IND": 99.1, "JPN": 99.8}
    rows, checks, lines = [], [], []
    for (country, aum), g in mon.groupby(["country", "aum"]):
        for book in ("uncapped", "capped"):
            h = g[g.book == book].copy()
            a = A[country]
            a = a[np.isclose(a.aum, aum)]
            gcol, ncol = ("gross_ret", "net_ret_uncapped") if book == "uncapped" else ("gross_ret_capped", "net_ret_capped")
            a = a.assign(costA=a[gcol] - a[ncol])[["date", "cell", "costA"]]
            b = B[country]
            b = b[np.isclose(b.aum, aum) & (b.book == book)][["date", "cell", "cost_total"]].rename(columns={"cost_total": "costB"})
            h = h.merge(a, on=["date", "cell"], how="left").merge(b, on=["date", "cell"], how="left")
            for d_, x_, b_ in itertools.product("AB", repeat=3):
                h[f"V{d_}{x_}{b_}"] = h[f"V{d_}{x_}{b_}_lin"] + h[f"V{d_}{x_}{b_}_imp"] + h[f"V{d_}{x_}{b_}_bor"]
            rep_a = float((h["VAAA"] - h["costA"]).abs().max())
            rep_b = float((h["VBBB"] - h["costB"]).abs().max())
            rep_b_raw = float((h["VBBB"] - (h["B_spread"] + h["B_impact"] + h["B_borrow"])).abs().max())
            drift_err = float(h["recon_drift_err"].max())
            costA, costB = annual(h, "costA"), annual(h, "costB")
            G = costB - costA
            v = {c: annual(h, f"V{c}") for c in COMBOS}
            full, e, sh, interaction = attribute(v)
            G_rep = -full                                          # replicated discrepancy, B minus A
            R = G - G_rep
            material = abs(G) > MATERIAL
            reconciled = abs(R) <= max(TOL_ABS, TOL_REL * abs(G))
            rec = {"country": country, "aum": aum, "book": book, "cost_A": costA, "cost_B": costB,
                   "discrepancy_B_minus_A": G, "replicated_B_minus_A": G_rep, "residual_R": R,
                   "material": material, "reconciled": reconciled,
                   "e_D": e["D"], "e_X": e["X"], "e_B": e["B"], "interaction": interaction,
                   "shap_D": sh["D"], "shap_X": sh["X"], "shap_B": sh["B"],
                   "rep_err_A_max": rep_a, "rep_err_B_max": rep_b, "rep_err_B_vs_recorded": rep_b_raw,
                   "drift_recon_err_max": drift_err,
                   "exit_share_of_trade_A": float(h["exit_notional_A"].sum() / max(h["trade_notional_A"].sum(), 1e-12)),
                   "exits_A_per_cellmonth": float(h["n_exits_A"].mean()),
                   "exits_charged_by_B_share": float(h["n_exits_charged_B"].sum() / max(h["n_exits_A"].sum(), 1)),
                   "exit_notional_share_norow": float(h["exit_notional_norow"].sum() / max(h["exit_notional_A"].sum(), 1e-12)),
                   "exit_notional_share_uncertified": float(h["exit_notional_uncertified"].sum() / max(h["exit_notional_A"].sum(), 1e-12)),
                   "exit_notional_share_certified_unscored": float(h["exit_notional_certified_unscored"].sum() / max(h["exit_notional_A"].sum(), 1e-12)),
                   "coverage_pct_country": cov[country]}
            for m in "DXB":
                full_eff = full if abs(full) > 1e-12 else np.nan
                rec[f"closure_{m}"] = (e[m] / full) if material and np.isfinite(full_eff) and abs(full) > MATERIAL else np.nan
            # component split of the replicated discrepancy
            for part in ("lin", "imp", "bor"):
                rec[f"split_{part}_B_minus_A"] = annual(h, f"VBBB_{part}") - annual(h, f"VAAA_{part}")
            rows.append(rec)
    d = pd.DataFrame(rows).sort_values(["country", "aum", "book"]).reset_index(drop=True)
    d.to_csv(RES / "parity_summary.csv", index=False)
    mat = d[d.material]
    verdict = {}
    for m in "DXB":
        n12 = int((d[f"closure_{m}"] >= 0.9).sum())
        nmat = int((mat[f"closure_{m}"] >= 0.9).sum())
        verdict[m] = (n12, nmat, len(mat))
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)
    with open(RES / "parity_report.txt", "w", encoding="utf-8") as fh:
        def P(s=""):
            print(s)
            fh.write(s + "\n")
        P("PAIRS (12): annual cost points; discrepancy = Tier B - Tier A")
        P(d[["country", "aum", "book", "cost_A", "cost_B", "discrepancy_B_minus_A", "replicated_B_minus_A",
             "residual_R", "material", "reconciled"]].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
        P("\nONE-AT-A-TIME EFFECTS (switch one convention to Tier A from Tier B; change in cost, points) and Shapley")
        P(d[["country", "aum", "book", "e_D", "e_X", "e_B", "interaction", "shap_D", "shap_X", "shap_B"]]
          .to_string(index=False, float_format=lambda x: f"{x:.3f}"))
        P("\nCLOSURE (one-at-a-time effect / replicated discrepancy; material pairs only)")
        P(d[["country", "aum", "book", "closure_D", "closure_X", "closure_B"]]
          .to_string(index=False, float_format=lambda x: f"{x:.2f}"))
        P("\nCOMPONENT SPLIT of replicated discrepancy (B - A): spread+commission, impact, borrow")
        P(d[["country", "aum", "book", "split_lin_B_minus_A", "split_imp_B_minus_A", "split_bor_B_minus_A"]]
          .to_string(index=False, float_format=lambda x: f"{x:.3f}"))
        P("\nREPLICATION CHECKS (max abs monthly, return units) and drift reconstruction")
        P(d[["country", "aum", "book", "rep_err_A_max", "rep_err_B_max", "rep_err_B_vs_recorded",
             "drift_recon_err_max"]].to_string(index=False, float_format=lambda x: f"{x:.2e}"))
        P("\nEXIT STATISTICS and coverage (descriptive; 3 countries, no causal claim)")
        P(d[["country", "aum", "book", "exit_share_of_trade_A", "exits_A_per_cellmonth",
             "exits_charged_by_B_share", "coverage_pct_country"]].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
        P("\nWHY TIER A EXITS LEFT THE CROSS-SECTION (share of exit notional)")
        P(d[["country", "aum", "book", "exit_notional_share_norow", "exit_notional_share_uncertified",
             "exit_notional_share_certified_unscored"]].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
        P("\nDECISION RULE: mechanism closes >=90% in >=10 of 12 pairs")
        for m, (n12, nmat, tot) in verdict.items():
            P(f"  {m}: {n12} of 12 pairs; {nmat} of {tot} material pairs")
        P(f"  material pairs: {len(mat)} of 12; reconciled pairs: {int(d.reconciled.sum())} of 12")
    write_manifest()


def write_manifest():
    import hashlib
    import json
    import subprocess

    def git(*a):
        try:
            return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
        except Exception:  # noqa: BLE001
            return "unavailable"
    files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(RES.glob("*")) if p.is_file() and p.name != "MANIFEST.json"}
    (RES / "MANIFEST.json").write_text(json.dumps({
        "purpose": "Cost-accounting parity diagnostic (docs/COST_PARITY_DIAGNOSTIC_SPEC_2026-10-10.md)",
        "git_head_when_written": git("rev-parse", "HEAD"),
        "git_dirty_when_written": bool(git("status", "--porcelain")),
        "python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__,
        "regeneration": {
            "parity_monthly_*.csv.gz": "python tools/diag_cost_parity.py --stage run --country C  (needs the frozen "
                                       "data/, stage-02 predictions and the git-ignored decile weights; not in git)",
            "dtv_support.csv": "python tools/diag_dtv_support.py  (same upstream requirements as the monthly files)",
            "summary_and_report":"python tools/diag_cost_parity.py --stage summarize  (tracked files only: these "
                                  "monthly files plus results/capacity_return_difference/)"},
        "sha256": files}, indent=2))


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["run", "summarize"], required=True)
    ap.add_argument("--country", nargs="+", default=["DEU", "IND", "JPN"])
    a = ap.parse_args(argv)
    RES.mkdir(parents=True, exist_ok=True)
    if a.stage == "run":
        stage_run(a.country)
    else:
        stage_summarize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
