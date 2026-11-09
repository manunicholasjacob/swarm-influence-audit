# Paper prose, draft 1

Written by Manu Nicholas Jacob, 9 November 2026, from the slot workbook. Corrections applied the
same day after verifying every quoted figure against the committed JSONs and the section notes in
this directory.

**Every number below has been checked against its source.** The verification found one arithmetic
error (the crossover in SLOT 10), one merged citation (SLOT 4), one arm mislabelling (SLOT 2), and
a set of omissions where the source carried a caveat attached to the exact figure being quoted. The
change log at the end of this file lists every edit.

**Two structural notes before the sections.**

1. **SLOT 12 is not a paper section** and has been moved to the end under its own heading. It is a
   changelog about two articles published under the author's name, so it cannot appear in a
   double-blind submission.
2. **Self-references need anonymising at submission.** Phrases such as "the original report" and
   "the audit" refer to the author's own public work. TMLR permits citing a preprint, but the
   citation must be in third person and must not say it is the author's. Marked `[ANON]` wherever
   it occurs.

---

# SLOT 1: Introduction

Circular-shift surrogates can produce severely inflated false-positive rates when applied to
turn-ordered multi-agent conversations, reaching a family-wise error rate of 0.90 against a nominal
0.05. A generated benchmark separates two candidate mechanisms and points at non-stationary speaker
activity rather than turn-taking, which suppresses the failure rather than causing it. No setting of
either knob reproduces the observed 0.90, however, so what drives the full real-data failure remains
open. Restricted permutation surrogates substantially reduce the problem. Their error rate is flat
with respect to drift rather than at the nominal level, and for the global within-speaker variant it
depends on how many surrogate draws the null is built from. Calibration alone does not address
confounding, which motivates a conditional estimator validated against a benchmark with planted
ground truth. I also identify a symbolisation-dependent detection limit and develop label-free
diagnostics for it, and show that their calibration does not transport across degradation
mechanisms. The benchmark is released. `[ANON: the release link must be anonymised at submission.]`

# SLOT 2: Two explanations that did not hold

> **Provisional.** Every figure in this section comes from a sweep run at 100 surrogate draws. The
> global permutation surrogate is known to over-fire at that setting (SLOT 3), and a 200-draw repeat
> of this factorial is running. Do not submit this section until that lands.

I initially attributed the circular-shift failure to mutual exclusivity: only one agent can speak at
each tick, so shifting individual timelines could create overlaps that never occurred in the
original conversation. The benchmark did not support this explanation. A generated channel with
exactly one speaker per tick and steady activity produced an error rate of just 0.067 at 100
surrogate draws, far below the 0.90 observed in the real data. Mutual exclusivity alone therefore
cannot explain the failure.

I then suspected turn-taking. In the real channel, speakers repeat 36% of the time and return after
exactly one message 38% of the time. However, adding a Markov speaker chain to the generator
produced the opposite result. Turn-taking suppressed the error rather than increasing it. At the
nominal knob values and with no drift the error rate was 0.000, while removing turn-taking and
introducing drift raised it to 0.400. The contribution from drift was +0.345, compared with -0.055
for turn-taking. The same inversion appears in the arm calibrated so that the generated channel
reproduces the real channel's measured repeat, return and block-share statistics rather than merely
carrying those numbers as settings: there, turn-taking alone gives 0.005 and drift alone gives
0.105. Neither mechanism, nor their combination in the tested design, reproduced the real-data error
rate of 0.90. The largest cell anywhere in the design is 0.400. The real-data ablation removes
turn-taking and non-stationarity together, while the generator allows us to separate them. The
results point to non-stationary activity, but the remaining gap means the mechanism behind the full
real-data failure is not yet established.

# SLOT 3: How many surrogate draws are needed?

The number of surrogate draws matters more than I initially appreciated. In the paired comparison of
300 instances, the global permutation surrogate produced a false-positive rate of 0.1167 with 100
draws, falling to 0.0700 with 200 draws (95% Wilson interval [0.046, 0.105]). This difference was
statistically significant (McNemar p = 0.0043). The block-local and Runge local permutations were
less sensitive to the increase: their corresponding rates changed from 0.0900 to 0.0767 and from
0.0967 to 0.0800, respectively.

