"""Option-2 timing allocation, exact rational arithmetic; no new risk theorem/RTL.

Units inside timing arithmetic are ns, ticks are multiples of inherited xi.
All non-datasheet delays are requirements, never measured upper bounds.
"""
from fractions import Fraction as F
from hashlib import sha1
import json

from timing import HERE, ROOT, ceil, encode, load_inputs


def inputs():
    legacy, h, a = load_inputs()
    cfg = json.loads((HERE / "budget_config.json").read_text(encoding="utf-8"))
    for path, wanted in cfg["legacy_blobs"].items():
        raw = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        if sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != wanted:
            raise ValueError(f"historical gate changed: {path}")
    rows = json.loads((ROOT / h["working_selector"]["path"]).read_text(encoding="utf-8"))
    return cfg, legacy, h, a, rows


def timing_budget(cfg, h):
    d, p = cfg["design"], cfg["pin_ns"]
    p = {k: F(v) for k, v in p.items() if k != "source"}
    f = h["fixed_contract"]
    tm = F(f["tick_nominal_s"])*10**9*F(f["clock_constant_scale_lower"])
    tp = F(f["tick_nominal_s"])*10**9*F(f["clock_constant_scale_upper"])
    q = d["core_ticks"]
    j = 2 * F(d["edge_error_abs_ns"])
    out = F(d["pin_output_upper_ns"])
    back = F(d["return_path_upper_ns"])
    setup, hold = F(d["capture_setup_ns"]), F(d["capture_hold_ns"])
    logic = F(d["decision_logic_upper_ns"])
    off = F(d["output_disable_and_settle_ns"])
    margin = 1 + F(f["time_margin"])

    def round_wait(required):
        return q * ceil((required + j) / (q * tm))

    launch = q * d["dispatch_cycles"]
    access = max(p[k] for k in ("tAA", "tACE", "tDBE", "tDOE"))
    capture = launch + round_wait(out + access + back + setup)
    decide = capture + round_wait(max(logic, hold))
    # OE/CE deassert on ERR=0; only OE deassert on ERR=1. Ignore ERR after latch.
    drive = decide + round_wait(out + max(p["tHZOE"], p["tHZCE"]) + back)
    # OE already high; DQ drive and WE low may start on the same edge.
    write_end = drive + round_wait(out + max(p["tPWE"], p["tSD"]))
    data_off = write_end + round_wait(out + max(p["tHD"], p["tHA"]))
    end = max(data_off + round_wait(off), drive + round_wait(out + p["tWC"]))
    # Standalone application write: establish address/CE/BE before WE falls.
    app_we = launch + round_wait(out + p["tSA"])
    app_end = max(app_we + round_wait(out + p["tPWE"]),
                  launch + round_wait(out + max(p[k] for k in ("tAW", "tSCE", "tBW", "tSD"))))
    app_off = app_end + round_wait(out + max(p["tHD"], p["tHA"]))
    app_release = max(app_off + round_wait(off), launch + round_wait(out + p["tWC"]))
    upper = lambda ticks: ticks * tp + j
    charge = lambda ticks: round_wait(margin * upper(ticks))
    request_cdc = d["request_mailbox_mem_cycles"] * q * tp + j
    reply_cdc = d["response_mailbox_cpu_cycles"] * F(d["cpu_clock_upper_ns"]) + 2*F(d["cpu_edge_error_abs_ns"])
    command = d["command_mem_cycles"] * q * tp + j
    return {
        "tick_min_ns": tm, "tick_max_ns": tp, "edge_span_ns": j,
        "margin_factor": margin, "core_ticks": q,
        "control_ticks": {"grant_lock": 0, "launch_read": launch, "capture_DQ_ERR": capture,
                          "decision_disable_outputs": decide, "release_if_no_ERR": drive,
                          "drive_and_WE_low_if_ERR": drive, "write_end": write_end,
                          "controller_DQ_off": data_off, "release_if_ERR": end},
        "application_write_ticks": {"grant": 0, "address_CE_BE_DQ": launch,
                                    "WE_low": app_we, "write_end": app_end,
                                    "DQ_off": app_off, "release": app_release},
        "upper_ns": {"read_no_ERR": upper(drive), "read_ERR_repair": upper(end),
                     "unconditional_write_comparator": upper(end),
                     "application_read16": upper(drive), "application_write16": upper(app_release),
                     "application_read16_with_inline_repair": upper(end),
                     "application_read32_with_inline_repairs": 2*upper(end),
                     "application_read32_atomic_two_aliases": 2*upper(drive),
                     "application_write32_atomic_two_aliases": 2*upper(app_release)},
        "charge_ticks_with_margin": {"read_no_ERR": charge(drive), "read_ERR_repair": charge(end),
                                     "application_read16": charge(drive), "application_write16": charge(app_release),
                                     "application_read32_atomic": round_wait(margin*2*upper(drive)),
                                     "application_write32_atomic": round_wait(margin*2*upper(app_release))},
        "outside_lock_upper_ns": {"request_CDC_validation": request_cdc,
                                  "response_CDC": reply_cdc, "command_receive_validate_shadow": command},
        "first_VALID_to_done_no_queue_no_backpressure_ns": {
            "read16": request_cdc + upper(drive) + reply_cdc,
            "write16": request_cdc + upper(app_release) + reply_cdc,
            "read32_atomic": request_cdc + 2*upper(drive) + reply_cdc,
            "write32_atomic": request_cdc + 2*upper(app_release) + reply_cdc},
        "unbounded_until_contract": ["queue waiting", "reply backpressure", "CPU/monitor transport before command mailbox"],
        "rounding_rule": "ceil((required_ns + 2*edge_abs)/(q*xi_min_ns))*q; upper=ticks*xi_max_ns+2*edge_abs"
    }


