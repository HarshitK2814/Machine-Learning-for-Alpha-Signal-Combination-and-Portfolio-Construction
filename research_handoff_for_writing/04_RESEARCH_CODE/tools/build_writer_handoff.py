#!/usr/bin/env python
"""Build ``research_handoff_for_writing/``: a writer-friendly copy of the approved research artifacts.

Copies only tracked, approved material (no raw or licensed data, no security-level files, no monthly return series, no copyrighted
papers, no collaborator drafts), writes the figure and table indexes from the asset catalog, and records every file with its
SHA-256 in ``HANDOFF_MANIFEST.csv`` together with the exclusions and their reasons. The Git repository stays the source of truth.

    python tools/build_writer_handoff.py                 # build the package and the archive
    python tools/build_writer_handoff.py --drive-map m.json   # fill the Drive column from {package path: Drive file id}
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "research_handoff_for_writing"
CAND = ROOT / "submission_candidate_as_run_only"
ASSETS = ROOT / "paper_assets_as_run_only"
TEXT = {".csv", ".md", ".py", ".yaml", ".yml", ".json", ".txt", ".tex", ".svg", ".bib", ".toml"}
GENERATED = ["01_MANUSCRIPT", "02_FIGURES", "03_TABLES", "04_RESEARCH_CODE", "05_RESULTS_AND_PROVENANCE", "06_LITERATURE", "07_LIMITATIONS_AND_OPEN_ITEMS"]
GITHUB_STATUS = "yes: branch main of the public origin repository (owner-authorised)"

INTENDED = {
    "FIG_M1_pipeline": "Section 4 (framework)", "FIG_M2_cost_input_coverage": "Section 3 (data)", "FIG_M3_sharpe_ladder_channels": "Section 5.1",
    "FIG_M4_capacity_B_tierB": "Section 5.2 (candidate Figure 1)", "TAB_M1_markets_coverage": "Section 3 (data)", "TAB_M2_matched_book_outcomes": "Section 5.1 (candidate Table 1)",
    "TAB_M3_tax_regimes": "Section 5.3 (or Section 3)", "TAB_M4_construction_friction_spec": "Section 4.1",
    "FIG_S1_uncapped_terminal_wealth": "Section 5.2 or supplement (candidate Figure 2)", "TAB_S2_capacity_all_rungs": "Supplement; selected rungs are candidate Table 2",
}
GROUPS = [("FIG_S5", "Supplement A: data and coverage"), ("FIG_S6", "Supplement A: data and coverage"), ("FIG_S7", "Supplement A: data and coverage (supports the Section 3 India disclosure)"),
          ("TAB_S9", "Supplement A: data and coverage"), ("TAB_S10", "Supplement A: data and coverage"), ("TAB_S11", "Supplement A: data and coverage (supports the Section 3 India disclosure)"),
          ("FIG_S8", "Supplement B: executable-book paths"), ("FIG_S9", "Supplement B"), ("FIG_S10", "Supplement B"), ("FIG_S11", "Supplement B"), ("FIG_S12", "Supplement B"),
          ("FIG_S13", "Supplement C: capacity and liquidity"), ("FIG_S14", "Supplement C"), ("FIG_S15", "Supplement C"), ("FIG_S2", "Supplement C"), ("TAB_S17", "Supplement C"), ("TAB_S18", "Supplement C"),
          ("FIG_S3", "Supplement D: costs and tax by mandate size"), ("FIG_S20", "Supplement D"), ("TAB_S1", "Supplement D"), ("TAB_S12", "Supplement D"), ("TAB_S13", "Supplement D"), ("TAB_S14", "Supplement D"),
          ("FIG_S18", "Supplement D"), ("FIG_S4", "Supplement E: design axes (diagnostic)"), ("FIG_S22", "Supplement E: design axes"), ("TAB_S3", "Supplement E"), ("TAB_S20", "Supplement E"),
          ("FIG_S16", "Supplement F: diagnostics (never main text)"), ("FIG_S17", "Supplement F"), ("FIG_S19", "Supplement F"), ("FIG_S21", "Supplement F"), ("TAB_S15", "Supplement F"), ("TAB_S16", "Supplement F"), ("TAB_S19", "Supplement F"),
          ("TAB_S4", "Supplement G: traceability and exclusions"), ("TAB_S5", "Supplement G"), ("TAB_S6", "Supplement G"), ("TAB_S7", "Supplement G"), ("TAB_S8", "Supplement G"), ("TAB_S21", "Supplement G")]

LIMIT_DOCS = ["AMENDMENT_001C_JAPAN_PREDICTION_SCORECARD.md", "AMENDMENT_001C_CAPACITY_HYPOTHESIS_PREREGISTRATION.md", "AMENDMENT_001D_CAPACITY_CHANNEL_SIGN_FLIP.md",
              "EXIT_POLICY_RULING_AND_001E_RESPONSE_2026-10-13.md", "NON_TRADEABLE_TREATMENT.md", "PHASE_C_VENDOR_COVERAGE_FEASIBILITY_2026-10-14.md", "PHASE_C_RUN_READINESS_V2_2026-10-14.md",
              "PHASE_C_REVISED_ANALYSIS_SPEC_2026-10-14.md", "FINAL_NUMERICAL_TRACEABILITY_GAPS.md", "FINALIZATION_AUDIT_2026-10-09.md", "INFERENCE_AUDIT_2026-10-13.md", "ECONOMIC_ARM_CAPABILITY_GAP.md"]
PROV_DOCS = ["FINAL_CLAIM_EVIDENCE_MATRIX.md", "FINAL_NUMERICAL_TRACEABILITY_GAPS.md", "MANUSCRIPT_EVIDENCE_MAP_2026-10-14.md", "PROJECT_COMPLETION_REPORT.md", "PHASE_C_AFTER_TAX_CONFIGURATION_RECOVERY_2026-10-14.md"]
LIT_DOCS = ["FINAL_PRIOR_ART_REVIEW.md", "FINAL_PUBLICATION_PATH.md"]
RESULT_RES = ["results/capacity_return_difference/tierA_DEU.csv", "results/capacity_return_difference/tierA_IND.csv", "results/capacity_return_difference/tierA_JPN.csv",
              "results/capacity_return_difference/tierB_DEU.csv", "results/capacity_return_difference/tierB_IND.csv", "results/capacity_return_difference/tierB_JPN.csv",
              "results/capacity_return_difference/reconciliation_DEU.csv", "results/capacity_return_difference/reconciliation_IND.csv", "results/capacity_return_difference/reconciliation_JPN.csv",
              "results/cost_parity_diagnostic/parity_summary.csv", "results/cost_parity_diagnostic/dtv_support.csv",
              "results/phase_c_census_v3_2026-10-14/input_coverage_by_country_month.csv", "results/phase_c_census_v3_2026-10-14/tier_counts_by_metric.csv", "results/phase_c_census_v3_2026-10-14/c4_support_flag_crosstab.csv",
              "results/phase_c_after_tax_config_recovery_2026-10-14/after_tax_arms.csv", "results/phase_c_after_tax_config_recovery_2026-10-14/after_tax_weight_identity.csv",
              "results/figures/fig1_capacity_return_difference_B.png", "results/figures/fig2_uncapped_terminal_wealth.png"]
EXCLUDED = [
    ("results/capacity_return_difference/tierB_monthly_*.csv.gz", "monthly portfolio return series derived from licensed vendor data; redistribution not verified; not needed for writing (the repository regenerates the assets from them)"),
    ("results/cost_parity_diagnostic/parity_monthly_*.csv.gz", "monthly security-derived series from licensed vendor data; redistribution not verified"),
    ("docs/attachments/IND_112A_BOUND_*_V2_*.csv", "security-level vendor price values (permno-level); licence not verified"),
    ("docs/attachments/CAPACITY_CHANNEL_INFERENCE_*.csv", "Sharpe-point capacity-channel inference: the framing withdrawn in the candidate (one file is a non-compliant ladder); withheld to prevent reuse"),
    ("results/phase_c_census*/held_names*, support_by_series*.csv", "security- and series-month level census files; not needed for writing; Phase C is blocked"),
    ("data/, outputs/ (git-ignored)", "raw and intermediate licensed data; never shared"),
    ("root-level data-extraction scripts (extract_*, build_c*, certify_*, ...)", "vendor-extraction code for the data workstream; not needed to write the paper; remains in the repository"),
    ("configs/*.json", "frozen-decision and evaluation-sample files may name securities; not needed for writing"),
    ("docs/PAPER_2026-10-09_FULL_ACCOUNT.md", "the original full account contains claims later withdrawn; withheld to prevent accidental reuse; remains in the repository, unchanged"),
    ("submission_candidate_as_run_only/references_QF_style_DRAFT.md", "the collaborator's journal-format draft; preserved untouched and not shared without the owner's authorisation"),
    ("research/09_Reports/*.pdf, *.xlsx, *.docx", "internal planning documents, not needed for writing"),
    ("downloaded journal articles", "copyrighted; never committed; only metadata and provenance are shared"),
]


def sha_lf(p: Path) -> str:
    b = p.read_bytes()
    if p.suffix.lower() in TEXT:
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def git(*a) -> str:
    return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()


def copy(src: Path, dst: Path, category: str, kind: str, rows: list, note: str = ""):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    rows.append({"path": dst.relative_to(PKG).as_posix(), "sha256_lf_normalised_for_text": sha_lf(dst), "bytes": dst.stat().st_size, "category": category, "kind": kind,
                 "repo_path": src.relative_to(ROOT).as_posix(), "note": note})


def parse_catalog() -> list[dict]:
    t = (ASSETS / "ASSET_CATALOG.md").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"^### (\S+)\n\n\* Status: `(\w+)`; placement: (\w+)\.\n.*?\* Caption: (.*?)\n\* Review: (.*?)\n\* Sources \(path, SHA-256\):\n(.*?)\n\n", t, re.S | re.M):
        aid, status, place, cap, rev, src = m.groups()
        srcs = re.findall(r"`([^`]+)` `([0-9a-f]{64})`", src)
        out.append({"id": aid, "status": status, "placement": place, "caption": cap, "review": rev, "sources": srcs})
    return out


def intended(aid: str, status: str, place: str) -> str:
    if aid in INTENDED:
        return INTENDED[aid]
    for p, g in GROUPS:
        if aid.startswith(p + "_"):
            return g
    return "Main text" if place == "main_text" else "Supplementary material"


def write_indexes(recs: list[dict], rows: list):
    for kind, folder, name, exts in (("FIG", "02_FIGURES", "FIGURE_INDEX", "pdf svg png"), ("TAB", "03_TABLES", "TABLE_INDEX", "csv tex md")):
        sel = [r for r in recs if r["id"].startswith(kind)]
        lines = [f"# {'Figure' if kind == 'FIG' else 'Table'} index", "",
                 "Refer to an asset by its ID. Each asset exists in the formats listed; the formats are one asset. Statuses: `MAIN_TEXT_ELIGIBLE`, `SUPPLEMENTARY_ELIGIBLE`, `DIAGNOSTIC_ONLY` (never the main text). "
                 "Captions are as written in the asset catalog; do not strengthen them. Full source hashes and review notes: `05_RESULTS_AND_PROVENANCE/ASSET_CATALOG.md`.", "",
                 "| ID | Status | Intended location | Formats | Sources (paths) |", "|---|---|---|---|---|"]
        recs_csv = []
        for r in sel:
            loc = intended(r["id"], r["status"], r["placement"])
            srcs = "; ".join(p for p, _ in r["sources"]) or "none (schematic or register)"
            lines.append(f"| `{r['id']}` | `{r['status']}` | {loc} | {exts} | {srcs} |")
            recs_csv.append({"id": r["id"], "status": r["status"], "intended_location": loc, "caption": r["caption"], "review_note": r["review"], "sources": srcs})
        lines += ["", "## Captions and limitations", ""]
        for r in sel:
            lines += [f"### {r['id']}", "", f"* Status: `{r['status']}`; intended location: {intended(r['id'], r['status'], r['placement'])}.", f"* Caption: {r['caption']}", f"* What it does and does not establish: {r['review']}", ""]
        d = PKG / folder
        (d / f"{name}.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
        with open(d / f"{name}.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(recs_csv[0].keys()), lineterminator="\n")
            w.writeheader()
            w.writerows(recs_csv)
        for f in (f"{name}.md", f"{name}.csv"):
            p = d / f
            rows.append({"path": p.relative_to(PKG).as_posix(), "sha256_lf_normalised_for_text": sha_lf(p), "bytes": p.stat().st_size, "category": "index", "kind": "documentation", "repo_path": "(generated from ASSET_CATALOG.md)", "note": ""})


def build(commit: str, branch: str):
    for g in GENERATED:
        if (PKG / g).exists():
            shutil.rmtree(PKG / g)
    rows: list[dict] = []
    # 01 manuscript
    for f in ("manuscript.md", "references.bib", "README.md"):
        copy(CAND / f, PKG / "01_MANUSCRIPT" / f, "manuscript", "editable manuscript" if f == "manuscript.md" else "documentation", rows)
    ms = (CAND / "manuscript.md").read_text(encoding="utf-8").split("\n")
    heads = [l for l in ms if l.startswith("#")]
    title = ms[0]
    abstract = ms[ms.index("## Abstract") + 2]
    outline = ["# Title, abstract and section outline (extracted from manuscript.md)", "", f"**Title:** {title.lstrip('# ')}", "", "**Abstract:**", "", abstract, "", "## Section outline", ""] + [f"* {h}" for h in heads]
    p = PKG / "01_MANUSCRIPT" / "TITLE_ABSTRACT_OUTLINE.md"
    p.write_text("\n".join(outline) + "\n", encoding="utf-8", newline="\n")
    rows.append({"path": p.relative_to(PKG).as_posix(), "sha256_lf_normalised_for_text": sha_lf(p), "bytes": p.stat().st_size, "category": "manuscript", "kind": "documentation", "repo_path": "(extracted)", "note": ""})
    sp = (CAND / "SUBMISSION_PREPARATION.md").read_text(encoding="utf-8")
    s3 = sp[sp.index("## 3. Fields requiring author confirmation"):sp.index("## 4. Draft availability wording")]
    s4 = sp[sp.index("## 4. Draft availability wording"):sp.index("## 5. Terminology rule")]
    s6 = sp[sp.index("## 6. Author decision register"):]
    dec = ["# Open author decisions and placeholders", "", "Extracted from `submission_candidate_as_run_only/SUBMISSION_PREPARATION.md`. Nothing here is decided and no author detail may be invented; the writer leaves these as placeholders for the authors.", "",
           "The manuscript candidate itself states that authors, affiliations and acknowledgements are not filled in, that it is not submission-ready, that venue selection is open and that amendments are not countersigned.", "", s3, s4, s6]
    p = PKG / "01_MANUSCRIPT" / "OPEN_DECISIONS_AND_PLACEHOLDERS.md"
    p.write_text("\n".join(dec) + "\n", encoding="utf-8", newline="\n")
    rows.append({"path": p.relative_to(PKG).as_posix(), "sha256_lf_normalised_for_text": sha_lf(p), "bytes": p.stat().st_size, "category": "manuscript", "kind": "documentation", "repo_path": "(extracted)", "note": ""})
    # 02, 03 figures and tables
    for sect in ("main_text", "supplementary"):
        for f in sorted((ASSETS / "figures" / sect).glob("*")):
            copy(f, PKG / "02_FIGURES" / sect / f.name, "figure", "figure", rows)
        for f in sorted((ASSETS / "tables" / sect).glob("*")):
            copy(f, PKG / "03_TABLES" / sect / f.name, "table", "table", rows)
    recs = parse_catalog()
    write_indexes(recs, rows)
    # 04 code
    for sub in ("src/alphacomb", "pipelines", "tools", "tests"):
        for f in sorted((ROOT / sub).rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts and f.suffix not in {".pyc"} and "egg-info" not in str(f):
                copy(f, PKG / "04_RESEARCH_CODE" / f.relative_to(ROOT), "code", "source code", rows)
    for f in sorted((ROOT / "configs").glob("*.yaml")) + [ROOT / "pyproject.toml", ROOT / "README.md"]:
        copy(f, PKG / "04_RESEARCH_CODE" / f.relative_to(ROOT), "code", "source code", rows)
    repro = ("# Reproducing what can be reproduced\n\nThis folder is a **copy** of code from the Git repository (source of truth), prepared from commit `%s` on branch `%s`. "
             "Do not edit it; changes belong in the repository.\n\n## What runs from tracked files alone\n\n```\npip install -e .            # from the repository root; needs Python 3.12 with pandas, numpy, matplotlib, pyyaml, pytest\n"
             "python tools/check_submission_candidate.py     # citations, hashes, every manuscript number re-derived\npython tools/check_withdrawn_claims.py         # screen for withdrawn wording\n"
             "python tools/make_paper_assets.py              # regenerates paper_assets_as_run_only/ (figures and tables)\npython tools/make_paper_assets.py --verify     # checks the folder against its manifest\n"
             "python tools/make_figures.py                   # the candidate's Figures 1 and 2\n```\n\nTests: run one directory at a time to stay within memory, for example `python -m pytest tests/tools -o addopts= -p no:cacheprovider -q`, then `tests/validation`, `tests/tax`, and the other directories under `tests/`. "
             "The last validated state was 715 passed across 13 sequential batches (not a single full-suite invocation).\n\n## What needs data that is not in this package\n\nThe heavy stages that produced the committed result snapshots (model training, portfolio construction, the lot-level backtest) read licensed vendor-derived panels that are not redistributed. "
             "Their outputs are committed as snapshots with hashes. Regenerating the snapshots is not part of the writing task and must not be attempted without the research owner.\n\nPhase C is blocked and must not be run.\n" % (commit[:7], branch))
    p = PKG / "04_RESEARCH_CODE" / "REPRODUCE.md"
    p.write_text(repro, encoding="utf-8", newline="\n")
    rows.append({"path": p.relative_to(PKG).as_posix(), "sha256_lf_normalised_for_text": sha_lf(p), "bytes": p.stat().st_size, "category": "code", "kind": "documentation", "repo_path": "(generated)", "note": ""})
    p = PKG / "04_RESEARCH_CODE" / "SOURCE_COMMIT.txt"
    p.write_text(f"repository: {git('remote', 'get-url', 'origin')}\nbranch: {branch}\ncommit: {commit}\nnote: copy of code for reading; the Git repository is canonical\n", encoding="utf-8", newline="\n")
    rows.append({"path": p.relative_to(PKG).as_posix(), "sha256_lf_normalised_for_text": sha_lf(p), "bytes": p.stat().st_size, "category": "code", "kind": "documentation", "repo_path": "(generated)", "note": ""})
    # 05 results and provenance
    for f in ("TRACEABILITY.csv",):
        copy(CAND / f, PKG / "05_RESULTS_AND_PROVENANCE" / f, "provenance", "documentation", rows)
    for f in ("ASSET_CATALOG.md", "ASSET_MANIFEST.csv"):
        copy(ASSETS / f, PKG / "05_RESULTS_AND_PROVENANCE" / f, "provenance", "documentation", rows)
    for f in PROV_DOCS:
        copy(ROOT / "docs" / f, PKG / "05_RESULTS_AND_PROVENANCE" / f, "provenance", "documentation", rows)
    short = {"phase_c_after_tax_config_recovery_2026-10-14": "after_tax_config_recovery", "phase_c_census_v3_2026-10-14": "census_v3", "capacity_return_difference": "capacity", "cost_parity_diagnostic": "cost_parity", "figures": "figures"}
    trace = list(csv.DictReader(open(CAND / "TRACEABILITY.csv", encoding="utf-8")))
    seen = set()
    for r in trace:
        rp = r["path"]
        if "tierB_monthly" in rp or rp in seen or r["key"].startswith("capinf_"):
            continue
        seen.add(rp)
        copy(ROOT / rp, PKG / "05_RESULTS_AND_PROVENANCE" / "result_snapshots" / (Path(rp).relative_to(Path(rp).parts[0]) if rp.startswith("docs/") else Path("results") / short.get(Path(rp).parts[1], Path(rp).parts[1]) / Path(rp).parts[2]), "result", "result snapshot", rows, "licence of vendor-derived aggregates not verified; see README data and licensing note")
    short = {"phase_c_after_tax_config_recovery_2026-10-14": "after_tax_config_recovery", "phase_c_census_v3_2026-10-14": "census_v3", "capacity_return_difference": "capacity", "cost_parity_diagnostic": "cost_parity", "figures": "figures"}
    for rp in RESULT_RES:
        if rp in seen:
            continue
        seen.add(rp)
        parts = Path(rp).parts      # results/<dir>/<file>: shortened directory names keep Windows paths under the limit
        copy(ROOT / rp, PKG / "05_RESULTS_AND_PROVENANCE" / "result_snapshots" / "results" / short.get(parts[1], parts[1]) / parts[2], "result", "result snapshot", rows, "licence of vendor-derived aggregates not verified; see README data and licensing note")
    # 06 literature
    for f in ("references.bib", "BIB_PROVENANCE.csv"):
        copy(CAND / f, PKG / "06_LITERATURE" / f, "literature", "documentation", rows)
    for f in LIT_DOCS:
        copy(ROOT / "docs" / f, PKG / "06_LITERATURE" / f, "literature", "documentation", rows)
    # 07 limitations
    for f in LIMIT_DOCS:
        copy(ROOT / "docs" / f, PKG / "07_LIMITATIONS_AND_OPEN_ITEMS" / f, "limitations", "documentation", rows)
    idx = ["# Limitations and open items: index", "", "* Phase C status and reopening prerequisites: `PHASE_C_VENDOR_COVERAGE_FEASIBILITY_2026-10-14.md`, `PHASE_C_RUN_READINESS_V2_2026-10-14.md`, `PHASE_C_REVISED_ANALYSIS_SPEC_2026-10-14.md` (reopening needs vendor access and documentation, a month-level flag query, written owner authorisation and a dated addendum).",
           "* Exit-treatment limitation: `EXIT_POLICY_RULING_AND_001E_RESPONSE_2026-10-13.md`, `NON_TRADEABLE_TREATMENT.md` (the sensitivity of the as-run numbers is unknown).",
           "* Japan prediction scorecard: `AMENDMENT_001C_JAPAN_PREDICTION_SCORECARD.md` (the amendment text is `AMENDMENT_001C_CAPACITY_HYPOTHESIS_PREREGISTRATION.md`; its filename uses a word the paper must not use: it is a repository commit by the project team, not countersigned).",
           "* Germany inference-statistic exclusion and the data-provenance gaps: `FINAL_NUMERICAL_TRACEABILITY_GAPS.md`.", "* Withdrawn claims and the reasons: `FINALIZATION_AUDIT_2026-10-09.md` section 1.2.", "* Inference limits: `INFERENCE_AUDIT_2026-10-13.md`.", "* Economic-arm exclusion: `ECONOMIC_ARM_CAPABILITY_GAP.md`.",
           "* Newer findings: see `PROJECT_COMPLETION_REPORT.md` section 8b in `05_RESULTS_AND_PROVENANCE/` (India 2009-10 coverage month; Tier A versus Tier B differences).", "", "Nothing in this folder may be turned into a claim; it explains what the paper cannot say."]
    p = PKG / "07_LIMITATIONS_AND_OPEN_ITEMS" / "LIMITATIONS_INDEX.md"
    p.write_text("\n".join(idx) + "\n", encoding="utf-8", newline="\n")
    rows.append({"path": p.relative_to(PKG).as_posix(), "sha256_lf_normalised_for_text": sha_lf(p), "bytes": p.stat().st_size, "category": "limitations", "kind": "documentation", "repo_path": "(generated)", "note": ""})
    # 00 (hand-written) and status
    for f in sorted((PKG / "00_START_HERE").glob("*.md")):
        rows.append({"path": f.relative_to(PKG).as_posix(), "sha256_lf_normalised_for_text": sha_lf(f), "bytes": f.stat().st_size, "category": "start_here", "kind": "documentation", "repo_path": f.relative_to(ROOT).as_posix(), "note": ""})
    f = PKG / "HANDOFF_STATUS.md"
    if f.exists():
        rows.append({"path": f.name, "sha256_lf_normalised_for_text": sha_lf(f), "bytes": f.stat().st_size, "category": "start_here", "kind": "documentation", "repo_path": f.relative_to(ROOT).as_posix(), "note": ""})
    return rows


def write_manifest(rows: list[dict], commit: str, drive: dict):
    with open(PKG / "HANDOFF_MANIFEST.csv", "w", encoding="utf-8", newline="") as fh:
        fields = ["path", "sha256_lf_normalised_for_text", "bytes", "category", "kind", "repo_path", "source_commit", "in_drive", "in_github", "note"]
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in sorted(rows, key=lambda r: r["path"]):
            r = dict(r, source_commit=commit[:7], in_github=GITHUB_STATUS, in_drive=(drive.get(r["path"]) and "yes" or "pending"))
            w.writerow(r)
        for pat, why in EXCLUDED:
            w.writerow({"path": pat, "category": "EXCLUDED", "kind": "excluded", "note": why, "in_drive": "no", "in_github": "n/a", "source_commit": commit[:7]})


def make_archive(commit: str) -> Path:
    z = ROOT / f"research_handoff_for_writing_{commit[:7]}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(PKG.rglob("*")):
            if f.is_file():
                zi = zipfile.ZipInfo(f.relative_to(ROOT).as_posix(), (2026, 10, 14, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(zi, f.read_bytes())
    h = hashlib.sha256(z.read_bytes()).hexdigest()
    (ROOT / (z.name + ".sha256")).write_text(f"{h}  {z.name}\n", encoding="utf-8", newline="\n")
    return z


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive-map", type=Path)
    ap.add_argument("--commit", default=None, help="source commit to record (default: the commit of HEAD at the time the code and assets were last changed)")
    a = ap.parse_args()
    commit = a.commit or git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    drive = json.load(open(a.drive_map, encoding="utf-8")) if a.drive_map else {}
    rows = build(commit, branch)
    write_manifest(rows, commit, drive)
    z = make_archive(commit)
    print(f"{len(rows)} files; archive {z.name} ({z.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