At 200 draws, the global permutation's interval covers the nominal 0.05 and overlaps the real-data
estimate of 0.0633 [0.0409, 0.0968]. The published real-data result is therefore corroborated rather
than overstated. For practical use, the important point is that reducing the number of surrogate
draws can materially change the result. In particular, the global permutation over-fires at 100
draws by approximately a factor of two. I would therefore not treat the choice of draw count as a
minor computational detail. The factorial estimate of 0.0942 should not be relied upon until its
planned 200-draw rerun is available.

One limit on this recommendation. I compared 100 draws against 200 and did not test any larger
value, so what the experiment establishes is that 100 is too few, not that 200 is enough. Two
hundred is a lower bound on the draw count rather than a converged setting, and a practitioner
whose conclusions sit near a decision boundary should check their own sensitivity rather than adopt
the number.

# SLOT 4: The symbolisation floor

The results also show that the performance of these methods depends on how the original messages are
converted into symbols. On the benchmark, where the underlying topics are known, detection
performance drops sharply when agreement between the symboliser and the ground truth falls below
roughly ARI 0.44. This behaviour appears across the tested estimators. Importantly, the
false-positive rate can actually look better below this point because the shared topic structure
needed to produce confounded detections is no longer represented reliably. A pipeline that stops
detecting relationships may therefore have lost the signal it needs rather than become more
reliable.

We can now detect this degradation without access to ground-truth labels. Across the nine-level
benchmark sweep, three statistics separate the below-floor cases with zero errors: seed stability at
a threshold of 0.623, agreement with LSA at 0.646, and the Calinski-Harabasz index at 138.9. Seed
stability here is the **minimum** pairwise agreement across seeds, not the mean; the mean variant
makes one error, at a different threshold of 0.791. Interestingly, silhouette has the strongest
correlation with true ARI, at 0.979, but is not useful for identifying the boundary because its
threshold falls within a gap of just 0.002. A statistic that tracks clustering quality most closely
is not necessarily the best one for making a classification decision.

Error count cannot choose among the three that were perfect, so I tested whether each threshold
still means what it meant when the channel changes for reasons other than topic separability.
Applying each cut unchanged to thirty cells that vary turn-taking, drift, agent count, volume skew,
message length and corpus size, twenty-seven of which hold true ARI at exactly 1.000:

| proxy | cut | errors where fitted | errors on the nuisance set | of those at true ARI 1.000 |
|---|---|---|---|---|
| seed stability, min across seeds | 0.623 | 0 | 2 | 0 |
| LSA agreement | 0.646 | 0 | 2 | 0 |
| Calinski-Harabasz | 138.9 | 0 | 6 | 3 |

The two bounded statistics err only on the short-message cells, where the symbolisation genuinely
has degraded. Calinski-Harabasz additionally condemns all three cells whose true ARI is exactly
1.000, for no reason beyond the corpus holding 2,000 messages rather than 8,000, where it reads 76
to 77 against its own cut of 138.9. It is unbounded and grows with sample size, so a published
numeric threshold for it carries no meaning on another corpus. That is why I recommend the two
bounded statistics and not the index that matched them on error count. A cut that moves with the
corpus is not a floor cut.

This is not a weak statistic being discarded on a technicality. Calinski-Harabasz correlates with
true ARI at 0.973, almost as closely as silhouette, and unlike silhouette it classifies the floor
perfectly where it was fitted. It still cannot carry a published threshold. That is the sharper form
of the point above: neither the statistic that tracks quality most closely nor the one that
classifies best on the fitting mechanism is necessarily the one whose cut another researcher can
reuse.

There are important limits to this result. The effective sample size is nine, rather than 54,
because the classification label is determined by overlap level. There are no observations between
ARI 0.444 and 0.222, so the exact location of the boundary within that interval remains unknown.
These diagnostics classify whether a result is below the tested detection floor; they do not
estimate ARI, and their behaviour is flat between 0.68 and 1.00, and not even monotone there. The
benchmark also uses a single degradation mechanism with a known and correct value of k, whereas the
true number of topics in real conversations is unknown. I therefore treat 0.44 as a
benchmark-specific, bracketed result rather than a universal threshold.

