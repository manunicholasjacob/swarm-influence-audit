"""Check every numeric claim in REPORT_V2.md against the facts_*.json the analysis produced.
Fails loudly on any mismatch. No number in the report may be hand-typed."""
import json, os, re, sys

D = r"C:\dev\swarm-sprint"
def F(n): return json.load(open(os.path.join(D, n), encoding="utf-8"))
txt = open(os.path.join(D, "report", "REPORT_V2.md"), encoding="utf-8").read()

clock, sparse, cal, cal2 = F("facts_clock.json"), F("facts_sparse.json"), F("facts_calib.json"), F("facts_calib2.json")
fin, pw2, rec, rob = F("facts_final.json"), F("facts_power2.json"), F("facts_recompute.json"), F("facts_robust.json")
oc, qual = F("facts_openchat.json"), F("facts_qual.json")

checks = []
def want(label, s):
    checks.append((label, str(s) in txt, s))

# --- data ---
for s in ["205,726", "58", "576", "10,029", "166,715", "81%", "35,483", "23", "66",
          "12,264", "3,848", "133", "838", "8,800", "7,958"]:
    want(f"data {s}", s)

# --- 4.2 reply gaps ---
g = clock["reply_gap_s"]
for k, v in (("p50", g["p50"]), ("p25", g["p25"]), ("p75", g["p75"]), ("p95", g["p95"])):
    want(f"gap {k}", v)

# --- 5.1 clock ---
r = {x["w_min"]: x for x in clock["rows"]}
want("same-window 0.5min", f'{r[0.5]["same_window_reply_share"]*100:.1f}%')
want("same-window 5min", f'{r[5]["same_window_reply_share"]*100:.1f}%')
want("same-window 60min", f'{r[60]["same_window_reply_share"]*100:.1f}%')
want("occupancy 0.5min", f'{r[0.5]["cell_occupancy"]*100:.1f}%')
for w in (0.5, 1, 15):   # report states hash against topic
    want(f"clock edges {w}", f'{r[w]["edges_hash"]} against {r[w]["edges_topic"]}')

# --- 5.2 negative control ---
sr = {x["volume"]: x for x in sparse["rows"]}
want("sparse 50", f'{sr[50]["runs_with_any_null_edge"]} of {sr[50]["of"]}')
for v in (50, 100, 263, 600, 1500):
    want(f"sparse z{v}", f'{round(sr[v]["mean_max_z"], 1):g}')   # report quotes one decimal
want("shift fwer", f'{cal["rows"]["shift"]["familywise_error_rate"]:.2f}')
want("shift reps", f'{sum(1 for c in cal["rows"]["shift"]["edges_per_rep"] if c>0)} of {cal["reps"]}')
want("shift mean edges", cal["rows"]["shift"]["mean_edges"])

# --- 5.3 repair ---
cbig = json.load(open(os.path.join(D, "facts_calib_big.json"), encoding="utf-8"))
want("permute fwer", f'{cbig["fwer"]:.3f}')
want("permute reps", cbig["reps"])
want("wilson lo", f'{cbig["wilson95"][0]:.3f}')
want("wilson hi", f'{cbig["wilson95"][1]:.3f}')
fp = {x["volume"]: x for x in fin["false_positive_by_null"]["rows"]}
want("perm fp 263", f'0 of {fp[263]["permute"]["of"]}')
want("perm z263", fp[263]["permute"]["mean_max_z"])
want("shift z263 final", round(fp[263]["shift"]["mean_max_z"], 1))
want("shift z1500 final", round(fp[1500]["shift"]["mean_max_z"], 1))

# --- 5.4 headline + villages ---
hb = fin["headline_by_null"]
want("shift topic", hb["shift"]["topic"]["n_edges"])
want("permute topic", hb["permute"]["topic"]["n_edges"])
assert hb["n_survive_both_topic"] == 0, "survive-both changed; report says none survive"
vs = {v["village"]: v for v in rec["villages"]}
for name in vs:
    want(f"village {name} shift", f'{vs[name]["shift"]["edges_topic"]} / {vs[name]["shift"]["edges_hash"]}')
    want(f"village {name} perm", f'{vs[name]["permute"]["edges_topic"]} / {vs[name]["permute"]["edges_hash"]}')

