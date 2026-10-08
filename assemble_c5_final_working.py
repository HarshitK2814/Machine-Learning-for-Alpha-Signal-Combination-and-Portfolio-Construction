"""Assemble the complete per-country C5 working contract.

The daily/external block supplies MKTVOL, ILLIQ, SENT, CREDIT, TERM, INFL and
DRATE.  The previously built internal block supplies BEAR, DISP and FMOM_*.
No state is recomputed here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from alphacomb.contracts import validate


ROOT = Path(__file__).resolve().parent
FULL = ROOT / "data" / "intl_c5" / "candidate_daily_market_working" / "C5_FULL_WORKING_CANDIDATE.csv"
INTERNAL = ROOT / "data" / "intl_c5" / "internal"
OUT = ROOT / "data" / "intl_c5" / "candidate_final_working"
AUDIT = OUT / "C5_FINAL_WORKING_AUDIT.json"
COUNTRIES = ["DEU", "IND", "JPN"]
CORE = ["date", "MKTVOL", "BEAR", "ILLIQ", "SENT", "CREDIT", "TERM", "INFL", "DRATE", "DISP"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    external = pd.read_csv(FULL, parse_dates=["date"])
    outputs: list[dict[str, object]] = []
    OUT.mkdir(parents=True, exist_ok=True)
    for country in COUNTRIES:
        internal_path = INTERNAL / country / "states_internal.parquet"
        internal = pd.read_parquet(internal_path)
        internal["date"] = pd.to_datetime(internal["date"])
        fmom = sorted(column for column in internal.columns if column.startswith("FMOM_"))
        if len(fmom) != 13:
            raise RuntimeError(f"{country}: expected 13 FMOM states, found {len(fmom)}")
        left = external.loc[external["country"].eq(country), ["date", "MKTVOL", "ILLIQ", "SENT", "CREDIT", "TERM", "INFL", "DRATE"]]
        right = internal[["date", "BEAR", "DISP", *fmom]]
        out = left.merge(right, on="date", how="outer", validate="one_to_one").sort_values("date", kind="stable")
        out = out[[*CORE, *fmom]].reset_index(drop=True)
        if len(out) != 372 or out["date"].min() != pd.Timestamp("1990-01-31") or out["date"].max() != pd.Timestamp("2020-12-31"):
            raise RuntimeError(f"{country}: incomplete C5 calendar")
        if not np.isfinite(out.drop(columns="date").to_numpy(dtype=float)).all():
            raise RuntimeError(f"{country}: non-finite C5 state")
        if not set(out["BEAR"].unique()).issubset({0.0, 1.0}):
            raise RuntimeError(f"{country}: BEAR is not binary")
        validate(out, "states")
        path = OUT / country / "states.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        out.to_parquet(path, index=False)
        outputs.append({
            "country": country,
            "rows": len(out),
            "columns": len(out.columns),
            "fmom_columns": len(fmom),
            "term_first_nonzero": str(out.loc[out["TERM"].ne(0), "date"].min().date()),
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
        })
    audit = {
        "verdict": "PASS_COMPLETE_C5_WORKING_CONTRACT",
        "construction": "mechanical merge only; certified daily/external states plus frozen internal BEAR/DISP/FMOM states",
        "source_daily_external": {"path": str(FULL.relative_to(ROOT)), "sha256": sha256(FULL)},
        "outputs": outputs,
        "contract_validation": "PASS C5 states schema for every country",
        "production_written": False,
        "github_written": False,
    }
    AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
