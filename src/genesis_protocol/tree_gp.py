"""Nested tree genetic programming with a bounded, host-isolated interpreter."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TypeAlias

from .genome import Op


@dataclass(frozen=True, slots=True)
class Primitive:
    op: Op
    amount: int = 1

    def __post_init__(self) -> None:
        if self.op not in (Op.MOVE, Op.GATHER, Op.REST, Op.COOPERATE):
            raise ValueError("tree primitive must be an action")
        if not 1 <= self.amount <= 5:
            raise ValueError("primitive amount must be in [1, 5]")


@dataclass(frozen=True, slots=True)
class SequenceNode:
    children: tuple[TreeNode, ...]

    def __post_init__(self) -> None:
        if not self.children or len(self.children) > 16:
            raise ValueError("sequence requires 1 to 16 children")


@dataclass(frozen=True, slots=True)
class EnergyGuard:
    threshold: int
    body: TreeNode

    def __post_init__(self) -> None:
        if not 0 <= self.threshold <= 100:
            raise ValueError("energy threshold must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class RepeatNode:
    count: int
    body: TreeNode

    def __post_init__(self) -> None:
        if not 1 <= self.count <= 5:
            raise ValueError("repeat count must be in [1, 5]")


TreeNode: TypeAlias = Primitive | SequenceNode | EnergyGuard | RepeatNode


@dataclass(frozen=True, slots=True)
class TreeEvaluation:
    energy_remaining: int
    resources_gathered: int
    cooperation_actions: int
    instructions_executed: int
    budget_exhausted: bool


def tree_depth(node: TreeNode) -> int:
    if isinstance(node, Primitive):
        return 1
    if isinstance(node, SequenceNode):
        return 1 + max(tree_depth(child) for child in node.children)
    return 1 + tree_depth(node.body)


def tree_size(node: TreeNode) -> int:
    if isinstance(node, Primitive):
        return 1
    if isinstance(node, SequenceNode):
        return 1 + sum(tree_size(child) for child in node.children)
    return 1 + tree_size(node.body)


def evaluate_tree(root: TreeNode, *, initial_energy: int = 20,
                  resource_supply: int = 20, instruction_budget: int = 128
                  ) -> TreeEvaluation:
    if min(initial_energy, resource_supply) < 0 or instruction_budget < 1:
        raise ValueError("invalid initial state or instruction budget")
    energy, gathered, cooperation, executed = initial_energy, 0, 0, 0
    exhausted = False

    def visit(node: TreeNode) -> None:
        nonlocal energy, gathered, cooperation, executed, exhausted
        if executed >= instruction_budget:
            exhausted = True
            return
        executed += 1
        if isinstance(node, Primitive):
            if node.op is Op.MOVE:
                energy = max(0, energy - node.amount)
            elif node.op is Op.GATHER:
                amount = min(node.amount, max(0, resource_supply - gathered))
                gathered += amount
                energy += amount * 2
            elif node.op is Op.REST:
                energy += node.amount
            else:
                cooperation += node.amount
                energy += node.amount
        elif isinstance(node, SequenceNode):
            for child in node.children:
                visit(child)
                if exhausted:
                    break
        elif isinstance(node, EnergyGuard):
            if energy < node.threshold:
                visit(node.body)
        else:
            for _ in range(node.count):
                visit(node.body)
                if exhausted:
                    break

    visit(root)
    return TreeEvaluation(energy, gathered, cooperation, executed, exhausted)


def random_tree(rng: random.Random, *, max_depth: int = 4) -> TreeNode:
    if not 1 <= max_depth <= 8:
        raise ValueError("max_depth must be in [1, 8]")
    actions = (Op.MOVE, Op.GATHER, Op.REST, Op.COOPERATE)
    if max_depth == 1 or rng.random() < 0.4:
        return Primitive(rng.choice(actions), rng.randint(1, 5))
    choice = rng.randrange(3)
    if choice == 0:
        return SequenceNode(tuple(random_tree(rng, max_depth=max_depth - 1)
                                  for _ in range(rng.randint(1, 3))))
    if choice == 1:
        return EnergyGuard(rng.randint(0, 20),
                           random_tree(rng, max_depth=max_depth - 1))
    return RepeatNode(rng.randint(1, 3),
                      random_tree(rng, max_depth=max_depth - 1))


def mutate_tree(root: TreeNode, rng: random.Random, *, max_depth: int = 4) -> TreeNode:
    """Bounded subtree replacement; root replacement guarantees a valid AST."""
    if rng.random() < 0.25:
        return random_tree(rng, max_depth=max_depth)
    if isinstance(root, SequenceNode):
        children = list(root.children)
        index = rng.randrange(len(children))
        children[index] = random_tree(rng, max_depth=max(1, max_depth - 1))
        return SequenceNode(tuple(children))
    if isinstance(root, EnergyGuard):
        return EnergyGuard(root.threshold, random_tree(rng, max_depth=max(1, max_depth - 1)))
    if isinstance(root, RepeatNode):
        return RepeatNode(root.count, random_tree(rng, max_depth=max(1, max_depth - 1)))
    return random_tree(rng, max_depth=max_depth)


def crossover_trees(left: TreeNode, right: TreeNode, rng: random.Random,
                    *, max_depth: int = 6) -> TreeNode:
    """A safe bounded crossover that inserts the right parent as a subtree."""
    if max_depth < 1:
        raise ValueError("max_depth must be positive")
    if isinstance(left, SequenceNode) and tree_depth(right) < max_depth:
        children = list(left.children)
        children[rng.randrange(len(children))] = right
        child: TreeNode = SequenceNode(tuple(children))
    else:
        child = right if rng.random() < 0.5 else left
    return child if tree_depth(child) <= max_depth else left
