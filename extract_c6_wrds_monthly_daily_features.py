from __future__ import annotations

"""Extract monthly C5/C6 daily-data diagnostics from WRDS ``g_secd``.

The extraction is restricted to exact frozen-C1 ``(gvkey, iid)`` keys and to
years in which those keys are investible.  Rolling calculations are performed
on WRDS; only one endpoint/diagnostic row per requested security-month is
cached locally.  Outputs are non-production candidates.
"""

import argparse
import hashlib
import json
import time
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import wrds

from pilot_c6_daily_wrds import discover_wrds_username


VERSION = "C6_WRDS_MONTHLY_DAILY_FEATURES_v3_2026-10-06"
SOURCE = "comp_global_daily.g_secd"
MONTHLY_SOURCE = "comp_global_daily.g_secm"
CROSSWALK = Path("data/intl_c6/staging/C1_WRDS_CROSSWALK.csv")
MONTH_LEDGER = Path("data/intl_c6/staging/C1_INVESTIBLE_MONTHS.csv.gz")
CACHE_DIR = Path("data/intl_c6/cache/monthly_daily_features")
OUT_MASTER = Path("data/intl_c6/staging/C6_WRDS_MONTHLY_DAILY_FEATURES.csv.gz")
OUT_AUDIT = Path("data/intl_c6/audit/C6_WRDS_MONTHLY_DAILY_FEATURES_AUDIT.json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sql_quote(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def key_clause(keys: pd.DataFrame) -> str:
    rows = []
    for index, row in enumerate(
        keys[["gvkey", "iid"]].drop_duplicates().itertuples(index=False)
    ):
        gvkey = sql_quote(str(row.gvkey).zfill(6))
        iid = sql_quote(str(row.iid))
        if index == 0:
            rows.append(f"({gvkey}::varchar,{iid}::varchar)")
        else:
            rows.append(f"({gvkey},{iid})")
    return ",".join(rows)


def daily_sql(year: int, keys: pd.DataFrame) -> str:
    # Sixty-two calendar days safely supplies >21 prior trading observations
    # around the first month-end of each extraction year.
    start = (pd.Timestamp(year=year, month=1, day=1) - timedelta(days=62)).date()
    end = pd.Timestamp(year=year, month=12, day=31).date()
    tuples = key_clause(keys)
    return f"""
with c1_keys(gvkey, iid) as (
    values {tuples}
), fx_ranked as (
    select
        datadate, tocurd, exrattpd, exratd,
        row_number() over (
            partition by datadate, tocurd
            order by case when exrattpd = 'AR' then 0 else 1 end
        ) as fx_rank
    from comp_global_daily.g_exrt_dly
    where datadate between {sql_quote(str(start))} and {sql_quote(str(end))}
      and fromcurd = 'GBP'
      and exrattpd in ('AR', 'CF')
), fx as (
    select datadate, tocurd, exrattpd, exratd
    from fx_ranked
    where fx_rank = 1
), raw as (
    select
        p.gvkey, p.iid, p.datadate, p.prccd, p.prcod, p.prchd, p.prcld,
        cshtrd, cshoc, ajexdi, trfd, curcdd, qunit,
        exchg, fic, isin, sedol, secstat, prcstd,
        fx_local.exrattpd as local_fx_status,
        fx_usd.exrattpd as usd_fx_status,
        case
            when fx_local.exratd > 0 and fx_usd.exratd > 0
            then fx_usd.exratd / fx_local.exratd
        end as usd_per_local,
        case
            when prccd > 0 and ajexdi > 0
            then prccd / ajexdi
        end as adjusted_price,
        case
            when prccd > 0 and ajexdi > 0 and trfd > 0
            then (prccd / ajexdi) * trfd
        end as return_index,
        case
            when prccd > 0 and cshtrd >= 0
            then prccd * cshtrd
        end as notional_reported,
        case
            when prccd > 0 and cshtrd >= 0 and qunit > 0
            then prccd * cshtrd / qunit
        end as notional_qunit,
        case
            when prccd > 0 and cshtrd >= 0 and qunit > 0
             and fx_local.exratd > 0 and fx_usd.exratd > 0
            then (prccd * cshtrd / qunit)
                 * (fx_usd.exratd / fx_local.exratd)
        end as notional_usd
    from {SOURCE} p
    inner join c1_keys k
      on p.gvkey = k.gvkey and p.iid = k.iid
    left join fx fx_local
      on p.datadate = fx_local.datadate and p.curcdd = fx_local.tocurd
    left join fx fx_usd
      on p.datadate = fx_usd.datadate and fx_usd.tocurd = 'USD'
    where p.datadate between {sql_quote(str(start))} and {sql_quote(str(end))}
      and p.prcstd in (3, 4, 10)
), lagged as (
    select
        raw.*,
        lag(datadate) over w as prior_date,
        lag(curcdd) over w as prior_currency,
        lag(adjusted_price) over w as prior_adjusted_price,
        lag(return_index) over w as prior_return_index
    from raw
    window w as (partition by gvkey, iid order by datadate)
), daily as (
    select
        lagged.*,
        case
            when curcdd = prior_currency
             and return_index > 0 and prior_return_index > 0
            then return_index / prior_return_index - 1.0
        end as daily_total_return,
        case
            when curcdd = prior_currency
             and adjusted_price > 0 and prior_adjusted_price > 0
            then adjusted_price / prior_adjusted_price - 1.0
        end as daily_price_return,
        case
            when prchd > 0 and prcld > 0 and prchd >= prcld
            then (prchd - prcld) / ((prchd + prcld) / 2.0)
        end as daily_hl_range,
        datadate - prior_date as observation_gap_days
    from lagged
), rolled as (
    select
        daily.*,
        count(*) over w21 as raw_obs_21,
        count(daily_total_return) over w21 as return_obs_21,
        count(cshtrd) over w21 as volume_obs_21,
        count(daily_hl_range) over w21 as ohlc_obs_21,
        stddev_samp(daily_total_return) over w21 as sigma_total_21,
        stddev_samp(daily_price_return) over w21 as sigma_price_21,
        avg(notional_reported) over w21 as adv_reported_21,
        avg(notional_qunit) over w21 as adv_qunit_21,
        avg(notional_usd) over w21 as adv_usd_21,
        avg(daily_hl_range) over w21 as hl_range_21,
        avg(
            case when notional_qunit > 0
                 then abs(daily_total_return) / notional_qunit end
        ) over w21 as amihud_qunit_21,
        avg(
            case when notional_usd > 0
                 then abs(daily_total_return) / notional_usd end
        ) over w21 as amihud_usd_21,
        max(observation_gap_days) over w21 as max_gap_days_21,
        row_number() over (
            partition by gvkey, iid, date_trunc('month', datadate)
            order by datadate desc
        ) as endpoint_rank,
        count(*) over (
            partition by gvkey, iid, date_trunc('month', datadate)
        ) as month_raw_rows,
        count(prccd) over (
            partition by gvkey, iid, date_trunc('month', datadate)
        ) as month_close_rows,
        count(cshtrd) over (
            partition by gvkey, iid, date_trunc('month', datadate)
        ) as month_volume_rows,
        count(daily_total_return) over (
            partition by gvkey, iid, date_trunc('month', datadate)
        ) as month_return_rows,
        min(datadate) over (
            partition by gvkey, iid, date_trunc('month', datadate)
        ) as month_first_date,
        sum(cshtrd) over (
            partition by gvkey, iid, date_trunc('month', datadate)
        ) as month_sum_cshtrd,
        min(curcdd) over (
            partition by gvkey, iid, date_trunc('month', datadate)
        ) as month_min_currency,
        max(curcdd) over (
            partition by gvkey, iid, date_trunc('month', datadate)
        ) as month_max_currency
    from daily
    window w21 as (
        partition by gvkey, iid order by datadate
        rows between 20 preceding and current row
    )
)
select
    gvkey, iid,
    (date_trunc('month', datadate) + interval '1 month - 1 day')::date
        as month_end,
    datadate as endpoint_date,
    month_first_date, month_raw_rows, month_close_rows,
    month_volume_rows, month_return_rows, month_sum_cshtrd,
    raw_obs_21, return_obs_21, volume_obs_21, ohlc_obs_21,
    sigma_total_21, sigma_price_21,
    adv_reported_21, adv_qunit_21, adv_usd_21,
    hl_range_21, amihud_qunit_21, amihud_usd_21, max_gap_days_21,
    prccd, prcod, prchd, prcld, cshtrd, cshoc,
    ajexdi, trfd, adjusted_price, return_index,
    curcdd, qunit, local_fx_status, usd_fx_status, usd_per_local,
    month_min_currency, month_max_currency,
    exchg, fic, isin, sedol, secstat, prcstd
from rolled
where endpoint_rank = 1
  and datadate between {sql_quote(f'{year}-01-01')} and {sql_quote(f'{year}-12-31')}
order by gvkey, iid, month_end
"""


def monthly_sql(year: int, keys: pd.DataFrame) -> str:
    tuples = key_clause(keys)
    return f"""
with c1_keys(gvkey, iid) as (
    values {tuples}
)
select p.gvkey, p.iid,
       (date_trunc('month', datadate) + interval '1 month - 1 day')::date
           as month_end,
       datadate as monthly_source_date,
       prccm, cshtrm, ajexm, curcdm
from {MONTHLY_SOURCE} p
inner join c1_keys k
  on p.gvkey = k.gvkey and p.iid = k.iid
where p.datadate between {sql_quote(f'{year}-01-01')} and {sql_quote(f'{year}-12-31')}
order by p.gvkey, p.iid, p.datadate
"""


def coerce_keys(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["gvkey"] = out["gvkey"].astype("string").str.strip().str.zfill(6)
    out["iid"] = out["iid"].astype("string").str.strip()
    return out


def extract_year(db: wrds.Connection, year: int, ledger: pd.DataFrame) -> pd.DataFrame:
    requested = ledger.loc[ledger["year"].eq(year)].copy()
    keys = requested[["gvkey", "iid"]].drop_duplicates()
    if requested.empty:
        raise RuntimeError(f"{year}: no requested C1 months")

    started = time.perf_counter()
    daily = db.raw_sql(
        daily_sql(year, keys),
        chunksize=100_000,
        date_cols=["month_end", "endpoint_date", "month_first_date"],
    )
    daily = coerce_keys(daily)
    monthly = db.raw_sql(
        monthly_sql(year, keys),
        chunksize=None,
        date_cols=["month_end", "monthly_source_date"],
    )
    monthly = coerce_keys(monthly)

    if daily.duplicated(["gvkey", "iid", "month_end"]).any():
        raise RuntimeError(f"{year}: duplicate g_secd monthly endpoint")
    if monthly.duplicated(["gvkey", "iid", "month_end"]).any():
        raise RuntimeError(f"{year}: duplicate g_secm monthly row")

    remote = daily.merge(
        monthly,
        on=["gvkey", "iid", "month_end"],
        how="left",
        validate="one_to_one",
    )
    requested["month_end"] = requested["date"]
    out = requested.merge(
        remote,
        on=["gvkey", "iid", "month_end"],
        how="left",
        validate="one_to_one",
        indicator="_wrds_merge",
    )
    out["wrds_month_present"] = out["_wrds_merge"].eq("both")
    out = out.drop(columns=["_wrds_merge", "year"])
    out["query_elapsed_seconds"] = round(time.perf_counter() - started, 3)
    return out


def build_audit(master: pd.DataFrame, cache_paths: list[Path]) -> dict:
    master = master.copy()
    master["month_end"] = pd.to_datetime(master["month_end"])
    master["endpoint_date"] = pd.to_datetime(master["endpoint_date"])
    master["endpoint_staleness_days"] = (
        master["month_end"] - master["endpoint_date"]
    ).dt.days
    master["currency_stable_in_month"] = (
        master["month_min_currency"].notna()
        & master["month_min_currency"].eq(master["month_max_currency"])
    )

    country_rows: dict[str, dict[str, int | float | None]] = {}
    for country, group in master.groupby("country", sort=True):
        present = group["wrds_month_present"].fillna(False)
        country_rows[str(country)] = {
            "requested_investible_months": len(group),
            "wrds_months_present": int(present.sum()),
            "wrds_months_missing": int((~present).sum()),
            "coverage_fraction": float(present.mean()),
            "full_21_return_windows": int(group["return_obs_21"].eq(21).sum()),
            "full_21_volume_windows": int(group["volume_obs_21"].eq(21).sum()),
            "full_21_ohlc_windows": int(group["ohlc_obs_21"].eq(21).sum()),
            "currency_stable_months": int(group["currency_stable_in_month"].sum()),
            "max_endpoint_staleness_days": (
                None
                if group["endpoint_staleness_days"].dropna().empty
                else int(group["endpoint_staleness_days"].max())
            ),
        }

    missing = int((~master["wrds_month_present"].fillna(False)).sum())
    return {
        "version": VERSION,
        "source": SOURCE,
        "monthly_validation_source": MONTHLY_SOURCE,
        "crosswalk_source": str(CROSSWALK),
        "crosswalk_sha256": sha256(CROSSWALK),
        "investible_month_ledger": str(MONTH_LEDGER),
        "investible_month_ledger_sha256": sha256(MONTH_LEDGER),
        "query_scope": "EXACT_FROZEN_C1_GVKEY_IID_BY_INVESTIBLE_YEAR",
        "trading_observation_rule": (
            "g_secd.prcstd in (3,4,10); status 5 carry-forward rows excluded "
            "per comp_global_daily.r_prc_stat"
        ),
        "download_scope": "ONE_SERVER_AGGREGATED_ROW_PER_C1_INVESTIBLE_MONTH",
        "formulas_under_certification": {
            "adjusted_price": "prccd / ajexdi",
            "return_index": "(prccd / ajexdi) * trfd",
            "daily_total_return": "return_index_t / return_index_t-1 - 1; same currency only",
            "sigma_total_21": "sample standard deviation of last 21 daily total returns",
            "adv_reported_21": "mean(prccd * cshtrd), reported volume units",
            "adv_qunit_21": "mean(prccd * cshtrd / qunit), reported volume units",
            "adv_usd_21": (
                "mean((prccd*cshtrd/qunit) * "
                "GBP_to_USD_rate/GBP_to_local_rate)"
            ),
            "hl_range_21": "diagnostic mean 2*(high-low)/(high+low); not final spread",
            "amihud_qunit_21": "diagnostic mean abs(return)/(prccd*cshtrd/qunit)",
            "amihud_usd_21": "diagnostic mean abs(return)/USD_traded_notional",
        },
        "currency_policy": "USD_ADV_USD_AUM",
        "fx_source": "comp_global_daily.g_exrt_dly",
        "fx_rule": (
            "GBP base; USD per local = exratd(GBP->USD) / "
            "exratd(GBP->local); prefer AR, allow same-date vendor CF"
        ),
        "country": country_rows,
        "totals": {
            "requested_investible_months": len(master),
            "wrds_months_present": int(master["wrds_month_present"].fillna(False).sum()),
            "wrds_months_missing": missing,
        },
        "cache_files": [
            {"path": str(p), "sha256": sha256(p), "bytes": p.stat().st_size}
            for p in cache_paths
        ],
        "master_output": str(OUT_MASTER),
        "master_sha256": sha256(OUT_MASTER),
        "production_written": False,
        "github_written": False,
        "verdict": (
            "PASS_EXTRACTION_READY_FOR_SEMANTIC_CERTIFICATION"
            if missing == 0
            else "FAIL_C1_INVESTIBLE_MONTHS_MISSING_WRDS_DAILY_ROWS"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=1990)
    parser.add_argument("--end-year", type=int, default=2020)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--country-chunks",
        action="store_true",
        help="Run separate exact-key queries per country to reduce server sort size.",
    )
    args = parser.parse_args()
    if args.start_year < 1990 or args.end_year > 2020:
        raise ValueError("Certification range must stay within frozen C1 1990-2020")
    if args.start_year > args.end_year:
        raise ValueError("start-year must be <= end-year")

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MASTER.parent.mkdir(parents=True, exist_ok=True)
    OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

    ledger = pd.read_csv(
        MONTH_LEDGER,
        dtype={"country": "string", "permno": "int32", "gvkey": "string", "iid": "string"},
        parse_dates=["date"],
    )
    ledger = coerce_keys(ledger)
    ledger["year"] = ledger["date"].dt.year
    if ledger.duplicated(["country", "date", "permno"]).any():
        raise RuntimeError("Duplicate keys in C1 investible-month ledger")

    years = list(range(args.start_year, args.end_year + 1))
    db: wrds.Connection | None = None
    cache_paths: list[Path] = []
    try:
        for year in years:
            cache_path = CACHE_DIR / f"C6_WRDS_MONTHLY_DAILY_FEATURES_{year}.csv.gz"
            cache_paths.append(cache_path)
            if cache_path.exists() and not args.force:
                cached = pd.read_csv(cache_path, nrows=5)
                required_cache_columns = {
                    "adv_usd_21",
                    "amihud_usd_21",
                    "usd_per_local",
                    "prcstd",
                }
                if not cached.empty and required_cache_columns.issubset(cached.columns):
                    print(f"{year}: cached -> {cache_path}", flush=True)
                    continue
                print(f"{year}: stale cache schema -> rebuilding", flush=True)
            if db is None:
                db = wrds.Connection(wrds_username=discover_wrds_username())
            requested = int(ledger["year"].eq(year).sum())
            unique_keys = int(
                ledger.loc[ledger["year"].eq(year), ["gvkey", "iid"]]
                .drop_duplicates()
                .shape[0]
            )
            print(
                f"{year}: extracting {requested:,} requested months / "
                f"{unique_keys:,} exact keys...",
                flush=True,
            )
            if args.country_chunks:
                country_parts = []
                for country in ("DEU", "IND", "JPN"):
                    country_ledger = ledger.loc[ledger["country"].eq(country)]
                    country_requested = int(country_ledger["year"].eq(year).sum())
                    if country_requested == 0:
                        continue
                    print(
                        f"{year} {country}: extracting "
                        f"{country_requested:,} requested months...",
                        flush=True,
                    )
                    country_parts.append(extract_year(db, year, country_ledger))
                output = pd.concat(country_parts, ignore_index=True)
            else:
                output = extract_year(db, year, ledger)
            if len(output) != requested:
                raise RuntimeError(f"{year}: output/request count mismatch")
            output.to_csv(cache_path, index=False, compression="gzip")
            missing = int((~output["wrds_month_present"]).sum())
            elapsed = float(output["query_elapsed_seconds"].iloc[0])
            print(
                f"{year}: rows={len(output):,}; missing={missing:,}; "
                f"elapsed={elapsed:.1f}s",
                flush=True,
            )
    finally:
        if db is not None:
            db.close()

    # A partial range is useful for benchmarking, but only the full cached set
    # can emit the consolidated certification artefact.
    all_paths = [
        CACHE_DIR / f"C6_WRDS_MONTHLY_DAILY_FEATURES_{year}.csv.gz"
        for year in range(1990, 2021)
    ]
    if not all(p.exists() for p in all_paths):
        print("Partial extraction complete; full 1990-2020 cache not yet present.")
        return

    parts = [
        pd.read_csv(
            path,
            dtype={"country": "string", "permno": "int32", "gvkey": "string", "iid": "string"},
            parse_dates=["date", "month_end", "endpoint_date", "month_first_date", "monthly_source_date"],
        )
        for path in all_paths
    ]
    master = pd.concat(parts, ignore_index=True)
    if len(master) != 757_297:
        raise RuntimeError(f"Expected 757,297 investible months, got {len(master):,}")
    if master.duplicated(["country", "date", "permno"]).any():
        raise RuntimeError("Duplicate consolidated C6 keys")
    master = master.sort_values(["country", "date", "permno"], kind="stable")
    master.to_csv(OUT_MASTER, index=False, compression="gzip")

    audit = build_audit(master, all_paths)
    OUT_AUDIT.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    print("=" * 100)
    print("C6 WRDS MONTHLY DAILY FEATURE EXTRACTION:", audit["verdict"])
    print(json.dumps(audit["totals"], indent=2))
    print("master:", OUT_MASTER)
    print("audit :", OUT_AUDIT)
    print("PRODUCTION WRITTEN: NO")
    print("GITHUB WRITTEN    : NO")
    print("=" * 100)


if __name__ == "__main__":
    main()
