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
