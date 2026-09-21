"""Tax terms inside the optimiser: let the portfolio know what a trade costs in tax before it trades.

Measuring tax after the fact (``alphacomb.tax``) tells you the damage. Putting it in the objective
lets the optimiser avoid it. Both are needed, and they must use the same ledger, or the optimiser
will be optimising against a tax model the accountant does not recognise.

The term added to the objective is

    tax(w) = sum_i  rate_i * max(g_i, 0) * pos(w_prev_i - w_i)      (gains: a cost of selling)
           - sum_i  rate_i * |min(g_i, 0)| * s_i                     (losses: a benefit of selling)

where ``g_i`` is the embedded gain per dollar of position i, ``rate_i`` is the blended statutory
rate the ledger would apply to that position today, and ``s_i`` is a bounded sell variable with
``0 <= s_i <= w_prev_i`` and ``s_i <= w_prev_i - w_i``.

Convexity. The first sum is convex (``pos`` is convex, coefficients are non-negative), so its
negative is concave and safe inside a maximisation. The second sum needs the auxiliary variable:
writing it directly as a function of ``w`` would make the objective non-concave. Bounding ``s_i`` by
the existing position is what stops the solver from manufacturing unlimited harvesting.

The wash-sale trap. An optimiser with a harvesting reward and no further constraint will sell a
loser and buy it straight back the next month - and s1091 will disallow exactly that loss. This is
not hypothetical; it is what a naive tax-aware optimiser does. ``blocked`` carries the names that
are inside the 30-day window, and ``apply_wash_block`` forbids re-establishing them. We run the
optimiser with and without the block on purpose, because the gap between the two is a result.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class TaxState:
    """What the optimiser needs to know about the tax position, as of the rebalance date.

    Produced by ``from_ledger`` so that the optimiser and the after-tax backtest cannot disagree.
    """

    gain_rate: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))   # gain per dollar held
    tax_rate: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))    # blended statutory rate
    blocked: pd.Index = field(default_factory=lambda: pd.Index([], dtype="int64"))  # s1091 window
    allow_harvest: bool = True

    @staticmethod
    def from_ledger(ledger, permnos: pd.Index, date, wash_block: bool = False) -> "TaxState":
        gains, rates = {}, {}
        for permno in permnos:
            g, r = ledger.embedded_gain_rate(int(permno), date)
            gains[permno] = g
            rates[permno] = r
        blocked = pd.Index([], dtype="int64")
        if wash_block:
            window = pd.Timedelta(days=ledger.regime.wash_sale_window_days)
            cutoff = pd.Timestamp(date) - window
            blocked = pd.Index(sorted({p.permno for p in ledger._pending_losses if p.date >= cutoff}),
                               dtype="int64")
        return TaxState(gain_rate=pd.Series(gains, dtype=float),
                        tax_rate=pd.Series(rates, dtype=float), blocked=blocked)

    def aligned(self, permnos: pd.Index) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(gain per dollar, rate, blocked mask) as dense arrays over the optimisation universe."""
        g = self.gain_rate.reindex(permnos).fillna(0.0).to_numpy(dtype=float)
        r = self.tax_rate.reindex(permnos).fillna(0.0).to_numpy(dtype=float)
        blocked = np.isin(np.asarray(permnos), np.asarray(self.blocked))
        return g, r, blocked

    @property
    def empty(self) -> bool:
        return self.gain_rate.empty or float(np.abs(self.tax_rate.to_numpy()).max(initial=0.0)) == 0.0


def tax_cost_numpy(w: np.ndarray, w_prev: np.ndarray, gain_rate: np.ndarray,
                   tax_rate: np.ndarray) -> np.ndarray:
    """Per-name tax consequence of moving from ``w_prev`` to ``w``, in return units.

    Positive is a cost. Used for reporting and for checking the convex term against a direct
    computation in the tests.
    """
    sold = np.clip(np.asarray(w_prev, dtype=float) - np.asarray(w, dtype=float), 0.0, None)
    sold = np.where(np.asarray(w_prev, dtype=float) > 0, sold, 0.0)   # long positions only
    return np.asarray(tax_rate, dtype=float) * np.asarray(gain_rate, dtype=float) * sold


