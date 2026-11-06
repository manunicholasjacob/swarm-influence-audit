"""Is the test actually well powered where we claim structure?

The paper reports 18 certified edges in open-chat and 2 in main-village, and measures power only on
main-village, where it is poor. That leaves a gap: the open-chat result is only meaningful if the test
has power there. Same spike-in protocol, same repaired surrogate, on open-chat.
"""
import json, time, collections
import numpy as np
import swarmlib as S

VIL = "open-chat-village"
K, N, TOP_K, SEEDS = 8, 200, 15, 4
COUPLINGS = [0.0, 0.1, 0.2, 0.4, 0.8]
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village(VIL)
room = S.busiest_room(msgs)
span, lo, hi = S.cut_window(msgs, room, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
stream = [(m["_sp"], m["_topic"]) for m in sub]
alphabet = [s for _, s in stream]
counts = collections.Counter(s for s, _ in stream)
n_synth = int(np.median(list(counts.values())))
leader = counts.most_common(1)[0][0]
lead_pos = [i for i, (sp, _) in enumerate(stream) if sp == leader]
log(f"{len(stream)} ticks, {len(agents)} agents, leader {names.get(leader,leader)} "
    f"({counts[leader]}), synth volume {n_synth}")

rows = []
for c in COUPLINGS:
    hits = 0
    for seed in range(SEEDS):
        rng = np.random.default_rng(909*seed + int(c*1000))
        n_resp = int(round(c*n_synth))
        ins = collections.defaultdict(list)
        if n_resp and lead_pos:
            for p in rng.choice(lead_pos, size=min(n_resp, len(lead_pos)), replace=False):
                ins[int(p)].append(stream[int(p)][1])
        rest = n_synth - sum(len(v) for v in ins.values())
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
    rows.append({"coupling": c, "detected": hits, "of": SEEDS, "rate": hits/SEEDS})
    log(f"c={c}: detected {hits}/{SEEDS}")
    json.dump({"village": VIL, "leader": names.get(leader, leader), "leader_msgs": counts[leader],
               "n_synth": n_synth, "ticks": len(stream), "seeds": SEEDS, "rows": rows},
              open("facts_power_openchat.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_power_openchat.json")
