# The extended paper

Target **TMLR**. No APC, no page limit, and it takes careful negative-plus-method results.
**Double-blind**: the submitted PDF carries no author names, no "our earlier preprint", and no
repository URLs. **arXiv preprint first**, which TMLR permits because a preprint is not an archival
venue.

**The prose itself is now drafted: `00_PROSE_v1.md`.** Eleven sections written 9 Nov, with every
quoted figure verified against the committed JSONs by `verify_prose.py` and a change log recording
all 29 corrections. **One thing in it still needs action:** every `[ANON]` marker must be resolved
before a double-blind submission. The 200-draw factorial has landed, so nothing is provisional.

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
| 5 | The repair, compared | report 5.2 + `surrogate_variants.json` | **Unblocked 9 Nov.** The variant comparison is done and says no repair beats another; the section must now argue the choice on grounds other than error rate |
| 6 | Continuous time | new | **Done, 7 Nov, and the answer is neither of the two expected ones.** See `06_continuous_time.md` |
| 7 | Confounding | report 5.4 | Written |
| 8 | The symbolisation floor | report Appendix E + floor proxy | **Rewritten 7 Nov, corrected 9 Nov.** See `08_symbolisation_floor.md`: the contradiction resolved against the proxy, three claims withdrawn, and the proxy recommendation now rests on a measured transportability test rather than on error count |
| 9 | The benchmark | report Appendix E | Written. Promote to a section; it is a contribution |
| 10 | Real channels | report 5.3, 5.5, 5.6 | Written. **Demote**: the real-data result is weak and should look it |
| 11 | Controls | report 6 | Written. Six controls, the practical payload |

## What is new since the sprint, and where it lives

| Result | Artifact | Headline |
|---|---|---|
| Turn-taking separated from non-stationarity | `../../swarm-bench/turntaking_factorial.json` | Turn-taking **suppresses** the failure; drift is the only inflating factor; neither reaches the real 0.90 |
| Permutation surrogate, at precision | `../../swarm-bench/turntaking_factorial.json` and `_200.json` | **0.0679 [0.0585, 0.0787]** over 2,400 instances at **200 draws**, still excluding nominal, flat across all cells. The 100-draw version of this row read 0.0942; paired, the difference is McNemar **p = 2.7e-10**. The claim survives, the number moved by a third, so quote the draw count |
| Label-free symbolisation-floor proxy | `../../swarm-bench/floor_proxy_sweep.json` | seed stability and LSA agreement each separate the floor with zero errors |
| Real-channel floor verdict | `../../swarm-bench/floor_proxy_real.json` | **Contradicted by the audit's own edge counts. Not usable yet** |
| Surrogate variants, paired at 300 replicates | `../../swarm-bench/surrogate_variants.json` and `_200.json` | At 200 draws the shift reads 0.033 and the global permutation 0.070, both covering nominal, while block-local and local still marginally exclude it. **The three repairs remain mutually indistinguishable.** The 100-draw version of this row read "all three run 2 to 3x nominal", which was a draw-count artifact |
| Floor proxy cuts, tested out of mechanism | `../../swarm-bench/proxy_transport.json` | **Three** proxies are perfect where they were fitted, not two, so error count cannot choose. Only the two bounded ones keep their cut: Calinski-Harabasz condemns three cells at true ARI **1.000** on corpus size alone |
| Closest prior work | report Appendix J | Papadopoulos and Psannis (2026) measured the same failure in MARL |

## The three things that would finish it

1. ~~**Continuous-time comparison.**~~ **Done. See `06_continuous_time.md`.** The two estimators
   agree that nothing is detectable in event timing, and the audit's edges turn out to live in a
   channel the continuous-time estimator cannot read at all.
2. ~~**The open-chat contradiction.**~~ **Resolved 7 Nov: the proxy was wrong, not the edge counts.**
   The below-floor verdict is an artifact of k=8; at k=4 open-chat gives the highest stability
   reading either channel produces anywhere. Three claims were withdrawn in the process, including
   "below the floor there is no topic signal left", which is false. See `08_symbolisation_floor.md`.
