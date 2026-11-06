"""Sprint day 1: first read of the real AI Village chat. List files, load one village, inspect schema."""
import sys, json, collections
sys.path.insert(0, r"C:\dev\swarm-prep")
from swarm_load import hf_files, load_rows

REPO = "aidigestorg/ai-village"

print("=== repo filenames (no download) ===")
files = hf_files(REPO)
print("total siblings:", len(files))
by_ext = collections.Counter()
for f in files:
    by_ext["/".join(f.split("/")[:1]) if "/" in f else "(root)"] += 1
for k, v in sorted(by_ext.items()):
    print(f"  {k:30s} {v}")
chat = [f for f in files if f.endswith("chat_messages.jsonl.gz")]
print("chat_messages.jsonl.gz files:")
for f in chat:
    print("   ", f)

print("\n=== load main-village/chat_messages.jsonl.gz ===")
rows = list(load_rows(REPO, hf_pattern="main-village/chat_messages.jsonl.gz"))
print("rows:", len(rows))
if rows:
    r0 = rows[0]
    print("columns:", sorted(r0.keys()))
    print("first row (truncated):")
    for k, v in r0.items():
        sv = str(v)
        print(f"   {k:20s} = {sv[:120]}")
    # agent / speaker distribution
    for key in ("agent", "speaker", "author", "sender", "name", "from", "model", "room", "channel", "village"):
        if key in r0:
            c = collections.Counter(str(x.get(key)) for x in rows)
            print(f"\n{key} distribution ({len(c)} distinct):")
            for name, n in c.most_common(40):
                print(f"   {name:40s} {n}")
