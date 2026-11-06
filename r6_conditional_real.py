"""Conditional TE on the real channels, and the calibration check it has to pass first.

On the benchmark, conditioning on the channel's recent modal topic removed every common-cause false
edge (22.7 -> 0.0) while keeping all four planted edges. Two things must hold before that is usable:
it must not be silently over-conservative (pure nulls must still behave, and planted edges must still
be found), and it must say something about the real channels.
"""
import json, time, collections
import numpy as np
import swarmlib as S
import swarm_te
import fastte

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, TOP_K = 8, 200, 15
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)


def build(span, agents, key="_topic"):
    sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
    n = len(sub)
    series = {a: [swarm_te.SILENT] * n for a in agents}
    for t, m in enumerate(sub):
        series[m["_sp"]][t] = m[key]
    coded, A = fastte.code_series(series)
    alpha = sorted({x for v in series.values() for x in v})
    sil = alpha.index(swarm_te.SILENT)
    chan = [alpha.index(m[key]) for m in sub]
    return coded, A, sil, chan, n


def modal_ctx(chan, sil, window=12):
    out = np.zeros(len(chan), dtype=np.int64)
    for t in range(len(chan)):
        lo = max(0, t - window)
        c = [x for x in chan[lo:max(lo, t - 1)] if x != sil]
        out[t] = collections.Counter(c).most_common(1)[0][0] if c else sil
    return out


out = {"k": K, "n_surrogates": N, "window": 12}

# ---- calibration: structure-free data must still behave under conditioning ----
msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
speakers = [m["_sp"] for m in sub]; symbols = [m["_topic"] for m in sub]
REPS = 20
fired = 0
for r in range(REPS):
    rng = np.random.default_rng(8800 + r)
    sh = list(symbols); rng.shuffle(sh)
    n = len(sh)
    series = {a: [swarm_te.SILENT] * n for a in agents}
    for t, (sp, sy) in enumerate(zip(speakers, sh)):
        series[sp][t] = sy
    coded, A = fastte.code_series(series)
    alpha = sorted({x for v in series.values() for x in v}); sil = alpha.index(swarm_te.SILENT)
    ctx = modal_ctx([alpha.index(x) for x in sh], sil)
    t_ = fastte.directed_tests_conditional(coded, ctx, A, A, sil, n_perm=N, seed=r)
    fired += any(v["p"] < 0.05 for v in t_.values())
out["calibration_pure_null"] = {"reps": REPS, "fired": fired, "fwer": round(fired / REPS, 3)}
log(f"calibration on structure-free real data: {fired}/{REPS} (FWER {fired/REPS:.3f})")
json.dump(out, open("facts_conditional.json", "w", encoding="utf-8"), indent=2)

# ---- the real channels ----
for village, room_id in (("main-village", GENERAL), ("open-chat-village", None)):
    m2, nm2, rm2 = S.load_village(village)
    room = room_id or S.busiest_room(m2)
    sp2, l2, h2 = S.cut_window(m2, room, days=14)
    S.symbolise(sp2, k=K, seed=0)
    ag2 = S.select_agents(sp2, min_msgs=50, top_k=TOP_K)
    label = lambda a: nm2.get(a, a)
    coded, A, sil, chan, n = build(sp2, ag2)
    ctx = modal_ctx(chan, sil)
    tp = fastte.directed_tests_permute(coded, A, sil, n_perm=N, seed=0)
    tc = fastte.directed_tests_conditional(coded, ctx, A, A, sil, n_perm=N, seed=0)
    ep = {e for e, v in tp.items() if v["p"] < 0.05}
    ec = {e for e, v in tc.items() if v["p"] < 0.05}
    out[village] = {
        "n_ticks": n, "agents": len(ag2),
        "pairwise_edges": len(ep), "conditional_edges": len(ec),
        "surviving": sorted([[label(i), label(j)] for (i, j) in (ep & ec)]),
        "n_surviving": len(ep & ec),
        "conditional_only": sorted([[label(i), label(j)] for (i, j) in (ec - ep)]),
    }
    log(f"{village}: pairwise {len(ep)} -> conditional {len(ec)} "
        f"(surviving both {len(ep & ec)})")
    json.dump(out, open("facts_conditional.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_conditional.json")
