"""E29: attribution of net-of-cost value across the 2x2x2x2 design.

This is the paper's headline analysis. The design crosses four binary factors -

    N  nonlinearity        linear            vs nonlinear
    C  state dependence    static            vs conditional
    E  cost-aware objective prediction loss  vs economic loss
    U  uncertainty          no shrinkage     vs uncertainty shrinkage

- giving 16 cells, and asks how much of the *net-of-cost, after-tax* value each factor contributes,
alone and in combination.

Why contrasts of return series, not a regression on cell means
--------------------------------------------------------------
The obvious implementation is to take the 16 cell Sharpe ratios, regress them on contrast-coded
factors, and read off coefficients. That is wrong here, and wrong in a way that inflates
significance.

The 16 cells are run on the *same months*, over the *same universe*, with the *same* optimiser and
cost model. Their return series are therefore enormously correlated - typically 0.9+ between cells
that differ in one factor. Treating the 16 cell statistics as 16 independent observations throws
that away and produces standard errors that are far too small.

The fix is to form the contrast *in the time domain first*. For a contrast vector w over cells with
sum(w) = 0, define

    d(t) = sum_c w_c * r_c(t)

d is itself a monthly return series - a long/short portfolio of strategies. Its mean is the effect,
and its Newey-West standard error is the right standard error, because forming the difference has
already differenced out everything the cells share. Common variation cancels in d rather than being
mismodelled as noise.

This is also why the effects here are reported in return units (per month, and annualised) rather
than as Sharpe differences: a difference of Sharpe ratios is not the Sharpe of a difference, and
only the latter has a series whose autocorrelation we can model.

Shapley
-------
``shapley_attribution`` answers a different question: of the total value the full specification
delivers over the plain baseline cell, how much does each factor deserve? Factorial effects measure
marginal contributions at the design's centre; Shapley averages a factor's marginal contribution
over every order in which factors could be added, so the four numbers sum exactly to the total. The
paper should report both - they disagree precisely when interactions are large, and that
disagreement is itself a finding.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, permutations

import numpy as np
import pandas as pd

from .inference import newey_west_se

#: Factor codes in canonical order. Cell codes are "<N>-<C>-<E>-<U>", e.g. "N-C-E-U".
FACTORS = ("nonlinear", "conditional", "economic", "uncertainty")

#: The "on" level for each factor position in a cell code.
_ON = {0: "N", 1: "C", 2: "E", 3: "U"}
_OFF = {0: "L", 1: "S", 2: "P", 3: "0"}


def parse_cell(code: str) -> dict[str, int]:
    """Decode a cell label into +1/-1 per factor.

    ``"N-C-E-U"`` -> all four on; ``"L-S-P-0"`` -> all four off. Raises on anything else, because a
    silently mis-parsed cell would corrupt every contrast built from it.
    """
    parts = code.strip().split("-")
    if len(parts) != 4:
        raise ValueError(f"cell code {code!r} must have four factor positions, e.g. 'N-C-E-U'")
    levels = {}
    for i, (part, factor) in enumerate(zip(parts, FACTORS)):
        if part == _ON[i]:
            levels[factor] = 1
        elif part == _OFF[i]:
            levels[factor] = -1
        else:
            raise ValueError(
                f"position {i} of {code!r} is {part!r}; expected {_ON[i]!r} or {_OFF[i]!r}")
    return levels


def design_matrix(cells: list[str]) -> pd.DataFrame:
    """Contrast-coded (+1/-1) design over the supplied cells, indexed by cell code."""
    return pd.DataFrame({c: parse_cell(c) for c in cells}).T[list(FACTORS)]


@dataclass
class Effect:
    """One factorial effect, estimated from the contrast's own return series."""

    term: str
    order: int
    estimate_monthly: float
    se_monthly: float
    t_stat: float
    annualised: float
    n_months: int

    @property
    def significant_at_5pct(self) -> bool:
        return bool(np.isfinite(self.t_stat) and abs(self.t_stat) > 1.96)

    def __str__(self) -> str:
        star = "*" if self.significant_at_5pct else " "
        return (f"{self.term:<34} {self.annualised:+8.4f} p.a.  "
                f"t = {self.t_stat:+6.2f} {star}")


def _contrast_series(returns: pd.DataFrame, weights: pd.Series) -> np.ndarray:
    aligned = returns[weights.index]
    return aligned.to_numpy(dtype="float64") @ weights.to_numpy(dtype="float64")


def unbalanced_months(returns: pd.DataFrame) -> pd.DataFrame:
    """Months where at least one cell has no return, and which cells are missing.

    A contrast is only a difference between specifications if every cell is measured over the same
    months. Dropping an incomplete month silently changes the estimation window for *all* effects
    at once, and nothing downstream carries a record that it happened.
    """
    missing = returns.isna()
    bad = missing.any(axis=1)
    if not bad.any():
        return pd.DataFrame(columns=["n_missing", "cells"])
    rows = []
    for date in returns.index[bad]:
        absent = [c for c in returns.columns if bool(missing.loc[date, c])]
        rows.append({"n_missing": len(absent), "cells": ", ".join(absent)})
    return pd.DataFrame(rows, index=returns.index[bad])


