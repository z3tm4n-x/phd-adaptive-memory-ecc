"""Config-driven bounded executions for EXP-001."""

from __future__ import annotations

import csv
import ctypes
import hashlib
import json
import math
import os
import platform
import random
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .arrivals import (
    first_moment_l3u_scenario,
    generate_arrival_times,
    generate_l3u_arrival_times,
    integrated_intensity,
    integrated_l3u_intensity,
)
from .config import (
    initial_state_from_config,
    memory_from_config,
    validate_bounded_config,
    validate_joint_config,
)
from .model import PeriodicScrub, PhysicalMapping, simulate_joint_events, simulate_physical_events
from .representations import (
    convert_l0_to_l1,
    derive_l2_marginals,
    derive_seed,
    expected_event_multiplicity,
    generate_j_events,
    generate_l3u_events,
    generate_physical_events,
    j_model_marginals,
    reconstruct_l2_independent_word_marginals,
)
from .statistics import (
    BinaryAccumulator,
    PairedDifferenceAccumulator,
    paired_normal_interval,
    wilson_interval,
)


def _scrub_from_config(config: Mapping[str, object], period: float) -> PeriodicScrub:
    return PeriodicScrub(
        period=period,
        phase_origin=float(config["phase_origin"]),
        transition=str(config["transition"]),
        event_at_boundary=str(config["event_at_boundary"]),
    )


def _timed_call(runtime: dict[str, float], label: str, function, **kwargs):
    start = time.perf_counter()
    result = function(**kwargs)
    runtime[label] += time.perf_counter() - start
    return result


def _row_key(
    mapping: str,
    topology: str,
    arrival: str,
    initial_state: str,
    scrub_period: float,
    representation: str,
) -> tuple[object, ...]:
    return mapping, topology, arrival, initial_state, scrub_period, representation


def _summary_row(
    *,
    key: tuple[object, ...],
    accumulator: BinaryAccumulator,
    confidence: float,
    precision_limit: float,
    l2_fingerprint: str | None,
    paired_disagreement_valid: bool,
) -> dict[str, object]:
    low, high = wilson_interval(accumulator.successes, accumulator.trials, confidence)
    half_width = (high - low) / 2.0
    mapping, topology, arrival, initial_state, scrub_period, representation = key
    return {
        "mapping": mapping,
        "topology_scenario": topology,
        "arrival_scenario": arrival,
        "initial_state": initial_state,
        "scrub_period": scrub_period,
        "representation": representation,
        "trials": accumulator.trials,
        "e_cap_count": accumulator.successes,
        "f_a": accumulator.successes / accumulator.trials,
        "ci_method": "wilson_score",
        "confidence_level": confidence,
        "ci_low": low,
        "ci_high": high,
        "ci_half_width": half_width,
        "precision_limit": precision_limit,
        "precision_satisfied": half_width <= precision_limit + 1e-15,
        "paired_disagreement_rate_vs_l1": (
            accumulator.disagreements / accumulator.trials
            if paired_disagreement_valid
            else None
        ),
        "l2_input_fingerprint": l2_fingerprint,
    }


def _add_reference_errors(rows: list[dict[str, object]]) -> None:
    references: dict[tuple[object, ...], dict[str, object]] = {}
    for row in rows:
        if row["representation"] == "L1":
            key = (
                row["mapping"],
                row["topology_scenario"],
                row["arrival_scenario"],
                row["initial_state"],
                row["scrub_period"],
            )
            references[key] = row
    for row in rows:
        key = (
            row["mapping"],
            row["topology_scenario"],
            row["arrival_scenario"],
            row["initial_state"],
            row["scrub_period"],
        )
        reference = references[key]
        signed = float(row["f_a"]) - float(reference["f_a"])
        row["signed_error_vs_l1"] = signed
        row["absolute_error_vs_l1"] = abs(signed)
        row["relative_error_vs_l1"] = (
            signed / float(reference["f_a"]) if float(reference["f_a"]) else None
        )


