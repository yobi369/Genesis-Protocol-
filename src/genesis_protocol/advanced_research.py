"""Advanced ecological and genetic-programming validation experiments.

This module is additive: the original spatial model and first campaign remain
unchanged as baselines. Outputs retain raw replicates and holdout boundaries.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .genome import Op
from .reference_ecology import PopulationPoint, load_hudson_bay_csv
from .research import SpatialConfig, SpatialEcosystem
from .tree_gp import (
    EnergyGuard,
    Primitive,
    RepeatNode,
    SequenceNode,
    TreeNode,
    evaluate_tree,
    random_tree,
    tree_depth,
    tree_size,
)


@dataclass(frozen=True, slots=True)
class PredatorStep:
    step: int
    prey: int
    predators: int
    resources: int
    predation_events: int
    predator_births: int


@dataclass(frozen=True, slots=True)
class PredatorReproductionConfig:
    spatial: SpatialConfig
    reproduction_threshold: int | None = None
    reproduction_cost: int = 8
    offspring_energy: int = 12
    reproduction_probability: float = 0.5
    predator_cap_multiplier: int = 4

    def __post_init__(self) -> None:
        if self.reproduction_threshold is not None and self.reproduction_threshold < 1:
            raise ValueError("reproduction threshold must be positive or None")
        if self.reproduction_cost < 1 or self.offspring_energy < 1:
            raise ValueError("reproduction cost and offspring energy must be positive")
        if not 0 <= self.reproduction_probability <= 1:
            raise ValueError("reproduction probability must be in [0, 1]")
        if self.predator_cap_multiplier < 1:
            raise ValueError("predator cap multiplier must be positive")


class ReproductiveSpatialEcosystem:
    """Spatial predator-prey model with energy-gated, probabilistic predator births."""

    def __init__(self, config: PredatorReproductionConfig, *, seed: int) -> None:
        self.config = config
        self.seed = seed
        self.rng = random.Random(seed)
        spatial = config.spatial
        self.resources = [[2 for _ in range(spatial.width)] for _ in range(spatial.height)]
        self.prey = {
            i: [self.rng.randrange(spatial.width), self.rng.randrange(spatial.height),
                spatial.initial_energy] for i in range(spatial.prey)
        }
        self.predators = {
            i: [self.rng.randrange(spatial.width), self.rng.randrange(spatial.height),
                spatial.initial_energy * 2] for i in range(spatial.predators)
        }

    def _move(self, agent: list[int]) -> None:
        spatial = self.config.spatial
        dx, dy = self.rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)))
        agent[0] = (agent[0] + dx) % spatial.width
        agent[1] = (agent[1] + dy) % spatial.height

    def run(self) -> tuple[PredatorStep, ...]:
        spatial = self.config.spatial
        next_prey_id, next_predator_id = len(self.prey), len(self.predators)
        trajectory: list[PredatorStep] = []
        predator_cap = max(spatial.predators, 1) * self.config.predator_cap_multiplier
        for step in range(spatial.steps):
            for row in self.resources:
                for x in range(len(row)):
                    row[x] = min(8, row[x] + spatial.resource_regrowth)
            for agent_id in list(self.prey):
                agent = self.prey[agent_id]
                self._move(agent)
                x, y = agent[0], agent[1]
                food = min(2, self.resources[y][x])
                self.resources[y][x] -= food
                agent[2] += food * 2 - 1
                if agent[2] <= 0:
                    del self.prey[agent_id]

            predation = births = 0
            eligible: list[int] = []
            for predator_id in list(self.predators):
                predator = self.predators[predator_id]
                self._move(predator)
                prey_here = [i for i, p in self.prey.items()
                             if p[0] == predator[0] and p[1] == predator[1]]
                if prey_here:
                    del self.prey[min(prey_here)]
                    predator[2] += 5
                    predation += 1
                predator[2] -= 1
                if predator[2] <= 0:
                    del self.predators[predator_id]
                elif (self.config.reproduction_threshold is not None
                      and predator[2] >= self.config.reproduction_threshold):
                    eligible.append(predator_id)

            for parent_id in eligible:
                if len(self.predators) >= predator_cap:
                    break
                if self.rng.random() > self.config.reproduction_probability:
                    continue
                parent = self.predators.get(parent_id)
                if parent is None or parent[2] - self.config.reproduction_cost <= 0:
                    continue
                parent[2] -= self.config.reproduction_cost
                self.predators[next_predator_id] = [
                    parent[0], parent[1], self.config.offspring_energy
                ]
                next_predator_id += 1
                births += 1

            parents = [i for i, p in self.prey.items() if p[2] >= 18]
            for parent_id in parents[:max(0, spatial.prey // 4)]:
                if len(self.prey) >= spatial.prey * 3:
                    break
                parent = self.prey[parent_id]
                parent[2] -= 6
                self.prey[next_prey_id] = [parent[0], parent[1], spatial.initial_energy]
                next_prey_id += 1
            trajectory.append(PredatorStep(
                step, len(self.prey), len(self.predators),
                sum(sum(row) for row in self.resources), predation, births,
            ))
        return tuple(trajectory)


def _species_log_rmse(predicted: Sequence[float], observed: Sequence[float],
                      start: int, stop: int) -> float:
    errors = [math.log1p(max(0.0, p)) - math.log1p(max(0.0, o))
              for p, o in zip(predicted[start:stop], observed[start:stop])]
    if not errors:
        raise ValueError("RMSE window must contain at least one observation")
    return math.sqrt(statistics.mean(error * error for error in errors))


def _paired_interval(differences: Sequence[float], *, seed: int) -> dict[str, Any]:
    if len(differences) < 2:
        raise ValueError("paired uncertainty requires at least two replicates")
    rng = random.Random(seed)
    means = [
        statistics.mean(rng.choices(differences, k=len(differences)))
        for _ in range(3000)
    ]
    ordered = sorted(means)
    return {
        "n": len(differences),
        "mean_difference": statistics.mean(differences),
        "standard_deviation": statistics.stdev(differences),
        "bootstrap_95_percentile_interval": [
            ordered[int(0.025 * (len(ordered) - 1))],
            ordered[int(0.975 * (len(ordered) - 1))],
        ],
    }


def run_predator_reproduction_experiment(
    observations: Sequence[PopulationPoint], seeds: Sequence[int],
) -> dict[str, Any]:
    """Select reproduction parameters on training data; report species holdouts separately."""
    if len(observations) < 10 or len(seeds) < 30 or len(set(seeds)) != len(seeds):
        raise ValueError("need >=10 observations and >=30 unique seeds")
    split = int(len(observations) * 0.70)
    if split < 5 or split >= len(observations):
        raise ValueError("chronological split leaves too few train or holdout points")
    first = observations[0]
    base_spatial = SpatialConfig(
        width=12, height=12, prey=max(1, round(first.prey)),
        predators=max(1, round(first.predators)), resource_regrowth=2,
        steps=len(observations) - 1, initial_energy=12,
    )
    observed_prey = [p.prey for p in observations]
    observed_predators = [p.predators for p in observations]
    baseline_prey, baseline_predators = [], []
    for seed in seeds:
        result = SpatialEcosystem(base_spatial, seed=seed).run()
        baseline_prey.append([float(base_spatial.prey)] + [float(p.prey) for p in result.trajectory])
        baseline_predators.append([float(base_spatial.predators)] + [
            float(p.predators) for p in result.trajectory
        ])
    baseline_mean_prey = [statistics.mean(row[t] for row in baseline_prey)
                          for t in range(len(observations))]
    baseline_mean_pred = [statistics.mean(row[t] for row in baseline_predators)
                          for t in range(len(observations))]
    baseline_seed_errors = [{
        "seed": seed,
        "holdout_prey_log_rmse": _species_log_rmse(prey, observed_prey, split, len(observations)),
        "holdout_predator_log_rmse": _species_log_rmse(
            predators, observed_predators, split, len(observations)),
    } for seed, prey, predators in zip(seeds, baseline_prey, baseline_predators)]
    baseline = {
        "model": "no_predator_reproduction",
        "train_prey_log_rmse": _species_log_rmse(baseline_mean_prey, observed_prey, 0, split),
        "train_predator_log_rmse": _species_log_rmse(
            baseline_mean_pred, observed_predators, 0, split),
        "holdout_prey_log_rmse": _species_log_rmse(
            baseline_mean_prey, observed_prey, split, len(observations)),
        "holdout_predator_log_rmse": _species_log_rmse(
            baseline_mean_pred, observed_predators, split, len(observations)),
    }

    candidates = []
    for threshold in (14, 18, 22):
        for cost in (6, 10):
            for probability in (0.25, 0.5, 0.75):
                prey_runs, predator_runs, replicate_rows = [], [], []
                for seed in seeds:
                    cfg = PredatorReproductionConfig(
                        base_spatial, reproduction_threshold=threshold,
                        reproduction_cost=cost, offspring_energy=12,
                        reproduction_probability=probability,
                    )
                    trajectory = ReproductiveSpatialEcosystem(cfg, seed=seed).run()
                    prey_series = [float(base_spatial.prey)] + [float(p.prey) for p in trajectory]
                    predator_series = [float(base_spatial.predators)] + [
                        float(p.predators) for p in trajectory
                    ]
                    prey_runs.append(prey_series)
                    predator_runs.append(predator_series)
                    replicate_rows.append({
                        "seed": seed, "final_prey": prey_series[-1],
                        "final_predators": predator_series[-1],
                        "total_predator_births": sum(p.predator_births for p in trajectory),
                        "total_predation_events": sum(p.predation_events for p in trajectory),
                        "holdout_prey_log_rmse": _species_log_rmse(
                            prey_series, observed_prey, split, len(observations)),
                        "holdout_predator_log_rmse": _species_log_rmse(
                            predator_series, observed_predators, split, len(observations)),
                    })
                mean_prey = [statistics.mean(row[t] for row in prey_runs)
                             for t in range(len(observations))]
                mean_pred = [statistics.mean(row[t] for row in predator_runs)
                             for t in range(len(observations))]
                train_prey = _species_log_rmse(mean_prey, observed_prey, 0, split)
                train_pred = _species_log_rmse(mean_pred, observed_predators, 0, split)
                candidates.append({
                    "parameters": {"threshold": threshold, "cost": cost,
                                   "probability": probability},
                    "train_prey_log_rmse": train_prey,
                    "train_predator_log_rmse": train_pred,
                    "train_joint_log_rmse": math.sqrt((train_prey ** 2 + train_pred ** 2) / 2),
                    "holdout_prey_log_rmse": _species_log_rmse(
                        mean_prey, observed_prey, split, len(observations)),
                    "holdout_predator_log_rmse": _species_log_rmse(
                        mean_pred, observed_predators, split, len(observations)),
                    "mean_trajectory": {"prey": mean_prey, "predators": mean_pred},
                    "replicates": replicate_rows,
                })
    best = min(candidates, key=lambda row: row["train_joint_log_rmse"])
    baseline_by_seed = {row["seed"]: row for row in baseline_seed_errors}
    paired_prey = [
        row["holdout_prey_log_rmse"] - baseline_by_seed[row["seed"]]["holdout_prey_log_rmse"]
        for row in best["replicates"]
    ]
    paired_predators = [
        row["holdout_predator_log_rmse"]
        - baseline_by_seed[row["seed"]]["holdout_predator_log_rmse"]
        for row in best["replicates"]
    ]
    return {
        "design": "paired 30+ seeds; chronological 70/30 split; model selection uses training years only",
        "split": {"train_count": split, "holdout_count": len(observations) - split,
                  "holdout_start": observations[split].time},
        "baseline": baseline,
        "selected_reproductive_model": {
            key: value for key, value in best.items() if key != "replicates"
        },
        "selected_replicates": best["replicates"],
        "candidate_grid": [{key: value for key, value in row.items()
                            if key not in ("replicates", "mean_trajectory")}
                           for row in candidates],
        "holdout_change_vs_baseline": {
            "prey_log_rmse": _paired_interval(paired_prey, seed=seeds[0] + 31),
            "predator_log_rmse": _paired_interval(paired_predators, seed=seeds[0] + 32),
        },
        "interpretation_rule": (
            "A predator improvement is not accepted if prey holdout RMSE worsens materially. "
            "Parameters are selected on training data only; holdout values are reported once."
        ),
        "limitation": (
            "The Hudson Bay pelt index is an indirect abundance proxy, not a census. Predator "
            "births are a simple demographic mechanism and do not establish biological realism."
        ),
    }


def _node_paths(root: TreeNode) -> list[tuple[int, ...]]:
    paths: list[tuple[int, ...]] = [()]
    def visit(node: TreeNode, prefix: tuple[int, ...]) -> None:
        children = node.children if isinstance(node, SequenceNode) else (
            (node.body,) if isinstance(node, (EnergyGuard, RepeatNode)) else ()
        )
        for index, child in enumerate(children):
            path = prefix + (index,)
            paths.append(path)
            visit(child, path)
    visit(root, ())
    return paths


def _get_node(root: TreeNode, path: tuple[int, ...]) -> TreeNode:
    node = root
    for index in path:
        node = node.children[index] if isinstance(node, SequenceNode) else node.body
    return node


def _replace_node(root: TreeNode, path: tuple[int, ...], replacement: TreeNode) -> TreeNode:
    if not path:
        return replacement
    index, *tail = path
    if isinstance(root, SequenceNode):
        children = list(root.children)
        children[index] = _replace_node(children[index], tuple(tail), replacement)
        return SequenceNode(tuple(children))
    if isinstance(root, EnergyGuard):
        return EnergyGuard(root.threshold, _replace_node(root.body, tuple(tail), replacement))
    if isinstance(root, RepeatNode):
        return RepeatNode(root.count, _replace_node(root.body, tuple(tail), replacement))
    raise ValueError("cannot descend through a primitive")


def mutate_tree_advanced(root: TreeNode, rng: random.Random, *,
                         max_depth: int = 6, max_size: int = 64) -> TreeNode:
    """Choose point, subtree or hoist mutation under strict structural budgets."""
    paths = _node_paths(root)
    path = rng.choice(paths)
    target = _get_node(root, path)
    mode = rng.choice(("point", "subtree", "hoist"))
    if mode == "hoist" and isinstance(target, (SequenceNode, EnergyGuard, RepeatNode)):
        replacement = (target.children[rng.randrange(len(target.children))]
                       if isinstance(target, SequenceNode) else target.body)
    elif mode == "point" and isinstance(target, Primitive):
        replacement = Primitive(
            rng.choice((Op.MOVE, Op.GATHER, Op.REST, Op.COOPERATE)), rng.randint(1, 5)
        )
    else:
        remaining = max(1, max_depth - len(path))
        replacement = random_tree(rng, max_depth=min(remaining, 8))
    candidate = _replace_node(root, path, replacement)
    if tree_depth(candidate) > max_depth or tree_size(candidate) > max_size:
        return root
    return candidate


def crossover_tree_advanced(left: TreeNode, right: TreeNode, rng: random.Random, *,
                            max_depth: int = 6, max_size: int = 64) -> TreeNode:
    """Subtree crossover that rejects children exceeding configured budgets."""
    left_path = rng.choice(_node_paths(left))
    right_path = rng.choice(_node_paths(right))
    candidate = _replace_node(left, left_path, _get_node(right, right_path))
    if tree_depth(candidate) > max_depth or tree_size(candidate) > max_size:
        return left
    return candidate


def run_richer_tree_operator_smoke(seeds: Sequence[int]) -> dict[str, Any]:
    """Exercise nested grammar and operators on at least 30 independent seeds."""
    if len(seeds) < 30:
        raise ValueError("tree operator campaign requires at least 30 seeds")
    rows = []
    for seed in seeds:
        rng = random.Random(seed)
        tree = random_tree(rng, max_depth=4)
        accepted_mutations = accepted_crossovers = 0
        for _ in range(100):
            mutated = mutate_tree_advanced(tree, rng, max_depth=6, max_size=64)
            crossed = crossover_tree_advanced(tree, random_tree(rng, max_depth=4), rng)
            accepted_mutations += mutated != tree
            accepted_crossovers += crossed != tree
            for candidate in (mutated, crossed):
                if tree_depth(candidate) > 6 or tree_size(candidate) > 64:
                    raise AssertionError("operator emitted a tree outside configured bounds")
                evaluate_tree(candidate, instruction_budget=256)
            tree = mutated
        rows.append({"seed": seed, "accepted_mutations": accepted_mutations,
                     "accepted_crossovers": accepted_crossovers,
                     "final_depth": tree_depth(tree), "final_size": tree_size(tree)})
    return {"seeds": list(seeds), "operator_trials_per_seed": 100,
            "grammar": "nested sequence, energy guard, repeat, primitive actions",
            "replicates": rows}


def run_advanced_campaign(output: str | Path, *, seed_count: int = 30) -> dict[str, Any]:
    if seed_count < 30:
        raise ValueError("advanced campaign requires at least 30 seeds")
    seeds = tuple(range(5001, 5001 + seed_count))
    root = Path(__file__).resolve().parents[2]
    observations = load_hudson_bay_csv(
        root / "data" / "empirical" / "hudson_bay_lynx_hare_1900_1920.csv"
    )
    result = {
        "schema": "genesis-advanced-research-v1",
        "seed_policy": {"count": seed_count, "seeds": list(seeds)},
        "predator_reproduction": run_predator_reproduction_experiment(observations, seeds),
        "richer_tree_operators": run_richer_tree_operator_smoke(seeds),
        "empirical_dataset_registry": {
            "status": "candidate_sources_documented; raw data import and harmonization pending",
            "sources": [
                {"name": "Tetlin NWR snowshoe hare pellet quadrats", "years": "1990-2024",
                 "species": "hare only", "method": "pellet counts across quadrats and sites",
                 "url": "https://catalog.data.gov/dataset/snowshoe-hare-population-monitoring-at-tetlin-national-wildlife-refuge-raw-datas-1990-2024"},
                {"name": "Kluane hare monitoring and experiments",
                 "years": "multi-decade; monitoring and capture records",
                 "species": "hare and small-mammal context",
                 "method": "live trapping, mark-recapture, experimental grids",
                 "url": "https://datadryad.org/dataset/doi:10.5061/dryad.684s1"},
                {"name": "Wood Buffalo hare pellet survey", "years": "2006-2017",
                 "species": "hare only", "method": "annual June pellet counts on four permanent transects",
                 "url": "https://open.canada.ca/data/en/dataset/045239c3-f835-4be8-921a-f17caf264097"},
                {"name": "Kluane/Yukon boreal community monitoring", "years": "1973-2022",
                 "species": "hares and multiple carnivores",
                 "method": "annual pellet plots; predator snow-track indices",
                 "url": "https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2023.1187222/full"},
            ],
            "guardrail": (
                "Do not combine hare-only series with predator indices from different sites, "
                "years, units or survey protocols as if they were synchronous paired counts."
            ),
        },
    }
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Genesis Protocol's advanced research campaign")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--output", default="artifacts/advanced-research-validation.json")
    args = parser.parse_args()
    result = run_advanced_campaign(args.output, seed_count=args.seeds)
    print(json.dumps({
        "output": args.output, "seed_count": args.seeds,
        "predator_baseline": result["predator_reproduction"]["baseline"],
        "predator_reproduction": result["predator_reproduction"]["selected_reproductive_model"],
        "tree_operator_trials_per_seed": result["richer_tree_operators"]["operator_trials_per_seed"],
        "empirical_registry_status": result["empirical_dataset_registry"]["status"],
    }, indent=2))


if __name__ == "__main__":
    main()
