# Genesis Protocol

**An experimental platform for evolving software organisms under measurable environmental pressures.**

Genesis Protocol is a research-oriented evolutionary computing platform. It models digital organisms with heritable genomes and bounded behavioral policies; subjects populations to explicit environments, resource constraints, competition and cooperation; and records reproducible evolutionary experiments.

> Research status: early-stage implementation. The initial engine is a deterministic, inspectable evolutionary simulation—not evidence of biological life, general intelligence, or open-ended evolution.

## Research goals

- Genetic programming over a deliberately constrained instruction set.
- Selection, mutation, crossover, reproduction and lineage tracking.
- Fitness landscapes with explicit, versioned objective functions.
- Resource-limited environments and measurable ecological interactions.
- Sandboxed organism evaluation with deterministic resource accounting.
- Reproducible runs, experiment manifests, metrics and exportable records.
- Baselines, ablations, parameter sweeps and independent replication.

## Initial implementation

The first milestone provides:
- Immutable genome and organism records.
- A small bounded policy instruction set (no arbitrary Python execution).
- A deterministic environment and fitness evaluator.
- A seeded evolutionary loop with elitism, tournament selection, mutation and crossover.
- Generation metrics and a JSON-serializable experiment result.
- Unit tests for determinism, bounds and evolutionary operators.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
genesis-run --seed 7 --generations 50 --population 100
```

## Safety model

Organism policies are interpreted by Genesis Protocol's own bounded evaluator. Organisms do not execute arbitrary source code, access the filesystem, open network connections, spawn processes, or import host modules. Evaluation is limited by instruction count and explicit environment state. This is a safer design boundary than attempting to run untrusted Python in-process; it is not a claim of a formally verified operating-system sandbox.

## Reproducibility

A run records its seed, configuration, engine version, environment identifier, and per-generation metrics. Identical inputs are expected to produce identical results within the same supported engine version. Cross-version reproducibility must be tested and is not assumed.

## Roadmap

1. Core evolutionary engine and deterministic experiments.
2. Multi-objective fitness, dynamic environments and ecological interactions.
3. Genetic programming and structural genome evolution.
4. Experiment registry, lineage analysis and visualization.
5. Benchmark suite, statistical analysis and independent reproduction.
6. Optional distributed execution and external integrations after the core is validated.

## Scientific standards

Results must be compared with explicit baselines and reported with replicate counts, uncertainty and configuration provenance. Fitness improvements on a designed task are evidence about that task and implementation—not proof of general intelligence or open-ended evolution.

## License

License selection is intentionally pending. Do not assume the project is licensed for redistribution until a license file is added.
