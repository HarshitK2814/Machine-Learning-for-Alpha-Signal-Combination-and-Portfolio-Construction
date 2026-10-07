"""Resume and verify the blocked C5/C6 work after WRDS Duo is restored."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PREFLIGHT = ROOT / "data" / "intl_c6" / "audit" / "C5_C6_DAILY_PREFLIGHT.json"


def run(script: str, *, allow_failure: bool = False) -> int:
    print(f"\n=== {script} ===", flush=True)
    completed = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=False)
    if completed.returncode and not allow_failure:
        completed.check_returncode()
    return completed.returncode


def main() -> None:
    scripts = [
        "extract_c6_wrds_abdi_ranaldo.py",
        "probe_c6_wrds_sigma_outliers.py",
        "build_c6_working_candidate.py",
        "audit_c6_sigma_outlier_resolution.py",
        "preflight_c5_c6_daily_candidates.py",
        "audit_c6_projected_fallback_coverage.py",
        "audit_c6_actual_fallback_coverage.py",
        "audit_c6_consumer_compatibility.py",
    ]
    preflight_returncode = 0
    for script in scripts:
        code = run(script, allow_failure=script == "preflight_c5_c6_daily_candidates.py")
        if script == "preflight_c5_c6_daily_candidates.py":
            preflight_returncode = code
    audit = json.loads(PREFLIGHT.read_text(encoding="utf-8"))
    print(f"\nFINAL PREFLIGHT: {audit['verdict']}")
    if preflight_returncode:
        print("Preflight remained fail-closed; downstream read-only audits still completed.")
    print("No production or GitHub write was performed.")


if __name__ == "__main__":
    main()
