"""Project image for the submission form: the one number that carries the paper.

Writes project_image.png and, beside it, project_image_claims.json: every string the figure
draws, plus the facts behind them. The sidecar exists because this file was the only artifact
nothing verified, and it drifted. report/check_image.py reads it. Pass an output directory as
argv[1] to write somewhere other than this repository; inputs always resolve from here.
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Resolved from this file, never hardcoded. report/verify_v2.py pinned an absolute path and so
# kept reporting on one working copy no matter where it was run from; a generator with the same
# bug silently writes the image from someone else's numbers.
D = os.path.dirname(os.path.abspath(__file__))
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
# The largest of the per-volume MEANS of each run's largest z, not a single observed z. The name
# matters: this was called worst_z and printed as "reaches z = 72", which reads as one agent
# hitting 72. The report says "the mean largest z rising ... to 71.7" and the caption must not
# claim more than that. The same conflation got into an outreach draft once already.
peak_mean_max_z = max(r["mean_max_z"] for r in sp["rows"])
n_seeds = sp["seeds"]

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
         f"A planted agent coupled to nothing reaches a mean largest z of "
         f"{peak_mean_max_z:.0f} over {n_seeds} runs.    "
         f"{n_villages} villages, {total_msgs:,} agent messages.",
         ha="center", fontsize=12, color="#6B7280")
fig.text(0.5, 0.062,
         f"Released benchmark with a known influence graph: conditioning on the channel "
         f"lifts precision from {prec_pw:.2f} to {prec_cd:.2f}.",
         ha="center", fontsize=12, color="#6B7280")
fig.text(0.5, 0.018, "Manu Nicholas Jacob, Independent Researcher   |   "
         "Apart Swarm Alignment Hackathon, November 2026",
         ha="center", fontsize=10.5, color="#9CA3AF")
OUT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else D
fig.savefig(os.path.join(OUT, "project_image.png"), dpi=100, facecolor="white")


def _texts(f):
    """Every string the figure draws, in no particular order.

    A PNG cannot be read back, so the only way to check what the image claims is to record what
    was drawn. Axis tick labels are included: "circular shift (standard practice)" is a claim
    about what the field does, and it belongs under the same guard as the numbers.
    """
    out = [t.get_text() for t in f.texts]
    for a in f.axes:
        out += [a.get_title(), a.get_xlabel(), a.get_ylabel()]
        out += [t.get_text() for t in a.texts]
        out += [t.get_text() for t in a.get_xticklabels() + a.get_yticklabels()]
    return [s for s in (x.strip() for x in out) if s]


json.dump(
    {
        "drawn_text": sorted(_texts(fig)),
        # The facts, named as what they are, so check_image.py compares against the analysis
        # output rather than against a number retyped into a caption.
        "facts": {
            "shift_fwer": shift_fwer,
            "perm_fwer": perm_fwer,
            "n_edges_shift": n_shift,
            "n_edges_permute": n_perm,
            "peak_mean_max_z": peak_mean_max_z,
            "n_seeds": n_seeds,
            "n_villages": n_villages,
            "total_agent_msgs": total_msgs,
            "precision_pairwise": prec_pw,
            "precision_conditional": prec_cd,
        },
    },
    open(os.path.join(OUT, "project_image_claims.json"), "w", encoding="utf-8"),
    indent=2,
    sort_keys=True,
)
print(f"wrote project_image.png and project_image_claims.json to {OUT}")
