"""After-tax backtest: gross -> net of trading cost -> net of tax, in dollars.

This is the measurement the project is ultimately judged on. It extends the cost ledger of contract
C12 additively with a tax ledger, so Maham's statistics code keeps working unchanged and simply
gains extra columns.

What it models
--------------
* **Dollars, not weights.** Tax is a lot-level dollar quantity, so the backtest runs a real NAV.
  Positions are ``w_i * NAV``; trading costs and tax are debited from NAV.
* **Total return split into price and dividend.** ``ret_next`` is a total return. Lot values are
  rolled forward by the *price* part only and the dividend arrives as taxable cash, because that is
  what determines the split between dividend tax and capital-gains tax. The economic P&L is
  unchanged by the split; only its tax character changes.
* **Shorts pay the dividend.** A short position owes a substitute payment. Under the default
  taxable-individual regime that payment is not currently deductible (s263(h) and the
  investment-interest limits), which is a real and rarely modelled asymmetry of long/short
  strategies in taxable hands.
* **Annual settlement with carryforward.** Gains net within character, then across (s1222), losses
  offset ordinary income only up to the statutory cap (s1211(b)), and the excess carries forward
  (s1212(b)).
* **Deferred tax.** Reporting only realised tax flatters any strategy that defers gains, so the
  summary also reports a liquidation figure in which every open position is sold on the last day.

What it does not model (stated, not hidden)
-------------------------------------------
* State and local tax, the alternative minimum tax, and s1256 or straddle rules.
* Constructive-sale rules (s1259) for offsetting long/short positions in the same name; our
  optimiser never holds both sides of one name, so this does not bind here.
* Intra-month timing: trades settle at month end, so the wash-sale window is evaluated on
  month-end dates. Adjacent month ends are 28-31 days apart, so a sale followed by a repurchase
  in the next month is treated as a wash. That is the conservative reading and we report how much
  of the loss it disallows.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..portfolio.cost_terms import (BorrowFeeProxy, borrow_fee_proxy_from_cost_config,
                                    cost_inputs_for, trade_cost_numpy)
from .dated import (DatedC12Patch, LossCarryforwardBook,
                    MissingDatedTaxConfiguration, RealisedTaxEvent)
from .lots import LotMethod, TaxLotLedger
from .regimes import TaxRegime, get_regime


@dataclass
class TaxConfig:
    """Everything about the after-tax run that is not a statutory rate."""

    regime: TaxRegime = field(default_factory=lambda: get_regime("taxable"))
    lot_method: LotMethod = LotMethod.HIFO
    accounting: str = "accrual"        # accrual | year_end | cash
    dividend_yield_annual: float = 0.02   # [verify] sample-period average; a sensitivity parameter
    liquidate_at_end: bool = True
    initial_nav: float = 1.0e9
    dated_engine: DatedC12Patch | None = None
    dated_country: str | None = None
    dated_local_currency: str | None = None

    def __post_init__(self) -> None:
        if self.dated_engine is not None and not self.dated_country:
            raise ValueError("dated_country is required when dated_engine is configured")
        if self.dated_engine is not None and not self.dated_local_currency:
            raise ValueError("dated_local_currency is required when dated_engine is configured")

    @staticmethod
    def of(regime: str | TaxRegime, **kwargs) -> "TaxConfig":
        return TaxConfig(regime=get_regime(regime), **kwargs)


class _YearBook:
    """Running within-year tax computation, so monthly accrual and annual settlement agree."""

    def __init__(self, regime: TaxRegime):
        self.regime = regime
        self.reset()
        self.carryforward = 0.0
        self._vintages: list[list[float]] = []
        self._year = 0

    def reset(self) -> None:
        self.st = 0.0
        self.lt = 0.0
        self.div_qualified = 0.0
        self.div_ordinary = 0.0
        self.short_div_paid = 0.0
        self.accrued = 0.0

    def owed(self) -> float:
        r = self.regime
        st, lt, loss = self.st, self.lt, self.carryforward
        if loss > 0:
            take = min(loss, max(st, 0.0)); st -= take; loss -= take
            take = min(loss, max(lt, 0.0)); lt -= take
        if st < 0 and lt > 0:
            offset = min(-st, lt); st += offset; lt -= offset
        elif lt < 0 and st > 0:
            offset = min(-lt, st); lt += offset; st -= offset
        gains_tax = max(st, 0.0) * r.short_term_rate + max(lt, 0.0) * r.long_term_rate
        net_loss = -(min(st, 0.0) + min(lt, 0.0))
        if net_loss > 0:
            gains_tax -= min(net_loss, r.annual_ordinary_offset) * r.short_term_rate
        div_tax = (self.div_qualified * r.qualified_dividend_rate
                   + self.div_ordinary * r.ordinary_dividend_rate)
        deduction = (self.short_div_paid * r.ordinary_dividend_rate
                     if r.short_dividend_deductible else 0.0)
        return gains_tax + div_tax - deduction

    def close_year(self, year: int | None = None) -> None:
        r = self.regime
        if year is not None:
            self._year = year
        net_current = self.st + self.lt
        if net_current > 0:
            remaining_gain = net_current
            for vintage in sorted(self._vintages, key=lambda item: item[0]):
                take = min(vintage[1], remaining_gain)
                vintage[1] -= take
                remaining_gain -= take
                if remaining_gain <= 1e-12:
                    break
            self._vintages = [v for v in self._vintages if v[1] > 1e-12]
        elif net_current < 0:
            usable = min(-net_current, r.annual_ordinary_offset)
            fresh = (-net_current - usable) if r.loss_carryforward else 0.0
            if fresh > 1e-12:
                self._vintages.append([self._year, fresh])
        life = getattr(r, "carryforward_years", float("inf"))
        if life != float("inf"):
            self._vintages = [v for v in self._vintages if self._year - v[0] <= life]
        self.carryforward = float(sum(v[1] for v in self._vintages))
        self.reset()


class _DatedYearBook:
    """Fail-closed annual book for C14 events and statutory loss vintages."""

    def __init__(self, engine: DatedC12Patch, country: str, local_currency: str):
        self.engine = engine
        self.country = country
        self.local_currency = local_currency
        self.carry = LossCarryforwardBook()
        self.events: list[RealisedTaxEvent] = []
        self.dividends: list[tuple[float, float]] = []
        self.short_div_paid = 0.0
        self.accrued = 0.0

    @property
    def carryforward(self) -> float:
        return float(sum(v.remaining_amount for v in self.carry.vintages()))

    def add_event(self, event: RealisedTaxEvent) -> None:
        if event.currency != self.local_currency:
            raise MissingDatedTaxConfiguration("dated event currency differs from annual book")
        self.events.append(event)

    def add_dividend(self, amount_local: float, rate: float) -> None:
        self.dividends.append((float(amount_local), float(rate)))

    def owed(self, year: int) -> float:
        book = self.carry.copy()
        self._add_current_losses(book, year)
        tax = self._tax_gains(book, year)
        tax += sum(amount * rate for amount, rate in self.dividends)
        return float(tax)

    def close_year(self, year: int) -> None:
        book = self.carry.copy()
        book.expire(year)
        self._add_current_losses(book, year)
        self._tax_gains(book, year)
        self.carry = book
        self.events = []
        self.dividends = []
        self.short_div_paid = 0.0
        self.accrued = 0.0

    def _add_current_losses(self, book: LossCarryforwardBook, year: int) -> None:
        for event in self.events:
            if event.taxable_gain >= -1e-12:
                continue
            if event.carryforward_years is None or event.losses_ring_fenced is None:
                raise MissingDatedTaxConfiguration(
                    f"loss configuration unresolved for {event.applied_rule_id}"
                )
            book.add_loss(
                year, -event.taxable_gain, event.loss_bucket,
                carryforward_years=event.carryforward_years,
                eligible_gain_buckets=event.eligible_gain_buckets,
            )

    def _tax_gains(self, book: LossCarryforwardBook, year: int) -> float:
        taxable_events: list[tuple[RealisedTaxEvent, float]] = []
        for event in (item for item in self.events if item.taxable_gain > 1e-12):
            if event.losses_ring_fenced is None:
                raise MissingDatedTaxConfiguration(
                    f"loss ring-fence unresolved for {event.applied_rule_id}"
                )
            taxable, _ = book.offset(
                year, event.taxable_gain, event.loss_bucket,
                ring_fenced=event.losses_ring_fenced,
            )
            taxable_events.append((event, taxable))

        # Section 112A is an annual allowance on aggregate qualifying LTCG,
        # not a per-lot exemption.  Apply it after statutory loss offsets and
        # only to the long-term bucket.  General/personal allowances remain
        # governed by the explicit allocation configuration; decision 2C
        # allocates zero to this strategy.
        threshold_remaining: dict[tuple[str, str, float], float] = {}
        tax = 0.0
        for event, taxable in taxable_events:
            kind = event.annual_amount_kind
            if kind == "CAPITAL_INCOME_ALLOWANCE":
                allocated = self.engine.annual_amount_local(
                    event.country, event.disposal_date
                )
                if allocated is None or allocated.currency != self.local_currency:
                    raise MissingDatedTaxConfiguration(
                        f"annual allowance currency/configuration unresolved for {event.applied_rule_id}"
                    )
                if allocated.amount_local > 1e-12:
                    raise MissingDatedTaxConfiguration(
                        "positive capital-income allowance requires an approved cross-income allocation stage"
                    )
            elif kind == "SECTION_112A_EXCESS_ONLY_THRESHOLD" and event.long_term:
                if event.annual_amount_local is None or event.annual_amount_currency != self.local_currency:
                    raise MissingDatedTaxConfiguration(
                        f"section 112A threshold currency/configuration unresolved for {event.applied_rule_id}"
                    )
                key = (event.annual_amount_currency, kind, float(event.annual_amount_local))
                remaining = threshold_remaining.setdefault(key, float(event.annual_amount_local))
                sheltered = min(remaining, taxable)
                threshold_remaining[key] = remaining - sheltered
                taxable -= sheltered
            tax += taxable * event.tax_rate
        return float(tax)


def after_tax_backtest(weights: pd.DataFrame, bundle, cfg: dict, tax_cfg: TaxConfig | None = None,
                       cost_multiplier: float = 1.0) -> pd.DataFrame:
    """Run one strategy's weights through costs and tax. Returns an extended contract-C12 table."""
    tax_cfg = tax_cfg or TaxConfig()
    regime = tax_cfg.regime
    costs_cfg = cfg["costs"]
    aum = float(costs_cfg["aum_usd_2020"])
    k = float(costs_cfg["impact_k"]) * cost_multiplier
    commission = float(costs_cfg["commission_bps"])
    borrow_fee_proxy = borrow_fee_proxy_from_cost_config(costs_cfg)
    tax_year_end_month = 12
    if tax_cfg.dated_engine is not None:
        if tax_cfg.accounting != "year_end":
            raise MissingDatedTaxConfiguration(
                "dated C14 evaluation requires year_end accounting under frozen decision 3A"
            )
        tax_year_end_month = tax_cfg.dated_engine.tax_year_end_month(
            str(tax_cfg.dated_country)
        )

    returns = bundle.targets.set_index(["date", "permno"])["ret_next"]
    div_col = "div_next" if "div_next" in bundle.targets.columns else None
    if div_col:
        dividends = bundle.targets.set_index(["date", "permno"])[div_col]
    monthly_div = tax_cfg.dividend_yield_annual / 12.0

    ledger = TaxLotLedger(
        regime, tax_cfg.lot_method,
        dated_engine=tax_cfg.dated_engine,
        dated_country=tax_cfg.dated_country,
        dated_currency=tax_cfg.dated_local_currency,
    )
    if tax_cfg.dated_engine is None:
        book: _YearBook | _DatedYearBook = _YearBook(regime)
    else:
        book = _DatedYearBook(
            tax_cfg.dated_engine, str(tax_cfg.dated_country),
            str(tax_cfg.dated_local_currency),
        )
    nav = float(tax_cfg.initial_nav)
    deferred_cash: list[tuple[int, float]] = []   # (year owed, amount) for cash-basis accounting

    rows = []
    dates = sorted(weights["date"].unique())
    for i, date in enumerate(dates):
        date = pd.Timestamp(date)
        tax_year = (
            tax_cfg.dated_engine.tax_year(str(tax_cfg.dated_country), date)
            if tax_cfg.dated_engine is not None else date.year
        )
        group = weights[weights["date"] == date]
        target_w = pd.Series(group["w"].to_numpy(dtype=float), index=group["permno"].to_numpy())
        held = pd.Index([p for p in ledger.lots if abs(ledger.position(p)) > 1e-8])
        idx = target_w.index.union(held)
        w_full = target_w.reindex(idx).fillna(0.0)
        prev_dollars = pd.Series([ledger.position(p) for p in idx], index=idx, dtype=float)
        prev_w = prev_dollars / nav if nav > 0 else prev_dollars * 0.0

        # ---- trade to target, lot by lot -------------------------------------------------
        target_dollars = w_full * nav
        ledger.expire_wash_window(date)
        realised_st = realised_lt = disallowed = 0.0
        for permno in idx:
            gains = ledger.trade_to(int(permno), date, float(target_dollars[permno]))
            for g in gains:
                if isinstance(book, _DatedYearBook):
                    if g.dated_event is None:
                        raise MissingDatedTaxConfiguration("dated realised event was not produced")
                    book.add_event(g.dated_event)
                if g.long_term:
                    realised_lt += g.allowed
                else:
                    realised_st += g.allowed
                disallowed += g.disallowed
        if isinstance(book, _YearBook):
            book.st += realised_st
            book.lt += realised_lt
        ledger.snapshot_statutory_references(date)

        # ---- trading costs ----------------------------------------------------------------
        ci = cost_inputs_for(
            date,
            bundle.cost_inputs,
            idx,
            borrow_fee_proxy=borrow_fee_proxy,
            allow_synthetic_market_imputation=str(getattr(bundle, "source", "")).startswith("synthetic"),
        )
        dw = (w_full - prev_w).to_numpy()
        spread_arr = ci["spread"].to_numpy() * cost_multiplier
        spread_cost = float((0.5 * spread_arr * np.abs(dw)).sum() + commission / 10_000.0 * np.abs(dw).sum())
        total_trade = float(trade_cost_numpy(dw, spread_arr, ci["sigma_d"].to_numpy(),
                                             ci["adv_usd"].to_numpy(), aum, k, commission).sum())
        impact_cost = max(total_trade - spread_cost, 0.0)
        borrow_cost = float((ci["borrow_fee"].to_numpy() / 12.0
                             * np.clip(-w_full.to_numpy(), 0, None)).sum())
        transaction_tax_cost = 0.0
        if tax_cfg.dated_engine is not None:
            transaction_tax_cost = tax_cfg.dated_engine.transaction_tax(
                str(tax_cfg.dated_country),
                date,
                buy_notional=float(np.clip(dw, 0, None).sum()),
                sell_notional=float(np.clip(-dw, 0, None).sum()),
            ).total

        # ---- hold for one month ------------------------------------------------------------
        r = returns.reindex(pd.MultiIndex.from_product([[date], idx])).fillna(0.0)
        r.index = idx
        if div_col:
            q = dividends.reindex(pd.MultiIndex.from_product([[date], idx])).fillna(0.0)
            q.index = idx
        else:
            q = pd.Series(monthly_div, index=idx)
        q = q.clip(lower=0.0)

        w_arr = w_full.to_numpy()
        r_arr = r.to_numpy()
        gross = float((w_arr * r_arr).sum())
        long_ret = float((np.clip(w_arr, 0, None) * r_arr).sum())
        short_ret = float((np.clip(w_arr, None, 0) * r_arr).sum())

        # dividends: longs receive, shorts pay a substitute payment
        pos_dollars = w_full * nav
        div_received = float((np.clip(pos_dollars, 0, None) * q).sum())
        div_paid = float((np.clip(-pos_dollars, 0, None) * q).sum())
        qualified = div_received * _qualifies(ledger, idx, date, regime)
        if isinstance(book, _DatedYearBook):
            assert tax_cfg.dated_engine is not None
            dividend_rate = tax_cfg.dated_engine.dividend_tax_rate(
                str(tax_cfg.dated_country), date
            )
            book.add_dividend(
                _accounting_to_local(div_received, date, tax_cfg.dated_engine,
                                     str(tax_cfg.dated_local_currency)),
                dividend_rate,
            )
            book.short_div_paid += _accounting_to_local(
                div_paid, date, tax_cfg.dated_engine, str(tax_cfg.dated_local_currency)
            )
        else:
            book.div_qualified += qualified
            book.div_ordinary += div_received - qualified
            book.short_div_paid += div_paid

        ledger.accrue_returns(r - q)   # price return only; the dividend already came out as cash

        # ---- tax accrual --------------------------------------------------------------------
        if regime.mark_to_market and date.month == 12 and isinstance(book, _YearBook):
            book.st += ledger.mark_to_market(date)
        tax_due = 0.0
        if regime.taxable:
            if tax_cfg.accounting == "accrual":
                owed = book.owed(date.year) if isinstance(book, _DatedYearBook) else book.owed()
                due_local_or_accounting = owed - book.accrued
                book.accrued = owed
                tax_due = (
                    _local_to_accounting(due_local_or_accounting, date, tax_cfg.dated_engine,
                                         str(tax_cfg.dated_local_currency))
                    if isinstance(book, _DatedYearBook) else due_local_or_accounting
                )
            elif tax_cfg.accounting == "year_end" and date.month == tax_year_end_month:
                owed = book.owed(tax_year) if isinstance(book, _DatedYearBook) else book.owed()
                due_local_or_accounting = owed - book.accrued
                book.accrued = owed
                tax_due = (
                    _local_to_accounting(due_local_or_accounting, date, tax_cfg.dated_engine,
                                         str(tax_cfg.dated_local_currency))
                    if isinstance(book, _DatedYearBook) else due_local_or_accounting
                )
            elif tax_cfg.accounting == "cash":
                if date.month == 12:
                    owed = book.owed(date.year) if isinstance(book, _DatedYearBook) else book.owed()
                    due = owed - book.accrued
                    if isinstance(book, _DatedYearBook):
                        due = _local_to_accounting(
                            due, date, tax_cfg.dated_engine, str(tax_cfg.dated_local_currency)
                        )
                    deferred_cash.append((date.year + 1, due))
                    book.accrued = owed
                tax_due = sum(amt for yr, amt in deferred_cash
                              if yr == date.year and date.month == regime.payment_month)
                deferred_cash = [(yr, amt) for yr, amt in deferred_cash
                                 if not (yr == date.year and date.month == regime.payment_month)]

        costs_dollars = (spread_cost + impact_cost + borrow_cost + transaction_tax_cost) * nav
        pnl = nav * gross
        nav_next = nav + pnl - costs_dollars - tax_due
        net_ret = gross - spread_cost - impact_cost - borrow_cost - transaction_tax_cost
        tax_ret = tax_due / nav if nav > 0 else 0.0

        rows.append({
            "date": date, "gross_ret": gross, "net_ret": net_ret,
            "after_tax_ret": net_ret - tax_ret,
            "turnover": float(np.abs(dw).sum() / 2),
            "cost_spread": spread_cost, "cost_impact": impact_cost, "cost_borrow": borrow_cost,
            "cost_transaction_tax": transaction_tax_cost,
            "long_ret": long_ret, "short_ret": short_ret,
            "tax_ret": tax_ret, "tax_dollars": tax_due,
            "realised_st": realised_st / nav, "realised_lt": realised_lt / nav,
            "wash_disallowed": disallowed / nav,
            "div_received": div_received / nav, "div_paid": div_paid / nav,
            "unrealised": ledger.unrealised_total() / nav,
            "carryforward": (
                _local_to_accounting(book.carryforward, date, tax_cfg.dated_engine,
                                     str(tax_cfg.dated_local_currency))
                if isinstance(book, _DatedYearBook) else book.carryforward
            ) / nav,
            "nav": nav_next,
        })

        if date.month == tax_year_end_month:
            book.close_year(tax_year)
        if nav_next <= 0:
            break
        # rescale lots so the book keeps matching NAV after costs and tax are paid out of capital
        _rescale(ledger, nav + pnl, nav_next)
        nav = nav_next

    frame = pd.DataFrame(rows)
    if tax_cfg.liquidate_at_end and regime.taxable and not frame.empty:
        if isinstance(book, _DatedYearBook):
            frame.attrs["deferred_tax_ret"] = _deferred_tax_dated(
                ledger, book, nav, dates[-1], tax_cfg
            )
        else:
            frame.attrs["deferred_tax_ret"] = _deferred_tax(ledger, book, nav, dates[-1])
    frame.attrs["regime"] = regime.name
    frame.attrs["lot_method"] = tax_cfg.lot_method.value
    frame.attrs["accounting"] = tax_cfg.accounting
    return frame


