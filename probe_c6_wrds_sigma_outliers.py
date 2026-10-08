"""Fetch a bounded raw-data audit for the four extreme C6 sigma observations.

The query is restricted to the three implicated (gvkey, iid) keys and their
short review intervals.  It writes audit artefacts only and changes no
candidate values.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import wrds

from pilot_c6_daily_wrds import discover_wrds_username


ROOT = Path(__file__).resolve().parent
OUTLIERS = ROOT / "data" / "intl_c6" / "audit" / "C6_DAILY_ECONOMIC_OUTLIERS.csv"
OUT = ROOT / "data" / "intl_c6" / "audit" / "C6_SIGMA_OUTLIER_RAW.csv"
AUDIT = ROOT / "data" / "intl_c6" / "audit" / "C6_SIGMA_OUTLIER_RAW_AUDIT.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    flagged = pd.read_csv(OUTLIERS, dtype={"gvkey": "string", "iid": "string"}, parse_dates=["date", "endpoint_date"])
    flagged["gvkey"] = flagged["gvkey"].str.zfill(6)
    # The flagged securities can be extremely thin.  A fixed 75-calendar-day
    # review did not contain the 21 actual-price observations used by sigma_d
    # for one key, so retain a bounded but sufficiently wide lookback.
    flagged["start_date"] = flagged["date"] - pd.Timedelta("400 days")
    intervals = (
        flagged.groupby(["gvkey", "iid"], as_index=False)
        .agg(start_date=("start_date", "min"), end_date=("endpoint_date", "max"))
    )
    values = ",".join(
        f"({quote(row.gvkey)}::varchar,{quote(row.iid)}::varchar,{quote(str(row.start_date.date()))}::date,{quote(str(row.end_date.date()))}::date)"
        for row in intervals.itertuples(index=False)
    )
    sql = f"""
with review_keys(gvkey, iid, start_date, end_date) as (values {values})
select p.gvkey, p.iid, p.datadate, p.curcdd, p.prcstd,
       p.prccd, p.prcod, p.prchd, p.prcld, p.ajexdi, p.trfd,
       p.cshtrd, p.qunit
from comp_global_daily.g_secd p
inner join review_keys k on p.gvkey=k.gvkey and p.iid=k.iid
where p.datadate between k.start_date and k.end_date
order by p.gvkey, p.iid, p.datadate
"""

    pgpass = Path(os.environ.get("APPDATA", "")) / "postgresql" / "pgpass.conf"
    if pgpass.exists():
        os.environ.setdefault("PGPASSFILE", str(pgpass))
    db = wrds.Connection(wrds_username=discover_wrds_username())
    try:
        raw = db.raw_sql(sql, date_cols=["datadate"])
    finally:
        db.close()
    raw["gvkey"] = raw["gvkey"].astype("string").str.strip().str.zfill(6)
    raw["iid"] = raw["iid"].astype("string").str.strip()
    raw["actual_price_row"] = raw["prcstd"].isin([3, 4, 10]) & raw["prccd"].gt(0) & raw["ajexdi"].gt(0) & raw["trfd"].gt(0)
    raw["adjusted_price"] = np.where(raw["actual_price_row"], raw["prccd"] / raw["ajexdi"], np.nan)
    raw["return_index"] = raw["adjusted_price"] * raw["trfd"]
    raw["daily_total_return"] = pd.Series(pd.NA, index=raw.index, dtype="Float64")
    actual = raw.loc[raw["actual_price_row"]].copy()
    actual["daily_total_return"] = actual.groupby(["gvkey", "iid", "curcdd"], sort=False)["return_index"].pct_change(fill_method=None)
    raw.loc[actual.index, "daily_total_return"] = actual["daily_total_return"]
    raw["absolute_daily_return"] = raw["daily_total_return"].abs()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    raw.to_csv(OUT, index=False)

    largest = (
        raw.nlargest(20, "absolute_daily_return")
        [["gvkey", "iid", "datadate", "curcdd", "prcstd", "prccd", "ajexdi", "trfd", "adjusted_price", "return_index", "daily_total_return"]]
        .replace({np.nan: None})
        .to_dict(orient="records")
    )
    audit = {
        "verdict": "PASS_BOUNDED_RAW_REVIEW_EXTRACTED",
        "scope": "three exact C1 keys implicated by four sigma_d>=1 observations",
        "keys": int(len(intervals)),
        "rows": int(len(raw)),
        "actual_price_rows": int(raw["actual_price_row"].sum()),
        "max_absolute_daily_return": float(raw["absolute_daily_return"].max()),
        "largest_return_rows": largest,
        "review_rule": "inspect adjustment-factor and price transitions; do not clip or alter candidate values automatically",
        "input": {"path": str(OUTLIERS.relative_to(ROOT)), "sha256": sha256(OUTLIERS)},
        "output": {"path": str(OUT.relative_to(ROOT)), "sha256": sha256(OUT)},
        "production_written": False,
        "github_written": False,
    }
    AUDIT.write_text(json.dumps(audit, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, default=str))


if __name__ == "__main__":
    main()
