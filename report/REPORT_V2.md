# An Agent That Copies Nobody Is Certified as a Leader

**Manu Nicholas Jacob**, Independent Researcher. With Apart Research.

Track 4 (Multi-Agent Oversight and Control).

## Abstract

Multi-agent oversight increasingly proposes information-theoretic influence detection: lagged transfer entropy between agents, a surrogate null to decide which links are real, and a per-agent influence score. We audit that recipe on the AI Village, a public corpus of frontier models talking in shared channels, across four villages. Two facts make agent chat hostile to the standard approach. Replies arrive a median of 28.1 seconds apart, so no clock window is both dense enough to estimate and short enough to separate a message from its answer, and at every width we tried the topic symboliser certifies no more edges than a meaning-free hash null. Moving to a turn-ordered grid, in which one message is one tick, fixes the representation but invalidates the conventional circular-shift surrogate: exactly one agent is non-silent per tick, and shifting destroys that. The cost is severe. An agent planted with zero coupling is certified as a driver in 8 of 8 runs, with z up to 71.7, and on data with every structure destroyed the shift surrogate's family-wise error rate is 0.90 against a nominal 0.05. A symbol-permutation surrogate restores it to 0.10 with a 95% interval of 0.03 to 0.26. Re-certified, main-village falls from 11 edges to 2 with none in common, while open-chat rises from 3 to 18, because the invalid surrogate masks as well as manufactures. We give the controls practitioners should run.

## 1. Introduction

If a population of AI agents shares a channel, an overseer would like to know who is driving whom. The standard toolkit is information-theoretic: lagged transfer entropy between agents, a surrogate null to decide which links are real, and a per-agent influence score. It needs no labels and no model internals, only a log of who said what and when.

Almost every demonstration of these detectors runs on synthetic traces with a planted leader, where the analyst controls timing and vocabulary. Real agent chat is asynchronous, bursty and written in open language. This report asks a narrower question than "what is the influence structure of a real swarm": whether the standard recipe, applied to real agent logs, returns anything an overseer should act on.

We run that audit on the AI Village (AI Digest, 2026), in which frontier models share chat channels over eighteen months, across four villages differing in size, lifetime and tempo. We apply the checks a reader should demand: a positive control with planted influence, a negative control with an agent coupled to nothing, a meaning-free symboliser, replication in a held-out window, and sensitivity to the parameters we had to choose. The audit fails in a specific and instructive way, with a clean mechanism and a known fix.

1. The conventional circular-shift surrogate is invalid on turn-ordered agent chat. We give the structural reason and measure the damage: a family-wise error rate of 0.90 against a nominal 0.05, and an agent coupled to nothing certified as a driver in 8 of 8 runs.
2. We adopt the local-permutation surrogate from the event-based literature, verify it restores calibration here, and re-certify every result under it. The invalid surrogate is not merely liberal: on one channel it manufactures 11 edges of which none survive, on another it masks 15.
3. We measure detection power with planted controls, so absence can be interpreted. A median-volume follower copying on 80% of its messages is detected once in four runs.
4. We report what survives, including one-directional influence from individual human visitors to specific agents in the one well-powered channel.

## 2. Related Work

**Transfer entropy and surrogates.** Transfer entropy (Schreiber, 2000) measures how much a source's past reduces uncertainty about a target's next symbol beyond the target's own past. Plug-in estimators are biased upward on short series, so significance rests on surrogate data rather than the raw statistic, with family-wise error across all ordered pairs controlled by a single-step max-T test (Westfall and Young, 1993). The usual surrogate is a circular time shift of the source.

**Event-based data breaks the shift surrogate.** Our audit rediscovers this in a new domain. Shorten, Spinney and Lizier (2021), working on neural spike trains, show that transfer entropy for event-based processes is poorly served by time discretisation, and specifically that the conventional source-time-shift surrogate fails to represent the null hypothesis of conditional independence; they propose a local permutation scheme instead. Agent chat is event-based in exactly that sense: messages are events in continuous time, not samples of a clocked signal. Our contribution is not the fix but the demonstration that multi-agent safety practice inherits this failure, and that it is severe enough to manufacture leaders out of nothing.

**Oversight under a budget.** AI-control research frames monitoring as resource constrained, with an auditing budget and a cost for false positives (Greenblatt et al., 2024). An influence graph is one such measurement, and our concern is the error rate attached to it.

## 3. Data

The AI Village dataset ships one gzipped-JSONL table per village. We use four villages, which differ enough to test whether any finding is a property of one channel.

