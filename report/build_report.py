"""Build the submission .docx from REPORT_DRAFT.md inside the official Apart template (exported from Manu's
Drive copy as template.docx): fills the template's own title box, author grid and abstract cell, removes the
instruction box and guidance text, and lays out the body in the template's styles.
Usage: python -X utf8 -I report/build_report.py report/REPORT_DRAFT.md report/template.docx OUT.docx"""
import copy, re, sys
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

md_path, tpl_path, out_path = sys.argv[1:4]
md = open(md_path, encoding="utf-8").read()
D = docx.Document(tpl_path)
root = __import__("os").path.dirname(__import__("os").path.abspath(md_path)) + "/.."


def set_text(p, lines, bold=False, italic=None, size=None):
    """Replace a paragraph's runs with `lines` (line breaks between), keeping the first run's formatting."""
    runs = p.runs
    rpr = copy.deepcopy(runs[0]._r.rPr) if runs and runs[0]._r.rPr is not None else None
    keep = []  # the template's footnote marker on the title must survive
    for r in list(p._p):
        if r.tag in (qn("w:r"), qn("w:hyperlink")):
            if r.find(".//" + qn("w:footnoteReference")) is not None:
                keep.append(r)
            p._p.remove(r)
    for i, line in enumerate(lines):
        r = p.add_run(line)
        if rpr is not None:
            r._r.insert(0, copy.deepcopy(rpr))
        if bold:
            r.bold = True
        if italic is not None:
            r.italic = italic
        if size:
            r.font.size = Pt(size)
        if i < len(lines) - 1:
            r.add_break()
    for r in keep:
        p._p.append(r)


# ---- parse the draft ----
title = re.search(r"^# (.+)$", md, re.M).group(1).strip()
abstract = md.split("## Abstract", 1)[1].split("\n## ", 1)[0].strip()
body = "## " + md.split("\n## 1.", 1)[1].join(["", ""]) if False else "## 1." + md.split("\n## 1.", 1)[1]

# ---- title box ----
box = D.tables[0]
title_cell = box.rows[0].cells[0]
for p in title_cell.paragraphs:
    if p.style.name == "Title":
        set_text(p, [title])
    elif p.text.strip():
        set_text(p, [""])  # stray header-like text in the title cell
# Replace the 6-slot author grid with one author line above "With Apart Research".
holder = box.rows[1].cells[0].tables[0].rows[0].cells[0]
grid_el = holder.tables[0]._tbl
with_p = next(p for p in holder.paragraphs if p.text.strip().startswith("With"))
author_p = copy.deepcopy(with_p._p)
grid_el.addprevious(author_p)
grid_el.getparent().remove(grid_el)
ap = docx.text.paragraph.Paragraph(author_p, with_p._parent)
set_text(ap, ["Manu Nicholas Jacob", "Independent Researcher"], bold=False)
ap.paragraph_format.space_after = Pt(6)
abs_cell = box.rows[1].cells[0].tables[1].rows[0].cells[0]
set_text(abs_cell.paragraphs[0], [abstract], italic=False, size=10.5)  # keeps a 250-word abstract inside the title box
for extra in abs_cell.paragraphs[1:]:
    extra._p.getparent().remove(extra._p)

# ---- remove the instruction box and all guidance after it (keep the final sectPr) ----
bd = D.element.body
instructions = D.tables[1]._tbl
started = False
for el in list(bd):
    if el is instructions:
        started = True
    if started and el.tag != qn("w:sectPr"):
        bd.remove(el)


URL_RE = re.compile(r"(https?://[^\s)]+[^\s).,;])")


def add_link(p, url, size=None):
    """Append `url` to paragraph `p` as a clickable, underlined blue hyperlink."""
    rid = p.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), rid)
    r = OxmlElement("w:r"); rpr = OxmlElement("w:rPr")
    c = OxmlElement("w:color"); c.set(qn("w:val"), "1155CC"); rpr.append(c)
    u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rpr.append(u)
    if size:
        sz = OxmlElement("w:sz"); sz.set(qn("w:val"), str(int(size * 2))); rpr.append(sz)
    r.append(rpr); t = OxmlElement("w:t"); t.text = url; t.set(qn("xml:space"), "preserve"); r.append(t)
    h.append(r); p._p.append(h)


