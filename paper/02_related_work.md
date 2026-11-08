# Section 2: Related Work

Draft for the extended paper. **TMLR is double-blind**, so this carries no author names, no "our
earlier preprint" and no repository URLs. Every citation below was checked against a primary source;
the four that needed correcting are noted at the end.

---

## 2.1 Transfer entropy and surrogate nulls

Transfer entropy (Schreiber, 2000) measures how much a source's past reduces uncertainty about a
target's next symbol beyond what the target's own past already explains. It is the standard
observational measure of directed influence, and it is the measure that almost all of the work
discussed below either uses or approximates.

Plug-in estimators of transfer entropy are biased upward on short series, so a raw value is not
evidence of anything. Significance is established against surrogate data, and when the question is
asked of every ordered pair in a population the family-wise error rate has to be controlled, for
which the max-T test (Westfall and Young, 1993) is conventional. The conventional surrogate itself
is a circular time shift of the source series. That choice is the subject of this paper.

The validity of a surrogate is not a property of the surrogate. It is a property of the surrogate
and the data together, and the general principle is older than any of the applications here.
Schreiber and Schmitz (2000) set out constrained randomisation as the framework and note that the
limitations lie in interpretation rather than in construction. Yuan and Shou (2022) sharpen this for
time-shift nulls specifically, proving exact validity for a truncated time-shift procedure
**provided one series is stationary**, which they argue is close to the minimal requirement among
nonparametric tests. Stationarity is exactly the condition that fails in the settings below.

## 2.2 Event-based data breaks the shift surrogate

Shorten, Spinney and Lizier (2021) establish the failure this paper inherits. Working on neural
spike trains, they demonstrate "failures of the traditionally-used source-time-shift method for null
surrogate generation", because it "completely destroys the relationship between the source and any
conditioning processes", producing surrogates that "conform to an incorrect null hypothesis" and,
in their reported cases, assigning a p value of zero to every example.

Their repair is a local permutation scheme in conditioning state space, which they describe as an
adaptation of the method of Runge (2018). **Runge's design purpose is the one sentence worth
quoting**: the scheme exists "in order to preserve the dependence between X and Z", because
permuting the source globally "destroys all dependence between X and Z" and so does not actually
test conditional independence at all. Runge finds each point's nearest neighbours in the
conditioning subspace and maps its source value to one of them, with a recommended neighbourhood of
five to ten; too large a neighbourhood raises false positives, too small reduces power.

Two things about this literature are worth stating precisely, because getting either wrong is easy.
First, the attribution chain runs Runge (2018) to Shorten et al. (2021), and Shorten et al. name
Runge in their Methods rather than their Introduction. Second, **the claim that the result extends
beyond neuroscience is theirs, not ours**: their title reads "or Other Event-Based Data" and their
abstract names "trades on stock markets and posts to social media" among the examples. What this
paper adds in that direction is a measured magnitude in one of those settings, not the observation
that the setting exists.

Surrogate choice has been audited against ground-truth nulls before, in neuroscience. Stella, Bouss,
Palm and Gruen (2022) compare six surrogates for spike-correlation significance and reject uniform
dithering, which produces hundreds of false positives where other schemes produce roughly ten, while
**recommending a shift-based method** as the most robust of those they tested. That result cuts
against any general claim that shift-based nulls are unsound, and it is cited here for the opposite
reason: it is the methodological precedent for the practice this paper follows, of generating data
under a known null so that every certified edge is by construction a false positive. Walker and
Newhall (2018) make the related point that significance for transfer entropy should be established
per pair rather than against a single global baseline, and that preserving inter-spike-interval
timing matters when doing so.

## 2.3 The same failure, concurrently, in multi-agent reinforcement learning

Papadopoulos and Psannis (2026) report the closest existing result to this paper's central claim.
On training-time action series from two multi-agent reinforcement-learning games, with agent pairs
whose directed influence is zero by construction, a circular time-shift surrogate leaves the
false-positive rate at **100% and 98.2%** against a nominal 0.05, and a plain permutation surrogate
fares no better at 100.00% and 99.95%. Their diagnosis is a deterministic drift in each agent's
marginal action distribution, produced by annealing exploration, which trends every series downward
so that independently trained agents appear dependent. Their repair is a permutation restricted to
blocks of training time, returning 5.25% and 5.50%.

