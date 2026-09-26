# -*- coding: utf-8 -*-
"""Minimal, robust Markdown -> PDF renderer (ReportLab) with citations, TOC, bookmarks, tables, figures."""
import os, re
from fontTools.ttLib import TTFont as FTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

from common import FIGS, short_author, surnames, apa_authors

FONT_DIR = r"C:\Windows\Fonts"
NAVY, BLUE, INK, INK2, MUTED, HAIR, ZEBRA = "#0d366b", "#184f95", "#1d1d1b", "#52514e", "#898781", "#d9d8d2", "#f4f4f1"
COVER = set()


def _reg(family, files):
    paths = [os.path.join(FONT_DIR, f) for f in files]
    base = paths[0]
    names = []
    for suffix, p in zip(["", "-Bold", "-Italic", "-BoldItalic"], paths):
        p = p if os.path.exists(p) else base
        pdfmetrics.registerFont(TTFont(family + suffix, p))
        names.append(family + suffix)
    pdfmetrics.registerFontFamily(family, normal=names[0], bold=names[1], italic=names[2], boldItalic=names[3])
    return set(FTFont(base)["cmap"].getBestCmap().keys())


def setup_fonts():
    global COVER
    c1 = _reg("Body", ["georgia.ttf", "georgiab.ttf", "georgiai.ttf", "georgiaz.ttf"])
    c2 = _reg("Sans", ["segoeui.ttf", "segoeuib.ttf", "segoeuii.ttf", "segoeuiz.ttf"])
    _reg("Mono", ["consola.ttf", "consolab.ttf", "consolai.ttf", "consolaz.ttf"])
    COVER = c1 & c2


SUBST = {"\u2297": "x", "\u2016": "||", "\u2194": "<->", "\u2248": "~", "\u2265": ">=", "\u2264": "<=", "\u2212": "-",
         "\u2192": "->", "\u00b2": "^2", "\u0303": "", "\u0304": "", "\u2610": "[ ]", "\u2011": "-", "\u03ba": "kappa",
         "\u2713": "v", "\u221a": "sqrt", "\u2208": " in ", "\u2209": " not in ", "\u2260": "!=", "\u2026": "...",
         "\u2211": "Sum", "\u00b1": "+/-", "\u2193": "v", "\u2191": "^", "\u207a": "+"}


def sanitize(s):
    out = []
    for ch in s:
        if ord(ch) < 128 or ord(ch) in COVER:
            out.append(ch)
        else:
            out.append(SUBST.get(ch, "?"))
    return "".join(out)


def styles():
    st = {}
    base = dict(fontName="Body", fontSize=9.3, leading=13.4, textColor=INK, alignment=TA_LEFT)
    st["Body"] = ParagraphStyle("Body", spaceAfter=5, **base)
    st["H1"] = ParagraphStyle("H1", fontName="Sans-Bold", fontSize=17, leading=21, textColor=NAVY, spaceBefore=6, spaceAfter=9)
    st["H2"] = ParagraphStyle("H2", fontName="Sans-Bold", fontSize=12.6, leading=16, textColor=BLUE, spaceBefore=11, spaceAfter=5)
    st["H3"] = ParagraphStyle("H3", fontName="Sans-Bold", fontSize=10.6, leading=14, textColor=INK, spaceBefore=8, spaceAfter=3)
    st["H4"] = ParagraphStyle("H4", fontName="Sans-Bold", fontSize=9.4, leading=12.5, textColor=INK2, spaceBefore=6, spaceAfter=2)
    for h in ("H1", "H2", "H3", "H4"):
        st[h].keepWithNext = 1  # never leave a heading orphaned at the bottom of a page
    st["TOCHead"] = ParagraphStyle("TOCHead", parent=st["H1"])
    st["Bullet"] = ParagraphStyle("Bullet", parent=st["Body"], leftIndent=14, bulletIndent=3, spaceAfter=2.5, bulletFontName="Body")
    st["Quote"] = ParagraphStyle("Quote", parent=st["Body"], fontName="Body-Italic", leftIndent=10, rightIndent=6,
                                 backColor="#f0efec", borderPadding=(5, 6, 5, 6), spaceBefore=3, spaceAfter=7, textColor="#2c2c2a")
    st["Code"] = ParagraphStyle("Code", fontName="Mono", fontSize=6.9, leading=8.4, textColor="#2c2c2a", backColor="#f5f5f3",
                                borderPadding=5, spaceBefore=4, spaceAfter=8)
    st["Caption"] = ParagraphStyle("Caption", fontName="Sans-Italic", fontSize=7.8, leading=10, textColor=INK2, spaceAfter=10)
    st["Ref"] = ParagraphStyle("Ref", fontName="Body", fontSize=8.1, leading=10.6, leftIndent=14, firstLineIndent=-14, spaceAfter=3, textColor=INK)
    st["Small"] = ParagraphStyle("Small", fontName="Sans", fontSize=7.8, leading=10.2, textColor=INK2, spaceAfter=6)
    for n, fs, ld in [("Cell", 7.6, 9.6), ("CellS", 6.9, 8.7), ("CellL", 8.2, 10.4)]:
        st[n] = ParagraphStyle(n, fontName="Sans", fontSize=fs, leading=ld, textColor=INK)
        st[n + "H"] = ParagraphStyle(n + "H", fontName="Sans-Bold", fontSize=fs, leading=ld, textColor=colors.white)
    return st


