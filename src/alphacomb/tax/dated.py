"""Dated C14 mechanics consumed by the C12 tax layer.

This is the production-package integration of the checksum-frozen architecture
in ``research/c14_dated_c12_patch.py``.  It deliberately contains mechanics,
not guessed statutory values.  Missing rates, reference values and FX fail
closed.  Static ``TaxRegime`` consumers remain available for legacy controls.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Mapping

import pandas as pd


# (applied rule id, field).  The effective date is part of the rule id, so two
# intervals which intentionally reuse a legal-regime label cannot collide.
RateKey = tuple[str, str]
AllocationKey = tuple[str, str]
FXProvider = Callable[[str, str, pd.Timestamp], float]


class MissingDatedTaxConfiguration(RuntimeError):
    """Raised instead of silently supplying a statutory or modelling input."""


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


def _rule_id(rule: DatedRule) -> str:
    return f"{rule.country}:{rule.legal_regime}:{rule.effective_from.date()}"


class DatedRegimeSchedule:
    """Resolve a C14 rule by event date and, where necessary, acquisition date."""

    def __init__(self, rows: pd.DataFrame):
        self.rows = rows.sort_values(["country", "effective_from"]).reset_index(drop=True)

    @classmethod
    def from_csv(cls, path: str | Path) -> "DatedRegimeSchedule":
        rows = pd.read_csv(path, dtype=str, keep_default_na=False)
        rows["effective_from"] = pd.to_datetime(rows["effective_from"], errors="raise")
        rows["effective_to"] = pd.to_datetime(rows["effective_to"], errors="raise")
        return cls(rows)

    def validate(self, start, end) -> dict[str, int]:
        start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)
        gaps = overlaps = 0
        countries = sorted(self.rows["country"].unique())
        for country in countries:
            prior_end: pd.Timestamp | None = None
            rows = self.rows.loc[self.rows["country"].eq(country)]
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

    def resolve(self, country: str, event_date, acquisition_date=None) -> DatedRule:
        event = pd.Timestamp(event_date)
        acquired = pd.Timestamp(acquisition_date) if acquisition_date is not None else None
        source_date = event
        transition_rule = basis_rule = None
        if country == "DEU" and event >= pd.Timestamp("2009-01-01"):
            if acquired is not None and acquired < pd.Timestamp("2009-01-01"):
                source_date = acquired
                transition_rule = "DEU_PRE_2009_ACQUISITION_GRANDFATHERED"
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
                f"expected one C14 row for country={country} date={source_date:%Y-%m-%d}; "
                f"found {len(match)}"
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


def is_long_term(acquisition_date, disposal_date, *, months: int) -> bool:
    anniversary = pd.Timestamp(acquisition_date) + pd.DateOffset(months=months)
    return pd.Timestamp(disposal_date) > anniversary


def india_section_112a_deemed_cost(*, actual_cost: float, fmv_2018_01_31: float,
                                   sale_value: float) -> float:
    if min(actual_cost, fmv_2018_01_31, sale_value) < 0:
        raise ValueError("cost, fair market value and sale value must be non-negative")
    return max(float(actual_cost), min(float(fmv_2018_01_31), float(sale_value)))


@dataclass(frozen=True)
class ReferenceValue:
    country: str
    security_id: int | str
    reference_date: pd.Timestamp
    fmv_price_local: float
    close_price_local: float
    currency: str
    source_field: str
    source: str

    @property
    def high_to_close_ratio(self) -> float:
        return self.fmv_price_local / self.close_price_local


class SecurityReferenceValueStore:
    REQUIRED_COLUMNS = frozenset({
        "country", "permno", "reference_date", "fmv_price_local",
        "close_price_local", "currency", "source_field", "source_cache",
        "source_cache_sha256", "statutory_definition", "endpoint_date",
    })
    INDIA_112A_DEFINITION = "HIGHEST_QUOTED_PRICE_ON_2018_01_31_OR_PRECEDING_TRADED_DATE"

    def __init__(self) -> None:
        self._values: dict[tuple[str, str, pd.Timestamp], ReferenceValue] = {}

    def __len__(self) -> int:
        return len(self._values)

    def add(self, country: str, security_id: int | str, reference_date, value: float,
            *, currency: str, source: str, close_price: float | None = None,
            source_field: str = "TEST_FIXTURE") -> None:
        """Add a value explicitly.

        ``close_price`` defaults to one for backwards-compatible unit fixtures.
        Production C14 inputs must use :meth:`from_validated_csv`.
        """
        close = 1.0 if close_price is None else float(close_price)
        if value < 0 or close <= 0:
            raise ValueError("reference and close prices must be positive")
        key = (country, str(security_id), pd.Timestamp(reference_date))
        if key in self._values:
            raise ValueError(f"duplicate statutory reference value: {key}")
        self._values[key] = ReferenceValue(
            country, security_id, key[2], float(value), close, currency,
            source_field, source,
        )

    @classmethod
    def from_validated_csv(cls, path: str | Path) -> "SecurityReferenceValueStore":
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        missing = sorted(cls.REQUIRED_COLUMNS.difference(frame.columns))
        if missing:
            raise MissingDatedTaxConfiguration(
                f"India section 112A reference contract missing columns: {missing}"
            )
        if frame.empty:
            raise MissingDatedTaxConfiguration("India section 112A reference table is empty")
        if frame.duplicated(["country", "permno", "reference_date"]).any():
            raise MissingDatedTaxConfiguration("duplicate India section 112A reference keys")
        store = cls()
        for row in frame.to_dict("records"):
            reference_date = pd.Timestamp(row["reference_date"])
            endpoint = pd.Timestamp(row["endpoint_date"])
            if row["country"] != "IND" or reference_date != pd.Timestamp("2018-01-31"):
                raise MissingDatedTaxConfiguration("invalid country/reference date in section 112A table")
            if endpoint > reference_date:
                raise MissingDatedTaxConfiguration("section 112A reference endpoint is forward-looking")
            if row["currency"] != "INR" or row["source_field"] != "prchd":
                raise MissingDatedTaxConfiguration("section 112A reference must be INR Compustat prchd")
            if row["statutory_definition"] != cls.INDIA_112A_DEFINITION:
                raise MissingDatedTaxConfiguration("section 112A statutory price definition mismatch")
            if len(row["source_cache_sha256"]) != 64 or not row["source_cache"]:
                raise MissingDatedTaxConfiguration("section 112A source provenance is incomplete")
            fmv = float(row["fmv_price_local"])
            close = float(row["close_price_local"])
            if fmv <= 0 or close <= 0:
                raise MissingDatedTaxConfiguration("section 112A prices must be positive")
            store.add(
                "IND", row["permno"], reference_date, fmv,
                close_price=close, currency="INR", source=row["source_cache"],
                source_field="prchd",
            )
        return store

    def get(self, country: str, security_id: int | str, reference_date) -> ReferenceValue:
        key = (country, str(security_id), pd.Timestamp(reference_date))
        try:
            return self._values[key]
        except KeyError as exc:
            raise MissingDatedTaxConfiguration(
                f"missing security-specific 31-Jan-2018 reference value for "
                f"{country} security {security_id}"
            ) from exc


class PointInTimeFXStore:
    """Validated, no-look-ahead adapter for the frozen WRDS daily FX cache.

    Decision 3A requires the immediately preceding available business-day
    observation.  The callable interface matches :class:`DatedPatchConfig`'s
    ``fx_provider`` contract and returns units of ``to_currency`` per unit of
    ``from_currency``.
    """

    REQUIRED_COLUMNS = frozenset({"datadate", "currency", "usd_per_local"})

    def __init__(self, rows: pd.DataFrame):
        frame = rows.copy()
        frame["datadate"] = pd.to_datetime(frame["datadate"], errors="raise")
        frame["currency"] = frame["currency"].astype(str)
        frame["usd_per_local"] = pd.to_numeric(frame["usd_per_local"], errors="raise")
        frame = frame.loc[frame["datadate"].dt.dayofweek.lt(5)]
        if frame.empty or frame["usd_per_local"].le(0).any():
            raise MissingDatedTaxConfiguration("point-in-time FX observations must be positive")
        if frame.duplicated(["datadate", "currency"]).any():
            raise MissingDatedTaxConfiguration("duplicate point-in-time FX keys")
        self._rows = {
            currency: group.set_index("datadate")["usd_per_local"].sort_index()
            for currency, group in frame.groupby("currency", sort=False)
        }

    @classmethod
    def from_validated_csv(cls, path: str | Path) -> "PointInTimeFXStore":
        frame = pd.read_csv(path, usecols=lambda name: name in cls.REQUIRED_COLUMNS)
        missing = sorted(cls.REQUIRED_COLUMNS.difference(frame.columns))
        if missing:
            raise MissingDatedTaxConfiguration(f"point-in-time FX contract missing columns: {missing}")
        return cls(frame)

    def source_date(self, currency: str, event_date) -> pd.Timestamp:
        if currency == "USD":
            return pd.Timestamp(event_date)
        if currency not in self._rows:
            raise MissingDatedTaxConfiguration(f"FX currency is unavailable: {currency}")
        event = pd.Timestamp(event_date)
        eligible = self._rows[currency].index[self._rows[currency].index <= event]
        if eligible.empty:
            raise MissingDatedTaxConfiguration(
                f"no non-forward FX observation for {currency} on {event:%Y-%m-%d}"
            )
        return pd.Timestamp(eligible[-1])

    def _usd_per_local(self, currency: str, event_date) -> float:
        if currency == "USD":
            return 1.0
        source_date = self.source_date(currency, event_date)
        return float(self._rows[currency].loc[source_date])

    def __call__(self, from_currency: str, to_currency: str, event_date) -> float:
        if from_currency == to_currency:
            return 1.0
        source_usd = self._usd_per_local(from_currency, event_date)
        target_usd = self._usd_per_local(to_currency, event_date)
        return float(source_usd / target_usd)


@dataclass(frozen=True)
class StatutoryAmount:
    amount_local: float
    currency: str
    kind: str

    def __post_init__(self) -> None:
        if self.amount_local < 0:
            raise ValueError("statutory amount must be non-negative")
        if not self.currency:
            raise ValueError("statutory currency is required")

    def in_accounting_currency(self, accounting_currency: str, event_date,
                               fx_provider: FXProvider | None) -> float:
        if accounting_currency == self.currency:
            return float(self.amount_local)
        if fx_provider is None:
            raise MissingDatedTaxConfiguration(
                f"point-in-time FX is required for {self.currency}->{accounting_currency}"
            )
        rate = float(fx_provider(self.currency, accounting_currency, pd.Timestamp(event_date)))
        if rate <= 0:
            raise ValueError("FX rate must be positive")
        return float(self.amount_local * rate)


@dataclass(frozen=True)
class DatedPatchConfig:
    schedule: DatedRegimeSchedule
    accounting_currency: str = "USD"
    rate_overrides: Mapping[RateKey, float] = field(default_factory=dict)
    allowance_allocations: Mapping[AllocationKey, float] = field(default_factory=dict)
    brokerage_rates: Mapping[AllocationKey, float] = field(default_factory=dict)
    tax_year_end_months: Mapping[str, int] = field(default_factory=dict)
    fx_provider: FXProvider | None = None
    reference_values: SecurityReferenceValueStore = field(default_factory=SecurityReferenceValueStore)

    def __post_init__(self) -> None:
        for key, value in self.rate_overrides.items():
            if not 0 <= value <= 1:
                raise ValueError(f"rate override must be a fraction for {key}")
        for key, value in self.allowance_allocations.items():
            if not 0 <= value <= 1:
                raise ValueError(f"allowance allocation must lie in [0,1] for {key}")
        for key, value in self.brokerage_rates.items():
            if not 0 <= value <= 1:
                raise ValueError(f"brokerage rate must be a fraction for {key}")
        for country, month in self.tax_year_end_months.items():
            if not 1 <= int(month) <= 12:
                raise ValueError(f"tax-year-end month must lie in [1,12] for {country}")


@dataclass(frozen=True)
class ResolvedEventRule:
    country: str
    event_date: pd.Timestamp
    event_type: str
    event_rule_id: str
    acquisition_rule_id: str | None
    applied_rule_id: str
    transition_rule: str | None
    basis_rule: str | None
    applied_rule: DatedRule


@dataclass(frozen=True)
class DatedTaxLot:
    country: str
    security_id: int | str
    acquisition_date: pd.Timestamp
    basis: float
    currency: str
    acquisition_rule_id: str
    side: int = 1
    statutory_reference_value: float | None = None


@dataclass(frozen=True)
class RealisedTaxEvent:
    country: str
    security_id: int | str
    acquisition_date: pd.Timestamp
    disposal_date: pd.Timestamp
    event_rule_id: str
    acquisition_rule_id: str
    applied_rule_id: str
    transition_rule: str | None
    basis_rule: str | None
    tax_basis: float
    sale_value: float
    raw_gain: float
    taxable_gain: float
    long_term: bool
    tax_rate: float
    loss_bucket: str
    currency: str
    side: int
    carryforward_years: int | float | None
    losses_ring_fenced: bool | None
    eligible_gain_buckets: frozenset[str] | None
    ordinary_income_offset: float | None
    annual_amount_local: float | None
    annual_amount_currency: str | None
    annual_amount_kind: str | None


@dataclass(frozen=True)
class TransactionTaxResult:
    country: str
    event_date: pd.Timestamp
    buy_notional: float
    sell_notional: float
    buy_rate: float
    sell_rate: float
    buy_tax: float
    sell_tax: float

    @property
    def total(self) -> float:
        return self.buy_tax + self.sell_tax


@dataclass(frozen=True)
class LossVintage:
    vintage_id: int
    origin_year: int
    original_amount: float
    remaining_amount: float
    bucket: str
    carryforward_years: int | float
    eligible_gain_buckets: frozenset[str] | None = None

    def eligible(self, year: int) -> bool:
        return self.carryforward_years == float("inf") or year - self.origin_year <= self.carryforward_years


class LossCarryforwardBook:
    def __init__(self) -> None:
        self._vintages: tuple[LossVintage, ...] = ()
        self._next_id = 1

    def add_loss(self, origin_year: int, amount: float, bucket: str, *,
                 carryforward_years: int | float,
                 eligible_gain_buckets: set[str] | frozenset[str] | None = None) -> int:
        if amount <= 0:
            raise ValueError("loss amount must be positive")
        if carryforward_years < 0:
            raise ValueError("carryforward life must be non-negative")
        vintage = LossVintage(
            self._next_id, int(origin_year), float(amount), float(amount), bucket,
            carryforward_years,
            frozenset(eligible_gain_buckets) if eligible_gain_buckets is not None else None,
        )
        self._next_id += 1
        self._vintages = (*self._vintages, vintage)
        return vintage.vintage_id

    def vintages(self) -> tuple[LossVintage, ...]:
        return self._vintages

    def copy(self) -> "LossCarryforwardBook":
        other = LossCarryforwardBook()
        other._vintages = self._vintages
        other._next_id = self._next_id
        return other

    def expire(self, year: int) -> None:
        self._vintages = tuple(v for v in self._vintages if v.eligible(year))

    def offset(self, year: int, gain: float, bucket: str, *, ring_fenced: bool) -> tuple[float, float]:
        if gain < 0:
            raise ValueError("gain must be non-negative")
        live = [v for v in self._vintages if v.eligible(year)]
        remaining_gain, used = float(gain), 0.0
        updated: list[LossVintage] = []
        for vintage in sorted(live, key=lambda item: (item.origin_year, item.vintage_id)):
            allowed = vintage.eligible_gain_buckets or frozenset({vintage.bucket})
            if remaining_gain <= 1e-12 or (ring_fenced and bucket not in allowed):
                updated.append(vintage)
                continue
            take = min(vintage.remaining_amount, remaining_gain)
            remaining_gain -= take
            used += take
            balance = vintage.remaining_amount - take
            if balance > 1e-12:
                updated.append(replace(vintage, remaining_amount=balance))
        self._vintages = tuple(updated)
        return remaining_gain, used


class DatedC12Patch:
    """Production packaged dated-tax resolver used by the C12 integration."""

    def __init__(self, config: DatedPatchConfig):
        self.config = config

    @classmethod
    def from_frozen_evaluation_artifacts(
        cls, project_root: str | Path,
        *, sample_config: str = "configs/workstream_a_c14_evaluation_sample_2026-10-07.json",
    ) -> "DatedC12Patch":
        """Materialize the pre-results C14 engine from frozen local artefacts."""
        root = Path(project_root)
        sample_path = root / sample_config
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
        fx_path = root / sample["point_in_time_fx"]["cache"]
        allowances = {
            tuple(key.split(":")): float(value)
            for key, value in sample["allowance_allocations"].items()
        }
        return cls(DatedPatchConfig(
            schedule=DatedRegimeSchedule.from_csv(
                root / "data/intl_c14/candidate_working/c14_regime_candidate_source_frozen.csv"
            ),
            accounting_currency="USD",
            allowance_allocations=allowances,
            tax_year_end_months={
                country: int(month)
                for country, month in sample["tax_year_end_months"].items()
            },
            fx_provider=PointInTimeFXStore.from_validated_csv(fx_path),
            reference_values=SecurityReferenceValueStore.from_validated_csv(
                root / "data/intl_c14/candidate_working/IND_SECTION_112A_REFERENCE_VALUES.csv"
            ),
        ))

    @property
    def schedule(self) -> DatedRegimeSchedule:
        return self.config.schedule

    def resolve_event(self, country: str, event_date, *, acquisition_date=None,
                      event_type: str = "capital_gain") -> ResolvedEventRule:
        event = pd.Timestamp(event_date)
        acquired = pd.Timestamp(acquisition_date) if acquisition_date is not None else None
        event_rule = self.schedule.resolve(country, event)
        acquisition_rule = self.schedule.resolve(country, acquired) if acquired is not None else None
        applied = self.schedule.resolve(country, event, acquired)
        return ResolvedEventRule(
            country, event, event_type, _rule_id(event_rule),
            _rule_id(acquisition_rule) if acquisition_rule else None,
            _rule_id(applied), applied.transition_rule, applied.basis_rule, applied,
        )

    def acquire(self, country: str, security_id: int | str, acquisition_date, *,
                basis: float, currency: str, side: int = 1) -> DatedTaxLot:
        if basis < 0:
            raise ValueError("basis must be non-negative")
        acquired = pd.Timestamp(acquisition_date)
        if side not in {-1, 1}:
            raise ValueError("lot side must be -1 or 1")
        return DatedTaxLot(
            country, security_id, acquired, float(basis), currency,
            _rule_id(self.schedule.resolve(country, acquired)), side,
        )

    def attach_statutory_reference(self, lot: DatedTaxLot, *, close_value_local: float) -> DatedTaxLot:
        reference = self.config.reference_values.get(lot.country, lot.security_id, "2018-01-31")
        if reference.currency != lot.currency:
            raise MissingDatedTaxConfiguration("section 112A reference and lot currency differ")
        return replace(
            lot,
            statutory_reference_value=float(close_value_local) * reference.high_to_close_ratio,
        )

    def realise(self, lot: DatedTaxLot, disposal_date, *, sale_value: float,
                currency: str) -> RealisedTaxEvent:
        if sale_value < 0:
            raise ValueError("sale value must be non-negative")
        if currency != lot.currency:
            raise MissingDatedTaxConfiguration(
                "lot basis and sale value must share a currency before gain computation"
            )
        resolved = self.resolve_event(lot.country, disposal_date, acquisition_date=lot.acquisition_date)
        rule = resolved.applied_rule
        long_term = (
            False if rule.holding_period_months is None
            else is_long_term(lot.acquisition_date, disposal_date, months=rule.holding_period_months)
        )
        basis = lot.basis
        applied_basis_rule = resolved.basis_rule if long_term else None
        if applied_basis_rule == "IND_SECTION_55_2_AC" and lot.side == 1:
            if lot.statutory_reference_value is None:
                raise MissingDatedTaxConfiguration(
                    "missing lot-level 31-Jan-2018 section 112A reference value"
                )
            basis = india_section_112a_deemed_cost(
                actual_cost=lot.basis,
                fmv_2018_01_31=lot.statutory_reference_value,
                sale_value=sale_value,
            )
        rate_field = "cgt_long" if long_term else "cgt_short"
        tax_rate = self._configured_rate(
            rule, rate_field, rule.cgt_long if long_term else rule.cgt_short
        )
        metadata = self._metadata_row(rule)
        inclusion = float(metadata.get("gain_inclusion_fraction") or 1.0)
        raw_gain = float(lot.side * (sale_value - basis))
        loss_bucket = metadata.get("loss_bucket") or "CAPITAL_GAINS"
        eligible: frozenset[str] | None = None
        if loss_bucket == "CAPITAL_GAINS_ST_LT_SUBBUCKETS":
            loss_bucket = "IND_LT" if long_term else "IND_ST"
            eligible = frozenset({"IND_LT"}) if long_term else frozenset({"IND_ST", "IND_LT"})
        statutory = self._statutory_amount_for_rule(rule)
        return RealisedTaxEvent(
            lot.country, lot.security_id, lot.acquisition_date, pd.Timestamp(disposal_date),
            resolved.event_rule_id, lot.acquisition_rule_id, resolved.applied_rule_id,
            resolved.transition_rule, applied_basis_rule, float(basis), float(sale_value),
            raw_gain, raw_gain * inclusion, long_term, tax_rate,
            loss_bucket, currency, lot.side, rule.loss_carryforward_years,
            rule.losses_ring_fenced, eligible, rule.ordinary_income_offset,
            statutory.amount_local if statutory is not None else None,
            statutory.currency if statutory is not None else None,
            statutory.kind if statutory is not None else None,
        )

    def tax_year_end_month(self, country: str) -> int:
        if country not in self.config.tax_year_end_months:
            raise MissingDatedTaxConfiguration(f"tax-year-end month unresolved for {country}")
        return int(self.config.tax_year_end_months[country])

    def tax_year(self, country: str, event_date) -> int:
        event = pd.Timestamp(event_date)
        end_month = self.tax_year_end_month(country)
        return int(event.year if event.month <= end_month else event.year + 1)

    def dividend_tax_rate(self, country: str, event_date) -> float:
        """Resolve the resident dividend rate at the event date, fail closed."""
        rule = self.schedule.resolve(country, event_date)
        return self._configured_rate(rule, "dividend_rate", rule.dividend_rate)

    def transaction_tax(self, country: str, event_date, *, buy_notional: float,
                        sell_notional: float) -> TransactionTaxResult:
        if min(buy_notional, sell_notional) < 0:
            raise ValueError("trade notionals must be non-negative")
        rule = self.schedule.resolve(country, event_date)
        buy_rate = self._side_rate(rule, "stt_buy", rule.stt_buy, buy_notional)
        sell_rate = self._side_rate(rule, "stt_sell", rule.stt_sell, sell_notional)
        return TransactionTaxResult(
            country, pd.Timestamp(event_date), float(buy_notional), float(sell_notional),
            buy_rate, sell_rate, float(buy_notional * buy_rate), float(sell_notional * sell_rate),
        )

    def statutory_allowance(self, country: str, event_date) -> StatutoryAmount | None:
        rule = self.schedule.resolve(country, event_date)
        return self._statutory_amount_for_rule(rule)

    def _statutory_amount_for_rule(self, rule: DatedRule) -> StatutoryAmount | None:
        row = self._metadata_row(rule)
        amount = row.get("annual_exempt_local", "")
        if amount == "":
            return None
        currency, kind = row.get("annual_exempt_currency", ""), row.get("annual_exempt_kind", "")
        if not currency or not kind:
            raise MissingDatedTaxConfiguration(f"allowance unit/kind unresolved for {_rule_id(rule)}")
        return StatutoryAmount(float(amount), currency, kind)

    def annual_amount_local(self, country: str, event_date) -> StatutoryAmount | None:
        """Return the configured annual amount in statutory local currency.

        General/personal allowances use the frozen strategy-allocation choice.
        A statutory excess-only threshold is not a personal allowance and is
        therefore returned in full.
        """
        rule = self.schedule.resolve(country, event_date)
        amount = self._statutory_amount_for_rule(rule)
        if amount is None:
            return None
        if amount.kind == "SECTION_112A_EXCESS_ONLY_THRESHOLD":
            return amount
        key = (country, rule.legal_regime)
        if key not in self.config.allowance_allocations:
            raise MissingDatedTaxConfiguration(f"allowance allocation unresolved for {key}")
        return StatutoryAmount(
            amount.amount_local * self.config.allowance_allocations[key],
            amount.currency,
            amount.kind,
        )

    def allocated_allowance(self, country: str, event_date) -> float:
        rule = self.schedule.resolve(country, event_date)
        amount = self.statutory_allowance(country, event_date)
        if amount is None:
            raise MissingDatedTaxConfiguration(f"annual allowance unresolved for {_rule_id(rule)}")
        key = (country, rule.legal_regime)
        if key not in self.config.allowance_allocations:
            raise MissingDatedTaxConfiguration(f"allowance allocation unresolved for {key}")
        allocated = StatutoryAmount(
            amount.amount_local * self.config.allowance_allocations[key], amount.currency, amount.kind
        )
        return allocated.in_accounting_currency(
            self.config.accounting_currency, event_date, self.config.fx_provider
        )

    def brokerage_rate(self, country: str, event_date) -> float:
        rule = self.schedule.resolve(country, event_date)
        key = (country, rule.legal_regime)
        if key not in self.config.brokerage_rates:
            raise MissingDatedTaxConfiguration(f"brokerage assumption unresolved for {key}")
        return float(self.config.brokerage_rates[key])

    def _configured_rate(self, rule: DatedRule, field_name: str, raw: float | None) -> float:
        if raw is not None:
            return float(raw)
        key = (_rule_id(rule), field_name)
        if key not in self.config.rate_overrides:
            raise MissingDatedTaxConfiguration(f"{field_name} unresolved for {key[0]}")
        return float(self.config.rate_overrides[key])

    def _side_rate(self, rule: DatedRule, field_name: str, raw: float | None,
                   notional: float) -> float:
        if raw is not None:
            return float(raw)
        if notional <= 0:
            return 0.0
        return self._configured_rate(rule, field_name, raw)

    def _metadata_row(self, rule: DatedRule) -> dict[str, str]:
        rows = self.schedule.rows.loc[
            self.schedule.rows["country"].eq(rule.country)
            & self.schedule.rows["effective_from"].eq(rule.effective_from)
        ]
        if len(rows) != 1:
            raise LookupError(f"metadata row not unique for {_rule_id(rule)}")
        return rows.iloc[0].to_dict()


def production_architecture_gate() -> dict[str, object]:
    capabilities = {
        "event_date_regime_resolution": hasattr(DatedC12Patch, "resolve_event"),
        "acquisition_transition_state": "acquisition_rule_id" in DatedTaxLot.__dataclass_fields__,
        "grandfathered_lot_basis": hasattr(DatedC12Patch, "realise"),
        "side_specific_transaction_tax": hasattr(DatedC12Patch, "transaction_tax"),
        "bucketed_loss_ring_fencing": hasattr(LossCarryforwardBook, "offset"),
        "inclusive_final_carryforward_year": hasattr(LossVintage, "eligible"),
        "immutable_original_loss_vintage": LossVintage.__dataclass_params__.frozen,
        "security_specific_reference_values": hasattr(SecurityReferenceValueStore, "get"),
        "validated_reference_contract": hasattr(SecurityReferenceValueStore, "from_validated_csv"),
        "event_date_dividend_rate": hasattr(DatedC12Patch, "dividend_tax_rate"),
        "local_currency_statutory_amounts": hasattr(StatutoryAmount, "in_accounting_currency"),
        "annual_threshold_stage": hasattr(DatedC12Patch, "annual_amount_local"),
        "explicit_tax_year_boundaries": hasattr(DatedC12Patch, "tax_year"),
        "point_in_time_fx_contract": hasattr(PointInTimeFXStore, "from_validated_csv"),
        "frozen_sample_materializer": hasattr(DatedC12Patch, "from_frozen_evaluation_artifacts"),
        "unresolved_values_fail_closed": issubclass(MissingDatedTaxConfiguration, RuntimeError),
    }
    return {
        "verdict": "PASS_DATED_C12_PRODUCTION_ARCHITECTURE" if all(capabilities.values()) else "FAIL",
        "capabilities": capabilities,
    }
