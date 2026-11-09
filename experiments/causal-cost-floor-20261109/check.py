"""Lower bounds on lifetime protective reads for arbitrary causal controls, 0.25 MiB."""
import argparse
import json
from fractions import Fraction
from pathlib import Path

EXPERIMENTS = Path(__file__).resolve().parents[1]
INPUTS = EXPERIMENTS / "c1-common-geo-20261109"
W = 65536
BIT_PAIR = Fraction(38, 78)
EPSILON = Fraction(1, 1000)
APERTURE = Fraction(124, 10**9) * Fraction(100001, 100000) + Fraction(3, 2 * 10**9)
BUS_READ = Fraction(48, 10**9) * Fraction(99999, 100000) - Fraction(1, 2 * 10**9)


def plateau_floor(mission, plateau, word_peak, word_background):
    exposure = Fraction(0)
    correction = Fraction(0)
    block_words = Fraction(0)
    # A two-aperture gap between evidence blocks prevents double charging a read.
    for duration, block, word_rate in (
        (plateau, Fraction(1), word_peak),
        (mission - plateau, Fraction(3600), word_background),
    ):
        blocks = duration // (block + 2 * APERTURE)
        empty = 1 - W * word_rate * block
        assert empty > 0
        weight = blocks * (1 - EPSILON) * empty
        exposure += W * weight * word_rate * (block + APERTURE)
        correction += 2 * BIT_PAIR * W * APERTURE * weight * word_rate**2 * (block + APERTURE)
        block_words += W * weight
    return BIT_PAIR * exposure**2 / (EPSILON + correction) - block_words


def unknown_start_floor(mission, bit_factor, background, peak, growth, quota, mass):
    groups = 900
    height = Fraction(1, 32)
    hold = Fraction(500)
    hot_probability = Fraction(1, 2)
    ramp = height / growth
    slot = ramp + hold
    slots_per_group = (mission / groups) // (slot + 2 * APERTURE)
    extra = height * (hold + ramp / 2)
    assert groups * height <= quota and groups * extra <= mass and background + height <= peak
    assert slots_per_group > 0
    total_hot = W * bit_factor * (background * slot + extra)
    assert 0 < total_hot < 64
    empty_hot = (1 - total_hot / 64)**64  # <= exp(-total_hot)
    empty_quiet = 1 - W * bit_factor * background * slot
    assert empty_quiet > 0
    rate_on_hold = bit_factor * (background + height)
    weight = hot_probability * groups * (1 - EPSILON) * empty_hot * BIT_PAIR * rate_on_hold**2

    # This integer already suffices. Test the inequality without rounding any inputs.
    visits = 47543
    free_squares = max(0, W * hold - visits * APERTURE)**2 / (W + visits)
    assert weight * free_squares > EPSILON
    return (1 - hot_probability) * empty_quiet * groups * slots_per_group * (1 - EPSILON) * visits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=INPUTS)
    inputs = parser.parse_args().inputs
    six = json.loads((inputs / "six.json").read_text(encoding="utf-8"))
    coverage = json.loads((inputs / "coverage.json").read_text(encoding="utf-8"))
    mission = Fraction(six["T"])
    background = Fraction(coverage["b_s_inv"])
    peak = Fraction(coverage["B_s_inv"])
    bit_factor = Fraction(39, six["D"])
    mass = Fraction(six["F"])
    plateau = mass / (peak - background)
    quota = Fraction("28.855")
    growth = Fraction("0.004392116")
    assert peak - background < quota
    fixed_row = next(r for r in six["rows"] if r["W"] == W and Fraction(r["epsilon"]) == EPSILON)
    fixed_lower = Fraction(fixed_row["necessary"]["bus_lower_percent"])
    cases = {
        "initial plateau and background": plateau_floor(mission, plateau, bit_factor * peak,
                                                       bit_factor * background),
        "unknown starts of bounded rises": unknown_start_floor(mission, bit_factor, background, peak,
                                                               growth, quota, mass),
    }
    for label, reads in cases.items():
        seconds = reads * BUS_READ
        percent = 100 * seconds / mission
        print(f"{label}: {float(seconds):.6f} s, {float(percent):.12f}% bus, "
              f"{float(percent / fixed_lower):.9f} of fixed-class lower bound")


if __name__ == "__main__":
    main()
