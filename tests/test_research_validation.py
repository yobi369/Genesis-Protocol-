# ruff: noqa: I001
import importlib.util
import math
from pathlib import Path

from genesis_protocol.evaluator import evaluate
from genesis_protocol.genome import Op
from genesis_protocol.models import Environment, Organism
from genesis_protocol.program import Action, IfEnergyBelow, Program, RepeatAction
from genesis_protocol.reference_ecology import (
    calibrate_empirical_references,
    load_hudson_bay_csv,
    simulate_lotka_volterra,
    simulate_rosenzweig_macarthur,
)
from genesis_protocol.research import SpatialEcosystem, nsga2_select
from genesis_protocol.tree_gp import evaluate_tree
from genesis_protocol.validation import (
    _adjusted_rand,
    _deap_select,
    _gp_fitness,
    _program_to_tree,
    _tree_fitness,
)


ROOT = Path(__file__).resolve().parents[1]


def test_reference_odes_are_positive_and_return_requested_steps():
    lv = simulate_lotka_volterra(24, 4, steps=20)
    rm = simulate_rosenzweig_macarthur(24, 4, steps=20)
    assert len(lv) == len(rm) == 21
    assert all(point.prey >= 0 and point.predators >= 0 for point in lv + rm)
    assert all(math.isfinite(point.prey + point.predators) for point in lv + rm)


def test_empirical_index_load_and_chronological_holdout_calibration():
    data = load_hudson_bay_csv(ROOT / "data/empirical/hudson_bay_lynx_hare_1900_1920.csv")
    assert len(data) == 21
    assert data[0].time == 1900
    result = calibrate_empirical_references(data)
    assert result["train_observations"] == 14
    assert result["holdout_observations"] == 7
    for model in result["models"].values():
        assert math.isfinite(model["training_log_rmse"])
        assert math.isfinite(model["holdout_log_rmse"])
        assert model["holdout_start_year"] == 1914


def test_spatial_ecosystem_supports_default_config():
    result = SpatialEcosystem(seed=5).run()
    assert len(result.trajectory) == 50


def test_matched_tree_and_linear_grammar_have_identical_action_semantics():
    program = Program((
        Action(Op.GATHER, 3),
        IfEnergyBelow(4, Action(Op.REST, 2)),
        RepeatAction(Action(Op.COOPERATE, 1), 2),
    ))
    tree = _program_to_tree(program)
    tree_result = evaluate_tree(tree, initial_energy=20, resource_supply=20, instruction_budget=256)
    linear_result = evaluate(
        Organism(1, program.compile()),
        Environment(resource_supply=20, movement_cost=1, gather_reward=2, cooperation_bonus=1),
        initial_energy=20,
        instruction_budget=256,
    )
    assert (tree_result.energy_remaining, tree_result.resources_gathered,
            tree_result.cooperation_actions) == (
                linear_result.energy_remaining, linear_result.resources_gathered,
                linear_result.cooperation_actions,
            )
    assert _tree_fitness(tree, 1) == _gp_fitness(program, 1)


def test_deap_reference_selection_matches_genesis_front_on_simple_points():
    if importlib.util.find_spec("deap") is None:
        return
    points = ((-1.0, -5.0), (-2.0, -3.0), (-3.0, -2.0), (-5.0, -1.0),
              (-5.0, -5.0), (-4.0, -4.0), (-0.5, -8.0), (-8.0, -0.5))
    ours = nsga2_select(points, 4)
    reference = _deap_select(points, 4)
    assert set(ours) == set(reference)


def test_adjusted_rand_index_known_partitions():
    assert _adjusted_rand((0, 0, 1, 1), (8, 8, 4, 4)) == 1.0
    assert _adjusted_rand((0, 0, 1, 1), (0, 1, 0, 1)) < 0
