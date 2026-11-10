"""Build every variant of the manuscript from one source, and refuse to accept an anonymous PDF
that leaks an identifier.

One source, three modes, chosen with \\def at build time so the variants cannot drift apart:

  submission   anonymous, for TMLR. The tmlr package hides the author block; the \\ifpreprint
               branches in main.tex suppress the repository URLs and the benchmark's name.
  preprint     de-anonymised, for arXiv. Author block shown, URLs and benchmark name present.
  accepted     camera-ready.

The leak check is the point of this script. The anonymous PDF is the one that gets uploaded, and a
non-anonymous submission is rejected without review, so the check runs on the extracted text of the
built PDF rather than on the source. It also asserts the preprint build DOES carry the identifiers,
because a gate that is stuck shut would silently produce an arXiv preprint with no author on it.

    python -X utf8 build.py [--mode submission|preprint|accepted|all]
"""
from __future__ import annotations
import argparse
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEXBIN = pathlib.Path(r"C:\texlive\2026\bin\windows")

# Strings that must NOT appear in the anonymous build, and MUST appear in the preprint.
IDENTIFIERS = ["Manu", "Nicholas Jacob", "manunicholasjacob", "github.com",
               "SwarmInfluence", "swarm-influence"]
# "Apart" is deliberately absent from this list: the word occurs in ordinary prose ("tell those
# apart") and the organisation's name is not in the manuscript at all.

MODES = {
    "submission": None,
    "preprint": "preprint",
    "accepted": "accepted",
}


def env() -> dict:
    e = dict(os.environ)
    if TEXBIN.exists():
        e["PATH"] = str(TEXBIN) + os.pathsep + e.get("PATH", "")
    return e


def run(cmd: list[str], cwd: pathlib.Path) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, env=env(), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def build(mode: str) -> pathlib.Path:
    """Build one mode into its own jobname so the variants do not overwrite each other."""
    opt = MODES[mode]
    job = "main" if mode == "submission" else f"main-{mode}"
    body = r"\input{main}" if opt is None else rf"\def\TMLRMODE{{{opt}}}\input{{main}}"
    print(f"\n=== building {mode} -> {job}.pdf")
    # Three passes plus bibtex: latexmk decides for itself when a rerun is needed, but it does not
    # thread a \def through reliably, so the passes are explicit.
    for i in (1, 2, 3):
        rc, out = run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                       f"-jobname={job}", body], HERE)
        if rc != 0:
            bad = [ln for ln in out.splitlines() if ln.startswith("!")][:5]
            print(f"  pass {i} FAILED\n    " + "\n    ".join(bad or out.splitlines()[-5:]))
            raise SystemExit(1)
        if i == 1:
            rc, out = run(["bibtex", job], HERE)
            if "error" in out.lower() and rc != 0:
                print("  bibtex FAILED\n" + out[:800])
                raise SystemExit(1)
    pdf = HERE / f"{job}.pdf"
    if not pdf.exists():
        print(f"  no {pdf.name} produced")
        raise SystemExit(1)
    return pdf


def text_of(pdf: pathlib.Path) -> str:
    out = pdf.with_suffix(".txt")
    rc, _ = run(["pdftotext", pdf.name, out.name], HERE)
    if rc != 0 or not out.exists():
        import fitz
        with fitz.open(pdf) as d:
            out.write_text("\n".join(p.get_text() for p in d), encoding="utf-8")
    return out.read_text(encoding="utf-8", errors="replace")


def check(mode: str, pdf: pathlib.Path) -> list[str]:
    txt = text_of(pdf)
    # pdftotext puts a form feed AFTER every page including the last, so splitting yields one
    # empty trailing part and "count + 1" over-reports by one. This said 15 for a 14-page PDF,
    # which is only cosmetic but was confusing enough to need chasing down once.
    parts = txt.split("\f")
    pages = len(parts) - 1 if not parts[-1].strip() else len(parts)
    print(f"  built, {pages} pages, {len(txt.split())} words of extracted text")
    problems = []
    if mode == "submission":
        for s in IDENTIFIERS:
            if s.lower() in txt.lower():
                hits = [ln.strip() for ln in txt.splitlines() if s.lower() in ln.lower()][:2]
                problems.append(f"ANONYMITY LEAK: {s!r} appears in the submission build: {hits}")
        if not problems:
            print("  anonymity: no identifier appears in the submitted PDF")
    else:
        missing = [s for s in IDENTIFIERS if s.lower() not in txt.lower()]
        # The benchmark name and the URLs only appear in the preprint; the author block appears in
        # both preprint and accepted.
        if missing:
            problems.append(f"the de-anonymised build is MISSING {missing}, so the gate is stuck shut")
        else:
            print("  de-anonymised: author and both repository URLs present, as intended")

    # TMLR's FAQ requires the LLM-use disclosure and specifies where it goes: "as a footnote on the
    # first page". A footnote can be pushed to the next page by the surrounding material, so the
    # requirement is checked on the rendered page and not on the source. Verified against
    # jmlr.org/tmlr/faq.html on 10 Nov 2026.
    # TMLR's Regular threshold: "the main content (all pages before references and appendices) is
    # 12 pages or less". This was submitted as Long on 10 Nov because the Conclusion ran onto page
    # 13, then brought under the threshold the same day. The check keeps it there: it finds the
    # page the references begin on and fails if any main content precedes them on that page. The
    # running header is not content, so it is excluded.
    pages = txt.split("\f")
    HEADER = "under review as submission to tmlr"
    ref_page = next((i + 1 for i, p in enumerate(pages) if "References" in p), None)
    if ref_page is None:
        problems.append("no References section found in the built PDF")
    else:
        before = pages[ref_page - 1].split("References")[0]
        leftover = " ".join(before.replace("\f", " ").split())
        if leftover.lower().replace(HEADER, "").strip():
            problems.append(
                f"main content runs onto page {ref_page}, so this is a Long submission, not "
                f"Regular. Overflow: {leftover[:120]!r}")
        else:
            print(f"  length: main content ends on page {ref_page - 1}, "
                  f"references begin page {ref_page} (Regular submission qualifies)")

    page1 = txt.split("\f")[0].lower()
    if "large language model" not in page1:
        where = next((i + 1 for i, p in enumerate(txt.split("\f"))
                      if "large language model" in p.lower()), None)
        problems.append(
            "the required LLM-use disclosure is not on page 1 of the "
            f"{mode} build" + (f"; it rendered on page {where}" if where
                               else "; it is absent from the PDF entirely"))
    else:
        print("  disclosure: LLM-use footnote present on page 1, as TMLR requires")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all", choices=[*MODES, "all"])
    args = ap.parse_args()
    if not shutil.which("pdflatex", path=str(TEXBIN)) and not shutil.which("pdflatex"):
        print("pdflatex not found")
        return 1

    modes = list(MODES) if args.mode == "all" else [args.mode]
    problems: list[str] = []
    for m in modes:
        problems += check(m, build(m))

    print()
    if problems:
        for p in problems:
            print(f"FAIL  {p}")
        return 1
    print(f"ALL {len(modes)} BUILD(S) OK. The submission PDF carries no identifier; "
          f"the preprint carries all of them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
