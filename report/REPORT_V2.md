# An Agent That Copies Nobody Is Certified as a Leader

**Manu Nicholas Jacob**, Independent Researcher. With Apart Research.

Track 4 (Multi-Agent Oversight and Control).

## Abstract

Multi-agent oversight increasingly proposes information-theoretic influence detection: lagged transfer entropy between agents, a surrogate null to decide which links are real, and a per-agent influence score. We audit that recipe on the AI Village, a public corpus of frontier models talking in shared channels, across four villages, and find it needs two repairs before it says anything. Replies arrive a median of 28.1 seconds apart, so no clock window both holds two speakers and separates a message from its answer, and at every width the topic symboliser certifies no more edges than a meaning-free hash null. A turn-ordered grid fixes that but breaks the conventional circular-shift surrogate: an agent planted with zero coupling is certified as a driver in 8 of 8 runs, and on structure-free data the family-wise error rate is 0.90 against a nominal 0.05. We isolate the cause as the turn-taking of the speaker sequence, since randomising who speaks when removes the failure entirely, and a symbol-permutation surrogate restores the error rate to 0.063 over 300 replicates. Calibration is not confounding, so we also condition on the channel's recent state, validating it on a released benchmark with a known influence graph where common-cause false edges fall from 22.7 to 0.0 and precision rises from 0.17 to 1.00 with no loss of power. With both repairs, main-village keeps 2 dyad-specific edges, open-chat's 18 vanish entirely, and where humans are present the surviving influence runs from people to agents and never back. We release the benchmark and the controls.

## 1. Introduction

If a population of AI agents shares a channel, an overseer would like to know who is driving whom. The standard toolkit is information-theoretic: lagged transfer entropy between agents, a surrogate null to decide which links are real, and a per-agent influence score. It needs no labels and no model internals, only a log of who said what and when.

Almost every demonstration of these detectors runs on synthetic traces with a planted leader, where the analyst controls timing and vocabulary. Real agent chat is asynchronous, bursty and written in open language. This report asks a narrower question than "what is the influence structure of a real swarm": whether the standard recipe, applied to real agent logs, returns anything an overseer should act on.

We run that audit on the AI Village (AI Digest, 2026), in which frontier models share chat channels over eighteen months, across four villages differing in size, lifetime and tempo, applying the checks a reader should demand: planted positive and negative controls, a meaning-free symboliser, replication in a held-out window, and sensitivity to the parameters we had to choose. The audit fails in a specific and instructive way, with a clean mechanism and a known fix.

1. The conventional circular-shift surrogate is invalid on turn-ordered agent chat. We measure the damage, a family-wise error rate of 0.90 against a nominal 0.05, and isolate the cause as the turn-taking structure of the speaker sequence.
2. We adopt the local-permutation surrogate from the event-based literature, verify it restores calibration, and re-certify every result under it. The invalid surrogate is not merely liberal: on one channel it manufactures 11 edges of which none survive, on another it masks 15.
3. Calibration is not confounding, so we also report a conditional estimate and validate it on a generated benchmark with a known influence graph: common-cause false edges fall from 22.7 to 0.0 and precision rises from 0.17 to 1.00 with no loss of power. We release the benchmark.
4. Applied to the real channels, conditioning leaves main-village's two edges standing and removes all 18 of open-chat's, and what survives alongside humans runs from people to agents rather than between agents.

## 2. Related Work

**Transfer entropy and surrogates.** Transfer entropy (Schreiber, 2000) measures how much a source's past reduces uncertainty about a target's next symbol beyond the target's own past. Plug-in estimators are biased upward on short series, so significance rests on surrogate data, with family-wise error across all ordered pairs controlled by a max-T test (Westfall and Young, 1993). The usual surrogate is a circular time shift of the source.

**Event-based data breaks the shift surrogate.** Our audit rediscovers this in a new domain. Shorten, Spinney and Lizier (2021), working on neural spike trains, show that transfer entropy for event-based processes is poorly served by time discretisation, and specifically that the conventional source-time-shift surrogate fails to represent the null hypothesis of conditional independence; they propose a local permutation scheme instead. Agent chat is event-based in exactly that sense: messages are events in continuous time, not samples of a clocked signal. Our contribution is not the fix but the demonstration that multi-agent safety practice inherits this failure, and that it is severe enough to manufacture leaders out of nothing.

