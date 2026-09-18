#!/usr/bin/env python
"""Stage 02 (workstream B): train the factorial cells and write predictions/proposals.

Examples
--------
    python pipelines/02_train_models.py --cells L-S-P-0 --years 2015 2020 --fast
    python pipelines/02_train_models.py --cells all --years 1995 2020
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alphacomb.contracts import load_bundle, load_config, new_run_id, paths  # noqa: E402
from alphacomb.contracts.interfaces import ALL_CELLS, CellSpec  # noqa: E402
from alphacomb.models import CellRunConfig, run_cell  # noqa: E402
from alphacomb.risk import RiskCache, StructuralRiskModel  # noqa: E402

log = logging.getLogger("stage02")


def main() -> None:
    p = argparse.ArgumentParser(description="Train factorial model cells (experiments E20-E28).")
    p.add_argument("--cells", nargs="+", default=["all"], help="cell codes such as N-C-E-U, or 'all'")
    p.add_argument("--years", nargs=2, type=int, metavar=("FIRST", "LAST"), default=None)
    p.add_argument("--horizon", type=int, default=1, choices=[1, 3, 6, 12])
    p.add_argument("--data", default=None, help="synthetic | real (default: configs/base.yaml)")
    p.add_argument("--fast", action="store_true", help="small grids and short training, for development")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--members", type=int, default=5, help="ensemble members for uncertainty cells")
    p.add_argument("--manifest", default=None, help="CSV to append run metadata to")
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config("base")
    source = a.data or cfg["data_source"]
    bundle = load_bundle(source)
    risk = RiskCache(StructuralRiskModel(bundle, cfg))

    cells = ALL_CELLS if a.cells == ["all"] else [CellSpec.parse(c) for c in a.cells]
    first, last = (a.years if a.years else (None, None))
    manifest_rows = []
    for spec in cells:
        started = time.time()
        run_cfg = CellRunConfig(horizon=a.horizon, first_test_year=first, last_test_year=last, fast=a.fast,
                                seed=a.seed, uncertainty_members=a.members)
        log.info("=== cell %s (%s) ===", spec.code, spec.describe())
        try:
            result = run_cell(spec, bundle, risk, run_cfg, base_cfg=cfg)
        except Exception as exc:  # pragma: no cover - keeps a long batch alive
            log.exception("cell %s failed: %s", spec.code, exc)
            manifest_rows.append({"cell": spec.code, "status": "failed", "error": str(exc)})
            continue
        result.update({"status": "ok", "minutes": round((time.time() - started) / 60, 2),
                       "horizon": a.horizon, "source": source, "fast": a.fast})
        manifest_rows.append(result)
        log.info("%s -> %s (%d rows, %.1f min)", spec.code, result["artefact"], result["rows"], result["minutes"])

    manifest = pd.DataFrame(manifest_rows)
    out = Path(a.manifest) if a.manifest else paths.outputs_root() / "manifest_models.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_csv(out, mode="a", header=not out.exists(), index=False)
    print(manifest.to_string(index=False))
    print(f"\nmanifest: {out}\ntrials:   {paths.trials_path()}")


if __name__ == "__main__":
    main()
