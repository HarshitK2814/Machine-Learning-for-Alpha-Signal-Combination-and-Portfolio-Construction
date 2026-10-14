"""Vendor-coverage aggregation: counts only, no identifiers or values written. Synthetic fixtures only."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

TOOL = Path(__file__).resolve().parents[2] / "tools" / "phase_c_vendor_coverage_aggregate.py"
spec = importlib.util.spec_from_file_location("phase_c_vendor_coverage_aggregate", TOOL)
mod = importlib.util.module_from_spec(spec)
sys.modules["phase_c_vendor_coverage_aggregate"] = mod
spec.loader.exec_module(mod)

O = pd.Period("2012-01", "M").ordinal


def _flags(seq_by_p):
    rows = [(O + k, p, ok) for p, seq in seq_by_p.items() for k, ok in enumerate(seq) if ok is not None]
    return pd.DataFrame(rows, columns=["mi", "permno", "ret_ok"])


def _cov(rows):
    return pd.DataFrame(rows, columns=["permno", "daily_rows", "actual_price_status_rows", "carry_forward_status_rows",
                                       "first_daily_date", "last_daily_date"])


def test_summary_counts_and_spans():
    runs = mod.gap_runs_keyed(_flags({1: [True, False, False, True, True], 2: [True, False, True, True, True],
                                      3: [False, None, False, True, True]}), O, O + 10)
    cov = _cov([(1, 100, 80, 20, "2011-06-30", "2012-12-31"), (2, 10, 10, 0, "2012-03-31", "2012-12-31")])
    s = mod.summarise(runs, cov)
    assert s["gap_runs"] == 4 and s["gap_months"] == 5 and s["gap_securities"] == 3
    assert s["gap_securities_with_any_vendor_daily"] == 2 and s["gap_securities_with_any_carry_forward_rows"] == 1
    assert s["gap_runs_vendor_date_range_spans_run"] == 1          # permno 2 starts after its gap run; 3 absent
    assert s["gap_runs_not_in_vendor_file_or_no_daily"] == 2
    assert s["vendor_other_status_rows_all_securities"] == 0 and "unknown" in s["month_level_status_for_gap_months"]


def test_output_has_no_identifier_or_value_keys():
    runs = mod.gap_runs_keyed(_flags({7: [True, False, True]}), O, O + 5)
    s = mod.summarise(runs, _cov([(7, 5, 5, 0, "2012-01-31", "2012-03-31")]))
    assert all(isinstance(v, (int, str)) for v in s.values()) and "permno" not in " ".join(s)
