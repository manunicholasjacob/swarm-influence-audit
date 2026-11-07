"""Check that the submission pack is consistent with the report it is supposed to carry.

This exists because the pack drifts silently. Three real failures it would have caught:

  - the submission form carried an abstract from an earlier draft, containing three claims that had
    since been retracted, while the report's own abstract was correct
  - the project image showed a 10 percent error rate taken from a superseded 30-replicate pilot
    while the report headlined 6.3 percent from 300 replicates
  - a stale PDF sat in the pack while the current one sat in the build directory

None of these break a build or fail a test. They are only visible if something compares the pack
against the source, which is what this does.

Usage:  python check_pack.py <deliverables_dir> [--report REPORT_V2.md]

Exit code 0 if the pack is consistent, 1 if it is not.
"""
from __future__ import annotations

import argparse
import filecmp
import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
PDF_NAME = "Apart_Swarm_Report_Manu_Nicholas_Jacob.pdf"
DOCX_NAME = "Apart_Swarm_Report_Manu_Nicholas_Jacob.docx"

# Numbers and phrases that were retracted during the work. If one reappears anywhere in the pack's
# own prose, something was written from memory rather than from the report.
RETRACTED = [
    "0.17 to 1.00",
    "22.7 to 0.0",
    "mutual exclusivity",
    "all 18 of open-chat",
    "18 edges to 0",
    "Four controls",
]


def abstract_of(markdown: str) -> str:
    m = re.search(r"## Abstract\n+(.+?)\n\n", markdown, re.S)
    if not m:
        raise SystemExit("FAIL  could not find an Abstract section in the report")
    return " ".join(m.group(1).split())


def quoted_abstract(form_text: str) -> str | None:
    m = re.search(r"\*\*Abstract.*?\n((?:> .*\n)+)", form_text)
    if not m:
        return None
    return " ".join(" ".join(l[2:] for l in m.group(1).splitlines()).split())


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pack")
    ap.add_argument("--report", default=str(HERE / "REPORT_V2.md"))
    args = ap.parse_args()

    pack = pathlib.Path(args.pack)
    report = pathlib.Path(args.report)
    if not pack.is_dir():
        print(f"FAIL  no such directory: {pack}")
        return 1

    problems: list[str] = []
    md = report.read_text(encoding="utf-8")

    # 1. the built artifacts in the pack must be byte-identical to the ones beside the source
    for name in (PDF_NAME, DOCX_NAME):
        built, shipped = HERE / name, pack / name
        if not shipped.exists():
            problems.append(f"{name} missing from the pack")
        elif not built.exists():
            problems.append(f"{name} missing from the build directory, cannot compare")
        elif not filecmp.cmp(built, shipped, shallow=False):
            problems.append(f"{name} in the pack differs from the build "
                            f"(build {sha(built)}, pack {sha(shipped)}). Re-copy it.")

    # 2. the report source in the pack must match the one that was built from
    shipped_md = pack / report.name
    if not shipped_md.exists():
        problems.append(f"{report.name} missing from the pack")
    elif shipped_md.read_text(encoding="utf-8") != md:
        problems.append(f"{report.name} in the pack differs from the source. Re-copy it.")

    # 3. any abstract quoted in the pack must match the report's, exactly
    abstract = abstract_of(md)
    for form in sorted(pack.glob("*.md")):
        text = form.read_text(encoding="utf-8")
        q = quoted_abstract(text)
        if q is None:
            continue
        if q != abstract:
            problems.append(f"{form.name} quotes an abstract that differs from the report's. "
                            f"Re-sync it.")

    # 4. retracted claims must not appear in the pack's own prose
    for form in sorted(pack.glob("*.md")):
        if form.name == report.name:
            continue           # the report itself is checked by verify_v2.py
        text = form.read_text(encoding="utf-8")
        for phrase in RETRACTED:
            if phrase.lower() in text.lower():
                # allow it where the file is explicitly flagging the retraction
                window = text.lower()
                i = window.index(phrase.lower())
                context = window[max(0, i - 220):i + 220]
                before = window[max(0, i - 24):i]
                if any(w in context for w in
                       ("retract", "superseded", "refuted", "wrong", "do not", "removed",
                        "stale", "withdraw", "corrected", "regenerated", "no longer",
                        "earlier draft", "used to")):
                    continue
                # "..., not 0.17 to 1.00" and "rather than X" are corrections, not assertions
                if any(before.rstrip().endswith(w) for w in
                       ("not", "rather than", "instead of", "never", "no longer")):
                    continue
                problems.append(f"{form.name} states the retracted claim {phrase!r} "
                                f"without flagging it as retracted")

    # 5. the arXiv abstract limits, since the pack feeds that submission
    if len(abstract) > 1920:
        problems.append(f"abstract is {len(abstract)} characters, over arXiv's 1920 cap")
    non_ascii = sorted({c for c in abstract if ord(c) > 126})
    if non_ascii:
        problems.append(f"abstract contains non-ASCII characters {non_ascii}, "
                        f"which arXiv rejects as bad characters")

    print(f"pack: {pack}")
    print(f"abstract: {len(abstract.split())} words, {len(abstract)} characters, "
          f"{'ASCII' if not non_ascii else 'NON-ASCII'}")
    if problems:
        print(f"\nFAIL  {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("PASS  pack is consistent with the report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
