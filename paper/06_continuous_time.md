# Section 6: Continuous time

Run 7 November 2026. The sprint report's Appendix A says a continuous-time estimator is the
principled route for event data and that we did not attempt it. We have now attempted it, and the
answer is neither of the two we expected.

## The result

| | main-village #general | open-chat #busiest |
|---|---|---|
| Discrete, turn-ordered, symbol-permutation + max-T | **2** edges | **18** edges |
| Continuous time (CoTETE), surrogates + max-T | **0** | **0** |
| Overlap / additions / losses | 0 / 0 / 2 | 0 / 0 / 18 |
| Highest observed z | 3.062 | 3.980 |
| max-T threshold (95th of max null) | 4.171 | 4.308 |

Both channels: 210 ordered pairs, 100 surrogates per pair, 15 agents, 7,958 and 7,735 events. The
discrete side was reproduced from the same export with the audit's own estimator, giving exactly 2
and 18 on one agent-id space, so this is a comparison and not two separately-named answers.

## Why zero is not disagreement

**The two estimators consume different variables.** CoTETE's entire public API takes
`Vector{Float64}` of event times. There is no mark or symbol channel. The audit's discrete transfer
entropy runs on a grid whose per-tick value is the agent's **topic symbol** when it spoke. So this
is not one variable under two time representations. It is two variables.

The decisive control is to give the audit's own estimator exactly CoTETE's information. Collapse the
grid to timing only, every spoken symbol becoming a single `SPOKE` code, and re-run:

- **Timing only, symbol-permutation null: 0 edges in both villages**, matching CoTETE.
- **Timing only, circular-shift null: 12 and 3 edges.** The invalid null is the one that responds
  to timing.

So the two methods agree. What they agree on is that **nothing is detectable in event timing
alone**, and the audit's edges live in symbol correspondence, which the continuous-time estimator
cannot read.

## The finding that belongs in the abstract

On timing-only data the symbol-permutation surrogate is **exactly degenerate**. Permuting identical
symbols is the identity, so the null and the observed statistic coincide: `max|null - obs| = 0`,
`sd = 0` across all 210 pairs, `p = 1.0` everywhere. The single nonzero z, 0.997, is float
cancellation noise.

**The repair this paper recommends has zero power against timing structure by construction.**

That is a real limitation and it should be stated plainly rather than discovered by a reader. The
two nulls partition the hypothesis space: symbol permutation tests symbol correspondence, the
circular shift partly tests timing. A practitioner who adopts the repair is choosing to test one and
abandon the other. The honest recommendation is therefore narrower than "use the permutation
surrogate": it is "use it for the symbol question, and understand that you have stopped asking the
timing question".

## Robustness

- **History length is not the cause.** Sweeping `l_x = l_y = 1, 2, 3` on four audit-certified edges,
  the highest z anywhere was 2.63 against thresholds of 4.17 and 4.31. At `l = 3` one pair was not
  estimable at all, with 2001 of 2001 observed attempts failing.
- **Ranking agreement is weak.** Spearman rho of z across all 210 pairs: **-0.049** (main-village),
  **+0.038** (open-chat). Main-village's 2 edges sit in the bottom 9% of continuous-time z
  (permutation p = 0.959). Open-chat's 18 rank modestly high (mean normalised rank 0.628,
  p = 0.032) but none reaches threshold.

## Three caveats the paper must carry

1. **A real bug in CoTETE v0.2.3.** `make_surrogate!` enlarges `exclusion_windows`; on sparse bursty
   trains those windows can empty the `inrange` result, so `maximum(colwise(...))` at
   `CoTETE.jl:739` throws `ArgumentError: reducing over an empty collection`. One throw kills a
   whole pair and the public entry point has no handling. The first campaign lost 5 of 16 shards to
   it. The surrogate loop was reimplemented with redraw-on-failure; 124 draws were retried. **This
   should be reported upstream.**
2. **One pair's null is conditional.** An open-chat pair needed **1,936 failed draws for 100
   successes**, a 4.9% success rate. Those surrogates are conditioned on being estimable, so the
   null is biased in an unknown direction, and that pair happens to carry open-chat's highest z
   (3.980). Flagged in the results file.
3. **Point estimates are stochastic to about 17%.** Twenty independent estimates of one pair: mean
   -4.74e-4, sd 8.11e-5, range -6.34e-4 to -3.50e-4. Do not quote a single-shot value to more than
   two significant figures. 111 of 210 point estimates are negative, which CoTETE's own
   documentation explains as expected Kraskov bias when the target depends on its own history and is
   conditionally independent of the source.

`add_dummy_exclusion_windows = true` throughout, CoTETE's own parameter, so observed and surrogate
statistics are computed under identical exclusion. Without it the surrogate distribution is not a
valid null for the observed value.

## Cost, for the reproducibility section

The whole certified comparison is about **one CPU-hour**. Julia install plus clone plus six
dependencies: two minutes. All 210 point estimates: 86.6 s. Full campaign, two villages, 210 pairs,
100 surrogates: **319 s wall** at 20-way parallelism, 3,666 s of estimator work. The audit's
discrete recompute: 12 s. **Compute was never the blocker; the blocker was that CoTETE.jl is not in
the Julia General registry and needs a pinned clone with submodules.**

## What a true same-variable comparison would need

CoTETE cannot be given the symbols. An apples-to-apples test needs either a **marked** point-process
transfer-entropy estimator, or a construction splitting each agent into per-symbol subprocesses,
which is 210 x 64 estimates plus a much larger family-wise correction. That is a separate project,
not a parameter change, and the paper should say so rather than leave it as an obvious next step.

## Artifacts

- `../facts_cotete.json`, committed: the aggregate result with agents under opaque labels and no
  corpus identifiers.
- `../cotete_export/cotete_results.json` and the two TE matrices, **gitignored**: they carry 32
  corpus agent and room UUIDs, and no committed `facts_*.json` in this repository contains any. The
  exporter and the scripts are documented so anyone with their own dataset access can regenerate
  them.
- CoTETE.jl at tag v0.2.3, commit `2c7234d`, submodule `5f8535d`.