**Oversight under a budget.** AI-control research frames monitoring as resource constrained, with a cost for false positives (Greenblatt et al., 2024). An influence graph is one such measurement, and our concern is the error rate attached to it.

## 3. Data

The AI Village dataset ships one gzipped-JSONL table per village. We use four villages, which differ enough to test whether any finding is a property of one channel.

| village | agent messages | agents | lifetime | human messages | busiest room |
|---|---|---|---|---|---|
| main | 205,726 | 58 | 576 days | 10,029 | #general (166,715, 81%) |
| open-chat | 35,483 | 23 | 66 days | 12,264 | #general (all) |
| swarm | 3,848 | 133 | 1 day | 5 | room a (3,846) |
| game-jam | 838 | 6 | 3 days | 36 | per-team rooms |

A 2026 scaffolding change scopes each agent to its current room's context, so the busiest room of each village is a self-contained influence substrate and we analyse it alone.

The primary analysis window is the final fourteen days of main-village #general, 17 to 31 October 2026, holding 8,800 agent messages. Twenty-two models posted at least 50 messages each in that window, and the directed test uses the 15 busiest of them, giving 7,958 message events. Two scaffolding facts are disclosed rather than corrected: the automated nudger that injects messages was off throughout this window, and the unused #best and #rest rooms were soft-deleted mid-window, which does not touch #general. We read message metadata and text only, and individual human participants appear only as aggregated or anonymised nodes.

## 4. Method

### 4.1 From open language to symbols

Transfer entropy needs discrete symbols, so each message is mapped to a small alphabet before influence is estimated, and that mapping is kept separate from the estimator. A topic symboliser (TF-IDF then k-means, k=8) gives a message its topic cluster id, so paraphrases of one idea share a symbol. A hash symboliser (a stable hash of the normalised text into k=8 buckets) assigns symbols with no notion of meaning and serves as a null: an edge surviving under topics but not hashing lives in shared meaning, one appearing under both lives in timing alone.

### 4.2 The lag problem, and why clock windows cannot solve it

A lag-1 transfer entropy compares window t-1 with window t, so influence landing inside one window is invisible to it. Agent chat makes this binding. Among the fifteen analysed agents the gap between consecutive messages by different speakers has a median of 28.1 seconds (25th percentile 9.2, 75th 66.2, 95th 159.3). Turn-taking is therefore a seconds-scale process, while any clock window wide enough to hold two speakers is minutes wide and swallows both a message and its answer. Section 5.1 measures both horns directly.

Appendix F measures both horns: at 30 seconds only 1.2% of agent-windows hold a message while 32.0% of replies already land in the same window as what they answer, by 5 minutes that share is 84.4%, and at every width the meaning-free hash null certifies about as many edges as the topic symboliser. Clock windows do not detect shared meaning here.

We avoid the bind by ordering messages canonically and letting one message be one tick. Each agent's series carries its symbol where it spoke and a silent symbol elsewhere, so the lag-1 comparison is between a message and the one immediately before it. The cost is that the measure captures immediate-predecessor influence only.

### 4.3 Two surrogate nulls

The preexisting estimator certifies an edge by comparing the observed transfer entropy with a **circular-shift** surrogate of the source, using a max-T family-wise test at level 0.05 across all ordered pairs. On the turn-ordered grid this surrogate fails, and Section 5.2 both measures the failure and isolates its cause: the structure of the real speaker sequence. Real conversation is not a sequence of independent draws about who talks next. It has strong turn-taking, and circularly shifting one agent's series slides that burst pattern to a different part of the timeline, where it aligns against the other agents differently than it ever does in the data.

We therefore add a **symbol-permutation** surrogate, following the local-permutation idea of Shorten et al. (2021): the source keeps the exact ticks at which it spoke, and only its symbols are permuted among them. Speaking pattern, sparsity and turn-taking are preserved exactly, and only the correspondence between symbol and time is destroyed. Both surrogates are reported throughout.

### 4.4 A second repair, for common cause

A valid surrogate fixes calibration but not confounding. If every agent tracks a drifting channel topic, every pair is genuinely dependent through the channel, and pairwise transfer entropy cannot tell that from direct influence. We therefore also report a **conditional** estimate, which asks whether a source's last message adds anything about a target's next one beyond the target's own history **and the channel's recent state**. The conditioning variable is the modal symbol of the last twelve messages, excluding the immediately preceding one so that it does not simply restate the source.

