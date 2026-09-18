"""Frozen data contracts C1-C13 and a lightweight validator.

SHARED FILE - changing it is a Contract Change Request that needs all three members to agree,
and bumps ``VERSION``.

The validator deliberately avoids a heavy dependency (pandera): it checks the columns that the
contract promises, their dtypes, key uniqueness and value ranges. Extra columns are allowed
(additive changes are the preferred way to evolve a contract).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

VERSION = "1.0.0"


class SchemaError(ValueError):
    """Raised when a table does not satisfy its contract."""


@dataclass(frozen=True)
class Column:
    name: str
    kind: str  # "date" | "int" | "float" | "bool" | "str"
    required: bool = True
    minimum: float | None = None
    maximum: float | None = None
    nullable: bool = False


@dataclass(frozen=True)
class Schema:
    contract: str
    description: str
    columns: tuple[Column, ...]
    keys: tuple[str, ...] = ("date", "permno")
    prefixes: tuple[tuple[str, str], ...] = ()  # (prefix, kind) e.g. ("sig_", "float")
    min_prefix_matches: dict[str, int] = field(default_factory=dict)

    @property
    def required_columns(self) -> list[str]:
        return [c.name for c in self.columns if c.required]


_KIND_CHECK = {
    "date": lambda s: pd.api.types.is_datetime64_any_dtype(s),
    "int": lambda s: pd.api.types.is_integer_dtype(s),
    "float": lambda s: pd.api.types.is_float_dtype(s) or pd.api.types.is_integer_dtype(s),
    "bool": lambda s: pd.api.types.is_bool_dtype(s),
    "str": lambda s: pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s),
}

SCHEMAS: dict[str, Schema] = {
    "universe": Schema(
        contract="C1",
        description="Investable universe and descriptive fields, one row per stock-month.",
        columns=(
            Column("date", "date"),
            Column("permno", "int"),
            Column("in_universe", "bool"),
            Column("me", "float", minimum=0.0),
            Column("price", "float", minimum=0.0),
            Column("exchcd", "int"),
            Column("ff49", "int"),
            Column("nyse_size_pct", "float", minimum=0.0, maximum=100.0),
        ),
    ),
    "signals": Schema(
        contract="C2",
        description="Cross-sectionally rank-normalised signals in [-0.5, 0.5] plus theme missing flags.",
        columns=(Column("date", "date"), Column("permno", "int")),
        prefixes=(("sig_", "float"), ("miss_", "int")),
        min_prefix_matches={"sig_": 10},
    ),
    "signal_meta": Schema(
        contract="C3",
        description="One row per signal: theme, publication year and source.",
        columns=(
            Column("signal", "str"),
            Column("theme", "str"),
            Column("pub_year", "int"),
            Column("source", "str"),
        ),
        keys=("signal",),
    ),
    "targets": Schema(
        contract="C4",
        description="Forward excess returns at several horizons, delisting-adjusted.",
        columns=(
            Column("date", "date"),
            Column("permno", "int"),
            Column("r_1m", "float", nullable=True),
            Column("r_3m", "float", nullable=True),
            Column("r_6m", "float", nullable=True),
            Column("r_12m", "float", nullable=True),
            Column("ret_next", "float", nullable=True),
        ),
    ),
    "states": Schema(
        contract="C5",
        description="Observable market-state variables, lagged and standardised, one row per month.",
        columns=(
            Column("date", "date"),
            Column("MKTVOL", "float"),
            Column("BEAR", "float"),
            Column("ILLIQ", "float"),
            Column("SENT", "float"),
            Column("CREDIT", "float"),
            Column("TERM", "float"),
            Column("INFL", "float"),
            Column("DRATE", "float"),
            Column("DISP", "float"),
        ),
        keys=("date",),
        prefixes=(("FMOM_", "float"),),
    ),
    "cost_inputs": Schema(
        contract="C6",
        description="Inputs to the transaction-cost model, one row per stock-month.",
        columns=(
            Column("date", "date"),
            Column("permno", "int"),
            Column("spread", "float", minimum=0.0),
            Column("sigma_d", "float", minimum=0.0),
            Column("adv_usd", "float", minimum=0.0),
            Column("borrow_fee", "float", minimum=0.0),
        ),
    ),
    "predictions": Schema(
        contract="C9",
        description="Model scores and scaled alphas for one strategy and run.",
        columns=(
            Column("date", "date"),
            Column("permno", "int"),
            Column("score", "float"),
            Column("alpha", "float"),
            Column("unc_sd", "float", required=False, nullable=True),
        ),
    ),
    "weight_proposals": Schema(
        contract="C10",
        description="Unconstrained weight proposals from economic-objective learners.",
        columns=(Column("date", "date"), Column("permno", "int"), Column("w_prop", "float")),
    ),
    "weights": Schema(
        contract="C11",
        description="Implementable portfolio weights after optimisation or projection.",
        columns=(Column("date", "date"), Column("permno", "int"), Column("w", "float")),
    ),
    "returns": Schema(
        contract="C12",
        description="Backtest output: gross and net returns with the cost ledger.",
        columns=(
            Column("date", "date"),
            Column("gross_ret", "float"),
            Column("net_ret", "float"),
            Column("turnover", "float", minimum=0.0),
            Column("cost_spread", "float", minimum=0.0),
            Column("cost_impact", "float", minimum=0.0),
            Column("cost_borrow", "float", minimum=0.0),
            Column("long_ret", "float"),
            Column("short_ret", "float"),
        ),
        keys=("date",),
    ),
    "trials": Schema(
        contract="C13",
        description="Append-only log of every fitted configuration (feeds DSR and PBO).",
        columns=(
            Column("run_id", "str"),
            Column("strategy", "str"),
            Column("cell", "str"),
            Column("params_json", "str"),
            Column("seed", "int"),
            Column("train_end", "str"),
            Column("val_metric", "float"),
            Column("git_sha", "str"),
            Column("timestamp", "str"),
        ),
        keys=(),
    ),
}


def validate(df: pd.DataFrame, name: str, *, allow_empty: bool = False) -> pd.DataFrame:
    """Validate ``df`` against the named contract. Returns the frame so calls can be chained."""
    if name not in SCHEMAS:
        raise SchemaError(f"unknown contract '{name}'; known: {sorted(SCHEMAS)}")
    s = SCHEMAS[name]
    if df.empty and not allow_empty:
        raise SchemaError(f"{name} ({s.contract}): table is empty")

    missing = [c for c in s.required_columns if c not in df.columns]
    if missing:
        raise SchemaError(f"{name} ({s.contract}): missing required columns {missing}")

    for col in s.columns:
        if col.name not in df.columns:
            continue
        series = df[col.name]
        if not _KIND_CHECK[col.kind](series):
            raise SchemaError(f"{name} ({s.contract}): column '{col.name}' should be {col.kind}, got {series.dtype}")
        if not col.nullable and series.isna().any():
            raise SchemaError(f"{name} ({s.contract}): column '{col.name}' contains nulls but is not nullable")
        finite = series.dropna()
        if col.kind in {"float", "int"} and len(finite):
            if col.minimum is not None and float(np.nanmin(finite)) < col.minimum - 1e-9:
                raise SchemaError(f"{name} ({s.contract}): '{col.name}' below minimum {col.minimum}")
            if col.maximum is not None and float(np.nanmax(finite)) > col.maximum + 1e-9:
                raise SchemaError(f"{name} ({s.contract}): '{col.name}' above maximum {col.maximum}")

    for prefix, kind in s.prefixes:
        matches = [c for c in df.columns if c.startswith(prefix)]
        needed = s.min_prefix_matches.get(prefix, 0)
        if len(matches) < needed:
            raise SchemaError(f"{name} ({s.contract}): expected >= {needed} '{prefix}*' columns, found {len(matches)}")
        for c in matches:
            if not _KIND_CHECK[kind](df[c]):
                raise SchemaError(f"{name} ({s.contract}): column '{c}' should be {kind}, got {df[c].dtype}")

    if s.keys:
        if any(k not in df.columns for k in s.keys):
            raise SchemaError(f"{name} ({s.contract}): key columns {s.keys} missing")
        if df.duplicated(list(s.keys)).any():
            n = int(df.duplicated(list(s.keys)).sum())
            raise SchemaError(f"{name} ({s.contract}): {n} duplicated rows on keys {s.keys}")

    if name == "signals":
        sig_cols = [c for c in df.columns if c.startswith("sig_")]
        block = df[sig_cols].to_numpy(dtype="float64", na_value=np.nan)
        if np.nanmin(block) < -0.5 - 1e-6 or np.nanmax(block) > 0.5 + 1e-6:
            raise SchemaError("signals (C2): rank-normalised signals must lie in [-0.5, 0.5]")
    return df
