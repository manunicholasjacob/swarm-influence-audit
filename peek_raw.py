"""Fetch doc files + raw-peek chat_messages and events to learn the true message schema."""
import sys, gzip, json
from huggingface_hub import hf_hub_download

REPO = "aidigestorg/ai-village"

# docs
for doc in ("SCHEMA.md", "README.md", "main-village/README.md"):
    try:
        p = hf_hub_download(REPO, doc, repo_type="dataset")
        txt = open(p, encoding="utf-8").read()
        print(f"\n######## {doc} ({len(txt)} chars) ########")
        print(txt[:4000])
    except Exception as e:
        print(f"\n[{doc}] error: {e}")

def peek(name, n=3):
    p = hf_hub_download(REPO, name, repo_type="dataset")
    print(f"\n######## RAW {name} ########")
    with gzip.open(p, "rt", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if i >= n: break
            r = json.loads(line)
            print(f"-- row {i}: keys = {sorted(r.keys())}")
            for k, v in r.items():
                print(f"     {k:28s} = {str(v)[:140]}")

peek("main-village/chat_messages.jsonl.gz")
peek("main-village/agents.jsonl.gz")
