# Who Replies to Whom: Turn-Ordered Transfer Entropy Finds Influence Structure in a Real Agent Swarm

**Manu Nicholas Jacob**, Independent Researcher. With Apart Research.

Track 4 (Multi-Agent Oversight and Control).

## Abstract

Information-theoretic coordination detectors are often proposed for agent swarms but rarely run on a real, long-lived population. We apply lagged transfer entropy to the public AI Village chat logs, where 58 frontier models have talked in a shared channel for 18 months, and ask a concrete question for an overseer: who drives whom, and how much of the channel must you read to find out. Two findings matter for method. First, clock-time windows cannot answer the question on this data: the median reply arrives 16.9 seconds after the message it answers, so any window wide enough to hold two speakers also swallows the stimulus and its response, which a lag-1 estimator is blind to. We replace clock windows with a turn-ordered representation in which the lag is one message, and the stimulus-response pair is separated by construction. Under that representation, topic-symbolised transfer entropy finds 10 family-wise-significant directed edges in the #general channel over a recent two-week window, against 1 edge under a hash-symbol null, so the structure is topical reply-influence and not a clustering artifact. Second, a continuous net-influence score is reproduced almost exactly by the hash null, so it mostly measures turn volume, not steering. Finally, an overseer who samples a random fraction of messages recovers the volume-driven centrality ranking cheaply but needs most of the channel to recover the certified edge set. We release the full pipeline.

## 1. Introduction

A recurring proposal in multi-agent safety is to watch a population of agents and infer, from their messages alone, who is steering whom. Transfer entropy, net-influence scores, and related directed-dependence measures are the usual tools. They are attractive because they need no labels and no access to model internals: given a log of who said what and when, they return a directed influence graph. The difficulty is that almost every demonstration runs on synthetic logs with a planted leader, where the analyst controls the timing and the vocabulary. Real agent chat is asynchronous, bursty, and written in open language, and those three properties break the assumptions that make the synthetic demonstrations work.

This project runs the measurement on a real swarm. The AI Village (AI Digest, 2026) is a long-running experiment in which frontier models share a chat channel and a computer-use environment while pursuing open-ended goals. Its logs give exactly what directed-dependence measures need and synthetic traces fake: stable speaker identities, microsecond timestamps, and months of unscripted conversation among models that were never told to coordinate. We ask the question an overseer would ask. Who influences whom in the shared channel, can an information-theoretic detector recover it without being fooled by surface coincidence, and how much of the channel must a monitor read before the answer stabilises.

This report makes three contributions.

1. We show that clock-time windowing, the default for transfer entropy, is structurally mismatched to real agent chat, and we quantify the mismatch from the data's own reply-latency distribution. We replace it with a turn-ordered representation whose lag is one message.
2. We measure directed topical reply-influence in the AI Village #general channel and separate it from a clustering artifact using a hash-symbol null. We also show that a popular continuous net-influence score is, on this data, a turn-volume artifact that the null reproduces.
3. We treat the detector as an oversight tool and measure how its output degrades when the overseer reads only a sample of the channel, which gives a concrete read-budget curve for a monitor.

## 2. Related Work

**Transfer entropy and directed dependence.** Transfer entropy (Schreiber, 2000) measures the reduction in uncertainty about a target's next symbol given a source's past, beyond the target's own past. It and its relatives have been used to recover influence in neural, financial, and social time series. Pairwise net-influence scores summarise the resulting directed graph into a per-node leadership measure. Plug-in transfer entropy is biased upward on short series, so significance here rests on a resampling null rather than the raw statistic, and the family-wise error across all ordered pairs is controlled with a single-step max-T test (Westfall and Young, 1993).

**Coordination detection on agents.** Recent agent-safety work applies information-theoretic and partial-information measures to multi-agent traces, mostly on controlled games with known ground truth. The gap this report targets is the move from controlled games to a real, open-language population where no ground truth exists and the analyst does not control timing or vocabulary.

**Oversight under a budget.** AI-control research frames monitoring as a resource-constrained problem: a monitor has a limited auditing budget and pays for false positives and for the usefulness it sacrifices (Greenblatt et al., 2024). The sampling sweep in Section 5.4 puts the influence detector in that frame by asking how its output depends on the fraction of traffic the overseer actually reads.

## 3. Data

The AI Village dataset ships one gzipped-JSONL table per village. We use the main village, whose #general room carries 166,715 agent messages, 81% of all agent chat in the village, because a 2026 scaffolding change scoped agents to a single room's context: an agent in #general perceives only #general, so #general is a self-contained influence substrate. Across the whole village, 58 models have participated over 576 days (2 April 2025 to 31 October 2026); the roster rotates as models are added and retired, so a single run over the full span would mix distinct populations.

