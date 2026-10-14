"""Phase C input census: column whitelist, no outcome columns, no delisting inference, no overwrite.

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

TOOL = Path(__file__).resolve().parents[2] / "tools" / "phase_c_input_census.py"
spec = importlib.util.spec_from_file_location("phase_c_input_census", TOOL)
census = importlib.util.module_from_spec(spec)
sys.modules["phase_c_input_census"] = census
spec.loader.exec_module(census)

MONTHS = pd.period_range("2009-01", "2009-06", freq="M")


def _ends(m):
    return m.to_timestamp(how="end").normalize()


def _build(root: Path):
    """Names 1,2,3 in every month; name 4 leaves C4 after Feb (held in Feb); name 5 leaves then returns."""
    for c in census.COUNTRIES:
        c4 = []
        for m in MONTHS:
            names = [1, 2, 3]
            if m <= MONTHS[1]:
                names.append(4)
            if m not in (MONTHS[2], MONTHS[3]):
                names.append(5)
            c4 += [(_ends(m), p, 9.99, 7.77) for p in names]
        t = pd.DataFrame(c4, columns=["date", "permno", "ret_next", "div_next"])
        for col in ("r_1m", "r_3m", "r_6m", "r_12m"):
            t[col] = 9.99
        (root / f"data/intl_c4/production/{c}").mkdir(parents=True)
        t.to_parquet(root / f"data/intl_c4/production/{c}/targets.parquet")
        u = t[["date", "permno"]].copy()
        u["in_universe"] = True
        u["me"], u["price"], u["exchcd"], u["ff49"], u["nyse_size_pct"] = 5.55, 5.55, 1, 1, 0.5
        (root / f"data/intl_c1/production/{c}").mkdir(parents=True)
        u.to_parquet(root / f"data/intl_c1/production/{c}/universe.parquet")
        wdir = root / "outputs/decile_weights" / c / "tierb" / "aum_1e+06"
        wdir.mkdir(parents=True)
        w = pd.DataFrame([(_ends(m), p, 0.25) for m in MONTHS for p in (1, 2, 4)], columns=["date", "permno", "w"])
        w.to_parquet(wdir / "capped_X-0.parquet")
        w2 = pd.DataFrame([(_ends(m), p, 0.5) for m in MONTHS for p in (1, 2)], columns=["date", "permno", "w"])
        w2.to_parquet(wdir / "uncapped_X-0.parquet")
    rows = []
    for c in census.COUNTRIES:
        for m in MONTHS:
            for p in (1, 2, 3, 4, 5):
                if p == 4 and m > MONTHS[1]:
                    continue                      # name 4 has no C6 row after February
                rows.append((c, _ends(m), p, 8.88, 1.0, 1.0, 0.01, "s", "b", 1.0, 1.0, 21, 21, 1, 20, 1.0, "USD", _ends(m)))
    cols = ["country", "date", "permno", "spread", "sigma_d", "adv_usd", "borrow_fee", "spread_source", "borrow_fee_source",
            "edge_21_strict", "ar_21_strict", "return_obs_21", "volume_obs_21", "ohlc_complete_21", "pair_obs_20",
            "usd_per_local", "curcdd", "endpoint_date"]
    (root / "data/intl_c6/production").mkdir(parents=True)
    pd.DataFrame(rows, columns=cols).to_csv(root / "data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz",
                                            index=False)


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

    monkeypatch.setattr(census.pq, "read_table", spy_pq)
    monkeypatch.setattr(census.pd, "read_csv", spy_csv)
    # make the 2009 window cover the fixture
    out = tmp_path / "census"
    census.run_census(root, out, command="test")
    return root, out, seen


def test_every_data_read_is_a_projection_inside_the_whitelist(run):
    _, _, seen = run
    allowed = {col for cols in census.ACCESSED.values() for col in cols}
    assert seen["parquet"], "no parquet read recorded"
    for name, cols in seen["parquet"]:
        assert cols is not None, f"{name} read without a column projection"
        assert set(cols) <= allowed
        assert not set(cols) & census.FORBIDDEN_COLUMNS
    for name, usecols, nrows in seen["csv"]:
        if nrows == 0:                      # header-only schema scan
            continue
        assert usecols is not None and set(usecols) <= allowed
        assert not set(usecols) & census.FORBIDDEN_COLUMNS


def test_whitelist_and_forbidden_sets_are_disjoint_and_outcome_columns_listed():
    allowed = {col for cols in census.ACCESSED.values() for col in cols}
    assert not allowed & census.FORBIDDEN_COLUMNS
    for must in ("ret_next", "div_next", "price", "spread", "borrow_fee", "net_ret", "nav"):
        assert must in census.FORBIDDEN_COLUMNS


def test_no_read_call_in_the_script_lacks_an_explicit_projection():
    tree = ast.parse(TOOL.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"read_table", "read_csv"}:
            kws = {k.arg for k in node.keywords}
            assert kws & {"columns", "usecols"} or "nrows" in kws, ast.dump(node)[:120]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"read_parquet"}:
            pytest.fail("read_parquet loads every column")


def test_outcome_sentinels_never_reach_the_outputs(run):
    _, out, _ = run
    for f in out.glob("*"):
        text = f.read_text(encoding="utf-8")
        for sentinel in ("9.99", "7.77", "8.88", "5.55"):
            assert sentinel not in text, (f.name, sentinel)


def test_flows_and_held_exit_counts_match_the_constructed_panel(run):
    _, out, _ = run
    flows = pd.read_csv(out / "panel_flows_by_country_month.csv")
    c4 = flows[(flows.country == "DEU") & (flows.panel == "C4_row_present")].set_index("month")
    assert c4.loc["2009-02", "exits"] == 2                      # names 4 (never returns) and 5 (returns in May)
    assert c4.loc["2009-02", "exits_permanent_in_panel"] == 1
    assert c4.loc["2009-02", "exits_with_later_return"] == 1
    assert c4.loc["2009-03", "exits"] == 0
    held = pd.read_csv(out / "held_names_affected_by_panel_exits.csv")
    cap = held[(held.country == "DEU") & (held.book == "capped")].set_index("month")
    assert cap.loc["2009-02", "n_held_not_in_next_c4"] == 1
    assert cap.loc["2009-02", "n_held_not_in_next_c4_permanent"] == 1
    assert cap.loc["2009-01", "n_held_not_in_next_c4"] == 0
    unc = held[(held.country == "DEU") & (held.book == "uncapped")]
    assert unc["n_held_not_in_next_c4"].sum() == 0
    first = pd.read_csv(out / "projected_unresolved_share_by_strategy.csv")
    r = first[(first.country == "DEU") & (first.book == "capped")].iloc[0]
    assert r.first_month_with_held_c4_panel_exit == "2009-02"
    assert r.first_month_held_c6_lapse == "2009-02" and r.first_unresolved_month_if_no_evidence == "2009-03"
    assert r.months_unresolved_if_no_evidence == 4
    assert r.projected_unresolved_share_if_first_held_exit_is_unresolved == pytest.approx(4 / 6, abs=1e-4)


def test_missing_rows_are_not_called_delistings_and_no_evidence_field_is_found(run):
    _, out, _ = run
    scan = json.loads((out / "terminal_event_field_scan.json").read_text())
    assert scan["terminal_event_fields_found"] == []
    man = json.loads((out / "MANIFEST.json").read_text())
    assert "NOT inferred to be a delisting" in man["definition_panel_exit"]
    assert man["label"].startswith("OUTCOME-FREE INPUT CENSUS")
    held = pd.read_csv(out / "held_names_affected_by_panel_exits.csv")
    assert (held["n_held_without_terminal_event_evidence"] == held["n_held_not_in_next_c4"]).all()
    assert man["input_sha256"] and man["columns_accessed"]


def test_refuses_to_overwrite_an_existing_output(tmp_path):
    root = tmp_path / "repo"
    _build(root)
    out = tmp_path / "census"
    out.mkdir()
    (out / "keep.txt").write_text("old")
    with pytest.raises(SystemExit):
        census.run_census(root, out)
    assert (out / "keep.txt").read_text() == "old"
