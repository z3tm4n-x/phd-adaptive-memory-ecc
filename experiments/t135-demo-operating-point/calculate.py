"""T135: finite substitutions in ACCEPTED T114, no online controller/search.

All admission decisions are Fraction/accepted directed Decimal intervals.
Accepted sources are imported/read only. --write writes this package alone.
Optional --service accepts complete measured/proposed service inputs; a clock
frequency without operation/CDC bounds never yields a numeric certificate.
"""
import argparse
from contextlib import contextmanager
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / 'experiments/t114-two-stage-err'))
spec=importlib.util.spec_from_file_location('_t135_accepted_t114', ROOT/'experiments/t114-two-stage-err/calculate.py')
accepted=importlib.util.module_from_spec(spec)
spec.loader.exec_module(accepted)

CFG = json.loads((HERE / 'config.json').read_text())
TM, TP, J = accepted.TM, accepted.TP, accepted.JIT
ceil = accepted.old.ceil
serial = accepted.old.serial


def base_environment():
    return accepted.old.environment(accepted.old.HANDOFF['rows'][0])


def environment(demo=False):
    p = base_environment()
    if demo:
        p['FS'] = F(CFG['demo']['FS_cap'])
        p['F'] = min(p['B']*p['T'], p['b']*p['T']+p['FS'])
        p['S2exact'] = min(F(CFG['demo']['S2_cap']), p['B']**2*p['T'],
            p['B']*p['F'], p['b']**2*p['T']+(p['B']+p['b'])*p['FS'])
        assert p['S2exact'] == F(CFG['demo']['S2_cap'])
    return p


def service_original():
    t = accepted.T
    return dict(service_quantum_ticks=4,timer_quantum_ticks=4,g_ticks=196,
        c_ticks=164,app_charge_ticks=240,gate_min_ticks=320,gate_max_ticks=320,
        request_to_queue_s=t['req'],release_to_response_s=t['reply'],
        decision_transport_s=t['command'],ERR_or_loss_to_rule_s=F('1.2e-6'),
        backpressure_s=F('1e-7'),R_s=t['R'],E_s=t['E'],
        write16_s=F('68.500680e-9'),observed_write32_s=F('217.002160e-9'),
        read32_s=t['app'],timer_mode='aligned_original',measured=False)


def parse_service(s):
    r = dict(s)
    for k,v in r.items():
        if k.endswith('_s'):
            if v is None: raise ValueError('Unknown service time: '+k)
            r[k] = F(v)
    required = set(service_original())-{'timer_mode','measured'}
    if not required <= set(r): raise ValueError('Missing service fields: '+str(required-set(r)))
    r.setdefault('timer_mode','asynchronous_countdown')
    for k in required:
        if not isinstance(r[k],(int,F)) or r[k]<=0: raise ValueError('Nonpositive service field: '+k)
    q=r['service_quantum_ticks']
    if any(r[k]%q for k in ('g_ticks','c_ticks','app_charge_ticks','gate_min_ticks','gate_max_ticks')):
        raise ValueError('Calendar is not on the service grid')
    if r['gate_min_ticks']>r['gate_max_ticks']:raise ValueError('Reversed freeze bounds')
    if r['observed_write32_s']<r['E_s']+r['write16_s']:raise ValueError('Unpaid observed write')
    if r['read32_s']<2*r['R_s']:raise ValueError('Unpaid read32')
    if r['E_s']<r['R_s']:raise ValueError('Invalid E duration')
    return r


def timer(duration, service):
    q=service['timer_quantum_ticks']
    n=ceil((duration+J)/(q*TM))
    if service.get('timer_mode')=='aligned_original':
        return dict(lower=n*q*TM-J,upper=n*q*TP+J,count=n,bits=n.bit_length())
    # First decrement can occur immediately after load. Pay one full quantum;
    # expire strictly AFTER terminal equality. No wraparound deadline compare.
    n+=1
    return dict(lower=(n-1)*q*TM-J,upper=n*q*TP+J,count=n,bits=n.bit_length())


