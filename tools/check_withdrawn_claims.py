#!/usr/bin/env python
"""Fail if a withdrawn claim or figure appears in a document without a label attached to it.

Acceptance criterion of audit task P0-1: "grep finds no withdrawn figure outside a labelled
retraction". This is a *screen*, not a proof (see LIMITS).

A hit (a withdrawn figure or phrase, PATTERNS) is accepted only if ONE of these holds:

  A. the hit lies inside a ~~strikethrough~~ span on its own line;
  B. its own line carries a retraction label (dagger, WITHDRAWN, superseded, insolvent, ...);
  C. a retraction label appears within BLOCK_RADIUS lines of it AND in the same block
     (a block is a run of non-blank lines, so a label in another paragraph never counts);
  D. the governing heading (level 2 or deeper, never the document title) announces a retraction.
     Table rows are exempt from C: a label on a neighbouring row does not count.

There is deliberately NO document-level exemption: a banner or header marker at the top of a file
does not excuse any claim in its body, and record files are checked like any other file.

LIMITS (do not describe a PASS as sufficient verification)
  * It cannot tell whether a label explains the withdrawal, or whether a label on the same line
    refers to the figure rather than to something else on that line.
  * It only knows the figures and phrases in PATTERNS. A stale claim stated in new words or with
    new numbers is invisible to it (STATUS.md's stale table passed an earlier version).
  * It scans markdown under docs/, research/, prereg/ and submission_candidate_as_run_only/ and paper_assets_as_run_only/ plus the root README.

Usage:  python tools/check_withdrawn_claims.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCK_RADIUS = 3

# (label, regex). Each is a claim or figure that has been withdrawn.
PATTERNS = [
    ("insolvent-book capacity gain, Germany $1bn/$10bn", r"\+?8\.92\d?\b|\+?9\.256\b"),
    ("insolvent-book capacity gain, India $1bn/$10bn", r"\+?5\.69\d?\b|\+?5\.967\b"),
    # "+10.40" is deliberately NOT a pattern: it is also an IC t-statistic and a Japanese channel
    # t-statistic elsewhere. The asymptotic-channel claim it came from is caught by wording below.
    ("non-compliant-ladder capacity figures", r"\+8\.77\b|\+10\.02\b|\+11\.06\b"),
    ("asymptotic-channel regularity", r"asymptotic (channel|ratio)|4\.58.{0,20}4\.82|4\.375"),
    ("survival framing", r"first-order for survival|decisive for\s+survival|goes negative after tax|unviable after tax"),
    ("share-of-net-Sharpe-kept figures", r"keeps? 98%|keeps? \*\*98%|98% of its net"),
    ("tax-placebo exact match", r"within \*\*1%\*\*|within 1%"),
    ("US-frontier comparison", r"10x to 100x|10[–-]100[x×]"),
    ("all-cell cost-over-tax ratios", r"\b53x\b|\*\*53x\*\*"),
    ("sign-flip crossover", r"\$3\.79mn|H-FLIP CONFIRMED"),
    # Sharpe-point capacity gains against near-ruined comparators (status "unresolved - do not quote", evidence map C3).
    ("Sharpe-point capacity gain vs near-ruined comparator", r"\+6\.80\d?|\+6\.92\d?|\+3\.19\d?"),
]

# A label on the hit's own line, or within the same block.
LABEL = re.compile(
    r"†|‡|withdr(?:awn|aw|ew|awal)|supersed|retract|insolvent|unconfirmed|pre-fix|"
    r"not quotable|not interpretable|never to be restated|near-ruined",
    re.IGNORECASE,
)
# A heading that announces the whole section is a retraction.
HEADING_LABEL = re.compile(r"WITHDRAWN|SUPERSEDED|RETRACT|INVALID|withdrawn|superseded|retraction")

# "within 1%" in this file is a position cap, not the withdrawn tax-placebo claim.
PATTERN_EXEMPT = {("docs/CAPACITY_CONSTRAINT_DEU.md", "tax-placebo exact match")}


def _in_strike(line: str, pos: int) -> bool:
    return line[:pos].count("~~") % 2 == 1 and "~~" in line[pos:]


def check_text(rel: str, text: str) -> list[tuple[int, str, str]]:
    """Return (line_number, pattern_label, line) for every unlabelled withdrawn-claim hit."""
    lines = text.splitlines()
    bad: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        for label, pat in PATTERNS:
            if (rel, label) in PATTERN_EXEMPT:
                continue
            for m in re.finditer(pat, line):
                if _labelled(lines, i, m.start()):
                    continue
                bad.append((i + 1, label, line.strip()[:110]))
                break
    return bad


def _labelled(lines: list[str], i: int, pos: int) -> bool:
    line = lines[i]
    if _in_strike(line, pos) or LABEL.search(line):                      # A, B
        return True
    if re.match(r"^[>\s]*\|", line):       # table row: a label on a neighbouring row never counts
        return _heading_labels(lines, i)
    lo = i
    while lo > 0 and lines[lo - 1].strip() and i - lo < BLOCK_RADIUS:     # C: same block only
        lo -= 1
    hi = i
    while hi < len(lines) - 1 and lines[hi + 1].strip() and hi - i < BLOCK_RADIUS:
        hi += 1
    if any(LABEL.search(lines[j]) for j in range(lo, hi + 1)):
        return True
    return _heading_labels(lines, i)


def _heading_labels(lines: list[str], i: int) -> bool:
    """D: the governing heading (level 2 or deeper; a document title never counts) is a retraction."""
    for j in range(i, -1, -1):
        m = re.match(r"^\s*(#+)\s", lines[j])
        if m and len(m.group(1)) >= 2:
            return bool(HEADING_LABEL.search(lines[j]))
    return False


def files() -> list[Path]:
    out: list[Path] = []
    for sub in ("docs", "research", "prereg", "submission_candidate_as_run_only", "paper_assets_as_run_only"):
        out += sorted((ROOT / sub).rglob("*.md"))
    readme = ROOT / "README.md"
    if readme.exists():
        out.append(readme)
    return out


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    bad: list[str] = []
    fs = files()
    for f in fs:
        rel = f.relative_to(ROOT).as_posix()
        for ln, label, text in check_text(rel, f.read_text(encoding="utf-8", errors="replace")):
            bad.append(f"{rel}:{ln}: [{label}] {text}")
    print(f"scanned {len(fs)} files")
    if bad:
        print(f"\nFAIL: {len(bad)} withdrawn-claim hit(s) with no label attached:\n")
        for b in bad:
            print("  " + b)
        return 1
    print("PASS: no pattern hit is unlabelled. This is a screen, not verification (see LIMITS).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
