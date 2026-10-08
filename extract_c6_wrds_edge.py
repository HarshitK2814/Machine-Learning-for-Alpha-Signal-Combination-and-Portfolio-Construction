"""Build monthly 21-trading-observation EDGE spreads for C1 investible keys.

Uses the authors' ``bidask`` Python implementation of Ardia, Guidotti, and
Kroencke (JFE 2024).  WRDS extraction is exact-key, annual, and raw rows are
discarded after monthly endpoint estimates are cached.  No production writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from importlib.metadata import version as package_version
from pathlib import Path

import numpy as np
import pandas as pd
import wrds
from bidask import edge, edge_rolling

from pilot_c6_daily_wrds import discover_wrds_username


ROOT = Path(__file__).resolve().parent
LEDGER = ROOT / "data" / "intl_c6" / "staging" / "C1_INVESTIBLE_MONTHS.csv.gz"
CACHE = ROOT / "data" / "intl_c6" / "cache" / "edge_monthly"
MARKET_CACHE = ROOT / "data" / "intl_c6" / "cache" / "market_daily"
FX_PATH = ROOT / "data" / "intl_c6" / "cache" / "C6_WRDS_DAILY_FX_TO_USD.csv.gz"
OUT = ROOT / "data" / "intl_c6" / "staging" / "C6_WRDS_EDGE_21.csv.gz"
MARKET_OUT = ROOT / "data" / "intl_c6" / "staging" / "C5_WRDS_MARKET_DAILY.csv.gz"
AUDIT = ROOT / "data" / "intl_c6" / "audit" / "C6_WRDS_EDGE_21_AUDIT.json"


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
with c1_keys(gvkey, iid) as (values {key_values(keys)})
select p.gvkey, p.iid, p.datadate, p.prcod, p.prchd, p.prcld, p.prccd,
       p.cshoc, p.ajexdi, p.trfd, p.qunit, p.curcdd, p.prcstd
from comp_global_daily.g_secd p
inner join c1_keys k on p.gvkey=k.gvkey and p.iid=k.iid
where p.datadate between {quote(str(start))} and {quote(str(end))}
  and p.prcstd in (3,4,10)
order by p.gvkey, p.iid, p.datadate
"""