The two estimates answer different questions and bound the answer rather than one superseding the other. Pairwise asks whether there is directed topical dependence at all, including dependence mediated by the shared channel. Conditional asks whether there is dependence that is specific to the pair. In a group chat the distinction is substantive, because influence that works by shifting what the room is talking about is real influence, and conditioning removes it.

### 4.5 Controls

**Positive control (spike-in).** Real logs have no ground truth, so we plant it. A synthetic agent is inserted into the real stream; a fraction c of its messages are responses placed immediately after a chosen leader's message, copying that leader's topic, and the rest land at random positions with a symbol from the channel's marginal. Sweeping c, and separately the follower's volume, gives the detection floor.

**Negative controls.** An agent planted with no coupling, at a range of volumes, should never be certified. And the real speaker sequence with its symbols globally permuted contains no directed topical influence by construction, so a calibrated procedure should fire in about 5% of replicates.

**Replication and sensitivity.** The edge set is recomputed in the adjacent fourteen-day window (agents active in both, one topic space fit on the union), in each half of the primary window, and at several alphabet sizes.

## 5. Results

### 5.1 On a turn-ordered grid the standard surrogate is invalid

We plant an agent into the real stream, drawing its symbols from the channel's marginal and coupling it to nothing at all, then ask how often it is certified as driving something.

It is certified in 3 of 8 runs when it posts 50 messages, and in 8 of 8 at 100, 263, 600 and 1500 messages, with the mean largest z rising from 5.6 to 12.3, 21.7, 38.3 and 71.7. The error grows with how much the agent speaks, which rules out a small-sample explanation and says the mismatch is in structure rather than in sample size.

A planted agent could be dismissed as artificial, so we also measure the error rate directly. Keeping the real speaker sequence and permuting the symbols globally leaves data with no directed topical influence by construction. The shift surrogate certifies at least one edge in 9 of 10 such replicates, a family-wise error rate of 0.90 against a nominal 0.05.

**What breaks it is the speaker sequence.** Destroying one structure at a time isolates the cause (Appendix D). With the real speaker order intact and only the symbols shuffled, the shift surrogate fires in 10 of 10 replicates; randomising the speaker order as well drops it to 0 of 10. Replacing the real symbols with uniform draws, keeping the real order, still gives 6 of 10. So the failure is driven by turn-taking, not by the symbol distribution and not by sparsity: the real sequence repeats the same speaker 36% of the time and returns to a speaker after one other message 38% of the time. Shifting slides that burst pattern across the timeline; permuting symbols within an agent's own speaking positions leaves it intact, which is why the repair is unaffected in every condition.

### 5.2 A sparsity-preserving surrogate restores calibration

Following the local-permutation idea of Shorten et al. (2021), we keep each source's speaking positions and permute only its symbols among them. On the same destroyed-structure data the family-wise error rate falls to 0.063 over 300 replicates, with a 95% Wilson interval of 0.041 to 0.097, so it is close to the nominal 0.05 and clearly separated from the 0.90 it replaces. The planted uncoupled agent is now never certified: 0 of 5 at both 263 and 1500 messages, with mean max z of 2.8 in each case against 22.0 and 68.3 under the shift surrogate.

The failure is not an artifact of the configuration we chose. Appendix D shows it holds across swarm sizes from 5 to 20 agents, on a near-uniform alphabet as well as the skewed topic one, and that both the inflation and the masking reproduce under an independent symboliser.

[Figure 1: f2_null.png. Caption: Left, how often an agent coupled to nothing is certified as a driver, under each surrogate. Middle, family-wise error rate measured on data with all structure destroyed, with a Wilson interval; the dotted line is the nominal 0.05. Right, what each surrogate certifies on the real channel.]

### 5.3 The same channels, re-certified

Re-running every channel under the repaired surrogate changes the answers, and not in one direction.

| channel | window messages | shift: topic / hash | permutation: topic / hash |
|---|---|---|---|
| main #general | 8,800 | 11 / 1 | 2 / 0 |
| open-chat #general | 8,226 | 3 / 0 | 18 / 0 |
| swarm, room a | 3,846 | 2 / 1 | 1 / 0 |

