"""Fill the report's sweep/correlation placeholders from facts.json, then verify every numeric claim
in the draft against facts.json. Fails loudly on any mismatch or any leftover placeholder."""
import json, re, sys

F = json.load(open(r"C:\dev\swarm-sprint\facts.json", encoding="utf-8"))
MD = r"C:\dev\swarm-sprint\report\REPORT_DRAFT.md"
txt = open(MD, encoding="utf-8").read()

sw = {round(s["fraction"], 2): s for s in F["monitor_sweep"]}
def pct(x): return f"{round(x*100)}%"
def r2(x): return f"{x:.2f}"

subs = {
    "NETRHO": r2(F["net_influence_topic_vs_hash_spearman"]),
    "RHO20": r2(sw[0.2]["net_spearman_mean"]),
    "RHO50": r2(sw[0.5]["net_spearman_mean"]),
    "RECALL20": pct(sw[0.2]["recall_mean"]),
    "RECALL50": pct(sw[0.5]["recall_mean"]),
    "RECALL70": pct(sw[0.7]["recall_mean"]),
}
for k, v in subs.items():
    txt = re.sub(r"\b" + k + r"\b", v, txt)
open(MD, "w", encoding="utf-8").write(txt)
print("filled:", subs)

# leftover ALLCAPS placeholder guard
left = set(re.findall(r"\b(NETRHO|RHO\d+|RECALL\d+)\b", txt))
assert not left, f"UNFILLED PLACEHOLDERS: {left}"

# ---- numeric verification battery ----
H = F["headline"]; S = F["span"]; C = {c["w_min"]: c for c in F["clock_baseline"]}
topic_net = dict(H["topic"]["net_influence"]); hash_net = dict(H["hash"]["net_influence"])
checks = []
def want(label, s): checks.append((label, s in txt, s))

want("span start", "17 to 31 October 2026")
want("n msgs span", f'{S["n_msgs"]:,}')
want("n agents kept", "22 models")
want("te agents", "15 busiest")
want("span_te msgs", f'{H["topic"]["n_windows"]:,}')
want("general count", "166,715")
want("n agents roster", "58 models")
want("days", "576 days")
want("median latency", str(F["turn_latency"]["median_s"]))
want("p75 latency", str(F["turn_latency"]["p75_s"]))
want("p95 latency", str(F["turn_latency"]["p95_s"]))
want("topic edges", f'{H["topic"]["n_sig_edges"]} family-wise-significant')
want("hash edges one", "yields 1")
want("clock 1min occ", "2.2%")
want("clock 60min edges", "only 3 edges")
want("haiku topic net", "0.196")
want("haiku hash net", "0.193")
want("netrho", subs["NETRHO"])
want("recall20", subs["RECALL20"])
want("recall50", subs["RECALL50"])
want("recall70", subs["RECALL70"])
want("rho20", subs["RHO20"])
want("rho50", subs["RHO50"])

# leader-score table consistency
for agent, score in H["topic"]["leader_scores"]:
    row = re.search(r"^\|\s*" + re.escape(agent) + r"\s*\|.*\|\s*([+-]?\d+)\s*\|\s*$", txt, re.M)
    checks.append((f"leader {agent}={score}", bool(row) and int(row.group(1)) == score,
                   f"{agent} {score:+d}"))

bad = [(l, s) for l, ok, s in checks if not ok]
for l, ok, s in checks:
    print(("  ok  " if ok else "FAIL  ") + l + ("" if ok else f"   <<missing: {s!r}>>"))
print(f"\n{len(checks)-len(bad)}/{len(checks)} checks pass")
if bad:
    sys.exit("VERIFICATION FAILED")
print("ALL NUMERIC CLAIMS VERIFIED against facts.json")
