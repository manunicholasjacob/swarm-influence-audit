"""Project image for the submission form: the one number that carries the paper."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = r"C:\dev\swarm-sprint"
cal = json.load(open(os.path.join(D, "facts_calib.json"), encoding="utf-8"))
# 300 replicates, the figure the report headlines. facts_calib2.json is the 30-replicate pilot
# (0.10) and must not be used here: the image would disagree with the paper.
calbig = json.load(open(os.path.join(D, "facts_calib_big.json"), encoding="utf-8"))
fin = json.load(open(os.path.join(D, "facts_final.json"), encoding="utf-8"))
sp = json.load(open(os.path.join(D, "facts_sparse.json"), encoding="utf-8"))
bv = json.load(open(os.path.join(D, "..", "swarm-bench", "bench_validation.json"), encoding="utf-8"))

# Agent messages per village, exactly as the report's Data table states them. Summed here rather
# than rounded by hand: the footer used to claim "250k messages", which was never computed.
VILLAGE_AGENT_MSGS = {"main": 205_726, "open-chat": 35_483, "swarm": 3_848, "game-jam": 838}
total_msgs = sum(VILLAGE_AGENT_MSGS.values())
n_villages = len(VILLAGE_AGENT_MSGS)
st = bv["families"]["structure"]
prec_pw, prec_cd = st["pairwise"]["pooled_precision"], st["conditional"]["pooled_precision"]

shift_fwer = cal["rows"]["shift"]["familywise_error_rate"]
perm_fwer = calbig["fwer"]
hb = fin["headline_by_null"]
n_shift, n_perm = hb["shift"]["topic"]["n_edges"], hb["permute"]["topic"]["n_edges"]
worst_z = max(r["mean_max_z"] for r in sp["rows"])

plt.rcParams.update({"font.family": "DejaVu Sans"})
fig = plt.figure(figsize=(12, 6.75), dpi=100)
fig.patch.set_facecolor("white")

fig.text(0.5, 0.93, "An agent that copies nobody is certified as a leader",
         ha="center", va="top", fontsize=27, fontweight="bold", color="#111827")
fig.text(0.5, 0.845,
         "Information-theoretic influence detection on real AI agent chat is miscalibrated.\n"
         "The standard circular-shift surrogate is invalid once one message is one tick.",
         ha="center", va="top", fontsize=13.5, color="#374151", linespacing=1.5)

ax = fig.add_axes([0.09, 0.215, 0.40, 0.46])
bars = ax.bar([0, 1], [shift_fwer, perm_fwer], width=0.58, color=["#DC2626", "#059669"])
ax.axhline(0.05, color="#6B7280", ls=":", lw=2)
ax.text(-0.42, 0.085, "nominal 0.05", fontsize=11, color="#6B7280", ha="left")
for x, v in zip([0, 1], [shift_fwer, perm_fwer]):
    ax.text(x, v + 0.035, f"{v:.0%}", ha="center", fontsize=21, fontweight="bold",
            color="#111827")
ax.set_xticks([0, 1])
ax.set_xticklabels(["circular shift\n(standard practice)", "symbol permutation\n(the repair)"],
                   fontsize=12.5)
ax.set_ylim(0, 1.12)
ax.set_ylabel("false-positive rate on data\nwith all structure destroyed", fontsize=12)
ax.set_title("Error rate when there is nothing to find", fontsize=14, pad=14)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

bx = fig.add_axes([0.58, 0.215, 0.35, 0.46])
bx.bar([0, 1], [n_shift, n_perm], width=0.58, color=["#DC2626", "#059669"])
for x, v in zip([0, 1], [n_shift, n_perm]):
    bx.text(x, v + 0.35, str(v), ha="center", fontsize=21, fontweight="bold", color="#111827")
bx.set_xticks([0, 1])
bx.set_xticklabels(["circular shift", "symbol permutation"], fontsize=12.5)
bx.set_ylim(0, max(n_shift, n_perm) * 1.3)
bx.set_ylabel("certified influence edges", fontsize=12)
bx.set_title("Same channel, re-certified:\nnone of the 11 survives", fontsize=14, pad=12)
for s in ("top", "right"):
    bx.spines[s].set_visible(False)

fig.text(0.5, 0.105,
         f"A planted agent coupled to nothing reaches z = {worst_z:.0f}.    "
         f"{n_villages} villages, {total_msgs:,} agent messages.",
         ha="center", fontsize=12, color="#6B7280")
fig.text(0.5, 0.062,
         f"Released benchmark with a known influence graph: conditioning on the channel "
         f"lifts precision from {prec_pw:.2f} to {prec_cd:.2f}.",
         ha="center", fontsize=12, color="#6B7280")
fig.text(0.5, 0.018, "Manu Nicholas Jacob, Independent Researcher   |   "
         "Apart Swarm Alignment Hackathon, November 2026",
         ha="center", fontsize=10.5, color="#9CA3AF")
fig.savefig(os.path.join(D, "project_image.png"), dpi=100, facecolor="white")
print("wrote project_image.png")
