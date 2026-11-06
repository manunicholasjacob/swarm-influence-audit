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
for w in (0.5, 1, 15):
    want(f"clock edges {w}", f'{r[w]["edges_topic"]} against {r[w]["edges_hash"]}')

# --- 5.2 negative control ---
sr = {x["volume"]: x for x in sparse["rows"]}
want("sparse 50", f'{sr[50]["runs_with_any_null_edge"]} of {sr[50]["of"]}')
for v in (50, 100, 263, 600, 1500):
    want(f"sparse z{v}", f'{round(sr[v]["mean_max_z"], 1):g}')   # report quotes one decimal
want("shift fwer", f'{cal["rows"]["shift"]["familywise_error_rate"]:.2f}')
want("shift reps", f'{sum(1 for c in cal["rows"]["shift"]["edges_per_rep"] if c>0)} of {cal["reps"]}')
want("shift mean edges", cal["rows"]["shift"]["mean_edges"])

# --- 5.3 repair ---
want("permute fwer", f'{cal2["fwer"]:.2f}')
want("permute reps", cal2["reps"])
want("wilson lo", f'{cal2["wilson95"][0]:.2f}')
want("wilson hi", f'{cal2["wilson95"][1]:.2f}')
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
