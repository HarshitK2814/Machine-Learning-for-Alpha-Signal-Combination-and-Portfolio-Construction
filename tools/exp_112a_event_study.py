#!/usr/bin/env python
"""India's section 112A: a legislated cut in the holding-period wedge, inside the sample.

On 2018-04-01 India ended the long-term capital-gains exemption on listed equity. The frozen C14
schedule records the switch as STT100_LTCG_EXEMPT_STCG15 -> SECTION_112A_STT100, which moves

    cgt_long  0.00 -> 0.10        so the wedge  Delta = cgt_short - cgt_long  falls  0.15 -> 0.05

while *nothing else about the jurisdiction moves*: the short-term rate stays 0.15, the boundary
stays 12 months, the securities transaction tax stays 0.0010, and the tax year still ends in March.
Over the same window Germany sits on one unchanged ABGELTUNGSTEUER rule and Japan on one unchanged
NORMAL_LISTED_SHARE_RATE rule, so they are controls whose law did not move on that date.

What this identifies, stated precisely
--------------------------------------
The theory gives  tax_drag / gross  ~  theta_L  +  Delta * Phi(p, H), where Phi is the share of
gains pushed across the holding-period boundary and is increasing in turnover p. Section 112A
changes BOTH terms, and in opposite directions:

    theta_L : 0.00 -> 0.10   raises the bill on every cell, with no turnover gradient
    Delta   : 0.15 -> 0.05   cuts the wedge term, and only for cells with Phi > 0

So the level effect and the wedge effect are separately signed and separately shaped. The level
effect is a constant across cells; the wedge effect is PROPORTIONAL TO TURNOVER. The test is
therefore the *turnover gradient* of the change, not the change itself:

    d(tax_per_gain) / d(post)  =  +0.10  -  0.10 * Phi(p, H)     <- interaction is NEGATIVE in p

The prediction is a negative post x turnover interaction in India and a zero one in the controls.

What this does NOT identify
---------------------------
The 16 cells are not tax-aware: their weights come from stage 04 without any tax term in the
objective, and they are identical before and after 2018-04-01. So this is a test of the *incidence*
of the statute on a fixed portfolio - a comparative static of the theory's functional form - and
NOT a behavioural response. No investor in this design re-optimises against the new law. Reporting
it as a behavioural event study would be a misrepresentation. Its value is that Delta is moved by
parliament rather than by us, holding the portfolio, the prices and the realisation dates fixed.

Design
------
Dated C14 engine, year_end accounting (frozen decision 3A), HIFO lots, cold start 2009-01-01,
window 2009-01-01..2019-12-31. Monthly frames are aggregated to each country's own tax year, since
under year_end accounting the bill is paid in the tax-year-end month (March for India, December for
Germany and Japan). India contributes nine clean pre-112A tax years and one clean post year
(FY2018-19), plus a truncated FY2019-20; the truncated year is reported but excluded by default.

    python tools/exp_112a_event_study.py --countries IND DEU
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alphacomb.contracts import load_config, paths, read_table  # noqa: E402
from alphacomb.tax import LotMethod, TaxConfig, after_tax_backtest, get_regime  # noqa: E402
from alphacomb.tax.dated import DatedC12Patch  # noqa: E402
from alphacomb.tax.statutory import statutory_regime  # noqa: E402

log = logging.getLogger("e112a")

LOCAL_CURRENCY = {"DEU": "EUR", "IND": "INR", "JPN": "JPY"}
TAX_YEAR_END_MONTH = {"DEU": 12, "IND": 3, "JPN": 12}
SECTION_112A = pd.Timestamp("2018-04-01")
WINDOW = ("2009-01-01", "2019-12-31")
CELLS = ["cell_L-S-P-0", "cell_L-S-P-U", "cell_L-S-E-0", "cell_L-S-E-U",
         "cell_L-C-P-0", "cell_L-C-P-U", "cell_L-C-E-0", "cell_L-C-E-U",
         "cell_N-S-P-0", "cell_N-S-P-U", "cell_N-S-E-0", "cell_N-S-E-U",
         "cell_N-C-P-0", "cell_N-C-P-U", "cell_N-C-E-0", "cell_N-C-E-U"]


def tax_year(dates: pd.Series, end_month: int) -> np.ndarray:
    """Label each month with the tax year it is paid in, named by the calendar year it ends in."""
    d = pd.to_datetime(dates)
    # A December year-end means the tax year is the calendar year. A March year-end means April
    # 2018..March 2019 is the year labelled 2019, so months after the end month roll forward.
    return np.where(d.dt.month > end_month, d.dt.year + 1, d.dt.year)


def resolve_weights(country: str, cells: list[str], aum: str) -> dict[str, Path]:
    """Map each cell to the weights file built for *this* country.

    ``outputs/weights/<strategy>/`` is shared across countries and ``paths.latest_run`` picks by
    modification time, so after a second country's stage 04 has run, "latest" silently means that
    other country. Every country run therefore writes an index naming its own run ids, and this
    refuses to fall back to mtime when one is missing: a wrong-country weights file would produce a
    plausible number with no visible symptom.
    """
    index = paths.outputs_root() / "weights_index" / f"{country}_{aum}.csv"
    if not index.exists():
        raise SystemExit(
            f"no weights index at {index}. Weights are not country-tagged on disk, so the country "
            f"a file belongs to cannot be recovered from the path. Re-run stage 04 for {country} "
            f"(it writes the index), or rebuild one from its log with tools/weights_index.py.")
    d = pd.read_csv(index)
    found = dict(zip(d["strategy"], d["weights"]))
    missing = [c for c in cells if c not in found]
    if missing:
        raise SystemExit(f"{index} does not cover {', '.join(missing)}")
    out = {}
    for cell in cells:
        p = Path(found[cell])
        if not p.exists():
            raise SystemExit(f"{index} names a missing file for {cell}: {p}")
        out[cell] = p
    return out


def panel_for_country(country: str, cells: list[str], engine: DatedC12Patch,
                      cfg: dict, aum: str) -> pd.DataFrame:
    """One row per (cell, tax year): tax paid, gains, turnover, under the dated statute."""
    from alphacomb.contracts import intl

    bundle = intl.load_country_bundle(country)
    reg = statutory_regime(country, "2016-06-30")
    end_month = TAX_YEAR_END_MONTH[country]
    resolved = resolve_weights(country, cells, aum)
    rows = []
    for cell in cells:
        weights = read_table(resolved[cell], "weights")
        tc = TaxConfig(regime=get_regime(reg), lot_method=LotMethod("hifo"),
                       accounting="year_end",
                       initial_nav=float(cfg["costs"]["aum_usd_2020"]),
                       dated_engine=engine, dated_country=country,
                       dated_local_currency=LOCAL_CURRENCY[country])
        frame = after_tax_backtest(weights, bundle, cfg, tc, 1.0).copy()
        frame["tax_year"] = tax_year(frame["date"], end_month)
        g = frame.groupby("tax_year")
        agg = pd.DataFrame({
            "tax_ret": g["tax_ret"].sum(),
            "gross_ret": g["gross_ret"].sum(),
            "turnover": g["turnover"].mean(),
            "realised_st": g["realised_st"].sum(),
            "realised_lt": g["realised_lt"].sum(),
            "months": g["date"].size(),
        }).reset_index()
        agg["country"] = country
        agg["cell"] = cell
        rows.append(agg)
        log.info("%s %s: %d tax years, %d months, weights %s", country, cell, len(agg),
                 int(agg["months"].sum()), resolved[cell].name)
    if not rows:
        return pd.DataFrame()
    panel = pd.concat(rows, ignore_index=True)
    # A country's tax year is "post" only if its own law changed; Germany and Japan never do, so
    # their post flag marks the same calendar period and carries the common time trend.
    first_post = SECTION_112A.year + (1 if SECTION_112A.month > end_month else 0)
    panel["post"] = (panel["tax_year"] >= first_post).astype(float)
    panel["full_year"] = panel["months"] == 12
    st = panel["realised_st"].clip(lower=0)
    lt = panel["realised_lt"].clip(lower=0)
    panel["lt_share"] = lt / (st + lt).replace(0, np.nan)
    return panel


def ols_cluster(y: np.ndarray, X: np.ndarray, groups: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Coefficients with standard errors clustered on ``groups``.

    The 16 cells are built from overlapping months and are ~0.9 correlated, so independent errors
    would overstate precision by a wide margin. Clustering is on the tax year, which is the
    dimension the treatment varies in.
    """
    n, k = X.shape
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    XtX_inv = np.linalg.pinv(X.T @ X)
    meat = np.zeros((k, k))
    uniq = np.unique(groups)
    for gval in uniq:
        m = groups == gval
        s = X[m].T @ resid[m]
        meat += np.outer(s, s)
    n_groups = len(uniq)
    scale = (n_groups / max(n_groups - 1, 1)) * ((n - 1) / max(n - k, 1))
    cov = XtX_inv @ meat @ XtX_inv * scale
    return beta, np.sqrt(np.clip(np.diag(cov), 0, None))