def _decision_rows(
    rows: Sequence[Mapping[str, object]],
    epsilon_grid: Sequence[float],
    duration: float,
) -> list[dict[str, object]]:
    groups: dict[tuple[object, ...], list[Mapping[str, object]]] = defaultdict(list)
    for row in rows:
        groups[
            (
                row["mapping"],
                row["topology_scenario"],
                row["arrival_scenario"],
                row["initial_state"],
            )
        ].append(row)

    output: list[dict[str, object]] = []
    for group_key, group_rows in sorted(groups.items()):
        representations = sorted({str(row["representation"]) for row in group_rows})
        by_rep = {
            representation: sorted(
                (row for row in group_rows if row["representation"] == representation),
                key=lambda row: float(row["scrub_period"]),
            )
            for representation in representations
        }
        for epsilon in epsilon_grid:
            reference_feasible = [
                float(row["scrub_period"])
                for row in by_rep["L1"]
                if float(row["ci_high"]) <= epsilon
            ]
            reference_selected = max(reference_feasible) if reference_feasible else None
            for representation in representations:
                feasible = [
                    float(row["scrub_period"])
                    for row in by_rep[representation]
                    if float(row["ci_high"]) <= epsilon
                ]
                selected = max(feasible) if feasible else None
                false_safe = sorted(set(feasible) - set(reference_feasible))
                false_conservative = sorted(set(reference_feasible) - set(feasible))
                scrub_operations = (
                    math.floor(duration / selected + 1e-12) if selected is not None else None
                )
                output.append(
                    {
                        "mapping": group_key[0],
                        "topology_scenario": group_key[1],
                        "arrival_scenario": group_key[2],
                        "initial_state": group_key[3],
                        "epsilon": epsilon,
                        "epsilon_status": "experiment_parameter_not_project_requirement",
                        "representation": representation,
                        "reference_representation": "L1",
                        "feasibility_rule": "wilson_ci_upper_le_epsilon",
                        "feasible_periods": json.dumps(feasible, separators=(",", ":")),
                        "reference_feasible_periods": json.dumps(
                            reference_feasible, separators=(",", ":")
                        ),
                        "selected_period": selected,
                        "reference_selected_period": reference_selected,
                        "selected_period_discrepancy": selected != reference_selected,
                        "selected_period_delta": (
                            selected - reference_selected
                            if selected is not None and reference_selected is not None
                            else None
                        ),
                        "false_safe_periods": json.dumps(false_safe, separators=(",", ":")),
                        "false_conservative_periods": json.dumps(
                            false_conservative, separators=(",", ":")
                        ),
                        "false_safe_decision": bool(false_safe),
                        "false_conservative_decision": bool(false_conservative),
                        "selected_scrub_operations_over_reporting_window": scrub_operations,
                    }
                )
    return output