def calendar(p,s,ka=3,w=F(90),h=F(180)):
    if ka%2!=1:raise ValueError('Inverse address permutation requires odd ka')
    wt,ht=timer(w,s),timer(h,s);g=s['g_ticks']
    ps=p['W']*g*TP;pl=ka*ps
    tau=pl+s['E_s']+s['observed_write32_s']+s['ERR_or_loss_to_rule_s']+2*J
    recovery=timer((ht['lower'] if s.get('timer_mode')!='aligned_original' else h)+tau,s)
    # Old row is reproduced under its accepted abstract recovery upper.
    # The NEW explicit slow countdown must also pay rounding of tau itself.
    recovery_extra=(max(F(0),recovery['upper']-ht['upper']-tau)
                    if s.get('timer_mode')!='aligned_original' else F(0))
    return dict(g=g,ka=ka,Ps=ps,Ps_min=p['W']*g*TM,Pl=pl,
        frame=8*g*TP,frame_min=8*g*TM,app=s['observed_write32_s'],
        app_charge=s['app_charge_ticks'],
        tau=tau,recovery_hold_lower=recovery['lower'],recovery_hold_upper=recovery['upper'],
        recovery_count=recovery['count'],recovery_rounding_extra=recovery_extra,
        lag=pl+s['gate_max_ticks']*TP+2*J,
        w=wt['lower'],h=ht['lower'],w_upper=wt['upper'],h_upper=ht['upper'],
        w_ticks=wt['count']*s['timer_quantum_ticks'],h_ticks=ht['count']*s['timer_quantum_ticks'],
        w_count=wt['count'],h_count=ht['count'],timer_counter_bits=max(wt['bits'],ht['bits'],recovery['bits']),
        phi=F('0.9')-F(1,p['W']),blackout=F(0),blackout_edge=F(0))


def resources(c,s):
    a=CFG['application'];sigma=F(a['joint_burst']);rate=F(a['joint_rate_s'])
    dl=F('3e-6');window=F('.001');m=F('1.1')
    fixed=s['request_to_queue_s']+J+c['app']+s['release_to_response_s']+s['backpressure_s']
    mem=8*s['E_s']*(window/c['frame_min']+2)/window
    x=F('.0001')+(F('209e-9')+F('.0001')*dl)/window
    peak=mem+x+c['app']*(sigma+rate*(window+dl))/window
    max_sum=dl/m-sigma*c['frame']-J-c['app']-s['backpressure_s']
    res=dict(whole_bus_peak=peak,response_upper=m*(fixed+sigma*c['frame']),
        peak_slack=F('.8')-peak,response_slack=dl-m*(fixed+sigma*c['frame']),
        request_response_sum_max=max_sum,
        command_path_max=(s['gate_min_ticks']*TM-J)/m-c['app'],
        request_rate_slack=1-rate*c['frame'],
        E_margin_slack=s['c_ticks']*TM-J-m*s['E_s'],
        E_upper_allowed_by_reserve=(s['c_ticks']*TM-J)/m,
        app_margin_slack=s['app_charge_ticks']*TM-J-m*c['app'],
        placement_slack=c['frame_min']-8*s['c_ticks']*TP-J-(s['app_charge_ticks']*TP+J),
        gate_slack=s['gate_min_ticks']*TM-J-m*(c['app']+s['decision_transport_s']),
        FIFO_including_inflight_held_reply=2,
        max_freeze_advance_s=s['gate_max_ticks']*TP+J)
    res['admitted']=all(res[k]>=0 for k in ('peak_slack','response_slack','request_rate_slack',
                         'E_margin_slack','app_margin_slack','placement_slack','gate_slack'))
    return res


def full_mask_price(p,c,s):
    """Deterministic all-ERR cap, using the accepted finite-edge charges.

    This does not need A6 availability/false-flag bounds. The quiet-set
    geometry, control bus envelope and app mean envelopes are still needed.
    """
    pc=accepted.CFG['price_contract']
    tq=F(pc['quiet_fraction'])*p['T'];kq=pc['quiet_components']
    x=F(pc['X_rate'])+kq*(F(pc['X_burst_s'])+F(pc['X_rate'])*F('3e-6'))/tq
    edges=4*8*s['E_s']*kq/tq
    app=c['app']*F(CFG['application']['mean_write_s'])+s['read32_s']*F(CFG['application']['mean_read_s'])
    return s['E_s']/(c['g']*TM)+x+edges+app


@contextmanager
def price_parameters(s):
    # Only RAM objects, restored even on exceptions. No accepted file mutation.
    oldT=dict(accepted.T);oldG=accepted.CFG['calendar']['gate_ticks']
    try:
        accepted.T.update(R=s['R_s'],E=s['E_s'],d=s['E_s'],app=s['read32_s'])
        accepted.CFG['calendar']['gate_ticks']=s['gate_max_ticks']
        yield
    finally:
        accepted.T.clear();accepted.T.update(oldT)
        accepted.CFG['calendar']['gate_ticks']=oldG