The underlying idea of using clustering stability as a quality indicator is not new. It has a
substantial history in earlier work, including Ben-Hur et al. (2002), Lange et al. (2004), von
Luxburg's review of clustering stability, and Tibshirani and Walther on prediction strength. What is
different here is the calibration of these diagnostics against a detection-performance floor rather
than against cluster recovery alone.

# SLOT 5: Revisiting the open-chat contradiction

I initially used the label-free diagnostics to classify open-chat as being below the symbolisation
floor. That conclusion did not agree with the channel's measured results: open-chat certified 18 and
22 edges under the two symbolisers, compared with 2 and 1 for main-village. Its hash-based null
certified zero edges. Rather than treating this disagreement as evidence that the original
measurements were wrong, I revisited the diagnostic itself.

The problem was the choice of k. When I repeated the comparison using the same channels, loader and
window, the published k=8 results were reproduced to the digit. However, at k=4, open-chat reached
stability scores of 0.950 and 0.978, the highest values produced by either channel across the tested
settings. Both exceeded the diagnostic thresholds. The earlier below-floor classification was
therefore a conclusion about one arbitrary choice of k, not a reliable statement about the channel.
Message length also does not explain the difference: 27.1% of main-village messages contain fewer
than five tokens, compared with 2.3% in open-chat.

This correction changes how I interpret the symbolisation results. First, the claim that no topic
signal remains below the floor is too strong. The circular-shift surrogate recovers all four planted
edges at every tested overlap level, including 0.95, where ARI is 0.011. The observed collapse is in
the permutation null, not necessarily in the underlying data. Second, ARI 0.44 cannot be treated as
a universal detection threshold. When shared_topic is 0, detection continues down to ARI 0.296,
indicating that the boundary depends on both the symboliser and the channel. Third, edge counts
cannot be used as a direct measure of symboliser quality. Even at ARI exactly 1.000, changing
shared_topic alone moves the permutation count from 5 to 78.

The diagnostics also do not transfer reliably outside the mechanism on which they were evaluated.
Their balanced accuracy falls from 1.00 to 0.75 and 0.571 under the alternative settings. All seven
errors made by seed stability are false below-floor classifications, and in every one of those cases
the detector still identifies all planted edges. Of the fourteen cells it condemned, eleven had full
conditional recall.

This was an important correction to my own interpretation. I introduced a diagnostic to check
whether the symbolisation was reliable, applied it to the real channels, and found that it
contradicted the measurements already in the paper. Investigating that contradiction showed that the
diagnostic was sensitive to an arbitrary modelling choice. The result is not that the original
measurements were necessarily wrong, but that the control was being asked to support a broader
conclusion than the evidence allowed. These diagnostics remain useful within their tested setting,
but their thresholds should not be transferred directly to real conversations.

# SLOT 6: Positioning against prior work

Papadopoulos and Psannis (2026) report a closely related surrogate failure in multi-agent
reinforcement-learning action series. Their agent pairs have zero influence by construction, yet
circular time shifts produce false-positive rates of 100% and 98.2% against a nominal 0.05. A plain
permutation surrogate fares no better in their setting, at 100.00% and 99.95%. Their proposed
correction restricts permutations to blocks of training time, which returns the rates to 5.25% and
5.50%.

There are important differences between their setting and ours. Their data consist of binary actions
recorded over twelve thousand training rounds, whereas our data consist of symbolised
natural-language messages arranged on a turn-ordered conversational grid. Their non-stationarity
comes from monotone drift associated with annealing exploration; in our experiments, the relevant
non-stationarity appears in the speaker sequence. Neither result should be taken as a direct
extension of the other.

