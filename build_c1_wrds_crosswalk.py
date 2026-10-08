from __future__ import annotations

"""Build the authoritative frozen-C1 to WRDS security crosswalk.

This is a non-production C6 staging/audit build.  The synthetic C1 ``permno``
is preserved exactly, while ``gvkey`` and ``iid`` come only from the frozen C1
audit lineage.  No country/FIC inference is used.
"""

import hashlib
import json
from pathlib import Path

import pandas as pd


VERSION = "C1_WRDS_CROSSWALK_v1_2026-10-05"
COUNTRIES = ("DEU", "IND", "JPN")
EXPECTED_ROWS = {"DEU": 273_068, "IND": 755_806, "JPN": 1_254_688}
EXPECTED_INVESTIBLE = {"DEU": 122_784, "IND": 71_646, "JPN": 562_867}
EXPECTED_SECURITIES = {"DEU": 1_858, "IND": 5_449, "JPN": 5_803}

C1_ROOT = Path("data/intl_c1/production")
OUT_DIR = Path("data/intl_c6/staging")
AUDIT_DIR = Path("data/intl_c6/audit")
OUT_CROSSWALK = OUT_DIR / "C1_WRDS_CROSSWALK.csv"
OUT_MONTHS = OUT_DIR / "C1_INVESTIBLE_MONTHS.csv.gz"
OUT_AUDIT = AUDIT_DIR / "C1_WRDS_CROSSWALK_AUDIT.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def clean_key(series: pd.Series, width: int | None = None) -> pd.Series:
    out = series.astype("string").str.strip()
    if width is not None:
        out = out.str.zfill(width)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    crosswalk_parts: list[pd.DataFrame] = []
    investible_parts: list[pd.DataFrame] = []
    inputs: dict[str, dict[str, str | int]] = {}
    country_audit: dict[str, dict[str, int | str]] = {}

    for country in COUNTRIES:
        universe_path = C1_ROOT / country / "universe.parquet"
        audit_path = C1_ROOT / country / "c1_audit.parquet"

        universe = pd.read_parquet(
            universe_path,
            columns=["date", "permno", "in_universe"],
        )
        lineage = pd.read_parquet(
            audit_path,
            columns=["id", "gvkey", "iid"],
        )

        universe["date"] = pd.to_datetime(universe["date"], errors="raise")
        universe["permno"] = pd.to_numeric(
            universe["permno"], errors="raise"
        ).astype("int32")
        universe["in_universe"] = universe["in_universe"].astype(bool)

        lineage["id"] = pd.to_numeric(lineage["id"], errors="raise").astype(
            "int32"
        )
        lineage["gvkey"] = clean_key(lineage["gvkey"], 6)
        lineage["iid"] = clean_key(lineage["iid"])
        lineage = lineage.drop_duplicates().reset_index(drop=True)

        if len(universe) != EXPECTED_ROWS[country]:
            raise RuntimeError(f"{country}: frozen C1 row count changed")
        if int(universe["in_universe"].sum()) != EXPECTED_INVESTIBLE[country]:
            raise RuntimeError(f"{country}: frozen investible count changed")
        if universe["permno"].nunique() != EXPECTED_SECURITIES[country]:
            raise RuntimeError(f"{country}: frozen security count changed")
        if universe.duplicated(["date", "permno"]).any():
            raise RuntimeError(f"{country}: duplicate C1 keys")
        if lineage[["id", "gvkey", "iid"]].isna().any().any():
            raise RuntimeError(f"{country}: null lineage key")
        if lineage.groupby("id").size().max() != 1:
            raise RuntimeError(f"{country}: one permno maps to multiple WRDS keys")
        if lineage.groupby(["gvkey", "iid"]).size().max() != 1:
            raise RuntimeError(f"{country}: one WRDS key maps to multiple permnos")

        universe_ids = set(universe["permno"].astype(int))
        lineage_ids = set(lineage["id"].astype(int))
        if universe_ids != lineage_ids:
            raise RuntimeError(
                f"{country}: universe/lineage identifier sets differ; "
                f"missing={len(universe_ids-lineage_ids)}, "
                f"extra={len(lineage_ids-universe_ids)}"
            )

        spans = (
            universe.groupby("permno", as_index=False)
            .agg(
                c1_first_month=("date", "min"),
                c1_last_month=("date", "max"),
                c1_months=("date", "size"),
                investible_months=("in_universe", "sum"),
            )
        )
        investible_spans = (
            universe.loc[universe["in_universe"]]
            .groupby("permno", as_index=False)
            .agg(
                investible_first_month=("date", "min"),
                investible_last_month=("date", "max"),
            )
        )
        spans = spans.merge(
            investible_spans,
            on="permno",
            how="left",
            validate="one_to_one",
        )

        country_crosswalk = (
            lineage.rename(columns={"id": "permno"})
            .merge(spans, on="permno", how="inner", validate="one_to_one")
        )
        country_crosswalk.insert(0, "country", country)
        crosswalk_parts.append(country_crosswalk)

        investible = universe.loc[
            universe["in_universe"], ["date", "permno"]
        ].merge(
            country_crosswalk[["permno", "gvkey", "iid"]],
            on="permno",
            how="left",
            validate="many_to_one",
        )
        investible.insert(0, "country", country)
        investible_parts.append(investible)

        inputs[country] = {
            "universe": str(universe_path),
            "universe_sha256": sha256(universe_path),
            "audit": str(audit_path),
            "audit_sha256": sha256(audit_path),
        }
        country_audit[country] = {
            "c1_rows": len(universe),
            "investible_rows": int(universe["in_universe"].sum()),
            "securities": len(country_crosswalk),
            "ever_investible_securities": int(
                (country_crosswalk["investible_months"] > 0).sum()
            ),
            "mapping_conflicts": 0,
        }

    crosswalk = pd.concat(crosswalk_parts, ignore_index=True)
    investible = pd.concat(investible_parts, ignore_index=True)

    if len(crosswalk) != 13_110:
        raise RuntimeError(f"Expected 13,110 crosswalk rows, got {len(crosswalk):,}")
    if len(investible) != 757_297:
        raise RuntimeError(
            f"Expected 757,297 investible months, got {len(investible):,}"
        )
    if crosswalk.duplicated(["country", "permno"]).any():
        raise RuntimeError("Duplicate country/permno crosswalk keys")
    if crosswalk.duplicated(["country", "gvkey", "iid"]).any():
        raise RuntimeError("Duplicate country/WRDS crosswalk keys")
    if investible.duplicated(["country", "date", "permno"]).any():
        raise RuntimeError("Duplicate investible-month keys")

    date_cols = [
        "c1_first_month",
        "c1_last_month",
        "investible_first_month",
        "investible_last_month",
    ]
    for col in date_cols:
        crosswalk[col] = pd.to_datetime(crosswalk[col]).dt.strftime("%Y-%m-%d")
    investible["date"] = investible["date"].dt.strftime("%Y-%m-%d")

    crosswalk.to_csv(OUT_CROSSWALK, index=False)
    investible.to_csv(OUT_MONTHS, index=False, compression="gzip")

    output = {
        "version": VERSION,
        "authoritative_source": "FROZEN_C1_PRODUCTION_AUDIT_GVKEY_IID",
        "fic_used_for_mapping": False,
        "inputs": inputs,
        "country": country_audit,
        "totals": {
            "c1_rows": sum(EXPECTED_ROWS.values()),
            "investible_rows": len(investible),
            "securities": len(crosswalk),
            "mapping_conflicts": 0,
        },
        "outputs": {
            "crosswalk": str(OUT_CROSSWALK),
            "crosswalk_sha256": sha256(OUT_CROSSWALK),
            "investible_months": str(OUT_MONTHS),
            "investible_months_sha256": sha256(OUT_MONTHS),
        },
        "production_written": False,
        "github_written": False,
        "verdict": "PASS_C1_WRDS_CROSSWALK_READY_FOR_DAILY_CERTIFICATION",
    }
    OUT_AUDIT.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("=" * 92)
    print("C1 <-> WRDS CROSSWALK: PASS")
    print("securities       :", f"{len(crosswalk):,}")
    print("investible months:", f"{len(investible):,}")
    print("mapping conflicts:", 0)
    print("crosswalk        :", OUT_CROSSWALK)
    print("month ledger     :", OUT_MONTHS)
    print("audit            :", OUT_AUDIT)
    print("PRODUCTION WRITTEN: NO")
    print("GITHUB WRITTEN    : NO")
    print("=" * 92)


if __name__ == "__main__":
    main()
