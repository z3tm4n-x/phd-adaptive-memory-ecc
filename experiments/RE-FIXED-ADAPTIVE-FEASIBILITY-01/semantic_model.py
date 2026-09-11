#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class WordState:
    nbits: int = 39
    errors: set[int] = field(default_factory=set)
    first_cap_time: Optional[float] = None
    pending_corrected_image: Optional[set[int]] = None
    correction_pending: bool = False

    def _record_cap(self, t: float) -> None:
        if len(self.errors) > 1 and self.first_cap_time is None:
            self.first_cap_time = t

    def inject_toggle(self, bit: int, t: float) -> None:
        if not (0 <= bit < self.nbits):
            raise ValueError('bit out of range')
        if bit in self.errors:
            self.errors.remove(bit)
        else:
            self.errors.add(bit)
        self._record_cap(t)

    def read_and_decode(self, t: float) -> str:
        self._record_cap(t)
        if len(self.errors) == 0:
            self.pending_corrected_image = None
            self.correction_pending = False
            return 'clean'
        if len(self.errors) == 1:
            self.pending_corrected_image = set()
            self.correction_pending = True
            return 'correctable'
        self.pending_corrected_image = None
        self.correction_pending = False
        return 'uncorrectable'

    def complete_conditional_write(self, t: float) -> bool:
        if not self.correction_pending:
            return False
        self.errors = set(self.pending_corrected_image or set())
        self.pending_corrected_image = None
        self.correction_pending = False
        return True

@dataclass
class PassState:
    word_count: int
    next_index: int = 0
    correction_count: int = 0
    completed: bool = False
    snapshot_count: Optional[int] = None

    def commit_word(self, corrected_write_completed: bool) -> None:
        if self.completed:
            raise RuntimeError('pass already complete')
        if corrected_write_completed:
            self.correction_count += 1
        self.next_index += 1
        if self.next_index == self.word_count:
            self.completed = True
            self.snapshot_count = self.correction_count

@dataclass(frozen=True)
class Command:
    arrival_time: float
    requested_period: float

@dataclass
class CommandEndpoint:
    fallback_period: float
    deadline: float

    def choose(self, command: Optional[Command]) -> tuple[str, float]:
        if command is None or command.arrival_time > self.deadline:
            return 'fallback', self.fallback_period
        return 'command', command.requested_period

@dataclass(frozen=True)
class Op:
    kind: str
    start: float
    duration: float

    @property
    def end(self) -> float:
        return self.start + self.duration

@dataclass
class WordBoundaryArbiter:
    app_word_s: float
    scrub_grab_s: float

    def dispatch_scrub(self, due: float, active_app: Optional[Op]) -> Op:
        start = due
        if active_app is not None and active_app.start <= due < active_app.end:
            start = active_app.end
        return Op('scrub', start, self.scrub_grab_s)

    def release_envelope(self, interval_s: float, min_release_spacing_s: float) -> float:
        rho = self.scrub_grab_s / min_release_spacing_s
        return self.scrub_grab_s + rho * interval_s
