"""Reproducible, paired research-validation campaign for Genesis Protocol.

Run with at least 30 independent seeds. Raw per-seed outputs are retained in
JSON so summaries can be audited and reanalyzed. This is a benchmark protocol,
not an automatic scientific-validity certificate.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import time
from pathlib import Path
from typing import Any
from collections.abc import Sequence

from .ecology import EcologyConfig, EcosystemEngine, EnvironmentalPhase, SpeciesDefinition
from .evaluator import evaluate
from .genome import Genome, Instruction, Op
from .models import Environment, Organism
from .program import Action, IfEnergyBelow, Program, RepeatAction
from .reference_ecology import (
    LotkaVolterraParameters,
    RosenzweigMacArthurParameters,
    calibrate_empirical_references,
    load_hudson_bay_csv,
    simulate_lotka_volterra,
    simulate_rosenzweig_macarthur,
)
from .research import SpatialConfig, SpatialEcosystem, cluster_genomes, normalized_genome_distance
from .statistics import bootstrap_mean_interval, paired_effect_summary, paired_permutation_test
from .tree_gp import EnergyGuard, Primitive, RepeatNode, SequenceNode, TreeNode, evaluate_tree


def _summary(values: Sequence[float], *, seed: int) -> dict[str, float]:
    low, high = bootstrap_mean_interval(values, replicates=2000, seed=seed)
    return {
        "n": len(values),
        "mean": statistics.mean(values),
        "standard_deviation": statistics.stdev(values),
        "median": statistics.median(values),
        "bootstrap_95_percentile_interval": [low, high],
    }


def _paired(differences: Sequence[float], *, seed: int) -> dict[str, Any]:
    return {
        **paired_effect_summary(differences),
        "permutation_test": paired_permutation_test(differences, permutations=5000, seed=seed),
        "bootstrap_95_percentile_interval": list(
            bootstrap_mean_interval(differences, replicates=5000, seed=seed + 1)
        ),
    }


def run_ecological_replicates(seeds: Sequence[int]) -> dict[str, Any]:
    """Run three ecological pressure regimes with the same seed set."""
    if len(seeds) < 30 or len(set(seeds)) != len(seeds):
        raise ValueError("ecological campaign requires at least 30 unique seeds")
    species = (SpeciesDefinition(0, "foragers", 12), SpeciesDefinition(1, "scavengers", 12))
    regimes = {
        "resource_rich": (EnvironmentalPhase(0, 90), EnvironmentalPhase(12, 65)),
        "resource_scarce": (EnvironmentalPhase(0, 28), EnvironmentalPhase(12, 16)),
        "resource_pulse": (
            EnvironmentalPhase(0, 48), EnvironmentalPhase(8, 95), EnvironmentalPhase(16, 22)
        ),
    }
    config = EcologyConfig(generations=24, mutation_rate=0.08, instruction_budget=96)
    output: dict[str, Any] = {"seed_count_per_condition": len(seeds), "conditions": {}}
    for name, schedule in regimes.items():
        rows = []
        for seed in seeds:
            result = EcosystemEngine(species, schedule, config, seed=seed).run()
            report = result.reports[-1]
            rows.append({
                "seed": seed,
                "final_generation": report.generation,
                "mean_resources": report.mean_resources,
                "mean_survival_energy": report.mean_survival,
                "mean_reciprocal_cooperation": report.mean_reciprocal_cooperation,
                "pareto_front_size": report.pareto_front_size,
                "genotype_diversity": report.genotype_diversity,
                "species_count": len({item.species_id for item in result.final_population}),
                "final_population": len(result.final_population),
                "extinctions_last_generation": report.extinctions,
            })
        output["conditions"][name] = {
            "replicates": rows,
            "metrics": {
                key: _summary([float(row[key]) for row in rows], seed=seeds[0] + offset)
                for offset, key in enumerate((
                    "mean_resources", "mean_survival_energy", "mean_reciprocal_cooperation",
                    "species_count", "genotype_diversity", "final_population",
                ))
            },
        }
    rich = output["conditions"]["resource_rich"]["replicates"]
    scarce = output["conditions"]["resource_scarce"]["replicates"]
    by_seed = {row["seed"]: row for row in scarce}
    output["paired_rich_minus_scarce"] = {
        metric: _paired(
            [row[metric] - by_seed[row["seed"]][metric] for row in rich],
            seed=seeds[0] + index,
        )
        for index, metric in enumerate(("mean_resources", "mean_survival_energy",
                                        "species_count", "genotype_diversity"))
    }
    return output


def _log_trajectory_rmse(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("trajectories must have equal non-empty lengths")
    errors = [math.log1p(a) - math.log1p(b) for a, b in zip(left, right)]
    return math.sqrt(statistics.mean(value * value for value in errors))


def run_spatial_reference_comparison(seeds: Sequence[int]) -> dict[str, Any]:
    """Compare seeded spatial trajectories with LV and Rosenzweig–MacArthur ODEs."""
    if len(seeds) < 30:
        raise ValueError("spatial comparison requires at least 30 seeds")
    rows = []
    for seed in seeds:
        rng = random.Random(seed ^ 0x5A17)
        initial_prey = rng.randint(20, 28)
        initial_predators = rng.randint(2, 5)
        spatial = SpatialEcosystem(
            SpatialConfig(width=12, height=12, prey=initial_prey, predators=initial_predators,
                          resource_regrowth=2, steps=40, initial_energy=12),
            seed=seed,
        ).run()
        spatial_prey = [float(item.prey) for item in spatial.trajectory]
        spatial_predators = [float(item.predators) for item in spatial.trajectory]
        lv = simulate_lotka_volterra(
            initial_prey, initial_predators, LotkaVolterraParameters(), steps=40
        )
        rm = simulate_rosenzweig_macarthur(
            initial_prey, initial_predators, RosenzweigMacArthurParameters(), steps=40
        )
        lv_prey = [point.prey for point in lv[1:]]
        lv_predators = [point.predators for point in lv[1:]]
        rm_prey = [point.prey for point in rm[1:]]
        rm_predators = [point.predators for point in rm[1:]]
        rows.append({
            "seed": seed,
            "initial_prey": initial_prey,
            "initial_predators": initial_predators,
            "spatial_final_prey": spatial.trajectory[-1].prey,
            "spatial_final_predators": spatial.trajectory[-1].predators,
            "spatial_predation_events": sum(item.predation_events for item in spatial.trajectory),
            "spatial_social_edges_final": spatial.trajectory[-1].social_edges,
            "lv_log_rmse_prey": _log_trajectory_rmse(spatial_prey, lv_prey),
            "lv_log_rmse_predators": _log_trajectory_rmse(spatial_predators, lv_predators),
            "rm_log_rmse_prey": _log_trajectory_rmse(spatial_prey, rm_prey),
            "rm_log_rmse_predators": _log_trajectory_rmse(spatial_predators, rm_predators),
            "lv_final_prey": lv[-1].prey,
            "lv_final_predators": lv[-1].predators,
            "rm_final_prey": rm[-1].prey,
            "rm_final_predators": rm[-1].predators,
        })
    metrics = ("spatial_final_prey", "spatial_final_predators", "spatial_predation_events",
               "spatial_social_edges_final", "lv_log_rmse_prey", "lv_log_rmse_predators",
               "rm_log_rmse_prey", "rm_log_rmse_predators")
    return {
        "design": "30+ matched seeds; same initial populations; spatial stochastic model vs deterministic ODE trajectories",
        "interpretation": (
            "Descriptive structural comparison only. The ODEs are well-mixed deterministic "
            "references; the spatial model has discrete agents, finite habitat and local predation. "
            "RMSE is not a test of equivalence and no parameters were calibrated to these runs."
        ),
        "replicates": rows,
        "metrics": {key: _summary([float(row[key]) for row in rows], seed=seeds[0] + index)
                    for index, key in enumerate(metrics)},
    }


def _mutate_genome(genome: Genome, rng: random.Random, rate: float) -> Genome:
    genes = list(genome.instructions)
    for index in range(len(genes)):
        if rng.random() < rate:
            genes[index] = Instruction(rng.choice(tuple(Op)), rng.randint(1, 5))
    return Genome(tuple(genes))


def _distribution_genomes(seed: int, distribution: str, count_per_group: int = 12
                          ) -> tuple[list[Genome], list[int]]:
    rng = random.Random(seed)
    genomes: list[Genome] = []
    labels: list[int] = []
    if distribution == "separated_lineages":
        templates = [Genome.random(rng, 12, 12) for _ in range(3)]
        for group, template in enumerate(templates):
            for _ in range(count_per_group):
                genomes.append(_mutate_genome(template, rng, 0.08))
                labels.append(group)
    elif distribution == "continuous_random":
        for index in range(count_per_group * 3):
            genomes.append(Genome.random(rng, 6, 20))
            labels.append(0)
    elif distribution == "length_shifted":
        for group, length in enumerate((6, 12, 18)):
            template = Genome(tuple(
                Instruction((Op.MOVE, Op.GATHER, Op.REST, Op.COOPERATE)[group], 1)
                for _ in range(length)
            ))
            for _ in range(count_per_group):
                genomes.append(_mutate_genome(template, rng, 0.04))
                labels.append(group)
    else:
        raise ValueError("unknown genome distribution")
    return genomes, labels


def _adjusted_rand(labels: Sequence[int], clusters: Sequence[int]) -> float:
    if len(labels) != len(clusters):
        raise ValueError("label vectors must have equal length")
    n = len(labels)
    if n < 2:
        return 1.0
    def pair_count(counts: Sequence[int]) -> float:
        return sum(count * (count - 1) / 2 for count in counts)
    label_ids, cluster_ids = sorted(set(labels)), sorted(set(clusters))
    contingency = [[sum(a == x and b == y for a, b in zip(labels, clusters))
                    for y in cluster_ids] for x in label_ids]
    row_counts = [sum(value == label for value in labels) for label in label_ids]
    column_counts = [sum(value == cluster for value in clusters) for cluster in cluster_ids]
    sum_cells = pair_count([value for row in contingency for value in row])
    sum_rows = pair_count(row_counts)
    sum_columns = pair_count(column_counts)
    total = n * (n - 1) / 2
    expected = sum_rows * sum_columns / total
    maximum = (sum_rows + sum_columns) / 2
    return (sum_cells - expected) / (maximum - expected) if maximum != expected else 1.0


def run_speciation_sensitivity(seeds: Sequence[int]) -> dict[str, Any]:
    """Measure cluster count, ARI and input-order sensitivity across genome families."""
    if len(seeds) < 30:
        raise ValueError("speciation sensitivity requires at least 30 seeds")
    thresholds = tuple(round(value, 2) for value in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9))
    distributions = ("separated_lineages", "continuous_random", "length_shifted")
    output: dict[str, Any] = {"thresholds": list(thresholds), "distributions": {}}
    for distribution in distributions:
        rows = []
        for seed in seeds:
            genomes, labels = _distribution_genomes(seed, distribution)
            for threshold in thresholds:
                forward = cluster_genomes(genomes, threshold)
                reverse = cluster_genomes(tuple(reversed(genomes)), threshold)
                predicted = [next(index for index, group in enumerate(forward)
                                  if item in group.members) for item in range(len(genomes))]
                rows.append({
                    "seed": seed,
                    "threshold": threshold,
                    "cluster_count": len(forward),
                    "adjusted_rand_index": _adjusted_rand(labels, predicted),
                    "reverse_order_cluster_count": len(reverse),
                    "order_sensitivity_absolute": abs(len(forward) - len(reverse)),
                    "mean_within_cluster_distance": statistics.mean(
                        normalized_genome_distance(genomes[a], genomes[b])
                        for group in forward for a in group.members for b in group.members if a < b
                    ) if any(len(group.members) > 1 for group in forward) else 0.0,
                })
        output["distributions"][distribution] = {
            "replicate_count": len(seeds),
            "replicates": rows,
            "by_threshold": [{
                "threshold": threshold,
                "mean_cluster_count": statistics.mean(
                    row["cluster_count"] for row in rows if row["threshold"] == threshold
                ),
                "mean_adjusted_rand_index": statistics.mean(
                    row["adjusted_rand_index"] for row in rows if row["threshold"] == threshold
                ),
                "mean_order_sensitivity": statistics.mean(
                    row["order_sensitivity_absolute"] for row in rows if row["threshold"] == threshold
                ),
            } for threshold in thresholds],
        }
    return output


def _benchmark_objectives(problem: str, rng: random.Random, count: int
                          ) -> list[tuple[float, ...]]:
    rows = []
    for _ in range(count):
        if problem == "zdt1":
            decision = [rng.random() for _ in range(30)]
            first = decision[0]
            g = 1 + 9 * sum(decision[1:]) / 29
            second = g * (1 - math.sqrt(first / g))
            rows.append((-first, -second))
        else:
            decision = [rng.random() for _ in range(12)]
            g = sum((value - 0.5) ** 2 for value in decision[2:])
            f1 = (1 + g) * math.cos(decision[0] * math.pi / 2) * math.cos(decision[1] * math.pi / 2)
            f2 = (1 + g) * math.cos(decision[0] * math.pi / 2) * math.sin(decision[1] * math.pi / 2)
            f3 = (1 + g) * math.sin(decision[0] * math.pi / 2)
            rows.append((-f1, -f2, -f3))
    return rows


def _deap_population(points: Sequence[Sequence[float]]) -> tuple[Any, Any, list[Any]]:
    try:
        from deap import base, tools
    except ImportError as exc:
        raise RuntimeError("install the 'research' extra to run DEAP reference benchmarks") from exc
    fitness_type = type("GenesisFitnessMax", (base.Fitness,), {
        "weights": tuple(1.0 for _ in points[0])
    })
    individual_type = type("GenesisIndividual", (list,), {})
    population = []
    for index, point in enumerate(points):
        item = individual_type([float(value) for value in point])
        item.row_index = index
        item.fitness = fitness_type()
        item.fitness.values = tuple(float(value) for value in point)
        population.append(item)
    return tools, fitness_type, population


def _deap_first_front(points: Sequence[Sequence[float]]) -> set[int]:
    tools, _, population = _deap_population(points)
    front = tools.sortNondominated(population, k=len(population), first_front_only=True)[0]
    return {item.row_index for item in front}


def _deap_select(points: Sequence[Sequence[float]], capacity: int) -> tuple[int, ...]:
    tools, _, population = _deap_population(points)
    fronts = tools.sortNondominated(population, k=len(population), first_front_only=False)
    ranked: list[tuple[int, float, int]] = []
    for rank, front in enumerate(fronts):
        tools.emo.assignCrowdingDist(front)
        ranked.extend((rank, -item.fitness.crowding_dist, item.row_index) for item in front)
    return tuple(index for _, _, index in sorted(ranked)[:capacity])


def run_nsga2_reference_benchmark(seeds: Sequence[int]) -> dict[str, Any]:
    """Compare Genesis rank/crowding selection against DEAP's NSGA-II utilities."""
    if len(seeds) < 30:
        raise ValueError("NSGA-II benchmark requires at least 30 seeds")
    from .research import nsga2_ranks, nsga2_select
    rows = []
    for problem in ("zdt1", "dtlz2"):
        for population_size in (100, 250, 500):
            capacity = population_size // 2
            for seed in seeds:
                points = _benchmark_objectives(problem, random.Random(seed), population_size)
                start = time.perf_counter()
                ours = nsga2_select(points, capacity)
                ours_seconds = time.perf_counter() - start
                start = time.perf_counter()
                reference = _deap_select(points, capacity)
                reference_seconds = time.perf_counter() - start
                ours_ranks = nsga2_ranks(points)
                deap_front = _deap_first_front(points)
                ours_front = {index for index, rank in enumerate(ours_ranks) if rank == 0}
                rows.append({
                    "problem": problem,
                    "population_size": population_size,
                    "seed": seed,
                    "capacity": capacity,
                    "selected_overlap_fraction": len(set(ours) & set(reference)) / capacity,
                    "first_front_jaccard": (
                        len(ours_front & deap_front) / len(ours_front | deap_front)
                        if ours_front | deap_front else 1.0
                    ),
                    "genesis_seconds": ours_seconds,
                    "deap_seconds": reference_seconds,
                })
    groups = {}
    for problem in ("zdt1", "dtlz2"):
        groups[problem] = {}
        for size in (100, 250, 500):
            subset = [row for row in rows if row["problem"] == problem and row["population_size"] == size]
            groups[problem][str(size)] = {
                "mean_selected_overlap": statistics.mean(row["selected_overlap_fraction"] for row in subset),
                "mean_first_front_jaccard": statistics.mean(row["first_front_jaccard"] for row in subset),
                "mean_genesis_seconds": statistics.mean(row["genesis_seconds"] for row in subset),
                "mean_deap_seconds": statistics.mean(row["deap_seconds"] for row in subset),
                "replicates": len(subset),
            }
    return {
        "reference": "DEAP tools.sortNondominated + tools.emo.assignCrowdingDist",
        "objective_direction": "minimization benchmark objectives negated to common maximization convention",
        "replicates_per_problem_and_population": len(seeds),
        "results": groups,
        "raw_replicates": rows,
        "caveat": "DEAP is an independent software reference, not a proof of theoretical correctness; tie handling may differ.",
    }


