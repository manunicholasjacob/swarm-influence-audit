# The extended paper

Target **TMLR**. No APC, no page limit, and it takes careful negative-plus-method results.
**Double-blind**: the submitted PDF carries no author names, no "our earlier preprint", and no
repository URLs. **arXiv preprint first**, which TMLR permits because a preprint is not an archival
venue.

This directory holds material written for the paper that does not exist in the sprint report.
Everything else is reused from `../report/REPORT_V2.md`, which is verified and whose numbers are
recomputed from `../facts_*.json` by `../report/verify_v2.py`.

## Status

| # | Section | Source | State |
|---|---|---|---|
| 1 | Introduction | report 1, reframed | Reframe needed: lead with the error rate, not the village |
| 2 | Related work | **`02_related_work.md`** | **Written, 7 Nov.** Six subsections, every citation checked against a primary source |
| 3 | Representation | report 4.1 to 4.2 | Written. Promote: the clock-window failure is a result, not setup |
| 4 | The surrogate failure | report 5.1 + turn-taking factorial | **Unblocked.** Turn-taking and non-stationarity now separated, and the answer inverts the hypothesis |
| 5 | The repair, compared | report 5.2 + variants | Partly written. Needs the variant comparison at 300 replicates |
| 6 | Continuous time | new | **Done, 7 Nov, and the answer is neither of the two expected ones.** See `06_continuous_time.md` |
| 7 | Confounding | report 5.4 | Written |
| 8 | The symbolisation floor | report Appendix E + floor proxy | **Has a result and an open contradiction** |
| 9 | The benchmark | report Appendix E | Written. Promote to a section; it is a contribution |
| 10 | Real channels | report 5.3, 5.5, 5.6 | Written. **Demote**: the real-data result is weak and should look it |
| 11 | Controls | report 6 | Written. Six controls, the practical payload |

## What is new since the sprint, and where it lives

| Result | Artifact | Headline |
|---|---|---|
| Turn-taking separated from non-stationarity | `../../swarm-bench/turntaking_factorial.json` | Turn-taking **suppresses** the failure; drift is the only inflating factor; neither reaches the real 0.90 |
| Permutation surrogate, at precision | same | **0.0942 [0.083, 0.107]**, excludes nominal, flat across all cells |
| Label-free symbolisation-floor proxy | `../../swarm-bench/floor_proxy_sweep.json` | seed stability and LSA agreement each separate the floor with zero errors |
| Real-channel floor verdict | `../../swarm-bench/floor_proxy_real.json` | **Contradicted by the audit's own edge counts. Not usable yet** |
| Closest prior work | report Appendix J | Papadopoulos and Psannis (2026) measured the same failure in MARL |

## The three things that would finish it

1. ~~**Continuous-time comparison.**~~ **Done. See `06_continuous_time.md`.** The two estimators
   agree that nothing is detectable in event timing, and the audit's edges turn out to live in a
   channel the continuous-time estimator cannot read at all.
2. **The open-chat contradiction.** The floor proxy calls open-chat below the floor; open-chat
   certifies 18 and 22 edges against main-village's 2 and 1, with its hash null at 0. A below-floor
   channel should certify near zero and should look like its own meaning-free null. It does neither.
   Until this resolves the open-chat verdict is unusable, and resolving it is probably the most
   interesting single question left here.
3. **Surrogate variants at 300 replicates.** Global within-speaker permutation, block-local
   permutation, and the local permutation of Runge as adapted by Shorten et al., compared at the
   precision the headline already reached. Compute, not research.

## Reproducibility

Public, MIT, with `facts_*.json` and a verifier that recomputes every number and fails on a
mismatch. `../verify_all.py` runs eight checks: the numeric verifier, the page cap, the submission
pack, the benchmark suite, the sprint's own submission rules, arXiv source freshness, a guard that
no withdrawn claim is restated in any document, and an ASCII sweep. Zenodo DOI on release.

**Cite the version DOI, not the concept DOI.**

**One defect to fix before submission:** `../../swarm-bench/bench_stationarity_big.json`'s exact
counts do not reproduce today, off by one or two replicates per cell. The generator, the estimator
and BLAS threading were ruled out, so it is a library or environment difference. Every 200-replicate
rate falls inside the published 30-replicate interval, so no conclusion moves, but the paper must
not cite those counts as reproducible. Re-run the sweep with a pinned environment.
