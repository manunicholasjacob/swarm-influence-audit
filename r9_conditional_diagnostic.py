"""Is the conditional estimator removing confounding, or just unable to reject?

An external audit of the benchmark argues that the conditional test's "zero false edges" is
degeneracy: with Ac = A = 9 the joint space is A^4 = 6561 cells over ~8000 ticks, and the surrogate
statistic reportedly sits about 2 sd ABOVE the observed one, so a max-T threshold rejects almost
nothing. If true, "open-chat 18 -> 0" is not evidence that those edges were common cause.

Three diagnostics on the real channels, which is what the report actually claims about:
  1. the z distribution. A conservative test shows systematically negative z.
  2. resolution sensitivity. Coarsen the SAME conditioning variable; if edges reappear, the zero was
     driven by cell count rather than by confounding.
  3. pure-null calibration of the conditional test itself, with enough replicates to mean something.
"""
import json, time, collections
import numpy as np
import swarmlib as S
import swarm_te
import fastte

GENERAL = "18a3b2fb-9d2e-4ce7-b9b1-52e09c5408a8"
K, N, TOP_K = 8, 200, 15
t0 = time.time()
def log(m): print(f"[{time.time()-t0:5.0f}s] {m}", flush=True)


def modal_ctx(chan, sil, window=12, levels=None):
    """Modal recent symbol. `levels` coarsens it by binning symbol ids, to vary cell count only."""
    out = np.zeros(len(chan), dtype=np.int64)
    for t in range(len(chan)):
        lo = max(0, t - window)
        c = [x for x in chan[lo:max(lo, t - 1)] if x != sil]
        out[t] = collections.Counter(c).most_common(1)[0][0] if c else sil
    if levels is not None:
        out = out % levels
    return out


def build(span, agents):
    sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
    n = len(sub)
    series = {a: [swarm_te.SILENT] * n for a in agents}
    for t, m in enumerate(sub):
        series[m["_sp"]][t] = m["_topic"]
    coded, A = fastte.code_series(series)
    alpha = sorted({x for v in series.values() for x in v}); sil = alpha.index(swarm_te.SILENT)
    return coded, A, sil, [alpha.index(m["_topic"]) for m in sub], n


out = {"k": K, "n_surrogates": N, "window": 12}

for village, room_id in (("main-village", GENERAL), ("open-chat-village", None)):
    msgs, names, rooms = S.load_village(village)
    room = room_id or S.busiest_room(msgs)
    span, lo, hi = S.cut_window(msgs, room, days=14)
    S.symbolise(span, k=K, seed=0)
    agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
    coded, A, sil, chan, n = build(span, agents)
    rec = {"n_ticks": n, "agents": len(agents), "alphabet_A": A}

    # 1 + 2: z distribution and resolution sensitivity
    for levels, tag in ((None, f"full_Ac{A}"), (4, "coarse_Ac4"), (2, "coarse_Ac2")):
        ctx = modal_ctx(chan, sil, levels=levels)
        Ac = int(ctx.max()) + 1
        t_ = fastte.directed_tests_conditional(coded, ctx, A, Ac, sil, n_perm=N, seed=0)
        zs = np.array([v["z"] for v in t_.values()])
        edges = [k for k, v in t_.items() if v["p"] < 0.05]
        cells = A * A * A * Ac
        rec[tag] = {"Ac": Ac, "joint_cells": cells, "ticks_per_cell": round(n / cells, 3),
                    "edges": len(edges), "mean_z": round(float(zs.mean()), 3),
                    "frac_z_negative": round(float((zs < 0).mean()), 3),
                    "max_z": round(float(zs.max()), 2)}
        log(f"{village} {tag}: Ac={Ac} cells={cells} ticks/cell={n/cells:.2f} "
            f"edges={len(edges)} mean_z={zs.mean():+.2f} frac_neg={(zs<0).mean():.2f} max_z={zs.max():.1f}")
    out[village] = rec
    json.dump(out, open("facts_cond_diag.json", "w", encoding="utf-8"), indent=2)

# 3: pure-null calibration of the conditional test on real structure-free data
msgs, names, rooms = S.load_village("main-village")
span, lo, hi = S.cut_window(msgs, GENERAL, days=14)
S.symbolise(span, k=K, seed=0)
agents = S.select_agents(span, min_msgs=50, top_k=TOP_K)
sub = sorted([m for m in span if m["_sp"] in set(agents)], key=lambda m: (m["_t"], m["id"]))
speakers = [m["_sp"] for m in sub]; symbols = [m["_topic"] for m in sub]
REPS = 40
fired = 0; zmeans = []
for r in range(REPS):
    rng = np.random.default_rng(9100 + r)
    sh = list(symbols); rng.shuffle(sh)
    nn = len(sh)
    series = {a: [swarm_te.SILENT] * nn for a in agents}
    for t, (sp, sy) in enumerate(zip(speakers, sh)):
        series[sp][t] = sy
    coded, A = fastte.code_series(series)
    alpha = sorted({x for v in series.values() for x in v}); sil = alpha.index(swarm_te.SILENT)
    ctx = modal_ctx([alpha.index(x) for x in sh], sil)
    t_ = fastte.directed_tests_conditional(coded, ctx, A, int(ctx.max()) + 1, sil, n_perm=N, seed=r)
    fired += any(v["p"] < 0.05 for v in t_.values())
    zmeans.append(float(np.mean([v["z"] for v in t_.values()])))
    if (r + 1) % 10 == 0:
        log(f"pure-null calibration {r+1} reps: fired {fired}, mean z {np.mean(zmeans):+.2f}")
out["conditional_pure_null"] = {"reps": REPS, "fired": fired, "fwer": round(fired / REPS, 3),
                                "mean_z": round(float(np.mean(zmeans)), 3)}
json.dump(out, open("facts_cond_diag.json", "w", encoding="utf-8"), indent=2)
log("wrote facts_cond_diag.json")
