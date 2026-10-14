"""The publication-asset pipeline must be deterministic, source-verified, honest about missing cells, and free of withdrawn claims."""
from __future__ import annotations

import csv
import importlib.util
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

TOOL = Path(__file__).resolve().parents[2] / "tools" / "make_paper_assets.py"
spec = importlib.util.spec_from_file_location("make_paper_assets", TOOL)
mod = importlib.util.module_from_spec(spec)
sys.modules["make_paper_assets"] = mod
spec.loader.exec_module(mod)

ALLOWED = {"MAIN_TEXT_ELIGIBLE", "SUPPLEMENTARY_ELIGIBLE", "DIAGNOSTIC_ONLY", "NOT_SUPPORTED_BY_AVAILABLE_ARTIFACTS", "EXCLUDED_WITH_REASON"}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    a = tmp_path_factory.mktemp("assets_a")
    b = tmp_path_factory.mktemp("assets_b")
    ra = mod.build(a)
    mod.build(b)
    return a, b, ra


def test_two_builds_are_byte_identical(built):
    a, b, _ = built
    ma = (a / "ASSET_MANIFEST.csv").read_text(encoding="utf-8")
    mb = (b / "ASSET_MANIFEST.csv").read_text(encoding="utf-8")
    assert ma == mb and len(ma.splitlines()) > 40


def test_manifest_covers_every_output_file(built):
    a, _, recs = built
    listed = {r["file"] for r in csv.DictReader(open(a / "ASSET_MANIFEST.csv", encoding="utf-8"))}
    on_disk = {p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file() and p.name != "ASSET_MANIFEST.csv"}
    assert listed == on_disk


def test_every_asset_has_a_valid_status_and_files(built):
    a, _, recs = built
    assert {r["status"] for r in recs} <= ALLOWED
    assert {s for _, s, _ in mod.NOT_BUILT} <= ALLOWED
    for r in recs:
        for f in r["files"]:
            assert (a / f).stat().st_size > 0, f
    assert sum(r["kind"] == "figure" for r in recs) >= 6 and sum(r["kind"] == "table" for r in recs) >= 6


def test_diagnostic_figures_are_not_in_the_main_text(built):
    _, _, recs = built
    for r in recs:
        if r["status"] == "DIAGNOSTIC_ONLY":
            assert r["section"] == "supplementary"
        if r["section"] == "main_text":
            assert r["status"] == "MAIN_TEXT_ELIGIBLE"


