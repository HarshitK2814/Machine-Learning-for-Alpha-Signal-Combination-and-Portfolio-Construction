#!/usr/bin/env python
"""Rebuild a country's weights index from the stage-04 log that produced it.

``outputs/weights/<strategy>/`` is shared across countries and ``paths.latest_run`` resolves by
modification time, so after a second country's stage 04 has run there is nothing on disk that says
which country a weights file belongs to. Stage 04 now writes ``outputs/weights_index/<C>_<aum>.csv``
as it goes, but runs made before that will have left only their log, which names every run id it
wrote. This reconstructs the index from such a log so an older country run stays usable.

    python tools/weights_index.py --log .../cap_1e9_stage04.log --country DEU --aum 1e9

Verify before trusting it: the log must be the one from the run you mean, and ``--expect`` fails
the rebuild if it does not name exactly that many strategies.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RUN_ID = re.compile(r"pf_([A-Za-z0-9_.\-]+?)_(\d{8}_\d{6}_[0-9a-f]{6})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", required=True, type=Path, help="the stage-04 log for that run")
    ap.add_argument("--country", required=True, choices=["DEU", "IND", "JPN"])
    ap.add_argument("--aum", default="1e9", help="tag for the filename, e.g. 1e9")
    ap.add_argument("--expect", type=int, default=None,
                    help="fail unless the log names exactly this many strategies")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    if not args.log.exists():
        print(f"no such log: {args.log}")
        return 2
    text = args.log.read_text(encoding="utf-8", errors="replace")
    pairs = sorted(set(RUN_ID.findall(text)))
    if not pairs:
        print(f"{args.log} names no pf_<strategy>_<run id> artefacts")
        return 2
    # One strategy can appear more than once if the run was restarted; the last id wins, which is
    # the file stage 04 actually left behind.
    latest: dict[str, str] = {}
    for strategy, stamp in pairs:
        latest[strategy] = max(stamp, latest.get(strategy, ""))

    rows, missing = [], []
    for strategy, stamp in sorted(latest.items()):
        run_id = f"pf_{strategy}_{stamp}"
        path = ROOT / "outputs" / "weights" / strategy / f"{run_id}.parquet"
        if not path.exists():
            missing.append(str(path))
        rows.append({"country": args.country, "aum": float(args.aum), "strategy": strategy,
                     "run_id": run_id, "weights": str(path)})
    frame = pd.DataFrame(rows)
    if args.expect is not None and len(frame) != args.expect:
        print(f"refusing to write: log names {len(frame)} strategies, --expect {args.expect}")
        print(frame["strategy"].to_string(index=False))
        return 3
    if missing:
        # A named-but-absent file means this log is not the run that is on disk, and writing the
        # index anyway would hand a downstream exhibit a path that silently resolves to nothing.
        print(f"refusing to write: {len(missing)} named weights files do not exist, e.g.")
        for m in missing[:5]:
            print(f"  {m}")
        return 4

    out = args.out or (ROOT / "outputs" / "weights_index" / f"{args.country}_{args.aum}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    print(frame[["strategy", "run_id"]].to_string(index=False))
    print(f"\n{len(frame)} strategies -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
