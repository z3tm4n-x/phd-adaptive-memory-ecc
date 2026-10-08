"""Independent test-only full38 E-envelope oracle, NOT a CY62167 transistor model.

No reference/RTL imports. An abstract error position has a birth time; on repair
we choose the allowed worst-residual realization retaining post-start errors.
This is one member of the conditional E contract, not proof of physical E.
Data is authoritative logical data, errors are separate. The six hidden check
positions are distinct positions, not a newly invented external code layout.
"""
from dataclasses import dataclass, field


@dataclass
class Word:
    data: int = 0
    errors: dict = field(default_factory=dict)
    first_exceedance: int | None = None

    def toggle(self, bit, at):
        if not 0 <= bit < 38:
            raise ValueError("not a protected position")
        if bit in self.errors:
            del self.errors[bit]
        else:
            self.errors[bit] = at
        if len(self.errors) >= 2 and self.first_exceedance is None:
            self.first_exceedance = at


class MemoryOracle:
    def __init__(self, words):
        self.words = [Word() for _ in range(words)]
        self.lock = None
        self.preobserved = False
        self.observed_err = False
        self.flags = []
        self.trace = []
        self.writes = set()

    def begin(self, transaction, word, at, kind):
        if self.lock is not None:
            raise ValueError("alias/global lock conflict")
        if kind not in ("control", "read32", "write32"):
            raise ValueError("unknown transaction")
        self.lock = (transaction, word, at, kind)
        self.preobserved = self.observed_err = False
        self.writes = set()
        self.trace.append((at, "accept", transaction, word))

    def observe(self, at):
        transaction, word, start, kind = self.lock
        if at != start + 60 or self.preobserved:
            raise ValueError("missing/duplicated coherent preobservation")
        self.preobserved = True
        self.observed_err = bool(self.words[word].errors)
        if self.observed_err and kind != "read32":
            self.flags.append((start + 64, transaction, word))
        self.trace.append((at, "observe", transaction, self.observed_err))
        return self.words[word].data, self.observed_err

    def write(self, at, alias, value, byte_enable=3, transaction_id=None):
        transaction, word, start, kind = self.lock
        if transaction_id is not None and transaction_id != transaction:
            raise ValueError("stale pending image")
        if not self.preobserved:
            raise ValueError("unobserved write loses ERR")
        expected = start + (132 if alias == 0 else 200)
        if alias not in (0, 1) or alias in self.writes or at != expected or kind == "read32" or (kind == "control" and
                (not self.observed_err or alias != 0)):
            raise ValueError("wrong write/epoch")
        self.writes.add(alias)
        w = self.words[word]
        # Conditional implementation may preserve new hits; NEVER assert clean
        # release from a clean latch. First exceedance is absorbing telemetry.
        w.errors = {bit: birth for bit, birth in w.errors.items() if birth >= start}
        if kind == "write32":
            for byte in range(2):
                if byte_enable & (1 << byte):
                    shift = 16 * alias + 8 * byte
                    w.data = ((w.data & ~(255 << shift))
                              | (((value >> (8 * byte)) & 255) << shift))
        self.trace.append((at, "write", transaction, alias, w.data))

    def release(self, at):
        transaction, word, start, kind = self.lock
        duration = (216 if kind == "write32" else 184 if kind == "read32"
                    else 148 if self.observed_err else 92)
        if not self.preobserved or at != start + duration:
            raise ValueError("early or unobserved completion")
        required = ({0, 1} if kind == "write32" else
                    {0} if kind == "control" and self.observed_err else set())
        if self.writes != required:
            raise ValueError("missing write before completion")
        self.trace.append((at, "release", transaction, word))
        self.lock = None

    def soft_reset(self):
        # Controller health changes elsewhere. Memory and pending are not reset.
        return self.lock
