"""Multi-species ecology, reciprocal interactions and Pareto evolution.

The model is intentionally deterministic for a fixed seed and configuration.
It is a research simulation, not a claim of biological equivalence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import random
from statistics import mean
from typing import Any

from .genome import Genome, Op
from .models import Environment


@dataclass(frozen=True, slots=True)
class SpeciesDefinition:
    species_id: int
    name: str
    initial_population: int

    def __post_init__(self) -> None:
        if self.species_id < 0 or not self.name.strip() or self.initial_population < 1:
            raise ValueError("species requires a non-empty name, non-negative id and positive population")


@dataclass(frozen=True, slots=True)
class EnvironmentalPhase:
    start_generation: int
    resource_supply: int
    movement_cost: int = 1
    gather_reward: int = 3
    cooperation_reward: int = 2
    unreciprocated_cost: int = 1

    def __post_init__(self) -> None:
        if self.start_generation < 0:
            raise ValueError("phase generation must be non-negative")
        if min(self.resource_supply, self.movement_cost, self.gather_reward,
               self.cooperation_reward, self.unreciprocated_cost) < 0:
            raise ValueError("environmental quantities must be non-negative")


@dataclass(frozen=True, slots=True)
class EcologyConfig:
    generations: int = 40
    mutation_rate: float = 0.08
    crossover_rate: float = 0.75
    elite_fraction: float = 0.10
    tournament_size: int = 3
    initial_energy: int = 20
    instruction_budget: int = 128
    speciation_distance: float = 0.65

    def __post_init__(self) -> None:
        if self.generations < 1 or self.tournament_size < 1 or self.instruction_budget < 1:
            raise ValueError("generation, tournament and instruction budgets must be positive")
        if not 0 <= self.mutation_rate <= 1 or not 0 <= self.crossover_rate <= 1:
            raise ValueError("mutation and crossover rates must be in [0, 1]")
        if not 0 <= self.elite_fraction < 1:
            raise ValueError("elite_fraction must be in [0, 1)")
        if not 0 < self.speciation_distance <= 1:
            raise ValueError("speciation_distance must be in (0, 1]")


@dataclass(frozen=True, slots=True)
class EcologicalOrganism:
    organism_id: int
    species_id: int
    genome: Genome
    parent_ids: tuple[int, ...] = ()
    generation_born: int = 0


@dataclass(frozen=True, slots=True)
class FitnessVector:
    resources: float
    survival: float
    reciprocal_cooperation: float

    def values(self) -> tuple[float, float, float]:
        return (self.resources, self.survival, self.reciprocal_cooperation)


@dataclass(frozen=True, slots=True)
class OrganismOutcome:
    organism_id: int
    species_id: int
    fitness: FitnessVector
    energy_remaining: int
    resources_gathered: int
    cooperation_attempts: int
    reciprocal_cooperation: int
    survived: bool


@dataclass(frozen=True, slots=True)
class LineageRecord:
    organism_id: int
    species_id: int
    parent_ids: tuple[int, ...]
    generation_born: int


@dataclass(frozen=True, slots=True)
class GenerationReport:
    generation: int
    resource_supply: int
    resources_remaining: int
    species_population: dict[str, int]
    mean_resources: float
    mean_survival: float
    mean_reciprocal_cooperation: float
    pareto_front_size: int
    genotype_diversity: int
    speciation_events: int
    extinctions: int


@dataclass(frozen=True, slots=True)
class EcosystemResult:
    seed: int
    config: EcologyConfig
    species: tuple[SpeciesDefinition, ...]
    schedule: tuple[EnvironmentalPhase, ...]
    reports: tuple[GenerationReport, ...]
    lineage: tuple[LineageRecord, ...]
    final_population: tuple[EcologicalOrganism, ...]
    engine_version: str = "0.2.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "engine_version": self.engine_version,
            "config": asdict(self.config),
            "species": [asdict(item) for item in self.species],
            "environment_schedule": [asdict(item) for item in self.schedule],
            "reports": [asdict(item) for item in self.reports],
            "lineage": [asdict(item) for item in self.lineage],
            "final_population": [
                {
                    "organism_id": item.organism_id,
                    "species_id": item.species_id,
                    "parent_ids": list(item.parent_ids),
                    "generation_born": item.generation_born,
                    "genome": item.genome.to_dict(),
                } for item in self.final_population
            ],
        }


def genome_distance(left: Genome, right: Genome) -> float:
    """Normalized edit-like distance based on aligned instruction differences."""
    a, b = left.instructions, right.instructions
    width = max(len(a), len(b))
    if width == 0:
        return 0.0
    mismatches = abs(len(a) - len(b))
    mismatches += sum(x != y for x, y in zip(a, b))
    return mismatches / width


def dominates(left: FitnessVector, right: FitnessVector) -> bool:
    a, b = left.values(), right.values()
    return all(x >= y for x, y in zip(a, b)) and any(x > y for x, y in zip(a, b))


def pareto_ranks(scores: list[FitnessVector]) -> list[int]:
    """Return nondominated-sort ranks; rank zero is the Pareto front."""
    count = len(scores)
    dominates_set: list[list[int]] = [[] for _ in scores]
    dominated_by = [0] * count
    ranks = [-1] * count
    front: list[int] = []
    for i in range(count):
        for j in range(count):
            if i == j:
                continue
            if dominates(scores[i], scores[j]):
                dominates_set[i].append(j)
            elif dominates(scores[j], scores[i]):
                dominated_by[i] += 1
        if dominated_by[i] == 0:
            ranks[i] = 0
            front.append(i)
    rank = 0
    while front:
        next_front: list[int] = []
        for i in front:
            for j in dominates_set[i]:
                dominated_by[j] -= 1
                if dominated_by[j] == 0:
                    ranks[j] = rank + 1
                    next_front.append(j)
        rank += 1
        front = next_front
    return ranks


def crowding_distances(scores: list[FitnessVector], ranks: list[int]) -> list[float]:
    """Compute NSGA-II-style crowding distances within each Pareto front."""
    distances = [0.0] * len(scores)
    for rank in sorted(set(ranks)):
        indices = [i for i, value in enumerate(ranks) if value == rank]
        if len(indices) <= 2:
            for index in indices:
                distances[index] = float("inf")
            continue
        for objective in range(3):
            ordered = sorted(indices, key=lambda i: scores[i].values()[objective])
            low = scores[ordered[0]].values()[objective]
            high = scores[ordered[-1]].values()[objective]
            distances[ordered[0]] = float("inf")
            distances[ordered[-1]] = float("inf")
            if high == low:
                continue
            for position in range(1, len(ordered) - 1):
                index = ordered[position]
                before = scores[ordered[position - 1]].values()[objective]
                after = scores[ordered[position + 1]].values()[objective]
                if distances[index] != float("inf"):
                    distances[index] += (after - before) / (high - low)
    return distances


class EcosystemEngine:
    """Seeded multi-species evolutionary ecosystem with shared resource competition."""

    def __init__(
        self,
        species: tuple[SpeciesDefinition, ...],
        schedule: tuple[EnvironmentalPhase, ...],
        config: EcologyConfig | None = None,
        *,
        seed: int = 1,
    ) -> None:
        if not species or len({item.species_id for item in species}) != len(species):
            raise ValueError("provide species with unique ids")
        if not schedule or schedule[0].start_generation != 0:
            raise ValueError("environment schedule must start at generation zero")
        if tuple(sorted(schedule, key=lambda item: item.start_generation)) != schedule:
            raise ValueError("environment phases must be ordered")
        if len({item.start_generation for item in schedule}) != len(schedule):
            raise ValueError("environment phase start generations must be unique")
        self.species = {item.species_id: item for item in species}
        self.schedule = schedule
        self.config = config or EcologyConfig()
        self.seed = seed
        self.rng = random.Random(seed)
        self.next_id = 0
        self.speciation_count = 0

    def _new(self, species_id: int, genome: Genome, generation: int,
             parents: tuple[int, ...] = ()) -> EcologicalOrganism:
        organism = EcologicalOrganism(self.next_id, species_id, genome, parents, generation)
        self.next_id += 1
        return organism

    def _phase(self, generation: int) -> EnvironmentalPhase:
        active = self.schedule[0]
        for phase in self.schedule:
            if phase.start_generation > generation:
                break
            active = phase
        return active

    def _evaluate_population(
        self, population: list[EcologicalOrganism], phase: EnvironmentalPhase
    ) -> tuple[list[OrganismOutcome], int]:
        """Evaluate in seeded random order against one shared finite resource pool."""
        remaining = phase.resource_supply
        order = list(population)
        self.rng.shuffle(order)
        partner_map: dict[int, int] = {}
        for index in range(0, len(order) - 1, 2):
            partner_map[order[index].organism_id] = order[index + 1].organism_id
            partner_map[order[index + 1].organism_id] = order[index].organism_id
        by_id = {item.organism_id: item for item in population}
        cooperative = {
            item.organism_id: any(gene.op is Op.COOPERATE for gene in item.genome.instructions)
            for item in population
        }
        reciprocal_ids: set[int] = set()
        for organism_id, partner_id in partner_map.items():
            if cooperative[organism_id] and cooperative[partner_id]:
                reciprocal_ids.add(organism_id)

        outcomes: list[OrganismOutcome] = []
        for organism in order:
            energy = self.config.initial_energy
            gathered = 0
            attempts = 0
            executed = 0
            for instruction in organism.genome.instructions:
                if executed >= self.config.instruction_budget:
                    break
                executed += 1
                if instruction.op is Op.MOVE:
                    energy = max(0, energy - phase.movement_cost * instruction.amount)
                elif instruction.op is Op.GATHER:
                    amount = min(instruction.amount, remaining)
                    remaining -= amount
                    gathered += amount
                    energy += amount * phase.gather_reward
                elif instruction.op is Op.REST:
                    energy += instruction.amount
                elif instruction.op is Op.COOPERATE:
                    attempts += instruction.amount
            reciprocal = min(attempts, 5) if organism.organism_id in reciprocal_ids else 0
            if attempts and reciprocal == 0:
                energy = max(0, energy - phase.unreciprocated_cost * attempts)
            energy += reciprocal * phase.cooperation_reward
            survived = energy > 0
            outcomes.append(OrganismOutcome(
                organism.organism_id, organism.species_id,
                FitnessVector(float(gathered), float(energy), float(reciprocal)),
                energy, gathered, attempts, reciprocal, survived,
            ))
        return outcomes, remaining

    def _ranked(self, population: list[EcologicalOrganism], outcomes: list[OrganismOutcome]
                ) -> list[tuple[EcologicalOrganism, OrganismOutcome, int, float]]:
        lookup = {item.organism_id: item for item in population}
        ranks = pareto_ranks([item.fitness for item in outcomes])
        distances = crowding_distances([item.fitness for item in outcomes], ranks)
        ranked = [
            (lookup[outcome.organism_id], outcome, ranks[index], distances[index])
            for index, outcome in enumerate(outcomes)
        ]
        return sorted(ranked, key=lambda item: (item[2], -item[3]))

    def _speciate(self, child: Genome, parent: EcologicalOrganism, generation: int) -> int:
        if genome_distance(child, parent.genome) >= self.config.speciation_distance:
            new_id = max(self.species) + 1
            self.species[new_id] = SpeciesDefinition(new_id, f"{self.species[parent.species_id].name}-branch-{new_id}", 1)
            self.speciation_count += 1
            return new_id
        return parent.species_id

    def run(self) -> EcosystemResult:
        population: list[EcologicalOrganism] = []
        for species in self.species.values():
            for _ in range(species.initial_population):
                population.append(self._new(species.species_id, Genome.random(self.rng), 0))
        lineage = [
            LineageRecord(item.organism_id, item.species_id, item.parent_ids, item.generation_born)
            for item in population
        ]
        reports: list[GenerationReport] = []
        previous_species = set(self.species)

        for generation in range(self.config.generations):
            phase = self._phase(generation)
            outcomes, remaining = self._evaluate_population(population, phase)
            ranked = self._ranked(population, outcomes)
            species_counts: dict[str, int] = {}
            for item in population:
                label = self.species[item.species_id].name
                species_counts[label] = species_counts.get(label, 0) + 1
            reports.append(GenerationReport(
                generation, phase.resource_supply, remaining, species_counts,
                mean(item.fitness.resources for item in outcomes),
                mean(item.fitness.survival for item in outcomes),
                mean(item.fitness.reciprocal_cooperation for item in outcomes),
                sum(item[2] == 0 for item in ranked),
                len({item.genome for item in population}),
                self.speciation_count,
                len(previous_species - {item.species_id for item in population}),
            ))
            previous_species = {item.species_id for item in population}
            if generation == self.config.generations - 1:
                break

            outcome_by_id = {item.organism_id: item for item in outcomes}
            next_population: list[EcologicalOrganism] = []
            groups: dict[int, list[tuple[EcologicalOrganism, OrganismOutcome, int, float]]] = {}
            for entry in ranked:
                groups.setdefault(entry[0].species_id, []).append(entry)

            for species_id, group in groups.items():
                target_count = len(group)
                elite_count = min(target_count - 1, int(target_count * self.config.elite_fraction))
                next_population.extend(item[0] for item in group[:elite_count])
                while sum(item.species_id == species_id for item in next_population) < target_count:
                    contestants = self.rng.sample(group, min(self.config.tournament_size, len(group)))
                    parent_a = min(contestants, key=lambda item: (item[2], -item[3]))[0]
                    contestants = self.rng.sample(group, min(self.config.tournament_size, len(group)))
                    parent_b = min(contestants, key=lambda item: (item[2], -item[3]))[0]
                    genome = parent_a.genome
                    if self.rng.random() < self.config.crossover_rate:
                        genome = genome.crossover(parent_b.genome, self.rng)
                    genome = genome.mutate(self.rng, self.config.mutation_rate)
                    child_species = self._speciate(genome, parent_a, generation + 1)
                    child = self._new(child_species, genome, generation + 1,
                                      (parent_a.organism_id, parent_b.organism_id))
                    next_population.append(child)
                    lineage.append(LineageRecord(child.organism_id, child.species_id,
                                                  child.parent_ids, child.generation_born))
            # Keep population size stable if a species split changed membership counts.
            if len(next_population) > len(population):
                next_population = next_population[:len(population)]
            while len(next_population) < len(population):
                parent = self.rng.choice(ranked)[0]
                genome = parent.genome.mutate(self.rng, self.config.mutation_rate)
                child_species = self._speciate(genome, parent, generation + 1)
                child = self._new(child_species, genome, generation + 1, (parent.organism_id,))
                next_population.append(child)
                lineage.append(LineageRecord(child.organism_id, child.species_id,
                                              child.parent_ids, child.generation_born))
            population = next_population

        return EcosystemResult(
            self.seed, self.config, tuple(self.species.values()), self.schedule,
            tuple(reports), tuple(lineage), tuple(population),
        )
