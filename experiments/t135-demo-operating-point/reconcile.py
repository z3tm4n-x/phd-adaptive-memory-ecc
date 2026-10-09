"""T135 r2: finite sensitivity and composition with engineering SHA 5498bf5.

No accepted source or v1 report mutation. All decisions use exact fractions
and the accepted directed interval majorants. No RTL/STA execution.
"""
import argparse
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('t135_v1',HERE/'calculate.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
ENGINEER='5498bf5790cc8f90a26cc3a556e64768d31cbdbf'
OLD='71fa4680d1e737bb1fb3b0cce31ee24cec410f4a'
INPUT=HERE/'inputs/t104-5498bf5-timing_balance.json'
E=json.loads(INPUT.read_text())
NS=F(1,10**9)


def operation_inputs(group):
    names=dict(R='R_s',E='E_s',write16='write16_s',
               read32='read32_s',observed_write32='observed_write32_s')
    return {dest:F(E[group][src]['max_ns'])*NS for src,dest in names.items()}


def count_bound(p):
    pc=b.accepted.CFG['price_contract']
    # BEFORE the first physical/observation bad history: one principal ERR
    # per word touch, at most one extra per predictable aperture hit, initial
    # residual, false flags, and loss rises (including an ongoing end loss).
    return (p['F']*(1+F(1,p['W']))+p['K0']
            +F(pc['false_flag_rate_max'])*p['T']+pc['recoveries_max']+1)


def saturation(p,bits):
    n=count_bound(p);threshold=2**bits-1
    return dict(bits=bits,threshold=threshold,expected_increments_before_bad_upper=n,
                probability_before_bad_upper=min(F(1),n/threshold))


def finish(p,s,c,ma,cross,initial,q,kind):
    prof=next(x for x in b.accepted.CFG['profiles'] if x['name']=='MCU_calibrated_write')
    sat=saturation(p,32);bad=min(F(1),q+sat['probability_before_bad_upper'])
    with b.price_parameters(s):
        pr0=b.accepted.price(p,c,prof,q,2)
        pr=b.accepted.price(p,c,prof,bad,2)
    pr0=b.pay_recovery_rounding(pr0,p,c,s)
    pr=b.pay_recovery_rounding(pr,p,c,s)
    a=b.CFG['application'];rw,rr=F(a['mean_write_s']),F(a['mean_read_s'])
    app=c['app']*rw+s['read32_s']*rr
    mask=b.full_mask_price(p,c,s)
    res=b.resources(c,s)
    return dict(bound=kind,service=s,calendar=c,majorant=ma,cross=cross,initial=initial,
        risk_upper=q,slack=p['eps']-q,relative_slack=(p['eps']-q)/p['eps'],
        risk_admitted=q<=p['eps'],resources=res,
        mathematical_admission=q<=p['eps'] and res['admitted'],
        price_bad_probability=bad,saturation=sat,price=pr,
        saturation_quiet_price_increment=pr['quiet_upper_intercept']-pr0['quiet_upper_intercept'],
        saturation_mission_price_increment=pr['mission_upper_intercept']-pr0['mission_upper_intercept'],
        full_bus_quiet=min(mask,pr['quiet_upper_intercept']+app),
        full_bus_mission=min(mask,pr['mission_upper_intercept']+app),
        full_bus_quiet_without_saturation=pr0['quiet_upper_intercept']+app,
        full_bus_mission_without_saturation=pr0['mission_upper_intercept']+app,
        full_bus_mask=mask,implemented_and_timed=False)


def joint(p,s):
    assert p['W']==524288 and s['g_ticks']==196 and s['c_ticks']==164
    assert s['gate_min_ticks']==s['gate_max_ticks']==320
    sys.path.insert(0,str(b.ROOT/'experiments/t119-err-joint-bound'))
    import joint as j
    c=b.calendar(p,s)
    ma=j.majorant(p,c,F('.048'),2,phase_cells=8,q_cells=192,refinements=5)
    cross=b.accepted.old.cross(dict(p,beta=F(1,2*p['W'])),c['Ps_min'],c['Pl'],3,p['S2exact'],s['E_s'])
    initial=p['K0']*p['B']*(c['Ps']+s['E_s'])/p['W']
    q=p['errors']+p['D']+initial+ma['integral']/(2*p['W'])+cross['X']
    return finish(p,s,c,ma,cross,initial,q,'accepted T119 fixed c164/g196/freeze320')


def old_bound(p,s,ka=3):
    r=b.compute(p,s,ka)
    return finish(p,s,r['calendar'],r['majorant'],r['cross'],r['initial'],r['risk_upper'],
                  'accepted T114; T119 NOT transferred to changed grid')


def source_checks():
    base='experiments/t104-rtl-resume/split/'
    ps=['REPORT.md','CONTRACT.md','timing_balance.json','timing_balance.py',
        'predecision_guard.sv','operation_lane.sv','relative_calendar.sv',
        'handshake_channel.sv','slow_queue.sv']
    sources={p:subprocess.check_output(['git','show',ENGINEER+':'+base+p],cwd=b.ROOT) for p in ps}
    assert sources['timing_balance.json']==INPUT.read_bytes()
    scope={'__name__':'t135_check_engineer'}
    exec(compile(sources['timing_balance.py'],base+'timing_balance.py','exec'),scope)
    assert scope['calculate']()==E  # read-only call, no __main__ output write
    guard=sources['predecision_guard.sv'].decode()
    assert 'GEN_BITS=16' in guard and 'assign exhausted = &generation' in guard
    assert '&& !exhausted' in guard
    return {base+p:hashlib.sha256(v).hexdigest() for p,v in sources.items()}


def timing_ledger():
    c={k:F(v['max_ns'])*NS for k,v in E['components_250_50'].items()}
    inbound=sum(c[k] for k in ('source_sampling','request_preparation_budget',
                               'request_slow_queue_and_handshake_to_fast_consumer','fast_prefetch_dispatch'))
    outbound=c['reply_outbox']+c['response_handshake_and_slow_queue_to_consumer']
    total=F('1.1')*(inbound+c['wait_one_calendar_frame']+c['observed_write32']+outbound+F('100e-9'))
    assert total==F(E['end_to_end_upper_with_10pct_ns'])*NS
    return dict(engineer_components_s=c,inbound_s=inbound,outbound_s=outbound,
        upper_from_decomposition_s=total,inbound_budget_s=F('320e-9'),outbound_budget_s=F('320e-9'),
        inbound_unallocated_s=F('320e-9')-inbound,outbound_unallocated_s=F('320e-9')-outbound,
        engineer_local_loss_veto_s=F(E['runtime_loss_to_fast_veto']['max_ns'])*NS,
        common_joint_rate_s=10000,engineer_separate_rate_s=180000,
        status='arithmetic decomposition conditional on idle queues/transport; integrated WCET unknown')


def epoch16_price(p,c,s):
    # Each autonomous barrier needs 65534 new generation increments.
    # No deterministic bound on ERR count is introduced.
    barrier=F('10e-6')  # proposed all-channel quiescence bound, not measured
    edge=2*c['frame']+s['gate_max_ticks']*b.TP+2*b.J
    n=count_bound(p)/65534
    duration=barrier+c['recovery_hold_upper']+edge
    density=s['E_s']/(c['g']*b.TM)
    return dict(trigger=65534,expected_barriers_before_bad_upper=n,
        quiescence_budget_s=barrier,recovery_upper_s=c['recovery_hold_upper'],
        additional_mission_price=density*n*duration/p['T'],
        additional_quiet_price=density*n*duration/(F('.9')*p['T']),
        status='alternative only; stop/drain/ack/recovery protocol NOT implemented')


def report():
    pins=source_checks();p=b.environment();demo=b.environment(True)
    orig=b.prefetch_service()
    assert all(orig[k]==v for k,v in operation_inputs('operations_250').items())
    rows={}
    rows['original_250']=joint(p,orig)
    common=dict(orig,ERR_or_loss_to_rule_s=F('10e-6'))
    rows['recommended_250']=joint(p,common)
    rows['ERR_100us_250']=joint(p,dict(orig,ERR_or_loss_to_rule_s=F('100e-6')))
    # A rectangular sufficient timing domain with the SAME deterministic grid.
    edge=dict(common,E_s=(164*b.TM-b.J)/F('1.1'),
              observed_write32_s=(240*b.TM-b.J)/F('1.1'))
    assert edge['observed_write32_s']>=edge['E_s']+edge['write16_s']
    rows['same_grid_service_edges_250']=joint(p,edge)
    # One extra 4 ns inside the write-containing E and hence observed write.
    plus=dict(orig,E_s=orig['E_s']+F('4e-9'),
              observed_write32_s=orig['observed_write32_s']+F('4e-9'))
    plus=b.reserve_calendar(plus)
    rows['extra_fast_cycle_E']=old_bound(p,plus)
    s100=dict(b.CFG['dual_domain'],service_quantum_ticks=10)
    s100.update(operation_inputs('candidate_100_operations'))
    s100=b.reserve_calendar(s100)
    rows['reserve100_original']=old_bound(p,s100)
    rows['reserve100_demo']=old_bound(demo,s100)
    s100f=dict(s100,request_to_queue_s=F('250e-9'),release_to_response_s=F('250e-9'))
    rows['reserve100_demo_rebalanced']=old_bound(demo,s100f)
    rows['reserve100_FAST_original']=old_bound(p,s100,1)
    for row in rows.values():
        row['delta_Q_from_v1']=row['risk_upper']-F(json.loads((HERE/'report.json').read_text())['rows']['recommended_T119_prefetch']['risk_upper'])
    old=json.loads((HERE/'report.json').read_text())['rows']['recommended_T119_prefetch']
    assert rows['original_250']['risk_upper']==F(old['risk_upper'])
    assert rows['original_250']['full_bus_mission_without_saturation']==F(old['full_bus_mission'])
    floor=p['errors']+p['D']+rows['reserve100_FAST_original']['initial']+rows['reserve100_FAST_original']['calendar']['Ps']*p['S2exact']/(2*p['W'])
    v1paths=['calculate.py','config.json','report.json','test_contract.py','verify.py']
    for n in v1paths:
        assert (HERE/n).read_bytes()==subprocess.check_output(['git','show',OLD+':experiments/t135-demo-operating-point/'+n],cwd=b.ROOT)
    return dict(task=135,revision=2,instructions_sha=b.CFG['instructions_sha'],
        scientific_parent=OLD,engineer_sha=ENGINEER,environment=p,conditional_demo_environment=demo,
        rows=rows,timing=timing_ledger(),counter16=saturation(p,16),counter32=saturation(p,32),
        epoch16_alternative=epoch16_price(p,rows['recommended_250']['calendar'],common),
        reserve100_pointwise_certificate_floor=floor,
        floor_scope='lower value of the selected sufficient pointwise expression, NOT lower physical risk',
        unknowns=dict(integrated_candidate_WCET=None,integrated_ERR_rule_WCET=None,
            frame_protocol=None,actual_100MHz_request_reply=None,actual_100MHz_ERR=None,
            pad_WCET=None,closed_STA=None,engineer_acceptance_of_common_contract=None),
        engineer_source_sha256=pins,accepted_source_sha256=b.source_pins(),
        local_source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()
            for n in ('reconcile.py','test_reconcile.py','common-contract.json')})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');a=ap.parse_args()
    out=report();text=json.dumps(b.serial(out),ensure_ascii=False,indent=2)+'\n'
    path=HERE/'report-r2.json'
    if a.write:path.write_text(text)
    else:assert path.read_text()==text,'T135 r2 report mismatch'
    for k,r in out['rows'].items():
        print(k,'U<=',b.accepted.old.text_number(r['risk_upper'],digits=15),
              'slack%',float(100*r['relative_slack']),'mission%',float(100*r['full_bus_mission']),
              'reply_us',float(1e6*r['resources']['response_upper']),'admitted',r['mathematical_admission'])
    print('T135 r2 report written.' if a.write else 'T135 r2 report reproduced byte-for-byte.')


if __name__=='__main__':main()
