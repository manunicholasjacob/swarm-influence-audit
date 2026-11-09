# Section 8: The symbolisation floor

Rewritten 7 November 2026, after an experiment built to defend a result instead demolished three of
its claims. What survives is narrower and better founded. The arc of this section is the paper's
best evidence that its own controls were run honestly, so it should be written as that arc rather
than as a tidy finding.

## 8.1 What the floor is, and what survives

Everything these methods produce is downstream of turning text into symbols. On the benchmark,
where true topics are known, detection collapses once the symboliser's agreement with truth falls
far enough, and below that point the false-positive rate looks **better**, because there is no
shared topic left to be confounded by. A pipeline that suddenly certifies nothing has not found
peace. It may have gone blind, and nothing downstream of the symboliser can tell those apart.

That much stands. Three things that were said around it do not.

## 8.2 Three withdrawn claims

**Withdrawn 1: "below the floor there is no topic signal left."** False. The circular-shift
surrogate recovers all four planted edges at **every** overlap level, including 0.95 where ARI is
0.011 and the permutation null certifies nothing at all. The collapse is specific to the
**permutation** null, whose surrogate absorbs the signal once symbols become near-exchangeable. The
signal is still there; our repaired test stops being able to see it.

**Withdrawn 2: ARI 0.44 is not a universal floor.** It is a property of the pair (symboliser,
channel). Holding the symboliser fixed and setting `shared_topic` to 0, conditional detection keeps
all four planted edges down to true ARI **0.296**. The published 0.44 is conditional on
`shared_topic = 0.55`, which happened to be pinned at that value at all nine sweep levels.

**Withdrawn 3: the certified-edge count is not a symboliser score.** Among cells where true ARI is
exactly 1.000 and seed stability is exactly 1.000, raising `shared_topic` alone takes the
permutation edge count from **5 to 78**. Channel volume moves it too, 23.7 to 7.3 edges at unchanged
ARI. The count is a function of common-cause strength, volume and family size, none of which is
measurable on real text.

## 8.3 Detecting the floor without labels, and the limit of that

**Three** label-free statistics separate the floor with zero errors **on the mechanism they were
fitted to**: seed stability, specifically the **minimum** pairwise agreement across seeds, at a cut
of 0.623; cross-symboliser agreement with LSA at 0.646; and the **Calinski-Harabasz index** at
138.9. An earlier draft of this section said two and recommended the first pair without mentioning
the third. Error count cannot justify that, because where they were fitted all three are perfect.
Note also that it is the minimum across seeds and not the mean: the mean variant makes one error,
at a different cut of 0.791.

**What chooses between them is transportability, and it is measured rather than argued.** A floor
proxy is a claim about the symbolisation, so a cut that moves when the corpus changes while the
symbolisation stays perfect is a property of the corpus instead. Applying each cut unchanged to the
30 nuisance cells of `floor_contradiction.json`, 27 of which hold true ARI at 1.000:

| proxy | cut | errors where fitted | errors on nuisance set | of those at true ARI 1.000 |
|---|---|---|---|---|
| seed stability, min across seeds | 0.623 | 0 | 2 | **0** |
| LSA agreement | 0.646 | 0 | 2 | **0** |
| Calinski-Harabasz | 138.9 | 0 | 6 | **3** |

The two bounded statistics err only on the short-message cells, where the symbolisation really has
degraded. Calinski-Harabasz additionally condemns all three cells whose true ARI is exactly
**1.000**, for no reason beyond the corpus holding 2,000 messages rather than 8,000: it reads 76 to
77 there against its own cut of 138.9. It is unbounded and grows with sample size, so a published
numeric cut for it means nothing on anyone else's corpus. **A cut that moves with the corpus is not
a floor cut.** See `../../swarm-bench/proxy_transport.py` and `proxy_transport.json`.

