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
    validate_joint_analytical_preconditions,
    validate_joint_config,
)
from exp001.experiment import (  # noqa: E402
    J_ANALYTICAL_VALIDITY_DOMAIN,
    j_conditional_survival_after_two,
    j_exact_decision_table,
    j_interval_survival,
    j_reporting_window_failure,
    run_bounded,
    run_joint_discriminator,
)
from exp001.model import MemorySpec  # noqa: E402
from exp001.representations import generate_j_events  # noqa: E402
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

    def test_declared_trial_total_must_equal_seed_product(self) -> None:
        config = load_json(JOINT_CONFIG)
        config["common"]["monte_carlo"]["total_trials_per_aggregate"] -= 1
        with self.assertRaisesRegex(ValueError, "total_trials_per_aggregate"):
            validate_joint_config(config)

    def test_all_configuration_level_J_analytical_preconditions_are_enforced(self) -> None:
        mutations = {
            "exactly four words": lambda value: value["common"]["domain"].update(
                {"word_count": 5}
            ),
            "t_c equals one": lambda value: value["common"]["domain"].update(
                {"ecc_correction_capability_distinct_bits": [1, 1, 0, 1]}
            ),
            "clean start": lambda value: value["common"]["initial_state"][
                "erroneous_logical_cells"
            ].append({"word": 0, "bit": 0}),
            "distinct in-range pair": lambda value: value["joint_models"][0]["subsets"].__setitem__(
                0, [0, 0]
            ),
            "full reset": lambda value: value["common"]["scrub"].update(
                {"transition": "partial_reset"}
            ),
            "boundary order": lambda value: value["common"]["scrub"].update(
                {"event_at_boundary": "event_then_scrub"}
            ),
            "phase alignment": lambda value: value["common"]["scrub"].update(
                {"phase_origin": 0.25}
            ),
            "complete reporting intervals": lambda value: value["common"][
                "reporting_window"
            ].update({"duration": 3.5}),
        }
        for label, mutate in mutations.items():
            with self.subTest(precondition=label):
                config = load_json(JOINT_CONFIG)
                mutate(config)
                with self.assertRaises(ValueError):
                    validate_joint_analytical_preconditions(config)

    def test_fresh_bit_capacity_is_enforced_before_analytical_use(self) -> None:
        memory = MemorySpec.homogeneous(4, 1, 1)
        with self.assertRaisesRegex(RuntimeError, "fresh-bit capacity exhausted"):
            generate_j_events(
                arrival_times=(0.1, 0.2),
                selection_uniforms=(0.1, 0.1),
                model={"name": "J-A", "subsets": [[0, 1], [2, 3]]},
                memory=memory,
            )

    def test_J_q_endpoints_interval_survival_and_reporting_failure_are_exact(self) -> None:
        config = load_json(JOINT_CONFIG)
        models = {item["name"]: item for item in config["joint_models"]}
        q_a = j_conditional_survival_after_two(models["J-A"]["subsets"])
        q_b = j_conditional_survival_after_two(models["J-B"]["subsets"])
        self.assertEqual(q_a, 0.5)
        self.assertAlmostEqual(q_b, 1.0 / 6.0, places=15)
        self.assertAlmostEqual(j_interval_survival(q_a, 0.25), 0.9856697410747468, places=15)
        self.assertAlmostEqual(j_interval_survival(q_b, 0.25), 0.9775572329177530, places=15)

        expected = {
            0.5: (0.10905397335118927, 0.16605473501960577),
            1.0: (0.19333885171048215, 0.27600173212563106),
            2.0: (0.3148651286146482, 0.4126072776188684),
            4.0: (0.4586588670535492, 0.5488823892112910),
        }
        for period, (expected_a, expected_b) in expected.items():
            intervals = int(round(4.0 / period))
            mean = 0.5 * period
            with self.subTest(period=period, model="J-A"):
                self.assertAlmostEqual(
                    j_reporting_window_failure(q_a, mean, intervals), expected_a, places=14
                )
            with self.subTest(period=period, model="J-B"):
                self.assertAlmostEqual(
                    j_reporting_window_failure(q_b, mean, intervals), expected_b, places=14
                )

    def test_complete_fourteen_condition_validity_domain_is_machine_recorded(self) -> None:
        self.assertEqual(
            [item["id"] for item in J_ANALYTICAL_VALIDITY_DOMAIN], list(range(1, 15))
        )
        conditions = " ".join(item["condition"] for item in J_ANALYTICAL_VALIDITY_DOMAIN)
        for required_term in (
            "i.i.d.",
            "independent of HPP event times and counts",
            "aligned with the scrub phase",
            "sufficient unused bit positions",
        ):
            with self.subTest(required_term=required_term):
                self.assertIn(required_term, conditions)

    def test_exact_J_decision_values_match_the_registered_table(self) -> None:
        rows = j_exact_decision_table(load_json(JOINT_CONFIG))
        selected = {
            row["epsilon"]: (
                row["exact_j_a_selected_period"],
                row["exact_j_b_selected_period"],
                row["robust_exact_over_q_interval_selected_period"],
            )
            for row in rows
        }
        self.assertEqual(
            selected,
            {
                0.02: (None, None, None),
                0.05: (None, None, None),
                0.1: (None, None, None),
                0.15: (0.5, None, None),
                0.25: (1.0, 0.5, 0.5),
                0.35: (2.0, 1.0, 1.0),
                0.45: (2.0, 2.0, 2.0),
                0.55: (4.0, 4.0, 4.0),
                0.65: (4.0, 4.0, 4.0),
            },
        )

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
        joint_result = run_joint_discriminator(joint)
        self.assertTrue(joint_result["invariants"]["derived_per_word_l2_inputs_identical"])
        self.assertTrue(joint_result["invariants"]["joint_association_differs"])
        self.assertTrue(
            joint_result["analytical_validation"]["configuration_and_runtime_preconditions"][
                "fresh_bit_capacity_validated_before_analytical_output"
            ]
        )


if __name__ == "__main__":
    unittest.main()