3. ~~**Surrogate variants at 300 replicates.**~~ **Done, 9 Nov 2026.**
   `../../swarm-bench/surrogate_variants.json`, 300 replicates, pure nulls, **all four surrogates
   on identical symbol grids** so this compares nulls rather than datasets.

   | surrogate | FWER | 95% CI | nominal 0.05 |
   |---|---|---|---|
   | circular shift | 0.0433 | [0.025, 0.073] | inside |
   | global permutation (the repair) | 0.1167 | [0.085, 0.158] | **excluded** |
   | block-local permutation | 0.0900 | [0.063, 0.128] | **excluded** |
   | local permutation (Runge) | 0.0967 | [0.068, 0.135] | **excluded** |

   Because the grids are shared the outcomes are paired, so the comparison is an exact McNemar
   test rather than overlapping intervals. **The shift differs from all three repairs**
   (p = 0.0013, 0.0336, 0.0139). **The three repairs are mutually indistinguishable**
   (p = 0.27, 0.38, 0.86): no variant is measurably better than another at this precision, so the
   paper must not rank them.

   **Read this carefully before writing it up.** It does not contradict the headline. These are
   stationary, generated pure nulls, which is the regime where the shift was already known to be
   roughly calibrated; the 0.90 belongs to real turn-ordered chat. What is new, and what the paper
   has to state, is that **all three permutation repairs carry their own inflation of roughly two
   to three times nominal on clean data**, and that choosing between them cannot be justified by
   error rate.

   **DO NOT write this up as contradicting the report's 0.063 without settling one thing first.**
   Three differences separate the two numbers and only the third is interesting:

   - **Population.** `facts_calib_big.json`'s 0.0633 is measured on the structure-destroyed REAL
     channel, 15 agents and 7,958 ticks. This sweep is on generated pure nulls, 12 agents. Not the
     same population.
   - **Surrogate count.** The published figure used **200** draws per test; this sweep used
     **100**. The intervals, [0.0409, 0.0968] published against [0.085, 0.158] here, overlap only
     in a sliver, so the gap is real and needs an explanation that is not hand-waving.
   - **The suspicious coincidence.** `facts_calib.json`, the 10-replicate pilot on the real
     channel, puts the permutation surrogate at **0.1**, which matches this sweep and not the
     300-replicate figure. That is consistent with the inflation being a function of how many
     surrogate draws the max-T null is built from rather than of the data at all.

   **SETTLED 9 Nov 2026: it is the draws.** `../../swarm-bench/surrogate_variants_200.json`, the
   same 300 instances at 200 draws instead of 100, so the comparison is paired.

   | surrogate | 100 draws | 200 draws | McNemar p |
   |---|---|---|---|
   | circular shift | 0.0433 | 0.0333 [0.018, 0.060] | 0.45 |
   | global permutation | **0.1167** | **0.0700 [0.046, 0.105]** | **0.0043** |
   | block-local | 0.0900 | 0.0767 [0.052, 0.112] | 0.39 |
   | local (Runge) | 0.0967 | 0.0800 [0.054, 0.116] | 0.33 |

   **Only the global permutation is draw-sensitive**, and it is strongly so: 18 instances fired at
   100 draws and not at 200, against 4 the other way. At 200 draws its interval **covers nominal
   0.05** and **overlaps the report's published 0.0633 [0.0409, 0.0968]**. So the report's figure
   is corroborated, not contradicted, and the apparent inflation at 100 draws was an artifact of
   too few draws rather than a property of the repair.

   **The practitioner result this buys:** the global within-speaker permutation needs on the order
   of 200 surrogate draws. At 100 it over-fires by roughly a factor of two. The other two variants
   do not improve with draws and still marginally exclude nominal at 200, which is the first thing
   that has distinguished them at all.

   The three repairs remain mutually indistinguishable at 200 draws (p = 0.85, 0.65, 1.00), so
   SLOT 9's instruction not to rank them still stands. What has changed is that only the global
   permutation reaches nominal, which is a reason to prefer it that is about calibration rather
   than provenance.

   **One more comparison moves, and the paper has to carry it.** At 100 draws the shift differed
   from all three repairs. At 200 draws **it no longer differs from the global permutation
   (p = 0.0614)**, while still differing from block-local (p = 0.0294) and from Runge's local
   (p = 0.0201). So on clean stationary data the global repair costs nothing measurable against the
   surrogate this paper attacks. That is a point in the repair's favour, and it is only visible at
   the honest draw count.

   **The drift sweep was repeated at 200 draws too**
   (`../../swarm-bench/stationarity_pinned_200.json`). The headline defence is unchanged and does
   not depend on the draw count: Cochran-Armitage still gives the shift **z = 8.667, p < 1e-15**
   and every repair nothing (**p = 0.51, 0.63, 0.37**). Under drift, three of the four surrogates
   do fire significantly less with the extra draws (shift p = 0.0113, global p = 0.0033, block
   p = 0.0003; local unmoved at p = 0.42), so **quote the 200-draw column**.

   One asymmetry worth not hiding: under drift the **block-local** variant's interval covers
   nominal in 3 of 4 cells where the global repair's covers 1 of 4. They remain pairwise
   indistinguishable, so this is not grounds to switch the recommendation, but the paper should
   not assert that the global repair is the best calibrated under drift.

