"""Guard the project image, which was the only artifact nothing checked.

The submission's project image is the first thing a judge sees and the last thing anything
verified. Two defects were sitting in it on 8 Nov 2026, both found by reading the generator
rather than by any check:

  - it printed "A planted agent coupled to nothing reaches z = 72", built from
    max(mean_max_z). 71.7 is the largest of the per-volume MEANS of each run's largest z, over
    eight seeds. It is not a z anyone observed. On a project whose finding is that influence
    statistics get overstated, that is the worst available place to be loose, and the same
    conflation had already reached an outreach draft once.
  - it resolved its input directory from a hardcoded absolute path, so from any other working
    copy it would have drawn the image from this machine's numbers.

Both are now fixed in project_image.py. This exists so neither can come back, and so that the
numbers on the image cannot drift away from the analysis output the way arxiv/main.tex drifted
away from the report.

Five rounds:
  1. the committed PNG is byte-identical to a fresh generation
  2. the committed claims sidecar is identical to a fresh generation
  3. every fact in the sidecar, recomputed independently from the analysis JSONs
  4. the drawn text is consistent with the facts, including the one survivorship claim
  5. no retired claim, and no bare-z phrasing, anywhere in the drawn text

Usage:  python check_image.py [--pack DIR]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

# Resolved from this file. The defect this module exists to guard was a hardcoded path, so
# hardcoding one here would be its own punchline.
ROOT = pathlib.Path(__file__).resolve().parent.parent
GEN = ROOT / "project_image.py"
PNG = ROOT / "project_image.png"
CLAIMS = ROOT / "project_image_claims.json"

failures: list[str] = []
rounds = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global rounds
    rounds += 1
    if not ok:
        failures.append(f"{label}: {detail}" if detail else label)


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default=None, help="submission pack deliverables directory")
    args = ap.parse_args()

    for p in (GEN, PNG, CLAIMS):
        if not p.exists():
            print(f"FAIL  {p.name} is missing. Run: python project_image.py")
            return 1

    # --- rounds 1 and 2: the committed artifacts match a fresh generation -------------------
    # matplotlib's PNG output is byte-reproducible for a given version, so this is a real
    # equality check and not an approximation. If it ever stops being reproducible the right
    # answer is to compare the sidecar only, not to weaken round 3.
    with tempfile.TemporaryDirectory() as td:
        p = subprocess.run([sys.executable, "-X", "utf8", str(GEN), td],
                           capture_output=True, text=True, timeout=600)
        if p.returncode != 0:
            print(f"FAIL  could not regenerate the image: {(p.stderr or '').strip()[-500:]}")
            return 1
        fresh_png = (pathlib.Path(td) / "project_image.png").read_bytes()
        fresh_claims = json.loads(
            (pathlib.Path(td) / "project_image_claims.json").read_text(encoding="utf-8"))

    check("committed PNG matches a fresh generation", PNG.read_bytes() == fresh_png,
          "project_image.png is stale. Regenerate it:  python project_image.py")
    committed = json.loads(CLAIMS.read_text(encoding="utf-8"))
    check("committed claims match a fresh generation", committed == fresh_claims,
          "project_image_claims.json is stale. Regenerate it:  python project_image.py")

    facts = fresh_claims["facts"]
    drawn = fresh_claims["drawn_text"]
    blob = "\n".join(drawn)

    # --- round 3: every fact recomputed from the analysis output ----------------------------
    # Recomputed here from the JSONs rather than read from the sidecar, so that an edit to the
    # generator that quietly swaps one input for another fails this file.
    cal, calbig = load("facts_calib.json"), load("facts_calib_big.json")
    fin, sp = load("facts_final.json"), load("facts_sparse.json")
    bv = json.loads((ROOT.parent / "swarm-bench" / "bench_validation.json")
                    .read_text(encoding="utf-8"))
    st = bv["families"]["structure"]
    # facts_calib2.json is the 30-replicate pilot and must never be the source of the headline
    # error rate. Naming the expected value against the 300-replicate file is what stops a
    # one-character edit to the generator from silently halving the result.
    expected = {
        "shift_fwer": cal["rows"]["shift"]["familywise_error_rate"],
        "perm_fwer": calbig["fwer"],
        "n_edges_shift": fin["headline_by_null"]["shift"]["topic"]["n_edges"],
        "n_edges_permute": fin["headline_by_null"]["permute"]["topic"]["n_edges"],
        "peak_mean_max_z": max(r["mean_max_z"] for r in sp["rows"]),
        "n_seeds": sp["seeds"],
        "n_villages": 4,
        "total_agent_msgs": 245_895,
        "precision_pairwise": st["pairwise"]["pooled_precision"],
        "precision_conditional": st["conditional"]["pooled_precision"],
    }
    for k, want in expected.items():
        got = facts.get(k)
        ok = got == want or (isinstance(want, float) and isinstance(got, (int, float))
                             and abs(got - want) < 1e-9)
        check(f"fact {k}", ok, f"image says {got!r}, analysis output says {want!r}")

    # The village message counts are summed in the generator, so check the total against the
    # report's own Data table rather than against the generator's own arithmetic. The footer
    # once claimed "250k messages", a number nothing had computed.
    check("agent message total is the sum of the four villages",
          205_726 + 35_483 + 3_848 + 838 == facts["total_agent_msgs"],
          f"{facts['total_agent_msgs']} is not the sum of the per-village counts")

    # --- round 4: the drawn text agrees with the facts --------------------------------------
    for k, pat in (("shift_fwer", f"{facts['shift_fwer']:.0%}"),
                   ("perm_fwer", f"{facts['perm_fwer']:.0%}")):
        check(f"{k} appears on the image as drawn", pat in blob,
              f"expected {pat!r} in the drawn text")
    check("village count and message total appear together",
          f"{facts['n_villages']} villages, {facts['total_agent_msgs']:,} agent messages" in blob,
          "the footer no longer states the villages and message total as computed")
    check("precision pair appears as drawn",
          f"from {facts['precision_pairwise']:.2f} to {facts['precision_conditional']:.2f}" in blob,
          "the benchmark precision line no longer matches bench_validation.json")

    # The right-hand panel is titled "none of the 11 survives" while its bars read 11 and 2,
    # which is true only because the two permutation edges are different edges, not survivors.
    # Verified against facts_final.json on 8 Nov 2026: the sets are disjoint. If that ever stops
    # being true the title becomes a false claim, so it is guarded rather than trusted.
    m = re.search(r"none of the (\d+) survives", blob)
    if m:
        hb = fin["headline_by_null"]
        check("survivorship claim: no edge survives both nulls",
              hb["n_survive_both_topic"] == 0 and not hb["survive_both_topic"],
              f"the image says no edge survives, but facts_final.json lists "
              f"{hb['survive_both_topic']!r}")
        check("survivorship claim names the right edge count",
              int(m.group(1)) == facts["n_edges_shift"],
              f"the title says {m.group(1)} edges, the shift null certified "
              f"{facts['n_edges_shift']}")

    # --- round 5: phrasing ------------------------------------------------------------------
    # The defect this file was written for. A mean of per-run maxima may not be drawn as though
    # it were a single observed z, however the sentence is arranged.
    z = f"{facts['peak_mean_max_z']:.0f}"
    for line in drawn:
        if z not in line:
            continue
        check("the peak z is labelled as a mean of maxima",
              "mean largest z" in line,
              f"this line states {z} without saying it is a mean largest z: {line!r}")
        check("the peak z states how many runs it averages",
              f"over {facts['n_seeds']} runs" in line,
              f"this line states {z} without the number of runs: {line!r}")
    # The \b after the digits is load-bearing. Without it \d+ backtracks to a single digit, the
    # lookahead then sees "2 over" instead of " over", and the pattern fires on correct text.
    for bad in (r"reaches z\s*=", r"\bz\s*=\s*\d", r"\bz of \d+(?:\.\d+)?\b(?!\s*over)",
                r"peak z\s*=", r"worst z"):
        check(f"no bare-z phrasing {bad!r}", re.search(bad, blob, re.I) is None,
              "the image presents a z value without saying what it is an average of")

    # Claims this project withdrew. Kept in step with verify_all.py's RETIRED list. No
    # retraction-marker escape hatch here: an image has no room to retract anything, so any
    # appearance is a restatement.
    for claim in ("0.17 to 1.00", "0.17 to 0.71", "22.7 to 0.0", "4.0 and recovers all 4",
                  "20 of 20 replicates"):
        check(f"no retired claim {claim!r}", claim not in blob,
              "a withdrawn number is drawn on the image")

    # --- the pack ---------------------------------------------------------------------------
    if args.pack:
        packed = pathlib.Path(args.pack) / "project_image.png"
        check("pack image is present", packed.exists(), f"{packed} is missing")
        if packed.exists():
            check("pack image is identical to the repository image",
                  packed.read_bytes() == fresh_png,
                  "the pack carries a different image from the one this repository generates")

    if failures:
        print(f"FAIL  {len(failures)} of {rounds} rounds failed\n")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"OK  project image: all {rounds} rounds pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
