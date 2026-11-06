"""Figures for the report. Every number is read from facts.json / results.npz (no hand-typed values)."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

plt.rcParams.update({"font.size": 10, "font.family": "DejaVu Sans", "svg.fonttype": "none"})
facts = json.load(open(r"C:\dev\swarm-sprint\facts.json", encoding="utf-8"))
R = np.load(r"C:\dev\swarm-sprint\results.npz", allow_pickle=True)

FAM = [("Gemini", "#4285F4"), ("GLM", "#8E44AD"), ("GPT", "#10A37F"), ("o1", "#10A37F"),
       ("o3", "#10A37F"), ("Claude", "#D97706"), ("Opus", "#D97706"), ("Haiku", "#D97706"),
       ("Sonnet", "#D97706"), ("Fable", "#D97706"), ("Grok", "#111827"), ("DeepSeek", "#2563EB"),
       ("Kimi", "#DC2626"), ("Muse", "#0EA5E9")]
def color(lbl):
    for k, c in FAM:
        if k in lbl:
            return c
    return "#6B7280"

# ---------- Figure 1: why clock windows fail (the lag bind) ----------
w = R["clock_w"]; occ = R["clock_occ"]; et = R["clock_topic"]; eh = R["clock_hash"]
fig, ax1 = plt.subplots(figsize=(6.6, 3.5))
x = np.arange(len(w))
ax1.bar(x - 0.18, et, 0.36, label="topic symboliser", color="#2563EB")
ax1.bar(x + 0.18, eh, 0.36, label="hash null", color="#9CA3AF")
ax1.set_xticks(x); ax1.set_xticklabels([f"{int(v)} min" for v in w])
ax1.set_xlabel("clock-window width"); ax1.set_ylabel("significant directed edges (FWER 0.05)")
ax1.legend(loc="upper left", fontsize=8, frameon=False)
ax2 = ax1.twinx()
ax2.plot(x, occ * 100, "o-", color="#DC2626", lw=1.8, label="cell occupancy")
ax2.set_ylabel("non-silent agent-windows (%)", color="#DC2626")
ax2.tick_params(axis="y", labelcolor="#DC2626"); ax2.set_ylim(0, max(occ * 100) * 1.4)
for xi, o in zip(x, occ):
    ax2.annotate(f"{o*100:.1f}%", (xi, o*100), textcoords="offset points", xytext=(0, 6),
                 fontsize=7.5, color="#DC2626", ha="center")
ax1.set_title("Clock-window transfer entropy: edges are unstable and barely clear the hash null", fontsize=9)
fig.tight_layout(); fig.savefig(r"C:\dev\swarm-sprint\fig1_lagbind.png", dpi=200); plt.close(fig)

# ---------- Figure 2: turn-ordered influence graph ----------
edges = facts["headline"]["topic"]["sig_edges"]            # [src, dst, p, te]
labels = list(R["te_labels"])
nodes = labels
n = len(nodes)
ang = np.linspace(0, 2*np.pi, n, endpoint=False) + np.pi/2
pos = {nd: (np.cos(a), np.sin(a)) for nd, a in zip(nodes, ang)}
indeg = {nd: 0 for nd in nodes}; outdeg = {nd: 0 for nd in nodes}
for s, d, p, te in edges:
    outdeg[s] += 1; indeg[d] += 1
fig, ax = plt.subplots(figsize=(6.6, 5.2))
for s, d, p, te in edges:
    x0, y0 = pos[s]; x1, y1 = pos[d]
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), connectionstyle="arc3,rad=0.12",
                 arrowstyle="-|>", mutation_scale=14, lw=1.1 + 60*te, color="#374151", alpha=0.75,
                 shrinkA=16, shrinkB=16))
for nd in nodes:
    x0, y0 = pos[nd]
    net = outdeg[nd] - indeg[nd]
    size = 300 + 230*(outdeg[nd] + indeg[nd])
    ax.scatter([x0], [y0], s=size, color=color(nd), edgecolor="white", zorder=3, linewidth=1.5)
    lx = x0*1.2; ly = y0*1.2 - (0.09 if y0 < -0.85 else 0.0)
    ax.text(lx, ly, nd, ha="center" if abs(x0) < 0.35 else ("left" if x0 > 0 else "right"),
            va="center", fontsize=7.4)
ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.45, 1.45); ax.axis("off"); ax.set_aspect("equal")
ne = len(edges); nh = facts["headline"]["hash"]["n_sig_edges"]
ax.set_title(f"Directed topical reply-influence in #general (turn-ordered lag-1 TE)\n"
             f"{ne} FWER-significant edges under topics vs {nh} under the hash null; node size = degree, "
             f"edge width ∝ TE", fontsize=8.6)
fig.tight_layout(); fig.savefig(r"C:\dev\swarm-sprint\fig2_graph.png", dpi=200); plt.close(fig)

# ---------- Figure 3: monitor sweep ----------
fr = R["fractions"]*100; rec = R["recall"]; rsd = R["recall_sd"]; prec = R["precision"]; rho = R["net_spearman"]
fig, ax = plt.subplots(figsize=(6.6, 3.6))
ax.fill_between(fr, np.clip(rec-rsd, 0, 1), np.clip(rec+rsd, 0, 1), color="#2563EB", alpha=0.15)
ax.plot(fr, rec, "o-", color="#2563EB", lw=2, label="edge recall (vs full-data edge set)")
ax.plot(fr, prec, "s--", color="#059669", lw=1.6, label="edge precision")
ax.plot(fr, rho, "^:", color="#9333EA", lw=1.4, label="net-influence rank ρ (volume-driven)")
ax.set_xlabel("fraction of #general messages the overseer reads (%)")
ax.set_ylabel("recovery of the full-channel result")
ax.set_ylim(0, 1.05); ax.set_xlim(0, 102); ax.grid(alpha=0.25)
ax.legend(fontsize=7.8, frameon=False, loc="lower right")
ax.set_title("How much of the channel an overseer must read to recover the influence structure", fontsize=9)
fig.tight_layout(); fig.savefig(r"C:\dev\swarm-sprint\fig3_sweep.png", dpi=200); plt.close(fig)
print("wrote fig1_lagbind.png, fig2_graph.png, fig3_sweep.png")
