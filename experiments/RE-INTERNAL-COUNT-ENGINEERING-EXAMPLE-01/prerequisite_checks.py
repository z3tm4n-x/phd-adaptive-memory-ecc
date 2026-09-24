"""Addressed full-codeword checks, NOT the five-policy experiment.

No imports from RES-003, RADAR, NumPy or the production simulator.
The code is shortened extended Hamming (39,32), not a bit-compatible
implementation of a particular vendor's BCH encoder.
"""
from fractions import Fraction
from functools import reduce
from itertools import combinations
import operator

PARITY = (1, 2, 4, 8, 16, 32)
DATA = tuple(p for p in range(1, 39) if p not in PARITY)
CHECK = PARITY + (39,)


def encode(data):
    if not 0 <= data < 2**32:
        raise ValueError("32 information bits required")
    word = sum(((data >> k) & 1) << (p - 1) for k, p in enumerate(DATA))
    for p in PARITY:
        bit = sum((word >> (j - 1)) & 1 for j in range(1, 39) if j & p) % 2
        word |= bit << (p - 1)
    word |= (word.bit_count() % 2) << 38
    return word


def decode(word):
    """Return corrected stored word, correction count, DED indication.

    Outside weights 0,1,2 no decoder guarantee is asserted. E_cap must be
    recorded from the error trajectory, not inferred from this indication.
    """
    if not 0 <= word < 2**39:
        raise ValueError("39 protected bits required")
    syndrome = reduce(operator.xor, (j for j in range(1, 39)
                                    if word & (1 << (j - 1))), 0)
    odd = word.bit_count() % 2
    if odd:
        position = syndrome or 39
        if position > 39:
            return word, 0, True
        return word ^ (1 << (position - 1)), 1, False
    return word, 0, bool(syndrome)


def check_matrix_oracle(word):
    """Independent seven parity equations, without encode/decode helpers."""
    bits = [(word // (2**j)) % 2 for j in range(39)]
    rows = [sum(bits[j] * (((j + 1) // (2**r)) % 2)
                for j in range(38)) % 2 for r in range(6)]
    rows.append(sum(bits) % 2)
    return tuple(rows)


def physical_trace(events, checks, delay, horizon, initial=0):
    """One-word direct coded-memory executor, times are exact integers.

    Event/check/commit ordering at equal times is event before check before
    commit. This is a declared test convention, not a hardware assertion.
    Corrected writes store a snapshot; clean reads cause no write.
    Count is published on commit; an unfinished write contributes no count.
    """
    queue = [(t, 0, bit) for t, bit in events if t <= horizon]
    queue += [(t, 1, None) for t in checks if t <= horizon]
    word = initial
    count = 0
    first = 0 if word.bit_count() > 1 else None
    trace = []
    while queue:
        queue.sort(key=lambda x: (x[0], x[1]))
        t, kind, payload = queue.pop(0)
        if kind == 0:
            word ^= 1 << (payload - 1)
        elif kind == 1:
            fixed, corrected, ded = decode(word)
            if corrected and not ded and t + delay <= horizon:
                queue.append((t + delay, 2, fixed))
        else:
            word = payload
            count += 1
        if word.bit_count() > 1 and first is None:
            first = t
        trace.append((t, kind, word, count, first))
    return trace


def set_oracle(events, checks, delay, horizon, initial=0):
    """Independent test oracle: sets, weight-based SEC, no syndrome decoder.

    Only the zero transmitted codeword is used for execution fixtures.
    For >1 errors, freeze correction; first-passage stays recorded.
    This matches the direct decoder only through the first E_cap.
    """
    bad = {j + 1 for j in range(39) if initial // 2**j % 2}
    first = 0 if len(bad) > 1 else None
    count = 0
    pending = []
    out = []
    for t in range(horizon + 1):
        for when, bit in events:
            if when == t:
                bad.symmetric_difference_update({bit})
                if len(bad) > 1 and first is None:
                    first = t
                out.append((t, 0, sum(2**(j - 1) for j in bad), count, first))
        for when in checks:
            if when == t:
                if len(bad) == 1 and t + delay <= horizon:
                    pending.append(t + delay)
                out.append((t, 1, sum(2**(j - 1) for j in bad), count, first))
        while t in pending:
            pending.remove(t)
            bad = set()
            count += 1
            out.append((t, 2, 0, count, first))
    return out


def normalization(words, per_bit_rate):
    """Equal susceptibility is an explicit premise, not a device claim."""
    return dict(information_bits=32 * words, protected_bits=39 * words,
                array_arrivals_per_second=39 * words * per_bit_rate,
                coding_overhead=Fraction(7, 32))


def window_guard(rate_upper, words, window_lengths):
    """Compensator/union upper under uniform independent word marks.

    Each supplied window belongs to one word; windows must be predictable
    with an independently justified intensity upper. Overlap only makes
    this upper more conservative. No parameter here is a project requirement.
    """
    if words < 1 or rate_upper < 0 or any(x < 0 for x in window_lengths):
        raise ValueError("invalid guard inputs")
    return min(Fraction(1), Fraction(rate_upper) * sum(window_lengths) / words)


def exhaustive_results():
    patterns = [0, 2**32 - 1, 0xAAAAAAAA, 0x55555555] + [1 << j for j in range(32)]
    singles = doubles = 0
    for data in patterns:
        clean = encode(data)
        assert check_matrix_oracle(clean) == (0,) * 7
        for bit in range(39):
            assert decode(clean ^ (1 << bit)) == (clean, 1, False)
            singles += 1
        for a, b in combinations(range(39), 2):
            assert decode(clean ^ (1 << a) ^ (1 << b))[1:] == (0, True)
            doubles += 1
    # Exhausting error locations is sufficient for every data value by linearity.
    return dict(data_patterns=len(patterns), single_error_checks=singles,
                double_error_checks=doubles, protected_positions=39,
                parity_positions_counted=len(CHECK))
