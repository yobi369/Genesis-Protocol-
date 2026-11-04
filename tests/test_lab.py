import json

from genesis_protocol.ecology import (
    EcologyConfig,
    EcosystemEngine,
    EnvironmentalPhase,
    SpeciesDefinition,
)
from genesis_protocol.lab import render_lab


def test_lab_generates_self_contained_html(tmp_path) -> None:
    result = EcosystemEngine(
        (SpeciesDefinition(0, "test species", 4),),
        (EnvironmentalPhase(0, 20),),
        EcologyConfig(generations=2, initial_energy=100),
        seed=1,
    ).run()
    output = tmp_path / "lab.html"
    path = render_lab(result.to_dict(), output)
    html = path.read_text(encoding="utf-8")
    assert "Genesis Protocol" in html
    assert "generation" in html
    assert "test species" in html
    assert "lineage-tree" in html
    assert "parent_ids" in html
    json.dumps(result.to_dict())