def cvx_tax_cost(w, w_prev: np.ndarray, gain_rate: np.ndarray, tax_rate: np.ndarray,
                 allow_harvest: bool = True, harvest_haircut: float = 1.0):
    """Convex CVXPY expression for the tax term, plus any auxiliary variables and constraints.

    Returns ``(expression, constraints)``. ``harvest_haircut`` scales the assumed benefit of
    realising a loss: 1.0 assumes the loss is fully usable against other gains this year, 0.0
    assumes it is worthless. The truth depends on the rest of the investor's tax position, so it is
    a parameter we report sensitivity to rather than a number we assert.
    """
    import cvxpy as cp

    prev = np.asarray(w_prev, dtype=float)
    g = np.asarray(gain_rate, dtype=float)
    rate = np.asarray(tax_rate, dtype=float)
    is_long = prev > 0

    gain_coeff = np.where(is_long, rate * np.clip(g, 0.0, None), 0.0)
    expr = gain_coeff @ cp.pos(prev - w)
    cons: list = []

    # The harvesting variable exists only for LONG positions, and so must its constraints.
    #
    # An earlier version created `s` over every name and imposed `s <= prev - w` on all of them.
    # For a short, prev < 0 forces s = 0 through `s <= max(prev, 0)` and nonnegativity, and the
    # second constraint then reads 0 <= prev - w, i.e. w <= prev < 0: **the short could only ever
    # get more negative, never be covered.** The book ratcheted its shorts open until the optimiser
    # went infeasible, and the tax-aware arms of the leverage sweep returned -117% a year.
    #
    # Restricting the variable to the long subset is not a patch on the symptom - harvesting a loss
    # means selling something you own, which is a long-side operation. Short-side losses are handled
    # by the gain term and by s1233 in the ledger.
    loss_coeff = np.where(is_long, rate * np.clip(-g, 0.0, None), 0.0) * float(harvest_haircut)
    long_idx = np.flatnonzero(is_long)
    if allow_harvest and len(long_idx) and float(loss_coeff[long_idx].max(initial=0.0)) > 0:
        s = cp.Variable(len(long_idx), nonneg=True)
        cons += [s <= prev[long_idx], s <= prev[long_idx] - w[long_idx]]
        expr = expr - loss_coeff[long_idx] @ s
    return expr, cons


def apply_wash_block(w, w_prev: np.ndarray, blocked: np.ndarray) -> list:
    """Forbid re-establishing a long position in a name whose loss is inside the s1091 window.

    Without this the optimiser harvests a loss and buys the name back, and the ledger then disallows
    the loss - the strategy pays the trading cost and gets nothing for it.
    """
    import cvxpy as cp

    mask = np.asarray(blocked, dtype=bool)
    if not mask.any():
        return []
    ceiling = np.where(mask, np.minimum(np.asarray(w_prev, dtype=float), 0.0), 1.0)
    return [w[mask] <= ceiling[mask]]


def tax_alpha_adjustment(alpha: pd.Series, holding_months: pd.Series, rate_spread: float,
                         expected_gain: pd.Series | None = None) -> pd.Series:
    """Deferral value of waiting for long-term treatment, expressed as an alpha bonus.

    A position two months short of twelve has an option worth ``rate_spread * embedded_gain`` if it
    is held rather than sold. Adding it to alpha makes the optimiser hold through the boundary when
    - and only when - the forecast loss from waiting is smaller than the tax saved. This is the
    mechanism Sialm and Sosner describe for tax-aware long/short books, written as an objective term.
    """
    months = holding_months.reindex(alpha.index).fillna(0.0)
    gain = (expected_gain.reindex(alpha.index).fillna(0.0)
            if expected_gain is not None else pd.Series(0.0, index=alpha.index))
    approaching = ((months > 6) & (months <= 12)).astype(float)
    return alpha + approaching * rate_spread * gain.clip(lower=0.0)
