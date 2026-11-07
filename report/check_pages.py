"""Assert the built PDF's BODY ends within the sprint's hard 8-page cap.

This exists because of a mistake. The cap was checked by looking at which page the "7. Conclusion"
heading landed on, which is not the same question: the heading sat on page 8 while the last lines of
the conclusion spilled onto page 9, so the body was over the cap and looked fine. Word's widow and
orphan control also moves the final two lines as a pair, so cutting a single line can change nothing
at all, which made the failure look like a build quirk rather than an over-length body.

Checks the thing that actually matters: no body text appears after the last body page.

    python check_pages.py [pdf] [--cap N]

Exit code 0 if the body fits, 1 if it does not.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pypdf

HERE = Path(__file__).resolve().parent
DEFAULT_PDF = HERE / "Apart_Swarm_Report_Manu_Nicholas_Jacob.pdf"
# The body ends where the appendices begin. Everything from this heading onward is excluded from
# the cap by the sprint guidelines, along with references.
FIRST_APPENDIX = "Appendix A"


def body_pages(pdf_path: Path) -> tuple[int, int, list[str]]:
    """Return (last page holding body text, total pages, the body lines on that page)."""
    reader = pypdf.PdfReader(str(pdf_path))
    last_body_page = 0
    overflow: list[str] = []
    for i, page in enumerate(reader.pages, start=1):
        lines = (page.extract_text() or "").splitlines()
        before, seen_appendix = [], False
        for line in lines:
            if line.strip().startswith(FIRST_APPENDIX):
                seen_appendix = True
                break
            before.append(line)
        if seen_appendix:
            # body text on the same page as the first appendix heading is still body text
            if any(l.strip() for l in before):
                last_body_page = i
                overflow = [l for l in before if l.strip()]
            break
        if any(l.strip() for l in lines):
            last_body_page = i
    return last_body_page, len(reader.pages), overflow


def main() -> int:
    args = [a for a in sys.argv[1:]]
    cap = 8
    if "--cap" in args:
        k = args.index("--cap")
        cap = int(args[k + 1])
        del args[k:k + 2]
    pdf_path = Path(args[0]) if args else DEFAULT_PDF
    if not pdf_path.exists():
        print(f"FAIL  no such pdf: {pdf_path}")
        return 1

    last, total, overflow = body_pages(pdf_path)
    print(f"{pdf_path.name}: {total} pages, body ends on page {last}, cap {cap}")
    if last > cap:
        print(f"FAIL  body runs to page {last}, which is {last - cap} over the {cap}-page cap")
        if overflow:
            print(f"      {len(overflow)} body line(s) spilled past the cap, starting:")
            for line in overflow[:3]:
                print(f"        {line.strip()[:88]}")
        print("      Word keeps the final two lines of a paragraph together, so cutting one line")
        print("      may change nothing. Cut roughly 200 characters at a time and rebuild.")
        return 1
    print(f"PASS  body fits in {cap} pages, appendices and references follow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
