"""Independent local checks for PR294; no Q/cost cell or policy search."""
from fractions import Fraction as F
from pathlib import Path
import json
import math

HERE = Path(__file__).resolve().parent
c = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
e, s = c["environment"], c["service"]
n = c["bank"]["code"][0]
D = e["reference_positions"]

# Enumerate the event used for the lower bound: any first excess during
# exactly two singleton arrivals, starting clean or with one erroneous bit.
# All single-error initial states are equivalent by permutation symmetry.
for initial in (0, 1):
    failures = 0
    for first in range(n):
        middle = initial ^ (1 << first)
        for second in range(n):
            final = middle ^ (1 << second)
            failures += middle.bit_count() > 1 or final.bit_count() > 1
    assert F(failures, n * n) == F(n - 1, n)

# Obtain the moments by integrating independent linear segments, rather
# than evaluating the author's closed moment expression alone.
def linear_moments(length, left, right):
    return (length * (left + right) / 2,
            length * (left * left + left * right + right * right) / 3)

t = e["template"]
b, B, Fs = (F(e[k]) for k in ("b", "B", "Fs"))
count, width, rise = t["count"], t["width_s"], t["rise_s"]
T = c["bank"]["mission_s"]
amplitude = 2 * Fs / (count * width)
for alpha in map(F, e["alpha_axis"]):
    a = (1 - alpha) * amplitude
    segments = (
        (t["left_s"], b, b),
        (rise, b, b + a),
        (rise, b + a, b),
        (t["cycle_s"] - t["left_s"] - width, b, b),
    )
    moments = [linear_moments(*segment) for segment in segments]
    first = count * sum(x[0] for x in moments)
    second = count * sum(x[1] for x in moments)
    assert first - b * T == (1 - alpha) * Fs
    assert second == b * b * T + 2 * b * (1-alpha) * Fs + count*width*a*a/3
    R = B - b - a
    # The proposed residual plateau is admissible: its initial jump is
    # unconstrained, its only subsequent jump is down, and mass is Fr.
    assert R > 0 and F(e["rho"]) * F(e["ell"]) - a/rise > 0
    length = alpha * Fs / R
    assert 0 <= length <= T
    assert R * length == alpha * Fs

# Independent normalization from the singleton pair coefficient.
# Also check hold coverage beyond the kH=1 values in check_inputs.py.
ns = F(1, 10**9)
xm, xp, jitter = F(s["xi_minus"]), F(s["xi_plus"]), F(s["J_ns"]) * ns
quantum = s["timer_quantum_ticks"]
dE = 124 * xp * ns + 3 * jitter
for W in c["bank"]["words_axis"]:
    pair = W * F(n-1, 2*n) * F(n, D)**2
    assert pair == F(W * n * (n-1), 2 * D**2)
    for k in (1, 2, 3, 20, 1780, 4096, 2**32):
        period = 196*k*W*xp*ns + jitter
        ticks = quantum * math.ceil((period+dE+jitter)/(quantum*xm*ns))
        assert ticks*xm*ns-jitter >= period+dE
        assert (ticks-quantum)*xm*ns-jitter < period+dE

print("Two-arrival first-excess enumeration: OK (clean and one-error states)")
print("Independent piecewise integrals and residual plateau admissibility: OK")
print("Pair normalization and directed hold rounding: OK")
print("No Q/cost cells, simulations, old campaign or resource replay executed.")
