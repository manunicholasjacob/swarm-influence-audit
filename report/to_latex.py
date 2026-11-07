#!/usr/bin/env python3
"""Convert the swarm-sprint Markdown report into an arXiv-ready LaTeX source file.

Usage:
    python to_latex.py <input.md> <output.tex> [--figure-source <dir>]

Example:
    python -X utf8 -I report/to_latex.py report/REPORT_V2.md arxiv/main.tex \
        --figure-source .

The converter is deliberately faithful. It never rewords, reflows or drops
content, it keeps the author's own figure numbers even where they run out of
order, and it keeps table cells byte for byte apart from markup translation.
Anything it does not recognise raises an error instead of being passed through
unchecked, so a change to the Markdown cannot silently lose text.

Markdown constructs handled:
    "# Title"                        document title
    front matter lines              author block (name, affiliation, email are
                                    constants below; remaining lines are kept)
    "## Abstract"                   abstract environment
    "## N. Heading"                 \\section, printed "N. Heading"
    "### N.M Heading"               \\subsection, printed "N.M Heading"
    "## Appendix X: Heading"        \\section after \\appendix, printed in full
    "## References"                 thebibliography block, one bibitem per line
    "| a | b |" tables              booktabs tabular, or tabularx when too wide
    "[Figure N: file.png. Caption: ...]"  figure with the author's own number
    "- item"                        itemize
    "N. item"                       enumerate
    "**bold**"                      \\textbf
    "`code`"                        \\texttt
    bare http(s) URLs               \\url
    paired straight double quotes   LaTeX opening and closing quotes

Output guarantees, all asserted before the file is written:
    pure ASCII, no "--" sequence anywhere (so no en dash can be produced),
    no unescaped LaTeX special character, appendix letters in order A..I.
"""

import argparse
import os
import re
import shutil
import sys

AUTHOR_NAME = "Manu Nicholas Jacob"
AUTHOR_AFFIL = "Independent Researcher"
AUTHOR_EMAIL = "manunicholasjacob@gmail.com"

FIGURE_WIDTH = r"0.9\textwidth"

# Natural table width, in characters, above which the table is set smaller and
# then, above the second threshold, wrapped with tabularx.
WIDTH_SMALL = 95
WIDTH_FOOTNOTE = 115

SPECIALS = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "%": r"\%",
    "#": r"\#",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

URL_PATTERN = r"https?://[^\s)]+[^\s).,;]"
CODE_PATTERN = r"`[^`]*`"
BOLD_PATTERN = r"\*\*[^*]+\*\*"
INLINE_RE = re.compile("(%s|%s|%s)" % (CODE_PATTERN, BOLD_PATTERN, URL_PATTERN))
URL_ONLY_RE = re.compile(URL_PATTERN + "$")

FIGURE_RE = re.compile(r"^\[Figure (\d+): (\S+\.png)\. Caption: (.+)\]$")
SECTION_RE = re.compile(r"^## (\d+)\.\s+(.+)$")
SUBSECTION_RE = re.compile(r"^### (\d+\.\d+)\s+(.+)$")
APPENDIX_RE = re.compile(r"^## Appendix ([A-Z]): (.+)$")
ORDERED_RE = re.compile(r"^(\d+)\.\s+(.+)$")
BULLET_RE = re.compile(r"^-\s+(.+)$")


# ---------------------------------------------------------------- inline text


def escape_text(text):
    """Escape every LaTeX special character, one pass, no double escaping."""
    return "".join(SPECIALS.get(ch, ch) for ch in text)


def apply_quotes(text, state):
    """Turn straight double quotes into LaTeX opening and closing quotes.

    `state` is a one-element list holding the running count of quotes seen so
    far on the current line, so that a quoted phrase split across a bold span
    still pairs up correctly.
    """
    out = []
    for ch in text:
        if ch == '"':
            out.append("``" if state[0] % 2 == 0 else "''")
            state[0] += 1
        else:
            out.append(ch)
    return "".join(out)


def plain(text, state):
    """Escape literal text and fix its quotes."""
    return apply_quotes(escape_text(text), state)


