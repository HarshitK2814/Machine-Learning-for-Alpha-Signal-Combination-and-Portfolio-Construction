"""Hand-built non-synthetic panels for the exit-policy tests.

Six names, eight month-ends. Names 1 and 2 are long (+2% a month), 3 and 4 are short (-1% a month),
5 and 6 are bystanders. The bundle ``source`` is not ``synthetic*`` so the evaluator takes the same
fail-closed real-panel path it takes on DEU/IND/JPN. No real data is read here.
"""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd

import alphacomb.tax.backtest as bt
from alphacomb.contracts import load_config
from alphacomb.tax import TaxConfig, get_regime

DATES = pd.date_range("2020-01-31", periods=8, freq="ME")
NAMES = [1, 2, 3, 4, 5, 6]
BASE_W = {1: 0.25, 2: 0.25, 3: -0.25, 4: -0.25}


def build_bundle(frozen=None, gone=None, unpriced=None, reappear=None, ret_override=None):
    """frozen=(permno, first_month_idx[, recertified_month_idx]): C6 row present, spread NaN meanwhile.
    gone=(permno, first_month_idx): no C6 and no targets row from then on.
    unpriced=(permno, month_idx): C6 row present, ret_next NaN in that month only.
    reappear=month_idx: with ``gone``, the name is back from that month.
    ret_override={(permno, month_idx): ret_next} replaces a single forward return."""
    ci, tg = [], []
    for i, d in enumerate(DATES):
        for p in NAMES:
            if gone and p == gone[0] and i >= gone[1] and (reappear is None or i < reappear):
                continue
            sp = 0.002
            if frozen and p == frozen[0] and i >= frozen[1] and (len(frozen) < 3 or i < frozen[2]):
                sp = np.nan
            ci.append(dict(date=d, permno=p, spread=sp, sigma_d=0.02, adv_usd=1e8, borrow_fee=np.nan))
            r = 0.02 if p in (1, 2) else (-0.01 if p in (3, 4) else 0.0)
            if unpriced and p == unpriced[0] and i == unpriced[1]:
                r = np.nan
            if ret_override and (p, i) in ret_override:
                r = ret_override[(p, i)]
            tg.append(dict(date=d, permno=p, ret_next=r, div_next=0.0))
    ci, tg = pd.DataFrame(ci), pd.DataFrame(tg)
    for df in (ci, tg):
        df["permno"] = df["permno"].astype("int32")
    return SimpleNamespace(source="wrds_test", cost_inputs=ci, targets=tg)


def build_weights(drop_from=None):
    """``drop_from={permno: month_idx}`` removes that name from the weights file from then on."""
    drop_from = drop_from or {}
    rows = []
    for i, d in enumerate(DATES):
        for p, w in BASE_W.items():
            if p in drop_from and i >= drop_from[p]:
                continue
            rows.append(dict(date=d, permno=p, w=w))
    out = pd.DataFrame(rows)
    out["permno"] = out["permno"].astype("int32")
    return out


def build_cfg():
    cfg = load_config("base")
    return {**cfg, "costs": {**cfg["costs"], "aum_usd_2020": 1e7}}


def run(bundle, weights, regime="taxable", **tax_kwargs):
    """Run the evaluator and also return the TaxLotLedger it used (for lot-level assertions)."""
    captured = {}
    orig = bt.TaxLotLedger

    class _Capture(orig):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            captured["ledger"] = self

    bt.TaxLotLedger = _Capture
    try:
        tc = TaxConfig(regime=get_regime(regime), initial_nav=1e7, liquidate_at_end=False, **tax_kwargs)
        frame = bt.after_tax_backtest(weights, bundle, build_cfg(), tc)
    finally:
        bt.TaxLotLedger = orig
    return frame, captured["ledger"]


SCENARIOS = {
    "baseline": lambda: (build_bundle(), build_weights()),
    "frozen_omitted": lambda: (build_bundle(frozen=(1, 3)), build_weights({1: 3})),
    "frozen_in_weights": lambda: (build_bundle(frozen=(1, 3)), build_weights()),
    "exit_unevidenced": lambda: (build_bundle(gone=(2, 3)), build_weights({2: 3})),
    "exit_then_reappear": lambda: (build_bundle(gone=(2, 3), reappear=6), build_weights({2: 3})),
    "unpriced": lambda: (build_bundle(unpriced=(1, 3)), build_weights()),
}


def evidence(permno, month_idx, kind="delisting", cost_frac=None):
    row = dict(permno=permno, event_date=DATES[month_idx], kind=kind)
    if cost_frac is not None:
        row["liquidation_cost_frac"] = cost_frac
    return pd.DataFrame([row])