In main-village, **none** of the 11 edges the standard recipe certifies survives the repair, and the two the valid surrogate certifies were not among them. In open-chat the correction runs the other way, 3 edges becoming 18, because pathological pairs inflate the max-T threshold and so raise the bar for everything else. An invalid surrogate does not simply add false positives, it scrambles the result.

### 5.4 Conditioning on the channel, and what it removes

A valid surrogate does not address confounding, so we built a generated benchmark with a known influence graph to measure that separately (Appendix E). Its decisive instances contain no influence at all while every agent tracks a shared drifting topic, so any certified edge is common cause. On those, pairwise transfer entropy certifies **22.7** edges on average; conditioning on the channel's recent state takes that to **0.0**. On instances with four planted edges, pairwise certifies 24 edges to recover the 4, while conditional certifies **4.0 and recovers all 4**, lifting precision from 0.17 to 1.00. Sweeping the coupling from 0.05 to 0.8, conditional finds the planted edge in 3 of 3 runs at every level while certifying about one edge in total, so the gain costs no power.

That benchmark flatters the conditional estimator by construction, since its common cause is a shared modal topic and the conditioning variable is the channel's modal topic. The real channels are the harder test, and there conditioning is consequential:

| channel | pairwise | conditional |
|---|---|---|
| main #general | 2 | **2, both the same edges** |
| open-chat #general | 18 | **0** |

main-village's two edges survive the strictest test we have, so they are dyad-specific. Open-chat's apparent structure does not survive at all: all 18 edges are mediated by the shared channel topic. On structure-free real data the conditional test certified nothing in 20 of 20 replicates, so it is well behaved and, if anything, conservative.

### 5.5 Power, and whether anything replicates

Both questions are answered in Appendix G and both bound the claims above. Power is governed by how much an agent says as much as by how strongly it copies, and it is channel-specific: in main-village a planted follower copying on 80% of its messages is caught only 1 time in 4, while in open-chat one copying 10% of the time is caught 3 times in 4. So main-village's two edges are a floor, not a description. Replication is weak throughout. Under the standard recipe the adjacent fourteen-day window shares 1 edge out of 8 and 4, and the one edge that persists is also the only edge the meaning-free hash null certifies.

### 5.6 Humans in the channel

main-village #general is now effectively human-free, with 3 human messages in the window, so the question has to be asked where humans are present. In open-chat, 32% of messages come from 124 human visitors, and adding them as nodes is where conditioning earns its keep.

Pairwise, with all humans collapsed into one node, 19 edges are certified: 13 agent to agent, 4 from humans to agents, 2 back. Conditioning on the channel removes almost all of the agent-to-agent structure and very little of the rest. **Four edges survive, of which three run from humans to agents, one is agent to agent, and none run from an agent to a human.** With the three busiest visitors as separate nodes the same thing happens, 20 edges falling to 2, of which one is an individual visitor driving a specific agent.

So the human-to-agent asymmetry is not an artifact of the confound; it is what is left once the confound is removed. Read it carefully all the same. Topical dependence from a person to an agent is also what ordinary responsiveness looks like, and the measurement supports only that the dependence is dyad-specific and directional, not that anyone is steering a swarm.

Two further traps, reported in Appendix D, are worth naming here: a continuous net-influence score turns out to measure volume rather than meaning, and a trivial copy-rate detector does not reproduce transfer entropy, so what this report indicts is the surrogate and not the statistic.

## 6. What an overseer should do

The audit suggests four controls, none expensive, that should accompany any published influence graph over an agent channel.

1. **Plant an agent coupled to nothing, at your channel's volumes, and check it is not certified.** This one test would have caught the failure reported here, and costs one run per volume.
2. **Measure the error rate directly,** by destroying the structure your method claims to find and checking the family-wise rate is near nominal. If it is not, the surrogate does not match the data.
3. **Preserve the speaker sequence in your surrogate.** Turn-taking is the structure that breaks the shift here, and any surrogate that moves an agent's messages in time will disturb it. For event-based data this is known, and Shorten et al. (2021) is the principled route.
4. **Establish the detection floor before interpreting an absence,** and report it beside the graph. "No edges" and "no influence" are different claims.
5. **Condition on the channel, and report both numbers.** A valid surrogate fixes calibration, not confounding. On our benchmark, conditioning took common-cause false edges from 22.7 to 0.0; on a real channel it removed all 18 edges. Pairwise and conditional bound the answer, and the gap between them is itself the result.

