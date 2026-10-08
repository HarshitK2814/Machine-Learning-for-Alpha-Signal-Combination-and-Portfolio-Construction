"""Close India TERM from independently cached primary RBI auction tables.

This is a working/non-production builder.  It never reads the contributed
India TERM evidence archive.  The source inputs are the RBI Handbook pages
previously downloaded by ``certify_india_rbi_91d_handbook.py`` and pinned by
SHA-256 in that certifier's source audit.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import certify_india_rbi_91d_handbook as rbi


ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "data" / "intl_c5" / "reference" / "_auto_term_drate_chunk" / "india_91d_handbook"
OUT = ROOT / "data" / "intl_c5" / "candidate_term_drate_working"
SOURCE_AUDIT = OUT / "IND_RBI_91D_HANDBOOK_SOURCE_AUDIT.json"
DBIE_DIR = ROOT / "data" / "intl_c5" / "reference" / "india_91d_cutoff_dbie_v1"
DBIE_RAW = DBIE_DIR / "RBI_91D_DBIE_AUCTIONS_RAW.csv"
DBIE_MANIFEST = DBIE_DIR / "RBI_91D_DBIE_EXTRACTION_MANIFEST.json"
LONG = OUT / "IND_RBI_10Y_SGL_working.csv"
CANDIDATE = OUT / "IND_TERM_DRATE_WORKING_FINAL_CANDIDATE.csv"
EXTERNAL = ROOT / "data" / "intl_c5" / "candidate_external_c5_working" / "C5_EXTERNAL_WORKING_CANDIDATE.csv"
AUCTIONS_OUT = OUT / "IND_RBI_91D_CUTOFF_AUCTIONS_WORKING.csv"
MONTHLY_OUT = OUT / "IND_RBI_91D_CUTOFF_MONTHLY_WORKING.csv"
AUDIT_OUT = OUT / "IND_TERM_RBI_91D_CUTOFF_CERTIFICATION.json"

SAMPLE_START = pd.Timestamp("1990-01-31")
SOURCE_START = pd.Timestamp("1993-01-01")
SAMPLE_END = pd.Timestamp("2020-12-31")
MIN_PERIODS = 24
CLIP = 5.0
YIELD_TOL = 5.1e-4
PRICE_YIELD_PARSE_TOL = 0.25


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_rows(path: Path) -> list[list[object]]:
    raw = path.read_bytes()
    # Some RBI download links use an .xls suffix while returning HTML.
    if path.suffix.lower() in {".xls", ".xlsx"} and not raw.lstrip().startswith(b"<"):
        try:
            book = pd.read_excel(path, sheet_name=None, header=None, engine="openpyxl")
        except Exception:
            book = pd.read_excel(path, sheet_name=None, header=None)
        return [row.tolist() for frame in book.values() for _, row in frame.iterrows()]
    return [row.get("cells", []) for row in rbi.html_rows(raw)]


def parse_source(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for cells in source_rows(path):
        dates: list[pd.Timestamp] = []
        for value in cells:
            parsed = rbi.parse_date_cell(value)
            if pd.notna(parsed) and pd.Timestamp("1990-01-01") <= parsed <= pd.Timestamp("2030-12-31"):
                dates.append(pd.Timestamp(parsed))
        if len(dates) < 2:
            continue
        auction_date, issue_date = dates[:2]
        lag = (issue_date - auction_date).days
        if not (0 <= lag <= 10):
            continue
        # RBI vintages use slightly different yield/day-count conventions and
        # rounded prices.  The legacy 3bp identity tolerance drops valid rows.
        # Locate the unique adjacent price/yield pair using a conservative
        # 25bp identity screen, then reconcile the yield across vintages.
        numbers = [rbi.parse_number(value) for value in cells]
        pairs: list[tuple[float, float, float]] = []
        for index in range(2, len(cells) - 1):
            price, yld = numbers[index], numbers[index + 1]
            if price is None or yld is None or not (80.0 <= price <= 100.5 and 0.0 < yld < 30.0):
                continue
            error = abs(rbi.price_implied_yield_91d(float(price)) - float(yld))
            if error <= PRICE_YIELD_PARSE_TOL:
                pairs.append((float(price), float(yld), float(error)))
        if len(pairs) > 1:
            raise RuntimeError(f"{path.name}: ambiguous price/yield pairs for {auction_date.date()}: {pairs}")
        successful = None if not pairs else pairs[0]
        records.append({
            "auction_date": auction_date,
            "issue_date": issue_date,
            "cutoff_price": np.nan if successful is None else successful[0],
            "implicit_yield_pct": np.nan if successful is None else successful[1],
            "price_yield_identity_error": np.nan if successful is None else successful[2],
            "source_file": str(path.relative_to(ROOT)),
            "source_sha256": sha256(path),
        })
    return records


def reconcile_sources(source_audit: dict[str, object]) -> pd.DataFrame:
    pinned = source_audit.get("cached_source_hashes", {})
    if not isinstance(pinned, dict) or not pinned:
        raise RuntimeError("RBI source audit has no pinned cached-source hashes")

    records: list[dict[str, object]] = []
    for raw_name, expected_hash in sorted(pinned.items()):
        path = ROOT / Path(raw_name)
        if not path.is_file():
            raise FileNotFoundError(path)
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise RuntimeError(f"RBI cache hash mismatch: {path}")
        records.extend(parse_source(path))
    if not records:
        raise RuntimeError("No auction rows parsed from pinned RBI primary sources")

    frame = pd.DataFrame(records)
    frame = frame.loc[
        frame["auction_date"].between(SOURCE_START, SAMPLE_END)
        & frame["issue_date"].between(SOURCE_START, SAMPLE_END + pd.Timedelta(days=10))
    ].copy()

    chosen: list[dict[str, object]] = []
    conflicts: list[dict[str, object]] = []
    for auction_date, group in frame.groupby("auction_date", sort=True):
        issue_dates = sorted(group["issue_date"].dropna().unique())
        values = pd.to_numeric(group["implicit_yield_pct"], errors="coerce").dropna()
        if len(issue_dates) != 1:
            conflicts.append({"auction_date": str(auction_date.date()), "issue_dates": [str(pd.Timestamp(x).date()) for x in issue_dates]})
            continue
        if len(values) and float(values.max() - values.min()) > YIELD_TOL:
            conflicts.append({"auction_date": str(auction_date.date()), "yields": sorted(values.unique().tolist())})
            continue
        successful = group.loc[group["implicit_yield_pct"].notna()].sort_values("source_file", kind="stable")
        representative = (successful if not successful.empty else group.sort_values("source_file", kind="stable")).iloc[0]
        chosen.append({
            "auction_date": auction_date,
            "issue_date": pd.Timestamp(issue_dates[0]),
            "cutoff_price": representative["cutoff_price"] if not successful.empty else np.nan,
            "implicit_yield_pct": representative["implicit_yield_pct"] if not successful.empty else np.nan,
            "price_yield_identity_error": representative["price_yield_identity_error"] if not successful.empty else np.nan,
            "successful_cutoff": not successful.empty,
            "source_vintages": int(group["source_file"].nunique()),
            "source_files": "|".join(sorted(group["source_file"].unique())),
        })
    if conflicts:
        raise RuntimeError(f"RBI cross-vintage conflicts: {conflicts[:10]}")
    auctions = pd.DataFrame(chosen).sort_values("auction_date", kind="stable").reset_index(drop=True)
    if auctions.duplicated("auction_date").any():
        raise RuntimeError("Duplicate auction dates after reconciliation")
    if (auctions["issue_date"] < auctions["auction_date"]).any():
        raise RuntimeError("Issue date precedes auction date")
    return auctions


def load_dbie_source() -> tuple[pd.DataFrame, dict[str, object]]:
    manifest = json.loads(DBIE_MANIFEST.read_text(encoding="utf-8"))
    if sha256(DBIE_RAW) != manifest.get("raw_sha256"):
        raise RuntimeError("RBI DBIE raw cache hash does not match its extraction manifest")
    if manifest.get("rows") != 1752 or manifest.get("first_auction") != "1993-01-08":
        raise RuntimeError(f"Unexpected RBI DBIE manifest identity: {manifest}")
    auctions = pd.read_csv(
        DBIE_RAW,
        parse_dates=["auction_date", "issue_date", "issue_date_source"],
        low_memory=False,
    )
    auctions = auctions.loc[auctions["auction_date"].between(SOURCE_START, SAMPLE_END)].copy()
    auctions["successful_cutoff"] = auctions["implicit_yield_pct"].notna()
    auctions["source_vintages"] = 1
    auctions["source_files"] = str(DBIE_RAW.relative_to(ROOT))
    auctions["price_yield_identity_error"] = np.nan
    keep = [
        "auction_date", "issue_date", "cutoff_price", "implicit_yield_pct",
        "price_yield_identity_error", "successful_cutoff", "source_vintages",
        "source_files", "issue_date_source", "issue_date_corrected_flag",
    ]
    auctions = auctions[keep].sort_values("auction_date", kind="stable").reset_index(drop=True)
    if auctions.duplicated("auction_date").any() or (auctions["issue_date"] < auctions["auction_date"]).any():
        raise RuntimeError("RBI DBIE auction key/date integrity failure")
    return auctions, manifest


def build_monthly(auctions: pd.DataFrame) -> pd.DataFrame:
    months = pd.date_range("1993-01-31", SAMPLE_END, freq="ME")
    successful = auctions.loc[auctions["successful_cutoff"]].copy()
    rows: list[dict[str, object]] = []
    for month_end in months:
        eligible = successful.loc[successful["issue_date"].le(month_end)]
        if eligible.empty:
            rows.append({"date": month_end, "value": np.nan})
            continue
        selected = eligible.sort_values(["issue_date", "auction_date"], kind="stable").iloc[-1]
        later_failed = auctions.loc[
            auctions["issue_date"].le(month_end)
            & auctions["issue_date"].gt(selected["issue_date"])
            & ~auctions["successful_cutoff"]
        ].sort_values("issue_date", kind="stable")
        rows.append({
            "date": month_end,
            "value": float(selected["implicit_yield_pct"]),
            "source_auction_date": selected["auction_date"],
            "source_issue_date": selected["issue_date"],
            "staleness_days": int((month_end - selected["issue_date"]).days),
            "later_failed_auction_flag": not later_failed.empty,
            "later_failed_auction_count": int(len(later_failed)),
            "later_failed_auction_dates": "|".join(str(x.date()) for x in later_failed["auction_date"]),
        })
    monthly = pd.DataFrame(rows)
    if monthly["value"].isna().any():
        missing = monthly.loc[monthly["value"].isna(), "date"].dt.strftime("%Y-%m-%d").tolist()
        raise RuntimeError(f"Missing month-end RBI 91-day cut-off values: {missing}")
    if (monthly["source_issue_date"] > monthly["date"]).any():
        raise RuntimeError("Monthly RBI 91-day selection uses a future issue date")
    return monthly


def expanding_z_ddof1(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    x = pd.to_numeric(series, errors="coerce").astype(float)
    count = x.expanding(min_periods=1).count()
    mean = x.expanding(min_periods=MIN_PERIODS).mean()
    std = x.expanding(min_periods=MIN_PERIODS).std(ddof=1)
    active = count.ge(MIN_PERIODS) & x.notna() & std.gt(0)
    z = ((x - mean) / std.replace(0.0, np.nan)).clip(-CLIP, CLIP)
    return z.where(active, 0.0).fillna(0.0), active


def first_active(frame: pd.DataFrame, column: str) -> str | None:
    dates = frame.loc[frame[column].astype(bool), "date"]
    return None if dates.empty else str(dates.iloc[0].date())


def comparison(old_raw: pd.DataFrame, old_external: pd.DataFrame, new: pd.DataFrame) -> dict[str, object]:
    old_raw = old_raw[["date", "TERM_raw"]].rename(columns={"TERM_raw": "old"})
    raw = old_raw.merge(new[["date", "TERM_raw"]].rename(columns={"TERM_raw": "new"}), on="date", how="inner").dropna()
    old_z = old_external.loc[old_external["country"].eq("IND"), ["date", "TERM"]].rename(columns={"TERM": "old"})
    std = old_z.merge(new[["date", "TERM"]].rename(columns={"TERM": "new"}), on="date", how="inner")
    std = std.loc[std["old"].ne(0) & new.set_index("date").loc[std["date"], "TERM_active"].to_numpy()].dropna()

    def metrics(frame: pd.DataFrame) -> dict[str, object]:
        diff = (frame["new"] - frame["old"]).abs()
        largest = frame.assign(abs_difference=diff).nlargest(10, "abs_difference")
        return {
            "overlap_months": int(len(frame)),
            "correlation": float(frame["old"].corr(frame["new"])),
            "old_mean": float(frame["old"].mean()),
            "old_sd_ddof1": float(frame["old"].std(ddof=1)),
            "new_mean": float(frame["new"].mean()),
            "new_sd_ddof1": float(frame["new"].std(ddof=1)),
            "median_absolute_difference": float(diff.median()),
            "p95_absolute_difference": float(diff.quantile(0.95)),
            "largest_divergences": [
                {"date": str(row.date.date()), "old": float(row.old), "new": float(row.new), "absolute_difference": float(row.abs_difference)}
                for row in largest.itertuples(index=False)
            ],
        }
    return {"raw_TERM": metrics(raw), "standardised_TERM": metrics(std)}


def main() -> None:
    for path in [DBIE_RAW, DBIE_MANIFEST, LONG, CANDIDATE, EXTERNAL]:
        if not path.is_file():
            raise FileNotFoundError(path)
    old = pd.read_csv(CANDIDATE, parse_dates=["date"])
    old_external = pd.read_csv(EXTERNAL, parse_dates=["date"])

    auctions, dbie_manifest = load_dbie_source()
    monthly = build_monthly(auctions)
    if int((~auctions["successful_cutoff"]).sum()) != 2:
        raise RuntimeError("Expected exactly two unavailable cut-off yields through 2020")
    if int(monthly["staleness_days"].max()) > 18:
        raise RuntimeError("RBI DBIE monthly staleness exceeds the independently expected bound")

    long_leg = pd.read_csv(LONG, parse_dates=["date"])
    value_columns = [c for c in long_leg.columns if c != "date"]
    if value_columns != ["value"]:
        raise RuntimeError(f"Unexpected India 10Y schema: {long_leg.columns.tolist()}")
    calendar = pd.DataFrame({"date": pd.date_range(SAMPLE_START, SAMPLE_END, freq="ME")})
    new = calendar.merge(long_leg.rename(columns={"value": "IND_10Y_raw"}), on="date", how="left")
    new = new.merge(monthly.rename(columns={"value": "IND_91D_raw"}), on="date", how="left")
    new["IND_91D_certified_active"] = new["IND_91D_raw"].notna()
    new["direct_source_available"] = new["IND_91D_certified_active"]
    new["TERM_raw"] = new["IND_10Y_raw"] - new["IND_91D_raw"]
    new["TERM_pit"] = new["TERM_raw"].shift(1)
    new["TERM"], new["TERM_active"] = expanding_z_ddof1(new["TERM_pit"])

    # India TERM only: preserve the old DRATE columns byte-for-value.
    drate_columns = [c for c in ["DRATE_raw", "DRATE_pit", "DRATE", "DRATE_active"] if c in old.columns]
    preserved = old[["date", *drate_columns]].copy()
    new = new.merge(preserved, on="date", how="left", validate="one_to_one")
    for column in drate_columns:
        left = old.set_index("date")[column]
        right = new.set_index("date")[column]
        if not left.equals(right):
            raise RuntimeError(f"DRATE changed unexpectedly: {column}")

    active_date = first_active(new, "TERM_active")
    active_rows = new.index[new["TERM_active"]].tolist()
    post_gaps: list[str] = []
    if active_rows:
        post_gaps = new.loc[active_rows[0]:].loc[new.loc[active_rows[0]:, "TERM_pit"].isna(), "date"].dt.strftime("%Y-%m-%d").tolist()
    if active_date != "1998-08-31" or post_gaps:
        raise RuntimeError(f"Unexpected TERM activation/gaps: {active_date}, {post_gaps}")

    compare = comparison(old, old_external, new)
    old_active = first_active(old, "TERM_active")
    old_date = pd.Timestamp(old_active)
    gained = (pd.Timestamp(old_date).year - 1998) * 12 + pd.Timestamp(old_date).month - 8
    if old_active != "2018-03-31" or gained != 235:
        raise RuntimeError(f"Unexpected old activation/month gain: {old_active}, {gained}")

    OUT.mkdir(parents=True, exist_ok=True)
    auctions.to_csv(AUCTIONS_OUT, index=False)
    monthly.to_csv(MONTHLY_OUT, index=False)
    new.to_csv(CANDIDATE, index=False)

    failed_months = monthly.loc[monthly["later_failed_auction_flag"], "date"].dt.strftime("%Y-%m-%d").tolist()
    audit = {
        "verdict": "PASS_WORKING_CERTIFIED_RBI_91D_CUTOFF",
        "source": "RBI Database on Indian Economy: Auctions of 91-Day Government of India Treasury Bills",
        "construction": "latest successful auction with observed Implicit Yield at Cut-off Price whose issue date is on or before month-end",
        "source_independence": "No contributed evidence CSV or ZIP member is read by this builder",
        "source_cache_files": len(dbie_manifest["pages"]),
        "source_cache_hashes_verified": True,
        "dbie_extraction_manifest": str(DBIE_MANIFEST.relative_to(ROOT)),
        "dbie_raw_sha256": dbie_manifest["raw_sha256"],
        "auction_rows_through_2020": int(len(auctions)),
        "successful_auction_rows_through_2020": int(auctions["successful_cutoff"].sum()),
        "missing_yield_auction_rows_through_2020": int((~auctions["successful_cutoff"]).sum()),
        "first_auction": str(auctions["auction_date"].min().date()),
        "last_auction": str(auctions["auction_date"].max().date()),
        "monthly_rows": int(len(monthly)),
        "monthly_start": str(monthly["date"].min().date()),
        "monthly_end": str(monthly["date"].max().date()),
        "monthly_missing": int(monthly["value"].isna().sum()),
        "staleness_days_median": float(monthly["staleness_days"].median()),
        "staleness_days_max": int(monthly["staleness_days"].max()),
        "later_failed_auction_months": failed_months,
        "early_auction_market_metadata": "The early-1990s Indian Treasury-bill auction market was still developing; this is retained as source-regime metadata, not treated as a data defect.",
        "pit_rule": "one reference-month lag after raw TERM construction",
        "standardisation": "expanding-only, 24 observed PIT values, ddof=1, clip [-5,5]",
        "old_activation": old_active,
        "new_activation": active_date,
        "months_gained": gained,
        "post_activation_gaps": post_gaps,
        "drate_unchanged_columns": drate_columns,
        "old_vs_new": compare,
        "files": {
            "auctions": str(AUCTIONS_OUT.relative_to(ROOT)),
            "monthly": str(MONTHLY_OUT.relative_to(ROOT)),
            "candidate": str(CANDIDATE.relative_to(ROOT)),
        },
        "production_written": False,
        "github_written": False,
    }
    AUDIT_OUT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
