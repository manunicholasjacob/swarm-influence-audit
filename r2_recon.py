"""Round-2 recon: how much data is in each village, how many human messages, roster overlap
between adjacent windows. Decides which round-2 experiments are feasible."""
import sys, collections, datetime as dt
sys.path.insert(0, r"C:\dev\swarm-prep")
from huggingface_hub import hf_hub_download
from swarm_load import load_rows, to_epoch

REPO = "aidigestorg/ai-village"
VILLAGES = ["main-village", "open-chat-village", "game-jam-village", "swarm-village"]
F = dt.datetime.utcfromtimestamp

def table(village, name):
    fp = hf_hub_download(REPO, f"{village}/{name}.jsonl.gz", repo_type="dataset")
    return list(load_rows(fp))

for v in VILLAGES:
    try:
        msgs = table(v, "chat_messages")
        rooms = {r["id"]: (r.get("name") or r["id"][:8]) for r in table(v, "chat_rooms")}
        ag = {a["id"]: (a.get("name") or a["id"][:8]) for a in table(v, "agents")}
    except Exception as e:
        print(f"\n### {v}: ERROR {type(e).__name__}: {e}")
        continue
    st = collections.Counter(m.get("speaker_type") for m in msgs)
    agent_msgs = [m for m in msgs if m.get("speaker_type") == "agent" and m.get("agent_speaker_id")]
    if not agent_msgs:
        print(f"\n### {v}: {len(msgs)} rows, no agent msgs")
        continue
    ts = sorted(to_epoch(m["created_at"]) for m in agent_msgs)
    room_ct = collections.Counter(m["room_id"] for m in agent_msgs)
    top_room, top_n = room_ct.most_common(1)[0]
    print(f"\n### {v}: {len(msgs)} rows | speaker_type {dict(st)} | agents {len(ag)}")
    print(f"    span {F(ts[0]):%Y-%m-%d} -> {F(ts[-1]):%Y-%m-%d} ({(ts[-1]-ts[0])/86400:.0f}d)")
    print(f"    top room '{rooms.get(top_room, top_room[:8])}' {top_n} agent msgs of {len(agent_msgs)}"
          f" ({len(room_ct)} rooms)")
    # agents with >=50 msgs in the last 14d of THIS village
    cut = ts[-1] - 14*86400
    recent = [m for m in agent_msgs if to_epoch(m["created_at"]) >= cut and m["room_id"] == top_room]
    ct = collections.Counter(m["agent_speaker_id"] for m in recent)
    print(f"    last 14d in top room: {len(recent)} msgs, {sum(1 for _,n in ct.items() if n>=50)} agents >=50")

# main-village specifics: humans in #general, and adjacent-window roster overlap
GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
msgs = table("main-village", "chat_messages")
for m in msgs:
    m["_t"] = to_epoch(m["created_at"])
gen = [m for m in msgs if m.get("room_id") == GENERAL]
tmax = max(m["_t"] for m in gen if m.get("speaker_type") == "agent")
for lo, hi, lbl in ((28, 14, "prev 14d"), (14, 0, "current 14d")):
    w = [m for m in gen if tmax - lo*86400 <= m["_t"] < tmax - hi*86400]
    a = [m for m in w if m.get("speaker_type") == "agent" and m.get("agent_speaker_id")]
    u = [m for m in w if m.get("speaker_type") == "user"]
    ct = collections.Counter(m["agent_speaker_id"] for m in a)
    keep = {x for x, n in ct.items() if n >= 50}
    print(f"\n{lbl}: {len(a)} agent msgs, {len(u)} HUMAN msgs, {len(keep)} agents >=50")
    globals().setdefault("sets", {})[lbl] = keep
s = globals()["sets"]
ov = s["prev 14d"] & s["current 14d"]
print(f"\nroster overlap between adjacent 14d windows: {len(ov)} agents "
      f"(prev {len(s['prev 14d'])}, cur {len(s['current 14d'])})")
