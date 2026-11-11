# Oscillator toy study v0.3

Archived source, settings and outputs retain original bytes and relative layout.

From this directory, the archived entrypoint is `python -B src/run_plateau_study.py --out run_repeat`. This command is provided for future reproduction and was not executed during publication preparation. Install the dependencies in [requirements.txt](requirements.txt) in a suitable environment first. Its lower bounds differ from a fully pinned environment.

Saved execution versions were Python 3.13.17, NumPy 2.5.4 and Matplotlib 3.11.2 on Windows 11. Settings and hashes are in the [original manifest](run/results/manifest.json).

- [Diagnostics](run/results/diagnostics.csv), [sweep](run/results/sweep.csv), [trace](run/results/trace.csv)
- [Area overview](run/figures/area_vs_plateau.png)
- Sweep figures for [18](run/figures/sweep_plateau_18.png), [36](run/figures/sweep_plateau_36.png), [72](run/figures/sweep_plateau_72.png), [144](run/figures/sweep_plateau_144.png)
- [Reproduction details](../docs/REPRODUCIBILITY.md) and [archived verification](../docs/VERIFICATION.md)

The trace stores R_mean at t - dt while H_mean and R_global use t. The late-window statistic follows the R_mean sample time. Finite-rate discrepancies do not establish quasistatic hysteresis or LLM goal drift.
