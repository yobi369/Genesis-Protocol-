# Genesis Protocol — Research Milestone 2

This milestone adds independent reference baselines, a spatial predator–prey/resource model, persistent local social ties, stronger phylogenetic diagnostics, a reference Pareto implementation, nested tree GP, distribution-free exploratory statistics, benchmark scenarios, and a browser-side experiment workbench.

## 1. Independent ecological comparisons

`run_reference_model` and `compare_reference_policies` implement a separate resource-economy model with harvest, conserve, and alternate policies. It deliberately does not reuse the evolutionary evaluator. This is a software-level independent baseline, not an external published ecological benchmark. Record the model definition, seeds, and all replicate rows.

## 2–3. Predator–prey, resources, space, and social ties

`SpatialEcosystem` uses a toroidal grid, renewable cell resources, prey energy costs, predator movement and predation, bounded prey reproduction, and persistent weighted co-location ties. The current implementation is a minimal mechanistic model. It omits age, sex, migration, disease, trophic complexity, and calibrated empirical parameters.

## 4. Speciation and phylogenetics

Exact Levenshtein edit distance is normalized by the longer genome length. Representative-based clustering is deterministic and threshold-explicit. `validate_lineage` checks parent references and temporal ordering. These are useful diagnostics, not a complete phylogenetic inference method: representative clustering is order-dependent and no molecular-clock or uncertainty model is claimed.

## 5. NSGA-II reference and convergence

The research module includes independently written nondominated sorting ranks, normalized crowding distances, capacity-limited NSGA-II reference selection, and a three-objective hypervolume trajectory. Hypervolume assumes maximization and a fixed reference point; comparisons are meaningful only when objective scales and reference point are held constant. The reference selector is tested against small hand-constructed fronts; broader benchmark comparisons and convergence studies remain required before making performance claims.

## 6. Nested tree genetic programming

`tree_gp` provides typed primitive, sequence, energy-guard, and repeat nodes; bounded tree generation, subtree mutation/crossover, and an instruction-budgeted interpreter. It does not execute Python or arbitrary generated source. The interpreter's action semantics are a distinct research model and should be compared against the linear engine before pooling results.

## 7. Benchmark and statistical analysis

`data/benchmark_scenarios.csv` provides fixed scenario definitions and seeds. Paired sign-flip randomization and percentile bootstrap helpers retain reproducibility. These procedures are exploratory; choose the analysis plan before examining outcomes, report all seeds, and avoid treating repeated parameter tuning as independent confirmation.

## 8. Browser workbench

Open `web/lab.html` locally. Import one or more experiment JSON records, inspect generation metrics and lineage, compare run summaries, add local notes, and export a manifest. Data stays in the browser; there is no server, account system, or collaboration backend. This is a browser-side research workbench, not a hosted multi-user experiment service.

## Reproducibility protocol

1. Pin engine version, configuration, scenario, and seeds.
2. Run at least 30 independent seeds for exploratory screening; use more when power analysis warrants it.
3. Compare against simple baselines and ablations using matched seeds.
4. Keep raw replicate data and report effect sizes and uncertainty, not only means.
5. Separate discovery seeds from holdout seeds.
6. Archive the exact JSON, code commit, and analysis settings.

## Scientific limitations

No results in this repository establish biological validity, ecological calibration, general intelligence, or open-ended evolution. The benchmark scenarios are synthetic. External datasets and expert domain review remain necessary before scientific claims about real ecosystems.