def test_source_hash_mismatch_is_refused(tmp_path, monkeypatch):
    rows = list(csv.DictReader(open(mod.TRACE, encoding="utf-8")))
    rows[0]["sha256"] = "0" * 64
    bad = tmp_path / "TRACEABILITY.csv"
    with open(bad, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    monkeypatch.setattr(mod, "TRACE", bad)
    with pytest.raises(SystemExit):
        mod.verify_sources()


def test_catalog_source_hashes_match_files(built):
    a, _, recs = built
    cat = (a / "ASSET_CATALOG.md").read_text(encoding="utf-8")
    for key in {k for r in recs for k in r["sources"]}:
        assert f"`{mod.SOURCES[key]}` `{mod.sha256(mod.src(key))}`" in cat


def test_png_dimensions_match_the_intended_page_width(built):
    from PIL import Image
    a, _, recs = built
    for r in recs:
        if r["kind"] != "figure":
            continue
        png = next(f for f in r["files"] if f.endswith(".png"))
        w, h = Image.open(a / png).size
        assert w == 2100 and 800 <= h <= 1400, (png, w, h)


def test_capacity_figure_plots_solvent_rungs_only_and_labels_units():
    mod.set_style()
    fig = mod.fig_capacity_B()
    frames = mod.b_frames()
    assert "points of NAV per year" in fig.axes[0].get_ylabel()
    for ax, c in zip(fig.axes, mod.COUNTRIES):
        d = frames[c]
        solvent = set(d[d["status"] == "solvent"]["aum"])
        insolvent = set(d[d["status"] == "insolvent"]["aum"])
        if c in ("DEU", "IND"):
            assert insolvent, "Germany and India have insolvent rungs that must stay unplotted"
        xs = set()
        for ln in ax.get_lines():
            x, y = np.asarray(ln.get_xdata(), float), np.asarray(ln.get_ydata(), float)
            if len(x) > 1 and np.allclose(y, 0):
                continue  # the zero reference line
            assert np.isfinite(y).all(), "no NaN may be plotted or connected"
            xs |= set(x)
        assert xs <= solvent and not (xs & insolvent)
        assert xs == solvent, "every solvent rung is drawn"
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_ladder_figure_excludes_the_uncapped_comparator():
    mod.set_style()
    fig = mod.fig_ladder()
    mb = mod.matched_book()
    unc = float(mb[mb["book"] == "uncapped"].sharpe_net.iloc[0])
    for ax in fig.axes:
        for ln in ax.get_lines():
            assert not np.any(np.isclose(np.asarray(ln.get_xdata(), float), unc))
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_rung_figure_has_one_india_point_and_no_interpolation():
    mod.set_style()
    fig = mod.fig_rungs()
    india = [ln for ln in fig.axes[0].get_lines() if ln.get_color() == mod.COL["IND"]]
    assert len(india) == 1 and len(india[0].get_xdata()) == 1
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_insolvent_rungs_appear_as_na_in_the_capacity_table(built):
    a, _, _ = built
    raw = pd.read_csv(a / "tables" / "supplementary" / "TAB_S2_capacity_all_rungs.csv")
    frames = mod.b_frames()
    n_ins = sum(int((f["status"] == "insolvent").sum()) for f in frames.values())
    assert n_ins > 0 and int((raw["status"] == "insolvent").sum()) == n_ins
    assert raw.loc[raw["status"] == "insolvent", "B_points_nav_per_year"].isna().all()
    md = (a / "tables" / "supplementary" / "TAB_S2_capacity_all_rungs.md").read_text(encoding="utf-8")
    assert md.count("comparator insolvent: no B(A)") == n_ins


def test_headline_table_values_agree_with_the_manuscript(built):
    a, _, _ = built
    ms = (mod.ROOT / "submission_candidate_as_run_only" / "manuscript.md").read_text(encoding="utf-8")
    t1 = pd.read_csv(a / "tables" / "main_text" / "TAB_M1_markets_coverage.csv")
    for v in t1["coverage_mean"]:
        assert f"{v:.3f}" in ms
    t2 = pd.read_csv(a / "tables" / "main_text" / "TAB_M2_matched_book_outcomes.csv")
    for v in t2[t2["book"] == "capped"]["tax_channel"]:
        assert f"{v:.3f}" in ms
    s1 = pd.read_csv(a / "tables" / "supplementary" / "TAB_S1_cost_tax_turnover.csv")
    for v in s1["turnover"]:
        assert f"{v:.4f}" in ms


def test_estimability_table_reports_560_series_and_no_estimable_tier(built):
    a, _, _ = built
    raw = pd.read_csv(a / "tables" / "supplementary" / "TAB_S4_estimability_census.csv")
    assert int(raw.groupby("country")["series"].first().sum()) == 560
    assert (raw["0%"] + raw["<=5%"] + raw["<=25%"]).sum() == 0


def test_no_withdrawn_or_overstated_claims_and_no_german_inference(built):
    a, _, _ = built
    banned = [r"pre-?registered", r"confirmatory", r"\bconfirm(s|ed)\b", r"investable (gain|improvement)", r"Maham (approved|acknowledged)"]
    for p in a.rglob("*"):
        if p.suffix in {".md", ".tex", ".csv"}:
            txt = p.read_text(encoding="utf-8")
            for pat in banned:
                assert not re.search(pat, txt, re.I), (p.name, pat)
    # "Sharpe-point gain" may appear only where it is labelled as withdrawn or not built (the register and the catalog)
    for p in a.rglob("*"):
        if p.suffix in {".md", ".tex", ".csv"} and re.search(r"Sharpe-point gain", p.read_text(encoding="utf-8"), re.I):
            assert p.name.startswith("TAB_S5_") or p.name == "ASSET_CATALOG.md", p.name
    reg = (a / "tables" / "supplementary" / "TAB_S5_not_reported_register.csv").read_text(encoding="utf-8")
    assert "Capacity Sharpe-point gains,withdrawn" in reg
    for p in (a / "tables").rglob("*.csv"):
        cols = set(pd.read_csv(p).columns)
        assert not ({"t_after_tax", "p_after_tax", "sharpe_after_tax_t"} & cols), p.name
    cat = (a / "ASSET_CATALOG.md").read_text(encoding="utf-8")
    assert "Phase C is blocked and unrun" in cat and "not presented as a confirmation" in cat
    assert not any("after_tax_inference" in line for line in cat.splitlines() if line.startswith("  * `"))


def test_vector_outputs_exist_and_are_not_empty(built):
    a, _, recs = built
    for r in recs:
        if r["kind"] == "figure":
            for ext in ("pdf", "svg", "png"):
                p = a / "figures" / r["section"] / f"{r['id']}.{ext}"
                assert p.stat().st_size > 1000
