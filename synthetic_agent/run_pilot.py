"""Chimera-Live programmed surrogate with source-tagged binary evidence."""

import argparse
import csv
import hashlib
import json
import platform
from collections import defaultdict
from pathlib import Path

import numpy as np


TRIALS = 1000
AGENTS = 9
ROUNDS = 16
CORRECTION_ROUND = 7
PRIVATE_RELIABILITY = 0.65
SOCIAL_WEIGHT = 0.45
CORRECTION_WEIGHT = 3.0
HISTORY_DECAY = 0.7
HISTORY_ROUNDS = 3
CONSENSUS_VOTES = 7
SEED = 20261109
BOOTSTRAPS = 2000
LABEL = "programmed surrogate"
CONDITIONS = ("A", "B", "C", "D")


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def evidence(rng):
    truth = int(rng.choice((-1, 1)))
    # Two private sources per agent, plus one shared by each group of three.
    portfolios = np.array([[2 * i, 2 * i + 1, 18 + i // 3] for i in range(AGENTS)])
    signs = np.where(rng.random(21) < PRIVATE_RELIABILITY, truth, -truth)
    picks = rng.integers(3, size=(ROUNDS, AGENTS))
    broadcasts = portfolios[np.arange(AGENTS)[None, :], picks]
    tie_votes = rng.choice((-1, 1), size=(ROUNDS, AGENTS))
    return truth, portfolios, signs, broadcasts, tie_votes


def simulate(condition, trial, fixture):
    truth, portfolios, signs, broadcasts, tie_votes = fixture
    past_explanations, trajectory = [], []
    for step in range(ROUNDS):
        round_no = step + 1
        votes, explanations = [], []
        for agent, private in enumerate(portfolios):
            contributions = [(int(source), 1.0) for source in private]
            if condition != "A":
                contributions.extend(
                    (int(source), SOCIAL_WEIGHT)
                    for peer, source in enumerate(broadcasts[step]) if peer != agent
                )
            if condition in ("C", "D"):
                for age, previous in enumerate(reversed(past_explanations[-HISTORY_ROUNDS:]), 1):
                    contributions.extend(
                        (source, SOCIAL_WEIGHT * HISTORY_DECAY ** (age - 1))
                        for peer, source in enumerate(previous) if peer != agent and source >= 0
                    )
            by_source = defaultdict(list)
            for source, weight in contributions:
                by_source[source].append(weight)
            weights = {source: (max(items) if condition == "D" else sum(items))
                       for source, items in by_source.items()}
            correction = CORRECTION_WEIGHT * truth if round_no >= CORRECTION_ROUND else 0.0
            score = sum(int(signs[source]) * weight for source, weight in weights.items()) + correction
            vote = int(tie_votes[step, agent]) if abs(score) < 1e-12 else (1 if score > 0 else -1)
            # A vote can cite its strongest supporting observed source. A corrected
            # vote cites the public correction when it outweighs any private source.
            # The public correction is scored once directly, so its citations are omitted.
            supporting = [source for source in weights if signs[source] == vote]
            citation = min(supporting, key=lambda source: (-weights[source], source), default=-1)
            if correction and vote == truth and (citation < 0 or CORRECTION_WEIGHT >= weights[citation]):
                citation = -1
            votes.append(vote)
            explanations.append(citation)
        past_explanations.append(explanations)
        correct = sum(vote == truth for vote in votes)
        trajectory.append({
            "label": LABEL, "trial": trial, "condition": condition, "round": round_no,
            "truth": truth, "correction_visible": bool(correction), "correct_votes": correct,
            "consensus": max(correct, AGENTS - correct) >= CONSENSUS_VOTES,
            "correct_consensus": correct >= CONSENSUS_VOTES,
            "wrong_consensus": AGENTS - correct >= CONSENSUS_VOTES,
            "votes": " ".join(map(str, votes)), "citation_source_ids": " ".join(map(str, explanations)),
        })
    return trajectory


def measure(trajectory):
    pre = trajectory[:CORRECTION_ROUND - 1]
    post = trajectory[CORRECTION_ROUND - 1:]
    recovery = next((i for i, (a, b) in enumerate(zip(post, post[1:]))
                     if a["correct_consensus"] and b["correct_consensus"]), len(post))
    persistence = 0
    if pre[-1]["wrong_consensus"]:
        for row in post:
            if not row["wrong_consensus"]:
                break
            persistence += 1
    return {
        "consensus_post": sum(row["consensus"] for row in post) / len(post),
        "correctness_post": sum(row["correct_votes"] for row in post) / (len(post) * AGENTS),
        "wrong_consensus_pre": sum(row["wrong_consensus"] for row in pre) / len(pre),
        "wrong_consensus_post": sum(row["wrong_consensus"] for row in post) / len(post),
        "wrong_at_correction": int(pre[-1]["wrong_consensus"]),
        "recovery_capped": recovery,
        "no_sustained_recovery": int(recovery == len(post)),
        "wrong_persistence": persistence,
    }


def describe(values, bootstrap):
    low, high = np.quantile(values[bootstrap].mean(axis=1), [0.025, 0.975])
    return {"mean": float(values.mean()), "sd": float(values.std(ddof=1)),
            "ci95_low": float(low), "ci95_high": float(high)}




def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    traces, trial_rows, fixtures = [], [], []
    for trial, child in enumerate(np.random.SeedSequence(SEED).spawn(TRIALS)):
        fixture = evidence(np.random.default_rng(child))
        truth, portfolios, signs, broadcasts, tie_votes = fixture
        fixtures.append({
            "trial": trial, "spawn_key": list(child.spawn_key), "truth": truth,
            "private_source_ids": portfolios.tolist(), "source_signs": signs.tolist(),
            "broadcast_source_ids": broadcasts.tolist(), "tie_votes": tie_votes.tolist(),
        })
        for condition in CONDITIONS:
            trace = simulate(condition, trial, fixture)
            traces.extend(trace)
            trial_rows.append({"label": LABEL, "trial": trial, "condition": condition, **measure(trace)})

    metrics = list(measure(traces[:ROUNDS]))
    samples = np.random.default_rng(SEED + 1).integers(TRIALS, size=(BOOTSTRAPS, TRIALS))
    vectors = {
        condition: {key: np.array([row[key] for row in trial_rows if row["condition"] == condition])
                    for key in metrics} for condition in CONDITIONS
    }
    stats = {condition: {key: describe(values, samples) for key, values in columns.items()}
             for condition, columns in vectors.items()}
    contrasts = {
        f"{left}-{right}": {key: describe(vectors[left][key] - vectors[right][key], samples)
                            for key in metrics}
        for left, right in (("B", "A"), ("C", "B"), ("D", "C"))
    }
    write_csv(args.out / "trace.csv", traces)
    write_csv(args.out / "trial_metrics.csv", trial_rows)
    write_csv(args.out / "summary.csv", [
        {"label": LABEL, "comparison": comparison, "metric": key, **result}
        for comparison, columns in (stats | contrasts).items() for key, result in columns.items()
    ])
    (args.out / "evidence.jsonl").write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in fixtures), encoding="utf-8"
    )
    manifest = {
        "label": LABEL, "seed": SEED, "trials": TRIALS, "agents": AGENTS, "rounds": ROUNDS,
        "conditions": {"A": "independent", "B": "sharing", "C": "sharing with history",
                       "D": "sharing with history and cross-channel source deduplication"},
        "correction_round": CORRECTION_ROUND, "correction_weight": CORRECTION_WEIGHT,
        "private_reliability": PRIVATE_RELIABILITY, "social_weight": SOCIAL_WEIGHT,
        "history_decay": HISTORY_DECAY, "history_rounds": HISTORY_ROUNDS,
        "consensus_votes": CONSENSUS_VOTES, "bootstrap_resamples": BOOTSTRAPS,
        "python": platform.python_version(), "numpy": np.__version__,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "output_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in sorted(args.out.iterdir())},
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Completed {TRIALS} matched trials, {len(trial_rows)} trial-arms, {len(traces)} trace rows.")


if __name__ == "__main__":
    main()
