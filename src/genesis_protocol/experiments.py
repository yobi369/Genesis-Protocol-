"""Replicated experiments and paired condition comparisons."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from statistics import mean, stdev
from typing import Any

from .ecology import (
    EcologyConfig, EcosystemEngine, EnvironmentalPhase, GenerationReport, SpeciesDefinition,
)


@dataclass(frozen=True, slots=True)
class ReplicateSummary:
    seed: int
    final_mean_resources: float
    final_mean_survival: float
    final_mean_reciprocal_cooperation: float
    final_species_count: int
    final_genotype_diversity: int


@dataclass(frozen=True, slots=True)
class ConditionSummary:
    name: str
    replicates: tuple[ReplicateSummary, ...]
    mean_resources: float
    standard_deviation_resources: float
    mean_survival: float
    mean_cooperation: float


@dataclass(frozen=True, slots=True)
class ExperimentComparison:
    metric: str
    baseline: ConditionSummary
    candidate: ConditionSummary
    paired_mean_difference: float
    paired_standard_deviation: float
    confidence_interval_95_normal: tuple[float, float]
    replicate_count: int
    interval_method: str = "paired normal approximation (mean +/- 1.96 standard errors)"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "baseline": asdict(self.baseline),
            "candidate": asdict(self.candidate),
            "paired_mean_difference": self.paired_mean_difference,
            "paired_standard_deviation": self.paired_standard_deviation,
            "confidence_interval_95_normal": list(self.confidence_interval_95_normal),
            "replicate_count": self.replicate_count,
            "interval_method": self.interval_method,
            "interpretation": (
                "Exploratory paired summary only. The normal interval is approximate; "
                "inspect raw replicates and use a pre-registered analysis for confirmatory claims."
            ),
        }


def _summary(
    name: str,
    species: tuple[SpeciesDefinition, ...],
    schedule: tuple[EnvironmentalPhase, ...],
    config: EcologyConfig,
    seeds: tuple[int, ...],
) -> ConditionSummary:
    records: list[ReplicateSummary] = []
    for seed in seeds:
        result = EcosystemEngine(species, schedule, config, seed=seed).run()
        final = result.reports[-1]
        records.append(ReplicateSummary(
            seed=seed,
            final_mean_resources=final.mean_resources,
            final_mean_survival=final.mean_survival,
            final_mean_reciprocal_cooperation=final.mean_reciprocal_cooperation,
            final_species_count=len({item.species_id for item in result.final_population}),
            final_genotype_diversity=final.genotype_diversity,
        ))
    resources = [item.final_mean_resources for item in records]
    return ConditionSummary(
        name=name,
        replicates=tuple(records),
        mean_resources=mean(resources),
        standard_deviation_resources=stdev(resources) if len(resources) > 1 else 0.0,
        mean_survival=mean(item.final_mean_survival for item in records),
        mean_cooperation=mean(item.final_mean_reciprocal_cooperation for item in records),
    )


def compare_conditions(
    species: tuple[SpeciesDefinition, ...],
    schedule: tuple[EnvironmentalPhase, ...],
    baseline: EcologyConfig,
    candidate: EcologyConfig,
    *,
    seeds: tuple[int, ...] = (11, 23, 37, 41, 59),
) -> ExperimentComparison:
    """Compare two configurations using the same seeds (paired design)."""
    if len(seeds) < 2 or len(set(seeds)) != len(seeds):
        raise ValueError("at least two unique replicate seeds are required")
    base = _summary("baseline", species, schedule, baseline, seeds)
    trial = _summary("candidate", species, schedule, candidate, seeds)
    differences = [
        candidate_run.final_mean_resources - baseline_run.final_mean_resources
        for baseline_run, candidate_run in zip(base.replicates, trial.replicates)
    ]
    delta = mean(differences)
    spread = stdev(differences)
    margin = 1.96 * spread / sqrt(len(differences))
    return ExperimentComparison(
        metric="final_mean_resources_per_organism",
        baseline=base,
        candidate=trial,
        paired_mean_difference=delta,
        paired_standard_deviation=spread,
        confidence_interval_95_normal=(delta - margin, delta + margin),
        replicate_count=len(seeds),
    )
