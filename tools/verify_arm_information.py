#!/usr/bin/env python
"""Does each factorial arm's stage-02 output actually carry information about returns?

Why this exists
---------------
The factorial's only significant main effect is the **economic** one, and it is negative: the
economic-loss cells lose to the prediction-loss cells by 0.0054 p.a. in Germany and 0.0063 in
India. That is only a statement about *objectives* if both arms learned something. If one arm
learned nothing, the "main effect" is measuring a training failure wearing the label of a design
axis, and no amount of downstream care fixes it.

So this measures the one thing that distinguishes those cases, and it is scale-free: the rank
correlation between each cell's stage-02 output and the realised next-month return. A
prediction-loss cell emits a score; an economic-loss cell emits a proposed weight. Either way, if
it has skill its cross-section should rank next month's winners above its losers.

On the India panel (2026-10-09) the answer was unambiguous:

    P arm  8 cells  mean IC +0.0368   every t between +2.85 and +5.42
    E arm  8 cells  mean IC -0.0061   every t between -1.91 and +0.40, 7 of 8 NEGATIVE

See ``docs/ECONOMIC_ARM_DOES_NOT_LEARN.md``.

Reading artefacts without trusting modification time
----------------------------------------------------
``outputs/predictions/<cell>/`` and ``outputs/weight_proposals/<cell>/`` are shared across
countries and ``paths.latest_run`` resolves by modification time, so "the latest artefact" for a
cell means whichever country ran stage 02 most recently. The first version of this diagnostic was
itself caught by that - three cells silently compared *Japan's* scores against India's targets and
returned zero overlapping months. Artefacts are therefore taken from the country's own stage-02
log, which names every file it wrote.

    python tools/verify_arm_information.py --country IND --log .../ind_stage02.log
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def artefacts_from_log(path: Path) -> dict[str, str]:
    """Map cell name -> the artefact that run wrote, parsed from its own log."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if " -> " not in line or "rows," not in line:
            continue
        head, rest = line.split(" -> ", 1)
        name = head.split("INFO ")[-1].strip()
        artefact = rest.rsplit(" (", 1)[0].strip()
        if artefact.endswith(".parquet"):
            out[name] = artefact
    return out


