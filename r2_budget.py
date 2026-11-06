"""Read budget, recomputed under the stated convention so it matches every other number.

An overseer reads a uniform random fraction p of the channel. Rebuild the turn order from the sample,
rerun the full certified test, and score recovery of the full-window edge set (recall / precision),
plus the Spearman correlation of the continuous net-influence ranking.
"""
import json, time, collections
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N_SHIFTS, TOP_K, REPEATS = 8, 200, 15, 8
FRACTIONS = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float); rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    d = np.sqrt((ra**2).sum()*(rb**2).sum())
    return float((ra*rb).sum()/d) if d else 0.0

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))

tests_full, full_edges, n_full = S.run_window(span, agents, key="_topic", n_shifts=N_SHIFTS)
net_full = collections.Counter()
for (i, j), v in tests_full.items():
    net_full[i] += v["te"]; net_full[j] -= v["te"]
fnet = np.array([net_full[a] for a in agents])
log(f"full window: {n_full} ticks, {len(full_edges)} certified edges")

rows = []
for p in FRACTIONS:
    rec, pre, rho = [], [], []
    reps = 1 if p >= 1.0 else REPEATS
    for r in range(reps):
        if p >= 1.0:
            smp = sub
        else:
            rg = np.random.default_rng(1000*r + int(p*100))
            smp = [m for m in sub if rg.random() < p]
        t, e, n = S.run_window(smp, agents, key="_topic", n_shifts=N_SHIFTS)
        tp = len(e & full_edges)
        rec.append(tp/len(full_edges) if full_edges else 0.0)
        pre.append(tp/len(e) if e else (1.0 if not full_edges else 0.0))
        net = collections.Counter()
        for (i, j), v in t.items():
            net[i] += v["te"]; net[j] -= v["te"]
        rho.append(spearman(fnet, np.array([net[a] for a in agents])))
    rows.append({"fraction": p, "recall_mean": round(float(np.mean(rec)), 4),
                 "recall_sd": round(float(np.std(rec)), 4),
                 "precision_mean": round(float(np.mean(pre)), 4),
                 "net_spearman_mean": round(float(np.mean(rho)), 4), "repeats": reps})
    log(f"p={p}: recall {np.mean(rec):.3f} prec {np.mean(pre):.3f} rho {np.mean(rho):.3f}")

json.dump({"k": K, "n_shifts": N_SHIFTS, "top_k": TOP_K, "repeats": REPEATS,
           "n_full_edges": len(full_edges), "n_ticks": n_full, "rows": rows},
          open("facts_budget.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_budget.json")
