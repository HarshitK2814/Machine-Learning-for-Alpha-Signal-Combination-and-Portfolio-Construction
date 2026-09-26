# -*- coding: utf-8 -*-
"""Shared loaders: references (with Crossref DOI resolution), citation formatting, idea scores, md tables."""
import csv, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "_build")
if BUILD not in sys.path:
    sys.path.insert(0, BUILD)

from lit_core import CORE            # noqa: E402
from lit_other import OTHER, S       # noqa: E402
from lit_tax_online import TAX_ONLINE  # noqa: E402
from ideas_data import IDEAS, ACADEMIC, WEIGHTS  # noqa: E402
from journal_data import J           # noqa: E402
from experiments_data import EXPERIMENTS  # noqa: E402

REPORTS = os.path.join(ROOT, "09_Reports")
FIGS = os.path.join(REPORTS, "figures")

EXTRA = [
    S("CST2002", "Clarke, R.; de Silva, H.; Thorley, S.", 2002, "Portfolio Constraints and the Fundamental Law of Active Management",
      "Financial Analysts Journal", "T3 Practitioner", "Portfolio construction", 4,
      "Introduces the transfer coefficient: constraints limit how much forecast information reaches portfolio weights.",
      "Transfer-coefficient reporting in our metrics."),
    S("MICH1989", "Michaud, R.O.", 1989, "The Markowitz Optimization Enigma: Is 'Optimized' Optimal?",
      "Financial Analysts Journal", "T3 Practitioner", "Portfolio construction", 3,
      "Mean-variance optimisers act as estimation-error maximisers.", "Error-maximisation argument."),
    S("BP1998", "Bai, J.; Perron, P.", 1998, "Estimating and Testing Linear Models with Multiple Structural Changes",
      "Econometrica", "Econometrics general", "Statistical inference", 3,
      "Estimation and tests for multiple structural breaks.", "Stability tests of cell differences."),
]

MANUAL_DOI = {
    "MARK1952": "10.1111/j.1540-6261.1952.tb01525.x",
    "DGU2009": "10.1093/rfs/hhm075",
}
NO_DOI_NOTE = {
    "Book": "Book (no DOI recorded)",
    "WP": "Working paper (journal DOI not available/verified)",
    "ML venue": "Conference/ML venue (not in Crossref or not matched)",
    "Industry": "Industry white paper (no DOI)",
    "Survey": "Survey (DOI not matched; verify)",
}
BAD_CONTAINER = ("handbook", "heuristics", "ssrn", "nber", "cran", "water", "neurocomputing", "findings of",
                 "ieee international conference", "proceedings of ieee", "portfolio optimization", "optimization",
                 "discussion series")


def _norm(s):
    s = (s or "").lower().replace("&amp;", "&")
    s = re.sub(r"^the\s+", "", s)
    return re.sub(r"[^a-z0-9& ]", "", s).strip()


def _rank(v):
    return {"MATCH": 3, "CHECK": 2, "WP_VERSION": 1}.get(v.get("status"), 0)


def load_crossref():
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "08_References", "crossref_raw", "crossref_*.json"))):
        for k, v in json.load(open(f, encoding="utf-8")).items():
            if k not in out or _rank(v) > _rank(out[k]):
                out[k] = v
    return out


