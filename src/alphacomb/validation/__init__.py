"""Credibility layer (design v2): falsification audit and search-inflation accounting."""
from .falsification import (InflationGap, audit_report, expected_max_of_trials, inflation_gap,  # noqa: F401
                            microstructure_placebo, zero_predictability_panel)

__all__ = [
    "InflationGap", "audit_report", "expected_max_of_trials", "inflation_gap",
    "microstructure_placebo", "zero_predictability_panel",
]
