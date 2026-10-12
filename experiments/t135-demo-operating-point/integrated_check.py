"""T135 r4: finite integrated contract audit, not an RTL or parameter campaign."""
import argparse
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('t135_r3_for_r4',HERE/'align64.py')
prev=importlib.util.module_from_spec(spec);spec.loader.exec_module(prev)
b=prev.b
ENGINEER='99c0a4147048da57c8b59f6a2d4cfd5183cbcf0f'
PARENT='5147d0d360e7483fb421c9b5d11ff96ac216ef78'
INSTRUCTIONS='8d85fe3d6ea3b3fb99a8e36600ecbfda43dbfc23'
NS=F(1,10**9)


def source_checks():
    base='experiments/t104-rtl-resume/integrated/'
    names=['HANDOFF.md','PROOF.md','bounds.py','outputs/bounds.json','executor.sv',
           'slow_rule.sv','candidate_link.sv','frame_engine.sv','event_fifo.sv','guard_proof.py']
    src={n:prev.git_bytes(ENGINEER,base+n) for n in names}
    scope={'__name__':'read_only_t104_bounds'}
    exec(compile(src['bounds.py'],base+'bounds.py','exec'),scope)
    data=scope['calculate']()
    assert scope['encode'](data)==json.loads(src['outputs/bounds.json'])
    assert src['outputs/bounds.json']==(HERE/'inputs/t104-99c0a41-bounds.json').read_bytes()
    rule=src['slow_rule.sv'].decode()
    for token in ('NW=34\'d4500045002','NH=34\'d9000090002','NR=34\'d9015504896',
                  "PAIR_WINDOW=64'd22500225010",'event_generation!=processed_generation+64\'d1',
                  'timestamp-last_err<=PAIR_WINDOW','recovery_left<=NR'):
        assert token in rule,token
    return data,{base+n:hashlib.sha256(v).hexdigest() for n,v in src.items()}


def recovery_transition_price(p,c,s):
    # NR starts on processing recovery, not on physical loss-fall/mission t0.
    # Pay a full joint 10us for load plus eventual usable candidate, in addition
    # to the already paid NR rounding and calendar edge. Conservative overpay;
    # ordinary outages and mission quotas themselves are NOT increased.
    latency=s['ERR_or_loss_to_rule_s']
    n=b.accepted.CFG['price_contract']['recoveries_max']+1
    density=s['E_s']/(c['g']*b.TM)
    return dict(joint_load_and_exit_budget_s=latency,startup_and_recoveries=n,
                mission=density*n*latency/p['T'],quiet=density*n*latency/(F('.9')*p['T']))


def row(p,s,ka=3,stages=2,w=F(90),h=F(180)):
    assert s['c_ticks']==164 and s['g_ticks']==196
    assert s['gate_min_ticks']==s['gate_max_ticks']==320 and p['W']==524288
    sys.path.insert(0,str(b.ROOT/'experiments/t119-err-joint-bound'))
    import joint as j
    c=b.calendar(p,s,ka,w,h)
    ma=j.majorant(p,c,F('.048'),stages,phase_cells=8,q_cells=192,refinements=5)
    cross=b.accepted.old.cross(dict(p,beta=F(1,2*p['W'])),c['Ps_min'],c['Pl'],ka,p['S2exact'],s['E_s'])
    initial=p['K0']*p['B']*(c['Ps']+s['E_s'])/p['W']
    q=p['errors']+p['D']+initial+ma['integral']/(2*p['W'])+cross['X']
    prof=next(x for x in b.accepted.CFG['profiles'] if x['name']=='MCU_calibrated_write')
    with b.price_parameters(s): pr=b.accepted.price(p,c,prof,q,stages)
    pr=b.pay_recovery_rounding(pr,p,c,s)
    extra=recovery_transition_price(p,c,s)
    app=c['app']*F(b.CFG['application']['mean_write_s'])+s['read32_s']*F(b.CFG['application']['mean_read_s'])
    res=b.resources(c,s)
    return dict(ka=ka,stages=stages,w_requested=w,h_requested=h,calendar=c,
        majorant=ma,cross=cross,initial=initial,risk_upper=q,slack=p['eps']-q,
        relative_slack=(p['eps']-q)/p['eps'],resources=res,price=pr,
        recovery_transition_price=extra,
        full_bus_quiet=min(b.full_mask_price(p,c,s),pr['quiet_upper_intercept']+app+extra['quiet']),
        full_bus_mission=min(b.full_mask_price(p,c,s),pr['mission_upper_intercept']+app+extra['mission']),
        full_bus_quiet_before_transition=pr['quiet_upper_intercept']+app,
        full_bus_mission_before_transition=pr['mission_upper_intercept']+app,
        conditional_admission=q<=p['eps'] and res['admitted'],full_hardware_acceptance=False)


