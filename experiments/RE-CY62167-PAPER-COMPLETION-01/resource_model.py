from __future__ import annotations

N_READ_R1 = 2**19
N_READ_R2 = 2**21
T_RC = 45e-9
T_WC = 45e-9

TIMING_AUDIT = [
    {"parameter": "tRC", "value_ns": 45.0, "conditions": "45-ns grade; read cycle time minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Read Cycle"},
    {"parameter": "tAA", "value_ns": 45.0, "conditions": "address to data/ERR valid maximum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Read Cycle"},
    {"parameter": "tOHA", "value_ns": 10.0, "conditions": "data/ERR hold from address change minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Read Cycle"},
    {"parameter": "tWC", "value_ns": 45.0, "conditions": "45-ns grade; write cycle time minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Write Cycle"},
    {"parameter": "tSCE", "value_ns": 35.0, "conditions": "chip-enable active to write end minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Write Cycle"},
    {"parameter": "tAW", "value_ns": 35.0, "conditions": "address setup to write end minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Write Cycle"},
    {"parameter": "tHA", "value_ns": 0.0, "conditions": "address hold from write end minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Write Cycle"},
    {"parameter": "tSA", "value_ns": 0.0, "conditions": "address setup to write start minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Write Cycle"},
    {"parameter": "tPWE", "value_ns": 35.0, "conditions": "WE pulse width minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Write Cycle"},
    {"parameter": "tSD", "value_ns": 25.0, "conditions": "data setup to write end minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Write Cycle"},
    {"parameter": "tHD", "value_ns": 0.0, "conditions": "data hold from write end minimum", "datasheet_page": 10, "table_or_figure": "Switching Characteristics / Write Cycle"},
    {"parameter": "tHZWE", "value_ns": 18.0, "conditions": "WE low to output High-Z maximum; with OE LOW note requires tPWE >= tHZWE+tSD", "datasheet_page": 10, "table_or_figure": "Switching Characteristics notes 31,34 / Fig.11"},
    {"parameter": "read_write_transition_gap", "value_ns": 0.0, "conditions": "no additional independent recovery gap identified beyond declared tRC/tWC and write setup/hold constraints in Figs. 10-14; DECLARED SERIAL BUS-OCCUPANCY MODEL only", "datasheet_page": "10-14", "table_or_figure": "Switching Characteristics and waveforms"},
]


def reads_per_cycle(scan_mode: str) -> int:
    if scan_mode == "R1": return N_READ_R1
    if scan_mode == "R2": return N_READ_R2
    raise ValueError("scan_mode must be R1 or R2")


def resource_semantics(tau_s: float, scan_mode: str, write_policy: str):
    """Semantic classification for the frozen serial resource model.

    For ERR-assisted policy E, the read-only quantity is a necessary read-time
    lower bound, not an exact total cost or architectural minimum. A sufficient
    full-pass feasibility check is also reported using the declared worst case
    of at most one write per read. Expected write cost remains unknown.
    """
    reads = reads_per_cycle(scan_mode)
    read_floor = reads * T_RC
    worst_full = reads * (T_RC + T_WC)
    read_ok = tau_s >= read_floor
    worst_ok = tau_s >= worst_full
    if write_policy == "U":
        return {"read_only_floor_s": read_floor,"necessary_read_time_feasible": read_ok,"worst_case_full_pass_bound_s": worst_full,"sufficient_full_pass_feasible": worst_ok,"full_pass_feasibility_status": "SUFFICIENT-FULL-PASS-FEASIBLE" if worst_ok else "FULL-PASS-INFEASIBLE-FOR-DECLARED-U-SCAN","resource_value_semantics": "EXACT-DECLARED-U-SERIAL-TOTAL","write_cost_status": "DEFINED-UNCONDITIONAL-ONE-WRITE-PER-READ","expected_total_cost_status": "DEFINED-FOR-DECLARED-U-MODEL"}
    if write_policy == "E":
        return {"read_only_floor_s": read_floor,"necessary_read_time_feasible": read_ok,"worst_case_full_pass_bound_s": worst_full,"sufficient_full_pass_feasible": worst_ok,"full_pass_feasibility_status": "SUFFICIENT-UNDER-AT-MOST-ONE-WRITE-PER-READ" if worst_ok else "WORST-CASE-FULL-PASS-NOT-CERTIFIED","resource_value_semantics": "READ-ONLY-LOWER-BOUND","write_cost_status": "UNKNOWN-EXPECTED-WRITE-COST","expected_total_cost_status": "UNKNOWN-WITHOUT-ERR-WRITE-MODEL"}
    raise ValueError("write_policy must be U or E")


