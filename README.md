# Genesis Protocol

**An experimental platform for evolving software organisms under measurable environmental pressures.**

Genesis Protocol is a research-oriented evolutionary computing platform. It models digital organisms with heritable genomes and bounded behavioral policies; subjects populations to explicit environments, resource constraints, competition and cooperation; and records reproducible evolutionary experiments.

> Research status: early-stage implementation. The engine is a deterministic, inspectable evolutionary simulation—not evidence of biological life, general intelligence, or open-ended evolution.

## Current capabilities

- Multi-species populations with organism IDs and parent lineage.
- Shared-resource competition and species-level extinction.
- Partner-dependent reciprocal cooperation.
- Scheduled environmental shifts and selection pressures.
- Three-objective Pareto ranking with crowding distance.
- Genome-distance speciation events.
- Linear instruction genomes with conditional branches and bounded repeats.
- Typed structured genetic-programming nodes and seeded mutation/crossover.
- Seeded experiment records and paired configuration comparisons.
- Offline HTML laboratory viewer.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Run the original single-population baseline:

```bash
genesis-run --seed 7 --generations 50 --population 100
```

Run the multi-species ecosystem:

```bash
genesis-ecology --seed 7 --generations 40 --population-per-species 30 --output run.json
```

Generate the offline research viewer using `genesis_protocol.lab.render_lab`; see [Experiment and Lab Guide](docs/EXPERIMENTS_AND_LAB.md).

## Safety model

Organism policies are interpreted by Genesis Protocol's own bounded evaluator. Organisms do not execute arbitrary source code, access the filesystem, open network connections, spawn processes, or import host modules. Evaluation is limited by instruction count and explicit environment state. This is an application-level execution boundary, not a formally verified operating-system sandbox.

## Scientific standards

A successful run demonstrates only that this implementation optimizes its defined objectives under its defined evaluator. Results require independent seeds, baselines, ablations, uncertainty reporting and holdout experiments. The simple speciation heuristic and ecological interaction model are research abstractions, not validated biological models.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Ecological Model](docs/ECOLOGICAL_MODEL.md)
- [Structured Genetic Programming](docs/GENETIC_PROGRAMMING.md)
- [Experiment Comparison and Laboratory](docs/EXPERIMENTS_AND_LAB.md)
- [Scientific Method](docs/SCIENTIFIC_METHOD.md)

## License

License selection is pending. Do not assume the project is licensed for redistribution until a license file is added.