class Ctx:
    def __init__(self, refs, width, tokens=None):
        self.refs, self.width, self.tokens = refs, width, tokens or {}
        self.cited, self.warnings = [], set()
        self.st = styles()

    def cite(self, rid):
        if rid not in self.cited:
            self.cited.append(rid)


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s, ctx):
    s = _esc(sanitize(s))
    codes = []

    def code_sub(m):
        codes.append(m.group(1)); return f"\x01{len(codes) - 1}\x01"
    s = re.sub(r"`([^`]+)`", code_sub, s)

    def group(m):
        out = []
        for p in [p.strip() for p in m.group(1).split(";")]:
            mm_ = re.match(r"@([A-Z][A-Z0-9]+)(.*)$", p)
            if mm_ and mm_.group(1) in ctx.refs:
                r = ctx.refs[mm_.group(1)]; ctx.cite(mm_.group(1))
                out.append(f"{_esc(short_author(r))}, {r['year']}{mm_.group(2)}")
            else:
                if mm_:
                    ctx.warnings.add(mm_.group(1))
                out.append(p)
        return "(" + "; ".join(out) + ")"
    s = re.sub(r"\[([^\[\]]*@[A-Z][A-Z0-9]+[^\[\]]*)\]", group, s)

    def narr(m):
        rid = m.group(1)
        if rid in ctx.refs:
            r = ctx.refs[rid]; ctx.cite(rid)
            return f"{_esc(short_author(r))} ({r['year']})"
        ctx.warnings.add(rid)
        return m.group(0)
    s = re.sub(r"(?<![\w@/])@([A-Z][A-Z0-9]+)\b", narr, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\*\w])\*(?![\s\*])(.+?)(?<![\s\*])\*(?![\*\w])", r"<i>\1</i>", s)
    s = re.sub(r"\[(inference|verify|hypothesis|proposed)([^\]]*)\]",
               lambda m: f'<font color="#8a5a00">[{m.group(1)}{m.group(2)}]</font>', s, flags=re.I)
    for i, c in enumerate(codes):
        s = s.replace(f"\x01{i}\x01", f'<font name="Mono" size="7.8">{c}</font>')
    return s


def make_table(rows, ctx):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    if len(cells) > 1 and all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells[1] if c):
        cells.pop(1)
    n = max(len(r) for r in cells)
    cells = [r + [""] * (n - len(r)) for r in cells]
    key = "CellL" if n <= 3 else ("Cell" if n <= 7 else "CellS")
    st, sth = ctx.st[key], ctx.st[key + "H"]
    lens = []
    for j in range(n):
        col = [len(re.sub(r"\[@[^\]]*\]", "x" * 18, cells[i][j])) for i in range(len(cells))]
        lens.append(min(60.0, max(4.0, 0.45 * max(col) + 0.55 * sum(col) / len(col))))
    minw = 13 * mm if n > 8 else 16 * mm
    # never break a single token (e.g. paper IDs): floor each column at its longest word width
    longest = []
    for j in range(n):
        words = [wd for i in range(len(cells)) for wd in re.sub(r"\[@[^\]]*\]|@[A-Z0-9]+", "", cells[i][j]).split()]
        wmax = max([pdfmetrics.stringWidth(sanitize(wd), "Sans-Bold", st.fontSize) for wd in words] or [0])
        longest.append(min(wmax + 8, ctx.width * 0.28))
    w = [max(minw, longest[j], ctx.width * x / sum(lens)) for j, x in enumerate(lens)]
    scale = ctx.width / sum(w)
    w = [x * scale for x in w]
    data = [[Paragraph(inline(c, ctx), sth if i == 0 else st) for c in r] for i, r in enumerate(cells)]
    t = Table(data, colWidths=w, repeatRows=1, hAlign="LEFT")
    style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BLUE)), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LINEBELOW", (0, 0), (-1, -1), 0.35, colors.HexColor(HAIR)),
             ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
             ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.8)]
    for i in range(1, len(cells)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(ZEBRA)))
    t.setStyle(TableStyle(style))
    return [t, Spacer(1, 7)]