def _qualifies(ledger: TaxLotLedger, idx, date, regime: TaxRegime) -> float:
    """Crude but stated: dividends are qualified only if the average long lot is old enough.

    The statutory test (s1(h)(11)) is per share and per ex-dividend date, which monthly data cannot
    resolve. We apply it at the position level using the holding period of the long book.
    """
    if regime.qualified_dividend_rate == regime.ordinary_dividend_rate:
        return 1.0
    days = regime.qualified_dividend_days
    total = aged = 0.0
    for permno in idx:
        for lot in ledger.lots.get(int(permno), []):
            if lot.side != 1:
                continue
            total += lot.value
            if (pd.Timestamp(date) - lot.holding_date()).days > days:
                aged += lot.value
    return (aged / total) if total > 0 else 0.0


def _rescale(ledger: TaxLotLedger, value_before: float, value_after: float) -> None:
    """Costs and tax are paid from capital; shrink the book proportionally, keeping basis ratios."""
    if value_before <= 0 or value_after <= 0:
        return
    factor = value_after / value_before
    if abs(factor - 1.0) < 1e-12:
        return
    for lots in ledger.lots.values():
        for lot in lots:
            lot.value *= factor
            lot.basis *= factor
            if lot.dated_basis_local is not None:
                lot.dated_basis_local *= factor
            if lot.statutory_reference_local is not None:
                lot.statutory_reference_local *= factor