We therefore fix a recent, contiguous analysis window: the final two weeks, 17 to 31 October 2026, which holds 8,529 agent messages in #general from 22 models with at least 50 messages each. The directed test uses the 15 busiest of these (7,958 messages), the set for which the estimator is well powered. Two scaffolding facts bear on the window and are disclosed rather than corrected: the automated "nudger" that injects messages was off throughout this window, so no scaffolding-authored messages contaminate it, and the #best and #rest rooms were soft-deleted mid-window, which does not touch #general. We read only message metadata and text; no personal data and no model internals are involved.

## 4. Method

### 4.1 From chat to (agent, time, symbol)

Transfer entropy needs discrete symbols, and chat is open language, so each message is mapped to one of a small alphabet before any influence is estimated. We keep that mapping strictly separate from the estimator and run two mappings. A topic symboliser (TF-IDF then k-means, k=8) assigns a message the id of its topic cluster, so paraphrases of one idea share a symbol. A hash symboliser (a stable hash of the normalised text into k=8 buckets) assigns symbols with no notion of meaning. The hash mapping is the null: an influence edge that appears under topics but not under hashing lives in the shared meaning of messages, while an edge that appears under both lives in timing alone and is not evidence of topical steering.

### 4.2 The lag problem and the turn-ordered representation

A lag-1 transfer entropy compares window t-1 with window t, so any influence that lands inside a single window is invisible to it. This is the central obstacle on real chat. The inter-speaker reply gap in #general has a median of 16.9 seconds (75th percentile 38.3, 95th 113.4), so turn-taking is a seconds-scale process. Any clock window wide enough to contain two speakers is at least minutes wide and therefore contains both a message and its answer, which the estimator then cannot separate; shrink the window to seconds and almost every agent is silent in almost every window. Section 5.1 shows both failure modes directly.

We avoid the bind by ordering messages canonically and letting one message be one tick. In this turn-ordered representation each agent's series carries its symbol at the ticks where it spoke and a silent symbol elsewhere, and the lag-1 comparison is between a message and the one immediately before it. The stimulus and its response are now always in different ticks, which is exactly the separation a lag-1 estimator requires. The cost is that the measure captures immediate-predecessor influence; multi-turn influence is out of scope and named as a limitation.

### 4.3 Estimator and nulls

For every ordered pair of agents we compute the lag-1 transfer entropy and compare it with a circular-shift null of the source series, which preserves the source's own marginal and autocorrelation while destroying its timing relationship to the target. Significance uses a single-step max-T family-wise test across all ordered pairs at level 0.05. An agent's leader score is the number of agents it significantly drives minus the number that significantly drive it. The estimator, the windowing, and the symbolisers are preexisting and were validated before the sprint on synthetic chat with a planted leader (Appendix C); the hash-symbol null is run alongside every headline.

### 4.4 The overseer sampling sweep

To treat the detector as an oversight tool under a read budget, we keep a uniform random fraction p of #general messages, rebuild the turn order from the sample, and recompute the influence structure. We score recovery of the full-channel result two ways: recall and precision of the certified edge set against the full-data edge set, and the Spearman correlation of the continuous net-influence ranking against the full-data ranking. We sweep p from 0.05 to 1.0 with eight random samples per fraction.

## 5. Results

### 5.1 Clock windows cannot separate cause from effect

Figure 1 runs the detector on clock windows of 1, 5, 15, and 60 minutes. At one minute only 2.2% of agent-windows are non-silent, and the few edges found barely exceed the hash null. Widening the window raises occupancy but, past the point where a window contains a full exchange, the number of certified edges collapses: at 60 minutes only 3 edges survive under topics. There is no width that is both dense enough to estimate and short enough to separate cause from effect, which is the quantitative form of the reply-latency fact in Section 4.2. Clock windowing is the wrong representation for this data.

