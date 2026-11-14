"""T196: addressed exact arithmetic only; no simulation/campaign or file writes.

Run --json for a candidate report; --check compares the committed report.
All decisions use Fraction. Display intervals enclose, never replace, fractions.
"""
from fractions import Fraction as F
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
from math import gcd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CFG = json.loads((HERE / 'common-input.json').read_text())
R4 = json.loads((ROOT / 'experiments/t135-demo-operating-point/report-r4.json').read_text())
ENV = {k: F(v) if isinstance(v, str) and k != 'shield' else v
       for k, v in R4['environment'].items()}
W, N, T = ENV['W'], ENV['n'], ENV['T']
B, B0, FS, S2 = ENV['B'], ENV['b'], ENV['FS'], ENV['S2exact']
TM, TP, J = F('0.99999e-9'), F('1.00001e-9'), F('0.5e-9')
R, E = F('92.500920e-9'), F('148.501480e-9')
AR, AW = F('185.001840e-9'), F('217.002160e-9')
RM = 92*TM-J
PS, PSM = W*196*TP, W*196*TM
BETA, QSUM = F(N-1, 2*N*W), F('0.000006')
START = PS+E


def ceil(x):
    x = F(x)
    return -(-x.numerator//x.denominator)


def shown(x, places=18):
    q = 10**places
    lo, hi = x.numerator*q//x.denominator, ceil(x*q)
    def decimal(a):
        sign = '-' if a < 0 else ''
        a = abs(a)
        return f'{sign}{a//q}.{a%q:0{places}d}'
    return {'exact': str(x), 'lower': decimal(lo), 'upper': decimal(hi)}


def serial(obj):
    if isinstance(obj, F): return shown(obj)
    if isinstance(obj, dict): return {k: serial(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [serial(v) for v in obj]
    return obj


def source_check():
    out = {}
    for p, expected in CFG['runtime_sources'].items():
        data = (ROOT/p).read_bytes()
        actual = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if actual != expected: raise AssertionError(('source changed', p, actual, expected))
        out[p] = actual
    return out


def delivery():
    c = CFG['delivery']
    cut_lo, cut_hi = c['cut_ticks']*TM-J, c['cut_ticks']*TP+J
    ingress = F(c['ingress_budget_ns'], 10**9)
    batch = F(c['batch_compute_and_local_install_budget_ns'], 10**9)
    gate, gap = c['freeze_ticks']*TP+J, c['maximum_control_gap_ticks']*TP+J
    effective = ingress+cut_hi+batch+gate+gap
    # Source records have a positive fast-edge separation. Ingress can bunch
    # at most ingress-span extra records; cut endpoints are conservatively paid.
    packet_max = ceil((cut_hi+ingress+J)/(4*TM))+2
    flight_max = ceil((ingress+J)/(4*TM))+2
    bank_capacity = c['bank_records']
    total_capacity = c['banks']*bank_capacity
    assert batch < cut_lo
    assert packet_max <= bank_capacity
    assert 2*packet_max+flight_max <= total_capacity
    assert effective <= F('10e-6')
    assert cut_hi+ingress < F(90)  # sufficient source span for optional OUR summary
    return dict(cut_lower_s=cut_lo, cut_upper_s=cut_hi,
        ingress_s=ingress, batch_and_install_s=batch, gate_s=gate, phase_s=gap,
        source_to_applicable_fresh_rule_s=effective,
        remaining_to_10us_s=F('10e-6')-effective,
        extra_cut_after_expiry_s=effective+cut_hi,
        extra_cut_after_expiry_admitted=effective+cut_hi<=F('10e-6'),
        records_per_packet_upper=packet_max, records_in_ingress_upper=flight_max,
        allocated_records=total_capacity, allocated_bytes=total_capacity*c['record_bytes'],
        old_cut_lower_s=c['legacy_cut_ticks']*TM-J,
        nominal_cut_count=int(T/F('4e-6')), nominal_old_cut_count=int(T/F('188160e-9')),
        cut_service_ratio=F(c['legacy_cut_ticks'], c['cut_ticks']),
        mean_shared_bus_seconds_per_cut_if_all_X=F('0.0001')*c['cut_ticks']*TM,
        hardware_WCET=None)


def common_upper(k, errors=QSUM):
    if type(k) is not int or k<1 or gcd(k,W)!=1:
        raise ValueError('mandatory stride must visit every word')
    p = k*PS
    # All mandatory/startup cells, plus crossing an unfinished mandatory E.
    # This is the first (quadratic) branch of T110, not a random partition.
    cross = BETA*(E+p/W)*S2
    initial = ENV['K0']*B*START/W
    pair = BETA*p*S2
    return dict(k=k, period_upper_s=p, initial=initial, pair=pair, cross=cross,
                risk_upper=min(F(1), errors+ENV['D']+initial+pair+cross))


def fixed_risk(M, errors=F('0.000003')):
    p = M*TP
    return errors+ENV['D']+ENV['K0']*B*START/W+BETA*p*S2+BETA*(E+p/W)*S2


def fixed_candidate(epsilon=F('.001')):
    # Globally affine scalar sufficient bound on this 4-tick calendar family.
    q0 = fixed_risk(0)
    slope = fixed_risk(4)-q0
    if epsilon < q0: return dict(status='no sufficient candidate: direct plus quotas exceeds epsilon')
    M = 4*int((epsilon-q0)/slope)
    assert fixed_risk(M) <= epsilon < fixed_risk(M+4)
    if M < W*196:
        return dict(status='sufficient root outside family M>=Wg; no admission',M_ticks=M)
    groups = W//8
    floor_frame = 4*(M//(4*groups))
    ceil_frame = 4*ceil(F(M, 4*groups))
    pminus, pplus = M*TM, M*TP
    fm, fp = floor_frame*TM, ceil_frame*TP
    response = F('1.1')*(F('320e-9')+fp+J+AW+F('320e-9')+F('100e-9'))
    other_peak = F('.0001')+(F('209e-9')+F('.0001')*F('3e-6'))/F('.001')
    other_peak += AW*(1+10000*(F('.001')+F('3e-6')))/F('.001')
    periodic_peak = 8*E*(F('.001')/fm+2)/F('.001')+other_peak
    # An arbitrary 1ms window may include startup or cross the transition.
    # Minimum spacing of frame starts, not a convex mean of two peak bounds.
    peak = 8*E*(F('.001')/min(fm,8*196*TM)+2)/F('.001')+other_peak
    placement = fm-8*164*TP-J-(240*TP+J)
    max_gap=ceil_frame-7*164
    fixed_delivery=delivery()['source_to_applicable_fresh_rule_s']+(max_gap-CFG['delivery']['maximum_control_gap_ticks'])*TP
    resource_ok = response<=F('3e-6') and peak<=F('.8') and placement>=0
    # All-history price, startup and terminal edges explicit; no free stop at A.
    op_rate = F(W)/pminus+F(3*W)/T
    q = fixed_risk(M)
    corrections = ENV['F']/T*(1+F(1,W))+F(ENV['K0'])/T+F('1e-6')+q*op_rate
    app = 1000*(AR+AW)
    x = F('.0001')+(F('209e-9')+F('.0001')*F('3e-6'))/T
    cost = R*op_rate+(E-R)*corrections+app+x
    lower_read = max(F(0), W*RM*(1-START/T)/pplus-F(2*W)*R/T)
    return dict(status='sufficient candidate' if resource_ok else 'risk candidate rejected by resources',
        M_ticks=M, period_upper_s=pplus, frame_min_ticks=floor_frame, frame_max_ticks=ceil_frame,
        risk_upper=q, next_grid_risk_upper=fixed_risk(M+4),
        risk_upper_paying_all_six=fixed_risk(M,QSUM),
        placement_margin_s=placement, response_upper_s=response, peak_upper=peak,
        maximum_control_gap_ticks=max_gap,
        common_transport_fresh_install_upper_s=fixed_delivery,
        periodic_only_peak_upper=periodic_peak,
        resource_admitted=resource_ok, read_price_lower=lower_read,
        full_mission_price_upper=cost,
        full_app_term=app, common_X_term=x,
        true_optimal_period=None)


def profile_counts(profile, length, per_word=False):
    p = CFG['application']['profiles'][profile]
    if not p['per_epoch']: return 0
    # Fixed interval contained in the mission, arbitrary phase. At most one
    # extra epoch at each endpoint; safe for short and nonintegral intervals.
    n = p['per_epoch']*(ceil(length/F(p['epoch_ns'],10**9))+2)
    # Write q's are consecutive; 5 invertible mod W. No distinct-word oracle.
    return ceil(F(n,W)) if per_word else n


def moderate(p0, p1, profile, eps=F('.001')):
    L = FS/(B-B0)-START
    nw = profile_counts(profile,L+F('3e-6'))
    core = L-2*p1-F(2*nw,W)*p1
    if not (F('3e-6') < p0 <= p1 < L/2 and core > 0 and B*p1/W<1):
        raise ValueError('moderate lower domain')
    z = BETA*B*B*core*p0*(1-E/p0)**2*(1-B*p1/W)
    return max(F(0), z/(1+z)-F('1e-6'))


def tail(profile):
    L = FS/(B-B0)-START
    p1 = F(CFG['necessary']['tail_split_s'])
    nw_word = profile_counts(profile,L+F('3e-6'),per_word=True)
    intervals = int(L/p1)+2+nw_word
    cstar = max(E,F('3e-6'))
    a = (L-intervals*cstar)/(4*intervals)
    x = B*a/W
    assert 0<x<1
    z = 2*W*intervals*F(N-1,2*N)*x*x*(1-x)
    return dict(lower=max(F(0),z/(1+z)-F('1e-6')),
                windows_per_word_upper=intervals, writes_per_word_upper=nw_word, cell_s=a)


def necessary(profile, epsilon=F('.001')):
    first = F(CFG['necessary']['first_split_s']); last=F(CFG['necessary']['tail_split_s'])
    tail_result=tail(profile)
    if tail_result['lower'] <= epsilon:
        return dict(status='tail lower does not exclude every large period', tail=tail_result)
    # Epsilon .01 can need a different predeclared bracket; do not silently tune it.
    middle=moderate(first,last,profile)
    if middle <= epsilon:
        return dict(status='registered middle lower inconclusive',middle_lower=middle,tail=tail_result)
    step=F(CFG['necessary']['period_search_quantum_s'])
    lo,hi=ceil(F('3e-6')/step),int(first/step)
    while hi-lo>1:
        md=(hi+lo)//2
        if moderate(md*step,first,profile)>epsilon: hi=md
        else: lo=md
    p0=hi*step
    assert moderate(p0,first,profile)>epsilon>=moderate((hi-1)*step,first,profile)
    read_floor=max(F(0), W*RM*(1-START/T)/p0-F(2*W)*R/T)
    return dict(status='necessary P<P0 for full declared class',P0_s=p0,
                neighbor_lower=moderate((hi-1)*step,first,profile),
                exclusion_lower=moderate(p0,first,profile),middle_lower=middle,
                tail=tail_result,mission_read_price_floor=read_floor,
                ignored_positive_application_cost=True)


def app_edges(profile):
    p=CFG['application']['profiles'][profile]
    if not p['per_epoch']: return dict(mission_extra_price=F(0),quiet_extra_price=F(0))
    burst=F(p['burst_each']); rate=F(1000); d=F('3e-6');k=1000;tq=F('.9')*T
    excess=k*(burst+rate*d)/tq
    newrate=F(p['per_epoch']*10**9,p['epoch_ns']+CFG['application']['strict_cap_epoch_extra_ns'])
    strict_rate_upper=newrate+k*(burst+newrate*d)/tq
    assert strict_rate_upper <= rate
    return dict(edge_rate_excess_per_s=excess,quiet_extra_price=(AR+AW)*excess,
        quiet_m_only_edge_price=(AR+AW)*k*burst/tq,
        quiet_left_expansion_price=(AR+AW)*k*rate*d/tq,
        protection_quiet_extra_price=R*excess,
        mission_extra_price=(AR+AW)*burst/T,
        strict_20ns_nominal_rate_per_s=newrate,
        strict_20ns_expanded_quiet_rate_upper=strict_rate_upper,
        strict_20ns_aggregate_count_margin=(rate-newrate)*tq-k*(burst+newrate*d),
        individual_unexpanded_component_sufficient_length_s=burst/(rate-newrate),
        individual_component_mean_cap_proved=False,
        original_arbitrary_quiet_mean_1000_proved=False)


def tests():
    result=[]
    def check(name, condition):
        if not condition: raise AssertionError(name)
        result.append(name)
    check('same full R0-A exposure',S2==B0*B0*T+(B+B0)*FS)
    check('initial plateau allowed and exposure exact',(B-B0)*F(115776)==FS)
    d=delivery()
    check('positive nonzero timing budgets',d['ingress_s']>0 and d['batch_and_install_s']>0)
    check('legacy cut violates literal10us',d['old_cut_lower_s']>F('10e-6'))
    check('extra expiry cut rejected',not d['extra_cut_after_expiry_admitted'])
    check('pending corrections need crossing cost',common_upper(1)['cross']>0)
    check('support3 general upper not proof of failure',common_upper(3)['risk_upper']>F('.001'))
    check('full fixed k1 sufficient',common_upper(1)['risk_upper']<=F('.001'))
    def next_cut(t): return (t//4000+1)*4000
    check('cut equality belongs to next packet',next_cut(4000)==8000)
    check('record just before cut included',next_cut(3999)==4000)
    # Minimal abstract state check: a candidate certifies a processed prefix,
    # never merely a copied live generation. No hardware timing claim.
    def low(now,end,processed,current,pending=False,healthy=True):
        return now>end and processed==current and not pending and healthy
    check('deadline equality is FAST',not low(10,10,7,7))
    check('mature precomputed permission accepted',low(11,10,7,7))
    check('unprocessed generation cannot permit',not low(11,10,7,8))
    check('pending history veto',not low(11,10,7,7,True))
    check('loss veto',not low(11,10,7,7,healthy=False))
    w=90*10**9
    source_pair = w <= w
    delivery_pair = (w+4000)-0 <= w
    check('PAIR uses source, not delivery gap',source_pair and not delivery_pair)
    def replay(records):
        last=None; short=long=0
        for source,processed in records:
            short=max(short,processed+90*10**9)
            if last is not None and source-last<=w:
                long=max(long,processed+180*10**9)
            last=source
        return short,long
    a=replay([(0,5000),(100,5000)])
    b=replay([(100,5000)])
    check('last-only packet loses long HOLD',a[1]>0 and b[1]==0)
    # Conditional two-arrival witness, all correctable states, small n only.
    for n in (3,4,5):
        for initial in (0,1):
            failures=0
            for i in range(n):
                for j in range(n):
                    state=initial^(1<<i)
                    hit=state.bit_count()>1
                    state^=1<<j
                    failures+=hit or state.bit_count()>1
            check(f'cell lower any correctable state/n{n}/initial{initial}',F(failures,n*n)>=F(n-1,n))
    for profile in ('none','uniform','bursty'):
        low=necessary(profile)
        check(profile+' lower all-period coverage',low['status'].startswith('necessary'))
        if profile!='none':
            check(profile+' useful writes weaken lower',low['mission_read_price_floor']<=necessary('none')['mission_read_price_floor'])
            e=app_edges(profile)
            check(profile+' finite quiet-edge price positive',e['quiet_extra_price']>0)
            check(profile+' strict cap on proposed20ns profile',e['strict_20ns_expanded_quiet_rate_upper']<=1000)
            check(profile+' aggregate count slack positive',e['strict_20ns_aggregate_count_margin']>0)
            check(profile+' quiet edge separates expansion',e['quiet_extra_price']==e['quiet_m_only_edge_price']+e['quiet_left_expansion_price'])
    # One arrival in a 1ns component: aggregate contract does not assert a
    # false pointwise cap for each arbitrarily short quiet component.
    check('individual quiet component cap not implied',F(1)/F('1e-9')>1000)
    spec=importlib.util.spec_from_file_location('accepted126',ROOT/'experiments/t126-regime-map/bounds.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    p0=necessary('none')['P0_s'];first=F('.2');L=FS/(B-B0)-START
    check('no-app reduction equals accepted T126 lower',moderate(p0,first,'none')==mod.moderate_lower(W,N,B,L,E,p0,first,F('1e-6')))
    # Finite-cell erase counting, independent literal geometry: each short
    # write envelope intersects at most two free cells when width<P.
    for P in (10,11,17):
        cells=[(j*P+2,(j+1)*P) for j in range(20)]
        for a in range(20*P):
            touched=sum(max(x,a)<min(y,a+3) for x,y in cells)
            check(f'erased-cell-count/P{P}/a{a}',touched<=2)
    for x in (F(1,3),F(-1,3),F(0),F(1,10**25)):
        s=shown(x)
        check('directed display '+str(x),F(s['lower'])<=x<=F(s['upper']))
    candidate=fixed_candidate()
    check('fixed all-grid sufficient root neighbor',candidate['risk_upper']<=F('.001')<candidate['next_grid_risk_upper'])
    check('constant candidate resource admitted',candidate['resource_admitted'])
    check('stronger fixed changed phase still admits10us',candidate['common_transport_fresh_install_upper_s']<=F('10e-6'))
    check('constant startup peak not discarded',candidate['peak_upper']>=F(R4['rows']['selected_r3_original']['resources']['whole_bus_peak']))
    return dict(passed=len(result),names=result)


def calculate():
    own=R4['rows']['selected_r3_original']
    own_price=F(own['full_bus_mission'])
    lows={p:necessary(p) for p in ('none','uniform','bursty')}
    edges={p:app_edges(p) for p in ('none','uniform','bursty')}
    for p in lows:
        lows[p]['gain_over_our_r4_bus_lower']=lows[p]['mission_read_price_floor']/(own_price+edges[p]['mission_extra_price'])
    return dict(task=196,scope=CFG['scope'],sources=source_check(),
        addressed_tests=tests(),delivery=delivery(),
        environment={k:ENV[k] for k in ('T','eps','B','b','FS','S2exact','D','W','n','K0')},
        general_mandatory_support={str(k):common_upper(k) for k in (1,3,9,27)},
        our_r4=dict(risk_upper=F(own['risk_upper']),
          full_bus_mission=own_price,full_bus_quiet=F(own['full_bus_quiet']),
          peak=F(own['resources']['whole_bus_peak']),response_s=F(own['resources']['response_upper']),
          applicability='conditional on common full contract, not the unmodified stage2 simulator'),
        fixed_candidate=fixed_candidate(),necessary_classes=lows,application_edges=edges,
        epsilon_sensitivity={str(e):dict(necessary=necessary('bursty',e),candidate=fixed_candidate(e)) for e in (F('.01'),F('.0001'))},
        CPU_cost=None,energy_cost=None,global_optimum=None)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--json',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    report=serial(calculate())
    rendered=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if args.check:
        expected=(HERE/'outputs/report.json').read_text()
        assert rendered==expected,'report differs; no files overwritten'
        print(f"PASS: {report['addressed_tests']['passed']} checks; report byte-for-byte; 3 accepted source blobs unchanged")
    elif args.json: print(rendered,end='')
    else:
        for key in ('delivery','general_mandatory_support','fixed_candidate','necessary_classes','application_edges'):
            print(key);print(json.dumps(report[key],ensure_ascii=False,indent=2))