def pin_margins(cfg, b):
    """Sufficient interval checks including adverse pin skew and clock edges.

    No extra internal tRC is added to an external write. Each inequality is
    min available interval minus datasheet/design requirement, in ns.
    """
    p, d, t = cfg["pin_ns"], cfg["design"], b["control_ticks"]
    p = {k: F(v) for k, v in p.items() if k != "source"}
    out = F(d["pin_output_upper_ns"])
    back = F(d["return_path_upper_ns"])
    dt = lambda end, start: (end-start)*b["tick_min_ns"]-b["edge_span_ns"]
    cap, launch, dec, drive = (t[k] for k in ("capture_DQ_ERR", "launch_read", "decision_disable_outputs", "drive_and_WE_low_if_ERR"))
    we, off, end = (t[k] for k in ("write_end", "controller_DQ_off", "release_if_ERR"))
    m = {
        "DQ_ERR_capture_setup": dt(cap, launch)-out-max(p[k] for k in ("tAA", "tACE", "tDBE", "tDOE"))-back-F(d["capture_setup_ns"]),
        "capture_hold_before_OE_CE_change": dt(dec, cap)-F(d["capture_hold_ns"]),
        "ERR_decision_logic": dt(dec, cap)-F(d["decision_logic_upper_ns"]),
        "read_cycle": dt(dec, launch)-out-p["tRC"],
        "SRAM_HIZ_before_FPGA_drive_or_release": dt(drive, dec)-out-max(p["tHZOE"], p["tHZCE"])-back,
        "WE_pulse": dt(we, drive)-out-p["tPWE"],
        "DQ_setup_to_earliest_WE_CE_end": dt(we, drive)-out-p["tSD"],
        "address_setup_to_WE_low": dt(drive, launch)-out-p["tSA"],
        "address_setup_to_write_end": dt(we, launch)-out-p["tAW"],
        "CE_setup_to_write_end": dt(we, launch)-out-p["tSCE"],
        "BE_setup_to_write_end": dt(we, launch)-out-p["tBW"],
        "DQ_hold_to_controller_off": dt(off, we)-out-p["tHD"],
        "address_hold_to_release": dt(end, we)-out-p["tHA"],
        "write_cycle_before_next_launch": dt(end, drive)-out-p["tWC"],
        "FPGA_HIZ_before_next_grant": dt(end, off)-F(d["output_disable_and_settle_ns"]),
    }
    a = b["application_write_ticks"]
    for key, finish, start, requirement in (
        ("address_setup", "WE_low", "address_CE_BE_DQ", p["tSA"]),
        ("WE_pulse", "write_end", "WE_low", p["tPWE"]),
        ("address_CE_BE_setup", "write_end", "address_CE_BE_DQ", max(p[k] for k in ("tAW", "tSCE", "tBW"))),
        ("DQ_setup", "write_end", "address_CE_BE_DQ", p["tSD"]),
        ("DQ_hold", "DQ_off", "write_end", p["tHD"]),
        ("address_hold", "release", "write_end", p["tHA"]),
        ("write_cycle", "release", "address_CE_BE_DQ", p["tWC"]),
    ):
        m["app_write_"+key] = dt(a[finish], a[start])-out-requirement
    m["app_write_output_HIZ"] = dt(a["release"], a["DQ_off"])-F(d["output_disable_and_settle_ns"])
    for kind in ("read_no_ERR", "read_ERR_repair", "application_read16", "application_write16"):
        m[kind+"_margin_reservation"] = (b["charge_ticks_with_margin"][kind]*b["tick_min_ns"]
                                                - b["edge_span_ns"] - b["margin_factor"]*b["upper_ns"][kind])
    return m