def add_par(text="", style="normal", align=None, size=None, italic=False, space_after=4):
    p = D.add_paragraph(style=style)
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        bold = part.startswith("**")
        for piece in URL_RE.split(part[2:-2] if bold else part):
            if not piece:
                continue
            if URL_RE.fullmatch(piece):
                add_link(p, piece, size); continue
            r = p.add_run(piece)
            r.bold = bold or None
            r.italic = italic or None
            if size:
                r.font.size = Pt(size)
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p


def borders(tbl):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "BFBFBF")
        b.append(e)
    tblPr.append(b)


def add_table(lines):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\|\s*-", l)]
    t = D.add_table(rows=len(rows), cols=len(rows[0]))
    borders(t)
    for i, r in enumerate(rows):
        for j, val in enumerate(r):
            cell = t.cell(i, j); cell.text = ""
            run = cell.paragraphs[0].add_run(val.replace("**", ""))
            run.font.size = Pt(8.5); run.bold = (i == 0) or None
    D.add_paragraph(style="normal").paragraph_format.space_after = Pt(2)


fig_re = re.compile(r"^\[Figure ([A-Z]?\d+): ([^.]+\.png)\. Caption: (.+)\]$")
lines = body.splitlines()
i = 0
while i < len(lines):
    ln = lines[i].rstrip()
    if not ln:
        i += 1; continue
    if ln.startswith("### "):
        D.add_paragraph(ln[4:], style="Heading 3")
    elif ln.startswith("## "):
        D.add_paragraph(ln[3:], style="Heading 2")
    elif ln.startswith("|"):
        block = []
        while i < len(lines) and lines[i].startswith("|"):
            block.append(lines[i]); i += 1
        add_table(block); continue
    elif fig_re.match(ln):
        n, path, cap = fig_re.match(ln).groups()
        D.add_picture(f"{root}/{path.strip()}", width=Inches(4.9))
        D.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        D.paragraphs[-1].paragraph_format.keep_with_next = True  # never strand a caption on the next page
        add_par(f"**Figure {n}.** {cap}", size=8.5, italic=False, space_after=8)
    elif re.match(r"^\d+\. ", ln) or ln.startswith("- "):
        txt = ln[2:] if ln.startswith("- ") else ln
        p = add_par(("• " + txt) if ln.startswith("- ") else txt, space_after=2)
        p.paragraph_format.left_indent = Inches(0.25)
    else:
        add_par(ln)
    i += 1

cp = D.core_properties
cp.title, cp.author, cp.last_modified_by, cp.comments = title, "Manu Nicholas Jacob", "Manu Nicholas Jacob", ""

# The template carries a footnote on the title naming the sprint, and it named the WRONG one.
# template.docx was reused from the AI Collusion Research Sprint, so every build of this report
# said "Research conducted at the AI Collusion Research Sprint, October 2026" on page one, in a
# document submitted to a different hackathon run by the same organisation. The title box, author
# grid and abstract cell were all being filled from the markdown; the footnote was not, so nothing
# ever corrected it. Rewrite it here rather than editing the template, so a future template swap
# cannot silently reintroduce it.
FOOTNOTE = "Research conducted at the Apart Research Swarm Alignment Hackathon, November 2026"
_fn_part = next((p for p in D.part.package.parts
                 if p.partname.endswith("footnotes.xml")), None)
if _fn_part is not None:
    # This part is raw XML rather than a parsed element, so edit the bytes and put them back.
    from lxml import etree as _etree
    _root = _etree.fromstring(_fn_part.blob)
    _ts = _root.findall(".//" + qn("w:t"))
    # The template's footnote is split across runs by its own formatting. Put the whole corrected
    # sentence in the first text node and blank the rest, which keeps the run properties intact.
    _body = [t for t in _ts if (t.text or "").strip()]
    if _body:
        _body[0].text = FOOTNOTE
        _body[0].set(qn("xml:space"), "preserve")
        for t in _body[1:]:
            t.text = ""
        _fn_part._blob = _etree.tostring(_root, xml_declaration=True,
                                         encoding="UTF-8", standalone=True)
        print("footnote set to:", FOOTNOTE)
    else:
        print("WARNING: footnote part found but no text nodes; check page 1 by eye")
else:
    print("WARNING: no footnotes.xml in the template; nothing to correct")

D.save(out_path)
print("wrote", out_path)
