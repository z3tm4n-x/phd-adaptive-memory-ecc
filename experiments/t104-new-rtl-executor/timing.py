"""Exact pre-RTL timing checks. No physical WCET or new T95 certificate."""
from fractions import Fraction as F
from hashlib import sha1
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NS = F(1, 10**9)


def ceil(x):
    x = F(x)
    return -(-x.numerator // x.denominator)


def load_inputs():
    cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    for name, wanted in cfg["sources"].items():
        raw = (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
        got = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if got != wanted:
            raise ValueError(f"accepted source changed: {name}")
    h = json.loads((ROOT / "experiments/t95-method-regime-map/handoff.json")
                   .read_text(encoding="utf-8"))
    a = json.loads((ROOT / "experiments/t96-hybrid-rule-implementation/outputs/reproduction.json")
                   .read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "experiments/RE-CY62167-EXECUTOR-TIMING-GATE-01/"
                          "reference-continuation-01/source_manifest.json")
                          .read_text(encoding="utf-8"))
    if cfg["datasheet"]["sha256"] != manifest["primary_documents"][0]["sha256"]:
        raise ValueError("datasheet identity changed")
    return cfg, h, a


def fixed_phase_cycle(q, required, tick_min, tick_max):
    """Minimum fixed phase count satisfying the fastest-clock interval.

    Ignoring EXTRA delays here gives only an optimistic exclusion test. The
    real unknown upper bounds remain None; a passing row is NOT qualification.
    """
    q = F(q)
    if q <= 0 or required <= 0 or not 0 < tick_min <= tick_max:
        raise ValueError("invalid phase contract")
    count = ceil(required / (q * tick_min))
    return {"phase_ticks": q, "phase_count": count,
            "virtual_duration_ticks": count*q,
            "fastest_interval_s": count*q*tick_min,
            "slowest_interval_s": count*q*tick_max}


def staged_choice(old, new, activation, decision, received, cutoff,
                  revoked=False):
    """Pointwise timing projection ONLY, not firmware or a CDC implementation.

    Caller supplies immutable, validated payloads and handles ERR/holds first.
    Revocation invalidates BOTH the old command and any pre-loss shadow.
    In particular a future nominal issued_at must not defeat revocation.
    """
    if revoked:
        return None
    if decision < activation:
        return old
    return new if received <= cutoff else None  # Expiry/default S on a miss.


def queue_capacity(burst, rate, delay):
    """Conservative count bound including in-flight/response-held requests."""
    if min(burst, rate, delay) < 0:
        raise ValueError("negative count envelope")
    return ceil(F(burst) + F(rate)*delay)


def encode(x):
    if isinstance(x, F):
        return str(x)
    if isinstance(x, dict):
        return {k: encode(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)):
        return [encode(v) for v in x]
    return x


def calculate():
    cfg, h, a = load_inputs()
    fc, ds = h["fixed_contract"], cfg["datasheet"]
    tick = F(fc["tick_nominal_s"])
    tm = tick * F(fc["clock_constant_scale_lower"])
    tp = tick * F(fc["clock_constant_scale_upper"])
    margin = 1 + F(fc["time_margin"])
    umax = F(h["conditional_timing"]["joint_U_WCET_required_s"])
    gp = F(h["resources"]["max_extra_atomic_request_s"])
    # Check the application value too, rather than equating X with CPU silently.
    rows = json.loads((ROOT / "experiments/t90-monitor-physical/outputs/pinned_inputs.json")
                      .read_text(encoding="utf-8"))
    row = next(r for r in rows if r["shield"] == "3")
    ap = row["effective_T88_input"]["service"]["application_contract"]
    assert gp == F(ap["application_max_request_s"])
    assert umax == fc["c_ticks"]*tm/margin
    read = max(F(ds["read_cycle_min_ns"]), F(ds["address_access_max_ns"]))*NS
    write = F(ds["write_cycle_min_ns"])*NS
    candidates = []
    for q in cfg["fixed_phase_candidates_ticks"]:
        r = fixed_phase_cycle(q, read, tm, tp)
        w = fixed_phase_cycle(q, write, tm, tp)
        optimistic = r["slowest_interval_s"] + w["slowest_interval_s"]
        candidates.append({"read": r, "write": w,
            "scope": "two separate full cycles; optimistic exclusion only",
            "optimistic_two_cycle_s": optimistic,
            "U_residual_s": umax-optimistic,
            "minimum_4tick_slot_for_optimistic_U_with_margin": 4*ceil(margin*optimistic/(4*tm)),
            "U_arithmetic_fits_before_unknown_extras": optimistic <= umax,
            "application_arithmetic_fits_before_unknown_extras": r["slowest_interval_s"] <= gp,
            "physical_timing_qualified": False})
    core = cfg["command_projection"]["core_ticks"]
    p = a["parameters"]
    activation = p["window"] + p["delivery"]
    cutoff = activation // core * core
    first_after = ceil(F(activation, core))*core
    jitter = F(cfg["command_projection"]["diagnostic_jitter_ns"])*NS
    # This is the WHOLE post-window path, including CDC/validation/publication.
    # Subtract their nonzero certified bounds before assigning an upstream budget.
    early_total = ((cutoff-p["window"])*tm-jitter)/margin
    qc = cfg["queue_candidate"]
    delay = F(a["independent_resource_substitution"]["application_delay_margin_upper_s"])
    required_entries = queue_capacity(qc["count_burst"], qc["count_rate_per_s"], delay)
    return encode({
        "task": 104, "stage": "B", "scope": "first timing gate before main RTL",
        "base_sha": cfg["base_sha"], "stage_A_sha": cfg["stage_A_sha"],
        "science_sha": cfg["science_sha"], "source_blobs": cfg["sources"],
        "units": "seconds unless field explicitly names ticks/ns/count",
        "limits": {"joint_U_s": umax, "application_s": gp, "margin": margin,
                   "tick_min_s": tm, "tick_max_s": tp},
        "fixed_phase_candidates": candidates,
        "fixed_phase_necessary_application_s": read*tp/tm,
        "nominal_two_cycle_U_residual_s": umax-read-write,
        "positive_path_counterexample": {
            "memory_read_s": F(ds["address_access_max_ns"])*NS,
            "diagnostic_extra_path_s": F(cfg["diagnostic_counterexample"]["path_ns"])*NS,
            "completion_s": (F(ds["address_access_max_ns"])+F(cfg["diagnostic_counterexample"]["path_ns"]))*NS,
            "status": "datasheet-permitted late read plus hypothetical positive path; not measured"},
        "write_turnaround_constraints": {
            "OE_high_to_drive_pin_min_s": F(ds["output_disable_max_ns"])*NS,
            "write_end_after_DQ_stable_min_s": F(ds["write_data_setup_min_ns"])*NS,
            "OE_low_WE_pulse_min_s": max(F(ds["write_pulse_min_ns"]),
                                         F(ds["output_disable_max_ns"])+F(ds["write_data_setup_min_ns"]))*NS,
            "full_pin_timing_closed": False},
        "command_projection": {"original_activation_ticks": activation,
            "core_ticks": core, "last_early_edge_ticks": cutoff,
            "first_eligible_edge_ticks": first_after,
            "all_window_activations_same_residue": p["stride"] % core == 0,
            "not_before_ticks": activation,
            "original_lease_ticks": p["lease"],
            "zero_jitter_early_total_path_s": (cutoff-p["window"])*tm/margin,
            "diagnostic_edge_uncertainty_s": jitter,
            "diagnostic_early_total_path_s": early_total,
            "actual_CDC_and_jitter_qualified": False},
        "queue": {"count_burst": qc["count_burst"], "count_rate_per_s": qc["count_rate_per_s"],
            "delay_bound_used_s": delay, "required_entries_conservative": required_entries,
            "proposed_total_capacity": qc["total_outstanding_capacity"],
            "fits_under_both_count_and_original_work_contracts": required_entries <= qc["total_outstanding_capacity"],
            "actual_workload_confirmed": False, "hardware_implemented": False},
        "physical_upper_bounds_s": cfg["physical_upper_bounds_s"],
        "decision": {"continue_main_RTL": False,
            "blocker": "45-ns complete application request has no allowance for the full pin-limited read path",
            "all_possible_architectures_excluded": False,
            "accepted_service_changed": False, "RTL_formal_proof_performed": False,
            "stages_C_D_started": False}})
