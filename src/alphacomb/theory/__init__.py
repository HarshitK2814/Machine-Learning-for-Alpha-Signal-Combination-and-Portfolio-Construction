"""The economic model. Converts "we measured this" into "theory predicts this and we test it".

The publication audit named the absence of a mechanism as one of two fatal blockers we could
actually act on. This package supplies it: a tractable steady-state model of a taxable investor
facing a realisation-based capital-gains tax with a holding-period boundary, which delivers a
closed-form comparative static that maps one-to-one onto the cross-country empirical design.

The result in one line:

    after-tax return  =  g(1 - theta_L)  -  kappa * p  -  g * Delta * Phi(p, H)

where ``g`` is the gross return, ``kappa`` the round-trip transaction cost and transaction tax,
``p`` the per-period turnover, ``H`` the statutory holding-period boundary, ``Delta = theta_S -
theta_L`` the **wedge**, and ``Phi(p, H)`` the share of gains realised at the short-term rate.

The two friction channels separate cleanly, and that separation is the whole paper:

    d(return)/dp  =  -kappa            (turnover channel, independent of tax architecture)
                     - g * Delta * dPhi/dp   (holding-period channel, proportional to the WEDGE)

**In a flat-rate country Delta = 0 and the second channel vanishes identically.** Not "is small" -
vanishes, as a matter of law. Germany and Japan are therefore placebos the tax code wrote for us,
and the empirical prediction that the friction penalty is ordered by the wedge rather than by the
transaction tax is a theorem here, not a hope.
"""
from .tax_model import (TaxedStrategy, after_tax_return, channel_decomposition,  # noqa: F401
                        comparative_static, long_term_share, marginal_cost_of_turnover,
                        optimal_turnover, short_term_share)

__all__ = [
    "TaxedStrategy", "after_tax_return", "channel_decomposition", "comparative_static",
    "long_term_share", "marginal_cost_of_turnover", "optimal_turnover", "short_term_share",
]
