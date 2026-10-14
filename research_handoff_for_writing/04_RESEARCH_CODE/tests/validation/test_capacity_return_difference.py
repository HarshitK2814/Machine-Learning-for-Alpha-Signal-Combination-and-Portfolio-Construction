"""Tests for the B(A) accounting helpers in tools/exp_capacity_return_difference.py."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import exp_capacity_return_difference as t  # noqa: E402


def _comp(T=60, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2010-01-31", periods=T, freq="ME")
    g_u = rng.normal(0.01, 0.03, T)
    g_c = 0.7 * g_u
    return pd.DataFrame({"gross_ret": g_u, "gross_ret_capped": g_c,
                         "net_ret_uncapped": g_u - 0.02, "net_ret_capped": g_c - 0.004}, index=idx)


def test_b_equals_forgone_gross_plus_cost_saved():
    r = t.b_row(_comp(), "gross_ret_capped", "gross_ret", "net_ret_capped", "net_ret_uncapped", 100, 6, 0)
    assert abs(r["recon_residual"]) < 1e-12
    assert r["B"] == pytest.approx(r["gross_forgone"] + r["cost_saved"])
    assert r["cost_saved"] == pytest.approx(12 * 0.016)


def test_holm_is_monotone_and_capped_at_one():
    out = t.holm({"a": 0.01, "b": 0.02, "c": 0.5})
    assert out["a"] == pytest.approx(0.03) and out["b"] == pytest.approx(0.04) and out["c"] == pytest.approx(0.5)


def test_cell_level_rule_is_stricter_than_composite_rule():
    # one of eight cells goes to -150% while the composite stays above -100%
    dates = pd.date_range("2010-01-31", periods=3, freq="ME")
    rows = []
    for cell in range(8):
        for i, d in enumerate(dates):
            r = -1.5 if (cell == 0 and i == 1) else 0.01
            rows.append({"date": d, "cell": f"c{cell}", "net_ret_uncapped": r, "net_ret_capped": 0.01})
    g = pd.DataFrame(rows)
    comp = t.composite_from_cells(g, ["net_ret_uncapped", "net_ret_capped"])
    assert comp["net_ret_uncapped"].min() > -1.0          # composite rule would pass
    assert g["net_ret_uncapped"].min() <= -1.0            # cell rule fails: that account is gone
