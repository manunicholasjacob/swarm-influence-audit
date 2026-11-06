"""Does the influence graph survive the choices we made?

(1) headline under the stated convention, (2) alphabet size k, (3) which corpus the topic model is
fit on, (4) replication in the adjacent 14-day window, (5) split-half inside the window.
Replication and split-half share ONE topic space fit on the union, so symbols mean the same thing
in both halves and only the influence estimate is being compared.
"""
import json, time, collections
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N_SHIFTS, TOP_K = 8, 200, 15
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float); rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    d = np.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra*rb).sum()/d) if d else 0.0

msgs, names, rooms = S.load_village("main-village")
cur, lo, hi = S.cut_window(msgs, GENERAL, days=14)
nm = lambda a: names.get(a, a)
out = {}

# ---------- 1. headline (convention: topic model fit on ALL agent messages in the window) ----------
S.symbolise(cur, k=K, seed=0)
agents = S.select_agents(cur, min_msgs=50, top_k=TOP_K)
res = {}
for key, lab in (("_topic", "topic"), ("_hash", "hash")):
    t, e, n = S.run_window(cur, agents, key=key, n_shifts=N_SHIFTS)
    sc, sig = S.leader_scores(t)
    net = collections.Counter()
    for (i, j), v in t.items():
        net[i] += v["te"]; net[j] -= v["te"]
    res[lab] = {"n_ticks": n, "n_edges": len(e),
                "edges": [[nm(i), nm(j), round(t[(i, j)]["p"], 4), round(t[(i, j)]["te"], 4)]
                          for (i, j) in sorted(e, key=lambda x: t[x]["p"])],
                "leader_scores": sorted(((nm(a), s) for a, s in sc.items()), key=lambda x: -x[1]),
                "net": {nm(a): round(net[a], 4) for a in agents}, "_edges": e, "_net": net}
    log(f"headline {lab}: {len(e)} edges (n={n})")
nt = np.array([res["topic"]["_net"][a] for a in agents])
nh = np.array([res["hash"]["_net"][a] for a in agents])
out["headline"] = {
    "window": {"start": time.strftime("%Y-%m-%d", time.gmtime(lo)),
               "end": time.strftime("%Y-%m-%d", time.gmtime(hi)),
               "n_msgs_window": len(cur), "n_agents_ge50": len(S.select_agents(cur, 50, None)),
               "n_te_agents": len(agents), "agent_labels": [nm(a) for a in agents]},
    "topic": {k: v for k, v in res["topic"].items() if not k.startswith("_")},
    "hash": {k: v for k, v in res["hash"].items() if not k.startswith("_")},
    "net_topic_vs_hash_spearman": round(spearman(nt, nh), 4),
}
base_edges = res["topic"]["_edges"]

# ---------- 2. alphabet size k ----------
ks = []
for k in (4, 8, 16, 32):
    S.symbolise(cur, k=k, seed=0)
    ag_k = S.select_agents(cur, min_msgs=50, top_k=TOP_K)
    _, et, _ = S.run_window(cur, ag_k, key="_topic", n_shifts=N_SHIFTS)
    _, eh, _ = S.run_window(cur, ag_k, key="_hash", n_shifts=N_SHIFTS)
    ks.append({"k": k, "edges_topic": len(et), "edges_hash": len(eh),
               "jaccard_vs_k8": round(S.jaccard(et, base_edges), 4),
               "recovered_of_k8": len(et & base_edges)})
    log(f"k={k}: topic {len(et)} hash {len(eh)} jaccard_vs_k8 {ks[-1]['jaccard_vs_k8']}")
out["k_sweep"] = ks

# ---------- 3. which corpus the topic model is fit on ----------
S.symbolise(cur, k=K, seed=0)
ge50 = set(S.select_agents(cur, min_msgs=50, top_k=None))
variants = {
    "all_window_msgs": [m["content"] for m in cur],
    "agents_ge50_msgs": [m["content"] for m in cur if m["_sp"] in ge50],
    "te_agents_msgs": [m["content"] for m in cur if m["_sp"] in set(agents)],
}
fits = []
for lab, corpus in variants.items():
    S.symbolise(cur, k=K, seed=0, fit_corpus=corpus)
    _, e, _ = S.run_window(cur, agents, key="_topic", n_shifts=N_SHIFTS)
    fits.append({"fit_corpus": lab, "n_fit_msgs": len(corpus), "edges_topic": len(e),
                 "jaccard_vs_all": round(S.jaccard(e, base_edges), 4)})
    log(f"fit on {lab} ({len(corpus)} msgs): {len(e)} edges, J={fits[-1]['jaccard_vs_all']}")
