"""Does the failure get worse as the swarm gets bigger?

The max-T family grows with the square of the agent count, and the shift surrogate's pathology is
per-pair, so a bigger swarm should be worse served by it. This measures the family-wise error rate of
both surrogates on structure-free data (real speaker order, symbols globally permuted) as a function
of how many agents are in the test. Directly relevant to anyone pointing these detectors at a swarm.
"""
import json, time
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, REPS = 8, 200, 6
SIZES = [5, 10, 15, 20, 25]
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
all_agents = S.select_agents(span, min_msgs=50, top_k=None)
log(f"{len(all_agents)} agents available")

out = {"k": K, "n_surrogates": N, "reps": REPS, "sizes": SIZES, "rows": []}
for n_ag in SIZES:
    if n_ag > len(all_agents):
        continue
    agents = all_agents[:n_ag]
    sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
    speakers = [m["_sp"] for m in sub]; symbols = [m["_topic"] for m in sub]
    rec = {"n_agents": n_ag, "n_pairs": n_ag*(n_ag-1), "n_ticks": len(sub)}
    for null in ("shift", "permute"):
        counts = []
        for rep in range(REPS):
            rng = np.random.default_rng(31337 + rep)
            sh = list(symbols); rng.shuffle(sh)
            series, _ = S.series_from_stream(list(zip(speakers, sh)), agents)
            t = S.directed(series, n_shifts=N, seed=rep, null=null)
            counts.append(len(S.sig_edges(t)))
        k = sum(c > 0 for c in counts)
        rec[null] = {"edges_per_rep": counts, "mean_edges": round(float(np.mean(counts)), 2),
                     "fwer": round(k/REPS, 4), "wilson95": wilson(k, REPS)}
        log(f"n={n_ag:2d} ({rec['n_pairs']} pairs, {len(sub)} ticks) {null:8s}: "
            f"FWER {k}/{REPS} mean edges {np.mean(counts):.2f}")
    out["rows"].append(rec)
    json.dump(out, open("facts_scale.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_scale.json")
