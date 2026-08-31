from __future__ import annotations

import inspect
import random
import sys
import unittest
from pathlib import Path


SIMULATION_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SIMULATION_ROOT / "src"))
sys.path.insert(0, str(TEST_ROOT))

import independent_l0_oracle as oracle_module  # noqa: E402
from independent_l0_oracle import (  # noqa: E402
    OracleResult,
    map_physical_cell,
    simulate_physical_stream,
)
from exp001.model import (  # noqa: E402
    JointImpactEvent,
    MemorySpec,
    PeriodicScrub,
    PhysicalEvent,
    PhysicalMapping,
    WordImpact,
    simulate_joint_events,
    simulate_physical_events,
)
from exp001.representations import convert_l0_to_l1  # noqa: E402


def _trace_signature(records) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (record.time, record.kind, record.parent_id, record.state) for record in records
    )


def _physical_cell(kind: str, word: int, bit: int, memory: MemorySpec) -> int:
    if kind == "contiguous_words":
        return word * memory.bits_per_word + bit
    if kind == "round_robin_words":
        return bit * memory.word_count + word
    raise ValueError(kind)


class IndependentL0OracleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = MemorySpec.homogeneous(8, 8, 1)

    def assert_production_paths_match_oracle(
        self,
        *,
        mapping_kind: str,
        events: tuple[PhysicalEvent, ...],
        initial_state=None,
        scrub: PeriodicScrub | None = None,
        t0: float = 0.0,
        duration: float = 2.0,
        semantics: str = "toggle",
    ) -> tuple[OracleResult, object, object]:
        mapping = PhysicalMapping(mapping_kind, mapping_kind, self.memory)
        scrub = scrub or PeriodicScrub(10.0)
        expected = simulate_physical_stream(
            word_count=self.memory.word_count,
            bits_per_word=self.memory.bits_per_word,
            correction_capability=self.memory.correction_capability,
            mapping_kind=mapping_kind,
            physical_events=events,
            initial_state=initial_state,
            scrub_period=scrub.period,
            scrub_phase_origin=scrub.phase_origin,
            scrub_transition=scrub.transition,
            event_at_boundary=scrub.event_at_boundary,
            t0=t0,
            duration=duration,
            bit_update_semantics=semantics,
        )
        common = {
            "memory": self.memory,
            "initial_state": initial_state,
            "scrub": scrub,
            "t0": t0,
            "duration": duration,
            "bit_update_semantics": semantics,
            "record_trace": True,
        }
        production_l0 = simulate_physical_events(
            mapping=mapping,
            events=events,
            **common,
        )
        production_l1 = simulate_joint_events(
            events=convert_l0_to_l1(events, mapping),
            **common,
        )

        for label, actual in (("production L0", production_l0), ("production L1", production_l1)):
            with self.subTest(path=label, mapping=mapping_kind, semantics=semantics):
                self.assertEqual(actual.e_cap, expected.e_cap)
                self.assertEqual(actual.first_passage_time, expected.first_passage_time)
                self.assertEqual(actual.final_state, expected.final_state)
                self.assertEqual(
                    _trace_signature(actual.transition_trace),
                    _trace_signature(expected.transition_trace),
                )
        return expected, production_l0, production_l1

    def test_oracle_source_is_independent_of_production_mapping_and_updates(self) -> None:
        source = inspect.getsource(oracle_module)
        forbidden = (
            "physical_to_joint",
            "convert_l0_to_l1",
            "PhysicalMapping.map_cells",
            "simulate_joint_events",
            "simulate_physical_events",
            "_apply_joint_event",
        )
        for name in forbidden:
            with self.subTest(forbidden=name):
                self.assertNotIn(name, source)
        self.assertNotIn("from exp001", source)
        self.assertNotIn("import exp001", source)

    def test_exhaustive_single_cell_mapping_over_fixed_8x8_domain(self) -> None:
        for mapping_kind in ("contiguous_words", "round_robin_words"):
            mapping = PhysicalMapping(mapping_kind, mapping_kind, self.memory)
            for physical_cell in range(self.memory.total_cells):
                with self.subTest(mapping=mapping_kind, physical_cell=physical_cell):
                    expected_logical = map_physical_cell(
                        physical_cell,
                        mapping_kind=mapping_kind,
                        word_count=self.memory.word_count,
                        bits_per_word=self.memory.bits_per_word,
                    )
                    event = PhysicalEvent(
                        f"cell-{physical_cell:02d}",
                        0.25,
                        (physical_cell,),
                        "single_cell",
                    )
                    converted = convert_l0_to_l1((event,), mapping)
                    actual_logical = (
                        converted[0].impacts[0].word,
                        converted[0].impacts[0].bits[0],
                    )
                    self.assertEqual(actual_logical, expected_logical)
                    self.assert_production_paths_match_oracle(
                        mapping_kind=mapping_kind,
                        events=(event,),
                        duration=0.5,
                    )

    def test_clean_single_multi_repeat_toggle_and_immediate_exceedance(self) -> None:
        events = (
            PhysicalEvent("single-set", 0.20, (0,), "single_cell"),
            PhysicalEvent("repeat-clear", 0.40, (0,), "single_cell"),
            PhysicalEvent("multi", 0.75, (0, 1, 8), "compact_multi_cell"),
        )
        for mapping_kind in ("contiguous_words", "round_robin_words"):
            expected, _, _ = self.assert_production_paths_match_oracle(
                mapping_kind=mapping_kind,
                events=events,
            )
            self.assertEqual(expected.transition_trace[0].state, ((0,), (), (), (), (), (), (), ()))
            self.assertEqual(expected.transition_trace[1].state, ((), (), (), (), (), (), (), ()))
            self.assertTrue(expected.e_cap)
            self.assertEqual(expected.first_passage_time, 0.75)

    def test_nonclean_start_and_sequential_accumulation(self) -> None:
        for mapping_kind in ("contiguous_words", "round_robin_words"):
            first = _physical_cell(mapping_kind, 2, 1, self.memory)
            second = _physical_cell(mapping_kind, 2, 2, self.memory)
            events = (
                PhysicalEvent("first", 0.25, (first,), "single_cell"),
                PhysicalEvent("second", 0.50, (second,), "single_cell"),
            )
            expected, _, _ = self.assert_production_paths_match_oracle(
                mapping_kind=mapping_kind,
                events=events,
                initial_state={0: (7,)},
            )
            self.assertTrue(expected.e_cap)
            self.assertEqual(expected.first_passage_time, 0.50)

    def test_set_error_repeat_is_idempotent_and_fresh_bit_exceeds(self) -> None:
        for mapping_kind in ("contiguous_words", "round_robin_words"):
            first = _physical_cell(mapping_kind, 4, 3, self.memory)
            second = _physical_cell(mapping_kind, 4, 4, self.memory)
            events = (
                PhysicalEvent("set", 0.20, (first,), "single_cell"),
                PhysicalEvent("repeat", 0.40, (first,), "single_cell"),
                PhysicalEvent("fresh", 0.60, (second,), "single_cell"),
            )
            expected, _, _ = self.assert_production_paths_match_oracle(
                mapping_kind=mapping_kind,
                events=events,
                semantics="set_error",
            )
            self.assertEqual(expected.transition_trace[0].state, expected.transition_trace[1].state)
            self.assertTrue(expected.e_cap)
            self.assertEqual(expected.first_passage_time, 0.60)

    def test_initial_capability_exceedance_is_first_passage_at_t0(self) -> None:
        for mapping_kind in ("contiguous_words", "round_robin_words"):
            expected, _, _ = self.assert_production_paths_match_oracle(
                mapping_kind=mapping_kind,
                events=(),
                initial_state={1: (0, 1)},
            )
            self.assertTrue(expected.e_cap)
            self.assertEqual(expected.first_passage_time, 0.0)

    def test_scrub_boundary_complete_trace_is_scrub_then_event(self) -> None:
        for mapping_kind in ("contiguous_words", "round_robin_words"):
            first = _physical_cell(mapping_kind, 0, 0, self.memory)
            boundary = _physical_cell(mapping_kind, 0, 1, self.memory)
            events = (
                PhysicalEvent("before", 0.50, (first,), "single_cell"),
                PhysicalEvent("boundary", 1.00, (boundary,), "single_cell"),
            )
            expected, _, _ = self.assert_production_paths_match_oracle(
                mapping_kind=mapping_kind,
                events=events,
                scrub=PeriodicScrub(1.0),
            )
            at_boundary = [item for item in expected.transition_trace if item.time == 1.0]
            self.assertEqual([item.kind for item in at_boundary], ["scrub", "event"])
            self.assertEqual(at_boundary[0].state, ((), (), (), (), (), (), (), ()))
            self.assertEqual(at_boundary[1].state[0], (1,))
            self.assertFalse(expected.e_cap)

    def test_bounded_randomized_streams_match_complete_oracle_traces(self) -> None:
        initial_states = (None, {0: (0,), 3: (1,)})
        semantics_values = ("toggle", "set_error")
        for seed in range(16):
            rng = random.Random(91_000 + seed)
            events: list[PhysicalEvent] = []
            for ordinal in range(18):
                if ordinal < 2:
                    event_time = 1.0
                elif ordinal == 2:
                    event_time = 2.0
                else:
                    event_time = rng.uniform(0.0, 4.0)
                multiplicity = rng.randint(1, 4)
                cells = tuple(sorted(rng.sample(range(self.memory.total_cells), multiplicity)))
                events.append(
                    PhysicalEvent(
                        f"random-{ordinal:02d}",
                        event_time,
                        cells,
                        "bounded_random",
                    )
                )
            physical_stream = tuple(events)
            for mapping_kind in ("contiguous_words", "round_robin_words"):
                for initial_state in initial_states:
                    for semantics in semantics_values:
                        with self.subTest(
                            seed=seed,
                            mapping=mapping_kind,
                            initial=initial_state is not None,
                            semantics=semantics,
                        ):
                            self.assert_production_paths_match_oracle(
                                mapping_kind=mapping_kind,
                                events=physical_stream,
                                initial_state=initial_state,
                                scrub=PeriodicScrub(1.0),
                                duration=4.0,
                                semantics=semantics,
                            )

    def test_mutant_conversion_passes_joint_simulator_but_oracle_rejects_it(self) -> None:
        mapping_kind = "round_robin_words"
        event = PhysicalEvent("sentinel", 0.5, (8,), "single_cell")
        expected, _, _ = self.assert_production_paths_match_oracle(
            mapping_kind=mapping_kind,
            events=(event,),
            initial_state={0: (0,)},
            duration=1.0,
        )

        # Intentional mutation: apply the contiguous formula while declaring the
        # round-robin mapping.  The resulting L1 object is structurally valid and
        # the production joint simulator accepts it.
        wrong_word, wrong_bit = divmod(event.physical_cells[0], self.memory.bits_per_word)
        mutant_event = JointImpactEvent(
            parent_id=event.parent_id,
            time=event.time,
            impacts=(WordImpact(word=wrong_word, bits=(wrong_bit,)),),
        )
        mutant_result = simulate_joint_events(
            memory=self.memory,
            events=(mutant_event,),
            initial_state={0: (0,)},
            scrub=PeriodicScrub(10.0),
            t0=0.0,
            duration=1.0,
            bit_update_semantics="toggle",
            record_trace=True,
        )

        self.assertFalse(mutant_result.e_cap)
        self.assertTrue(expected.e_cap)
        self.assertNotEqual(
            _trace_signature(mutant_result.transition_trace),
            _trace_signature(expected.transition_trace),
        )


if __name__ == "__main__":
    unittest.main()
