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


def _maxT(obs, null, n_draw, pairs):
    """Shared max-T family-wise reduction. Identical arithmetic to the two tests above.

    Factored out when the surrogate variants were added so that a comparison between surrogates
    cannot accidentally become a comparison between two slightly different FWER reductions. The
    two preexisting functions are deliberately left inline and untouched: their outputs are
    verified numbers in the report.
    """
    mu, sd = null.mean(1), null.std(1, ddof=1)
    sd = sd.copy(); sd[sd == 0] = np.inf
    z_obs = (obs - mu) / sd
    max_null = ((null - mu[:, None]) / sd[:, None]).max(0)
    p_fwer = (1 + (max_null[None, :] >= z_obs[:, None]).sum(1)) / (1 + n_draw)
    return {pr: {"te": float(o), "z": float(z), "p": float(p)}
            for pr, o, z, p in zip(pairs, obs, z_obs, p_fwer)}


def directed_tests_permute_block(series_int, A, silent_code, n_perm=200, seed=0, block_size=500):
    """BLOCK-LOCAL permutation: like directed_tests_permute, but confined to blocks of ticks.

    The global within-speaker permutation destroys an agent's symbol-to-time correspondence over
    the whole timeline, so it also destroys any slow drift in WHAT an agent talks about. If the
    channel's topic wanders and every agent follows it, a global permutation makes the surrogate
    less like the observed data than it should be, which inflates z. Permuting only within a block
    of `block_size` consecutive ticks preserves drift at scales longer than the block while still
    destroying correspondence within it.

    This is the direct analogue of the block-permutation null in the attribution-calibration
    package, restricted here to the positions where the agent actually spoke so that sparsity is
    preserved exactly as in the global version.
    """
    rng = np.random.default_rng(seed)
    ids = list(series_int)
    n = len(series_int[ids[0]])
    pairs = [(i, j) for i in ids for j in ids if i != j]
    obs = np.array([te_int(series_int[i], series_int[j], A) for i, j in pairs])

    # Spoken positions per agent, split into blocks once. A trailing block holding fewer than two
    # spoken positions is folded into the previous one: left alone it would be a stretch of the
    # surrogate identical to the real series, which leaks real structure into the null.
    blocks = {}
    for i in ids:
        spoke = np.flatnonzero(series_int[i] != silent_code)
        starts = list(range(0, n, block_size))
        groups = []
        for b, st in enumerate(starts):
            sp = starts[b + 1] if b + 1 < len(starts) else n
            g = spoke[(spoke >= st) & (spoke < sp)]
            if g.size > 1:
                groups.append(g)
            elif g.size == 1 and groups:
                groups[-1] = np.concatenate([groups[-1], g])
        blocks[i] = groups

    null = np.empty((len(pairs), n_perm))
    for p in range(n_perm):
        shuffled = {}
        for i in ids:
            s = series_int[i].copy()
            for g in blocks[i]:
                s[g] = s[g][rng.permutation(g.size)]
            shuffled[i] = s
        for q, (i, j) in enumerate(pairs):
            null[q, p] = te_int(shuffled[i], series_int[j], A)
    return _maxT(obs, null, n_perm, pairs)


def directed_tests_permute_local(series_int, A, silent_code, n_perm=200, seed=0):
    """LOCAL permutation in conditioning state space: Runge (2018), adapted by Shorten et al. (2021).

    Runge's scheme permutes the source only among points whose CONDITIONING state is similar, in
    order to preserve the dependence between source and conditioning while destroying source to
    target. In his continuous setting "similar" means a nearest-neighbour search; at history one
    over a small discrete alphabet the exact analogue is available and needs no neighbourhood
    parameter at all, because states can be matched exactly rather than approximately.

    For the pair (i -> j), te_int reads the triple (t[u+1], t[u], s[u]). The conditioning variable
    is the target's own previous symbol t[u]. So the surrogate permutes s[u] only among positions
    sharing the same t[u], which holds the joint distribution of (source symbol, target past)
    fixed. Positions where the source was silent are excluded, so sparsity is preserved exactly as
    in the other two variants.

    Unlike the global and block variants this null is TARGET-DEPENDENT, so a surrogate has to be
    drawn per ordered pair rather than once per source. That is a property of the method, not an
    inefficiency: a null that preserved the source's relationship to one target would not preserve
    it to another.
    """
    rng = np.random.default_rng(seed)
    ids = list(series_int)
    n = len(series_int[ids[0]])
    pairs = [(i, j) for i in ids for j in ids if i != j]
    obs = np.array([te_int(series_int[i], series_int[j], A) for i, j in pairs])

    null = np.empty((len(pairs), n_perm))
    for q, (i, j) in enumerate(pairs):
        src, tgt = series_int[i], series_int[j]
        # Usable positions: u in [0, n-2] (u+1 must exist) where the source actually spoke.
        u = np.flatnonzero(src[:-1] != silent_code)
        cond = tgt[:-1][u]                      # the conditioning state at each usable position
        order = np.argsort(cond, kind="stable")
        u_sorted, cond_sorted = u[order], cond[order]
        # Contiguous runs of equal conditioning state; runs of length 1 cannot be permuted.
        cuts = np.flatnonzero(np.diff(cond_sorted)) + 1
        groups = [g for g in np.split(u_sorted, cuts) if g.size > 1]
        for p in range(n_perm):
            s = src.copy()
            for g in groups:
                s[g] = s[g][rng.permutation(g.size)]
            null[q, p] = te_int(s, tgt, A)
    return _maxT(obs, null, n_perm, pairs)


