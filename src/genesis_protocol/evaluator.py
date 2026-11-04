"""Deterministic bounded interpreter for organism policies."""

from __future__ import annotations

from .genome import Op
from .models import Environment, Evaluation, Organism


def evaluate(
    organism: Organism,
    environment: Environment,
    *,
    initial_energy: int = 20,
    instruction_budget: int = 128,
) -> Evaluation:
    if initial_energy < 0 or instruction_budget < 1:
        raise ValueError("invalid evaluation budget")

    energy = initial_energy
    gathered = 0
    cooperation = 0
    executed = 0

    for instruction in organism.genome.instructions[:instruction_budget]:
        executed += 1
        if instruction.op is Op.MOVE:
            energy = max(0, energy - environment.movement_cost * instruction.amount)
        elif instruction.op is Op.GATHER:
            possible = min(instruction.amount, environment.resource_supply - gathered)
            possible = max(0, possible)
            gathered += possible
            energy += possible * environment.gather_reward
        elif instruction.op is Op.REST:
            energy += instruction.amount
        elif instruction.op is Op.COOPERATE:
            cooperation += instruction.amount
            energy += environment.cooperation_bonus * instruction.amount

    # Explicit task fitness: acquired resources plus a bounded cooperation reward.
    fitness = float(gathered + min(cooperation, 10) * 0.25 + energy * 0.05)
    return Evaluation(
        organism_id=organism.organism_id,
        fitness=fitness,
        energy_remaining=energy,
        resources_gathered=gathered,
        cooperation_actions=cooperation,
        instructions_executed=executed,
    )
