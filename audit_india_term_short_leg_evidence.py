"""Audit an external India 91-day T-bill evidence archive without importing it.

The archive remains external evidence.  This script validates its internal
identities and computes a non-production activation preview against the current
certified India 10-year working leg.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
LONG = ROOT / "data" / "intl_c5" / "candidate_term_drate_working" / "IND_RBI_10Y_SGL_working.csv"
CURRENT_SHORT = ROOT / "data" / "intl_c5" / "candidate_term_drate_working" / "IND_RBI_91D_DIRECT_MONTHLY_V2_working.csv"
CURRENT_CANDIDATE = ROOT / "data" / "intl_c5" / "candidate_term_drate_working" / "IND_TERM_DRATE_WORKING_FINAL_CANDIDATE.csv"
OUT = ROOT / "data" / "intl_c5" / "audit" / "INDIA_TERM_SHORT_LEG_EVIDENCE_AUDIT.json"
PREFIX = "India_TERM_short_leg_and_audit/"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(archive: zipfile.ZipFile, name: str, **kwargs: object) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(archive.read(PREFIX + name)), **kwargs)


def monthly_pit(raw: pd.DataFrame, date_column: str) -> pd.DataFrame:
    valid = raw.dropna(subset=[date_column, "implicit_yield_pct"]).sort_values(
        [date_column, "date_auction"], kind="stable"
    )
    months = pd.period_range(
        valid[date_column].min().to_period("M"),
        valid[date_column].max().to_period("M"),
        freq="M",
    )
    rows: list[dict[str, object]] = []
    for month in months:
        month_end = month.to_timestamp(how="end").normalize()
        available = valid.loc[valid[date_column].le(month_end)]
        if available.empty:
            continue
        last = available.iloc[-1]
        rows.append({
            "month": month,
            "tbill91_yield_pct": float(last["implicit_yield_pct"]),
            "source_auction_date": last["date_auction"],
            "source_issue_date": last["date_issue"],
            "staleness_days": int((month_end - last[date_column]).days),
        })
    return pd.DataFrame(rows)


def first_true(frame: pd.DataFrame, column: str) -> str | None:
    values = frame.loc[frame[column], "date"]
    return None if values.empty else str(values.iloc[0].date())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()
    archive_path = args.zip_path.resolve()
    if not archive_path.is_file():
        raise FileNotFoundError(archive_path)

    with zipfile.ZipFile(archive_path) as archive:
        names = sorted(archive.namelist())
        raw = read_csv(
            archive,
            "india_tbill91_auctions_raw.csv",
            parse_dates=["date_auction", "date_issue"],
        )
        supplied = read_csv(archive, "india_tbill91_monthly_pit.csv")
        fetch_source = archive.read(PREFIX + "fetch_tbill91.py").decode("utf-8")

    raw["implicit_yield_pct"] = pd.to_numeric(raw["implicit_yield_pct"], errors="coerce")
    supplied["month"] = pd.PeriodIndex(supplied["month"], freq="M")
    supplied["source_auction_date"] = pd.to_datetime(supplied["source_auction_date"])
    supplied["source_issue_date"] = pd.to_datetime(supplied["source_issue_date"])

    issue_rollover_mask = (
        raw["date_issue"].lt(raw["date_auction"])
        & (raw["date_auction"] - raw["date_issue"]).dt.days.gt(300)
    )
    corrected_raw = raw.copy()
    corrected_raw.loc[issue_rollover_mask, "date_issue"] = (
        corrected_raw.loc[issue_rollover_mask, "date_issue"] + pd.DateOffset(years=1)
    )

    rebuilt = monthly_pit(raw, "date_issue")
    comparison = supplied.merge(
        rebuilt,
        on="month",
        how="outer",
        suffixes=("_supplied", "_rebuilt"),
        indicator=True,
    )
    pit_exact = bool(
        comparison["_merge"].eq("both").all()
        and np.isclose(
            comparison["tbill91_yield_pct_supplied"],
            comparison["tbill91_yield_pct_rebuilt"],
            atol=1e-12,
            rtol=0,
        ).all()
        and comparison["source_auction_date_supplied"].equals(
            comparison["source_auction_date_rebuilt"]
        )
        and comparison["source_issue_date_supplied"].equals(
            comparison["source_issue_date_rebuilt"]
        )
        and comparison["staleness_days_supplied"].equals(
            comparison["staleness_days_rebuilt"]
        )
    )
    corrected_rebuilt = monthly_pit(corrected_raw, "date_issue")
    correction_compare = rebuilt.merge(
        corrected_rebuilt[["month", "tbill91_yield_pct"]],
        on="month",
        how="outer",
        suffixes=("_original", "_corrected"),
        indicator=True,
    )
    correction_changes_values = bool(
        not correction_compare["_merge"].eq("both").all()
        or not np.isclose(
            correction_compare["tbill91_yield_pct_original"],
            correction_compare["tbill91_yield_pct_corrected"],
            atol=1e-12,
            rtol=0,
        ).all()
    )

    expected_months = pd.period_range(supplied["month"].min(), supplied["month"].max(), freq="M")
    issue_lag = (raw["date_issue"] - raw["date_auction"]).dt.days
    corrected_issue_lag = (
        corrected_raw["date_issue"] - corrected_raw["date_auction"]
    ).dt.days
    auction_keyed = monthly_pit(raw, "date_auction")
    issue_vs_auction = rebuilt.merge(
        auction_keyed[["month", "tbill91_yield_pct"]],
        on="month",
        how="inner",
        suffixes=("_issue", "_auction"),
    )

    # Verify whether any month's chronologically last auction has a missing
    # implicit yield; this is stricter than merely rebuilding after dropna.
    last_auction_missing_months: list[str] = []
    for month in expected_months:
        end = month.to_timestamp(how="end").normalize()
        available = raw.loc[raw["date_issue"].le(end)].sort_values(
            ["date_issue", "date_auction"], kind="stable"
        )
        if not available.empty and pd.isna(available.iloc[-1]["implicit_yield_pct"]):
            last_auction_missing_months.append(str(month))

    selected_issue_lag = (
        supplied["source_issue_date"] - supplied["source_auction_date"]
    ).dt.days

    current_short = pd.read_csv(CURRENT_SHORT, parse_dates=["date"])
    current_short["month"] = current_short["date"].dt.to_period("M")
    current_short["value"] = pd.to_numeric(current_short["value"], errors="coerce")
    overlap = supplied.merge(
        current_short[["month", "value"]].dropna(),
        on="month",
        how="inner",
    )
    overlap_difference = overlap["tbill91_yield_pct"] - overlap["value"]

    calendar = pd.DataFrame({
        "date": pd.date_range("1990-01-31", "2020-12-31", freq="ME")
    })
    long_leg = pd.read_csv(LONG, parse_dates=["date"])
    short_leg = corrected_rebuilt.copy()
    short_leg["date"] = short_leg["month"].dt.to_timestamp(how="end").dt.normalize()
    preview = calendar.merge(long_leg.rename(columns={"value": "long"}), on="date", how="left")
    preview = preview.merge(
        short_leg[["date", "tbill91_yield_pct"]].rename(columns={"tbill91_yield_pct": "short"}),
        on="date",
        how="left",
    )
    preview["term_raw"] = preview["long"] - preview["short"]
    preview["term_pit"] = preview["term_raw"].shift(1)
    count = preview["term_pit"].expanding(min_periods=1).count()
    std = preview["term_pit"].expanding(min_periods=24).std(ddof=0)
    preview["term_active"] = count.ge(24) & preview["term_pit"].notna() & std.gt(0)
    first_position = np.flatnonzero(preview["term_active"].to_numpy())
    post_activation_gaps: list[str] = []
    if len(first_position):
        missing = preview.loc[first_position[0]:, "term_pit"].isna()
        post_activation_gaps = [
            str(value.date())
            for value in preview.loc[first_position[0]:, "date"].loc[missing]
        ]

    current_candidate = pd.read_csv(CURRENT_CANDIDATE, parse_dates=["date"])
    current_first = first_true(current_candidate, "TERM_active")
    preview_first = first_true(preview, "term_active")

    checks = {
        "raw_rows_1752": len(raw) == 1_752,
        "raw_unique_auction_dates": not raw["date_auction"].duplicated().any(),
        "selected_monthly_issue_never_precedes_auction": bool(
            selected_issue_lag.dropna().ge(0).all()
        ),
        "year_rollover_correction_changes_no_monthly_yield": not correction_changes_values,
        "five_missing_implicit_yields": int(raw["implicit_yield_pct"].isna().sum()) == 5,
        "monthly_rows_405": len(supplied) == 405,
        "monthly_zero_calendar_gaps": pd.PeriodIndex(supplied["month"]).equals(expected_months),
        "monthly_pit_exactly_rebuilt_from_raw": pit_exact,
        "staleness_nonnegative": bool(supplied["staleness_days"].ge(0).all()),
        "fetch_script_uses_issue_date_and_no_interpolation": (
            'dropna(subset=["date_issue", "implicit_yield_pct"])' in fetch_source
            and 'd[d["date_issue"] <= cutoff]' in fetch_source
            and ".interpolate(" not in fetch_source
            and ".bfill(" not in fetch_source
        ),
    }
    all_internal_checks_pass = all(checks.values())

    audit = {
        "verdict": (
            "PASS_EVIDENCE__PRIMARY_AUCTION_CUTOFF_COMPATIBLE_WITH_EXISTING_91D_CONTRACT__INDEPENDENT_REBUILD_REQUIRED"
            if all_internal_checks_pass and preview_first == "1998-08-31" and not post_activation_gaps
            else "BLOCKED_EVIDENCE_OR_ACTIVATION_CHECK_FAILED"
        ),
        "semantic_decision": (
            "Admissible as the India TERM short leg. The frozen project definition already uses "
            "an RBI 91-day primary-auction implicit yield, so secondary-market pricing is not a "
            "current contract requirement. This archive changes the monthly statistic from a "
            "monthly average to the last issue-date-available weekly cut-off yield."
        ),
        "archive": {
            "path": str(archive_path),
            "sha256": sha256(archive_path),
            "members": names,
        },
        "internal_checks": checks,
        "raw": {
            "rows": int(len(raw)),
            "first_auction": str(raw["date_auction"].min().date()),
            "last_auction": str(raw["date_auction"].max().date()),
            "missing_implicit_yields": int(raw["implicit_yield_pct"].isna().sum()),
            "source_issue_dates_preceding_auction": int(issue_rollover_mask.sum()),
            "source_issue_date_rollover_rows": [
                {
                    "auction_date": str(row.date_auction.date()),
                    "source_issue_date": str(row.date_issue.date()),
                    "corrected_issue_date": str(
                        corrected_raw.loc[index, "date_issue"].date()
                    ),
                }
                for index, row in raw.loc[issue_rollover_mask].iterrows()
            ],
            "corrected_issue_lag_days_min": int(corrected_issue_lag.min()),
            "corrected_issue_lag_days_median": float(corrected_issue_lag.median()),
            "corrected_issue_lag_days_max": int(corrected_issue_lag.max()),
            "rollover_correction_changes_monthly_yield": correction_changes_values,
            "last_auction_missing_yield_months": last_auction_missing_months,
        },
        "monthly": {
            "rows": int(len(supplied)),
            "first_month": str(supplied["month"].min()),
            "last_month": str(supplied["month"].max()),
            "missing_months": [str(value) for value in expected_months.difference(supplied["month"])],
            "staleness_days_median": float(supplied["staleness_days"].median()),
            "staleness_days_max": int(supplied["staleness_days"].max()),
            "issue_vs_auction_key_value_difference_months": int(
                (~np.isclose(
                    issue_vs_auction["tbill91_yield_pct_issue"],
                    issue_vs_auction["tbill91_yield_pct_auction"],
                    atol=1e-12,
                    rtol=0,
                )).sum()
            ),
        },
        "comparison_with_current_monthly_average_source": {
            "overlap_months": int(len(overlap)),
            "correlation": float(overlap["tbill91_yield_pct"].corr(overlap["value"])),
            "mean_absolute_difference_percentage_points": float(overlap_difference.abs().mean()),
            "max_absolute_difference_percentage_points": float(overlap_difference.abs().max()),
            "interpretation": "Different monthly statistics; agreement is economic, not an expected identity.",
        },
        "nonproduction_activation_preview": {
            "term_definition": "current RBI 10Y working leg minus supplied last-available 91-day cut-off yield",
            "pit_rule": "existing one-reference-month lag after raw TERM construction",
            "standardisation_warmup": "24 observed PIT values, expanding ddof=0",
            "current_first_active": current_first,
            "preview_first_active": preview_first,
            "months_earlier": (
                int((pd.Period(current_first, freq="M") - pd.Period(preview_first, freq="M")).n)
                if current_first and preview_first
                else None
            ),
            "post_activation_gaps": post_activation_gaps,
            "production_candidate_written": False,
        },
        "caveats": [
            "The short leg begins in January 1993; it does not solve 1990-1992.",
            "The early auction market was developing and must be recorded in source metadata.",
            "The supplied Playwright scraper is UI-dependent; production must independently fetch, hash, and certify RBI rows.",
            "Issue-date keying is conservative; the project-level one-month lag remains in force.",
            "Three raw issue dates have a same-year rollover error; adding one year restores nonnegative auction-to-issue lags and changes no selected monthly yield.",
            "At four month ends the latest auction has no cut-off yield; the monthly value is explicitly the prior successful auction and its staleness must remain visible.",
        ],
        "production_written": False,
        "github_written": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if audit["verdict"].startswith("BLOCKED"):
        raise RuntimeError("India TERM short-leg evidence audit failed")


if __name__ == "__main__":
    main()
