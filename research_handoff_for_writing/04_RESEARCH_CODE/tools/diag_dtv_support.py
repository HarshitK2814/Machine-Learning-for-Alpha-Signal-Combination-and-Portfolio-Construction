#!/usr/bin/env python
"""Descriptive: how large are the books' trades relative to daily volume (ADV)?

Published live-trade impact estimates (Frazzini-Israel-Moskowitz 2018) are supported only up to about 12% of daily
volume per trade. This reports, for the six diagnostic rungs, the share of traded notional that lies beyond 12%
and beyond 100% of the name's daily volume. Accounting only: reads the frozen weights and cost inputs, changes
nothing. Trade size follows the wedge-tool convention (target to target, current-month ADV).

    python tools/diag_dtv_support.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RES = ROOT / "results" / "cost_parity_diagnostic"
RUNGS = [("DEU", 1e5), ("DEU", 3e5), ("DEU", 1e8), ("IND", 3e7), ("JPN", 1e9), ("JPN", 1e10)]
CELLS = [f"{a}-{b}-P-{d}" for a in "LN" for b in "SC" for d in ("0", "U")]


def main() -> int:
    from alphacomb.contracts import intl

    rows = []
    for country in ("DEU", "IND", "JPN"):
        bundle = intl.load_country_bundle(country, max_names=600)
        ci = bundle.cost_inputs[["date", "permno", "adv_usd"]].copy()
        ci["date"] = pd.to_datetime(ci["date"])
        adv = ci.set_index(["date", "permno"])["adv_usd"]
        for c, aum in [r for r in RUNGS if r[0] == country]:
            for book in ("uncapped", "capped"):
                num = {"all": 0.0, "gt12": 0.0, "gt100": 0.0}
                xs, ws = [], []
                for cell in CELLS:
                    w = pd.read_parquet(ROOT / "outputs" / "decile_weights" / country / "tierb" / f"aum_{aum:.0e}"
                                        / f"{book}_{cell}.parquet")
                    w["date"] = pd.to_datetime(w["date"])
                    piv = w.pivot(index="date", columns="permno", values="w").fillna(0.0).sort_index()
                    dw = piv.diff().abs()
                    dw.iloc[0] = piv.iloc[0].abs()
                    st = dw.stack()
                    st = st[st > 0]
                    a = adv.reindex(st.index)
                    x = st.to_numpy() * aum / a.to_numpy()
                    ok = np.isfinite(x)
                    st, x = st[ok], x[ok]
                    num["all"] += float(st.sum())
                    num["gt12"] += float(st[x > 0.12].sum())
                    num["gt100"] += float(st[x > 1.0].sum())
                    xs.append(x)
                    ws.append(st.to_numpy())
                x, wgt = np.concatenate(xs), np.concatenate(ws)
                order = np.argsort(x)
                cw = np.cumsum(wgt[order]) / wgt.sum()
                med = float(x[order][np.searchsorted(cw, 0.5)])
                rows.append({"country": c, "aum": aum, "book": book,
                             "share_notional_gt12pct_ADV": num["gt12"] / num["all"],
                             "share_notional_gt100pct_ADV": num["gt100"] / num["all"],
                             "notional_weighted_median_trade_pct_ADV": 100 * med})
    d = pd.DataFrame(rows)
    d.to_csv(RES / "dtv_support.csv", index=False)
    pd.set_option("display.width", 200)
    print(d.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
