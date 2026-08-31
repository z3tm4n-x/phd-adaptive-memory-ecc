"""JSON configuration loading and scientific-contract validation."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Mapping

from .arrivals import validate_arrival_scenario
from .model import MemorySpec
from .representations import joint_pair_invariants, topology_support
from .statistics import worst_case_wilson_half_width


def load_json(path: str | Path) -> dict[str, object]:
    with Path(path).open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("top-level configuration must be a JSON object")
    return value


def memory_from_config(domain: Mapping[str, object]) -> MemorySpec:
    word_count = int(domain["word_count"])
    bits_per_word = int(domain["bits_per_word"])
    capability = domain["ecc_correction_capability_distinct_bits"]
    if isinstance(capability, list):
        return MemorySpec(word_count, bits_per_word, tuple(int(item) for item in capability))
    return MemorySpec.homogeneous(word_count, bits_per_word, int(capability))


def initial_state_from_config(state: Mapping[str, object]) -> dict[int, tuple[int, ...]]:
    result: dict[int, list[int]] = {}
    for cell in state["erroneous_logical_cells"]:
        result.setdefault(int(cell["word"]), []).append(int(cell["bit"]))
    return {word: tuple(bits) for word, bits in result.items()}


def _validate_precision(config: Mapping[str, object]) -> None:
    seeds = list(config["batch_seeds"])
    trials_per_seed = int(config["trials_per_seed"])
    if len(seeds) < 2 or len(set(seeds)) != len(seeds):
        raise ValueError("multiple distinct deterministic batch seeds are required")
    if trials_per_seed <= 0:
        raise ValueError("trials_per_seed must be positive")
    trials = len(seeds) * trials_per_seed
    declared_trials = int(config["total_trials_per_aggregate"])
    if declared_trials != trials:
        raise ValueError(
            "declared total_trials_per_aggregate must equal "
            "len(batch_seeds) * trials_per_seed"
        )
    confidence = float(config["confidence_level"])
    threshold = float(config["max_wilson_half_width"])
    worst = worst_case_wilson_half_width(trials, confidence)
    if worst > threshold + 1e-15:
        raise ValueError(
            f"predeclared precision cannot be met: worst Wilson half-width {worst:.6g} > {threshold:.6g}"
        )
    if config["confidence_interval"] != "wilson_score":
        raise ValueError("Phase 1 predeclares Wilson score intervals")


def _is_integer_multiple(value: float, unit: float) -> bool:
    if unit <= 0:
        return False
    quotient = value / unit
    return math.isclose(quotient, round(quotient), rel_tol=0.0, abs_tol=1e-12)


def validate_joint_analytical_preconditions(
    config: Mapping[str, object],
) -> dict[str, object]:
    """Validate every configuration-level precondition of the J closed form.

    Fresh-bit capacity is additionally checked against every generated finite
    stream in ``run_joint_discriminator`` before analytical rows are produced.
    """

    common = config["common"]
    memory = memory_from_config(common["domain"])
    if memory.word_count != 4:
        raise ValueError("the J analytical result requires exactly four words")
    if memory.correction_capability != (1, 1, 1, 1):
        raise ValueError("the J analytical result requires t_c=1 for all four words")
    if common["initial_state"]["erroneous_logical_cells"]:
        raise ValueError("the J analytical result requires a clean reporting-window start")

    models = list(config["joint_models"])
    if len(models) != 2 or {item["name"] for item in models} != {"J-A", "J-B"}:
        raise ValueError("both and only J-A/J-B models are required")
    for model in models:
        subsets = list(model["subsets"])
        if not subsets:
            raise ValueError(f"{model['name']} requires at least one pair mark")
        normalized_pairs: list[tuple[int, int]] = []
        for subset in subsets:
            words = tuple(int(word) for word in subset)
            if len(words) != 2 or len(set(words)) != 2:
                raise ValueError("every J mark must contain exactly two distinct words")
            if any(not 0 <= word < memory.word_count for word in words):
                raise ValueError("every J mark word must lie inside the four-word domain")
            normalized_pairs.append(tuple(sorted(words)))
        if len(set(normalized_pairs)) != len(normalized_pairs):
            raise ValueError("each declared J pair mark must be unique within its model")

    state_update = common["state_update"]
    if state_update["bit_update_semantics"] != "set_error":
        raise ValueError("the J analytical result requires fresh-bit set semantics")
    if state_update["bit_allocation"] != "fresh_monotone_per_word":
        raise ValueError("the J analytical result requires fresh monotone bit allocation")
    if state_update["parent_event_is_simultaneous"] is not True:
        raise ValueError("J parent impacts must be simultaneous")
    if state_update["capability_check_order"] != "after_complete_parent_mark":
        raise ValueError("E_cap must be checked after the complete J parent mark")

    scrub = common["scrub"]
    if scrub["kind"] != "periodic_global_synchronous":
        raise ValueError("the J analytical result requires periodic synchronous scrubbing")
    if scrub["transition"] != "clear_all_erroneous_bits":
        raise ValueError("the J analytical result requires a full-state reset scrub")
    if scrub["event_at_boundary"] != "scrub_then_event":
        raise ValueError("the declared deterministic boundary order must be scrub_then_event")

    reporting = common["reporting_window"]
    t0 = float(reporting["t0"])
    duration = float(reporting["duration"])
    phase_origin = float(scrub["phase_origin"])
    if duration <= 0:
        raise ValueError("the J analytical reporting duration must be positive")
    if reporting["endpoints"] != "closed":
        raise ValueError("the DEC-001 J reporting window must use the declared closed endpoints")
    periods = [float(value) for value in common["candidate_scrub_periods"]]
    if not periods or len(set(periods)) != len(periods) or any(value <= 0 for value in periods):
        raise ValueError("candidate J scrub periods must be distinct and positive")
    for period in periods:
        if not _is_integer_multiple(t0 - phase_origin, period):
            raise ValueError("t0 must be aligned with the scrub phase for every J period")
        if not _is_integer_multiple(duration, period):
            raise ValueError(
                "the reporting duration must contain an integer number of complete J intervals"
            )

    arrival = common["arrival_scenario"]
    end = t0 + duration
    validate_arrival_scenario(arrival, t0, end)
    if arrival["kind"] != "hpp_constant" or float(arrival["rate"]) <= 0:
        raise ValueError("the bounded J analytical result requires a positive-rate HPP")

    _validate_precision(common["monte_carlo"])
    return {
        "exactly_four_words": True,
        "all_correction_capabilities_equal_one": True,
        "clean_initial_state": True,
        "valid_unique_distinct_two_word_marks": True,
        "fresh_monotone_set_error_semantics": True,
        "simultaneous_complete_parent_mark_before_capability_check": True,
        "periodic_synchronous_full_reset_scrub": True,
        "scrub_then_event_boundary_order": True,
        "phase_and_complete_window_alignment": True,
        "positive_rate_hpp": True,
        "declared_trial_total_matches_seed_product": True,
        "configured_bits_per_word": memory.bits_per_word,
        "fresh_bit_capacity_validation_stage": "finite_stream_runtime_before_analytical_output",
    }


def validate_bounded_config(config: Mapping[str, object]) -> None:
    if config.get("experiment_id") != "EXP-001":
        raise ValueError("configuration must belong to EXP-001")
    representations = list(config["representations"])
    required = {"L0", "L1", "L2-independent_word_marginals", "L3-U"}
    if set(representations) != required:
        raise ValueError(f"bounded comparison requires exactly {sorted(required)}")
    if any(value == "L3-E" for value in representations):
        raise ValueError("L3-E is deferred and prohibited in Phase 1")

    memory = memory_from_config(config["domain"])
    mapping_kinds = {item["kind"] for item in config["mappings"]}
    if mapping_kinds != {"contiguous_words", "round_robin_words"}:
        raise ValueError("two declared W variants are required")

    observed_topologies: set[str] = set()
    for scenario in config["topology_scenarios"]:
        total_probability = math.fsum(float(item["probability"]) for item in scenario["classes"])
        if abs(total_probability - 1.0) > 1e-12:
            raise ValueError("topology scenario probabilities must sum to one")
        for item in scenario["classes"]:
            observed_topologies.add(str(item["kind"]))
            topology_support(memory, item)
    required_topologies = {"single_cell", "compact_multi_cell", "spatially_separated"}
    if not required_topologies.issubset(observed_topologies):
        raise ValueError("all three mandated topology classes must be present")

    t0 = float(config["reporting_window"]["t0"])
    end = t0 + float(config["reporting_window"]["duration"])
    arrival_kinds = set()
    for scenario in config["arrival_scenarios"]:
        validate_arrival_scenario(scenario, t0, end)
        arrival_kinds.add(scenario["kind"])
    if arrival_kinds != {"hpp_constant", "piecewise_constant_nhpp"}:
        raise ValueError("constant HPP and deterministic time-varying NHPP are both required")

    update = config["state_update"]
    if update["bit_update_semantics"] != "toggle" or not update["parent_event_is_simultaneous"]:
        raise ValueError("bounded comparison requires declared simultaneous toggle semantics")
    scrub = config["scrub"]
    if (
        scrub["transition"] != "clear_all_erroneous_bits"
        or scrub["event_at_boundary"] != "scrub_then_event"
    ):
        raise ValueError("scrub semantics must be explicit and supported")
    if not any(state["erroneous_logical_cells"] for state in config["initial_states"]):
        raise ValueError("at least one non-clean initial state is required")
    if not any(not state["erroneous_logical_cells"] for state in config["initial_states"]):
        raise ValueError("a clean initial state is required")

    l2 = config["l2"]
    if l2["rule"] != "independent_word_marginals":
        raise ValueError("undeclared L2 reconstruction rule")
    l3 = config["l3_u"]
    if l3["primitive_object"] != "individual_ungrouped_bit_toggle_arrival":
        raise ValueError("L3-U primitive must be an individual ungrouped upset")
    if l3["intensity_units"] != "ungrouped_upsets_per_arbitrary_time_unit_over_A":
        raise ValueError("L3-U intensity units must be explicit over A")
    if l3["allocation_rule"] != "uniform_over_logical_cells_in_A":
        raise ValueError("L3-U allocation rule must be explicit")
    if l3["calibration_target"] != "expected_total_upset_exposure_over_A_first_moment":
        raise ValueError("L3-U must use the declared first-moment calibration")
    if l3["stochastic_process_equivalence_claimed"] is not False:
        raise ValueError("first-moment calibration cannot claim process equivalence")

    if config["epsilon_grid_status"] != "experiment_parameters_not_project_requirements":
        raise ValueError("epsilon sweep must not be labelled as a project requirement")
    if config["restoration_decision"]["rule"] != "maximal_period_with_wilson_upper_bound_le_epsilon":
        raise ValueError("restoration decision rule is not the predeclared rule")
    _validate_precision(config["monte_carlo"])


def validate_joint_config(config: Mapping[str, object]) -> dict[str, object]:
    if config.get("experiment_id") != "EXP-001":
        raise ValueError("configuration must belong to EXP-001")
    common = config["common"]
    memory = memory_from_config(common["domain"])
    validate_joint_analytical_preconditions(config)
    if common["epsilon_grid_status"] != "experiment_parameters_not_project_requirements":
        raise ValueError("epsilon sweep must not be labelled as a project requirement")
    if common["restoration_decision"]["rule"] != "maximal_period_with_wilson_upper_bound_le_epsilon":
        raise ValueError("restoration decision rule is not the predeclared rule")
    invariants = joint_pair_invariants(config)
    required = (
        "all_words_have_impact_probability_one_half",
        "exactly_two_words_impacted_per_event",
        "derived_per_word_l2_inputs_identical",
        "joint_association_differs",
        "no_other_model_parameter_differs",
    )
    if not all(invariants[item] for item in required):
        raise AssertionError(f"J-A/J-B construction violates invariants: {invariants}")
    return invariants
