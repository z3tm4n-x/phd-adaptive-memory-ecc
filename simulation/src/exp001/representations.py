"""L0/L1/L2/L3-U transformations and the J-A/J-B construction."""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Mapping, Sequence

from .model import (
    JointImpactEvent,
    MemorySpec,
    PhysicalEvent,
    PhysicalMapping,
    WordImpact,
    physical_to_joint,
)


@dataclass(frozen=True)
class L2Marginals:
    """Exact per-word event multiplicity PMFs used by one named L2 rule."""

    word_pmfs: tuple[tuple[tuple[int, float], ...], ...]
    source_description: str

    def as_jsonable(self) -> dict[str, object]:
        return {
            "source_description": self.source_description,
            "word_pmfs": [
                {str(multiplicity): probability for multiplicity, probability in pmf}
                for pmf in self.word_pmfs
            ],
        }

    @property
    def fingerprint(self) -> str:
        # The provenance description is intentionally excluded: the scientific
        # input is the PMF itself.  Thus J-A and J-B produce the same fingerprint
        # when (and only when) their derived marginal inputs are identical.
        return _pmf_fingerprint(self.word_pmfs)


def _pmf_fingerprint(word_pmfs: object) -> str:
    encoded = json.dumps(word_pmfs, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def derive_seed(*parts: object) -> int:
    """Stable substream seed independent of Python's salted ``hash``."""

    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def topology_support(memory: MemorySpec, class_spec: Mapping[str, object]) -> tuple[tuple[int, ...], ...]:
    kind = str(class_spec["kind"])
    multiplicity = int(class_spec["multiplicity"])
    if multiplicity <= 0 or multiplicity > memory.total_cells:
        raise ValueError("topology multiplicity is outside the physical domain")
    if kind == "single_cell":
        if multiplicity != 1:
            raise ValueError("single_cell topology must have multiplicity one")
        return tuple((cell,) for cell in range(memory.total_cells))
    if kind == "compact_multi_cell":
        return tuple(
            tuple(range(start, start + multiplicity))
            for start in range(memory.total_cells - multiplicity + 1)
        )
    if kind == "spatially_separated":
        stride = int(class_spec["stride"])
        if stride <= 1:
            raise ValueError("spatially separated topology requires stride > 1")
        max_start = memory.total_cells - 1 - (multiplicity - 1) * stride
        if max_start < 0:
            raise ValueError("separated topology does not fit in the physical domain")
        return tuple(
            tuple(start + index * stride for index in range(multiplicity))
            for start in range(max_start + 1)
        )
    raise ValueError(f"unknown topology class: {kind}")


def _validate_topology_scenario(memory: MemorySpec, scenario: Mapping[str, object]) -> None:
    classes = list(scenario["classes"])
    if not classes:
        raise ValueError("a topology scenario must contain at least one class")
    total_probability = math.fsum(float(item["probability"]) for item in classes)
    if abs(total_probability - 1.0) > 1e-12:
        raise ValueError("topology-class probabilities must sum to one")
    for item in classes:
        if float(item["probability"]) < 0:
            raise ValueError("topology probability cannot be negative")
        if not topology_support(memory, item):
            raise ValueError("topology class has empty support")


def enumerate_weighted_physical_marks(
    memory: MemorySpec, scenario: Mapping[str, object]
) -> tuple[tuple[float, tuple[int, ...], str], ...]:
    _validate_topology_scenario(memory, scenario)
    result: list[tuple[float, tuple[int, ...], str]] = []
    for class_spec in scenario["classes"]:
        support = topology_support(memory, class_spec)
        weight = float(class_spec["probability"]) / len(support)
        for mark in support:
            result.append((weight, mark, str(class_spec["kind"])))
    return tuple(result)


def expected_event_multiplicity(memory: MemorySpec, scenario: Mapping[str, object]) -> float:
    _validate_topology_scenario(memory, scenario)
    return math.fsum(
        float(class_spec["probability"]) * int(class_spec["multiplicity"])
        for class_spec in scenario["classes"]
    )


def _weighted_choice_index(weights: Sequence[float], rng: random.Random) -> int:
    draw = rng.random()
    cumulative = 0.0
    for index, weight in enumerate(weights):
        cumulative += weight
        if draw < cumulative:
            return index
    return len(weights) - 1


def generate_physical_events(
    *,
    arrival_times: Sequence[float],
    memory: MemorySpec,
    topology_scenario: Mapping[str, object],
    rng: random.Random,
) -> tuple[PhysicalEvent, ...]:
    _validate_topology_scenario(memory, topology_scenario)
    classes = list(topology_scenario["classes"])
    class_weights = [float(item["probability"]) for item in classes]
    supports = [topology_support(memory, item) for item in classes]
    result: list[PhysicalEvent] = []
    for ordinal, time_value in enumerate(arrival_times):
        class_index = _weighted_choice_index(class_weights, rng)
        support = supports[class_index]
        mark = support[rng.randrange(len(support))]
        result.append(
            PhysicalEvent(
                parent_id=f"parent-{ordinal:06d}",
                time=time_value,
                physical_cells=mark,
                topology_class=str(classes[class_index]["kind"]),
            )
        )
    return tuple(result)


def convert_l0_to_l1(
    events: Sequence[PhysicalEvent], mapping: PhysicalMapping
) -> tuple[JointImpactEvent, ...]:
    return tuple(physical_to_joint(event, mapping) for event in events)


def derive_l2_marginals(
    memory: MemorySpec,
    mapping: PhysicalMapping,
    topology_scenario: Mapping[str, object],
) -> L2Marginals:
    accumulators: list[dict[int, float]] = [dict() for _ in range(memory.word_count)]
    for probability, physical_mark, _ in enumerate_weighted_physical_marks(memory, topology_scenario):
        counts = [0] * memory.word_count
        for impact in mapping.map_cells(physical_mark):
            counts[impact.word] = len(impact.bits)
        for word, multiplicity in enumerate(counts):
            accumulators[word][multiplicity] = (
                accumulators[word].get(multiplicity, 0.0) + probability
            )
    word_pmfs: list[tuple[tuple[int, float], ...]] = []
    for accumulator in accumulators:
        total = math.fsum(accumulator.values())
        if abs(total - 1.0) > 1e-10:
            raise AssertionError("derived L2 marginal does not normalize")
        word_pmfs.append(
            tuple(
                (multiplicity, probability / total)
                for multiplicity, probability in sorted(accumulator.items())
            )
        )
    return L2Marginals(
        word_pmfs=tuple(word_pmfs),
        source_description=(
            f"exact enumeration of {topology_scenario['name']} through W={mapping.name}"
        ),
    )


def _sample_pmf(pmf: Sequence[tuple[int, float]], rng: random.Random) -> int:
    return pmf[_weighted_choice_index([item[1] for item in pmf], rng)][0]


def reconstruct_l2_independent_word_marginals(
    *,
    arrival_times: Sequence[float],
    memory: MemorySpec,
    marginals: L2Marginals,
    rng: random.Random,
    fresh_bit_allocation: bool = False,
) -> tuple[JointImpactEvent, ...]:
    """Named L2 rule: sample every exact word marginal independently.

    The rule preserves each supplied per-word multiplicity PMF by construction,
    but discards inter-word dependence and does not preserve the number of
    impacted words per parent event.
    """

    next_fresh_bit = [0] * memory.word_count
    result: list[JointImpactEvent] = []
    for ordinal, time_value in enumerate(arrival_times):
        impacts: list[WordImpact] = []
        for word, pmf in enumerate(marginals.word_pmfs):
            multiplicity = _sample_pmf(pmf, rng)
            if multiplicity == 0:
                continue
            if multiplicity > memory.bits_per_word:
                raise ValueError("L2 multiplicity exceeds word size")
            if fresh_bit_allocation:
                start = next_fresh_bit[word]
                stop = start + multiplicity
                if stop > memory.bits_per_word:
                    raise RuntimeError("fresh-bit capacity exhausted in the bounded J run")
                bits = tuple(range(start, stop))
                next_fresh_bit[word] = stop
            else:
                bits = tuple(sorted(rng.sample(range(memory.bits_per_word), multiplicity)))
            impacts.append(WordImpact(word=word, bits=bits))
        result.append(
            JointImpactEvent(
                parent_id=f"l2-parent-{ordinal:06d}",
                time=time_value,
                impacts=tuple(impacts),
                primitive_kind="parent_event",
            )
        )
    return tuple(result)


def generate_l3u_events(
    *,
    arrival_times: Sequence[float],
    memory: MemorySpec,
    rng: random.Random,
) -> tuple[JointImpactEvent, ...]:
    """Allocate ungrouped primitive upsets uniformly over logical cells in A."""

    result: list[JointImpactEvent] = []
    for ordinal, time_value in enumerate(arrival_times):
        logical_cell = rng.randrange(memory.total_cells)
        word, bit = divmod(logical_cell, memory.bits_per_word)
        result.append(
            JointImpactEvent(
                parent_id=f"ungrouped-upset-{ordinal:06d}",
                time=time_value,
                impacts=(WordImpact(word=word, bits=(bit,)),),
                primitive_kind="ungrouped_upset",
            )
        )
    return tuple(result)


def _subset_word_pmfs(
    word_count: int, subsets: Sequence[Sequence[int]]
) -> tuple[tuple[tuple[int, float], ...], ...]:
    denominator = len(subsets)
    result: list[tuple[tuple[int, float], ...]] = []
    for word in range(word_count):
        hits = sum(word in subset for subset in subsets)
        result.append(((0, (denominator - hits) / denominator), (1, hits / denominator)))
    return tuple(result)


def joint_pair_invariants(config: Mapping[str, object]) -> dict[str, object]:
    common = config["common"]
    word_count = int(common["domain"]["word_count"])
    models = config["joint_models"]
    details: dict[str, object] = {}
    pmfs: dict[str, tuple[tuple[tuple[int, float], ...], ...]] = {}
    pair_probabilities: dict[str, dict[str, str]] = {}
    all_exactly_two = True
    all_half = True

    for model in models:
        name = str(model["name"])
        subsets = [tuple(int(word) for word in subset) for subset in model["subsets"]]
        denominator = len(subsets)
        impact_probabilities = [
            Fraction(sum(word in subset for subset in subsets), denominator)
            for word in range(word_count)
        ]
        pmfs[name] = _subset_word_pmfs(word_count, subsets)
        pair_probability: dict[str, str] = {}
        for first in range(word_count):
            for second in range(first + 1, word_count):
                value = Fraction(
                    sum(first in subset and second in subset for subset in subsets),
                    denominator,
                )
                pair_probability[f"w{first + 1},w{second + 1}"] = str(value)
        pair_probabilities[name] = pair_probability
        exactly_two = all(len(subset) == 2 and len(set(subset)) == 2 for subset in subsets)
        half = all(value == Fraction(1, 2) for value in impact_probabilities)
        all_exactly_two &= exactly_two
        all_half &= half
        details[name] = {
            "per_word_impact_probability": [str(value) for value in impact_probabilities],
            "impacted_words_per_event": 2 if exactly_two else None,
            "pair_probabilities": pair_probability,
        }

    names = [str(model["name"]) for model in models]
    identical_pmfs = len(names) == 2 and pmfs[names[0]] == pmfs[names[1]]
    association_differs = (
        len(names) == 2 and pair_probabilities[names[0]] != pair_probabilities[names[1]]
    )
    only_allowed_keys = all(set(model) == {"name", "subsets"} for model in models)
    return {
        "all_words_have_impact_probability_one_half": all_half,
        "exactly_two_words_impacted_per_event": all_exactly_two,
        "derived_per_word_l2_inputs_identical": identical_pmfs,
        "joint_association_differs": association_differs,
        "no_other_model_parameter_differs": only_allowed_keys,
        "common_parameter_object_sha256": hashlib.sha256(
            json.dumps(common, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "model_details": details,
        "derived_l2_fingerprint": _pmf_fingerprint(pmfs[names[0]])
        if identical_pmfs
        else None,
    }


def j_model_marginals(config: Mapping[str, object], model_name: str) -> L2Marginals:
    common = config["common"]
    word_count = int(common["domain"]["word_count"])
    model = next(model for model in config["joint_models"] if model["name"] == model_name)
    return L2Marginals(
        word_pmfs=_subset_word_pmfs(word_count, model["subsets"]),
        source_description=f"exact per-word marginals derived from {model_name}",
    )


def generate_j_events(
    *,
    arrival_times: Sequence[float],
    selection_uniforms: Sequence[float],
    model: Mapping[str, object],
    memory: MemorySpec,
) -> tuple[JointImpactEvent, ...]:
    """Generate J-A/J-B marks with a fresh bit for every selected word/event."""

    if len(arrival_times) != len(selection_uniforms):
        raise ValueError("one common selection uniform is required per parent epoch")
    subsets = [tuple(int(word) for word in subset) for subset in model["subsets"]]
    next_fresh_bit = [0] * memory.word_count
    result: list[JointImpactEvent] = []
    for ordinal, (time_value, draw) in enumerate(zip(arrival_times, selection_uniforms)):
        subset_index = min(int(draw * len(subsets)), len(subsets) - 1)
        impacts: list[WordImpact] = []
        for word in subsets[subset_index]:
            bit = next_fresh_bit[word]
            if bit >= memory.bits_per_word:
                raise RuntimeError("fresh-bit capacity exhausted in the bounded J run")
            next_fresh_bit[word] += 1
            impacts.append(WordImpact(word=word, bits=(bit,)))
        result.append(
            JointImpactEvent(
                parent_id=f"joint-parent-{ordinal:06d}",
                time=time_value,
                impacts=tuple(sorted(impacts, key=lambda impact: impact.word)),
                primitive_kind="parent_event",
            )
        )
    return tuple(result)
