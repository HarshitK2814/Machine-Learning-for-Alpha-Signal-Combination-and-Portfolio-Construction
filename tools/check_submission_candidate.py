#!/usr/bin/env python
"""Consistency check for ``submission_candidate_as_run_only/`` (no TeX toolchain is installed; this is the build check).

It does NOT validate the science. It verifies, deterministically:
  1. every ``[@key]`` citation resolves to an entry in the candidate ``references.bib``; each entry is identical to the
     one in the generated ``research/08_References/references.bib`` or has a row in ``BIB_PROVENANCE.csv``;
  2. every artifact in ``TRACEABILITY.csv`` exists and matches its recorded SHA-256;
  3. every headline number quoted in the manuscript re-derives from the committed artifact (formatted strings
     computed here must occur in the manuscript);
  4. Table/Figure references are defined, referenced figure files exist;
  5. required disclosures are present and no banned claim wording appears.

    python tools/check_submission_candidate.py            # check
    python tools/check_submission_candidate.py --write-traceability   # (re)write TRACEABILITY.csv hashes
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "submission_candidate_as_run_only"
ATT = "docs/attachments/"
ARTIFACTS = {
    "after_tax_inference": ATT + "AFTER_TAX_INFERENCE_1E9_2026-10-09.csv",
    "matched_1e9": ATT + "MATCHED_BOOK_1E+09_2026-10-09.csv",
    "matched_1e8": ATT + "MATCHED_BOOK_1E+08_2026-10-09.csv",
    "matched_3e7": ATT + "MATCHED_BOOK_3E+07_2026-10-09.csv",
    "gate2": ATT + "GATE2_POWER_1E9_2026-10-09.csv",
    "design_deu": ATT + "DESIGN_IDENTIFIABILITY_DEU_2026-10-09.csv",
    "design_ind": ATT + "DESIGN_IDENTIFIABILITY_IND_2026-10-09.csv",
    "capinf_deu_noncompliant": ATT + "CAPACITY_CHANNEL_INFERENCE_DEU_2026-10-09.csv",
    "capinf_deu_cov": ATT + "CAPACITY_CHANNEL_INFERENCE_DEU_COV_2026-10-09.csv",
    "tierB_DEU": "results/capacity_return_difference/tierB_DEU.csv",
    "tierB_IND": "results/capacity_return_difference/tierB_IND.csv",
    "tierB_JPN": "results/capacity_return_difference/tierB_JPN.csv",
    "coverage": "results/phase_c_census_v3_2026-10-14/input_coverage_by_country_month.csv",
    "fig1": "results/figures/fig1_capacity_return_difference_B.png",
    "fig2": "results/figures/fig2_uncapped_terminal_wealth.png",
    "sum_deu_1e9": ATT + "SUMMARY_AFTER_TAX_DEU_1E9_2026-10-09.csv",
    "sum_ind_1e9": ATT + "SUMMARY_AFTER_TAX_IND_1E9_2026-10-09.csv",
    "sum_deu_1e8": ATT + "SUMMARY_AFTER_TAX_DEU_1E8_2026-10-09.csv",
    "sum_deu_1e10": ATT + "SUMMARY_AFTER_TAX_DEU_1E10_2026-10-09.csv",
    "sum_jpn_1e8": ATT + "SUMMARY_AFTER_TAX_JPN_1E8_2026-10-09.csv",
    "sum_jpn_1e9": ATT + "SUMMARY_AFTER_TAX_JPN_1E9_2026-10-09.csv",
    "sum_jpn_1e10": ATT + "SUMMARY_AFTER_TAX_JPN_1E10_2026-10-09.csv",
}
TABLE2_RUNGS = {"DEU": [(1e5, "$100k", "Germany"), (1e6, "$1mn", "Germany"), (1e7, "$10mn", "Germany"), (1e8, "$100mn", "Germany")],
                "IND": [(1e5, "$100k", "India"), (1e6, "$1mn", "India"), (3e7, "$30mn", "India")],
                "JPN": [(1e5, "$100k", "Japan"), (1e9, "$1bn", "Japan"), (1e10, "$10bn", "Japan")]}
REQUIRED_PHRASES = ["Phase C", "has **not been run**", "as_run", "not countersigned", "Not submission-ready",
                    "(abstract level", "exploratory, not pre-specified"]
# Wording that must never appear in the candidate (the withdrawn-claims screen covers the figures).
BANNED = [r"pre-?registered (result|analysis|confirm)", r"confirmatory (result|sample|analysis)(?! status)", r"pre-specified (result|analysis)", r"\bH-FLIP CONFIRMED\b", r"established (economic )?gain", r"cap(?: never| does not) hurts?\b(?! at)",
          r"Maham (approved|acknowledged)", r"approved by (Maham|Absar)", r"submission[- ]ready\b(?!\.)(?<!not submission-ready)"]


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def art(key: str) -> Path:
    return ROOT / ARTIFACTS[key]


def derived_strings() -> dict[str, str]:
    """Strings that must occur in the manuscript, each computed from a committed artifact."""
    out: dict[str, str] = {}
    mb = {c: pd.read_csv(art(k)) for c, k in (("1e9", "matched_1e9"),)}["1e9"]
    for c, name in (("DEU", "Germany"), ("IND", "India"), ("JPN", "Japan")):
        r = mb[(mb.country == c) & (mb.book == "capped")].iloc[0]
        out[f"table1_{c}"] = (f"| {name} | {r.sharpe_net:+.3f} | {r.net_t_vs_zero:+.2f} | {r.tax_channel:+.3f} | "
                              f"{r.tax_t:+.2f} | {r.tax_p:.3f} |")
    at = pd.read_csv(art("after_tax_inference"))
    comp = at[at.scope == "composite"].set_index("country")
    i, j = comp.loc["IND"], comp.loc["JPN"]
    out["ind_net"] = f"India {i.sharpe_net:+.3f} (t {i.t_net:+.2f}, p {i.p_net:.3f}; after tax {i.sharpe_after_tax:+.3f}, t {i.t_after_tax:+.2f})"
    out["jpn_net"] = f"Japan {j.sharpe_net:+.3f} (t {j.t_net:+.2f}, p {j.p_net:.3f}; after tax {j.sharpe_after_tax:+.3f}, t {j.t_after_tax:+.2f})"
    out["opt_tax"] = (f"Japanese tax channel is {j.tax_channel:.4f} (t {j.t:.2f}, {int(j.cells_holm_sig)} of 8 cells significant under Holm) "
                      f"and the Indian {i.tax_channel:.4f} (t {i.t:.2f}, {int(i.cells_holm_sig)} of 8)")
    gross = (pd.read_csv(art("matched_1e8")).query("country=='DEU' and book=='uncapped'").sharpe_gross.iloc[0],
             pd.read_csv(art("matched_3e7")).query("country=='IND' and book=='uncapped'").sharpe_gross.iloc[0],
             mb.query("country=='JPN' and book=='uncapped'").sharpe_gross.iloc[0])
    out["gross"] = f"+{gross[0]:.3f} (Germany), +{gross[1]:.3f} (India) and +{gross[2]:.3f} (Japan)"
    cov = pd.read_csv(art("coverage"))
    cov["c"] = cov.c4_with_certified_c6 / cov.c4_in_c1_universe
    m = cov.groupby("country")["c"].mean()
    out["coverage"] = f"{m['DEU']:.3f} in Germany, {m['IND']:.3f} in India and {m['JPN']:.3f} in Japan"
    # B(A) rungs
    n_solv, n_sig, n_nr, n_mono = {}, {}, {}, {}
    for c in ("DEU", "IND", "JPN"):
        t = pd.read_csv(art(f"tierB_{c}")).sort_values("aum")
        n_solv[c], n_sig[c] = len(t), int((t.p_holm < 0.05).sum())
        n_nr[c], n_mono[c] = int((t.uncapped_terminal_wealth < 0.1).sum()), bool(t.B.diff().dropna().gt(0).all())
        for aum, label, nm in TABLE2_RUNGS[c]:
            r = t[t.aum == aum].iloc[0]
            w = r.uncapped_terminal_wealth
            out[f"table2_{c}_{label}"] = (f"| {nm} | {label} | {r.B * 100:+.2f} | [{r.B_ci_low * 100:+.2f}, {r.B_ci_high * 100:+.2f}] | {r.p_holm:.3f} |")
            out[f"table2w_{c}_{label}"] = w
    out["b_counts"] = (f"Holm-significant at {n_sig['DEU']} of {n_solv['DEU']} German, {n_sig['IND']} of {n_solv['IND']} Indian "
                       f"and {n_sig['JPN']} of {n_solv['JPN']} Japanese rungs")
    out["nearruined"] = (f"below 0.1 at {n_nr['DEU']} of {n_solv['DEU']} German, {n_nr['IND']} of {n_solv['IND']} Indian "
                         f"and {n_nr['JPN']} of {n_solv['JPN']} Japanese rungs")
    out["monotone"] = str(all(n_mono.values()))
    out["rungs"] = f"all {sum(n_solv.values())} solvent rungs (Germany {n_solv['DEU']}, India {n_solv['IND']}, Japan {n_solv['JPN']})"
    # design
    for c, k in (("Germany", "design_deu"), ("India", "design_ind")):
        d = pd.read_csv(art(k))
        for book in ("capped", "uncapped"):
            g = d[d.book == book]
            out[f"design_{c}_{book}"] = f"{int((g.p_holm < 0.05).sum())} of {len(g)}"
    g2 = pd.read_csv(art("gate2"))
    se = g2.se
    out["mde"] = f"{2.8 * se.min():.2f} to {2.8 * se.max():.2f}"
    jc = g2[(g2.country == "JPN") & (g2.axis == "conditioning")].iloc[0]
    out["jpn_cond"] = f"effect {jc.effect:+.3f} (t {jc.t:+.2f})"
    # coverage failure
    nc = pd.read_csv(art("capinf_deu_noncompliant"))
    nc = nc[(nc.scope == "composite") & (nc.aum == 1e5)].iloc[0]
    cv = pd.read_csv(art("capinf_deu_cov"))
    cv = cv[(cv.scope == "composite") & (cv.aum == 1e5)].iloc[0]
    out["noncompliant_t"] = f"t = {nc.t_stat:.3f} at $100k"
    out["compliant"] = f"{cv.capacity_channel:+.3f}, t {cv.t_stat:+.2f}"
    # lt_share
    mx = 0.0
    n = 0
    for k in ("sum_deu_1e8", "sum_deu_1e10", "sum_jpn_1e8", "sum_jpn_1e9", "sum_jpn_1e10"):
        d = pd.read_csv(art(k))
        s = d[d.regime != "tax_exempt"]
        mx, n = max(mx, float(s.lt_share_of_gains.abs().max())), n + len(s)
    tv = {}
    for c, k in (("DEU", "sum_deu_1e9"), ("IND", "sum_ind_1e9"), ("JPN", "sum_jpn_1e9")):
        d = pd.read_csv(art(k))
        sp = d[(d.regime != "tax_exempt") & d.strategy.str.contains("-P-")]
        tv[c] = (sp.turnover_mean.mean(), sp.tax_drag_ann_bps.mean(), sp.lt_share_of_gains.mean())
    out["turnover"] = (f"turnover {tv['DEU'][0]:.4f} / {tv['IND'][0]:.4f} / {tv['JPN'][0]:.4f} (Germany / India / Japan) "
                       f"and tax drag {tv['DEU'][1]:.2f} / {tv['IND'][1]:.2f} / {tv['JPN'][1]:.2f} basis points per year")
    out["lt_india"] = f"{tv['IND'][2]:.4f} in India"
    nets = {}
    for c, k in (("DEU", "sum_deu_1e9"), ("JPN", "sum_jpn_1e9")):
        d = pd.read_csv(art(k))
        nets[c] = d[(d.regime == "tax_exempt") & d.strategy.str.contains("-P-")].net_sharpe.mean()
    dd = pd.read_csv(art("sum_deu_1e9"))
    dd = dd[(dd.regime != "tax_exempt") & dd.strategy.str.contains("-P-")]
    out["deu_summary"] = f"net Sharpe {nets['DEU']:+.3f} and after-tax Sharpe {dd.after_tax_sharpe.mean():+.3f}"
    out["p2"] = f"Japan's is {nets['JPN']:+.3f} against Germany's {nets['DEU']:+.3f}"
    comp_j = at[at.scope == "composite"].set_index("country").loc["JPN"]
    out["p2_composite"] = f"{comp_j.sharpe_net:+.3f} for the composite"
    rungs = []
    drags = []
    for k in ("sum_jpn_1e8", "sum_jpn_1e9", "sum_jpn_1e10"):
        dj = pd.read_csv(art(k))
        dj = dj[(dj.regime == "tax_exempt") & dj.strategy.str.contains("-P-")]
        rungs.append(dj.net_sharpe.mean())
        drags.append(dj.cost_drag_ann_bps.mean())
    out["jpn_rungs"] = f"({rungs[0]:+.3f}, {rungs[1]:+.3f}, {rungs[2]:+.3f})"
    out["jpn_nonmonotone"] = "True" if not (rungs[0] < rungs[1] < rungs[2] or rungs[0] > rungs[1] > rungs[2]) else "False"
    out["jpn_cost_falls"] = "True" if drags[0] > drags[1] > drags[2] else "False"
    out["lt_zero"] = f"80 rows across five summaries" if (mx == 0.0 and n == 80) else f"MISMATCH max={mx} rows={n}"
    return out


def check() -> list[str]:
    errs: list[str] = []
    ms = (CAND / "manuscript.md").read_text(encoding="utf-8")
    # 1 citations
    bib = (CAND / "references.bib").read_text(encoding="utf-8")
    main_bib = (ROOT / "research/08_References/references.bib").read_text(encoding="utf-8")

    def entries(t: str) -> dict[str, str]:
        return {m.group(1): e.strip() for e in re.split(r"\n(?=@)", t) if (m := re.match(r"@\w+\{([^,]+),", e))}
    cand_e, main_e = entries(bib), entries(main_bib)
    cited = set(re.findall(r"@([A-Za-z0-9]+)", " ".join(re.findall(r"\[(@[^\]]+)\]", ms))))
    for k in sorted(cited):
        if k not in cand_e:
            errs.append(f"citation @{k} has no entry in candidate references.bib")
    prov = {r["key"]: r for r in csv.DictReader(open(CAND / "BIB_PROVENANCE.csv", encoding="utf-8"))}
    for k, e in cand_e.items():
        # an entry that differs from (or is absent in) the generated project bibliography needs a provenance row
        if main_e.get(k) != e and k not in prov:
            errs.append(f"bib entry {k} differs from research/08_References/references.bib and has no BIB_PROVENANCE.csv row")
        if k not in cited:
            errs.append(f"bib entry {k} is not cited")
    for k in prov:
        if k not in cand_e:
            errs.append(f"BIB_PROVENANCE.csv row {k} has no bib entry")
    # 2 artifacts
    rows = list(csv.DictReader(open(CAND / "TRACEABILITY.csv", encoding="utf-8")))
    seen = {r["key"] for r in rows}
    for k in ARTIFACTS:
        if k not in seen:
            errs.append(f"artifact {k} missing from TRACEABILITY.csv")
    for r in rows:
        p = ROOT / r["path"]
        if not p.exists():
            errs.append(f"missing artifact {r['path']}")
        elif sha(p) != r["sha256"]:
            errs.append(f"hash mismatch {r['path']}")
    # 3 derived numbers
    d = derived_strings()
    for k, v in d.items():
        if k.startswith("table2w_"):
            continue
        if k == "monotone":
            if v != "True":
                errs.append("B(A) not monotone in AUM")
            continue
        if k == "jpn_nonmonotone":
            if v != "True":
                errs.append("Japan net Sharpe is monotone: manuscript statement is wrong")
            continue
        if k == "jpn_cost_falls":
            if v != "True":
                errs.append("Japan cost drag does not fall: manuscript statement is wrong")
            continue
        if isinstance(v, str) and (v not in ms):
            errs.append(f"derived string not in manuscript [{k}]: {v}")
    for k, v in d.items():       # terminal wealth: last cell of the Table 2 row, within 6% of the artifact
        if not k.startswith("table2w_"):
            continue
        _, c, label = k.split("_", 2)
        name = {"DEU": "Germany", "IND": "India", "JPN": "Japan"}[c]
        row = next((l for l in ms.splitlines() if l.startswith(f"| {name} | {label} |")), None)
        try:
            cell = float(row.strip().strip("|").split("|")[-1])
        except Exception:
            errs.append(f"terminal-wealth cell not found [{k}]")
            continue
        if abs(cell - v) > 0.06 * abs(v):
            errs.append(f"terminal wealth mismatch [{k}]: manuscript {cell} artifact {v:.4g}")
    # 4 table / figure refs
    for kind in ("Table", "Figure"):
        defined = set(re.findall(rf"\*\*{kind} (\d+)\.", ms))
        used = set(re.findall(rf"{kind} (\d+)", ms))
        for n in sorted(used - defined):
            errs.append(f"{kind} {n} referenced but not defined")
    for m in re.findall(r"`(results/figures/[^`]+\.png)`", ms):
        if not (ROOT / m).exists():
            errs.append(f"figure file missing {m}")
    # 5 disclosures and banned wording
    for ph in REQUIRED_PHRASES:
        if ph not in ms:
            errs.append(f"required disclosure missing: {ph}")
    for pat in BANNED:
        for mm in re.finditer(pat, ms, re.I):
            errs.append(f"banned wording: {mm.group(0)}")
    return errs


def write_traceability() -> None:
    with open(CAND / "TRACEABILITY.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "path", "sha256", "tracked_in_git"])
        for k, rel in ARTIFACTS.items():
            w.writerow([k, rel, sha(ROOT / rel), "yes"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-traceability", action="store_true")
    a = ap.parse_args()
    if a.write_traceability:
        write_traceability()
        print("wrote TRACEABILITY.csv")
        return 0
    errs = check()
    if errs:
        print("FAIL:")
        for e in errs:
            print("  " + e)
        return 1
    print("PASS: citations, hashes, derived numbers, cross-references and disclosures are consistent. "
          "This is a consistency check, not scientific validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
