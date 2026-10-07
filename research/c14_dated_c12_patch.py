"""Opt-in, non-production dated C14 architecture for the existing C12 design.

Nothing under ``src/alphacomb`` imports this module.  It is the local patch the
production compatibility gate can exercise while statutory calibrations remain
explicitly unresolved.  The objects here model only mechanics that do not
depend on choosing a representative marginal rate, allowance allocation, or
brokerage schedule.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, Mapping

import pandas as pd

from research.c14_dated_engine_reference import (
    DatedRegimeSchedule,
    DatedRule,
    india_section_112a_deemed_cost,
    is_long_term,
)


RateKey = tuple[str, str, str]
AllocationKey = tuple[str, str]
FXProvider = Callable[[str, str, pd.Timestamp], float]


class MissingDatedTaxConfiguration(RuntimeError):
    """Raised instead of silently supplying an unresolved tax input."""


def _rule_id(rule: DatedRule) -> str:
    return f"{rule.country}:{rule.legal_regime}:{rule.effective_from.date()}"


@dataclass(frozen=True)
class ReferenceValue:
    country: str
    security_id: int | str
    reference_date: pd.Timestamp
    value: float
    currency: str
    source: str


class SecurityReferenceValueStore:
    """Security/date keyed statutory reference values with provenance."""

    def __init__(self) -> None:
        self._values: dict[tuple[str, str, pd.Timestamp], ReferenceValue] = {}

    def add(
        self,
        country: str,
        security_id: int | str,
        reference_date,
        value: float,
        *,
        currency: str,
        source: str,
    ) -> None:
        if value < 0:
            raise ValueError("reference value must be non-negative")
        key = (country, str(security_id), pd.Timestamp(reference_date))
        if key in self._values:
            raise ValueError(f"duplicate statutory reference value: {key}")
        self._values[key] = ReferenceValue(
            country=country,
            security_id=security_id,
            reference_date=key[2],
            value=float(value),
            currency=currency,
            source=source,
        )

    def get(self, country: str, security_id: int | str, reference_date) -> ReferenceValue:
        key = (country, str(security_id), pd.Timestamp(reference_date))
        try:
            return self._values[key]
        except KeyError as exc:
            raise MissingDatedTaxConfiguration(
                f"missing security-specific 31-Jan-2018 reference value for "
                f"{country} security {security_id}"
            ) from exc


@dataclass(frozen=True)
class StatutoryAmount:
    """An amount whose source of truth remains in statutory local currency."""

    amount_local: float
    currency: str
    kind: str

    def __post_init__(self) -> None:
        if self.amount_local < 0:
            raise ValueError("statutory amount must be non-negative")
        if not self.currency:
            raise ValueError("statutory currency is required")

    def in_accounting_currency(
        self,
        accounting_currency: str,
        event_date,
        fx_provider: FXProvider | None,
    ) -> float:
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
        return (
            self.carryforward_years == float("inf")
            or year - self.origin_year <= self.carryforward_years
        )


class LossCarryforwardBook:
    """Bucketed loss vintages whose origin year can never be refreshed."""

    def __init__(self) -> None:
        self._vintages: tuple[LossVintage, ...] = ()
        self._next_id = 1

    def add_loss(
        self,
        origin_year: int,
        amount: float,
        bucket: str,
        *,
        carryforward_years: int | float,
        eligible_gain_buckets: set[str] | frozenset[str] | None = None,
    ) -> int:
        if amount <= 0:
            raise ValueError("loss amount must be positive")
        if carryforward_years < 0:
            raise ValueError("carryforward life must be non-negative")
        vintage = LossVintage(
            vintage_id=self._next_id,
            origin_year=int(origin_year),
            original_amount=float(amount),
            remaining_amount=float(amount),
            bucket=bucket,
            carryforward_years=carryforward_years,
            eligible_gain_buckets=(
                frozenset(eligible_gain_buckets) if eligible_gain_buckets is not None else None
            ),
        )
        self._next_id += 1
        self._vintages = (*self._vintages, vintage)
        return vintage.vintage_id

    def vintages(self) -> tuple[LossVintage, ...]:
        return self._vintages

    def offset(
        self,
        year: int,
        gain: float,
        bucket: str,
        *,
        ring_fenced: bool,
    ) -> tuple[float, float]:
        if gain < 0:
            raise ValueError("gain must be non-negative")
        live = [v for v in self._vintages if v.eligible(year)]
        remaining_gain = float(gain)
        used = 0.0
        updated: list[LossVintage] = []
        for vintage in sorted(live, key=lambda item: (item.origin_year, item.vintage_id)):
            allowed_buckets = vintage.eligible_gain_buckets or frozenset({vintage.bucket})
            if remaining_gain <= 1e-12 or (ring_fenced and bucket not in allowed_buckets):
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
    """Mechanically determined dated-tax operations for later C12 integration."""

    def __init__(self, config: DatedPatchConfig):
        self.config = config

    @property
    def schedule(self) -> DatedRegimeSchedule:
        return self.config.schedule

    def resolve_event(
        self,
        country: str,
        event_date,
        *,
        acquisition_date=None,
        event_type: str = "capital_gain",
    ) -> ResolvedEventRule:
        event = pd.Timestamp(event_date)
        acquired = pd.Timestamp(acquisition_date) if acquisition_date is not None else None
        event_rule = self.schedule.resolve(country, event)
        acquisition_rule = self.schedule.resolve(country, acquired) if acquired is not None else None
        applied = self.schedule.resolve(country, event, acquired)
        return ResolvedEventRule(
            country=country,
            event_date=event,
            event_type=event_type,
            event_rule_id=_rule_id(event_rule),
            acquisition_rule_id=_rule_id(acquisition_rule) if acquisition_rule else None,
            applied_rule_id=_rule_id(applied),
            transition_rule=applied.transition_rule,
            basis_rule=applied.basis_rule,
            applied_rule=applied,
        )

    def acquire(
        self,
        country: str,
        security_id: int | str,
        acquisition_date,
        *,
        basis: float,
        currency: str,
    ) -> DatedTaxLot:
        if basis < 0:
            raise ValueError("basis must be non-negative")
        acquired = pd.Timestamp(acquisition_date)
        rule = self.schedule.resolve(country, acquired)
        return DatedTaxLot(
            country=country,
            security_id=security_id,
            acquisition_date=acquired,
            basis=float(basis),
            currency=currency,
            acquisition_rule_id=_rule_id(rule),
        )

    def realise(
        self,
        lot: DatedTaxLot,
        disposal_date,
        *,
        sale_value: float,
        currency: str,
    ) -> RealisedTaxEvent:
        if sale_value < 0:
            raise ValueError("sale value must be non-negative")
        if currency != lot.currency:
            raise MissingDatedTaxConfiguration(
                "lot basis and sale value must share a currency before gain computation"
            )
        resolved = self.resolve_event(
            lot.country,
            disposal_date,
            acquisition_date=lot.acquisition_date,
        )
        rule = resolved.applied_rule
        if rule.holding_period_months is None:
            long_term = False
        else:
            long_term = is_long_term(
                lot.acquisition_date,
                disposal_date,
                months=rule.holding_period_months,
            )
        basis = lot.basis
        applied_basis_rule = resolved.basis_rule if long_term else None
        if applied_basis_rule == "IND_SECTION_55_2_AC":
            reference = self.config.reference_values.get(
                lot.country, lot.security_id, "2018-01-31"
            )
            if reference.currency != lot.currency:
                raise MissingDatedTaxConfiguration(
                    "India reference value and lot basis require a certified common currency"
                )
            basis = india_section_112a_deemed_cost(
                actual_cost=lot.basis,
                fmv_2018_01_31=reference.value,
                sale_value=sale_value,
            )
        rate_field = "cgt_long" if long_term else "cgt_short"
        raw_rate = rule.cgt_long if long_term else rule.cgt_short
        tax_rate = self._configured_rate(rule, rate_field, raw_rate)
        metadata = self._metadata_row(rule)
        inclusion = float(metadata.get("gain_inclusion_fraction") or 1.0)
        raw_gain = float(sale_value - basis)
        taxable_gain = raw_gain * inclusion
        return RealisedTaxEvent(
            country=lot.country,
            security_id=lot.security_id,
            acquisition_date=lot.acquisition_date,
            disposal_date=pd.Timestamp(disposal_date),
            event_rule_id=resolved.event_rule_id,
            acquisition_rule_id=lot.acquisition_rule_id,
            applied_rule_id=resolved.applied_rule_id,
            transition_rule=resolved.transition_rule,
            basis_rule=applied_basis_rule,
            tax_basis=float(basis),
            sale_value=float(sale_value),
            raw_gain=raw_gain,
            taxable_gain=taxable_gain,
            long_term=long_term,
            tax_rate=tax_rate,
            loss_bucket=metadata.get("loss_bucket") or "CAPITAL_GAINS",
            currency=currency,
        )

    def transaction_tax(
        self,
        country: str,
        event_date,
        *,
        buy_notional: float,
        sell_notional: float,
    ) -> TransactionTaxResult:
        if min(buy_notional, sell_notional) < 0:
            raise ValueError("trade notionals must be non-negative")
        rule = self.schedule.resolve(country, event_date)
        buy_rate = self._side_rate(rule, "stt_buy", rule.stt_buy, buy_notional)
        sell_rate = self._side_rate(rule, "stt_sell", rule.stt_sell, sell_notional)
        return TransactionTaxResult(
            country=country,
            event_date=pd.Timestamp(event_date),
            buy_notional=float(buy_notional),
            sell_notional=float(sell_notional),
            buy_rate=buy_rate,
            sell_rate=sell_rate,
            buy_tax=float(buy_notional * buy_rate),
            sell_tax=float(sell_notional * sell_rate),
        )

    def statutory_allowance(self, country: str, event_date) -> StatutoryAmount | None:
        rule = self.schedule.resolve(country, event_date)
        row = self._metadata_row(rule)
        amount = row.get("annual_exempt_local", "")
        if amount == "":
            return None
        currency = row.get("annual_exempt_currency", "")
        kind = row.get("annual_exempt_kind", "")
        if not currency or not kind:
            raise MissingDatedTaxConfiguration(
                f"allowance unit/kind is unresolved for {_rule_id(rule)}"
            )
        return StatutoryAmount(float(amount), currency, kind)

    def allocated_allowance(self, country: str, event_date) -> float:
        rule = self.schedule.resolve(country, event_date)
        amount = self.statutory_allowance(country, event_date)
        if amount is None:
            raise MissingDatedTaxConfiguration(f"annual allowance is unresolved for {_rule_id(rule)}")
        key = (country, rule.legal_regime)
        if key not in self.config.allowance_allocations:
            raise MissingDatedTaxConfiguration(f"allowance allocation is unresolved for {key}")
        allocated_local = StatutoryAmount(
            amount.amount_local * self.config.allowance_allocations[key],
            amount.currency,
            amount.kind,
        )
        return allocated_local.in_accounting_currency(
            self.config.accounting_currency,
            event_date,
            self.config.fx_provider,
        )

    def brokerage_rate(self, country: str, event_date) -> float:
        rule = self.schedule.resolve(country, event_date)
        key = (country, rule.legal_regime)
        if key not in self.config.brokerage_rates:
            raise MissingDatedTaxConfiguration(f"brokerage assumption is unresolved for {key}")
        return float(self.config.brokerage_rates[key])

    def _configured_rate(self, rule: DatedRule, field_name: str, raw: float | None) -> float:
        if raw is not None:
            return float(raw)
        key = (rule.country, rule.legal_regime, field_name)
        if key not in self.config.rate_overrides:
            raise MissingDatedTaxConfiguration(f"{field_name} is unresolved for {key[:2]}")
        return float(self.config.rate_overrides[key])

    def _side_rate(
        self,
        rule: DatedRule,
        field_name: str,
        raw: float | None,
        notional: float,
    ) -> float:
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


def local_patch_architecture_gate() -> dict[str, object]:
    """Capability declaration for the opt-in patch; not a production approval."""

    capabilities = {
        "event_date_regime_resolution": hasattr(DatedC12Patch, "resolve_event"),
        "acquisition_transition_state": "acquisition_rule_id" in DatedTaxLot.__dataclass_fields__,
        "grandfathered_lot_basis": hasattr(DatedC12Patch, "realise"),
        "side_specific_transaction_tax": hasattr(DatedC12Patch, "transaction_tax"),
        "bucketed_loss_ring_fencing": hasattr(LossCarryforwardBook, "offset"),
        "inclusive_final_carryforward_year": hasattr(LossVintage, "eligible"),
        "immutable_original_loss_vintage": LossVintage.__dataclass_params__.frozen,
        "security_specific_reference_values": hasattr(SecurityReferenceValueStore, "get"),
        "local_currency_statutory_amounts": hasattr(StatutoryAmount, "in_accounting_currency"),
        "unresolved_values_fail_closed": issubclass(MissingDatedTaxConfiguration, RuntimeError),
    }
    return {
        "verdict": "PASS_LOCAL_NONPRODUCTION_ARCHITECTURE" if all(capabilities.values()) else "FAIL",
        "capabilities": capabilities,
        "production_compatible": False,
        "production_blocker": "explicit statutory/model configuration and integration into frozen C12 remain outstanding",
    }
