# swarm-sprint — Apart Swarm Alignment Hackathon (6-8 Nov 2026)

**An Agent That Copies Nobody Is Certified as a Leader.** Track 4 (Multi-Agent Oversight and Control):
an audit of information-theoretic influence detection on real AI Village chat, across four villages.

Author: Manu Nicholas Jacob (Independent Researcher). AI coding assistance used and disclosed; the
author is responsible for every claim. No result or reference is fabricated.

## Headline

Applied to real agent chat, the standard recipe for "who drives whom" fails and the failure is
checkable. Clock windows cannot separate a message from its answer (median reply 28.1 s), and at every
width the meaning-free hash null certifies as many edges as the topic symboliser. The turn-ordered
representation that fixes this (one message = one tick) **invalidates the conventional circular-shift
surrogate**, because exactly one agent is non-silent per tick and shifting destroys that.

- An agent coupled to **nothing** is certified as a driver in **8 of 8** runs, z up to **71.7**.
- On structure-free data the shift surrogate's family-wise error rate is **0.90** (nominal 0.05).
- A **symbol-permutation surrogate** restores it to **0.10** [0.03, 0.26].
- Re-certified: main-village **11 -> 2 edges, none shared**; open-chat **3 -> 18** (the bad surrogate
  masks as well as manufactures).
- Power: a median-volume follower copying 80% of the time is detected **1 of 4**; at 800 messages, 4 of 4.
- Surviving: ~1/3 of open-chat's edges replicate across windows; **4 human-to-agent edges, 0 the other way**.

This independently rediscovers a known event-based result (Shorten et al. 2021) that multi-agent safety
practice has not imported.

## Preexisting vs new (this matters for judging)

**Preexisting, declared** — `C:\dev\swarm-prep` (commit `b90ca01`), untouched this weekend:
`swarm_te.py` (lag-1 TE, circular-shift surrogate, max-T) and `swarm_load.py` (reader, Topic/Hash
symbolisers), both validated pre-sprint on synthetic chat. That validation used a representation in
which several agents speak per window, where the shift surrogate IS valid; the invalidity reported
here arises only on the turn-ordered grid introduced this weekend.

**New this weekend (everything here):** window/agent selection on real data; the reply-latency
justification; the turn-ordered representation; the symbol-permutation surrogate (`fastte.py`);
planted positive and negative controls; the calibration measurement; replication and sensitivity;
four-village comparison; human-node analysis; trivial-baseline comparison; all figures; and a
vectorised reimplementation of the preexisting estimator verified bit-for-bit against it.

## Layout

| file | what |
|---|---|
| `swarmlib.py` | shared pipeline (load, window, symbolise, turn-grid, certify) |
| `fastte.py` | vectorised estimator + **the permutation surrogate**; `python fastte.py` proves equivalence |
| `r2_clock.py` | clock-window failure + reply latency |
| `r2_sparse.py`, `r2_final.py` | negative controls, re-certification, power |
| `r2_calib.py`, `r2_calib2.py` | family-wise error rate of each surrogate |
| `r2_recompute.py` | villages + humans under the valid surrogate |
| `r2_openchat.py` | replication/split-half/k in the well-powered channel |
| `r2_qual.py` | topic terms + trivial-baseline comparison |
| `figures_r2.py` | the four figures, all values read from `facts_*.json` |
| `report/` | `REPORT_V2.md`, template, build + footnote scripts, `verify_v2.py` |

## Reproduce

```
python -X utf8 fastte.py            # fast estimator == preexisting estimator
python -X utf8 r2_clock.py          # -> facts_clock.json
python -X utf8 r2_final.py          # -> facts_final.json   (re-certification + power)
python -X utf8 r2_calib.py          # -> facts_calib.json   (error rate of each surrogate)
python -X utf8 r2_recompute.py      # -> facts_recompute.json
python -X utf8 figures_r2.py        # -> f1..f4 png
python -X utf8 report/verify_v2.py  # 71/71 numeric claims checked against the analysis
```

Data: `aidigestorg/ai-village` (gated, research terms). Needs `hf auth login` once. Pull each table as a
single file via `hf_hub_download`; do NOT use the HF-repo path of `load_rows` for one table, because it
reads the whole cached snapshot directory and co-mingles tables.
