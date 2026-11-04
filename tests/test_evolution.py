import json

import pytest

from genesis_protocol.engine import EvolutionConfig, EvolutionEngine
from genesis_protocol.evaluator import evaluate
from genesis_protocol.genome import Genome, Instruction, Op
from genesis_protocol.models import Environment, Organism


def test_same_seed_produces_same_experiment() -> None:
    config = EvolutionConfig(population_size=20, generations=8)
    first = EvolutionEngine(config, seed=42).run().to_dict()
    second = EvolutionEngine(config, seed=42).run().to_dict()
    assert first == second
    json.dumps(first)


def test_different_seeds_are_recorded_and_can_diverge() -> None:
    config = EvolutionConfig(population_size=20, generations=5)
    first = EvolutionEngine(config, seed=1).run()
    second = EvolutionEngine(config, seed=2).run()
    assert first.seed != second.seed


def test_evaluator_respects_resource_supply_and_instruction_budget() -> None:
    genome = Genome(tuple(Instruction(Op.GATHER, 5) for _ in range(10)))
    organism = Organism(1, genome)
    result = evaluate(
        organism,
        Environment(resource_supply=7),
        instruction_budget=3,
    )
    assert result.resources_gathered == 7
    assert result.instructions_executed == 3


def test_genome_rejects_empty_and_oversized_programs() -> None:
    with pytest.raises(ValueError):
        Genome(())
    with pytest.raises(ValueError):
        Genome(tuple(Instruction(Op.REST) for _ in range(65)))


def test_config_rejects_invalid_rates() -> None:
    with pytest.raises(ValueError):
        EvolutionConfig(mutation_rate=1.5)