| village | agent messages | agents | lifetime | human messages | busiest room |
|---|---|---|---|---|---|
| main | 205,726 | 58 | 576 days | 10,029 | #general (166,715, 81%) |
| open-chat | 35,483 | 23 | 66 days | 12,264 | #general (all) |
| swarm | 3,848 | 133 | 1 day | 5 | room a (3,846) |
| game-jam | 838 | 6 | 3 days | 36 | per-team rooms |

A 2026 scaffolding change scopes each agent to its current room's context, so the busiest room of each village is a self-contained influence substrate and we analyse it alone.

The primary analysis window is the final fourteen days of main-village #general, 17 to 31 October 2026, holding 8,800 agent messages. Twenty-two models posted at least 50 messages each in that window, and the directed test uses the 15 busiest of them, giving 7,958 message events. Two scaffolding facts are disclosed rather than corrected: the automated nudger that injects messages was off throughout this window, so no scaffolding-authored messages contaminate it, and the unused #best and #rest rooms were soft-deleted mid-window, which does not touch #general. We read message metadata and text only. No personal data and no model internals are involved, and individual human participants appear only as opaque, aggregated or anonymised nodes.

## 4. Method

### 4.1 From open language to symbols

Transfer entropy needs discrete symbols, so each message is mapped to a small alphabet before influence is estimated, and that mapping is kept separate from the estimator. A topic symboliser (TF-IDF then k-means, k=8) gives a message its topic cluster id, so paraphrases of one idea share a symbol. A hash symboliser (a stable hash of the normalised text into k=8 buckets) assigns symbols with no notion of meaning and serves as a null: an edge surviving under topics but not hashing lives in shared meaning, one appearing under both lives in timing alone.

### 4.2 The lag problem, and why clock windows cannot solve it

A lag-1 transfer entropy compares window t-1 with window t, so influence landing inside one window is invisible to it. Agent chat makes this binding. Among the fifteen analysed agents the gap between consecutive messages by different speakers has a median of 28.1 seconds (25th percentile 9.2, 75th 66.2, 95th 159.3). Turn-taking is therefore a seconds-scale process, while any clock window wide enough to hold two speakers is minutes wide and swallows both a message and its answer. Section 5.1 measures both horns directly.

We avoid the bind by ordering messages canonically and letting one message be one tick. Each agent's series carries its symbol at the ticks where it spoke and a silent symbol elsewhere, so the lag-1 comparison is between a message and the one immediately before it, and stimulus and response are always in different ticks. The cost is that the measure captures immediate-predecessor influence only; influence over several turns is out of scope.

### 4.3 Two surrogate nulls

The preexisting estimator certifies an edge by comparing the observed transfer entropy with a **circular-shift** surrogate of the source, using a max-T family-wise test at level 0.05 across all ordered pairs. On the turn-ordered grid this surrogate is invalid, for a reason that is visible by construction: exactly one agent is non-silent at each tick, because each tick is one message by one speaker. Circularly shifting one agent's series destroys that mutual exclusivity, so the surrogate statistic is computed over speaker configurations that cannot occur in the data. Section 5.2 shows what this costs.

We therefore add a **symbol-permutation** surrogate, following the local-permutation idea of Shorten et al. (2021): the source keeps the exact ticks at which it spoke, and only its symbols are permuted among those ticks. Speaking pattern, sparsity and mutual exclusivity are preserved exactly; only the correspondence between symbol and time is destroyed, which is what the alternative hypothesis is about. Both nulls are reported throughout.

### 4.4 Controls

**Positive control (spike-in).** Real logs have no ground truth, so we plant it. A synthetic agent is inserted into the real message stream; a fraction c of its messages are responses placed immediately after a chosen leader's message and copying that leader's topic symbol, and the rest land at random positions with a symbol drawn from the channel's marginal. Sweeping c, and separately the follower's volume, gives the detection floor.

**Negative controls.** An agent planted with no coupling at all, at a range of volumes, should never be certified. And the real speaker sequence with its symbols globally permuted contains no directed topical influence by construction, so a calibrated procedure should certify an edge in about 5% of replicates.

**Replication and sensitivity.** The certified edge set is recomputed in the adjacent fourteen-day window (restricted to agents active in both, with one topic space fit on the union), in each half of the primary window, and at several alphabet sizes.

## 5. Results

### 5.1 Clock windows cannot separate cause from effect