def pass_occupancy(W, K, read, repair):
    """Upper charged work of W completed visits, K correction outcomes."""
    if not 0 <= K <= W or read <= 0 or repair < read:
        raise ValueError("invalid visit/correction bounds")
    return W*read+K*(repair-read)


def mask(h, period, duration):
    if h < 0 or period <= 0 or not 0 <= duration <= period:
        raise ValueError("invalid periodic mask")
    n = h // period
    return n*duration + min(h-n*period, duration)


def exact_periodic_max(h, period, intervals):
    """Independent event-edge maximum for disjoint periodic intervals.

    Used for tests/diagnostics; production bound below also covers edge error.
    Window integral changes slope only at an edge or an edge minus remainder.
    """
    if h < 0 or period <= 0:
        raise ValueError("invalid period/window")
    last = F(0)
    for a, z in intervals:
        if not last <= a <= z <= period:
            raise ValueError("overlapping/out-of-period intervals")
        last = z
    n, r = divmod(h, period)
    total = sum(z-a for a, z in intervals)
    candidates = {F(0)}
    for a, z in intervals:
        for e in (a, z):
            candidates.update((e % period, (e-r) % period))
    def at(x):
        return sum(max(F(0), min(x+r, z+k*period)-max(x, a+k*period))
                   for a, z in intervals for k in (0, 1))
    return n*total+max(at(x) for x in candidates)


def peak_bound(b, g, h_ns, x_rate, x_burst_ns, K=None):
    """Conditional paired-calendar resource bound, not selection of a rule.

    At slots 2gm and 2gm+c, use charged lengths r or c. The physical
    operation releases earlier. K counts ALL correction intervals intersecting
    the window, including a carry-in interval; never a mission-average count.
    Without such a contract the all-correction bound is mandatory.
    """
    c = b["charge_ticks_with_margin"]["read_ERR_repair"]
    r = b["charge_ticks_with_margin"]["read_no_ERR"]
    tm, tp, j = (b[k] for k in ("tick_min_ns", "tick_max_ns", "edge_span_ns"))
    period = 2*g*tm
    duration = 2*c*tp+j
    if g < c or duration > period:
        return {"nonoverlap": False, "peak_upper": None, "reason": "paired worst-case reservations overlap"}
    full = mask(h_ns, period, duration)
    read = min(full, 2*mask(h_ns, period, r*tp+j))
    if K is not None and K < 0:
        raise ValueError("negative correction cap")
    work = full if K is None else min(full, read+K*(c-r)*tp)
    peak = work/h_ns+x_rate+x_burst_ns/h_ns
    return {"nonoverlap": True, "peak_upper": peak, "full_control_ns": full,
            "read_control_upper_ns": read, "control_upper_ns": work,
            "correction_cap_intersecting_window": K, "slack_to_80_percent": F(4,5)-peak}


