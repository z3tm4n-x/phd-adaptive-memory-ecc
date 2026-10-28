"""Exact service-only preflight for #186. Does not evaluate radiation/Q.

Reuse the accepted full39 service and timing functions. No model family or
N0/N+/M policy is synthesized while the theorist's definitions are pending.
"""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / 'experiments/t186-method-comparison/code-strength'
sys.path.insert(0, str(BASE))
spec = importlib.util.spec_from_file_location('accepted_service', BASE / 'comparison.py')
cmp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmp)
NS = 10**9


def sha(data):
    return hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()


def encode(value):
    return (json.dumps(value, default=str, sort_keys=True, indent=2) + '\n').encode()


def load():
    inputs = json.loads((HERE / 'RESOURCE_INPUTS.json').read_text(encoding='utf-8'))
    for path, digest in inputs['source_sha256_LF'].items():
        if sha((ROOT / path).read_bytes()) != digest:
            raise ValueError('Resource dependency changed: ' + path)
    cfg = json.loads((BASE / 'common-input.json').read_text(encoding='utf-8'))
    return inputs, cfg


def configuration(cfg, useful_bytes):
    if type(useful_bytes) is not int or useful_bytes <= 0 or useful_bytes % 4:
        raise ValueError('Integral useful 32-bit words required')
    W = useful_bytes // 4
    if W % 8 or W & (W - 1):
        raise ValueError('Declared bank must have power-of-two W divisible by 8')
    answer = deepcopy(cfg)
    answer['words'] = W
    answer['useful_bytes'] = useful_bytes
    return answer


