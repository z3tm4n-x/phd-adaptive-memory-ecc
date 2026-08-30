from __future__ import annotations

import sys
import unittest
from pathlib import Path


SIMULATION_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIMULATION_ROOT / "src"))

from exp001.model import (  # noqa: E402
    MemorySpec,
    PeriodicScrub,
    PhysicalEvent,
    PhysicalMapping,
    physical_to_joint,
    simulate_joint_events,
    simulate_physical_events,
)


class DeterministicStateSemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = MemorySpec.homogeneous(2, 4, 1)
        self.mapping = PhysicalMapping("contiguous", "contiguous_words", self.memory)
        self.no_scrub = PeriodicScrub(10.0)

    def simulate(self, events, *, scrub=None, initial=None, trace=True):
        return simulate_physical_events(
            memory=self.memory,
            mapping=self.mapping,
            events=events,
            initial_state=initial,
            scrub=scrub or self.no_scrub,
            t0=0.0,
            duration=2.0,
            bit_update_semantics="toggle",
            record_trace=trace,
        )

    def test_single_event_trace(self) -> None:
        event = PhysicalEvent("p0", 0.5, (0,), "single_cell")
        result = self.simulate((event,))
        self.assertFalse(result.e_cap)
        self.assertEqual(result.final_state, ((0,), ()))
        self.assertEqual(result.transition_trace[-1].parent_id, "p0")

    def test_two_event_accumulation(self) -> None:
        events = (
            PhysicalEvent("p0", 0.5, (0,), "single_cell"),
            PhysicalEvent("p1", 0.75, (1,), "single_cell"),
        )
        result = self.simulate(events)
        self.assertTrue(result.e_cap)
        self.assertEqual(result.first_passage_time, 0.75)
        self.assertEqual(result.final_state, ((0, 1), ()))

    def test_repeat_hit_toggle_semantics(self) -> None:
        events = (
            PhysicalEvent("p0", 0.5, (0,), "single_cell"),
            PhysicalEvent("p1", 0.75, (0,), "single_cell"),
        )
        result = self.simulate(events)
        self.assertFalse(result.e_cap)
        self.assertEqual(result.final_state, ((), ()))
        self.assertEqual(result.transition_trace[0].state, ((0,), ()))
        self.assertEqual(result.transition_trace[1].state, ((), ()))

    def test_immediate_e_cap_from_one_parent_mark(self) -> None:
        event = PhysicalEvent("p0", 0.25, (0, 1), "compact_multi_cell")
        result = self.simulate((event,))
        self.assertTrue(result.e_cap)
        self.assertEqual(result.first_passage_time, 0.25)

    def test_scrub_boundary_is_scrub_then_event(self) -> None:
        events = (
            PhysicalEvent("p0", 0.5, (0,), "single_cell"),
            PhysicalEvent("p1", 1.0, (1,), "single_cell"),
        )
        result = self.simulate(events, scrub=PeriodicScrub(1.0))
        self.assertFalse(result.e_cap)
        self.assertEqual(result.final_state, ((), ()))  # second scrub occurs at t=2
        at_one = [record for record in result.transition_trace if record.time == 1.0]
        self.assertEqual([record.kind for record in at_one], ["scrub", "event"])
        self.assertEqual(at_one[0].state, ((), ()))
        self.assertEqual(at_one[1].state, ((1,), ()))

    def test_initial_capability_exceedance_is_at_t0(self) -> None:
        result = self.simulate((), initial={0: (0, 1)})
        self.assertTrue(result.e_cap)
        self.assertEqual(result.first_passage_time, 0.0)

    def test_exact_l0_l1_state_event_and_trace_equivalence(self) -> None:
        events = (
            PhysicalEvent("p0", 0.25, (0, 5), "spatially_separated"),
            PhysicalEvent("p1", 1.0, (1, 4), "spatially_separated"),
            PhysicalEvent("p2", 1.5, (0,), "single_cell"),
        )
        l1_events = tuple(physical_to_joint(event, self.mapping) for event in events)
        common = dict(
            memory=self.memory,
            initial_state={1: (3,)},
            scrub=PeriodicScrub(1.0),
            t0=0.0,
            duration=2.0,
            bit_update_semantics="toggle",
            record_trace=True,
        )
        l0 = simulate_physical_events(mapping=self.mapping, events=events, **common)
        l1 = simulate_joint_events(events=l1_events, **common)
        self.assertEqual(l0, l1)


if __name__ == "__main__":
    unittest.main()
