"""The self-adapting combiner: turn several model cells into one strategy that re-weights itself.

The pieces:

  member cells  ->  each cell's own weights  ->  each cell's realised after-tax return
                                                          |
                                                          v
                                              HedgeAggregator (fixed rule, no tuning)
                                                          |
                                                          v
                             combination weights for month t, using data through t-1
                                                          |
                                                          v
                      combined alpha -> the one shared optimiser -> after-tax backtest

Two properties make this defensible rather than a monthly specification search:

1. **Strict causality.** The weight applied to a member in month t is produced by ``update`` calls
   on months t-1 and earlier. ``assert_causal`` checks this on the produced panel rather than
   trusting the loop.
2. **The reward is the objective.** Members are scored on after-tax net return - the thing the
   investor keeps - not on information coefficient or gross Sharpe. A model that forecasts well but
   trades expensively loses weight automatically, which is the entire point.

The honest comparison is not "adaptive versus the worst member". It is adaptive versus (a) the
equal-weighted blend of the same members, (b) the best single member chosen in hindsight, and
(c) each member alone. ``compare`` reports all of them, because online aggregation routinely fails
to beat the equal-weighted blend and a paper that hides that is not worth writing.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..tax import TaxConfig, after_tax_backtest, summarise_after_tax
from .drift import detect
from .hedge import HedgeAggregator, HedgeConfig


@dataclass
class MemberResult:
    name: str
    returns: pd.DataFrame        # extended C12 table from the after-tax backtest
    predictions: pd.DataFrame    # contract C9


def member_rewards(members: list[MemberResult], column: str = "after_tax_ret") -> pd.DataFrame:
    """Monthly reward panel (index = date, columns = member names) for the aggregator."""
    frames = {}
    for m in members:
        s = m.returns.set_index("date")[column]
        frames[m.name] = s[~s.index.duplicated(keep="last")]
    panel = pd.DataFrame(frames).sort_index()
    return panel.dropna(how="all")


def assert_causal(weights: pd.DataFrame, rewards: pd.DataFrame) -> None:
    """Fail loudly if a combination weight could have seen the month it is applied to.

    Cheap to run and the single most valuable assertion in this module: the whole claim rests on it.
    """
    wdates = pd.DatetimeIndex(weights["date"]).sort_values()
    rdates = pd.DatetimeIndex(rewards.index).sort_values()
    if len(wdates) == 0:
        return
    first_active = weights.loc[weights["n_updates"] > 0, "date"]
    if not len(first_active):
        return
    first = pd.Timestamp(first_active.iloc[0])
    if first <= rdates[0]:
        raise AssertionError(
            f"combination weights became active on {first.date()} but the first reward observation "
            f"is {rdates[0].date()}; the rule would be using contemporaneous information")


def combine(members: list[MemberResult], cfg: HedgeConfig | None = None,
            reward_column: str = "after_tax_ret") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the aggregator over the members. Returns (weight panel, combined alpha table C9)."""
    rewards = member_rewards(members, reward_column)
    names = list(rewards.columns)
    agg = HedgeAggregator(names, cfg)

    rows = []
    active = agg.state.as_series()
    updates = 0
    for date, row in rewards.iterrows():
        rows.append({"date": pd.Timestamp(date), "n_updates": updates,
                     "n_effective": float(1.0 / np.sum(active.to_numpy() ** 2)),
                     **{n: float(active[n]) for n in names}})
        active = agg.update(row)
        updates += 1
    weight_panel = pd.DataFrame(rows)
    assert_causal(weight_panel, rewards)

    preds = {m.name: m.predictions.set_index(["date", "permno"]) for m in members}
    combined = []
    for _, wrow in weight_panel.iterrows():
        date = wrow["date"]
        acc = None
        for name in names:
            table = preds[name]
            if date not in table.index.get_level_values(0):
                continue
            slice_ = table.xs(date, level=0)
            contrib = slice_[["score", "alpha"]] * float(wrow[name])
            acc = contrib if acc is None else acc.add(contrib, fill_value=0.0)
        if acc is None or acc.empty:
            continue
        acc = acc.reset_index()
        acc.insert(0, "date", date)
        combined.append(acc)
    alpha = (pd.concat(combined, ignore_index=True) if combined
             else pd.DataFrame(columns=["date", "permno", "score", "alpha"]))
    if not alpha.empty:
        alpha["permno"] = alpha["permno"].astype("int32")
    weight_panel.attrs["regret_bound"] = agg.regret_bound()
    weight_panel.attrs["best_member"] = names[int(np.argmax(agg.state.cumulative))]
    weight_panel.attrs["member_totals"] = dict(zip(names, agg.state.cumulative.tolist()))
    return weight_panel, alpha


