"""Shared round-2 pipeline. WEEKEND CODE. Wraps the preexisting estimator/symbolisers
(swarm_te.py, swarm_load.py in C:\\dev\\swarm-prep) and the verified fast estimator (fastte.py).

Keeps one definition of: load a village, pick a room, cut a window, select agents, symbolise,
build the turn-ordered series, run the directed test. Every round-2 experiment uses these, so the
headline run and the robustness runs cannot silently diverge.
"""
import sys, collections
sys.path.insert(0, r"C:\dev\swarm-prep")
import numpy as np
from huggingface_hub import hf_hub_download
import swarm_te
from swarm_load import load_rows, to_epoch, TopicSymboliser, HashSymboliser, SILENT
import fastte

REPO = "aidigestorg/ai-village"
ALPHA = 0.05
_cache = {}


def table(village, name):
    key = (village, name)
    if key not in _cache:
        fp = hf_hub_download(REPO, f"{village}/{name}.jsonl.gz", repo_type="dataset")
        _cache[key] = list(load_rows(fp))   # single file in: no snapshot co-mingling
    return _cache[key]


def load_village(village):
    """messages (with _t epoch and _sp speaker id), agent-name map, room-name map."""
    agents = {a["id"]: (a.get("name") or a["id"][:8]) for a in table(village, "agents")}
    try:
        rooms = {r["id"]: (r.get("name") or r["id"][:8]) for r in table(village, "chat_rooms")}
    except Exception:
        rooms = {}
    msgs = []
    for m in table(village, "chat_messages"):
        if not m.get("content"):
            continue
        if m.get("speaker_type") == "agent" and m.get("agent_speaker_id"):
            sp = m["agent_speaker_id"]
        elif m.get("speaker_type") == "user":
            sp = "user:" + str(m.get("user_speaker_id") or "anon")
        else:
            continue
        m = dict(m)
        m["_t"] = to_epoch(m["created_at"])
        m["_sp"] = sp
        msgs.append(m)
    msgs.sort(key=lambda m: (m["_t"], m["id"]))
    return msgs, agents, rooms


def busiest_room(msgs):
    ct = collections.Counter(m["room_id"] for m in msgs if not m["_sp"].startswith("user:"))
    return ct.most_common(1)[0][0]


def cut_window(msgs, room, days=14, offset_days=0, end_ts=None, include_humans=False):
    """The `days`-long window ending `offset_days` before the last agent message in `room`."""
    inroom = [m for m in msgs if m["room_id"] == room]
    agent_t = [m["_t"] for m in inroom if not m["_sp"].startswith("user:")]
    tmax = (max(agent_t) if end_ts is None else end_ts) - offset_days * 86400
    lo = tmax - days * 86400
    out = [m for m in inroom if lo <= m["_t"] < tmax + (0 if offset_days else 1)]
    if not include_humans:
        out = [m for m in out if not m["_sp"].startswith("user:")]
    return out, lo, tmax


def select_agents(span, min_msgs=50, top_k=15, restrict=None):
    ct = collections.Counter(m["_sp"] for m in span)
    keep = [a for a, n in ct.most_common() if n >= min_msgs and (restrict is None or a in restrict)]
    return keep[:top_k] if top_k else keep


def symbolise(span, k=8, seed=0, fit_corpus=None):
    """Attach _topic and _hash to each message. fit_corpus lets several windows share one topic space."""
    texts = [m["content"] for m in span]
    topic = TopicSymboliser(k=k, seed=seed).fit(fit_corpus if fit_corpus is not None else texts)
    hashr = HashSymboliser(k=k)
    for m, st, sh in zip(span, topic.transform(texts), hashr.transform(texts)):
        m["_topic"], m["_hash"] = st, sh
    return topic


def turn_series(messages, agents, key):
    """One message = one tick, so lag-1 is 'the message immediately before'."""
    sub = [m for m in messages if m["_sp"] in set(agents)]
    sub.sort(key=lambda m: (m["_t"], m["id"]))
    ev = [(m["_sp"], float(i), m[key]) for i, m in enumerate(sub)]
    if not ev:
        return {a: [] for a in agents}, 0
    return swarm_te.windowed_series(ev, width=1.0, agents=list(agents))


def series_from_stream(stream, agents):
    """stream: ordered [(speaker, symbol)]. One element = one tick. Used by the spike-in control."""
    agents = list(agents)
    idx = {a: k for k, a in enumerate(agents)}
    n = len(stream)
    series = {a: [SILENT] * n for a in agents}
    for t, (sp, sym) in enumerate(stream):
        if sp in idx:
            series[sp][t] = sym
    return series, n


def directed(series, n_shifts=200, seed=0, null="shift"):
    """null='shift' is the preexisting circular-shift null; null='permute' is the weekend
    sparsity-preserving null (source keeps its speaking positions, only symbols are permuted)."""
    coded, A = fastte.code_series(series)
    if null == "permute":
        alpha = sorted({s for v in series.values() for s in v})
        return fastte.directed_tests_permute(coded, A, alpha.index(SILENT) if SILENT in alpha else -1,
                                             n_perm=n_shifts, seed=seed)
    return fastte.directed_tests_fast(coded, A, n_shifts=n_shifts, seed=seed)


def sig_edges(tests, alpha=ALPHA):
    return {e for e, v in tests.items() if v["p"] < alpha}


def leader_scores(tests, alpha=ALPHA):
    return swarm_te.leader_scores(tests, alpha=alpha)


def run_window(span, agents, key="_topic", n_shifts=200, seed=0, null="shift"):
    s, n = turn_series(span, agents, key)
    t = directed(s, n_shifts=n_shifts, seed=seed, null=null)
    return t, sig_edges(t), n


def jaccard(a, b):
    u = a | b
    return len(a & b) / len(u) if u else float("nan")