Two habits follow: publish a meaning-free symboliser's edge count beside the real one, and require replication in a held-out window before calling a graph the structure of a swarm.

## 7. Conclusion

Applied to real agent chat, the standard recipe for "who drives whom" needs two repairs before it says anything. Clock windows cannot separate a message from its answer at the timescale agents reply on, and the edges they certify are reproduced by a null with no access to meaning. The turn-ordered representation that fixes this breaks the circular-shift surrogate, whose family-wise error rate on structure-free data we measure at 0.90 against a nominal 0.05, and the cause is the turn-taking structure of conversation itself. A valid surrogate then fixes calibration but not confounding, and conditioning on the channel removes a further 18 of 18 edges in one channel while leaving 2 of 2 standing in another.

What survives both repairs is small and worth stating plainly: a pair of dyad-specific edges in one channel, almost nothing between agents in the other, and, where humans are present, influence that runs from people into agents and never back. For an overseer that is the operative finding. An influence graph is a measurement with an error rate and a confound, and until both are reported it should not be acted on.

## Appendix A: Limitations

- **Immediate-predecessor only.** The turn-ordered lag-1 measure sees influence from the message directly before a reply. Influence acting over several turns, or through a room's accumulated context, is out of scope and needs a higher-order or memory-aware estimator.
- **Discrete approximation to an event process.** Agent chat is event-based in continuous time. We use a turn-ordered discretisation with a permutation surrogate as a practical fix; a continuous-time estimator (Shorten et al., 2021) is the principled route and we did not attempt it.
- **Symbolisation is a free parameter.** The central result survives an independent symboliser (Section 5.3), but the edge count does not: it moves with the alphabet size and with which messages the topic model is fit on, and we report those sensitivities rather than tuning them. Two of the eight topic clusters are dominated by function words, because the preexisting symboliser does not remove stopwords.
- **No ground truth in the real logs.** The validity argument rests on planted controls and on the meaning-free null, not on recovering a known answer.
- **Scaffolding confounds.** Agent behaviour is shaped by prompt, tool and memory changes logged in the dataset's changelog. We chose a window in which the message-injecting nudger was off, but other scaffolding is held fixed only by the shortness of the window.
- **Conditioning removes real influence too.** The conditional estimate discards any influence that works by shifting what the channel is talking about, which in a group chat may be a large part of genuine influence. It is a lower bound on dyadic influence, not a better measurement of influence in general, which is why both estimates are reported. On structure-free real data it certified nothing in 20 of 20 replicates, so it may also be conservative.
- **The human result is exploratory.** It rests on one village and one window, and should be read as a lead. Topical dependence from a human to an agent is also consistent with ordinary responsiveness rather than steering.

## Appendix B: Dual-Use and Ethical Considerations

This work audits influence detection on a population of AI agents, which is dual-use. Used defensively it helps an overseer decide what an influence graph is worth, and our main result is deflationary: it tells practitioners to trust these outputs less, which reduces rather than increases the chance of acting on a bad attribution. The same tooling could be used to identify the most influential agent in a swarm in order to target it, or to surveil participants in a channel. Three properties limit the misuse. The subjects are AI models; the dataset is already public under research terms and we add no re-identification; and the measure is weak and local, recovering immediate-predecessor topical dependence rather than any model of how to steer an agent.

We followed the dataset's research terms: research use only, no training on the data, no re-identification, and citation of the source. Human participants appear only as an aggregate node or as anonymised visitor-1..n labels, never by name or handle, and we report no content attributable to an individual person. We read message text and metadata only, never model weights or private user data.

## Appendix C: Preexisting tools, new work, and LLM usage

**Preexisting (declared).** The estimator (lag-1 transfer entropy, circular-shift surrogate, max-T family-wise test) and the reader and symbolisers (topic and hash) were built before the sprint in the repository swarm-prep and are declared preexisting with their validation numbers in that repository's README. Before the sprint, authentication was verified and filenames were listed, but no chat content was read or described, so the weekend is the first reading of the data. The preexisting validation used synthetic chat in which several agents speak per window, a setting in which the circular-shift surrogate is valid; the invalidity reported here arises only on the one-message-per-tick grid introduced this weekend, and is not a defect of the preexisting tool as validated.

