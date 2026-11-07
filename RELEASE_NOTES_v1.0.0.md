# swarm-influence-audit v1.0.0

An audit of information-theoretic influence detection on real multi-agent chat, plus the analysis
pipeline, the verifier, and everything needed to recompute every number in the report.

**Do not cut this release until the repository is enabled in Zenodo.** The webhook is installed only
when you enable the repository, and the documented flow is enable, then release. Releasing first
means cutting a fresh release later.

## What this is

Produced for Apart Research's Swarm Alignment Hackathon, 6 to 8 November 2026. The report is
`report/Apart_Swarm_Report_Manu_Nicholas_Jacob.pdf`: an 8-page body within the sprint's hard cap,
plus appendices A to I.

## The finding

The standard recipe for "who drives whom" in a multi-agent channel is lagged transfer entropy, a
surrogate null, and a per-agent influence score. On real agent chat it needs two repairs before it
says anything.

- Clock windows cannot separate a message from its answer at the timescale agents reply on (median
  28.1 seconds), and across widths a meaning-free hash null certifies comparably many edges as the
  topic symboliser, more at five minutes.
- The turn-ordered representation that fixes this **breaks the conventional circular-shift
  surrogate**: family-wise error **0.90** against a nominal **0.05**. An agent planted into the real
  stream, coupled to nothing, is certified as a driver in **8 of 8** runs with z reaching **71.7**,
  and the error grows the more it talks.
- The cause is the **structure of the speaker sequence**. Real order with shuffled symbols fires 10
  of 10; randomising the order gives 0 of 10.
- A **symbol-permutation surrogate** restores the error rate to **0.063** over 300 replicates,
  interval 0.041 to 0.097.
- Re-certifying **scrambles rather than shrinks**: one channel loses all 11 of its edges and gains 2
  that were not among them; another goes from 3 to 18.
- Conditioning on the channel separates dyad-specific influence from common cause, and is itself
  nominal: 2 of 40 structure-free replicates, mean z -0.001.
- **A symbolisation floor at adjusted Rand index 0.44**, below which detection collapses regardless
  of estimator. Real LLM text sits at 0.937, above it.
- **Nothing replicates out of sample.** Not one certified edge.

## Five claims were weakened or withdrawn under checking

Each is disclosed in the report rather than quietly dropped, which is the part a reader can most
easily verify.

1. An earlier version's 10 edges failed replication and are superseded.
2. "Mutual exclusivity" as the cause was **refuted by our own benchmark**, which left the shift
   surrogate roughly calibrated at 0.067 with exactly one speaker per tick.
3. "The hash null certifies fewer edges at every width" is false; it certifies comparably many, and
   more at five minutes.
4. "Open-chat's 18 edges all vanish under conditioning" is **retracted** as conditioning-resolution
   degeneracy. Coarsening returns 7, then 13. Open-chat is undetermined.
5. The benchmark numbers were **regenerated** after the benchmark's own audit; the old 22.7, 0.0 and
   precision 1.00 are retired.

## Verification

`report/verify_v2.py` runs twelve rounds: 71 numeric claims recomputed from the `facts_*.json`
analysis outputs, guards that fail the build if any retracted number reappears, a check that every
section and appendix cross-reference resolves, and checks on each sweep.

`report/check_pages.py` asserts the body fits the 8-page cap. It exists because the cap was once
checked by looking at which page the Conclusion heading landed on, which is a different question:
the heading sat on page 8 while the conclusion's last lines spilled onto page 9.

```
python report/verify_v2.py
python report/check_pages.py
```

`report/locked_strings.json` lists the 144 literals the verifier requires, extracted by
instrumenting the verifier rather than by reading it, so the list cannot drift from the checks.

## Also in this release

- `export_event_trains.py` writes both analysed channels as per-agent event trains and emits
  `run_cotete.jl`, so the continuous-time comparison the report says it did not attempt becomes a
  script rather than a project. Julia is not installed here, so it has **not** been run and nothing
  claims otherwise.
- `arxiv/` holds a LaTeX package of the report, regenerable with `report/to_latex.py`.

## Attribution

The transfer-entropy estimator, the circular-shift surrogate, the max-T family-wise test and the
symbolisers are **preexisting**, written before the sprint and declared in Appendix C. New here: the
demonstration of the failure, the symbol-permutation repair applied to this domain, the conditional
estimator, the benchmark, the controls, and the symbolisation floor.

The local permutation scheme is **Runge (2018)**, AISTATS PMLR 84, 938-947, adapted to
continuous-time event data by **Shorten, Spinney and Lizier (2021)**, PLOS Computational Biology
17(4) e1008054. Neither is ours.

## Data

The AI Village corpus (AI Digest, 2026), used under its research terms: research use only, no
training on the data, no re-identification, read-only, with human participants appearing only as
aggregated or anonymised nodes.

**No dataset content is redistributed here.** Only derived aggregate statistics are committed. The
event-train export is gitignored for the same reason: it carries no text and no identities, but
exact per-agent timestamps for every message in the window would be redistribution in substance.

## Companion

The benchmark is a separate citable artifact:
github.com/manunicholasjacob/swarm-influence-bench

MIT.
