# Research Validation Results — 30 Paired Seeds

**Campaign:** 2026-11-04  
**Workflow run:** https://github.com/yobi369/Genesis-Protocol-/actions/runs/41797358407  
**Raw artifact:** https://github.com/yobi369/Genesis-Protocol-/actions/runs/41797358407/artifacts/13306056948  
**Seed set:** 1001–1030, paired across conditions

The machine-readable artifact is authoritative. This document summarizes the
observed results and their limits; it is not a scientific validation certificate.

## 1. Replicated ecological conditions

Each condition ran 30 independent seeds.

| Condition | Mean resources | Mean survival-energy proxy | Reciprocal cooperation | Final species count | Genotype diversity |
|---|---:|---:|---:|---:|---:|
| Resource rich | 3.338 | 30.220 | 0.219 | 15.20 | 14.867 |
| Resource scarce | 1.019 | 24.891 | 0.232 | 15.10 | 14.500 |
| Resource pulse | 1.367 | 25.165 | 0.368 | 15.93 | 15.567 |

Paired rich-minus-scarce results:

| Metric | Mean paired difference | 95% bootstrap interval | Two-sided sign-flip p | Standardized paired effect |
|---|---:|---:|---:|---:|
| Mean resources | +2.319 | [1.964, 2.663] | 0.00020 | 2.330 |
| Survival-energy proxy | +5.330 | [3.228, 7.401] | 0.00020 | 0.884 |
| Species count | +0.100 | [-1.033, 1.233] | 0.905 | 0.031 |
| Genotype diversity | +0.367 | [-0.800, 1.500] | 0.578 | 0.114 |

**Interpretation:** the resource schedule clearly changed resource acquisition
and the energy/survival proxy. This campaign did not detect a corresponding
change in final species count or genotype diversity. Do not interpret a
non-significant result as proof of no effect.

## 2. Spatial agent model versus ecological ODE references

Thirty matched initial-condition seeds were run for 40 steps. The spatial
agent-based model was compared with deterministic fourth-order Runge–Kutta
integrations of Lotka–Volterra and Rosenzweig–MacArthur equations.

| Reference | Prey log-trajectory RMSE | Predator log-trajectory RMSE |
|---|---:|---:|
| Lotka–Volterra | 1.762 | 1.474 |
| Rosenzweig–MacArthur | 0.911 | 1.401 |

Across spatial replicates, final prey averaged 71.8 (SD 8.48), final predators
3.57 (SD 1.19), predation events 37.1 (SD 14.30), and final social edges 439.4
(SD 111.85).

These are descriptive structural comparisons, not equivalence tests. The
spatial engine is discrete, local and resource-limited; the ODEs are
well-mixed continuous models.

## 3. Speciation threshold sensitivity

Thirty seeds were evaluated for each synthetic genome distribution at nine
edit-distance thresholds from 0.10 to 0.90.

- **Separated lineages:** threshold 0.60 recovered three clusters on average
  with adjusted Rand index (ARI) 1.00 and zero forward/reverse order-count
  sensitivity. Threshold 0.50 was nearly as strong (ARI 0.999).
- **Length-shifted lineages:** threshold 0.50 recovered three clusters with
  ARI 1.00 and zero order-count sensitivity.
- **Continuous random genomes:** ARI remained 0.00. At thresholds 0.10–0.60,
  the mean cluster count remained 36; at 0.80 it fell to 23.8 and at 0.90 to
  6.9. The algorithm is merging a continuum, not discovering true species.

**Interpretation:** thresholds around 0.5–0.6 worked for these two constructed
lineage distributions, but no universal biological threshold is justified.
The order sensitivity of representative clustering remains a limitation.

## 4. NSGA-II selection against DEAP

The Genesis nondominated sorting and crowding selector was compared with
DEAP's independent `sortNondominated` and `assignCrowdingDist` utilities on
ZDT1 (two objectives) and DTLZ2 (three objectives), at populations of 100, 250
and 500, with 30 seeds for each case.

- Selected-set overlap: **1.000** in all six problem/size groups.
- First-front Jaccard agreement: **1.000** in all six groups.
- At 500 candidates, Genesis averaged 0.318 seconds on ZDT1 and 0.318 seconds
  on DTLZ2; DEAP averaged 0.097 and 0.091 seconds respectively.

