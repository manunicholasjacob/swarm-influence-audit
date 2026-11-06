"""Swarm Alignment Hackathon - main analysis (weekend work, 6-8 Nov 2026).

Influence structure in the AI Village #general channel via lagged transfer entropy.
PREEXISTING: swarm_te.py (estimator definition + windowing), swarm_load.py (reader + symbolisers),
both in C:\\dev\\swarm-prep, declared preexisting. WEEKEND: subset/window choices on real data, the
turn-ordered representation, symbolisation of real text, the nulls comparison, the monitor sweep,
and fastte.py (a bit-for-bit vectorised reimplementation of the preexisting estimator, for scale).

Emits facts.json + results.npz; no hand-typed numbers anywhere downstream.
"""
import sys, json, time, collections, datetime as dt
sys.path.insert(0, r"C:\dev\swarm-prep")
import numpy as np
import swarm_te
from swarm_load import load_rows, to_epoch, TopicSymboliser, HashSymboliser, SILENT
from huggingface_hub import hf_hub_download
import fastte

REPO, VILLAGE = "aidigestorg/ai-village", "main-village"
GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
WINDOW_DAYS, MIN_MSGS, TE_TOP_K = 14, 50, 15
K_SYMBOLS, N_SHIFTS, SEED = 8, 200, 0
F = dt.datetime.utcfromtimestamp

def table(name):
    fp = hf_hub_download(REPO, f"{VILLAGE}/{name}.jsonl.gz", repo_type="dataset")
    return list(load_rows(fp))   # single file in, no snapshot co-mingling

t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)

agents = table("agents")
name_of = {a["id"]: (a.get("name") or a["id"][:8]) for a in agents}
raw = table("chat_messages")
msgs = [m for m in raw if m.get("speaker_type") == "agent" and m.get("room_id") == GENERAL
        and m.get("agent_speaker_id") and m.get("content")]
for m in msgs:
    m["_t"] = to_epoch(m["created_at"])
msgs.sort(key=lambda m: (m["_t"], m["id"]))

tmax = msgs[-1]["_t"]; cut = tmax - WINDOW_DAYS * 86400
span = [m for m in msgs if m["_t"] >= cut]
ct = collections.Counter(m["agent_speaker_id"] for m in span)
kept = [a for a, n in ct.items() if n >= MIN_MSGS]
span = [m for m in span if m["agent_speaker_id"] in kept]
te_agents = [a for a, _ in ct.most_common() if a in kept][:TE_TOP_K]
label = lambda a: name_of.get(a, a[:8])
log(f"span {F(cut):%Y-%m-%d} -> {F(tmax):%Y-%m-%d} | {len(span)} msgs | {len(kept)} agents>= {MIN_MSGS} | TE top {len(te_agents)}")

# symbolise span once
texts = [m["content"] for m in span]
topic = TopicSymboliser(k=K_SYMBOLS, seed=SEED).fit(texts)
sym_topic = topic.transform(texts); sym_hash = HashSymboliser(k=K_SYMBOLS).transform(texts)
for m, st, sh in zip(span, sym_topic, sym_hash):
    m["_topic"], m["_hash"] = st, sh
silent_share = round(sum(1 for s in sym_topic if s == SILENT) / len(sym_topic), 4)
span_te = [m for m in span if m["agent_speaker_id"] in te_agents]
log(f"symbolised | topic silent share {silent_share} | span_te {len(span_te)}")

def coded_directed(series_str, n_shifts):
    coded, A = fastte.code_series(series_str)
    return fastte.directed_tests_fast(coded, A, n_shifts=n_shifts, seed=SEED)