def inline(text, state=None, allow_bold=True):
    """Translate one line of Markdown inline markup into LaTeX."""
    if state is None:
        state = [0]
    pieces = []
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            pieces.append(r"\texttt{%s}" % escape_text(part[1:-1]))
        elif part.startswith("**") and part.endswith("**"):
            if not allow_bold:
                raise ValueError("nested bold span: %r" % part)
            pieces.append(r"\textbf{%s}" % inline(part[2:-2], state, allow_bold=False))
        elif URL_ONLY_RE.match(part):
            pieces.append(r"\url{%s}" % part)
        else:
            pieces.append(plain(part, state))
    return "".join(pieces)


def strip_markup(text):
    """Markup-free text, used only to estimate how wide a table will be."""
    return text.replace("**", "").replace("`", "")


# -------------------------------------------------------------------- parsing


def split_front_matter(lines):
    """Return (title, extra author lines, index of the first "## " heading)."""
    if not lines or not lines[0].startswith("# "):
        raise ValueError("expected the document title on line 1")
    title = lines[0][2:].strip()
    i = 1
    extra = []
    while i < len(lines) and not lines[i].startswith("## "):
        text = lines[i].strip()
        if text:
            text = re.sub(r"^\*\*%s\*\*,?\s*" % re.escape(AUTHOR_NAME), "", text)
            text = re.sub(r"^%s\.?\s*" % re.escape(AUTHOR_AFFIL), "", text)
            if text:
                extra.append(text)
        i += 1
    return title, extra, i


def read_table(lines, i):
    """Read a pipe table starting at line i. Returns (rows, next index)."""
    rows = []
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        raw = lines[i].strip()
        if not re.match(r"^\|[\s:|-]+\|$", raw):
            cells = [c.strip() for c in raw.strip("|").split("|")]
            rows.append(cells)
        i += 1
    widths = {len(r) for r in rows}
    if len(widths) != 1:
        raise ValueError("ragged table near line %d: column counts %s" % (i, widths))
    return rows, i


def read_list(lines, i, pattern, group):
    """Read a run of list items starting at line i, allowing blank separators."""
    items = []
    while i < len(lines):
        m = pattern.match(lines[i].rstrip())
        if m:
            items.append(m.group(group))
            i += 1
            continue
        if not lines[i].strip():
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and pattern.match(lines[j].rstrip()):
                i = j
                continue
        break
    return items, i


def render_table(rows):
    ncols = len(rows[0])
    widths = [max(len(strip_markup(r[j])) for r in rows) for j in range(ncols)]
    natural = sum(widths) + 3 * ncols
    if natural <= WIDTH_SMALL:
        size, env = r"\small", "tabular"
    elif natural <= WIDTH_FOOTNOTE:
        size, env = r"\footnotesize", "tabular"
    else:
        size, env = r"\footnotesize", "tabularx"

    if env == "tabular":
        colspec = "l" * ncols
        opening = r"\begin{tabular}{%s}" % colspec
        closing = r"\end{tabular}"
    else:
        colspec = "".join("L" if widths[j] > 10 else "l" for j in range(ncols))
        if "L" not in colspec:
            colspec = "L" * ncols
        opening = r"\begin{tabularx}{\textwidth}{%s}" % colspec
        closing = r"\end{tabularx}"

    out = [r"\begin{center}", size, opening, r"\toprule"]
    header = " & ".join(r"\textbf{%s}" % inline(c) for c in rows[0])
    out.append(header + r" \\")
    out.append(r"\midrule")
    for row in rows[1:]:
        out.append(" & ".join(inline(c) for c in row) + r" \\")
    out.append(r"\bottomrule")
    out.append(closing)
    out.append(r"\end{center}")
    return out


def resolve_figure(name, source_dir):
    """Map a figure name in the Markdown onto a file that exists on disk."""
    if source_dir is None:
        return name
    direct = os.path.join(source_dir, name)
    if os.path.isfile(direct):
        return name
    candidates = [f for f in os.listdir(source_dir) if f.lower().endswith(".png")]
    for cand in candidates:
        if cand.lower() == name.lower():
            return cand
    stem = os.path.splitext(name)[0].lower()
    for cand in candidates:
        if os.path.splitext(cand)[0].lower() == stem:
            return cand
    raise ValueError("figure %r not found in %s (saw %s)" % (name, source_dir, candidates))


