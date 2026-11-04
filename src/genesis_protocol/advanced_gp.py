"""Matched tree/linear GP comparisons across distinct fitness landscapes."""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path
from typing import Any, Sequence

from .evaluator import evaluate
from .genome import Op
from .models import Environment, Organism
from .program import Action, IfEnergyBelow, Program, RepeatAction
from .tree_gp import EnergyGuard, Primitive, RepeatNode, SequenceNode, TreeNode, evaluate_tree


ACTIONS = (Op.MOVE, Op.GATHER, Op.REST, Op.COOPERATE)
LANDSCAPES = ("foraging", "energy_conservation", "cooperation", "balanced")


def _random_pair(rng: random.Random) -> tuple[Program, SequenceNode]:
    nodes = []
    for _ in range(rng.randint(3, 8)):
        action = Action(rng.choice(ACTIONS), rng.randint(1, 5))
        kind = rng.randrange(3)
        if kind == 0:
            nodes.append(action)
        elif kind == 1:
            nodes.append(IfEnergyBelow(rng.randint(1, 5), action))
        else:
            nodes.append(RepeatAction(action, rng.randint(1, 4)))
    program = Program(tuple(nodes))
    children: list[TreeNode] = []
    for node in program.nodes:
        if isinstance(node, Action):
            children.append(Primitive(node.op, node.amount))
        elif isinstance(node, IfEnergyBelow):
            children.append(EnergyGuard(node.threshold, Primitive(node.action.op, node.action.amount)))
        else:
            children.append(RepeatNode(node.additional_repetitions + 1,
                                       Primitive(node.action.op, node.action.amount)))
    return program, SequenceNode(tuple(children))


def _program_from_tree(tree: SequenceNode) -> Program:
    nodes = []
    for node in tree.children:
        if isinstance(node, Primitive):
            nodes.append(Action(node.op, node.amount))
        elif isinstance(node, EnergyGuard) and isinstance(node.body, Primitive):
            nodes.append(IfEnergyBelow(node.threshold, Action(node.body.op, node.body.amount)))
        elif isinstance(node, RepeatNode) and isinstance(node.body, Primitive):
            nodes.append(RepeatAction(Action(node.body.op, node.body.amount), node.count - 1))
        else:
            raise TypeError("matched comparison tree escaped its common grammar")
    return Program(tuple(nodes))


def _score(metrics: tuple[float, float, float, float], landscape: str) -> float:
    gathered, cooperation, energy, instructions = metrics
    if landscape == "foraging":
        return gathered + 0.25 * min(cooperation, 10) + 0.05 * energy
    if landscape == "energy_conservation":
        return energy + 0.15 * gathered - 0.20 * instructions
    if landscape == "cooperation":
        return 2.0 * cooperation + 0.10 * energy + 0.05 * gathered
    if landscape == "balanced":
        return 0.50 * gathered + 0.50 * cooperation + 0.10 * energy - 0.02 * instructions
    raise ValueError("unknown fitness landscape")


def _linear_metrics(program: Program, seed_id: int) -> tuple[float, float, float, float]:
    result = evaluate(
        Organism(seed_id, program.compile()),
        Environment(identifier="matched-multilandscape-v1", resource_supply=20,
                    movement_cost=1, gather_reward=2, cooperation_bonus=1),
        initial_energy=20, instruction_budget=256,
    )
    return (float(result.resources_gathered), float(result.cooperation_actions),
            float(result.energy_remaining), float(result.instructions_executed))


def _tree_metrics(tree: SequenceNode) -> tuple[float, float, float, float]:
    result = evaluate_tree(tree, initial_energy=20, resource_supply=20, instruction_budget=256)
    return (float(result.resources_gathered), float(result.cooperation_actions),
            float(result.energy_remaining), float(result.instructions_executed))


def _mutate_program(program: Program, rng: random.Random, rate: float = 0.18) -> Program:
    nodes = list(program.nodes)
    for index, node in enumerate(nodes):
        if rng.random() < rate:
            replacement, _ = _random_pair(rng)
            nodes[index] = replacement.nodes[0]
    if rng.random() < rate and len(nodes) < 16:
        replacement, _ = _random_pair(rng)
        nodes.insert(rng.randrange(len(nodes) + 1), replacement.nodes[0])
    if rng.random() < rate and len(nodes) > 1:
        del nodes[rng.randrange(len(nodes))]
    return Program(tuple(nodes[:16]))


def _mutate_tree(tree: SequenceNode, rng: random.Random, rate: float = 0.18) -> SequenceNode:
    children = list(tree.children)
    for index in range(len(children)):
        if rng.random() < rate:
            _, replacement = _random_pair(rng)
            children[index] = replacement.children[0]
    if rng.random() < rate and len(children) < 16:
        _, replacement = _random_pair(rng)
        children.insert(rng.randrange(len(children) + 1), replacement.children[0])
    if rng.random() < rate and len(children) > 1:
        del children[rng.randrange(len(children))]
    return SequenceNode(tuple(children[:16]))


