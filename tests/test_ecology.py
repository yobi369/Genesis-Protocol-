import json

import pytest

from genesis_protocol.ecology import (
    EcologyConfig,
    EcosystemEngine,
    EnvironmentalPhase,
    FitnessVector,
    SpeciesDefinition,
    dominates,
    genome_distance,
    pareto_ranks,
)
from genesis_protocol.experiments import compare_conditions
from genesis_protocol.genome import Genome, Instruction, Op


def test_pareto_dominance_and_ranking() -> None:
    strong = FitnessVector(5, 5, 5)
    weak = FitnessVector(2, 2, 2)
    tradeoff = FitnessVector(6, 1, 1)
    assert dominates(strong, weak)
    assert not dominates(strong, tradeoff)
    ranks = pareto_ranks([strong, weak, tradeoff])
    assert ranks[0] == 0
    assert ranks[1] == 1
    assert ranks[2] == 0


def test_shared_resources_are_competed_for_and_never_overdrawn() -> None:
    species = (SpeciesDefinition(0, "alpha", 2), SpeciesDefinition(1, "beta", 2))
    engine = EcosystemEngine(
        species,
        (EnvironmentalPhase(0, resource_supply=3),),
        EcologyConfig(generations=1),
        seed=5,
    )
    population = [
        engine._new(item.species_id, Genome((Instruction(Op.GATHER, 5),)), 0)
        for item in (species[0], species[0], species[1], species[1])
    ]
    outcomes, remaining = engine._evaluate_population(population, engine.schedule[0])
    assert sum(item.resources_gathered for item in outcomes) == 3
    assert remaining == 0


def test_partner_dependent_cooperation_rewards_mutual_cooperators() -> None:
    species = (SpeciesDefinition(0, "pair", 2),)
    engine = EcosystemEngine(
        species, (EnvironmentalPhase(0, 30, cooperation_reward=4),),
        EcologyConfig(generations=1), seed=2,
    )
    genome = Genome((Instruction(Op.COOPERATE, 2),))
    population = [engine._new(0, genome, 0), engine._new(0, genome, 0)]
    outcomes, _ = engine._evaluate_population(population, engine.schedule[0])
    assert all(item.reciprocal_cooperation == 2 for item in outcomes)


def test_dynamic_environment_schedule_changes_by_generation() -> None:
    species = (SpeciesDefinition(0, "one", 4),)
    schedule = (
        EnvironmentalPhase(0, resource_supply=50),
        EnvironmentalPhase(2, resource_supply=9, movement_cost=3),
    )
    result = EcosystemEngine(
        species, schedule, EcologyConfig(generations=4), seed=12,
    ).run()
    assert [item.resource_supply for item in result.reports] == [50, 50, 9, 9]


def test_ecological_run_is_reproducible_and_serializable() -> None:
    species = (SpeciesDefinition(0, "alpha", 8), SpeciesDefinition(1, "beta", 8))
    schedule = (EnvironmentalPhase(0, 60), EnvironmentalPhase(3, 20, movement_cost=2))
    config = EcologyConfig(generations=5)
    first = EcosystemEngine(species, schedule, config, seed=99).run().to_dict()
    second = EcosystemEngine(species, schedule, config, seed=99).run().to_dict()
    assert first == second
    json.dumps(first)


def test_lineage_records_preserve_parentage() -> None:
    species = (SpeciesDefinition(0, "founders", 6),)
    result = EcosystemEngine(
        species, (EnvironmentalPhase(0, 40),), EcologyConfig(generations=3), seed=8,
    ).run()
    children = [item for item in result.lineage if item.generation_born > 0]
    assert children
    assert all(item.parent_ids for item in children)


def test_speciation_can_create_new_species_and_lineage_branch() -> None:
    species = (SpeciesDefinition(0, "founder", 10),)
    result = EcosystemEngine(
        species,
        (EnvironmentalPhase(0, 100),),
        EcologyConfig(generations=3, mutation_rate=1.0, speciation_distance=0.01),
        seed=17,
    ).run()
    assert len(result.species) >= 2
    assert any(item.species_id > 0 for item in result.lineage)


def test_genome_distance_is_normalized() -> None:
    a = Genome((Instruction(Op.REST), Instruction(Op.MOVE)))
    b = Genome((Instruction(Op.GATHER), Instruction(Op.MOVE)))
    assert genome_distance(a, b) == 0.5


def test_paired_experiment_comparison_requires_unique_replicates() -> None:
    species = (SpeciesDefinition(0, "replicators", 5),)
    schedule = (EnvironmentalPhase(0, 30),)
    config = EcologyConfig(generations=2)
    with pytest.raises(ValueError):
        compare_conditions(species, schedule, config, config, seeds=(1, 1))


def test_paired_experiment_comparison_records_uncertainty() -> None:
    species = (SpeciesDefinition(0, "replicators", 6),)
    schedule = (EnvironmentalPhase(0, 30),)
    baseline = EcologyConfig(generations=2, mutation_rate=0.02)
    candidate = EcologyConfig(generations=2, mutation_rate=0.2)
    comparison = compare_conditions(species, schedule, baseline, candidate, seeds=(2, 3, 5))
    assert comparison.replicate_count == 3
    assert len(comparison.confidence_interval_95_normal) == 2
    assert comparison.to_dict()["metric"] == "final_mean_resources_per_organism"
