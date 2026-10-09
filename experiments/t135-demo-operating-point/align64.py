"""T135 r3: exact reconciliation with the registered 250/50 lane.

One previously selected row, no search, no RTL/STA invocation. Imports accepted
arithmetic read-only. Historical r1/r2 reports and scientific sources unchanged.
"""
import argparse
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('t135_r2_for_r3', HERE/'reconcile.py')
r2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r2)
b = r2.b
ENGINEER = 'eab470df3c4a33b101aaa4eeab64c426b9f10aeb'
PARENT = 'b3bbc5f2171c66ac4b975060111aab704ab3734b'
ENGINEER_BASE = 'experiments/t104-rtl-resume/registered/'
NS = F(1, 10**9)


def git_bytes(sha, path):
    return subprocess.check_output(['git', 'show', sha+':'+path], cwd=b.ROOT)


def edge_bound(T, fast_period_min, endpoint_span):
    if T < 0 or fast_period_min <= 0 or endpoint_span < 0:
        raise ValueError('invalid clock/horizon domain')
    return int((T+endpoint_span)//fast_period_min)+2


def generation_certificate(T=F(315576000), bits=64, initial=0):
    n = edge_bound(T, 4*b.TM, b.J)
    if initial < 0 or initial >= 2**bits-1:
        raise ValueError('unqualified initial generation')
    return dict(horizon_s=T, bits=bits, initial=initial, max_edges_upper=n,
                final_generation_upper=initial+n, saturation_value=2**bits-1,
                saturation_unreachable=initial+n < 2**bits-1,
                max_increments_per_edge=1, runtime_reset_allowed=False,
                extra_saturation_unavailability_s=0 if initial+n < 2**bits-1 else None,
                scope='all fast edges, including coalesced invalidate/config; no ERR-count assumption')


def source_checks():
    names = ['contract_check.py', 'contract.json', 'generation_guard.sv',
             'HANDOFF.md', 'REPORT.md', 'operation_lane.sv', 'handshake_channel.sv']
    src = {name: git_bytes(ENGINEER, ENGINEER_BASE+name) for name in names}
    assert src['contract.json'] == (HERE/'inputs/t104-eab470d-contract.json').read_bytes()
    scope = {'__name__': 'read_only_engineer_contract'}
    exec(compile(src['contract_check.py'], ENGINEER_BASE+'contract_check.py', 'exec'), scope)
    engineer = json.loads(src['contract.json'])
    assert scope['calculate']() == engineer  # no __main__, no report write
    cert = generation_certificate()
    assert cert['max_edges_upper'] == engineer['max_edges_upper']
    assert cert['bits'] == engineer['implemented_bits'] == 64
    assert cert['saturation_unreachable'] and cert['max_edges_upper'] < 2**57
    ops = r2.operation_inputs('operations_250')
    for key, field in {'R':'R_s', 'E':'E_s', 'read32':'read32_s',
                       'observed_write32':'observed_write32_s'}.items():
        assert F(engineer['component_deadlines_ns'][key])*NS == ops[field]
    # Structural checks of the actual pinned component, NOT composed RTL proof.
    guard = src['generation_guard.sv'].decode()
    assert 'parameter integer BITS=64' in guard
    assert 'generation=0' in guard and 'input wire clk, loss, err_event, invalidate' in guard
    assert 'err_event || invalidate || (loss && !previous_loss)' in guard
    assert "if(change && !exhausted) generation<=generation+1'b1;" in guard
    assert '!loss && !err_event && !invalidate' in guard
    assert 'candidate_generation==generation' in guard
    lane = src['operation_lane.sv'].decode()
    assert 'output wire [63:0] generation' in lane
    assert ".candidate_generation(64'd0)" in lane and ".candidate_valid(1'b0)" in lane
    return {ENGINEER_BASE+n: hashlib.sha256(v).hexdigest() for n, v in src.items()}


def timing_ledger():
    old = r2.timing_ledger()
    parts = dict(old['engineer_components_s'])
    # Same endpoints of each existing handshake interval: add a source cycle
    # to its coefficient. Endpoint jitter is already paid, not per register.
    di, do = 20*b.TP, 4*b.TP
    parts['request_slow_queue_and_handshake_to_fast_consumer'] += di
    parts['response_handshake_and_slow_queue_to_consumer'] += do
    inbound = old['inbound_s']+di
    outbound = old['outbound_s']+do
    response = F('1.1')*(inbound+parts['wait_one_calendar_frame']+
                        parts['observed_write32']+outbound+F('100e-9'))
    return dict(components_s=parts, request_source_extra_s=di, reply_source_extra_s=do,
        inbound_s=inbound, outbound_s=outbound,
        inbound_budget_s=F('320e-9'), outbound_budget_s=F('320e-9'),
        inbound_unallocated_s=F('320e-9')-inbound,
        outbound_unallocated_s=F('320e-9')-outbound,
        decomposition_response_upper_s=response,
        integrated_inbound_WCET_s=None, integrated_outbound_WCET_s=None,
        status='conditional component placement only; integrated WCET remains unproved')


def unchanged_sources():
    old = json.loads((HERE/'report.json').read_text())
    assert b.source_pins() == old['source_sha256']
    names = ['calculate.py', 'config.json', 'report.json', 'test_contract.py', 'verify.py',
             'reconcile.py', 'test_reconcile.py', 'report-r2.json', 'verification-r2.txt']
    result = {}
    for name in names:
        data = (HERE/name).read_bytes()
        assert data == git_bytes(PARENT, 'experiments/t135-demo-operating-point/'+name)
        result[name] = hashlib.sha256(data).hexdigest()
    return result


def validate_common_contract(cfg, row, cert, timing):
    assert cfg['revision'] == 3 and cfg['engineer_input_sha'] == ENGINEER
    assert cfg['scientific_parent_sha'] == PARENT
    c, s, rec = row['calendar'], row['service'], cfg['recommended']
    assert rec['generation_bits_required'] == cert['bits'] == rec['delivered_generation_bits']
    assert rec['generation_end_to_end_proved'] is False
    assert rec['generation_clock_bound']['max_edges_upper'] == cert['max_edges_upper']
    assert F(rec['effective_ERR_or_loss_rule_s']) == s['ERR_or_loss_to_rule_s'] == F('10e-6')
    fields = {'N_w':'w_count', 'N_h':'h_count', 'N_recovery':'recovery_count',
              'bits':'timer_counter_bits', 'tau_s':'tau',
              'recovery_lower_s':'recovery_hold_lower', 'recovery_upper_s':'recovery_hold_upper',
              'extra_rounding_s':'recovery_rounding_extra'}
    for key, field in fields.items():
        assert F(rec['timers'][key]) == c[field], key
    for key, field in {'inbound_component_sum_s':'inbound_s',
                       'outbound_component_sum_s':'outbound_s',
                       'inbound_unallocated_s':'inbound_unallocated_s',
                       'outbound_unallocated_s':'outbound_unallocated_s',
                       'decomposition_response_upper_s':'decomposition_response_upper_s'}.items():
        assert F(cfg['registered_preparation'][key]) == timing[field], key
    for key, field in {'application_inbound_s':'request_to_queue_s',
                       'application_outbound_s':'release_to_response_s',
                       'local_dispatch_s':'decision_transport_s'}.items():
        assert F(rec[key]) == s[field], key
    assert all(value is None for value in cfg['actual_integrated_bounds'].values())


def report():
    pins = source_checks()
    historical = unchanged_sources()
    cfg = json.loads((HERE/'common-contract.json').read_text())
    p = b.environment()
    s = dict(b.prefetch_service(), ERR_or_loss_to_rule_s=F('10e-6'))
    # Recompute the accepted joint bound at the exact unchanged c/g/freeze.
    # r2 returns both price variants; discard only its 32-bit saturation charge.
    row = r2.joint(p, s)
    prior = json.loads((HERE/'report-r2.json').read_text())['rows']['recommended_250']
    for key in ('risk_upper', 'slack', 'relative_slack'):
        assert row[key] == F(prior[key]), key
    assert b.serial(row['calendar']) == prior['calendar']
    assert b.serial(row['resources']) == prior['resources']
    prof = next(x for x in b.accepted.CFG['profiles'] if x['name']=='MCU_calibrated_write')
    with b.price_parameters(s):
        price = b.accepted.price(p, row['calendar'], prof, row['risk_upper'], 2)
    price = b.pay_recovery_rounding(price, p, row['calendar'], s)
    app = s['observed_write32_s']*F(b.CFG['application']['mean_write_s'])
    app += s['read32_s']*F(b.CFG['application']['mean_read_s'])
    old_quiet, old_mission = row['full_bus_quiet'], row['full_bus_mission']
    row['full_bus_quiet'] = min(row['full_bus_mask'], price['quiet_upper_intercept']+app)
    row['full_bus_mission'] = min(row['full_bus_mask'], price['mission_upper_intercept']+app)
    assert row['full_bus_quiet'] == F(prior['full_bus_quiet_without_saturation'])
    assert row['full_bus_mission'] == F(prior['full_bus_mission_without_saturation'])
    for key in ('saturation', 'saturation_quiet_price_increment', 'saturation_mission_price_increment',
                'full_bus_quiet_without_saturation', 'full_bus_mission_without_saturation'):
        row.pop(key)
    row.update(price=price, price_bad_probability=row['risk_upper'],
               saturation_probability=F(0), saturation_price_increment=F(0))
    cert, timing = generation_certificate(), timing_ledger()
    assert cert['saturation_unreachable']
    validate_common_contract(cfg, row, cert, timing)
    assert timing['inbound_unallocated_s'] >= 0 and timing['outbound_unallocated_s'] >= 0
    local = ['align64.py', 'test_align64.py', 'common-contract.json']
    return dict(task=135, revision=3, scientific_parent=PARENT, engineer_sha=ENGINEER,
        instructions_sha=cfg['instructions_sha'], environment=p, recommended_250_64=row,
        generation=cert, timing=timing,
        change_from_r2=dict(risk=F(0), resources_unchanged=True, calendar_unchanged=True,
            quiet_price=row['full_bus_quiet']-old_quiet,
            mission_price=row['full_bus_mission']-old_mission),
        reference_alternatives=dict(report='report-r2.json', recomputed=False,
            note='cap/100MHz historical conditional rows retain their stated 32-bit price convention; not the selected 64-bit interface'),
        actual_integrated_bounds=cfg['actual_integrated_bounds'],
        engineer_source_sha256=pins, accepted_source_sha256=b.source_pins(),
        unchanged_local_sha256=historical,
        local_source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in local})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()
    out = report()
    text = json.dumps(b.serial(out), ensure_ascii=False, indent=2)+'\n'
    path = HERE/'report-r3.json'
    if args.write:
        path.write_text(text)
    else:
        assert path.read_text() == text, 'T135 r3 report mismatch'
    row = out['recommended_250_64']
    for key in ('risk_upper', 'slack', 'relative_slack', 'full_bus_quiet', 'full_bus_mission'):
        print(key, b.accepted.old.text_number(row[key], digits=17))
    print('T135 r3 report written.' if args.write else 'T135 r3 report reproduced byte-for-byte.')


if __name__ == '__main__':
    main()