def render_figure(number, filename, caption):
    return [
        r"\setcounter{figure}{%d}" % (int(number) - 1),
        r"\begin{figure}[H]",
        r"\centering",
        r"\includegraphics[width=%s]{%s}" % (FIGURE_WIDTH, filename),
        r"\caption{%s}" % inline(caption),
        r"\end{figure}",
    ]


def render_bibliography(entries):
    out = [r"\begin{thebibliography}{}"]
    for key, text in entries:
        out.append(r"\bibitem{%s}" % key)
        out.append(inline(text))
    out.append(r"\end{thebibliography}")
    return out


def bib_key(text, index):
    first = re.match(r"[A-Za-z]+", text)
    year = re.search(r"\((\d{4})\)", text)
    stem = (first.group(0).lower() if first else "ref") + (year.group(1) if year else str(index))
    return stem


# ------------------------------------------------------------------- preamble


PREAMBLE = r"""\documentclass[11pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[letterpaper,margin=1in]{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
\usepackage{float}
\usepackage[labelfont=bf,labelsep=period,font=small]{caption}
\usepackage{enumitem}
\usepackage{parskip}
\usepackage{microtype}
\usepackage[hidelinks]{hyperref}
\usepackage{xurl}

\newcolumntype{L}{>{\raggedright\arraybackslash}X}
\setlist[enumerate]{leftmargin=1.6em,itemsep=0.35em,topsep=0.4em,parsep=0pt}
\setlist[itemize]{leftmargin=1.2em,itemsep=0.35em,topsep=0.4em,parsep=0pt}

%% Headings carry the same numbers the source document uses: "1. Introduction"
%% for a section, "4.1 From open language to symbols" for a subsection.
\renewcommand{\thesection}{\arabic{section}.}
\renewcommand{\thesubsection}{\arabic{section}.\arabic{subsection}}
\makeatletter
\renewcommand{\@seccntformat}[1]{\csname the#1\endcsname\hspace{0.5em}}
%% Reference list entries are plain hanging paragraphs, with no bracket labels,
%% because the source cites by author and year in running text.
\renewcommand{\@biblabel}[1]{}
\makeatother

\title{TITLE}
\author{AUTHORBLOCK}
\date{}
"""


def build_preamble(title, extra_lines):
    author = [escape_text(AUTHOR_NAME), escape_text(AUTHOR_AFFIL),
              r"\texttt{%s}" % escape_text(AUTHOR_EMAIL)]
    tail = [inline(line) for line in extra_lines]
    block = r" \\ ".join(author)
    if tail:
        block += r" \\[0.6em] " + r" \\ ".join(tail)
    return (PREAMBLE
            .replace("TITLE", r"\textbf{%s}" % inline(title))
            .replace("AUTHORBLOCK", block))


# ----------------------------------------------------------------- conversion


