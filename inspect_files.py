"""Map the repo properly: group by extension, find every non-tar data file, peek at each distinct basename."""
import sys, collections
sys.path.insert(0, r"C:\dev\swarm-prep")
from swarm_load import hf_files

REPO = "aidigestorg/ai-village"
files = hf_files(REPO)
print("total siblings:", len(files))

ext = collections.Counter()
for f in files:
    low = f.lower()
    if low.endswith(".jsonl.gz"): ext[".jsonl.gz"] += 1
    elif low.endswith(".tar"): ext[".tar"] += 1
    else:
        ext["."+f.split(".")[-1]] += 1
print("by extension:", dict(ext))

print("\n=== root files ===")
for f in files:
    if "/" not in f:
        print("  ", f)

print("\n=== distinct basenames among .jsonl.gz (non-tar data) ===")
base = collections.Counter()
for f in files:
    if f.lower().endswith(".jsonl.gz"):
        base[f.split("/")[-1]] += 1
for b, n in base.most_common():
    print(f"  {b:40s} {n}")

print("\n=== all main-village non-tar files ===")
for f in files:
    if f.startswith("main-village/") and not f.lower().endswith(".tar"):
        print("  ", f)
