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
from .program import Program, Action, IfEnergyBelow, IfResourcesBelow, RepeatAction

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
    "Program",
    "Action",
    "IfEnergyBelow",
    "IfResourcesBelow",
    "RepeatAction",
]

__version__ = "0.2.0"
