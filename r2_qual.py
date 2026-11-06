"""Grounding and a trivial-baseline check.

(1) What are the topic clusters, in words? Reporting top terms keeps the abstraction honest without
    reproducing agent message text.
(2) Does transfer entropy earn its complexity? Compare it with a trivial detector: the copy rate,
    P(j repeats the previous message's topic | that message was i's), minus j's base rate. If the
    trivial statistic ranks pairs the same way, the information-theoretic machinery adds nothing.
"""
import json, time, collections
import numpy as np
import swarmlib as S
import fastte

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N_SHIFTS, TOP_K = 8, 200, 15
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
topic = S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
nm = lambda a: names.get(a, a)

# ---- 1. what the clusters are ----
terms = np.array(topic._vec.get_feature_names_out())
clusters = []
for c in range(K):
    centre = topic._km.cluster_centers_[c]
    top = terms[np.argsort(-centre)[:10]]
    n = sum(1 for m in span if m["_topic"] == f"t{c}")
    clusters.append({"symbol": f"t{c}", "messages": n, "share": round(n/len(span), 4),
                     "top_terms": list(top)})
    log(f"t{c}: {n:5d} msgs | " + ", ".join(top[:8]))

# which agents own which topic
by_agent = collections.defaultdict(collections.Counter)
for m in span:
    if m["_sp"] in set(agents):
        by_agent[m["_sp"]][m["_topic"]] += 1
agent_topic = {nm(a): {"n": sum(c.values()),
                       "modal_topic": c.most_common(1)[0][0],
                       "modal_share": round(c.most_common(1)[0][1]/sum(c.values()), 3)}
               for a, c in by_agent.items()}

# ---- 2. trivial baseline vs transfer entropy ----
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
stream = [(m["_sp"], m["_topic"]) for m in sub]
base_rate = collections.Counter(s for _, s in stream)
tot = sum(base_rate.values())

copy, opp = collections.Counter(), collections.Counter()
for t in range(1, len(stream)):
    i, si = stream[t-1]; j, sj = stream[t]
    if i == j:
        continue
    opp[(i, j)] += 1
    if sj == si:
        copy[(i, j)] += 1

series, n = S.turn_series(span, agents, "_topic")
coded, A = fastte.code_series(series)
tests = fastte.directed_tests_fast(coded, A, n_shifts=N_SHIFTS, seed=0)
sig = S.sig_edges(tests)

rows = []
for (i, j), v in tests.items():
    o = opp.get((i, j), 0)
    if o < 20:
        continue
    rate = copy.get((i, j), 0) / o
    expected = base_rate[max(base_rate, key=base_rate.get)] and 0  # placeholder, computed below
    # j's own base rate of emitting whatever symbol: expected copy rate if independent
    exp = sum((base_rate[s]/tot) * (sum(1 for a, ss in stream if a == j and ss == s) /
              max(1, sum(1 for a, _ in stream if a == j))) for s in base_rate)
    rows.append({"src": nm(i), "dst": nm(j), "opportunities": o,
                 "copy_rate": round(rate, 4), "expected_copy_rate": round(exp, 4),
                 "excess": round(rate - exp, 4), "te": round(v["te"], 5),
                 "p": round(v["p"], 4), "significant": (i, j) in sig})

te_vals = np.array([r["te"] for r in rows]); ex_vals = np.array([r["excess"] for r in rows])
def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float); rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    d = np.sqrt((ra**2).sum()*(rb**2).sum())
    return float((ra*rb).sum()/d) if d else 0.0
rho = spearman(te_vals, ex_vals)

# would the trivial statistic pick the same edges? rank pairs by excess copy rate, take as many as TE certified
n_sig = sum(1 for r in rows if r["significant"])
top_by_excess = {(r["src"], r["dst"]) for r in sorted(rows, key=lambda r: -r["excess"])[:n_sig]}
sig_set = {(r["src"], r["dst"]) for r in rows if r["significant"]}
overlap = len(top_by_excess & sig_set)
log(f"TE vs excess-copy-rate: spearman {rho:.3f}; top-{n_sig} by copy rate shares "
    f"{overlap}/{n_sig} with the certified edges")

json.dump({"k": K, "clusters": clusters, "agent_topic": agent_topic,
           "baseline": {"pairs_compared": len(rows), "spearman_te_vs_excess_copy": round(rho, 4),
                        "n_significant": n_sig, "top_by_excess_overlap": overlap,
                        "rows": sorted(rows, key=lambda r: -r["te"])[:25]}},
          open("facts_qual.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_qual.json")
