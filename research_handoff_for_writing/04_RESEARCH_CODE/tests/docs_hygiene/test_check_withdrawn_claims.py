"""Regression tests for tools/check_withdrawn_claims.py.

The checker screens documents for withdrawn figures that are not labelled as withdrawn. These tests
pin the behaviours it must have, including the two ways an earlier version let stale claims pass:
an unrelated retraction word nearby, and a document-level banner that excused the whole body.
They test the screen; they do not make a PASS on the real documents sufficient verification.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import check_withdrawn_claims as chk  # noqa: E402

FIG = "+8.92"  # a withdrawn insolvent-book figure (Germany, $1bn)


def hits(text: str, rel: str = "docs/X.md"):
    return chk.check_text(rel, text)


def test_withdrawn_figure_presented_as_current_fails():
    assert hits(f"At a $1bn mandate the capacity channel is {FIG} Sharpe points.\n")


def test_each_pattern_family_is_detected_when_unlabelled():
    for claim in ("The asymptotic channel is stable.", "within 1% of Japan", "costs beat taxes 53x",
                  "crossover at $3.79mn", "taxes are first-order for survival", "India keeps 98% of it",
                  "second-order as a channel but decisive for survival"):
        assert hits(claim + "\n"), claim


def test_strikethrough_historical_figure_passes():
    assert not hits(f"Earlier we reported ~~{FIG}~~ for Germany.\n")


def test_same_line_label_passes():
    assert not hits(f"{FIG} † (insolvent comparison book)\n")
    assert not hits(f"WITHDRAWN: the {FIG} figure.\n")


def test_labelled_retraction_block_passes():
    text = f"> **Withdrawn.** The figure below was an artefact.\n> The channel was {FIG} at $1bn.\n"
    assert not hits(text)


def test_unrelated_retraction_marker_in_another_paragraph_does_not_legitimise():
    text = f"The channel is {FIG} at $1bn.\n\nA different result was withdrawn earlier today.\n"
    assert hits(text)


def test_unrelated_marker_far_away_in_same_block_does_not_legitimise():
    filler = "\n".join(f"line {i} of an ordinary paragraph" for i in range(6))
    text = f"The channel is {FIG} at $1bn.\n{filler}\nsomething was superseded\n"
    assert hits(text)


def test_generic_words_are_not_labels():
    # Words that an earlier version treated as retraction markers.
    text = f"The channel is {FIG}, a corrected, historical, artefact-free, no longer moot figure.\n"
    assert hits(text)


def test_document_level_banner_does_not_exempt_body():
    banner = "> **SUPERSEDED IN PART (finalization audit, Phase 1).** historical record\n"
    text = banner + "\n## Results\n\n" + f"The channel is {FIG} at $1bn.\n"
    assert hits(text)


def test_record_file_is_checked_like_any_other():
    text = "# RETRACTED result\n\n" + f"The channel is {FIG} at $1bn.\n"
    # a retraction word in the document TITLE (level-1 heading) does not excuse the body
    assert hits(text, rel="docs/RESULTS_SIGN_FLIP_2026-10-09.md")


def test_retraction_heading_labels_its_own_section_only():
    text = f"## 8.7 WITHDRAWN: the capacity figure\n\n{FIG} was reported.\n\n## 9 Results\n\n{FIG} again.\n"
    found = hits(text)
    assert [h[0] for h in found] == [7]


def test_table_row_needs_its_own_label():
    text = f"| rung | gain |\n|---|---|\n| $1bn | {FIG} |\n| $10bn | {FIG} † |\n"
    assert [h[0] for h in hits(text)] == [3]


def test_known_limitation_label_on_same_line_is_trusted():
    # Documented limit: the screen cannot tell WHAT a same-line label refers to.
    assert not hits(f"The channel is {FIG}; a different number was withdrawn.\n")


def test_pattern_exemption_is_file_and_pattern_specific():
    assert not hits("position cap within 1% of ADV\n", rel="docs/CAPACITY_CONSTRAINT_DEU.md")
    assert hits("position cap within 1% of ADV\n", rel="docs/OTHER.md")
