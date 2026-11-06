"""Final figures. Every value is read from facts_*.json; nothing is typed by hand."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D = r"C:\dev\swarm-sprint"
plt.rcParams.update({"font.size": 9.5, "font.family": "DejaVu Sans"})
def load(n):
    p = os.path.join(D, n)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None

BLUE, GREY, RED, GREEN, ORANGE = "#2563EB", "#9CA3AF", "#DC2626", "#059669", "#F59E0B"

clock = load("facts_clock.json"); fin = load("facts_final.json")
cal = load("facts_calib.json"); cal2 = load("facts_calib2.json")
sp = load("facts_sparse.json"); rec = load("facts_recompute.json")
pw2 = load("facts_power2.json")

# ---------- FIGURE 1: clock windows cannot work ----------
if clock:
    r = clock["rows"]; w = [x["w_min"] for x in r]; xs = np.arange(len(w))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.0))
    a1.plot(xs, [x["same_window_reply_share"]*100 for x in r], "o-", color=RED, lw=2,
            label="reply lands in the SAME window\n(invisible to a lag-1 test)")
    a1.plot(xs, [x["cell_occupancy"]*100 for x in r], "s--", color=BLUE, lw=1.8,
            label="agent-windows that are non-silent\n(data available to estimate)")
    a1.set_xticks(xs); a1.set_xticklabels([f"{v:g}" for v in w])
    a1.set_xlabel("clock-window width (minutes)"); a1.set_ylabel("percent")
    a1.legend(fontsize=6.4, frameon=False, loc="center left"); a1.grid(alpha=0.25)
    a1.set_title("(a) No width is both estimable\nand causally separating", fontsize=8.5)
    a2.bar(xs-0.18, [x["edges_topic"] for x in r], 0.36, color=BLUE, label="topic symboliser")
    a2.bar(xs+0.18, [x["edges_hash"] for x in r], 0.36, color=GREY, label="hash null (no meaning)")
    a2.set_xticks(xs); a2.set_xticklabels([f"{v:g}" for v in w])
    a2.set_xlabel("clock-window width (minutes)"); a2.set_ylabel("certified directed edges")
    a2.legend(fontsize=7, frameon=False)
    a2.set_title("(b) Whatever clock windows find,\nthe meaning-free null finds too", fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(D, "f1_clock.png"), dpi=200); plt.close(fig)
    print("wrote f1_clock.png")

# ---------- FIGURE 2: the surrogate is invalid; the repair is calibrated ----------
if sp and fin and cal:
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(7.4, 2.9))
    vols = [r["volume"] for r in sp["rows"]]
    a1.plot(vols, [r["false_edge_rate"] for r in sp["rows"]], "o-", color=RED, lw=2,
            label="circular shift")
    fv = {r["volume"]: r for r in fin["false_positive_by_null"]["rows"]}
    if fv:
        xs2 = sorted(fv)
        a1.plot(xs2, [fv[v]["permute"]["rate"] for v in xs2], "s-", color=GREEN, lw=2,
                label="symbol permutation")
    a1.axhline(0.05, color=GREY, ls=":", lw=1)
    a1.set_xscale("log"); a1.set_ylim(-0.05, 1.1)
    a1.set_xlabel("messages by an agent\ncoupled to NOTHING")
    a1.set_ylabel("runs certifying it as a driver")
    a1.legend(fontsize=6.6, frameon=False, loc="center right")
    a1.set_title("(a) A null agent is certified,\nand worse the more it speaks", fontsize=8)

    fw = [cal["rows"]["shift"]["familywise_error_rate"],
          cal2["fwer"] if cal2 else cal["rows"]["permute"]["familywise_error_rate"]]
    a2.bar([0, 1], fw, color=[RED, GREEN], width=0.6)
    if cal2:
        lo_, hi_ = cal2["wilson95"]
        a2.errorbar([1], [cal2["fwer"]], yerr=[[cal2["fwer"]-lo_], [hi_-cal2["fwer"]]],
                    fmt="none", ecolor="#111827", capsize=4, lw=1.2)
    for i, v in enumerate(fw):
        a2.text(i, v + 0.04, f"{v:.0%}", ha="center", fontsize=8.5)
    a2.axhline(0.05, color=GREY, ls=":", lw=1.2)
    a2.text(-0.42, 0.075, "nominal 5%", fontsize=6.5, color=GREY, ha="left")
    a2.set_xticks([0, 1]); a2.set_xticklabels(["circular\nshift", "symbol\npermutation"], fontsize=7.5)
    a2.set_ylim(0, 1.12); a2.set_ylabel("family-wise error rate")
    a2.set_title("(b) Error rate with all\nstructure destroyed", fontsize=8)

    hb = fin["headline_by_null"]
    t = [hb["shift"]["topic"]["n_edges"], hb["permute"]["topic"]["n_edges"]]
    h = [hb["shift"]["hash"]["n_edges"], hb["permute"]["hash"]["n_edges"]]
    a3.bar(np.arange(2)-0.18, t, 0.36, color=BLUE, label="topic")
    a3.bar(np.arange(2)+0.18, h, 0.36, color=GREY, label="hash null")
    a3.set_xticks([0, 1]); a3.set_xticklabels(["circular\nshift", "symbol\npermutation"], fontsize=7.5)
    a3.set_ylabel("certified edges, main #general")
    a3.legend(fontsize=7, frameon=False)
    a3.set_title(f"(c) {hb['n_survive_both_topic']} of the {t[0]} shift-certified\nedges survive the repair",
                 fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(D, "f2_null.png"), dpi=200); plt.close(fig)
    print("wrote f2_null.png")

# ---------- FIGURE 3: what a valid test says about each channel, and about humans ----------
if rec:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 3.0))
    vs = rec["villages"]
    labs = [v["village"].replace("-village", "") for v in vs]
    xs = np.arange(len(vs))
    a1.bar(xs-0.18, [v["shift"]["edges_topic"] for v in vs], 0.36, color=RED,
           label="circular shift (invalid here)")
    a1.bar(xs+0.18, [v["permute"]["edges_topic"] for v in vs], 0.36, color=GREEN,
           label="symbol permutation")
    for i, v in enumerate(vs):
        a1.annotate(f"{v['window_msgs']:,}\nmsgs", (i, 0), textcoords="offset points",
                    xytext=(0, -30), ha="center", fontsize=6.3, color=GREY)
    a1.set_xticks(xs); a1.set_xticklabels(labs, fontsize=8)
    a1.set_ylabel("certified directed edges")
    a1.legend(fontsize=6.8, frameon=False)
    a1.set_title("(a) The invalid surrogate inflates one\nchannel and masks another", fontsize=8.5)

    h = rec["humans_open_chat"]; ind = h["individual"]["permute"]
    aa, h2a, a2h = ind["agent_agent"], len(ind["human_drives_agent"]), len(ind["agent_drives_human"])
    a2.bar([0], [h["agents_only"]["permute"]], 0.5, color=GREY, label="agent -> agent")
    a2.bar([1], [aa], 0.5, color=GREY)
    a2.bar([1], [h2a], 0.5, bottom=[aa], color=RED, label="human -> agent")
    a2.bar([1], [a2h], 0.5, bottom=[aa+h2a], color=BLUE, label="agent -> human")
    a2.set_xticks([0, 1])
    a2.set_xticklabels(["agents only", "+ 3 individual\nvisitors"], fontsize=7.5)
    a2.set_ylabel("certified directed edges")
    a2.legend(fontsize=7, frameon=False)
    a2.set_title(f"(b) open-chat ({h['human_share']:.0%} human):\n"
                 f"{h2a} human->agent, {a2h} agent->human", fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(D, "f3_channels.png"), dpi=200); plt.close(fig)
    print("wrote f3_channels.png")

# ---------- FIGURE 4: power under the valid surrogate ----------
if fin and "power_permute" in fin:
    fig, axes = plt.subplots(1, 2 if pw2 else 1, figsize=(7.2 if pw2 else 4.0, 2.9))
    axes = np.atleast_1d(axes)
    P = fin["power_permute"]
    cs = [r["coupling"] for r in P["rows"]]; rt = [r["rate"] for r in P["rows"]]
    axes[0].plot(cs, rt, "o-", color=BLUE, lw=2)
    axes[0].set_ylim(-0.05, 1.05); axes[0].grid(alpha=0.25)
    axes[0].set_xlabel("fraction of the follower's messages\nthat copy the leader")
    axes[0].set_ylabel("runs detecting the planted edge")
    axes[0].set_title(f"(a) Follower at the median volume\n({P['n_synth']} messages)", fontsize=8.5)
    if pw2:
        vs = [r["synth_volume"] for r in pw2["rows"]]; rs = [r["rate"] for r in pw2["rows"]]
        axes[1].plot(vs, rs, "s-", color=GREEN, lw=2)
        axes[1].set_ylim(-0.05, 1.05); axes[1].grid(alpha=0.25)
        axes[1].set_xlabel("messages posted by the follower")
        axes[1].set_ylabel("runs detecting the planted edge")
        axes[1].set_title(f"(b) Strong coupling (c={pw2['coupling']}),\nvarying how much it speaks",
                          fontsize=8.5)
    fig.tight_layout(); fig.savefig(os.path.join(D, "f4_power.png"), dpi=200); plt.close(fig)
    print("wrote f4_power.png")
