#!/usr/bin/env python
"""Stage 06 (workstream B): what does the investor actually keep?

Runs every strategy that has weights through the after-tax ledger under each investor regime and
each lot-selection method, and writes one table. The tax-exempt row is the control: it reproduces
the net-of-cost number the rest of the literature reports, so the distance between that row and the
others is the size of the thing the literature leaves out.

    python pipelines/06_after_tax_eval.py
    python pipelines/06_after_tax_eval.py --strategies cell_N-C-P-0 --regimes taxable_us_top_bracket
    python pipelines/06_after_tax_eval.py --lot-methods hifo fifo tax_optimal --dividend-yield 0.03
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alphacomb.contracts import load_bundle, load_config, new_run_id, paths, read_table, write_table  # noqa: E402
from alphacomb.tax import LotMethod, TaxConfig, after_tax_backtest, get_regime, summarise_after_tax  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
log = logging.getLogger("stage06")

# Jurisdiction of listing, which is what the dated schedule and the FX cache are keyed on.
LOCAL_CURRENCY = {"DEU": "EUR", "IND": "INR", "JPN": "JPY"}

REPORT_COLUMNS = [
    "strategy", "country", "wedge", "dated", "held_share", "regime", "lot_method", "months", "gross_sharpe", "net_sharpe", "after_tax_sharpe",
    "gross_mean_ann", "net_mean_ann", "after_tax_mean_ann", "after_tax_liq_mean_ann",
    "cost_drag_ann_bps", "tax_drag_ann_bps", "total_drag_ann_bps", "tax_share_of_gross",
    "wash_disallowed_ann_bps", "lt_share_of_gains", "turnover_mean", "max_drawdown",
    "deferred_tax_ret", "terminal_nav_multiple",
]


def construction_quality() -> pd.DataFrame:
    """Held-weight share per strategy, from the portfolio manifest.

    A month that fell back to held weights is last month's book, not this month's model. Carrying
    the share into every results row means a reader never has to take on trust that the optimiser
    succeeded - and never compares a stale cell with a clean one without seeing it.
    See docs/SILENT_OPTIMISER_FAILURE.md.
    """
    path = paths.outputs_root() / "manifest_portfolios.csv"
    if not path.exists():
        return pd.DataFrame(columns=["strategy", "held_share"])
    try:
        frame = pd.read_csv(path)
    except pd.errors.ParserError:
        log.warning("manifest_portfolios.csv is damaged by header drift; construction quality "
                    "unavailable. Re-run stage 04 to regenerate it.")
        return pd.DataFrame(columns=["strategy", "held_share"])
    if "held_share" not in frame.columns:
        return pd.DataFrame(columns=["strategy", "held_share"])
    latest = frame.dropna(subset=["held_share"]).groupby("strategy").tail(1)
    return latest[["strategy", "held_share"]].reset_index(drop=True)


def main() -> None:
    p = argparse.ArgumentParser(description="After-tax evaluation of every strategy (stage 06).")
    p.add_argument("--strategies", nargs="+", default=["all"])
    p.add_argument("--data", default=None)
    p.add_argument("--country", default=None, choices=["DEU", "IND", "JPN"],
                   help="evaluate the promoted international panel for one country. Implies the "
                        "statutory regime in force there unless --regimes is given explicitly.")
    p.add_argument("--as-of", default="2016-06-30",
                   help="date at which the statutory regime is resolved for --country. The default "
                        "sits inside the frozen mechanism subwindow 2014-01-01..2018-03-31, where "
                        "all three countries are on a single constant-rate rule.")
    p.add_argument("--regimes", nargs="+", default=None,
                   help="investor regimes. Defaults to the statutory regime for --country, or to "
                        "the four US investor types when no country is given.")
    p.add_argument("--lot-methods", nargs="+", default=["hifo"],
                   choices=[m.value for m in LotMethod])
    p.add_argument("--accounting", default="accrual", choices=["accrual", "year_end", "cash"])
    p.add_argument("--dividend-yield", type=float, default=0.02)
    p.add_argument("--cost-multiplier", type=float, default=1.0)
    p.add_argument("--aum", type=float, default=None, help="override AUM (cost and impact scale)")
    p.add_argument("--max-names", type=int, default=None,
                   help="cap each month to the N largest names by market cap (amendment 001B; slack for DEU/IND, binds on JPN)")
    p.add_argument("--weights-aum", default=None,
                   help="resolve weights through outputs/weights_index/<COUNTRY>_<this>.csv "
                        "instead of by modification time. Stage 06 reads outputs/weights/, which "
                        "is shared across countries and AUM arms, so without this it silently "
                        "evaluates whichever arm ran stage 04 most recently.")
    p.add_argument("--out", default=None,
                   help="where to write the summary. Defaults to outputs/summary_after_tax.csv, "
                        "which is a FIXED path: concurrent runs overwrite each other, so pass this "
                        "whenever sweeping AUM or country in parallel")
    p.add_argument("--save-returns", action="store_true", help="write the full monthly C12 tables")
    p.add_argument("--dated", action="store_true",
                   help="resolve the tax rule on each event's own date through the frozen C14 "
                        "dated engine instead of holding one statutory regime fixed. Requires "
                        "--country and forces year_end accounting (frozen decision 3A). This is "
                        "what makes India's section 112A change visible inside the sample.")
    a = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config("base")
    if a.aum is not None:
        cfg = {**cfg, "costs": {**cfg["costs"], "aum_usd_2020": a.aum}}
    regimes: list = a.regimes or ["tax_exempt", "taxable_us_top_bracket", "trader_475f_mtm",
                                  "offshore_fund"]
    if a.country:
        from alphacomb.contracts import intl
        bundle = intl.load_country_bundle(a.country, max_names=a.max_names)
        if a.regimes is None:
            # The paper's treatment variable is the statutory holding-period wedge, so the default
            # regime for a country run is the one its own law specifies, derived from the frozen
            # C14 schedule rather than hardcoded. tax_exempt is kept alongside it as the zero-tax
            # control that reproduces the net-of-cost number the literature reports.
            from alphacomb.tax.statutory import statutory_regime
            statutory = statutory_regime(a.country, a.as_of)
            regimes = ["tax_exempt", statutory]
            log.info("%s statutory regime at %s: %s  short=%.5f long=%.5f WEDGE=%.5f boundary=%sm",
                     a.country, a.as_of, statutory.name, statutory.short_term_rate,
                     statutory.long_term_rate, statutory.rate_spread, statutory.long_term_months)
        log.info("international bundle %s: %d security-months", a.country, len(bundle.universe))
    else:
        bundle = load_bundle(a.data or cfg["data_source"])

    dated_engine = None
    dated_currency = None
    if a.dated:
        if not a.country:
            raise SystemExit("--dated requires --country; the dated engine resolves by jurisdiction")
        if a.accounting != "year_end":
            # The engine refuses anything else, and silently rewriting the user's choice would
            # hide which accounting convention produced the numbers.
            raise SystemExit("--dated requires --accounting year_end (frozen decision 3A)")
        from alphacomb.tax.dated import DatedC12Patch

        dated_engine = DatedC12Patch.from_frozen_evaluation_artifacts(ROOT)
        dated_currency = LOCAL_CURRENCY[a.country]
        window = ("2009-01-01", "2019-12-31")
        coverage = dated_engine.schedule.validate(*window)
        log.info("dated C14 engine: %s rules cover %s..%s, currency %s",
                 coverage, window[0], window[1], dated_currency)
        for probe in ("2018-03-31", "2018-04-01"):
            rule = dated_engine.schedule.resolve(a.country, probe)
            log.info("  %s rule in force on %s: %s short=%s long=%s boundary=%sm transition=%s",
                     a.country, probe, rule.legal_regime, rule.cgt_short, rule.cgt_long,
                     rule.holding_period_months, rule.transition_rule)

    root = paths.outputs_root() / "weights"
    if not root.exists():
        raise SystemExit("no weights found; run pipelines/04_construct_portfolios.py first")
    wanted = None if a.strategies == ["all"] else set(a.strategies)
    pinned: dict[str, Path] = {}
    if a.weights_aum:
        from alphacomb.contracts import provenance

        if not a.country:
            raise SystemExit("--weights-aum requires --country")
        pinned = provenance.country_weights(a.country, a.weights_aum)
        log.info("weights pinned via weights_index/%s_%s.csv: %d strategies",
                 a.country, a.weights_aum, len(pinned))
    elif a.country:
        log.warning("resolving weights by MODIFICATION TIME. outputs/weights/ is shared across "
                    "countries and AUM arms, so if any other arm has run stage 04 since %s's, "
                    "these numbers describe that arm. Pass --weights-aum to pin them.", a.country)

    rows = []
    names = sorted(pinned) if pinned else [f.name for f in sorted(root.iterdir())]
    for name in names:
        if wanted and name not in wanted:
            continue
        latest = pinned.get(name) if pinned else paths.latest_run("weights", name)
        if latest is None:
            continue
        folder = root / name
        weights = read_table(latest, "weights")
        for regime_name in regimes:
            for method_name in a.lot_methods:
                tc = TaxConfig(regime=get_regime(regime_name), lot_method=LotMethod(method_name),
                               accounting=a.accounting, dividend_yield_annual=a.dividend_yield,
                               initial_nav=float(cfg["costs"]["aum_usd_2020"]),
                               **({} if dated_engine is None or regime_name == "tax_exempt" else
                                  {"dated_engine": dated_engine, "dated_country": a.country,
                                   "dated_local_currency": dated_currency}))
                frame = after_tax_backtest(weights, bundle, cfg, tc, a.cost_multiplier)
                summary = {"strategy": folder.name, **summarise_after_tax(frame)}
                rows.append(summary)
                reg = get_regime(regime_name)
                summary["regime"] = reg.name
                summary["wedge"] = reg.rate_spread
                # In a dated run the wedge is a function of time, not a scalar, so publishing the
                # as-of value in this column would invite exactly the misreading the dated engine
                # exists to prevent.
                summary["dated"] = bool(dated_engine is not None and regime_name != "tax_exempt")
                if summary["dated"]:
                    summary["wedge"] = float("nan")
                summary["country"] = a.country or ""
                log.info("%s | %s | %s: after-tax Sharpe %.3f, tax drag %.0f bps, "
                         "lt_share %.3f, wedge %.5f",
                         folder.name, reg.name, method_name, summary["after_tax_sharpe"],
                         summary["tax_drag_ann_bps"], summary.get("lt_share_of_gains", float("nan")),
                         reg.rate_spread)
                if a.save_returns:
                    run_id = new_run_id(f"tax_{folder.name}_{regime_name}_{method_name}")
                    write_table(frame, paths.returns_path(folder.name, run_id), "returns")

    report = pd.DataFrame(rows)
    quality = construction_quality()
    report = report.merge(quality, on="strategy", how="left")
    report = report[[c for c in REPORT_COLUMNS if c in report.columns]]
    stale = report.loc[report["held_share"].fillna(0) > 0.02, "strategy"].unique()
    if len(stale):
        log.warning("STALE: %s fell back to held weights on more than 2%% of months. Their rows "
                    "below describe a drifting portfolio, not the model.", ", ".join(sorted(stale)))
    unknown = report.loc[report["held_share"].isna(), "strategy"].unique()
    if len(unknown):
        log.warning("held_share unknown for %s - manifest predates the check; re-run stage 04 "
                    "before reporting these.", ", ".join(sorted(unknown)))
    # A FIXED output path means two concurrent invocations - say the same country at two AUMs -
    # silently overwrite each other, and the survivor is whichever finished last. That happened on
    # 2026-10-09 with DEU at 1e8 and 1e10. --out exists so a sweep can keep its runs apart.
    out = Path(a.out) if a.out else paths.outputs_root() / "summary_after_tax.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(out, index=False)
    pd.set_option("display.width", 250)
    print(report.round(4).to_string(index=False))
    print(f"\nreport: {out}")
    _print_headline(report)


def _print_headline(report: pd.DataFrame) -> None:
    """The one comparison a referee will look for first."""
    if report.empty or "regime" not in report:
        return
    exempt = report[report["regime"] == "tax_exempt"]
    taxable = report[report["regime"] == "taxable_us_top_bracket"]
    if exempt.empty or taxable.empty:
        return
    print("\nHeadline: what the tax-exempt literature reports vs what a taxable investor keeps")
    for strategy in sorted(set(exempt["strategy"]) & set(taxable["strategy"])):
        e = exempt[exempt["strategy"] == strategy].iloc[0]
        t = taxable[taxable["strategy"] == strategy].iloc[0]
        print(f"  {strategy:<20} net Sharpe {e['net_sharpe']:.3f}  ->  after-tax Sharpe "
              f"{t['after_tax_sharpe']:.3f}  ({t['tax_drag_ann_bps']:.0f} bps of tax)")


if __name__ == "__main__":
    main()
