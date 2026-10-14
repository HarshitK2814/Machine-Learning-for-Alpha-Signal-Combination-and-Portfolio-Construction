"""Phase C support census v3: corrected classification, presence-only access, no numerical values retained.

Synthetic fixtures only; no repository data is read.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools" / "phase_c_input_census_v3.py"
spec = importlib.util.spec_from_file_location("phase_c_input_census_v3", TOOL)
c3 = importlib.util.module_from_spec(spec)
sys.modules["phase_c_input_census_v3"] = c3
spec.loader.exec_module(c3)

MONTHS = pd.period_range("2009-01", "2009-06", freq="M")
JAN, FEB, MAR, APR, MAY, JUN = MONTHS
RET, DIV, SPR, ADV = 9.99, 7.77, 8.88, 6.66


def _ends(m):
    return m.to_timestamp(how="end").normalize()


# name -> months with NO C4 row / NO C6 row / ret_next NaN / div_next NaN / adv_usd NaN (uncertified)
NO_C4 = {5: {MAR, APR, MAY}}
NO_C6 = {4: {FEB, MAR}, 5: set(MONTHS[1:]), 6: set(MONTHS[1:])}
NAN_RET = {6: {MAR}}
NAN_DIV = {8: {APR}}
UNCERT = {7: {FEB}}


def _build(root: Path):
    names = [1, 2, 4, 5, 6, 7, 8]
    c4, u, c6 = [], [], []
    for c in c3.COUNTRIES:
        for m in MONTHS:
            for p in names:
                if m in NO_C4.get(p, ()):
                    continue
                c4.append((c, _ends(m), p, np.nan if m in NAN_RET.get(p, ()) else RET,
                           np.nan if m in NAN_DIV.get(p, ()) else DIV))
                u.append((c, _ends(m), p, m not in NO_C6.get(p, ()), 5.55))
                if m not in NO_C6.get(p, ()) and m not in NO_C4.get(p, ()):
                    c6.append((c, _ends(m), p, SPR, 1.0, np.nan if m in UNCERT.get(p, ()) else ADV, 0.01, "s", "b", 1.0, 1.0,
                               21, 21, 1, 20, 1.0, "USD", _ends(m)))
    for c in c3.COUNTRIES:
        t = pd.DataFrame([r[1:] for r in c4 if r[0] == c], columns=["date", "permno", "ret_next", "div_next"])
        for col in ("r_1m", "r_3m", "r_6m", "r_12m"):
            t[col] = 9.99
        (root / f"data/intl_c4/production/{c}").mkdir(parents=True)
        t.to_parquet(root / f"data/intl_c4/production/{c}/targets.parquet")
        uu = pd.DataFrame([r[1:] for r in u if r[0] == c], columns=["date", "permno", "in_universe", "me"])
        uu["price"], uu["exchcd"], uu["ff49"], uu["nyse_size_pct"] = 5.55, 1, 1, 0.5
        (root / f"data/intl_c1/production/{c}").mkdir(parents=True)
        uu.to_parquet(root / f"data/intl_c1/production/{c}/universe.parquet")

        def wfile(name, spec_):
            d = root / "outputs/decile_weights" / c / "tierb" / "aum_1e+06"
            d.mkdir(parents=True, exist_ok=True)
            rows = [(_ends(m), p, 0.25) for m in MONTHS for p in spec_(m)]
            pd.DataFrame(rows, columns=["date", "permno", "w"]).to_parquet(d / f"{name}.parquet")

        wfile("capped_frozen", lambda m: (1, 2, 4) if m == JAN else (1, 2))     # name 4 loses C6 Feb-Mar, stays in C4
        wfile("capped_vanish", lambda m: (1, 5) if m == JAN else (1,))          # 5: frozen Feb, absent from C4 Mar-May
        wfile("capped_noret", lambda m: (1, 6) if m == JAN else (1,))           # 6: frozen Feb, ret_next NaN in Mar
        wfile("capped_cost", lambda m: (1, 2, 7) if m == FEB else (1, 2))       # 7 enters Feb with uncertified C6
        wfile("capped_div", lambda m: (1, 8))                                    # 8 has div_next NaN in Apr
    cols = ["country", "date", "permno", "spread", "sigma_d", "adv_usd", "borrow_fee", "spread_source", "borrow_fee_source",
            "edge_21_strict", "ar_21_strict", "return_obs_21", "volume_obs_21", "ohlc_complete_21", "pair_obs_20",
            "usd_per_local", "curcdd", "endpoint_date"]
    (root / "data/intl_c6/production").mkdir(parents=True)
    pd.DataFrame(c6, columns=cols).to_csv(root / "data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz", index=False)


@pytest.fixture()
def run(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    _build(root)
    seen = {"parquet": [], "csv": []}
    real_pq, real_csv = pq.read_table, pd.read_csv

    def spy_pq(path, columns=None, **kw):
        seen["parquet"].append((Path(str(path)).name, None if columns is None else list(columns)))
        return real_pq(path, columns=columns, **kw)

    def spy_csv(path, *a, **kw):
        seen["csv"].append((Path(str(path)).name, kw.get("usecols"), kw.get("nrows")))
        return real_csv(path, *a, **kw)

    monkeypatch.setattr(c3.pq, "read_table", spy_pq)
    monkeypatch.setattr(c3.pd, "read_csv", spy_csv)
    out = tmp_path / "census"
    c3.run_census(root, out, command="test")
    series = real_csv(out / "support_by_series.csv")          # unspied: the spy records the TOOL's reads only
    months = real_csv(out / "support_by_series_month.csv")
    return root, out, seen, series, months


def _s(series, cell, country="DEU"):
    return series[(series.country == country) & (series.cell == cell)].iloc[0]


def _m(months, cell, month, country="DEU"):
    return months[(months.country == country) & (months.cell == cell) & (months.month == month)].iloc[0]


# ------------------------------------------------------------------------------------------ access discipline
def test_every_read_is_a_projection_inside_the_declared_sets(run):
    _, _, seen, *_ = run
    assert seen["parquet"]
    for name, cols in seen["parquet"]:
        assert cols is not None and set(cols) <= c3.ALLOWED_PROJECTION and not set(cols) & c3.FORBIDDEN_COLUMNS
    for name, usecols, nrows in seen["csv"]:
        if nrows == 0:
            continue
        assert usecols is not None and set(usecols) <= c3.ALLOWED_PROJECTION and not set(usecols) & c3.FORBIDDEN_COLUMNS


def test_price_levels_cost_fields_beyond_the_certification_triple_and_borrow_are_never_read(run):
    _, _, seen, *_ = run
    touched = {c for _, cols in seen["parquet"] for c in cols} | {c for _, u, n in seen["csv"] if n != 0 for c in u}
    for forbidden in ("price", "me", "borrow_fee", "usd_per_local", "r_1m", "r_12m"):
        assert forbidden not in touched
    assert touched & {"ret_next", "div_next"}, "presence flags for ret_next/div_next must be read (and only flagged)"


def test_presence_columns_are_reduced_to_booleans_at_load_time():
    t = pd.DataFrame({"date": [pd.Timestamp("2009-01-31")] * 3, "permno": [1, 2, 3],
                      "ret_next": [0.123456, np.nan, np.inf], "div_next": [0.0, 0.5, np.nan]})
    f = c3.c4_flags(t)
    assert list(f.columns) == ["month", "permno", "ret_ok", "div_ok"]
    assert f["ret_ok"].dtype == bool and f["div_ok"].dtype == bool
    assert f["ret_ok"].tolist() == [True, False, False] and f["div_ok"].tolist() == [True, True, False]
    c = pd.DataFrame({"country": ["DEU"] * 4, "date": [pd.Timestamp("2009-01-31")] * 4, "permno": [1, 2, 3, 4],
                      "spread": [0.01, 0.01, -1.0, 0.01], "sigma_d": [0.02] * 4, "adv_usd": [5.0, 0.0, 5.0, np.nan]})
    g = c3.c6_flags(c)
    assert list(g.columns) == ["country", "month", "permno", "cert"]
    assert g["cert"].tolist() == [True, False, False, False]          # the engine's predicate: adv>0, spread>=0, finite


def test_no_read_call_lacks_an_explicit_projection():
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"read_table", "read_csv"}:
            kws = {k.arg for k in node.keywords}
            assert kws & {"columns", "usecols"} or "nrows" in kws
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "read_parquet":
            pytest.fail("read_parquet loads every column")


def test_numerical_sentinels_never_reach_any_output(run):
    _, out, *_ = run
    for f in out.glob("*"):
        text = f.read_text(encoding="utf-8")
        for sentinel in ("9.99", "7.77", "8.88", "6.66", "5.55"):
            assert sentinel not in text, (f.name, sentinel)


# ------------------------------------------------------------------------------------- corrected classification
def test_c6_lapse_with_c4_support_is_held_but_untradeable_not_an_exit(run):
    *_, series, months = run
    s = _s(series, "frozen")
    assert s.months_valuation_unresolved == 0 and s.first_unresolved_month != s.first_unresolved_month   # NaN: none
    assert s.tier_gross_valuation == "0%" and s.tier_after_tax_valuation_cost_or_tax == "0%"
    assert _m(months, "frozen", "2009-02").n_frozen_no_c6_or_c1 == 1
    assert _m(months, "frozen", "2009-03").n_frozen_no_c6_or_c1 == 1
    assert _m(months, "frozen", "2009-04").n_frozen_no_c6_or_c1 == 0         # certification returned; tradeable again
    assert not months[months.cell == "frozen"].cost_unsupported.any()        # no cost problem for a trade never made


def test_disappearance_from_c4_of_a_held_name_is_unresolved_and_sticky_and_reappearance_does_not_resolve(run):
    *_, series, months = run
    s = _s(series, "vanish")
    assert _m(months, "vanish", "2009-02").n_frozen_no_c6_or_c1 == 1 and _m(months, "vanish", "2009-02").n_unresolved_cumulative == 0
    assert _m(months, "vanish", "2009-03").n_new_unresolved_absent_from_c4 == 1
    assert s.first_unresolved_month == "2009-03"
    assert s.months_valuation_unresolved == 4                                 # Mar, Apr, May, and Jun after it reappears in C4
    assert s.unresolved_names_that_later_reappear_in_c4 == 1
    assert s.reason_absent_from_c4 == 1 and s.tier_gross_valuation == ">25%"
    assert _m(months, "vanish", "2009-06").n_unresolved_cumulative == 1


def test_unusable_return_makes_the_month_unresolved_never_zero_filled(run):
    *_, series, months = run
    s = _s(series, "noret")
    assert _m(months, "noret", "2009-03").n_new_unresolved_ret_missing == 1
    assert s.first_unresolved_month == "2009-03" and s.reason_ret_next_missing == 1 and s.months_valuation_unresolved == 4


def test_only_an_entry_needs_certified_cost_inputs(run):
    *_, series, months = run
    s = _s(series, "cost")
    assert s.months_cost_unsupported == 1 and _m(months, "cost", "2009-02").n_entries_without_certified_cost_inputs == 1
    assert s.months_valuation_unresolved == 0
    assert s.share_gross_valuation == 0 and s.share_net_valuation_or_cost == pytest.approx(1 / 6, abs=1e-4)
    assert s.tier_gross_valuation == "0%" and s.tier_net_valuation_or_cost == "(5%,25%]"


def test_missing_dividend_flag_affects_only_the_after_tax_mask(run):
    *_, series, months = run
    s = _s(series, "div")
    assert s.months_dividend_unsupported == 1 and _m(months, "div", "2009-04").n_exposed_without_div_next == 1
    assert s.share_gross_valuation == 0 and s.share_net_valuation_or_cost == 0
    assert s.share_after_tax_valuation_cost_or_tax == pytest.approx(1 / 6, abs=1e-4)


def test_metric_union_is_counted_once_per_month():
    sim = pd.DataFrame({"valuation_unresolved": [True, True, False, False], "cost_unsupported": [True, False, True, False],
                        "dividend_unsupported": [False, False, True, True]})
    sh = c3.metric_shares(sim)
    assert sh == {"share_gross_valuation": 0.5, "share_net_valuation_or_cost": 0.75,
                  "share_after_tax_valuation_cost_or_tax": 1.0}


def test_simulation_is_deterministic_and_symmetric_across_countries(run):
    *_, series, _ = run
    for cell in ("frozen", "vanish", "noret", "cost", "div"):
        rows = series[series.cell == cell].drop(columns=["country"]).reset_index(drop=True)
        assert all(rows.iloc[0].equals(rows.iloc[i]) for i in range(1, len(rows)))


# --------------------------------------------------------------------------------------------- provenance
def test_manifest_records_fields_predicates_rules_and_limits_and_no_terminal_field(run):
    _, out, *_ = run
    man = json.loads((out / "MANIFEST.json").read_text())
    assert man["label"].startswith("OUTCOME-FREE SUPPORT CENSUS v3")
    assert man["presence_only_columns_accessed"]["C4 targets"]["ret_next"] == "isfinite"
    assert "certified" in man["presence_only_columns_accessed"]["C6 cost inputs"]["adv_usd"]
    assert "held_but_untradeable" in man["rules"] and man["limitations"] and man["input_sha256"]
    assert json.loads((out / "terminal_event_field_scan.json").read_text())["terminal_event_fields_found"] == []


def test_refuses_to_overwrite_an_existing_output(tmp_path):
    root = tmp_path / "repo"
    _build(root)
    out = tmp_path / "census"
    out.mkdir()
    (out / "keep.txt").write_text("old")
    with pytest.raises(SystemExit):
        c3.run_census(root, out)
    assert (out / "keep.txt").read_text() == "old"


def test_flag_crosstab_and_unusable_return_positions_on_the_constructed_panel(run):
    _, out, *_ = run
    ct = pd.read_csv(out / "c4_support_flag_crosstab.csv")
    d = ct[ct.country == "DEU"]
    assert d["n_c4_rows"].sum() == 7 * 6 - 3                      # 7 names x 6 months minus name 5's three absent C4 months
    nan_ret = d[~d.ret_ok]["n_c4_rows"].sum()
    assert nan_ret == 1                                            # name 6, March
    pos = pd.read_csv(out / "c4_unusable_ret_next_position.csv")
    r = pos[pos.country == "DEU"].iloc[0]
    assert (r.n_c4_rows_with_unusable_ret_next, bool(r.is_last_c4_row_of_name), bool(r.later_usable_ret_exists)) == (1, False, True)