def pay_recovery_rounding(pr,p,c,s):
    # Enlarge the already paid startup/recovery strips; their old calendar
    # edges remain applicable. Using full E density is conservative for the
    # increase in the FAST fraction (the accepted price uses only R density).
    pc=accepted.CFG['price_contract'];extra=c['recovery_rounding_extra']
    count=F(pc['recoveries_max'])+1
    density=s['E_s']/(c['g']*TM)
    mission=density*count*extra/p['T']
    quiet=mission/F(pc['quiet_fraction'])
    return dict(pr,mission_upper_intercept=pr['mission_upper_intercept']+mission,
        quiet_upper_intercept=pr['quiet_upper_intercept']+quiet,
        additional_recovery_time=extra,additional_mission_price=mission,
        additional_quiet_price=quiet)


def compute(p,s,ka=3,stages=2):
    c=calendar(p,s,ka)
    if not c['h']>=c['w']>c['tau']:raise ValueError('Timer admission failed')
    ma=accepted.majorant(p,c,F('.048'),stages)
    cross=accepted.old.cross(dict(p,beta=F(1,2*p['W'])),c['Ps_min'],c['Pl'],ka,p['S2exact'],s['E_s'])
    initial=p['K0']*p['B']*(c['Ps']+s['E_s'])/p['W']
    q=p['errors']+p['D']+initial+ma['integral']/(2*p['W'])+cross['X']
    profile=next(x for x in accepted.CFG['profiles'] if x['name']=='MCU_calibrated_write')
    with price_parameters(s):pr=accepted.price(p,c,profile,q,stages)
    pr=pay_recovery_rounding(pr,p,c,s)
    a=CFG['application'];rw=F(a['mean_write_s']);rr=F(a['mean_read_s'])
    res=resources(c,s)
    return dict(calendar=c,majorant=ma,cross=cross,initial=initial,risk_upper=q,
        slack=p['eps']-q,relative_slack=(p['eps']-q)/p['eps'],resources=res,
        risk_admitted=q<=p['eps'],admitted=q<=p['eps'] and res['admitted'],
        price=pr,protection_quiet=pr['quiet_upper_intercept']+s['R_s']*rw,
        protection_mission=pr['mission_upper_intercept']+s['R_s']*rw,
        full_bus_quiet=pr['quiet_upper_intercept']+c['app']*rw+s['read32_s']*rr,
        full_bus_mission=pr['mission_upper_intercept']+c['app']*rw+s['read32_s']*rr,
        full_bus_mask_without_availability=full_mask_price(p,c,s),
        constant_class_gain=None,hardware_qualification=None)


def prefetch_service():
    s=dict(CFG['dual_domain'])
    s.update(gate_min_ticks=320,gate_max_ticks=320,
        decision_transport_s=CFG['prefetch']['local_dispatch_s'])
    return parse_service(s)


def joint_prefetch(p):
    # The accepted joint proof has fixed freeze320 and c164. Do not silently
    # use it for the earlier-freeze or 100 MHz sensitivity calendars.
    sys.path.insert(0,str(ROOT/'experiments/t119-err-joint-bound'))
    import joint
    s=prefetch_service();c=calendar(p,s)
    ma=joint.majorant(p,c,F('.048'),2,phase_cells=8,q_cells=192,refinements=5)
    cross=accepted.old.cross(dict(p,beta=F(1,2*p['W'])),c['Ps_min'],c['Pl'],3,p['S2exact'],s['E_s'])
    initial=p['K0']*p['B']*(c['Ps']+s['E_s'])/p['W']
    q=p['errors']+p['D']+initial+ma['integral']/(2*p['W'])+cross['X']
    profile=next(x for x in accepted.CFG['profiles'] if x['name']=='MCU_calibrated_write')
    with price_parameters(s):pr=accepted.price(p,c,profile,q,2)
    pr=pay_recovery_rounding(pr,p,c,s)
    rw,rr=(F(CFG['application'][k]) for k in ('mean_write_s','mean_read_s'))
    res=resources(c,s)
    earliest=CFG['prefetch']['earliest_candidate_lead_ticks']
    res['prefetch_margin_slack']=(earliest-320)*TM-J-F('1.1')*F(CFG['prefetch']['precompute_and_transport_s'])
    assert res['prefetch_margin_slack']>=0
    return dict(calendar=c,majorant=ma,cross=cross,initial=initial,risk_upper=q,
        slack=p['eps']-q,relative_slack=(p['eps']-q)/p['eps'],resources=res,
        admitted=q<=p['eps'] and res['admitted'],
        price=pr,protection_quiet=pr['quiet_upper_intercept']+s['R_s']*rw,
        protection_mission=pr['mission_upper_intercept']+s['R_s']*rw,
        full_bus_quiet=pr['quiet_upper_intercept']+c['app']*rw+s['read32_s']*rr,
        full_bus_mission=pr['mission_upper_intercept']+c['app']*rw+s['read32_s']*rr,
        full_bus_mask_without_availability=full_mask_price(p,c,s),
        constant_class_gain=None,hardware_qualification=None,
        prefetch_equivalence_obligation='candidate -> exact virtual freeze, local invalidation; NOT an earlier committed decision')