**New this weekend.** The subset and window choices on the real data; the measured reply-latency justification for the lag; the turn-ordered representation; the symbolisation of real message text; the clock-window failure analysis; the symbol-permutation surrogate, the demonstration that the shift surrogate is invalid on this grid, and the ablation isolating turn-taking as the cause; the conditional estimator and its validation; **SwarmInfluence-Bench**, the generated benchmark of Appendix E; the planted positive and negative controls; the calibration measurements; the replication and sensitivity battery; the four-village comparison; the human-node analysis; the trivial-baseline comparison; all figures; and a vectorised reimplementation of the preexisting estimator, used only for scale and verified bit-for-bit against the preexisting code before use.

**LLM usage.** The author used an AI coding assistant (Claude) to help write and run the analysis code, to help draft this report, and to structure the figures. The author is responsible for every claim, number and figure here. All results come from the released code run on the public dataset, no result or reference is fabricated, and the numbers in this document are checked against the analysis output by a script that fails on any mismatch.

## Appendix D: Isolating the cause, robustness, and two further traps

**Which structure breaks the surrogate.** Each condition below contains no directed topical influence by construction, so a calibrated procedure should fire in about 5% of replicates. Ten replicates each.

| condition | circular shift | symbol permutation |
|---|---|---|
| real speaker order, symbols shuffled | **10 / 10** | 0 / 10 |
| real speaker order, uniform i.i.d. symbols | 6 / 10 | 1 / 10 |
| speaker order shuffled, symbols shuffled | **0 / 10** | 1 / 10 |
| speaker order shuffled, uniform i.i.d. symbols | 0 / 10 | 1 / 10 |

Speaker order is the switch. The symbol distribution only modulates. A synthetic channel that draws speakers independently does not reproduce the failure at all, which is how we found this: a generated benchmark with exactly one speaker per tick left the shift surrogate roughly calibrated, so mutual exclusivity alone, which we had first proposed as the explanation, is not sufficient.

**The surrogate failure is not an artifact of our configuration.** It is not a large-swarm effect: across swarms of 5, 10, 15 and 20 agents the shift surrogate certifies something in 22 of 24 null replicates, against 3 of 24 for the permutation surrogate, so shrinking the swarm does not rescue it. It is not a property of the skewed topic alphabet either, since on the near-uniform hash alphabet, where the largest symbol holds 13% of messages rather than 37%, the shift surrogate still fires in 10 of 10 replicates.

**Both corrections survive a different symboliser.** Replacing TF-IDF and k-means with latent semantic analysis gives 12 edges against 1 in main-village and 2 against 22 in open-chat: the same inflation and the same masking, reached by an independent route to topics. The meaning-free hash control gives 1 against 0 and 0 against 0. So the central result concerns the surrogate rather than any one clustering choice, although the edge count itself remains sensitive to the alphabet size.

**A continuous influence score measures volume.** Summed outgoing minus incoming transfer entropy, a common per-node leadership summary, ranks agents almost identically under the topic symboliser and under the meaning-free hash null (Spearman 0.85), with the same agent on top at nearly the same value. A score the hash null reproduces cannot be measuring shared meaning, so the certified edge set should be reported instead.

**The estimator is not redundant, though.** A trivial detector, the rate at which an agent repeats the previous message's topic in excess of its own base rate, ranks pairs very differently from transfer entropy (Spearman 0.21), and the pairs it ranks highest overlap the certified set in only 3 of 10 cases. So transfer entropy is not an expensive way to compute a copy rate, and the failure documented in this report belongs to the surrogate rather than to the statistic.

## Appendix E: the benchmark, and why it exists

Real logs have no ground truth, so the common-cause question could not be settled on them. We built a generator in which the influence graph is known by construction: it decides, in code, who speaks at which tick, on which topic, and who reacts to whom. Surface text is a separate, replaceable layer drawn from disjoint per-topic vocabularies, so the whole thing runs offline and a detector still has to symbolise raw text rather than read the labels.

It has two null families and the distinction is the point. **Pure nulls** have no influence and no common cause, and measure calibration. **Common-cause nulls** have no influence between agents but a shared drifting channel topic, so every pair is genuinely dependent through the channel; they measure confounding. A benchmark with signal in every instance cannot see the failure mode this report is about.

Two findings came out of building it. It **refuted our own first explanation** of the surrogate failure: a generated channel with exactly one speaker per tick left the shift surrogate roughly calibrated at 0.08, which is what sent us to isolate turn-taking instead. And it showed that **precision, not recall, is the weak point** of pairwise transfer entropy, which is what motivated the conditional estimate.

