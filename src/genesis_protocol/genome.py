"""Constrained, serializable genomes for safe policy evaluation."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum


class Op(StrEnum):
    """Instructions understood by the deterministic policy interpreter."""

    MOVE = "move"
    GATHER = "gather"
    REST = "rest"
    COOPERATE = "cooperate"
    IF_ENERGY_BELOW = "if_energy_below"
    IF_RESOURCES_BELOW = "if_resources_below"
    REPEAT_PREVIOUS = "repeat_previous"


@dataclass(frozen=True, slots=True)
class Instruction:
    op: Op
    amount: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.op, Op):
            raise ValueError("instruction opcode must be an Op value")
        if not 1 <= self.amount <= 5:
            raise ValueError("instruction amount must be between 1 and 5")


@dataclass(frozen=True, slots=True)
class Genome:
    instructions: tuple[Instruction, ...]

    def __post_init__(self) -> None:
        if not self.instructions:
            raise ValueError("a genome must contain at least one instruction")
        if len(self.instructions) > 64:
            raise ValueError("genome cannot exceed 64 instructions")

    @classmethod
    def random(cls, rng: random.Random, min_length: int = 4, max_length: int = 16) -> Genome:
        if min_length < 1 or max_length < min_length or max_length > 64:
            raise ValueError("invalid genome length bounds")
        length = rng.randint(min_length, max_length)
        ops = tuple(Op)
        return cls(tuple(Instruction(rng.choice(ops), rng.randint(1, 5)) for _ in range(length)))

    def mutate(self, rng: random.Random, rate: float) -> Genome:
        if not 0.0 <= rate <= 1.0:
            raise ValueError("mutation rate must be in [0, 1]")
        genes = list(self.instructions)
        for index in range(len(genes)):
            if rng.random() < rate:
                genes[index] = Instruction(rng.choice(tuple(Op)), rng.randint(1, 5))
        if rng.random() < rate and len(genes) < 64:
            genes.insert(rng.randrange(len(genes) + 1), Instruction(rng.choice(tuple(Op)), rng.randint(1, 5)))
        if rng.random() < rate and len(genes) > 1:
            del genes[rng.randrange(len(genes))]
        return Genome(tuple(genes))

    def crossover(self, other: Genome, rng: random.Random) -> Genome:
        left = rng.randrange(len(self.instructions) + 1)
        right = rng.randrange(len(other.instructions) + 1)
        child = self.instructions[:left] + other.instructions[right:]
        if not child:
            child = (rng.choice(self.instructions),)
        return Genome(tuple(child[:64]))

    def to_dict(self) -> dict[str, object]:
        return {"instructions": [{"op": item.op.value, "amount": item.amount} for item in self.instructions]}
