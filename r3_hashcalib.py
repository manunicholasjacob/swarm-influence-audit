"""Is the surrogate failure about the turn-ordered grid, or about the topic alphabet?

The calibration measurement used topic symbols, whose marginal is skewed (one cluster holds a third of
the messages). If the circular-shift surrogate also fails on the near-uniform hash alphabet, the
failure belongs to the representation rather than to any property of the symbols, which is the more
general and more useful claim.
"""
import json, time
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

import collections
out = {"k": K, "n_surrogates": N, "reps": REPS, "n_ticks": len(sub), "alphabets": {}}
for key, lab in (("_topic", "topic"), ("_hash", "hash")):
    syms = [m[key] for m in sub]
    share = collections.Counter(syms).most_common(1)[0][1] / len(syms)
    rec = {"largest_symbol_share": round(share, 4)}
    for null in ("shift", "permute"):
        counts = []
        for rep in range(REPS):
            rng = np.random.default_rng(606 + rep)
            sh = list(syms); rng.shuffle(sh)
            series, _ = S.series_from_stream(list(zip(speakers, sh)), agents)
            t = S.directed(series, n_shifts=N, seed=rep, null=null)
            counts.append(len(S.sig_edges(t)))
        k = sum(c > 0 for c in counts)
        rec[null] = {"fwer": round(k/REPS, 3), "mean_edges": round(float(np.mean(counts)), 2),
                     "edges_per_rep": counts}
        log(f"{lab} alphabet (top symbol {share:.0%}) {null:8s}: FWER {k}/{REPS}, "
            f"mean edges {np.mean(counts):.2f}")
    out["alphabets"][lab] = rec
    json.dump(out, open("facts_hashcalib.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_hashcalib.json")
