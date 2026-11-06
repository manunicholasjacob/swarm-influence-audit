"""Does the human->agent result replicate in a second village?

open-chat-village is a third human by volume. main-village #general is human-free NOW, but was not
always. Find the 14-day stretch of main-village #general with the most human traffic and run the same
test there: agents-only control, then humans added as one node and as individuals.
"""
import json, time, collections, datetime as dt
import numpy as np
import swarmlib as S

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N_SHIFTS, TOP_AGENTS, TOP_HUMANS = 8, 200, 12, 3
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)
F = dt.datetime.utcfromtimestamp

msgs, names, rooms = S.load_village("main-village")
gen = [m for m in msgs if m["room_id"] == GENERAL]
hum = [m for m in gen if m["_sp"].startswith("user:")]
log(f"#general: {len(gen)} msgs, {len(hum)} human")

# monthly human volume, then slide a 14d window to find the human-heaviest stretch
by_month = collections.Counter(F(m["_t"]).strftime("%Y-%m") for m in hum)
log("human msgs by month: " + ", ".join(f"{k}:{v}" for k, v in sorted(by_month.items()) if v > 100))

ht = np.array(sorted(m["_t"] for m in hum))
best_end, best_n = None, -1
for end in np.arange(ht.min() + 14*86400, ht.max() + 86400, 86400.0):
    n = int(((ht >= end - 14*86400) & (ht < end)).sum())
    if n > best_n:
        best_n, best_end = n, float(end)
lo, hi = best_end - 14*86400, best_end
span = [m for m in gen if lo <= m["_t"] < hi]
humans = [m for m in span if m["_sp"].startswith("user:")]
amsgs = [m for m in span if not m["_sp"].startswith("user:")]
log(f"human-heaviest 14d: {F(lo):%Y-%m-%d} -> {F(hi):%Y-%m-%d} | {len(amsgs)} agent + "
    f"{len(humans)} human msgs ({len(humans)/max(1,len(span)):.1%} human)")

S.symbolise(span, k=K, seed=0)
agent_ids = S.select_agents(amsgs, min_msgs=50, top_k=TOP_AGENTS)
nm = lambda a: names.get(a, a)
hv = collections.Counter(m["_sp"] for m in humans)
alias = {uid: f"visitor-{i+1}" for i, (uid, _) in enumerate(hv.most_common(TOP_HUMANS))}
log(f"{len(hv)} distinct visitors; busiest {[n for _, n in hv.most_common(5)]}")

def run(relabel, extra, tag):
    stream = [dict(m, _sp=relabel(m["_sp"])) for m in sorted(span, key=lambda m: (m["_t"], m["id"]))
              if relabel(m["_sp"]) is not None]
    nodes = list(agent_ids) + extra
    tt, et, n = S.run_window(stream, nodes, key="_topic", n_shifts=N_SHIFTS)
    _, eh, _ = S.run_window(stream, nodes, key="_hash", n_shifts=N_SHIFTS)
    lab = lambda a: a if a in extra else nm(a)
    ho = [[lab(i), lab(j), round(tt[(i, j)]["p"], 4)] for (i, j) in et if i in extra]
    hi_ = [[lab(i), lab(j), round(tt[(i, j)]["p"], 4)] for (i, j) in et if j in extra]
    log(f"{tag}: ticks {n} topic {len(et)} hash {len(eh)} | human->agent {len(ho)} | agent->human {len(hi_)}")
    return {"tag": tag, "n_ticks": n, "edges_topic": len(et), "edges_hash": len(eh),
            "human_drives_agent": ho, "agent_drives_human": hi_,
            "all_edges": [[lab(i), lab(j), round(tt[(i, j)]["p"], 4)]
                          for (i, j) in sorted(et, key=lambda x: tt[x]["p"])][:20]}

res = {}
_, ea, _ = S.run_window(amsgs, agent_ids, key="_topic", n_shifts=N_SHIFTS)
res["agents_only"] = {"edges_topic": len(ea), "nodes": len(agent_ids)}
log(f"agents-only control: {len(ea)} edges")
res["collapsed"] = run(lambda s: "HUMANS" if s.startswith("user:") else s, ["HUMANS"], "HUMANS collapsed")
res["individual"] = run(lambda s: alias.get(s) if s.startswith("user:") else s,
                        list(alias.values()), "top visitors individually")

json.dump({"village": "main-village", "room": "general", "k": K, "n_shifts": N_SHIFTS,
           "window": {"start": F(lo).strftime("%Y-%m-%d"), "end": F(hi).strftime("%Y-%m-%d")},
           "window_agent_msgs": len(amsgs), "window_human_msgs": len(humans),
           "human_share": round(len(humans)/max(1, len(span)), 4), "distinct_visitors": len(hv),
           "visitor_msg_counts": [n for _, n in hv.most_common(TOP_HUMANS)], "results": res},
          open("facts_humans_main.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_humans_main.json")
