from io import StringIO
from pathlib import Path

import pytest

from genesis_protocol.empirical_datasets import (
    HarePelletObservation,
    chronological_holdout,
    load_bonanza_hare_pellets_csv,
)


def test_bonanza_loader_aggregates_only_within_site_and_year(tmp_path: Path):
    source = tmp_path / "bnz.csv"
    source.write_text(
        "YEAR,SITE,TRAY,LEAF(g),WOOD(g),PELLET(count),FLAGS,NOTE,LOG WT.\n"
        "1985,FP1A,1,0.7,0.17,0,,,\n"
        "1985,FP1A,2,0.66,0,4,,,\n"
        "1985,FP1B,1,0.5,0,8,,,\n"
        "1986,FP1A,1,0.5,0,6,,,\n",
        encoding="utf-8",
    )
    rows = load_bonanza_hare_pellets_csv(source)
    assert rows == (
        HarePelletObservation(1985, "FP1A", 2, 4, 2.0),
        HarePelletObservation(1985, "FP1B", 1, 8, 8.0),
        HarePelletObservation(1986, "FP1A", 1, 6, 6.0),
    )


def test_bonanza_loader_rejects_bad_schema_and_negative_counts(tmp_path: Path):
    bad = tmp_path / "bad.csv"
    bad.write_text("YEAR,SITE,TRAY\n1985,FP1A,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain columns"):
        load_bonanza_hare_pellets_csv(bad)
    bad.write_text(
        "YEAR,SITE,TRAY,PELLET(count)\n1985,FP1A,1,-1\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="out-of-range"):
        load_bonanza_hare_pellets_csv(bad)


def test_chronological_holdout_keeps_later_years_untouched():
    rows = tuple(HarePelletObservation(year, "A", 2, year, year / 2)
                 for year in range(1985, 1995))
    train, holdout = chronological_holdout(rows)
    assert max(row.year for row in train) < min(row.year for row in holdout)
    assert len(train) == 7
    assert len(holdout) == 3
