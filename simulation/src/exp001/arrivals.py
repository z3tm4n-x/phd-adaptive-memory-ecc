"""Synthetic HPP and deterministic piecewise-constant NHPP scenarios."""

from __future__ import annotations

import copy
import random
from typing import Mapping, Sequence


def validate_arrival_scenario(scenario: Mapping[str, object], t0: float, end: float) -> None:
    kind = scenario.get("kind")
    units = scenario.get("intensity_units")
    if units != "parent_events_per_arbitrary_time_unit_over_A":
        raise ValueError("parent-arrival intensity units must be explicit over A")
    if kind == "hpp_constant":
        if float(scenario["rate"]) < 0:
            raise ValueError("HPP rate cannot be negative")
        return
    if kind != "piecewise_constant_nhpp":
        raise ValueError(f"unsupported arrival scenario: {kind}")
    segments = list(scenario["segments"])
    if not segments:
        raise ValueError("NHPP requires at least one segment")
    cursor = t0
    for segment in segments:
        start = float(segment["start"])
        stop = float(segment["end"])
        rate = float(segment["rate"])
        if abs(start - cursor) > 1e-12 or stop <= start or rate < 0:
            raise ValueError("NHPP segments must be contiguous, ordered and non-negative")
        cursor = stop
    if abs(cursor - end) > 1e-12:
        raise ValueError("NHPP segments must cover the complete reporting window")


def generate_arrival_times(
    scenario: Mapping[str, object], rng: random.Random, t0: float, end: float
) -> tuple[float, ...]:
    validate_arrival_scenario(scenario, t0, end)
    kind = scenario["kind"]
    if kind == "hpp_constant":
        return _generate_hpp_interval(float(scenario["rate"]), rng, t0, end)

    result: list[float] = []
    for segment in scenario["segments"]:
        result.extend(
            _generate_hpp_interval(
                float(segment["rate"]),
                rng,
                float(segment["start"]),
                float(segment["end"]),
            )
        )
    return tuple(result)


def _generate_hpp_interval(
    rate: float, rng: random.Random, start: float, end: float
) -> tuple[float, ...]:
    if rate == 0:
        return ()
    time_value = start
    result: list[float] = []
    while True:
        time_value += rng.expovariate(rate)
        if time_value > end:
            break
        result.append(time_value)
    return tuple(result)


def integrated_intensity(scenario: Mapping[str, object], t0: float, end: float) -> float:
    validate_arrival_scenario(scenario, t0, end)
    if scenario["kind"] == "hpp_constant":
        return float(scenario["rate"]) * (end - t0)
    return sum(
        float(segment["rate"])
        * (float(segment["end"]) - float(segment["start"]))
        for segment in scenario["segments"]
    )


def first_moment_l3u_scenario(
    parent_scenario: Mapping[str, object], expected_upsets_per_parent: float
) -> dict[str, object]:
    """Scale intensity only for the declared first-moment L3-U calibration.

    This operation does not assert stochastic-process equivalence.  The caller
    must generate an independent ungrouped-upset process.
    """

    if expected_upsets_per_parent < 0:
        raise ValueError("expected multiplicity cannot be negative")
    result = copy.deepcopy(dict(parent_scenario))
    result["intensity_units"] = "ungrouped_upsets_per_arbitrary_time_unit_over_A"
    if result["kind"] == "hpp_constant":
        result["rate"] = float(result["rate"]) * expected_upsets_per_parent
    else:
        for segment in result["segments"]:
            segment["rate"] = float(segment["rate"]) * expected_upsets_per_parent
    return result


def generate_l3u_arrival_times(
    scenario: Mapping[str, object], rng: random.Random, t0: float, end: float
) -> tuple[float, ...]:
    if scenario.get("intensity_units") != "ungrouped_upsets_per_arbitrary_time_unit_over_A":
        raise ValueError("L3-U intensity must use ungrouped-upset units over A")
    kind = scenario["kind"]
    if kind == "hpp_constant":
        return _generate_hpp_interval(float(scenario["rate"]), rng, t0, end)
    if kind != "piecewise_constant_nhpp":
        raise ValueError(f"unsupported L3-U temporal scenario: {kind}")
    result: list[float] = []
    for segment in scenario["segments"]:
        result.extend(
            _generate_hpp_interval(
                float(segment["rate"]),
                rng,
                float(segment["start"]),
                float(segment["end"]),
            )
        )
    return tuple(result)


def integrated_l3u_intensity(scenario: Mapping[str, object], t0: float, end: float) -> float:
    if scenario.get("intensity_units") != "ungrouped_upsets_per_arbitrary_time_unit_over_A":
        raise ValueError("L3-U intensity must use ungrouped-upset units over A")
    if scenario["kind"] == "hpp_constant":
        return float(scenario["rate"]) * (end - t0)
    return sum(
        float(segment["rate"])
        * (float(segment["end"]) - float(segment["start"]))
        for segment in scenario["segments"]
    )
