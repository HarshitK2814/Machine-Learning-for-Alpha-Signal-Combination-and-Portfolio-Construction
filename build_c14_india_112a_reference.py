"""Build the non-production C14 India section 112A reference-price contract.

The source is the already-certified WRDS daily cache.  No network access or new
market extraction is permitted.  Income-tax Act section 55(2)(ac) defines FMV
as the highest exchange-quoted price on 31 January 2018, or on the immediately
preceding traded date if the security did not trade that day.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.tax.dated import SecurityReferenceValueStore


SOURCE = ROOT / "data/intl_c6/cache/monthly_daily_features/C6_WRDS_MONTHLY_DAILY_FEATURES_2018.csv.gz"
OUTPUT = ROOT / "data/intl_c14/candidate_working/IND_SECTION_112A_REFERENCE_VALUES.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    usecols = ["country", "date", "permno", "endpoint_date", "prccd", "prchd", "curcdd"]
    frame = pd.read_csv(SOURCE, usecols=usecols, parse_dates=["date", "endpoint_date"])
    frame = frame.loc[frame["country"].eq("IND") & frame["date"].eq(pd.Timestamp("2018-01-31"))].copy()
    if frame.empty or frame["permno"].duplicated().any():
        raise RuntimeError("India 31-Jan-2018 cache slice is empty or has duplicate securities")
    if frame[["prccd", "prchd", "endpoint_date"]].isna().any().any():
        raise RuntimeError("India 31-Jan-2018 statutory price inputs are incomplete")
    if frame["endpoint_date"].gt(pd.Timestamp("2018-01-31")).any():
        raise RuntimeError("forward-looking section 112A endpoint")
    if not frame["curcdd"].eq("INR").all():
        raise RuntimeError("section 112A cache slice is not uniformly INR")
    if (frame["prchd"] < frame["prccd"]).any() or (frame[["prchd", "prccd"]] <= 0).any().any():
        raise RuntimeError("invalid daily high/close relationship")

    relative = SOURCE.relative_to(ROOT).as_posix()
    digest = sha256(SOURCE)
    out = pd.DataFrame({
        "country": "IND",
        "permno": frame["permno"].astype("int64"),
        "reference_date": "2018-01-31",
        "fmv_price_local": frame["prchd"].astype(float),
        "close_price_local": frame["prccd"].astype(float),
        "currency": "INR",
        "source_field": "prchd",
        "source_cache": relative,
        "source_cache_sha256": digest,
        "statutory_definition": SecurityReferenceValueStore.INDIA_112A_DEFINITION,
        "endpoint_date": frame["endpoint_date"].dt.strftime("%Y-%m-%d"),
    }).sort_values("permno")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False)
    validated = SecurityReferenceValueStore.from_validated_csv(OUTPUT)
    if len(validated) != len(out):
        raise RuntimeError("reference contract round-trip count mismatch")
    print(f"wrote {len(out)} validated section 112A reference rows to {OUTPUT}")


if __name__ == "__main__":
    main()
