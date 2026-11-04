import random

import pytest

from genesis_protocol.evaluator import evaluate
from genesis_protocol.genome import Op
from genesis_protocol.models import Environment, Organism
from genesis_protocol.program import Action, IfEnergyBelow, IfResourcesBelow, Program, RepeatAction


def test_structured_program_compiles_to_bounded_genome() -> None:
    program = Program((
        Action(Op.REST, 2),
        IfEnergyBelow(5, Action(Op.GATHER, 3)),
        IfResourcesBelow(2, Action(Op.COOPERATE, 1)),
        RepeatAction(Action(Op.MOVE, 1), 2),
    ))
    genome = program.compile()
    assert len(genome.instructions) == 7
    assert genome.instructions[1].op is Op.IF_ENERGY_BELOW
    assert genome.instructions[-1].op is Op.REPEAT_PREVIOUS


def test_program_mutation_and_crossover_preserve_bounds() -> None:
    rng = random.Random(123)
    left = Program.random(rng, 3, 8)
    right = Program.random(rng, 3, 8)
    mutated = left.mutate(rng, 1.0)
    child = left.crossover(right, rng)
    assert 1 <= len(mutated.nodes) <= 32
    assert 1 <= len(child.nodes) <= 32
    assert len(mutated.compile().instructions) <= 64
    assert len(child.compile().instructions) <= 64


def test_program_rejects_invalid_node_bounds_and_mutation_rate() -> None:
    with pytest.raises(ValueError):
        Program(())
    with pytest.raises(ValueError):
        Program.random(random.Random(1), 0, 2)
    with pytest.raises(ValueError):
        Program((RepeatAction(Action(Op.REST), 0),))


def test_conditional_execution_skips_or_executes_one_action() -> None:
    # Energy is 20, so IF_ENERGY_BELOW 5 skips the gather instruction.
    skipped = Program((
        IfEnergyBelow(5, Action(Op.GATHER, 3)),
        Action(Op.REST, 1),
    )).compile()
    result = evaluate(Organism(1, skipped), Environment(), initial_energy=20)
    assert result.resources_gathered == 0
    assert result.energy_remaining == 21

    # IF_RESOURCES_BELOW 5 executes its action when supply is only 2.
    executed = Program((IfResourcesBelow(5, Action(Op.GATHER, 3)),)).compile()
    result = evaluate(Organism(2, executed), Environment(resource_supply=2))
    assert result.resources_gathered == 2


def test_repeat_action_obeys_instruction_budget() -> None:
    genome = Program((RepeatAction(Action(Op.REST, 2), 5),)).compile()
    result = evaluate(Organism(3, genome), Environment(), instruction_budget=3)
    assert result.energy_remaining == 24
    assert result.instructions_executed == 3