def compare(members: list[MemberResult], combined_returns: pd.DataFrame,
            reward_column: str = "after_tax_ret") -> pd.DataFrame:
    """Adaptive versus every benchmark it has to beat before the result means anything."""
    rewards = member_rewards(members, reward_column)
    rows = []
    for name in rewards.columns:
        m = next(x for x in members if x.name == name)
        rows.append({"strategy": name, "kind": "member", **summarise_after_tax(m.returns)})
    eq = rewards.mean(axis=1)
    rows.append({"strategy": "equal_weight_blend", "kind": "benchmark",
                 **_summary_from_series(eq)})
    best = rewards.sum().idxmax()
    rows.append({"strategy": f"best_in_hindsight[{best}]", "kind": "not_implementable",
                 **_summary_from_series(rewards[best])})
    rows.append({"strategy": "adaptive_hedge", "kind": "adaptive",
                 **summarise_after_tax(combined_returns)})
    keep = ["strategy", "kind", "months", "net_sharpe", "after_tax_sharpe", "after_tax_mean_ann",
            "tax_drag_ann_bps", "total_drag_ann_bps", "turnover_mean", "max_drawdown"]
    frame = pd.DataFrame(rows)
    return frame[[c for c in keep if c in frame.columns]]


def _summary_from_series(series: pd.Series, periods: int = 12) -> dict:
    """Summary for a synthetic return stream that has no cost ledger of its own."""
    ann = np.sqrt(periods)
    sd = series.std(ddof=1)
    cum = (1 + series).cumprod()
    return {"months": int(len(series)),
            "after_tax_sharpe": float(series.mean() / sd * ann) if sd > 0 else float("nan"),
            "after_tax_mean_ann": float(series.mean() * periods),
            "max_drawdown": float((cum / cum.cummax() - 1).min())}


def adaptation_report(weight_panel: pd.DataFrame, members: list[MemberResult],
                      reward_column: str = "after_tax_ret") -> dict:
    """How much did the rule actually move, and did it move for a reason?"""
    rewards = member_rewards(members, reward_column)
    names = list(rewards.columns)
    w = weight_panel.set_index("date")[names]
    turnover = w.diff().abs().sum(axis=1).mean() / 2
    drift_events = detect(rewards.mean(axis=1))
    return {
        "months": int(len(w)),
        "members": names,
        "mean_effective_members": float(weight_panel["n_effective"].mean()),
        "min_effective_members": float(weight_panel["n_effective"].min()),
        "weight_turnover_monthly": float(turnover),
        "final_weights": w.iloc[-1].round(4).to_dict(),
        "max_weight_ever": float(w.to_numpy().max()),
        "regret_bound": float(weight_panel.attrs.get("regret_bound", float("nan"))),
        "best_member": weight_panel.attrs.get("best_member", ""),
        "drift_events": [(e.date.date().isoformat(), e.direction) for e in drift_events],
    }


def build_members(strategies: list[str], bundle, cfg: dict, tax_cfg: TaxConfig | None = None,
                  read_table=None, paths=None) -> list[MemberResult]:
    """Load each member's weights and predictions and run its own after-tax backtest."""
    from ..contracts import paths as default_paths, read_table as default_read
    read_table = read_table or default_read
    paths = paths or default_paths
    out = []
    for name in strategies:
        wpath = paths.latest_run("weights", name)
        ppath = paths.latest_run("predictions", name)
        if wpath is None or ppath is None:
            continue
        weights = read_table(wpath, "weights")
        returns = after_tax_backtest(weights, bundle, cfg, tax_cfg)
        out.append(MemberResult(name=name, returns=returns, predictions=read_table(ppath, "predictions")))
    return out
