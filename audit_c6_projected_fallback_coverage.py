"""Project the conservative coverage gain from the pending AR extraction.

This is a local eligibility audit, not a substitute for computing the Abdi--
Ranaldo estimates.  It uses already-certified rolling observation counts to
identify windows that necessarily contain the 21 positive, same-currency
close/high/low observations required by the strict estimator.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
PANEL = ROOT / "data" / "intl_c6" / "staging" / "C6_CERTIFIED_MONTHLY_DAILY_FEATURES.csv.gz"
EDGE = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_EDGE_21.csv.gz"
AR = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_ABDI_RANALDO_21.csv.gz"
ACTUAL_AUDIT = ROOT / "data" / "intl_c6" / "audit" / "C6_ACTUAL_AR_COVERAGE_AUDIT.json"
OUT_CSV = ROOT / "data" / "intl_c6" / "audit" / "C6_PROJECTED_AR_COVERAGE_BY_COUNTRY_YEAR.csv"
OUT_JSON = ROOT / "data" / "intl_c6" / "audit" / "C6_PROJECTED_AR_COVERAGE_AUDIT.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    keys = ["country", "date", "permno"]
    panel = pd.read_csv(
        PANEL,
        usecols=keys + [
            "raw_obs_21", "return_obs_21", "ohlc_obs_21",
            "sigma_d_21_strict", "adv_usd_21_strict",
        ],
        parse_dates=["date"],
        low_memory=False,
    )
    edge = pd.read_csv(EDGE, usecols=keys + ["edge_21_strict"], parse_dates=["date"], low_memory=False)
    data = panel.merge(edge, on=keys, how="left", validate="one_to_one")
    if len(data) != 757_297 or data.duplicated(keys).any():
        raise RuntimeError("C6 projection key contract failed")

    # return_obs==21 is a conservative close/currency condition because the
    # certified return is only defined for positive adjacent return indices in
    # the same currency.  ohlc_obs==21 supplies all 21 high/low pairs.
    data["ar_strict_eligible_conservative"] = (
        data["raw_obs_21"].eq(21)
        & data["return_obs_21"].eq(21)
        & data["ohlc_obs_21"].eq(21)
    )
    data["edge_strict"] = data["edge_21_strict"].notna()
    data["projected_spread_available_lower_bound"] = data["edge_strict"] | data["ar_strict_eligible_conservative"]
    data["projected_complete_market_inputs_lower_bound"] = (
        data["projected_spread_available_lower_bound"]
        & data["sigma_d_21_strict"].notna()
        & data["adv_usd_21_strict"].notna()
    )
    data["year"] = data["date"].dt.year

    def summarize(g: pd.DataFrame) -> pd.Series:
        eligible = g["ar_strict_eligible_conservative"]
        edge_ok = g["edge_strict"]
        projected = g["projected_spread_available_lower_bound"]
        return pd.Series({
            "rows": len(g),
            "edge_strict": int(edge_ok.sum()),
            "ar_strict_eligible_conservative": int(eligible.sum()),
            "projected_ar_increment_lower_bound": int((eligible & ~edge_ok).sum()),
            "projected_spread_available_lower_bound": int(projected.sum()),
            "projected_spread_coverage_lower_bound": float(projected.mean()),
            "sigma_strict": int(g["sigma_d_21_strict"].notna().sum()),
            "adv_usd_strict": int(g["adv_usd_21_strict"].notna().sum()),
            "projected_complete_market_inputs_lower_bound": int(g["projected_complete_market_inputs_lower_bound"].sum()),
        })

    by_country_year = data.groupby(["country", "year"], sort=True).apply(summarize, include_groups=False).reset_index()
    count_columns = [
        "rows", "edge_strict", "ar_strict_eligible_conservative",
        "projected_ar_increment_lower_bound", "projected_spread_available_lower_bound",
        "sigma_strict", "adv_usd_strict", "projected_complete_market_inputs_lower_bound",
    ]
    by_country_year[count_columns] = by_country_year[count_columns].astype("int64")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    by_country_year.to_csv(OUT_CSV, index=False)

    totals = summarize(data).to_dict()
    for column in count_columns:
        totals[column] = int(totals[column])
    totals["projected_spread_coverage_lower_bound"] = float(totals["projected_spread_coverage_lower_bound"])
    by_country_frame = data.groupby("country", sort=True).apply(summarize, include_groups=False).reset_index()
    by_country_frame[count_columns] = by_country_frame[count_columns].astype("int64")
    by_country = by_country_frame.to_dict(orient="records")
    actual_available = AR.exists() and ACTUAL_AUDIT.exists()
    audit = {
        "verdict": (
            "PASS_HISTORICAL_PROJECTION__SUPERSEDED_BY_ACTUAL_EXTRACTION"
            if actual_available
            else "PASS_LOCAL_AR_COVERAGE_PROJECTION__EXTRACTION_STILL_REQUIRED"
        ),
        "scope": (
            "historical eligibility lower bound retained for audit; actual WRDS coverage is authoritative"
            if actual_available
            else "eligibility lower bound from certified local observation counts; no spread values imputed"
        ),
        "eligibility_rule": "raw_obs_21=21 and return_obs_21=21 and ohlc_obs_21=21",
        "interpretation": "sufficient but not necessary for 20 same-currency Abdi--Ranaldo pair moments; actual WRDS extraction may cover additional windows",
        "actual_coverage_audit": (
            str(ACTUAL_AUDIT.relative_to(ROOT)) if actual_available else None
        ),
        "totals": totals,
        "by_country": by_country,
        "inputs": {
            "daily_features": {"path": str(PANEL.relative_to(ROOT)), "sha256": sha256(PANEL)},
            "edge": {"path": str(EDGE.relative_to(ROOT)), "sha256": sha256(EDGE)},
        },
        "output": {"path": str(OUT_CSV.relative_to(ROOT)), "sha256": sha256(OUT_CSV)},
        "production_written": False,
        "github_written": False,
    }
    OUT_JSON.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
