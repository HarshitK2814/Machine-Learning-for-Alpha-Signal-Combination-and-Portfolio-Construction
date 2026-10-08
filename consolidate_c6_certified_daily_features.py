"""Consolidate the exact-key WRDS daily extracts and attach point-in-time USD FX.

This is a staging/certification build only.  It intentionally does not write into
any frozen or production C1--C6 path.  No FX value is interpolated or carried.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "data" / "intl_c6" / "cache" / "monthly_daily_features"
FX_PATH = ROOT / "data" / "intl_c6" / "cache" / "C6_WRDS_DAILY_FX_TO_USD.csv.gz"
MONTHS_PATH = ROOT / "data" / "intl_c6" / "staging" / "C1_INVESTIBLE_MONTHS.csv.gz"
OUT_PATH = ROOT / "data" / "intl_c6" / "staging" / "C6_CERTIFIED_MONTHLY_DAILY_FEATURES.csv.gz"
AUDIT_PATH = ROOT / "data" / "intl_c6" / "audit" / "C6_CERTIFIED_MONTHLY_DAILY_FEATURES_AUDIT.json"

LOCAL_COLUMNS = [
    "country", "date", "permno", "gvkey", "iid", "month_end",
    "endpoint_date", "month_first_date", "month_raw_rows", "month_close_rows",
    "month_volume_rows", "month_return_rows", "month_sum_cshtrd", "raw_obs_21",
    "return_obs_21", "volume_obs_21", "ohlc_obs_21", "sigma_total_21",
    "sigma_price_21", "adv_reported_21", "adv_qunit_21", "hl_range_21",
    "amihud_qunit_21", "max_gap_days_21", "prccd", "prcod", "prchd", "prcld",
    "cshtrd", "cshoc", "ajexdi", "trfd", "adjusted_price", "return_index",
    "curcdd", "qunit", "month_min_currency", "month_max_currency", "exchg",
    "fic", "isin", "sedol", "secstat", "prcstd", "monthly_source_date",
    "prccm", "cshtrm", "ajexm", "curcdm", "wrds_month_present",
    "query_elapsed_seconds",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def clean_key(series: pd.Series, width: int | None = None) -> pd.Series:
    out = series.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    if width is not None:
        out = out.str.zfill(width)
    return out


def main() -> None:
    annual = sorted(CACHE_DIR.glob("C6_WRDS_MONTHLY_DAILY_FEATURES_*.csv.gz"))
    if len(annual) != 31:
        raise RuntimeError(f"Expected 31 annual caches, found {len(annual)}")

    frames: list[pd.DataFrame] = []
    schemas: dict[str, int] = {}
    for path in annual:
        frame = pd.read_csv(path, low_memory=False)
        missing = sorted(set(LOCAL_COLUMNS) - set(frame.columns))
        if missing:
            raise RuntimeError(f"{path.name} lacks required local columns: {missing}")
        frames.append(frame.loc[:, LOCAL_COLUMNS])
        schemas[path.name] = len(frame.columns)
    panel = pd.concat(frames, ignore_index=True)

    panel["date"] = pd.to_datetime(panel["date"], errors="raise")
    panel["month_end"] = pd.to_datetime(panel["month_end"], errors="raise")
    panel["endpoint_date"] = pd.to_datetime(panel["endpoint_date"], errors="raise")
    panel["permno"] = pd.to_numeric(panel["permno"], errors="raise").astype("int64")
    panel["gvkey"] = clean_key(panel["gvkey"])
    panel["iid"] = clean_key(panel["iid"])
    panel["curcdd"] = clean_key(panel["curcdd"]).str.upper()

    months = pd.read_csv(MONTHS_PATH, low_memory=False)
    months["date"] = pd.to_datetime(months["date"], errors="raise")
    months["permno"] = pd.to_numeric(months["permno"], errors="raise").astype("int64")
    expected_keys = months[["country", "date", "permno"]].drop_duplicates()
    actual_keys = panel[["country", "date", "permno"]].drop_duplicates()
    key_check = expected_keys.merge(actual_keys, how="outer", indicator=True)
    missing_expected = int((key_check["_merge"] == "left_only").sum())
    unexpected = int((key_check["_merge"] == "right_only").sum())

    dup_rows = int(panel.duplicated(["country", "date", "permno"], keep=False).sum())
    if missing_expected or unexpected or dup_rows:
        raise RuntimeError(
            f"Key contract failed: missing={missing_expected}, unexpected={unexpected}, duplicates={dup_rows}"
        )

    fx = pd.read_csv(FX_PATH, low_memory=False)
    fx["datadate"] = pd.to_datetime(fx["datadate"], errors="raise")
    fx["currency"] = clean_key(fx["currency"]).str.upper()
    fx_dup = int(fx.duplicated(["datadate", "currency"], keep=False).sum())
    if fx_dup:
        raise RuntimeError(f"FX cache contains {fx_dup} duplicate date/currency rows")

    panel = panel.merge(
        fx.rename(columns={"datadate": "endpoint_date", "currency": "curcdd"}),
        on=["endpoint_date", "curcdd"],
        how="left",
        validate="many_to_one",
    )
    panel["adv_usd_21"] = panel["adv_qunit_21"] * panel["usd_per_local"]
    panel["amihud_usd_21"] = panel["amihud_qunit_21"] / panel["usd_per_local"]

    # Strict candidates require all 21 actual-price observations.  Less complete
    # windows remain visible in the raw metrics but are not certified candidates.
    panel["sigma_d_21_strict"] = panel["sigma_total_21"].where(panel["return_obs_21"] == 21)
    panel["adv_usd_21_strict"] = panel["adv_usd_21"].where(panel["volume_obs_21"] == 21)
    panel["ohlc_range_21_strict_diagnostic"] = panel["hl_range_21"].where(panel["ohlc_obs_21"] == 21)

    panel = panel.sort_values(["country", "date", "permno"], kind="stable").reset_index(drop=True)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT_PATH, index=False, compression="gzip")

    endpoint_fx_missing = panel["usd_per_local"].isna()
    currencies = (
        panel.groupby(["country", "curcdd"], dropna=False)
        .size().rename("rows").reset_index().to_dict("records")
    )
    coverage = []
    for country, group in panel.groupby("country", sort=True):
        coverage.append({
            "country": country,
            "rows": int(len(group)),
            "sigma_strict_nonnull": int(group["sigma_d_21_strict"].notna().sum()),
            "adv_usd_any_nonnull": int(group["adv_usd_21"].notna().sum()),
            "adv_usd_strict_nonnull": int(group["adv_usd_21_strict"].notna().sum()),
            "ohlc_strict_diagnostic_nonnull": int(group["ohlc_range_21_strict_diagnostic"].notna().sum()),
            "endpoint_fx_missing": int(group["usd_per_local"].isna().sum()),
        })

    audit = {
        "status": "PASS_CERTIFIED_STAGING_CONSOLIDATION" if not endpoint_fx_missing.any() else "PASS_WITH_EXPLICIT_ENDPOINT_FX_GAPS",
        "scope": "staging/certification only; no production promotion",
        "rows": int(len(panel)),
        "unique_securities": int(panel[["country", "permno"]].drop_duplicates().shape[0]),
        "expected_rows": int(len(expected_keys)),
        "missing_expected_keys": missing_expected,
        "unexpected_keys": unexpected,
        "duplicate_contract_rows": dup_rows,
        "endpoint_fx_missing_rows": int(endpoint_fx_missing.sum()),
        "endpoint_fx_missing_examples": panel.loc[
            endpoint_fx_missing, ["country", "date", "permno", "endpoint_date", "curcdd"]
        ].head(25).astype(str).to_dict("records"),
        "fx_rule": "USD per local at the exact WRDS endpoint date; no interpolation or carry-forward performed by this build",
        "adv_rule": "mean(prccd*cshtrd/qunit) over last 21 actual-price rows, converted with endpoint-date USD-per-local FX",
        "strict_rule": "candidate populated only when all 21 relevant observations exist",
        "ohlc_range_status": "diagnostic_only_not_an_approved_effective_spread_estimator",
        "currencies": currencies,
        "coverage": coverage,
        "annual_cache_schema_column_counts": schemas,
        "inputs": {
            "c1_investible_months": {"path": str(MONTHS_PATH.relative_to(ROOT)), "sha256": sha256(MONTHS_PATH)},
            "daily_fx": {"path": str(FX_PATH.relative_to(ROOT)), "sha256": sha256(FX_PATH)},
            "annual_caches": [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in annual],
        },
        "output": {"path": str(OUT_PATH.relative_to(ROOT)), "sha256": sha256(OUT_PATH)},
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: audit[k] for k in ["status", "rows", "unique_securities", "endpoint_fx_missing_rows", "coverage"]}, indent=2))


if __name__ == "__main__":
    main()
