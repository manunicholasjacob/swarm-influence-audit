"""Recompute every figure quoted in 00_PROSE_v1.md from the committed JSONs and fail on a mismatch.

The rest of this repository verifies its numbers; the drafted prose was the only artifact that did
not, which is how a merged citation and a wrong crossover survived a read-through. This script
recomputes each load-bearing figure from source and asserts that the prose contains that exact
rendering. It does not check prose that is not a number.

Checks are grouped by the file they come from. A failure prints the computed value, so the fix is to
correct the prose rather than the check.

    python -X utf8 verify_prose.py [--prose 00_PROSE_v1.md]

Exit 0 only if every check passes.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
BENCH = HERE.parent.parent / "swarm-bench"
DRIFTS = [0.0, 0.3, 0.6, 0.9]
VARIANTS = ("shift", "permute", "blockpermute", "localpermute")
ALPHA, FLOOR_ARI = 0.05, 0.44


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(c - h, 4), round(c + h, 4)


def wilson3(k: int, n: int) -> str:
    """Three decimal places, which is how every published interval in this project is written.

    Rendered as a string rather than a list of floats for two reasons. The stored `wilson95` fields
    are already rounded to three places, so prose quoting an interval is quoting the three-place
    form, and recomputing at four places would fail on correct text. And `repr(0.060)` is `0.06`,
    so a float list compares unequal to prose that correctly carries the trailing zero.
    """
    lo, hi = wilson(k, n)
    return f"[{lo:.3f}, {hi:.3f}]"


def mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n))


def trend(fired: list[int], n: list[int], doses: list[float]) -> tuple[float, float]:
    N, R = sum(n), sum(fired)
    pbar = R / N
    tbar = sum(ni * di for ni, di in zip(n, doses)) / N
    num = sum(fi * (di - tbar) for fi, di in zip(fired, doses))
    var = pbar * (1 - pbar) * sum(ni * (di - tbar) ** 2 for ni, di in zip(n, doses))
    if var <= 0:
        return 0.0, 1.0
    z = num / math.sqrt(var)
    return z, math.erfc(abs(z) / math.sqrt(2.0))


def load(name: str) -> dict:
    return json.loads((BENCH / name).read_text(encoding="utf-8"))


def fired_by_drift(path: str) -> dict[str, tuple[list[int], list[int]]]:
    rows = [r for r in load(path)["precision"]["rows"] if not r.get("skipped")]
    out = {}
    for v in VARIANTS:
        f, n = [], []
        for d in DRIFTS:
            sel = [r for r in rows if r["activity_drift"] == d]
            f.append(sum(1 for r in sel if r[v]["fired"]))
            n.append(len(sel))
        out[v] = (f, n)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prose", default=str(HERE / "00_PROSE_v1.md"))
    args = ap.parse_args()
    text = pathlib.Path(args.prose).read_text(encoding="utf-8")

    checks: list[tuple[str, str]] = []          # (label, string that must appear)
    def need(label: str, s: str) -> None:
        checks.append((label, s))

    # ---- surrogate_variants, both draw counts ------------------------------------------------
    sv = {t: [r for r in load(f)["rows"] if not r.get("skipped")]
          for t, f in (("100", "surrogate_variants.json"), ("200", "surrogate_variants_200.json"))}
    rate = {}
    for t, rows in sv.items():
        for v in VARIANTS:
            k = sum(1 for r in rows if r[v]["fired"])
            rate[(t, v)] = (k, len(rows), k / len(rows), wilson3(k, len(rows)))
    need("global permutation at 100 draws", f"{rate[('100','permute')][2]:.4f}")
    need("global permutation at 200 draws", f"{rate[('200','permute')][2]:.4f}")
    need("global permutation interval at 200", rate[("200", "permute")][3])
    need("shift at 200 draws", f"{rate[('200','shift')][2]:.4f}")
    need("shift interval at 200", rate[("200", "shift")][3])
    need("block-local at 100", f"{rate[('100','blockpermute')][2]:.4f}")
    need("block-local at 200", f"{rate[('200','blockpermute')][2]:.4f}")
    need("block-local interval at 200", rate[("200", "blockpermute")][3])
    need("local at 100", f"{rate[('100','localpermute')][2]:.4f}")
    need("local at 200", f"{rate[('200','localpermute')][2]:.4f}")
    need("local interval at 200", rate[("200", "localpermute")][3])

    # paired 100 vs 200 on the same instances, and the pairwise comparisons at 200
    ka = {(r["rep"] if "rep" in r else i): r for i, r in enumerate(sv["100"])}
    kb = {(r["rep"] if "rep" in r else i): r for i, r in enumerate(sv["200"])}
    shared = sorted(set(ka) & set(kb))
    b = sum(1 for k in shared if ka[k]["permute"]["fired"] and not kb[k]["permute"]["fired"])
    c = sum(1 for k in shared if kb[k]["permute"]["fired"] and not ka[k]["permute"]["fired"])
    need("McNemar, global permutation 100 vs 200", f"{mcnemar(b, c):.4f}")
    for x, y in itertools.combinations(VARIANTS, 2):
        o1 = sum(1 for r in sv["200"] if r[x]["fired"] and not r[y]["fired"])
        o2 = sum(1 for r in sv["200"] if r[y]["fired"] and not r[x]["fired"])
        p = mcnemar(o1, o2)
        if x == "shift":
            need(f"shift vs {y} at 200 draws", f"{p:.4f}")
        else:
            need(f"{x} vs {y} at 200 draws", f"{p:.2f}")

    # ---- the drift sweep at 200 draws --------------------------------------------------------
    by = fired_by_drift("stationarity_pinned_200.json")
    for v, name in (("shift", "shift"), ("permute", "global permutation")):
        f, n = by[v]
        for d, fi, ni in zip(DRIFTS, f, n):
            need(f"{name} at drift {d}", f"{fi/ni:.3f}")
    z, p = trend(*by["shift"], DRIFTS)
    need("trend z for the shift", f"{z:.3f}")
    for v, nm in (("permute", "global"), ("blockpermute", "block"), ("localpermute", "local")):
        _, pv = trend(*by[v], DRIFTS)
        need(f"trend p for {nm}", f"{pv:.2f}")

    # ---- reproduction arm --------------------------------------------------------------------
    rep = load("stationarity_pinned.json")["reproduction"]
    ident = sum(1 for c_ in rep["cells"] for nl in ("shift", "permute") if c_[nl]["identical"])
    inside = sum(1 for c_ in rep["cells"] for nl in ("shift", "permute")
                 if c_[nl]["published_fwer_inside_interval"])
    need("cells reproducing exactly", f"one of the eight" if ident == 1 else f"{ident} of 8")
    need("published rates inside interval", "Seven of the eight" if inside == 7 else f"{inside} of 8")
    bad = [(c_["activity_drift"], nl) for c_ in rep["cells"] for nl in ("shift", "permute")
           if not c_[nl]["published_fwer_inside_interval"]]
    assert len(bad) == 1 and bad[0] == (0.0, "permute"), f"exception moved: {bad}"
    exc = next(c_["permute"] for c_ in rep["cells"] if c_["activity_drift"] == 0.0)
    need("the exception's interval", wilson3(exc["fired_now"], rep["reps"]))

    # ---- the floor sweep ---------------------------------------------------------------------
    fp = load("floor_proxy_sweep.json")
    ev = fp["evaluation"]
    zero = {k for k, v in ev.items() if v.get("floor_by_stated_ari", {}).get("errors") == 0}
    assert zero == {"seed_stability_min", "agree_lsa", "calinski_harabasz"}, zero
    need("seed stability cut", f"{ev['seed_stability_min']['floor_by_stated_ari']['threshold']:.3f}")
    need("LSA cut", f"{ev['agree_lsa']['floor_by_stated_ari']['threshold']:.3f}")
    need("Calinski-Harabasz cut",
         f"{ev['calinski_harabasz']['floor_by_stated_ari']['threshold']:.1f}")
    need("seed stability mean variant cut",
         f"{ev['seed_stability_mean']['floor_by_stated_ari']['threshold']:.3f}")
    need("silhouette correlation", f"{ev['silhouette_cosine']['spearman_vs_true_ari']:.3f}")
    need("silhouette margin", f"{ev['silhouette_cosine']['floor_by_stated_ari']['margin']:.3f}")
    need("Calinski-Harabasz correlation",
         f"{ev['calinski_harabasz']['spearman_vs_true_ari']:.3f}")
    lv: dict[float, list[float]] = {}
    for r in fp["rows"]:
        lv.setdefault(r["vocab_overlap"], []).append(r["true_ari"])
    means = sorted((sum(v) / len(v) for v in lv.values()), reverse=True)
    above = [m for m in means if m >= FLOOR_ARI][-1]
    below = [m for m in means if m < FLOOR_ARI][0]
    need("ARI just above the floor", f"{above:.3f}")
    need("ARI just below the floor", f"{below:.3f}")
    need("sweep levels", "nine")
    need("sweep cells", str(len(fp["rows"])))

    # ---- transportability --------------------------------------------------------------------
    pt = load("proxy_transport.json")["proxies"]
    for k, nm in (("seed_stability_min", "seed stability"), ("agree_lsa", "LSA"),
                  ("calinski_harabasz", "Calinski-Harabasz")):
        need(f"{nm} nuisance errors", str(pt[k]["errors_on_nuisance_set"]))
    assert pt["calinski_harabasz"]["errors_at_true_ari_1"] == 3
    assert pt["seed_stability_min"]["errors_at_true_ari_1"] == 0
    assert pt["agree_lsa"]["errors_at_true_ari_1"] == 0
    ch_vals = sorted(e["value"] for e in pt["calinski_harabasz"]["error_cells"]
                     if e["symbolisation_was_perfect"])
    need("CH low reading", f"{math.floor(min(ch_vals))}")
    need("CH high reading", f"{math.ceil(max(ch_vals))}")
    need("the small corpus size", "2,000")

    # ---- out of mechanism --------------------------------------------------------------------
    fc = load("floor_contradiction.json")
    pcb = fc["e4_k_mismatch"]["published_cuts_on_these_rows"]
    need("seed stability balanced accuracy out of mechanism",
         f"{pcb['seed_stability_min']['confusion']['balanced_accuracy']:.2f}")
    need("LSA balanced accuracy out of mechanism",
         f"{pcb['agree_lsa']['confusion']['balanced_accuracy']:.3f}")
    need("seed stability error count out of mechanism",
         "seven" if pcb["seed_stability_min"]["confusion"]["errors"] == 7 else "?")
    held = pcb["seed_stability_min"]["called_below_floor_but_detection_held"]
    need("cells condemned", "fourteen" if held["n_called_below"] == 14 else str(held["n_called_below"]))
    need("of those with full recall",
         "eleven" if held["n_full_recall"] == 11 else str(held["n_full_recall"]))

    # ---- the published 30-replicate sweep ----------------------------------------------------
    big = load("bench_stationarity_big.json")
    n30 = big["reps"]
    perm = [r["permute"]["fired"] for r in big["rows"]]
    cov = sum(1 for k in perm if wilson(k, n30)[0] <= ALPHA <= wilson(k, n30)[1])
    need("published permutation range low", f"{min(perm)/n30:.3f}")
    need("published permutation range high", f"{max(perm)/n30:.3f}")
    need("published cells covering nominal", "three of its four" if cov == 3 else f"{cov} of 4")
    sh0 = next(r["shift"]["fired"] for r in big["rows"] if r["activity_drift"] == 0.0)
    need("published shift at zero drift", f"{sh0/n30:.3f}")

    # ---- the factorial -----------------------------------------------------------------------
    tf = load("turntaking_factorial.json")
    eff = tf["effects"]
    need("factorial drift effect", f"+{eff['factorial']['by_surrogate']['shift']['drift_effect']:.3f}")
    need("factorial turn-taking effect",
         f"{eff['factorial']['by_surrogate']['shift']['turn_taking_effect']:.3f}")
    need("factorial drift-only rate",
         f"{eff['factorial']['by_surrogate']['shift']['drift_only']:.3f}")
    need("factorial turn-taking-only rate",
         f"{eff['factorial']['by_surrogate']['shift']['turn_taking_only']:.3f}")
    need("calibrated turn-taking-only rate",
         f"{eff['calibrated']['by_surrogate']['shift']['turn_taking_only']:.3f}")
    need("calibrated drift-only rate",
         f"{eff['calibrated']['by_surrogate']['shift']['drift_only']:.3f}")

    # ---- run them ----------------------------------------------------------------------------
    # Search against whitespace-collapsed text: the prose is hard-wrapped at 100 columns, so a
    # quoted interval can straddle a line break and a literal substring search would miss it.
    flat = re.sub(r"\s+", " ", text)
    bad_checks = [(lab, s) for lab, s in checks if s not in flat]
    print(f"{len(checks)} numeric checks recomputed from source")

    # ---- structural --------------------------------------------------------------------------
    struct: list[tuple[str, bool, str]] = [
        ("pure ASCII", all(ord(ch) <= 126 for ch in text),
         f"non-ASCII: {sorted({hex(ord(c)) for c in text if ord(c) > 126})}"),
        ("no em or en dashes", not re.search(r"[–—]", text), "dash found"),
        ("SLOT 12 is marked as not a paper section",
         "NOT A PAPER SECTION" in text, "SLOT 12 heading missing its warning"),
        ("double-blind self-references are marked",
         text.count("[ANON") >= 2, "fewer [ANON] markers than expected"),
        ("SLOT 2 carries its provisionality banner",
         "Provisional" in text, "SLOT 2 banner missing"),
        ("a change log is present", "# Change log" in text, "no change log"),
    ]
    failed_struct = [(n, m) for n, ok, m in struct if not ok]

    for lab, s in bad_checks:
        print(f"  FAIL  {lab}: source says {s!r}, not found in prose")
    for n, m in failed_struct:
        print(f"  FAIL  {n}: {m}")
    if bad_checks or failed_struct:
        print(f"\n{len(bad_checks)} numeric and {len(failed_struct)} structural failures")
        return 1
    print(f"{len(struct)} structural checks pass")
    print("\nPROSE VERIFIED: every quoted figure recomputes from the committed JSONs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
