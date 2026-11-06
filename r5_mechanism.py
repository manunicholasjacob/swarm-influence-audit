"""What exactly makes the circular-shift surrogate fail on real logs?

The benchmark gave an unwelcome surprise: synthetic channels with one speaker per tick, even strongly
non-stationary ones, do NOT reproduce the 0.90 family-wise error rate measured on real data. So
neither mutual exclusivity alone nor non-stationary activity explains it, and the report's stated
mechanism is not yet earned.

This isolates the cause on the real data by destroying one structure at a time. Every condition has
NO directed topical influence by construction, so a calibrated procedure should fire about 5% of the
time in all of them.

  A  real speaker order, real symbols shuffled        the condition already measured (expect ~0.90)
  B  real speaker order, symbols drawn i.i.d. uniform does the symbol distribution matter?
  C  speaker order shuffled, real symbols shuffled    does TURN-TAKING structure matter?
  D  speaker order shuffled, i.i.d. uniform symbols   both destroyed, the floor
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
alpha = sorted(set(symbols))
log(f"{len(sub)} ticks, {len(agents)} agents, {len(alpha)} symbols")

# how structured is the real speaker sequence? repeat rate and dyadic return rate
rep = np.mean([speakers[i] == speakers[i-1] for i in range(1, len(speakers))])
ret = np.mean([speakers[i] == speakers[i-2] for i in range(2, len(speakers))])
log(f"real speaker sequence: immediate repeat {rep:.3f}, return-after-one {ret:.3f}")

CONDITIONS = {
    "A_real_order_real_symbols": (False, "real"),
    "B_real_order_iid_symbols": (False, "iid"),
    "C_shuffled_order_real_symbols": (True, "real"),
    "D_shuffled_order_iid_symbols": (True, "iid"),
}
out = {"reps": REPS, "n_surrogates": N, "k": K, "n_ticks": len(sub),
       "speaker_repeat_rate": round(float(rep), 4),
       "speaker_return_after_one": round(float(ret), 4), "conditions": {}}

for name, (shuffle_speakers, symmode) in CONDITIONS.items():
    rec = {}
    for null in ("shift", "permute"):
        fired, counts = 0, []
        for rep_i in range(REPS):
            rng = np.random.default_rng(31000 + rep_i)
            sp = list(speakers)
            if shuffle_speakers:
                rng.shuffle(sp)
            if symmode == "real":
                sy = list(symbols); rng.shuffle(sy)
            else:
                sy = [alpha[i] for i in rng.integers(0, len(alpha), size=len(sub))]
            series, _ = S.series_from_stream(list(zip(sp, sy)), agents)
            t = S.directed(series, n_shifts=N, seed=rep_i, null=null)
            e = len(S.sig_edges(t))
            fired += e > 0; counts.append(e)
        rec[null] = {"fwer": round(fired / REPS, 3), "mean_edges": round(float(np.mean(counts)), 2)}
        log(f"{name:32s} {null:8s}: FWER {fired}/{REPS} mean edges {np.mean(counts):.2f}")
    out["conditions"][name] = rec
    json.dump(out, open("facts_mechanism.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_mechanism.json")