def information_coefficient(path: str, kind: str, targets: pd.DataFrame) -> tuple:
    from alphacomb.contracts import read_table
    from scipy.stats import spearmanr

    frame = read_table(path, kind)
    col = ("score" if "score" in frame.columns
           else [c for c in frame.columns if c not in ("date", "permno", "unc_sd")][0])
    f = frame[["date", "permno", col]].copy()
    f["date"] = pd.to_datetime(f["date"])
    merged = f.merge(targets, on=["date", "permno"], how="inner").dropna(subset=[col, "ret_next"])
    per_month = [spearmanr(g[col].to_numpy(), g["ret_next"].to_numpy()).statistic
                 for _, g in merged.groupby("date") if len(g) > 10]
    vals = np.array([v for v in per_month if np.isfinite(v)])
    if not len(vals):
        return np.nan, np.nan, 0, col
    return vals.mean(), vals.std(ddof=1), len(vals), col


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--country", required=True, choices=["DEU", "IND", "JPN"])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--log", type=Path,
                     help="that country's stage-02 log, which names the artefacts it wrote")
    src.add_argument("--from-weights-index", action="store_true",
                     help="resolve artefacts via outputs/weights_index/<C>_<aum>.csv and the "
                          "portfolio manifest's source_artefact. This is the authoritative route: "
                          "it names exactly the stage-02 outputs the published portfolios "
                          "consumed, rather than whatever a log happened to write.")
    ap.add_argument("--aum", default="1e9", help="which weights index to read")
    ap.add_argument("--max-names", type=int, default=None,
                    help="must match the stage-02 run (amendment 001B)")
    ap.add_argument("--min-ic-t", type=float, default=1.96,
                    help="an arm is reported as not having learned below this |t|")
    args = ap.parse_args(argv)

    from alphacomb.contracts import intl

    if args.from_weights_index:
        index = ROOT / "outputs" / "weights_index" / f"{args.country}_{args.aum}.csv"
        manifest = ROOT / "outputs" / "manifest_portfolios.csv"
        if not index.exists():
            print(f"no weights index at {index}")
            return 2
        want = set(pd.read_csv(index)["run_id"])
        man = pd.read_csv(manifest)
        man = man[man["run_id"].isin(want)]
        artefacts = {}
        for _, r in man.iterrows():
            strategy = str(r["strategy"])
            if not strategy.startswith("cell_"):
                continue
            artefacts[strategy.removeprefix("cell_")] = str(r["source_artefact"])
        print(f"{args.country}: {len(artefacts)} cells resolved from {index.name} via the "
              f"portfolio manifest (the artefacts the published portfolios actually consumed)")
    else:
        if not args.log.exists():
            print(f"no such log: {args.log}")
            return 2
        artefacts = artefacts_from_log(args.log)
        print(f"{args.country}: {len(artefacts)} stage-02 artefacts named by the run's own log")
    if not artefacts:
        print("no stage-02 artefacts resolved")
        return 2

    bundle = intl.load_country_bundle(args.country, max_names=args.max_names)
    targets = bundle.targets[["date", "permno", "ret_next"]].copy()
    targets["date"] = pd.to_datetime(targets["date"])

    rows = []
    for name in sorted(artefacts):
        parts = name.split("-")
        if len(parts) != 4 or parts[2] not in ("P", "E"):
            continue  # a baseline, not a factorial cell
        arm = parts[2]
        kind = "weight_proposals" if arm == "E" else "predictions"
        mu, sd, n, col = information_coefficient(artefacts[name], kind, targets)
        t = mu / (sd / np.sqrt(n)) if sd and sd > 0 and n else np.nan
        rows.append({"cell": name, "arm": arm, "mean_ic": mu, "ic_t": t, "months": n,
                     "column": col})
    if not rows:
        print("no factorial cells found in that log")
        return 2
    res = pd.DataFrame(rows)
    out_dir = ROOT / "outputs" / "arm_information"
    out_dir.mkdir(parents=True, exist_ok=True)
    res.to_csv(out_dir / f"arm_information_{args.country}.csv", index=False)

    print()
    print(res.to_string(index=False, float_format=lambda v: f"{v:,.5f}"))
    print()
    # A cell with no overlapping months has no evidence either way, and reporting that as "did not
    # learn" would turn a missing file into a finding. The first version of this tool did exactly
    # that on a stale Germany log whose artefacts had been superseded on disk, and announced that
    # BOTH arms had failed to learn on zero observations. Absence is refused, not interpreted.
    empty = res[res["months"] == 0]
    if len(empty):
        print(f"  *** REFUSING TO JUDGE: {len(empty)} of {len(res)} cells have NO overlapping")
        print("      months with this country's targets, so there is no evidence either way. The")
        print("      artefacts named by that log are probably no longer on disk (stage-02 output")
        print("      is shared across countries and gets superseded), or the log is for a")
        print("      different country. Cells affected:")
        print("        " + ", ".join(empty["cell"].tolist()))
        if len(empty) == len(res):
            return 2
        print("      The arms below are judged on the remaining cells only.")
        print()
        res = res[res["months"] > 0]

    verdict = 0
    for arm, label in (("P", "prediction-loss"), ("E", "economic-loss")):
        sub = res[res["arm"] == arm]
        if sub.empty:
            print(f"  {label:16} ({arm}): no cells with usable data - not judged")
            continue
        learned = (sub["ic_t"] > args.min_ic_t).sum()
        print(f"  {label:16} ({arm}): {len(sub)} cells, mean IC {sub['mean_ic'].mean():+.5f}, "
              f"range {sub['mean_ic'].min():+.5f}..{sub['mean_ic'].max():+.5f}, "
              f"{learned} of {len(sub)} with IC t > {args.min_ic_t}")
        if learned == 0:
            verdict = 1
            print(f"  *** THE {label.upper()} ARM DID NOT LEARN. Its output carries no")
            print("      information about next-month returns, so any 'main effect' involving it")
            print("      measures a training failure and not the design axis it is labelled with.")
    return verdict


if __name__ == "__main__":
    raise SystemExit(main())
