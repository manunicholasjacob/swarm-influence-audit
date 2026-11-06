"""Pin down the repaired surrogate's error rate.

The paper reports 0.10 with a 95% interval of 0.03 to 0.26 on 30 replicates, which covers the nominal
0.05 but is too wide to say much. This runs many more replicates of exactly the reported
configuration and writes incrementally, so whatever finishes is usable.
"""
import json, time
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, TOP_K, REPS = 8, 200, 15, 300
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p = k/n; d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (round(max(0.0, c-h), 4), round(min(1.0, c+h), 4))

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
speakers = [m["_sp"] for m in sub]; symbols = [m["_topic"] for m in sub]
log(f"{len(sub)} ticks, {len(agents)} agents, target {REPS} replicates")

counts = []
for rep in range(REPS):
    rng = np.random.default_rng(500000 + rep)
    sh = list(symbols); rng.shuffle(sh)
    series, _ = S.series_from_stream(list(zip(speakers, sh)), agents)
    t = S.directed(series, n_shifts=N, seed=rep, null="permute")
    counts.append(len(S.sig_edges(t)))
    if (rep + 1) % 10 == 0:
        k = sum(c > 0 for c in counts)
        json.dump({"null": "permute", "reps": len(counts), "n_with_edge": k,
                   "fwer": round(k/len(counts), 4), "wilson95": wilson(k, len(counts)),
                   "mean_edges": round(float(np.mean(counts)), 3),
                   "n_surrogates": N, "k": K, "agents": len(agents)},
                  open("facts_calib_big.json", "w", encoding="utf-8"), indent=2)
        log(f"{len(counts)} reps: {k} with an edge, FWER {k/len(counts):.3f}, "
            f"Wilson {wilson(k, len(counts))}")
log("done")
