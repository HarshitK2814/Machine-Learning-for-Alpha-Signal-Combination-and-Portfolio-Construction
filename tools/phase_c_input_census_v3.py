#!/usr/bin/env python
"""Phase C outcome-free SUPPORT census, v3 (corrects the classification used by v2).

v2 treated "no C6 row" as a panel exit. Corrected rules (user ruling 2026-10-14), applied here by MEMBERSHIP / FLAG
simulation only:

  * held name, C4 row present with a usable ``ret_next`` and ``div_next``, but no C6 row / not in the C1 universe /
    C6 inputs not certified -> HELD-BUT-UNTRADEABLE ("frozen"): drifted holding preserved, no discretionary trade,
    no new position until certification returns. Absence of C6 inputs alone creates no exit, no missing valuation and
    no unsupported cost for a trade that was never made.
  * held name with NO C4 row at the date -> UNRESOLVED (sticky) unless approved terminal-event evidence exists; none
    exists in C1/C4/C6, so none is applied. A later reappearance does not resolve it and nothing is closed at an old value.
  * held name whose ``ret_next`` is unavailable -> UNRESOLVED (never filled with zero).
  * missing ``div_next`` on an exposed name -> dividend/tax month unsupported under the frozen fail-closed rule.

Fields accessed (nothing else is ever loaded) -- values are reduced to presence flags at load time and discarded:
  C1 universe : date, permno, in_universe
  C4 targets  : date, permno ; ret_next, div_next -> flag ``is finite`` only
  C6 inputs   : country, date, permno ; spread, sigma_d, adv_usd -> flag ``certified`` only, with the engine's own
                predicate (eligible_cost_input_permnos): present, finite, spread>=0, sigma_d>=0, adv_usd>0
  weights     : date, permno, w   (w only through the test ``w != 0``)
No numerical return, price, dividend, cost, tax, NAV or performance value is printed, summarised or written.

    python tools/phase_c_input_census_v3.py --out results/phase_c_census_v3_2026-10-14
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
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
WINDOW = (pd.Timestamp("2009-01-01"), pd.Timestamp("2019-12-31"))
COUNTRIES = ["DEU", "IND", "JPN"]
FORBIDDEN_COLUMNS = {"r_1m", "r_3m", "r_6m", "r_12m", "price", "me", "borrow_fee", "usd_per_local", "edge_21_strict",
                     "ar_21_strict", "return_obs_21", "volume_obs_21", "endpoint_date", "nav", "net_ret", "gross_ret"}
STRUCTURAL = {
    "C1 universe": ["date", "permno", "in_universe"],
    "C4 targets": ["date", "permno"],
    "C6 cost inputs": ["country", "date", "permno"],
    "weights": ["date", "permno", "w"],
}
PRESENCE_ONLY = {   # columns whose values are reduced to a boolean at load time
    "C4 targets": {"ret_next": "isfinite", "div_next": "isfinite"},
    "C6 cost inputs": {"spread": "certified: finite and >= 0", "sigma_d": "certified: finite and >= 0",
                       "adv_usd": "certified: finite and > 0"},
}
ALLOWED_PROJECTION = ({c for v in STRUCTURAL.values() for c in v}
                      | {c for v in PRESENCE_ONLY.values() for c in v})
TIERS = ["0%", "(0,5%]", "(5%,25%]", ">25%"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tier(x: float) -> str:
    return "0%" if x == 0 else "(0,5%]" if x <= 0.05 else "(5%,25%]" if x <= 0.25 else ">25%"


def _month(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s).dt.to_period("M")


def c4_flags(frame: pd.DataFrame) -> pd.DataFrame:
    """date, permno, ret_next, div_next -> month, permno, ret_ok, div_ok (booleans); values are dropped here."""
    return pd.DataFrame({"month": _month(frame["date"]), "permno": frame["permno"].to_numpy(),
                         "ret_ok": np.isfinite(frame["ret_next"].to_numpy(dtype=float)),
                         "div_ok": np.isfinite(frame["div_next"].to_numpy(dtype=float))})


def c6_flags(frame: pd.DataFrame) -> pd.DataFrame:
    """country, date, permno, spread, sigma_d, adv_usd -> country, month, permno, cert (boolean)."""
    s, v, a = (frame[c].to_numpy(dtype=float) for c in ("spread", "sigma_d", "adv_usd"))
    with np.errstate(invalid="ignore"):
        cert = np.isfinite(s) & np.isfinite(v) & np.isfinite(a) & (s >= 0) & (v >= 0) & (a > 0)
    return pd.DataFrame({"country": frame["country"].to_numpy(), "month": _month(frame["date"]),
                         "permno": frame["permno"].to_numpy(), "cert": cert})


def simulate_series(months: list, targets: dict, c4_row: dict, c4_ret: dict, c4_div: dict,
                    c1_in: dict, c6_row: dict, c6_cert: dict) -> pd.DataFrame:
    """Membership/flag simulation of one weight series. All arguments are dicts month -> set of permnos
    (``targets``: names with w != 0). Returns one row per month. No value is read."""
    carried: set = set()          # post-trade book of the previous month, excluding unresolved names
    unresolved: dict = {}         # permno -> reason (sticky)
    ever_reappeared: set = set()
    rows = []
    E = set()
    for m in months:
        tgt = targets.get(m, E)
        row4, ret4, div4 = c4_row.get(m, E), c4_ret.get(m, E), c4_div.get(m, E)
        in1, row6, cert6 = c1_in.get(m, E), c6_row.get(m, E), c6_cert.get(m, E)
        new_absent = new_noret = 0
        # (1) names carried in from last month: valuation support at this date
        frozen_nc6, frozen_unc = set(), set()
        for p in carried:
            if p not in row4:
                unresolved[p] = "absent_from_c4"; new_absent += 1
            elif p not in ret4:
                unresolved[p] = "ret_next_missing"; new_noret += 1
            elif p not in row6 or p not in in1:
                frozen_nc6.add(p)
            elif p not in cert6:
                frozen_unc.add(p)
        # (2) target names: need a C4 row and a usable return to be held over the month
        for p in tgt:
            if p in unresolved or p in carried:
                continue
            if p not in row4:
                unresolved[p] = "target_absent_from_c4"; new_absent += 1
            elif p not in ret4:
                unresolved[p] = "target_ret_next_missing"; new_noret += 1
        ever_reappeared |= {p for p, why in unresolved.items() if why.endswith("absent_from_c4") and p in row4}
        frozen = frozen_nc6 | frozen_unc
        live_targets = {p for p in tgt if p not in unresolved}
        book = live_targets | frozen
        # cost support: a trade is made in a name that is a live target, not frozen, and not already held;
        # that trade needs certified inputs. Held names kept at drift need none.
        entries = live_targets - carried - frozen
        cost_gap = {p for p in entries if p not in cert6}
        div_gap = {p for p in book if p not in div4}
        live_book = {p for p in book if p in row4}
        rows.append({
            "n_targets": len(tgt), "n_carried_in": len(carried), "n_frozen_no_c6_or_c1": len(frozen_nc6),
            "n_frozen_uncertified": len(frozen_unc),
            "n_new_unresolved_absent_from_c4": new_absent, "n_new_unresolved_ret_missing": new_noret,
            "n_unresolved_cumulative": len(unresolved),
            "n_entries_without_certified_cost_inputs": len(cost_gap),
            "n_exposed_without_div_next": len(div_gap & live_book),
            "valuation_unresolved": len(unresolved) > 0,
            "cost_unsupported": len(cost_gap) > 0,
            "dividend_unsupported": len(div_gap & live_book) > 0,
        })
        carried = book
        carried -= set(unresolved)
    out = pd.DataFrame(rows)
    out.insert(0, "month", [str(m) for m in months])
    out.attrs["n_reappeared_unresolved"] = len(ever_reappeared)
    out.attrs["distinct_unresolved"] = len(unresolved)
    out.attrs["distinct_reasons"] = dict(pd.Series(list(unresolved.values()), dtype=object).value_counts())
    return out


def metric_shares(sim: pd.DataFrame) -> dict:
    """Per-metric unsupported share: union of the months that affect the metric, counted once (addendum 1)."""
    n = len(sim)
    v, c, d = (sim[k].to_numpy(bool) for k in ("valuation_unresolved", "cost_unsupported", "dividend_unsupported"))
    return {"share_gross_valuation": float(v.sum() / n), "share_net_valuation_or_cost": float((v | c).sum() / n),
            "share_after_tax_valuation_cost_or_tax": float((v | c | d).sum() / n)}


def run_census(ROOT: Path, out: Path, command: str = "") -> None:
    if out.exists():
        sys.exit(f"refusing to overwrite existing {out}")
    assert not ALLOWED_PROJECTION & FORBIDDEN_COLUMNS, "whitelist overlaps forbidden outcome columns"
    out.mkdir(parents=True)
    lo, hi = WINDOW[0].to_period("M"), WINDOW[1].to_period("M")

    c6_path = ROOT / "data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz"
    c6_cols = STRUCTURAL["C6 cost inputs"] + list(PRESENCE_ONLY["C6 cost inputs"])
    c6 = c6_flags(pd.read_csv(c6_path, usecols=c6_cols, parse_dates=["date"]))
    inputs = {str(c6_path.relative_to(ROOT)): sha(c6_path)}

    series_rows, month_frames, cov_rows, crosstabs, positions = [], [], [], [], []
    for ctry in COUNTRIES:
        p1 = ROOT / f"data/intl_c1/production/{ctry}/universe.parquet"
        p4 = ROOT / f"data/intl_c4/production/{ctry}/targets.parquet"
        for p in (p1, p4):
            inputs[str(p.relative_to(ROOT))] = sha(p)
        u = pq.read_table(p1, columns=STRUCTURAL["C1 universe"]).to_pandas()
        u = pd.DataFrame({"month": _month(u["date"]), "permno": u["permno"], "ins": u["in_universe"].astype(bool)})
        t4 = c4_flags(pq.read_table(p4, columns=STRUCTURAL["C4 targets"] + list(PRESENCE_ONLY["C4 targets"])).to_pandas())
        sets = lambda df, col=None: {m: set(g["permno"][g[col]] if col else g["permno"]) for m, g in df.groupby("month")}
        c4_row, c4_ret, c4_div = sets(t4), sets(t4, "ret_ok"), sets(t4, "div_ok")
        c1_in = sets(u, "ins")
        cc = c6[c6["country"] == ctry]
        c6_row, c6_cert = sets(cc), sets(cc, "cert")
        for m in sorted(c4_row):
            if lo <= m <= hi:
                cov_rows.append({"country": ctry, "month": str(m), "c4_rows": len(c4_row[m]),
                                 "c4_ret_next_usable": len(c4_ret.get(m, ())), "c4_div_next_usable": len(c4_div.get(m, ())),
                                 "c4_with_c6_row": len(c4_row[m] & c6_row.get(m, set())),
                                 "c4_with_certified_c6": len(c4_row[m] & c6_cert.get(m, set())),
                                 "c4_in_c1_universe": len(c4_row[m] & c1_in.get(m, set()))})
        # flag crosstab over ALL C4 rows in the window: counts only (which flag combinations occur)
        x = t4.merge(u[["month", "permno", "ins"]], how="left", on=["month", "permno"]).merge(
            cc[["month", "permno", "cert"]].assign(c6=True), how="left", on=["month", "permno"])
        x = x[(x["month"] >= lo) & (x["month"] <= hi)]
        x = x.assign(in_c1_universe=x["ins"].eq(True), has_c6_row=x["c6"].eq(True),
                     c6_certified=x["cert"].eq(True))
        ct = (x.groupby(["in_c1_universe", "has_c6_row", "c6_certified", "ret_ok", "div_ok"]).size()
              .rename("n_c4_rows").reset_index())
        ct.insert(0, "country", ctry)
        crosstabs.append(ct)
        # where do unusable ret_next flags sit in a name's life? (positions only; NOT interpreted as delisting)
        ti = t4.assign(mi=pd.PeriodIndex(t4["month"]).asi8)
        last_c4 = ti.groupby("permno")["mi"].max()
        later_ok = ti[ti["ret_ok"]].groupby("permno")["mi"].max()
        bad = ti[(~ti["ret_ok"]) & (t4["month"] >= lo) & (t4["month"] <= hi)].copy()
        bad["is_last_c4_row_of_name"] = (bad["mi"] == bad["permno"].map(last_c4)).to_numpy()
        bad["later_usable_ret_exists"] = (bad["permno"].map(later_ok).fillna(-1) > bad["mi"]).to_numpy()
        pos = (bad.groupby(["is_last_c4_row_of_name", "later_usable_ret_exists"]).size()
               .rename("n_c4_rows_with_unusable_ret_next").reset_index())
        pos.insert(0, "country", ctry)
        positions.append(pos)
        for adir in sorted((ROOT / "outputs/decile_weights" / ctry / "tierb").glob("aum_*")):
            aum = float(adir.name.split("_", 1)[1])
            for wp in sorted(adir.glob("*.parquet")):
                book, cell = wp.stem.split("_", 1)
                inputs[str(wp.relative_to(ROOT))] = sha(wp)
                w = pq.read_table(wp, columns=STRUCTURAL["weights"]).to_pandas()
                w = w[w["w"].to_numpy() != 0.0][["date", "permno"]]
                w["month"] = _month(w["date"])
                w = w[(w["month"] >= lo) & (w["month"] <= hi)]
                targets = {m: set(g["permno"]) for m, g in w.groupby("month")}
                months = sorted(targets)
                sim = simulate_series(months, targets, c4_row, c4_ret, c4_div, c1_in, c6_row, c6_cert)
                sh = metric_shares(sim)
                first = sim.loc[sim["valuation_unresolved"], "month"]
                key = dict(country=ctry, aum=aum, book=book, cell=cell)
                m2 = sim.assign(**key)
                month_frames.append(m2)
                series_rows.append({
                    **key, "months_with_weights": len(sim),
                    "first_unresolved_month": first.iloc[0] if len(first) else "",
                    "months_valuation_unresolved": int(sim["valuation_unresolved"].sum()),
                    "months_cost_unsupported": int(sim["cost_unsupported"].sum()),
                    "months_dividend_unsupported": int(sim["dividend_unsupported"].sum()),
                    **{k: round(v, 4) for k, v in sh.items()},
                    **{"tier_" + k.removeprefix("share_"): tier(v) for k, v in sh.items()},
                    "max_frozen_names": int((sim["n_frozen_no_c6_or_c1"] + sim["n_frozen_uncertified"]).max()),
                    "distinct_names_unresolved": sim.attrs["distinct_unresolved"],
                    "unresolved_names_that_later_reappear_in_c4": sim.attrs["n_reappeared_unresolved"],
                    "reason_absent_from_c4": int(sum(v for k, v in sim.attrs["distinct_reasons"].items() if "absent" in k)),
                    "reason_ret_next_missing": int(sum(v for k, v in sim.attrs["distinct_reasons"].items() if "ret_next" in k))})
    series = pd.DataFrame(series_rows)
    months_df = pd.concat(month_frames, ignore_index=True)
    series.to_csv(out / "support_by_series.csv", index=False)
    months_df.to_csv(out / "support_by_series_month.csv", index=False)
    pd.DataFrame(cov_rows).to_csv(out / "input_coverage_by_country_month.csv", index=False)
    pd.concat(crosstabs, ignore_index=True).to_csv(out / "c4_support_flag_crosstab.csv", index=False)
    pd.concat(positions, ignore_index=True).to_csv(out / "c4_unusable_ret_next_position.csv", index=False)
    tcols = [c for c in series.columns if c.startswith("tier_")]
    tiers = (series.melt(id_vars=["country"], value_vars=tcols, var_name="metric", value_name="tier")
             .groupby(["country", "metric", "tier"]).size().rename("n_series").reset_index())
    tiers.to_csv(out / "tier_counts_by_metric.csv", index=False)

    scan = {"terminal_event_fields_found": [], "fields_scanned": {
        "C1": pq.read_schema(ROOT / "data/intl_c1/production/DEU/universe.parquet").names,
        "C4": pq.read_schema(ROOT / "data/intl_c4/production/DEU/targets.parquet").names,
        "C6": pd.read_csv(c6_path, nrows=0).columns.tolist()}}
    names = [n.lower() for v in scan["fields_scanned"].values() for n in v]
    scan["terminal_event_fields_found"] = [n for n in names if any(k in n for k in ("delist", "terminal", "dlst", "event", "exit"))]
    (out / "terminal_event_field_scan.json").write_text(json.dumps(scan, indent=2))

    manifest = {
        "label": "OUTCOME-FREE SUPPORT CENSUS v3 - not a result; revised analysis, not confirmatory",
        "supersedes": "results/phase_c_census_v2_2026-10-14 (C6-lapse treated as exit); v1 and v2 kept as historical artifacts",
        "command": command,
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip(),
        "git_dirty_script": bool(subprocess.run(["git", "status", "--porcelain", "--", "tools/phase_c_input_census_v3.py"],
                                                cwd=ROOT, capture_output=True, text=True).stdout.strip()),
        "window": [str(WINDOW[0].date()), str(WINDOW[1].date())],
        "structural_columns_accessed": STRUCTURAL,
        "presence_only_columns_accessed": PRESENCE_ONLY,
        "presence_only_meaning": "values are converted to a boolean at load time (c4_flags/c6_flags) and are never stored, printed or aggregated",
        "values_not_read": "price levels, market equity, borrow fee, FX, any cost/tax/NAV/Sharpe/performance value; r_1m..r_12m",
        "rules": {
            "held_but_untradeable": "C4 row with usable ret_next, but no C6 row / not in C1 universe / C6 inputs not certified: carried at drift, no trade",
            "unresolved": "held or target name with no C4 row, or with ret_next unusable; sticky; no terminal-event evidence exists in C1/C4/C6",
            "dividend": "exposed name with unusable div_next -> dividend month unsupported (frozen fail-closed primary rule)",
            "cost": "only an ENTRY (live target, not carried, not frozen) needs certified C6 inputs; holding at drift needs none",
            "metric_masks": "gross: valuation; net: valuation U cost; after-tax: valuation U cost U dividend; union per metric counted once per month",
        },
        "definition_held": "weights-file row with w != 0 (identifier test only); later carried names are simulated from membership",
        "limitations": [
            "membership simulation, not the engine: the optimiser's trades and the exact book after rebalancing are not replicated",
            "a carried name that is tradeable and not a target is assumed sold this month; a frozen name is assumed carried",
            "ret_next usability is a finiteness flag; whether the CRSP-style terminal return is correct is not assessed",
            "the shipped engine (carry_v1, f201f9c) still treats a missing C6 row as a panel exit; this census applies the corrected rule the engine does not yet implement"],
        "pandas": pd.__version__, "numpy": np.__version__,
        "input_sha256": inputs,
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print("done", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out) if Path(a.out).is_absolute() else ROOT / a.out
    run_census(ROOT, out, command="python tools/phase_c_input_census_v3.py " + " ".join(sys.argv[1:]))


if __name__ == "__main__":
    main()
