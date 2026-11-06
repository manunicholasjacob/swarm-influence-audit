"""Does any of this generalise? Run the same pipeline on all four villages, which differ in size,
agent count, lifetime and tempo. Also measure each village's reply latency, to show the clock-window
problem is a property of agent chat and not of one channel.
"""
import json, time, collections
import numpy as np
import swarmlib as S

K, N_SHIFTS, TOP_K, MIN_MSGS = 8, 200, 15, 50
VILLAGES = ["main-village", "open-chat-village", "swarm-village", "game-jam-village"]
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

rows = []
for v in VILLAGES:
    msgs, names, rooms = S.load_village(v)
    agent_msgs = [m for m in msgs if not m["_sp"].startswith("user:")]
    room = S.busiest_room(msgs)
    span_days = (max(m["_t"] for m in agent_msgs) - min(m["_t"] for m in agent_msgs)) / 86400
    days = 14 if span_days > 14 else span_days + 1     # short-lived villages: use the whole life
    span, lo, hi = S.cut_window(msgs, room, days=days)
    if len(span) < 200:
        log(f"{v}: only {len(span)} msgs in window, skipping TE"); continue
    # reply latency in this room/window
    ss = sorted(span, key=lambda m: (m["_t"], m["id"]))
    gaps = [ss[i]["_t"] - ss[i-1]["_t"] for i in range(1, len(ss))
            if ss[i]["_sp"] != ss[i-1]["_sp"] and ss[i]["_t"] >= ss[i-1]["_t"]]
    S.symbolise(span, k=K, seed=0)
    agents = S.select_agents(span, min_msgs=MIN_MSGS, top_k=TOP_K)
    if len(agents) < 4:
        log(f"{v}: only {len(agents)} eligible agents, skipping TE"); continue
    nm = lambda a: names.get(a, a)
    tt, et, n = S.run_window(span, agents, key="_topic", n_shifts=N_SHIFTS)
    th, eh, _ = S.run_window(span, agents, key="_hash", n_shifts=N_SHIFTS)
    sc, _ = S.leader_scores(tt)
    rows.append({
        "village": v, "room": rooms.get(room, room[:8]),
        "window_days": round(days, 2), "lifetime_days": round(span_days, 1),
        "total_agents_in_village": len({m["_sp"] for m in agent_msgs}),
        "window_msgs": len(span), "te_agents": len(agents), "n_ticks": n,
        "median_reply_gap_s": round(float(np.median(gaps)), 1) if gaps else None,
        "p95_reply_gap_s": round(float(np.percentile(gaps, 95)), 1) if gaps else None,
        "edges_topic": len(et), "edges_hash": len(eh),
        "edge_density_topic": round(len(et) / (len(agents)*(len(agents)-1)), 4),
        "top_leaders": sorted(((nm(a), s) for a, s in sc.items()), key=lambda x: -x[1])[:5],
        "edges": [[nm(i), nm(j), round(tt[(i, j)]["p"], 4)] for (i, j) in
                  sorted(et, key=lambda x: tt[x]["p"])][:15],
    })
    log(f"{v}: {len(span)} msgs, {len(agents)} agents, topic {len(et)} vs hash {len(eh)} edges, "
        f"median gap {rows[-1]['median_reply_gap_s']}s")

json.dump({"k": K, "n_shifts": N_SHIFTS, "min_msgs": MIN_MSGS, "top_k": TOP_K, "villages": rows},
          open("facts_villages.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_villages.json")