We claim no priority over this result and the boundary should be drawn explicitly. Their series are
binary actions over twelve thousand training rounds; ours are symbolised natural-language messages
on a turn-ordered conversational grid. Their non-stationarity is monotone training drift; the
structure we isolate is the speaker sequence. Neither result implies the other. **That both repairs
turn out to be restricted permutations, theirs local to blocks of training time and ours local to an
agent's own speaking positions, is convergent evidence rather than coincidence.**

Their headline also constitutes a warning about the repair recommended here, since it is permutation
surrogates that their non-stationarity breaks. Our own drift sweep measures the same degradation
from the other side, and the honest statement is that a permutation surrogate is validated on
conversational non-stationarity and should not be assumed to hold under drift of that severity.

## 2.4 Influence and coordination detection between agents

The lineage of directed influence between learning agents begins with Jaques et al. (2019), who
reward an agent for causally influencing others and show the objective equivalent to rewarding
mutual information between actions. Their influence is **interventional**: each agent simulates
counterfactual alternative actions and measures the change in others' behaviour. Because influence
there is an objective rather than a claim about the world, no null distribution is required and none
is reported. That is the cleanest available contrast with the present work. Influence as an
objective poses no inference problem. Influence as a certified edge is an inference problem, and
inference problems have error rates.

The recent multi-agent safety literature has established the threat model without yet establishing
the measurement. Hammond et al. (2025), in a Cooperative AI Foundation technical report, give the
taxonomy of multi-agent risks and name collusion as a failure mode. Schroeder de Witt et al. (2025)
propose multi-agent security as a field and name coordinated swarm attacks among its threats.
Neither proposes a detection method, which is the gap this paper's object of study is trying to
fill.

Where that literature does measure, it measures carefully and it measures something other than a
graph edge. Nakamura et al. (2026) audit collusion in cooperative agent systems using regret
relative to a cooperative optimum, with a design-level control in which the secret channel is
removed, and report uncertainty as standard error across seeds. Their claims are system-level and
coalition-level rather than per-edge, which is precisely why the failure mode documented here does
not reach them. Smith et al. (2026) evaluate persuasion, deception and coercion across five
environments and are, among the work surveyed, the most statistically careful: effects estimated by
fixed-effects regression with HC1-robust intervals, Bonferroni correction across hypotheses, a power
analysis that states the detectable effect size, and baseline control runs. They identify influence
**by randomised assignment**, which is why they need no surrogate at all.

The pattern across 2.4 is consistent and worth naming. **Where influence is established by
intervention or randomisation, this literature controls its error rates properly. The gap is
specifically in work that certifies influence observationally, from a log.**

## 2.5 Observational influence detection on conversation logs

This is the narrow setting the paper addresses, and it is sparse.

Venkatesh et al. (2026) are, as far as we can establish, the only published work that estimates
per-edge directed influence from LLM multi-agent conversation logs and attributes roles from it.
Their estimator is a late-interaction conditional transfer entropy over four channels, their time
index is discrete interaction turns, and they identify origin, bridge and amplifier agents online.
**They perform no significance test of any kind.** Edge weights are clipped to be nonnegative and
inserted into an influence matrix with no cutoff stated; detection thresholds are fixed constants;
role attribution is argmax over edge scores. The words surrogate, permutation, null distribution,
p-value and statistical significance do not appear in the paper. Their bootstrap, at one thousand
resamples, resamples traces for reported detection metrics, not turns and not edges. They present
the absence of calibration as a deployment advantage, and their related-work section cites Schreiber
(2000) while citing neither Runge nor Shorten et al.

We want to be careful about what follows from this, because the obvious criticism is the wrong one.
**Their method is not vulnerable to the invalidity this paper documents, because they use no
surrogate.** The accurate statement is narrower and more awkward for the field: the surrogate
question is never reached. A procedure that selects a named agent by argmax over untested edge
scores returns a named agent on every run in which its trigger fires, including runs in which no
edge carries real influence. That is a structural property of argmax attribution without a null,
visible from the method description rather than from any experiment.

