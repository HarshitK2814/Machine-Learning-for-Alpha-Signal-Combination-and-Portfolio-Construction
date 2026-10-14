#!/usr/bin/env python
"""Rebuild a country's stage-02 source index from the model manifests.

Why this exists
---------------
`outputs/source_index/<COUNTRY>.csv` is what lets every later stage resolve *this country's*
scores, instead of falling back to `paths.latest_run`, which resolves by modification time and
silently returns whichever country trained a cell most recently. That hazard has already produced
eight wrong exhibits in this project.

The index was written with `to_csv`, i.e. **overwritten**, by each stage-02 invocation. A country
whose cells are trained by more than one invocation - a split `--manifest`, a resumed run, one cell
re-run at a different setting - therefore ended up with only the last invocation's strategies.
Japan was left with 7 rows and **none of the eight prediction cells** that amendments 001C and
001D make predictions about. Stage 02 now merges (see `pipelines/02_train_models.py`), but a run
already in flight under the old code will still clobber the file when it finishes, and historical
indexes are already wrong.

What this does
--------------
Reads every `outputs/manifest_models*.csv`, selects rows whose ``source`` is ``real_<COUNTRY>`` and
whose ``status`` is ``ok``, infers ``kind`` from the artefact path exactly as stage 02 does, keeps
the newest artefact per (strategy, kind), and writes the index. Existing index rows are merged in
rather than discarded, so running this can only ever add information.

It verifies that every artefact it names exists on disk, and refuses to write an index that would
claim a missing file.

Usage
-----
    python tools/repair_source_index.py --country JPN
    python tools/repair_source_index.py --country JPN --dry-run
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def rebuild(country: str, outputs: Path, dry_run: bool = False) -> pd.DataFrame:
    manifests = sorted(outputs.glob("manifest_models*.csv"))
    if not manifests:
        raise SystemExit(f"no manifest_models*.csv under {outputs}")

    want = f"real_{country}"
    rows: list[dict] = []
    for m in manifests:
        try:
            d = pd.read_csv(m)
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] could not read {m.name}: {exc}")
            continue
        if "source" not in d.columns:
            continue
        sel = d[(d["source"].astype(str) == want) & (d.get("status").astype(str) == "ok")]
        if sel.empty:
            continue
        print(f"  {m.name}: {len(sel)} ok rows for {country}")
        for _, r in sel.iterrows():
            artefact = r.get("artefact")
            if not isinstance(artefact, str) or not artefact:
                continue
            text = artefact.replace("\\", "/")
            kind = "weight_proposals" if "/weight_proposals/" in text else "predictions"
            rows.append({"country": country,
                         "strategy": r.get("strategy") or r.get("cell"),
                         "kind": kind, "artefact": artefact, "rows": r.get("rows")})

    index = outputs / "source_index" / f"{country}.csv"
    if index.exists():
        try:
            prior = pd.read_csv(index)
            print(f"  existing index: {len(prior)} rows, merged in")
            rows = prior.to_dict("records") + rows
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] existing index unreadable ({exc}); rebuilding from manifests only")

    if not rows:
        raise SystemExit(f"nothing found for {country}; is the stage-02 run finished?")

    out = pd.DataFrame(rows)
    # Newest artefact wins. run_id embeds a sortable timestamp, and the artefact path carries it,
    # so sorting on the artefact string orders runs correctly within a strategy.
    out = (out.sort_values("artefact")
              .drop_duplicates(subset=["country", "strategy", "kind"], keep="last")
              .sort_values(["kind", "strategy"])
              .reset_index(drop=True))

    missing = [a for a in out["artefact"] if not Path(a).exists()]
    if missing:
        print(f"\n  REFUSING TO WRITE: {len(missing)} named artefact(s) do not exist on disk:")
        for a in missing[:10]:
            print(f"    {a}")
        raise SystemExit("index would claim files that are not there")

    print(f"\n  {len(out)} strategies for {country}:")
    for kind, g in out.groupby("kind"):
        print(f"    {kind}: {', '.join(sorted(g['strategy'].astype(str)))}")
    pred = [s for s in out["strategy"].astype(str) if "-P-" in s]
    print(f"\n  prediction cells present: {len(pred)} ({', '.join(sorted(pred)) or 'NONE'})")

    if dry_run:
        print("\n  --dry-run: nothing written")
        return out
    index.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(index, index=False)
    print(f"\n  wrote {index}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", nargs="+", required=True)
    ap.add_argument("--outputs", type=Path, default=ROOT / "outputs")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    for c in a.country:
        print(f"\n=== {c} ===")
        rebuild(c, a.outputs, a.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
