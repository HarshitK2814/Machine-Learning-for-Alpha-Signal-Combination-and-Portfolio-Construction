"""Mechanically certify C1/Compustat Global daily return and unit semantics.

The script is intentionally fail-closed and writes audit/staging artefacts only.
It does not approve an OHLC spread estimator or fabricate borrow-fee data.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
PANEL_PATH = ROOT / "data" / "intl_c6" / "staging" / "C6_CERTIFIED_MONTHLY_DAILY_FEATURES.csv.gz"
BENCH_PATH = ROOT / "data" / "intl_c6" / "staging" / "C4_DAILY_ENDPOINT_BENCHMARK.csv.gz"
REV_PATH = ROOT / "data" / "intl_c6" / "audit" / "C6_RETURN_INDEX_CURRENT_VINTAGE_REVISIONS.csv"
COVERAGE_PATH = ROOT / "data" / "intl_c6" / "audit" / "C6_DAILY_COVERAGE_BY_COUNTRY_YEAR.csv"
AUDIT_PATH = ROOT / "data" / "intl_c6" / "audit" / "C6_DAILY_SEMANTICS_CERTIFICATION.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fsummary(values: pd.Series) -> dict[str, float | int | None]:
    x = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if x.empty:
        return {"n": 0, "min": None, "p50": None, "p99": None, "max": None}
    return {
        "n": int(len(x)),
        "min": float(x.min()),
        "p50": float(x.quantile(0.5)),
        "p99": float(x.quantile(0.99)),
        "max": float(x.max()),
    }


def main() -> None:
    panel = pd.read_csv(PANEL_PATH, low_memory=False)
    bench = pd.read_csv(BENCH_PATH, low_memory=False)
    for c in ["date", "endpoint_date"]:
        panel[c] = pd.to_datetime(panel[c], errors="raise")
    for c in ["eom", "daily_endpoint_date"]:
        bench[c] = pd.to_datetime(bench[c], errors="raise")
    panel["permno"] = pd.to_numeric(panel["permno"], errors="raise").astype("int64")
    bench["id"] = pd.to_numeric(bench["id"], errors="raise").astype("int64")

    if panel.duplicated(["country", "date", "permno"]).any():
        raise RuntimeError("Duplicate panel contract keys")
    if bench.duplicated(["excntry", "eom", "id"]).any():
        raise RuntimeError("Duplicate benchmark contract keys")

    merged = panel.merge(
        bench,
        left_on=["country", "date", "permno"],
        right_on=["excntry", "eom", "id"],
        how="outer",
        indicator=True,
        validate="one_to_one",
        suffixes=("", "_c4"),
    )
    if not (merged["_merge"] == "both").all():
        raise RuntimeError(f"C4/panel key mismatch: {merged['_merge'].value_counts().to_dict()}")

    merged["adjusted_price_abs_diff"] = (merged["adjusted_price"] - merged["daily_adj_price"]).abs()
    merged["trfd_abs_diff"] = (merged["trfd"] - merged["daily_trfd"]).abs()
    merged["return_index_abs_diff"] = (merged["return_index"] - merged["daily_ri_local"]).abs()
    revision = (
        (merged["adjusted_price_abs_diff"] > 1e-8)
        | (merged["trfd_abs_diff"] > 1e-8)
        | (merged["return_index_abs_diff"] > 1e-8)
    )
    revision_cols = [
        "country", "date", "permno", "gvkey", "iid", "endpoint_date",
        "adjusted_price", "daily_adj_price", "adjusted_price_abs_diff",
        "trfd", "daily_trfd", "trfd_abs_diff", "return_index",
        "daily_ri_local", "return_index_abs_diff", "curcdd", "daily_curcd",
    ]
    revisions = merged.loc[revision, revision_cols].sort_values(["country", "permno", "date"])
    REV_PATH.parent.mkdir(parents=True, exist_ok=True)
    revisions.to_csv(REV_PATH, index=False)

    formula_valid = merged[["prccd", "ajexdi", "trfd", "adjusted_price", "return_index"]].notna().all(axis=1)
    price_formula_error = (merged.loc[formula_valid, "adjusted_price"] - merged.loc[formula_valid, "prccd"] / merged.loc[formula_valid, "ajexdi"]).abs()
    ri_formula_error = (merged.loc[formula_valid, "return_index"] - merged.loc[formula_valid, "adjusted_price"] * merged.loc[formula_valid, "trfd"]).abs()
    price_formula_relative_error = price_formula_error / merged.loc[formula_valid, "adjusted_price"].abs().clip(lower=1e-30)
    ri_formula_relative_error = ri_formula_error / merged.loc[formula_valid, "return_index"].abs().clip(lower=1e-30)

    vol_valid = merged[["month_sum_cshtrd", "cshtrm"]].notna().all(axis=1) & (merged["cshtrm"] != 0)
    volume_ratio = merged.loc[vol_valid, "month_sum_cshtrd"] / merged.loc[vol_valid, "cshtrm"]
    volume_factor_error = (volume_ratio - 1000.0).abs()
    qunit_valid = pd.to_numeric(merged["qunit"], errors="coerce").dropna()

    endpoint_future = int((merged["endpoint_date"] > merged["date"]).sum())
    endpoint_mismatch = int((merged["endpoint_date"] != merged["daily_endpoint_date"]).sum())
    currency_mismatch = int(
        (merged["curcdd"].astype("string").str.strip() != merged["daily_curcd"].astype("string").str.strip()).sum()
    )

    merged["year"] = merged["date"].dt.year
    rows = []
    for (country, year), g in merged.groupby(["country", "year"], sort=True):
        n = len(g)
        rows.append({
            "country": country,
            "year": int(year),
            "investible_months": n,
            "return_21_complete": int((g["return_obs_21"] == 21).sum()),
            "return_21_complete_rate": float((g["return_obs_21"] == 21).mean()),
            "adv_any": int(g["adv_usd_21"].notna().sum()),
            "adv_any_rate": float(g["adv_usd_21"].notna().mean()),
            "volume_21_complete": int((g["volume_obs_21"] == 21).sum()),
            "volume_21_complete_rate": float((g["volume_obs_21"] == 21).mean()),
            "ohlc_any": int(g["hl_range_21"].notna().sum()),
            "ohlc_any_rate": float(g["hl_range_21"].notna().mean()),
            "ohlc_21_complete": int((g["ohlc_obs_21"] == 21).sum()),
            "ohlc_21_complete_rate": float((g["ohlc_obs_21"] == 21).mean()),
            "endpoint_fx_missing": int(g["usd_per_local"].isna().sum()),
            "max_internal_calendar_gap": float(g["max_gap_days_21"].max()),
        })
    coverage = pd.DataFrame(rows)
    coverage.to_csv(COVERAGE_PATH, index=False)

    monthly_price_valid = merged[["prccd", "prccm"]].notna().all(axis=1)
    monthly_price_error = (merged.loc[monthly_price_valid, "prccd"] - merged.loc[monthly_price_valid, "prccm"]).abs()
    volume_exact = int((volume_factor_error <= 1e-6).sum())

    audit = {
        "verdict": "PASS_RETURN_AND_TRADED_SHARE_SEMANTICS_WITH_EXPLICIT_COVERAGE_GAPS",
        "scope": "certification/staging only; no production promotion",
        "rows": int(len(merged)),
        "unique_investible_securities": int(merged[["country", "permno"]].drop_duplicates().shape[0]),
        "key_match": {"both": int((merged["_merge"] == "both").sum()), "left_only": 0, "right_only": 0},
        "no_lookahead": {"endpoint_after_formation_rows": endpoint_future, "pass": endpoint_future == 0},
        "endpoint_consistency": {"c4_endpoint_date_mismatches": endpoint_mismatch},
        "currency_consistency": {"c4_endpoint_currency_mismatches": currency_mismatch},
        "adjusted_return_semantics": {
            "adjusted_price_formula": "prccd / ajexdi",
            "return_index_formula": "(prccd / ajexdi) * trfd",
            "daily_total_return_formula": "return_index[t] / return_index[t-1] - 1 within security and currency",
            "mechanical_price_formula_max_abs_error": float(price_formula_error.max()),
            "mechanical_return_index_formula_max_abs_error": float(ri_formula_error.max()),
            "mechanical_price_formula_max_relative_error": float(price_formula_relative_error.max()),
            "mechanical_return_index_formula_max_relative_error": float(ri_formula_relative_error.max()),
            "archived_c4_current_vintage_revision_rows": int(revision.sum()),
            "archived_c4_current_vintage_revision_securities": int(merged.loc[revision, ["country", "permno"]].drop_duplicates().shape[0]),
            "revision_rule": "differences above 1e-8 are isolated vendor current-vintage revisions; frozen C4 is not modified",
            "adjusted_price_abs_diff": fsummary(merged["adjusted_price_abs_diff"]),
            "trfd_abs_diff": fsummary(merged["trfd_abs_diff"]),
            "return_index_abs_diff": fsummary(merged["return_index_abs_diff"]),
        },
        "monthly_price_validation": {
            "comparable_rows": int(monthly_price_valid.sum()),
            "exact_within_1e_8": int((monthly_price_error <= 1e-8).sum()),
            "absolute_difference": fsummary(monthly_price_error),
        },
        "traded_share_semantics": {
            "daily_field": "g_secd.cshtrd",
            "monthly_field": "g_secm.cshtrm",
            "certified_relation": "sum(daily cshtrd actual-price rows) = 1000 * monthly cshtrm when source month coverage agrees",
            "comparable_rows": int(vol_valid.sum()),
            "factor_1000_exact_within_1e_6": volume_exact,
            "factor_1000_nonexact_rows": int(vol_valid.sum()) - volume_exact,
            "ratio_summary": fsummary(volume_ratio),
            "endpoint_qunit_nonnull_rows": int(len(qunit_valid)),
            "endpoint_qunit_unique": sorted(float(x) for x in qunit_valid.unique()),
            "certified_daily_notional_local": "prccd * cshtrd / qunit; qunit is 1 throughout this C1 investible panel",
        },
        "fx_semantics": {
            "formula": "USD_per_local = GBP_to_USD / GBP_to_local",
            "application": "21-day mean local traded notional multiplied by exact endpoint-date USD_per_local",
            "no_fill": True,
            "endpoint_fx_missing_rows": int(merged["usd_per_local"].isna().sum()),
            "endpoint_fx_missing_dates": int(merged.loc[merged["usd_per_local"].isna(), "endpoint_date"].nunique()),
        },
        "coverage_totals": {
            "sigma_21_strict": int(merged["sigma_d_21_strict"].notna().sum()),
            "adv_usd_any": int(merged["adv_usd_21"].notna().sum()),
            "adv_usd_21_strict": int(merged["adv_usd_21_strict"].notna().sum()),
            "ohlc_21_strict_diagnostic": int(merged["ohlc_range_21_strict_diagnostic"].notna().sum()),
        },
        "internal_gap_days_summary": fsummary(merged["max_gap_days_21"]),
        "spread_status": "BLOCKED_PENDING_APPROVED_ESTIMATOR; hl_range_21 is diagnostic only",
        "borrow_fee_status": "BLOCKED_NO_CERTIFIED_SECURITIES_LENDING_OR_BORROW_FEE_SOURCE",
        "inputs": {
            "daily_panel": {"path": str(PANEL_PATH.relative_to(ROOT)), "sha256": sha256(PANEL_PATH)},
            "c4_endpoint_benchmark": {"path": str(BENCH_PATH.relative_to(ROOT)), "sha256": sha256(BENCH_PATH)},
        },
        "outputs": {
            "revision_rows": {"path": str(REV_PATH.relative_to(ROOT)), "sha256": sha256(REV_PATH)},
            "country_year_coverage": {"path": str(COVERAGE_PATH.relative_to(ROOT)), "sha256": sha256(COVERAGE_PATH)},
        },
        "production_written": False,
        "github_written": False,
    }

    hard_failures = [
        audit["key_match"]["both"] != 757_297,
        endpoint_future != 0,
        endpoint_mismatch != 0,
        currency_mismatch != 0,
        audit["adjusted_return_semantics"]["mechanical_price_formula_max_relative_error"] > 1e-12,
        audit["adjusted_return_semantics"]["mechanical_return_index_formula_max_relative_error"] > 1e-12,
        audit["traded_share_semantics"]["endpoint_qunit_unique"] != [1.0],
    ]
    if any(hard_failures):
        audit["verdict"] = "FAIL_DAILY_SEMANTICS_CERTIFICATION"
    AUDIT_PATH.write_text(json.dumps(audit, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict": audit["verdict"],
        "rows": audit["rows"],
        "return_revision_rows": audit["adjusted_return_semantics"]["archived_c4_current_vintage_revision_rows"],
        "volume_relation": audit["traded_share_semantics"],
        "coverage_totals": audit["coverage_totals"],
        "endpoint_fx_missing_rows": audit["fx_semantics"]["endpoint_fx_missing_rows"],
    }, indent=2))
    if audit["verdict"].startswith("FAIL"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
