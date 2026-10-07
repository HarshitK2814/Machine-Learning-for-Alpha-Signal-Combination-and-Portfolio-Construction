"""Certify actual EDGE plus Abdi--Ranaldo spread coverage after extraction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
PANEL = ROOT / "data" / "intl_c6" / "staging" / "C6_CERTIFIED_MONTHLY_DAILY_FEATURES.csv.gz"
EDGE = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_EDGE_21.csv.gz"
AR = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_ABDI_RANALDO_21.csv.gz"
OUT_CSV = ROOT / "data" / "intl_c6" / "audit" / "C6_ACTUAL_AR_COVERAGE_BY_COUNTRY_YEAR.csv"
OUT_JSON = ROOT / "data" / "intl_c6" / "audit" / "C6_ACTUAL_AR_COVERAGE_AUDIT.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize(group: pd.DataFrame) -> pd.Series:
    edge = group["edge_21_strict"].notna()
    ar = group["ar_21_strict"].notna()
    spread = edge | ar
    fallback = ~edge & ar
    complete = spread & group["sigma_d_21_strict"].notna() & group["adv_usd_21_strict"].notna()
    return pd.Series({
        "rows": int(len(group)),
        "edge_strict": int(edge.sum()),
        "ar_strict": int(ar.sum()),
        "ar_fallback_increment": int(fallback.sum()),
        "actual_spread_available": int(spread.sum()),
        "actual_spread_coverage": float(spread.mean()),
        "actual_complete_market_inputs": int(complete.sum()),
    })


def main() -> None:
    keys = ["country", "date", "permno"]
    panel = pd.read_csv(
        PANEL,
        usecols=keys + ["sigma_d_21_strict", "adv_usd_21_strict"],
        parse_dates=["date"],
        low_memory=False,
    )
    edge = pd.read_csv(EDGE, usecols=keys + ["edge_21_strict"], parse_dates=["date"])
    ar = pd.read_csv(AR, usecols=keys + ["ar_21_strict"], parse_dates=["date"])
    data = panel.merge(edge, on=keys, how="left", validate="one_to_one")
    data = data.merge(ar, on=keys, how="left", validate="one_to_one")
    if len(data) != 757_297 or data.duplicated(keys).any():
        raise RuntimeError("Actual AR coverage key contract failed")
    data["year"] = data["date"].dt.year

    by_country_year = (
        data.groupby(["country", "year"], sort=True)
        .apply(summarize, include_groups=False)
        .reset_index()
    )
    count_columns = [
        "rows", "edge_strict", "ar_strict", "ar_fallback_increment",
        "actual_spread_available", "actual_complete_market_inputs",
    ]
    by_country_year[count_columns] = by_country_year[count_columns].astype("int64")
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    by_country_year.to_csv(OUT_CSV, index=False)

    totals = summarize(data).to_dict()
    for column in count_columns:
        totals[column] = int(totals[column])
    totals["actual_spread_coverage"] = float(totals["actual_spread_coverage"])
    by_country_frame = (
        data.groupby("country", sort=True)
        .apply(summarize, include_groups=False)
        .reset_index()
    )
    by_country_frame[count_columns] = by_country_frame[count_columns].astype("int64")
    audit = {
        "verdict": "PASS_ACTUAL_ABDI_RANALDO_COVERAGE_CERTIFIED",
        "scope": "actual strict WRDS estimates; no projected eligibility and no imputation",
        "hierarchy": "EDGE strict first; Abdi--Ranaldo strict only where EDGE is null",
        "totals": totals,
        "by_country": by_country_frame.to_dict(orient="records"),
        "inputs": {
            "daily_features": {"path": str(PANEL.relative_to(ROOT)), "sha256": sha256(PANEL)},
            "edge": {"path": str(EDGE.relative_to(ROOT)), "sha256": sha256(EDGE)},
            "abdi_ranaldo": {"path": str(AR.relative_to(ROOT)), "sha256": sha256(AR)},
        },
        "output": {"path": str(OUT_CSV.relative_to(ROOT)), "sha256": sha256(OUT_CSV)},
        "production_written": False,
        "github_written": False,
    }
    OUT_JSON.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
