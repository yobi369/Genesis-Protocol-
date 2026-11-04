"""Seeded evolutionary loop and reproducible run records."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import Any

from .evaluator import evaluate
from .genome import Genome
from .models import Environment, Evaluation, Organism


@dataclass(frozen=True, slots=True)
class EvolutionConfig:
    population_size: int = 100
    generations: int = 50
    mutation_rate: float = 0.08
    crossover_rate: float = 0.75
    elite_count: int = 2
    tournament_size: int = 3
    initial_energy: int = 20
    instruction_budget: int = 128

    def __post_init__(self) -> None:
        if self.population_size < 2 or self.generations < 1:
            raise ValueError("population_size must be >= 2 and generations >= 1")
        if not 0 <= self.mutation_rate <= 1 or not 0 <= self.crossover_rate <= 1:
            raise ValueError("rates must be in [0, 1]")
        if not 0 <= self.elite_count < self.population_size:
            raise ValueError("elite_count must be in [0, population_size)")
        if not 1 <= self.tournament_size <= self.population_size:
            raise ValueError("invalid tournament_size")


@dataclass(frozen=True, slots=True)
class GenerationMetrics:
    generation: int
    best_fitness: float
    mean_fitness: float
    median_fitness: float
    diversity: int


@dataclass(frozen=True, slots=True)
class EvolutionResult:
    seed: int
    config: EvolutionConfig
    environment: Environment
    metrics: tuple[GenerationMetrics, ...]
    best_organism: Organism
    best_evaluation: Evaluation
    engine_version: str = "0.1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed": self.seed,
            "engine_version": self.engine_version,
            "config": asdict(self.config),
            "environment": asdict(self.environment),
            "metrics": [asdict(item) for item in self.metrics],
            "best_organism": {
                "organism_id": self.best_organism.organism_id,
                "generation_born": self.best_organism.generation_born,
                "parent_ids": list(self.best_organism.parent_ids),
                "genome": self.best_organism.genome.to_dict(),
            },
            "best_evaluation": asdict(self.best_evaluation),
        }


class EvolutionEngine:
    def __init__(
        self,
        config: EvolutionConfig | None = None,
        environment: Environment | None = None,
        *,
        seed: int = 1,
    ) -> None:
        self.config = config or EvolutionConfig()
        self.environment = environment or Environment()
        self.seed = seed
        self.rng = random.Random(seed)
        self._next_id = 0

    def _new_organism(self, genome: Genome, generation: int, parents: tuple[int, ...] = ()) -> Organism:
        organism = Organism(self._next_id, genome, parents, generation)
        self._next_id += 1
        return organism

    def _tournament(self, scored: list[tuple[Organism, Evaluation]]) -> Organism:
        contestants = self.rng.sample(scored, self.config.tournament_size)
        return max(contestants, key=lambda item: item[1].fitness)[0]

    def run(self) -> EvolutionResult:
        population = [
            self._new_organism(Genome.random(self.rng), 0)
            for _ in range(self.config.population_size)
        ]
        history: list[GenerationMetrics] = []
        best_pair: tuple[Organism, Evaluation] | None = None

        for generation in range(self.config.generations):
            scored = [
                (organism, evaluate(
                    organism,
                    self.environment,
                    initial_energy=self.config.initial_energy,
                    instruction_budget=self.config.instruction_budget,
                ))
                for organism in population
            ]
            scored.sort(key=lambda pair: pair[1].fitness, reverse=True)
            current_best = scored[0]
            if best_pair is None or current_best[1].fitness > best_pair[1].fitness:
                best_pair = current_best

            values = sorted(item.fitness for _, item in scored)
            middle = len(values) // 2
            median = values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2
            history.append(GenerationMetrics(
                generation=generation,
                best_fitness=current_best[1].fitness,
                mean_fitness=sum(values) / len(values),
                median_fitness=median,
                diversity=len({org.genome for org, _ in scored}),
            ))

            if generation == self.config.generations - 1:
                break

            next_population = [pair[0] for pair in scored[: self.config.elite_count]]
            while len(next_population) < self.config.population_size:
                parent_a = self._tournament(scored)
                parent_b = self._tournament(scored)
                child_genome = parent_a.genome
                parents = (parent_a.organism_id, parent_b.organism_id)
                if self.rng.random() < self.config.crossover_rate:
                    child_genome = parent_a.genome.crossover(parent_b.genome, self.rng)
                child_genome = child_genome.mutate(self.rng, self.config.mutation_rate)
                next_population.append(self._new_organism(child_genome, generation + 1, parents))
            population = next_population

        assert best_pair is not None
        return EvolutionResult(
            seed=self.seed,
            config=self.config,
            environment=self.environment,
            metrics=tuple(history),
            best_organism=best_pair[0],
            best_evaluation=best_pair[1],
        )
