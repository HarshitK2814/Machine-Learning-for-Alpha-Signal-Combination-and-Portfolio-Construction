"""Presence-only gap census: run detection, recovery flags, no numeric value retained. Synthetic fixtures only."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

TOOL = Path(__file__).resolve().parents[2] / "tools" / "phase_c_recovery_presence_check.py"
spec = importlib.util.spec_from_file_location("phase_c_recovery_presence_check", TOOL)
mod = importlib.util.module_from_spec(spec)
sys.modules["phase_c_recovery_presence_check"] = mod
spec.loader.exec_module(mod)

M = pd.period_range("2012-01", "2012-08", freq="M")


def _frames(spec_by_name):
    """spec_by_name: permno -> list per month of (ret_usable, price_present, in_universe) or None (no C4 row)."""
    c4, c1 = [], []
    for p, seq in spec_by_name.items():
        for m, s in zip(M, seq):
            if s is None:
                continue
            ret, price, inu = s
            d = m.to_timestamp(how="end").normalize()
            c4.append((d, p, 0.5551234 if ret else np.nan, 0.0777 if ret else np.nan))
            c1.append((d, p, inu, 4.4412 if price else np.nan))
    t = pd.DataFrame(c4, columns=["date", "permno", "ret_next", "div_next"])
    u = pd.DataFrame(c1, columns=["date", "permno", "in_universe", "price"])
    return mod.flags_c4(t), mod.flags_c1(u)


def _runs(spec):
    c4, c1 = _frames(spec)
    return mod.gap_runs(c4, c1, M[0].ordinal, M[-1].ordinal)


OK, GAP, GAPNP = (True, True, False), (False, True, False), (False, False, False)


def test_flags_hold_only_booleans_and_keys():
    c4, c1 = _frames({1: [OK, GAP]})
    assert set(c4.columns) == {"mi", "permno", "ret_ok", "div_ok"} and c4["ret_ok"].dtype == bool
    assert set(c1.columns) == {"mi", "permno", "in_univ", "price_present"} and c1["price_present"].dtype == bool


def test_recovering_run_with_price_only_at_some_months():
    r = _runs({1: [OK, GAP, GAPNP, OK, OK, OK, OK, OK]})
    assert len(r) == 1
    x = r.iloc[0]
    assert x.run_len_months == 2 and x.ends == "recovers_to_usable_ret_next"
    assert not x.c1_price_present_at_every_run_month and x.c1_price_present_at_recovery_month
    assert x.div_next_unusable_throughout_run and not x.all_run_months_in_universe and x.prior_month_ret_next_usable


def test_open_run_and_missing_c4_row_are_not_recoveries():
    r = _runs({1: [OK, GAP, GAP, GAP, GAP, GAP, GAP, GAP], 2: [OK, GAP, None, OK, OK, OK, OK, OK]})
    assert (r["ends"] != "recovers_to_usable_ret_next").all()          # a later usable return after a missing C4 month is not a bridge


def test_run_with_price_at_every_month_is_flagged_but_still_has_no_dividend_information():
    r = _runs({1: [OK, GAP, GAP, OK, OK, OK, OK, OK]})
    x = r.iloc[0]
    assert x.c1_price_present_at_every_run_month and x.div_next_unusable_throughout_run