def _random_gp_node(rng: random.Random) -> Primitive | EnergyGuard | RepeatNode:
    action = Primitive(rng.choice((Op.MOVE, Op.GATHER, Op.REST, Op.COOPERATE)), rng.randint(1, 5))
    kind = rng.randrange(3)
    if kind == 0:
        return action
    if kind == 1:
        return EnergyGuard(rng.randint(1, 5), action)
    return RepeatNode(rng.randint(2, 5), action)


def _random_linear_program(rng: random.Random) -> Program:
    nodes = []
    for _ in range(rng.randint(3, 10)):
        action = Action(rng.choice((Op.MOVE, Op.GATHER, Op.REST, Op.COOPERATE)), rng.randint(1, 5))
        kind = rng.randrange(3)
        if kind == 0:
            nodes.append(action)
        elif kind == 1:
            nodes.append(IfEnergyBelow(rng.randint(1, 5), action))
        else:
            nodes.append(RepeatAction(action, rng.randint(1, 4)))
    return Program(tuple(nodes))


def _random_tree_program(rng: random.Random) -> SequenceNode:
    return SequenceNode(tuple(_random_gp_node(rng) for _ in range(rng.randint(3, 10))))


def _tree_to_program(tree: TreeNode) -> Program:
    root = tree if isinstance(tree, SequenceNode) else SequenceNode((tree,))
    nodes = []
    for node in root.children:
        if isinstance(node, Primitive):
            nodes.append(Action(node.op, node.amount))
        elif isinstance(node, EnergyGuard) and isinstance(node.body, Primitive):
            nodes.append(IfEnergyBelow(node.threshold, Action(node.body.op, node.body.amount)))
        elif isinstance(node, RepeatNode) and isinstance(node.body, Primitive):
            nodes.append(RepeatAction(Action(node.body.op, node.body.amount), node.count - 1))
        else:
            raise TypeError("comparison tree contains a node outside the matched grammar")
    return Program(tuple(nodes))


