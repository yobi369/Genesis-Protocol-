import random

import pytest

from genesis_protocol.ecology import LineageRecord
from genesis_protocol.genome import Genome, Instruction, Op
from genesis_protocol.research import (
    SpatialConfig,
    SpatialEcosystem,
    cluster_genomes,
    compare_reference_policies,
    hypervolume_3d,
    levenshtein_distance,
    normalized_genome_distance,
    pareto_convergence,
    pareto_front_indices,
    run_reference_model,
    validate_lineage,
)
from genesis_protocol.statistics import (
    bootstrap_mean_interval,
    paired_effect_summary,
    paired_permutation_test,
)
from genesis_protocol.tree_gp import (
    EnergyGuard,
    Primitive,
    RepeatNode,
    SequenceNode,
    crossover_trees,
    evaluate_tree,
    mutate_tree,
    random_tree,
    tree_depth,
    tree_size,
)


def test_reference_policies_are_reproducible_and_distinct():
    a = run_reference_model(seed=4, policy="harvest", steps=8)
    assert a == run_reference_model(seed=4, policy="harvest", steps=8)
    report = compare_reference_policies(seeds=(2, 5), steps=4, population=3)
    assert set(report["summaries"]) == {"harvest", "conserve", "alternate"}
    assert len(report["replicates"]) == 6
    with pytest.raises(ValueError):
        run_reference_model(seed=1, policy="unknown")
    with pytest.raises(ValueError):
        compare_reference_policies(seeds=(1, 1))


def test_spatial_ecosystem_and_social_ties_are_seeded():
    config = SpatialConfig(width=1, height=1, prey=4, predators=0,
                            resource_regrowth=1, steps=5)
    first = SpatialEcosystem(config, seed=8).run()
    second = SpatialEcosystem(config, seed=8).run()
    assert first == second
    assert len(first.trajectory) == 5
    assert first.trajectory[-1].prey >= 1
    assert first.social_ties
    with pytest.raises(ValueError):
        SpatialConfig(width=0)


def test_spatial_predation_occurs_in_single_cell():
    result = SpatialEcosystem(
        SpatialConfig(width=1, height=1, prey=3, predators=1, steps=2), seed=2
    ).run()
    assert sum(row.predation_events for row in result.trajectory) >= 1


def test_edit_distance_clustering_and_lineage_validation():
    assert levenshtein_distance(("a", "b"), ("a", "c", "d")) == 2
    a = Genome((Instruction(Op.MOVE), Instruction(Op.GATHER)))
    b = Genome((Instruction(Op.MOVE), Instruction(Op.REST)))
    assert normalized_genome_distance(a, b) == 0.5
    assert len(cluster_genomes((a, b), 0.1)) == 2
    assert len(cluster_genomes((a, b), 1.0)) == 1
    rows = (
        LineageRecord(0, 0, (), 0),
        LineageRecord(1, 0, (0,), 1),
    )
    assert validate_lineage(rows)["valid"] is True
    bad = (LineageRecord(1, 0, (8,), 0),)
    assert validate_lineage(bad)["missing_parents"] == 1
    assert validate_lineage((LineageRecord(0, 0, (0,), 0),))["temporal_violations"] == 1
    with pytest.raises(ValueError):
        cluster_genomes((a,), 0)


def test_pareto_reference_and_hypervolume():
    points = ((1, 1, 1), (2, 0, 0), (0, 2, 0), (0, 0, 2), (0.5, 0.5, 0.5))
    assert pareto_front_indices(points) == (0, 1, 2, 3)
    assert hypervolume_3d(((1, 1, 1),), (0, 0, 0)) == 1
    history = pareto_convergence((points, ((2, 2, 2),)))
    assert history[0]["front_size"] == 4
    assert history[1]["hypervolume_3d"] == 8


def test_nested_tree_evaluation_and_bounds():
    tree = SequenceNode((
        Primitive(Op.GATHER, 2),
        EnergyGuard(30, Primitive(Op.REST, 2)),
        RepeatNode(2, Primitive(Op.COOPERATE, 1)),
    ))
    result = evaluate_tree(tree, initial_energy=2, resource_supply=5)
    assert result.resources_gathered == 2
    assert result.cooperation_actions == 2
    assert result.instructions_executed == 7
    assert tree_depth(tree) == 3
    assert tree_size(tree) == 6
    limited = evaluate_tree(RepeatNode(5, Primitive(Op.REST)), instruction_budget=2)
    assert limited.budget_exhausted
    with pytest.raises(ValueError):
        evaluate_tree(tree, instruction_budget=0)
    with pytest.raises(ValueError):
        Primitive(Op.IF_ENERGY_BELOW)


def test_tree_generation_mutation_crossover_are_bounded():
    rng = random.Random(11)
    left = random_tree(rng, max_depth=4)
    right = random_tree(rng, max_depth=3)
    assert tree_depth(left) <= 4
    assert tree_size(left) >= 1
    changed = mutate_tree(left, rng, max_depth=4)
    child = crossover_trees(left, right, rng, max_depth=6)
    assert tree_depth(changed) <= 4
    assert tree_depth(child) <= 6
    with pytest.raises(ValueError):
        random_tree(rng, max_depth=9)


def test_distribution_free_statistics_are_reproducible():
    differences = (1.0, 2.0, 2.5, 3.0, 4.0)
    first = paired_permutation_test(differences, permutations=500, seed=9)
    assert first == paired_permutation_test(differences, permutations=500, seed=9)
    assert 0 < first["p_value_two_sided"] <= 1
    interval = bootstrap_mean_interval(differences, replicates=300, seed=9)
    assert interval[0] <= interval[1]
    summary = paired_effect_summary(differences)
    assert summary["n"] == 5
    with pytest.raises(ValueError):
        paired_permutation_test((1.0,))
    with pytest.raises(ValueError):
        bootstrap_mean_interval((1.0, 2.0), replicates=10)
    with pytest.raises(ValueError):
        paired_effect_summary((1.0,))



def test_nsga2_reference_ranking_crowding_and_selection():
    points = ((1, 1, 1), (2, 0, 0), (0, 2, 0), (0, 0, 2), (0, 0, 0))
    ranks = nsga2_ranks(points)
    assert ranks == (0, 0, 0, 0, 1)
    distances = nsga2_crowding(points, ranks)
    assert sum(value == float("inf") for value in distances[:4]) >= 1\n    assert distances[0] >= 0
    selected = nsga2_select(points, 3)
    assert len(selected) == 3
    assert all(index != 4 for index in selected)
    with pytest.raises(ValueError):
        nsga2_select(points, -1)
    with pytest.raises(ValueError):
        nsga2_crowding(points, (0,))
