"""Characterise main-village chat: rooms, agents, activity over time, inter-message gaps.
Pull each table as a SINGLE file (hf_hub_download) then hand the one path to load_rows, so the
preexisting loader never co-mingles tables from a shared snapshot dir."""
import sys, json, collections, datetime as dt
sys.path.insert(0, r"C:\dev\swarm-prep")
import numpy as np
from huggingface_hub import hf_hub_download
from swarm_load import load_rows, to_epoch

REPO = "aidigestorg/ai-village"
VILLAGE = "main-village"

def table(name):
    fp = hf_hub_download(REPO, f"{VILLAGE}/{name}.jsonl.gz", repo_type="dataset")
    return list(load_rows(fp))

agents = table("agents")
rooms = table("chat_rooms")
msgs = table("chat_messages")

print("agents rows:", len(agents), "| rooms rows:", len(rooms), "| chat rows:", len(msgs))

agent_name = {a["id"]: (a.get("name") or a.get("model_string") or a["id"][:8]) for a in agents}
agent_model = {a["id"]: a.get("model_string") for a in agents}
room_name = {r["id"]: (r.get("name") or r["id"][:8]) for r in rooms}

# speaker type split
st = collections.Counter(m.get("speaker_type") for m in msgs)
print("\nspeaker_type:", dict(st))

# per-room counts (agent messages only)
room_ct = collections.Counter(m["room_id"] for m in msgs if m.get("speaker_type") == "agent")
print("\ntop rooms (agent msgs):")
for rid, n in room_ct.most_common(10):
    print(f"   {room_name.get(rid, rid[:8]):30s} {n:8d}  {rid}")

# per-agent counts (agent messages)
ag_ct = collections.Counter(m["agent_speaker_id"] for m in msgs if m.get("speaker_type") == "agent" and m.get("agent_speaker_id"))
print(f"\nagents that spoke: {len(ag_ct)}")
print("top 25 speakers:")
for aid, n in ag_ct.most_common(25):
    print(f"   {agent_name.get(aid, aid[:8]):34s} {n:7d}  {agent_model.get(aid)}")

# time span + monthly activity (agent msgs)
times = sorted(to_epoch(m["created_at"]) for m in msgs if m.get("speaker_type") == "agent")
t0, t1 = times[0], times[-1]
f = dt.datetime.utcfromtimestamp
print(f"\nspan: {f(t0)} -> {f(t1)}  ({(t1-t0)/86400:.0f} days, {len(times)} agent msgs)")
monthly = collections.Counter(f(t).strftime("%Y-%m") for t in times)
print("monthly agent-message counts:")
for mo in sorted(monthly):
    print(f"   {mo}  {monthly[mo]:7d}  {'#'*(monthly[mo]//400)}")