def figure(token, ctx):
    name, _, cap = token.partition("|")
    p = os.path.join(FIGS, name.strip())
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(p).getSize()
    w = ctx.width
    h = w * ih / iw
    if h > 150 * mm:
        h = 150 * mm; w = h * iw / ih
    return [KeepTogether([Spacer(1, 4), Image(p, width=w, height=h), Paragraph(inline(cap.strip(), ctx), ctx.st["Caption"])])]


def md_to_flow(md, ctx):
    for k, v in ctx.tokens.items():
        md = md.replace("{{%s}}" % k, v)
    lines, flow, para, i = md.splitlines(), [], [], 0
    st = ctx.st

    def flush():
        if para:
            flow.append(Paragraph(inline(" ".join(para), ctx), st["Body"])); para.clear()
    while i < len(lines):
        ln = lines[i]; s = ln.strip()
        if s.startswith("```"):
            flush(); j, buf = i + 1, []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                buf.append(lines[j]); j += 1
            flow.append(Preformatted(sanitize("\n".join(buf)), st["Code"], maxLineLength=118))
            i = j + 1; continue
        if not s:
            flush(); i += 1; continue
        if s == "{{PAGEBREAK}}":
            flush(); flow.append(PageBreak()); i += 1; continue
        if s.startswith("{{FIG:") and s.endswith("}}"):
            flush(); flow += figure(s[6:-2], ctx); i += 1; continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            flush(); lvl = len(m.group(1))
            flow.append(Paragraph(inline(m.group(2), ctx), st["H%d" % lvl])); i += 1; continue
        if s.startswith("|"):
            flush(); rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i]); i += 1
            flow += make_table(rows, ctx); continue
        if s.startswith(">"):
            flush(); chunks, cur = [], []
            while i < len(lines) and lines[i].strip().startswith(">"):
                t = lines[i].strip()[1:].strip()
                if t:
                    cur.append(t)
                elif cur:
                    chunks.append(" ".join(cur)); cur = []
                i += 1
            if cur:
                chunks.append(" ".join(cur))
            for c in chunks:
                flow.append(Paragraph(inline(c, ctx), st["Quote"]))
            continue
        mb = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", ln)
        if mb:
            flush(); indent = len(mb.group(1).expandtabs(2)) // 2
            marker, txt = mb.group(2), mb.group(3)
            j = i + 1
            while (j < len(lines) and lines[j].strip() and lines[j].startswith("  ")
                   and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[j])):
                txt += " " + lines[j].strip(); j += 1
            bullet = "\u2022" if marker in "-*" else marker
            if txt.startswith("[ ] "):
                bullet = "\u25a1" if 0x25A1 in COVER else "[ ]"; txt = txt[4:]
            style = ParagraphStyle("b%d" % indent, parent=st["Bullet"], leftIndent=14 + 12 * indent, bulletIndent=3 + 12 * indent)
            flow.append(Paragraph(inline(txt, ctx), style, bulletText=sanitize(bullet)))
            i = j; continue
        para.append(s); i += 1
    flush()
    return flow


