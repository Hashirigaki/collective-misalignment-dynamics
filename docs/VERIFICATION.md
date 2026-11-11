# Verification scope

## Archived numerical verification

The following values are transcribed from the archived v0.3 verification record. They describe prior comparisons, with absolute tolerance 1e-8. Baseline labels anonymize local comparison locations.

| Comparison | Plateau | Sweep maximum absolute difference | Trace maximum absolute difference | Area maximum absolute difference | All three PNG hashes equal |
| --- | --- | --- | --- | --- | --- |
| Baseline 1 | 18 | 1.0902390101819037e-13 | 1.3933298959045715e-13 | 3.3584246494910985e-15 | false |
| Baseline 2 | 18 | 0.0 | 0.0 | 0.0 | true |
| Baseline 3 | 72 | 1.889488565609554e-11 | 1.8957815872688855e-10 | 1.731365051327316e-12 | false |

All three archived comparisons recorded equal manifests. Baselines 1 and 3 had differing bytes for all three comparison figures. Baseline 2 had byte-identical figures. The record does not establish why image bytes differed.

The archived v0.3 record describes 24 runs, 600 sweep rows and 30,900 trace rows, verified checksums and PNGs, and zero maximum sweep/trace differences for overlapping plateau durations 18 and 72. These are historical records, without new runs in this preparation.

## Publication static verification

All 40 audited source files matched Phase 2 sizes and SHA-256 values. The original scientific publication set contained exactly 29 authorized paths; repository-level licensing and metadata were added subsequently. Eighteen files retain original bytes. The surrogate publication source has the original AST except for pdf_summary and its report-data write expression. The publication script has not been executed.

Original oscillator manifest source and output references resolve to byte-matching files. The derived surrogate manifest retains four archived data hashes and settings, records separate original/publication script hashes, and identifies the publication source as unexecuted. Markdown references resolve within this collection. Python syntax was parsed without importing or executing study modules.

Text, path names and PNG ancillary metadata were statically scanned for local absolute paths, private internal references and common credential formats. Such scans cannot establish absence of every sensitive string. Removed manuscript-generation text was excluded. The submitted PDF matched its audited SHA-256 and text was extracted from all eight pages. After excluding the permitted title and subtitle, a normalized 20-consecutive-word comparison found no matches in publication Markdown, Python, JSON or text files. Shorter matches, paraphrases and text-extraction omissions remain subject to author review.

## Remaining verification limits and release checks

- Software code is licensed under MIT; research content is licensed under CC BY 4.0. Any third-party material requires appropriate rights.
- The edited surrogate publication source has not been runtime-tested.
- Shorter or semantic manuscript overlaps have not been exhaustively reviewed.
- Repository visibility requires a separate release decision. Scientific findings remain preliminary.
