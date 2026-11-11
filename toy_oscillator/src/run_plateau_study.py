"""Chimera-Live v0.3 Toy simulation: matched finite-rate staircase sweeps."""

import argparse
import hashlib
import inspect
import json
import platform
from collections import defaultdict
from pathlib import Path

import inertial_swarm_v02 as model
import numpy as np


LABEL = "Toy simulation"


def compare_branches(rows, field):
    up = [(row["K"], row[field]) for row in rows if row["phase"] == "up"]
    down = [(row["K"], row[field]) for row in rows if row["phase"] == "down"]
    k, r_up = np.array(up[:-1]).T
    k_down, r_down = np.array(down[::-1]).T
    gap = np.abs(r_up - np.interp(k, k_down, r_down))
    return float(np.sum(0.5 * (gap[1:] + gap[:-1]) * np.diff(k)))


def annotate_endpoints(endpoints, trace, plateau):
    samples = defaultdict(list)
    for row in trace:
        samples[row["phase"], row["K"]].append(row)
    for index, row in enumerate(endpoints):
        start = index * plateau
        tail = [
            sample["R_mean"] for sample in samples[row["phase"], row["K"]]
            if sample["t"] - start - DT >= 0.8 * plateau - 1e-9
        ]
        row["tail_R_mean"] = float(np.mean(tail))
        row["tail_sample_count"] = len(tail)


DT = 0.025
K_MAX = 5.0
NK = 13
SEEDS = (7, 11, 19)
PLATEAUS = (18, 36, 72, 144)


def make_figures(out, sweeps, diagnostics):
    plt = model.plt
    for plateau in PLATEAUS:
        fig, axes = plt.subplots(len(SEEDS), 2, figsize=(10, 8), sharex=True, sharey=True,
                                 layout="constrained")
        for seed, panels in zip(SEEDS, axes):
            for enabled, ax in zip((False, True), panels):
                rows = sweeps[plateau, seed, enabled]
                for direction, color in (("up", "tab:blue"), ("down", "tab:orange")):
                    branch = [row for row in rows if row["phase"] == direction]
                    k = [row["K"] for row in branch]
                    ax.plot(k, [row["R_mean"] for row in branch], "o-", ms=3,
                            color=color, label=f"{direction} endpoint")
                    ax.plot(k, [row["tail_R_mean"] for row in branch], "--",
                            color=color, label=f"{direction} late mean")
                ax.set(title=f"Seed {seed} | H feedback {'ON' if enabled else 'OFF'}",
                       ylim=(0, 1.05))
        axes[0, 0].legend(fontsize=7)
        fig.supxlabel("Nominal coupling K")
        fig.supylabel("Mean within-group phase coherence")
        fig.suptitle(f"{LABEL} | Chimera-Live v0.3 | Plateau {plateau}")
        fig.savefig(out / f"sweep_plateau_{plateau}.png", dpi=150)
        plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(9, 6), sharex=True, sharey=True,
                             layout="constrained")
    for row_axes, (field, measure) in zip(axes, (
        ("endpoint_area", "Endpoint"),
        ("tail_area", "Late sample mean"),
    )):
        for ax, enabled in zip(row_axes, (False, True)):
            for seed in SEEDS:
                rows = [row for row in diagnostics if row["seed"] == seed
                        and row["memory_feedback"] == enabled]
                ax.plot([row["plateau"] for row in rows], [row[field] for row in rows],
                        "o-", label=f"Seed {seed}")
            ax.set(title=f"{measure} | H feedback {'ON' if enabled else 'OFF'}",
                   xscale="log", ylim=(0, None))
            ax.set_xticks(PLATEAUS, [str(value) for value in PLATEAUS])
            ax.tick_params(axis="x", which="minor", bottom=False, labelbottom=False)
    axes[0, 0].legend()
    fig.supxlabel("Plateau duration (simulation time)")
    fig.supylabel("Finite-rate sweep discrepancy area")
    fig.suptitle(f"{LABEL} | Chimera-Live v0.3")
    fig.savefig(out / "area_vs_plateau.png", dpi=150)
    plt.close(fig)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New output directory")
    args = parser.parse_args()
    out = args.out
    if out.exists():
        parser.error("--out must be a new directory")
    results, figures = out / "results", out / "figures"
    results.mkdir(parents=True, exist_ok=False)
    figures.mkdir()

    sweeps, diagnostics, traces = {}, [], []
    for plateau in PLATEAUS:
        for seed in SEEDS:
            for enabled in (False, True):
                endpoints, trace = model.simulate(seed, enabled, plateau, DT, K_MAX, NK)
                annotate_endpoints(endpoints, trace, plateau)
                sweeps[plateau, seed, enabled] = endpoints
                traces.extend({"label": LABEL, "plateau": plateau, **row} for row in trace)
                diagnostics.append({
                    "label": LABEL, "plateau": plateau,
                    "nominal_step_rate": K_MAX / (NK - 1) / plateau,
                    "seed": seed, "memory_feedback": enabled,
                    "endpoint_area": compare_branches(endpoints, "R_mean"),
                    "tail_area": compare_branches(endpoints, "tail_R_mean"),
                })
        print(f"Finished plateau {plateau}", flush=True)

    model.save_csv(results / "sweep.csv", [
        {"label": LABEL, "plateau": plateau, **row}
        for (plateau, _, _), endpoints in sweeps.items() for row in endpoints
    ])
    model.save_csv(results / "trace.csv", traces)
    model.save_csv(results / "diagnostics.csv", diagnostics)
    make_figures(figures, sweeps, diagnostics)

    parameters = {
        name: parameter.default
        for name, parameter in inspect.signature(model.simulate).parameters.items()
        if parameter.default is not inspect.Parameter.empty
    }
    manifest = {
        "label": LABEL, "version": "0.3",
        "platform": platform.platform(), "python": platform.python_version(),
        "numpy": np.__version__, "matplotlib": model.matplotlib.__version__,
        "seeds": SEEDS, "plateaus": PLATEAUS, "dt": DT, "kmax": K_MAX, "nk": NK,
        "model_parameters": parameters,
        "integration": "Forward Euler for H and v, then phase update with updated v",
        "conditions": [
            {"memory_feedback": False, "effective_memory_gain": 0.0},
            {"memory_feedback": True, "effective_memory_gain": parameters["memory_gain"]},
        ],
        "design": "Each plateau/seed/feedback run restarts with seed-matched phases, frequencies and velocities; H starts at zero. Within a run, state carries through all 25 plateaus.",
        "trace_sampling": "Every floor(plateau / dt / 50) steps, starting at the first step. t, R_global and H_mean are post-step; R_mean is pre-step (time t - dt).",
        "endpoint_area": "Trapezoid of absolute up/down endpoint R_mean gaps over common K = 0 to 55/12; omit Kmax, which is visited once.",
        "tail_area": "Same area using the mean of sampled pre-step R_mean in the last 20% of each plateau; samples are not independent replicates.",
        "nominal_step_rate": "(kmax / (nk - 1)) / plateau; staircase schedule with discrete jumps",
        "limits": "Finite staircase sweeps at one dt and group size. Genuine hysteresis, Chimera states, chaos, and collective LLM goal drift are untested. Phase coherence measures oscillator phase synchrony.",
        "runs": diagnostics,
        "source_sha256": {
            path.name: sha256(path)
            for path in (Path(__file__), Path(model.__file__))
        },
        "output_sha256": {
            path.relative_to(out).as_posix(): sha256(path)
            for path in sorted([*results.iterdir(), *figures.iterdir()])
        },
    }
    (results / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