Two honest caveats. The benchmark's common cause is a shared modal topic and our conditioning variable is the channel's modal topic, so Section 5.4's synthetic numbers are close to a best case; the real-channel result is the harder test and we report it alongside. And the generator draws speakers independently, so it does **not** reproduce the turn-taking that breaks the shift surrogate on real logs, which is a limitation we found rather than designed.

## Appendix F: clock windows in full

Running the detector on clock windows from 30 seconds to an hour shows the two failure modes closing on each other. At 30 seconds only 1.2% of agent-windows contain a message, so there is almost nothing to estimate from, while 32.0% of replies already land in the same window as the message they answer and are invisible to a lag-1 test. By 5 minutes that share is 84.4% and by an hour 98.6%.

More telling is what the edges are made of. At every width the meaning-free hash null certifies about as many edges as the topic symboliser, 12 against 9 at 30 seconds, 19 against 17 at one minute and 44 against 27 at fifteen, and at 5 minutes it certifies more, 19 against 17. Whatever clock-window transfer entropy is detecting on this data, it is not shared meaning, which is what sends us to the turn-ordered grid.

[Figure 3: f1_clock.png. Caption: Clock-window transfer entropy on the 15 analysed agents of main-village #general. Left, the two failure modes as a function of window width. Right, edges certified under the topic symboliser against the meaning-free hash null.]

## Appendix G: power and replication in full

**How much influence could we have seen?**

Absence of edges is only informative if the test could have found them, so we plant one. A synthetic follower at the median agent's volume copies the busiest agent's topic on a fraction of its messages. In main-village it goes undetected in 0 of 4 runs at couplings up to 0.4 and is caught in only 1 of 4 at 0.8. Holding coupling at 0.8 and varying how much it speaks, detection rises from 1 of 4 at 263 messages to 4 of 4 at 800 and stays there at 2000 and 4000, so the floor sits between 3% and 10% of the channel's messages.

Power is governed by how much an agent says, not only by how strongly it copies, and it is channel-specific: in open-chat a follower at that channel's median volume is caught in 3 of 4 runs at coupling 0.1 and in 4 of 4 from 0.2 upward. main-village's two edges are therefore a floor rather than a description.

[Figure 2: f4_power.png. Caption: Detection of a planted follower under the repaired surrogate. Left, varying the fraction of its messages that copy the leader, at the median agent's volume. Right, varying how much it speaks, at strong coupling.]

**Does anything replicate?**

In main-village, no. Under the standard recipe the adjacent fourteen-day window shares 1 edge with the primary window out of 8 and 4, a Jaccard of 0.09, and the two halves share none. Under the repaired surrogate the adjacent window certifies nothing. The one edge that persists, GLM-5.2 to Gemini 3.5 Flash, is also the only edge the hash null certifies, so the single stable thing the standard recipe finds carries no meaning.

In open-chat, where the valid test has power, the picture is better but still partial: restricted to agents active in both windows and sharing one topic space, the current window certifies 9 edges and the previous 5, with 3 in common, a Jaccard of 0.27, against 0 from the hash null. About a third holds up. Splitting that window into halves is harsher, 7 edges against 2 with 1 in common, which the power result predicts, since halving the data moves agents below the floor.

The alphabet size remains a live degree of freedom even under the repaired surrogate, with open-chat certifying 8 edges at k=4, 18 at k=8 and 21 at k=16, so an edge count is never a property of a channel alone.

## References

AI Digest (2026). AI Village dataset. https://huggingface.co/datasets/aidigestorg/ai-village and https://theaidigest.org/village

Greenblatt, R., Shlegeris, B., Sachan, K., and Roger, F. (2024). AI Control: Improving Safety Despite Intentional Subversion. arXiv:2312.06942.

Schreiber, T. (2000). Measuring Information Transfer. Physical Review Letters, 85(2), 461-464.

Shorten, D. P., Spinney, R. E., and Lizier, J. T. (2021). Estimating Transfer Entropy in Continuous Time Between Neural Spike Trains or Other Event-Based Data. PLOS Computational Biology, 17(4), e1008054.

Westfall, P. H., and Young, S. S. (1993). Resampling-Based Multiple Testing: Examples and Methods for p-Value Adjustment. Wiley.