Nevertheless, the fact that both approaches rely on restricted permutations is worth noting. Their
permutation blocks are defined by training time, while ours are defined by an agent's own speaking
positions. This provides convergent evidence that unrestricted temporal rearrangement can be
problematic in non-stationary multi-agent data. Their findings also serve as a useful warning for
our own approach, and the warning has a measured form rather than a rhetorical one: in their data
the unrestricted permutation failed as completely as the time shift, at 100.00% against a nominal
0.05. Permutation-based surrogates are not automatically protected against non-stationarity, and
what protects ours is the restriction, not the permutation. We make no priority claim and view the
two studies as complementary results addressing different forms of structured multi-agent data.

# SLOT 7: The timing limitation

An earlier audit of this corpus identified continuous-time estimation as a more principled option
for event data but did not evaluate it. `[ANON]` I have since tested CoTETE on both channels. It
certifies 0 edges in either case, compared with 2 for main-village and 18 for open-chat under that
audit. Its highest z-scores are 3.062 and 3.980, below the respective max-T thresholds of 4.171 and
4.308.

At first, these results might appear to contradict the symbol-based analysis. However, the two
estimators operate on different information. CoTETE's public API uses event times without a symbol
channel, while our transfer-entropy analysis uses topic symbols. To test whether this difference
explains the results, I reduced our own data to timing alone, replacing every spoken symbol with the
same code. Under this representation, our estimator also detects 0 edges in both channels, matching
CoTETE. Using the circular-shift surrogate instead produces 12 and 3 edges.

The agreement indicates that neither method detects relationships from event timing alone in these
channels. The edges identified by the original analysis depend on symbol correspondence, which the
continuous-time estimator cannot access.

Two caveats attach to the z-scores above, and the second attaches to the larger of them. Point
estimates from this estimator are stochastic to about 17% across repeated runs, so none of these
values should be read to more than two significant figures. And open-chat's highest z, the 3.980,
belongs to the one pair whose surrogate draws mostly failed: it needed 1,936 failed draws to obtain
100 successes, a 4.9% success rate. Those surrogates are conditioned on being estimable, so that
pair's null is biased in an unknown direction. The conclusion does not rest on it, since the pair
falls below threshold and so does every other pair, but the number should not be quoted as though it
were a clean measurement.

The failures themselves were a defect rather than a property of the data. CoTETE v0.2.3's
`make_surrogate!` enlarges its exclusion windows, which on sparse bursty event trains can empty the
neighbour search and raise an error that terminates a whole pair, with no handling at the public
entry point. The first campaign lost 5 of 16 shards to it before the surrogate loop was
reimplemented to redraw on failure. This has been reported upstream.

There is also a fundamental limitation in applying the recommended permutation surrogate to
timing-only data. When every event carries the same symbol, permuting those symbols changes nothing.
The observed statistic and the surrogate null are therefore identical, making the test exactly
degenerate: sd = 0 across all 210 pairs and p = 1.0 everywhere. The repair has zero power against
timing structure by construction.

This distinction matters when interpreting the recommendation. The permutation surrogate is
appropriate for testing relationships in the symbol sequence, but it does not answer whether
relationships exist in event timing. These are different questions, and choosing one null means
giving up the ability to test the other with that procedure.

# SLOT 9: Choosing a repair

The comparison of the three permutation-based repairs does not produce a clear winner. I evaluated
all four surrogates on identical symbol grids across 300 pure-null replicates, ensuring that the
comparison reflected differences between the null models rather than differences between datasets.

At 200 surrogate draws, the circular shift has a family-wise error rate of 0.0333, with a 95% Wilson
interval of [0.018, 0.060]. The global within-speaker permutation gives 0.0700 [0.046, 0.105],
block-local permutation gives 0.0767 [0.052, 0.112], and Runge's local permutation gives 0.0800
[0.054, 0.116]. The nominal 0.05 lies within the intervals for the circular shift and global
permutation, but not for the other two repairs.

The paired comparisons add an important qualification. At 200 draws, the circular shift is not
significantly different from the global permutation (p = 0.0614), although it differs from
block-local permutation (p = 0.0294) and Runge's local permutation (p = 0.0201). The three repairs
remain statistically indistinguishable from one another, with pairwise p-values of 0.85, 0.65 and
1.00. The apparent differences in their error rates are therefore not sufficient to establish a
ranking.

