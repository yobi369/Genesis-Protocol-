"""Distribution-free paired inference helpers for exploratory experiments."""
from __future__ import annotations

import random
from collections.abc import Sequence
from math import sqrt
from statistics import mean, stdev


def paired_permutation_test(differences: Sequence[float], *, permutations: int = 10000,
                            seed: int = 1) -> dict[str, float | int | str]:
    """Two-sided sign-flip randomization test of a paired mean difference."""
    if len(differences) < 2 or permutations < 1:
        raise ValueError("at least two paired observations and one permutation required")
    observed = abs(mean(differences))
    rng = random.Random(seed)
    extreme = 0
    for _ in range(permutations):
        candidate = abs(mean(value if rng.random() < 0.5 else -value
                             for value in differences))
        extreme += candidate >= observed - 1e-15
    p_value = (extreme + 1) / (permutations + 1)
    return {"method": "paired sign-flip randomization", "statistic_abs_mean": observed,
            "p_value_two_sided": p_value, "permutations": permutations, "seed": seed}


def bootstrap_mean_interval(values: Sequence[float], *, confidence: float = 0.95,
                            replicates: int = 5000, seed: int = 1
                            ) -> tuple[float, float]:
    """Percentile bootstrap interval for a mean; preserves reproducibility."""
    if len(values) < 2 or not 0 < confidence < 1 or replicates < 100:
        raise ValueError("need >=2 values, confidence in (0,1), and >=100 replicates")
    rng = random.Random(seed)
    estimates = sorted(mean([rng.choice(values) for _ in values]) for _ in range(replicates))
    tail = (1 - confidence) / 2
    low = estimates[int(tail * (replicates - 1))]
    high = estimates[int((1 - tail) * (replicates - 1))]
    return low, high


def paired_effect_summary(differences: Sequence[float]) -> dict[str, float | int]:
    if len(differences) < 2:
        raise ValueError("at least two paired differences required")
    spread = stdev(differences)
    delta = mean(differences)
    return {"n": len(differences), "mean_difference": delta,
            "standard_deviation": spread,
            "standardized_paired_effect": delta / spread if spread else 0.0,
            "standard_error": spread / sqrt(len(differences))}