def tau_min_arch(scan_mode: str, write_policy: str, expected_writes_per_cycle: float | None = None):
    reads = reads_per_cycle(scan_mode)
    if write_policy == "U":
        writes = reads
        return reads * T_RC + writes * T_WC, writes, "DECLARED SERIAL BUS-OCCUPANCY MODEL"
    if write_policy == "E":
        if expected_writes_per_cycle is None:
            return reads * T_RC, None, "LEGACY NUMERIC FIELD: deterministic read-only lower bound; NOT an architectural minimum; ERR expected write cost is model-dependent"
        return reads * T_RC + expected_writes_per_cycle * T_WC, expected_writes_per_cycle, "DECLARED SERIAL BUS-OCCUPANCY MODEL with supplied expected writes"
    raise ValueError("write_policy must be U or E")


def resource_at_period(tau_s: float, scan_mode: str, write_policy: str, expected_writes_per_cycle: float | None = None):
    if tau_s <= 0: raise ValueError("tau must be positive")
    reads = reads_per_cycle(scan_mode)
    min_tau, writes, note = tau_min_arch(scan_mode, write_policy, expected_writes_per_cycle)
    reads_s = reads / tau_s
    if writes is None:
        writes_s = None
        interface = reads_s * T_RC
    else:
        writes_s = writes / tau_s
        interface = reads_s * T_RC + writes_s * T_WC
    sem = resource_semantics(tau_s, scan_mode, write_policy)
    if write_policy == "E" and expected_writes_per_cycle is not None:
        sem = dict(sem); sem["resource_value_semantics"] = "DECLARED-TOTAL-WITH-SUPPLIED-EXPECTED-WRITES"; sem["write_cost_status"] = "SUPPLIED-EXPECTED-WRITES"; sem["expected_total_cost_status"] = "DEFINED-CONDITIONALLY-ON-SUPPLIED-WRITES"
    margin = tau_s / min_tau if min_tau > 0 else float("inf")
    if write_policy == "E" and expected_writes_per_cycle is None:
        status = "NECESSARY-READ-TIME-FEASIBLE" if sem["necessary_read_time_feasible"] else "READ-TIME-INFEASIBLE"
    else:
        status = "ARCHITECTURALLY-FEASIBLE" if margin >= 1 else "ARCHITECTURALLY-INFEASIBLE-FOR-DECLARED-SCAN"
    return {"reads_per_cycle": reads,"writes_per_cycle_or_expected": writes if writes is not None else "MODEL_DEPENDENT","t_read_effective_s": T_RC,"t_write_effective_s": T_WC,"tau_min_arch_s": min_tau,"tau_min_arch_interpretation": "LEGACY-E-READ-ONLY-FLOOR" if write_policy == "E" and expected_writes_per_cycle is None else "DECLARED-FULL-PASS-QUANTITY","resource_margin": margin,"period_feasible": sem["necessary_read_time_feasible"] if write_policy == "E" and expected_writes_per_cycle is None else margin >= 1,"architecture_status": status,"reads_per_s": reads_s,"writes_per_s": writes_s if writes_s is not None else "MODEL_DEPENDENT","interface_fraction": interface,"interface_percent": interface * 100.0,"interface_value_semantics": "READ-ONLY-LOWER-BOUND" if writes is None else "DECLARED-TOTAL","note": note,**sem}


def old_article_interface_fraction(tau_s: float) -> float:
    return resource_at_period(tau_s, "R2", "U")["interface_fraction"]