Choosing between them requires considering more than calibration. Runge's local permutation has the
strongest methodological justification for preserving the structure it is intended to preserve, and
it follows the approach adapted to event data by Shorten, Spinney and Lizier. Block-local
permutation is more heuristic and introduces a free parameter that has not been tuned. Global
permutation is the simplest option. On the other hand, the global permutation has the most
favourable interval relative to the nominal rate among the three repairs, although that difference
is not statistically established.

I therefore do not consider the observed error rates sufficient to select one repair over the
others. The choice should be guided by the structure the null is intended to preserve and the
assumptions that can be justified for the data. The results do not support claiming that any of the
three repairs performs best.

# SLOT 10: When to use the repair

The drift experiment provides a more practical way to interpret the results. Across 150 replicates
per cell, the circular-shift surrogate's error rate increases steadily as activity drift increases.
At drift levels of 0.0, 0.3, 0.6 and 0.9, its rates are 0.013, 0.100, 0.193 and 0.380, respectively.
The three permutation repairs behave differently: their rates remain relatively stable across the
same conditions.

This pattern is supported by a formal trend test. The circular shift shows a strong increasing trend
across drift levels (Cochran-Armitage z = 8.667, p < 1e-15). None of the permutation repairs shows a
significant trend: p = 0.51 for global permutation, p = 0.63 for block-local permutation and p = 0.37
for Runge's local permutation. The same pattern holds at both surrogate draw counts.

However, the results also show why the repair should not be treated as universally preferable. At
zero drift, the circular shift has an error rate of 0.013, while the three repairs are all around
0.08 to 0.09. That advantage is gone by the first drift step: at drift 0.3 the shift reads 0.100
against the global permutation's 0.100 and block-local's 0.093, so the crossover falls between drift
0.0 and 0.3 rather than at some higher level. By drift 0.6 the shift is roughly four times the
repairs. In other words, the circular shift performs well under stationary activity and loses that
advantage as soon as activity begins to drift at all.

The practical trade-off is therefore straightforward. The permutation repairs provide greater
robustness to changing activity, but this robustness comes with a higher error rate under stationary
conditions. If a channel has been checked and found to be stationary, the circular shift may be
sufficient. When activity is non-stationary, the permutation repairs offer a more stable
alternative, and the margin for error on that judgement is narrow: the crossover arrives by the
first drift level tested. What the repair buys is insensitivity to drift, rather than guaranteed
correctness.

# SLOT 11: Reproducibility limitation

I also found a reproducibility limitation in the stationarity benchmark. When I reran the counts in
`bench_stationarity_big.json` using the same seeds and configuration, only one of the eight cells
reproduced exactly. The remaining differences were small, with each differing by one or two
replicates. Seven of the eight published rates still fell within the recomputed Wilson intervals,
and none of the paper's conclusions changed. The exception is the zero-drift cell under the
permutation null, where the published 1 of 30 falls just below the recomputed interval of [0.035,
0.256] for 3 of 30. No result in this paper depends on that cell.

The generator, estimator and BLAS configuration were investigated and ruled out as the source of the
discrepancy. The most likely explanation is a library-level difference, particularly in
scikit-learn's k-means implementation within the symboliser, whose output can vary between versions.

To make future runs easier to verify, the environment is now recorded alongside each sweep: Python
3.14.6, numpy 2.5.1, scipy 1.18.0 and scikit-learn 1.9.0, including the BLAS build and the number of
BLAS threads each worker ran under.

This does not make the previously published counts exactly reproducible. It provides a more clearly
specified environment in which subsequent results can be checked. For that reason, I report rates
alongside their confidence intervals rather than relying on exact replicate counts. The conclusions
remain unchanged, but the distinction between reproducing a result within its uncertainty and
reproducing every individual count is important.

---

# NOT A PAPER SECTION: the articles and their corrections

**This was SLOT 12 of the workbook. It is a record of what changed in two articles published under
the author's name, and it cannot appear in a double-blind submission.** Keep it as a changelog, in
the workbook or in the article repository, and delete it from any manuscript.

