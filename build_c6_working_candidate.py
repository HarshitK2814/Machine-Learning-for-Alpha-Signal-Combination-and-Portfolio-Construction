"""Assemble the non-production C6 cost-input working candidate.

The build is deliberately nullable and fail-closed.  It never fabricates a
spread, ADV, volatility, or borrow fee.  EDGE is primary and the certified
Abdi--Ranaldo estimate is the fallback when its completed artefact is present.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
PANEL = ROOT / "data" / "intl_c6" / "staging" / "C6_CERTIFIED_MONTHLY_DAILY_FEATURES.csv.gz"
EDGE = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_EDGE_21.csv.gz"
AR = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_ABDI_RANALDO_21.csv.gz"
OUT_DIR = ROOT / "data" / "intl_c6" / "candidate_working"
OUT = OUT_DIR / "C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz"
AUDIT = OUT_DIR / "C6_COST_INPUTS_WORKING_AUDIT.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    panel = pd.read_csv(
        PANEL,
        usecols=[
            "country", "date", "permno", "sigma_d_21_strict",
            "adv_usd_21_strict", "return_obs_21", "volume_obs_21",
            "usd_per_local", "curcdd", "endpoint_date",
        ],
        parse_dates=["date", "endpoint_date"],
        low_memory=False,
    )
    edge = pd.read_csv(
        EDGE,
        usecols=["country", "date", "permno", "edge_21_min3", "edge_21_strict", "ohlc_complete_21"],
        parse_dates=["date"],
        low_memory=False,
    )
    out = panel.merge(edge, on=["country", "date", "permno"], how="left", validate="one_to_one")
    ar_complete = AR.exists()
    if ar_complete:
        ar = pd.read_csv(
            AR,
            usecols=["country", "date", "permno", "pair_obs_20", "ar_21_min3", "ar_21_strict"],
            parse_dates=["date"],
            low_memory=False,
        )
        out = out.merge(ar, on=["country", "date", "permno"], how="left", validate="one_to_one")
    else:
        out["pair_obs_20"] = np.nan
        out["ar_21_min3"] = np.nan
        out["ar_21_strict"] = np.nan

    out["spread"] = out["edge_21_strict"].combine_first(out["ar_21_strict"])
    out["spread_source"] = np.select(
        [out["edge_21_strict"].notna(), out["ar_21_strict"].notna()],
        ["EDGE_21_STRICT", "ABDI_RANALDO_21_STRICT"],
        default="MISSING",
    )
    out["sigma_d"] = out["sigma_d_21_strict"]
    out["adv_usd"] = out["adv_usd_21_strict"]
    out["borrow_fee"] = np.nan
    out["borrow_fee_source"] = "BLOCKED_NO_CERTIFIED_SECURITIES_LENDING_SOURCE"

    if len(out) != 757_297 or out.duplicated(["country", "date", "permno"]).any():
        raise RuntimeError("C6 candidate key contract failed")
    if (out[["spread", "sigma_d", "adv_usd"]].dropna() < 0).any().any():
        raise RuntimeError("Negative C6 market input")
    if out["borrow_fee"].notna().any():
        raise RuntimeError("Borrow fee must remain null until a certified source exists")

    columns = [
        "country", "date", "permno", "spread", "sigma_d", "adv_usd", "borrow_fee",
        "spread_source", "borrow_fee_source", "edge_21_strict", "ar_21_strict",
        "return_obs_21", "volume_obs_21", "ohlc_complete_21", "pair_obs_20",
        "usd_per_local", "curcdd", "endpoint_date",
    ]
    out = out.sort_values(["country", "date", "permno"], kind="stable")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out[columns].to_csv(OUT, index=False, compression="gzip")

    complete_market = out[["spread", "sigma_d", "adv_usd"]].notna().all(axis=1)
    complete_contract = complete_market & out["borrow_fee"].notna()
    by_country = []
    for country, g in out.groupby("country", sort=True):
        by_country.append({
            "country": country,
            "rows": int(len(g)),
            "spread_nonnull": int(g["spread"].notna().sum()),
            "spread_edge": int(g["spread_source"].eq("EDGE_21_STRICT").sum()),
            "spread_ar_fallback": int(g["spread_source"].eq("ABDI_RANALDO_21_STRICT").sum()),
            "sigma_d_nonnull": int(g["sigma_d"].notna().sum()),
            "adv_usd_nonnull": int(g["adv_usd"].notna().sum()),
            "market_inputs_complete": int(g[["spread", "sigma_d", "adv_usd"]].notna().all(axis=1).sum()),
            "borrow_fee_nonnull": int(g["borrow_fee"].notna().sum()),
        })
    blockers = []
    if not ar_complete:
        blockers.append("ABDI_RANALDO_EXTRACTION_INCOMPLETE")
    if out["spread"].isna().any():
        blockers.append("SPREAD_COVERAGE_INCOMPLETE")
    if out["sigma_d"].isna().any():
        blockers.append("SIGMA_21_STRICT_COVERAGE_INCOMPLETE")
    if out["adv_usd"].isna().any():
        blockers.append("ADV_USD_21_STRICT_COVERAGE_INCOMPLETE")
    blockers.append("BORROW_FEE_SOURCE_UNAVAILABLE")

    audit = {
        "verdict": "BLOCKED_NOT_READY_FOR_C6_PRODUCTION",
        "scope": "working candidate only; no production promotion",
        "rows": int(len(out)),
        "unique_investible_securities": int(out[["country", "permno"]].drop_duplicates().shape[0]),
        "spread_hierarchy": "EDGE 21-observation strict, else Abdi--Ranaldo 21-observation strict, else null",
        "ar_complete": ar_complete,
        "market_inputs_complete_rows": int(complete_market.sum()),
        "full_contract_complete_rows": int(complete_contract.sum()),
        "by_country": by_country,
        "blockers": blockers,
        "borrow_fee_policy": "null until genuine securities-lending/borrow-fee data are certified; short volume and disclosed short positions are not substitutes",
        "inputs": {
            "daily_features": {"path": str(PANEL.relative_to(ROOT)), "sha256": sha256(PANEL)},
            "edge": {"path": str(EDGE.relative_to(ROOT)), "sha256": sha256(EDGE)},
            "abdi_ranaldo": {"path": str(AR.relative_to(ROOT)), "sha256": sha256(AR)} if ar_complete else None,
        },
        "output": {"path": str(OUT.relative_to(ROOT)), "sha256": sha256(OUT)},
        "production_written": False,
        "github_written": False,
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
