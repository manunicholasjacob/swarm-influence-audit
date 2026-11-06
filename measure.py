"""Measure turn latency and per-window occupancy in the general room to choose the TE window.
Also find the recent co-present active agent set."""
import sys, collections, datetime as dt
sys.path.insert(0, r"C:\dev\swarm-prep")
import numpy as np
from huggingface_hub import hf_hub_download
from swarm_load import load_rows, to_epoch

REPO, VILLAGE = "aidigestorg/ai-village", "main-village"
GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"

def table(name):
    fp = hf_hub_download(REPO, f"{VILLAGE}/{name}.jsonl.gz", repo_type="dataset")
    return list(load_rows(fp))

agents = table("agents")
name_of = {a["id"]: (a.get("name") or a["id"][:8]) for a in agents}
msgs = [m for m in table("chat_messages")
        if m.get("speaker_type") == "agent" and m.get("room_id") == GENERAL and m.get("agent_speaker_id")]
for m in msgs:
    m["_t"] = to_epoch(m["created_at"])
msgs.sort(key=lambda m: m["_t"])
print("general-room agent msgs:", len(msgs))

# turn latency: gap to next message by a DIFFERENT agent
lat = []
for i in range(1, len(msgs)):
    if msgs[i]["agent_speaker_id"] != msgs[i-1]["agent_speaker_id"]:
        lat.append(msgs[i]["_t"] - msgs[i-1]["_t"])
lat = np.array([x for x in lat if x >= 0])
qs = [10,25,50,75,90,95]
print("inter-speaker gap (s) percentiles:", {q: round(float(np.percentile(lat, q)),1) for q in qs})
print("  gap median min:", round(float(np.median(lat))/60,2), "| mean min:", round(float(lat.mean())/60,2))

# all consecutive gaps
allgap = np.diff([m["_t"] for m in msgs])
allgap = allgap[allgap >= 0]
print("all consecutive gap (s) pct:", {q: round(float(np.percentile(allgap, q)),1) for q in qs})

# recent windows: last 14 / 30 / 60 days; co-present active agents
tmax = msgs[-1]["_t"]
for days in (14, 30, 60, 90):
    cut = tmax - days*86400
    sub = [m for m in msgs if m["_t"] >= cut]
    ct = collections.Counter(m["agent_speaker_id"] for m in sub)
    active = [(name_of.get(a,a[:8]), n) for a, n in ct.most_common() if n >= 50]
    print(f"\nlast {days}d: {len(sub)} msgs, {len(ct)} speakers, {len(active)} with >=50 msgs")
    for nm, n in active[:18]:
        print(f"    {nm:30s} {n}")

# per-window occupancy for candidate widths, over last 30 days, agents with >=50 msgs
cut = tmax - 30*86400
sub = [m for m in msgs if m["_t"] >= cut]
ct = collections.Counter(m["agent_speaker_id"] for m in sub)
keep = {a for a,n in ct.items() if n >= 50}
sub = [m for m in sub if m["agent_speaker_id"] in keep]
print(f"\n--- occupancy over last 30d, {len(keep)} agents, {len(sub)} msgs ---")
t0 = min(m["_t"] for m in sub); t1 = max(m["_t"] for m in sub)
for w_min in (1, 2, 5, 10, 20, 30, 60):
    w = w_min*60
    nwin = int((t1-t0)//w)+1
    # fraction of (agent,window) cells that are non-empty
    cells = collections.Counter((m["agent_speaker_id"], int((m["_t"]-t0)//w)) for m in sub)
    occ = len(cells)/(len(keep)*nwin)
    # mean distinct speakers per occupied window
    perwin = collections.defaultdict(set)
    for (a,w_i) in cells: perwin[w_i].add(a)
    multi = sum(1 for s in perwin.values() if len(s)>=2)
    print(f"  w={w_min:2d}min  nwin={nwin:6d}  cell-occupancy={occ:.3f}  windows_with>=2_speakers={multi} ({multi/nwin:.3f})")