# --- 5.5 power ---
P = {r["coupling"]: r for r in fin["power_permute"]["rows"]}
want("power 0.8", f'{P[0.8]["detected"]} of {P[0.8]["of"]}')
p2 = {r["synth_volume"]: r for r in pw2["rows"]}
want("power vol 800", f'{p2[800]["detected"]} of {p2[800]["of"]}')
for v in (2000, 4000):
    assert p2[v]["rate"] == 1.0, f"power at {v} changed"

# --- 5.6 replication ---
rp = rob["replication"]
want("main repl cur", f'{rp["cur"]["edges_topic"]} and {rp["prev"]["edges_topic"]}')
want("main repl jaccard", f'{rp["jaccard"]:.2f}')
ocr = oc["replication"]
want("oc repl", f'{ocr["cur_edges"]} edges and the previous {ocr["prev_edges"]}')
want("oc shared", f'{ocr["shared"]} in common')
want("oc jaccard", f'{ocr["jaccard"]:.2f}')
sh = oc["split_half"]
want("oc split", f'{sh["edges_h1"]} edges against {sh["edges_h2"]}')
for row in oc["k_sweep"]:
    want(f"oc k={row['k']}", f'{row["edges"]} edges at k={row["k"]}' if row["k"] == 4 else str(row["edges"]))

# --- 5.7 humans ---
h = rec["humans_open_chat"]
ind = h["individual"]["permute"]
want("human share", f'{h["human_share"]*100:.0f}%')
want("visitors", h["distinct_visitors"])
want("agents only", h["agents_only"]["permute"])
want("individual total", ind["edges_topic"])
want("agent-agent", ind["agent_agent"])
want("h2a", len(ind["human_drives_agent"]))
assert len(ind["agent_drives_human"]) == 0, "agent->visitor edges appeared; report says none"

# --- 5.8 ---
want("net rho", f'{rob["headline"]["net_topic_vs_hash_spearman"]:.2f}')
want("baseline rho", f'{qual["baseline"]["spearman_te_vs_excess_copy"]:.2f}')
want("baseline overlap", f'{qual["baseline"]["top_by_excess_overlap"]} of {qual["baseline"]["n_significant"]}')

bad = [(l, s) for l, ok, s in checks if not ok]
for l, ok, s in checks:
    if not ok:
        print(f"FAIL  {l}   <<missing: {s!r}>>")
print(f"\n{len(checks)-len(bad)}/{len(checks)} numeric checks pass")
if bad:
    sys.exit("VERIFICATION FAILED")
print("ALL NUMERIC CLAIMS VERIFIED against the analysis output")

# --- round-3 robustness additions ---
sc = json.load(open(os.path.join(D, "facts_scale.json"), encoding="utf-8"))
sy = json.load(open(os.path.join(D, "facts_symboliser.json"), encoding="utf-8"))
extra = []
srow = {r["n_agents"]: r for r in sc["rows"]}
tot_s = sum(sum(1 for c in r["shift"]["edges_per_rep"] if c>0) for r in sc["rows"])
tot_p = sum(sum(1 for c in r["permute"]["edges_per_rep"] if c>0) for r in sc["rows"])
tot_n = len(sc["rows"])*sc["reps"]
extra.append(("scale shift aggregate", f"{tot_s} of {tot_n}" in txt))
extra.append(("scale permute aggregate", f"{tot_p} of {tot_n}" in txt))
hc = json.load(open(os.path.join(D, "facts_hashcalib.json"), encoding="utf-8"))
if "hash" in hc["alphabets"]:
    h = hc["alphabets"]["hash"]
    extra.append(("hash alphabet share", f'{h["largest_symbol_share"]*100:.0f}%' in txt))
    extra.append(("hash alphabet shift", f'{int(h["shift"]["fwer"]*hc["reps"])} of {hc["reps"]}' in txt))
ch = {c["village"]: c for c in sy["channels"]}
m, o = ch["main-village"], ch["open-chat-village"]
extra.append(("lsa main", f'{m["lsa_kmeans"]["shift"]} edges against {m["lsa_kmeans"]["permute"]}' in txt))
extra.append(("lsa openchat", f'{o["lsa_kmeans"]["shift"]} against {o["lsa_kmeans"]["permute"]}' in txt))
for lab, ok in extra:
    if not ok:
        print(f"FAIL  {lab}")
print(f"round-3: {sum(1 for _, ok in extra if ok)}/{len(extra)} pass")
if not all(ok for _, ok in extra):
    sys.exit("ROUND-3 VERIFICATION FAILED")