def add_edge(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("datadate", kind="stable").copy()
    currency = group["curcdd"].astype("string").fillna("<MISSING>")
    currency_change = currency.ne(currency.shift()).fillna(True)
    group["currency_segment"] = currency_change.cumsum()
    out_parts = []
    for _, segment in group.groupby("currency_segment", sort=False):
        # WRDS may return nullable pandas extension dtypes; the authors'
        # reference implementation expects ordinary NumPy NaN semantics.
        ohlc = segment[["open", "high", "low", "close"]].astype("float64")
        segment = segment.copy()
        # Minimum-three result supports transparent coverage diagnostics.  The
        # contract candidate below is additionally restricted to 21 complete
        # OHLC observations and therefore never uses a partial window.
        segment["edge_21_min3"] = edge_rolling(ohlc, window=21, min_periods=3).to_numpy()
        valid_ohlc = ohlc.notna().all(axis=1).astype("int8")
        segment["ohlc_complete_21"] = valid_ohlc.rolling(21, min_periods=1).sum().to_numpy()
        segment["trading_rows_21"] = pd.Series(1, index=segment.index).rolling(21, min_periods=1).sum().to_numpy()
        segment["edge_21_strict"] = segment["edge_21_min3"].where(
            (segment["trading_rows_21"] == 21) & (segment["ohlc_complete_21"] == 21)
        )
        out_parts.append(segment)
    return pd.concat(out_parts, ignore_index=False).sort_values("datadate", kind="stable")


def extract_year(
    db: wrds.Connection, year: int, ledger: pd.DataFrame, fx: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    requested = ledger.loc[ledger["date"].dt.year.eq(year)].copy()
    # Daily country-index membership in calendar month M is frozen at the end
    # of M-1.  This avoids selecting constituents using information from later
    # in the 21-day state window.
    membership = ledger.loc[
        ledger["date"].between(
            pd.Timestamp(year=year - 1, month=12, day=31),
            pd.Timestamp(year=year, month=11, day=30),
        )
    ].copy()
    membership["active_month"] = membership["date"] + pd.offsets.MonthEnd(1)
    keys = pd.concat(
        [requested[["gvkey", "iid"]], membership[["gvkey", "iid"]]],
        ignore_index=True,
    ).drop_duplicates()
    started = time.perf_counter()
    raw = db.raw_sql(sql_for_year(year, keys), date_cols=["datadate"])
    elapsed = time.perf_counter() - started
    raw["gvkey"] = raw["gvkey"].astype("string").str.strip().str.zfill(6)
    raw["iid"] = raw["iid"].astype("string").str.strip()
    raw["curcdd"] = raw["curcdd"].astype("string").str.strip()
    if raw.duplicated(["gvkey", "iid", "datadate"]).any():
        raise RuntimeError(f"{year}: duplicate daily key/date rows")

    factor = pd.to_numeric(raw["ajexdi"], errors="coerce")
    factor = factor.where(factor > 0)
    for source, target in [("prcod", "open"), ("prchd", "high"), ("prcld", "low"), ("prccd", "close")]:
        price = pd.to_numeric(raw[source], errors="coerce").where(lambda x: x > 0)
        raw[target] = price / factor

    raw = raw.merge(
        fx,
        left_on=["datadate", "curcdd"],
        right_on=["datadate", "currency"],
        how="left",
        validate="many_to_one",
    )
    raw["return_index_usd"] = raw["close"] * pd.to_numeric(raw["trfd"], errors="coerce") * raw["usd_per_local"]
    raw["market_cap_usd"] = (
        pd.to_numeric(raw["prccd"], errors="coerce")
        * pd.to_numeric(raw["cshoc"], errors="coerce")
        / pd.to_numeric(raw["qunit"], errors="coerce").where(lambda x: x > 0)
        * raw["usd_per_local"]
    )

    parts = []
    for _, group in raw.groupby(["gvkey", "iid"], sort=False):
        parts.append(add_edge(group))
    daily = pd.concat(parts, ignore_index=True) if parts else raw.assign(
        edge_21_min3=np.nan, edge_21_strict=np.nan, ohlc_complete_21=0, trading_rows_21=0
    )
    daily = daily.sort_values(["gvkey", "iid", "datadate"], kind="stable")
    same_security = (
        daily["gvkey"].eq(daily["gvkey"].shift())
        & daily["iid"].eq(daily["iid"].shift())
        & daily["curcdd"].eq(daily["curcdd"].shift())
    )
    daily["daily_total_return_usd"] = (
        daily["return_index_usd"] / daily["return_index_usd"].shift() - 1.0
    ).where(same_security)
    daily["prior_market_cap_usd"] = daily["market_cap_usd"].shift().where(same_security)
    daily["month_end"] = daily["datadate"] + pd.offsets.MonthEnd(0)
    endpoints = (
        daily.loc[daily["datadate"].dt.year.eq(year)]
        .sort_values("datadate", kind="stable")
        .drop_duplicates(["gvkey", "iid", "month_end"], keep="last")
    )
    keep = [
        "gvkey", "iid", "month_end", "datadate", "curcdd", "edge_21_min3",
        "edge_21_strict", "ohlc_complete_21", "trading_rows_21",
    ]
    out = requested.rename(columns={"date": "month_end"}).merge(
        endpoints[keep], on=["gvkey", "iid", "month_end"], how="left", validate="one_to_one"
    )
    out = out.rename(columns={"month_end": "date", "datadate": "endpoint_date"})
    out["query_elapsed_seconds"] = elapsed

    market_rows = daily.loc[daily["datadate"].dt.year.eq(year)].copy()
    market_rows["active_month"] = market_rows["datadate"] + pd.offsets.MonthEnd(0)
    market_rows = market_rows.merge(
        membership[["country", "permno", "gvkey", "iid", "active_month"]],
        on=["gvkey", "iid", "active_month"],
        how="inner",
        validate="many_to_one",
    )
    market_rows = market_rows.loc[
        market_rows["daily_total_return_usd"].notna()
        & market_rows["prior_market_cap_usd"].gt(0)
    ].copy()
    market_rows["weighted_return"] = (
        market_rows["daily_total_return_usd"] * market_rows["prior_market_cap_usd"]
    )
    market = (
        market_rows.groupby(["country", "datadate"], sort=True)
        .agg(
            weighted_return_sum=("weighted_return", "sum"),
            prior_market_cap_usd=("prior_market_cap_usd", "sum"),
            constituents=("permno", "nunique"),
        )
        .reset_index()
    )
    expected = (
        membership.groupby(["country", "active_month"], sort=True)["permno"]
        .nunique().rename("expected_constituents").reset_index()
    )
    market["active_month"] = market["datadate"] + pd.offsets.MonthEnd(0)
    market = market.merge(expected, on=["country", "active_month"], how="left", validate="many_to_one")
    market["constituent_participation"] = market["constituents"] / market["expected_constituents"]
    # Remove exchange-holiday artefacts where only a handful of cross-listed
    # or off-calendar securities report.  The 50% breadth rule is observable
    # contemporaneously and is retained in the audit columns.
    market = market.loc[market["constituent_participation"] >= 0.50].copy()
    market["market_vw_return_usd"] = market["weighted_return_sum"] / market["prior_market_cap_usd"]
    market["membership_rule"] = "prior_month_end_C1_investible_and_at_least_50pct_constituent_participation"
    print(
        f"{year}: raw={len(raw):,}, requested={len(out):,}, "
        f"EDGE any={out['edge_21_min3'].notna().sum():,}, strict={out['edge_21_strict'].notna().sum():,}, "
        f"query={elapsed:.1f}s",
        flush=True,
    )
    return out, market


def reference_self_test() -> dict[str, float | bool]:
    frame = pd.DataFrame({
        "open": [100, 101, 100, 102, 104, 103],
        "high": [102, 103, 102, 105, 106, 105],
        "low": [99, 99.5, 98, 101, 102, 101],
        "close": [101, 100, 101.5, 104, 103, 104.5],
    }, dtype=float)
    direct = edge(frame.open, frame.high, frame.low, frame.close)
    rolling = float(edge_rolling(frame, window=len(frame)).iloc[-1])
    return {"direct": direct, "rolling": rolling, "match": bool(np.isclose(direct, rolling, rtol=0, atol=1e-15))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=1990)
    parser.add_argument("--end-year", type=int, default=2020)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    ledger = pd.read_csv(
        LEDGER,
        dtype={"country": "string", "permno": "int64", "gvkey": "string", "iid": "string"},
        parse_dates=["date"],
    )
    ledger["gvkey"] = ledger["gvkey"].str.strip().str.zfill(6)
    ledger["iid"] = ledger["iid"].str.strip()
    if len(ledger) != 757_297 or ledger.duplicated(["country", "date", "permno"]).any():
        raise RuntimeError("Frozen C1 investible ledger contract changed")
    test = reference_self_test()
    if not test["match"]:
        raise RuntimeError("Official EDGE direct/rolling reference self-test failed")

    fx = pd.read_csv(
        FX_PATH,
        dtype={"currency": "string"},
        parse_dates=["datadate"],
        usecols=["datadate", "currency", "usd_per_local"],
    )
    fx["currency"] = fx["currency"].str.strip()
    CACHE.mkdir(parents=True, exist_ok=True)
    MARKET_CACHE.mkdir(parents=True, exist_ok=True)
    db = None
    try:
        for year in range(args.start_year, args.end_year + 1):
            path = CACHE / f"C6_WRDS_EDGE_21_{year}.csv.gz"
            market_path = MARKET_CACHE / f"C5_MARKET_DAILY_{year}.csv.gz"
            if path.exists() and market_path.exists() and not args.force:
                print(f"{year}: cached", flush=True)
                continue
            if db is None:
                db = wrds.Connection(wrds_username=discover_wrds_username())
            edge_year, market_year = extract_year(db, year, ledger, fx)
            edge_year.to_csv(path, index=False, compression="gzip")
            market_year.to_csv(market_path, index=False, compression="gzip")
    finally:
        if db is not None:
            db.close()

    paths = sorted(CACHE.glob("C6_WRDS_EDGE_21_*.csv.gz"))
    years = {int(p.stem.split("_")[-1].split(".")[0]) for p in paths}
    if years != set(range(1990, 2021)):
        print(f"Partial build complete: {len(years)}/31 years cached")
        return
    panel = pd.concat([
        pd.read_csv(p, dtype={"country": "string", "permno": "int64", "gvkey": "string", "iid": "string"})
        for p in paths
    ], ignore_index=True)
    if len(panel) != 757_297 or panel.duplicated(["country", "date", "permno"]).any():
        raise RuntimeError("Consolidated EDGE key contract failed")
    panel = panel.sort_values(["country", "date", "permno"], kind="stable")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT, index=False, compression="gzip")
    market_paths = sorted(MARKET_CACHE.glob("C5_MARKET_DAILY_*.csv.gz"))
    market_years = {int(p.stem.split("_")[-1].split(".")[0]) for p in market_paths}
    if market_years != set(range(1990, 2021)):
        raise RuntimeError(f"Expected 31 market daily caches, found {len(market_years)}")
    market_panel = pd.concat([pd.read_csv(p) for p in market_paths], ignore_index=True)
    market_panel = market_panel.sort_values(["country", "datadate"], kind="stable")
    if market_panel.duplicated(["country", "datadate"]).any():
        raise RuntimeError("Duplicate country/date market returns")
    market_panel.to_csv(MARKET_OUT, index=False, compression="gzip")
    audit = {
        "verdict": "PASS_EDGE_21_REFERENCE_IMPLEMENTATION_WITH_EXPLICIT_COVERAGE_GAPS",
        "estimator": "EDGE effective spread, unsigned root-mean-square estimate",
        "reference": "Ardia, Guidotti, and Kroencke (2024), Journal of Financial Economics 161:103916",
        "implementation": "authors' bidask Python package",
        "bidask_version": package_version("bidask"),
        "reference_self_test": test,
        "window": "21 actual-price observations; prcstd in (3,4,10); adjusted OHLC; reset at currency changes",
        "rows": int(len(panel)),
        "edge_any_nonnull": int(panel["edge_21_min3"].notna().sum()),
        "edge_strict_nonnull": int(panel["edge_21_strict"].notna().sum()),
        "by_country": [
            {
                "country": c,
                "rows": int(len(g)),
                "edge_any_nonnull": int(g["edge_21_min3"].notna().sum()),
                "edge_strict_nonnull": int(g["edge_21_strict"].notna().sum()),
            }
            for c, g in panel.groupby("country", sort=True)
        ],
        "input": {"path": str(LEDGER.relative_to(ROOT)), "sha256": sha256(LEDGER)},
        "output": {"path": str(OUT.relative_to(ROOT)), "sha256": sha256(OUT)},
        "market_daily_output": {
            "path": str(MARKET_OUT.relative_to(ROOT)),
            "sha256": sha256(MARKET_OUT),
            "rows": int(len(market_panel)),
            "definition": "prior-month C1 investible membership; lagged daily USD market-cap weights; USD total returns",
        },
        "production_written": False,
        "github_written": False,
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
