"""Resolve the four extreme sigma observations against bounded raw WRDS data.

The audit never clips or replaces a return.  It reconstructs each exact
21-return window and verifies whether the flagged observation can enter a
complete C6 market-input row.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
FLAGGED = ROOT / "data" / "intl_c6" / "audit" / "C6_DAILY_ECONOMIC_OUTLIERS.csv"
RAW = ROOT / "data" / "intl_c6" / "audit" / "C6_SIGMA_OUTLIER_RAW.csv"
OUT = ROOT / "data" / "intl_c6" / "audit" / "C6_SIGMA_OUTLIER_RESOLUTION.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    flagged = pd.read_csv(
        FLAGGED,
        dtype={"gvkey": "string", "iid": "string"},
        parse_dates=["date", "endpoint_date"],
    )
    raw = pd.read_csv(
        RAW,
        dtype={"gvkey": "string", "iid": "string"},
        parse_dates=["datadate"],
    )
    raw = raw.loc[raw["actual_price_row"].astype("string").str.lower().eq("true")].copy()
    raw = raw.sort_values(["gvkey", "iid", "datadate"], kind="stable")

    rows: list[dict[str, object]] = []
    for item in flagged.itertuples(index=False):
        window = raw.loc[
            raw["gvkey"].eq(item.gvkey)
            & raw["iid"].eq(item.iid)
            & raw["datadate"].le(item.endpoint_date)
        ].tail(21)
        returns = pd.to_numeric(window["daily_total_return"], errors="coerce")
        rebuilt = float(returns.std(ddof=1))
        shock = window.loc[returns.abs().ge(0.25)]
        matches = bool(
            returns.notna().sum() == 21
            and np.isclose(rebuilt, float(item.sigma_d), atol=1e-12, rtol=1e-12)
        )
        adv_missing = bool(pd.isna(item.adv_usd))
        rows.append({
            "country": item.country,
            "date": str(item.date.date()),
            "permno": int(item.permno),
            "gvkey": str(item.gvkey),
            "iid": str(item.iid),
            "endpoint_date": str(item.endpoint_date.date()),
            "window_start": str(window["datadate"].min().date()),
            "window_observations": int(returns.notna().sum()),
            "reported_sigma_d": float(item.sigma_d),
            "rebuilt_sigma_d": rebuilt,
            "sigma_matches_raw_window": matches,
            "max_absolute_daily_return": float(returns.abs().max()),
            "shock_dates_abs_return_ge_25pct": [
                str(value.date()) for value in shock["datadate"].tolist()
            ],
            "shock_rows_with_recorded_volume": int(shock["cshtrd"].notna().sum()),
            "adv_usd_missing": adv_missing,
            "complete_market_input_row": bool(
                pd.notna(item.spread) and pd.notna(item.sigma_d) and pd.notna(item.adv_usd)
            ),
            "resolution": (
                "RAW_WINDOW_REPRODUCED__PRESERVE_SIGMA__EXCLUDED_BY_MISSING_STRICT_ADV"
                if matches and adv_missing
                else "UNRESOLVED"
            ),
        })

    resolved = bool(
        len(rows) == 4
        and all(row["sigma_matches_raw_window"] for row in rows)
        and all(row["adv_usd_missing"] for row in rows)
        and not any(row["complete_market_input_row"] for row in rows)
    )
    audit = {
        "verdict": (
            "PASS_RAW_CONFIRMED_PRESERVED_AND_FAIL_CLOSED"
            if resolved
            else "BLOCKED_OUTLIER_REVIEW_INCOMPLETE"
        ),
        "policy": (
            "Do not clip or replace raw total returns. Preserve mechanically correct sigma_d; "
            "the flagged rows remain outside usable C6 because strict ADV is null."
        ),
        "flagged_rows": int(len(flagged)),
        "resolved_rows": int(sum(row["resolution"] != "UNRESOLVED" for row in rows)),
        "rows": rows,
        "inputs": {
            "flagged": {"path": str(FLAGGED.relative_to(ROOT)), "sha256": sha256(FLAGGED)},
            "raw": {"path": str(RAW.relative_to(ROOT)), "sha256": sha256(RAW)},
        },
        "candidate_values_modified": False,
        "production_written": False,
        "github_written": False,
    }
    OUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    if not resolved:
        raise RuntimeError("C6 sigma outlier resolution remains incomplete")


if __name__ == "__main__":
    main()