def convert(md_text, figure_source=None):
    lines = md_text.replace("\r\n", "\n").split("\n")
    title, extra, start = split_front_matter(lines)

    body = []
    figures = {}
    bib = []
    in_appendix = False
    appendix_seen = []
    i = start

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue

        if line.startswith("## Abstract"):
            i += 1
            para = []
            while i < len(lines) and not lines[i].startswith("## "):
                if lines[i].strip():
                    para.append(lines[i].strip())
                i += 1
            body.append(r"\begin{abstract}")
            body.extend(inline(p) for p in para)
            body.append(r"\end{abstract}")
            continue

        if line.startswith("## References"):
            i += 1
            n = 0
            while i < len(lines):
                text = lines[i].strip()
                if text:
                    n += 1
                    bib.append((bib_key(text, n), text))
                i += 1
            continue

        m = APPENDIX_RE.match(line)
        if m:
            letter, heading = m.group(1), m.group(2)
            if not in_appendix:
                body.append("")
                body.append("%% ================ APPENDICES A to I ================")
                body.append(r"\appendix")
                body.append(r"\renewcommand{\thesection}{Appendix \Alph{section}:}")
                in_appendix = True
            appendix_seen.append(letter)
            body.append("")
            body.append(r"\section{%s}" % inline(heading))
            i += 1
            continue

        m = SECTION_RE.match(line)
        if m:
            if in_appendix:
                raise ValueError("numbered section after the appendices: %r" % line)
            if m.group(1) == "1":
                body.append("%% ================ BODY, SECTIONS 1 to 7 ================")
            body.append("")
            body.append(r"\section{%s}" % inline(m.group(2)))
            i += 1
            continue

        m = SUBSECTION_RE.match(line)
        if m:
            body.append("")
            body.append(r"\subsection{%s}" % inline(m.group(2)))
            i += 1
            continue

        m = FIGURE_RE.match(line)
        if m:
            number, name, caption = m.group(1), m.group(2), m.group(3)
            resolved = resolve_figure(name, figure_source)
            figures[name] = resolved
            body.append("")
            body.extend(render_figure(number, resolved, caption))
            i += 1
            continue

        if line.lstrip().startswith("|"):
            rows, i = read_table(lines, i)
            body.append("")
            body.extend(render_table(rows))
            continue

        if ORDERED_RE.match(line):
            items, i = read_list(lines, i, ORDERED_RE, 2)
            body.append("")
            body.append(r"\begin{enumerate}")
            body.extend(r"\item %s" % inline(it) for it in items)
            body.append(r"\end{enumerate}")
            continue

        if BULLET_RE.match(line):
            items, i = read_list(lines, i, BULLET_RE, 1)
            body.append("")
            body.append(r"\begin{itemize}")
            body.extend(r"\item %s" % inline(it) for it in items)
            body.append(r"\end{itemize}")
            continue

        if line.startswith("#"):
            raise ValueError("unhandled heading: %r" % line)
        if line.lstrip().startswith(("> ", "![", "```")):
            raise ValueError("unhandled block: %r" % line)

        body.append("")
        body.append(inline(line.strip()))
        i += 1

    expected = [chr(ord("A") + n) for n in range(len(appendix_seen))]
    if appendix_seen != expected:
        raise ValueError("appendix letters out of order: %s" % appendix_seen)

    out = [build_preamble(title, extra)]
    out.append(r"\begin{document}")
    out.append(r"\maketitle")
    out.extend(body)
    if bib:
        out.append("")
        out.extend(render_bibliography(bib))
    out.append("")
    out.append(r"\end{document}")
    return "\n".join(out) + "\n", figures


def check_output(tex):
    """Fail loudly rather than ship a file that breaks a stated requirement."""
    try:
        tex.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("output is not pure ASCII: %s" % exc)
    if "--" in tex:
        where = tex.index("--")
        raise ValueError("output contains a double hyphen near: %r" % tex[where - 40:where + 40])

    # Unescaped specials are checked on the document body, where the report's
    # own prose lives. File names and URLs are verbatim arguments and are
    # exempt, as are LaTeX comment lines.
    body = tex.split(r"\begin{document}", 1)[1]
    in_table = False
    for line in body.split("\n"):
        if re.search(r"\\begin\{tabular", line):
            in_table = True
        if re.search(r"\\end\{tabular", line):
            in_table = False
        if line.lstrip().startswith("%"):
            continue
        rest = re.sub(r"\\url\{[^}]*\}", "", line)
        rest = re.sub(r"\\includegraphics(\[[^]]*\])?\{[^}]*\}", "", rest)
        for pair in (r"\%", r"\&", r"\$", r"\#", r"\_", r"\{", r"\}"):
            rest = rest.replace(pair, "")
        # Inside a tabular, "&" is the column separator and is meant to be bare.
        suspects = "%$#_" if in_table else "%&$#_"
        for ch in suspects:
            if ch in rest:
                raise ValueError("unescaped %r in: %r" % (ch, line))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("input", help="path to the Markdown report")
    ap.add_argument("output", help="path to the .tex file to write")
    ap.add_argument("--figure-source", default=None,
                    help="directory holding the PNG figures; when given, the "
                         "referenced figures are copied next to the .tex")
    args = ap.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        md_text = fh.read()

    tex, figures = convert(md_text, args.figure_source)
    check_output(tex)

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with open(args.output, "w", encoding="ascii", newline="\n") as fh:
        fh.write(tex)
    print("wrote %s (%d lines)" % (args.output, tex.count("\n")))

    if args.figure_source:
        for name, resolved in sorted(figures.items()):
            src = os.path.join(args.figure_source, resolved)
            dst = os.path.join(out_dir, resolved)
            if os.path.abspath(src) != os.path.abspath(dst):
                shutil.copyfile(src, dst)
            note = "" if name == resolved else " (named %s in the Markdown)" % name
            print("  figure %s%s" % (resolved, note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
