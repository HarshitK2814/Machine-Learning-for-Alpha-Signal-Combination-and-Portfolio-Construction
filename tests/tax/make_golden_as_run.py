"""One-off: regenerate the as_run golden frames. Run ONLY against an unmodified evaluator."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from exit_fixtures import SCENARIOS, run  # noqa: E402

frames = []
for name, make in SCENARIOS.items():
    b, w = make()
    f, _ = run(b, w)
    f.insert(0, "scenario", name)
    frames.append(f)
pd.concat(frames, ignore_index=True).to_parquet(Path(__file__).parent / "golden" / "as_run_exit_scenarios.parquet")
print("written")
