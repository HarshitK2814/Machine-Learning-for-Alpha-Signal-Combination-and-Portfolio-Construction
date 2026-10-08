"""Country-aware resolution of the promoted international layout.

These tests pin the properties that matter for correctness rather than the shape of
the implementation: that the frozen paths are the ones read, that a missing artefact
fails loudly instead of silently resolving to the old flat layout, that pooling can
never merge two countries' securities, and that the frozen tax evaluation window is
enforced at the gate.

Everything here runs on synthetic fixtures, so the suite stays green whether or not
the real promoted data is present on the machine.
"""
from __future__ import annotations

import json

import pandas as pd
import pytest

from alphacomb.contracts import intl


@pytest.fixture()
def frozen_layout(tmp_path, monkeypatch):
    """A miniature copy of the promoted data/intl_c* layout."""
    root = tmp_path / "data"
    monkeypatch.setenv("ALPHACOMB_DATA", str(root))

    dates = pd.to_datetime(["2008-12-31", "2009-01-31", "2015-06-30", "2018-03-31", "2020-06-30"])
    for i, country in enumerate(intl.COUNTRIES):
        base = 1000 * (i + 1)
        permnos = [base + 1, base + 2]
        rows = [(d, p) for d in dates for p in permnos]
        frame = pd.DataFrame(rows, columns=["date", "permno"])
        frame["permno"] = frame["permno"].astype("int32")

        uni = frame.assign(in_universe=True, me=1.0, price=10.0, ff49=1, nyse_size_pct=50.0)
        (root / intl.C1_DIR / country).mkdir(parents=True, exist_ok=True)
        uni.to_parquet(root / intl.C1_DIR / country / "universe.parquet")

        (root / intl.C2_DIR / country).mkdir(parents=True, exist_ok=True)
        frame.assign(sig_a=0.1, sig_b=-0.2).to_parquet(root / intl.C2_DIR / country / "signals.parquet")

        (root / intl.C4_DIR / country).mkdir(parents=True, exist_ok=True)
        frame.assign(ret_next=0.01, r_1m=0.01).to_parquet(root / intl.C4_DIR / country / "targets.parquet")

        (root / intl.C5_DIR / country).mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"date": dates, "MKTVOL": 0.1, "TERM": 0.02}).to_parquet(
            root / intl.C5_DIR / country / "states.parquet"
        )

    pd.DataFrame({"signal": ["sig_a", "sig_b"], "theme": ["value", "momentum"],
                  "pub_year": [1992, 1993], "source": ["x", "y"]}).to_csv(
        root / intl.C2_DIR / "signal_meta.csv", index=False)

    cost_rows = []
    for i, country in enumerate(intl.COUNTRIES):
        base = 1000 * (i + 1)
        for d in dates:
            for p in (base + 1, base + 2):
                cost_rows.append({"date": d, "permno": p, "spread": 0.002,
                                  "sigma_d": 0.02, "adv_usd": 1e7, "borrow_fee": None})
    (root / "intl_c6" / "production").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cost_rows).to_csv(root / intl.C6_FILE, index=False, compression="gzip")

    (root / "intl_c14" / "production").mkdir(parents=True, exist_ok=True)
    (root / intl.C14_FILE).write_text("country,start,end\nDEU,2009-01-01,2019-12-31\n", encoding="utf-8")

    cfg = tmp_path / "sample.json"
    cfg.write_text(json.dumps({
        "primary_after_tax_evaluation_window": {"start": "2009-01-01", "end": "2019-12-31"},
        "clean_mechanism_subwindow": {"start": "2014-01-01", "end": "2018-03-31"},
        "tax_ledger_inception": "2009-01-01",
        "tax_year_end_months": {"DEU": 12, "JPN": 12, "IND": 3},
    }), encoding="utf-8")
    return {"root": root, "config": cfg, "dates": dates}


def test_all_three_countries_resolve(frozen_layout):
    assert intl.available_countries() == list(intl.COUNTRIES)


