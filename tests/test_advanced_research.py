from genesis_protocol.advanced_gp import run_matched_gp_landscapes
from genesis_protocol.advanced_research import (
    PredatorReproductionConfig,
    ReproductiveSpatialEcosystem,
    crossover_tree_advanced,
    mutate_tree_advanced,
    run_richer_tree_operator_smoke,
)
from genesis_protocol.research import SpatialConfig, SpatialEcosystem
from genesis_protocol.tree_gp import random_tree, tree_depth, tree_size
import random


def test_predator_reproduction_disabled_matches_existing_spatial_population_counts():
    config = SpatialConfig(width=8, height=8, prey=12, predators=3,
                           resource_regrowth=1, steps=12, initial_energy=10)
    baseline = SpatialEcosystem(config, seed=41).run()
    candidate = ReproductiveSpatialEcosystem(
        PredatorReproductionConfig(config, reproduction_threshold=None), seed=41
    ).run()
    assert [(p.prey, p.predators) for p in candidate] == [
        (p.prey, p.predators) for p in baseline.trajectory
    ]


def test_predator_births_are_energy_gated_and_population_bounded():
    config = SpatialConfig(width=6, height=6, prey=20, predators=4,
                           resource_regrowth=2, steps=30, initial_energy=12)
    model = ReproductiveSpatialEcosystem(
        PredatorReproductionConfig(
            config, reproduction_threshold=1, reproduction_cost=1,
            offspring_energy=8, reproduction_probability=1.0,
            predator_cap_multiplier=2,
        ), seed=9,
    )
    trajectory = model.run()
    assert sum(point.predator_births for point in trajectory) > 0
    assert max(point.predators for point in trajectory) <= 8


def test_advanced_tree_operators_preserve_depth_and_size_budgets():
    rng = random.Random(101)
    left, right = random_tree(rng, max_depth=4), random_tree(rng, max_depth=4)
    for _ in range(50):
        left = mutate_tree_advanced(left, rng, max_depth=6, max_size=64)
        child = crossover_tree_advanced(left, right, rng, max_depth=6, max_size=64)
        assert tree_depth(child) <= 6
        assert tree_size(child) <= 64


def test_richer_tree_operator_campaign_has_30_replicates():
    result = run_richer_tree_operator_smoke(tuple(range(30)))
    assert len(result["replicates"]) == 30
    assert result["operator_trials_per_seed"] == 100


def test_matched_gp_runs_four_landscapes_with_paired_replicates():
    result = run_matched_gp_landscapes(
        tuple(range(30)), population_size=6, generations=3
    )
    assert set(result["results"]) == {
        "foraging", "energy_conservation", "cooperation", "balanced"
    }
    assert all(row["replicates"] == 30 for row in result["results"].values())
