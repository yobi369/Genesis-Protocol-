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


def test_bonanza_prey_only_benchmark_keeps_sites_separate_and_holds_out_later_years():
    from genesis_protocol.empirical_datasets import run_bonanza_prey_only_benchmark

    rows = []
    for site, scale in (("A", 1.0), ("B", 2.0)):
        for year in range(1985, 2000):
            count = (year - 1984) * scale
            rows.append(HarePelletObservation(year, site, 6, int(count * 6), count))
    result = run_bonanza_prey_only_benchmark(rows)
    assert result["site_count"] == 2
    assert {row["site"] for row in result["site_results"]} == {"A", "B"}
    assert all(min(row["holdout_years"]) > max(row["train_years"])
               for row in result["site_results"])
    assert set(result["mean_site_holdout_log_rmse"]) == {
        "ar1", "training_mean", "last_observation"
    }


def test_bonanza_loader_treats_blank_pellet_values_as_missing_not_zero(tmp_path: Path):
    source = tmp_path / "bnz.csv"
    source.write_text(
        "YEAR,SITE,TRAY,PELLET(count)\n"
        "1985,FP1A,1,4\n"
        "1985,FP1A,2,\n",
        encoding="utf-8",
    )
    rows = load_bonanza_hare_pellets_csv(source)
    assert rows[0].tray_count == 1
    assert rows[0].pellet_total == 4
    assert rows[0].mean_pellets_per_tray == 4.0
    assert rows[0].missing_tray_count == 1


def test_bonanza_loader_rejects_duplicate_tray_keys(tmp_path: Path):
    source = tmp_path / "duplicate.csv"
    source.write_text(
        "YEAR,SITE,TRAY,PELLET(count)\n"
        "1985,FP1A,1,4\n"
        "1985,FP1A,1,5\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate BNZ tray key"):
        load_bonanza_hare_pellets_csv(source)


def test_bonanza_ar1_benchmark_handles_irregular_year_gaps():
    from genesis_protocol.empirical_datasets import run_bonanza_prey_only_benchmark

    rows = tuple(
        HarePelletObservation(year, "A", 6, count * 6, float(count))
        for year, count in zip(
            (1985, 1986, 1987, 1988, 1990, 1991, 1992, 1994, 1995, 1996, 1997, 1998),
            range(1, 13),
        )
    )
    result = run_bonanza_prey_only_benchmark(rows)
    assert result["site_count"] == 1
    assert result["site_results"][0]["holdout_years"][-1] == 1998