def factorial_effects(returns: pd.DataFrame, max_order: int = 4,
                      periods: int = 12, lags: int | None = None,
                      require_balanced: bool = True) -> pd.DataFrame:
    """Estimate every factorial effect up to ``max_order``.

    ``returns`` is months x cells of **net-of-cost (and, for the main table, after-tax) returns**,
    with cell codes as columns. Every cell must be present on every month: an unbalanced panel
    makes the contrasts compare different time periods, so by default this **raises** rather than
    dropping. ``require_balanced=False`` estimates on the balanced subset instead, and the caller
    is then responsible for reporting which months went - ``unbalanced_months`` lists them.

    (Until 8 October 2026 the docstring promised that raise and the code did not do it: it dropped
    incomplete months and warned only if more than half the panel disappeared. A handful of missing
    months would therefore have moved the estimation window of every effect in the headline table
    with nothing on the face of the exhibit saying so.)

    Each effect is the mean of its own contrast series, with a Newey-West standard error. The
    contrast is scaled so the estimate is a difference of group means (the conventional "effect"),
    not a raw sum.
    """
    if returns.empty:
        raise ValueError("no cell returns supplied")
    bad = unbalanced_months(returns)
    if len(bad) and require_balanced:
        worst = bad.head(5).to_string()
        raise ValueError(
            f"factorial panel is unbalanced: {len(bad)} of {len(returns)} months are missing at "
            f"least one cell. Contrasts across different months are not differences between "
            f"specifications. Re-run the missing cells, or pass require_balanced=False to estimate "
            f"on the balanced subset and report the loss.\n{worst}")
    frame = returns.dropna(how="any")
    if frame.empty:
        raise ValueError(
            "no month has a return for every cell; factorial contrasts require a balanced panel")

    cells = list(frame.columns)
    design = design_matrix(cells)
    rows: list[Effect] = []

    for order in range(1, max_order + 1):
        for combo in combinations(FACTORS, order):
            # Interaction column is the elementwise product of the contrast codes.
            code = design[list(combo)].prod(axis=1)
            # Scale to a difference of means between the +1 and -1 halves.
            weights = code / (len(cells) / 2.0)
            series = _contrast_series(frame, weights)
            mean = float(np.mean(series))
            se = float(newey_west_se(series, lags=lags))
            rows.append(Effect(
                term=" x ".join(combo),
                order=order,
                estimate_monthly=mean,
                se_monthly=se,
                t_stat=float(mean / se) if se > 0 else float("nan"),
                annualised=mean * periods,
                n_months=len(frame),
            ))

    out = pd.DataFrame([vars(e) for e in rows])
    out["significant_5pct"] = out["t_stat"].abs() > 1.96
    return out.sort_values(["order", "term"]).reset_index(drop=True)


def shapley_attribution(returns: pd.DataFrame, periods: int = 12) -> pd.DataFrame:
    """Shapley value of each factor, over the mean net return of each cell.

    The four values sum exactly to the difference between the all-on cell and the all-off cell, so
    the table reconciles: every unit of value the full specification delivers is assigned to one
    factor. Compare against :func:`factorial_effects` - where the two disagree, interactions are
    doing the work, which is itself reportable.
    """
    frame = returns.dropna(how="any")
    if frame.empty:
        raise ValueError("no month has a return for every cell")
    cells = list(frame.columns)
    design = design_matrix(cells)
    means = frame.mean()

    def value(active: frozenset) -> float:
        """Mean return of the cell with exactly ``active`` factors switched on."""
        mask = pd.Series(True, index=design.index)
        for f in FACTORS:
            want = 1 if f in active else -1
            mask &= design[f] == want
        hits = design.index[mask]
        if len(hits) == 0:
            raise KeyError(f"no cell with factors on = {sorted(active)}")
        return float(means[hits].mean())

    n = len(FACTORS)
    contributions = {f: 0.0 for f in FACTORS}
    orders = list(permutations(FACTORS))
    for order in orders:
        active: set = set()
        prev = value(frozenset(active))
        for f in order:
            active.add(f)
            cur = value(frozenset(active))
            contributions[f] += cur - prev
            prev = cur
    for f in contributions:
        contributions[f] /= len(orders)

    total = value(frozenset(FACTORS)) - value(frozenset())
    out = pd.DataFrame({
        "factor": list(FACTORS),
        "shapley_monthly": [contributions[f] for f in FACTORS],
    })
    out["shapley_annualised"] = out["shapley_monthly"] * periods
    out["share_of_total"] = out["shapley_monthly"] / total if total != 0 else np.nan
    # Reconciliation is the point of Shapley; assert it rather than trusting it.
    assert np.isclose(out["shapley_monthly"].sum(), total, atol=1e-10), (
        "Shapley values must sum to the all-on minus all-off difference")
    out.attrs["total_monthly"] = total
    out.attrs["total_annualised"] = total * periods
    return out


def attribution_report(returns: pd.DataFrame, periods: int = 12,
                       max_order: int = 4,
                       require_balanced: bool = True) -> dict[str, pd.DataFrame]:
    """Both attributions plus the cell table, ready for the paper's main exhibit.

    The returned ``cells`` table carries ``attrs["n_months"]`` and ``attrs["months_dropped"]`` so
    the exhibit can state the estimation window rather than implying the full sample.
    """
    bad = unbalanced_months(returns)
    frame = returns.dropna(how="any")
    cells = design_matrix(list(frame.columns))
    cells["mean_monthly"] = frame.mean()
    cells["annualised"] = cells["mean_monthly"] * periods
    cells["sd_monthly"] = frame.std()
    cells["sharpe_annualised"] = np.where(
        cells["sd_monthly"] > 0,
        cells["mean_monthly"] / cells["sd_monthly"] * np.sqrt(periods), np.nan)
    cells.attrs["n_months"] = int(len(frame))
    cells.attrs["months_dropped"] = int(len(bad))
    return {
        "cells": cells.sort_values("annualised", ascending=False),
        "effects": factorial_effects(returns, max_order=max_order, periods=periods,
                                     require_balanced=require_balanced),
        "shapley": shapley_attribution(frame, periods=periods),
        "balance": bad,
    }
