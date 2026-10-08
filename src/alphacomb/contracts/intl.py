"""Country-aware contract resolution for the promoted international panel (C1-C6, C14).

Workstream A's 7 October promotion froze the handoff at

    data/intl_c1/production/{DEU,IND,JPN}/universe.parquet
    data/intl_c2/production/{DEU,IND,JPN}/signals.parquet
    data/intl_c2/production/signal_meta.csv          (shared C3)
    data/intl_c4/production/{DEU,IND,JPN}/targets.parquet
    data/intl_c5/candidate_final_working/{DEU,IND,JPN}/states.parquet
    data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz   (all countries)
    data/intl_c14/production/c14_regime_candidate_source_frozen.csv

and **prohibits materialising the legacy flat ``data/real`` bundle**
(handoff document 13). Every existing workstream-B reader — ``contracts.paths``,
``contracts.io.load_bundle``, pipelines 02/04/06/07 — resolves a flat
``data/<source>/<artefact>.parquet`` with no country dimension, so this module is
the bridge. It reads the frozen layout in place and never writes a derived bundle.

Panel mode
----------
How the three countries combine is a research decision, not an implementation
detail, and it was still open when this module was written. All three options are
supported through ``PanelMode`` so the choice is a one-line config change rather
than a rewrite:

``separate``
    Fit, optimise and evaluate each country independently.
``pooled``
    One cross-section per month spanning all three countries.
``pooled_fit_separate_construct`` (default)
    One model trained on the pooled cross-section, then per-country portfolio
    construction and per-country tax ledgers.

The default is the third because **the tax side is already per-country and cannot
be pooled**: C14 tax year-ends differ (DEU and JPN December, India March), so an
after-tax ledger spanning the three has no well-defined tax year. Since portfolio
construction must therefore be per-country regardless, pooling only the model fit
is the option that buys training data without pretending the tax accounting is
unified. Record whichever mode is used in the pre-registration.

Identifier safety
-----------------
``permno`` is only unique *within* a country in this panel, so pooling on
``(date, permno)`` alone would silently merge unrelated securities. Pooled frames
therefore carry a ``country`` column and a ``gid`` composite key, and
:func:`assert_permno_disjoint` is available to check the assumption directly.

Evaluation window
-----------------
Document 13 requirement 7 limits the tax-dependent international evaluation to
2009-01-01 .. 2019-12-31, with a clean mechanism subwindow of
2014-01-01 .. 2018-03-31 and a cold-start ledger. :func:`evaluation_window` reads
those bounds from the frozen configuration rather than hard-coding them, and
:func:`gate_evaluation_frame` enforces them at the workstream-B input gate.
Pre-2009 rows stay available for training and feature construction.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pandas as pd

from . import paths

COUNTRIES: tuple[str, ...] = ("DEU", "IND", "JPN")

# Frozen locations from the 7 October promotion manifest.
C1_DIR = "intl_c1/production"
C2_DIR = "intl_c2/production"
C4_DIR = "intl_c4/production"
C5_DIR = "intl_c5/candidate_final_working"
C6_FILE = "intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz"
C14_FILE = "intl_c14/production/c14_regime_candidate_source_frozen.csv"
SAMPLE_CONFIG = "workstream_a_c14_evaluation_sample_2026-10-07.json"


class PanelMode(str, Enum):
    SEPARATE = "separate"
    POOLED = "pooled"
    POOLED_FIT_SEPARATE_CONSTRUCT = "pooled_fit_separate_construct"


class ContractLayoutError(FileNotFoundError):
    """A frozen contract artefact is missing from the promoted layout."""


class EvaluationWindowError(ValueError):
    """Data crosses the frozen tax-dependent evaluation boundary."""


# --------------------------------------------------------------------------- paths


def _require(path: Path, what: str) -> Path:
    if not path.exists():
        raise ContractLayoutError(
            f"{what} not found at {path}. The promoted international layout is expected "
            "in place; document 13 prohibits materialising a data/real bundle."
        )
    return path


def universe_path(country: str) -> Path:
    return _require(paths.data_root() / C1_DIR / country / "universe.parquet", f"C1 universe ({country})")


def signals_path(country: str) -> Path:
    return _require(paths.data_root() / C2_DIR / country / "signals.parquet", f"C2 signals ({country})")


def signal_meta_path() -> Path:
    return _require(paths.data_root() / C2_DIR / "signal_meta.csv", "C3 signal_meta")


def targets_path(country: str) -> Path:
    return _require(paths.data_root() / C4_DIR / country / "targets.parquet", f"C4 targets ({country})")


def states_path(country: str) -> Path:
    return _require(paths.data_root() / C5_DIR / country / "states.parquet", f"C5 states ({country})")


def cost_inputs_path() -> Path:
    return _require(paths.data_root() / C6_FILE, "C6 cost inputs")


def c14_schedule_path() -> Path:
    return _require(paths.data_root() / C14_FILE, "C14 regime schedule")


def available_countries() -> list[str]:
    """Countries whose full C1/C2/C4/C5 set is present."""
    out = []
    for c in COUNTRIES:
        try:
            universe_path(c), signals_path(c), targets_path(c), states_path(c)
        except ContractLayoutError:
            continue
        out.append(c)
    return out


# --------------------------------------------------------------- evaluation window


@dataclass(frozen=True)
class EvaluationWindow:
    start: pd.Timestamp
    end: pd.Timestamp
    mechanism_start: pd.Timestamp
    mechanism_end: pd.Timestamp
    ledger_inception: pd.Timestamp
    tax_year_end_months: dict[str, int]

    def contains(self, dates: pd.Series) -> pd.Series:
        d = pd.to_datetime(dates)
        return (d >= self.start) & (d <= self.end)

    def mechanism_contains(self, dates: pd.Series) -> pd.Series:
        d = pd.to_datetime(dates)
        return (d >= self.mechanism_start) & (d <= self.mechanism_end)


def evaluation_window(config_path: Path | None = None) -> EvaluationWindow:
    """Read the frozen tax-dependent evaluation sample (document 13 requirement 7)."""
    path = config_path or (paths.REPO_ROOT / "configs" / SAMPLE_CONFIG)
    cfg = json.loads(_require(path, "frozen C14 evaluation sample config").read_text(encoding="utf-8"))
    primary = cfg["primary_after_tax_evaluation_window"]
    mech = cfg["clean_mechanism_subwindow"]
    return EvaluationWindow(
        start=pd.Timestamp(primary["start"]),
        end=pd.Timestamp(primary["end"]),
        mechanism_start=pd.Timestamp(mech["start"]),
        mechanism_end=pd.Timestamp(mech["end"]),
        ledger_inception=pd.Timestamp(cfg["tax_ledger_inception"]),
        tax_year_end_months=dict(cfg["tax_year_end_months"]),
    )


def gate_evaluation_frame(df: pd.DataFrame, *, mechanism_only: bool = False,
                          window: EvaluationWindow | None = None) -> pd.DataFrame:
    """Restrict a frame to the frozen tax-dependent evaluation domain.

    This is the workstream-B input gate. It is for *tax-dependent evaluation only* —
    training and feature construction may still use the full history, which is why
    this is an explicit call rather than something :func:`load_panel` does implicitly.
    """
    w = window or evaluation_window()
    if "date" not in df.columns:
        raise EvaluationWindowError("frame has no 'date' column to gate on")
    mask = w.mechanism_contains(df["date"]) if mechanism_only else w.contains(df["date"])
    return df.loc[mask].reset_index(drop=True)


# ------------------------------------------------------------------------- loading


def assert_permno_disjoint(frames: dict[str, pd.DataFrame]) -> None:
    """Fail loudly if two countries share a permno.

    Pooling on ``(date, permno)`` across countries that reuse identifiers would merge
    unrelated securities without raising anything, so this is checked rather than assumed.
    """
    seen: dict[int, str] = {}
    for country, df in frames.items():
        for pid in df["permno"].unique().tolist():
            prior = seen.get(pid)
            if prior is not None and prior != country:
                raise ValueError(
                    f"permno {pid} appears in both {prior} and {country}; the pooled panel "
                    "must key on (country, permno) — use the 'gid' column, not 'permno'."
                )
            seen[pid] = country


def load_cost_inputs(countries: list[str] | None = None) -> pd.DataFrame:
    """Load C6 for the whole panel. Market fields are never imputed (document 13 req. 2)."""
    df = pd.read_csv(cost_inputs_path(), parse_dates=["date"])
    if countries is not None and "country" in df.columns:
        df = df.loc[df["country"].isin(countries)]
    return df.reset_index(drop=True)


def load_country(country: str, *, with_costs: bool = True) -> dict[str, pd.DataFrame]:
    """Every contract artefact for one country, read in place from the frozen layout."""
    out = {
        "universe": pd.read_parquet(universe_path(country)),
        "signals": pd.read_parquet(signals_path(country)),
        "signal_meta": pd.read_csv(signal_meta_path()),
        "targets": pd.read_parquet(targets_path(country)),
        "states": pd.read_parquet(states_path(country)),
    }
    if with_costs:
        costs = load_cost_inputs([country])
        if "country" not in costs.columns:
            # C6 is a single combined file; restrict to this country's securities.
            costs = costs.loc[costs["permno"].isin(out["universe"]["permno"].unique())]
        out["cost_inputs"] = costs.reset_index(drop=True)
    return out


def load_panel(mode: PanelMode | str = PanelMode.POOLED_FIT_SEPARATE_CONSTRUCT,
               countries: list[str] | None = None,
               *, check_identifiers: bool = True) -> dict:
    """Load the international panel under the chosen combination mode.

    Returns ``{"mode", "countries", "by_country", "pooled"}``. ``pooled`` is ``None``
    in ``separate`` mode. Pooled frames carry ``country`` and a ``gid`` composite key;
    the per-country frames are always returned so that portfolio construction and the
    tax ledger can stay per-country, which they must.
    """
    mode = PanelMode(mode)
    countries = countries or available_countries()
    if not countries:
        raise ContractLayoutError("no country has a complete C1/C2/C4/C5 set under data/intl_c*")

    by_country = {c: load_country(c) for c in countries}

    if check_identifiers:
        assert_permno_disjoint({c: v["universe"] for c, v in by_country.items()})

    pooled = None
    if mode in (PanelMode.POOLED, PanelMode.POOLED_FIT_SEPARATE_CONSTRUCT):
        pooled = {}
        for key in ("universe", "signals", "targets", "states", "cost_inputs"):
            parts = []
            for c, tables in by_country.items():
                if key not in tables:
                    continue
                part = tables[key].copy()
                part["country"] = c
                if "permno" in part.columns:
                    part["gid"] = part["country"] + ":" + part["permno"].astype(str)
                parts.append(part)
            if parts:
                pooled[key] = pd.concat(parts, ignore_index=True)
        pooled["signal_meta"] = next(iter(by_country.values()))["signal_meta"]

    return {"mode": mode, "countries": countries, "by_country": by_country, "pooled": pooled}
