"""Recompute the generality and human results under the VALID surrogate.

Everything reported in Sections 5.5 and 5.6 was first computed with the circular-shift surrogate,
which Section 5.2 shows is invalid on this grid. Reporting those numbers would contradict our own
result, so every cross-village and human-node count is recomputed with the symbol-permutation
surrogate. Shift values are kept alongside only to show the size of the correction.
"""
import json, time, collections
import numpy as np
import swarmlib as S

K, N, TOP_K, MIN_MSGS = 8, 200, 15, 50
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)
out = {}
def save(): json.dump(out, open("facts_recompute.json", "w", encoding="utf-8"), indent=2)

# ---------- villages ----------
rows = []
for v in ["main-village", "open-chat-village", "swarm-village"]:
    msgs, names, rooms = S.load_village(v)
    agent_msgs = [m for m in msgs if not m["_sp"].startswith("user:")]
    room = S.busiest_room(msgs)
    life = (max(m["_t"] for m in agent_msgs) - min(m["_t"] for m in agent_msgs))/86400
    days = 14 if life > 14 else life + 1
    span, lo, hi = S.cut_window(msgs, room, days=days)
    S.symbolise(span, k=K, seed=0)
    agents = S.select_agents(span, min_msgs=MIN_MSGS, top_k=TOP_K)
    if len(agents) < 4:
        continue
    rec = {"village": v, "room": rooms.get(room, room[:8]), "window_msgs": len(span),
           "te_agents": len(agents), "lifetime_days": round(life, 1),
           "total_agents": len({m["_sp"] for m in agent_msgs})}
    for null in ("shift", "permute"):
        _, et, n = S.run_window(span, agents, key="_topic", n_shifts=N, null=null)
        _, eh, _ = S.run_window(span, agents, key="_hash", n_shifts=N, null=null)
        rec[null] = {"edges_topic": len(et), "edges_hash": len(eh)}
        rec["n_ticks"] = n
    rows.append(rec)
    log(f"{v}: {len(span)} msgs | shift {rec['shift']} | permute {rec['permute']}")
    out["villages"] = rows; save()

# ---------- humans in open-chat ----------
VIL = "open-chat-village"
msgs, names, rooms = S.load_village(VIL)
room = S.busiest_room(msgs)
span, lo, hi = S.cut_window(msgs, room, days=14, include_humans=True)
humans = [m for m in span if m["_sp"].startswith("user:")]
amsgs = [m for m in span if not m["_sp"].startswith("user:")]
S.symbolise(span, k=K, seed=0)
agent_ids = S.select_agents(amsgs, min_msgs=50, top_k=12)
nm = lambda a: names.get(a, a)
hv = collections.Counter(m["_sp"] for m in humans)
alias = {u: f"visitor-{i+1}" for i, (u, _) in enumerate(hv.most_common(3))}
log(f"{VIL}: {len(amsgs)} agent + {len(humans)} human msgs, {len(hv)} visitors")

def run(relabel, extra, tag):
    stream = [dict(m, _sp=relabel(m["_sp"])) for m in sorted(span, key=lambda m: (m["_t"], m["id"]))
              if relabel(m["_sp"]) is not None]
    nodes = list(agent_ids) + extra
    rec = {"tag": tag}
    for null in ("shift", "permute"):
        t, e, n = S.run_window(stream, nodes, key="_topic", n_shifts=N, null=null)
        lab = lambda a: a if a in extra else nm(a)
        rec[null] = {"edges_topic": len(e), "n_ticks": n,
                     "human_drives_agent": [[lab(i), lab(j)] for (i, j) in e if i in extra],
                     "agent_drives_human": [[lab(i), lab(j)] for (i, j) in e if j in extra],
                     "agent_agent": sum(1 for (i, j) in e if i not in extra and j not in extra)}
    log(f"{tag}: shift {rec['shift']['edges_topic']} (h->a {len(rec['shift']['human_drives_agent'])}) "
        f"| permute {rec['permute']['edges_topic']} (h->a {len(rec['permute']['human_drives_agent'])})")
    return rec

H = {"window_agent_msgs": len(amsgs), "window_human_msgs": len(humans),
     "human_share": round(len(humans)/max(1, len(span)), 4), "distinct_visitors": len(hv)}
H["agents_only"] = {}
for null in ("shift", "permute"):
    _, ea, _ = S.run_window(amsgs, agent_ids, key="_topic", n_shifts=N, null=null)
    H["agents_only"][null] = len(ea)
log(f"agents-only: shift {H['agents_only']['shift']} permute {H['agents_only']['permute']}")
H["collapsed"] = run(lambda s: "HUMANS" if s.startswith("user:") else s, ["HUMANS"], "HUMANS collapsed")
H["individual"] = run(lambda s: alias.get(s) if s.startswith("user:") else s,
                      list(alias.values()), "individual visitors")
out["humans_open_chat"] = H
save()
log("wrote facts_recompute.json")
