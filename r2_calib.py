"""Family-wise error rate of each null under a TRUE null, with real speaking patterns.

The planted-agent test could be dismissed as an artificial insertion. This is the cleaner check:
keep the real sequence of speakers exactly as it is, and destroy only the symbols by permuting them
globally. Now no directed topical influence exists by construction, so a correctly calibrated
procedure should certify an edge in about 5% of replicates and no more.
"""
import json, time, collections
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, TOP_K, REPS = 8, 200, 15, 10
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
speakers = [m["_sp"] for m in sub]
symbols = [m["_topic"] for m in sub]
log(f"{len(sub)} ticks, {len(agents)} agents")

res = {"reps": REPS, "n_perm": N, "k": K, "n_ticks": len(sub), "rows": {}}
for null in ("shift", "permute"):
    edge_counts = []
    for rep in range(REPS):
        rng = np.random.default_rng(4242 + rep)
        shuffled = list(symbols)
        rng.shuffle(shuffled)                      # speakers untouched, symbols destroyed
        series, n = S.series_from_stream(list(zip(speakers, shuffled)), agents)
        t = S.directed(series, n_shifts=N, seed=rep, null=null)
        edge_counts.append(len(S.sig_edges(t)))
    fwer = float(np.mean([c > 0 for c in edge_counts]))
    res["rows"][null] = {"edges_per_rep": edge_counts, "mean_edges": round(float(np.mean(edge_counts)), 2),
                         "familywise_error_rate": round(fwer, 3)}
    log(f"{null}: edges per replicate {edge_counts} | mean {np.mean(edge_counts):.2f} | FWER {fwer:.2f}")
    json.dump(res, open("facts_calib.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_calib.json")