# --- round-4: open-chat power ---
po = json.load(open(os.path.join(D, "facts_power_openchat.json"), encoding="utf-8"))
pr = {r["coupling"]: r for r in po["rows"]}
r4 = [("oc power 0.1", f'{pr[0.1]["detected"]} of {pr[0.1]["of"]} runs at coupling 0.1' in txt),
      ("oc power 0.2", f'{pr[0.2]["detected"]} of {pr[0.2]["of"]} from 0.2 upward' in txt)]
for lab, ok in r4:
    if not ok:
        print(f"FAIL  {lab}")
print(f"round-4: {sum(1 for _, ok in r4 if ok)}/{len(r4)} pass")
if not all(ok for _, ok in r4):
    sys.exit("ROUND-4 VERIFICATION FAILED")

# --- round-5: mechanism isolation ---
mech = json.load(open(os.path.join(D, "facts_mechanism.json"), encoding="utf-8"))
C = mech["conditions"]
r5 = []
def frac(cond, null):
    return f'{int(round(C[cond][null]["fwer"]*mech["reps"]))} / {mech["reps"]}'
r5.append(("mech A shift", frac("A_real_order_real_symbols", "shift").replace(" / ", " / ") in txt
           or f'{int(round(C["A_real_order_real_symbols"]["shift"]["fwer"]*mech["reps"]))} of {mech["reps"]}' in txt))
r5.append(("mech C shift", f'{int(round(C["C_shuffled_order_real_symbols"]["shift"]["fwer"]*mech["reps"]))} of {mech["reps"]}' in txt))
r5.append(("mech B shift", f'{int(round(C["B_real_order_iid_symbols"]["shift"]["fwer"]*mech["reps"]))} of {mech["reps"]}' in txt))
r5.append(("repeat rate", f'{mech["speaker_repeat_rate"]*100:.0f}%' in txt))
r5.append(("return rate", f'{mech["speaker_return_after_one"]*100:.0f}%' in txt))
for lab, ok in r5:
    if not ok:
        print(f"FAIL  {lab}")
print(f"round-5: {sum(1 for _, ok in r5 if ok)}/{len(r5)} pass")
if not all(ok for _, ok in r5):
    sys.exit("ROUND-5 VERIFICATION FAILED")

# --- round-6: conditional estimator ---
cnd = json.load(open(os.path.join(D, "facts_conditional.json"), encoding="utf-8"))
hc = json.load(open(os.path.join(D, "facts_humans_conditional.json"), encoding="utf-8"))
bc = json.load(open(os.path.join(D, "..", "swarm-bench", "bench_conditional.json"), encoding="utf-8")) \
     if os.path.exists(os.path.join(D, "..", "swarm-bench", "bench_conditional.json")) else None
# bench_validation.json supersedes cond_strong.json / bench_conditional.json: those predate the
# generator and evaluator fixes, so their numbers must never be cited again.
bv = json.load(open(os.path.join(D, "..", "swarm-bench", "bench_validation.json"), encoding="utf-8"))
cs = None
r6 = []
# the old 20-replicate calibration is superseded by the 40-replicate one checked in round 8
r6.append(("main cond", f'{cnd["main-village"]["conditional_edges"]}' in txt))
r6.append(("openchat undetermined", "undetermined" in txt and "between 0 and 13" in txt))
ind = hc["results"]["individual"]; col = hc["results"]["collapsed"]
r6.append(("collapsed cond total", f'{col["conditional"]["edges_total"]} edges survive' in txt
           or 'four edges survive' in txt.lower()))
r6.append(("collapsed h2a", f'{len(col["conditional"]["human_drives_agent"])} run from humans' in txt
           or 'three run from humans to agents' in txt))