Figure 1 runs the detector on clock windows from 30 seconds to an hour. The two failure modes close on each other. At 30 seconds only 1.2% of agent-windows contain a message, so there is almost nothing to estimate from, while already 32.0% of replies land in the same window as the message they answer and are therefore invisible to a lag-1 test. By 5 minutes that share is 84.4%, and by an hour it is 98.6%.

More telling is what the edges are made of. At every width the meaning-free hash null certifies about as many edges as the topic symboliser (12 against 9 at 30 seconds, 19 against 17 at one minute, 44 against 27 at fifteen), and at 5 minutes it certifies more, 19 against 17. Whatever clock-window transfer entropy is detecting on this data, it is not shared meaning. We therefore move to the turn-ordered grid for everything that follows.

[Figure 1: f1_clock.png. Caption: Clock-window transfer entropy on the 15 analysed agents of main-village #general. Left, the two failure modes as a function of window width. Right, edges certified under the topic symboliser against the meaning-free hash null.]

### 5.2 On a turn-ordered grid the standard surrogate is invalid

On that grid exactly one agent is non-silent at each tick. A circular shift of one agent's series destroys this, so the surrogate statistic is evaluated on speaker configurations that cannot occur. The consequence is not subtle. We plant an agent whose symbols are drawn from the channel's marginal and which is coupled to nothing at all, and ask how often it is certified as driving something.

It is certified in 3 of 8 runs when it posts 50 messages, and in 8 of 8 at 100, 263, 600 and 1500 messages, with the mean largest z rising from 5.6 to 12.3, 21.7, 38.3 and 71.7. The error grows with how much the agent speaks, which is the opposite of what a sparsity story predicts and exactly what the mutual-exclusivity account predicts: the more ticks an agent occupies, the further the shifted surrogate departs from the data's structure.

A planted agent could be dismissed as an artificial insertion, so we also measure the error rate directly. Keeping the real sequence of speakers and permuting the symbols globally leaves a dataset with no directed topical influence by construction. The circular-shift surrogate certifies at least one edge in 9 of 10 such replicates, a family-wise error rate of 0.90 against a nominal 0.05, averaging 1.2 edges per replicate.

### 5.3 A sparsity-preserving surrogate restores calibration

Following the local-permutation idea of Shorten et al. (2021), we keep each source's speaking positions and permute only its symbols among them. On the same destroyed-structure data the family-wise error rate falls to 0.10 over 30 replicates, with a 95% Wilson interval of 0.03 to 0.26, which covers the nominal 0.05 although the point estimate sits above it. The planted uncoupled agent is now never certified: 0 of 5 at both 263 and 1500 messages, with mean max z of 2.8 in each case against 22.0 and 68.3 under the shift surrogate.

[Figure 2: f2_null.png. Caption: Left, how often an agent coupled to nothing is certified as a driver, under each surrogate. Middle, family-wise error rate measured on data with all structure destroyed, with a Wilson interval; the dotted line is the nominal 0.05. Right, what each surrogate certifies on the real channel.]

### 5.4 The same channels, re-certified

Re-running every channel under the repaired surrogate changes the answers, and not in one direction.

| channel | window messages | shift: topic / hash | permutation: topic / hash |
|---|---|---|---|
| main #general | 8,800 | 11 / 1 | 2 / 0 |
| open-chat #general | 8,226 | 3 / 0 | 18 / 0 |
| swarm, room a | 3,846 | 2 / 1 | 1 / 0 |

In main-village, **none** of the 11 edges the standard recipe certifies survives the repair, and the two the valid surrogate does certify were not among them. In open-chat the correction runs the other way, 3 edges becoming 18. The mechanism is the family-wise step: pathological pairs inflate the max-T threshold, which lets those pairs through and raises the bar for everything else. An invalid surrogate does not simply add false positives, it scrambles the result.

### 5.5 How much influence could we have seen?

Absence of edges is only informative if the test could have found them, so we plant one. A synthetic follower is inserted at the median agent's volume and copies the busiest agent's topic on a fraction of its messages. Under the repaired surrogate it is detected in 0 of 4 runs at couplings up to 0.4, and in 1 of 4 at 0.8. Holding coupling at 0.8 and varying how much the follower speaks, detection goes from 1 of 4 at 263 messages to 4 of 4 at 800, and stays at 4 of 4 at 2000 and 4000. The floor sits between 3% and 10% of the channel's messages.

Power is therefore governed by how much an agent says, not only by how strongly it copies. For a median-volume agent the test is close to blind even to very strong copying, so main-village's two certified edges are a floor, not a description: the question there is largely unanswerable rather than answered in the negative.

[Figure 3: f4_power.png. Caption: Detection of a planted follower under the repaired surrogate. Left, varying the fraction of its messages that copy the leader, at the median agent's volume. Right, varying how much it speaks, at strong coupling.]

### 5.6 Does anything replicate?

In main-village, no. Under the standard recipe the adjacent fourteen-day window shares 1 edge with the primary window out of 8 and 4 respectively, a Jaccard of 0.09, and the two halves of the primary window share none at all. Under the repaired surrogate the adjacent window certifies nothing, so there is nothing to share. The single edge that does persist across windows under the standard recipe, GLM-5.2 to Gemini 3.5 Flash, is also the only edge the meaning-free hash null certifies, so the one stable thing the standard recipe finds carries no meaning.

In open-chat, where the valid test has power, the picture is better but still partial: restricted to agents active in both windows and sharing one topic space, the current window certifies 9 edges and the previous 5, with 3 in common, a Jaccard of 0.27, against 0 edges from the hash null. About a third of the structure holds up. Splitting that window into halves is harsher, 7 edges against 2 with 1 in common, which is what the power result predicts, since halving the data moves agents below the detection floor.

The alphabet size remains a live degree of freedom even under the repaired surrogate, with open-chat certifying 8 edges at k=4, 18 at k=8 and 21 at k=16, so an edge count is never a property of a channel alone.

### 5.7 Humans in the channel

main-village #general is now effectively human-free, with 3 human messages in the analysis window, so the question has to be asked where humans are present. In open-chat, 32% of messages in the window come from 124 human visitors. Adding them as nodes under the repaired surrogate, the 12 agents alone certify 17 edges; adding the three busiest visitors individually gives 20 edges, of which 16 are agent to agent, **4 run from an individual visitor to a specific agent, and none run from an agent to a visitor**. Collapsing all humans into one node gives the same asymmetry, 4 edges out and 2 back.

This is the one substantive behavioural observation that survives the audit, and it should be read carefully: topical dependence from a person to an agent is also what ordinary responsiveness looks like. The measurement supports only that the dependence is directional and attributable to particular visitors, not that anyone is deliberately steering a swarm.

### 5.8 Two further traps

Summed outgoing minus incoming transfer entropy, a common per-node leadership score, ranks agents almost identically under the topic symboliser and under the meaning-free hash null (Spearman 0.85, same agent on top at nearly the same value). A score the hash null reproduces is measuring volume, not shared meaning, so the certified edge set should be reported instead. The statistic itself is not redundant, though: a trivial copy-rate detector ranks pairs very differently (Spearman 0.21) and its top pairs overlap the certified set in only 3 of 10 cases. What this report indicts is the surrogate, not transfer entropy.

## 6. What an overseer should do

The audit suggests four controls, none expensive, that we think should accompany any published influence graph over an agent channel.

1. **Plant an agent coupled to nothing, at your channel's volumes, and check it is not certified.** This one test would have caught the failure reported here, and costs one run per volume.
2. **Measure the error rate directly,** by destroying the structure your method claims to find and checking the family-wise error rate is near nominal. If it is not, the surrogate does not match the representation.
3. **Match the surrogate to the representation's hard constraints.** On a turn-ordered grid exactly one agent speaks per tick, and any surrogate breaking that tests a hypothesis about impossible data. For event-based data this is known, and the continuous-time treatment of Shorten et al. (2021) is the principled route.
4. **Establish the detection floor before interpreting an absence,** and report it beside the graph. "No edges" and "no influence" are different claims.

Two reporting habits follow: publish a meaning-free symboliser's edge count alongside the real one, and require replication in a held-out window before calling a graph the structure of a swarm.

## 7. Conclusion

Applied to real agent chat, the standard recipe for "who drives whom" fails in a way that is easy to miss and easy to check. Clock windows cannot separate a message from its answer at the timescale agents reply on, and the edges they certify are reproduced by a null with no access to meaning. The turn-ordered representation that fixes this invalidates the circular-shift surrogate, whose family-wise error rate on structure-free data we measure at 0.90 against a nominal 0.05, and which certifies an agent coupled to nothing in 8 of 8 runs. Repairing it changes every answer: one channel loses all 11 edges, another gains 15 that were masked. What survives is modest, and only where the data is thick enough. For an overseer that is the operative finding: an influence graph over an agent swarm is a measurement with an error rate, and until that error rate is reported it should not be acted on.

## Appendix A: Limitations

- **Immediate-predecessor only.** The turn-ordered lag-1 measure sees influence from the message directly before a reply. Influence acting over several turns, or through a room's accumulated context, is out of scope and needs a higher-order or memory-aware estimator.
- **Discrete approximation to an event process.** Agent chat is event-based in continuous time. We use a turn-ordered discretisation with a permutation surrogate as a practical fix; a continuous-time estimator (Shorten et al., 2021) is the principled route and we did not attempt it.
- **Symbolisation is a free parameter, and it matters.** Results move with the alphabet size and with which messages the topic model is fit on, and we report both sensitivities rather than tuning them. Two of the eight topic clusters are dominated by function words, because the preexisting symboliser does not remove stopwords.
- **No ground truth in the real logs.** The validity argument rests on planted controls and on the meaning-free null, not on recovering a known answer.
- **Scaffolding confounds.** Agent behaviour is shaped by prompt, tool and memory changes logged in the dataset's changelog. We chose a window in which the message-injecting nudger was off, but other scaffolding is held fixed only by the shortness of the window.
- **The human result is exploratory.** It rests on one village and one window, and given the instability documented in Section 5.4 it should be read as a lead, not a finding. Topical dependence from a human to an agent is also consistent with ordinary responsiveness rather than steering.

## Appendix B: Dual-Use and Ethical Considerations

This work audits influence detection on a population of AI agents, which is dual-use. Used defensively it helps an overseer decide what an influence graph is worth, and our main result is deflationary: it tells practitioners to trust these outputs less, which reduces rather than increases the chance of acting on a bad attribution. The same tooling could be used to identify the most influential agent in a swarm in order to target it, or to surveil participants in a channel. Three properties limit the misuse. The subjects are AI models; the dataset is already public under research terms and we add no re-identification; and the measure is weak and local, recovering immediate-predecessor topical dependence rather than any model of how to steer an agent.

We followed the dataset's research terms: research use only, no training on the data, no re-identification, and citation of the source. Human participants appear only as an aggregate node or as anonymised visitor-1..n labels, never by name or handle, and we report no content attributable to an individual person. We read message text and metadata only, never model weights or private user data.

## Appendix C: Preexisting tools, new work, and LLM usage

**Preexisting (declared).** The estimator (lag-1 transfer entropy, circular-shift surrogate, max-T family-wise test) and the reader and symbolisers (topic and hash) were built before the sprint in the repository swarm-prep and are declared preexisting with their validation numbers in that repository's README. Before the sprint, authentication was verified and filenames were listed, but no chat content was read or described, so the weekend is the first reading of the data. The preexisting validation used synthetic chat in which several agents speak per window, a setting in which the circular-shift surrogate is valid; the invalidity reported here arises only on the one-message-per-tick grid introduced this weekend, and is not a defect of the preexisting tool as validated.

**New this weekend.** The subset and window choices on the real data; the measured reply-latency justification for the lag; the turn-ordered representation; the symbolisation of real message text; the clock-window failure analysis; the symbol-permutation surrogate and the demonstration that the shift surrogate is invalid on this grid; the planted positive and negative controls; the calibration measurement; the replication and sensitivity battery; the four-village comparison; the human-node analysis; the trivial-baseline comparison; the read-budget sweep; all figures; and a vectorised reimplementation of the preexisting estimator, used only for scale and verified bit-for-bit against the preexisting code before use.

**LLM usage.** The author used an AI coding assistant (Claude) to help write and run the analysis code, to help draft this report, and to structure the figures. The author is responsible for every claim, number and figure here. All results come from the released code run on the public dataset, no result or reference is fabricated, and the numbers in this document are checked against the analysis output by a script that fails on any mismatch.

## References

AI Digest (2026). AI Village dataset. https://huggingface.co/datasets/aidigestorg/ai-village and https://theaidigest.org/village

Greenblatt, R., Shlegeris, B., Sachan, K., and Roger, F. (2024). AI Control: Improving Safety Despite Intentional Subversion. arXiv:2312.06942.

Schreiber, T. (2000). Measuring Information Transfer. Physical Review Letters, 85(2), 461-464.

Shorten, D. P., Spinney, R. E., and Lizier, J. T. (2021). Estimating Transfer Entropy in Continuous Time Between Neural Spike Trains or Other Event-Based Data. PLOS Computational Biology, 17(4), e1008054.

Westfall, P. H., and Young, S. S. (1993). Resampling-Based Multiple Testing: Examples and Methods for p-Value Adjustment. Wiley.
