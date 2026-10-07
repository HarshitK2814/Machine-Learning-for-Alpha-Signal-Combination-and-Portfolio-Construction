"""Compatibility entry point for the manifest-based post-promotion validator."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

from alphacomb.contracts import validate


ROOT = Path(__file__).resolve().parent
COUNTRIES = ["DEU", "IND", "JPN"]
DECISIONS = ROOT / "configs" / "workstream_a_frozen_decisions.json"


def main() -> None:
    # The final authority promoted only the two manifest-listed C6/C14 files;
    # it did not authorize materializing the earlier proposed data/real layout.
    # Preserve this historical command while routing it to the final validator.
    from validate_workstream_a_post_promotion_2026_10_07 import main as validate_current

    validate_current()
    return

    if not DECISIONS.is_file():
        raise FileNotFoundError(f"Missing approved six-decision configuration: {DECISIONS}")
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    required = {
        "representative_taxable_investor_rate_paths", "allowance_allocation",
        "statutory_currency_FX_timing", "brokerage_platform_fee_scope",
        "pre_2003_Japan_taxpayer_route", "missing_borrow_fee_treatment",
    }
    if set(decisions.get("decisions", {})) != required:
        raise RuntimeError("Approved configuration does not contain exactly the six frozen decisions")

    for country in COUNTRIES:
        base = ROOT / "data" / "real" / country
        files = {
            "universe": base / "universe.parquet",
            "signals": base / "signals.parquet",
            "signal_meta": base / "signal_meta.csv",
            "targets": base / "targets.parquet",
            "states": base / "states.parquet",
            "cost_inputs": base / "cost_inputs.parquet",
        }
        for path in files.values():
            if not path.is_file():
                raise FileNotFoundError(path)
        frames = {
            "universe": pd.read_parquet(files["universe"]),
            "signals": pd.read_parquet(files["signals"]),
            "signal_meta": pd.read_csv(files["signal_meta"]),
            "targets": pd.read_parquet(files["targets"]),
            "states": pd.read_parquet(files["states"]),
            "cost_inputs": pd.read_parquet(files["cost_inputs"]),
        }
        for contract, frame in frames.items():
            validate(frame, contract)
        c1_keys = frames["universe"][["date", "permno"]]
        for contract in ["signals", "targets"]:
            merged = c1_keys.merge(frames[contract][["date", "permno"]], on=["date", "permno"], how="outer", indicator=True, validate="one_to_one")
            if not merged["_merge"].eq("both").all():
                raise RuntimeError(f"{country}: {contract} does not have the exact C1 spine")

    consumer = (ROOT / "src" / "alphacomb" / "portfolio" / "cost_terms.py").read_text(encoding="utf-8")
    if "fillna(0.0025)" in consumer:
        raise RuntimeError("Prohibited implicit 25 bp borrow-fee fallback remains")

    command = [
        sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
        "--basetemp", str(ROOT / ".pytest_tmp_post_promotion"),
        "tests/c14", "tests/portfolio/test_optimizer.py", "tests/portfolio/test_tax_terms.py",
        "tests/contracts/test_manifest.py",
    ]
    subprocess.run(command, cwd=ROOT, check=True)
    print("WORKSTREAM-A POST-PROMOTION VALIDATION: PASS")


if __name__ == "__main__":
    main()
