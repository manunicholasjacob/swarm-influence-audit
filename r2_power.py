"""Spike-in positive control: the ground truth the real logs do not have.

Plant a synthetic follower SYNTH into the real #general turn stream. A fraction c of SYNTH's messages
are responses placed immediately after a real leader L's message, copying L's topic symbol; the rest
land at random positions with a symbol drawn from the channel's empirical distribution. Then run the
real detector and ask whether the planted edge L->SYNTH is certified.

This gives (a) the detection threshold - how strongly must one agent track another to be seen at this
channel's sparsity - and (b) the false-positive rate at c=0 under a real data background.
"""
import json, collections, time
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N_SHIFTS, SEEDS = 8, 200, 5
COUPLINGS = [0.0, 0.05, 0.1, 0.2, 0.4, 0.8]
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=15)
sub = [m for m in span if m["_sp"] in set(agents)]
sub.sort(key=lambda m: (m["_t"], m["id"]))
stream = [(m["_sp"], m["_topic"]) for m in sub]
counts = collections.Counter(s for s, _ in stream)
n_synth = int(np.median(list(counts.values())))
alphabet = [s for _, s in stream]
log(f"stream {len(stream)} ticks, {len(agents)} agents, synth posts {n_synth} msgs")

# three leaders spanning the volume range, so the curve is not about one agent
ordered = [a for a, _ in counts.most_common()]
LEADERS = [ordered[0], ordered[len(ordered)//2], ordered[-1]]
log("leaders: " + ", ".join(f"{names.get(l,l)}({counts[l]})" for l in LEADERS))

def build(stream, leader, c, rng):
    """Insert SYNTH: c of its messages copy the leader's topic right after a leader message."""
    n_resp = int(round(c * n_synth))
    lead_pos = [i for i, (sp, _) in enumerate(stream) if sp == leader]
    inserts = collections.defaultdict(list)   # position -> [symbols to insert AFTER that index]
    if n_resp and lead_pos:
        for p in rng.choice(lead_pos, size=min(n_resp, len(lead_pos)), replace=False):
            inserts[int(p)].append(stream[int(p)][1])          # copy the leader's symbol
    n_rand = n_synth - sum(len(v) for v in inserts.values())
    for p in rng.integers(0, len(stream), size=max(0, n_rand)):
        inserts[int(p)].append(alphabet[int(rng.integers(0, len(alphabet)))])
    out = []
    for i, ev in enumerate(stream):
        out.append(ev)
        for sym in inserts.get(i, ()):
            out.append(("SYNTH", sym))
    return out

rows = []
for leader in LEADERS:
    for c in COUPLINGS:
        hits, fp_synth, tot_edges = 0, 0, 0
        for seed in range(SEEDS):
            rng = np.random.default_rng(10_000 * seed + int(c * 1000) + hash(leader) % 997)
            st = build(stream, leader, c, rng)
            series, n = S.series_from_stream(st, agents + ["SYNTH"])
            tests = S.directed(series, n_shifts=N_SHIFTS, seed=seed)
            edges = S.sig_edges(tests)
            hits += (leader, "SYNTH") in edges
            # any OTHER certified edge touching SYNTH is a false positive about the planted agent
            fp_synth += sum(1 for (i, j) in edges
                            if "SYNTH" in (i, j) and (i, j) != (leader, "SYNTH"))
            tot_edges += len(edges)
        rows.append({"leader": names.get(leader, leader), "leader_msgs": counts[leader],
                     "coupling": c, "detected": hits, "of": SEEDS,
                     "detect_rate": hits / SEEDS, "synth_false_edges": fp_synth,
                     "mean_total_edges": tot_edges / SEEDS})
        log(f"L={names.get(leader,leader)[:16]:16s} c={c:<5} detected {hits}/{SEEDS} "
            f"synthFP={fp_synth} meanEdges={tot_edges/SEEDS:.1f}")

out = {"n_synth_msgs": n_synth, "stream_ticks": len(stream), "n_agents": len(agents),
       "k_symbols": K, "n_shifts": N_SHIFTS, "seeds": SEEDS, "couplings": COUPLINGS,
       "leaders": [{"name": names.get(l, l), "msgs": counts[l]} for l in LEADERS], "rows": rows}
json.dump(out, open("facts_power.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_power.json")