def _cross_program(left: Program, right: Program, rng: random.Random) -> Program:
    a = rng.randrange(len(left.nodes) + 1)
    b = rng.randrange(len(right.nodes) + 1)
    nodes = left.nodes[:a] + right.nodes[b:]
    return Program(tuple(nodes[:16] or (rng.choice(left.nodes),)))


def _cross_tree(left: SequenceNode, right: SequenceNode, rng: random.Random) -> SequenceNode:
    a = rng.randrange(len(left.children) + 1)
    b = rng.randrange(len(right.children) + 1)
    children = left.children[:a] + right.children[b:]
    return SequenceNode(tuple(children[:16] or (rng.choice(left.children),)))


def _tournament(population: Sequence[Any], scores: Sequence[float], rng: random.Random) -> Any:
    candidates = rng.sample(range(len(population)), 3)
    return population[max(candidates, key=lambda i: scores[i])]


def run_matched_gp_landscapes(seeds: Sequence[int], *,
                              population_size: int = 36,
                              generations: int = 20) -> dict[str, Any]:
    """Compare paired common-grammar phenotypes under four fitness landscapes."""
    if len(seeds) < 30 or len(set(seeds)) != len(seeds):
        raise ValueError("multi-landscape GP requires >=30 unique seeds")
    all_rows = []
    summaries: dict[str, Any] = {}
    for landscape_index, landscape in enumerate(LANDSCAPES):
        rows = []
        for seed in seeds:
            init_rng = random.Random(seed + landscape_index * 100_003)
            pairs = [_random_pair(init_rng) for _ in range(population_size)]
            linear_pop = [pair[0] for pair in pairs]
            tree_pop = [pair[1] for pair in pairs]
            lrng = random.Random(seed ^ (0x1A2B + landscape_index))
            trng = random.Random(seed ^ (0x3C4D + landscape_index))
            linear_history, tree_history = [], []
            for generation in range(generations):
                ls = [_score(_linear_metrics(p, i), landscape)
                      for i, p in enumerate(linear_pop)]
                ts = [_score(_tree_metrics(t), landscape) for t in tree_pop]
                linear_history.append(max(ls))
                tree_history.append(max(ts))
                if generation == generations - 1:
                    break
                le = sorted(range(population_size), key=lambda i: ls[i], reverse=True)[:2]
                te = sorted(range(population_size), key=lambda i: ts[i], reverse=True)[:2]
                next_l = [linear_pop[i] for i in le]
                next_t = [tree_pop[i] for i in te]
                while len(next_l) < population_size:
                    la, lb = _tournament(linear_pop, ls, lrng), _tournament(linear_pop, ls, lrng)
                    ta, tb = _tournament(tree_pop, ts, trng), _tournament(tree_pop, ts, trng)
                    next_l.append(_mutate_program(_cross_program(la, lb, lrng), lrng))
                    next_t.append(_mutate_tree(_cross_tree(ta, tb, trng), trng))
                linear_pop, tree_pop = next_l, next_t
            linear_final = max(_score(_linear_metrics(p, i), landscape)
                               for i, p in enumerate(linear_pop))
            tree_final = max(_score(_tree_metrics(t), landscape)
                             for t in tree_pop)
            rows.append({
                "seed": seed, "linear_best": max(linear_history),
                "tree_best": max(tree_history), "linear_final_best": linear_final,
                "tree_final_best": tree_final,
                "tree_minus_linear": max(tree_history) - max(linear_history),
            })
        differences = [r["tree_minus_linear"] for r in rows]
        summaries[landscape] = {
            "replicates": len(rows),
            "linear_best_mean": statistics.mean(r["linear_best"] for r in rows),
            "tree_best_mean": statistics.mean(r["tree_best"] for r in rows),
            "paired_tree_minus_linear_mean": statistics.mean(differences),
            "raw_replicates": rows,
        }
        all_rows.extend({"landscape": landscape, **row} for row in rows)
    return {
        "design": "30+ paired seeds; identical initial phenotypes; common action/energy-guard/repeat grammar; same evaluator budgets and evolution settings",
        "population_size": population_size, "generations": generations,
        "fitness_landscapes": list(LANDSCAPES), "results": summaries,
        "raw_replicates": all_rows,
        "caveat": "This isolates representation/operator behavior only within the shared grammar. Arbitrary nested-tree expressivity is evaluated separately by the advanced operator stress tests; these scores are not directly comparable across landscapes.",
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Matched multi-landscape GP validation")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--output", default="artifacts/matched-gp-landscapes.json")
    args = parser.parse_args()
    if args.seeds < 30:
        parser.error("--seeds must be at least 30")
    result = run_matched_gp_landscapes(tuple(range(7001, 7001 + args.seeds)))
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"output": args.output, "landscapes": result["fitness_landscapes"]}, indent=2))


if __name__ == "__main__":
    main()