The earlier versions of the Alignment Forum and LessWrong articles included a reassuring
interpretation of the permutation results that the larger experiments do not support. The original
statement was numerically accurate for the 30-replicate sweep it described: the repair produced
rates between 0.033 and 0.167, with three of its four 95% intervals covering the nominal 0.05. The
problem was not that those numbers were incorrect. It was that 30 replicates per cell were
insufficient to establish the level of calibration implied by the wording.

The larger experiment, using 150 replicates per cell and 200 surrogate draws, gives a different
picture. The repair rates across drift levels are 0.093, 0.100, 0.053 and 0.087. Only one of the
four confidence intervals covers the nominal 0.05. The more defensible conclusion is that the repair
remains relatively stable as drift increases, rather than that it is calibrated to the nominal error
rate.

I have updated both articles to reflect this. The drift discussion now uses the 200-draw results and
includes the Cochran-Armitage trend tests. The main point is that the circular shift becomes
increasingly unreliable under drift, while the repair remains comparatively flat. The revised
wording therefore focuses on what the repair actually provides: reduced sensitivity to changing
activity, not guaranteed correctness.

I also added a caveat about surrogate draw counts. In the paired comparison, the global permutation
rate changes from 0.1167 at 100 draws to 0.0700 at 200 draws on the same instances. This is an
important practical detail, because a smaller number of draws can make the method appear
substantially less reliable than it is at the larger setting.

The simulator paragraph in the second article has also been corrected. The earlier values of 0.067
and 0.367 have been replaced with 0.013 and 0.380, reflecting the more recent drift sweep. I added a
sentence after the 0.063 real-data result to make clear that practitioners should not economise on
surrogate draws.

I deliberately did not add the factorial experiment's turn-taking result to the articles. The
earlier wording has been narrowed to describe what the real-data ablation establishes, without
claiming that it separates turn-taking from non-stationarity. The factorial experiment provides
additional evidence, but its 200-draw rerun was still pending in the supplied results. I would
rather leave that result out than introduce a stronger claim before the corresponding analysis is
settled.

Finally, the comparison between the permutation repairs does not justify ranking them. Although the
global permutation has an interval that covers the nominal rate in the paired comparison, the three
repairs remain statistically indistinguishable. Block-local permutation also covers the nominal rate
in more of the drift conditions. I therefore avoid describing any one repair as the best-calibrated
option under drift.

The articles are now more cautious about what the experiments establish. That is intentional. The
stronger result is not that the repair solves every problem, but that it addresses a specific
failure mode, has measurable limitations, and needs to be evaluated with enough surrogate draws to
support the conclusions being made.

---

# Change log

Every edit made to the drafted prose, with the source that forced it.

