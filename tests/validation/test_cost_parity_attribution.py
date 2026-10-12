"""Tests for the arithmetic of tools/diag_cost_parity.py (attribution and cost split)."""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import diag_cost_parity as dcp  # noqa: E402
from alphacomb.portfolio.cost_terms import trade_cost_numpy  # noqa: E402


def _v(base, dD, dX, dB):
    """Cost under each combination when the three switches act additively (A convention = effect added)."""
    return {"".join(c): base + (dD if c[0] == "A" else 0) + (dX if c[1] == "A" else 0) + (dB if c[2] == "A" else 0)
            for c in itertools.product("AB", repeat=3)}


def test_additive_switches_have_no_interaction_and_shapley_equals_effects():
    full, e, sh, inter = dcp.attribute(_v(10.0, 2.0, -3.0, 1.0))
    assert full == pytest.approx(0.0)
    assert inter == pytest.approx(0.0)
    for m, eff in zip("DXB", (2.0, -3.0, 1.0)):
        assert e[m] == pytest.approx(eff) and sh[m] == pytest.approx(eff)


def test_shapley_is_efficient_even_with_interaction():
    v = {"".join(c): float(np.random.default_rng(i).normal()) for i, c in enumerate(itertools.product("AB", repeat=3))}
    full, e, sh, inter = dcp.attribute(v)
    assert sum(sh.values()) == pytest.approx(full)
    assert inter == pytest.approx(full - sum(e.values()))


def test_one_at_a_time_effect_is_measured_from_the_tier_b_baseline():
    v = _v(0.0, 1.0, 1.0, 1.0)
    v["ABB"] = 5.0                                   # switching only D from B to A
    _, e, _, _ = dcp.attribute(v)
    assert e["D"] == pytest.approx(5.0 - v["BBB"])


def test_cost_split_is_exact_and_k_zero_is_the_linear_part():
    rng = np.random.default_rng(0)
    dw = rng.normal(0, 0.01, 20)
    sp, sd, ad = rng.uniform(0.001, 0.01, 20), rng.uniform(0.01, 0.03, 20), rng.uniform(1e6, 1e8, 20)
    lin, imp = dcp._parts(dw, sp, sd, ad, 1e8, 1.0, 1.0)
    assert lin + imp == pytest.approx(float(trade_cost_numpy(dw, sp, sd, ad, 1e8, 1.0, 1.0).sum()))
    assert lin == pytest.approx(float(((0.5 * sp + 1e-4) * np.abs(dw)).sum()))
    assert imp > 0
    assert dcp._parts(np.array([]), sp[:0], sd[:0], ad[:0], 1e8, 1.0, 1.0) == (0.0, 0.0)
