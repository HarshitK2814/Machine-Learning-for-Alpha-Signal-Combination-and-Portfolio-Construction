#!/usr/bin/env python
"""Refuse to report a bounding run whose bound did not bind.

Why this exists
---------------
On 2026-10-09 a section 112A bounding exercise returned **bit-identical** results at both the
maximum-tax and minimum-tax extremes, and that was nearly reported as "the 456 missing reference
values cannot change the conclusion". It was not a finding. The engine consumes
``close_value_local * (fmv_price_local / close_price_local)``, and both bound files had been
written with ``fmv == close`` on the affected rows, so the **ratio was 1.0 in both** and the two
runs were the same run. Meanwhile 422 of the 456 names were materially held and 75 were held after
the reform, so their treatment genuinely did enter the result.

The general rule, from `docs/VERIFICATION_PROTOCOL_2026-10-09.md` C1:

> **A bounding or sensitivity run whose output is unchanged is a null result about the plumbing
> until proven otherwise.** Identical output across extreme inputs is a symptom, not a finding.

What this does
--------------
Given the two **input** files and the two **output** files of a bounding pair:

1. Asserts the inputs differ, and reports on how many rows and in which columns.
2. If ``--derived`` is given as ``NUM/DEN``, asserts the **derived** quantity differs too. This is
   the check that would have caught the 112A failure: the edited column differed, the quantity the
   engine actually consumed did not.
3. Asserts the outputs differ. **Exits non-zero if they do not**, with the diagnosis spelled out.

Exit codes: 0 the bound is live; 2 the bound did not bind; 3 the inputs were not actually different.

Usage
-----
    python tools/verify_bound_is_live.py \
        --inputs  outputs/bounds/IND_112A_REFERENCE_BOUND_MAXTAX_V2.csv \
                  outputs/bounds/IND_112A_REFERENCE_BOUND_MINTAX_V2.csv \
        --outputs outputs/event_112a_MAXTAX_V2/event_112a.csv \
                  outputs/event_112a_MINTAX_V2/event_112a.csv \
        --derived fmv_price_local/close_price_local
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def _load(p: Path) -> pd.DataFrame:
    if not p.exists():
        raise SystemExit(f"missing file: {p}")
    return pd.read_csv(p)


def _differing_columns(a: pd.DataFrame, b: pd.DataFrame) -> dict[str, int]:
    out: dict[str, int] = {}
    if len(a) != len(b):
        return {"<row count>": abs(len(a) - len(b))}
    for c in a.columns:
        if c not in b.columns:
            out[f"{c} (only in first)"] = len(a)
            continue
        x, y = a[c], b[c]
        if x.dtype.kind in "fi" and y.dtype.kind in "fi":
            n = int((~np.isclose(x.to_numpy(dtype=float), y.to_numpy(dtype=float),
                                 rtol=0, atol=0, equal_nan=True)).sum())
        else:
            n = int((x.astype(str) != y.astype(str)).sum())
        if n:
            out[c] = n
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inputs", nargs=2, type=Path, required=True,
                    help="the two bound INPUT files")
    ap.add_argument("--outputs", nargs=2, type=Path, required=True,
                    help="the two bound OUTPUT files")
    ap.add_argument("--derived", default=None,
                    help="NUM/DEN: also assert this derived ratio differs between inputs. Use it "
                         "whenever the consumer reads a ratio or other transform rather than the "
                         "column you edited")
    a = ap.parse_args(argv)

    ia, ib = (_load(p) for p in a.inputs)
    oa, ob = (_load(p) for p in a.outputs)

    print("=" * 78)
    print("BOUND LIVENESS CHECK")
    print("=" * 78)

    in_diff = _differing_columns(ia, ib)
    print(f"\ninputs : {a.inputs[0].name}  vs  {a.inputs[1].name}")
    if not in_diff:
        print("  IDENTICAL. The two bound inputs are the same file in content.")
        print("\nVERDICT: the bound was never constructed. Nothing can be concluded.")
        return 3
    for c, n in in_diff.items():
        print(f"  {c}: {n} differing rows")

    if a.derived:
        if "/" not in a.derived:
            raise SystemExit("--derived must look like NUM/DEN")
        num, den = a.derived.split("/", 1)
        for frame, name in ((ia, a.inputs[0].name), (ib, a.inputs[1].name)):
            for col in (num, den):
                if col not in frame.columns:
                    raise SystemExit(f"{name} has no column {col}")
        ra = ia[num].to_numpy(dtype=float) / ia[den].to_numpy(dtype=float)
        rb = ib[num].to_numpy(dtype=float) / ib[den].to_numpy(dtype=float)
        n = int((~np.isclose(ra, rb, rtol=0, atol=0, equal_nan=True)).sum())
        print(f"\nderived {a.derived}: {n} differing rows")
        if n == 0:
            print("  THE DERIVED QUANTITY IS IDENTICAL IN BOTH BOUNDS.")
            print("  The columns you edited differ, but the quantity the consumer actually reads")
            print("  does not. This is exactly the 2026-10-09 section 112A failure.")
            print("\nVERDICT: the bound does not bind. Nothing can be concluded.")
            return 3

    out_diff = _differing_columns(oa, ob)
    print(f"\noutputs: {a.outputs[0].name}  vs  {a.outputs[1].name}")
    if not out_diff:
        print("  IDENTICAL.")
        print("\nVERDICT: BOUND DID NOT BIND.")
        print("  The inputs differ but the outputs do not. Before reporting this as")
        print("  'the uncertainty cannot change the conclusion', rule out:")
        print("    1. the consumer reads a transform of the edited column (try --derived);")
        print("    2. the affected rows are never used - check they appear in the held book;")
        print("    3. the argument is accepted and logged but not threaded into the computation.")
        print("  Only after all three are excluded is insensitivity a finding about the world.")
        return 2
    for c, n in out_diff.items():
        print(f"  {c}: {n} differing rows")

    print("\nVERDICT: BOUND IS LIVE. Inputs differ, outputs differ. The spread between these")
    print("  two outputs is a genuine bound on the effect of the underlying uncertainty.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
