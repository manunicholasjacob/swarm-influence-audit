"""Run every check this project has, in one command, and fail on the first that fails.

There are now five independent checks across two repositories and a submission pack, each of which
caught something real at least once. Running them one at a time is how one gets skipped. This runs
all of them and prints a single verdict.

  1. report/verify_v2.py    71 numeric claims recomputed from the analysis output, plus eleven
                            further rounds including guards that fail if a retracted number
                            reappears and a check that every cross-reference resolves
  2. report/check_pages.py  the body fits the sprint's hard 8-page cap. Checking by eye missed this
                            once: the Conclusion heading sat on page 8 while its last lines spilled
                            onto page 9
  3. report/check_pack.py   the submission pack matches the report it claims to carry
  4. benchmark tests        150 tests in the companion repository, covering the generator, the
                            detector harness, the text layer, the floor analysis and the
                            turn-taking factorial. It said 46 until 9 Nov 2026; the count grew
                            with the 7 Nov work and nothing updated it
  5. report/check_image.py  the project image, which was the only artifact nothing checked until
                            8 Nov 2026 and had drifted. It is the first thing a judge sees
  6. ascii and dashes       no em dashes, no en dashes, no non-ASCII anywhere in the deliverables

Usage:  python verify_all.py [--pack DIR] [--bench DIR]
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
# The benchmark is a sibling checkout, so resolve it that way rather than by absolute path.
DEFAULT_BENCH = HERE.parent / "swarm-bench"
# The submission pack lives outside any repository and has no portable default, so it stays
# unset. What this file used to claim here, and in --pack's help, was that a missing pack is
# reported as a skip that fails the run. That was never true: the pack checks are only added to
# the list when --pack is given, so a bare run has nothing to skip and prints a clean verdict
# with the pack unexamined. The claim is removed rather than implemented, because a runner that
# fails every time it is run from the repository is a runner nobody reads. The verdict now says
# out loud when the pack was not checked.
DEFAULT_PACK = None


def run(label: str, cmd: list[str], cwd: pathlib.Path) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=900)
    except FileNotFoundError as e:
        return False, f"could not run: {e}"
    except subprocess.TimeoutExpired:
        return False, "timed out"
    tail = "\n".join((p.stdout or "").strip().splitlines()[-3:])
    if p.returncode != 0:
        err = "\n".join((p.stderr or "").strip().splitlines()[-5:])
        return False, (tail + "\n" + err).strip()
    return True, tail


# Claims this project withdrew or corrected. report/verify_v2.py guards the report against these;
# until 7 Nov 2026 nothing guarded anything else, and the public README stated two of them
# ("22.7 to 0.0" and "0.17 to 1.00") for as long as the repository had been public. The README is
# read far more often than the report, so guarding only the report guarded the wrong document.
# Keep this list in step with the "no stale ..." rounds in report/verify_v2.py.
RETIRED = [
    "0.17 to 1.00", "precision of **1.00**",
    "22.7 to 0.0", "from 22.7 to",
    "0.17 to 0.71", "precision of **0.71**",
    "4.0 and recovers all 4",
    "every 95% interval covering", "all four 95% intervals",
    "20 of 20 replicates",
]
# A retired claim may legitimately be named in order to retract it. These markers, appearing in the
# same sentence, mean the text is disowning the claim rather than making it.
RETRACTION_MARKERS = (
    "retract", "withdrawn", "no longer", "earlier draft", "was wrong", "refuted",
    "incorrect", "superseded", "not ", "rather than", "instead of", "corrected",
)
DOC_GLOBS = ("*.md", "*.tex", "*.cff")
# A sentence end is a full stop that is not a decimal point.
_SENTENCE_END = re.compile(r"(?<![0-9])\.(?![0-9])")


def _docs(root: pathlib.Path):
    skip_names = {"SWARM_SPRINT_HANDOFF.md"}      # the brief he wrote; not outgoing
    for g in DOC_GLOBS:
        for p in sorted(root.rglob(g)):
            s = str(p)
            if p.name in skip_names or "superseded" in s or ".git" in s.split(os.sep):
                continue
            yield p


def check_retired(root: pathlib.Path) -> tuple[bool, str]:
    """No withdrawn claim may reappear in any document, not just in the report."""
    offenders, n = [], 0
    for p in _docs(root):
        n += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        for claim in RETIRED:
            start = 0
            while (i := text.find(claim, start)) != -1:
                start = i + len(claim)
                # Look at the sentence around the hit plus the one after it, not the whole file.
                # Two things this has to get right, both found by its own false positives:
                #   - the FOLLOWING sentence matters, because documenting a withdrawal reads
                #     'The README stated "X". Both are withdrawn.', and a window stopping at the
                #     first full stop misses the marker and flags honest retraction text;
                #   - a period between digits is a decimal point, not a sentence end. Every claim
                #     guarded here is full of them ("22.7 to 0.0"), so naive splitting closes the
                #     window inside the number it is checking.
                ends = [m.start() for m in _SENTENCE_END.finditer(text)]
                left = max([e + 1 for e in ends if e < i], default=0)
                after = [e for e in ends if e >= start]
                right = after[1] if len(after) > 1 else (after[0] if after else len(text))
                window = text[left:right].lower()
                if any(m in window for m in RETRACTION_MARKERS):
                    continue
                offenders.append(f"{p.relative_to(root)}: states retired claim {claim!r}")
    if offenders:
        return False, "\n".join(sorted(set(offenders))[:12])
    return True, f"checked {n} documents, no retired claim restated"


def check_arxiv_fresh(root: pathlib.Path) -> tuple[bool, str]:
    """arxiv/main.tex is generated from the report, so it must match a fresh generation.

    It had drifted by 58 lines before 7 Nov 2026, including a missing contribution bullet and an
    attribution the report had already corrected. Nothing noticed, because nothing compared them.
    """
    import tempfile
    src = root / "report" / "REPORT_V2.md"
    gen = root / "report" / "to_latex.py"
    out = root / "arxiv" / "main.tex"
    if not (src.exists() and gen.exists() and out.exists()):
        return True, "arxiv package not present, nothing to compare"
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "main.tex"
        p = subprocess.run([sys.executable, "-X", "utf8", str(gen), str(src), str(tmp)],
                           capture_output=True, text=True, timeout=300)
        if p.returncode != 0:
            return False, f"could not regenerate: {(p.stderr or '').strip()[-400:]}"
        fresh = tmp.read_text(encoding="utf-8").splitlines()
    committed = out.read_text(encoding="utf-8").splitlines()
    if fresh == committed:
        return True, f"arxiv/main.tex matches a fresh generation ({len(fresh)} lines)"
    import difflib
    diff = list(difflib.unified_diff(committed, fresh, "committed", "regenerated", lineterm="", n=0))
    return False, (f"arxiv/main.tex is stale by {len(diff)} diff lines. "
                   f"Regenerate it:\n  python -X utf8 report/to_latex.py report/REPORT_V2.md "
                   f"arxiv/main.tex\n" + "\n".join(diff[:12]))


def check_ascii(root: pathlib.Path) -> tuple[bool, str]:
    """No em dashes, en dashes, or other non-ASCII in anything the author ships."""
    offenders, n = [], 0
    for p in _docs(root):
        n += 1
        text = p.read_text(encoding="utf-8", errors="replace")
        bad = sorted({c for c in text if ord(c) > 126})
        if bad:
            offenders.append(f"{p.relative_to(root)}: {[hex(ord(c)) for c in bad]}")
    if offenders:
        return False, "\n".join(offenders[:10])
    return True, f"checked {n} documents, all pure ASCII"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default=None,
                    help="submission pack directory. Without it the two pack checks are not "
                         "run at all and the verdict says so. Pass it before submitting.")
    ap.add_argument("--bench", default=str(DEFAULT_BENCH))
    args = ap.parse_args()

    pack_root = pathlib.Path(args.pack) if args.pack else None
    bench = pathlib.Path(args.bench)
    py = sys.executable

    # check_image.py runs with or without a pack: the image lives in this repository, and only
    # the "pack carries the same image" round needs the pack. It is listed before the pack
    # checks so that a bad image fails even when nobody passed --pack.
    image_cmd = [py, "-X", "utf8", "check_image.py"]
    if pack_root is not None:
        image_cmd += ["--pack", str(pack_root / "deliverables")]

    checks = [
        ("numeric claims and consistency", [py, "verify_v2.py"], HERE / "report"),
        ("8-page body cap", [py, "check_pages.py"], HERE / "report"),
        ("project image claims", image_cmd, HERE / "report"),
        ("benchmark tests", [py, "-m", "pytest", "tests", "-q"], bench),
    ]
    if pack_root is not None:
        pdf = pack_root / "deliverables" / "Apart_Swarm_Report_Manu_Nicholas_Jacob.pdf"
        checks.append(("submission pack matches report",
                       [py, "check_pack.py", str(pack_root / "deliverables")], HERE / "report"))
        checks.append(("sprint submission rules",
                       [py, "check_rubric.py", str(pdf), "--readme", str(HERE / "README.md")],
                       HERE / "report"))

    names = [n for n, _, _ in checks] + ["arxiv source in sync", "retired claims in docs",
                                         "ascii and dashes"]
    total = len(names)
    width = max(len(n) for n in names) + 2
    failed, skipped = [], []

    for name, cmd, cwd in checks:
        if not cwd.exists():
            print(f"{name:<{width}} SKIP  {cwd} not found")
            skipped.append((name, f"{cwd} not found, so this check did not run"))
            continue
        ok, detail = run(name, cmd, cwd)
        print(f"{name:<{width}} {'PASS' if ok else 'FAIL'}")
        if not ok:
            failed.append((name, detail))

    ok, detail = check_arxiv_fresh(HERE)
    print(f"{'arxiv source in sync':<{width}} {'PASS' if ok else 'FAIL'}")
    if not ok:
        failed.append(("arxiv source in sync", detail))

    # These two run over this repository, the benchmark repository, and the pack when one was
    # given. The benchmark was added on 8 Nov 2026: it is linked from the public submission page,
    # so a judge reads its README, and until then nothing guarded it. That is the same mistake as
    # guarding the report but not the README, one repository further out.
    roots = [HERE]
    if bench.exists():
        roots.append(bench)
    if pack_root is not None and pack_root.exists():
        roots.append(pack_root)
    for label, fn in (("retired claims in docs", check_retired), ("ascii and dashes", check_ascii)):
        oks, details = [], []
        for r in roots:
            ok, detail = fn(r)
            oks.append(ok)
            if not ok:
                details.append(detail)
        ok = all(oks)
        print(f"{label:<{width}} {'PASS' if ok else 'FAIL'}")
        if not ok:
            failed.append((label, "\n".join(details)))

    print()
    for name, detail in failed:
        print(f"--- {name} ---")
        print(detail)
        print()
    if skipped and not failed:
        for name, detail in skipped:
            print(f"--- {name}: SKIPPED ---")
            print(detail)
            print()

    ran = total - len(skipped)
    if failed or skipped:
        print(f"NOT ALL CHECKS PASSED: {ran} of {total} ran, "
              f"{len(failed)} failed, {len(skipped)} skipped")
        return 1
    if pack_root is None:
        print(f"ALL {total} CHECKS PASS, but the submission pack was NOT checked. "
              f"Before submitting:  python verify_all.py --pack DIR")
    else:
        print(f"ALL {total} CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
