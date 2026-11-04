"""Numerical ecological reference models and empirical-data adapters.

Lotka–Volterra and Rosenzweig–MacArthur are deterministic ODE baselines.
They are not expected to reproduce the agent-based spatial model without
parameter calibration and an explicit observation model.
"""
from __future__ import annotations

import csv
import math
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PopulationPoint:
    time: float
    prey: float
    predators: float


@dataclass(frozen=True, slots=True)
class LotkaVolterraParameters:
    prey_growth: float = 0.55
    predation_rate: float = 0.025
    predator_conversion: float = 0.008
    predator_mortality: float = 0.35


@dataclass(frozen=True, slots=True)
class RosenzweigMacArthurParameters:
    prey_growth: float = 0.65
    carrying_capacity: float = 90.0
    attack_rate: float = 0.025
    handling_time: float = 0.004
    conversion_efficiency: float = 0.45
    predator_mortality: float = 0.30


def _rk4_step(
    state: tuple[float, float],
    dt: float,
    derivative: Callable[[float, float], tuple[float, float]],
) -> tuple[float, float]:
    x, y = state
    k1 = derivative(x, y)
    k2 = derivative(x + dt * k1[0] / 2, y + dt * k1[1] / 2)
    k3 = derivative(x + dt * k2[0] / 2, y + dt * k2[1] / 2)
    k4 = derivative(x + dt * k3[0], y + dt * k3[1])
    return (
        max(0.0, x + dt * (k1[0] + 2*k2[0] + 2*k3[0] + k4[0]) / 6),
        max(0.0, y + dt * (k1[1] + 2*k2[1] + 2*k3[1] + k4[1]) / 6),
    )


def _integrate(
    derivative: Callable[[float, float], tuple[float, float]],
    initial: tuple[float, float],
    steps: int,
    dt: float,
    substeps: int,
) -> tuple[PopulationPoint, ...]:
    if steps < 1 or dt <= 0 or substeps < 1:
        raise ValueError("steps, dt and substeps must be positive")
    state = initial
    output = [PopulationPoint(0.0, *state)]
    h = dt / substeps
    for step in range(1, steps + 1):
        for _ in range(substeps):
            state = _rk4_step(state, h, lambda x, y: derivative(x, y))
            if not all(math.isfinite(value) for value in state) or max(state) > 1e12:
                raise ArithmeticError("reference ODE diverged")
        output.append(PopulationPoint(step * dt, *state))
    return tuple(output)


def simulate_lotka_volterra(
    initial_prey: float,
    initial_predators: float,
    parameters: LotkaVolterraParameters | None = None,
    *,
    steps: int = 50,
    dt: float = 1.0,
    substeps: int = 20,
) -> tuple[PopulationPoint, ...]:
    """Classical two-species Lotka–Volterra model solved with RK4."""
    if min(initial_prey, initial_predators) <= 0:
        raise ValueError("initial populations must be positive")
    p = parameters or LotkaVolterraParameters()

    def derivative(prey: float, predators: float) -> tuple[float, float]:
        return (
            p.prey_growth * prey - p.predation_rate * prey * predators,
            p.predator_conversion * prey * predators - p.predator_mortality * predators,
        )

    return _integrate(derivative, (initial_prey, initial_predators), steps, dt, substeps)


def simulate_rosenzweig_macarthur(
    initial_prey: float,
    initial_predators: float,
    parameters: RosenzweigMacArthurParameters | None = None,
    *,
    steps: int = 50,
    dt: float = 1.0,
    substeps: int = 20,
) -> tuple[PopulationPoint, ...]:
    """Logistic prey growth with a Holling-II functional response."""
    if min(initial_prey, initial_predators) <= 0:
        raise ValueError("initial populations must be positive")
    p = parameters or RosenzweigMacArthurParameters()

    def derivative(prey: float, predators: float) -> tuple[float, float]:
        intake = p.attack_rate * prey / (1 + p.attack_rate * p.handling_time * prey)
        return (
            p.prey_growth * prey * (1 - prey / p.carrying_capacity) - intake * predators,
            p.conversion_efficiency * intake * predators - p.predator_mortality * predators,
        )

    return _integrate(derivative, (initial_prey, initial_predators), steps, dt, substeps)


