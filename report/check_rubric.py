"""Check the SUBMITTED PDF against the sprint's published submission rules.

Deliberately independent of verify_v2.py and check_pack.py. Those two work from REPORT_V2.md and
from a rebuild of it, so they verify that the source is self-consistent and that the PDF matches the
source. Neither of them reads the artifact that is actually uploaded and asks whether it obeys the
rules a judge checks it against. That is this file.

Rules, from apartresearch.com/sprints/swarm-alignment-2026, read 7 Nov 2026:
  - report is a PDF using the official template
  - body at most 8 pages, excluding references and appendices  (check_pages.py owns this one)
  - abstract 150 to 250 words
  - title and author information present
  - a required appendix: "Limitations and Dual-Use / Ethical Considerations"
  - recommended sections: Introduction, Related Work, Methodology, Results, Discussion,
    Limitations and Dual-Use/Ethical Considerations, References
  - pre-existing code marked as preexisting in the README and the report

Usage:  python check_rubric.py <pdf> [--readme PATH]
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ABSTRACT_MIN, ABSTRACT_MAX = 150, 250


def pdf_text(path: pathlib.Path) -> tuple[str, int]:
    import pypdf
    r = pypdf.PdfReader(str(path))
    if r.is_encrypted:
        raise SystemExit(f"{path.name} is encrypted; a judge may not be able to open it")
    pages = [p.extract_text() or "" for p in r.pages]
    return "\n".join(pages), len(pages)


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--readme", default=None)
    a = ap.parse_args()

    pdf = pathlib.Path(a.pdf)
    if not pdf.exists():
        raise SystemExit(f"no such file: {pdf}")
    raw, npages = pdf_text(pdf)
    t = norm(raw)
    tl = t.lower()

    checks: list[tuple[str, bool, str]] = []

    # Abstract word count, as rendered in the PDF rather than as written in the source.
    # Stop at the title footnote, which sits at the foot of page 1 and so lands between the
    # abstract and the Introduction in extraction order. Counting it put a compliant 247-word
    # abstract at 265 and looked like a rule violation.
    m = re.search(r"\bAbstract\b(.*?)(?=\b1\.?\s+Introduction\b)", t, re.I)
    if not m:
        checks.append(("abstract located", False, "could not find Abstract ... Introduction"))
    else:
        seg = re.split(r"\d*\s*Research conducted at", m.group(1))[0]
        # PDF extraction puts a space beside a hyphen that fell on a line break, so "open-chat's"
        # comes back as "open -chat's" and counts as two words. Left uncorrected this read a
        # compliant 247-word abstract as 274 and looked like a rule violation.
        seg = re.sub(r"(?<=[A-Za-z])\s+-\s*(?=[A-Za-z])", "-", seg)
        seg = re.sub(r"(?<=[A-Za-z])-\s+(?=[A-Za-z])", "-", seg)
        words = len(seg.split())
        ok = ABSTRACT_MIN <= words <= ABSTRACT_MAX
        checks.append((f"abstract within {ABSTRACT_MIN} to {ABSTRACT_MAX} words", ok,
                       f"{words} words"
                       + ("" if ok else f"  OUT OF RANGE, the form will reject or a judge will notice")))

    # Author information.
    checks.append(("author named", "manu nicholas jacob" in tl, ""))
    checks.append(("affiliation stated", "independent researcher" in tl, ""))

    # The required appendix, by name or by an explicit statement of where it lives.
    has_named = "limitations and dual-use" in tl or "limitations and dual use" in tl
    has_split = ("appendices a and b" in tl and "required" in tl)
    checks.append(("required Limitations and Dual-Use appendix present", has_named or has_split,
                   "named directly" if has_named else
                   ("split across A and B, and the report says so" if has_split else
                    "NOT FOUND: the sprint asks for this appendix by name")))

    # Recommended sections. Missing ones are reported but do not fail the run, since the sprint
    # calls them recommended rather than required.
    want = {"introduction": "introduction", "related work": "related work",
            "method": "methodology or method", "results": "results",
            "references": "references", "limitations": "limitations"}
    missing = [label for key, label in want.items() if key not in tl]
    checks.append(("recommended sections present", True,
                   "all present" if not missing else f"not found (recommended, not required): {missing}"))

    # Dual-use appendix has to actually discuss dual use, not just be titled that way.
    checks.append(("dual-use content present", "dual-use" in tl or "dual use" in tl, ""))

    # Preexisting work declared in the report, which the sprint rules require.
    checks.append(("preexisting work declared in the report",
                   "preexisting" in tl or "pre-existing" in tl, ""))

    # And in the README, which the rules name separately.
    if a.readme:
        rp = pathlib.Path(a.readme)
        if rp.exists():
            rt = rp.read_text(encoding="utf-8", errors="replace").lower()
            checks.append(("preexisting work declared in the README",
                           "preexisting" in rt or "pre-existing" in rt, str(rp)))
        else:
            checks.append(("preexisting work declared in the README", False, f"no such file: {rp}"))

    # The title footnote names the sprint. The template was reused from a DIFFERENT Apart sprint,
    # so every build said "AI Collusion Research Sprint, October 2026" on page one of a report
    # submitted to the Swarm Alignment hackathon. Nothing caught it because the build filled the
    # title, authors and abstract from the markdown and left the footnote alone.
    wrong_sprint = re.search(r"Research conducted at the\s+(.{0,80}?(?:Sprint|Hackathon))", t, re.I)
    fn = norm(wrong_sprint.group(1)) if wrong_sprint else ""
    checks.append(("title footnote names THIS sprint",
                   bool(fn) and "swarm alignment" in fn.lower(),
                   f"footnote says: {fn!r}" if fn else "no sprint footnote found"))

    # Nothing unexpected should reach a judge's PDF reader as a mangled glyph. Typographic
    # characters the renderer inserts for list bullets are expected and are not the author's text.
    RENDERER_GLYPHS = {"•", " ", "ﬁ", "ﬂ"}   # bullet, nbsp, fi and fl ligatures
    bad = sorted({c for c in raw if ord(c) > 126} - RENDERER_GLYPHS)
    checks.append(("PDF text free of unexpected non-ASCII", not bad,
                   "" if not bad else f"found: {[hex(ord(c)) for c in bad][:8]}"))

    print(f"{pdf.name}: {npages} pages")
    width = max(len(n) for n, _, _ in checks) + 2
    failed = 0
    for name, ok, detail in checks:
        print(f"  {name:<{width}} {'PASS' if ok else 'FAIL'}  {detail}")
        if not ok:
            failed += 1
    print()
    if failed:
        print(f"FAILED {failed} of {len(checks)} rubric checks")
        return 1
    print(f"PASS  all {len(checks)} rubric checks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