## Reproducibility

Public, MIT, with `facts_*.json` and a verifier that recomputes every number and fails on a
mismatch. `../verify_all.py` runs ten checks: the numeric verifier, the page cap, a guard over the
project image's own claims, the benchmark suite, **the 65 figures quoted in `00_PROSE_v1.md`**, the
submission pack, the sprint's own submission rules, arXiv source freshness, a guard that no
withdrawn claim is restated in any document, and an ASCII sweep. Zenodo DOI on release.

**Cite the version DOI, not the concept DOI.**

**The reproducibility defect, now measured rather than suspected.** The pinned re-run asked for here
has been done: `../../swarm-bench/stationarity_pinned.json`, reproduction arm, which repeats the
published configuration exactly (drifts 0.0/0.3/0.6/0.9, 30 replicates, 100 draws, generator seed
7000+s, through the original `bench_eval.te_detector` path) and **reports** the agreement rather
than asserting it. It confirms the defect rather than fixing it:

- **1 of 8 cells reproduces the published count exactly.** The rest are off by one or two
  replicates, in both directions.
- **7 of the 8 published rates fall inside the re-run's own 95% interval.** The exception is drift
  0.0 under the permutation null, where the published 1/30 sits just below the re-run's 3/30
  interval [0.035, 0.256]. Nothing in the report depends on that cell.

The generator, the estimator and BLAS threading were ruled out earlier, so it is a library
difference, most likely scikit-learn's k-means inside the symboliser, whose output moves between
versions. **Every sweep now records the environment it ran under**: Python 3.14.6, numpy 2.5.1,
scipy 1.18.0, scikit-learn 1.9.0, OpenBLAS 0.3.33, one BLAS thread per worker.

**The position to take in the paper:** cite rates with intervals, never exact counts, and state the
environment. Recording the environment does not make the old counts reproducible. It means the new
ones can be checked by someone who matches it, and that is the strongest claim available here.

**One trap in reading `turntaking_factorial_200.json`.** It carries a `published_sweep_agreement`
block, inherited from the 100-draw script, which reports `exact match False` against
`bench_stationarity_big.json`. That is **not** a further reproducibility failure: the published
sweep used 100 surrogate draws and this run used 200, so the counts cannot agree and the block is
vacuous here. The meaningful version of that check is the one in `turntaking_factorial.json`, which
does run at 100 draws. Read the 200-draw file's agreement block as not applicable rather than as
negative.