def calculate():
    cfg, legacy, h, a, rows = inputs()
    b = timing_budget(cfg, h)
    margins = pin_margins(cfg, b)
    if min(margins.values()) < 0:
        raise ValueError("invalid candidate pin allocation")
    f, res = h["fixed_contract"], h["resources"]
    W = f["W"]
    upper = b["upper_ns"]
    r, c = (b["charge_ticks_with_margin"][k] for k in ("read_no_ERR", "read_ERR_repair"))
    tm, tp, j = (b[k] for k in ("tick_min_ns", "tick_max_ns", "edge_span_ns"))
    h_ns, x_burst = F(res["peak_window_s"])*10**9, F(res["sigmaX_s"])*10**9
    x_rate = F(res["CX"])
    # M(h,p,d) <= h*d/p+d gives a closed-form sufficient g; no grid search.
    # This concerns only bus resources, not Q(T) or a new scientific calendar.
    duration = 2*c*tp+j
    remaining_rate = F(4,5)-x_rate-(x_burst+duration)/h_ns
    if remaining_rate <= 0:
        raise ValueError("no sufficient g from this boundary bound")
    sufficient_g = duration/(2*tm*remaining_rate)
    resource_g = b["core_ticks"]*ceil(max(F(c+1), sufficient_g)/b["core_ticks"])
    resource = peak_bound(b, resource_g, h_ns, x_rate, x_burst)
    if not resource["nonoverlap"] or resource["peak_upper"] > F(4,5):
        raise ValueError("closed-form resource bound failed")
    read_peak = peak_bound(b, resource_g, h_ns, x_rate, x_burst, 0)
    end_ticks = b["control_ticks"]["release_if_ERR"]
    gap_ticks = max(c-end_ticks, 2*resource_g-c-end_ticks)
    requests = {
        "read16_no_inline_repair": b["charge_ticks_with_margin"]["application_read16"],
        "read16_with_inline_repair": c,
        "read32_atomic_no_inline_repair": b["charge_ticks_with_margin"]["application_read32_atomic"],
        "write32_atomic": b["charge_ticks_with_margin"]["application_write32_atomic"],
    }
    atomic_gaps = {name: {"request_charge_ticks": ticks,
                         "fits_one_gap_at_resource_example": ticks <= gap_ticks,
                         "g_sufficient_for_one_gap_only": b["core_ticks"]*ceil(F(c+end_ticks+ticks, 2*b["core_ticks"]))}
                   for name, ticks in requests.items()}
    boundaries = []
    for row in rows:
        s = row["selected_source_row"]
        g = s["g"]
        boundaries.append({
            "shield_g_cm2": row["shield"], "Dstar": s["Dstar"], "old_g": g, "old_ka": s["ka"],
            "old_period_ticks": W*g, "old_period_upper_ns": W*g*tp,
            "old_calendar_no_ERR_margin_deficit_ns": b["margin_factor"]*upper["read_no_ERR"]-(s["c"]*tm-j),
            "old_calendar_ERR_overlap_ns": upper["read_ERR_repair"]-(s["c"]*tm-j),
            "new_reservation_unchanged_g": peak_bound(b, g, h_ns, x_rate, x_burst),
            "new_Q_upper": None, "new_quiet_control_load": None,
        })
    # Original early cutoff kept ONLY as a diagnostic allocation comparison.
    p = a["parameters"]
    cutoff = ((p["window"]+p["delivery"])//b["core_ticks"])*b["core_ticks"]
    post_path_ns = ((cutoff-p["window"])*tm-j)/b["margin_factor"]
    report = {
        "status": cfg["status"], "previous_delivery_sha": cfg["previous_delivery_sha"],
        "science_sha_unchanged": legacy["science_sha"], "stage_A_sha_unchanged": legacy["stage_A_sha"],
        "source_blobs": legacy["sources"], "historical_gate_blobs": cfg["legacy_blobs"],
        "primary_documents": [legacy["datasheet"], cfg["application_note"]],
        "budget": b, "pin_and_margin_slack_ns": margins,
        "internal_write": {"external_reads_per_visit": 1, "external_writes_no_ERR": 0,
                           "external_writes_ERR": 1, "external_writes_unconditional": 1,
                           "extra_external_internal_RMW_cycle": False,
                           "microscopic_full38_commit_time": None},
        "completed_pass": {
            "W": W, "K_domain": [0, W], "formula_ns": "W*R + K*(E-R)",
            "K_zero_upper_ns": pass_occupancy(W, 0, upper["read_no_ERR"], upper["read_ERR_repair"]),
            "K_all_upper_ns": pass_occupancy(W, W, upper["read_no_ERR"], upper["read_ERR_repair"]),
            "max_busy_time_saving_fraction": 1-upper["read_no_ERR"]/upper["read_ERR_repair"],
            "unchanged_calendar_period_saving_ns": 0,
            "fixed_new_calendar_period_formula_ns": "W*g*xi; same for E and unconditional comparator",
            "compact_serial_no_application_optimistic_ns": "sum of visit upper times; not certified service period",
            "charged_work_ticks_formula": f"{W}*{r} + K*({c}-{r})",
            "unfinished_pass": "charge actual intersection of each busy interval with measurement horizon; never drop a pending tail",
        },
        "old_rows_not_transferred": boundaries,
        "resource_algebra_only": {
            "status": "conditional sufficient resource witness, NOT proposed/accepted scientific calendar",
            "assumes_old_X_envelope_still_satisfied": True,
            "old_X_envelope_revalidated": False,
            "g_core_aligned_sufficient": resource_g, "c_charge_ticks": c, "r_charge_ticks": r,
            "g_sufficient_before_rounding": sufficient_g,
            "derivation": "M(h,p,d)<=h*d/p+d; g>=d/[2*xi_min*(0.8-CX-(sigmaX+d)/h)]; no grid search",
            "worst_corrections_every_visit": resource,
            "no_corrections_in_expanded_window": read_peak,
            "lower_adjacent_core_g": peak_bound(b, resource_g-b["core_ticks"], h_ns, x_rate, x_burst),
            "period_upper_ns": W*resource_g*tp,
            "last_start_ticks_in_first_pass": W*resource_g-2*resource_g+c,
            "first_pass_release_upper_ns_no_ERR": (W*resource_g-2*resource_g+c+b["control_ticks"]["release_if_no_ERR"])*tp+j,
            "first_pass_release_upper_ns_all_ERR": (W*resource_g-2*resource_g+c+b["control_ticks"]["release_if_ERR"])*tp+j,
            "only_last_visit_release_saving_ns": (b["control_ticks"]["release_if_ERR"]-b["control_ticks"]["release_if_no_ERR"])*tp,
            "period_not_selected_for_any_shield": True,
            "correction_envelope": "K_I <= N visits whose correction intervals intersect I; no smaller bound currently supplied",
            "longest_all_ERR_gap_ticks_at_actual_release": gap_ticks,
            "longest_no_ERR_gap_ticks_at_actual_release": max(c-b["control_ticks"]["release_if_no_ERR"], 2*resource_g-c-b["control_ticks"]["release_if_no_ERR"]),
            "atomic_gap_checks": atomic_gaps,
            "atomic_gap_scope": "one request can fit only; not a traffic/delay guarantee; fixed next control starts cannot move",
        },
        "command_comparison_only": {
            "old_early_cutoff_ticks": cutoff, "total_post_window_with_old_deadline_ns": post_path_ns,
            "remaining_before_mailbox_ns": post_path_ns-b["outside_lock_upper_ns"]["command_receive_validate_shadow"],
            "actual_monitor_CPU_path_ns": None, "new_scientific_deadline": None,
            "early_semantics": "inactive validated shadow; exact nominal not_before; alarms revoke shadow and active before future decisions; no retroactive skip",
        },
        "queue": {"repair_depth": 1, "repair_never_deferred": True,
                  "application_depth_candidate": cfg["design"]["application_queue_candidate_entries"],
                  "count_contract": "B >= ceil(b_count+rho_count*D_offer_to_departure); include CDC and held responses",
                  "D_offer_to_departure_ns": None,
                  "entries_if_old_diagnostic_count_and_whole_3us_delay_hold": ceil(F(cfg["design"]["application_count_burst_diagnostic"])+F(cfg["design"]["application_count_rate_diagnostic_per_s"])*F(res["app_delay_with_margin_limit_s"])),
                  "depth_certified": False},
        "unknowns": cfg["unqualified"],
        "decision": {"budget_pin_constraints_satisfied_conditionally": True, "physical_WCET_qualified": False,
                     "new_risk_certificate": False, "main_RTL_started": False, "stages_C_D_started": False}
    }
    handoff = {
        "task": 104, "scope": "Option 2 timing inputs for addressed theoretical supplement; not a new scientific SHA",
        "new_scientific_SHA": None,
        "report": "outputs/budget.json", "config": "budget_config.json",
        "previous_engineering_sha": cfg["previous_delivery_sha"], "T95_sha": legacy["science_sha"],
        "A_sha": legacy["stage_A_sha"], "T90_sha": h["T90_sha"], "T88_sha": h["T88_sha"],
        "pinned_sources": legacy["sources"],
        "T95_baseline_unchanged_not_new_timing": f, "monitor_baseline": h["monitor"],
        "loss_policy_unchanged": h["loss_policy"], "T95_resource_baseline_not_new_atomic_limit": res,
        "fixed_goals": {"epsilon": f["epsilon"], "T_s": f["T_s"], "time_margin": f["time_margin"],
                        "peak_limit": res["peak_limit"], "peak_window_s": res["peak_window_s"],
                        "app_delay_with_margin_limit_s": res["app_delay_with_margin_limit_s"],
                        "quiet_control_load_limit": "1/100"},
        "rows": [{"shield": row["shield"], "Dstar": row["selected_source_row"]["Dstar"],
                  "environment": row["effective_T88_input"]["environment"],
                  "quotas": row["effective_T88_input"]["quotas"],
                  "mark_contract": row["effective_T88_input"]["mark_contract"],
                  "old_application_contract": row["effective_T88_input"]["service"]["application_contract"],
                  "source_selector": f"{h['working_selector']['path']} shield={row['shield']}",
                  "new_selected_calendar": None, "new_Q_upper": None} for row in rows],
        "proposed_service_timing": b,
        "must_reprove": [
            "E is not clean-U: a hit after clean observation and before old fence survives with no write",
            "service/observation epochs and all in-operation hits, full38 ERR lower contract and existing delta_svc",
            "paired calendar/nonoverlap, intervals per full word, initial scan, mandatory phases and finite horizon edges",
            "command freeze/LOW/hold/lease with bounded edge error and full path; no early or retroactive permissions",
            "Q(T) and probability margin at unchanged Dstar/environment/quotas for each shielding row",
            "quiet control occupancy, returns, monitor loss with same whole-history U_M, availability",
            "every sliding 1ms peak including arbitrary correction clusters/repeats and channel/control work",
            "application transaction width and unchanged offered useful work, first-VALID delay, finite queue and CDC",
            "strong constant-period E competitor with same implementation and a new justified lower price bound"
        ],
        "missing_physical_inputs": cfg["unqualified"],
        "next": "new scientific SHA + checked new reference/contract before main RTL; old T95/A are immutable"
    }
    return encode(report), encode(handoff)
