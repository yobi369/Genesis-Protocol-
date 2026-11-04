# Advanced ecological and genetic-programming validation protocol

This milestone is additive to the original 30-seed campaign. The Hudson Bay
1900–1920 pelt-index analysis remains an unchanged historical baseline. Run:

```bash
python -m pip install -e ".[dev,research]"
genesis-advanced-research --seeds 30 --output artifacts/advanced-research-validation.json
genesis-gp-landscapes --seeds 30 --output artifacts/matched-gp-landscapes.json
```

For the independent Bonanza Creek hare-pellet series, download the raw CSV
from [BNZ:69](https://www.lter.uaf.edu/data/data-detail/id/69), preserve the
publisher's original file, then run:

```bash
genesis-advanced-research --seeds 30 \
  --bonanza-csv data/empirical/69_litter_wood_pellet_1985-2025.csv \
  --output artifacts/advanced-research-validation.json
```

The raw BNZ:69 CSV is not committed because the current run environment could
not retrieve it. The loader and benchmark are tested against synthetic fixture
rows; no empirical benchmark result is claimed until the source CSV is
downloaded, hashed, and run locally or in CI with that exact file.

## Predator reproduction experiment

The spatial extension adds an energy threshold, reproduction cost, offspring
starting energy, stochastic birth probability and a hard predator population
cap. A no-reproduction run uses the same seeds and spatial configuration as
the reproductive candidate. Candidate parameters are selected only on the
first 70% of the Hudson Bay historical index. Prey and predator holdout
log-RMSE are reported separately and paired by seed with bootstrap intervals.

The acceptance decision uses a declared prey non-inferiority margin of 0.05
log-RMSE units: predator error must improve on the held-out years, while the
upper bound of the paired 95% interval for prey error change must remain at or
below +0.05. This tolerance is an operational modelling choice, not a
biologically established threshold. The held-out series is not used to select the
candidate. This is an exploratory single short historical series, so even a
positive result would not establish predictive validity.

The reproduction mechanism remains a simplified hypothesis. It does not yet
include age, sex, mating, density dependence, juvenile survival,
territoriality, dispersal or alternate prey. A better curve fit is not proof
that omitted processes are unimportant.

## Independent empirical datasets

The registry is documented in `data/empirical/README.md`.

- **Bonanza Creek LTER BNZ:69 (1985–2025):** 1 m² litter trays, six trays in
  each of 24 permanent control plots, with hare pellets counted and discarded
  during litter collections. The litter year spans spring-to-spring. The
  included loader aggregates within site-year only, preserving tray counts.
  Its benchmark is prey-only and compares site-specific AR(1), training-mean
  and persistence forecasts. It never fabricates a predator series.
- **Tetlin NWR (1990–2024):** hare pellet counts across quadrats and sites.
  It is an independent prey index, not a paired predator-prey time series.
- **Wood Buffalo (2006 onward):** annual June pellet counts on permanent
  transects, with plots cleared after counting. This is also prey-only.
- **Kluane/Yukon CEMP:** a long-term, multi-site monitoring program beginning
  in 1973 at Kluane, with additional protocols and sites added over time.
  Hare abundance is represented by spring/fall live-trapping and spatial
  capture-mark-recapture estimates at Kluane, plus annual summer pellet plots
  across CEMP sites. Lynx/coyote indices are winter snow-track counts on
  established routes at Kluane (since 1987) and Mayo (since 1999), not all
  five sites. Snow-track observations depend on fresh snowfall, route effort
  and weather, and must be modelled as an observation index rather than a
  census. The article describes methods and trends, but the CEMP summary
  dataset is not openly downloadable from the project page; permission is
  required before reuse.

These datasets are not interchangeable. Do not combine sites, sampling
protocols, pellet counts, live-trap abundance estimates and snow-track indices
as though they were synchronized population counts. A future predator-prey
fit should use only paired site-year observations with documented temporal
overlap and explicit observation models. Until then, BNZ/Tetlin/Wood Buffalo
support prey-only robustness checks, while CEMP is a promising paired-data
candidate subject to access and data review.

## Genetic programming

The matched benchmark now runs 30+ paired seeds across foraging, energy
conservation, cooperation and balanced landscapes. Each linear/tree pair
starts from the same executable phenotype and shares the objective,
environment and evaluation budget. The linear side evolves a flat instruction
grammar. The tree side evolves nested sequence, energy-guard and repeat
structures using bounded point/subtree/hoist mutation and subtree crossover.

Results are summarized separately by landscape with paired bootstrap
intervals, tree depth/size, linear program length and instruction-budget
exhaustion. The representations have equal initial phenotypes but different
expressive capacity after evolution. This measures these specific
grammar/operator packages; it does not isolate a universal effect of
representation. Objective scores are not pooled across landscapes.

A separate operator stress campaign exercises the richer grammar and records
validity and acceptance under strict depth/size budgets. It is a structural
robustness test, not evidence that the operators improve evolutionary fitness.

## Interpretation and acceptance

- Keep all raw seed-level replicates in the JSON artifacts.
- Report prey and predator errors separately, not just a combined metric.
- Preserve chronological holdouts; never tune parameters on them.
- Keep site-specific ecological observations separate unless a matching rule
  and observation model are justified.
- Report GP results separately by landscape; do not average incomparable
  objective scales into one headline.
- Report tree size/depth and instruction-budget exhaustion before making
  claims about bloat control.
- CI success validates software execution and invariants, not ecological truth.
- Thirty seeds are a reproducibility floor, not a power analysis.
