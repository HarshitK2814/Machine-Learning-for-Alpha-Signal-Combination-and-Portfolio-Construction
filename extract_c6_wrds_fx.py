from __future__ import annotations

"""Extract the compact Compustat daily FX panel needed by international C6."""

import hashlib
import json
from pathlib import Path

import pandas as pd
import wrds

from pilot_c6_daily_wrds import discover_wrds_username


VERSION = "C6_WRDS_FX_v1_2026-10-06"
CURRENCIES = ("DEM", "EUR", "FIM", "INR", "JPY", "USD", "ZAR")
OUT = Path("data/intl_c6/cache/C6_WRDS_DAILY_FX_TO_USD.csv.gz")
AUDIT = Path("data/intl_c6/audit/C6_WRDS_DAILY_FX_TO_USD_AUDIT.json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    currency_sql = ",".join(f"'{x}'" for x in CURRENCIES)
    db = wrds.Connection(wrds_username=discover_wrds_username())
    try:
        raw = db.raw_sql(
            "select datadate, tocurd, exrattpd, exratd "
            "from comp_global_daily.g_exrt_dly "
            "where datadate between '1989-10-01' and '2020-12-31' "
            "and fromcurd='GBP' "
            f"and tocurd in ({currency_sql}) "
            "and exrattpd in ('AR','CF') "
            "order by datadate, tocurd, "
            "case when exrattpd='AR' then 0 else 1 end",
            chunksize=None,
            date_cols=["datadate"],
        )
    finally:
        db.close()

    raw = raw.drop_duplicates(["datadate", "tocurd"], keep="first")
    if raw.duplicated(["datadate", "tocurd"]).any():
        raise RuntimeError("Duplicate FX date/currency keys")
    usd = raw.loc[raw["tocurd"].eq("USD"), ["datadate", "exratd"]].rename(
        columns={"exratd": "gbp_to_usd"}
    )
    out = raw.merge(usd, on="datadate", how="left", validate="many_to_one")
    out["usd_per_local"] = out["gbp_to_usd"] / out["exratd"]
    out = out.rename(
        columns={
            "tocurd": "currency",
            "exrattpd": "local_rate_status",
            "exratd": "gbp_to_local",
        }
    )
    invalid = out["usd_per_local"].isna() | (out["usd_per_local"] <= 0)
    if invalid.any():
        bad = out.loc[
            invalid
        ]
        print("invalid FX rows by currency:")
        print(bad.groupby("currency", dropna=False).size().to_string())
        print(bad.head(30).to_string(index=False))
    usd_error = (
        out.loc[out["currency"].eq("USD"), "usd_per_local"].dropna() - 1.0
    ).abs()
    if usd_error.max() > 1e-12:
        raise RuntimeError("USD self-conversion identity failed")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False, compression="gzip")
    payload = {
        "version": VERSION,
        "source": "comp_global_daily.g_exrt_dly",
        "rate_type_reference": "comp_global_daily.r_exrt_typ",
        "base_currency": "GBP",
        "currencies": list(CURRENCIES),
        "formula": "USD per local = GBP-to-USD / GBP-to-local",
        "status_rule": "prefer AR; allow same-date vendor CF",
        "rows": len(out),
        "rows_missing_usd_leg": int(invalid.sum()),
        "missing_usd_leg_dates": sorted(
            str(x.date()) for x in out.loc[invalid, "datadate"].drop_duplicates()
        ),
        "first_date": str(out["datadate"].min().date()),
        "last_date": str(out["datadate"].max().date()),
        "output": str(OUT),
        "output_sha256": sha256(OUT),
        "production_written": False,
        "github_written": False,
        "verdict": "PASS_WRDS_DAILY_FX_TO_USD_WITH_EXPLICIT_SOURCE_DATE_GAPS",
    }
    AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("WRDS DAILY FX: PASS")
    print("rows:", f"{len(out):,}")
    print("dates:", payload["first_date"], "->", payload["last_date"])
    print("output:", OUT)


if __name__ == "__main__":
    main()
