#!/usr/bin/env python
"""E29: assemble the factorial attribution exhibit from C12 return series.

Reads every ``outputs/returns/<strategy>/<run_id>.parquet`` the repository holds, pivots the net
return columns into a months x cells panel, and produces the paper's main table: cell performance,
factorial effects with Newey-West t-statistics, and the Shapley reconciliation.

Deflation uses the trial count from the frozen pre-registration (PLAN_002), not a count inferred
from ``outputs/trials.csv`` after the fact. That is the whole point of having written the plan
down: N is a property of the design, not of how much searching happened to occur.

    python tools/exp_e29_attribution.py                      # net-of-cost
    python tools/exp_e29_attribution.py --column after_tax_ret
    python tools/exp_e29_attribution.py --out outputs/e29

Every table is stamped with the data source. A run against ``data_source: synthetic`` is a
*dress rehearsal*, not a result, and the stamp is there so a synthetic table can never be mistaken
for an empirical one in a draft.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts import load_config, paths  # noqa: E402
from alphacomb.validation import factorial  # noqa: E402
from alphacomb.validation.inference import deflated_sharpe, inference_report  # noqa: E402
from alphacomb.validation.preregistration import PreRegistration  # noqa: E402

PLAN = ROOT / "prereg" / "PLAN_001_after_tax_attribution.json"
AMENDMENT = ROOT / "prereg" / "AMENDMENT_001A_international_scenario_freeze_2026-10-08.json"


def latest_per_strategy(returns_root: Path) -> dict[str, Path]:
    """Most recent returns file for each strategy directory."""
    out: dict[str, Path] = {}
    if not returns_root.exists():
        return out
    for folder in sorted(returns_root.iterdir()):
        if not folder.is_dir():
            continue
        files = sorted(folder.glob("*.parquet"), key=lambda p: p.stat().st_mtime)
        if files:
            out[folder.name] = files[-1]
    return out


def strategy_to_cell(name: str) -> str | None:
    """``cell_N-C-E-U`` -> ``N-C-E-U``; baselines and benchmarks return None."""
    if not name.startswith("cell_"):
        return None
    code = name[len("cell_"):]
    try:
        factorial.parse_cell(code)
    except ValueError:
        return None
    return code


def build_panel(files: dict[str, Path], column: str,
                require_source: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return (cell panel, comparator panel, sources), both panels months x strategy.

    ``require_source`` keeps a stale series out of a live exhibit. The returns directories
    accumulate runs: a synthetic dress rehearsal, an older country, a one-off comparator. Each
    strategy folder resolves independently to its own newest file, so without this filter a cell
    that simply was not re-run would contribute its *previous* source's returns to the panel and
    the attribution would silently mix populations. ``dev_backtest`` stamps ``data_source`` into
    every series it writes; a series without the column predates the stamp and is treated as
    unknown rather than assumed to match.
    """
    cells, others, sources = {}, {}, {}
    for name, path in files.items():
        df = pd.read_parquet(path)
        if column not in df.columns:
            continue
        src = (str(df["data_source"].iloc[0]) if "data_source" in df.columns and len(df)
               else "unstamped")
        sources[name] = src
        if require_source is not None and src != require_source:
            continue
        series = df.set_index(pd.to_datetime(df["date"]))[column].astype("float64")
        code = strategy_to_cell(name)
        (cells if code else others)[code or name] = series
    return pd.DataFrame(cells).sort_index(), pd.DataFrame(others).sort_index(), sources


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--column", default="net_ret",
                    help="return column to attribute (net_ret, after_tax_ret, gross_ret)")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "e29")
    ap.add_argument("--periods", type=int, default=12)
    ap.add_argument("--source", default=None,
                    help="attribute only series stamped with this data_source (e.g. real_DEU). "
                         "Without it, every strategy's newest series is taken whatever its "
                         "provenance, which is only safe when the whole tree was built in one go.")
    args = ap.parse_args(argv)

    cfg = load_config()
    files = latest_per_strategy(paths.outputs_root() / "returns")
    if not files:
        print("no C12 return series under outputs/returns - run stage 04 and the backtest first")
        return 2

    cells, others, sources = build_panel(files, args.column, require_source=args.source)
    # The stamp on the exhibit is the provenance of the series actually attributed, not of
    # configs/base.yaml. Mixing populations in one factorial is never a reportable result, so it
    # stops the run instead of printing a caveat nobody will carry into the draft.
    kept = set(cells.columns) | set(others.columns)
    used = sorted({v for k, v in sources.items() if (strategy_to_cell(k) or k) in kept})
    if len(used) > 1:
        print("")
        print(f"REFUSING TO ATTRIBUTE ACROSS SOURCES: {', '.join(used)}")
        print("Each strategy folder resolves to its own newest returns file, so this means some")
        print("cells were re-run and others were not. Re-run the stale cells, or pass --source")
        print("to restrict the exhibit to one population.")
        for name in sorted(sources):
            print(f"  {name:<34} {sources[name]}")
        return 2
    source = used[0] if used else cfg.get("data_source", "unknown")
    skipped = {k: v for k, v in sources.items() if v != source}
    print(f"data_source      : {source}")
    print(f"return column    : {args.column}")
    print(f"cells found      : {len(cells.columns)} of 16")
    print(f"comparators found: {len(others.columns)}")
    if skipped:
        print(f"excluded (other provenance): {len(skipped)}")
        for name, src in sorted(skipped.items()):
            print(f"  {name:<34} {src}")
    if cells.empty:
        print("no factorial cells present; nothing to attribute")
        return 2

    missing = sorted(set(
        f"{n}-{c}-{e}-{u}" for n in "LN" for c in "SC" for e in "PE" for u in ("0", "U")
    ) - set(cells.columns))
    if missing:
        print(f"\nINCOMPLETE DESIGN - missing {len(missing)} cells: {', '.join(missing)}")
        print("Factorial effects need all 16. Reporting cell statistics only.\n")

    args.out.mkdir(parents=True, exist_ok=True)
    stamp = {"data_source": source, "column": args.column,
             "is_dress_rehearsal": not source.startswith("real"),
             "series_provenance": sources,
             "excluded_other_provenance": skipped}

    if not missing:
        report = factorial.attribution_report(cells, periods=args.periods)
        for key, table in report.items():
            path = args.out / f"e29_{key}.csv"
            table.to_csv(path)
            print(f"wrote {path}")

        print("\n--- factorial effects (annualised, Newey-West t) ---")
        for _, r in report["effects"].iterrows():
            star = "*" if r["significant_5pct"] else " "
            print(f"  {r['term']:<34} {r['annualised']:+8.4f}  t={r['t_stat']:+6.2f} {star}")

        print("\n--- Shapley attribution ---")
        sh = report["shapley"]
        for _, r in sh.iterrows():
            print(f"  {r['factor']:<16} {r['shapley_annualised']:+8.4f} p.a."
                  f"   {r['share_of_total']:+6.1%} of total")
        print(f"  {'TOTAL':<16} {sh.attrs['total_annualised']:+8.4f} p.a.")

    # N comes from the frozen plan, never from counting trials.csv after the fact. Amendment 001A
    # keeps PLAN_001's grid and therefore its N: only the empirical setting was pinned down, not
    # the search. If the two disagree on the fingerprint, the grid moved and N is stale.
    n_trials = None
    if PLAN.exists():
        plan = PreRegistration.load(PLAN)
        n_trials = plan.n_configurations
        note = f"PLAN_001, fingerprint {plan.fingerprint}"
        if AMENDMENT.exists():
            amd = json.loads(AMENDMENT.read_text(encoding="utf-8"))
            if amd.get("parent_fingerprint") != plan.fingerprint:
                raise SystemExit(
                    "amendment 001A does not match PLAN_001's fingerprint: the grid changed, so N "
                    "must be recomputed before anything is deflated")
            n_trials = int(amd["confirmatory_trial_count_N"])
            note += f" + amendment {amd['amendment_id']}"
        print(f"\npre-registered N : {n_trials}  ({note})")
    else:
        print("\nPLAN_001 absent - deflation skipped rather than guessing N")

    if n_trials:
        panel = pd.concat([cells, others], axis=1)
        rep = inference_report(panel, n_trials=n_trials)
        per_strategy = rep["per_strategy"]
        per_strategy.to_csv(args.out / "e29_inference.csv", index=False)
        print(f"wrote {args.out / 'e29_inference.csv'}")
        print(f"\n--- deflated Sharpe at the pre-registered N = {n_trials} ---")
        cols = ["strategy", "sharpe", "t_stat", "deflated_sr_prob", "survives_deflation",
                "expected_max_sr_from_search"]
        print(per_strategy[cols].to_string(index=False, float_format=lambda v: f"{v:,.4f}"))
        hurdle = per_strategy["expected_max_sr_from_search"].iloc[0]
        survivors = int(per_strategy["survives_deflation"].sum())
        print(f"\nsearch hurdle (E[max SR] under the null): {hurdle:.4f} annualised")
        print(f"strategies surviving deflation          : {survivors} of {len(per_strategy)}")
        # PBO and Romano-Wolf are the other two things a referee asks for.
        for key in ("pbo", "romano_wolf"):
            if key in rep:
                print(f"\n--- {key} ---\n{rep[key]}")

    (args.out / "e29_provenance.json").write_text(json.dumps(stamp, indent=2), encoding="utf-8")
    if stamp["is_dress_rehearsal"]:
        print("\n" + "=" * 72)
        print("SYNTHETIC DRESS REHEARSAL - these numbers describe planted data, not markets.")
        print("They validate that the analysis path runs end to end. They are not findings and")
        print("must never appear in a draft without this label.")
        print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
