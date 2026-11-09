"""Necessary bus time with a common fully unavailable correction report."""
import argparse
import json
from fractions import Fraction as F
from math import ceil
from pathlib import Path

INPUTS = Path(__file__).resolve().parents[1] / "c1-common-geo-20261109"
WORDS = 65536
EPSILON = F(1, 1000)
QUOTA = F("28.855")
GROWTH = F("0.004392116")
CLOCK_LO = F(99999, 100000)
CLOCK_HI = F(100001, 100000)
JITTER = F(1, 2 * 10**9)
APERTURE = F(124, 10**9) * CLOCK_HI + 3 * JITTER
MIN_READ = F(48, 10**9) * CLOCK_LO - JITTER
NOMINAL_READ = F(48, 10**9)


def visit_floor(duration, pieces, word_rate):
    """Largest k excluded as a weighted average number of word visits on one plateau."""
    mesh = F(160)
    coefficient = F(38, 78) * (1 - word_rate * mesh) * word_rate**2
    assert duration <= mesh * pieces and coefficient > 0
    length = WORDS * duration
    offset = WORDS * pieces + coefficient * length**2

    def excluded(visits):
        free = max(0, length - visits * APERTURE)
        return (1 - EPSILON) * coefficient * free**2 > EPSILON * (visits + offset)

    lower, upper = 0, 1
    assert excluded(lower)
    while excluded(upper):
        upper *= 2
    while upper - lower > 1:
        middle = (lower + upper) // 2
        if excluded(middle):
            lower = middle
        else:
            upper = middle
    assert excluded(lower) and not excluded(upper)
    return lower


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=INPUTS)
    inputs = parser.parse_args().inputs
    six = json.loads((inputs / "six.json").read_text(encoding="utf-8"))
    coverage = json.loads((inputs / "coverage.json").read_text(encoding="utf-8"))
    mission = F(six["T"])
    exposure = F(six["F"])
    background, peak = (F(coverage[key]) for key in ("b_s_inv", "B_s_inv"))
    height = peak - background
    ramp = height / GROWTH

    windows = 2256
    width = mission / windows
    duration = width - 2 * APERTURE
    assert width > ramp and height <= QUOTA
    assert height * (duration + ramp / 2) <= exposure
    assert height * (duration + APERTURE) <= exposure  # initial plateau starts at t=0
    cuts = ceil(duration / 160)
    visits = visit_floor(duration, cuts, 39 * peak / six["D"])
    reads = windows * (1 - EPSILON) * visits
    seconds = MIN_READ * reads
    pct = 100 * seconds / mission

    row = next(r for r in six["rows"] if r["W"] == WORDS and F(r["epsilon"]) == EPSILON)
    fixed_lo = F(row["necessary"]["bus_lower_s"])
    fixed_hi = F(row["candidate"]["price"]["bus"]["upper_s"])
    assert pct > F("5.11122457") and seconds > fixed_hi / 2
    print(f"{windows} alternative laws, plateau {float(duration):.9f} s, {cuts} subdivisions")
    print(f"per-window visit test k={visits}, lower bus {float(seconds):.8f} s, "
          f"{float(pct):.10f} %, ratio to fixed lower {float(seconds / fixed_lo):.8f}")
    print(f"half of fixed candidate upper {float(fixed_hi / 2):.8f} s")

    # Separate stronger cost convention: nominal execution and the full fixed control reserve.
    frames = ceil((mission + 2 * JITTER) / (F(1568, 10**9) * CLOCK_LO)) + 2
    reserve = frames * (F(64, 10**9) * CLOCK_HI + JITTER)
    half_all_slots = (fixed_hi + reserve) / 2
    nominal = NOMINAL_READ * reads
    assert nominal > half_all_slots
    print(f"nominal-only branch: lower {float(nominal):.8f} s, half with all fixed "
          f"control slots {float(half_all_slots):.8f} s, margin "
          f"{float(nominal - half_all_slots):.8f} s")


if __name__ == "__main__":
    main()