def timing(data,s):
    a,h,c=data['application'],data['history'],data['candidates']
    # Independent verification of the piecewise-linear backlog/delay extrema.
    lo,hi=b.TM/NS,b.TP/NS
    C=20*hi;L=212*hi+F('.5');kink=(2002-3)*20*lo
    arrivals=lambda t:min(F(2002),3+t/(20*lo))+1+(t+F('.5'))/(164*lo)
    knots=[F(0),L,kink]
    backlog=max(arrivals(t)-max(F(0),(t-L)/C) for t in knots)
    delay=L+C+max(C*arrivals(t)-t for t in knots)
    assert backlog==h['backlog_upper'] and delay==h['processed_history_ns']
    assert b.ceil(backlog)+16==h['full_flag_occupancy_upper']<512
    fresh=delay+36*hi+F('.5')+(3*1568-320)*hi+F('.5')+8*hi+F('.5')
    assert fresh==h['last_history_to_fresh_applicable_including_loss_CDC_ns']
    # Startup is synchronized from fast running to slow rule; do not set it to zero.
    start_load=(4+6*20)*hi+F('.5')
    startup_exit=start_load+(3*1568-320)*hi+F('.5')+8*hi+F('.5')
    assert max(fresh,startup_exit)*NS<=s['ERR_or_loss_to_rule_s']
    assert a['inbound_ns']*NS<=s['request_to_queue_s']
    assert a['outbound_ns']*NS<=s['release_to_response_s']
    # app_waiting may be raised on the preparation edge, whose old value
    # was sampled. Pay one fast edge BEFORE using the one-frame wait bound.
    usable_input=a['inbound_ns']+4*hi+F('.5')
    assert usable_input*NS<=s['request_to_queue_s']
    assert c['with_10pct_ns']<=1000 and c['dispatch_ns']*NS<=s['decision_transport_s']
    return dict(engineer=data,inbound_remaining_ns=320-a['inbound_ns'],
        outbound_remaining_ns=320-a['outbound_ns'],reaction_remaining_ns=10000-fresh,
        inbound_for_frame_wait_ns=usable_input,
        inbound_for_frame_wait_remaining_ns=320-usable_input,
        candidate_remaining_ns=1000-c['with_10pct_ns'],startup_load_upper_ns=start_load,
        startup_load_and_exit_upper_ns=startup_exit,
        status='conditional digital composition; complete payload/CDC proof and STA still required')


def original_certificate_floor(p,s):
    # K(q)>=Ps in the selected accepted certificate, NOT lower physical Q.
    floor=p['errors']+p['D']+p['W']*s['g_ticks']*b.TP*p['S2exact']/(2*p['W'])
    cheaper=dict(s,g_ticks=192)
    res192=b.resources(b.calendar(p,cheaper),cheaper)
    assert res192['placement_slack']<0
    return dict(value=floor,relative_slack_ceiling=(p['eps']-floor)/p['eps'],
        scope='lower value of these sufficient expressions with K>=Ps and fixed service; not physical probability or global optimality',
        g192_placement_slack_s=res192['placement_slack'],
        grid_statement='g196 is first 4xi-spaced g with this c164, app240, batch8 placement')


def unchanged_sources():
    assert b.source_pins()==json.loads((HERE/'report.json').read_text())['source_sha256']
    names=['calculate.py','config.json','reconcile.py','align64.py',
           'report.json','report-r2.json','report-r3.json',
           'test_contract.py','test_reconcile.py','test_align64.py']
    pins={}
    for name in names:
        raw=(HERE/name).read_bytes()
        assert raw==prev.git_bytes(PARENT,'experiments/t135-demo-operating-point/'+name)
        pins[name]=hashlib.sha256(raw).hexdigest()
    for name in ['experiments/t68-v21-inputs/contracts.md',
                 'experiments/RE-CY62167-ADDRESS-MAPPING-01/REPORT.md',
                 'experiments/RE-CY62167-ADDRESS-MAPPING-01/w32seq_scenario.json']:
        raw=(b.ROOT/name).read_bytes()
        assert raw==prev.git_bytes(PARENT,name)
        pins[name]=hashlib.sha256(raw).hexdigest()
    return pins


