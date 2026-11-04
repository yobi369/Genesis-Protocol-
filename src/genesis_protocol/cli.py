"""Command-line entry point."""

from __future__ import annotations

import argparse
import json

from .engine import EvolutionConfig, EvolutionEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a reproducible Genesis Protocol experiment.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--generations", type=int, default=50)
    parser.add_argument("--population", type=int, default=100)
    parser.add_argument("--output", default="genesis-run.json")
    args = parser.parse_args()

    result = EvolutionEngine(
        EvolutionConfig(generations=args.generations, population_size=args.population),
        seed=args.seed,
    ).run()
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2)
    print(f"Best fitness: {result.best_evaluation.fitness:.3f}")
    print(f"Experiment record: {args.output}")


if __name__ == "__main__":
    main()
