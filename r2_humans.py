"""Do human visitors steer the swarm?

main-village #general is now effectively human-free, but open-chat-village is about a quarter human
messages, so that is where the question can be asked. Humans enter the graph two ways: collapsed into
one HUMANS node (do humans as a class drive the agents?) and as the few busiest individual visitors,
anonymised as visitor-1..n (can one person steer a swarm?).
"""
import json, time, collections
import numpy as np
import swarmlib as S

VILLAGE = "open-chat-village"
K, N_SHIFTS, TOP_AGENTS, TOP_HUMANS = 8, 200, 12, 3
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

msgs, names, rooms = S.load_village(VILLAGE)
room = S.busiest_room(msgs)
span, lo, hi = S.cut_window(msgs, room, days=14, include_humans=True)
humans = [m for m in span if m["_sp"].startswith("user:")]
agents_msgs = [m for m in span if not m["_sp"].startswith("user:")]
log(f"{VILLAGE}/{rooms.get(room,room[:8])} 14d: {len(agents_msgs)} agent + {len(humans)} human msgs "
    f"({len(humans)/max(1,len(span)):.1%} human)")

S.symbolise(span, k=K, seed=0)          # one topic space over agent and human text alike
agent_ids = S.select_agents(agents_msgs, min_msgs=50, top_k=TOP_AGENTS)
nm = lambda a: names.get(a, a)

hv = collections.Counter(m["_sp"] for m in humans)
log(f"{len(hv)} distinct visitors; busiest {[n for _, n in hv.most_common(5)]}")
alias = {uid: f"visitor-{i+1}" for i, (uid, _) in enumerate(hv.most_common(TOP_HUMANS))}

def run(relabel, extra_nodes, tag):
    stream = []
    for m in sorted(span, key=lambda m: (m["_t"], m["id"])):
        sp = relabel(m["_sp"])
        if sp is None:
            continue
        stream.append(dict(m, _sp=sp))
    nodes = list(agent_ids) + extra_nodes
    tt, et, n = S.run_window(stream, nodes, key="_topic", n_shifts=N_SHIFTS)
    th, eh, _ = S.run_window(stream, nodes, key="_hash", n_shifts=N_SHIFTS)
    lab = lambda a: a if a in extra_nodes else nm(a)
    hum_out = [[lab(i), lab(j), round(tt[(i, j)]["p"], 4)] for (i, j) in et if i in extra_nodes]
    hum_in = [[lab(i), lab(j), round(tt[(i, j)]["p"], 4)] for (i, j) in et if j in extra_nodes]
    log(f"{tag}: ticks {n} topic {len(et)} hash {len(eh)} | human->agent {len(hum_out)} "
        f"| agent->human {len(hum_in)}")
    return {"tag": tag, "n_ticks": n, "nodes": len(nodes), "edges_topic": len(et),
            "edges_hash": len(eh), "human_drives_agent": hum_out, "agent_drives_human": hum_in,
            "all_edges": [[lab(i), lab(j), round(tt[(i, j)]["p"], 4)]
                          for (i, j) in sorted(et, key=lambda x: tt[x]["p"])][:20]}

res = {}
res["collapsed"] = run(lambda s: "HUMANS" if s.startswith("user:") else s, ["HUMANS"], "HUMANS collapsed")
res["individual"] = run(lambda s: alias.get(s) if s.startswith("user:") else s,
                        list(alias.values()), "top visitors individually")

# agents-only control in the same village/window, for the edge-count baseline
agent_only, et_a, _ = S.run_window(agents_msgs, agent_ids, key="_topic", n_shifts=N_SHIFTS)
res["agents_only"] = {"edges_topic": len(et_a), "nodes": len(agent_ids)}
log(f"agents-only control: {len(et_a)} edges")

json.dump({"village": VILLAGE, "room": rooms.get(room, room[:8]), "k": K, "n_shifts": N_SHIFTS,
           "window_agent_msgs": len(agents_msgs), "window_human_msgs": len(humans),
           "human_share": round(len(humans)/max(1, len(span)), 4),
           "distinct_visitors": len(hv),
           "visitor_msg_counts": [n for _, n in hv.most_common(TOP_HUMANS)],
           "results": res}, open("facts_humans.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_humans.json")
