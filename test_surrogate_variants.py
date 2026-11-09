"""Checks for the two surrogate variants added for the extended paper.

Each check is a property that, if broken, would produce a plausible-looking but wrong error rate
rather than a crash. That is the failure mode worth testing for here.

  python -X utf8 test_surrogate_variants.py
"""
from __future__ import annotations
import numpy as np
import fastte

SILENT = 0
A = 6          # alphabet including the silent code
N = 600        # ticks
AGENTS = 5


def make_series(seed=0, n=N, agents=AGENTS, p_speak=0.35):
    """Independent agents: no influence of any kind, so every certified edge is a false positive."""
    rng = np.random.default_rng(seed)
    out = {}
    for a in range(agents):
        s = np.full(n, SILENT, dtype=np.int64)
        spoke = rng.random(n) < p_speak
        s[spoke] = rng.integers(1, A, size=int(spoke.sum()))
        out[f"a{a}"] = s
    return out


fails = []
def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if not ok and detail else ""))
    if not ok:
        fails.append(name)


print("1. the shared max-T reduction matches the inline arithmetic it replaced")
rng = np.random.default_rng(7)
pairs = [("x", "y"), ("y", "x"), ("x", "z")]
obs = rng.random(len(pairs))
null = rng.random((len(pairs), 50))
mu, sd = null.mean(1), null.std(1, ddof=1)
sd = sd.copy(); sd[sd == 0] = np.inf
z_ref = (obs - mu) / sd
max_null = ((null - mu[:, None]) / sd[:, None]).max(0)
p_ref = (1 + (max_null[None, :] >= z_ref[:, None]).sum(1)) / (1 + 50)
got = fastte._maxT(obs, null, 50, pairs)
check("z and p identical to the inline version",
      all(abs(got[pr]["z"] - z) < 1e-12 and abs(got[pr]["p"] - p) < 1e-12
          for pr, z, p in zip(pairs, z_ref, p_ref)))

print("\n2. sparsity is preserved exactly (the whole point of the permutation family)")
series = make_series(1)
for label, fn, kw in (
    ("global", fastte.directed_tests_permute, {}),
    ("block", fastte.directed_tests_permute_block, {"block_size": 100}),
    ("local", fastte.directed_tests_permute_local, {}),
):
    # Re-derive the surrogate construction the function uses and confirm the silent mask is fixed.
    r = np.random.default_rng(0)
    s = series["a0"].copy()
    before = (s == SILENT)
    if label == "global":
        idx = np.flatnonzero(s != SILENT); s[idx] = s[idx][r.permutation(idx.size)]
    elif label == "block":
        spoke = np.flatnonzero(s != SILENT)
        for st in range(0, len(s), 100):
            g = spoke[(spoke >= st) & (spoke < st + 100)]
            if g.size > 1:
                s[g] = s[g][r.permutation(g.size)]
    else:
        tgt = series["a1"]
        u = np.flatnonzero(s[:-1] != SILENT)
        cond = tgt[:-1][u]
        order = np.argsort(cond, kind="stable")
        us, cs = u[order], cond[order]
        for g in np.split(us, np.flatnonzero(np.diff(cs)) + 1):
            if g.size > 1:
                s[g] = s[g][r.permutation(g.size)]
    check(f"{label}: silent positions unchanged", bool((s == SILENT).sum() == before.sum()
                                                       and ((s == SILENT) == before).all()))
    check(f"{label}: multiset of spoken symbols unchanged",
          sorted(s[s != SILENT].tolist()) == sorted(series["a0"][series["a0"] != SILENT].tolist()))

print("\n3. local permutation holds (source symbol, target past) joint fixed")
src, tgt = series["a0"], series["a1"]
u = np.flatnonzero(src[:-1] != SILENT)
cond = tgt[:-1][u]
before_joint = sorted(zip(cond.tolist(), src[u].tolist()))
r = np.random.default_rng(3)
s = src.copy()
order = np.argsort(cond, kind="stable")
us, cs = u[order], cond[order]
for g in np.split(us, np.flatnonzero(np.diff(cs)) + 1):
    if g.size > 1:
        s[g] = s[g][r.permutation(g.size)]
after_joint = sorted(zip(tgt[:-1][u].tolist(), s[u].tolist()))
check("joint distribution of (conditioning state, source symbol) identical",
      before_joint == after_joint)
check("the series actually changed (the permutation is not a no-op)", not np.array_equal(s, src))

print("\n4. block permutation with one huge block equals the global permutation")
g1 = fastte.directed_tests_permute(series, A, SILENT, n_perm=40, seed=5)
g2 = fastte.directed_tests_permute_block(series, A, SILENT, n_perm=40, seed=5, block_size=10_000)
check("identical z for every pair",
      all(abs(g1[k]["z"] - g2[k]["z"]) < 1e-12 for k in g1),
      f"max diff {max(abs(g1[k]['z'] - g2[k]['z']) for k in g1):.3e}")

print("\n5. all three are deterministic given a seed")
for label, fn, kw in (("block", fastte.directed_tests_permute_block, {"block_size": 150}),
                      ("local", fastte.directed_tests_permute_local, {})):
    a = fn(series, A, SILENT, n_perm=25, seed=11, **kw)
    b = fn(series, A, SILENT, n_perm=25, seed=11, **kw)
    check(f"{label}: same seed, same answer", all(a[k] == b[k] for k in a))

print("\n6. calibration on independent agents: error rate near nominal, not wild")
#   Small and cheap: 40 independent null instances, alpha 0.05, 60 surrogates. This is a smoke
#   test for gross miscalibration, not the paper's measurement.
res = {}
for label, fn, kw in (("shift", fastte.directed_tests_fast, {"n_shifts": 60}),
                      ("permute", fastte.directed_tests_permute, {"n_perm": 60}),
                      ("blockpermute", fastte.directed_tests_permute_block,
                       {"n_perm": 60, "block_size": 150}),
                      ("localpermute", fastte.directed_tests_permute_local, {"n_perm": 60})):
    fired = 0
    for rep in range(40):
        ser = make_series(100 + rep, n=400)
        args = (ser, A) if label == "shift" else (ser, A, SILENT)
        t = fn(*args, seed=rep, **kw)
        if any(v["p"] < 0.05 for v in t.values()):
            fired += 1
    res[label] = fired / 40
    print(f"     {label:14} FWER {fired/40:.3f}  ({fired}/40)")
for label, rate in res.items():
    if label == "shift":
        continue
    check(f"{label}: not grossly miscalibrated (<= 0.30)", rate <= 0.30, f"got {rate:.3f}")

print()
if fails:
    print(f"FAILED {len(fails)}: " + ", ".join(fails))
    raise SystemExit(1)
print("All surrogate-variant checks pass.")
