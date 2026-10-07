"""Tax-lot ledger: the accounting engine behind every after-tax number in this project.

A portfolio-level "turnover x tax rate" approximation is not good enough for a paper, because the
three things that actually decide the tax bill are all lot-level:

1. **Which lot you sell.** Selling the highest-cost lot realises less gain than selling the oldest.
2. **How long you held it.** One day either side of twelve months changes the rate by 17 points
   under the default US regime (s1222, s1(h)).
3. **Whether the loss is allowed.** A monthly-rebalanced strategy re-buys names constantly, so the
   wash-sale rule (s1091) disallows a large share of exactly the losses a tax-aware strategy is
   trying to harvest. Ignoring s1091 is the easiest way to overstate after-tax alpha.

Everything is tracked in dollars. A lot carries the market value it had when it was opened (its
basis) and its current market value, which is rolled forward by the stock's realised return each
month. This is equivalent to tracking shares and prices, and avoids needing a price history.

Sign convention: ``side`` is +1 for a long lot and -1 for a short lot; both store positive
``basis`` and ``value``. Realised gain on closing a fraction f of a lot is
``side * f * (value - basis)``, which is correct for both sides: a short lot whose price has risen
has ``value > basis`` and therefore produces a loss.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

from .dated import DatedC12Patch, DatedTaxLot, RealisedTaxEvent
from .regimes import TaxRegime


class LotMethod(str, Enum):
    """Which lot to sell first. HIFO is the industry default for tax-managed accounts."""

    FIFO = "fifo"          # oldest first: the statutory default, and the worst of the four here
    LIFO = "lifo"          # newest first
    HIFO = "hifo"          # highest basis first: minimises realised gain AND, in a churning
                           # book, leaves the oldest lots untouched so they age into long-term
    TAX_OPTIMAL = "tax_optimal"  # losses first (largest first), then long-term gains, then short-term


@dataclass
class Lot:
    permno: int
    open_date: pd.Timestamp
    basis: float
    value: float
    side: int = 1
    washed_from: pd.Timestamp | None = None  # s1223(3): holding period tacked from a washed lot
    dated_basis_local: float | None = None
    dated_currency: str | None = None
    dated_acquisition_rule_id: str | None = None
    statutory_reference_local: float | None = None

    @property
    def unrealised(self) -> float:
        return self.side * (self.value - self.basis)

    def holding_date(self) -> pd.Timestamp:
        """The date the holding period started, after any s1223(3) tacking."""
        return self.washed_from or self.open_date

    def months_held(self, asof) -> float:
        return (pd.Timestamp(asof) - self.holding_date()).days / 30.4375

    def held_beyond(self, asof, months: int) -> bool:
        """Exact anniversary test, not a month fraction.

        s1222 asks whether the asset was held for *more than* the period. The holding period starts
        the day after acquisition, so property bought on 31 January 2020 and sold on 31 January 2021
        has been held for exactly one year and the gain is short-term - even though 2020 was a leap
        year and 366 elapsed days would round to 12.02 months. The boundary is worth 17 points of
        tax under the default regime, so it is worth getting exactly right.
        """
        anniversary = self.holding_date() + pd.DateOffset(months=months)
        return pd.Timestamp(asof) > anniversary


@dataclass
class RealisedGain:
    date: pd.Timestamp
    permno: int
    amount: float            # signed: positive is a gain
    long_term: bool
    disallowed: float = 0.0  # portion denied by s1091 and rolled into a replacement lot's basis
    dated_event: RealisedTaxEvent | None = None

    @property
    def allowed(self) -> float:
        """The amount that actually enters the tax computation after s1091."""
        return self.amount + self.disallowed if self.amount < 0 else self.amount


@dataclass
class _PendingLoss:
    date: pd.Timestamp
    permno: int
    remaining: float  # positive magnitude of loss still available to be disallowed
    gain_ref: RealisedGain


@dataclass
class TaxLotLedger:
    """Lot-level position book with US wash-sale and holding-period rules.

    Usage per month: ``trade_to`` every name to reach the target position, then ``accrue_returns``
    to roll lot values forward. ``mark_to_market`` is called once a year under s475(f).
    """

    regime: TaxRegime
    method: LotMethod = LotMethod.HIFO
    dated_engine: DatedC12Patch | None = None
    dated_country: str | None = None
    dated_currency: str | None = None
    lots: dict[int, list[Lot]] = field(default_factory=dict)
    realised: list[RealisedGain] = field(default_factory=list)
    _pending_losses: list[_PendingLoss] = field(default_factory=list)
    _recent_buys: list[tuple[pd.Timestamp, int, Lot]] = field(default_factory=list)

    # ---------------------------------------------------------------- positions
    def position(self, permno: int) -> float:
        """Signed market value of the position in dollars."""
        return sum(lot.side * lot.value for lot in self.lots.get(permno, []))

    def gross_value(self) -> float:
        return sum(lot.value for lots in self.lots.values() for lot in lots)

    def net_value(self) -> float:
        return sum(lot.side * lot.value for lots in self.lots.values() for lot in lots)

    def unrealised_total(self) -> float:
        return sum(lot.unrealised for lots in self.lots.values() for lot in lots)

    def embedded_gain_rate(self, permno: int, asof) -> tuple[float, float]:
        """(gain per dollar of market value, effective tax rate) for selling this long position now.

        Feeds the optimiser's tax penalty, so the portfolio knows before it trades which names are
        expensive to sell. Returns (0, 0) for an empty or short position.
        """
        asof = pd.Timestamp(asof)
        lots = [lot for lot in self.lots.get(permno, []) if lot.side == 1]
        value = sum(lot.value for lot in lots)
        basis = sum(lot.basis for lot in lots)
        if value <= 0 or basis <= 0:
            return 0.0, 0.0
        gain = sum(lot.value - lot.basis for lot in lots)
        taxed = sum((lot.value - lot.basis) * self._rate(lot, asof, closing_short=False) for lot in lots)
        rate = taxed / gain if abs(gain) > 1e-12 else 0.0

        # Clip to [-1, 1]. For a winner gain/value is naturally bounded above by 1, but for a loser
        # it is unbounded below: a position down 99.99% reports an embedded loss of 9999x its
        # remaining value. Fed to the optimiser as a per-dollar harvesting credit that is roughly
        # 4000, against alphas of order 0.01, it destroys the conditioning of the problem and the
        # book explodes. That happened: the tax-aware arms of the leverage sweep reported
        # annualised returns of -112,000% because NAV hit zero in the first months.
        #
        # The clip is not a fudge. The optimiser term is a LINEAR approximation to the tax
        # consequence of a trade, valid near the current position. Once a holding has lost most of
        # its value the linearisation is meaningless, and -1 (the whole remaining position is
        # embedded loss) is the largest statement about it that still means anything.
        return float(np.clip(gain / value, -1.0, 1.0)), rate

    # ---------------------------------------------------------------- trading
    def buy(self, permno: int, date, value: float) -> Lot:
        """Open or add to a long lot with ``value`` dollars, applying any pending s1091 loss."""
        date = pd.Timestamp(date)
        if value <= 0:
            raise ValueError("buy value must be positive")
        lot = Lot(permno=permno, open_date=date, basis=value, value=value, side=1)
        self._attach_dated_acquisition(lot, date, value)
        if self.regime.wash_sale_rule:
            self._apply_wash(lot, date, value)
        self.lots.setdefault(permno, []).append(lot)
        self._recent_buys.append((date, permno, lot))
        return lot

    def short(self, permno: int, date, value: float) -> Lot:
        date = pd.Timestamp(date)
        if value <= 0:
            raise ValueError("short value must be positive")
        lot = Lot(permno=permno, open_date=date, basis=value, value=value, side=-1)
        self._attach_dated_acquisition(lot, date, value)
        self.lots.setdefault(permno, []).append(lot)
        return lot

    def sell(self, permno: int, date, value: float, side: int = 1) -> list[RealisedGain]:
        """Close ``value`` dollars of market value on the given side, realising gains lot by lot."""
        date = pd.Timestamp(date)
        pool = [lot for lot in self.lots.get(permno, []) if lot.side == side]
        remaining = min(value, sum(lot.value for lot in pool))
        out: list[RealisedGain] = []
        for lot in self._order(pool, date):
            if remaining <= 1e-12:
                break
            take = min(lot.value, remaining)
            fraction = take / lot.value if lot.value > 0 else 0.0
            gain = side * (take - lot.basis * fraction)
            dated_event = self._dated_realisation(lot, date, take, fraction)
            rg = RealisedGain(date=date, permno=permno, amount=gain,
                              long_term=(dated_event.long_term if dated_event is not None else
                                         self._is_long_term(lot, date, closing_short=(side == -1))),
                              dated_event=dated_event)
            lot.basis -= lot.basis * fraction
            if lot.dated_basis_local is not None:
                lot.dated_basis_local -= lot.dated_basis_local * fraction
            if lot.statutory_reference_local is not None:
                lot.statutory_reference_local -= lot.statutory_reference_local * fraction
            lot.value -= take
            remaining -= take
            if gain < 0 and self.regime.wash_sale_rule:
                self._register_loss(rg, date, permno, -gain)
            out.append(rg)
        self.lots[permno] = [lot for lot in self.lots.get(permno, []) if lot.value > 1e-10]
        self.realised.extend(out)
        return out

    def trade_to(self, permno: int, date, target: float) -> list[RealisedGain]:
        """Move the signed position in one name to ``target`` dollars, crossing zero if needed."""
        current = self.position(permno)
        gains: list[RealisedGain] = []
        if target >= 0 and current >= 0:
            if target < current:
                gains += self.sell(permno, date, current - target, side=1)
            elif target > current:
                self.buy(permno, date, target - current)
        elif target <= 0 and current <= 0:
            if target > current:                       # cover part of the short
                gains += self.sell(permno, date, target - current, side=-1)
            elif target < current:
                self.short(permno, date, current - target)
        else:                                          # crossing through zero
            if current > 0:
                gains += self.sell(permno, date, current, side=1)
            else:
                gains += self.sell(permno, date, -current, side=-1)
            if target > 0:
                self.buy(permno, date, target)
            elif target < 0:
                self.short(permno, date, -target)
        return gains

    # ---------------------------------------------------------------- roll forward
    def accrue_returns(self, returns: pd.Series) -> None:
        """Roll every lot's market value forward by its stock's realised return."""
        for permno, lots in self.lots.items():
            r = returns.get(permno)
            if r is None or not pd.notna(r):
                continue
            factor = max(1.0 + float(r), 0.0)
            for lot in lots:
                lot.value *= factor
        self.lots = {p: [lot for lot in lots if lot.value > 1e-10] for p, lots in self.lots.items()}

    def expire_wash_window(self, date) -> None:
        """Drop buys and pending losses outside the s1091 window, to bound memory."""
        cutoff = pd.Timestamp(date) - pd.Timedelta(days=self.regime.wash_sale_window_days)
        self._recent_buys = [b for b in self._recent_buys if b[0] >= cutoff]
        self._pending_losses = [p for p in self._pending_losses if p.date >= cutoff]

    def mark_to_market(self, date) -> float:
        """s475(f): treat every open lot as sold and re-bought at today's value. Returns the gain."""
        date = pd.Timestamp(date)
        total = 0.0
        for permno, lots in self.lots.items():
            for lot in lots:
                gain = lot.unrealised
                if abs(gain) > 1e-12:
                    self.realised.append(RealisedGain(date, permno, gain, long_term=False))
                    total += gain
                lot.basis = lot.value
                lot.open_date = date
                lot.washed_from = None
        return total

    def liquidate(self, date) -> list[RealisedGain]:
        """Close every position, so the deferred tax on unrealised gains is brought into the sum."""
        date = pd.Timestamp(date)
        out: list[RealisedGain] = []
        for permno in list(self.lots):
            for side in (1, -1):
                value = sum(lot.value for lot in self.lots.get(permno, []) if lot.side == side)
                if value > 1e-10:
                    out += self.sell(permno, date, value, side=side)
        return out

    def snapshot_statutory_references(self, date) -> None:
        """Freeze lot-level FMV on a statutory reference date.

        The validated security table supplies a high/close price ratio.  Applying
        it to each lot's close value preserves units and the security-specific
        statutory high without pretending a per-share price is a whole-lot basis.
        """
        if self.dated_engine is None or self.dated_country != "IND":
            return
        date = pd.Timestamp(date)
        if date != pd.Timestamp("2018-01-31"):
            return
        assert self.dated_currency is not None
        for permno, lots in self.lots.items():
            reference = self.dated_engine.config.reference_values.get("IND", permno, date)
            if reference.currency != self.dated_currency:
                raise ValueError("section 112A reference currency mismatch")
            for lot in lots:
                if lot.side != 1 or lot.open_date >= pd.Timestamp("2018-02-01"):
                    continue
                close_local = self._accounting_to_local(lot.value, date)
                lot.statutory_reference_local = close_local * reference.high_to_close_ratio

    # ---------------------------------------------------------------- internals
    def _order(self, lots: list[Lot], asof: pd.Timestamp) -> list[Lot]:
        if self.method is LotMethod.FIFO:
            return sorted(lots, key=lambda l: l.open_date)
        if self.method is LotMethod.LIFO:
            return sorted(lots, key=lambda l: l.open_date, reverse=True)
        if self.method is LotMethod.HIFO:
            return sorted(lots, key=lambda l: l.basis / max(l.value, 1e-12), reverse=True)
        # TAX_OPTIMAL: realise losses first (biggest first), then long-term gains, then short-term.
        def key(lot: Lot):
            g = lot.unrealised
            lt = self._is_long_term(lot, asof, closing_short=(lot.side == -1))
            bucket = 0 if g < 0 else (1 if lt else 2)
            return (bucket, g if g < 0 else -g)
        return sorted(lots, key=key)

    def _is_long_term(self, lot: Lot, date: pd.Timestamp, closing_short: bool) -> bool:
        if self.regime.mark_to_market:
            return False                      # s475(f) makes everything ordinary
        if closing_short:
            return False                      # s1233: closing a short is always short-term
        return lot.held_beyond(date, self.regime.long_term_months)

    def _rate(self, lot: Lot, date: pd.Timestamp, closing_short: bool) -> float:
        lt = self._is_long_term(lot, date, closing_short)
        return self.regime.long_term_rate if lt else self.regime.short_term_rate

    def _attach_dated_acquisition(self, lot: Lot, date: pd.Timestamp, value: float) -> None:
        if self.dated_engine is None:
            return
        if not self.dated_country or not self.dated_currency:
            raise ValueError("dated country and statutory local currency are required")
        local_basis = self._accounting_to_local(value, date)
        dated = self.dated_engine.acquire(
            self.dated_country, lot.permno, date, basis=local_basis,
            currency=self.dated_currency, side=lot.side,
        )
        lot.dated_basis_local = dated.basis
        lot.dated_currency = dated.currency
        lot.dated_acquisition_rule_id = dated.acquisition_rule_id

    def _dated_realisation(self, lot: Lot, date: pd.Timestamp, take: float,
                           fraction: float) -> RealisedTaxEvent | None:
        if self.dated_engine is None:
            return None
        if lot.dated_basis_local is None or lot.dated_currency is None or not self.dated_country:
            raise ValueError("dated lot acquisition state is missing")
        dated_lot = DatedTaxLot(
            country=self.dated_country,
            security_id=lot.permno,
            acquisition_date=lot.open_date,
            basis=lot.dated_basis_local * fraction,
            currency=lot.dated_currency,
            acquisition_rule_id=str(lot.dated_acquisition_rule_id),
            side=lot.side,
            statutory_reference_value=(
                None if lot.statutory_reference_local is None
                else lot.statutory_reference_local * fraction
            ),
        )
        return self.dated_engine.realise(
            dated_lot, date, sale_value=self._accounting_to_local(take, date),
            currency=lot.dated_currency,
        )

    def _accounting_to_local(self, amount: float, date: pd.Timestamp) -> float:
        assert self.dated_engine is not None and self.dated_currency is not None
        accounting = self.dated_engine.config.accounting_currency
        if accounting == self.dated_currency:
            return float(amount)
        provider = self.dated_engine.config.fx_provider
        if provider is None:
            raise ValueError(
                f"point-in-time FX is required for {self.dated_currency}->{accounting}"
            )
        rate = float(provider(self.dated_currency, accounting, pd.Timestamp(date)))
        if rate <= 0:
            raise ValueError("FX rate must be positive")
        return float(amount / rate)

    def _register_loss(self, rg: RealisedGain, date: pd.Timestamp, permno: int, magnitude: float) -> None:
        """s1091 looking backwards: a purchase in the 30 days *before* the loss sale disallows it."""
        window = pd.Timedelta(days=self.regime.wash_sale_window_days)
        remaining = magnitude
        for bdate, bpermno, blot in self._recent_buys:
            if bpermno != permno or remaining <= 1e-12 or not (date - window <= bdate <= date):
                continue
            absorbed = min(remaining, blot.value)
            blot.basis += absorbed
            blot.washed_from = min(blot.holding_date(), rg.date)
            rg.disallowed += absorbed
            remaining -= absorbed
        if remaining > 1e-12:
            self._pending_losses.append(_PendingLoss(date, permno, remaining, rg))

    def _apply_wash(self, lot: Lot, date: pd.Timestamp, value: float) -> None:
        """s1091 looking forwards: this purchase disallows a loss booked in the previous 30 days."""
        window = pd.Timedelta(days=self.regime.wash_sale_window_days)
        capacity = value
        for pending in self._pending_losses:
            if pending.permno != lot.permno or capacity <= 1e-12:
                continue
            if not (date - window <= pending.date <= date):
                continue
            absorbed = min(pending.remaining, capacity)
            lot.basis += absorbed
            lot.washed_from = min(lot.holding_date(), pending.date)
            pending.gain_ref.disallowed += absorbed
            pending.remaining -= absorbed
            capacity -= absorbed
        self._pending_losses = [p for p in self._pending_losses if p.remaining > 1e-12]