def _accounting_to_local(amount: float, date, engine: DatedC12Patch,
                         local_currency: str) -> float:
    if engine.config.accounting_currency == local_currency:
        return float(amount)
    if engine.config.fx_provider is None:
        raise MissingDatedTaxConfiguration(
            f"point-in-time FX is required for {local_currency}->{engine.config.accounting_currency}"
        )
    rate = float(engine.config.fx_provider(
        local_currency, engine.config.accounting_currency, pd.Timestamp(date)
    ))
    if rate <= 0:
        raise ValueError("FX rate must be positive")
    return float(amount / rate)


def _local_to_accounting(amount: float, date, engine: DatedC12Patch | None,
                         local_currency: str) -> float:
    if engine is None or engine.config.accounting_currency == local_currency:
        return float(amount)
    if engine.config.fx_provider is None:
        raise MissingDatedTaxConfiguration(
            f"point-in-time FX is required for {local_currency}->{engine.config.accounting_currency}"
        )
    rate = float(engine.config.fx_provider(
        local_currency, engine.config.accounting_currency, pd.Timestamp(date)
    ))
    if rate <= 0:
        raise ValueError("FX rate must be positive")
    return float(amount * rate)


def _deferred_tax(ledger: TaxLotLedger, book: _YearBook, nav: float, last_date) -> float:
    """Tax that would be due if every open position were sold on the last day of the sample."""
    snapshot = _YearBook(book.regime)
    snapshot.carryforward = book.carryforward
    for g in ledger.liquidate(last_date):
        if g.long_term:
            snapshot.lt += g.allowed
        else:
            snapshot.st += g.allowed
    return snapshot.owed() / nav if nav > 0 else 0.0


