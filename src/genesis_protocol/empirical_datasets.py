"""Validated import helpers for independent hare pellet monitoring datasets."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class HarePelletObservation:
    year: int
    site: str
    tray_count: int
    pellet_total: int
    mean_pellets_per_tray: float


def load_bonanza_hare_pellets_csv(path: str | Path) -> tuple[HarePelletObservation, ...]:
    """Load BNZ LTER 69 raw tray records and aggregate only within site-year.

    The source's litter year spans spring-to-spring and pellet counts are
    observations per 1 m² tray, not direct hare density estimates.
    """
    grouped: dict[tuple[int, str], list[int]] = defaultdict(list)
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        required = {"YEAR", "SITE", "TRAY", "PELLET(count)"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"BNZ LTER CSV must contain columns: {sorted(required)}")
        for line_number, row in enumerate(reader, start=2):
            try:
                year = int(row["YEAR"])
                site = row["SITE"].strip()
                int(row["TRAY"])
                raw_count = row["PELLET(count)"].strip()
                pellets = int(raw_count) if raw_count else 0
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid BNZ record on line {line_number}") from exc
            if not 1900 <= year <= 2200 or not site or pellets < 0:
                raise ValueError(f"out-of-range BNZ record on line {line_number}")
            grouped[(year, site)].append(pellets)
    if not grouped:
        raise ValueError("BNZ file contains no usable tray records")
    output = []
    for (year, site), counts in sorted(grouped.items()):
        mean = sum(counts) / len(counts)
        if not math.isfinite(mean):
            raise ValueError(f"non-finite pellet mean for {year} {site}")
        output.append(HarePelletObservation(
            year, site, len(counts), sum(counts), mean,
        ))
    return tuple(output)


def chronological_holdout(
    observations: Iterable[HarePelletObservation], train_fraction: float = 0.70,
) -> tuple[tuple[HarePelletObservation, ...], tuple[HarePelletObservation, ...]]:
    """Split unique ordered year/site rows without random leakage across years."""
    if not 0.5 <= train_fraction < 1.0:
        raise ValueError("train_fraction must be in [0.5, 1)")
    rows = tuple(sorted(observations, key=lambda row: (row.year, row.site)))
    years = sorted({row.year for row in rows})
    if len(years) < 5:
        raise ValueError("at least five distinct years are required")
    split_index = max(1, min(len(years) - 1, int(len(years) * train_fraction)))
    cutoff = years[split_index]
    train = tuple(row for row in rows if row.year < cutoff)
    holdout = tuple(row for row in rows if row.year >= cutoff)
    if not train or not holdout:
        raise ValueError("chronological split produced an empty partition")
    return train, holdout


def run_bonanza_prey_only_benchmark(
    observations: Iterable[HarePelletObservation], train_fraction: float = 0.70,
) -> dict[str, object]:
    """Fit a site-specific log-AR(1) baseline and compare naive forecasts.

    This is a prey-index benchmark only. It deliberately does not synthesize a
    predator series from hare-only observations or treat pellet counts as
    direct animal density.
    """
    rows = tuple(observations)
    by_site: dict[str, list[HarePelletObservation]] = defaultdict(list)
    for row in rows:
        by_site[row.site].append(row)
    site_results = []
    for site, site_rows in sorted(by_site.items()):
        site_rows = sorted(site_rows, key=lambda row: row.year)
        years = [row.year for row in site_rows]
        if len(set(years)) != len(years):
            raise ValueError(f"duplicate year/site rows for site {site}")
        if len(site_rows) < 10:
            continue
        split = max(5, min(len(site_rows) - 1, int(len(site_rows) * train_fraction)))
        train = [math.log1p(row.mean_pellets_per_tray) for row in site_rows[:split]]
        holdout = [math.log1p(row.mean_pellets_per_tray) for row in site_rows[split:]]
        x_values, y_values = train[:-1], train[1:]
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)
        variance = sum((x - x_mean) ** 2 for x in x_values)
        phi = (
            sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values)) / variance
            if variance > 1e-12 else 0.0
        )
        intercept = y_mean - phi * x_mean
        forecast = []
        previous = train[-1]
        for _ in holdout:
            previous = intercept + phi * previous
            forecast.append(previous)
        mean_forecast = [y_mean] * len(holdout)
        persistence_forecast = [train[-1]] * len(holdout)

        def rmse(prediction: list[float]) -> float:
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(prediction, holdout)) / len(holdout))

        site_results.append({
            "site": site,
            "train_years": years[:split],
            "holdout_years": years[split:],
            "train_tray_records": sum(row.tray_count for row in site_rows[:split]),
            "holdout_tray_records": sum(row.tray_count for row in site_rows[split:]),
            "ar1_parameters": {"intercept": intercept, "phi": phi},
            "holdout_log_rmse": {
                "ar1": rmse(forecast),
                "training_mean": rmse(mean_forecast),
                "last_observation": rmse(persistence_forecast),
            },
        })
    if not site_results:
        raise ValueError("no Bonanza site has at least 10 annual site-level observations")
    return {
        "model_scope": "hare-only pellet-index time-series benchmark",
        "site_count": len(site_results),
        "site_results": site_results,
        "mean_site_holdout_log_rmse": {
            model: sum(row["holdout_log_rmse"][model] for row in site_results) / len(site_results)
            for model in ("ar1", "training_mean", "last_observation")
        },
        "caveat": (
            "Pellet counts per tray are an indirect index. Site-specific fits are kept separate; "
            "no predator abundance is inferred and this is not a predator-prey validation."
        ),
    }