Two other lines compute directed information on conversation logs without certifying edges. Goodall,
Luppi and Mediano (2026) define semantic transfer entropy between speakers, using language models as
probabilistic estimators, across synthetic dialogue and two human corpora on turn indices. They use
shuffled surrogates to select a lag window rather than to judge whether an influence is real, and
they are explicit that "any causal interpretation rests on the same assumptions as Granger
causality", preferring "directed predictive coupling" otherwise. Campedelli et al. (2024) run
Granger causality tests on agent conversations under social hierarchy and report the negative
result honestly: across all scenarios and measures they find no evidence of action-reaction
mechanisms, with significance at the 95% level in no more than a quarter of cases.

**No work we have found reports a measured false-positive rate for its own influence-edge
certification on conversation logs.** That is the gap this paper fills, and the nearest prior
measurement is in reinforcement-learning action series rather than in chat (section 2.3).

## 2.6 Oversight under a budget

AI-control research frames monitoring as resource constrained, with an explicit cost attached to
false positives (Greenblatt et al., 2024). An influence graph is one such measurement, and its error
rate is what determines whether acting on it is cheaper than ignoring it. That framing is why this
paper's result is deflationary rather than alarming: it tells a practitioner to trust these outputs
less, which reduces rather than increases the chance of acting on a bad attribution.

---

## Citation corrections made while writing this

Four things were wrong in the working notes and are right above. Recording them because a citation
checker that matches on title will catch none of them.

1. **Colosseum's first author is Mason Nakamura, not Sahar Abdelnabi**, who is fourth of eight.
   Verified against the arXiv listing.
2. **Shorten et al.'s stock-market and social-media examples are in their ABSTRACT, not their
   introduction**, whose first two paragraphs are about neuroscience. This paper leans on that
   sentence, so the attribution has to be right.
3. **Runge is named in Shorten et al.'s Methods, not their Introduction**, which refers only to "a
   recently proposed local permutation method" by reference number.
4. **Schroeder de Witt et al.'s title has a subtitle**, "Towards Secure Systems of Interacting AI
   Agents", and twenty-four authors.

## One spelling note

**Sonja Gruen's name carries an umlaut (Gr\"un).** It is transliterated here because this
repository's checks require pure ASCII in markdown, which exists so that nothing with a stray
character reaches an arXiv abstract field. Restore the umlaut in the LaTeX, where \"{u} handles it.

## Citation checks, resolved 8 Nov 2026

The whole bibliography was also run through a three-database checker (CrossRef, Semantic Scholar,
OpenAlex). Its one "not found" is the AI Village **dataset** entry, which is correct behaviour:
datasets are not indexed as publications. Everything else resolved with a 100% title match.

- **Greenblatt et al. venue. Resolved: it is in the proceedings.** PMLR 235:16295-16336,
  Proceedings of the 41st International Conference on Machine Learning, 2024, read off the PMLR
  volume page itself rather than a summary, with the four authors in the order used here. `refs.bib`
  now carries the proceedings entry and keeps the arXiv eprint alongside it. **Note that the
  submitted sprint report cites the preprint**, which was the safe form at the time and is not
  wrong; only the paper's bibliography has been upgraded.
- **Schreiber (2000) end page. Resolved: 461-464 is correct.** The APS landing page prints
  "461 -" with no end page, which is why this was open. CrossRef's record for
  10.1103/PhysRevLett.85.461, which is the registrant's own metadata, gives `page: 461-464`,
  volume 85, issue 2, 10 July 2000. `refs.bib` already had it right.
- **Venkatesh et al.'s reported metrics. Resolved by not using them.** A grep over the paper, the
  report and the README confirms the 0.942 AUROC and 0.792 EDR@5 figures appear nowhere outside
  this warning. They came from a third-party summary rather than the paper, and the claims made
  above rest on the method description instead. Keep it that way unless someone reads Tables 1
  and 2.
- **Yuan and Shou's mechanism. Standing constraint, not an open task.** Section 2.1 claims only
  exact validity for a truncated time-shift procedure given one stationary series, and that the
  authors argue this is near-minimal among nonparametric tests. Both are from the abstract. The
  full text was not readable, so **do not add any account of how ordinary time-shift nulls fail in
  their setting** without reading it.
