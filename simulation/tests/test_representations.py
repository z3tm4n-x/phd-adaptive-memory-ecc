from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path


SIMULATION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIMULATION_ROOT / "src"))

from exp001.arrivals import (  # noqa: E402
    first_moment_l3u_scenario,
    integrated_intensity,
    integrated_l3u_intensity,
)
from exp001.config import load_json, validate_joint_config  # noqa: E402
from exp001.model import (  # noqa: E402
    MemorySpec,
    PeriodicScrub,
    PhysicalMapping,
    simulate_joint_events,
    simulate_physical_events,
)
from exp001.representations import (  # noqa: E402
    convert_l0_to_l1,
    derive_l2_marginals,
    expected_event_multiplicity,
    generate_physical_events,
    j_model_marginals,
    joint_pair_invariants,
)


REPO_ROOT = SIMULATION_ROOT.parent


class RepresentationTests(unittest.TestCase):
    def test_W_variants_reverse_compact_and_separated_concentration(self) -> None:
        memory = MemorySpec.homogeneous(8, 8, 1)
        contiguous = PhysicalMapping("contiguous", "contiguous_words", memory)
        interleaved = PhysicalMapping("interleaved", "round_robin_words", memory)
        compact = (0, 1, 2)
        separated = (0, 8, 16)
        self.assertEqual([len(x.bits) for x in contiguous.map_cells(compact)], [3])
        self.assertEqual([len(x.bits) for x in interleaved.map_cells(compact)], [1, 1, 1])
        self.assertEqual([len(x.bits) for x in contiguous.map_cells(separated)], [1, 1, 1])
        self.assertEqual([len(x.bits) for x in interleaved.map_cells(separated)], [3])

    def test_J_A_J_B_invariants_are_exact_and_machine_checked(self) -> None:
        config = load_json(
            REPO_ROOT / "simulation" / "configs" / "EXP-001" / "joint-discriminator.json"
        )
        invariants = validate_joint_config(config)
        self.assertTrue(invariants["all_words_have_impact_probability_one_half"])
        self.assertTrue(invariants["exactly_two_words_impacted_per_event"])
        self.assertTrue(invariants["derived_per_word_l2_inputs_identical"])
        self.assertTrue(invariants["joint_association_differs"])
        self.assertTrue(invariants["no_other_model_parameter_differs"])
        self.assertEqual(
            invariants["model_details"]["J-A"]["per_word_impact_probability"],
            ["1/2"] * 4,
        )
        self.assertEqual(
            invariants["model_details"]["J-B"]["per_word_impact_probability"],
            ["1/2"] * 4,
        )
        self.assertEqual(
            j_model_marginals(config, "J-A").fingerprint,
            j_model_marginals(config, "J-B").fingerprint,
        )
        self.assertEqual(
            invariants["derived_l2_fingerprint"],
            j_model_marginals(config, "J-A").fingerprint,
        )

    def test_exact_marginals_normalize(self) -> None:
        config = load_json(
            REPO_ROOT / "simulation" / "configs" / "EXP-001" / "bounded-phase1.json"
        )
        memory = MemorySpec.homogeneous(8, 8, 1)
        topology = config["topology_scenarios"][1]
        for mapping_config in config["mappings"]:
            mapping = PhysicalMapping(mapping_config["name"], mapping_config["kind"], memory)
            marginals = derive_l2_marginals(memory, mapping, topology)
            for pmf in marginals.word_pmfs:
                self.assertAlmostEqual(sum(probability for _, probability in pmf), 1.0)

    def test_L3_U_first_moment_calibration_not_parent_rate_substitution(self) -> None:
        parent = {
            "name": "test",
            "kind": "hpp_constant",
            "rate": 0.75,
            "intensity_units": "parent_events_per_arbitrary_time_unit_over_A",
        }
        l3 = first_moment_l3u_scenario(parent, 3.0)
        self.assertEqual(l3["rate"], 2.25)
        self.assertNotEqual(l3["intensity_units"], parent["intensity_units"])
        self.assertAlmostEqual(
            integrated_l3u_intensity(l3, 0.0, 4.0),
            integrated_intensity(parent, 0.0, 4.0) * 3.0,
        )

    def test_randomized_L0_L1_equivalence_under_both_W(self) -> None:
        memory = MemorySpec.homogeneous(8, 8, 1)
        topology = {
            "name": "mixed-test",
            "classes": [
                {"kind": "single_cell", "multiplicity": 1, "probability": 0.25},
                {"kind": "compact_multi_cell", "multiplicity": 3, "probability": 0.5},
                {
                    "kind": "spatially_separated",
                    "multiplicity": 3,
                    "stride": 8,
                    "probability": 0.25,
                },
            ],
        }
        for seed in range(50):
            times = tuple(sorted(random.Random(seed).uniform(0.0, 4.0) for _ in range(6)))
            physical = generate_physical_events(
                arrival_times=times,
                memory=memory,
                topology_scenario=topology,
                rng=random.Random(seed + 1000),
            )
            for kind in ("contiguous_words", "round_robin_words"):
                mapping = PhysicalMapping(kind, kind, memory)
                l1_events = convert_l0_to_l1(physical, mapping)
                common = dict(
                    memory=memory,
                    initial_state={0: (0,), 3: (1,)},
                    scrub=PeriodicScrub(1.0),
                    t0=0.0,
                    duration=4.0,
                    bit_update_semantics="toggle",
                    record_trace=True,
                )
                l0 = simulate_physical_events(mapping=mapping, events=physical, **common)
                l1 = simulate_joint_events(events=l1_events, **common)
                self.assertEqual(l0, l1)


if __name__ == "__main__":
    unittest.main()
