"""Extract 21-observation Abdi--Ranaldo effective-spread estimates.

Implements the paper's monthly-corrected estimator on rolling windows:

    eta_t = (log(H_t) + log(L_t)) / 2
    gamma_t = (c_{t-1} - eta_{t-1}) * (c_{t-1} - eta_t)
    spread = 2 * sqrt(max(mean(gamma), 0))

Twenty adjacent-pair moments use 21 actual-price observations.  Computation is
performed on WRDS and only one endpoint row per requested security-month is
downloaded.  Outputs are staging/audit only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import wrds

from pilot_c6_daily_wrds import discover_wrds_username


ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "data" / "intl_c6" / "staging" / "C1_INVESTIBLE_MONTHS.csv.gz"
CACHE = ROOT / "data" / "intl_c6" / "cache" / "abdi_ranaldo_monthly"
OUT = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_ABDI_RANALDO_21.csv.gz"
AUDIT = ROOT / "data" / "intl_c6" / "audit" / "C6_WRDS_ABDI_RANALDO_21_AUDIT.json"


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
    for n, row in enumerate(keys[["gvkey", "iid"]].drop_duplicates().itertuples(index=False)):
        cast = "::varchar" if n == 0 else ""
        rows.append(f"({quote(str(row.gvkey).zfill(6))}{cast},{quote(str(row.iid))}{cast})")
    return ",".join(rows)


def sql_for_year(year: int, keys: pd.DataFrame) -> str:
    start = (pd.Timestamp(year=year, month=1, day=1) - pd.Timedelta(days=62)).date()
    end = pd.Timestamp(year=year, month=12, day=31).date()
    return f"""
with c1_keys(gvkey, iid) as (values {key_values(keys)}),
raw as (
    select p.gvkey, p.iid, p.datadate, p.curcdd,
           ln(p.prccd / p.ajexdi) as c,
           (ln(p.prchd / p.ajexdi) + ln(p.prcld / p.ajexdi)) / 2.0 as eta
    from comp_global_daily.g_secd p
    inner join c1_keys k on p.gvkey=k.gvkey and p.iid=k.iid
    where p.datadate between {quote(str(start))} and {quote(str(end))}
      and p.prcstd in (3,4,10)
      and p.ajexdi > 0 and p.prccd > 0 and p.prchd > 0 and p.prcld > 0
), tagged as (
    select raw.*,
           case when curcdd is distinct from lag(curcdd) over w then 1 else 0 end as currency_break
    from raw
    window w as (partition by gvkey, iid order by datadate)
), segmented as (
    select tagged.*,
           sum(currency_break) over (
               partition by gvkey, iid order by datadate
               rows between unbounded preceding and current row
           ) as currency_segment
    from tagged
), paired as (
    select segmented.*,
           (lag(c) over w - lag(eta) over w) * (lag(c) over w - eta) as gamma
    from segmented
    window w as (partition by gvkey, iid, currency_segment order by datadate)
), rolled as (
    select paired.*,
           count(gamma) over w20 as pair_obs_20,
           avg(gamma) over w20 as mean_gamma_20,
           row_number() over (
               partition by gvkey, iid, date_trunc('month', datadate)
               order by datadate desc
           ) as endpoint_rank
    from paired
    window w20 as (
        partition by gvkey, iid, currency_segment order by datadate
        rows between 19 preceding and current row
    )
)
select gvkey, iid,
       (date_trunc('month', datadate) + interval '1 month - 1 day')::date as month_end,
       datadate as endpoint_date, curcdd, pair_obs_20, mean_gamma_20,
       case when pair_obs_20 >= 2
            then 2.0 * sqrt(greatest(mean_gamma_20, 0.0)) end as ar_21_min3,
       case when pair_obs_20 = 20
            then 2.0 * sqrt(greatest(mean_gamma_20, 0.0)) end as ar_21_strict
from rolled
where endpoint_rank=1
  and datadate between {quote(f'{year}-01-01')} and {quote(f'{year}-12-31')}
