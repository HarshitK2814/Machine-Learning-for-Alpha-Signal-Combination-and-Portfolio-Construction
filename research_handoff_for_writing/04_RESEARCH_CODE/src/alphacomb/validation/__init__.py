"""Credibility layer: statistical inference, falsification audit and search-inflation accounting.

``inference`` is the part a referee checks first. Without it every performance number in the
project is a bare point estimate produced by a search over hundreds of specifications, which is
exactly the situation the deflated Sharpe ratio and the probability of backtest overfitting exist
to police.
"""
from .falsification import (InflationGap, audit_report, expected_max_of_trials, inflation_gap,  # noqa: F401
                            microstructure_placebo, zero_predictability_panel)
from .preregistration import PreRegistration, audit as prereg_audit, factorial_plan  # noqa: F401
from .inference import (TestResult, benjamini_hochberg, deflated_sharpe, diebold_mariano,  # noqa: F401
                        hansen_spa, inference_report, newey_west_se, pbo_cscv, romano_wolf,
                        sharpe_se, sharpe_test)

__all__ = [
    "InflationGap", "TestResult", "audit_report", "benjamini_hochberg", "deflated_sharpe",
    "diebold_mariano", "expected_max_of_trials", "hansen_spa", "inference_report", "inflation_gap",
    "PreRegistration", "factorial_plan", "microstructure_placebo", "newey_west_se",
    "pbo_cscv", "prereg_audit", "romano_wolf", "sharpe_se",
    "sharpe_test", "zero_predictability_panel",
]
