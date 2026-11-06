"""Does the structure in the one well-powered channel actually replicate?

main-village has too little detectable signal under the valid surrogate for a replication test to mean
anything. open-chat-village has 18 certified edges, so it is the only channel where asking "does this
hold up" has power. Test: the adjacent 14-day window (shared topic space), the two halves of the
primary window, and alphabet size. All under the valid surrogate.
"""
import json, time, collections
import numpy as np
import swarmlib as S

VIL = "open-chat-village"
K, N, TOP_K = 8, 200, 15
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village(VIL)
room = S.busiest_room(msgs)
nm = lambda a: names.get(a, a)
cur, lo, hi = S.cut_window(msgs, room, days=14)
prev, plo, phi = S.cut_window(msgs, room, days=14, offset_days=14)
log(f"cur {len(cur)} msgs, prev {len(prev)} msgs")

out = {"village": VIL, "room": rooms.get(room, room[:8]),
       "cur_msgs": len(cur), "prev_msgs": len(prev)}

# ---- replication across adjacent windows, one shared topic space ----
cur_ok = set(S.select_agents(cur, 50, None)); prev_ok = set(S.select_agents(prev, 50, None))
common = S.select_agents(cur + prev, 50, None, restrict=cur_ok & prev_ok)[:TOP_K]
union = [m["content"] for m in cur] + [m["content"] for m in prev]
S.symbolise(cur, k=K, seed=0, fit_corpus=union)
S.symbolise(prev, k=K, seed=0, fit_corpus=union)
_, ec, nc = S.run_window(cur, common, key="_topic", n_shifts=N, null="permute")
_, ep, np_ = S.run_window(prev, common, key="_topic", n_shifts=N, null="permute")
_, ech, _ = S.run_window(cur, common, key="_hash", n_shifts=N, null="permute")
out["replication"] = {"common_agents": len(common), "cur_edges": len(ec), "prev_edges": len(ep),
                      "cur_hash_edges": len(ech), "shared": len(ec & ep),
                      "jaccard": round(S.jaccard(ec, ep), 4),
                      "shared_list": [[nm(i), nm(j)] for (i, j) in sorted(ec & ep)][:25]}
log(f"replication: cur {len(ec)} prev {len(ep)} shared {len(ec&ep)} J={out['replication']['jaccard']} "
    f"(hash {len(ech)})")
json.dump(out, open("facts_openchat.json", "w", encoding="utf-8"), indent=2)

# ---- split-half ----
cs = sorted(cur, key=lambda m: (m["_t"], m["id"])); mid = len(cs)//2
h1, h2 = cs[:mid], cs[mid:]
S.symbolise(cur, k=K, seed=0, fit_corpus=[m["content"] for m in cur])
ok1 = set(S.select_agents(h1, 25, None)); ok2 = set(S.select_agents(h2, 25, None))
ch = S.select_agents(cur, 50, None, restrict=ok1 & ok2)[:TOP_K]
_, e1, n1 = S.run_window(h1, ch, key="_topic", n_shifts=N, null="permute")
_, e2, n2 = S.run_window(h2, ch, key="_topic", n_shifts=N, null="permute")
out["split_half"] = {"agents": len(ch), "edges_h1": len(e1), "edges_h2": len(e2),
                     "shared": len(e1 & e2), "jaccard": round(S.jaccard(e1, e2), 4)}
log(f"split-half: h1 {len(e1)} h2 {len(e2)} shared {len(e1&e2)} J={out['split_half']['jaccard']}")
json.dump(out, open("facts_openchat.json", "w", encoding="utf-8"), indent=2)

# ---- alphabet size ----
agents = S.select_agents(cur, 50, TOP_K)
base = None; ks = []
for k in (4, 8, 16):
    S.symbolise(cur, k=k, seed=0)
    ag = S.select_agents(cur, 50, TOP_K)
    _, e, _ = S.run_window(cur, ag, key="_topic", n_shifts=N, null="permute")
    if k == 8:
        base = e
    ks.append({"k": k, "edges": len(e)})
    log(f"k={k}: {len(e)} edges")
for row in ks:
    row["jaccard_vs_k8"] = None
S.symbolise(cur, k=8, seed=0)
for row, k in zip(ks, (4, 8, 16)):
    if base is not None and k != 8:
        S.symbolise(cur, k=k, seed=0)
        ag = S.select_agents(cur, 50, TOP_K)
        _, e, _ = S.run_window(cur, ag, key="_topic", n_shifts=N, null="permute")
        row["jaccard_vs_k8"] = round(S.jaccard(e, base), 4)
    elif k == 8:
        row["jaccard_vs_k8"] = 1.0
out["k_sweep"] = ks
json.dump(out, open("facts_openchat.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_openchat.json")