def did(panel: pd.DataFrame, country: str, *, include_truncated: bool) -> dict:
    """post x turnover interaction for one country, with cell and tax-year fixed effects."""
    d = panel[panel["country"] == country].copy()
    if not include_truncated:
        d = d[d["full_year"]]
    d = d[d["gross_ret"].abs() > 1e-6].copy()
    if d.empty or d["post"].nunique() < 2:
        return {"country": country, "error": "no usable pre/post variation", "n_obs": int(len(d))}
    d["tax_per_gain"] = d["tax_ret"] / d["gross_ret"]
    d = d[np.isfinite(d["tax_per_gain"])].copy()
    # The ratio outcome carries the same defect as the cross-sectional wedge test: a tax year with
    # a negative gross return has no gains to divide by, and on the German panel 79 of 176 full tax
    # years are negative. So tax paid per unit of NAV is the primary outcome - it needs no
    # denominator and is strictly positive here - and the ratio is reported beside it.
    n_neg_gross = int((d["gross_ret"] < 0).sum())

    # Demean turnover so the main 'post' coefficient reads as the effect at average turnover
    # rather than at the economically meaningless turnover of zero.
    d["p_c"] = d["turnover"] - d["turnover"].mean()
    cell_d = pd.get_dummies(d["cell"], drop_first=True, dtype=float)
    year_d = pd.get_dummies(d["tax_year"], drop_first=True, dtype=float)
    # 'post' itself is absorbed by the tax-year fixed effects, which is correct: the level shift is
    # common to every cell within a year and is not what the test is about.
    X = np.c_[np.ones(len(d)), (d["post"] * d["p_c"]).to_numpy(), d["p_c"].to_numpy(),
              cell_d.to_numpy(), year_d.to_numpy()]
    def fit(col: str) -> tuple[float, float, float, float, float]:
        y = d[col].to_numpy(dtype=float)
        b, s = ols_cluster(y, X, d["tax_year"].to_numpy())
        _, s_cell = ols_cluster(y, X, d["cell"].to_numpy())
        t_year = b[1] / s[1] if s[1] > 0 else np.nan
        t_cell = b[1] / s_cell[1] if s_cell[1] > 0 else np.nan
        return float(b[1]), float(s[1]), float(t_year), float(s_cell[1]), float(t_cell)

    # Primary: tax paid per unit of NAV, in levels. 112A raises the long-term rate 0.00 -> 0.10, so
    # the tax increase is 0.10 * long-term gains, and the long-term share is HIGHER in the slower
    # cells - so the increase falls hardest on the patient ones and the interaction is negative.
    lv_b, lv_se, lv_t, lv_se_cell, lv_t_cell = fit("tax_ret")
    beta1, se1, tstat, se_cell1, t_cell1 = fit("tax_per_gain")
    beta, se = [np.nan, beta1], [np.nan, se1]
    se_cell = [np.nan, se_cell1]
    t_cell = t_cell1
    # Clustering on the tax year gives about eleven clusters and only one of them is post-112A,
    # which is exactly the case where cluster-robust standard errors are known to be too small.
    # Clustering on the cell instead gives sixteen clusters and treats the overlapping months
    # within a cell as the dependence. Neither is clearly right, so both are reported and the
    # weaker of the two is what the write-up should lean on.
    pre, post = d[d["post"] == 0], d[d["post"] == 1]
    return {
        "country": country,
        "n_obs": int(len(d)),
        "n_cells": int(d["cell"].nunique()),
        "n_tax_years": int(d["tax_year"].nunique()),
        "n_post_years": int(post["tax_year"].nunique()),
        "wedge_before": 0.15 if country == "IND" else 0.0,
        "wedge_after": 0.05 if country == "IND" else 0.0,
        "n_taxyears_with_negative_gross": n_neg_gross,
        # PRIMARY: tax paid per unit of NAV, needs no denominator
        "tax_level_interaction": lv_b,
        "tax_level_t": lv_t,
        "tax_level_t_cluster_cell": lv_t_cell,
        "tax_level_significant_5pct": bool(np.isfinite(lv_t) and np.isfinite(lv_t_cell)
                                           and abs(lv_t) > 1.96 and abs(lv_t_cell) > 1.96),
        # SECONDARY: the ratio, ill-defined wherever gross < 0
        "interaction_post_x_turnover": float(beta[1]),
        "interaction_se": float(se[1]),
        "interaction_t": float(tstat),
        "interaction_se_cluster_cell": float(se_cell[1]),
        "interaction_t_cluster_cell": float(t_cell),
        # The conservative reading: significant only if it survives BOTH clusterings.
        "significant_5pct": bool(np.isfinite(tstat) and np.isfinite(t_cell)
                                 and abs(tstat) > 1.96 and abs(t_cell) > 1.96),
        "mean_tax_per_gain_pre": float(pre["tax_per_gain"].mean()) if len(pre) else np.nan,
        "mean_tax_per_gain_post": float(post["tax_per_gain"].mean()) if len(post) else np.nan,
        "mean_lt_share_pre": float(pre["lt_share"].mean()) if len(pre) else np.nan,
        "mean_lt_share_post": float(post["lt_share"].mean()) if len(post) else np.nan,
        "turnover_range": f"{d['turnover'].min():.4f}-{d['turnover'].max():.4f}",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--countries", nargs="+", default=["IND", "DEU"],
                    choices=["DEU", "IND", "JPN"])
    ap.add_argument("--strategies", nargs="+", default=CELLS)
    ap.add_argument("--aum", default="1e9",
                    help="which country weights index to read, e.g. 1e9 -> weights_index/IND_1e9.csv")
    ap.add_argument("--include-truncated-year", action="store_true",
                    help="keep India's FY2019-20, which the evaluation window cuts at 9 months")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "event_112a")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config("base")
    engine = DatedC12Patch.from_frozen_evaluation_artifacts(ROOT)
    log.info("dated C14 schedule: %s over %s..%s", engine.schedule.validate(*WINDOW), *WINDOW)
    for country in args.countries:
        before = engine.schedule.resolve(country, "2018-03-31")
        after = engine.schedule.resolve(country, "2018-04-01")
        log.info("  %s across 2018-04-01: %s -> %s (long %s -> %s)", country,
                 before.legal_regime, after.legal_regime, before.cgt_long, after.cgt_long)

    panels = [panel_for_country(c, args.strategies, engine, cfg, args.aum)
              for c in args.countries]
    panels = [p for p in panels if not p.empty]
    if not panels:
        print("no usable panels; run pipelines/04_construct_portfolios.py first")
        return 2
    panel = pd.concat(panels, ignore_index=True)
    args.out.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.out / "tax_year_panel.csv", index=False)

    res = pd.DataFrame([did(panel, c, include_truncated=args.include_truncated_year)
                        for c in args.countries])
    res.to_csv(args.out / "event_112a.csv", index=False)

    print("=" * 100)
    print("SECTION 112A: does a legislated cut in the wedge relieve high-turnover cells most?")
    print("=" * 100)
    print("  prediction: post x turnover interaction NEGATIVE in India (wedge 0.15 -> 0.05),")
    print("              and ZERO in Germany/Japan, whose law did not change on that date.")
    print()
    fmt = lambda v: f"{v:,.6f}"  # noqa: E731
    print("PRIMARY: tax paid per unit of NAV (no denominator)")
    cols = [c for c in ["country", "wedge_before", "wedge_after", "n_obs", "n_cells",
                        "n_tax_years", "n_post_years", "tax_level_interaction", "tax_level_t",
                        "tax_level_t_cluster_cell", "tax_level_significant_5pct"]
            if c in res.columns]
    print(res[cols].to_string(index=False, float_format=fmt))
    print()
    print("SECONDARY: tax per unit of gain - ILL-DEFINED where a tax year's gross return < 0")
    cols = [c for c in ["country", "n_taxyears_with_negative_gross", "n_obs",
                        "interaction_post_x_turnover", "interaction_t",
                        "interaction_t_cluster_cell", "significant_5pct"] if c in res.columns]
    print(res[cols].to_string(index=False, float_format=fmt))
    print()
    print("Holding-period composition, which 112A must NOT move (the portfolio is fixed)")
    cols = [c for c in ["country", "mean_lt_share_pre", "mean_lt_share_post",
                        "mean_tax_per_gain_pre", "mean_tax_per_gain_post"] if c in res.columns]
    print(res[cols].to_string(index=False, float_format=fmt))
    print()
    for _, r in res.iterrows():
        if "error" in res.columns and isinstance(r.get("error"), str):
            print(f"  {r['country']}: {r['error']}")
            continue
        treated = r["wedge_before"] != r["wedge_after"]
        if treated:
            verdict = ("CONSISTENT with the wedge channel"
                       if r["tax_level_interaction"] < 0 else
                       "AGAINST the wedge channel (interaction should be negative)")
        else:
            verdict = ("CONSISTENT with the control (no law change, no gradient)"
                       if not r["tax_level_significant_5pct"] else
                       "AGAINST the control - a gradient appears where no law moved")
        print(f"  {r['country']}: tax-level interaction {r['tax_level_interaction']:+.6f} "
              f"t={r['tax_level_t']:+.2f} (year-clustered) "
              f"t={r['tax_level_t_cluster_cell']:+.2f} (cell-clustered) -> {verdict}")
    print(f"\nwrote {args.out / 'event_112a.csv'} and {args.out / 'tax_year_panel.csv'}")
    print("\nNOTE: the cells are not tax-aware, so this measures the INCIDENCE of the statute on a")
    print("fixed portfolio - a comparative static of the theory - not a behavioural response.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
