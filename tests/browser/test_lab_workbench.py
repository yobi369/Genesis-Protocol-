import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.getenv("GENESIS_BROWSER_TESTS") != "1", reason="browser suite runs in dedicated CI job")

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]


def _large_run(seed: int, offset: float) -> dict:
    reports = [
        {
            "generation": generation,
            "species_population": {"foragers": 60 + generation % 7, "scavengers": 40},
            "mean_resources": offset + generation * 0.25,
            "mean_survival": 18.5 + (generation % 5) / 10,
            "pareto_front_size": 12 + generation % 9,
        }
        for generation in range(250)
    ]
    lineage = [
        {
            "organism_id": index,
            "species_id": index % 4,
            "parent_ids": [index - 1] if index else [],
            "generation_born": index // 80,
        }
        for index in range(20000)
    ]
    return {"seed": seed, "engine_version": "0.3.0", "config": {"population": 100},
            "reports": reports, "lineage": lineage}


def test_large_import_comparison_mobile_layout_and_manifest(tmp_path):
    first = tmp_path / "baseline.json"
    second = tmp_path / "candidate.json"
    first.write_text(json.dumps(_large_run(101, 0)), encoding="utf-8")
    second.write_text(json.dumps(_large_run(101, 5)), encoding="utf-8")
    html = ROOT / "web" / "lab.html"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(html.as_uri())
        page.locator("#files").set_input_files([str(first), str(second)])
        page.get_by_text("2 experiment(s) loaded").wait_for(timeout=15000)
        assert page.locator("#population").inner_text() == "100"
        assert page.locator("#generation").get_attribute("max") == "249"
        assert page.locator("#lineage circle").count() <= 180
        page.locator("#base").select_option("0")
        page.locator("#candidate").select_option("1")
        page.get_by_role("button", name="Compare summaries").click()
        comparison = page.locator("#comparison").inner_text()
        assert "baseline.json" in comparison and "candidate.json" in comparison
        assert "difference" in comparison
        assert page.locator("canvas").get_attribute("aria-label") == "Experiment trajectory"
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.locator("#notes").fill("Holdout protocol recorded.")
        with page.expect_download() as download_info:
            page.get_by_role("button", name="Export manifest").click()
        download = download_info.value
        target = tmp_path / download.suggested_filename
        download.save_as(target)
        manifest = json.loads(target.read_text(encoding="utf-8"))
        assert manifest["format"] == "genesis-lab-manifest-v1"
        assert len(manifest["experiments"]) == 2
        assert manifest["notes"] == "Holdout protocol recorded."
        browser.close()