def cte_int(s, t, c, A, Ac):
    """Conditional TE(s->t | c), history 1: the extra information s's last symbol gives about t's
    next one, BEYOND t's own history and a channel-context variable c.

    WEEKEND ADDITION. Pairwise transfer entropy cannot tell direct influence from common cause: if
    every agent tracks a drifting channel topic, every pair looks dependent. Conditioning on the
    channel's recent state is the standard remedy. `c` is kept to a small alphabet (Ac) on purpose,
    because the joint space is A^3 * Ac and the series is only a few thousand ticks long.
    """
    s = np.asarray(s); t = np.asarray(t); c = np.asarray(c)
    if t.shape[0] < 3:
        return 0.0
    if c.size and int(c.max()) >= Ac:
        raise ValueError(f"context code {int(c.max())} >= Ac={Ac}; joint indices would collide")
    tt, tp, sp, cc = t[1:], t[:-1], s[:-1], c[:-1]
    h_ttpc = _H((tt * A + tp) * Ac + cc, A * A * Ac)
    h_tpc = _H(tp * Ac + cc, A * Ac)
    h_ttpspc = _H(((tt * A + tp) * A + sp) * Ac + cc, A * A * A * Ac)
    h_tpspc = _H((tp * A + sp) * Ac + cc, A * A * Ac)
    return max(0.0, (h_ttpc - h_tpc) - (h_ttpspc - h_tpspc))


def directed_tests_conditional(series_int, channel, A, Ac, silent_code, n_perm=200, seed=0):
    """Conditional TE for every ordered pair, with the sparsity-preserving permutation surrogate."""
    rng = np.random.default_rng(seed)
    ids = list(series_int)
    pairs = [(i, j) for i in ids for j in ids if i != j]
    obs = np.array([cte_int(series_int[i], series_int[j], channel, A, Ac) for i, j in pairs])
    spoke = {i: np.flatnonzero(series_int[i] != silent_code) for i in ids}
    null = np.empty((len(pairs), n_perm))
    for p in range(n_perm):
        shuffled = {}
        for i in ids:
            v = series_int[i].copy()
            idx = spoke[i]
            if idx.size > 1:
                v[idx] = v[idx][rng.permutation(idx.size)]
            shuffled[i] = v
        for q, (i, j) in enumerate(pairs):
            null[q, p] = cte_int(shuffled[i], series_int[j], channel, A, Ac)
    mu, sd = null.mean(1), null.std(1, ddof=1)
    sd = sd.copy(); sd[sd == 0] = np.inf
    z_obs = (obs - mu) / sd
    max_null = ((null - mu[:, None]) / sd[:, None]).max(0)
    p_fwer = (1 + (max_null[None, :] >= z_obs[:, None]).sum(1)) / (1 + n_perm)
    return {pr: {"te": float(o), "z": float(z), "p": float(p)}
            for pr, o, z, p in zip(pairs, obs, z_obs, p_fwer)}


def channel_context(stream_symbols, silent_code, window=12, n_levels=None):
    """A small-alphabet summary of the channel's recent topic, EXCLUDING the immediately preceding
    message so it does not simply restate the source. Returns an int array over [0, n_levels)."""
    import collections
    n = len(stream_symbols)
    out = np.zeros(n, dtype=np.int64)
    for t in range(n):
        lo = max(0, t - window)
        ctx = [x for x in stream_symbols[lo:max(lo, t - 1)] if x != silent_code]
        if not ctx:
            out[t] = 0
            continue
        mode, _ = collections.Counter(ctx).most_common(1)[0]
        # the channel's recent topic itself. An earlier version returned how CONCENTRATED the
        # window was on its mode, which discarded which topic it was and carried almost no
        # information about it, so conditioning on it did nothing.
        out[t] = mode if n_levels is None else (mode % n_levels)
    return out


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
