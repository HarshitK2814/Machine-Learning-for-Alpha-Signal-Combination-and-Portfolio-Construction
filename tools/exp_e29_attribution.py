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


def observed_trial_count(cells_present: list[str]) -> tuple[int, dict]:
    """Distinct configurations actually fitted for the artefacts THIS exhibit is built from.

    The deflation hurdle is only honest if ``N`` bounds the search that produced the numbers being
    deflated. ``outputs/trials.csv`` accumulates every fit ever logged - on this project that is
    1,371 rows over 13 commits and three weeks, most of them synthetic development runs that never
    saw the real evaluation sample and so cannot have overfitted it. Counting all of them would
    overstate the search; trusting the pre-registered N without looking would risk understating it.

    The exact link is the run id: a trial row's ``run_id`` is the stem of the model artefact it
    produced, so the configurations behind this exhibit are the rows whose ``run_id`` matches the
    artefact each cell actually resolved to. That is a property of the files in the exhibit, not of
    a time window or a guess.
    """
    trials_path = paths.outputs_root() / "trials.csv"
    if not trials_path.exists():
        return 0, {}
    trials = pd.read_csv(trials_path)
    if not {"run_id", "params_json", "cell"} <= set(trials.columns):
        return 0, {}

    per_cell: dict[str, int] = {}
    for code in cells_present:
        strategy = f"cell_{code}"
        artefact = None
        for kind in ("predictions", "weight_proposals"):
            found = paths.latest_run(kind, strategy)
            if found is not None:
                artefact = found
                break
        if artefact is None:
            continue
        run_id = artefact.stem
        rows = trials.loc[trials["run_id"] == run_id]
        if rows.empty:
            # Older artefacts predate run-id logging; fall back to the cell's own rows so the
            # count is never silently zero for a cell that is in the exhibit.
            rows = trials.loc[trials["cell"] == code]
        per_cell[code] = int(rows["params_json"].nunique())
    return int(sum(per_cell.values())), per_cell


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--column", default="net_ret",
                    help="return column to attribute (net_ret, after_tax_ret, gross_ret)")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "e29")
    ap.add_argument("--periods", type=int, default=12)
    ap.add_argument("--spa-benchmark", default="baseline_BASE-EW",
                    help="strategy to use as the Hansen SPA benchmark. Equal-weighting is the "
                         "right default: 'does ANY configuration beat equal-weighting once the "
                         "whole candidate set is accounted for' is the first question a referee "
                         "asks, and SPA is the test that answers it without cherry-picking the "
                         "best candidate. Ignored if the strategy is absent.")
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
        # State the estimation window rather than letting the table imply the full sample.
        n_used = report["cells"].attrs.get("n_months")
        dropped = report["cells"].attrs.get("months_dropped", 0)
        print(f"months in panel  : {len(cells)}")
        print(f"months estimated : {n_used}" + (f"  ({dropped} dropped as unbalanced)"
                                                if dropped else "  (balanced)"))
        for key, table in report.items():
            if key == "balance" and not len(table):
                continue
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

    # Verify N bounds the search rather than assuming it. Over-stating N raises the hurdle and is
    # the safe direction; under-stating it is not, so an observed count above the registered one
    # replaces it and is reported.
    if n_trials:
        observed, per_cell = observed_trial_count(list(cells.columns))
        print(f"configurations fitted for these artefacts: {observed} "
              f"(registered N = {n_trials})")
        if observed > n_trials:
            print("")
            print(f"WARNING: the search exceeded the registered trial count ({observed} > {n_trials}).")
            print("Deflating at the registered N would understate the search, so the observed "
                  "count is used.")
            print("Per cell: " + ", ".join(f"{k}={v}" for k, v in sorted(per_cell.items())))
            stamp["trial_count_exceeded_registration"] = True
            n_trials = observed
        else:
            print(f"  registered N is conservative by {n_trials - observed} configurations")
        stamp["configurations_fitted"] = observed
        stamp["configurations_per_cell"] = per_cell
        stamp["n_trials_used"] = int(n_trials)

    if n_trials:
        panel = pd.concat([cells, others], axis=1)
        bench = args.spa_benchmark if args.spa_benchmark in panel.columns else None
        if args.spa_benchmark and bench is None:
            print(f"note: SPA benchmark {args.spa_benchmark!r} is not in the panel; "
                  f"SPA skipped. Present: {', '.join(sorted(others.columns)) or 'no comparators'}")
        rep = inference_report(panel, n_trials=n_trials, benchmark=bench)
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
        if "spa" in rep:
            spa = rep["spa"]
            print("")
            print(f"--- Hansen SPA vs {bench} ---")
            print(f"  statistic {spa.statistic:.4f}   p = {spa.p_value:.4f}")
            print("  " + ("no candidate beats the benchmark once the full set is accounted for"
                          if spa.p_value > 0.05 else
                          "at least one candidate genuinely beats the benchmark"))
            for k, v in spa.detail.items():
                print(f"    {k}: {v}")
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
