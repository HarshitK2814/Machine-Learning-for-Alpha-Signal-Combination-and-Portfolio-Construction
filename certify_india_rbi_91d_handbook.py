from __future__ import annotations

"""
ISOLATED / NON-PRODUCTION INDIA 91-DAY TREASURY-BILL SOURCE CERTIFICATION

Purpose
-------
Certify a homogeneous monthly India ~3m government short-rate leg BEFORE it is
integrated into the full C5 TERM/DRATE runner.

Economic object
---------------
Exact 91-day Government of India Treasury Bill primary-market implicit yield.
Monthly state = arithmetic mean of the auction-level implicit yields whose
auction dates fall in that calendar month.

Primary source
--------------
RBI Handbook of Statistics on the Indian Economy:
    "Auctions of 91-Day Government of India Treasury Bills"

Why this script exists
----------------------
The current RBI Bulletin Table 26 workbook used by v5/v6 is not a sufficiently
long historical archive for the 1996-2020 research window.  This script uses
the cumulative/overlapping annual RBI Handbook tables instead and reconciles
their overlaps explicitly.

Safety
------
- no interpolation / backfill / forward-fill;
- no production C5 write;
- no GitHub write;
- hard-fails on ambiguous parser rows, material cross-edition conflicts,
  failed RBI-published monthly anchors, or any missing required month.
"""

import hashlib
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime, date

import numpy as np
import pandas as pd


ROOT = Path("data/intl_c5")
CACHE = ROOT / "reference" / "_auto_term_drate_chunk" / "india_91d_handbook"
OUT = ROOT / "candidate_term_drate_working"
CACHE.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

UA = "Mozilla/5.0 (C5 India 91d source certification; non-production)"

HANDBOOK_INDEX = "https://www.rbi.org.in/scripts/AnnualPublications.aspx"
HANDBOOK_HEAD = "Handbook of Statistics on Indian Economy"
TARGET_PHRASES = (
    "AUCTIONS OF 91 DAY GOVERNMENT OF INDIA TREASURY BILLS",
    "AUCTIONS OF 91-DAY GOVERNMENT OF INDIA TREASURY BILLS",
)

# Broad edition sweep.  We do not assume a single later vintage contains all
# earlier auctions.  Overlapping editions are reconciliation checks.
EDITION_YEARS = list(range(2001, 2025))
KNOWN_PAGES = {
    2016: "https://www.rbi.org.in/scripts/AnnualPublications.aspx?fromdate=09%2F15%2F2016&head=Handbook+of+Statistics+on+Indian+Economy&todate=09%2F17%2F2016",
    2023: "https://www.rbi.org.in/scripts/AnnualPublications.aspx?fromdate=09%2F14%2F2023&head=Handbook+of+Statistics+on+Indian+Economy&todate=09%2F16%2F2023",
}

REQUIRED_START = pd.Timestamp("1996-04-30")
REQUIRED_END = pd.Timestamp("2020-12-31")
REQUIRED_MONTHS = pd.date_range(REQUIRED_START, REQUIRED_END, freq="ME")
TARGET_GAP_MONTHS = pd.DatetimeIndex([
    pd.Timestamp("2001-08-31"),
    pd.Timestamp("2004-10-31"),
])

# Primary-RBI published monthly averages.
MONTHLY_ANCHORS = {
    "2003-04-30": 5.04, "2003-05-31": 4.56, "2003-06-30": 4.95,
    "2003-07-31": 4.87, "2003-08-31": 4.90, "2003-09-30": 4.60,
    "2003-10-31": 4.61, "2003-11-30": 4.37, "2003-12-31": 4.19,
    "2004-01-31": 4.25, "2004-02-29": 4.38, "2004-03-31": 4.27,
    "2004-04-30": 4.39, "2004-05-31": 4.40, "2004-06-30": 4.46,
    "2004-07-31": 4.48,
    "2008-04-30": 7.28, "2008-05-31": 7.41, "2008-06-30": 8.01,
    "2008-07-31": 9.07, "2008-08-31": 9.15, "2008-09-30": 8.74,
    "2008-10-31": 8.13, "2008-11-30": 7.30, "2008-12-31": 5.49,
    "2009-01-31": 4.69, "2009-02-28": 4.78, "2009-03-31": 4.77,
    "2009-04-30": 3.81, "2009-05-31": 3.26, "2009-06-30": 3.35,
    "2009-07-31": 3.23,
}

# Cross-edition tolerance for the same auction yield.
AUCTION_YIELD_CONFLICT_TOL = 5e-4

