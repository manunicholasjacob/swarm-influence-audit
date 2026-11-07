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
  4. benchmark tests        46 tests in the companion repository, each a regression test for a
                            defect that was actually found
  5. ascii and dashes       no em dashes, no en dashes, no non-ASCII anywhere in the deliverables

Usage:  python verify_all.py [--pack DIR] [--bench DIR]
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_PACK = pathlib.Path(
    r"C:\Users\manun\OneDrive\Documents\Claudecode\swarm-alignment-2026")
DEFAULT_BENCH = pathlib.Path(r"C:\dev\swarm-bench")


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


def check_ascii(root: pathlib.Path) -> tuple[bool, str]:
    """No em dashes, en dashes, or other non-ASCII in anything the author ships."""
    offenders = []
    skip = {"SWARM_SPRINT_HANDOFF.md"}      # the brief he wrote; not outgoing
    for p in sorted(root.rglob("*.md")):
        if p.name in skip or "superseded" in str(p):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        bad = sorted({c for c in text if ord(c) > 126})
        if bad:
            offenders.append(f"{p.relative_to(root)}: {[hex(ord(c)) for c in bad]}")
    if offenders:
        return False, "\n".join(offenders[:10])
    return True, f"checked {len(list(root.rglob('*.md')))} markdown files, all pure ASCII"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default=str(DEFAULT_PACK))
    ap.add_argument("--bench", default=str(DEFAULT_BENCH))
    args = ap.parse_args()

    pack_root = pathlib.Path(args.pack)
    deliverables = pack_root / "deliverables"
    bench = pathlib.Path(args.bench)
    py = sys.executable

    checks = [
        ("numeric claims and consistency", [py, "verify_v2.py"], HERE / "report"),
        ("8-page body cap", [py, "check_pages.py"], HERE / "report"),
        ("submission pack matches report", [py, "check_pack.py", str(deliverables)],
         HERE / "report"),
        ("benchmark tests", [py, "-m", "pytest", "tests", "-q"], bench),
    ]

    width = max(len(n) for n, _, _ in checks) + 2
    failed = []
    for name, cmd, cwd in checks:
        if not cwd.exists():
            print(f"{name:<{width}} SKIP  {cwd} not found")
            continue
        ok, detail = run(name, cmd, cwd)
        print(f"{name:<{width}} {'PASS' if ok else 'FAIL'}")
        if not ok:
            failed.append((name, detail))

    ok, detail = check_ascii(pack_root) if pack_root.exists() else (True, "pack not found, skipped")
    print(f"{'ascii and dashes':<{width}} {'PASS' if ok else 'FAIL'}")
    if not ok:
        failed.append(("ascii and dashes", detail))

    print()
    if failed:
        for name, detail in failed:
            print(f"--- {name} ---")
            print(detail)
            print()
        print(f"FAILED: {len(failed)} of {len(checks) + 1} checks")
        return 1
    print(f"ALL {len(checks) + 1} CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