The instructive part stands: the highest-correlating statistic is not the best classifier.
Silhouette correlates with true ARI at 0.979 and is useless for the decision, because its threshold
sits in a gap 0.002 wide. Calinski-Harabasz sharpens that point rather than blunting it, since it
correlates at 0.973 and classifies perfectly where it was fitted, and still cannot carry a cut.

**Out of mechanism they degrade badly.** Applied unchanged to instances with a known k mismatch,
seed stability's balanced accuracy falls from 1.00 to **0.75** and LSA agreement's to **0.571**. All
seven of seed stability's errors are false below-floor, and **in all seven the detector kept every
planted edge**. Eleven of the fourteen cells it condemned had full conditional recall. A cut fitted
on one degradation mechanism does not transfer to another, and the failure direction is the
dangerous one: it condemns working symbolisations.

Nuisance structure mostly does not break them. Turn-taking at the real channel's rates, activity
drift, five or twenty-five agents, volume skew and a quarter of the messages all left true ARI at
1.000 with both proxies above cut. **Message length does break them**, at four words per message.

## 8.4 The contradiction, and why it is the most useful page in this section

Applied to the two real channels, the proxies called main-village above the floor and open-chat
below it by a wide margin. That contradicted the audit's own measurement, where open-chat certifies
**18** and **22** edges against main-village's **2** and **1**, with open-chat's meaning-free hash
null at **0**. A channel called below-floor produced an order of magnitude more edges than the
healthy one, and its meaning-free null produced none.

**It resolves against the proxy.** A k sweep on the same channels, using the same loader, window and
five-seed protocol, reproduces the published k=8 readings to the digit. At **k=4**, open-chat reads
seed stability **0.9499** and LSA agreement **0.9784**, the highest either channel produces anywhere
on the grid, clearing both cuts by a wide margin.

| k | main-village | open-chat |
|---|---|---|
| 4 | 0.874 / 0.878 | **0.950 / 0.978** |
| 8 | 0.676 / 0.696 | **0.287 / 0.456** |
| 16 | 0.818 / 0.780 | 0.277 / 0.478 |

The below-floor verdict was a statement about one arbitrary k, presented as a statement about a
channel. The rival explanation, that open-chat's messages are too short, is ruled out by the text:
**27.1%** of main-village's messages are under five tokens against **2.3%** of open-chat's, so the
short-message channel is the one the control cleared.

And the edge count could never have arbitrated it either way, per withdrawn claim 3. The original
contradiction was a category error on both sides.

## 8.5 What may be claimed

- At a **fixed** k, these statistics distinguish a reproducible clustering from one that is not.
  Open-chat's k=8 clustering genuinely is not reproducible across initialisations.
- **No channel-level floor verdict may be issued from a single k.** The published control must
  sweep k and report a curve, refusing to certify any channel whose verdict changes along it. Both
  channels change.
- The floor control is real and worth running. Its calibration is not transportable, and a user has
  to re-fit it on a degradation mechanism resembling their own.

The audit report's statement that it cannot rule out the real channels sitting near the floor
**stands unchanged**, which is the right outcome: the control that was supposed to settle it turned
out to need settling itself.

## 8.6 Honest placement in the literature

Clustering stability as a label-free quality proxy is forty years old (Ben-Hur et al. 2002, Lange et
al. 2004, von Luxburg's review, Tibshirani and Walther). The statistic is not new. The only novel
move is calibrating it against a **detection-performance** floor rather than against cluster
recovery, and section 8.3 shows that calibration is exactly the part that does not transport. That
should be stated as the limitation it is rather than buried, because it is also the most useful
thing this section tells the next person.

## Artifacts

- `../../swarm-bench/floor_proxy_sweep.json`, the nine-level calibration
- `../../swarm-bench/floor_contradiction.json`, five experiments, 382 KB, reproducing all 54
  committed sweep cells exactly (edge diff 0, ARI diff 0.0)
- `../../swarm-bench/floor_proxy_real.json`, carrying an explicit retraction block with every
  verdict relabelled `says_at_k8`
