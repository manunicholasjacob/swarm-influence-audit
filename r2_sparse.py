"""Diagnostic: does the circular-shift + max-T procedure misbehave for SPARSE speakers?

The spike-in control raised a certified edge touching the planted agent in nearly every run even at
coupling 0, which should not happen under family-wise control. Hypothesis: an agent that is silent in
almost every tick has a near-degenerate shift-null TE distribution, so a tiny numerator is divided by
a tiny standard deviation and the z score explodes.

Plant an agent with NO coupling at all (symbols drawn from the channel's marginal) at a range of
message volumes, and measure how often it is certified as driving or being driven by anything.
"""
import json, time, collections
import numpy as np
import swarmlib as S
import fastte

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N_SHIFTS, SEEDS = 8, 200, 8
VOLUMES = [50, 100, 263, 600, 1500]
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=15)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
stream = [(m["_sp"], m["_topic"]) for m in sub]
alphabet = [s for _, s in stream]
counts = collections.Counter(s for s, _ in stream)
log(f"stream {len(stream)}; real agent volumes {sorted(counts.values())}")

rows = []
for vol in VOLUMES:
    any_edge, as_src, as_dst, zmax = 0, 0, 0, []
    for seed in range(SEEDS):
        rng = np.random.default_rng(777 * seed + vol)
        pos = rng.integers(0, len(stream), size=vol)
        ins = collections.defaultdict(list)
        for p in pos:
            ins[int(p)].append(alphabet[int(rng.integers(0, len(alphabet)))])
        st = []
        for i, ev in enumerate(stream):
            st.append(ev)
            for sym in ins.get(i, ()):
                st.append(("NULLAGENT", sym))
        series, n = S.series_from_stream(st, agents + ["NULLAGENT"])
        tests = S.directed(series, n_shifts=N_SHIFTS, seed=seed)
        edges = S.sig_edges(tests)
        e_null = [(i, j) for (i, j) in edges if "NULLAGENT" in (i, j)]
        any_edge += bool(e_null)
        as_src += sum(1 for i, j in e_null if i == "NULLAGENT")
        as_dst += sum(1 for i, j in e_null if j == "NULLAGENT")
        zmax.append(max(tests[(i, j)]["z"] for (i, j) in tests if "NULLAGENT" in (i, j)))
    rows.append({"volume": vol, "share_of_ticks": round(vol / (len(stream) + vol), 4),
                 "runs_with_any_null_edge": any_edge, "of": SEEDS,
                 "false_edge_rate": round(any_edge / SEEDS, 3),
                 "as_source": as_src, "as_target": as_dst,
                 "mean_max_z": round(float(np.mean(zmax)), 2)})
    log(f"vol={vol:5d} ({rows[-1]['share_of_ticks']:.1%} of ticks): any false edge in "
        f"{any_edge}/{SEEDS} runs (src {as_src}, dst {as_dst}), mean max z {rows[-1]['mean_max_z']}")

json.dump({"n_shifts": N_SHIFTS, "seeds": SEEDS, "k": K, "stream_ticks": len(stream),
           "real_agent_volumes": sorted(counts.values()), "rows": rows},
          open("facts_sparse.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_sparse.json")
