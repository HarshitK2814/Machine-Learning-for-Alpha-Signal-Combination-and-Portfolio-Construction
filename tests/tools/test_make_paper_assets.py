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
        assert f"`{mod.SOURCES[key]}` `{mod.sha256_portable(mod.src(key))}`" in cat


def test_png_dimensions_match_the_intended_page_width(built):
    from PIL import Image
    a, _, recs = built
    for r in recs:
        if r["kind"] != "figure":
            continue
        png = next(f for f in r["files"] if f.endswith(".png"))
        w, h = Image.open(a / png).size
        assert w == 2100 and 700 <= h <= 1400, (png, w, h)


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
    banned = [r"pre-?registered", r"confirmatory", r"\bconfirm(s|ed)\b", r"(?<!not an )investable (gain|improvement)", r"Maham (approved|acknowledged)"]
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


# ---------------------------------------------------------------------------------------------------------------
# second tranche (tools/make_paper_assets_extra.py)
# ---------------------------------------------------------------------------------------------------------------
def _extra():
    import make_paper_assets_extra as X
    X.register(mod)
    return X


def test_library_size_and_unique_ids(built):
    _, _, recs = built
    ids = [r["id"] for r in recs]
    assert len(ids) == len(set(ids))
    assert sum(r["kind"] == "figure" for r in recs) == 26 and sum(r["kind"] == "table" for r in recs) == 25


def test_unsupported_country_or_rung_is_rejected():
    X = _extra()
    with pytest.raises(ValueError):
        X.monthly("USA")
    with pytest.raises(ValueError):
        X.composite("DEU", 1e10, "capped", "net_ret")      # no committed Tier B series at this rung for Germany
    with pytest.raises(ValueError):
        X.composite("DEU", 1e6, "optimised", "net_ret")    # a book the artifact does not hold


def test_a_missing_month_is_a_visible_gap_never_interpolated():
    X = _extra()
    full = X.all_months()
    assert full.to_series().diff().dropna().dt.days.between(28, 31).all()
    for c in X.COUNTRIES:
        miss = set(X.missing_months(c))
        t = pd.read_csv(mod.src(f"tierB_{c}")).set_index("aum")
        for r in X.pick_rungs():
            s = X.composite(c, r, "capped", "net_ret")
            assert list(s.index) == list(full)
            assert {d.strftime("%Y-%m") for d in s.index[s.isna()]} == miss
            assert int(s.notna().sum()) == int(t.loc[r, "months"])
    assert "2009-10" in X.missing_months("IND") and not X.missing_months("DEU")


def test_derived_wealth_reproduces_the_published_terminal_wealth():
    X = _extra()
    for c in X.COUNTRIES:
        t = pd.read_csv(mod.src(f"tierB_{c}"))
        for _, row in t.iterrows():
            w = X.wealth(c, row["aum"], "uncapped").iloc[-1]
            assert np.isclose(w, row["uncapped_terminal_wealth"], rtol=1e-6, atol=1e-9), (c, row["aum"])


def test_wealth_figure_breaks_lines_at_missing_months_and_nowhere_else():
    X = _extra()
    mod.set_style()
    fig = X.fig_wealth_paths()
    import matplotlib.pyplot as plt
    for ax, c in zip(fig.axes, X.COUNTRIES):
        n_missing = len(X.missing_months(c))
        for ln in ax.get_lines():
            y = np.asarray(ln.get_ydata(), float)
            if len(y) > 2:
                assert len(y) == len(X.all_months()) and int(np.isnan(y).sum()) == n_missing
    plt.close(fig)


def test_coverage_denominators_are_consistent_across_sources():
    X = _extra()
    cv = mod.coverage_monthly()
    x = pd.read_csv(mod.src("flag_crosstab"))
    f = X.coverage_funnel()
    for c in X.COUNTRIES:
        # all C4 rows in the crosstab = the funnel total
        assert f[f["country"] == c]["n_c4_rows"].sum() == x[x["country"] == c]["n_c4_rows"].sum()
        # in-universe rows and certified rows agree between the monthly counts and the flag crosstab
        assert cv[cv["country"] == c]["c4_in_c1_universe"].sum() == x[(x["country"] == c) & x["in_c1_universe"]]["n_c4_rows"].sum()
        assert cv[cv["country"] == c]["c4_with_certified_c6"].sum() == x[(x["country"] == c) & x["c6_certified"]]["n_c4_rows"].sum()
        assert np.isclose(f[f["country"] == c]["share"].sum(), 1.0)


