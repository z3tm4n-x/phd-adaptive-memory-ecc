"""Independent, test-only physical-event oracle for EXP-001.

This module deliberately imports no production simulator objects.  It accepts
plain objects exposing the physical-event fields and independently implements
the fixed physical mappings, state updates, scrub ordering and DEC-001 first
passage used by the validation tests.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class OracleTransition:
    time: float
    kind: str
    parent_id: str | None
    state: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class OracleResult:
    e_cap: bool
    first_passage_time: float | None
    final_state: tuple[tuple[int, ...], ...]
    transition_trace: tuple[OracleTransition, ...]


def map_physical_cell(
    physical_cell: int,
    *,
    mapping_kind: str,
    word_count: int,
    bits_per_word: int,
) -> tuple[int, int]:
    """Apply either fixed 8x8-capable mapping from its declared formula."""

    total_cells = word_count * bits_per_word
    if not 0 <= physical_cell < total_cells:
        raise ValueError(f"physical cell {physical_cell} is outside A")
    if mapping_kind == "contiguous_words":
        return physical_cell // bits_per_word, physical_cell % bits_per_word
    if mapping_kind == "round_robin_words":
        return physical_cell % word_count, physical_cell // word_count
    raise ValueError(f"unknown mapping kind: {mapping_kind}")


def _snapshot(state: Sequence[set[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(sorted(word_bits)) for word_bits in state)


def _is_exceeded(
    state: Sequence[set[int]], correction_capability: Sequence[int]
) -> bool:
    return any(
        len(word_bits) > correction_capability[word]
        for word, word_bits in enumerate(state)
    )


def _scrub_times(
    *, period: float, phase_origin: float, t0: float, end: float
) -> tuple[float, ...]:
    if period <= 0:
        raise ValueError("scrub period must be positive")
    first_index = math.floor((t0 - phase_origin) / period) + 1
    index = max(first_index, 1)
    tolerance = 1e-12 * max(1.0, abs(end))
    result: list[float] = []
    while True:
        scrub_time = phase_origin + index * period
        if scrub_time > end + tolerance:
            break
        if scrub_time > t0 + tolerance:
            result.append(scrub_time)
        index += 1
    return tuple(result)


def simulate_physical_stream(
    *,
    word_count: int,
    bits_per_word: int,
    correction_capability: Sequence[int],
    mapping_kind: str,
    physical_events: Sequence[object],
    initial_state: Mapping[int, Iterable[int]] | None,
    scrub_period: float,
    scrub_phase_origin: float,
    scrub_transition: str,
    event_at_boundary: str,
    t0: float,
    duration: float,
    bit_update_semantics: str,
) -> OracleResult:
    """Process physical marks directly and return the complete transition trace."""

    if word_count <= 0 or bits_per_word <= 0:
        raise ValueError("word_count and bits_per_word must be positive")
    if len(correction_capability) != word_count:
        raise ValueError("one correction capability is required per word")
    if any(value < 0 for value in correction_capability):
        raise ValueError("correction capability cannot be negative")
    if duration < 0:
        raise ValueError("reporting duration cannot be negative")
    if scrub_transition != "clear_all_erroneous_bits":
        raise ValueError("the test oracle supports only the declared full reset")
    if event_at_boundary != "scrub_then_event":
        raise ValueError("the test oracle supports only scrub_then_event ordering")
    if bit_update_semantics not in {"toggle", "set_error"}:
        raise ValueError(f"unknown bit-update semantics: {bit_update_semantics}")

    state = [set() for _ in range(word_count)]
    if initial_state is not None:
        for word, bits in initial_state.items():
            if not 0 <= word < word_count:
                raise ValueError(f"initial-state word {word} is outside A")
            for bit in bits:
                if not 0 <= bit < bits_per_word:
                    raise ValueError(f"initial-state bit {bit} is outside word {word}")
                state[word].add(bit)

    end = t0 + duration
    first_passage = t0 if _is_exceeded(state, correction_capability) else None
    transitions: list[tuple[float, int, str, object | None]] = []
    for scrub_time in _scrub_times(
        period=scrub_period,
        phase_origin=scrub_phase_origin,
        t0=t0,
        end=end,
    ):
        transitions.append((scrub_time, 0, "scrub", None))
    for event in physical_events:
        event_time = float(getattr(event, "time"))
        if t0 <= event_time <= end:
            transitions.append((event_time, 1, "event", event))
    transitions.sort(
        key=lambda item: (
            item[0],
            item[1],
            str(getattr(item[3], "parent_id")) if item[3] is not None else "",
        )
    )

    trace: list[OracleTransition] = []
    for transition_time, _, kind, event in transitions:
        if kind == "scrub":
            for word_bits in state:
                word_bits.clear()
            parent_id = None
        else:
            assert event is not None
            parent_id = str(getattr(event, "parent_id"))
            physical_cells = tuple(int(cell) for cell in getattr(event, "physical_cells"))
            if len(set(physical_cells)) != len(physical_cells):
                raise ValueError("one physical parent mark must contain distinct cells")
            logical_cells = [
                map_physical_cell(
                    cell,
                    mapping_kind=mapping_kind,
                    word_count=word_count,
                    bits_per_word=bits_per_word,
                )
                for cell in physical_cells
            ]
            if len(set(logical_cells)) != len(logical_cells):
                raise ValueError("the declared mapping is not one-to-one for this mark")
            for word, bit in logical_cells:
                if bit_update_semantics == "toggle":
                    if bit in state[word]:
                        state[word].remove(bit)
                    else:
                        state[word].add(bit)
                else:
                    state[word].add(bit)
            if first_passage is None and _is_exceeded(state, correction_capability):
                first_passage = transition_time

        trace.append(
            OracleTransition(
                time=transition_time,
                kind=kind,
                parent_id=parent_id,
                state=_snapshot(state),
            )
        )

    return OracleResult(
        e_cap=first_passage is not None,
        first_passage_time=first_passage,
        final_state=_snapshot(state),
        transition_trace=tuple(trace),
    )
