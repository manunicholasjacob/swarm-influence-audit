"""Power under the valid surrogate as a function of the FOLLOWER's volume.

The first power curve planted a follower at the median agent's volume and found that even an
80%-coupled follower is caught only once in four runs. That is a statement about median-volume
agents, not about the method. Here the coupling is held at a strong value and the follower's volume
is swept, which is what an overseer needs: how much must an agent say before its copying is visible.
"""
import json, time, collections
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, TOP_K, SEEDS = 8, 200, 15, 4
VOLUMES = [263, 800, 2000, 4000]
COUPLING = 0.8
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
stream = [(m["_sp"], m["_topic"]) for m in sub]
alphabet = [s for _, s in stream]
counts = collections.Counter(s for s, _ in stream)
leader = counts.most_common(1)[0][0]
lead_pos = [i for i, (sp, _) in enumerate(stream) if sp == leader]
log(f"leader {names.get(leader,leader)} ({counts[leader]} msgs), stream {len(stream)}")

rows = []
for vol in VOLUMES:
    hits = 0
    for seed in range(SEEDS):
        rng = np.random.default_rng(555*seed + vol)
        n_resp = int(round(COUPLING*vol))
        ins = collections.defaultdict(list)
        pick = rng.choice(lead_pos, size=min(n_resp, len(lead_pos)), replace=(n_resp > len(lead_pos)))
        for p in pick:
            ins[int(p)].append(stream[int(p)][1])
        rest = vol - sum(len(v) for v in ins.values())
        for p in rng.integers(0, len(stream), size=max(0, rest)):
            ins[int(p)].append(alphabet[int(rng.integers(0, len(alphabet)))])
        st = []
        for i, ev in enumerate(stream):
            st.append(ev)
            for sym in ins.get(i, ()):
                st.append(("SYNTH", sym))
        series, n = S.series_from_stream(st, agents + ["SYNTH"])
        t = S.directed(series, n_shifts=N, seed=seed, null="permute")
        hits += (leader, "SYNTH") in S.sig_edges(t)
    rows.append({"synth_volume": vol, "coupling": COUPLING, "detected": hits, "of": SEEDS,
                 "rate": hits/SEEDS, "share_of_leader_msgs": round(min(1.0, COUPLING*vol/counts[leader]), 3)})
    log(f"vol={vol}: detected {hits}/{SEEDS}")
    json.dump({"leader": names.get(leader, leader), "leader_msgs": counts[leader],
               "coupling": COUPLING, "seeds": SEEDS, "n_perm": N, "rows": rows},
              open("facts_power2.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_power2.json")
