# Genesis Protocol

**An experimental platform for evolving software organisms under measurable environmental pressures.**

Genesis Protocol is a research-oriented evolutionary computing platform. It models digital organisms with heritable genomes and bounded behavioral policies; subjects populations to explicit environments, resource constraints, competition and cooperation; and records reproducible evolutionary experiments.

> Research status: early-stage implementation. The engine is a deterministic, inspectable evolutionary simulation—not evidence of biological life, general intelligence, or open-ended evolution.

## Capabilities

- Multi-species populations, shared-resource competition, reciprocal cooperation and environmental shifts.
- Pareto-based selection, genome-distance speciation and organism-level lineage records.
- Linear and nested tree genetic programming with bounded interpreters.
- Independent resource-economy reference policies and spatial predator–prey/resource simulations.
- Persistent local social ties, lineage validation and edit-distance-based genome clustering.
- Pareto-front reference calculations, 3D hypervolume trajectories and distribution-free paired statistics.
- Reproducible synthetic benchmark scenarios and a local browser research workbench.
- Seeded experiment records and an offline HTML run viewer.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
pytest
```

Run the original evolutionary baseline:

```bash
genesis-run --seed 7 --generations 50 --population 100
```

Run the multi-species ecosystem:

```bash
genesis-ecology --seed 7 --generations 40 --population-per-species 30 --output run.json
```

Open [web/lab.html](web/lab.html) in a browser to import JSON experiment records, compare run summaries, inspect trajectories and lineage, annotate the session, and export a manifest. The viewer is local-first and has no server or collaboration backend.

## Research validation campaign

Install the independent DEAP reference implementation and run the reproducible campaign (minimum 30 paired seeds):

```bash
python -m pip install -e ".[dev,research]"
genesis-research-validation --seeds 30 --output artifacts/research-validation.json
```

The campaign compares three ecological resource regimes, spatial dynamics against Lotka–Volterra and Rosenzweig–MacArthur ODE references, genome clustering across distributions and thresholds, NSGA-II selection against DEAP, and matched tree/linear GP. It also calibrates the reference ODEs against a short historical Hudson Bay lynx–hare pelt-index series with a chronological holdout. See [Research Validation Protocol](docs/RESEARCH_VALIDATION_PROTOCOL.md) and [empirical data provenance](data/empirical/README.md). The GitHub Actions research workflow runs the 30-seed campaign and uploads its raw JSON result as an artifact.

Run the browser-scale test locally after installing Chromium with Playwright:

```bash
python -m playwright install chromium
GENESIS_BROWSER_TESTS=1 pytest -q tests/browser/test_lab_workbench.py
```


## Research milestone 2

See [Research Milestone 2](docs/RESEARCH_MILESTONE_2.md) for:
1. Independent reference ecology comparisons.
2. Predator–prey and renewable-resource dynamics.
3. Spatial ecosystems and persistent social ties.
4. Edit-distance speciation and lineage validation.
5. Independent Pareto-front and hypervolume diagnostics.
6. Nested tree genetic programming.
7. Synthetic benchmarks and exploratory distribution-free statistics.
8. Browser-side experiment management and visualization.

## Safety model

Organism policies are interpreted by bounded application-level evaluators. They do not execute arbitrary source code, access the filesystem, open network connections, spawn processes, or import host modules. These execution boundaries are not formally verified operating-system sandboxes.

## Scientific standards and limitations

The reference and spatial models are synthetic, deliberately simplified research instruments. The benchmark CSV is a scenario registry, not an empirical dataset. Speciation clustering is representative-based and order-dependent. Hypervolume requires fixed objective scales and a fixed reference point. Statistical helpers are exploratory; confirmatory work requires a preregistered analysis, adequate power, holdout seeds, external datasets, and independent domain review.

A successful test run validates software behavior, not ecological realism or biological validity. The project makes no claim of general intelligence or open-ended evolution.

## License

License selection is pending. Do not assume the project is licensed for redistribution until a license file is added.