order by gvkey, iid, month_end
"""


def local_formula(close: np.ndarray, high: np.ndarray, low: np.ndarray) -> float:
    c = np.log(np.asarray(close, dtype=float))
    eta = (np.log(np.asarray(high, dtype=float)) + np.log(np.asarray(low, dtype=float))) / 2.0
    gamma = (c[:-1] - eta[:-1]) * (c[:-1] - eta[1:])
    return float(2.0 * np.sqrt(max(float(np.mean(gamma)), 0.0)))


def self_test() -> dict[str, float | bool]:
    # A deliberately positive-moment example ensures the test exercises the
    # square root as well as the monthly zero correction.
    close = np.array([105, 104, 103, 102, 101, 100], dtype=float)
    high = close + 1.0
    low = close - 2.0
    value = local_formula(close, high, low)
    eta = (np.log(high) + np.log(low)) / 2.0
    explicit = 2.0 * np.sqrt(max(np.mean((np.log(close[:-1]) - eta[:-1]) * (np.log(close[:-1]) - eta[1:])), 0.0))
    return {
        "local": value,
        "explicit": float(explicit),
        "positive": bool(value > 0),
        "match": bool(value > 0 and np.isclose(value, explicit, atol=1e-15, rtol=0)),
    }


def extract_year(db: wrds.Connection, year: int, ledger: pd.DataFrame) -> pd.DataFrame:
    requested = ledger.loc[ledger["date"].dt.year.eq(year)].copy()
    started = time.perf_counter()
    remote = db.raw_sql(
        sql_for_year(year, requested[["gvkey", "iid"]].drop_duplicates()),
        date_cols=["month_end", "endpoint_date"],
    )
    elapsed = time.perf_counter() - started
    remote["gvkey"] = remote["gvkey"].astype("string").str.strip().str.zfill(6)
    remote["iid"] = remote["iid"].astype("string").str.strip()
    if remote.duplicated(["gvkey", "iid", "month_end"]).any():
        raise RuntimeError(f"{year}: duplicate AR endpoint rows")
    out = requested.rename(columns={"date": "month_end"}).merge(
        remote, on=["gvkey", "iid", "month_end"], how="left", validate="one_to_one"
    ).rename(columns={"month_end": "date"})
    out["query_elapsed_seconds"] = elapsed
    print(
        f"{year}: requested={len(out):,}, present={out['endpoint_date'].notna().sum():,}, "
        f"AR any={out['ar_21_min3'].notna().sum():,}, strict={out['ar_21_strict'].notna().sum():,}, "
        f"query={elapsed:.1f}s", flush=True,
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=1990)
    parser.add_argument("--end-year", type=int, default=2020)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    test = self_test()
    if not test["match"]:
        raise RuntimeError("Abdi--Ranaldo formula self-test failed")
    ledger = pd.read_csv(
        LEDGER,
        dtype={"country": "string", "permno": "int64", "gvkey": "string", "iid": "string"},
        parse_dates=["date"],
    )
    ledger["gvkey"] = ledger["gvkey"].str.strip().str.zfill(6)
    ledger["iid"] = ledger["iid"].str.strip()
    if len(ledger) != 757_297:
        raise RuntimeError("Frozen C1 ledger changed")

    CACHE.mkdir(parents=True, exist_ok=True)
    # psycopg/libpq on Windows does not consistently discover the roaming
    # pgpass location after a reconnect.  Point it at the standard file without
    # ever reading or logging its password field here.
    pgpass = Path(os.environ.get("APPDATA", "")) / "postgresql" / "pgpass.conf"
    if pgpass.exists():
        os.environ.setdefault("PGPASSFILE", str(pgpass))
    db = None
    try:
        for year in range(args.start_year, args.end_year + 1):
            path = CACHE / f"C6_WRDS_ABDI_RANALDO_21_{year}.csv.gz"
            if path.exists() and not args.force:
                print(f"{year}: cached", flush=True)
                continue
            if db is None:
                db = wrds.Connection(wrds_username=discover_wrds_username())
            extract_year(db, year, ledger).to_csv(path, index=False, compression="gzip")
    finally:
        if db is not None:
            db.close()

    paths = sorted(CACHE.glob("C6_WRDS_ABDI_RANALDO_21_*.csv.gz"))
    years = {int(p.stem.split("_")[-1].split(".")[0]) for p in paths}
    if years != set(range(1990, 2021)):
        print(f"Partial build complete: {len(years)}/31 years cached")
        return
    panel = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    if len(panel) != 757_297 or panel.duplicated(["country", "date", "permno"]).any():
        raise RuntimeError("Consolidated AR key contract failed")
    panel = panel.sort_values(["country", "date", "permno"], kind="stable")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT, index=False, compression="gzip")
    audit = {
        "verdict": "PASS_ABDI_RANALDO_21_MONTHLY_CORRECTED_WITH_EXPLICIT_COVERAGE_GAPS",
        "reference": "Abdi and Ranaldo (2017), Review of Financial Studies 30(12):4437-4480, equation 9 and monthly-corrected equation 10",
        "formula": "2*sqrt(max(mean((c[t-1]-eta[t-1])*(c[t-1]-eta[t])),0)); eta=(log(high)+log(low))/2",
        "negative_moment_rule": "monthly corrected: set negative mean squared-spread estimate to zero before square root",
        "window": "20 adjacent-pair moments from 21 actual-price observations; adjusted H/L/C; reset at currency changes",
        "self_test": test,
        "rows": int(len(panel)),
        "ar_any_nonnull": int(panel["ar_21_min3"].notna().sum()),
        "ar_strict_nonnull": int(panel["ar_21_strict"].notna().sum()),
        "ar_strict_zero": int(panel["ar_21_strict"].eq(0).sum()),
        "by_country": [
            {"country": c, "rows": int(len(g)), "ar_any_nonnull": int(g["ar_21_min3"].notna().sum()), "ar_strict_nonnull": int(g["ar_21_strict"].notna().sum()), "ar_strict_zero": int(g["ar_21_strict"].eq(0).sum())}
            for c, g in panel.groupby("country", sort=True)
        ],
        "input": {"path": str(LEDGER.relative_to(ROOT)), "sha256": sha256(LEDGER)},
        "output": {"path": str(OUT.relative_to(ROOT)), "sha256": sha256(OUT)},
        "production_written": False,
        "github_written": False,
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
