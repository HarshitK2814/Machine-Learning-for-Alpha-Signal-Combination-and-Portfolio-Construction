"""Steady-state model of a taxable strategy under a realisation-based capital-gains tax.

Setup
-----
An investor runs a strategy at constant per-period turnover ``p``: each period a fraction ``p`` of
the book is closed and replaced. Holding durations are therefore geometric, ``D ~ Geom(p)``, with
``E[D] = 1/p``. While a position is held it accrues gains at rate ``g`` per period. On exit the
accumulated gain ``g * D`` is realised and taxed at

    theta(D) = theta_S  if D < H      (short-term)
               theta_L  if D >= H     (long-term)

Trading costs ``kappa`` per unit of value turned over cover spread, impact, brokerage **and**
statutory transaction taxes (India's STT, UK stamp duty, Taiwan's securities transaction tax).

The central algebra
-------------------
Expected tax paid per period is ``p * g * E[D * theta(D)]``. Split the rate into a base and a wedge,
``theta(D) = theta_L + Delta * 1{D < H}`` with ``Delta = theta_S - theta_L``:

    tax per period = p*g*( theta_L*E[D] + Delta*E[D*1{D<H}] )
                   = g*theta_L + g*Delta*Phi(p, H)

using ``p*E[D] = 1``, where

    Phi(p, H) = p * E[D * 1{D < H}] = 1 - H*(1-p)^(H-1) + (H-1)*(1-p)^H

is the **share of realised gains taxed at the short-term rate**. It runs from 0 (never trade,
everything long-term) to 1 (trade every period, everything short-term), and ``1 - Phi`` is exactly
the ``lt_share_of_gains`` the after-tax ledger reports - so the model's central object is something
the pipeline already measures.

Two consequences worth stating plainly, because both are easy to get wrong by intuition:

1. **Under a flat tax the bill does not depend on turnover at all.** With ``Delta = 0`` the tax per
   period is ``g*theta_L`` whatever ``p`` is: every dollar of gain is taxed once at the same rate,
   no matter how often it is realised. Turnover then matters only through ``kappa`` and through
   deferral, which is second order. The widespread belief that "high turnover means a big tax bill"
   is true *only* where a wedge exists.
2. **The wedge converts turnover into a rate.** With ``Delta > 0`` faster trading pushes gains
   across the boundary and raises the *effective rate*, not merely the amount traded. That is a
   first-order effect and it is the one the cost-aware machine-learning literature, which penalises
   turnover, cannot reach.

Deferral is deliberately omitted from the headline expression. Including it makes turnover costly
even at ``Delta = 0`` through the time value of postponed tax, which would blur the placebo. It is
available via ``discount`` for a robustness check, and the model is stated without it because the
identification rests on the clean ``Delta = 0`` case.

Limitations, stated rather than buried
--------------------------------------
Constant ``g`` and constant ``p``; geometric durations; no loss harvesting, no wash-sale rule, no
annual netting or carryforward; a single representative position. Each of those lives in the
lot-level ledger (``alphacomb.tax``), which is where the quantitative work happens. This model
exists to deliver a **sign and an ordering**, not a calibration.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


# --------------------------------------------------------------------------- the core object

def short_term_share(p: float | np.ndarray, H: int = 12) -> float | np.ndarray:
    """Phi(p, H): the share of realised gains that falls at the short-term rate.

    Closed form for geometric holding durations:

        Phi(p, H) = 1 - H*(1-p)^(H-1) + (H-1)*(1-p)^H

    Boundary behaviour: ``Phi(0, H) = 0`` (never trade, everything long-term) and ``Phi(1, H) = 1``
    (trade every period, everything short-term). ``H <= 1`` means every gain is short-term by
    definition, so ``Phi == 1``.
    """
    p = np.asarray(p, dtype=float)
    if H <= 1:
        return np.ones_like(p) if p.ndim else 1.0
    q = np.clip(1.0 - p, 0.0, 1.0)
    phi = 1.0 - H * q ** (H - 1) + (H - 1) * q ** H
    phi = np.clip(phi, 0.0, 1.0)
    return float(phi) if phi.ndim == 0 else phi


def long_term_share(p: float | np.ndarray, H: int = 12) -> float | np.ndarray:
    """1 - Phi. This is precisely ``lt_share_of_gains`` in the after-tax ledger."""
    return 1.0 - np.asarray(short_term_share(p, H))


def effective_tax_rate(p: float, theta_s: float, theta_l: float, H: int = 12) -> float:
    """The blended rate actually paid: theta_L + Delta * Phi(p, H)."""
    return theta_l + (theta_s - theta_l) * short_term_share(p, H)


# --------------------------------------------------------------------------- the strategy

@dataclass
class TaxedStrategy:
    """A strategy and the tax architecture it is run under.

    ``g`` is the gross return per period per unit of capital, ``kappa`` the round-trip cost and
    statutory transaction tax per unit turned over, ``p`` the per-period turnover.
    """

    g: float                       # gross return per period
    kappa: float                   # round-trip trading cost + transaction tax per unit turnover
    theta_s: float                 # short-term capital-gains rate
    theta_l: float                 # long-term capital-gains rate
    H: int = 12                    # statutory holding-period boundary, in periods
    discount: float = 0.0          # per-period discount rate, for the deferral robustness only

    @property
    def wedge(self) -> float:
        """Delta = theta_S - theta_L. Zero in a flat-rate country, and then so is channel two."""
        return self.theta_s - self.theta_l

    @property
    def has_wedge(self) -> bool:
        return abs(self.wedge) > 1e-12


def after_tax_return(strategy: TaxedStrategy, p: float) -> float:
    """After-tax return per period at turnover ``p``.

        R(p) = g*(1 - theta_L) - kappa*p - g*Delta*Phi(p, H)
    """
    s = strategy
    base = s.g * (1.0 - s.theta_l)
    trading = s.kappa * p
    wedge_cost = s.g * s.wedge * short_term_share(p, s.H)
    deferral = 0.0
    if s.discount > 0:
        # Tax deferred by the average holding period is worth roughly its discounted value; this
        # makes turnover costly even at Delta = 0, which is why it is off by default.
        mean_hold = 1.0 / max(p, 1e-9)
        deferral = -s.g * s.theta_l * (1.0 - 1.0 / (1.0 + s.discount) ** mean_hold)
    return float(base - trading - wedge_cost - deferral)


def marginal_cost_of_turnover(strategy: TaxedStrategy, p: float, eps: float = 1e-6) -> float:
    """-dR/dp: what one more unit of turnover costs, all in."""
    lo = after_tax_return(strategy, max(p - eps, 1e-9))
    hi = after_tax_return(strategy, min(p + eps, 1.0))
    return float(-(hi - lo) / (2 * eps))


def channel_decomposition(strategy: TaxedStrategy, p: float, eps: float = 1e-6) -> dict:
    """Split the marginal cost of turnover into its two channels. This is the paper's claim.

    * **turnover channel** = kappa. Present in every country, independent of the tax architecture.
    * **holding-period channel** = g * Delta * dPhi/dp. **Proportional to the wedge, so identically
      zero wherever the law sets a flat rate.**
    """
    s = strategy
    dphi = (short_term_share(min(p + eps, 1.0), s.H) -
            short_term_share(max(p - eps, 1e-9), s.H)) / (2 * eps)
    turnover_channel = s.kappa
    holding_channel = s.g * s.wedge * float(dphi)
    total = turnover_channel + holding_channel
    return {
        "turnover_channel": float(turnover_channel),
        "holding_period_channel": float(holding_channel),
        "total_marginal_cost": float(total),
        "holding_share_of_cost": float(holding_channel / total) if total != 0 else 0.0,
        "wedge": float(s.wedge),
        "dPhi_dp": float(dphi),
        "short_term_share": float(short_term_share(p, s.H)),
    }


def optimal_turnover(strategy: TaxedStrategy, signal_capture=None, grid: int = 2001) -> dict:
    """Turnover that maximises the after-tax return, when trading faster captures more signal.

    ``signal_capture(p)`` returns the gross return achievable at turnover ``p``; it should be
    increasing and concave. The default ``g * (1 - exp(-p / 0.1))`` saturates: the first units of
    turnover buy most of the available signal.

    Without such a function the problem is trivial - ``R`` is decreasing in ``p``, so ``p* = 0``.
    The economics is in the trade-off between capturing signal and paying to capture it.
    """
    s = strategy
    if signal_capture is None:
        def signal_capture(x):                      # noqa: ANN001
            return s.g * (1.0 - np.exp(-np.asarray(x, dtype=float) / 0.1))

    ps = np.linspace(1e-4, 1.0, grid)
    gs = np.asarray(signal_capture(ps), dtype=float)
    phi = np.asarray(short_term_share(ps, s.H))
    R = gs * (1.0 - s.theta_l) - s.kappa * ps - gs * s.wedge * phi
    k = int(np.argmax(R))
    return {
        "p_star": float(ps[k]),
        "return_at_p_star": float(R[k]),
        "gross_at_p_star": float(gs[k]),
        "short_term_share_at_p_star": float(phi[k]),
        "long_term_share_at_p_star": float(1.0 - phi[k]),
        "effective_rate_at_p_star": float(s.theta_l + s.wedge * phi[k]),
    }


def comparative_static(strategy: TaxedStrategy, wedges=None, signal_capture=None) -> "object":
    """**The testable prediction**: optimal turnover falls as the holding-period wedge rises.

    Holds everything else fixed - the same strategy, the same trading costs - and varies only
    ``Delta``. Returns one row per wedge with the optimal turnover, the long-term share of gains
    and the effective rate.

    Its empirical counterpart is the cross-country design: the United States has a 17-point wedge,
    India 7.5, and Germany, Japan, Singapore, Hong Kong and Taiwan have none at all.
    """
    import pandas as pd

    if wedges is None:
        wedges = [0.0, 0.025, 0.05, 0.075, 0.10, 0.13, 0.17]
    rows = []
    for delta in wedges:
        s = TaxedStrategy(g=strategy.g, kappa=strategy.kappa,
                          theta_s=strategy.theta_l + delta, theta_l=strategy.theta_l,
                          H=strategy.H, discount=strategy.discount)
        out = optimal_turnover(s, signal_capture)
        dec = channel_decomposition(s, out["p_star"])
        rows.append({
            "wedge": delta,
            "p_star": out["p_star"],
            "mean_holding_periods": 1.0 / max(out["p_star"], 1e-9),
            "lt_share_of_gains": out["long_term_share_at_p_star"],
            "effective_tax_rate": out["effective_rate_at_p_star"],
            "after_tax_return": out["return_at_p_star"],
            "turnover_channel": dec["turnover_channel"],
            "holding_period_channel": dec["holding_period_channel"],
        })
    return pd.DataFrame(rows)