def run_bounded(config: Mapping[str, object]) -> dict[str, object]:
    validate_bounded_config(config)
    memory = memory_from_config(config["domain"])
    t0 = float(config["reporting_window"]["t0"])
    duration = float(config["reporting_window"]["duration"])
    end = t0 + duration
    confidence = float(config["monte_carlo"]["confidence_level"])
    precision_limit = float(config["monte_carlo"]["max_wilson_half_width"])
    scrub_periods = [float(value) for value in config["candidate_scrub_periods"]]
    accumulators: dict[tuple[object, ...], BinaryAccumulator] = defaultdict(BinaryAccumulator)
    runtime: dict[str, float] = defaultdict(float)
    l2_fingerprints: dict[tuple[str, str], str] = {}
    calibration_checks: list[dict[str, object]] = []
    exact_checks = 0
    event_mark_checks = 0

    mappings = tuple(
        PhysicalMapping(
            name=str(mapping_config["name"]),
            kind=str(mapping_config["kind"]),
            memory=memory,
        )
        for mapping_config in config["mappings"]
    )
    l2_models = {
        (mapping.name, str(topology["name"])): derive_l2_marginals(
            memory, mapping, topology
        )
        for topology in config["topology_scenarios"]
        for mapping in mappings
    }
    l2_fingerprints.update(
        {key: marginals.fingerprint for key, marginals in l2_models.items()}
    )

    for topology in config["topology_scenarios"]:
        expected_multiplicity = expected_event_multiplicity(memory, topology)
        for arrival in config["arrival_scenarios"]:
            parent_expectation = integrated_intensity(arrival, t0, end)
            l3_scenario = first_moment_l3u_scenario(arrival, expected_multiplicity)
            l3_expectation = integrated_l3u_intensity(l3_scenario, t0, end)
            target = parent_expectation * expected_multiplicity
            calibration_checks.append(
                {
                    "topology_scenario": topology["name"],
                    "arrival_scenario": arrival["name"],
                    "parent_expected_count": parent_expectation,
                    "expected_upsets_per_parent": expected_multiplicity,
                    "l3_u_expected_ungrouped_upset_count": l3_expectation,
                    "calibration_target": target,
                    "first_moment_equal": math.isclose(
                        l3_expectation, target, rel_tol=0.0, abs_tol=1e-12
                    ),
                    "stochastic_process_equivalence_claimed": False,
                }
            )

            for batch_seed in config["monte_carlo"]["batch_seeds"]:
                for trial_index in range(int(config["monte_carlo"]["trials_per_seed"])):
                    stream_identity = (
                        config["experiment_id"],
                        topology["name"],
                        arrival["name"],
                        batch_seed,
                        trial_index,
                    )
                    arrival_times = generate_arrival_times(
                        arrival,
                        random.Random(derive_seed(*stream_identity, "parent-arrival")),
                        t0,
                        end,
                    )
                    physical_events = generate_physical_events(
                        arrival_times=arrival_times,
                        memory=memory,
                        topology_scenario=topology,
                        rng=random.Random(derive_seed(*stream_identity, "physical-mark")),
                    )
                    l3_times = generate_l3u_arrival_times(
                        l3_scenario,
                        random.Random(derive_seed(*stream_identity, "l3u-arrival")),
                        t0,
                        end,
                    )
                    l3_events = generate_l3u_events(
                        arrival_times=l3_times,
                        memory=memory,
                        rng=random.Random(derive_seed(*stream_identity, "l3u-allocation")),
                    )

                    for mapping in mappings:
                        l1_events = convert_l0_to_l1(physical_events, mapping)
                        event_mark_checks += len(physical_events)
                        marginals = l2_models[(mapping.name, str(topology["name"]))]
                        l2_events = reconstruct_l2_independent_word_marginals(
                            arrival_times=arrival_times,
                            memory=memory,
                            marginals=marginals,
                            rng=random.Random(derive_seed(*stream_identity, "l2-reconstruction")),
                            fresh_bit_allocation=False,
                        )

                        for initial_config in config["initial_states"]:
                            initial_state = initial_state_from_config(initial_config)
                            for scrub_period in scrub_periods:
                                scrub = _scrub_from_config(config["scrub"], scrub_period)
                                common_arguments = {
                                    "memory": memory,
                                    "initial_state": initial_state,
                                    "scrub": scrub,
                                    "t0": t0,
                                    "duration": duration,
                                    "bit_update_semantics": config["state_update"]["bit_update_semantics"],
                                    "record_trace": False,
                                }
                                l0_result = _timed_call(
                                    runtime,
                                    "L0",
                                    simulate_physical_events,
                                    mapping=mapping,
                                    events=physical_events,
                                    **common_arguments,
                                )
                                l1_result = _timed_call(
                                    runtime,
                                    "L1",
                                    simulate_joint_events,
                                    events=l1_events,
                                    **common_arguments,
                                )
                                if l0_result.equivalence_signature() != l1_result.equivalence_signature():
                                    raise AssertionError(
                                        "L0/L1 exact state/event equivalence failed; EXP-001 is invalid"
                                    )
                                exact_checks += 1
                                l2_result = _timed_call(
                                    runtime,
                                    "L2-independent_word_marginals",
                                    simulate_joint_events,
                                    events=l2_events,
                                    **common_arguments,
                                )
                                l3_result = _timed_call(
                                    runtime,
                                    "L3-U",
                                    simulate_joint_events,
                                    events=l3_events,
                                    **common_arguments,
                                )
                                outcomes = {
                                    "L0": l0_result,
                                    "L1": l1_result,
                                    "L2-independent_word_marginals": l2_result,
                                    "L3-U": l3_result,
                                }
                                for representation, result in outcomes.items():
                                    key = _row_key(
                                        mapping.name,
                                        str(topology["name"]),
                                        str(arrival["name"]),
                                        str(initial_config["name"]),
                                        scrub_period,
                                        representation,
                                    )
                                    accumulators[key].add(
                                        result.e_cap,
                                        disagreement=(
                                            result.e_cap != l1_result.e_cap
                                            if representation
                                            in {"L0", "L1", "L2-independent_word_marginals"}
                                            else False
                                        ),
                                    )

    if not all(item["first_moment_equal"] for item in calibration_checks):
        raise AssertionError("L3-U first-moment calibration invariant failed")

    rows: list[dict[str, object]] = []
    for key, accumulator in sorted(accumulators.items()):
        mapping, topology, _, _, _, representation = key
        rows.append(
            _summary_row(
                key=key,
                accumulator=accumulator,
                confidence=confidence,
                precision_limit=precision_limit,
                l2_fingerprint=(
                    l2_fingerprints[(str(mapping), str(topology))]
                    if representation == "L2-independent_word_marginals"
                    else None
                ),
                paired_disagreement_valid=representation
                in {"L0", "L1", "L2-independent_word_marginals"},
            )
        )
    _add_reference_errors(rows)
    if not all(bool(row["precision_satisfied"]) for row in rows):
        raise AssertionError("predeclared bounded-comparison precision rule failed")

    decisions = _decision_rows(rows, [float(value) for value in config["epsilon_grid"]], duration)
    return {
        "aggregate_rows": rows,
        "decision_rows": decisions,
        "invariants": {
            "l0_l1_exact_checks": exact_checks,
            "l0_l1_mismatches": 0,
            "l0_to_l1_event_marks_checked": event_mark_checks,
            "l3_u_first_moment_calibrations": calibration_checks,
            "l3_e_implemented": False,
        },
        "runtime_seconds_by_representation": dict(sorted(runtime.items())),
    }


