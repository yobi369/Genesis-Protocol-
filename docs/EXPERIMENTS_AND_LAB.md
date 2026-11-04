# Experiment Comparison and Interactive Laboratory

## Replicated comparisons

`compare_conditions` runs baseline and candidate configurations using the same replicate seeds. It reports raw replicate summaries, means, sample standard deviations, paired mean difference and an approximate 95% normal interval.

The interval is exploratory. It is not a substitute for a pre-registered analysis, an appropriate small-sample method, multiple-comparison correction or independent replication.

## Run an ecosystem

```bash
genesis-ecology --seed 7 --generations 40 --population-per-species 30 --output run.json
```

## Generate the offline laboratory viewer

```python
import json
from genesis_protocol.lab import render_lab

with open("run.json", encoding="utf-8") as handle:
    experiment = json.load(handle)

render_lab(experiment, "genesis-lab.html")
```

Open the generated HTML file locally. The viewer includes generation navigation, headline metrics, a resource trajectory and species population filtering. It does not upload data or require an external service.

## Recommended experimental protocol

- Use at least 20 independent seeds for exploratory comparisons where compute permits.
- Predefine the primary outcome and environmental schedule.
- Compare against random-search, no-mutation and no-cooperation controls.
- Report the full replicate distribution, not only the best run.
- Run ablations for crossover, mutation, reciprocity reward and Pareto selection.
- Reserve unseen environment schedules as holdouts.
- Preserve raw JSON records, code commit, package version and hardware/software metadata.
