#!/usr/bin/env python
"""Record the exact artefact chain behind a factorial exhibit (one row per cell).

Every stage of this pipeline resolves its input by "newest file in the strategy's folder", and
those folders accumulate runs - a synthetic dress rehearsal, an earlier country, a re-run of a
single cell. That is convenient while developing and indefensible in a paper: the exhibit is a
function of which file each stage happened to pick, and nothing in the exhibit itself records it.

This writes that resolution down. For each of the 16 cells it reports the model artefact, the C11
weights and the C12 returns that a run *now* would consume, each with a sha256, a row count and a
date range, plus the data_source stamp the backtest wrote into the returns. Re-running it after
the exhibit is regenerated and diffing the two manifests answers the only question that matters
for reproducibility: did the inputs move?

    python tools/exhibit_provenance.py --out outputs/e29/e29_artefact_chain.csv
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts import paths  # noqa: E402

CELLS = [f"{n}-{c}-{e}-{u}" for n in "LN" for c in "SC" for e in "PE" for u in ("0", "U")]


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def newest(kind: str, strategy: str) -> Path | None:
    folder = paths.outputs_root() / kind / strategy
    if not folder.exists():
        return None
    files = sorted(folder.glob("*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def describe(kind: str, strategy: str) -> dict:
    path = newest(kind, strategy)
    if path is None:
        return {f"{kind}_file": None, f"{kind}_sha256": None, f"{kind}_rows": None}
    df = pd.read_parquet(path)
    out = {
        f"{kind}_file": path.name,
        f"{kind}_sha256": sha256(path)[:16],
        f"{kind}_rows": len(df),
    }
    if "date" in df.columns and len(df):
        d = pd.to_datetime(df["date"])
        out[f"{kind}_first"] = str(d.min().date())
        out[f"{kind}_last"] = str(d.max().date())
    if "data_source" in df.columns and len(df):
        out[f"{kind}_source"] = str(df["data_source"].iloc[0])
    # How many cells' artefacts sit beside the chosen one; >1 means the folder holds history and
    # the choice is mtime-dependent rather than unique.
    out[f"{kind}_siblings"] = len(list(path.parent.glob("*.parquet")))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "e29" / "e29_artefact_chain.csv")
    args = ap.parse_args(argv)

    rows = []
    for code in CELLS:
        strategy = f"cell_{code}"
        row = {"cell": code}
        # Economic-loss cells emit weight proposals (C10); prediction cells emit C9. Whichever
        # exists is the model artefact for that cell.
        model = describe("predictions", strategy)
        if model["predictions_file"] is None:
            model = {k.replace("predictions", "model"): v for k, v in
                     describe("weight_proposals", strategy).items()}
            model["model_kind"] = "weight_proposals"
        else:
            model = {k.replace("predictions", "model"): v for k, v in model.items()}
            model["model_kind"] = "predictions"
        row.update(model)
        row.update(describe("weights", strategy))
        row.update(describe("returns", strategy))
        rows.append(row)

    frame = pd.DataFrame(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)

    cols = ["cell", "model_kind", "model_rows", "weights_rows", "returns_rows", "returns_source",
            "returns_first", "returns_last"]
    cols = [c for c in cols if c in frame.columns]
    print(frame[cols].to_string(index=False))
    print(f"\nwrote {args.out}")

    srcs = sorted(frame["returns_source"].dropna().unique()) if "returns_source" in frame else []
    if len(srcs) > 1:
        print(f"WARNING: returns span several sources: {', '.join(srcs)}")
    missing = frame.loc[frame["returns_file"].isna(), "cell"].tolist() if "returns_file" in frame else []
    if missing:
        print(f"WARNING: no returns for {len(missing)} cells: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
