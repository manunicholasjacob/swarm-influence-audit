# swarm-influence-audit

**An Agent That Copies Nobody Is Certified as a Leader.** An audit of information-theoretic influence
detection on real multi-agent chat, built for the Apart Research Swarm Alignment Hackathon, 6 to 8
November 2026 (Track 4, Multi-Agent Oversight and Control).

Report: [`report/Apart_Swarm_Report_Manu_Nicholas_Jacob.pdf`](report/Apart_Swarm_Report_Manu_Nicholas_Jacob.pdf).
Benchmark built out of this work: **[swarm-influence-bench](https://github.com/manunicholasjacob/swarm-influence-bench)**.

Author: Manu Nicholas Jacob, Independent Researcher (manunicholasjacob@gmail.com). AI coding
assistance used and disclosed in the report; the author is responsible for every claim. No result or
reference is fabricated.

## What it found

Applied to real agent chat, the standard recipe for "who drives whom" needs **two** repairs before it
says anything.

**1. The surrogate is invalid.** Replies in AI Village's #general arrive a median 28.1 s apart, so no
clock window both holds two speakers and separates a message from its answer. Moving to a
turn-ordered grid (one message = one tick) fixes that but breaks the conventional **circular-shift
surrogate**:

- an agent coupled to **nothing** is certified as a driver in **8 of 8** runs at 100 messages and
  above, with the mean largest z rising 5.6, 12.3, 21.7, 38.3, 71.7 across volumes (3 of 8 at 50);
- on structure-free data its family-wise error rate is **0.90** against a nominal 0.05.

The cause is **the structure of the speaker sequence**, isolated by ablation on the real data:
keeping the real speaker order and shuffling only symbols gives 10/10, randomising the order too
gives **0/10**, uniform symbols with the real order still give 6/10. That sequence is non-random in
two ways at once (speaker repeats 36%, returns-after-one 38%, median block-share CV 0.79), and
shuffling the order destroys both, so this does **not** isolate turn-taking from non-stationarity.
An earlier draft of this work blamed "mutual exclusivity" (one speaker per tick); the benchmark
refuted that, and the claim does not appear in the report.

A **symbol-permutation** surrogate (Shorten, Spinney & Lizier 2021; the fix is theirs, the
demonstration is ours) restores the error rate to **0.063 [0.041, 0.097] over 300 replicates**.

**2. A valid surrogate fixes calibration, not confounding.** Pairwise transfer entropy cannot
separate direct influence from a shared drifting channel topic. Conditioning on the channel's recent
modal topic does, validated on the benchmark (common-cause false edges **22.7 to 0.0**, precision
**0.17 to 1.00**, no power lost from coupling 0.05 to 0.8).

**What survives both repairs, on real channels:**

| channel | shift | permutation | + conditioning |
|---|---|---|---|
| main #general | 11 | 2 | **2** (same two) |
| open-chat #general | 3 | 18 | **0** |
| swarm, room a | 2 | 1 | **0** |

and **no certified edge replicates out of sample** (adjacent window certifies nothing, under either
estimator). Where humans are present, the influence that survives conditioning runs from people to
agents and never back (19 edges to 4: 3 human-to-agent, 1 agent-to-agent, 0 back).

## Preexisting vs new work (this matters for judging)

**Preexisting, declared** — `C:\dev\swarm-prep` (commit `b90ca01`), **untouched** during the sprint:
`swarm_te.py` (lag-1 TE, circular-shift surrogate, max-T test) and `swarm_load.py` (reader, Topic and
Hash symbolisers), both validated pre-sprint on synthetic chat. That validation used a representation
in which several agents speak per window, where the shift surrogate is valid; the invalidity reported
here arises only on the turn-ordered grid introduced during the sprint.

`swarm-prep` is a **private dependency and is not redistributed here**. The MIT licence in this
repository covers this repository's own code only.

**New during the sprint:** window and agent selection on the real data; the reply-latency
justification; the turn-ordered representation; symbolisation of real text; the clock-window failure
analysis; the **symbol-permutation surrogate**; the **ablation isolating the speaker sequence**; the
**conditional estimator and its validation**; **SwarmInfluence-Bench**; the planted positive and
negative controls; the 300-replicate calibration; the replication and sensitivity battery (swarm
size, alphabet, second symboliser, k, fitting corpus); the four-village comparison; the human-node
analysis; the trivial-baseline comparison; all figures; and `fastte.py`, a vectorised
reimplementation of the preexisting estimator verified bit-for-bit against it before use.

## Requirements and layout

Python 3.12+. Dependencies: `numpy`, `matplotlib`, `huggingface_hub`, `pymupdf` (page checks),
`python-docx` (report build only). **No scikit-learn**: the symbolisers are hand-rolled.

```
pip install numpy matplotlib huggingface_hub pymupdf python-docx
```

**Scripts use absolute paths and expect all three repositories side by side:**

```
C:\dev\swarm-prep     preexisting estimator and symbolisers (private)
C:\dev\swarm-sprint   this repository
C:\dev\swarm-bench    the benchmark (report/verify_v2.py reads ../swarm-bench/*.json)
```

On another layout or OS, edit the `sys.path.insert` lines at the top of `swarmlib.py`, `fastte.py`,
`figures_r2.py` and `report/verify_v2.py`.

## Verify every number without dataset access

The dataset is gated, but **every number in the report is checked against the committed
`facts_*.json`**, so this works from a clone alone:

```
python -X utf8 report/verify_v2.py      # 71 numeric claims + 23 assertions across rounds 3-7
```

## Reproduce the analysis (needs dataset access)

```
python -X utf8 fastte.py                 # fast estimator == preexisting estimator, bit for bit
python -X utf8 r2_clock.py               # clock-window failure + reply latency
python -X utf8 r2_final.py               # re-certification + power
python -X utf8 r2_calib.py               # error rate of each surrogate
python -X utf8 r4_calib_big.py           # 300-replicate calibration        (~40 min)
python -X utf8 r5_mechanism.py           # the speaker-sequence ablation    (~11 min)
python -X utf8 r6_conditional_real.py    # conditional estimator, real channels
python -X utf8 r7_humans_conditional.py  # humans under conditioning
python -X utf8 r8_conditional_extra.py   # conditional replication + swarm-village
python -X utf8 r2_recompute.py           # villages + humans under the valid surrogate
python -X utf8 r3_scale.py r3_symboliser.py r3_hashcalib.py   # robustness round
python -X utf8 figures_r2.py             # the figures
```

Other live scripts: `r2_robust.py`, `r2_villages.py`, `r2_humans.py`, `r2_humans_main.py`,
`r2_openchat.py`, `r2_power.py`, `r2_power2.py`, `r4_power_openchat.py`, `r2_budget.py`,
`r2_qual.py`, `r2_sparse.py`, `project_image.py`.

**Superseded round-1 exploration, kept for the record and not used by the report:** `analyze.py`,
`figures.py`, `characterise.py`, `measure.py`, `inspect_data.py`, `inspect_files.py`, `peek_raw.py`,
`r2_recon.py`, `r2_repair.py`, `facts.json`, `results.npz`.

**One documentation trap:** `fastte.channel_context` (3-level) is an early coarse conditioning
variable. The live scripts each define their own `modal_ctx(window=12)`, which is what the report's
method section specifies and what every real-data result uses.

## Data

`aidigestorg/ai-village` on Hugging Face: **gated, access reviewed by hand** under
`ai-village-research-terms` (research use only, no training without permission, no re-identification,
cite AI Digest). Request access on the dataset page, then `hf auth login` once.

No corpus content is redistributed here. Only derived aggregate statistics are committed; the single
corpus-derived strings released are the per-cluster unigram term lists in `facts_qual.json`. Human
participants appear only as `HUMANS` or `visitor-1..3`.

Pull each table as a single file via `hf_hub_download`; do **not** use the HF-repo path of
`load_rows` for one table, because it reads the whole cached snapshot directory and co-mingles tables.

## Citation

> Jacob, M. N. (2026). *An Agent That Copies Nobody Is Certified as a Leader: auditing
> information-theoretic influence detection on real agent swarms.* Apart Research Swarm Alignment
> Hackathon.

## Licence

MIT, see [LICENSE](LICENSE). Covers this repository's code only; see the preexisting-dependency note
above.
