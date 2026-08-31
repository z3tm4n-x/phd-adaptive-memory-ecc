"""Small, dependency-free statistical utilities for Bernoulli outputs."""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist


@dataclass
class BinaryAccumulator:
    trials: int = 0
    successes: int = 0
    disagreements: int = 0

    def add(self, value: bool, disagreement: bool = False) -> None:
        self.trials += 1
        self.successes += int(value)
        self.disagreements += int(disagreement)


@dataclass
class PairedDifferenceAccumulator:
    trials: int = 0
    total: float = 0.0
    total_squares: float = 0.0
    positive: int = 0
    negative: int = 0

    def add(self, candidate: bool, reference: bool) -> None:
        value = float(int(candidate) - int(reference))
        self.trials += 1
        self.total += value
        self.total_squares += value * value
        self.positive += int(value > 0)
        self.negative += int(value < 0)


def z_value(confidence_level: float) -> float:
    if not 0 < confidence_level < 1:
        raise ValueError("confidence level must lie strictly between zero and one")
    return NormalDist().inv_cdf(0.5 + confidence_level / 2.0)


def wilson_interval(
    successes: int, trials: int, confidence_level: float
) -> tuple[float, float]:
    if trials <= 0:
        raise ValueError("Wilson interval requires at least one trial")
    if not 0 <= successes <= trials:
        raise ValueError("success count is outside [0, trials]")
    z = z_value(confidence_level)
    estimate = successes / trials
    z2_over_n = z * z / trials
    denominator = 1.0 + z2_over_n
    centre = (estimate + z2_over_n / 2.0) / denominator
    half_width = (
        z
        * math.sqrt(estimate * (1.0 - estimate) / trials + z * z / (4.0 * trials * trials))
        / denominator
    )
    return max(0.0, centre - half_width), min(1.0, centre + half_width)


def wilson_half_width(successes: int, trials: int, confidence_level: float) -> float:
    low, high = wilson_interval(successes, trials, confidence_level)
    return (high - low) / 2.0


def worst_case_wilson_half_width(trials: int, confidence_level: float) -> float:
    return wilson_half_width(trials // 2, trials, confidence_level)


def paired_normal_interval(
    accumulator: PairedDifferenceAccumulator, confidence_level: float
) -> tuple[float, float, float]:
    if accumulator.trials <= 1:
        raise ValueError("paired interval requires at least two trials")
    count = accumulator.trials
    mean = accumulator.total / count
    sample_variance = max(
        0.0,
        (accumulator.total_squares - count * mean * mean) / (count - 1),
    )
    half_width = z_value(confidence_level) * math.sqrt(sample_variance / count)
    return mean, max(-1.0, mean - half_width), min(1.0, mean + half_width)
