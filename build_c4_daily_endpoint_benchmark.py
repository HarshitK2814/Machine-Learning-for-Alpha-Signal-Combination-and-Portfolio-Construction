from __future__ import annotations

"""Extract the independent C4 daily endpoint benchmark for C6 certification."""

import hashlib
import json
from pathlib import Path

import pandas as pd


VERSION = "C4_DAILY_ENDPOINT_BENCHMARK_v1_2026-10-06"
RAW = Path("data/intl_c4/raw/intl_c4_real_base_1990_2020.sas7bdat")
LEDGER = Path("data/intl_c6/staging/C1_INVESTIBLE_MONTHS.csv.gz")
OUT = Path("data/intl_c6/staging/C4_DAILY_ENDPOINT_BENCHMARK.parquet")
OUT_CSV = Path("data/intl_c6/staging/C4_DAILY_ENDPOINT_BENCHMARK.csv.gz")
AUDIT = Path("data/intl_c6/audit/C4_DAILY_ENDPOINT_BENCHMARK_AUDIT.json")

KEEP = [
    "id",
    "excntry",
    "eom",
    "daily_raw_rows",
    "daily_valid_rows",
    "daily_endpoint_date",
    "daily_exchg",
    "daily_prcstd",
    "daily_curcd",
    "daily_adj_price",
    "daily_trfd",
    "daily_ri_local",
    "has_daily_endpoint",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ledger = pd.read_csv(
        LEDGER,
        usecols=["country", "date", "permno", "gvkey", "iid"],
        dtype={
            "country": "string",
            "permno": "int32",
            "gvkey": "string",
            "iid": "string",
        },
        parse_dates=["date"],
    )
    if len(ledger) != 757_297:
        raise RuntimeError("Frozen C1 investible-month ledger changed")
    if ledger.duplicated(["country", "date", "permno"]).any():
        raise RuntimeError("Duplicate C1 investible keys")

    keys = ledger.rename(
        columns={"country": "excntry", "date": "eom", "permno": "id"}
    )
    parts: list[pd.DataFrame] = []
    raw_rows = 0
    reader = pd.read_sas(
        RAW,
        format="sas7bdat",
        encoding="utf-8",
        chunksize=250_000,
    )
    for chunk_number, chunk in enumerate(reader, start=1):
        raw_rows += len(chunk)
        missing = set(KEEP) - set(chunk.columns)
        if missing:
            raise RuntimeError(f"Raw C4 archive missing columns: {sorted(missing)}")
        work = chunk[KEEP].copy()
        work["id"] = pd.to_numeric(work["id"], errors="raise").astype("int32")
        work["eom"] = pd.to_datetime(work["eom"], errors="raise")
        work["excntry"] = work["excntry"].astype("string").str.strip()
        selected = keys.merge(
            work,
            on=["excntry", "eom", "id"],
            how="inner",
            validate="one_to_one",
        )
        parts.append(selected)
        print(
            f"chunk {chunk_number}: raw={len(chunk):,}; "
            f"investible={len(selected):,}",
            flush=True,
        )

    benchmark = pd.concat(parts, ignore_index=True)
    if raw_rows != 2_283_562:
        raise RuntimeError(f"Expected 2,283,562 raw C4 rows, got {raw_rows:,}")
    if len(benchmark) != 757_297:
        raise RuntimeError(
            f"Expected 757,297 benchmark rows, got {len(benchmark):,}"
        )
    if benchmark.duplicated(["excntry", "eom", "id"]).any():
        raise RuntimeError("Duplicate C4 benchmark keys")

    valid = benchmark[
        ["daily_adj_price", "daily_trfd", "daily_ri_local"]
    ].notna().all(axis=1)
    identity_error = (
        benchmark.loc[valid, "daily_adj_price"]
        * benchmark.loc[valid, "daily_trfd"]
        - benchmark.loc[valid, "daily_ri_local"]
    ).abs()
    max_identity_error = float(identity_error.max()) if valid.any() else None
    if max_identity_error is None or max_identity_error > 1e-12:
        raise RuntimeError("C4 return-index identity failed")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    try:
        benchmark.to_parquet(OUT, index=False)
    except ImportError:
        if not OUT.exists():
            raise
        print("Parquet engine unavailable; preserving the existing certified Parquet output")
    # Keep a compressed CSV mirror so certification is not coupled to an
    # optional Parquet engine in the runtime used for subsequent audits.
    benchmark.to_csv(OUT_CSV, index=False, compression="gzip")
    payload = {
        "version": VERSION,
        "raw_source": str(RAW),
        "raw_source_sha256": sha256(RAW),
        "investible_ledger": str(LEDGER),
        "investible_ledger_sha256": sha256(LEDGER),
        "raw_rows": raw_rows,
        "benchmark_rows": len(benchmark),
        "valid_return_index_rows": int(valid.sum()),
        "return_index_identity": "daily_adj_price * daily_trfd = daily_ri_local",
        "max_identity_error": max_identity_error,
        "output": str(OUT),
        "output_sha256": sha256(OUT),
        "output_csv": str(OUT_CSV),
        "output_csv_sha256": sha256(OUT_CSV),
        "production_written": False,
        "github_written": False,
        "verdict": "PASS_C4_DAILY_ENDPOINT_BENCHMARK",
    }
    AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("=" * 92)
    print("C4 DAILY ENDPOINT BENCHMARK: PASS")
    print("rows:", f"{len(benchmark):,}")
    print("valid return-index rows:", f"{int(valid.sum()):,}")
    print("max identity error:", max_identity_error)
    print("output:", OUT)
    print("audit :", AUDIT)
    print("=" * 92)


if __name__ == "__main__":
    main()