def repeat_joint_anchor(p):
    sys.path.insert(0,str(ROOT/'experiments/t119-err-joint-bound'))
    import joint
    prof=next(x for x in joint.accepted.CFG['profiles'] if x['name']=='MCU_calibrated_write')
    r=joint.compute(p,prof,joint.accepted.CFG['growth_classes'][0],3,2,
        phase_cells=8,q_cells=192,refinements=5)
    old=json.loads((ROOT/'experiments/t119-err-joint-bound/report.json').read_text())['rows'][0]
    assert r['risk_upper']==F(old['risk_upper'])
    assert r['majorant']['integral']==F(old['majorant']['integral'])
    assert r['price']['mission_upper_intercept']==F(old['price']['mission_upper_intercept'])
    return dict(name='same_rule_two',exact_Q_and_pair_and_mission_price_match=True)


def reserve_calendar(service):
    """Select same batch-eight geometry, all grants on provided q-tick grid.

    Calendar sizing, NOT inference of operation durations from MHz. Keep
    actual fields and snapshot/parent obligations in the engineer's contract.
    """
    r=dict(service);q=r['service_quantum_ticks'];m=F('1.1')
    for field,duration in (('c_ticks','E_s'),('app_charge_ticks','observed_write32_s')):
        if r.get(duration) is None:raise ValueError('Unknown service time: '+duration)
        r[field]=q*ceil((m*F(r[duration])+J)/(q*TM))
    c,a=r['c_ticks'],r['app_charge_ticks']
    r['g_ticks']=q*ceil(((8*c+a)*TP+2*J)/(8*q*TM))
    return parse_service(r)


def frozen_substitution(p):
    old=json.loads((ROOT/'experiments/t114-two-stage-err/report.json').read_text())['rows'][26]
    ma=old['majorant'];c=old['calendar']
    integ=min(F(c['Pl'])*p['S2exact'],F(ma['u'])*p['T']+F(ma['v'])*p['FS'])
    q=F(old['risk_upper'])+(integ-F(ma['integral']))/(2*p['W'])
    return dict(risk_upper=q,slack=p['eps']-q,relative_slack=(p['eps']-q)/p['eps'],
        interpretation='old majorant AND old non-pair terms retained; additional FS constraint explicit')


def source_pins():
    files=[]
    files += ['experiments/t114-two-stage-err/'+x for x in ('calculate.py','config.json','intervals.py','report.json','HANDOFF.md')]
    files += ['experiments/t110-err-write-service/'+x for x in ('calculate.py','inputs.json')]
    files += ['experiments/t119-err-joint-bound/'+x for x in ('joint.py','config.json','report.json')]
    files += ['experiments/t126-regime-map/outputs/map.json','experiments/t104-new-rtl-executor/handoff.json',
        'theory/t114-two-stage-err.md','theory/t114-two-stage-err-appendix.md']
    return {x:hashlib.sha256((ROOT/x).read_bytes()).hexdigest() for x in files}


