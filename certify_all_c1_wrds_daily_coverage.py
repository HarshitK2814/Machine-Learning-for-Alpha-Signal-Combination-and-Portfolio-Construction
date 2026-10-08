"""Certify exact g_secd history for every frozen C1 security.

Only the 13,110 authoritative (gvkey, iid) keys and each security's bounded
C1 history interval (plus 62 pre-start calendar days) are queried.  The server
returns one aggregate row per key; raw daily observations are never downloaded.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pandas as pd
import wrds

from pilot_c6_daily_wrds import discover_wrds_username


ROOT = Path(__file__).resolve().parent
CROSSWALK = ROOT / "data" / "intl_c6" / "staging" / "C1_WRDS_CROSSWALK.csv"
OUT = ROOT / "data" / "intl_c6" / "audit" / "C1_WRDS_ALL_SECURITY_DAILY_COVERAGE.csv"
AUDIT = ROOT / "data" / "intl_c6" / "audit" / "C1_WRDS_ALL_SECURITY_DAILY_COVERAGE_AUDIT.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def key_values(keys: pd.DataFrame) -> str:
    rows = []
    for n, row in enumerate(keys.itertuples(index=False)):
        prefix = "::varchar" if n == 0 else ""
        rows.append(
            "(" + ",".join([
                quote(str(row.country)) + prefix,
                str(int(row.permno)) + ("::bigint" if n == 0 else ""),
                quote(str(row.gvkey).zfill(6)) + prefix,
                quote(str(row.iid)) + prefix,
                quote(str(row.query_start.date())) + ("::date" if n == 0 else ""),
                quote(str(row.query_end.date())) + ("::date" if n == 0 else ""),
            ]) + ")"
        )
    return ",".join(rows)


def query_sql(keys: pd.DataFrame) -> str:
    values = key_values(keys)
    return f"""
with c1_keys(country, permno, gvkey, iid, query_start, query_end) as (
    values {values}
)
select
    k.country, k.permno, k.gvkey, k.iid, k.query_start, k.query_end,
    count(p.gvkey) as daily_rows,
    count(p.prccd) as close_rows,
    count(p.cshtrd) as volume_rows,
    count(*) filter (where p.prcod is not null and p.prchd is not null
                     and p.prcld is not null and p.prccd is not null) as ohlc_rows,
    count(*) filter (where p.prcstd in (3,4,10)) as actual_price_status_rows,
    count(*) filter (where p.prcstd = 5) as carry_forward_status_rows,
    min(p.datadate) as first_daily_date,
    max(p.datadate) as last_daily_date,
    min(p.curcdd) as min_currency,
    max(p.curcdd) as max_currency,
    string_agg(distinct p.curcdd, '|' order by p.curcdd) as currencies,
    string_agg(distinct p.prcstd::text, '|' order by p.prcstd::text) as price_statuses,
    string_agg(distinct p.secstat, '|' order by p.secstat) as security_statuses
from c1_keys k
left join comp_global_daily.g_secd p
  on p.gvkey = k.gvkey and p.iid = k.iid
 and p.datadate between k.query_start and k.query_end