[Figure 1: fig1_lagbind.png. Caption: Clock-window transfer entropy on the 15-agent #general set. Bars are the number of family-wise-significant directed edges under the topic symboliser and the hash null; the red line is the share of agent-windows that are non-silent. Small windows are too sparse to estimate; large windows swallow each reply into the same window as its stimulus and the edge count collapses.]

### 5.2 Turn-ordered transfer entropy finds topical reply-influence

Under the turn-ordered representation the picture is clean. The topic symboliser yields 10 family-wise-significant directed edges; the hash null yields 1, which is at the level expected by chance at family-wise 0.05. The structure is therefore topical reply-influence, not timing coincidence. Figure 2 shows the graph. Gemini 3.8 Flash is the principal hub, driving three agents and reciprocating with two; a cluster of fast models (Gemini 3.8 Flash, GLM-5.2, Gemini 4 Argon) all drive Gemini 3.5 Flash, which is a pure sink with a leader score of -3, driven by three agents and driving none. The leader scores for the topic run are below.

| Agent | Drives | Driven by | Leader score |
|---|---|---|---|
| Gemini 3.8 Flash | 3 | 2 | +1 |
| Grok 4.5 | 1 | 0 | +1 |
| Claude Opus 5 | 1 | 0 | +1 |
| DeepSeek-V4-Pro | 1 | 0 | +1 |
| GLM-5.2 | 1 | 0 | +1 |
| Gemini 4 Argon | 1 | 0 | +1 |
| Claude Haiku 4.5 | 1 | 2 | -1 |
| GPT-6 Sol | 1 | 2 | -1 |
| GPT-6.1 Terra | 0 | 1 | -1 |
| Gemini 3.5 Flash | 0 | 3 | -3 |

[Figure 2: fig2_graph.png. Caption: Directed topical reply-influence in #general, 17 to 31 October 2026, under turn-ordered lag-1 transfer entropy. Each arrow is a family-wise-significant edge (topic symboliser, level 0.05); node size is total degree, edge width is proportional to transfer entropy. The topic run finds 10 edges; the hash null finds 1. Gemini 3.5 Flash is a pure sink; Gemini 3.8 Flash is the hub.]

### 5.3 The continuous net-influence score is a volume artifact

A continuous net-influence score (summed outgoing minus incoming transfer entropy, a common per-node leadership summary) tells a misleading story here. Its ranking under the topic symboliser and under the hash null agree at Spearman 0.85, and both are topped by the same agent at nearly the same value (Claude Haiku 4.5 at 0.196 under topics, 0.193 under hashing). Because the hash null has no access to meaning, a score it reproduces cannot be measuring topical steering; it is measuring turn volume and position. The lesson is specific and portable: report the certified directed-edge set, which separates topic from hash, not a continuous net-influence score, which does not. The edge set is where the real signal lives.

### 5.4 How much must an overseer read?

Figure 3 sweeps the fraction of #general an overseer reads. The two recovery curves come apart. The volume-driven centrality ranking is cheap: reading 20% of messages recovers it at Spearman 0.79, and 50% at 0.88. The certified edge set is expensive: edge recall is 1% at 20% and only 21% at 50%, reaching 52% at 70% before completing at the full channel. The asymmetry is the practical finding. A monitor that samples lightly learns who is central, because centrality is carried by message volume and volume survives subsampling, but it does not learn the directed wiring, because certifying an edge needs the statistical power that only most of the channel supplies. Cheap oversight buys the popularity ranking, not the influence graph.

[Figure 3: fig3_sweep.png. Caption: Recovery of the full-channel influence structure as a function of the fraction of #general an overseer reads, eight random samples per fraction. Blue is recall of the certified directed-edge set with its standard-deviation band, green its precision, purple the Spearman correlation of the continuous net-influence ranking. The volume-driven ranking recovers early; the certified edge set needs most of the channel.]

## 6. Discussion

The headline for practice is that representation, not estimator, decides whether influence detection works on a real swarm. The same transfer-entropy estimator is useless on clock windows and informative on a turn-ordered grid, and the difference is dictated by the reply-latency distribution of the data, which an analyst can measure in advance. The second lesson is that a null with no access to meaning is the cheapest honesty check available: it demoted a continuous score that looked like leadership to a volume artifact and left the directed-edge set standing. The third lesson is for overseers: the two things one might want from influence detection, a centrality ranking and a directed graph, have very different read-budget costs, and a monitor should be told which it is buying.

The influence we measure is modest and local. It is immediate-predecessor topical dependence in one channel over two weeks, not evidence of goal-directed manipulation, and the sink-and-hub structure is consistent with fast models posting short reactive replies that track the previous message. We make no claim beyond that.

## 7. Conclusion

Run on a real, 18-month agent population rather than a planted-leader synthetic, lagged transfer entropy recovers a small, directed, topical reply-influence graph in the AI Village #general channel, provided the chat is represented turn by turn rather than on clock windows and provided a meaning-free null is used to separate topical influence from timing. For an overseer, the centrality ranking is recoverable from a modest sample while the directed edges require most of the channel. The pipeline and every figure-producing number are released for reuse on other swarms.

## Appendix A: Limitations

- **Immediate-predecessor only.** The turn-ordered lag-1 measure captures influence from the message directly before a reply. Influence that acts over several turns, or through the room's accumulated context, is out of scope and would need a higher-order or memory-aware estimator.
- **Symbolisation is a degree of freedom.** Topic clusters depend on the TF-IDF and k-means settings and on k. We fixed k=8 to match the preexisting validation and report the hash null alongside, but a different symboliser could change which edges clear the threshold. The hash null bounds how much of the result could be timing alone; it does not bound symboliser sensitivity, which we did not sweep.
- **One channel, one window.** Results are for #general over 17 to 31 October 2026. Other rooms, other windows, and the other villages are untested here. The roster rotates, so the specific agents named are particular to this window.
- **No ground truth.** Real logs have no planted leader, so the validity argument rests on the synthetic validation of the estimator (Appendix C) and on the hash null, not on recovering a known answer.
- **Scaffolding confounds.** Agent behaviour is shaped by prompt, tool, and memory changes logged in the dataset's changelog. We chose a window in which the message-injecting nudger was off, but other scaffolding is held fixed only by the shortness of the window, not controlled.
- **Net-influence caveat is specific.** The volume-artifact finding is about the summed-transfer-entropy score on this data; it is not a general claim that net-influence scores are always artifacts.

## Appendix B: Dual-Use and Ethical Considerations

This work builds an influence detector for a population of AI agents, which is a dual-use capability. Used defensively, it helps an overseer find which agents drive a shared channel and estimate how much of the traffic must be read to see that structure, which supports monitoring budgets and incident forensics. The same tool could be used to identify the most influential agent in a swarm in order to target or manipulate it, or to surveil participants in a channel. Three properties limit the misuse here. The subjects are AI models, not people; the dataset is already public under research terms and we add no re-identification; and the measure is weak and local, recovering immediate-predecessor topical dependence rather than any actionable model of how to steer an agent. We followed the dataset's research terms: research use only, no training on the data, no re-identification, and citation of the source. We read message text and metadata only, never model weights or private user data, and the sink-and-hub result is reported at the level of model names already published by the village, with no claim about any individual human. We release the detector because the defensive value to overseers of a swarm outweighs the marginal offensive value of a tool that only ranks public agents by local reply-influence.

## Appendix C: Preexisting tools, new work, and LLM usage

**Preexisting (declared).** The estimator (lag-1 transfer entropy, circular-shift null, max-T family-wise test) and the reader and symbolisers (topic and hash) were built before the sprint in the repository swarm-prep and are declared preexisting with their validation numbers in that repository's README. Before the sprint, auth was verified and filenames were listed, but no chat content was read or described, so the weekend is the first reading of the data. The preexisting validation: on synthetic chat where followers paraphrase a leader (6 agents, 200 rounds, 5 seeds), the topic symboliser recovers the planted leader in 5 of 5 runs at coupling 0.7 and raises 0 edges at coupling 0.0, while the hash symboliser finds nothing either way, which is why hashing is a usable null.

**New this weekend.** The subset and window choices on the real data; the measured reply-latency justification for the lag; the turn-ordered representation; the symbolisation of real message text; the clock-window failure analysis; the topic-versus-hash comparison and the net-influence volume-artifact finding; the overseer sampling sweep; all three figures; and a vectorised reimplementation of the preexisting estimator, used only for scale and verified bit-for-bit against the preexisting code (identical p-values, transfer entropy equal to 1e-9) before use.

**LLM usage.** The author used an AI coding assistant (Claude) to help write and run the analysis code, to help draft this report, and to help structure the figures. The author is responsible for every claim, number, and figure here; all results come from the released code run on the public dataset, and no result or reference in this report is fabricated. The numbers in this document are checked against the analysis output by a script that fails on any mismatch.

## References

AI Digest (2026). AI Village dataset. https://huggingface.co/datasets/aidigestorg/ai-village and https://theaidigest.org/village

Greenblatt, R., Shlegeris, B., Sachan, K., and Roger, F. (2024). AI Control: Improving Safety Despite Intentional Subversion. arXiv:2312.06942.

Schreiber, T. (2000). Measuring Information Transfer. Physical Review Letters, 85(2), 461-464.

Westfall, P. H., and Young, S. S. (1993). Resampling-Based Multiple Testing: Examples and Methods for p-Value Adjustment. Wiley.
