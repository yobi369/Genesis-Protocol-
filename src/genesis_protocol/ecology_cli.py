"""CLI for ecological evolution experiments."""

from __future__ import annotations

import argparse
import json

from .ecology import EcologyConfig, EcosystemEngine, EnvironmentalPhase, SpeciesDefinition


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a multi-species Genesis Protocol ecosystem.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--generations", type=int, default=40)
    parser.add_argument("--population-per-species", type=int, default=30)
    parser.add_argument("--output", default="genesis-ecology.json")
    args = parser.parse_args()

    species = (
        SpeciesDefinition(0, "foragers", args.population_per_species),
        SpeciesDefinition(1, "scavengers", args.population_per_species),
        SpeciesDefinition(2, "cooperators", args.population_per_species),
    )
    schedule = (
        EnvironmentalPhase(0, resource_supply=120),
        EnvironmentalPhase(max(1, args.generations // 2), resource_supply=65,
                           movement_cost=2, gather_reward=2, cooperation_reward=4),
    )
    result = EcosystemEngine(
        species, schedule,
        EcologyConfig(generations=args.generations),
        seed=args.seed,
    ).run()
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2)
    print(f"Generations: {len(result.reports)}")
    print(f"Final population: {len(result.final_population)}")
    print(f"Species represented: {len({item.species_id for item in result.final_population})}")
    print(f"Experiment record: {args.output}")


if __name__ == "__main__":
    main()