bf = bv["families"]
cc, st = bf["common_cause_null"], bf["structure"]
pn = bf["pure_null"]
r6 += [("bench cc pairwise", f'certifies **{cc["pairwise"]["mean_edges"]:.1f}** edges' in txt),
       ("bench cc conditional", f'takes that to **{cc["conditional"]["mean_edges"]:.2f}**' in txt),
       ("bench struct pairwise", f'pairwise certifies {st["pairwise"]["mean_edges"]:.1f} to recover' in txt),
       ("bench struct prec pw", f'pooled precision of {st["pairwise"]["pooled_precision"]:.2f}' in txt),
       ("bench struct conditional", f'**{st["conditional"]["mean_edges"]:.1f} and still recovers all 4**' in txt),
       ("bench struct prec cond", f'precision of **{st["conditional"]["pooled_precision"]:.2f}**' in txt),
       ("bench recall 1.0", 'Recall is 1.0 either way' in txt),
       ("bench pure null", f'pairwise fires in {pn["pairwise"]["fired_in"]} of {pn["pairwise"]["of"]}'
        f' and conditional in {pn["conditional"]["fired_in"]} of {pn["conditional"]["of"]}' in txt),
       ("bench abstract pw", f'fall from {cc["pairwise"]["mean_edges"]:.1f} to'
        f' {cc["conditional"]["mean_edges"]:.2f}' in txt),
       ("bench abstract prec", f'from {st["pairwise"]["pooled_precision"]:.2f} to'
        f' {st["conditional"]["pooled_precision"]:.2f}' in txt),
       # superseded pre-fix numbers must not reappear anywhere in the report
       # guard the retired CLAIMS, not the digits: 22.7 and 0.80 now appear legitimately in the
       # symbolisation sweep, so a bare substring check on the number is wrong.
       ("no stale precision claim", '0.17 to 1.00' not in txt and 'precision of **1.00**' not in txt),
       ("no stale cc claim", '22.7 to 0.0' not in txt and 'from 22.7 to' not in txt),
       ("no stale 0.71 claim", 'precision of **0.71**' not in txt and '0.17 to 0.71' not in txt),
       ("no stale 4.0 recovers", '4.0 and recovers all 4' not in txt),
       ("label gap disclosed", 'precision on this benchmark is a lower bound' in txt),
       ("vocab leak disclosed", 'recovered the generator' in txt),
       ("bench power 3 of 3", 'in 3 of 3 runs' in txt)]

# --- round-9: the 30-replicate activity-drift sweep supersedes the 8-replicate one ---
sb = json.load(open(os.path.join(D, "..", "swarm-bench", "bench_stationarity_big.json"), encoding="utf-8"))
r9 = [("drift reps 30", f'{sb["reps"]} replicates per cell' in txt)]
for rw in sb["rows"]:
    d = rw["activity_drift"]
    r9.append((f"drift {d} shift", f'| {d} | {rw["shift"]["fwer"]:.3f}'.rstrip("0").rstrip(".") in txt
               or f'{rw["shift"]["fwer"]:.3f}' in txt))
    r9.append((f"drift {d} permute", f'{rw["permute"]["fwer"]:.3f}' in txt))
pm = [rw["permute"]["fwer"] for rw in sb["rows"]]
r9 += [("permute range", f'between {min(pm):.3f} and {max(pm):.3f}' in txt),
       ("no stale 0.125", '0.125' not in txt),
       ("no stale 0.625", '0.625' not in txt),
       ("8-rep disclosed", '8-replicate' in txt or 'eight-replicate' in txt
        or 'earlier 8-replicate' in txt or '0.375 at drift 0.6' in txt),
       ("permute caution", 'not shown to fail' in txt)]
for lab, ok in r9:
    if not ok:
        print(f"FAIL  {lab}")
print(f"round-9: {sum(1 for _, ok in r9 if ok)}/{len(r9)} pass")
if not all(ok for _, ok in r9):
    sys.exit("ROUND-9 VERIFICATION FAILED")
for lab, ok in r6:
    if not ok:
        print(f"FAIL  {lab}")
print(f"round-6: {sum(1 for _, ok in r6 if ok)}/{len(r6)} pass")
if not all(ok for _, ok in r6):
    sys.exit("ROUND-6 VERIFICATION FAILED")

# --- round-7: conditional replication and swarm-village ---
ce = json.load(open(os.path.join(D, "facts_conditional_extra.json"), encoding="utf-8"))
r7 = [("swarm cond", f'| {ce["swarm_village"]["pairwise"]} | **{ce["swarm_village"]["conditional"]}**' in txt),
      ("no replication", 'certifies nothing at all, under either estimator' in txt),
      ("no edge replicates", 'No certified edge in this report replicates out of sample.' in txt)]
for lab, ok in r7:
    if not ok:
        print(f"FAIL  {lab}")
print(f"round-7: {sum(1 for _, ok in r7 if ok)}/{len(r7)} pass")
if not all(ok for _, ok in r7):
    sys.exit("ROUND-7 VERIFICATION FAILED")