def report():
    data,pins=source_checks();legacy=unchanged_sources()
    p=b.environment();demo=b.environment(True)
    assert p['S2exact']==p['b']**2*p['T']+(p['B']+p['b'])*p['FS']
    s=dict(b.prefetch_service(),ERR_or_loss_to_rule_s=F('10e-6'))
    rows={
        'selected_r3_original':row(p,s),
        'one_stage_h180_original':row(p,s,stages=1),
        'longer_holds_180_360_original':row(p,s,w=F(180),h=F(360)),
        'FAST_same_service_original':row(p,s,ka=1),
        'existing_demo_250_50':row(demo,s),
    }
    old=json.loads((HERE/'report-r3.json').read_text())['recommended_250_64']
    cur=rows['selected_r3_original']
    for k in ['risk_upper','slack','relative_slack']:
        assert cur[k]==F(old[k])
    assert b.serial(cur['calendar'])==old['calendar']
    assert b.serial(cur['resources'])==old['resources']
    for scope in ('quiet','mission'):
        assert cur['full_bus_'+scope+'_before_transition']==F(old['full_bus_'+scope])
    tm=timing(data,s)
    common=json.loads((HERE/'common-contract.json').read_text())
    assert common['revision']==4 and common['engineer_input_sha']==ENGINEER
    assert common['scientific_parent_sha']==PARENT and common['instructions_sha']==INSTRUCTIONS
    rec=common['recommended'];cond=common['integrated_conditional_bounds']
    for key in ('g_ticks','c_ticks','app_charge_ticks'):
        assert rec[key]==s[key]
    assert rec['ka']==3 and rec['generation_bits_required']==64 and rec['timer_bits']==34
    for key,expected in [
        ('application_inbound_s',s['request_to_queue_s']),
        ('application_outbound_s',s['release_to_response_s']),
        ('effective_ERR_or_loss_rule_s',s['ERR_or_loss_to_rule_s'])]:
        assert F(rec[key])==expected
    assert F(cond['app_first_VALID_to_frame_eligibility_s'])==tm['inbound_for_frame_wait_ns']*NS
    assert F(cond['application_outbound_s'])==data['application']['outbound_ns']*NS
    assert F(cond['ERR_loss_processed_history_fresh_decision_s_upper'])>=data['history']['last_history_to_fresh_applicable_including_loss_CDC_ns']*NS
    for scope in ('mission','quiet'):
        assert F(rec['timers']['recovery_transition_price_'+scope+'_upper'])>=cur['recovery_transition_price'][scope]
    assert data['application']['response_with_10pct_ns']*NS==cur['resources']['response_upper']
    assert data['application']['bus_any_1ms_upper']==cur['resources']['whole_bus_peak']
    assert demo['S2exact']==p['b']**2*p['T']+(p['B']+p['b'])*demo['FS']
    return dict(task=135,revision=4,parent_sha=PARENT,engineer_sha=ENGINEER,
        instructions_sha=INSTRUCTIONS,environment=p,conditional_demo_environment=demo,
        service=s,rows=rows,timing=tm,certificate_floor=original_certificate_floor(p,s),
        demo_exposure=dict(original_peak_equivalent_s=p['FS']/(p['B']-p['b']),
            demo_peak_equivalent_s=demo['FS']/(p['B']-p['b']),
            exposure_ratio=demo['FS']/p['FS'],physical_support=None,author_approved=False),
        conditional_address_map=dict(words=524288,external_x16_addresses=1048576,
            pi='2*w+alias, alias in {0,1}',inverse='(address//2,address%2)',
            source='W32_seq scenario after declared linear byte-to-x16 projection; not recovered manufacturer map',
            actual_chip_mapping=None,D_or_ERR_requalified=False),
        engineering_source_sha256=pins,accepted_source_sha256=b.source_pins(),
        unchanged_source_sha256=legacy,
        local_source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()
            for n in ['integrated_check.py','test_integrated_check.py','common-contract.json','verify-r4.py','PLAN-r4.md']})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');args=ap.parse_args()
    out=report();encoded=json.dumps(b.serial(out),ensure_ascii=False,indent=2)+'\n'
    dest=HERE/'report-r4.json'
    if args.write:dest.write_text(encoded)
    else:assert dest.read_text()==encoded,'r4 report differs'
    for name,r in out['rows'].items():
        print(name,'U',float(r['risk_upper']),'slack%',float(100*r['relative_slack']),
              'quiet%',float(100*r['full_bus_quiet']),'mission%',float(100*r['full_bus_mission']),
              'timer_bits',r['calendar']['timer_counter_bits'])
    print('floor',float(out['certificate_floor']['value']),
          'margin_ceiling%',float(100*out['certificate_floor']['relative_slack_ceiling']))
    print('T135 r4 report written.' if args.write else 'T135 r4 report reproduced byte-for-byte.')


if __name__=='__main__':main()