def load_hudson_bay_csv(path: str | Path) -> tuple[PopulationPoint, ...]:
    """Load a semicolon-delimited historical pelt-index series.

    The supplied source file is a teaching/research transcription, not a direct
    census. Units and source caveats are preserved in its adjacent README.
    """
    rows: list[PopulationPoint] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        required = {"Year", "Lynx", "Hare"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("empirical file must contain Year, Lynx and Hare columns")
        for row in reader:
            year, lynx, hare = float(row["Year"]), float(row["Lynx"]), float(row["Hare"])
            if min(lynx, hare) <= 0:
                raise ValueError("population-index observations must be positive")
            rows.append(PopulationPoint(year, hare, lynx))
    if len(rows) < 10 or any(b.time <= a.time for a, b in pairwise(rows)):
        raise ValueError("empirical series must have at least 10 increasing observations")
    return tuple(rows)


def _log_rmse(predicted: Sequence[PopulationPoint], observed: Sequence[PopulationPoint],
              start: int, stop: int) -> float:
    errors = []
    for prediction, actual in zip(predicted[start:stop], observed[start:stop]):
        errors.extend((
            math.log1p(prediction.prey) - math.log1p(actual.prey),
            math.log1p(prediction.predators) - math.log1p(actual.predators),
        ))
    return math.sqrt(sum(value * value for value in errors) / len(errors))


def calibrate_empirical_references(
    observations: Sequence[PopulationPoint],
    *,
    train_fraction: float = 0.70,
) -> dict[str, object]:
    """Coarse transparent grid calibration; final holdout is never optimized."""
    if len(observations) < 10 or not 0.5 <= train_fraction <= 0.85:
        raise ValueError("need >=10 observations and train_fraction in [0.5, 0.85]")
    split = int(len(observations) * train_fraction)
    first = observations[0]
    steps = len(observations) - 1
    dt = (observations[-1].time - first.time) / steps
    lv_candidates: list[tuple[float, LotkaVolterraParameters, tuple[PopulationPoint, ...]]] = []
    for a in (0.15, 0.3, 0.5, 0.75):
        for b in (0.002, 0.006, 0.012, 0.025):
            for c in (0.001, 0.003, 0.008, 0.015):
                for d in (0.08, 0.2, 0.35, 0.55):
                    params = LotkaVolterraParameters(a, b, c, d)
                    try:
                        trajectory = simulate_lotka_volterra(
                            first.prey, first.predators, params, steps=steps, dt=dt, substeps=10
                        )
                        score = _log_rmse(trajectory, observations, 0, split)
                        lv_candidates.append((score, params, trajectory))
                    except ArithmeticError:
                        continue
    rm_candidates: list[tuple[float, RosenzweigMacArthurParameters,
                              tuple[PopulationPoint, ...]]] = []
    for r in (0.25, 0.5, 0.8):
        for capacity in (50.0, 90.0, 140.0):
            for attack in (0.006, 0.015, 0.03):
                for handling in (0.001, 0.004):
                    for efficiency in (0.2, 0.45, 0.7):
                        for mortality in (0.08, 0.2, 0.4):
                            params = RosenzweigMacArthurParameters(
                                r, capacity, attack, handling, efficiency, mortality
                            )
                            try:
                                trajectory = simulate_rosenzweig_macarthur(
                                    first.prey, first.predators, params,
                                    steps=steps, dt=dt, substeps=10,
                                )
                                score = _log_rmse(trajectory, observations, 0, split)
                                rm_candidates.append((score, params, trajectory))
                            except ArithmeticError:
                                continue
    if not lv_candidates or not rm_candidates:
        raise ArithmeticError("all ecological reference parameterizations diverged")
    results = {}
    for name, candidates in (("lotka_volterra", lv_candidates),
                             ("rosenzweig_macarthur", rm_candidates)):
        candidates.sort(key=lambda item: item[0])
        train_score, params, trajectory = candidates[0]
        results[name] = {
            "parameters": asdict(params),
            "training_log_rmse": train_score,
            "holdout_log_rmse": _log_rmse(trajectory, observations, split, len(observations)),
            "trajectory": [asdict(point) for point in trajectory],
            "grid_candidates": len(candidates),
            "holdout_start_year": observations[split].time,
        }
    return {
        "dataset_observations": len(observations),
        "train_observations": split,
        "holdout_observations": len(observations) - split,
        "split_method": "chronological; first 70% train, final 30% untouched holdout",
        "observation_note": "historical harvest/pelt index, not direct census abundance",
        "models": results,
    }
