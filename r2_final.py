"""The gating numbers, in priority order so partial output is still usable.

B  re-certify the main-village headline under the invalid shift null and the repaired permutation null
C  replication across adjacent windows under the repaired null
A  complete the false-positive comparison at the median real agent's volume
P  an honest power curve under the repaired null
"""
import json, time, collections
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, TOP_K = 8, 200, 15
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)
out = {}
def save():
    json.dump(out, open("facts_final.json", "w", encoding="utf-8"), indent=2)

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
nm = lambda a: names.get(a, a)
log(f"window {len(span)} msgs, {len(agents)} agents")

# ---------------- B: headline under both nulls ----------------
B = {}
sets = {}
for null in ("shift", "permute"):
    res = {}
    for key, lab in (("_topic", "topic"), ("_hash", "hash")):
        t, e, n = S.run_window(span, agents, key=key, n_shifts=N, null=null)
        res[lab] = {"n_edges": len(e),
                    "edges": [[nm(i), nm(j), round(t[(i, j)]["p"], 4), round(t[(i, j)]["te"], 5)]
                              for (i, j) in sorted(e, key=lambda x: t[x]["p"])]}
        sets[(null, lab)] = {(nm(i), nm(j)) for (i, j) in e}
        log(f"B {null}/{lab}: {len(e)} edges")
    B[null] = res
B["survive_both_topic"] = sorted(map(list, sets[("shift", "topic")] & sets[("permute", "topic")]))
B["n_survive_both_topic"] = len(sets[("shift", "topic")] & sets[("permute", "topic")])
out["headline_by_null"] = B
save()
log(f"B: shift {len(sets[('shift','topic')])} -> permute {len(sets[('permute','topic')])}; "
    f"survive both {B['n_survive_both_topic']}")

# ---------------- C: replication under the repaired null ----------------
prev, plo, phi = S.cut_window(msgs, GENERAL, days=14, offset_days=14)
cur_ok = set(S.select_agents(span, 50, None)); prev_ok = set(S.select_agents(prev, 50, None))
common = S.select_agents(span + prev, 50, None, restrict=cur_ok & prev_ok)[:TOP_K]
union = [m["content"] for m in span] + [m["content"] for m in prev]
S.symbolise(span, k=K, seed=0, fit_corpus=union)
S.symbolise(prev, k=K, seed=0, fit_corpus=union)
C = {"common_agents": len(common)}
for null in ("shift", "permute"):
    _, ec, _ = S.run_window(span, common, key="_topic", n_shifts=N, null=null)
    _, ep, _ = S.run_window(prev, common, key="_topic", n_shifts=N, null=null)
    C[null] = {"cur_edges": len(ec), "prev_edges": len(ep), "shared": len(ec & ep),
               "jaccard": round(S.jaccard(ec, ep), 4),
               "shared_list": [[nm(i), nm(j)] for (i, j) in sorted(ec & ep)]}
    log(f"C {null}: cur {len(ec)} prev {len(ep)} shared {len(ec&ep)} J={C[null]['jaccard']}")
out["replication_by_null"] = C
save()

# ---------------- A: false positives at the median real volume ----------------
S.symbolise(span, k=K, seed=0)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
stream = [(m["_sp"], m["_topic"]) for m in sub]
alphabet = [s for _, s in stream]
SEEDS = 5
A = {"seeds": SEEDS, "rows": []}
for vol in (263, 1500):
    rec = {"volume": vol}
    for null in ("shift", "permute"):
        any_edge = 0; zs = []
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
            any_edge += bool(e)
            zs.append(max(t[(i, j)]["z"] for (i, j) in t if "NULLAGENT" in (i, j)))
        rec[null] = {"runs_with_false_edge": any_edge, "of": SEEDS,
                     "rate": round(any_edge/SEEDS, 3), "mean_max_z": round(float(np.mean(zs)), 2)}
        log(f"A vol={vol} {null}: false edge {any_edge}/{SEEDS}, mean max z {rec[null]['mean_max_z']}")
    A["rows"].append(rec)
    out["false_positive_by_null"] = A; save()

# ---------------- P: honest power curve under the repaired null ----------------
counts = collections.Counter(s for s, _ in stream)
n_synth = int(np.median(list(counts.values())))
leader = counts.most_common(1)[0][0]
P = {"leader": nm(leader), "leader_msgs": counts[leader], "n_synth": n_synth, "seeds": 4, "rows": []}
for c in (0.0, 0.1, 0.2, 0.4, 0.8):
    hits = 0
    for seed in range(4):
        rng = np.random.default_rng(31*seed + int(c*1000))
        n_resp = int(round(c*n_synth))
        lead_pos = [i for i, (sp, _) in enumerate(stream) if sp == leader]
        ins = collections.defaultdict(list)
        for p in rng.choice(lead_pos, size=min(n_resp, len(lead_pos)), replace=False):
            ins[int(p)].append(stream[int(p)][1])
        for p in rng.integers(0, len(stream), size=max(0, n_synth - sum(len(v) for v in ins.values()))):
            ins[int(p)].append(alphabet[int(rng.integers(0, len(alphabet)))])
        st = []
        for i, ev in enumerate(stream):
            st.append(ev)
            for sym in ins.get(i, ()):
                st.append(("SYNTH", sym))
        series, n = S.series_from_stream(st, agents + ["SYNTH"])
        t = S.directed(series, n_shifts=N, seed=seed, null="permute")
        hits += (leader, "SYNTH") in S.sig_edges(t)
    P["rows"].append({"coupling": c, "detected": hits, "of": 4, "rate": hits/4})
    log(f"P permute c={c}: detected {hits}/4")
    out["power_permute"] = P; save()
log("wrote facts_final.json")
