"""Does the human-to-agent observation survive conditioning on the channel?

open-chat's 18 agent-to-agent edges all vanish once the channel's recent topic is conditioned on, so
they were shared context rather than dyadic influence. The report's one substantive behavioural
claim, that individual human visitors drive specific agents, rests on edges found the same way. It
has to be re-tested the same way, and reported as a null if it does not survive.
"""
import json, time, collections
import numpy as np
import swarmlib as S
import swarm_te
import fastte

VIL = "open-chat-village"
K, N, TOP_AGENTS, TOP_HUMANS = 8, 200, 12, 3
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)


def modal_ctx(chan, sil, window=12):
    out = np.zeros(len(chan), dtype=np.int64)
    for t in range(len(chan)):
        lo = max(0, t - window)
        c = [x for x in chan[lo:max(lo, t - 1)] if x != sil]
        out[t] = collections.Counter(c).most_common(1)[0][0] if c else sil
    return out


msgs, names, rooms = S.load_village(VIL)
room = S.busiest_room(msgs)
span, lo, hi = S.cut_window(msgs, room, days=14, include_humans=True)
humans = [m for m in span if m["_sp"].startswith("user:")]
amsgs = [m for m in span if not m["_sp"].startswith("user:")]
S.symbolise(span, k=K, seed=0)
agent_ids = S.select_agents(amsgs, min_msgs=50, top_k=TOP_AGENTS)
nm = lambda a: names.get(a, a)
hv = collections.Counter(m["_sp"] for m in humans)
alias = {u: f"visitor-{i+1}" for i, (u, _) in enumerate(hv.most_common(TOP_HUMANS))}
log(f"{len(amsgs)} agent + {len(humans)} human msgs, {len(hv)} visitors")

out = {"village": VIL, "k": K, "n_surrogates": N,
       "window_agent_msgs": len(amsgs), "window_human_msgs": len(humans),
       "distinct_visitors": len(hv), "results": {}}


def run(relabel, extra, tag):
    stream = [dict(m, _sp=relabel(m["_sp"])) for m in sorted(span, key=lambda m: (m["_t"], m["id"]))
              if relabel(m["_sp"]) is not None]
    nodes = list(agent_ids) + extra
    sub = [m for m in stream if m["_sp"] in set(nodes)]
    n = len(sub)
    series = {a: [swarm_te.SILENT] * n for a in nodes}
    for t, m in enumerate(sub):
        series[m["_sp"]][t] = m["_topic"]
    coded, A = fastte.code_series(series)
    alpha = sorted({x for v in series.values() for x in v}); sil = alpha.index(swarm_te.SILENT)
    ctx = modal_ctx([alpha.index(m["_topic"]) for m in sub], sil)
    lab = lambda a: a if a in extra else nm(a)
    rec = {"n_ticks": n}
    for mode in ("pairwise", "conditional"):
        if mode == "conditional":
            t_ = fastte.directed_tests_conditional(coded, ctx, A, A, sil, n_perm=N, seed=0)
        else:
            t_ = fastte.directed_tests_permute(coded, A, sil, n_perm=N, seed=0)
        e = {k for k, v in t_.items() if v["p"] < 0.05}
        rec[mode] = {
            "edges_total": len(e),
            "human_drives_agent": [[lab(i), lab(j)] for (i, j) in e if i in extra],
            "agent_drives_human": [[lab(i), lab(j)] for (i, j) in e if j in extra],
            "agent_agent": sum(1 for (i, j) in e if i not in extra and j not in extra),
        }
        log(f"{tag} {mode:12s}: total {len(e)} | human->agent "
            f"{len(rec[mode]['human_drives_agent'])} | agent->human {len(rec[mode]['agent_drives_human'])}")
    return rec


out["results"]["collapsed"] = run(lambda s: "HUMANS" if s.startswith("user:") else s,
                                  ["HUMANS"], "HUMANS collapsed")
json.dump(out, open("facts_humans_conditional.json", "w", encoding="utf-8"), indent=2)
out["results"]["individual"] = run(lambda s: alias.get(s) if s.startswith("user:") else s,
                                   list(alias.values()), "individual visitors")
json.dump(out, open("facts_humans_conditional.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_humans_conditional.json")
