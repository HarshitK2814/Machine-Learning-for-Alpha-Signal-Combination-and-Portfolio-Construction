#!/usr/bin/env python
"""Orchestrator: runs the stages in order. SHARED FILE - it calls stage scripts and contains no logic.

    python pipelines/run_all.py --years 2015 2020 --cells all
    python pipelines/run_all.py --smoke                     # two cells, two years, fast settings
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print(f"\n=== {' '.join(cmd)} ===", flush=True)
    started = time.time()
    result = subprocess.run([sys.executable, *cmd], cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"stage failed: {' '.join(cmd)}")
    print(f"--- done in {(time.time() - started) / 60:.1f} min ---", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description="Run every stage end to end.")
    p.add_argument("--cells", nargs="+", default=["all"])
    p.add_argument("--years", nargs=2, type=int, default=None)
    p.add_argument("--fast", action="store_true")
    p.add_argument("--smoke", action="store_true", help="two cells, two years, fast settings")
    p.add_argument("--skip-data", action="store_true", help="reuse the existing synthetic panel")
    p.add_argument("--cost-multiplier", type=float, default=1.0)
    a = p.parse_args()

    cells = ["L-S-P-0", "N-S-P-0"] if a.smoke else a.cells
    years = [2019, 2020] if a.smoke else (a.years or [1995, 2020])
    fast = a.fast or a.smoke

    if not a.skip_data:
        run(["-m", "alphacomb.synthetic.generate", "--out", "data/synthetic"])

    stage02 = ["pipelines/02_train_models.py", "--cells", *cells, "--years", str(years[0]), str(years[1])]
    if fast:
        stage02.append("--fast")
    run(stage02)
    run(["pipelines/04_construct_portfolios.py", "--strategies", "all",
         "--cost-multiplier", str(a.cost_multiplier)])
    # TEMPORARY: replace with pipelines/05_backtest.py once workstream A delivers the C12 engine
    run(["tools/dev_backtest.py", "--cost-multiplier", str(a.cost_multiplier)])
    print("\nAll stages finished. Outputs under outputs/ ; trial log outputs/trials.csv")


if __name__ == "__main__":
    main()
