"""Typed structured genetic-programming representation.

Programs compile to the bounded Genesis instruction set; no host-language code
is evaluated. Conditional bodies are intentionally one action so compilation
preserves the interpreter's single-instruction branch semantics.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TypeAlias

from .genome import Genome, Instruction, Op


@dataclass(frozen=True, slots=True)
class Action:
    op: Op
    amount: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.op, Op) or self.op not in (Op.MOVE, Op.GATHER, Op.REST, Op.COOPERATE):
            raise ValueError("Action requires a primitive action opcode")
        if not 1 <= self.amount <= 5:
            raise ValueError("action amount must be between 1 and 5")


@dataclass(frozen=True, slots=True)
class IfEnergyBelow:
    threshold: int
    action: Action

    def __post_init__(self) -> None:
        if not 1 <= self.threshold <= 5:
            raise ValueError("energy threshold must be between 1 and 5")


@dataclass(frozen=True, slots=True)
class IfResourcesBelow:
    threshold: int
    action: Action

    def __post_init__(self) -> None:
        if not 1 <= self.threshold <= 5:
            raise ValueError("resource threshold must be between 1 and 5")


@dataclass(frozen=True, slots=True)
class RepeatAction:
    action: Action
    additional_repetitions: int

    def __post_init__(self) -> None:
        if not 1 <= self.additional_repetitions <= 5:
            raise ValueError("repeat count must be between 1 and 5")


ProgramNode: TypeAlias = Action | IfEnergyBelow | IfResourcesBelow | RepeatAction


@dataclass(frozen=True, slots=True)
class Program:
    nodes: tuple[ProgramNode, ...]

    def __post_init__(self) -> None:
        if not self.nodes or len(self.nodes) > 32:
            raise ValueError("program must contain between 1 and 32 nodes")

    def compile(self) -> Genome:
        instructions: list[Instruction] = []
        for node in self.nodes:
            if isinstance(node, Action):
                instructions.append(Instruction(node.op, node.amount))
            elif isinstance(node, IfEnergyBelow):
                instructions.extend((
                    Instruction(Op.IF_ENERGY_BELOW, node.threshold),
                    Instruction(node.action.op, node.action.amount),
                ))
            elif isinstance(node, IfResourcesBelow):
                instructions.extend((
                    Instruction(Op.IF_RESOURCES_BELOW, node.threshold),
                    Instruction(node.action.op, node.action.amount),
                ))
            elif isinstance(node, RepeatAction):
                instructions.extend((
                    Instruction(node.action.op, node.action.amount),
                    Instruction(Op.REPEAT_PREVIOUS, node.additional_repetitions),
                ))
        if len(instructions) > 64:
            raise ValueError("compiled program exceeds the 64-instruction genome limit")
        return Genome(tuple(instructions))

    @classmethod
    def random(cls, rng: random.Random, min_nodes: int = 2, max_nodes: int = 12) -> Program:
        if min_nodes < 1 or max_nodes < min_nodes or max_nodes > 32:
            raise ValueError("invalid program node bounds")
        actions = (Op.MOVE, Op.GATHER, Op.REST, Op.COOPERATE)
        nodes: list[ProgramNode] = []
        for _ in range(rng.randint(min_nodes, max_nodes)):
            choice = rng.randrange(4)
            action = Action(rng.choice(actions), rng.randint(1, 5))
            if choice == 0:
                nodes.append(action)
            elif choice == 1:
                nodes.append(IfEnergyBelow(rng.randint(1, 5), action))
            elif choice == 2:
                nodes.append(IfResourcesBelow(rng.randint(1, 5), action))
            else:
                nodes.append(RepeatAction(action, rng.randint(1, 5)))
        return cls(tuple(nodes))

    def mutate(self, rng: random.Random, rate: float) -> Program:
        if not 0 <= rate <= 1:
            raise ValueError("mutation rate must be in [0, 1]")
        nodes = list(self.nodes)
        for index in range(len(nodes)):
            if rng.random() < rate:
                nodes[index] = Program.random(rng, 1, 1).nodes[0]
        if rng.random() < rate and len(nodes) < 32:
            nodes.insert(rng.randrange(len(nodes) + 1), Program.random(rng, 1, 1).nodes[0])
        if rng.random() < rate and len(nodes) > 1:
            del nodes[rng.randrange(len(nodes))]
        return Program(tuple(nodes))

    def crossover(self, other: Program, rng: random.Random) -> Program:
        left = rng.randrange(len(self.nodes) + 1)
        right = rng.randrange(len(other.nodes) + 1)
        nodes = self.nodes[:left] + other.nodes[right:]
        if not nodes:
            nodes = (rng.choice(self.nodes),)
        return Program(tuple(nodes[:32]))
