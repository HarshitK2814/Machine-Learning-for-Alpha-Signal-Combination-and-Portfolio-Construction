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

from alphacomb.contracts import append_manifest, load_bundle, load_config, new_run_id, paths  # noqa: E402
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
    p.add_argument("--country", default=None, choices=["DEU", "IND", "JPN"],
                   help="run the promoted international panel for one country (amendment 001A "
                        "freezes DEU/IND/JPN as separate runs)")
    p.add_argument("--fast", action="store_true", help="small grids and short training, for development")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--members", type=int, default=5, help="ensemble members for uncertainty cells")
    p.add_argument("--manifest", default=None, help="CSV to append run metadata to")
    p.add_argument("--benchmarks", nargs="*", default=None,
                   help="published benchmark presets to run as well (E13), e.g. gkx_nn3 gkx_gbrt")
    p.add_argument("--baselines", nargs="*", default=None,
                   help="pre-registered comparators to run (E10-E12): BASE-EW BASE-THEME-EW "
                        "BASE-IC BASE-OLS BASE-RIDGE, or 'all'. They route through the same cell "
                        "runner and stage-04 path, which is what gives cost parity.")
    p.add_argument("--after-tax-objective", default=None, metavar="REGIME",
                   help="train economic cells on net-of-cost-AND-TAX utility, e.g. taxable_us_top_bracket")
    p.add_argument("--harvest-haircut", type=float, default=1.0,
                   help="how usable a realised loss is in the training objective")
    p.add_argument("--suffix", default="", help="append to strategy names, e.g. '_aftertax'")
    p.add_argument("--seeds", nargs="*", type=int, default=None,
                   help="run the given cells under several seeds and report dispersion (E56)")
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    tax_regime = None
    if a.after_tax_objective:
        from alphacomb.tax import get_regime

        tax_regime = get_regime(a.after_tax_objective)
        if not a.suffix:
            a.suffix = "_aftertax"
    cfg = load_config("base")
    source = a.data or cfg["data_source"]
    if a.country:
        # The promoted international panel is read in place from data/intl_c*; document 13
        # prohibits materialising the legacy flat data/real bundle, so there is nothing for
        # load_bundle to open. Amendment 001A freezes DEU/IND/JPN as separate runs, which is
        # why this is one country per invocation rather than a pooled panel.
        from alphacomb.contracts import intl
        bundle = intl.load_country_bundle(a.country)
        source = bundle.source
        log.info("international bundle %s: %d security-months, %d signals",
                 a.country, len(bundle.universe), len(bundle.signal_columns))
    else:
        bundle = load_bundle(source)
    risk = RiskCache(StructuralRiskModel(bundle, cfg))

    cells = ALL_CELLS if a.cells == ["all"] else [CellSpec.parse(c) for c in a.cells]
    first, last = (a.years if a.years else (None, None))
    manifest_rows = []

    if a.seeds:
        from alphacomb.models import compare_to_cell_gap, run_seeds

        for spec in cells:
            run_cfg = CellRunConfig(horizon=a.horizon, first_test_year=first, last_test_year=last,
                                    fast=a.fast, uncertainty_members=a.members)
            table = run_seeds(spec, bundle, risk, list(a.seeds), run_cfg, base_cfg=cfg)
            out = paths.outputs_root() / f"seed_stability_{spec.code}.csv"
            table.to_csv(out, index=False)
            log.info("seed dispersion %s: %s", spec.code, compare_to_cell_gap(table, cell_gap=0.0))
            print(table.to_string(index=False))
        return

    for spec in cells:
        started = time.time()
        run_cfg = CellRunConfig(horizon=a.horizon, first_test_year=first, last_test_year=last, fast=a.fast,
                                seed=a.seed, uncertainty_members=a.members,
                                tax_regime=tax_regime, tax_harvest_haircut=a.harvest_haircut,
                                strategy_suffix=a.suffix)
        log.info("=== cell %s (%s)%s ===", spec.code, spec.describe(),
                 f" [after-tax objective: {tax_regime.name}]" if tax_regime else "")
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

    baseline_codes = a.baselines or []
    if baseline_codes == ["all"]:
        from alphacomb.models import BASELINES
        baseline_codes = sorted(BASELINES)
    for code in baseline_codes:
        from alphacomb.models import run_baseline

        started = time.time()
        run_cfg = CellRunConfig(horizon=a.horizon, first_test_year=first, last_test_year=last,
                                fast=a.fast, seed=a.seed)
        log.info("=== baseline %s (E10-E12) ===", code)
        try:
            result = run_baseline(code, bundle, risk, run_cfg, base_cfg=cfg)
            result.update({"status": "ok", "minutes": round((time.time() - started) / 60, 2),
                           "horizon": a.horizon, "source": source, "fast": a.fast})
            log.info("%s -> %s (%d rows, %.1f min)", code, result["artefact"], result["rows"],
                     result["minutes"])
        except Exception as exc:  # pragma: no cover - keeps a long batch alive
            log.exception("baseline %s failed: %s", code, exc)
            result = {"cell": code, "status": "failed", "error": str(exc)}
        manifest_rows.append(result)

    for name in (a.benchmarks or []):
        from alphacomb.models import run_benchmark

        started = time.time()
        run_cfg = CellRunConfig(horizon=a.horizon, first_test_year=first, last_test_year=last, fast=a.fast,
                                seed=a.seed)
        log.info("=== benchmark %s (E13) ===", name)
        try:
            result = run_benchmark(name, bundle, risk, run_cfg, base_cfg=cfg)
            result.update({"status": "ok", "minutes": round((time.time() - started) / 60, 2),
                           "horizon": a.horizon, "source": source, "fast": a.fast})
        except Exception as exc:  # pragma: no cover
            log.exception("benchmark %s failed: %s", name, exc)
            result = {"cell": name, "status": "failed", "error": str(exc)}
        manifest_rows.append(result)

    manifest = pd.DataFrame(manifest_rows)
    out = Path(a.manifest) if a.manifest else paths.outputs_root() / "manifest_models.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    append_manifest(manifest, out)
    print(manifest.to_string(index=False))
    print(f"\nmanifest: {out}\ntrials:   {paths.trials_path()}")


if __name__ == "__main__":
    main()