# Price/yield identity tolerance.  RBI's quoted implicit yield is consistent
# with the 91-day T-bill discount-price/YTM convention:
#   y = ((100-P)/P) * (365/91) * 100
PRICE_YIELD_IDENTITY_TOL = 0.03


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def download_bytes(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
    if not raw:
        raise RuntimeError(f"empty download: {url}")
    return raw


def cache_url(url: str, name: str) -> tuple[bytes, Path]:
    path = CACHE / name
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes(), path
    raw = download_bytes(url)
    path.write_bytes(raw)
    return raw, path


class RowsAndLinksParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows = []
        self._in_tr = False
        self._in_cell = False
        self._cell_text = []
        self._row_cells = []
        self._row_links = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs = dict(attrs)
        if tag == "tr":
            self._in_tr = True
            self._row_cells = []
            self._row_links = []
        elif self._in_tr and tag in {"td", "th"}:
            self._in_cell = True
            self._cell_text = []
        elif self._in_tr and tag == "a":
            href = attrs.get("href")
            if href:
                self._row_links.append(href)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._in_tr and tag in {"td", "th"} and self._in_cell:
            txt = re.sub(r"\s+", " ", "".join(self._cell_text)).strip()
            self._row_cells.append(txt)
            self._cell_text = []
            self._in_cell = False
        elif tag == "tr" and self._in_tr:
            if self._row_cells or self._row_links:
                self.rows.append({
                    "cells": list(self._row_cells),
                    "links": list(dict.fromkeys(self._row_links)),
                })
            self._in_tr = False
            self._in_cell = False

    def handle_data(self, data):
        if self._in_cell:
            self._cell_text.append(data)


def html_rows(raw: bytes) -> list[dict]:
    parser = RowsAndLinksParser()
    parser.feed(raw.decode("utf-8", errors="replace"))
    return parser.rows


def norm_text(x: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(x).upper()).strip()


def target_row(row: dict) -> bool:
    txt = norm_text(" ".join(row.get("cells", [])))
    return (
        "AUCTIONS OF 91 DAY GOVERNMENT OF INDIA TREASURY BILLS" in txt
        or (
            "AUCTIONS" in txt
            and "91 DAY" in txt
            and "GOVERNMENT OF INDIA" in txt
            and "TREASURY BILLS" in txt
        )
    )


def annual_page_url(year: int) -> str:
    qs = urllib.parse.urlencode({
        "fromdate": f"01/01/{year}",
        "head": HANDBOOK_HEAD,
        "todate": f"12/31/{year}",
    })
    return f"{HANDBOOK_INDEX}?{qs}"


def extract_target_links(page_raw: bytes, page_url: str) -> list[str]:
    rows = html_rows(page_raw)
    out = []

    for row in rows:
        if not target_row(row):
            continue
        for href in row.get("links", []):
            u = urllib.parse.urljoin(page_url, href)
            if not u.lower().startswith("javascript:"):
                out.append(u)

    if not out:
        text = page_raw.decode("utf-8", errors="replace")
        m = re.search(
            r"AUCTIONS\s+OF\s+91\s*[- ]\s*DAY\s+GOVERNMENT\s+OF\s+INDIA\s+TREASURY\s+BILLS",
            text, re.I | re.S,
        )
        if m:
            lo = max(0, m.start() - 1600)
            hi = min(len(text), m.end() + 2600)
            window = text[lo:hi]
            for href in re.findall(r'href\s*=\s*["\']([^"\']+)["\']', window, flags=re.I):
                u = urllib.parse.urljoin(page_url, href)
                if not u.lower().startswith("javascript:"):
                    out.append(u)

    def score(u: str):
        lu = u.lower().split("?", 1)[0]
        if "publicationsview.aspx" in u.lower():
            return (0, u)
        if lu.endswith(".xlsx") or lu.endswith(".xls"):
            return (1, u)
        if lu.endswith(".pdf"):
            return (3, u)
        return (2, u)

    return sorted(dict.fromkeys(out), key=score)


def parse_date_cell(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return pd.NaT

    if isinstance(v, (pd.Timestamp, datetime, date, np.datetime64)):
        try:
            return pd.Timestamp(v).normalize()
        except Exception:
            pass

    if isinstance(v, (int, float, np.integer, np.floating)):
        fv = float(v)
        if 20000 <= fv <= 70000:
            try:
                return (pd.Timestamp("1899-12-30") + pd.to_timedelta(fv, unit="D")).normalize()
            except Exception:
                pass

    text = str(v).strip()
    if not text:
        return pd.NaT

    for fmt in (
        "%d-%b-%Y", "%d-%b-%y", "%d-%B-%Y", "%d-%B-%y",
        "%Y-%m-%d", "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y", "%d/%m/%y",
        "%d-%m-%Y", "%d-%m-%y",
    ):
        dt = pd.to_datetime(text, format=fmt, errors="coerce")
        if not pd.isna(dt):
            return pd.Timestamp(dt).normalize()

    return pd.NaT


def parse_number(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, (int, float, np.integer, np.floating)):
        fv = float(v)
        return fv if math.isfinite(fv) else None

    text = str(v).strip().replace(",", "")
    if text.upper() in {"", "-", "—", "–", "..", "...", "NA", "N.A.", "N/A"}:
        return None

    m = re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)", text)
    return None if not m else float(m.group(0))


def price_implied_yield_91d(price: float) -> float:
    return ((100.0 - price) / price) * (365.0 / 91.0) * 100.0


def parse_auction_row(cells: list) -> dict | None:
    """Parse one RBI Handbook auction row conservatively.

    We do NOT assume fixed column count across Handbook vintages.  Instead:
    1) locate exactly one plausible auction date in the row;
    2) after that date, locate a unique adjacent cut-off-price / implicit-yield pair;
    3) require the pair to satisfy the 91-day price-yield identity.
    """
    parsed_dates = []
    for i, v in enumerate(cells):
        dt = parse_date_cell(v)
        if pd.isna(dt):
            continue
        if pd.Timestamp("1990-01-01") <= dt <= pd.Timestamp("2030-12-31"):
            parsed_dates.append((i, dt))

    # Auction rows often also carry an issue date, so 1-2 dates are acceptable.
    if not parsed_dates:
        return None

    auction_idx, auction_date = parsed_dates[0]

    nums = [parse_number(v) for v in cells]
    pairs = []

    for i in range(auction_idx + 1, len(cells) - 1):
        p = nums[i]
        y = nums[i + 1]
        if p is None or y is None:
            continue
        if not (80.0 <= p <= 100.5 and 0.0 < y < 30.0):
            continue
        implied = price_implied_yield_91d(float(p))
        err = abs(implied - float(y))
        if err <= PRICE_YIELD_IDENTITY_TOL:
            pairs.append((i, float(p), float(y), float(err)))

    if len(pairs) == 0:
        return None
    if len(pairs) > 1:
        raise RuntimeError(
            f"ambiguous price/yield pairs for auction {auction_date.date()}: {pairs}"
        )

    idx, price, yld, identity_error = pairs[0]
    return {
        "auction_date": pd.Timestamp(auction_date),
        "cutoff_price": price,
        "implicit_yield": yld,
        "price_yield_identity_error": identity_error,
    }


def extract_records_from_html(raw: bytes, source_url: str, edition_year: int) -> list[dict]:
    records = []
    for row in html_rows(raw):
        cells = [re.sub(r"\s+", " ", str(x)).strip() for x in row.get("cells", [])]
        rec = parse_auction_row(cells)
        if rec is not None:
            rec.update({
                "edition_year": int(edition_year),
                "source_url": source_url,
                "source_format": "html",
            })
            records.append(rec)
    return records


def extract_records_from_excel(path: Path, source_url: str, edition_year: int) -> list[dict]:
    try:
        book = pd.read_excel(path, sheet_name=None, header=None, engine="openpyxl")
    except Exception:
        # Legacy .xls may need xlrd if present.
        book = pd.read_excel(path, sheet_name=None, header=None)

    records = []
    for sheet_name, df in book.items():
        for _, row in df.iterrows():
            cells = row.tolist()
            rec = parse_auction_row(cells)
            if rec is not None:
                rec.update({
                    "edition_year": int(edition_year),
                    "source_url": source_url,
                    "source_format": "excel",
                    "sheet": sheet_name,
                })
                records.append(rec)
    return records


def dedupe_within_source(records: list[dict]) -> list[dict]:
    by_date = {}
    for r in records:
        dt = pd.Timestamp(r["auction_date"])
        if dt not in by_date:
            by_date[dt] = r
            continue
        a = by_date[dt]
        if abs(float(a["implicit_yield"]) - float(r["implicit_yield"])) > AUCTION_YIELD_CONFLICT_TOL:
            raise RuntimeError(
                f"conflicting auction yield inside one source for {dt.date()}: "
                f"{a['implicit_yield']} vs {r['implicit_yield']}"
            )
    return [by_date[k] for k in sorted(by_date)]


def harvest() -> tuple[pd.DataFrame, dict]:
    all_records = []
    edition_audit = []
    source_hashes = {}

    for year in EDITION_YEARS:
        page_url = KNOWN_PAGES.get(year, annual_page_url(year))
        try:
            page_raw, page_path = cache_url(page_url, f"HANDBOOK_INDEX_{year}.html")
        except Exception as exc:
            edition_audit.append({
                "edition_year": year,
                "page_url": page_url,
                "status": "PAGE_FETCH_FAIL",
                "error": str(exc),
            })
            continue

        links = extract_target_links(page_raw, page_url)
        edition_records = []
        tried = []

        for j, link in enumerate(links[:8]):
            tried.append(link)
            lower = link.lower().split("?", 1)[0]

            if lower.endswith(".pdf"):
                continue

            ext = ".xlsx" if lower.endswith(".xlsx") else ".xls" if lower.endswith(".xls") else ".html"

            try:
                raw, path = cache_url(link, f"HANDBOOK_91D_{year}_{j}{ext}")
                source_hashes[str(path)] = sha256(path)

                if ext in {".xlsx", ".xls"}:
                    recs = extract_records_from_excel(path, link, year)
                else:
                    recs = extract_records_from_html(raw, link, year)

                recs = dedupe_within_source(recs)
                if len(recs) >= 20:
                    edition_records = recs
                    break
            except Exception as exc:
                continue

        edition_audit.append({
            "edition_year": year,
            "page_url": page_url,
            "target_links_found": links,
            "links_tried": tried,
            "records_extracted": len(edition_records),
            "first_auction": None if not edition_records else str(min(r["auction_date"] for r in edition_records).date()),
            "last_auction": None if not edition_records else str(max(r["auction_date"] for r in edition_records).date()),
            "status": "OK" if edition_records else "NO_PARSEABLE_TARGET_TABLE",
        })
        all_records.extend(edition_records)

    if not all_records:
        audit = {
            "verdict": "FAIL_NO_PRIMARY_RBI_91D_AUCTION_RECORDS",
            "editions": edition_audit,
        }
        (OUT / "IND_RBI_91D_HANDBOOK_SOURCE_AUDIT.json").write_text(
            json.dumps(audit, indent=2), encoding="utf-8"
        )
        raise RuntimeError(
            "No primary RBI Handbook 91-day auction records could be harvested"
        )

    # Reconcile the same auction across overlapping annual Handbook vintages.
    by_date = {}
    conflicts = []
    for r in sorted(all_records, key=lambda x: (x["auction_date"], x["edition_year"])):
        by_date.setdefault(pd.Timestamp(r["auction_date"]), []).append(r)

    chosen = []
    overlap_checks = []

    for dt, rows in sorted(by_date.items()):
        vals = [float(r["implicit_yield"]) for r in rows]
        spread = max(vals) - min(vals)
        if spread > AUCTION_YIELD_CONFLICT_TOL:
            conflicts.append({
                "auction_date": str(dt.date()),
                "values": vals,
                "sources": [r["source_url"] for r in rows],
            })
            continue

        first = sorted(rows, key=lambda r: r["edition_year"])[0]
        chosen.append(first)

        if len(rows) >= 2:
            overlap_checks.append({
                "auction_date": str(dt.date()),
                "n_editions": len(rows),
                "yield_spread": float(spread),
            })

    if conflicts:
        audit = {
            "verdict": "FAIL_CROSS_EDITION_AUCTION_CONFLICT",
            "conflicts": conflicts[:100],
            "editions": edition_audit,
        }
        (OUT / "IND_RBI_91D_HANDBOOK_SOURCE_AUDIT.json").write_text(
            json.dumps(audit, indent=2), encoding="utf-8"
        )
        raise RuntimeError("RBI Handbook editions materially disagree on 91-day auction yields")

    auctions = pd.DataFrame(chosen).sort_values("auction_date").reset_index(drop=True)

    # Ensure there is at most one 91-day auction observation per auction date.
    if auctions.duplicated("auction_date").any():
        raise RuntimeError("duplicate auction dates after cross-edition reconciliation")

    # Monthly arithmetic mean of the auction implicit yields.
    auctions["date"] = auctions["auction_date"] + pd.offsets.MonthEnd(0)
    monthly = (
        auctions.groupby("date", as_index=False)
        .agg(
            value=("implicit_yield", "mean"),
            auction_count=("auction_date", "count"),
            max_price_yield_identity_error=("price_yield_identity_error", "max"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    # Published monthly averages are the critical aggregation certification.
    anchor_checks = []
    for d, expected in MONTHLY_ANCHORS.items():
        dt = pd.Timestamp(d)
        rr = monthly.loc[monthly["date"].eq(dt)]
        actual = None if rr.empty else float(rr.iloc[0]["value"])
        rounded = None if actual is None else round(actual, 2)
        passed = actual is not None and abs(rounded - expected) < 1e-9
        anchor_checks.append({
            "date": d,
            "expected": expected,
            "actual": actual,
            "actual_rounded_2dp": rounded,
            "pass": bool(passed),
        })

    failed_anchors = [x for x in anchor_checks if not x["pass"]]

    have = pd.DatetimeIndex(monthly["date"])
    missing_required = REQUIRED_MONTHS.difference(have)
    missing_target = TARGET_GAP_MONTHS.difference(have)

    audit = {
        "economic_source": "Reserve Bank of India Handbook of Statistics on the Indian Economy",
        "source_table": "Auctions of 91-Day Government of India Treasury Bills",
        "construction": "calendar-month arithmetic mean of auction-level implicit yields at cut-off price",
        "auction_rows": int(len(auctions)),
        "first_auction": str(auctions["auction_date"].min().date()),
        "last_auction": str(auctions["auction_date"].max().date()),
        "first_month": str(monthly["date"].min().date()),
        "last_month": str(monthly["date"].max().date()),
        "anchor_checks": anchor_checks,
        "anchor_failures": len(failed_anchors),
        "required_window": f"{REQUIRED_START.date()}..{REQUIRED_END.date()}",
        "required_month_count": int(len(REQUIRED_MONTHS)),
        "missing_required_months": [str(x.date()) for x in missing_required],
        "target_gap_month_values": {
            str(dt.date()): (
                None
                if monthly.loc[monthly["date"].eq(dt), "value"].empty
                else float(monthly.loc[monthly["date"].eq(dt), "value"].iloc[0])
            )
            for dt in TARGET_GAP_MONTHS
        },
        "cross_edition_overlap_checks": overlap_checks,
        "edition_audit": edition_audit,
        "cached_source_hashes": source_hashes,
        "pit_note": "RBI release calendar states 91-day T-bill auction results are released the next day; a one-reference-month lag is conservative for the monthly feature.",
        "no_imputation": True,
        "production_written": False,
        "github_written": False,
    }

    if failed_anchors:
        audit["verdict"] = "FAIL_PRIMARY_RBI_MONTHLY_ANCHORS"
    elif len(missing_required):
        audit["verdict"] = "FAIL_REQUIRED_MONTHLY_COVERAGE"
    elif len(missing_target):
        audit["verdict"] = "FAIL_TARGET_MONTH_RECOVERY"
    else:
        audit["verdict"] = "PASS_CERTIFIED_PRIMARY_RBI_91D_MONTHLY"

    audit_path = OUT / "IND_RBI_91D_HANDBOOK_SOURCE_AUDIT.json"
    audit_path.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")

    auctions[[
        "auction_date", "cutoff_price", "implicit_yield",
        "price_yield_identity_error", "edition_year", "source_url",
    ]].to_csv(OUT / "IND_RBI_91D_HANDBOOK_AUCTIONS_working.csv", index=False)

    monthly.to_csv(OUT / "IND_RBI_91D_HANDBOOK_MONTHLY_working.csv", index=False)

    if audit["verdict"] != "PASS_CERTIFIED_PRIMARY_RBI_91D_MONTHLY":
        raise RuntimeError(
            f"India RBI 91-day source certification failed: {audit['verdict']}; "
            f"audit written to {audit_path}"
        )

    return monthly, audit


def main():
    monthly, audit = harvest()

    print("=" * 112)
    print("INDIA RBI EXACT 91-DAY TREASURY-BILL SOURCE CERTIFICATION: PASS")
    print(f"auction rows: {audit['auction_rows']}")
    print(f"auction window: {audit['first_auction']} .. {audit['last_auction']}")
    print(f"monthly window: {audit['first_month']} .. {audit['last_month']}")
    print(f"primary RBI monthly anchors failed: {audit['anchor_failures']}")
    print(f"missing required months 1996-04..2020-12: {len(audit['missing_required_months'])}")
    print("target months:", audit["target_gap_month_values"])
    print("VERDICT:", audit["verdict"])
    print("PRODUCTION WRITTEN: NO")
    print("GITHUB WRITTEN: NO")
    print("outputs:", OUT)
    print("=" * 112)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("=" * 112, file=sys.stderr)
        print("INDIA RBI EXACT 91-DAY TREASURY-BILL SOURCE CERTIFICATION: FAIL", file=sys.stderr)
        print(type(exc).__name__ + ":", exc, file=sys.stderr)
        print("PRODUCTION WRITTEN: NO", file=sys.stderr)
        print("GITHUB WRITTEN: NO", file=sys.stderr)
        print("=" * 112, file=sys.stderr)
        raise
