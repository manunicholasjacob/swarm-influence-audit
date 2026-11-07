"""Two gaps left by the conditional analysis.

(1) main-village's two edges survive conditioning, which makes them the strongest claim in the
    report. Do they also REPLICATE in the adjacent fourteen-day window under the same conditioning?
    Replication was only ever measured pairwise, so this is the claim's last untested leg.
(2) swarm-village, the 133-agent one-day burst, was never re-certified conditionally, so the
    cross-channel table is incomplete.
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


def modal_ctx(chan, sil, window=12):
    out = np.zeros(len(chan), dtype=np.int64)
    for t in range(len(chan)):
        lo = max(0, t - window)
        c = [x for x in chan[lo:max(lo, t - 1)] if x != sil]
        out[t] = collections.Counter(c).most_common(1)[0][0] if c else sil
    return out


def certify(span, agents, mode):
    sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
    n = len(sub)
    series = {a: [swarm_te.SILENT] * n for a in agents}
    for t, m in enumerate(sub):
        series[m["_sp"]][t] = m["_topic"]
    coded, A = fastte.code_series(series)
    alpha = sorted({x for v in series.values() for x in v}); sil = alpha.index(swarm_te.SILENT)
    if mode == "conditional":
        ctx = modal_ctx([alpha.index(m["_topic"]) for m in sub], sil)
        t_ = fastte.directed_tests_conditional(coded, ctx, A, A, sil, n_perm=N, seed=0)
    else:
        t_ = fastte.directed_tests_permute(coded, A, sil, n_perm=N, seed=0)
    return {e for e, v in t_.items() if v["p"] < 0.05}, n


out = {"k": K, "n_surrogates": N}

# ---- (1) conditional replication in main-village ----
msgs, names, rooms = S.load_village("main-village")
cur, lo, hi = S.cut_window(msgs, GENERAL, days=14)
prev, plo, phi = S.cut_window(msgs, GENERAL, days=14, offset_days=14)
cur_ok = set(S.select_agents(cur, 50, None)); prev_ok = set(S.select_agents(prev, 50, None))
common = S.select_agents(cur + prev, 50, None, restrict=cur_ok & prev_ok)[:TOP_K]
union = [m["content"] for m in cur] + [m["content"] for m in prev]
S.symbolise(cur, k=K, seed=0, fit_corpus=union)
S.symbolise(prev, k=K, seed=0, fit_corpus=union)
nm = lambda a: names.get(a, a)
rep = {"common_agents": len(common)}
for mode in ("pairwise", "conditional"):
    ec, nc = certify(cur, common, mode)
    ep, np_ = certify(prev, common, mode)
    rep[mode] = {"cur_edges": len(ec), "prev_edges": len(ep), "shared": len(ec & ep),
                 "jaccard": round(S.jaccard(ec, ep), 4),
                 "cur_list": [[nm(i), nm(j)] for (i, j) in sorted(ec)],
                 "shared_list": [[nm(i), nm(j)] for (i, j) in sorted(ec & ep)]}
    log(f"main replication {mode:12s}: cur {len(ec)} prev {len(ep)} shared {len(ec & ep)} "
        f"J={rep[mode]['jaccard']}")
out["main_replication"] = rep
json.dump(out, open("facts_conditional_extra.json", "w", encoding="utf-8"), indent=2)

# ---- (2) swarm-village, conditionally ----
m2, nm2, rm2 = S.load_village("swarm-village")
room = S.busiest_room(m2)
agent_msgs = [m for m in m2 if not m["_sp"].startswith("user:")]
life = (max(m["_t"] for m in agent_msgs) - min(m["_t"] for m in agent_msgs)) / 86400
sp2, l2, h2 = S.cut_window(m2, room, days=life + 1)
S.symbolise(sp2, k=K, seed=0)
ag2 = S.select_agents(sp2, min_msgs=50, top_k=TOP_K)
sv = {"agents": len(ag2), "window_msgs": len(sp2)}
for mode in ("pairwise", "conditional"):
    e, n = certify(sp2, ag2, mode)
    sv[mode] = len(e)
    sv["n_ticks"] = n
    log(f"swarm-village {mode:12s}: {len(e)} edges")
out["swarm_village"] = sv
json.dump(out, open("facts_conditional_extra.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_conditional_extra.json")