def slot(j, cal):
    return cal['frame_ticks'] * (j // cal['batch_size']) + cal['c_ticks'] * (j % cal['batch_size'])


def preflight(cfg, useful_bytes):
    cfg = configuration(cfg, useful_bytes)
    W = cfg['words']; T = F(cfg['mission_s']); cal = cfg['calendar']
    s = cmp.service(cfg, 39)
    frame = F(cal['frame_ticks']); xm, xp, J = s['xminus'], s['xplus'], s['J']
    assert cal['batch_size'] == 8 and cal['g_ticks'] * 8 == frame
    assert cal['application_grant_phase_ticks'] == 1312
    assert slot(W, cal) == W * cal['g_ticks']
    period = cmp.period(cfg, 1)
    inherited = cmp.timing(cfg, 39, 1)
    offered_reads = int(cmp.count_apps(cfg)['read'])
    completed_lower = max(0, offered_reads - 1)
    assert inherited['app_response_upper_ns'] < cfg['application']['epoch_ns']
    bus_read_lo = max(F(0), 3 * cfg['service']['read_beat_ns'] * xm - J)
    bus_read_hi = 3 * cfg['service']['read_beat_ns'] * xp + J
    app_lower = completed_lower * s['lower']['app_read'] / (T * NS)
    app_upper = offered_reads * s['upper']['app_read'] / (T * NS)
    cap = F(cfg['constraints']['peak_bus_fraction'])
    peak_ns = F(cfg['constraints']['peak_window_ns'])
    assert (T * NS) % peak_ns == 0  # partition [0,T] into existing 1ms caps
    management_chunk_hi = 64 * xp + J
    management_chunk_lo = 64 * xm - J
    # Existing PR261 slot1472..1536, not extra parallel bandwidth.
    frames = inherited['counted_control_operations'] // cal['batch_size']
    mgmt_peak = frames * management_chunk_hi / peak_ns
    total_peak = inherited['peak_bus_core_upper'] + mgmt_peak
    gap_left = 160 * xm - J - s['upper']['app_write']
    gap_right = 96 * xm - J - management_chunk_hi
    response_read = (sum(F(cfg['application'][k]) for k in
                         ('inbound_ns', 'ready_ns', 'outbound_ns', 'backpressure_ns'))
                     + frame * xp + J + s['upper']['app_read'])
    assert gap_left > 0 and gap_right > 0
    assert inherited['control_slack_ns'] > 0 and inherited['application_aperture_slack_ns'] > 0
    assert total_peak < cap and response_read <= inherited['app_response_upper_ns']
    return dict(
        useful_bytes=useful_bytes, words=W, active_code_bits=39 * W,
        raw_storage_required_bytes=6 * W, hardware_capacity_confirmed=False,
        per_bit_reference_positions=cfg['environment']['reference_words'] * cfg['environment']['reference_bits'],
        array_scale_from_reference=F(39 * W, cfg['environment']['reference_words'] * cfg['environment']['reference_bits']),
        calendar=dict(nominal_minimum_full_pass_cycle_ns=period['nominal_ns'],
                      cycle_lower_ns=period['lower_ns'], cycle_upper_ns=period['upper_ns'],
                      phase_formula='q(j)=1568*floor(j/8)+164*(j mod8), word=3j modW',
                      minimum_scope='full-pass grid; whole constant class also needs the necessary-count comparison below',
                      necessary_class_maximum_reads_upper=cmp.read_bounds(cfg, 1)['upper'],
                      necessary_count_exclusion='N_fixed_required_lower > maximum_reads_upper; do not impose candidate k-grid on arbitrary constant phases',
                      counter_drain_added=False, app_slots_reallocated=False),
        application=dict(offered_reads=offered_reads, completed_reads_lower=completed_lower,
                         useful_writes=0, read_repair=False, read_emits_ERR=False,
                         read_rate_per_s=F(offered_reads, T),
                         serial_mission_lower=app_lower, serial_mission_upper=app_upper,
                         pure_bus_mission_lower=completed_lower * bus_read_lo / (T * NS),
                         pure_bus_mission_upper=offered_reads * bus_read_hi / (T * NS),
                         read_response_upper_ns=response_read,
                         inherited_response_envelope_ns=inherited['app_response_upper_ns'],
                         response_deadline_ns=cfg['constraints']['application_deadline_ns'],
                         inherited_deadline_margin_ns=inherited['app_deadline_slack_ns'],
                         optional_target_ns=cfg['constraints']['map_targets']['response_ns']),
        resource=dict(serial_cap=cap, cap_window_ns=peak_ns,
                      available_serial_upper_for_necessary_exclusion=cap-app_lower,
                      sufficient_serial_average_remainder_after_app_upper=cap-app_upper,
                      these_average_remainders_do_not_replace_local_peak_or_slots=True,
                      pure_bus_is_not_serial_core=True,
                      inherited_peak_all_E_and_both_app_streams=inherited['peak_bus_core_upper'],
                      old_management_slot_peak_upper=mgmt_peak,
                      peak_including_full_reserved_management_slot=total_peak,
                      peak_margin_for_unaccounted_serial_work=cap-total_peak,
                      optional_peak_target=F(cfg['constraints']['map_targets']['peak_bus_fraction']),
                      management_slot_nominal_ticks=[1472,1536],
                      management_chunk_lower_ns=management_chunk_lo,
                      conditional_atomic_limit_ns=32,
                      guaranteed_management_progress_ns=management_chunk_lo-32,
                      gap_after_worst_app_ns=gap_left, gap_before_next_control_ns=gap_right,
                      control_E_margin_ns=inherited['control_slack_ns'],
                      app_aperture_margin_ns=inherited['application_aperture_slack_ns'],
                      unknown_management_cost_CPU_energy_memory=True,
                      physical_WCET=False),
        initialization=dict(before_t0=True, encodes=W, write_beats=3*W,
                            serial_upper_s=W*s['upper']['initial']/NS,
                            serial_price_amortized_over_T=W*s['upper']['initial']/(T*NS),
                            pure_bus_upper_s=W*(56*xp+J)/NS,
                            not_subtracted_from_in_mission_resource=True),
        fixed_class_excluded=None, Q_type='not evaluated before new family publication',
        N0=None, Nplus=None, M=None, full_cost_comparison=None)


def calculate():
    inputs, cfg = load()
    rows = [preflight(cfg, b) for b in inputs['mandatory_and_control_useful_bytes']]
    return dict(status='SERVICE_PREFLIGHT_ONLY_THEORY_INPUT_PENDING',
                base_main=inputs['base_main'], plan_commit=inputs['plan_commit'],
                input_manifest_sha256=sha((HERE/'RESOURCE_INPUTS.json').read_bytes()),
                implementation_sha256=sha(Path(__file__).read_bytes()),
                rows=rows, mission_s=cfg['mission_s'],
                no_new_environment_or_Q_evaluated=True, no_constant_class_exclusion_claimed=True,
                old_results_overwritten=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    start = time.perf_counter()
    raw = encode(calculate())
    target = HERE / 'resource-result.json'
    if args.write:
        target.write_bytes(raw)
        print('Wrote four service rows; no new Q or policy calculation.')
    else:
        assert target.read_bytes().replace(b'\r\n', b'\n') == raw, 'Resource result drift'
        print('Resource replay verified; SHA256 '+sha(raw))
    print(f'Preflight elapsed {time.perf_counter()-start:.6f}s; not WCET or full-grid runtime.')