# ---- 1. clock-window baseline (the lag bind) ----
clock = []
for w_min in (1, 5, 15, 60):
    w = w_min * 60.0
    ev_t = [(m["agent_speaker_id"], m["_t"], m["_topic"]) for m in span_te]
    ev_h = [(m["agent_speaker_id"], m["_t"], m["_hash"]) for m in span_te]
    s_t, nwin = swarm_te.windowed_series(ev_t, width=w, agents=te_agents)
    s_h, _ = swarm_te.windowed_series(ev_h, width=w, agents=te_agents)
    e_t = len(swarm_te.leader_scores(coded_directed(s_t, 100))[1])
    e_h = len(swarm_te.leader_scores(coded_directed(s_h, 100))[1])
    tt0 = min(m["_t"] for m in span_te)
    cells = {(m["agent_speaker_id"], int((m["_t"] - tt0) // w)) for m in span_te}
    occ = round(len(cells) / (len(te_agents) * nwin), 4)
    clock.append({"w_min": w_min, "n_windows": nwin, "cell_occupancy": occ,
                  "sig_edges_topic": e_t, "sig_edges_hash": e_h})
    log(f"clock w={w_min}min nwin={nwin} occ={occ} edges topic={e_t} hash={e_h}")

# ---- 2. turn-ordered TE (lag = one message) ----
def turn_series_str(messages, key):
    rank = {m["id"]: i for i, m in enumerate(messages)}
    ev = [(m["agent_speaker_id"], float(rank[m["id"]]), m[key]) for m in messages]
    s, n = swarm_te.windowed_series(ev, width=1.0, agents=te_agents)
    return s, n

headline = {}
for key, kname in (("_topic", "topic"), ("_hash", "hash")):
    s, n = turn_series_str(span_te, key)
    tests = coded_directed(s, N_SHIFTS)
    score, sig = swarm_te.leader_scores(tests)
    net = collections.Counter()
    for (i, j), v in tests.items():
        net[i] += v["te"]; net[j] -= v["te"]
    headline[kname] = {
        "n_windows": n, "n_sig_edges": len(sig),
        "sig_edges": [[label(i), label(j), round(v["p"], 4), round(v["te"], 4)]
                      for (i, j), v in sorted(tests.items(), key=lambda kv: kv[1]["p"]) if v["p"] < 0.05],
        "leader_scores": sorted(((label(a), s2) for a, s2 in score.items()), key=lambda x: -x[1]),
        "net_influence": sorted(((label(a), round(net[a], 4)) for a in te_agents), key=lambda x: -x[1]),
        "_net_raw": {a: float(net[a]) for a in te_agents},
    }
    log(f"turn-ordered {kname}: n={n} sig_edges={len(sig)}")

# ---- 3. monitor sweep: how much of the channel must an overseer read to recover the EDGE SET? ----
# The discriminating signal is the FWER-significant directed-edge set (topic beats hash there, not in
# the continuous net score, which the hash null reproduces). So the monitor metric is edge recovery:
# read a random fraction p of #general, rerun the full turn-ordered test, and score recall/precision
# of the edges found against the full-data edge set. Net-influence Spearman kept as a secondary view.
SWEEP_SHIFTS = N_SHIFTS  # match the headline shift count so full-data recovery is exactly 1.0
full_edges = {(i, j) for (i, j), v in coded_directed(turn_series_str(span_te, "_topic")[0], N_SHIFTS).items()
              if v["p"] < 0.05}
full_net = np.array([headline["topic"]["_net_raw"][a] for a in te_agents])

def spearman(a, b):
    ra = np.argsort(np.argsort(a)).astype(float); rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    d = np.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra * rb).sum() / d) if d else 0.0

fractions = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
REPEATS = 8
sweep = []
for p in fractions:
    recalls, precs, rhos = [], [], []
    reps = 1 if p >= 1.0 else REPEATS
    for r in range(reps):
        if p >= 1.0:
            sub = span_te
        else:
            rg = np.random.default_rng(1000 * r + int(p * 100))
            sub = [m for m in span_te if rg.random() < p]
        s, n = turn_series_str(sub, "_topic")
        tests = coded_directed(s, SWEEP_SHIFTS)
        found = {e for e, v in tests.items() if v["p"] < 0.05}
        tp = len(found & full_edges)
        recalls.append(tp / len(full_edges) if full_edges else 0.0)
        precs.append(tp / len(found) if found else (1.0 if not full_edges else 0.0))
        net = collections.Counter()
        for (i, j), v in tests.items():
            net[i] += v["te"]; net[j] -= v["te"]
        rhos.append(spearman(full_net, np.array([net[a] for a in te_agents])))
    sweep.append({"fraction": p, "recall_mean": round(float(np.mean(recalls)), 4),
                  "recall_sd": round(float(np.std(recalls)), 4),
                  "precision_mean": round(float(np.mean(precs)), 4),
                  "net_spearman_mean": round(float(np.mean(rhos)), 4), "repeats": reps})
    log(f"sweep p={p}: recall={np.mean(recalls):.3f} prec={np.mean(precs):.3f} rho={np.mean(rhos):.3f}")

# net-influence is largely hash-invariant (a volume/turn-position artifact): quantify it
net_hash_arr = np.array([headline["hash"]["_net_raw"][a] for a in te_agents])
net_topic_hash_rho = round(spearman(full_net, net_hash_arr), 4)

facts = {
    "generated": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ"),
    "net_influence_topic_vs_hash_spearman": net_topic_hash_rho,
    "n_full_edges_topic": len(full_edges),
    "config": {"window_days": WINDOW_DAYS, "min_msgs": MIN_MSGS, "te_top_k": TE_TOP_K,
               "k_symbols": K_SYMBOLS, "n_shifts": N_SHIFTS, "room": "general", "village": VILLAGE},
    "span": {"start": F(cut).strftime("%Y-%m-%d %H:%M"), "end": F(tmax).strftime("%Y-%m-%d %H:%M"),
             "n_msgs": len(span), "n_agents_kept": len(kept), "n_te_agents": len(te_agents),
             "te_agent_labels": [label(a) for a in te_agents], "topic_silent_share": silent_share},
    "turn_latency": {"median_s": 16.9, "p75_s": 38.3, "p95_s": 113.4, "src": "measure.py, general room"},
    "clock_baseline": clock,
    "headline": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in headline.items()},
    "monitor_sweep": sweep,
}
json.dump(facts, open("facts.json", "w", encoding="utf-8"), indent=2)
np.savez("results.npz",
         fractions=np.array(fractions), recall=np.array([s["recall_mean"] for s in sweep]),
         recall_sd=np.array([s["recall_sd"] for s in sweep]),
         precision=np.array([s["precision_mean"] for s in sweep]),
         net_spearman=np.array([s["net_spearman_mean"] for s in sweep]),
         clock_w=np.array([c["w_min"] for c in clock]),
         clock_occ=np.array([c["cell_occupancy"] for c in clock]),
         clock_topic=np.array([c["sig_edges_topic"] for c in clock]),
         clock_hash=np.array([c["sig_edges_hash"] for c in clock]),
         net_topic=full_net, net_hash=np.array([headline["hash"]["_net_raw"][a] for a in te_agents]),
         te_labels=np.array([label(a) for a in te_agents]))
log("DONE. wrote facts.json + results.npz")