out["fit_corpus_sensitivity"] = fits

# ---------- 4. replication in the adjacent window ----------
prev, plo, phi = S.cut_window(msgs, GENERAL, days=14, offset_days=14)
cur_ok = set(S.select_agents(cur, 50, None)); prev_ok = set(S.select_agents(prev, 50, None))
common = [a for a in S.select_agents(cur + prev, 50, None, restrict=cur_ok & prev_ok)][:TOP_K]
union_texts = [m["content"] for m in cur] + [m["content"] for m in prev]
S.symbolise(cur, k=K, seed=0, fit_corpus=union_texts)
S.symbolise(prev, k=K, seed=0, fit_corpus=union_texts)
tc, ec, nc = S.run_window(cur, common, key="_topic", n_shifts=N_SHIFTS)
tp, ep, np_ = S.run_window(prev, common, key="_topic", n_shifts=N_SHIFTS)
_, ech, _ = S.run_window(cur, common, key="_hash", n_shifts=N_SHIFTS)
_, eph, _ = S.run_window(prev, common, key="_hash", n_shifts=N_SHIFTS)
sc_c, _ = S.leader_scores(tc); sc_p, _ = S.leader_scores(tp)
rho = spearman(np.array([sc_c.get(a, 0) for a in common]), np.array([sc_p.get(a, 0) for a in common]))
out["replication"] = {
    "common_agents": len(common), "agent_labels": [nm(a) for a in common],
    "cur": {"start": time.strftime("%Y-%m-%d", time.gmtime(lo)), "n_ticks": nc,
            "edges_topic": len(ec), "edges_hash": len(ech)},
    "prev": {"start": time.strftime("%Y-%m-%d", time.gmtime(plo)), "n_ticks": np_,
             "edges_topic": len(ep), "edges_hash": len(eph)},
    "shared_edges": len(ec & ep), "jaccard": round(S.jaccard(ec, ep), 4),
    "leader_score_spearman": round(rho, 4),
    "shared_edge_list": [[nm(i), nm(j)] for (i, j) in sorted(ec & ep)],
    "cur_edge_list": [[nm(i), nm(j)] for (i, j) in sorted(ec)],
    "prev_edge_list": [[nm(i), nm(j)] for (i, j) in sorted(ep)],
}
log(f"replication: cur {len(ec)} prev {len(ep)} shared {len(ec&ep)} J={out['replication']['jaccard']} rho={rho:.3f}")

# ---------- 5. split-half inside the window ----------
cur_sorted = sorted(cur, key=lambda m: (m["_t"], m["id"]))
mid = len(cur_sorted)//2
h1, h2 = cur_sorted[:mid], cur_sorted[mid:]
S.symbolise(cur, k=K, seed=0, fit_corpus=[m["content"] for m in cur])
ok1 = set(S.select_agents(h1, 25, None)); ok2 = set(S.select_agents(h2, 25, None))
ch = [a for a in S.select_agents(cur, 50, None, restrict=ok1 & ok2)][:TOP_K]
_, e1, n1 = S.run_window(h1, ch, key="_topic", n_shifts=N_SHIFTS)
_, e2, n2 = S.run_window(h2, ch, key="_topic", n_shifts=N_SHIFTS)
out["split_half"] = {"agents": len(ch), "n1": n1, "n2": n2, "edges_h1": len(e1),
                     "edges_h2": len(e2), "shared": len(e1 & e2),
                     "jaccard": round(S.jaccard(e1, e2), 4)}
log(f"split-half: h1 {len(e1)} h2 {len(e2)} shared {len(e1&e2)} J={out['split_half']['jaccard']}")

json.dump(out, open("facts_robust.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_robust.json")
