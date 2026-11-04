# Genesis Protocol — Research Validation Protocol

## Campaign contract

The research-validation workflow runs 30 independent seeds (1001–1030), paired
across experimental conditions. The CLI rejects fewer than 30 unique seeds.
Every campaign writes a machine-readable JSON artifact with raw replicate rows,
configuration summaries, uncertainty intervals, and explicit caveats.

Run locally:

```bash
python -m pip install -e ".[dev,research]"
genesis-research-validation --seeds 30 --output artifacts/research-validation.json
```

The workflow uploads `genesis-research-validation-30-seeds` as a 30-day artifact.
The JSON is the authoritative record; summaries printed in Actions logs are only
a convenience.

## 1. Ecological replicated conditions

Three resource schedules (rich, scarce, pulsed) use the same 30 seeds, species
definitions, population sizes, and evolutionary settings. Raw per-seed final
resources, energy/survival proxy, reciprocal cooperation, Pareto-front size,
genotype diversity, species count and final population are retained. Rich vs
scarce conditions receive paired effect estimates, sign-flip permutation tests,
and bootstrap intervals.

## 2. Spatial model versus established ecological references

The spatial agent model is compared to two independent deterministic ODE
references solved with fourth-order Runge–Kutta integration:

- Classical Lotka–Volterra predator–prey equations.
- Rosenzweig–MacArthur logistic-prey / Holling type-II predation equations.

For each seed, the same randomized initial prey and predator counts are used
across models. Log-scale trajectory RMSE and persistence/resource/social metrics
are reported. This is a structural comparison, not a claim that well-mixed ODE
states should numerically equal discrete spatial agents. Default reference
parameters are explicit and are not tuned to the spatial replicates.

## 3. Speciation threshold and genome-distribution sensitivity

Thirty seeds are evaluated for three genome families: separated lineages,
continuous random genomes, and length-shifted lineages. Nine edit-distance
thresholds are tested (0.10–0.90). Metrics include mean cluster count, adjusted
Rand index against known synthetic labels, within-cluster distance, and
forward-versus-reversed input-order sensitivity. Representative clustering is
order-dependent by design; this campaign quantifies rather than conceals it.

## 4. NSGA-II reference comparison

The local nondominated sorting/crowding selector is compared against DEAP's
independent `tools.sortNondominated` and `tools.emo.assignCrowdingDist`
implementation on 2-objective ZDT1 and 3-objective DTLZ2 generated populations
of 100, 250 and 500 candidates, each over 30 seeds. It records selected-set
overlap, first-front Jaccard agreement and runtime. This is a selection
implementation parity benchmark, not a full optimizer convergence study.

## 5. Tree GP versus linear GP

Both representations receive identical initial phenotypes per seed, the same
population size (36), 20 generations, action semantics, resource environment,
fitness equation, tournament size, mutation rate and elitism. The matched
grammar is intentionally limited to primitive actions, one-action energy
guards and repeated actions so both interpreters can be compared without
silently changing the problem. Raw best-fitness trajectories and paired
differences are retained. This does not compare all possible nested-tree
expressivity against all linear bytecode features.

## 6. Empirical pattern check

The repository includes a 1900–1920 Hudson Bay lynx–hare historical
pelt-index transcription. A transparent coarse grid calibration fits
Lotka–Volterra and Rosenzweig–MacArthur models on the first 70% of years and
reports the final 30% as untouched chronological holdout. Pelt/trapping counts
are indirect abundance proxies, not standardized census counts. The time series
is short and must not be treated as ground truth or as a decisive model
validation. Provenance and caveats are in `data/empirical/README.md`.

For stronger empirical validation, a future study should use the USFWS Tetlin
Refuge hare monitoring data or the Kluane experimental snowshoe-hare datasets,
after reviewing survey design, sampling effort, units, permissions and metadata.
Do not pool incompatible observations or tune on the holdout.

## 7. Browser workbench usability and scale

A dedicated Chromium test imports two 250-generation JSON runs, each with
20,000 lineage records, checks generation navigation, metrics, run comparison,
bounded SVG rendering, a 390px mobile viewport, accessible chart naming and
manifest export. This is automated usability smoke testing, not a substitute
for moderated human usability studies or assistive-technology review.

## Statistical interpretation

- Thirty seeds are a minimum reproducibility floor, not a power calculation.
- Bootstrap and sign-flip results are exploratory unless assumptions and a
  confirmatory analysis plan are preregistered.
- Report effect sizes and intervals, not p-values alone.
- Keep seeds, raw rows, configurations and data provenance with every result.
- Do not claim ecological realism, predictive validity, or generality from CI
  success or synthetic benchmarks alone.
