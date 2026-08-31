from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SIMULATION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIMULATION_ROOT / "src"))

from exp001.config import (  # noqa: E402
    load_json,
    validate_bounded_config,
    validate_joint_config,
)
from exp001.experiment import run_bounded, run_joint_discriminator  # noqa: E402
from exp001.statistics import wilson_interval, worst_case_wilson_half_width  # noqa: E402


REPO_ROOT = SIMULATION_ROOT.parent
BOUNDED_CONFIG = REPO_ROOT / "simulation" / "configs" / "EXP-001" / "bounded-phase1.json"
JOINT_CONFIG = REPO_ROOT / "simulation" / "configs" / "EXP-001" / "joint-discriminator.json"


class ConfigAndStatisticsTests(unittest.TestCase):
    def test_fixed_configs_validate(self) -> None:
        validate_bounded_config(load_json(BOUNDED_CONFIG))
        validate_joint_config(load_json(JOINT_CONFIG))

    def test_L3_E_is_rejected(self) -> None:
        config = load_json(BOUNDED_CONFIG)
        config["representations"][-1] = "L3-E"
        with self.assertRaises(ValueError):
            validate_bounded_config(config)

    def test_parent_event_primitive_cannot_be_used_as_L3_U(self) -> None:
        config = load_json(BOUNDED_CONFIG)
        config["l3_u"]["primitive_object"] = "scalar_parent_event_arrival"
        with self.assertRaises(ValueError):
            validate_bounded_config(config)

    def test_predeclared_worst_case_precision_is_satisfied(self) -> None:
        bounded = load_json(BOUNDED_CONFIG)["monte_carlo"]
        trials = len(bounded["batch_seeds"]) * bounded["trials_per_seed"]
        self.assertLessEqual(
            worst_case_wilson_half_width(trials, bounded["confidence_level"]),
            bounded["max_wilson_half_width"],
        )
        low, high = wilson_interval(trials // 2, trials, bounded["confidence_level"])
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_small_end_to_end_execution_preserves_all_hard_invariants(self) -> None:
        bounded = copy.deepcopy(load_json(BOUNDED_CONFIG))
        bounded["monte_carlo"].update(
            {
                "batch_seeds": [1, 2],
                "trials_per_seed": 2,
                "total_trials_per_aggregate": 4,
                "max_wilson_half_width": 1.0,
            }
        )
        bounded_result = run_bounded(bounded)
        self.assertEqual(bounded_result["invariants"]["l0_l1_mismatches"], 0)
        self.assertTrue(
            all(
                item["first_moment_equal"]
                for item in bounded_result["invariants"]["l3_u_first_moment_calibrations"]
            )
        )

        joint = copy.deepcopy(load_json(JOINT_CONFIG))
        joint["common"]["monte_carlo"].update(
            {
                "batch_seeds": [1, 2],
                "trials_per_seed": 2,
                "total_trials_per_aggregate": 4,
                "max_wilson_half_width": 1.0,
                "max_paired_delta_half_width": 1.0,
            }
        )
        joint["common"]["analytical_sanity_tolerance"] = 1.0
        joint_result = run_joint_discriminator(joint)
        self.assertTrue(joint_result["invariants"]["derived_per_word_l2_inputs_identical"])
        self.assertTrue(joint_result["invariants"]["joint_association_differs"])


if __name__ == "__main__":
    unittest.main()
