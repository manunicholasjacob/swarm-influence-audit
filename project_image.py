"""Project image for the submission form: the one number that carries the paper."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = r"C:\dev\swarm-sprint"
cal = json.load(open(os.path.join(D, "facts_calib.json"), encoding="utf-8"))
cal2 = json.load(open(os.path.join(D, "facts_calib2.json"), encoding="utf-8"))
fin = json.load(open(os.path.join(D, "facts_final.json"), encoding="utf-8"))
sp = json.load(open(os.path.join(D, "facts_sparse.json"), encoding="utf-8"))

shift_fwer = cal["rows"]["shift"]["familywise_error_rate"]
perm_fwer = cal2["fwer"]
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

ax = fig.add_axes([0.09, 0.17, 0.40, 0.52])
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
ax.set_title("Error rate when there is nothing to find", fontsize=14, pad=12)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

bx = fig.add_axes([0.58, 0.17, 0.35, 0.52])
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

fig.text(0.5, 0.055,
         f"A planted agent coupled to nothing reaches z = {worst_z:.0f}.   "
         "Four villages, 250k messages.   Manu Nicholas Jacob, Apart Swarm Alignment Hackathon 2026",
         ha="center", fontsize=11.5, color="#6B7280")
fig.savefig(os.path.join(D, "project_image.png"), dpi=100, facecolor="white")
print("wrote project_image.png")