class Doc(BaseDocTemplate):
    def __init__(self, path, info, **kw):
        super().__init__(path, **kw)
        self.info = info
        self._hc = 0
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates([PageTemplate("Cover", [frame], onPage=self._cover),
                               PageTemplate("Body", [frame], onPage=self._page)])

    def beforeDocument(self):
        self._hc = 0  # stable bookmark keys across multiBuild passes

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("H1", "H2"):
            lvl = 0 if f.style.name == "H1" else 1
            text = f.getPlainText()
            key = "h%d" % self._hc; self._hc += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=lvl, closed=True)
            self.notify("TOCEntry", (lvl, text, self.page, key))

    def _cover(self, c, doc):
        W, H = A4
        c.saveState()
        c.setFillColor(colors.HexColor("#fcfcfb")); c.rect(0, 0, W, H, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(NAVY)); c.rect(0, H - 128 * mm, W, 128 * mm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor("#86b6ef")); c.setFont("Sans-Bold", 9.5)
        c.drawString(22 * mm, H - 30 * mm, self.info["kicker"].upper())
        ps = ParagraphStyle("ct", fontName="Sans-Bold", fontSize=25, leading=30, textColor=colors.white)
        p = Paragraph(_esc(sanitize(self.info["title"])), ps); w, h = p.wrap(W - 44 * mm, 80 * mm)
        p.drawOn(c, 22 * mm, H - 40 * mm - h)
        ps2 = ParagraphStyle("cs", fontName="Sans", fontSize=11.5, leading=15.5, textColor=colors.HexColor("#cde2fb"))
        p2 = Paragraph(_esc(sanitize(self.info["subtitle"])), ps2); w2, h2 = p2.wrap(W - 44 * mm, 50 * mm)
        p2.drawOn(c, 22 * mm, H - 48 * mm - h - h2)
        c.setFillColor(colors.HexColor(INK)); c.setFont("Sans-Bold", 10.5)
        c.drawString(22 * mm, H - 145 * mm, "Machine Learning for Alpha Signal Combination and Portfolio Construction")
        ps3 = ParagraphStyle("cb", fontName="Body", fontSize=9.2, leading=13.5, textColor=colors.HexColor(INK2))
        p3 = Paragraph(self.info["blurb"], ps3); w3, h3 = p3.wrap(W - 44 * mm, 90 * mm)
        p3.drawOn(c, 22 * mm, H - 152 * mm - h3)
        c.setStrokeColor(colors.HexColor(HAIR)); c.line(22 * mm, 36 * mm, W - 22 * mm, 36 * mm)
        c.setFont("Sans", 8); c.setFillColor(colors.HexColor(MUTED))
        c.drawString(22 * mm, 30 * mm, "Research package | Prepared September 2026 | Status: pre-empirical research proposal")
        c.drawString(22 * mm, 25 * mm, "Evidence labels: Verified | [inference] | [verify] | Proposed | Hypothesis (never a result)")
        c.drawString(22 * mm, 20 * mm, self.info["report_no"])
        c.restoreState()

    def _page(self, c, doc):
        W, H = A4
        c.saveState()
        c.setFont("Sans", 7.4); c.setFillColor(colors.HexColor(MUTED))
        c.drawString(self.leftMargin, H - 13 * mm, sanitize(self.info["short"]))
        c.drawRightString(W - self.rightMargin, H - 13 * mm, "ML Alpha Signal Combination & Portfolio Construction")
        c.setStrokeColor(colors.HexColor(HAIR)); c.setLineWidth(0.4)
        c.line(self.leftMargin, H - 14.8 * mm, W - self.rightMargin, H - 14.8 * mm)
        c.drawCentredString(W / 2, 11 * mm, "%d" % doc.page)
        c.restoreState()


def ref_html(r):
    s = f"{_esc(sanitize(apa_authors(r['authors'])))} ({r['year']}). {_esc(sanitize(r['title']))}. <i>{_esc(sanitize(r['venue']))}</i>."
    if r.get("doi"):
        u = "https://doi.org/" + r["doi"]
        s += f' <link href="{_esc(u)}" color="{BLUE}">{_esc(u)}</link>'
    elif r.get("url"):
        s += f' <link href="{_esc(r["url"])}" color="{BLUE}">{_esc(sanitize(r["url"]))}</link>'
    return s


def build_pdf(path, info, parts, refs, tokens=None):
    setup_fonts()
    doc = Doc(path, info, pagesize=A4, leftMargin=19 * mm, rightMargin=19 * mm, topMargin=21 * mm, bottomMargin=19 * mm,
              title=info["title"], author="ML Alpha Signal Combination Research Team", subject=info["subtitle"],
              creator="ReportLab build script (_build/build_all.py)")
    ctx = Ctx(refs, doc.width, tokens)
    body = []
    for kind, payload in parts:
        if kind == "md":
            body += md_to_flow(payload, ctx)
        elif kind == "break":
            body.append(PageBreak())
    story = [Spacer(1, 1), NextPageTemplate("Body"), PageBreak()]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("t0", fontName="Sans-Bold", fontSize=9.6, leading=13, leftIndent=0, spaceBefore=4, textColor=NAVY),
                       ParagraphStyle("t1", fontName="Sans", fontSize=8.6, leading=11, leftIndent=12, textColor=INK)]
    story += [Paragraph("Contents", ctx.st["TOCHead"]), toc, PageBreak()] + body
    if ctx.cited:
        story += [PageBreak(), Paragraph("References", ctx.st["H1"]),
                  Paragraph("All references cited in this report. DOIs were verified against Crossref or publisher pages where shown; "
                            "working papers, books and conference papers may lack DOIs. Verification status per entry: "
                            "08_References/crossref_verification.csv.", ctx.st["Small"])]
        order = sorted(ctx.cited, key=lambda k: (surnames(refs[k]["authors"])[0].lower(), refs[k]["year"], refs[k]["title"]))
        story += [Paragraph(ref_html(refs[k]), ctx.st["Ref"]) for k in order]
    doc.multiBuild(story)
    return ctx
