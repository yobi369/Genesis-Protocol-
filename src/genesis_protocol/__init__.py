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
from .research import (
    SpatialConfig,
    SpatialEcosystem,
    cluster_genomes,
    compare_reference_policies,
)
from .tree_gp import EnergyGuard, Primitive, RepeatNode, SequenceNode, evaluate_tree

__all__ = [
    "Action", "EcologyConfig", "EcosystemEngine", "EcosystemResult", "EnergyGuard",
    "EnvironmentalPhase", "EvolutionConfig", "EvolutionEngine", "EvolutionResult",
    "Genome", "IfEnergyBelow", "IfResourcesBelow", "Instruction", "Op", "Organism",
    "Primitive", "Program", "RepeatAction", "RepeatNode", "SequenceNode",
    "SpatialConfig", "SpatialEcosystem", "SpeciesDefinition", "cluster_genomes",
    "compare_reference_policies", "evaluate_tree",
]

__version__ = "0.3.0"