def _program_to_tree(program: Program) -> SequenceNode:
    children = []
    for node in program.nodes:
        if isinstance(node, Action):
            children.append(Primitive(node.op, node.amount))
        elif isinstance(node, IfEnergyBelow):
            children.append(EnergyGuard(node.threshold, Primitive(node.action.op, node.action.amount)))
        elif isinstance(node, RepeatAction):
            children.append(RepeatNode(node.additional_repetitions + 1,
                                       Primitive(node.action.op, node.action.amount)))
        else:
            raise TypeError("linear comparator contains an unsupported node")
    return SequenceNode(tuple(children))


def _mutate_tree_program(tree: SequenceNode, rng: random.Random, rate: float) -> SequenceNode:
    nodes = list(tree.children)
    for index in range(len(nodes)):
        if rng.random() < rate:
            nodes[index] = _random_gp_node(rng)
    if rng.random() < rate and len(nodes) < 16:
        nodes.insert(rng.randrange(len(nodes) + 1), _random_gp_node(rng))
    if rng.random() < rate and len(nodes) > 2:
        del nodes[rng.randrange(len(nodes))]
    return SequenceNode(tuple(nodes))


def _crossover_tree_program(left: SequenceNode, right: SequenceNode,
                            rng: random.Random) -> SequenceNode:
    cut_left = rng.randrange(len(left.children) + 1)
    cut_right = rng.randrange(len(right.children) + 1)
    nodes = left.children[:cut_left] + right.children[cut_right:]
    if not nodes:
        nodes = (rng.choice(left.children),)
    return SequenceNode(tuple(nodes[:16]))


