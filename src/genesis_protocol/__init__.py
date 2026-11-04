"""Genesis Protocol evolutionary computing laboratory."""

from .engine import EvolutionConfig, EvolutionEngine, EvolutionResult
from .genome import Genome, Instruction, Op
from .models import Organism

__all__ = [
    "EvolutionConfig",
    "EvolutionEngine",
    "EvolutionResult",
    "Genome",
    "Instruction",
    "Op",
    "Organism",
]

__version__ = "0.1.0"
