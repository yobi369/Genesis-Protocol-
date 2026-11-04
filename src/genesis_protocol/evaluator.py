"""Deterministic bounded interpreter for linear and conditional genomes."""

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
    pc = 0

    def apply(op: Op, amount: int) -> None:
        nonlocal energy, gathered, cooperation
        if op is Op.MOVE:
            energy = max(0, energy - environment.movement_cost * amount)
        elif op is Op.GATHER:
            possible = max(0, min(amount, environment.resource_supply - gathered))
            gathered += possible
            energy += possible * environment.gather_reward
        elif op is Op.REST:
            energy += amount
        elif op is Op.COOPERATE:
            cooperation += amount
            energy += environment.cooperation_bonus * amount

    instructions = organism.genome.instructions
    previous_action: tuple[Op, int] | None = None
    while pc < len(instructions) and executed < instruction_budget:
        instruction = instructions[pc]
        executed += 1
        if instruction.op is Op.IF_ENERGY_BELOW:
            pc += 1 if energy < instruction.amount else 2
            continue
        if instruction.op is Op.IF_RESOURCES_BELOW:
            remaining = max(0, environment.resource_supply - gathered)
            pc += 1 if remaining < instruction.amount else 2
            continue
        if instruction.op is Op.REPEAT_PREVIOUS:
            if previous_action is not None:
                for _ in range(instruction.amount):
                    if executed >= instruction_budget:
                        break
                    apply(*previous_action)
                    executed += 1
            pc += 1
            continue
        apply(instruction.op, instruction.amount)
        previous_action = (instruction.op, instruction.amount)
        pc += 1

    fitness = float(gathered + min(cooperation, 10) * 0.25 + energy * 0.05)
    return Evaluation(
        organism_id=organism.organism_id,
        fitness=fitness,
        energy_remaining=energy,
        resources_gathered=gathered,
        cooperation_actions=cooperation,
        instructions_executed=executed,
    )
