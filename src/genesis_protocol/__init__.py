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
from .program import Action, IfEnergyBelow, IfResourcesBelow, Program, RepeatAction

__all__ = [
    "Action",
    "EcologyConfig",
    "EcosystemEngine",
    "EcosystemResult",
    "EnvironmentalPhase",
    "EvolutionConfig",
    "EvolutionEngine",
    "EvolutionResult",
    "Genome",
    "IfEnergyBelow",
    "IfResourcesBelow",
    "Instruction",
    "Op",
    "Organism",
    "Program",
    "RepeatAction",
    "SpeciesDefinition",
]

__version__ = "0.2.0"