def report():
    p,pd=environment(),environment(True)
    anchor_check=repeat_joint_anchor(p)
    old=service_original();dual=parse_service(CFG['dual_domain'])
    rows={}
    for name,env,svc,ka in [('original_T114',p,old,3),('original_FAST',p,old,1),
                          ('original_dual',p,dual,3),('demo_dual',pd,dual,3)]:
        rows[name]=compute(env,svc,ka)
    rows['recommended_T119_prefetch']=joint_prefetch(p)
    originals=json.loads((ROOT/'experiments/t114-two-stage-err/report.json').read_text())
    assert rows['original_T114']['risk_upper']==F(originals['rows'][26]['risk_upper'])
    assert rows['original_T114']['price']['mission_upper_intercept']==F(originals['rows'][26]['price']['mission_upper_intercept'])
    joint=json.loads((ROOT/'experiments/t119-err-joint-bound/report.json').read_text())
    imported={x['name']:{k:x[k] for k in ('risk_upper','risk_slack','price','calendar')} for x in joint['rows'] if x['name'] in ('same_rule_two','same_rule_one','one_presented')}
    pointwise_floor=p['errors']+p['D']+p['K0']*p['B']*(rows['original_FAST']['calendar']['Ps']+old['E_s'])/p['W']+rows['original_FAST']['calendar']['Ps']*p['S2exact']/(2*p['W'])
    maps=json.loads((ROOT/'experiments/t126-regime-map/outputs/map.json').read_text())['rows']
    maprow=next(x for x in maps if x['id']==CFG['reference_map_id'])
    assert F(maprow['quiet_budget'])==F(1,2) and F(maprow['FS'])==p['FS']
    other=next(x for x in maps if x['id']=='cy_T95_anchor_c1/100')
    return dict(task=135,config=CFG,environment_original=p,environment_demo=pd,rows=rows,
        old_nonpair_frozen_candidate=frozen_substitution(pd),accepted_T119_rows=imported,
        only_S2_cap_without_FS=frozen_substitution(dict(p,S2exact=pd['S2exact'])),
        other_accepted_map_point={k:other.get(k) for k in ('id','Q_upper','adaptive_quiet_upper','adaptive_mission_upper','domain','channel','calendar')},
        certificate_floor=pointwise_floor,certificate_relative_slack_ceiling=(p['eps']-pointwise_floor)/p['eps'],
        floor_scope='T114/T119 pointwise majorants on SAME g196 calendar only; not lower physical risk',
        map_suffix_check='c1/2 is quiet-price budget, not radiation reduction',
        delay_delta_Q=rows['original_dual']['risk_upper']-rows['original_T114']['risk_upper'],
        recommended_delta_from_accepted_T119=rows['recommended_T119_prefetch']['risk_upper']-F(joint['rows'][0]['risk_upper']),
        reserve_100MHz=CFG['reserve_100MHz'],source_sha256=source_pins(),
        accepted_anchor_check=anchor_check,
        source_local_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('calculate.py','config.json','test_contract.py')})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');ap.add_argument('--service',type=Path)
    args=ap.parse_args()
    if args.service:
        raw=json.loads(args.service.read_text())
        if not raw.get('engineer_service_sha'):raise ValueError('Exact engineer service SHA is required')
        if not raw.get('same_semantic_E_and_single_word_lock_confirmed'):
            raise ValueError('Unconfirmed E/observation/lock semantics')
        for k in ('snapshot_ERR_from_grant_s','release_from_grant_s'):
            if raw.get(k) is None:raise ValueError('Unknown service phase: '+k)
        if not F(raw['snapshot_ERR_from_grant_s'])<=F(raw['release_from_grant_s'])<=F(raw['E_s']):
            raise ValueError('Uncovered ERR/release phase')
        if any(F(raw.get(k,'0'))!=v for k,v in (
            ('constant_scale_assumed_min_ns',F('.99999')),
            ('constant_scale_assumed_max_ns',F('1.00001')),
            ('edge_span_assumed_s',J))):raise ValueError('Clock/jitter requires separate resubstitution')
        s=reserve_calendar(raw)
        out=dict(service=s,original=compute(environment(),s),demo=compute(environment(True),s),
            warning='conditional numerical substitution; input timing source and semantic obligations still required')
        previous=json.loads((HERE/'report.json').read_text())
        for key in ('original','demo'):
            ref='recommended_T119_prefetch' if key=='original' else 'demo_dual'
            out[key]['slack_change_from_presented']=out[key]['slack']-F(previous['rows'][ref]['slack'])
        print(json.dumps(serial(out),indent=2));return
    out=report();encoded=json.dumps(serial(out),indent=2,ensure_ascii=False)+'\n'
    path=HERE/'report.json'
    if args.write:path.write_text(encoded)
    elif not path.exists() or path.read_text()!=encoded:raise AssertionError('New T135 report differs')
    for name,row in out['rows'].items():
        print(name,'U_Q=',accepted.old.text_number(row['risk_upper'],digits=15),
              'slack %=',float(100*row['relative_slack']),'full mission %=',float(100*row['full_bus_mission']))
    print('T135 read-only verification passed.' if not args.write else 'T135 report written.')


if __name__=='__main__':main()
