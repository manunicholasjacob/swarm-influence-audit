# arXiv package: An Agent That Copies Nobody Is Certified as a Leader

This directory is a self-contained LaTeX build of `../report/REPORT_V2.md`.
It is generated, not hand-written. Edit the Markdown, regenerate, recompile.

## Contents

| file | what it is |
|-|-|
| `main.tex` | the whole paper, generated from the Markdown, pure ASCII |
| `main.pdf` | the compiled result, 16 pages |
| `f2_null.png` | Figure 1, Section 5.2 |
| `f4_power.png` | Figure 2, Appendix G |
| `f1_clock.png` | Figure 3, Appendix F |
| `README_ARXIV.md` | this file |

There is no `refs.bib` and no BibTeX step. The reference entries live in a
`thebibliography` block at the end of `main.tex`, copied verbatim from the
Markdown's own References section, so `main.tex` plus the three PNGs is
everything the document needs. (`../report/refs.bib` exists but is stale: it
holds four of the six entries and is not used here.)

## Rebuild

Regenerate the LaTeX from the Markdown, then compile. Run both commands from
the repository root (`C:\dev\swarm-sprint`).

```
python -X utf8 report\to_latex.py report\REPORT_V2.md arxiv\main.tex --figure-source .
cd arxiv
C:\texlive\2026\bin\windows\pdflatex -interaction=nonstopmode -halt-on-error main.tex
C:\texlive\2026\bin\windows\pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

`--figure-source` points at the directory holding the PNGs; the converter
resolves every figure the Markdown references and copies it next to `main.tex`.
Both arguments to the converter are paths you pass in, so the same script works
from any checkout.

Run pdflatex twice. The second pass settles the hyperref bookmarks. There is no
BibTeX, no `makeindex` and no shell-escape.

The converter refuses to write a file that would break any of the rules this
package is built on. It fails if the output is not pure ASCII, if a `--`
sequence appears anywhere (which LaTeX would set as an en dash), if a LaTeX
special character in the body text is left unescaped, if a table has ragged
rows, or if the appendix letters do not run A, B, C and so on in order.

## What to upload to arXiv

Upload these four files, with no directory nesting:

```
main.tex
f1_clock.png
f2_null.png
f4_power.png
```

Do not upload `main.pdf`; arXiv builds the PDF from the source. Do not upload
`README_ARXIV.md` or any `.aux`, `.log` or `.out` file. arXiv's TeX Live has
every package used here: geometry, graphicx, booktabs, tabularx, array, float,
caption, enumitem, parskip, microtype, hyperref, xurl, lmodern.

## Things worth knowing before editing `main.tex` by hand

Prefer editing the Markdown and regenerating. If you do edit the LaTeX
directly, three things in it are deliberate.

**Figure numbers are set by hand.** The source numbers its figures 1, 3, 2 in
order of appearance, because Figure 2 is in Appendix G and Figure 3 is in
Appendix F. Each figure is preceded by a `\setcounter{figure}{...}` and placed
with `[H]` so it cannot float away from that counter. Reordering or renumbering
them would diverge from the Word build of the same report.

**Headings carry the source's own numbering.** `\thesection` is redefined so a
body section prints "1. Introduction" and a subsection prints "4.1 From open
language to symbols", matching the Markdown exactly. After `\appendix` it is
redefined again so an appendix prints its full title, "Appendix A: Limitations".
Sections 1 to 7 are the body and A to I are the appendices; the `\appendix`
command is the dividing line.

**The output is ASCII and stays ASCII.** Straight double quotes in the source
become LaTeX `` `` `` and `''` pairs, which is why curly quotes appear in the
PDF while the `.tex` file has none. No em dash or en dash appears in the source,
the `.tex` or the PDF.