group by k.country, k.permno, k.gvkey, k.iid, k.query_start, k.query_end
order by k.country, k.permno
"""


def main() -> None:
    keys = pd.read_csv(
        CROSSWALK,
        dtype={"country": "string", "permno": "int64", "gvkey": "string", "iid": "string"},
        parse_dates=["c1_first_month", "c1_last_month", "investible_first_month", "investible_last_month"],
    )
    keys["gvkey"] = keys["gvkey"].str.strip().str.zfill(6)
    keys["iid"] = keys["iid"].str.strip()
    keys["query_start"] = keys["c1_first_month"] - pd.Timedelta(days=62)
    keys["query_end"] = keys["c1_last_month"]
    if len(keys) != 13_110 or keys.duplicated(["gvkey", "iid"]).any():
        raise RuntimeError("Frozen C1 crosswalk key contract changed")

    print(f"Querying bounded aggregate coverage for {len(keys):,} exact keys...", flush=True)
    started = time.perf_counter()
    db = wrds.Connection(wrds_username=discover_wrds_username())
    try:
        result = db.raw_sql(
            query_sql(keys[["country", "permno", "gvkey", "iid", "query_start", "query_end"]]),
            date_cols=["query_start", "query_end", "first_daily_date", "last_daily_date"],
        )
    finally:
        db.close()
    elapsed = time.perf_counter() - started

    result["gvkey"] = result["gvkey"].astype("string").str.strip().str.zfill(6)
    result["iid"] = result["iid"].astype("string").str.strip()
    result["permno"] = pd.to_numeric(result["permno"], errors="raise").astype("int64")
    result = keys.merge(
        result,
        on=["country", "permno", "gvkey", "iid", "query_start", "query_end"],
        how="left",
        validate="one_to_one",
    )
    if len(result) != 13_110 or result["daily_rows"].isna().any():
        raise RuntimeError("WRDS aggregate did not return exactly one row per C1 key")

    numeric_counts = ["daily_rows", "close_rows", "volume_rows", "ohlc_rows", "actual_price_status_rows", "carry_forward_status_rows"]
    for col in numeric_counts:
        result[col] = pd.to_numeric(result[col], errors="raise").astype("int64")
    result["has_any_daily"] = result["daily_rows"] > 0
    result["has_actual_price"] = result["actual_price_status_rows"] > 0
    result["has_volume"] = result["volume_rows"] > 0
    result["has_ohlc"] = result["ohlc_rows"] > 0
    result["last_daily_before_c1_end"] = result["last_daily_date"] < result["c1_last_month"]
    result["historical_or_dead_before_2020"] = result["c1_last_month"] < pd.Timestamp("2020-12-31")
    result["historical_or_dead_has_daily"] = result["historical_or_dead_before_2020"] & result["has_any_daily"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT, index=False)

    by_country = []
    for country, g in result.groupby("country", sort=True):
        historical = g["historical_or_dead_before_2020"]
        by_country.append({
            "country": country,
            "securities": int(len(g)),
            "with_any_daily": int(g["has_any_daily"].sum()),
            "with_actual_price": int(g["has_actual_price"].sum()),
            "with_volume": int(g["has_volume"].sum()),
            "with_ohlc": int(g["has_ohlc"].sum()),
            "historical_or_dead": int(historical.sum()),
            "historical_or_dead_with_daily": int(g.loc[historical, "has_any_daily"].sum()),
        })

    no_daily = result.loc[~result["has_any_daily"], [
        "country", "permno", "gvkey", "iid", "c1_first_month", "c1_last_month", "investible_months"
    ]]
    audit = {
        "verdict": "PASS_ALL_C1_KEYS_AGGREGATED" if len(result) == 13_110 else "FAIL",
        "scope": "exact authoritative C1 (gvkey,iid) keys and bounded C1 date intervals; server aggregation only",
        "securities": int(len(result)),
        "mapping_duplicates": int(result.duplicated(["gvkey", "iid"]).sum()),
        "with_any_daily": int(result["has_any_daily"].sum()),
        "without_any_daily": int((~result["has_any_daily"]).sum()),
        "with_actual_price": int(result["has_actual_price"].sum()),
        "with_volume": int(result["has_volume"].sum()),
        "with_ohlc": int(result["has_ohlc"].sum()),
        "historical_or_dead": int(result["historical_or_dead_before_2020"].sum()),
        "historical_or_dead_with_daily": int(result["historical_or_dead_has_daily"].sum()),
        "no_daily_examples": no_daily.head(50).astype(str).to_dict("records"),
        "by_country": by_country,
        "query_elapsed_seconds": elapsed,
        "query_policy": "no raw bulk download; one aggregate row per exact C1 key",
        "input": {"path": str(CROSSWALK.relative_to(ROOT)), "sha256": sha256(CROSSWALK)},
        "output": {"path": str(OUT.relative_to(ROOT)), "sha256": sha256(OUT)},
        "production_written": False,
        "github_written": False,
    }
    AUDIT.write_text(json.dumps(audit, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: audit[k] for k in ["verdict", "securities", "with_any_daily", "without_any_daily", "historical_or_dead", "historical_or_dead_with_daily", "by_country", "query_elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