def _gp_fitness(program: Program, seed_id: int) -> tuple[float, int, int, int]:
    genome = program.compile()
    result = evaluate(Organism(seed_id, genome), Environment(
        identifier="matched-gp-foraging-v1", resource_supply=20,
        movement_cost=1, gather_reward=2, cooperation_bonus=1,
    ), initial_energy=20, instruction_budget=256)
    fitness = result.resources_gathered + min(result.cooperation_actions, 10) * 0.25 + result.energy_remaining * 0.05
    return fitness, result.resources_gathered, result.cooperation_actions, result.energy_remaining


def _tree_fitness(tree: SequenceNode, seed_id: int) -> tuple[float, int, int, int]:
    result = evaluate_tree(tree, initial_energy=20, resource_supply=20, instruction_budget=256)
    fitness = result.resources_gathered + min(result.cooperation_actions, 10) * 0.25 + result.energy_remaining * 0.05
    return fitness, result.resources_gathered, result.cooperation_actions, result.energy_remaining


def _tournament(population: Sequence[Any], scores: Sequence[float],
                rng: random.Random, size: int = 3) -> Any:
    candidates = rng.sample(range(len(population)), size)
    return population[max(candidates, key=lambda index: scores[index])]


def run_tree_vs_linear_gp(seeds: Sequence[int]) -> dict[str, Any]:
    """Paired-seed tree-AST vs linear typed-program evolutionary comparison."""
    if len(seeds) < 30:
        raise ValueError("tree-vs-linear GP comparison requires at least 30 seeds")
    rows = []
    population_size, generations = 36, 20
    for seed in seeds:
        init_rng = random.Random(seed)
        paired_initial = [_random_linear_program(init_rng) for _ in range(population_size)]
        linear_population = paired_initial[:]
        tree_population = [_program_to_tree(program) for program in paired_initial]
        linear_rng, tree_rng = random.Random(seed ^ 0x1A2B), random.Random(seed ^ 0x3C4D)
        linear_best_history, tree_best_history = [], []
        for generation in range(generations):
            linear_scores = [_gp_fitness(program, i)[0] for i, program in enumerate(linear_population)]
            tree_scores = [_tree_fitness(tree, i)[0] for i, tree in enumerate(tree_population)]
            linear_best_history.append(max(linear_scores))
            tree_best_history.append(max(tree_scores))
            if generation == generations - 1:
                break
            linear_elites = sorted(range(population_size), key=lambda i: linear_scores[i], reverse=True)[:2]
            tree_elites = sorted(range(population_size), key=lambda i: tree_scores[i], reverse=True)[:2]
            next_linear = [linear_population[i] for i in linear_elites]
            next_tree = [tree_population[i] for i in tree_elites]
            while len(next_linear) < population_size:
                a = _tournament(linear_population, linear_scores, linear_rng)
                b = _tournament(linear_population, linear_scores, linear_rng)
                child = a.crossover(b, linear_rng)
                next_linear.append(child.mutate(linear_rng, 0.18))
                ta = _tournament(tree_population, tree_scores, tree_rng)
                tb = _tournament(tree_population, tree_scores, tree_rng)
                child_tree = _crossover_tree_program(ta, tb, tree_rng)
                next_tree.append(_mutate_tree_program(child_tree, tree_rng, 0.18))
            linear_population, tree_population = next_linear, next_tree
        linear_final = [_gp_fitness(program, i)[0] for i, program in enumerate(linear_population)]
        tree_final = [_tree_fitness(tree, i)[0] for i, tree in enumerate(tree_population)]
        rows.append({
            "seed": seed,
            "linear_best_fitness": max(linear_best_history),
            "tree_best_fitness": max(tree_best_history),
            "linear_final_mean_fitness": statistics.mean(linear_final),
            "tree_final_mean_fitness": statistics.mean(tree_final),
            "linear_final_best_fitness": max(linear_final),
            "tree_final_best_fitness": max(tree_final),
            "linear_best_trajectory": linear_best_history,
            "tree_best_trajectory": tree_best_history,
        })
    differences = [row["tree_best_fitness"] - row["linear_best_fitness"] for row in rows]
    return {
        "design": "same seed, same initial Program phenotypes, same fitness function, same population size and generation count",
        "population_size": population_size,
        "generations": generations,
        "matched_grammar": "primitive actions, one-action energy guards, and repeated actions",
        "replicates": rows,
        "paired_tree_minus_linear_best_fitness": _paired(differences, seed=seeds[0]),
        "summary": {
            "linear_best": _summary([row["linear_best_fitness"] for row in rows], seed=seeds[0]),
            "tree_best": _summary([row["tree_best_fitness"] for row in rows], seed=seeds[0] + 1),
            "linear_final_mean": _summary([row["linear_final_mean_fitness"] for row in rows], seed=seeds[0] + 2),
            "tree_final_mean": _summary([row["tree_final_mean_fitness"] for row in rows], seed=seeds[0] + 3),
        },
        "caveat": "This is a matched grammar subset; it does not compare the full expressivity of arbitrary nested trees with all linear bytecode features.",
    }


