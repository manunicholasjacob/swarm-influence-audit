"""More replicates for the permutation surrogate's family-wise error rate.

Ten replicates put the repaired surrogate at 1/10, which is consistent with the nominal 0.05 but has
a wide interval. This adds replicates for the permutation arm only (the shift arm is already decisive
at 9/10) and reports a Wilson interval.
"""
import json, time
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, TOP_K, REPS = 8, 200, 15, 30
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
speakers = [m["_sp"] for m in sub]; symbols = [m["_topic"] for m in sub]

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 1.0)
    p = k/n; d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return (round(max(0.0, c-h), 4), round(min(1.0, c+h), 4))

counts = []
for rep in range(REPS):
    rng = np.random.default_rng(99000 + rep)
    sh = list(symbols); rng.shuffle(sh)
    series, n = S.series_from_stream(list(zip(speakers, sh)), agents)
    t = S.directed(series, n_shifts=N, seed=rep, null="permute")
    counts.append(len(S.sig_edges(t)))
    if (rep+1) % 5 == 0:
        k = sum(c > 0 for c in counts)
        log(f"{rep+1} reps: {k} with an edge, FWER {k/len(counts):.3f}")
        json.dump({"reps": len(counts), "edges_per_rep": counts,
                   "n_with_edge": k, "fwer": round(k/len(counts), 4),
                   "wilson95": wilson(k, len(counts)), "null": "permute", "n_perm": N},
                  open("facts_calib2.json", "w", encoding="utf-8"), indent=2)
k = sum(c > 0 for c in counts)
log(f"FINAL permute FWER {k}/{REPS} = {k/REPS:.3f}, Wilson95 {wilson(k, REPS)}")
