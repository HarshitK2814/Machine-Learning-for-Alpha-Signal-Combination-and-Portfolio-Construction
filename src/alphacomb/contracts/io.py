"""Reading and writing contract artefacts, plus the append-only trial log. SHARED FILE."""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import paths
from .schemas import validate


def read_yaml(path: str | Path) -> dict:
    """Minimal YAML reader for the flat config files in ``configs/`` (no external dependency)."""
    import ast

    out: dict = {}
    stack: list[tuple[int, dict]] = [(-1, out)]
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.split(" #")[0].rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        key, _, value = line.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        value = value.strip()
        if value == "":
            child: dict = {}
            parent[key.strip()] = child
            stack.append((indent, child))
            continue
        if value.lower() in {"null", "none", "~"}:
            parsed = None
        elif value.lower() in {"true", "false"}:
            parsed = value.lower() == "true"
        elif value.startswith("[") and value.endswith("]"):
            # inline list; items may be unquoted (e.g. [CLARABEL, SCS]) or numeric
            items = [it.strip() for it in value[1:-1].split(",") if it.strip()]
            parsed = []
            for it in items:
                try:
                    parsed.append(ast.literal_eval(it))
                except (ValueError, SyntaxError):
                    parsed.append(it.strip('"').strip("'"))
        else:
            try:
                parsed = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                parsed = value.strip('"').strip("'")
        parent[key.strip()] = parsed
    return out


def load_config(name: str = "base") -> dict:
    return read_yaml(paths.REPO_ROOT / "configs" / f"{name}.yaml")


def write_table(df: pd.DataFrame, path: Path, contract: str | None = None) -> Path:
    if contract:
        validate(df, contract)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def read_table(path: Path, contract: str | None = None) -> pd.DataFrame:
    df = pd.read_parquet(path)
    if contract:
        validate(df, contract)
    return df


@dataclass
class DataBundle:
    """Everything a model or optimiser may read (contracts C1-C6)."""

    universe: pd.DataFrame
    signals: pd.DataFrame
    signal_meta: pd.DataFrame
    targets: pd.DataFrame
    states: pd.DataFrame
    cost_inputs: pd.DataFrame
    source: str = "synthetic"

    @property
    def signal_columns(self) -> list[str]:
        return [c for c in self.signals.columns if c.startswith("sig_")]

    @property
    def state_columns(self) -> list[str]:
        return [c for c in self.states.columns if c not in {"date"}]

    @property
    def dates(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex(sorted(self.universe["date"].unique()))

    def panel(self, columns: list[str] | None = None) -> pd.DataFrame:
        """Universe x signals x targets x cost inputs joined on (date, permno), universe members only."""
        u = self.universe.loc[self.universe["in_universe"], ["date", "permno", "me", "price", "ff49", "nyse_size_pct"]]
        df = (
            u.merge(self.signals, on=["date", "permno"], how="left")
            .merge(self.targets, on=["date", "permno"], how="left")
            .merge(self.cost_inputs, on=["date", "permno"], how="left")
        )
        if columns:
            keep = ["date", "permno", *columns]
            df = df[[c for c in keep if c in df.columns]]
        return df.sort_values(["date", "permno"]).reset_index(drop=True)


def load_bundle(source: str = "synthetic", validate_contracts: bool = True) -> DataBundle:
    v = (lambda name: name) if validate_contracts else (lambda name: None)
    return DataBundle(
        universe=read_table(paths.universe_path(source), v("universe")),
        signals=read_table(paths.signals_path(source), v("signals")),
        signal_meta=pd.read_csv(paths.signal_meta_path(source)),
        targets=read_table(paths.targets_path(source), v("targets")),
        states=read_table(paths.states_path(source), v("states")),
        cost_inputs=read_table(paths.cost_inputs_path(source), v("cost_inputs")),
        source=source,
    )


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=paths.REPO_ROOT,
                                       stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:  # pragma: no cover - repository may not exist in a sandbox
        return "unknown"


def new_run_id(prefix: str = "run") -> str:
    return f"{prefix}_{dt.datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"


_TRIAL_COLUMNS = ["run_id", "strategy", "cell", "params_json", "seed", "train_end", "val_metric", "git_sha", "timestamp"]


def log_trial(run_id: str, strategy: str, cell: str, params: dict, seed: int, train_end, val_metric: float) -> None:
    """Append one row to outputs/trials.csv (contract C13).

    Every fitted configuration must be logged, including grid points that lose, so that the deflated
    Sharpe ratio and the probability of backtest overfitting use an honest trial count.
    """
    row = {
        "run_id": run_id,
        "strategy": strategy,
        "cell": cell,
        "params_json": json.dumps(params, sort_keys=True, default=str),
        "seed": int(seed),
        "train_end": str(pd.Timestamp(train_end).date()),
        "val_metric": float(val_metric),
        "git_sha": git_sha(),
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
    }
    path = paths.trials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    header = not path.exists() or path.stat().st_size == 0
    with open(path, "a", encoding="utf-8", newline="") as fh:
        pd.DataFrame([row], columns=_TRIAL_COLUMNS).to_csv(fh, header=header, index=False)


def read_trials() -> pd.DataFrame:
    path = paths.trials_path()
    if not path.exists():
        return pd.DataFrame(columns=_TRIAL_COLUMNS)
    return pd.read_csv(path)


def freeze_tag() -> str | None:
    """Returns the specification-freeze tag if the team has frozen the design, else None."""
    return os.environ.get("ALPHACOMB_FREEZE_TAG")
