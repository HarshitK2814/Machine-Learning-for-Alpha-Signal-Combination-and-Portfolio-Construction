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

from ..portfolio.cost_terms import cost_inputs_for, trade_cost_numpy
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

    @staticmethod
    def of(regime: str | TaxRegime, **kwargs) -> "TaxConfig":
        return TaxConfig(regime=get_regime(regime), **kwargs)


class _YearBook:
    """Running within-year tax computation, so monthly accrual and annual settlement agree."""

    def __init__(self, regime: TaxRegime):
        self.regime = regime
        self.reset()
        self.carryforward = 0.0      # positive number = losses available to offset future gains
        self._vintages: list[list[float]] = []   # [[year, amount], ...] for expiry accounting
        self._year = 0

    def reset(self) -> None:
        self.st = 0.0
        self.lt = 0.0
        self.div_qualified = 0.0
        self.div_ordinary = 0.0
        self.short_div_paid = 0.0
        self.accrued = 0.0           # tax already debited this year

    def owed(self) -> float:
        """Tax owed on the year to date, before anything already accrued."""
        r = self.regime
        st, lt = self.st, self.lt
        loss = self.carryforward
        if loss > 0:                                   # s1212(b): carryforward offsets gains
            take = min(loss, max(st, 0.0))
            st -= take
            loss -= take
            take = min(loss, max(lt, 0.0))
            lt -= take
        if st < 0 and lt > 0:                          # s1222(11): net across character
            offset = min(-st, lt)
            st += offset
            lt -= offset
        elif lt < 0 and st > 0:
            offset = min(-lt, st)
            lt += offset
            st -= offset
        gains_tax = max(st, 0.0) * r.short_term_rate + max(lt, 0.0) * r.long_term_rate
        net_loss = -(min(st, 0.0) + min(lt, 0.0))
        if net_loss > 0:                               # s1211(b): limited ordinary offset
            allowed = min(net_loss, r.annual_ordinary_offset)
            gains_tax -= allowed * r.short_term_rate
        div_tax = (self.div_qualified * r.qualified_dividend_rate
                   + self.div_ordinary * r.ordinary_dividend_rate)
        if not r.short_dividend_deductible:
            deduction = 0.0
        else:
            deduction = self.short_div_paid * r.ordinary_dividend_rate
        return gains_tax + div_tax - deduction

    def close_year(self, year: int | None = None) -> None:
        """Roll unusable losses into the carryforward, expire old vintages, start a fresh year.

        Carryforward life matters more than it looks. A strategy that harvests aggressively builds
        a loss balance that shelters its embedded gains later, which is what makes the "hidden
        deferred liability" criticism of tax-aware long/short weaker than it appears - but only
        where the balance survives. The US allows indefinite carryforward; Japan allows three years.
        Under a short life the shelter evaporates and the liability is real.
        """
        r = self.regime
        if year is not None:
            self._year = year
        total = self.st + self.lt - self.carryforward
        if total < 0:
            usable = min(-total, r.annual_ordinary_offset)
            fresh = (-total - usable) if r.loss_carryforward else 0.0
            self._vintages = [[self._year, fresh]] if fresh > 0 else []
        else:
            # gains absorbed the balance, oldest vintages first
            absorbed = self.carryforward
            for v in self._vintages:
                take = min(v[1], absorbed)
                v[1] -= take
                absorbed -= take
            self._vintages = [v for v in self._vintages if v[1] > 1e-12]

        life = getattr(r, "carryforward_years", float("inf"))
        if life != float("inf"):
            self._vintages = [v for v in self._vintages if self._year - v[0] < life]
        self.carryforward = float(sum(v[1] for v in self._vintages))
        self.reset()


