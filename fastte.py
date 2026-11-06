"""Vectorised integer-coded transfer entropy + max-T FWER null, for scale.

WEEKEND CODE. The ESTIMATOR DEFINITION is the preexisting one in swarm_te.py; this file only
reimplements it over small-alphabet integer arrays with numpy bincount so the circular-shift null
and the monitor sweep run in seconds instead of minutes. `python fastte.py` proves it reproduces
swarm_te.transfer_entropy and swarm_te.directed_tests bit-for-bit on real-shaped series.
"""
import numpy as np


def _H(codes, base):
    c = np.bincount(codes, minlength=base).astype(float)
    n = c.sum()
    if n == 0:
        return 0.0
    p = c[c > 0] / n
    return float(-(p * np.log2(p)).sum())


def te_int(s, t, A):
    """TE(s->t) at history 1 for integer series in [0, A). Same definition as swarm_te.transfer_entropy."""
    s = np.asarray(s); t = np.asarray(t)
    if t.shape[0] < 3:
        return 0.0
    tt, tp, sp = t[1:], t[:-1], s[:-1]
    h_ttp = _H(tt * A + tp, A * A)
    h_tp = _H(tp, A)
    h_ttpsp = _H((tt * A + tp) * A + sp, A * A * A)
    h_tpsp = _H(tp * A + sp, A * A)
    return max(0.0, (h_ttp - h_tp) - (h_ttpsp - h_tpsp))


def directed_tests_fast(series_int, A, n_shifts=200, seed=0, min_shift=2):
    """Reproduces swarm_te.directed_tests over integer series. series_int: {agent: np.int array}."""
    rng = np.random.default_rng(seed)
    ids = list(series_int)
    n = len(series_int[ids[0]])
    shifts = rng.integers(min_shift, max(min_shift + 1, n - min_shift), size=n_shifts)
    pairs = [(i, j) for i in ids for j in ids if i != j]
    obs = np.array([te_int(series_int[i], series_int[j], A) for i, j in pairs])
    null = np.array([[te_int(np.roll(series_int[i], int(k)), series_int[j], A) for k in shifts]
                     for i, j in pairs])
    mu, sd = null.mean(1), null.std(1, ddof=1)
    sd = sd.copy(); sd[sd == 0] = np.inf
    z_obs = (obs - mu) / sd
    max_null = ((null - mu[:, None]) / sd[:, None]).max(0)
    p_fwer = (1 + (max_null[None, :] >= z_obs[:, None]).sum(1)) / (1 + n_shifts)
    return {pr: {"te": float(o), "z": float(z), "p": float(p)}
            for pr, o, z, p in zip(pairs, obs, z_obs, p_fwer)}


def directed_tests_permute(series_int, A, silent_code, n_perm=200, seed=0):
    """WEEKEND ADDITION. Same max-T family-wise machinery, but a SPARSITY-PRESERVING null.

    The preexisting circular-shift null rolls the whole source series, which moves a sparse speaker's
    silences around and leaves the null TE distribution near-degenerate: a tiny numerator divided by a
    tiny standard deviation produces a huge z, so sparse speakers are certified as drivers of nothing.
    Here the source keeps the exact positions where it spoke and only its SYMBOLS are permuted among
    those positions. Speaking pattern, sparsity and adjacency are held fixed; only the symbol-to-time
    correspondence is destroyed, which is the thing the alternative hypothesis is about.
    """
    rng = np.random.default_rng(seed)
    ids = list(series_int)
    pairs = [(i, j) for i in ids for j in ids if i != j]
    obs = np.array([te_int(series_int[i], series_int[j], A) for i, j in pairs])
    spoke = {i: np.flatnonzero(series_int[i] != silent_code) for i in ids}
    null = np.empty((len(pairs), n_perm))
    for p in range(n_perm):
        shuffled = {}
        for i in ids:
            s = series_int[i].copy()
            idx = spoke[i]
            if idx.size > 1:
                s[idx] = s[idx][rng.permutation(idx.size)]
            shuffled[i] = s
        for q, (i, j) in enumerate(pairs):
            null[q, p] = te_int(shuffled[i], series_int[j], A)
    mu, sd = null.mean(1), null.std(1, ddof=1)
    sd = sd.copy(); sd[sd == 0] = np.inf
    z_obs = (obs - mu) / sd
    max_null = ((null - mu[:, None]) / sd[:, None]).max(0)
    p_fwer = (1 + (max_null[None, :] >= z_obs[:, None]).sum(1)) / (1 + n_perm)
    return {pr: {"te": float(o), "z": float(z), "p": float(p)}
            for pr, o, z, p in zip(pairs, obs, z_obs, p_fwer)}


def code_series(series_str):
    """Map {agent: [symbol strings]} to {agent: int array} over one shared alphabet; returns (coded, A)."""
    alpha = sorted({s for v in series_str.values() for s in v})
    idx = {a: k for k, a in enumerate(alpha)}
    return {a: np.array([idx[s] for s in v], dtype=np.int64) for a, v in series_str.items()}, len(alpha)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, r"C:\dev\swarm-prep")
    import swarm_te
    from swarm_load import to_events, TopicSymboliser, _synthetic_chat

    # 1) single-pair equivalence on synthetic coded series
    rng = np.random.default_rng(3)
    A = 9
    bad = 0
    for _ in range(200):
        n = rng.integers(5, 400)
        s = rng.integers(0, A, n); t = rng.integers(0, A, n)
        a = swarm_te.transfer_entropy([f"x{v}" for v in s], [f"x{v}" for v in t])
        b = te_int(s, t, A)
        bad += abs(a - b) > 1e-9
    print("single-pair TE mismatches out of 200:", bad)

    # 2) full directed_tests equivalence on a real-shaped synthetic chat
    rows = _synthetic_chat(couple=0.7, seed=1)
    ev = to_events(rows, symboliser=TopicSymboliser(k=4, seed=0))
    series, n = swarm_te.windowed_series(ev, width=30.0 * 6)
    ref = swarm_te.directed_tests(series, n_shifts=100, seed=0)
    coded, Ac = code_series(series)
    got = directed_tests_fast(coded, Ac, n_shifts=100, seed=0)
    dp = max(abs(ref[k]["p"] - got[k]["p"]) for k in ref)
    dte = max(abs(ref[k]["te"] - got[k]["te"]) for k in ref)
    print(f"directed_tests: max |dp|={dp:.3e}  max |dTE|={dte:.3e}  (A={Ac}, {len(ref)} pairs, n={n})")
    print("EQUIVALENT" if dp < 1e-12 and dte < 1e-9 else "DIFFERS")
