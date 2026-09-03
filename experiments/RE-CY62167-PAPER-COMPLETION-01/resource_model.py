from __future__ import annotations

from dataclasses import dataclass

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
    if scan_mode == "R1":
        return N_READ_R1
    if scan_mode == "R2":
        return N_READ_R2
    raise ValueError("scan_mode must be R1 or R2")


def tau_min_arch(scan_mode: str, write_policy: str, expected_writes_per_cycle: float | None = None):
    reads = reads_per_cycle(scan_mode)
    if write_policy == "U":
        writes = reads
        return reads * T_RC + writes * T_WC, writes, "DECLARED SERIAL BUS-OCCUPANCY MODEL"
    if write_policy == "E":
        if expected_writes_per_cycle is None:
            return reads * T_RC, None, "ERR_ASSISTED_WRITE_COST = MODEL_DEPENDENT; returned tau is deterministic read-only floor"
        return reads * T_RC + expected_writes_per_cycle * T_WC, expected_writes_per_cycle, "DECLARED SERIAL BUS-OCCUPANCY MODEL with supplied expected writes"
    raise ValueError("write_policy must be U or E")


def resource_at_period(tau_s: float, scan_mode: str, write_policy: str, expected_writes_per_cycle: float | None = None):
    if tau_s <= 0:
        raise ValueError("tau must be positive")
    reads = reads_per_cycle(scan_mode)
    min_tau, writes, note = tau_min_arch(scan_mode, write_policy, expected_writes_per_cycle)
    reads_s = reads / tau_s
    if writes is None:
        writes_s = None
        interface = reads_s * T_RC
    else:
        writes_s = writes / tau_s
        interface = reads_s * T_RC + writes_s * T_WC
    margin = tau_s / min_tau if min_tau > 0 else float("inf")
    status = "ARCHITECTURALLY-FEASIBLE" if margin >= 1 else "ARCHITECTURALLY-INFEASIBLE-FOR-DECLARED-SCAN"
    return {
        "reads_per_cycle": reads,
        "writes_per_cycle_or_expected": writes if writes is not None else "MODEL_DEPENDENT",
        "t_read_effective_s": T_RC,
        "t_write_effective_s": T_WC,
        "tau_min_arch_s": min_tau,
        "resource_margin": margin,
        "period_feasible": margin >= 1,
        "architecture_status": status,
        "reads_per_s": reads_s,
        "writes_per_s": writes_s if writes_s is not None else "MODEL_DEPENDENT",
        "interface_fraction": interface if writes is not None else "READ_ONLY_FLOOR=" + repr(interface),
        "interface_percent": interface * 100.0 if writes is not None else "MODEL_DEPENDENT",
        "note": note,
    }


def old_article_interface_fraction(tau_s: float) -> float:
    return resource_at_period(tau_s, "R2", "U")["interface_fraction"]
