"""Core state and transition semantics for EXP-001.

All state updates are defined on distinct erroneous logical bit cells.  A
parent event is simultaneous: every bit update in its mark is applied before
``E_cap`` is evaluated.  A periodic global scrub is the explicit Phase-1
approximation and clears every erroneous bit.  At an exact scrub boundary the
scrub transition precedes the event transition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class MemorySpec:
    """Declared homogeneous/partition-ready memory protection domain ``A``."""

    word_count: int
    bits_per_word: int
    correction_capability: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.word_count <= 0 or self.bits_per_word <= 0:
            raise ValueError("word_count and bits_per_word must be positive")
        if len(self.correction_capability) != self.word_count:
            raise ValueError("one correction capability is required per word")
        if any(value < 0 for value in self.correction_capability):
            raise ValueError("correction capability cannot be negative")

    @classmethod
    def homogeneous(
        cls, word_count: int, bits_per_word: int, correction_capability: int
    ) -> "MemorySpec":
        return cls(
            word_count=word_count,
            bits_per_word=bits_per_word,
            correction_capability=(correction_capability,) * word_count,
        )

    @property
    def total_cells(self) -> int:
        return self.word_count * self.bits_per_word


@dataclass(frozen=True)
class PhysicalMapping:
    """Deterministic physical-cell-to-logical-bit mapping ``W``."""

    name: str
    kind: str
    memory: MemorySpec

    def map_cell(self, physical_cell: int) -> tuple[int, int]:
        if not 0 <= physical_cell < self.memory.total_cells:
            raise ValueError(f"physical cell {physical_cell} is outside A")
        if self.kind == "contiguous_words":
            return divmod(physical_cell, self.memory.bits_per_word)
        if self.kind == "round_robin_words":
            word = physical_cell % self.memory.word_count
            bit = physical_cell // self.memory.word_count
            return word, bit
        raise ValueError(f"unknown mapping kind: {self.kind}")

    def map_cells(self, physical_cells: Iterable[int]) -> tuple["WordImpact", ...]:
        by_word: dict[int, list[int]] = {}
        seen: set[tuple[int, int]] = set()
        for physical_cell in physical_cells:
            logical = self.map_cell(physical_cell)
            if logical in seen:
                raise ValueError("W must not map one physical mark to duplicate logical cells")
            seen.add(logical)
            by_word.setdefault(logical[0], []).append(logical[1])
        return tuple(
            WordImpact(word=word, bits=tuple(sorted(bits)))
            for word, bits in sorted(by_word.items())
        )


@dataclass(frozen=True)
class PhysicalEvent:
    """L0 event: parent provenance, epoch and pre-W physical topology."""

    parent_id: str
    time: float
    physical_cells: tuple[int, ...]
    topology_class: str

    def __post_init__(self) -> None:
        if len(set(self.physical_cells)) != len(self.physical_cells):
            raise ValueError("one parent-event topology must contain distinct cells")


@dataclass(frozen=True)
class WordImpact:
    word: int
    bits: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(set(self.bits)) != len(self.bits):
            raise ValueError("a word impact must contain distinct logical bits")


@dataclass(frozen=True)
class JointImpactEvent:
    """L1-compatible joint mark or one L3-U primitive arrival.

    ``primitive_kind`` is deliberately explicit.  L3-U events use
    ``ungrouped_upset`` and never masquerade as scalar parent events.
    """

    parent_id: str
    time: float
    impacts: tuple[WordImpact, ...]
    primitive_kind: str = "parent_event"

    def __post_init__(self) -> None:
        words = [impact.word for impact in self.impacts]
        if len(words) != len(set(words)):
            raise ValueError("a joint mark must contain at most one impact per word")
        if self.primitive_kind not in {"parent_event", "ungrouped_upset"}:
            raise ValueError(f"unsupported primitive kind: {self.primitive_kind}")


@dataclass(frozen=True)
class PeriodicScrub:
    period: float
    phase_origin: float = 0.0
    transition: str = "clear_all_erroneous_bits"
    event_at_boundary: str = "scrub_then_event"

    def __post_init__(self) -> None:
        if self.period <= 0:
            raise ValueError("scrub period must be positive")
        if self.transition != "clear_all_erroneous_bits":
            raise ValueError("Phase 1 implements only the declared global clear transition")
        if self.event_at_boundary != "scrub_then_event":
            raise ValueError("Phase 1 requires explicit scrub_then_event boundary ordering")

    def times(self, t0: float, end: float) -> tuple[float, ...]:
        # The first scrub is strictly after t0.  Multiplication avoids cumulative
        # floating-point drift from repeatedly adding the period.
        first_index = int((t0 - self.phase_origin) // self.period) + 1
        result: list[float] = []
        index = max(first_index, 1)
        tolerance = 1e-12 * max(1.0, abs(end))
        while True:
            value = self.phase_origin + index * self.period
            if value > end + tolerance:
                break
            if value > t0 + tolerance:
                result.append(value)
            index += 1
        return tuple(result)


@dataclass(frozen=True)
class TransitionRecord:
    time: float
    kind: str
    parent_id: str | None
    state: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class SimulationResult:
    e_cap: bool
    first_passage_time: float | None
    final_state: tuple[tuple[int, ...], ...]
    transition_trace: tuple[TransitionRecord, ...]

    def equivalence_signature(self) -> tuple[object, ...]:
        return self.e_cap, self.first_passage_time, self.final_state


def physical_to_joint(event: PhysicalEvent, mapping: PhysicalMapping) -> JointImpactEvent:
    return JointImpactEvent(
        parent_id=event.parent_id,
        time=event.time,
        impacts=mapping.map_cells(event.physical_cells),
        primitive_kind="parent_event",
    )


def _normalise_initial_state(
    memory: MemorySpec,
    initial_state: Mapping[int, Iterable[int]] | None,
) -> list[set[int]]:
    state = [set() for _ in range(memory.word_count)]
    if initial_state is None:
        return state
    for word, bits in initial_state.items():
        if not 0 <= word < memory.word_count:
            raise ValueError(f"initial-state word {word} is outside A")
        for bit in bits:
            if not 0 <= bit < memory.bits_per_word:
                raise ValueError(f"initial-state bit {bit} is outside word {word}")
            state[word].add(bit)
    return state


def _snapshot(state: Sequence[set[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(sorted(bits)) for bits in state)


def _capability_exceeded(state: Sequence[set[int]], memory: MemorySpec) -> bool:
    return any(
        len(bits) > memory.correction_capability[word]
        for word, bits in enumerate(state)
    )


def _apply_joint_event(
    state: list[set[int]],
    event: JointImpactEvent,
    memory: MemorySpec,
    bit_update_semantics: str,
) -> None:
    for impact in event.impacts:
        if not 0 <= impact.word < memory.word_count:
            raise ValueError(f"event word {impact.word} is outside A")
        for bit in impact.bits:
            if not 0 <= bit < memory.bits_per_word:
                raise ValueError(f"event bit {bit} is outside word {impact.word}")
            if bit_update_semantics == "toggle":
                if bit in state[impact.word]:
                    state[impact.word].remove(bit)
                else:
                    state[impact.word].add(bit)
            elif bit_update_semantics == "set_error":
                state[impact.word].add(bit)
            else:
                raise ValueError(f"unknown bit-update semantics: {bit_update_semantics}")


def simulate_joint_events(
    *,
    memory: MemorySpec,
    events: Sequence[JointImpactEvent],
    initial_state: Mapping[int, Iterable[int]] | None,
    scrub: PeriodicScrub,
    t0: float,
    duration: float,
    bit_update_semantics: str,
    record_trace: bool = False,
) -> SimulationResult:
    """Evaluate DEC-001 first passage over the closed reporting window."""

    if duration < 0:
        raise ValueError("reporting duration cannot be negative")
    end = t0 + duration
    state = _normalise_initial_state(memory, initial_state)
    first_passage = t0 if _capability_exceeded(state, memory) else None
    trace: list[TransitionRecord] = []

    transitions: list[tuple[float, int, str, JointImpactEvent | None]] = []
    for scrub_time in scrub.times(t0, end):
        transitions.append((scrub_time, 0, "scrub", None))
    for event in events:
        if t0 <= event.time <= end:
            transitions.append((event.time, 1, "event", event))
    transitions.sort(key=lambda item: (item[0], item[1], item[3].parent_id if item[3] else ""))

    for transition_time, _, kind, event in transitions:
        if kind == "scrub":
            for bits in state:
                bits.clear()
            parent_id = None
        else:
            assert event is not None
            _apply_joint_event(state, event, memory, bit_update_semantics)
            parent_id = event.parent_id
            if first_passage is None and _capability_exceeded(state, memory):
                first_passage = transition_time
        if record_trace:
            trace.append(
                TransitionRecord(
                    time=transition_time,
                    kind=kind,
                    parent_id=parent_id,
                    state=_snapshot(state),
                )
            )

    return SimulationResult(
        e_cap=first_passage is not None,
        first_passage_time=first_passage,
        final_state=_snapshot(state),
        transition_trace=tuple(trace),
    )


def simulate_physical_events(
    *,
    memory: MemorySpec,
    mapping: PhysicalMapping,
    events: Sequence[PhysicalEvent],
    initial_state: Mapping[int, Iterable[int]] | None,
    scrub: PeriodicScrub,
    t0: float,
    duration: float,
    bit_update_semantics: str,
    record_trace: bool = False,
) -> SimulationResult:
    """L0 path: apply ``W`` to every physical event before state update."""

    joint_events = tuple(physical_to_joint(event, mapping) for event in events)
    return simulate_joint_events(
        memory=memory,
        events=joint_events,
        initial_state=initial_state,
        scrub=scrub,
        t0=t0,
        duration=duration,
        bit_update_semantics=bit_update_semantics,
        record_trace=record_trace,
    )