**Interpretation:** selection parity was exact on these tested populations,
but Genesis's Python implementation was roughly 3.3–3.5 times slower. This
benchmarks selection, not full optimizer convergence or solution quality.

## 5. Tree GP versus linear GP

Thirty matched seeds used identical initial phenotypes, the same fitness
function, environment, population size (36), generation count (20), elitism,
tournament selection and mutation rate.

| Representation | Mean best fitness across seeds |
|---|---:|
| Linear typed programs | 37.990 |
| Tree AST programs | 33.653 |

Paired tree-minus-linear best-fitness difference: **-4.337**, 95% bootstrap
interval **[-5.060, -3.532]**, two-sided paired sign-flip p = **0.00020**,
standardized paired effect = **-1.973**.

**Interpretation:** linear GP outperformed the current tree implementation in
this matched experiment. The tree grammar was deliberately restricted to
primitive actions, one-action energy guards and repeated actions to keep
semantics comparable. This does not establish that tree GP is generally
inferior; tree operators, grammar expressivity and bloat control need further
work.

## 6. Empirical Hudson Bay hare–lynx pattern check

The repository snapshot contains 21 annual observations from 1900–1920. The
chronological split used the first 14 years for calibration and the final seven
years for holdout. The data are historical trapping/pelt indices, not
standardized direct census counts. The TSA documentation describes the
historical hare series as based on trapper questionnaires; provenance is
documented in `data/empirical/README.md`.

Holdout log-RMSE (lower is better):

| Model / baseline | Combined | Prey (hare) | Predators (lynx) |
|---|---:|---:|---:|
| Training-mean baseline | 0.832 | 0.967 | 0.671 |
| Last-observation persistence | 1.176 | 1.523 | 0.668 |
| Lotka–Volterra | 0.990 | 0.535 | 1.294 |
| Rosenzweig–MacArthur | 0.732 | 0.612 | 0.835 |
| Genesis spatial agent model | 0.641 | 0.603 | 0.678 |

The spatial model's selected training configuration used resource regrowth 0,
initial energy 8, prey observation scale 1 and predator observation scale 4.
It was selected only on training error; holdout was scored after selection.

**Interpretation:** the spatial model's prey error was better than the
training-mean baseline, while its predator error was approximately the naive
baseline and slightly worse (0.678 versus 0.671). The current spatial engine
does not implement predator reproduction; the predator observation series
therefore lacks the mechanism needed to explain predator increases. The
aggregate score should not hide this weakness. The short 7-year holdout and
indirect pelt index make this a preliminary pattern check, not predictive
validation.

## 7. Browser workbench scale and usability smoke test

Chromium successfully imported two experiment JSON files, each with 250
generation reports and 20,000 lineage records. Automated checks covered:

- Run import and generation-range navigation.
- Summary comparison between two runs.
- Bounded lineage SVG rendering (at most 180 visible nodes).
- 390-pixel mobile viewport without horizontal overflow.
- Accessible chart name and status announcement.
- Research notes and manifest export.

This is automated browser smoke testing, not moderated human usability
research or a full assistive-technology audit.

## Engineering validation

The 30-seed research workflow completed successfully and uploaded the raw JSON
artifact. The Chromium browser job passed. The repository quality workflow
reported Ruff passed, **44 tests passed and 1 skipped**, and **93.33% measured
coverage** (the orchestration CLI is excluded from line coverage because the
dedicated research workflow executes it end-to-end).

## Limitations and next research steps

1. Add predator reproduction and test whether it improves the lynx holdout
   without degrading prey fit; use additional empirical time series.
2. Repeat empirical calibration on longer, independent datasets and validate
   observation models and sampling effort before interpreting parameters.
3. Improve species clustering with density-aware and order-invariant methods;
   evaluate on larger, noisy, recombining and reticulate genome distributions.
4. Benchmark NSGA-II convergence, hypervolume and IGD across independent
   implementations, including larger populations and more objective counts.
5. Improve tree GP variation operators and compare richer nested grammars under
   matched semantics, multiple fitness landscapes and bloat constraints.
6. Conduct moderated usability tests with researchers and keyboard/screen-reader
   users; the current browser test is only an automated smoke test.

Thirty seeds are a reproducibility floor, not a power calculation. Bootstrap
intervals and randomization tests are exploratory. Independent replication,
preregistered analysis, additional datasets and domain review remain necessary.
