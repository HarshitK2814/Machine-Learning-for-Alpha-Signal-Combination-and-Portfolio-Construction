# -*- coding: utf-8 -*-
"""Re-run the palette validator over every colour set the figures actually ship.

Colourblind-safety is computable, so it is computed rather than eyeballed. This script is the
reproducible record: run it after any change to a figure's colours, and before rebuilding the PDFs.

    python _build/validate_figure_palettes.py

Requires node and the dataviz skill's validator. If neither is present the script says so and exits
non-zero rather than silently passing - a skipped check must never look like a passed one.

Checks applied (see the validator for the exact thresholds):
  categorical  lightness band, chroma floor, CVD separation (protan/deutan/tritan),
               normal-vision floor, contrast against the surface
  ordinal      lightness monotonicity, adjacent delta-L, single hue, light-end contrast

Two failures this found on the first run, both real and both now fixed:
  * fig_tax_waterfall used ramp steps 100/300/600. The light end sat at 1.29:1 against the
    surface, below the 2:1 floor, so the "gross return" band was close to invisible. Re-stepped
    to 300/450/700.
  * fig_prior_art_positioning paired #1baf7a with #6da7ec, which separate by only 4.7 under
    tritanopia - below even the 6-8 conditional floor. Swapped the green slot for amber
    (#eda100), lifting the worst tritan pair to 26.1.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path("C:/Temp/claude/bundled-skills/2.1.277/6668c9b86fa1298987dded432f7dd32e/dataviz")
VALIDATOR = SKILL / "scripts" / "validate_palette.js"

# (figure, colours as shipped, kind). Keep in step with figures.py / figures_aftertax.py.
PALETTES: list[tuple[str, str, str]] = [
    ("SLOTS (shared categorical)", "#2a78d6,#eb6834,#1baf7a,#eda100,#e87ba4", "categorical"),
    ("fig_tax_waterfall", "#6da7ec,#2a78d6,#0d366b", "ordinal"),
    ("fig_tax_drag_decomposition", "#6da7ec,#eb6834", "categorical"),
    ("fig_lot_method_matters", "#2a78d6,#eb6834", "categorical"),
    ("fig_wash_sale_bite", "#eb6834,#184f95", "categorical"),
    ("fig_prior_art_positioning", "#eda100,#6da7ec,#eb6834,#184f95", "categorical"),
    # The infeasible-oracle bar is deliberately recessive grey plus a hatch: it is chrome marking
    # "not implementable", not a series, so it is excluded from the categorical set by design.
    ("fig_adaptive_vs_benchmarks", "#6da7ec,#eb6834,#184f95", "categorical"),
]


def run(palette: str, kind: str) -> tuple[bool, str]:
    cmd = ["node", str(VALIDATOR), palette, "--mode", "light"]
    if kind == "ordinal":
        cmd.append("--ordinal")
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    return ("ALL CHECKS PASS" in out), out


def main() -> int:
    if shutil.which("node") is None or not VALIDATOR.exists():
        print("CANNOT VALIDATE: node or the dataviz validator is unavailable.", file=sys.stderr)
        print(f"  node: {'found' if shutil.which('node') else 'MISSING'}", file=sys.stderr)
        print(f"  validator: {VALIDATOR} {'found' if VALIDATOR.exists() else 'MISSING'}", file=sys.stderr)
        return 2

    failures = []
    for name, palette, kind in PALETTES:
        ok, out = run(palette, kind)
        print(f"{name:<34} {kind:<12} {'PASS' if ok else 'FAIL'}")
        for line in out.splitlines():
            stripped = line.strip()
            if stripped.startswith("[WARN]") or stripped.startswith("[FAIL]"):
                print(f"    {stripped}")
        if not ok:
            failures.append(name)

    print()
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        return 1
    print("All shipped figure palettes pass.")
    print("Contrast WARNs are not dismissable: they oblige visible labels or a table view. Every")
    print("figure here carries direct labels and names the CSV its numbers came from, which is the")
    print("print equivalent of the table view.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
