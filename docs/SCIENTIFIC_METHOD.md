# Scientific Method and Validation Plan

## Claims policy

A successful run demonstrates only that this implementation optimizes its defined objective under its defined evaluator. It does not establish general intelligence, open-ended evolution, biological equivalence or real-world adaptation.

## Minimum experiment record

Every run should retain:
- Engine and schema versions.
- Random seed.
- Full evolutionary configuration.
- Environment identifier and parameters.
- Fitness definition/version.
- Per-generation population metrics.
- Best genome and lineage.
- Runtime/platform metadata when collected.

## Validation programme

1. **Determinism:** repeat identical runs and compare complete serialized outputs.
2. **Operator tests:** verify mutation/crossover preserve genome invariants and obey bounds.
3. **Evaluator tests:** verify each instruction's effect, resource limits and instruction budgets.
4. **Baselines:** compare against random search, no-mutation selection, mutation-only and crossover-only controls.
5. **Replicates:** run independent seeds; report distributions, confidence intervals and effect sizes.
6. **Ablations:** remove one evolutionary mechanism at a time.
7. **Sensitivity:** sweep mutation, crossover, selection pressure and population size.
8. **Holdout tasks:** evaluate evolved policies on environments not used during selection.
9. **Independent reproduction:** publish configurations, seeds, engine commit and raw metrics.

## Statistical caution

Do not report only the best run. Predefine replicate counts and outcome measures. Avoid tuning on the holdout. Distinguish exploratory analyses from confirmatory tests. Report failed runs and parameter choices.