def run_empirical_calibration(data_path: str | Path) -> dict[str, Any]:
    observations = load_hudson_bay_csv(data_path)
    return calibrate_empirical_references(observations)


def run_full_campaign(output: str | Path, *, seed_count: int = 30) -> dict[str, Any]:
    if seed_count < 30:
        raise ValueError("research campaign requires at least 30 seeds")
    seeds = tuple(range(1001, 1001 + seed_count))
    root = Path(__file__).resolve().parents[2]
    empirical_path = root / "data" / "empirical" / "hudson_bay_lynx_hare_1900_1920.csv"
    result = {
        "schema": "genesis-research-validation-v1",
        "seed_policy": {"count": seed_count, "seeds": list(seeds), "paired_across_conditions": True},
        "ecological_replicates": run_ecological_replicates(seeds),
        "spatial_reference_comparison": run_spatial_reference_comparison(seeds),
        "speciation_sensitivity": run_speciation_sensitivity(seeds),
        "nsga2_reference_benchmark": run_nsga2_reference_benchmark(seeds),
        "tree_vs_linear_gp": run_tree_vs_linear_gp(seeds),
        "empirical_calibration": run_empirical_calibration(empirical_path),
        "limitations": [
            "30 seeds are a reproducibility floor, not a power analysis.",
            "Spatial model and well-mixed ODEs have different state spaces and observation processes.",
            "Historical pelt indices are indirect abundance proxies and the 1900-1920 slice is short.",
            "Coarse grid calibration is exploratory; final 30% is held out chronologically.",
            "DEAP selection agreement validates implementation parity, not evolutionary convergence quality.",
            "Tree-vs-linear comparison uses a deliberately matched subset of the two grammars.",
        ],
    }
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Genesis Protocol's 30+ seed research campaign")
    parser.add_argument("--seeds", type=int, default=30, help="unique paired seeds (minimum 30)")
    parser.add_argument("--output", default="artifacts/research-validation.json")
    args = parser.parse_args()
    result = run_full_campaign(args.output, seed_count=args.seeds)
    print(json.dumps({
        "output": args.output,
        "seed_count": args.seeds,
        "ecology_conditions": list(result["ecological_replicates"]["conditions"]),
        "spatial_replicates": len(result["spatial_reference_comparison"]["replicates"]),
        "speciation_distributions": list(result["speciation_sensitivity"]["distributions"]),
        "nsga2_cases": sum(len(value) for value in result["nsga2_reference_benchmark"]["results"].values()),
        "tree_gp_replicates": len(result["tree_vs_linear_gp"]["replicates"]),
        "empirical_holdout": {
            name: model["holdout_log_rmse"]
            for name, model in result["empirical_calibration"]["models"].items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
