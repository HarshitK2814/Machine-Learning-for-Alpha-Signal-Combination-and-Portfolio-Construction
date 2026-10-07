"""Executable reference semantics for the C14 -> C12 dated-tax design.

This module is deliberately outside ``alphacomb.tax``.  It pins the mechanics
that are already determined by primary sources while the remaining statutory
and research-design choices stay fail-closed.  It is not a second backtest
engine and it is not imported by production code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class DatedRule:
    country: str
    effective_from: pd.Timestamp
    effective_to: pd.Timestamp
    legal_regime: str
    stt_buy: float | None
    stt_sell: float | None
    cgt_short: float | None
    cgt_long: float | None
    holding_period_months: int | None
    dividend_rate: float | None
    loss_carryforward_years: float | None
    losses_ring_fenced: bool | None
    ordinary_income_offset: float | None
    transition_rule: str | None = None
    basis_rule: str | None = None


def _nullable_float(value: Any) -> float | None:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    return float(value)


def _nullable_int(value: Any) -> int | None:
    parsed = _nullable_float(value)
    return None if parsed is None else int(parsed)


def _nullable_bool(value: Any) -> bool | None:
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    token = str(value).strip().lower()
    if token not in {"true", "false"}:
        raise ValueError(f"invalid nullable boolean: {value!r}")
    return token == "true"


class DatedRegimeSchedule:
    """Resolve a C14 rule by legal event date and, where required, lot date."""

    def __init__(self, rows: pd.DataFrame):
        self.rows = rows.sort_values(["country", "effective_from"]).reset_index(drop=True)

    @classmethod
    def from_csv(cls, path: str | Path) -> "DatedRegimeSchedule":
        rows = pd.read_csv(path, dtype=str, keep_default_na=False)
        rows["effective_from"] = pd.to_datetime(rows["effective_from"], errors="raise")
        rows["effective_to"] = pd.to_datetime(rows["effective_to"], errors="raise")
        return cls(rows)

    def validate(self, start: str | pd.Timestamp, end: str | pd.Timestamp) -> dict[str, int]:
        start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
        gaps = overlaps = 0
        countries = sorted(self.rows["country"].unique())
        for country in countries:
            rows = self.rows.loc[self.rows["country"].eq(country)]
            prior_end: pd.Timestamp | None = None
            for row in rows.itertuples(index=False):
                row_start = max(row.effective_from, start_ts)
                row_end = min(row.effective_to, end_ts)
                if row_end < start_ts or row_start > end_ts:
                    continue
                if prior_end is None:
                    gaps += int(row_start != start_ts)
                else:
                    gaps += int(row_start > prior_end + pd.Timedelta(days=1))
                    overlaps += int(row_start <= prior_end)
                prior_end = max(prior_end, row_end) if prior_end is not None else row_end
            gaps += int(prior_end != end_ts)
        return {"countries": len(countries), "gaps": gaps, "overlaps": overlaps}

    def resolve(
        self,
        country: str,
        event_date: str | pd.Timestamp,
        acquisition_date: str | pd.Timestamp | None = None,
    ) -> DatedRule:
        event = pd.Timestamp(event_date)
        acquired = pd.Timestamp(acquisition_date) if acquisition_date is not None else None
        source_date = event
        transition_rule = None
        basis_rule = None

        # Ordinary direct securities acquired before the Abgeltungsteuer start
        # retain the acquisition-era treatment.  The lot date must therefore
        # survive even when the sale occurs in a later regime.
        if country == "DEU" and event >= pd.Timestamp("2009-01-01"):
            if acquired is not None and acquired < pd.Timestamp("2009-01-01"):
                source_date = acquired
                transition_rule = "DEU_PRE_2009_ACQUISITION_GRANDFATHERED"

        # Section 55(2)(ac) applies a special basis to qualifying Section 112A
        # assets acquired before 1 February 2018.  The event rate remains the
        # sale-date rate; only the lot's basis rule changes.
        if country == "IND" and event >= pd.Timestamp("2018-04-01"):
            if acquired is not None and acquired < pd.Timestamp("2018-02-01"):
                basis_rule = "IND_SECTION_55_2_AC"

        match = self.rows.loc[
            self.rows["country"].eq(country)
            & self.rows["effective_from"].le(source_date)
            & self.rows["effective_to"].ge(source_date)
        ]
        if len(match) != 1:
            raise LookupError(
                f"expected one C14 row for {country=} {source_date=:%Y-%m-%d}; found {len(match)}"
            )
        row = match.iloc[0]
        return DatedRule(
            country=country,
            effective_from=row["effective_from"],
            effective_to=row["effective_to"],
            legal_regime=row["legal_regime"],
            stt_buy=_nullable_float(row["stt_buy"]),
            stt_sell=_nullable_float(row["stt_sell"]),
            cgt_short=_nullable_float(row["cgt_short"]),
            cgt_long=_nullable_float(row["cgt_long"]),
            holding_period_months=_nullable_int(row["holding_period_months"]),
            dividend_rate=_nullable_float(row["dividend_rate"]),
            loss_carryforward_years=_nullable_float(row["loss_carryforward_years"]),
            losses_ring_fenced=_nullable_bool(row["losses_ring_fenced"]),
            ordinary_income_offset=_nullable_float(row["ordinary_income_offset"]),
            transition_rule=transition_rule,
            basis_rule=basis_rule,
        )


def is_long_term(
    acquisition_date: str | pd.Timestamp,
    disposal_date: str | pd.Timestamp,
    *,
    months: int,
) -> bool:
    """Return true only after, not on, the holding-period anniversary."""

    anniversary = pd.Timestamp(acquisition_date) + pd.DateOffset(months=months)
    return pd.Timestamp(disposal_date) > anniversary


def india_section_112a_deemed_cost(
    *,
    actual_cost: float,
    fmv_2018_01_31: float,
    sale_value: float,
) -> float:
    """Mechanical Section 55(2)(ac) basis for a qualifying pre-Feb-2018 asset."""

    if min(actual_cost, fmv_2018_01_31, sale_value) < 0:
        raise ValueError("cost, fair market value, and sale value must be non-negative")
    return max(float(actual_cost), min(float(fmv_2018_01_31), float(sale_value)))


@dataclass
class _LossVintage:
    origin_year: int
    amount: float
    bucket: str


class LossCarryforwardLedger:
    """Reference loss-vintage semantics, including the final allowed year."""

    def __init__(self, *, carryforward_years: int | float, ring_fenced: bool):
        self.carryforward_years = carryforward_years
        self.ring_fenced = ring_fenced
        self._vintages: list[_LossVintage] = []

    def add_loss(self, *, origin_year: int, amount: float, bucket: str) -> None:
        if amount < 0:
            raise ValueError("loss amount must be a positive magnitude")
        self._vintages.append(_LossVintage(origin_year, float(amount), bucket))

    def offset(self, *, year: int, gain: float, bucket: str) -> tuple[float, float]:
        if gain < 0:
            raise ValueError("gain must be non-negative")
        if self.carryforward_years != float("inf"):
            self._vintages = [
                vintage
                for vintage in self._vintages
                if year - vintage.origin_year <= self.carryforward_years
            ]
        remaining = float(gain)
        used = 0.0
        for vintage in sorted(self._vintages, key=lambda item: item.origin_year):
            if self.ring_fenced and vintage.bucket != bucket:
                continue
            take = min(vintage.amount, remaining)
            vintage.amount -= take
            remaining -= take
            used += take
            if remaining <= 1e-12:
                break
        self._vintages = [v for v in self._vintages if v.amount > 1e-12]
        return remaining, used


def static_engine_compatibility_gate(repo_root: str | Path) -> dict[str, object]:
    """Verify that the production C12 path exposes every dated-C14 capability."""

    root = Path(repo_root)
    regimes = (root / "src" / "alphacomb" / "tax" / "regimes.py").read_text(encoding="utf-8")
    lots = (root / "src" / "alphacomb" / "tax" / "lots.py").read_text(encoding="utf-8")
    backtest = (root / "src" / "alphacomb" / "tax" / "backtest.py").read_text(encoding="utf-8")
    dated = (root / "src" / "alphacomb" / "tax" / "dated.py").read_text(encoding="utf-8")
    combined_runtime = lots + "\n" + backtest + "\n" + dated

    blockers: list[str] = []
    if "DatedRegimeSchedule" not in combined_runtime:
        blockers.append("dated_event_resolution")
    if (
        "DEU_PRE_2009_ACQUISITION_GRANDFATHERED" not in combined_runtime
        or "IND_SECTION_55_2_AC" not in combined_runtime
    ):
        blockers.append("acquisition_date_transition_rules")
    if "stt_buy" not in combined_runtime or "stt_sell" not in combined_runtime:
        blockers.append("transaction_tax_by_side")
    if combined_runtime.count("losses_ring_fenced") == 0:
        blockers.append("bucketed_loss_ring_fencing")
    if "self._year - v[0] < life" in backtest:
        blockers.append("correct_carryforward_expiry_boundary")
    if "self._vintages = [[self._year, fresh]]" in backtest:
        blockers.append("preserve_loss_vintage_origins")

    return {
        "verdict": "PASS" if not blockers else "BLOCKED_STATIC_REGIME_ENGINE",
        "blocking_capabilities": blockers,
        "evidence": {
            "production_dated_engine_packaged": "class DatedC12Patch" in dated,
            "production_backtest_accepts_dated_engine": "dated_engine: DatedC12Patch" in backtest,
            "tax_config_static_annotation": "regime: TaxRegime" in backtest,
            "ledger_stores_single_regime": "regime: TaxRegime" in lots,
            "ring_fence_declared_in_schema": "losses_ring_fenced" in regimes,
            "ring_fence_used_at_runtime": "losses_ring_fenced" in combined_runtime,
            "expiry_uses_strict_less_than": "self._year - v[0] < life" in backtest,
            "loss_balances_are_re_vintaged": "self._vintages = [[self._year, fresh]]" in backtest,
        },
    }