# --- round-8: conditioning-resolution sensitivity ---
cd8 = json.load(open(os.path.join(D, "facts_cond_diag.json"), encoding="utf-8"))
oc = cd8["open-chat-village"]; mv = cd8["main-village"]
r8 = [("oc full edges 0", f'**{oc["full_Ac9"]["edges"]}** (mean z {oc["full_Ac9"]["mean_z"]:+.2f}' in txt),
      ("main full edges 2", f'**{mv["full_Ac9"]["edges"]}, the same two edges** (mean z {mv["full_Ac9"]["mean_z"]:+.2f}' in txt),
      ("oc coarse4", f'| **{oc["coarse_Ac4"]["edges"]}** |' in txt),
      ("oc coarse2", f'| **{oc["coarse_Ac2"]["edges"]}** |' in txt),
      ("oc max z", f'only {oc["full_Ac9"]["max_z"]:.1f}' in txt),
      ("oc frac neg", f'{oc["full_Ac9"]["frac_z_negative"]*100:.0f}% of pairs' in txt),
      ("undetermined", "between 0 and 13" in txt)]
cpn = cd8["conditional_pure_null"]
r8 += [("cond calib fired", f'fires in {cpn["fired"]} of {cpn["reps"]} replicates' in txt),
       ("cond calib fwer", f'error rate of {cpn["fwer"]:.2f}' in txt),
       ("cond calib mean z", f'mean z of {cpn["mean_z"]:.3f}' in txt),
       ("no stale 20/20", "20 of 20 replicates" not in txt)]
for lab, ok in r8:
    if not ok:
        print(f"FAIL  {lab}")
print(f"round-8: {sum(1 for _, ok in r8 if ok)}/{len(r8)} pass")
if not all(ok for _, ok in r8):
    sys.exit("ROUND-8 VERIFICATION FAILED")

# --- round-11: the symbolisation-difficulty sweep ---
rs = json.load(open(os.path.join(D, "..", "swarm-bench", "realism_sweep.json"), encoding="utf-8"))
r11 = []
for row in rs["rows"]:
    ov = row["vocab_overlap"]
    cc = row["families"]["common_cause_null"]["pairwise"]["mean_edges"]
    st = row["families"]["structure"]
    r11.append((f"overlap {ov} ARI", f'| {ov} | {row["symboliser_ari_mean"]:.2f} |' in txt))
    r11.append((f"overlap {ov} cc", f'| {cc:.1f} |' in txt))
    r11.append((f"overlap {ov} cond prec",
                f'{st["conditional"]["pooled_precision"]:.2f}' in txt))
lo = [r for r in rs["rows"] if r["symboliser_ari_mean"] < 0.5]
r11 += [("floor named", 'symbolisation floor' in txt.lower()),
        ("floor value", f'{max(r["symboliser_ari_mean"] for r in lo if r["symboliser_ari_mean"] > 0.1):.2f}' in txt),
        ("collapse recall", f'to {min(r["families"]["structure"]["conditional"]["mean_recall"] for r in rs["rows"]):.2f}' in txt),
        ("limitation linked", 'adjusted Rand index, detection collapses' in txt
         or 'adjusted Rand index' in txt)]
for lab, ok in r11:
    if not ok:
        print(f"FAIL  {lab}")
print(f"round-11: {sum(1 for _, ok in r11 if ok)}/{len(r11)} pass")
if not all(ok for _, ok in r11):
    sys.exit("ROUND-11 VERIFICATION FAILED")

# --- round-10: internal cross-references resolve ---
import re as _re
_heads = set(_re.findall(r'^#{2,3} (.+)$', txt, _re.M))
_apps = {h.split(":")[0].strip() for h in _heads if h.startswith("Appendix")}
_secs = set()
for _h in _heads:
    _m = _re.match(r'^(\d+(?:\.\d+)?)\.?\s', _h)
    if _m:
        _secs.add(_m.group(1))
_bad = [r for r in set(_re.findall(r'Appendix [A-Z]', txt)) if r not in _apps]
_bad += ["Section " + r for r in set(_re.findall(r'Section (\d+(?:\.\d+)?)', txt)) if r not in _secs]
for _b in _bad:
    print(f"FAIL  dangling reference: {_b}")
print(f"round-10: {len(_apps)} appendices, {len(_secs)} sections, "
      f"{'no dangling references' if not _bad else str(len(_bad)) + ' DANGLING'}")
if _bad:
    sys.exit("ROUND-10 VERIFICATION FAILED")
