"""Independent reference models and research diagnostics for Genesis Protocol.

These deliberately small models are comparison instruments, not claims of
biological realism. They do not call EcosystemEngine or its evaluator.
"""
from __future__ import annotations

import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from itertools import pairwise

from .ecology import LineageRecord
from .genome import Genome


@dataclass(frozen=True, slots=True)
class ReferenceResult:
    seed: int
    policy: str
    steps: int
    population: int
    harvested: int
    energy_total: int
    resource_total: int


def run_reference_model(*, seed: int, policy: str, steps: int = 30,
                        population: int = 12, initial_resources: int = 80) -> ReferenceResult:
    """Run a separate resource-economy baseline with fixed, auditable policies."""
    if policy not in {"harvest", "conserve", "alternate"}:
        raise ValueError("unknown reference policy")
    if steps < 1 or population < 1 or initial_resources < 0:
        raise ValueError("steps and population must be positive; resources non-negative")
    rng = random.Random(seed)
    energy = [10] * population
    stock = initial_resources
    harvested = 0
    for step in range(steps):
        order = list(range(population))
        rng.shuffle(order)
        for index in order:
            if policy == "harvest" or (policy == "alternate" and step % 2 == 0):
                amount = min(2, stock)
                stock -= amount
                energy[index] += amount * 2
                harvested += amount
                energy[index] -= 1
            else:
                energy[index] += 1
            energy[index] = min(30, energy[index])
        stock = min(initial_resources, stock + max(1, initial_resources // 20))
    return ReferenceResult(seed, policy, steps, sum(e > 0 for e in energy),
                           harvested, sum(energy), stock)


def compare_reference_policies(*, seeds: Sequence[int] = (3, 7, 11, 19, 23),
                                steps: int = 30, population: int = 12) -> dict[str, object]:
    """Paired-seed independent baseline comparison; raw rows are retained."""
    if len(seeds) < 2 or len(set(seeds)) != len(seeds):
        raise ValueError("at least two unique seeds are required")
    rows = [run_reference_model(seed=s, policy=p, steps=steps, population=population)
            for s in seeds for p in ("harvest", "conserve", "alternate")]
    summaries: dict[str, dict[str, float]] = {}
    for policy in ("harvest", "conserve", "alternate"):
        group = [r for r in rows if r.policy == policy]
        summaries[policy] = {
            "mean_population": sum(r.population for r in group) / len(group),
            "mean_harvested": sum(r.harvested for r in group) / len(group),
            "mean_energy": sum(r.energy_total for r in group) / len(group),
            "mean_resources_remaining": sum(r.resource_total for r in group) / len(group),
        }
    return {"design": "paired seeds; independent resource-economy reference model",
            "seeds": list(seeds), "summaries": summaries,
            "replicates": [r.__dict__ if hasattr(r, "__dict__") else {
                "seed": r.seed, "policy": r.policy, "steps": r.steps,
                "population": r.population, "harvested": r.harvested,
                "energy_total": r.energy_total, "resource_total": r.resource_total}
                for r in rows]}


@dataclass(frozen=True, slots=True)
class SpatialConfig:
    width: int = 12
    height: int = 12
    prey: int = 24
    predators: int = 4
    resource_regrowth: int = 2
    steps: int = 50
    initial_energy: int = 12

    def __post_init__(self) -> None:
        if min(self.width, self.height, self.prey, self.steps, self.initial_energy) < 1:
            raise ValueError("grid dimensions, prey, steps and energy must be positive")
        if self.predators < 0 or self.resource_regrowth < 0:
            raise ValueError("predators and regrowth must be non-negative")


@dataclass(frozen=True, slots=True)
class SpatialStep:
    step: int
    prey: int
    predators: int
    resources: int
    predation_events: int
    social_edges: int


@dataclass(frozen=True, slots=True)
class SpatialResult:
    seed: int
    config: SpatialConfig
    trajectory: tuple[SpatialStep, ...]
    social_ties: tuple[tuple[int, int, int], ...]


class SpatialEcosystem:
    """Toroidal grid with renewable cells and persistent weighted social ties."""

    def __init__(self, config: SpatialConfig | None = None, *, seed: int = 1) -> None:
        self.config = config or SpatialConfig()
        self.seed = seed
        self.rng = random.Random(seed)
        self.resources = [[2 for _ in range(self.config.width)] for _ in range(self.config.height)]
        self.prey = {i: [self.rng.randrange(self.config.width), self.rng.randrange(self.config.height),
                         self.config.initial_energy] for i in range(self.config.prey)}
        self.predators = {i: [self.rng.randrange(self.config.width), self.rng.randrange(self.config.height),
                              self.config.initial_energy * 2] for i in range(self.config.predators)}
        self.ties: dict[tuple[int, int], int] = {}

    def _move(self, agent: list[int]) -> None:
        dx, dy = self.rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)))
        agent[0] = (agent[0] + dx) % self.config.width
        agent[1] = (agent[1] + dy) % self.config.height

    def run(self) -> SpatialResult:
        trajectory: list[SpatialStep] = []
        next_prey_id = len(self.prey)
        for step in range(self.config.steps):
            for row in self.resources:
                for x in range(len(row)):
                    row[x] = min(8, row[x] + self.config.resource_regrowth)
            for agent_id in list(self.prey):
                agent = self.prey[agent_id]
                self._move(agent)
                x, y = agent[0], agent[1]
                food = min(2, self.resources[y][x])
                self.resources[y][x] -= food
                agent[2] += food * 2 - 1
                if agent[2] <= 0:
                    del self.prey[agent_id]
            predation = 0
            for predator_id in list(self.predators):
                predator = self.predators[predator_id]
                self._move(predator)
                prey_here = [i for i, p in self.prey.items()
                             if p[0] == predator[0] and p[1] == predator[1]]
                if prey_here:
                    victim = min(prey_here)
                    del self.prey[victim]
                    predator[2] += 5
                    predation += 1
                predator[2] -= 1
                if predator[2] <= 0:
                    del self.predators[predator_id]
            # Local prey form persistent, strengthening ties when co-located.
            cell_members: dict[tuple[int, int], list[int]] = {}
            for prey_id, agent in self.prey.items():
                cell_members.setdefault((agent[0], agent[1]), []).append(prey_id)
            for ids in cell_members.values():
                ids.sort()
                for position, left in enumerate(ids):
                    for right in ids[position + 1:]:
                        key = (left, right)
                        self.ties[key] = min(10, self.ties.get(key, 0) + 1)
            # Bounded reproduction: successful prey can bud once per step.
            parents = [i for i, p in self.prey.items() if p[2] >= 18]
            for parent_id in parents[:max(0, self.config.prey // 4)]:
                if len(self.prey) >= self.config.prey * 3:
                    break
                parent = self.prey[parent_id]
                parent[2] -= 6
                self.prey[next_prey_id] = [parent[0], parent[1], self.config.initial_energy]
                next_prey_id += 1
            trajectory.append(SpatialStep(
                step, len(self.prey), len(self.predators),
                sum(sum(row) for row in self.resources), predation, len(self.ties)))
        ties = tuple((a, b, weight) for (a, b), weight in sorted(self.ties.items()))
        return SpatialResult(self.seed, self.config, tuple(trajectory), ties)


def levenshtein_distance(left: Sequence[object], right: Sequence[object]) -> int:
    """Exact edit distance; unlike aligned mismatch heuristics it is metric-bounded."""
    previous = list(range(len(right) + 1))
    for i, item in enumerate(left, 1):
        current = [i]
        for j, other in enumerate(right, 1):
            current.append(min(current[-1] + 1, previous[j] + 1,
                               previous[j - 1] + (item != other)))
        previous = current
    return previous[-1]


def normalized_genome_distance(left: Genome, right: Genome) -> float:
    width = max(len(left.instructions), len(right.instructions), 1)
    return levenshtein_distance(left.instructions, right.instructions) / width


@dataclass(frozen=True, slots=True)
class SpeciesCluster:
    species_id: int
    representative: int
    members: tuple[int, ...]


def cluster_genomes(genomes: Sequence[Genome], threshold: float) -> tuple[SpeciesCluster, ...]:
    """Deterministic representative-based clustering; threshold sensitivity is explicit."""
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in (0, 1]")
    clusters: list[list[int]] = []
    representatives: list[int] = []
    for index, genome in enumerate(genomes):
        match = next((k for k, rep in enumerate(representatives)
                      if normalized_genome_distance(genomes[rep], genome) <= threshold), None)
        if match is None:
            representatives.append(index)
            clusters.append([index])
        else:
            clusters[match].append(index)
    return tuple(SpeciesCluster(i, representatives[i], tuple(members))
                 for i, members in enumerate(clusters))


def validate_lineage(records: Iterable[LineageRecord]) -> dict[str, int | bool]:
    """Check parent existence, birth ordering and acyclicity for LineageRecord-like rows."""
    rows = list(records)
    by_id = {row.organism_id: row for row in rows}
    missing = 0
    temporal = 0
    for row in rows:
        for parent in row.parent_ids:
            if parent not in by_id:
                missing += 1
            elif by_id[parent].generation_born >= row.generation_born:
                temporal += 1
    return {"records": len(rows), "missing_parents": missing,
            "temporal_violations": temporal,
            "valid": missing == 0 and temporal == 0 and len(by_id) == len(rows)}


def pareto_front_indices(points: Sequence[Sequence[float]]) -> tuple[int, ...]:
    """Independent nondominated-sort reference for maximization objectives."""
    result = []
    for i, point in enumerate(points):
        if not any(j != i and all(a >= b for a, b in zip(other, point))
                   and any(a > b for a, b in zip(other, point))
                   for j, other in enumerate(points)):
            result.append(i)
    return tuple(result)


def hypervolume_3d(points: Sequence[Sequence[float]],
                   reference: tuple[float, float, float] = (0.0, 0.0, 0.0)) -> float:
    """Exact union volume for a small 3-objective maximizing Pareto set."""
    front = [p for i, p in enumerate(points)
             if all(len(p) == 3 and p[k] >= reference[k] for k in range(3))
             and i in pareto_front_indices(points)]
    xs = sorted({reference[0], *(p[0] for p in front)})
    volume = 0.0
    for x0, x1 in pairwise(xs):
        active = [(p[1], p[2]) for p in front if p[0] >= x1]
        ys = sorted({reference[1], *(p[0] for p in active)})
        area = 0.0
        for y0, y1 in pairwise(ys):
            zmax = max((z for y, z in active if y >= y1), default=reference[2])
            area += (y1 - y0) * max(0.0, zmax - reference[2])
        volume += (x1 - x0) * area
    return volume


def pareto_convergence(history: Sequence[Sequence[Sequence[float]]],
                       reference: tuple[float, float, float] = (0.0, 0.0, 0.0)
                       ) -> tuple[dict[str, float | int], ...]:
    rows = []
    for generation, population in enumerate(history):
        front = pareto_front_indices(population)
        rows.append({"generation": generation, "front_size": len(front),
                     "hypervolume_3d": hypervolume_3d(population, reference)})
    return tuple(rows)


def nsga2_ranks(points: Sequence[Sequence[float]]) -> tuple[int, ...]:
    """Canonical fast nondominated sorting ranks for a maximizing population."""
    size = len(points)
    dominates_set: list[list[int]] = [[] for _ in points]
    dominated_count = [0] * size
    ranks = [-1] * size
    front: list[int] = []
    for i, point in enumerate(points):
        for j, other in enumerate(points):
            if i == j:
                continue
            if all(a >= b for a, b in zip(point, other)) and any(
                a > b for a, b in zip(point, other)
            ):
                dominates_set[i].append(j)
            elif all(a >= b for a, b in zip(other, point)) and any(
                a > b for a, b in zip(other, point)
            ):
                dominated_count[i] += 1
        if dominated_count[i] == 0:
            ranks[i] = 0
            front.append(i)
    rank = 0
    while front:
        next_front: list[int] = []
        for i in front:
            for j in dominates_set[i]:
                dominated_count[j] -= 1
                if dominated_count[j] == 0:
                    ranks[j] = rank + 1
                    next_front.append(j)
        rank += 1
        front = next_front
    return tuple(ranks)


def nsga2_crowding(points: Sequence[Sequence[float]],
                   ranks: Sequence[int]) -> tuple[float, ...]:
    """Compute normalized crowding distance independently for each front."""
    if len(points) != len(ranks):
        raise ValueError("each point must have one rank")
    distances = [0.0] * len(points)
    for rank in sorted(set(ranks)):
        members = [i for i, value in enumerate(ranks) if value == rank]
        if len(members) <= 2:
            for index in members:
                distances[index] = float("inf")
            continue
        dimensions = len(points[members[0]])
        for objective in range(dimensions):
            ordered = sorted(members, key=lambda i: points[i][objective])
            low = points[ordered[0]][objective]
            high = points[ordered[-1]][objective]
            distances[ordered[0]] = float("inf")
            distances[ordered[-1]] = float("inf")
            if high == low:
                continue
            for position in range(1, len(ordered) - 1):
                index = ordered[position]
                if distances[index] != float("inf"):
                    before = points[ordered[position - 1]][objective]
                    after = points[ordered[position + 1]][objective]
                    distances[index] += (after - before) / (high - low)
    return tuple(distances)


def nsga2_select(points: Sequence[Sequence[float]], capacity: int) -> tuple[int, ...]:
    """Select population indices by nondomination rank then crowding distance."""
    if capacity < 0:
        raise ValueError("capacity must be non-negative")
    if capacity >= len(points):
        return tuple(range(len(points)))
    ranks = nsga2_ranks(points)
    crowding = nsga2_crowding(points, ranks)
    return tuple(sorted(range(len(points)), key=lambda i: (ranks[i], -crowding[i], i))[:capacity])