| # | Slot | Change | Why |
|---|---|---|---|
| 1 | 1 | "trace this failure to non-stationary speaker activity" softened, and the unreproduced 0.90 added | The draft abstract asserted a settled mechanism that SLOT 2 withdraws two paragraphs later. The largest cell in the design is 0.400 against a real 0.90 |
| 2 | 1 | Draw-count sensitivity attributed to the global within-speaker variant | Only that variant is draw-sensitive. Block-local and local move by p = 0.39 and 0.33 |
| 3 | 1 | Flatness distinguished from calibration | The repairs are flat under drift, not nominal. SLOT 10 and SLOT 12 both say so |
| 4 | 1 | Non-transport of the floor diagnostics added | SLOT 5 reports balanced accuracy falling to 0.75 and 0.571. An abstract claiming the diagnostics without that is an overclaim |
| 5 | 1 | Voice changed from "we/our" to "I" | SLOTs 2 to 12 are first-person singular. Mixed voice in one manuscript |
| 6 | 1 | `[ANON]` marker on the benchmark release | A release link de-anonymises a double-blind submission |
| 7 | 2 | Provisionality banner added | Every figure in the slot is at 100 draws, the setting SLOT 3 shows inflates this surrogate |
| 8 | 2 | "at the real-channel values" changed to "at the nominal knob values", and the calibrated arm's 0.005 and 0.105 added | 0.000 and 0.400 come from the factorial arm at nominal settings. The calibrated arm is the one tuned so the generated channel reproduces the real statistics, and the generator script warns against exactly this conflation |
| 9 | 2 | "0.067" qualified with its draw count | The articles now say 0.013 for the same quantity at 200 draws. Unqualified, the paper and the articles contradict each other |
| 10 | 3 | Paragraph added on what the draw experiment does not establish | 100 against 200 shows 100 is too few. Nothing above 200 was tested, so 200 is a lower bound, not a converged value |
| 11 | 4 | Calinski-Harabasz added as a third zero-error statistic, with the transportability result that excludes it | Three proxies reach zero errors where they were fitted, not two. Error count cannot choose between them. CH condemns three cells at true ARI exactly 1.000 on corpus size alone, reading 76 to 77 at 2,000 messages against its own cut of 138.9. New artifact: `../../swarm-bench/proxy_transport.py` |
| 12 | 4 | "seed stability" specified as the minimum across seeds | The mean variant makes one error at a different cut of 0.791. `calibrated_cuts_applied` names `seed_stability_min` |
| 13 | 4 | "von Luxburg, Tibshirani and Walther" split into two separate works | A merged author list across two distinct papers reads as a fabricated citation. Section 8.6 lists them separately |
| 14 | 4 | "flat between 0.68 and 1.00" extended with "and not even monotone there" | At true ARI 0.683 seed stability reads 0.875, higher than the 0.834 it reads at true ARI 0.927. This strengthens the point |
| 15 | 5 | "Of the fourteen cells it condemned, eleven had full conditional recall" added | Already in section 8.3 and it quantifies the failure direction |
| 16 | 6 | Their plain permutation's 100.00% and 99.95%, and their repair's 5.25% and 5.50%, added | The slot warns that permutation surrogates are not automatically safe. That warning had no evidence attached, and the evidence was in the cited paper |
| 17 | 7 | Caveat added that the 3.980 comes from the pair needing 1,936 failed draws for 100 successes | Section 6 flags that pair's null as conditioned on being estimable and biased in an unknown direction. The slot quoted the number as a clean measurement |
| 18 | 7 | Caveat added that point estimates are stochastic to about 17% | Section 6 says not to quote single-shot values beyond two significant figures |
| 19 | 7 | The CoTETE v0.2.3 surrogate defect added | Section 6 lists it as a caveat the paper must carry, and it is the author's own upstream contribution |
| 20 | 7 | "The original report" changed to "An earlier audit of this corpus", marked `[ANON]` | Self-reference in a double-blind submission |
| 21 | 10 | Crossover corrected from "between drift 0.3 and 0.6" to "between 0.0 and 0.3" | At drift 0.3 the shift already reads 0.100 against the global permutation's 0.100 and block-local's 0.093. The slot's own table contradicted the claim |
| 22 | 10 | Practical paragraph given the narrow margin | Follows from the corrected crossover: the advantage is gone by the first drift level tested |
| 23 | 11 | The eighth cell named | The slot said seven of eight fell inside without saying which did not |
| 24 | 11 | BLAS thread count added to the recorded environment | The environment block now records what the workers ran under rather than the parent's unpinned default |
| 25 | 12 | Moved out of the paper under its own heading | A changelog naming the author's published articles cannot appear in a double-blind submission |

## Unchanged, and verified against source

SLOT 9 in full. SLOT 5 apart from one addition. Every figure in SLOT 3, SLOT 10's four cells and
three trend p-values, SLOT 4's 0.623, 0.646, 0.979, 0.002, nine-against-54 and the ARI gap between
0.444 and 0.222, SLOT 5's edge counts, k sweep, token shares, 0.011, 0.296, 5-to-78, 0.75, 0.571 and
all seven error cells checked individually, SLOT 6's 100% and 98.2% and twelve thousand rounds, SLOT
7's z-scores, thresholds, 12-and-3, sd = 0 over 210 pairs, SLOT 11's one-of-eight and seven-of-eight.