def _j_conditional_failure_after_two(subsets: Sequence[Sequence[int]]) -> float:
    total = len(subsets) * len(subsets)
    no_repeat = sum(
        set(first).isdisjoint(second) for first in subsets for second in subsets
    )
    return 1.0 - no_repeat / total


def _j_analytical_f(
    *, rate: float, t0: float, duration: float, scrub: PeriodicScrub, subsets: Sequence[Sequence[int]]
) -> float:
    conditional_failure_two = _j_conditional_failure_after_two(subsets)
    boundaries = list(scrub.times(t0, t0 + duration))
    if not boundaries or not math.isclose(boundaries[-1], t0 + duration, abs_tol=1e-12):
        boundaries.append(t0 + duration)
    survival = 1.0
    start = t0
    for boundary in boundaries:
        mean = rate * (boundary - start)
        probability_zero = math.exp(-mean)
        probability_one = probability_zero * mean
        probability_two = probability_zero * mean * mean / 2.0
        interval_survival = (
            probability_zero
            + probability_one
            + probability_two * (1.0 - conditional_failure_two)
        )
        survival *= interval_survival
        start = boundary
    return 1.0 - survival


def _joint_decision_rows(
    rows: Sequence[Mapping[str, object]], epsilon_grid: Sequence[float], duration: float
) -> list[dict[str, object]]:
    by_model = {
        model: sorted(
            (row for row in rows if row["model"] == model),
            key=lambda row: float(row["scrub_period"]),
        )
        for model in sorted({str(row["model"]) for row in rows})
    }
    comparisons = (
        ("J-A", "J-B"),
        ("J-B", "J-A"),
        ("L2-independent_word_marginals", "J-A"),
        ("L2-independent_word_marginals", "J-B"),
    )
    output: list[dict[str, object]] = []
    for epsilon in epsilon_grid:
        for candidate_model, reference_model in comparisons:
            candidate_feasible = [
                float(row["scrub_period"])
                for row in by_model[candidate_model]
                if float(row["ci_high"]) <= epsilon
            ]
            reference_feasible = [
                float(row["scrub_period"])
                for row in by_model[reference_model]
                if float(row["ci_high"]) <= epsilon
            ]
            candidate_selected = max(candidate_feasible) if candidate_feasible else None
            reference_selected = max(reference_feasible) if reference_feasible else None
            false_safe = sorted(set(candidate_feasible) - set(reference_feasible))
            false_conservative = sorted(set(reference_feasible) - set(candidate_feasible))
            output.append(
                {
                    "epsilon": epsilon,
                    "epsilon_status": "experiment_parameter_not_project_requirement",
                    "candidate_model": candidate_model,
                    "reference_model": reference_model,
                    "feasibility_rule": "wilson_ci_upper_le_epsilon",
                    "candidate_feasible_periods": json.dumps(
                        candidate_feasible, separators=(",", ":")
                    ),
                    "reference_feasible_periods": json.dumps(
                        reference_feasible, separators=(",", ":")
                    ),
                    "candidate_selected_period": candidate_selected,
                    "reference_selected_period": reference_selected,
                    "selected_period_discrepancy": candidate_selected != reference_selected,
                    "selected_period_delta": (
                        candidate_selected - reference_selected
                        if candidate_selected is not None and reference_selected is not None
                        else None
                    ),
                    "false_safe_periods": json.dumps(false_safe, separators=(",", ":")),
                    "false_conservative_periods": json.dumps(
                        false_conservative, separators=(",", ":")
                    ),
                    "false_safe_decision": bool(false_safe),
                    "false_conservative_decision": bool(false_conservative),
                    "candidate_selected_scrub_operations": (
                        math.floor(duration / candidate_selected + 1e-12)
                        if candidate_selected is not None
                        else None
                    ),
                }
            )
    return output


