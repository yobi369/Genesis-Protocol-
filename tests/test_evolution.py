import json
import sys

import pytest

from genesis_protocol.cli import main
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


def test_different_seeds_are_recorded() -> None:
    config = EvolutionConfig(population_size=20, generations=5)
    first = EvolutionEngine(config, seed=1).run()
    second = EvolutionEngine(config, seed=2).run()
    assert first.seed != second.seed


def test_evaluator_respects_resource_supply_and_instruction_budget() -> None:
    genome = Genome(tuple(Instruction(Op.GATHER, 5) for _ in range(10)))
    result = evaluate(Organism(1, genome), Environment(resource_supply=7), instruction_budget=3)
    assert result.resources_gathered == 7
    assert result.instructions_executed == 3


def test_genome_rejects_empty_and_oversized_programs() -> None:
    with pytest.raises(ValueError):
        Genome(())
    with pytest.raises(ValueError):
        Genome(tuple(Instruction(Op.REST) for _ in range(65)))


def test_config_rejects_invalid_rates_and_bounds() -> None:
    with pytest.raises(ValueError):
        EvolutionConfig(mutation_rate=1.5)
    with pytest.raises(ValueError):
        EvolutionConfig(population_size=1)
    with pytest.raises(ValueError):
        EvolutionConfig(tournament_size=101)


def test_genome_random_mutation_and_crossover_are_bounded() -> None:
    import random

    rng = random.Random(9)
    first = Genome.random(rng, 4, 8)
    second = Genome.random(rng, 4, 8)
    mutated = first.mutate(rng, 1.0)
    child = first.crossover(second, rng)
    assert 1 <= len(mutated.instructions) <= 64
    assert 1 <= len(child.instructions) <= 64
    assert all(1 <= gene.amount <= 5 for gene in mutated.instructions)


def test_genome_rejects_invalid_mutation_rate_and_random_bounds() -> None:
    import random

    genome = Genome((Instruction(Op.REST),))
    with pytest.raises(ValueError):
        genome.mutate(random.Random(1), -0.1)
    with pytest.raises(ValueError):
        Genome.random(random.Random(1), 0, 2)


def test_environment_rejects_negative_quantities() -> None:
    with pytest.raises(ValueError):
        Environment(resource_supply=-1)
    with pytest.raises(ValueError):
        Environment(movement_cost=-1)


def test_cli_writes_json_experiment_record(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["genesis-run", "--seed", "3", "--generations", "2", "--population", "4", "--output", "run.json"],
    )
    main()
    record = json.loads((tmp_path / "run.json").read_text(encoding="utf-8"))
    assert record["seed"] == 3
    assert len(record["metrics"]) == 2