def load_refs():
    refs = {}
    for r in CORE + OTHER + TAX_ONLINE + EXTRA:
        if r["id"] in refs:
            continue  # core entries take precedence
        refs[r["id"]] = dict(r)
    cr = load_crossref()
    for pid, r in refs.items():
        c = cr.get(pid)
        r["crossref_status"] = c.get("status") if c else "not queried"
        r["crossref_doi"] = (c or {}).get("doi") or ""
        r["crossref_title"] = (c or {}).get("title") or ""
        r["crossref_journal"] = ((c or {}).get("journal") or "").replace("&amp;", "&")
        venue_n = _norm(r["venue"])
        doi, how = r.get("doi") or "", ""
        if doi:
            how = "DOI from publisher page/search"
            if c and c.get("doi", "").lower() == doi.lower():
                how += "; Crossref-confirmed"
        elif pid in MANUAL_DOI:
            doi, how = MANUAL_DOI[pid], "Publisher record (manual)"
        elif c and c.get("status") == "MATCH":
            doi, how = c["doi"], "Crossref match (title, author, year, journal)"
        elif c and c.get("status") == "CHECK":
            cont = _norm(c.get("journal"))
            y_ok = c.get("year") and abs(int(c["year"]) - int(r["year"])) <= 2
            if (c.get("title_similarity", 0) >= 0.97 and cont and not any(b in cont for b in BAD_CONTAINER)
                    and cont in venue_n and y_ok):
                doi, how = c["doi"], "Crossref match (online/issue year differs)"
        if not doi:
            how = NO_DOI_NOTE.get(r["tier"], "No DOI verified")
        r["doi"], r["doi_status"] = doi, how
        # Fill volume/pages for venues without them when Crossref matched the journal
        if doi and c and c.get("doi", "").lower() == doi.lower() and ":" not in r["venue"] and c.get("vol"):
            pages = f":{c['pages']}" if c.get("pages") else ""
            issue = f"({c['issue']})" if c.get("issue") else ""
            r["venue"] = f"{r['venue']} {c['vol']}{issue}{pages}"
    return refs


# ---------------- citation formatting ----------------
def surnames(authors):
    out = []
    for p in [p.strip() for p in authors.split(";") if p.strip()]:
        out.append("et al." if p.lower().startswith("et al") else p.split(",")[0].strip())
    return out


def short_author(r):
    s = surnames(r["authors"])
    if "et al." in s:
        return f"{s[0]} et al."
    if len(s) == 1:
        return s[0]
    if len(s) == 2:
        return f"{s[0]} & {s[1]}"
    if len(s) == 3:
        return f"{s[0]}, {s[1]} & {s[2]}"
    return f"{s[0]} et al."


def apa_authors(authors):
    parts = [p.strip() for p in authors.split(";") if p.strip()]
    if len(parts) == 1:
        return parts[0]
    if parts[-1].lower().startswith("et al"):
        return ", ".join(parts[:-1]) + ", et al."
    return ", ".join(parts[:-1]) + ", & " + parts[-1]


def ref_plain(r):
    s = f"{apa_authors(r['authors'])} ({r['year']}). {r['title']}. {r['venue']}."
    if r.get("doi"):
        s += f" https://doi.org/{r['doi']}"
    elif r.get("url"):
        s += f" {r['url']}"
    return s


# ---------------- ideas ----------------
def idea_score(i):
    w = dict(WEIGHTS)
    vals = [i["novelty"], ACADEMIC[i["id"]], i["practical"], i["publication"], i["data_feas"],
            10 - i["complexity"], 10 - i["risk"]]
    return round(sum(v * wt for v, (_, wt) in zip(vals, WEIGHTS)), 2)


def ideas_ranked():
    rows = sorted(IDEAS, key=lambda i: (-idea_score(i), i["id"]))
    return rows


def md_table(headers, rows):
    esc = lambda x: str(x).replace("|", "/").replace("\n", " ")
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(esc(c) for c in r) + " |")
    return "\n".join(out)


def idea_table_md():
    rows = []
    for k, i in enumerate(ideas_ranked(), 1):
        short = i["title"].split(":")[0] if len(i["title"]) > 70 else i["title"]
        rows.append([k, i["id"], short, i["novelty"], ACADEMIC[i["id"]], i["practical"], i["publication"],
                     i["data_feas"], i["complexity"], i["risk"], f"{idea_score(i):.2f}", i["journals"]])
    return md_table(["Rank", "ID", "Proposed title", "Nov.", "Acad.", "Prac.", "Pub.", "Data", "Impl. diff.", "Risk",
                     "Overall", "Target journals"], rows)


def parse_md_table(path, heading_contains=None):
    lines = open(path, encoding="utf-8").read().splitlines()
    rows, grab = [], heading_contains is None
    for ln in lines:
        if heading_contains and ln.startswith("#"):
            grab = heading_contains.lower() in ln.lower()
            continue
        if grab and ln.strip().startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            rows.append(cells)
    return rows
