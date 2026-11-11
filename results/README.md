# Archived results

The [oscillator summary](summary/oscillator_plateau_summary.csv) and [surrogate summary](summary/surrogate_arm_summary.csv) are byte-preserved transcriptions of reported aggregates. Phase 2 compared them with archived diagnostics and trial-level outputs. Publication preparation verified file integrity without recomputing statistics.

## Oscillator

The [diagnostics](../toy_oscillator/run/results/diagnostics.csv) record three seeds, two feedback settings and four plateau durations. Each run carries state across 25 coupling plateaus. Endpoint and sampled-final-fifth areas use distinct estimators. Late-window areas declined from duration 18 to 144 in all six paired comparisons. Intermediate values and endpoint areas are non-monotonic. The OFF endpoint average rises from 72 to 144. Feedback comparisons also change effective coupling.

Inspect the [sweep](../toy_oscillator/run/results/sweep.csv), [trace](../toy_oscillator/run/results/trace.csv), [figure](../toy_oscillator/run/figures/area_vs_plateau.png) and [settings manifest](../toy_oscillator/run/results/manifest.json).

## Programmed surrogate

The [trial metrics](../synthetic_agent/run/trial_metrics.csv), [summary](../synthetic_agent/run/summary.csv), [round trace](../synthetic_agent/run/trace.csv) and [evidence fixtures](../synthetic_agent/run/evidence.jsonl) describe saved synthetic trials. Consensus requires seven of nine votes. Correctness is the proportion of votes matching fixed truth. Post-correction outcomes average rounds 7–16. Recovery is the delay to two consecutive correct-consensus rounds, capped at ten. Persistence counts wrong-consensus rounds after correction across an already-wrong boundary, with zero when that boundary is absent.

The transcription rounds B and D wrong-consensus means to 0.001 and 0.007. Reported percentages are 0.14% and 0.69%. C is 10.0% and A is 0%. Paired intervals use 2,000 trial-level bootstrap samples. D deduplicates current and historical source mentions, so its comparison with C combines both channels.

These studies measure separate constructs. Stable attractors, genuine hysteresis, chaos and collective LLM objective drift remain unverified. See [reproduction](../docs/REPRODUCIBILITY.md) and [verification](../docs/VERIFICATION.md).
