"""Does the sparsity-preserving null fix the false-positive mode, and what survives under it?

A. Plant an UNCOUPLED agent at several volumes and compare false-edge rates: circular-shift null
   (preexisting) vs symbol-permutation null (weekend repair).
B. Re-certify the main-village headline under both nulls.
C. Re-run the adjacent-window replication under the repaired null.
"""
import json, time, collections
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, SEEDS, TOP_K = 8, 200, 6, 15
VOLUMES = [50, 100, 263, 600]
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
nm = lambda a: names.get(a, a)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
stream = [(m["_sp"], m["_topic"]) for m in sub]
alphabet = [s for _, s in stream]
out = {}

# ---------- A. false positives for an uncoupled planted agent ----------
rowsA = []
for vol in VOLUMES:
    rec = {"volume": vol}
    for null in ("shift", "permute"):
        any_edge, as_src = 0, 0
        for seed in range(SEEDS):
            rng = np.random.default_rng(777*seed + vol)
            ins = collections.defaultdict(list)
            for p in rng.integers(0, len(stream), size=vol):
                ins[int(p)].append(alphabet[int(rng.integers(0, len(alphabet)))])
            st = []
            for i, ev in enumerate(stream):
                st.append(ev)
                for sym in ins.get(i, ()):
                    st.append(("NULLAGENT", sym))
            series, n = S.series_from_stream(st, agents + ["NULLAGENT"])
            t = S.directed(series, n_shifts=N, seed=seed, null=null)
            e = [(i, j) for (i, j) in S.sig_edges(t) if "NULLAGENT" in (i, j)]
            any_edge += bool(e); as_src += sum(1 for i, j in e if i == "NULLAGENT")
        rec[null] = {"runs_with_false_edge": any_edge, "of": SEEDS,
                     "rate": round(any_edge/SEEDS, 3), "as_source": as_src}
        log(f"A vol={vol:4d} null={null:8s}: false edge in {any_edge}/{SEEDS} (src {as_src})")
    rowsA.append(rec)
out["false_positive"] = {"seeds": SEEDS, "n_perm": N, "rows": rowsA}

# ---------- B. headline under both nulls ----------
rowsB = {}
for null in ("shift", "permute"):
    res = {}
    for key, lab in (("_topic", "topic"), ("_hash", "hash")):
        t, e, n = S.run_window(span, agents, key=key, n_shifts=N, null=null)
        res[lab] = {"n_edges": len(e),
                    "edges": [[nm(i), nm(j), round(t[(i, j)]["p"], 4), round(t[(i, j)]["te"], 5)]
                              for (i, j) in sorted(e, key=lambda x: t[x]["p"])]}
        res[lab + "_set"] = {(nm(i), nm(j)) for (i, j) in e}
    rowsB[null] = res
    log(f"B null={null}: topic {res['topic']['n_edges']} hash {res['hash']['n_edges']}")
shift_t = rowsB["shift"]["topic_set"]; perm_t = rowsB["permute"]["topic_set"]
out["headline_by_null"] = {
    "shift": {k: v for k, v in rowsB["shift"].items() if not k.endswith("_set")},
    "permute": {k: v for k, v in rowsB["permute"].items() if not k.endswith("_set")},
    "shift_topic_edges": sorted(map(list, shift_t)),
    "permute_topic_edges": sorted(map(list, perm_t)),
    "survive_both": sorted(map(list, shift_t & perm_t)),
    "n_survive_both": len(shift_t & perm_t),
}
log(f"B: shift {len(shift_t)} topic edges, permute {len(perm_t)}, surviving both {len(shift_t & perm_t)}")

# ---------- C. replication under the repaired null ----------
prev, plo, phi = S.cut_window(msgs, GENERAL, days=14, offset_days=14)
cur_ok = set(S.select_agents(span, 50, None)); prev_ok = set(S.select_agents(prev, 50, None))
common = S.select_agents(span + prev, 50, None, restrict=cur_ok & prev_ok)[:TOP_K]
union = [m["content"] for m in span] + [m["content"] for m in prev]
S.symbolise(span, k=K, seed=0, fit_corpus=union)
S.symbolise(prev, k=K, seed=0, fit_corpus=union)
rep = {}
for null in ("shift", "permute"):
    _, ec, nc = S.run_window(span, common, key="_topic", n_shifts=N, null=null)
    _, ep, np_ = S.run_window(prev, common, key="_topic", n_shifts=N, null=null)
    rep[null] = {"cur_edges": len(ec), "prev_edges": len(ep), "shared": len(ec & ep),
                 "jaccard": round(S.jaccard(ec, ep), 4),
                 "shared_list": [[nm(i), nm(j)] for (i, j) in sorted(ec & ep)]}
    log(f"C null={null}: cur {len(ec)} prev {len(ep)} shared {len(ec&ep)} J={rep[null]['jaccard']}")
out["replication_by_null"] = {"common_agents": len(common), **rep}

json.dump(out, open("facts_repair.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_repair.json")
