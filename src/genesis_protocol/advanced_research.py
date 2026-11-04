"""Advanced ecological and genetic-programming validation experiments.

This module is deliberately additive: the original spatial model and the first
30-seed campaign remain unchanged as baselines. Outputs retain raw replicates
and train/holdout boundaries. It is not a claim of ecological realism.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .genome import Op
from .reference_ecology import PopulationPoint, load_hudson_bay_csv
from .research import SpatialConfig, SpatialEcosystem
from .tree_gp import (
    EnergyGuard,
    Primitive,
    RepeatNode,
    SequenceNode,
    TreeNode,
    evaluate_tree,
    random_tree,
    tree_depth,
    tree_size,
)


