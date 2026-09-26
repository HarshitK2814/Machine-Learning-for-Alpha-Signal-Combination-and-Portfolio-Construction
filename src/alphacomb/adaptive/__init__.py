"""Self-adapting model combination (workstream B).

Two capabilities, both with a fixed ex-ante rule and no tuning on test data:

* ``hedge`` - exponentially weighted aggregation over model cells, scored on realised after-tax
  return, with a regret bound against the best member in hindsight.
* ``drift`` - sequential change detection that decides *when* to refit, instead of refitting on a
  calendar because everybody else does.
"""
from .drift import DriftEvent, PageHinkley, calibrate_threshold, detect, refit_schedule  # noqa: F401
from .hedge import (HedgeAggregator, HedgeConfig, HedgeState, best_in_hindsight,  # noqa: F401
                    equal_weight_benchmark, run_aggregation)
from .meta import (MemberResult, adaptation_report, assert_causal, build_members,  # noqa: F401
                   combine, compare, equal_weight_alpha, member_rewards)

__all__ = [
    "DriftEvent", "HedgeAggregator", "HedgeConfig", "HedgeState", "MemberResult", "PageHinkley",
    "adaptation_report", "assert_causal", "best_in_hindsight", "build_members", "calibrate_threshold",
    "combine", "compare", "detect", "equal_weight_alpha", "equal_weight_benchmark", "member_rewards", "refit_schedule",
    "run_aggregation",
]