def _deferred_tax_dated(ledger: TaxLotLedger, book: _DatedYearBook, nav: float,
                        last_date, tax_cfg: TaxConfig) -> float:
    snapshot = _DatedYearBook(book.engine, book.country, book.local_currency)
    snapshot.carry = book.carry.copy()
    snapshot.events = list(book.events)
    snapshot.dividends = list(book.dividends)
    for gain in ledger.liquidate(last_date):
        if gain.dated_event is None:
            raise MissingDatedTaxConfiguration("dated liquidation event was not produced")
        snapshot.add_event(gain.dated_event)
    tax_year = tax_cfg.dated_engine.tax_year(str(tax_cfg.dated_country), last_date)
    local_tax = snapshot.owed(tax_year)
    accounting_tax = _local_to_accounting(
        local_tax, last_date, tax_cfg.dated_engine, str(tax_cfg.dated_local_currency)
    )
    return accounting_tax / nav if nav > 0 else 0.0


def summarise_after_tax(frame: pd.DataFrame, periods: int = 12) -> dict:
    """Headline numbers. Every Sharpe here is computed on the same NAV series that pays the tax."""
    ann = np.sqrt(periods)

    def sharpe(x: pd.Series) -> float:
        sd = x.std(ddof=1)
        return float(x.mean() / sd * ann) if sd > 0 else float("nan")

    gross, net = frame["gross_ret"], frame["net_ret"]
    after = frame["after_tax_ret"]
    cum = (1 + after).cumprod()
    dd = float((cum / cum.cummax() - 1).min())
    deferred = float(frame.attrs.get("deferred_tax_ret", 0.0))
    years = len(frame) / periods
    out = {
        "months": int(len(frame)),
        "regime": frame.attrs.get("regime", "unknown"),
        "lot_method": frame.attrs.get("lot_method", "unknown"),
        "gross_sharpe": sharpe(gross),
        "net_sharpe": sharpe(net),
        "after_tax_sharpe": sharpe(after),
        "gross_mean_ann": float(gross.mean() * periods),
        "net_mean_ann": float(net.mean() * periods),
        "after_tax_mean_ann": float(after.mean() * periods),
        "vol_ann": float(after.std(ddof=1) * ann),
        "max_drawdown": dd,
        "turnover_mean": float(frame["turnover"].mean()),
        "cost_drag_ann_bps": float((gross.mean() - net.mean()) * periods * 10_000),
        "tax_drag_ann_bps": float(frame["tax_ret"].mean() * periods * 10_000),
        "total_drag_ann_bps": float((gross.mean() - after.mean()) * periods * 10_000),
        "wash_disallowed_ann_bps": float(frame["wash_disallowed"].mean() * periods * 10_000),
        "realised_st_ann": float(frame["realised_st"].mean() * periods),
        "realised_lt_ann": float(frame["realised_lt"].mean() * periods),
        "lt_share_of_gains": _lt_share(frame),
        "deferred_tax_ret": deferred,
        "after_tax_liq_mean_ann": float(after.mean() * periods - deferred / max(years, 1e-9)),
        "terminal_nav_multiple": float(frame["nav"].iloc[-1] / frame["nav"].iloc[0]) if len(frame) else float("nan"),
    }
    out["tax_share_of_gross"] = (out["tax_drag_ann_bps"] / (out["gross_mean_ann"] * 10_000)
                                 if out["gross_mean_ann"] > 0 else float("nan"))
    return out


def _lt_share(frame: pd.DataFrame) -> float:
    st = frame["realised_st"].clip(lower=0).sum()
    lt = frame["realised_lt"].clip(lower=0).sum()
    return float(lt / (st + lt)) if (st + lt) > 0 else float("nan")


def compare_regimes(weights: pd.DataFrame, bundle, cfg: dict, regimes=("tax_exempt", "taxable_us_top_bracket",
                    "trader_475f_mtm"), lot_methods=(LotMethod.HIFO,), **kwargs) -> pd.DataFrame:
    """The table the paper needs: the same strategy seen by investors with different tax status."""
    rows = []
    for regime in regimes:
        for method in lot_methods:
            tc = TaxConfig(regime=get_regime(regime), lot_method=method, **kwargs)
            frame = after_tax_backtest(weights, bundle, cfg, tc)
            rows.append(summarise_after_tax(frame))
    return pd.DataFrame(rows)