def after_tax_backtest(weights: pd.DataFrame, bundle, cfg: dict, tax_cfg: TaxConfig | None = None,
                       cost_multiplier: float = 1.0) -> pd.DataFrame:
    """Run one strategy's weights through costs and tax. Returns an extended contract-C12 table."""
    tax_cfg = tax_cfg or TaxConfig()
    regime = tax_cfg.regime
    costs_cfg = cfg["costs"]
    aum = float(costs_cfg["aum_usd_2020"])
    k = float(costs_cfg["impact_k"]) * cost_multiplier
    commission = float(costs_cfg["commission_bps"])

    returns = bundle.targets.set_index(["date", "permno"])["ret_next"]
    div_col = "div_next" if "div_next" in bundle.targets.columns else None
    if div_col:
        dividends = bundle.targets.set_index(["date", "permno"])[div_col]
    monthly_div = tax_cfg.dividend_yield_annual / 12.0

    ledger = TaxLotLedger(regime, tax_cfg.lot_method)
    book = _YearBook(regime)
    nav = float(tax_cfg.initial_nav)
    deferred_cash: list[tuple[int, float]] = []   # (year owed, amount) for cash-basis accounting

    rows = []
    dates = sorted(weights["date"].unique())
    for i, date in enumerate(dates):
        date = pd.Timestamp(date)
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
                if g.long_term:
                    realised_lt += g.allowed
                else:
                    realised_st += g.allowed
                disallowed += g.disallowed
        book.st += realised_st
        book.lt += realised_lt

        # ---- trading costs ----------------------------------------------------------------
        ci = cost_inputs_for(date, bundle.cost_inputs, idx)
        dw = (w_full - prev_w).to_numpy()
        spread_arr = ci["spread"].to_numpy() * cost_multiplier
        spread_cost = float((0.5 * spread_arr * np.abs(dw)).sum() + commission / 10_000.0 * np.abs(dw).sum())
        total_trade = float(trade_cost_numpy(dw, spread_arr, ci["sigma_d"].to_numpy(),
                                             ci["adv_usd"].to_numpy(), aum, k, commission).sum())
        impact_cost = max(total_trade - spread_cost, 0.0)
        borrow_cost = float((ci["borrow_fee"].to_numpy() / 12.0
                             * np.clip(-w_full.to_numpy(), 0, None)).sum())

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
        book.div_qualified += qualified
        book.div_ordinary += div_received - qualified
        book.short_div_paid += div_paid

        ledger.accrue_returns(r - q)   # price return only; the dividend already came out as cash

        # ---- tax accrual --------------------------------------------------------------------
        if regime.mark_to_market and date.month == 12:
            book.st += ledger.mark_to_market(date)
        tax_due = 0.0
        if regime.taxable:
            if tax_cfg.accounting == "accrual":
                owed = book.owed()
                tax_due = owed - book.accrued
                book.accrued = owed
            elif tax_cfg.accounting == "year_end" and date.month == 12:
                tax_due = book.owed() - book.accrued
                book.accrued = book.owed()
            elif tax_cfg.accounting == "cash":
                if date.month == 12:
                    deferred_cash.append((date.year + 1, book.owed() - book.accrued))
                    book.accrued = book.owed()
                tax_due = sum(amt for yr, amt in deferred_cash
                              if yr == date.year and date.month == regime.payment_month)
                deferred_cash = [(yr, amt) for yr, amt in deferred_cash
                                 if not (yr == date.year and date.month == regime.payment_month)]

        costs_dollars = (spread_cost + impact_cost + borrow_cost) * nav
        pnl = nav * gross
        nav_next = nav + pnl - costs_dollars - tax_due
        net_ret = gross - spread_cost - impact_cost - borrow_cost
        tax_ret = tax_due / nav if nav > 0 else 0.0

        rows.append({
            "date": date, "gross_ret": gross, "net_ret": net_ret,
            "after_tax_ret": net_ret - tax_ret,
            "turnover": float(np.abs(dw).sum() / 2),
            "cost_spread": spread_cost, "cost_impact": impact_cost, "cost_borrow": borrow_cost,
            "long_ret": long_ret, "short_ret": short_ret,
            "tax_ret": tax_ret, "tax_dollars": tax_due,
            "realised_st": realised_st / nav, "realised_lt": realised_lt / nav,
            "wash_disallowed": disallowed / nav,
            "div_received": div_received / nav, "div_paid": div_paid / nav,
            "unrealised": ledger.unrealised_total() / nav,
            "carryforward": book.carryforward / nav,
            "nav": nav_next,
        })

        if date.month == 12:
            book.close_year(date.year)
        if nav_next <= 0:
            break
        # rescale lots so the book keeps matching NAV after costs and tax are paid out of capital
        _rescale(ledger, nav + pnl, nav_next)
        nav = nav_next

    frame = pd.DataFrame(rows)
    if tax_cfg.liquidate_at_end and regime.taxable and not frame.empty:
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
