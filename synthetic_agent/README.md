# Programmed surrogate

Nine programmed voting agents receive source-tagged binary evidence. Four rules share matched trial fixtures. Rule A uses private evidence, B adds current broadcasts, C adds historical peer citations, and D takes the maximum weight for each source across channels. A fixed correction is visible from round 7.

From this directory, the reproduction entrypoint is `python -B run_pilot.py --out run_repeat`. The archived environment used Python 3.13.17 and NumPy 2.5.4. This publication script has not been executed. It retains the experiment logic and four data writes while removing manuscript-text generation.

- [Fixtures](run/evidence.jsonl)
- [Round traces](run/trace.csv)
- [Trial metrics](run/trial_metrics.csv)
- [Summary statistics](run/summary.csv)
- [Derived archive manifest](run/manifest.json)
- [Provenance](../docs/PROVENANCE.md) and [reproduction scope](../docs/REPRODUCIBILITY.md)

The manifest describes retained outputs from the archived source, with separate archived and publication source hashes. A future execution writes a fresh runtime manifest, whose schema follows the script. The model contains no LLM. Robustness to correction weight and source reliability remains untested.