def test_missing_artefact_fails_loudly_rather_than_falling_back(frozen_layout):
    """A deleted contract must raise, never silently resolve to the flat data/<source> layout."""
    (frozen_layout["root"] / intl.C1_DIR / "IND" / "universe.parquet").unlink()
    with pytest.raises(intl.ContractLayoutError):
        intl.universe_path("IND")
    assert "IND" not in intl.available_countries()


def test_pooled_panel_carries_country_and_composite_key(frozen_layout):
    panel = intl.load_panel(intl.PanelMode.POOLED)
    pooled = panel["pooled"]["universe"]
    assert set(pooled["country"].unique()) == set(intl.COUNTRIES)
    assert pooled["gid"].str.contains(":").all()
    # gid is unique per security-month; permno alone would be too in this fixture,
    # but gid is what downstream code must key on.
    assert not pooled.duplicated(["date", "gid"]).any()


def test_separate_mode_does_not_build_a_pooled_frame(frozen_layout):
    panel = intl.load_panel(intl.PanelMode.SEPARATE)
    assert panel["pooled"] is None
    assert set(panel["by_country"]) == set(intl.COUNTRIES)


def test_default_mode_keeps_per_country_frames_for_tax_ledgers(frozen_layout):
    """The default pools the fit but must still hand back per-country frames,
    because C14 tax year-ends differ and an after-tax ledger cannot be pooled."""
    panel = intl.load_panel()
    assert panel["mode"] is intl.PanelMode.POOLED_FIT_SEPARATE_CONSTRUCT
    assert panel["pooled"] is not None
    assert set(panel["by_country"]) == set(intl.COUNTRIES)


def test_colliding_permnos_across_countries_raise(frozen_layout):
    """Two countries reusing an identifier would silently merge unrelated securities."""
    deu = pd.read_parquet(intl.universe_path("DEU"))
    clash = deu.copy()
    with pytest.raises(ValueError, match="must key on"):
        intl.assert_permno_disjoint({"DEU": deu, "JPN": clash})


def test_evaluation_window_read_from_frozen_config(frozen_layout):
    w = intl.evaluation_window(frozen_layout["config"])
    assert (w.start, w.end) == (pd.Timestamp("2009-01-01"), pd.Timestamp("2019-12-31"))
    assert (w.mechanism_start, w.mechanism_end) == (pd.Timestamp("2014-01-01"), pd.Timestamp("2018-03-31"))
    assert w.tax_year_end_months["IND"] == 3, "India's tax year ends in March, not December"


def test_gate_excludes_pre_2009_and_post_2019(frozen_layout):
    w = intl.evaluation_window(frozen_layout["config"])
    df = pd.DataFrame({"date": frozen_layout["dates"], "x": range(len(frozen_layout["dates"]))})
    gated = intl.gate_evaluation_frame(df, window=w)
    assert gated["date"].min() >= w.start and gated["date"].max() <= w.end
    assert pd.Timestamp("2008-12-31") not in set(gated["date"])
    assert pd.Timestamp("2020-06-30") not in set(gated["date"])


def test_mechanism_subwindow_is_tighter_than_primary(frozen_layout):
    w = intl.evaluation_window(frozen_layout["config"])
    df = pd.DataFrame({"date": frozen_layout["dates"]})
    assert len(intl.gate_evaluation_frame(df, mechanism_only=True, window=w)) < \
           len(intl.gate_evaluation_frame(df, window=w))


def test_gate_requires_a_date_column(frozen_layout):
    with pytest.raises(intl.EvaluationWindowError):
        intl.gate_evaluation_frame(pd.DataFrame({"permno": [1, 2]}),
                                   window=intl.evaluation_window(frozen_layout["config"]))


def test_c6_borrow_fee_is_not_filled_by_the_resolver(frozen_layout):
    """C6 borrow_fee stays null here; the modelled proxy is injected at the C11/experiment
    layer only, and the legacy 25 bp fallback is prohibited."""
    costs = intl.load_cost_inputs()
    assert costs["borrow_fee"].isna().all()
