# Advanced ecological and genetic-programming validation protocol

This milestone is additive to the original 30-seed campaign. The previous
Hudson Bay analysis remains an unchanged baseline. Run:

```bash
python -m pip install -e ".[dev,research]"
genesis-advanced-research --seeds 30 --output artifacts/advanced-research-validation.json
genesis-gp-landscapes --seeds 30 --output artifacts/matched-gp-landscapes.json
```

## Predator reproduction experiment

The new spatial extension adds an energy threshold, reproduction cost,
offspring starting energy, stochastic birth probability and a hard predator
population cap. A no-reproduction run uses the same seeds and spatial
configuration as the original model. Candidate parameters are selected only
on the first 70% of the historical Hudson Bay index. Prey and predator
holdout log-RMSE are reported separately. A candidate is not considered an
improvement if it lowers predator error by materially worsening prey error.

The reproduction mechanism is a deliberately simple hypothesis. It does not
yet include age, sex, mating, density dependence, juvenile survival,
territoriality, dispersal or alternate prey. A better curve fit is not proof
that these omitted processes are unimportant.

## Independent empirical datasets

The registry is documented in `data/empirical/README.md`. Candidate sources
include Tetlin NWR (hare pellet quadrats, 1990–2024), Kluane monitoring and
experimental records, Wood Buffalo (annual hare pellet transects, 2006–2017),
and Yukon boreal community monitoring. The sources are not interchangeable:
some measure hares only; others use live trapping/mark-recapture or predator
snow-track indices. Different sites, observation units and survey protocols
must remain separate. Dataset ingestion requires a source snapshot, checksum,
data dictionary, survey-effort metadata, explicit units, site identifiers and
documented transformations. No unverified values are transcribed into the
repository.

## Genetic programming

The matched benchmark repeats tree/linear comparison over foraging, energy
conservation, cooperation and balanced fitness landscapes. Initial phenotypes,
population size, generations, action semantics, instruction budget and seed
sets are paired. It remains restricted to the common action/energy-guard/repeat
grammar so semantic differences do not confound the comparison.

Separately, nested sequence/guard/repeat trees are exercised with point,
subtree and hoist mutation plus symmetric subtree crossover. Depth and size
budgets reject invalid offspring. The operator stress test measures validity
and acceptance, not evolutionary superiority. The matched benchmark and
nested-grammar stress test therefore answer different questions.

## Interpretation and acceptance

- Keep all raw seed-level replicates in the JSON artifacts.
- Report prey and predator errors separately, not just a combined metric.
- Preserve the chronological holdout; never tune parameters on it.
- Compare independent datasets only after verifying sampling methods and units.
- Report GP results separately by landscape; do not average incomparable
  objective scales into a single headline.
- Report tree size/depth distributions and operator rejection rates before
  making claims about bloat control.
- CI success validates execution and software invariants, not ecological truth.
- Thirty seeds remain a reproducibility floor, not a power analysis.
