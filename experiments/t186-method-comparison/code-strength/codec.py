"""Functional external codecs from accepted T187; no timing/RTL claim."""
from importlib.util import module_from_spec, spec_from_file_location
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = spec_from_file_location("t187_model", ROOT / "experiments/t187-code-strength/model.py")
t187 = module_from_spec(spec)
spec.loader.exec_module(t187)


class Code:
    """Systematic encoder and dense syndrome-to-error-mask reference decoder.

    Physical coordinates remain the T187 H-column order. Data occupy the
    non-pivot coordinates; parity occupies the greedy independent columns.
    Decoding beyond the correction radius has no correctness guarantee.
    """

    def __init__(self, t):
        self.t = t
        self.columns = t187.columns(t)
        self.n = len(self.columns)
        self.r = t187.rank(self.columns)
        self.k = self.n - self.r
        self.mask = (1 << self.n) - 1
        pivots, chosen = {}, []
        for index, column in enumerate(self.columns):
            x, combo = column, 1 << index
            while x:
                lead = x.bit_length() - 1
                if lead not in pivots:
                    pivots[lead] = (x, combo)
                    chosen.append(index)
                    break
                old, old_combo = pivots[lead]
                x ^= old
                combo ^= old_combo
        self.parity_positions = tuple(chosen)
        self.data_positions = tuple(i for i in range(self.n) if i not in chosen)

        def solve(target):
            out = 0
            while target:
                x, combo = pivots[target.bit_length() - 1]
                target ^= x
                out ^= combo
            return out

        self.generator = tuple((1 << i) ^ solve(self.columns[i]) for i in self.data_positions)
        self.table = [None] * (1 << self.r)
        self.table[0] = 0
        for weight in range(1, t + 1):
            for indices in combinations(range(self.n), weight):
                error = sum(1 << i for i in indices)
                syndrome = self.syndrome(error)
                if self.table[syndrome] is not None:
                    raise ArithmeticError("correctable syndromes collide")
                self.table[syndrome] = error

    def syndrome(self, word):
        if not isinstance(word, int) or not 0 <= word <= self.mask:
            raise ValueError("n-bit codeword required; padding must be removed")
        result = 0
        while word:
            low = word & -word
            result ^= self.columns[low.bit_length() - 1]
            word ^= low
        return result

    def encode(self, data):
        if not isinstance(data, int) or not 0 <= data < 1 << self.k:
            raise ValueError("k-bit payload required")
        word = 0
        while data:
            low = data & -data
            word ^= self.generator[low.bit_length() - 1]
            data ^= low
        return word

    def decode(self, word):
        error = self.table[self.syndrome(word)]
        if error is None:
            return {"status": "unmapped_syndrome", "data": None, "corrected_word": None}
        corrected = word ^ error
        data = sum(((corrected >> pos) & 1) << j for j, pos in enumerate(self.data_positions))
        return {"status": "correctable_syndrome", "data": data,
                "corrected_word": corrected, "ERR": bool(error),
                "error_mask": error, "guarantee": "only for errors of weight <= t"}

    def pack16(self, word):
        self.syndrome(word)  # Check the word width; do not silently drop code bits.
        return tuple((word >> (16 * i)) & 65535 for i in range((self.n + 15) // 16))

    def unpack16(self, beats):
        if len(beats) != (self.n + 15) // 16 or any(type(x) is not int or not 0 <= x <= 65535 for x in beats):
            raise ValueError("one x16 beat per physical address required")
        return sum(x << (16 * i) for i, x in enumerate(beats)) & self.mask

    def resources(self):
        # Unshared, balanced XOR trees are one explicit logical architecture,
        # not a minimum circuit or mapped FPGA resource count.
        syndrome_fanin = [sum((x >> j) & 1 for x in self.columns) for j in range(self.r)]
        parity_fanin = [sum((x >> pos) & 1 for x in self.generator) for pos in self.parity_positions]
        depth = lambda rows: max(((x - 1).bit_length() for x in rows if x), default=0)
        return dict(n=self.n, k=self.k, t=self.t, parity_bits=self.r,
                    data_positions=list(self.data_positions), parity_positions=list(self.parity_positions),
                    generator_columns=list(self.generator), check_columns=list(self.columns),
                    syndrome_two_input_xors=sum(max(0, x - 1) for x in syndrome_fanin),
                    syndrome_xor_depth=depth(syndrome_fanin),
                    encoder_two_input_xors=sum(max(0, x - 1) for x in parity_fanin),
                    encoder_xor_depth=depth(parity_fanin), correction_two_input_xors=self.n,
                    lookup_entries=1 << self.r, correctable_entries=sum(x is not None for x in self.table),
                    lookup_width_bits=self.n + 1, lookup_bits=(1 << self.r) * (self.n + 1),
                    lookup_bytes=((1 << self.r) * (self.n + 1) + 7) // 8,
                    architecture="dense syndrome ROM: n-bit mask plus valid bit; unshared XOR trees",
                    hardware_LUT=None, hardware_BRAM=None, decode_ns=None, encode_ns=None,
                    software_operation_time=None, measured=False)
