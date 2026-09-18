"""Model cells (workstream B): the 16 factorial combinations plus published ML benchmarks."""
from .attention import AttentionCell  # noqa: F401
from .base import FeatureSpec, build_design, rank_ic, split_frames  # noqa: F401
from .complexity import ComplexityCell, RandomFourierFeatures, spectrum_diagnostic  # noqa: F401
from .conformal import ConformalResult, coverage_report, split_conformal  # noqa: F401
from .benchmarks import PRESETS, jkmp_instructions, run_benchmark  # noqa: F401
from .cells import CellRunConfig, run_cell  # noqa: F401
from .stability import compare_to_cell_gap, dispersion, run_seeds  # noqa: F401
from .economic import EconomicPolicy, prepare_months  # noqa: F401
from .linear import RidgeCell  # noqa: F401
from .nonlinear import LGBMCell, MoECell, NNCell  # noqa: F401
from .uncertainty import proxy_weights, select_kappa  # noqa: F401

__all__ = [
    "AttentionCell", "ComplexityCell", "ConformalResult", "RandomFourierFeatures", "coverage_report",
    "spectrum_diagnostic", "split_conformal",
    "CellRunConfig", "EconomicPolicy", "FeatureSpec", "LGBMCell", "MoECell", "NNCell", "PRESETS", "RidgeCell",
    "build_design", "compare_to_cell_gap", "dispersion", "jkmp_instructions", "prepare_months", "proxy_weights",
    "rank_ic", "run_benchmark", "run_cell", "run_seeds", "select_kappa", "split_frames",
]
