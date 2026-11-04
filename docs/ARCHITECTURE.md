# Architecture

## Design boundary

Genesis Protocol separates heritable program representation, policy interpretation, environmental state, fitness measurement, population evolution and experiment provenance. The first implementation intentionally uses a constrained instruction set rather than executing organism-authored Python.

## Execution flow

1. A seeded random generator creates an initial population of immutable genomes.
2. The evaluator interprets each genome against a versioned environment and explicit energy/instruction budgets.
3. The fitness function produces a numeric score and decomposed outcome metrics.
4. Selection chooses parents; crossover and mutation produce offspring.
5. Elites survive unchanged; offspring receive stable IDs and parent lineage.
6. Each generation records best, mean, median and genotype-diversity metrics.
7. The result serializer records configuration, seed, environment, engine version, best genome and metrics.

## Current module boundaries

- `genome.py`: immutable instructions, genomes, mutation and one-point crossover.
- `models.py`: organism, environment and evaluation records.
- `evaluator.py`: deterministic bounded interpreter.
- `engine.py`: population lifecycle, selection and run provenance.
- `cli.py`: command-line experiment runner.

## Safety

The interpreter has no host-language eval/exec, imports, filesystem, network or process APIs. The instruction budget bounds policy steps. Environment resource supply bounds gather actions. This is an application-level execution boundary, not a formally verified sandbox. Future user-defined code execution requires a separate process/container isolation design and a threat model.

## Known limitations

- Fitness is currently a single scalar and task-specific.
- The environment is static during a run.
- Cooperation is rewarded directly; no partner-dependent payoff exists yet.
- Organisms are linear instruction sequences, not general evolving software architectures.
- Diversity is exact-genotype count, not a phylogenetic or behavioral distance.
- The current interpreter is sequential and deterministic; there is no concurrency or distributed execution.
