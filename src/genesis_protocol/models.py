"""Core organism and environment data structures."""

from __future__ import annotations

from dataclasses import dataclass

from .genome import Genome


@dataclass(frozen=True, slots=True)
class Organism:
    organism_id: int
    genome: Genome
    parent_ids: tuple[int, ...] = ()
    generation_born: int = 0

    def __post_init__(self) -> None:
        if self.organism_id < 0 or self.generation_born < 0:
            raise ValueError("organism identifiers and generation must be non-negative")


@dataclass(frozen=True, slots=True)
class Environment:
    identifier: str = "resource-foraging-v1"
    resource_supply: int = 100
    movement_cost: int = 1
    gather_reward: int = 3
    cooperation_bonus: int = 2

    def __post_init__(self) -> None:
        if self.resource_supply < 0 or min(self.movement_cost, self.gather_reward, self.cooperation_bonus) < 0:
            raise ValueError("environment quantities must be non-negative")


@dataclass(frozen=True, slots=True)
class Evaluation:
    organism_id: int
    fitness: float
    energy_remaining: int
    resources_gathered: int
    cooperation_actions: int
    instructions_executed: int