def test_coverage_audit_reproduces_the_manuscript_statistic_and_the_india_month():
    X = _extra()
    a = X.coverage_audit().set_index("country")
    ms = (mod.ROOT / "submission_candidate_as_run_only" / "manuscript.md").read_text(encoding="utf-8")
    for c in X.COUNTRIES:
        assert f"{a.loc[c, 'mean_of_monthly_shares']:.3f}" in ms
    assert a.loc["IND", "lowest_certified"] < 0.01 * a.loc["IND", "lowest_in_universe"]
    assert a.loc["IND", "mean_excluding_lowest_month"] > a.loc["IND", "mean_of_monthly_shares"]
    assert a.loc["DEU", "months_below_0_9"] == a.loc["DEU", "months"]


def test_cost_parity_effects_sum_to_the_difference():
    d = pd.read_csv(mod.src("parity_summary"))
    tot = d["e_D"] + d["e_X"] + d["e_B"] + d["interaction"]
    assert np.allclose(tot, -d["replicated_B_minus_A"], atol=1e-6)          # effects sum to the replicated difference
    resid = (d["cost_A"] - d["cost_B"]) - tot                               # the recorded difference differs by the replication residual
    assert np.allclose(resid, -d["residual_R"], atol=1e-6) and resid.abs().max() < 0.05


def test_tier_gap_is_reported_not_hidden(built):
    a, _, _ = built
    X = _extra()
    st = X.tier_gap_stats()
    assert st["DEU"]["max_abs_points"] > 10
    md = (a / "tables" / "supplementary" / "TAB_S16_tierA_tierB_reconciliation.md").read_text(encoding="utf-8")
    assert "not equal" in md and f"{st['DEU']['max_abs_points']:.1f}" in md
    cat = (a / "ASSET_CATALOG.md").read_text(encoding="utf-8")
    assert "not as confirmation" in cat or "not present" in cat or "confirmation" in cat


def test_specification_table_matches_the_manuscript(built):
    a, _, _ = built
    raw = pd.read_csv(a / "tables" / "main_text" / "TAB_M4_construction_friction_spec.csv").set_index("parameter")["value"]
    ms = (mod.ROOT / "submission_candidate_as_run_only" / "manuscript.md").read_text(encoding="utf-8")
    assert float(raw["Gross exposure limit"]) == 2.0 and "gross exposure 2.0" in ms
    assert float(raw["Per-name weight cap"]) == 0.01 and "1% per-name cap" in ms
    assert float(raw["Target volatility (annual)"]) == 0.1 and "10% volatility target" in ms
    assert float(raw["Impact coefficient k"]) == 1.0 and "k = 1.0" in ms
    assert float(raw["Flat borrow rate (annual)"]) == 0.01 and "1% per year" in ms


def test_registry_hashes_match_the_files(built):
    a, _, _ = built
    reg = pd.read_csv(a / "tables" / "supplementary" / "TAB_S7_source_provenance_registry.csv")
    for _, r in reg.iterrows():
        assert mod.sha256_portable(mod.ROOT / r["path"]) == r["sha256"]


def test_verify_folder_detects_tampering_and_ignores_line_endings(built, tmp_path):
    import shutil
    a, _, _ = built
    d = tmp_path / "copy"
    shutil.copytree(a, d)
    assert mod.verify_folder(d) == []
    # a Windows checkout converting LF to CRLF in a text file must still verify
    p = d / "tables" / "main_text" / "TAB_M1_markets_coverage.csv"
    p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
    assert mod.verify_folder(d) == []
    # a real change must be caught
    p.write_text(p.read_text(encoding="utf-8").replace("Germany", "Germanyx", 1), encoding="utf-8", newline="\n")
    assert any("hash differs" in m for m in mod.verify_folder(d))
    (d / "figures" / "main_text" / "FIG_M1_pipeline.png").write_bytes(b"x")
    assert any("FIG_M1_pipeline.png" in m for m in mod.verify_folder(d))


def test_every_asset_has_a_review_note_and_a_distinct_caption(built):
    a, _, recs = built
    cat = (a / "ASSET_CATALOG.md").read_text(encoding="utf-8")
    assert cat.count("* Review:") == len(recs)
    caps = [r["caption"] for r in recs]
    assert len(caps) == len(set(caps)), "two assets share a caption: a sign of a duplicate"
