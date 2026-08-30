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
    confidence = float(config["confidence_level"])
    threshold = float(config["max_wilson_half_width"])
    worst = worst_case_wilson_half_width(trials, confidence)
    if worst > threshold + 1e-15:
        raise ValueError(
            f"predeclared precision cannot be met: worst Wilson half-width {worst:.6g} > {threshold:.6g}"
        )
    if config["confidence_interval"] != "wilson_score":
        raise ValueError("Phase 1 predeclares Wilson score intervals")


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
    if memory.word_count != 4:
        raise ValueError("mandatory discriminator requires four words")
    if common["state_update"]["bit_update_semantics"] != "set_error":
        raise ValueError("J pair requires the declared fresh-bit set semantics")
    if common["state_update"]["bit_allocation"] != "fresh_monotone_per_word":
        raise ValueError("every selected J word must receive one new bit")
    if common["epsilon_grid_status"] != "experiment_parameters_not_project_requirements":
        raise ValueError("epsilon sweep must not be labelled as a project requirement")
    if common["restoration_decision"]["rule"] != "maximal_period_with_wilson_upper_bound_le_epsilon":
        raise ValueError("restoration decision rule is not the predeclared rule")
    t0 = float(common["reporting_window"]["t0"])
    end = t0 + float(common["reporting_window"]["duration"])
    validate_arrival_scenario(common["arrival_scenario"], t0, end)
    if common["arrival_scenario"]["kind"] != "hpp_constant":
        raise ValueError("the bounded analytical J discriminator uses the declared HPP scenario")
    if len(config["joint_models"]) != 2 or {item["name"] for item in config["joint_models"]} != {"J-A", "J-B"}:
        raise ValueError("both and only J-A/J-B models are required")
    _validate_precision(common["monte_carlo"])
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
