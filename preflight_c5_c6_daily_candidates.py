"""Mechanical preflight for the non-production daily C5/C6 candidates.

This script does not promote data.  It independently checks the candidate
keys, C5 lag/no-look-ahead identities, C6 source hierarchy, certified daily
feature identities, economic ranges, and the fail-closed borrow-fee policy.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
C5_DAILY = ROOT / "data" / "intl_c5" / "candidate_daily_market_working" / "C5_DAILY_MARKET_WORKING_CANDIDATE.csv"
C5_FULL = ROOT / "data" / "intl_c5" / "candidate_daily_market_working" / "C5_FULL_WORKING_CANDIDATE.csv"
C5_EXTERNAL = ROOT / "data" / "intl_c5" / "candidate_external_c5_working" / "C5_EXTERNAL_WORKING_CANDIDATE.csv"
C6 = ROOT / "data" / "intl_c6" / "candidate_working" / "C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz"
DAILY = ROOT / "data" / "intl_c6" / "staging" / "C6_CERTIFIED_MONTHLY_DAILY_FEATURES.csv.gz"
EDGE = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_EDGE_21.csv.gz"
AR = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_ABDI_RANALDO_21.csv.gz"
ENTITLEMENT = ROOT / "data" / "intl_c6" / "audit" / "WRDS_C6_ENTITLEMENT_SCHEMA_PROBE.json"
SIGMA_RESOLUTION = ROOT / "data" / "intl_c6" / "audit" / "C6_SIGMA_OUTLIER_RESOLUTION.json"
WORKSTREAM_B_COST_CONSUMER = ROOT / "src" / "alphacomb" / "portfolio" / "cost_terms.py"
OUT_JSON = ROOT / "data" / "intl_c6" / "audit" / "C5_C6_DAILY_PREFLIGHT.json"
OUT_CSV = ROOT / "data" / "intl_c6" / "audit" / "C5_C6_DAILY_PREFLIGHT_CHECKS.csv"
OUT_OUTLIERS = ROOT / "data" / "intl_c6" / "audit" / "C6_DAILY_ECONOMIC_OUTLIERS.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def max_abs_difference(left: pd.Series, right: pd.Series) -> float:
    common = left.notna() & right.notna()
    if not common.any():
        return 0.0
    return float((left[common] - right[common]).abs().max())


def numeric_series_match(left: pd.Series, right: pd.Series, *, atol: float, rtol: float) -> bool:
    if not left.isna().equals(right.isna()):
        return False
    common = left.notna() & right.notna()
    return bool(np.isclose(left[common], right[common], atol=atol, rtol=rtol).all())


def quantiles(series: pd.Series) -> dict[str, float | int | None]:
    x = pd.to_numeric(series, errors="coerce").dropna()
    if x.empty:
        return {"n": 0, "min": None, "p01": None, "p50": None, "p99": None, "max": None}
    q = x.quantile([0.01, 0.50, 0.99])
    return {
        "n": int(len(x)),
        "min": float(x.min()),
        "p01": float(q.loc[0.01]),
        "p50": float(q.loc[0.50]),
        "p99": float(q.loc[0.99]),
        "max": float(x.max()),
    }


def main() -> None:
    required = [C5_DAILY, C5_FULL, C5_EXTERNAL, C6, DAILY, EDGE, ENTITLEMENT, SIGMA_RESOLUTION, WORKSTREAM_B_COST_CONSUMER]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Required preflight inputs missing: {missing}")

    checks: list[dict[str, object]] = []

    def check(component: str, name: str, passed: bool, detail: str, blocked: bool = False) -> None:
        checks.append({
            "component": component,
            "check": name,
            "status": "BLOCKED" if blocked else ("PASS" if passed else "FAIL"),
            "detail": detail,
        })

    # C5 contract and independent lag identities.
    c5 = pd.read_csv(C5_DAILY, parse_dates=["date", "datadate"])
    full = pd.read_csv(C5_FULL, parse_dates=["date"])
    external = pd.read_csv(C5_EXTERNAL, parse_dates=["date"])
    expected_dates = pd.date_range("1990-01-31", "2020-12-31", freq="ME")
    expected_c5 = pd.MultiIndex.from_product(
        [["DEU", "IND", "JPN"], expected_dates], names=["country", "date"]
    )
    actual_c5 = pd.MultiIndex.from_frame(c5[["country", "date"]])
    check("C5", "exact_country_month_keys", len(c5) == 1_116 and actual_c5.equals(expected_c5), f"rows={len(c5)} expected=1116")
    check("C5", "unique_keys", not c5.duplicated(["country", "date"]).any(), "country,date are unique")
    check("C5", "finite_state_values", np.isfinite(c5[["MKTVOL", "ILLIQ"]].to_numpy()).all(), "no null/inf state values")
    in_bounds = c5[["MKTVOL", "ILLIQ"]].abs().le(5.0 + 1e-12).all().all()
    check("C5", "state_clip_bounds", bool(in_bounds), "MKTVOL and ILLIQ lie in [-5,5]")

    c5["MKTVOL_raw_rebuilt"] = np.log(c5["market_sigma_21"].where(c5["market_sigma_21"] > 0))
    c5["ILLIQ_raw_rebuilt"] = np.nan
    for _, index in c5.groupby("country", sort=True).groups.items():
        x = c5.loc[index, "ILLIQ_vw_raw"]
        trailing = x.rolling(12, min_periods=9).mean()
        c5.loc[index, "ILLIQ_raw_rebuilt"] = np.log(x.where(x > 0)) - np.log(trailing.where(trailing > 0))
    expected_mkt_lag = c5.groupby("country", sort=False)["MKTVOL_raw_rebuilt"].shift(1)
    expected_illiq_lag = c5.groupby("country", sort=False)["ILLIQ_raw_rebuilt"].shift(1)
    mkt_lag_match = c5["MKTVOL_lagged_raw"].isna().equals(expected_mkt_lag.isna()) and max_abs_difference(c5["MKTVOL_lagged_raw"], expected_mkt_lag) <= 1e-12
    illiq_lag_match = c5["ILLIQ_lagged_raw"].isna().equals(expected_illiq_lag.isna()) and max_abs_difference(c5["ILLIQ_lagged_raw"], expected_illiq_lag) <= 1e-12
    check("C5", "mktvol_one_month_lag_identity", mkt_lag_match, f"max_abs_error={max_abs_difference(c5['MKTVOL_lagged_raw'], expected_mkt_lag):.3g}")
    check("C5", "illiq_one_month_lag_identity", illiq_lag_match, f"max_abs_error={max_abs_difference(c5['ILLIQ_lagged_raw'], expected_illiq_lag):.3g}")
    endpoint_ok = (c5.loc[c5["datadate"].notna(), "datadate"] <= c5.loc[c5["datadate"].notna(), "date"]).all()
    check("C5", "daily_endpoint_no_lookahead", bool(endpoint_ok), "all market daily endpoints are on/before formation month-end")
    preactive_zero = (
        c5.loc[~c5["MKTVOL_active"], "MKTVOL"].eq(0).all()
        and c5.loc[~c5["ILLIQ_active"], "ILLIQ"].eq(0).all()
    )
    check("C5", "neutral_only_before_activation", bool(preactive_zero), "inactive MKTVOL/ILLIQ states are exactly zero")

    external_cols = [col for col in external.columns if col not in {"MKTVOL", "MKTVOL_active", "ILLIQ", "ILLIQ_active"}]
    merged_external = full[external_cols].merge(external, on=["country", "date"], how="outer", indicator=True, suffixes=("_full", "_source"))
    external_unchanged = merged_external["_merge"].eq("both").all()
    for col in [c for c in external_cols if c not in {"country", "date"}]:
        left = merged_external[f"{col}_full"]
        right = merged_external[f"{col}_source"]
        if pd.api.types.is_bool_dtype(left) and pd.api.types.is_bool_dtype(right):
            external_unchanged &= left.equals(right)
        elif pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right):
            external_unchanged &= left.isna().equals(right.isna()) and max_abs_difference(left, right) <= 1e-12
        else:
            external_unchanged &= left.fillna("<NA>").equals(right.fillna("<NA>"))
    check("C5", "external_states_unchanged", bool(external_unchanged), "daily-state merge did not alter pre-existing C5 columns")

    # C6 exact identities against certified staging inputs.
    c6 = pd.read_csv(C6, parse_dates=["date", "endpoint_date"], low_memory=False)
    daily = pd.read_csv(
        DAILY,
        usecols=["country", "date", "permno", "gvkey", "iid", "sigma_d_21_strict", "adv_usd_21_strict", "endpoint_date", "prccd", "ajexdi", "trfd"],
        parse_dates=["date", "endpoint_date"],
        low_memory=False,
    )
    edge = pd.read_csv(EDGE, usecols=["country", "date", "permno", "edge_21_strict"], parse_dates=["date"], low_memory=False)
    keys = ["country", "date", "permno"]
    check("C6", "row_count", len(c6) == 757_297, f"rows={len(c6)} expected=757297")
    check("C6", "unique_keys", not c6.duplicated(keys).any(), "country,date,permno are unique")
    key_match = c6[keys].merge(daily[keys], on=keys, how="outer", indicator=True)["_merge"].value_counts().to_dict()
    check("C6", "exact_certified_panel_keys", key_match.get("left_only", 0) == 0 and key_match.get("right_only", 0) == 0, json.dumps(key_match, sort_keys=True))

    identity = c6.merge(daily, on=keys, how="left", validate="one_to_one", suffixes=("", "_daily"))
    sigma_match = identity["sigma_d"].isna().equals(identity["sigma_d_21_strict"].isna()) and max_abs_difference(identity["sigma_d"], identity["sigma_d_21_strict"]) <= 1e-12
    adv_match = numeric_series_match(identity["adv_usd"], identity["adv_usd_21_strict"], atol=1e-8, rtol=1e-12)
    check("C6", "sigma_certified_identity", sigma_match, f"max_abs_error={max_abs_difference(identity['sigma_d'], identity['sigma_d_21_strict']):.3g}")
    check("C6", "adv_usd_certified_identity", adv_match, f"max_abs_error={max_abs_difference(identity['adv_usd'], identity['adv_usd_21_strict']):.3g}")
    endpoint_no_lookahead = (identity.loc[identity["endpoint_date"].notna(), "endpoint_date"] <= identity.loc[identity["endpoint_date"].notna(), "date"]).all()
    check("C6", "endpoint_no_lookahead", bool(endpoint_no_lookahead), "all certified endpoints are on/before formation month-end")

    edge_identity = c6.merge(edge, on=keys, how="left", validate="one_to_one", suffixes=("", "_reference"))
    edge_rows = c6["spread_source"].eq("EDGE_21_STRICT")
    edge_spread_match = max_abs_difference(edge_identity.loc[edge_rows, "spread"], edge_identity.loc[edge_rows, "edge_21_strict_reference"]) <= 1e-12
    source_labels_valid = set(c6["spread_source"].unique()).issubset({"EDGE_21_STRICT", "ABDI_RANALDO_21_STRICT", "MISSING"})
    hierarchy_valid = (
        c6.loc[c6["edge_21_strict"].notna(), "spread_source"].eq("EDGE_21_STRICT").all()
        and c6.loc[c6["spread_source"].eq("MISSING"), "spread"].isna().all()
    )
    check("C6", "edge_reference_identity", edge_spread_match, f"EDGE rows={int(edge_rows.sum())}")
    check("C6", "spread_source_hierarchy", bool(source_labels_valid and hierarchy_valid), "EDGE primary; AR fallback; otherwise null")
    nonnegative = (c6[["spread", "sigma_d", "adv_usd"]].dropna() >= 0).all().all()
    check("C6", "nonnegative_market_inputs", bool(nonnegative), "no negative spread, sigma_d, or ADV")
    # A monthly standard deviation above one implies at least one extraordinary
    # adjusted daily return and warrants source-row/corporate-action inspection.
    # Preserve and flag these values; never silently winsorise or delete them.
    outliers = identity.loc[
        identity["sigma_d"].ge(1.0),
        ["country", "date", "permno", "gvkey", "iid", "sigma_d", "adv_usd", "spread", "spread_source", "endpoint_date", "prccd", "ajexdi", "trfd"],
    ].copy()
    outliers.to_csv(OUT_OUTLIERS, index=False)
    sigma_resolution = json.loads(SIGMA_RESOLUTION.read_text(encoding="utf-8"))
    resolution_keys = {
        (row["country"], row["date"], int(row["permno"]))
        for row in sigma_resolution.get("rows", [])
        if row.get("resolution") != "UNRESOLVED"
    }
    outlier_keys = {
        (row.country, str(row.date.date()), int(row.permno))
        for row in outliers.itertuples(index=False)
    }
    outliers_resolved = bool(
        sigma_resolution.get("verdict") == "PASS_RAW_CONFIRMED_PRESERVED_AND_FAIL_CLOSED"
        and resolution_keys == outlier_keys
    )
    check(
        "C6",
        "extreme_sigma_raw_review",
        outliers_resolved or outliers.empty,
        (
            f"sigma_d>=1 rows={len(outliers)}; exact raw windows reproduced, values preserved, "
            "and all flagged rows excluded from complete market inputs by missing strict ADV"
            if outliers_resolved
            else f"sigma_d>=1 rows={len(outliers)}; raw resolution incomplete"
        ),
        blocked=bool(not outliers.empty and not outliers_resolved),
    )
    borrow_null = c6["borrow_fee"].isna().all() and c6["borrow_fee_source"].eq("BLOCKED_NO_CERTIFIED_SECURITIES_LENDING_SOURCE").all()
    check("C6", "borrow_fee_fail_closed", bool(borrow_null), "borrow_fee is null in every row and explicitly blocked")

    # Hard integration gate: a nullable, explicitly blocked fee must never be
    # converted into an economic assumption inside Workstream B.  This is a
    # FAIL (not merely a data-source BLOCK) because the current consumer would
    # silently change portfolio economics if C6 were passed to it.
    consumer_source = WORKSTREAM_B_COST_CONSUMER.read_text(encoding="utf-8")
    implicit_fixed_fill = 'fillna(0.0025)' in consumer_source
    unsafe_borrow_integration = borrow_null and implicit_fixed_fill
    check(
        "C6",
        "borrow_fee_consumer_integration_hard_gate",
        not unsafe_borrow_integration,
        (
            "HARD INTEGRATION FAILURE: certified borrow_fee is unavailable but "
            "Workstream B silently applies fillna(0.0025)"
            if unsafe_borrow_integration
            else "no implicit fixed borrow-fee substitution detected"
        ),
    )

    with ENTITLEMENT.open("r", encoding="utf-8") as fh:
        entitlement = json.load(fh)
    lending_candidates = entitlement.get("securities_finance_candidates", [])
    candidate_tables = [f"{x.get('library')}.{x.get('table')}" for x in lending_candidates if x.get("borrow_keyword_columns")]
    genuine_fee_terms = {"borrow_fee", "loan_fee", "lending_fee", "rebate_rate", "fee_rate", "cost_to_borrow"}
    found_fee_fields = sorted({col.lower() for x in lending_candidates for col in x.get("columns", [])} & genuine_fee_terms)
    no_fee_source = not found_fee_fields
    check("C6", "genuine_borrow_fee_source", False, f"no fee/rebate fields in visible candidates {candidate_tables}; short-volume/short-position data rejected", blocked=no_fee_source)

    ar_complete = AR.exists()
    check("C6", "abdi_ranaldo_fallback_extraction", ar_complete, "WRDS extraction artefact present" if ar_complete else "blocked by WRDS PAM authentication failure", blocked=not ar_complete)
    spread_complete = c6["spread"].notna().all()
    check("C6", "spread_coverage", spread_complete, f"nonnull={int(c6['spread'].notna().sum())}/{len(c6)}", blocked=not spread_complete)

    c5_failures = [x for x in checks if x["component"] == "C5" and x["status"] == "FAIL"]
    c6_failures = [x for x in checks if x["component"] == "C6" and x["status"] == "FAIL"]
    c6_blocks = [x for x in checks if x["component"] == "C6" and x["status"] == "BLOCKED"]
    if c5_failures or c6_failures:
        verdict = "FAIL_MECHANICAL_PREFLIGHT"
    else:
        verdict = "PASS_C5_WORKING_CANDIDATE__C6_BLOCKED_FAIL_CLOSED" if c6_blocks else "PASS_C5_C6_WORKING_CANDIDATES"

    by_country = []
    for country, g in c6.groupby("country", sort=True):
        by_country.append({
            "country": country,
            "rows": int(len(g)),
            "spread_nonnull": int(g["spread"].notna().sum()),
            "sigma_d_nonnull": int(g["sigma_d"].notna().sum()),
            "adv_usd_nonnull": int(g["adv_usd"].notna().sum()),
            "complete_market_inputs": int(g[["spread", "sigma_d", "adv_usd"]].notna().all(axis=1).sum()),
        })

    audit = {
        "verdict": verdict,
        "scope": "working candidates only; no production promotion",
        "c5_status": "PASS" if not c5_failures else "FAIL",
        "c6_status": "BLOCKED" if c6_blocks and not c6_failures else ("PASS" if not c6_failures else "FAIL"),
        "checks": checks,
        "economic_qa": {
            "C5_MKTVOL": quantiles(c5["MKTVOL"]),
            "C5_ILLIQ": quantiles(c5["ILLIQ"]),
            "C6_spread": quantiles(c6["spread"]),
            "C6_sigma_d": quantiles(c6["sigma_d"]),
            "C6_adv_usd": quantiles(c6["adv_usd"]),
            "C6_by_country": by_country,
        },
        "failures": [x["check"] for x in c5_failures + c6_failures],
        "blockers": [x["check"] for x in c6_blocks],
        "inputs": {str(path.relative_to(ROOT)): sha256(path) for path in required},
        "outputs": {
            "json": str(OUT_JSON.relative_to(ROOT)),
            "checks_csv": str(OUT_CSV.relative_to(ROOT)),
            "economic_outliers_csv": str(OUT_OUTLIERS.relative_to(ROOT)),
        },
        "production_written": False,
        "github_written": False,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(checks).to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if c5_failures or c6_failures:
        raise RuntimeError("Mechanical C5/C6 preflight failed")


if __name__ == "__main__":
    main()
