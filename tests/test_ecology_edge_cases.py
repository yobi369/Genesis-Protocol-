from genesis_protocol.ecology import (
    EcologyConfig,
    EcosystemEngine,
    EnvironmentalPhase,
    SpeciesDefinition,
)
from genesis_protocol.genome import Genome, Instruction, Op


def test_zero_energy_movement_organisms_do_not_survive() -> None:
    species = (SpeciesDefinition(0, "fragile", 4),)
    engine = EcosystemEngine(
        species,
        (EnvironmentalPhase(0, resource_supply=0, movement_cost=1),),
        EcologyConfig(generations=3, initial_energy=0),
        seed=4,
    )
    # Replace random founders with deterministic high-cost movement genomes.
    founders = [engine._new(0, Genome((Instruction(Op.MOVE, 5),)), 0) for _ in range(4)]
    outcomes, _ = engine._evaluate_population(founders, engine.schedule[0])
    assert all(not item.survived for item in outcomes)
    assert len({item.species_id for item in outcomes}) == 1


def test_genome_instruction_rejects_untyped_opcode() -> None:
    import pytest

    with pytest.raises(ValueError):
        Instruction("gather", 1)  # type: ignore[arg-type]
