"""Clock-window baseline under the stated convention, plus the reply-latency distribution that
explains it. Shows there is no clock-window width that is both dense enough to estimate and short
enough to put a message and its reply in different windows."""
import json, time
import numpy as np
import swarmlib as S
import swarm_te

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N_SHIFTS, TOP_K = 8, 200, 15
WIDTHS_MIN = [0.5, 1, 2, 5, 15, 60]
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))

gaps = np.array([sub[i]["_t"] - sub[i-1]["_t"] for i in range(1, len(sub))
                 if sub[i]["_sp"] != sub[i-1]["_sp"] and sub[i]["_t"] >= sub[i-1]["_t"]])
lat = {f"p{q}": round(float(np.percentile(gaps, q)), 1) for q in (25, 50, 75, 90, 95)}
log(f"reply gap (s): {lat}")

rows = []
for w_min in WIDTHS_MIN:
    w = w_min * 60.0
    out = {}
    for key, lab in (("_topic", "topic"), ("_hash", "hash")):
        ev = [(m["_sp"], m["_t"], m[key]) for m in sub]
        series, nwin = swarm_te.windowed_series(ev, width=w, agents=agents)
        t = S.directed(series, n_shifts=N_SHIFTS, seed=0)
        out[lab] = len(S.sig_edges(t)); out["n_windows"] = nwin
    t00 = sub[0]["_t"]
    cells = {(m["_sp"], int((m["_t"] - t00)//w)) for m in sub}
    occ = len(cells) / (len(agents) * out["n_windows"])
    # share of consecutive different-speaker pairs that fall in the SAME window (invisible to lag-1)
    same = np.mean([int((sub[i]["_t"]-t00)//w) == int((sub[i-1]["_t"]-t00)//w)
                    for i in range(1, len(sub)) if sub[i]["_sp"] != sub[i-1]["_sp"]])
    rows.append({"w_min": w_min, "n_windows": out["n_windows"], "cell_occupancy": round(occ, 4),
                 "same_window_reply_share": round(float(same), 4),
                 "edges_topic": out["topic"], "edges_hash": out["hash"]})
    log(f"w={w_min}min nwin={out['n_windows']} occ={occ:.4f} sameWin={same:.3f} "
        f"topic={out['topic']} hash={out['hash']}")

json.dump({"k": K, "n_shifts": N_SHIFTS, "agents": len(agents), "reply_gap_s": lat,
           "rows": rows}, open("facts_clock.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_clock.json")