def run_joint_discriminator(config: Mapping[str, object]) -> dict[str, object]:
    invariants = validate_joint_config(config)
    common = config["common"]
    memory = memory_from_config(common["domain"])
    t0 = float(common["reporting_window"]["t0"])
    duration = float(common["reporting_window"]["duration"])
    end = t0 + duration
    confidence = float(common["monte_carlo"]["confidence_level"])
    precision_limit = float(common["monte_carlo"]["max_wilson_half_width"])
    delta_precision_limit = float(common["monte_carlo"]["max_paired_delta_half_width"])
    initial_state = initial_state_from_config(common["initial_state"])
    models = {str(model["name"]): model for model in config["joint_models"]}
    marginals_a = j_model_marginals(config, "J-A")
    marginals_b = j_model_marginals(config, "J-B")
    if marginals_a.word_pmfs != marginals_b.word_pmfs:
        raise AssertionError("J-A/J-B derived L2 inputs are not identical")

    accumulators: dict[tuple[str, float], BinaryAccumulator] = defaultdict(BinaryAccumulator)
    deltas: dict[float, PairedDifferenceAccumulator] = defaultdict(PairedDifferenceAccumulator)
    runtime: dict[str, float] = defaultdict(float)
    epoch_checks = 0
    fresh_bit_checks = 0
    scrub_periods = [float(value) for value in common["candidate_scrub_periods"]]

    for batch_seed in common["monte_carlo"]["batch_seeds"]:
        for trial_index in range(int(common["monte_carlo"]["trials_per_seed"])):
            stream_identity = (config["experiment_id"], "joint-discriminator", batch_seed, trial_index)
            arrival_times = generate_arrival_times(
                common["arrival_scenario"],
                random.Random(derive_seed(*stream_identity, "parent-arrival")),
                t0,
                end,
            )
            selector_rng = random.Random(derive_seed(*stream_identity, "joint-selector"))
            uniforms = tuple(selector_rng.random() for _ in arrival_times)
            events_a = generate_j_events(
                arrival_times=arrival_times,
                selection_uniforms=uniforms,
                model=models["J-A"],
                memory=memory,
            )
            events_b = generate_j_events(
                arrival_times=arrival_times,
                selection_uniforms=uniforms,
                model=models["J-B"],
                memory=memory,
            )
            events_l2 = reconstruct_l2_independent_word_marginals(
                arrival_times=arrival_times,
                memory=memory,
                marginals=marginals_a,
                rng=random.Random(derive_seed(*stream_identity, "l2-reconstruction")),
                fresh_bit_allocation=True,
            )
            if tuple(event.time for event in events_a) != tuple(event.time for event in events_b):
                raise AssertionError("J-A/J-B parent-arrival epochs differ")
            epoch_checks += len(arrival_times)
            for events in (events_a, events_b):
                seen_by_word: list[set[int]] = [set() for _ in range(memory.word_count)]
                for event in events:
                    if len(event.impacts) != 2:
                        raise AssertionError("a J parent event must impact exactly two words")
                    for impact in event.impacts:
                        bit = impact.bits[0]
                        if bit in seen_by_word[impact.word]:
                            raise AssertionError("J event did not add a fresh erroneous bit")
                        seen_by_word[impact.word].add(bit)
                        fresh_bit_checks += 1

            for scrub_period in scrub_periods:
                scrub = _scrub_from_config(common["scrub"], scrub_period)
                common_arguments = {
                    "memory": memory,
                    "initial_state": initial_state,
                    "scrub": scrub,
                    "t0": t0,
                    "duration": duration,
                    "bit_update_semantics": common["state_update"]["bit_update_semantics"],
                    "record_trace": False,
                }
                result_a = _timed_call(
                    runtime, "J-A", simulate_joint_events, events=events_a, **common_arguments
                )
                result_b = _timed_call(
                    runtime, "J-B", simulate_joint_events, events=events_b, **common_arguments
                )
                result_l2 = _timed_call(
                    runtime,
                    "L2-independent_word_marginals",
                    simulate_joint_events,
                    events=events_l2,
                    **common_arguments,
                )
                accumulators[("J-A", scrub_period)].add(result_a.e_cap)
                accumulators[("J-B", scrub_period)].add(result_b.e_cap)
                accumulators[("L2-independent_word_marginals", scrub_period)].add(
                    result_l2.e_cap,
                    disagreement=result_l2.e_cap != result_a.e_cap,
                )
                deltas[scrub_period].add(result_b.e_cap, result_a.e_cap)

    rate = float(common["arrival_scenario"]["rate"])
    analytical_tolerance = float(common["analytical_sanity_tolerance"])
    rows: list[dict[str, object]] = []
    for (model_name, scrub_period), accumulator in sorted(accumulators.items()):
        low, high = wilson_interval(accumulator.successes, accumulator.trials, confidence)
        half_width = (high - low) / 2.0
        analytical = None
        analytical_error = None
        if model_name in {"J-A", "J-B"}:
            analytical = _j_analytical_f(
                rate=rate,
                t0=t0,
                duration=duration,
                scrub=_scrub_from_config(common["scrub"], scrub_period),
                subsets=models[model_name]["subsets"],
            )
            analytical_error = accumulator.successes / accumulator.trials - analytical
            if abs(analytical_error) > analytical_tolerance:
                raise AssertionError(
                    f"{model_name} Monte Carlo sanity error {analytical_error} exceeds tolerance"
                )
        rows.append(
            {
                "model": model_name,
                "scrub_period": scrub_period,
                "trials": accumulator.trials,
                "e_cap_count": accumulator.successes,
                "f_a": accumulator.successes / accumulator.trials,
                "ci_method": "wilson_score",
                "confidence_level": confidence,
                "ci_low": low,
                "ci_high": high,
                "ci_half_width": half_width,
                "precision_limit": precision_limit,
                "precision_satisfied": half_width <= precision_limit + 1e-15,
                "analytical_f_a": analytical,
                "monte_carlo_minus_analytical": analytical_error,
                "analytical_sanity_tolerance": analytical_tolerance
                if analytical is not None
                else None,
                "l2_input_fingerprint": marginals_a.fingerprint
                if model_name == "L2-independent_word_marginals"
                else None,
            }
        )
    if not all(bool(row["precision_satisfied"]) for row in rows):
        raise AssertionError("predeclared J discriminator precision rule failed")

    delta_rows: list[dict[str, object]] = []
    for scrub_period, accumulator in sorted(deltas.items()):
        mean, low, high = paired_normal_interval(accumulator, confidence)
        half_width = (high - low) / 2.0
        delta_rows.append(
            {
                "scrub_period": scrub_period,
                "delta_definition": "F_A(J-B)-F_A(J-A)",
                "paired_trials": accumulator.trials,
                "delta_f_a": mean,
                "ci_method": "paired_normal_binary_difference",
                "confidence_level": confidence,
                "ci_low": low,
                "ci_high": high,
                "ci_half_width": half_width,
                "precision_limit": delta_precision_limit,
                "precision_satisfied": half_width <= delta_precision_limit + 1e-15,
                "j_b_only_failures": accumulator.positive,
                "j_a_only_failures": accumulator.negative,
            }
        )
    if not all(bool(row["precision_satisfied"]) for row in delta_rows):
        raise AssertionError("predeclared paired-delta precision rule failed")

    decisions = _joint_decision_rows(
        rows, [float(value) for value in common["epsilon_grid"]], duration
    )
    invariants = dict(invariants)
    invariants.update(
        {
            "identical_parent_epoch_checks": epoch_checks,
            "fresh_bit_updates_checked": fresh_bit_checks,
            "derived_l2_inputs_exactly_equal": True,
            "derived_l2_input_fingerprint": marginals_a.fingerprint,
        }
    )
    return {
        "aggregate_rows": rows,
        "delta_rows": delta_rows,
        "decision_rows": decisions,
        "invariants": invariants,
        "runtime_seconds_by_model": dict(sorted(runtime.items())),
    }


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: str | Path, value: object) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def write_csv(path: str | Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty aggregate table")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def collect_environment() -> dict[str, object]:
    return {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "dependencies": {"third_party_runtime_dependencies": []},
        "test_framework": "unittest (Python standard library)",
        "prng": "random.Random / MT19937 with SHA-256-derived deterministic substreams",
    }


def peak_process_memory_bytes() -> tuple[int | None, str]:
    """Return native peak working-set memory without tracing every allocation."""

    if os.name == "nt":
        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p
        psapi.GetProcessMemoryInfo.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ProcessMemoryCounters),
            ctypes.c_ulong,
        )
        psapi.GetProcessMemoryInfo.restype = ctypes.c_int
        process = kernel32.GetCurrentProcess()
        success = psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb)
        if success:
            return int(counters.PeakWorkingSetSize), "Windows PeakWorkingSetSize"
        return None, "Windows PeakWorkingSetSize unavailable"

    try:
        import resource

        value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        multiplier = 1 if sys.platform == "darwin" else 1024
        return value * multiplier, "resource.getrusage(RUSAGE_SELF).ru_maxrss"
    except (ImportError, OSError):
        return None, "native peak process memory unavailable"


def git_head(repo_root: str | Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()
