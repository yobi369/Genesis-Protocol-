"""Genesis Protocol evolutionary computing laboratory."""

from .ecology import (
    EcologyConfig,
    EcosystemEngine,
    EcosystemResult,
    EnvironmentalPhase,
    SpeciesDefinition,
)
from .engine import EvolutionConfig, EvolutionEngine, EvolutionResult
from .genome import Genome, Instruction, Op
from .models import Organism

__all__ = [
    "EcologyConfig",
    "EcosystemEngine",
    "EcosystemResult",
    "EnvironmentalPhase",
    "SpeciesDefinition",
    "EvolutionConfig",
    "EvolutionEngine",
    "EvolutionResult",
    "Genome",
    "Instruction",
    "Op",
    "Organism",
]

__version__ = "0.2.0"
