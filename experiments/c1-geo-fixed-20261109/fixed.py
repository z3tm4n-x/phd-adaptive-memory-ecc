"""GEO envelope and constant schedules. Run with --check to replay the eight rows."""
import argparse
import csv
import hashlib
import json
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
from math import ceil
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
GRID = EXP/'regime-map-methodology-20261019/predictability-volume-20261028'
CHAIN = EXP/'t141-radiation-chain'
NS = 10**9


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def csv_rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def fmt(q, digits=7, upper=False):
    with localcontext() as ctx:
        ctx.prec = digits
        ctx.rounding = ROUND_CEILING if upper else ROUND_FLOOR
        q = F(q)
        return format(+(Decimal(q.numerator)/Decimal(q.denominator)), 'g')


INPUT = read(GRID/'inputs.json')
RESOURCE = read(GRID/'resource-result.json')['rows']
service = INPUT['service']
XM, XP = map(F, (service['xi_minus'], service['xi_plus']))
J = F(service['J_ns'])/NS
DE = 124*XP/NS + 3*J  # full weak-E aperture including relative endpoint jitter
T = F(INPUT['bank']['mission_s'])
DELTA = F(INPUT['information']['lifetime_delta_exec'])
DREF = INPUT['environment']['reference_positions']
N = 39
DIRECT = (F(0), F(1,100000), F(1,10000))


def environment():
    components = [r for r in csv_rows(CHAIN/'outputs/components.csv') if F(r['shield_g_cm2'])==3]
    assert len(components)==6
    rates = {phase: {r['component']: F(r['lambda_s_inv']) for r in components if r['phase']==phase}
             for phase in ('background', 'solar')}
    assert all(set(parts)=={'LET_exclusive','H_low','H_high'} for parts in rates.values())
    b, p = (sum(parts.values(), F(0)) for parts in rates.values())
    tau = F(str(read(CHAIN/'config.json')['cosrad_Teff_s']))
    B = b+p
    s1 = b*T + p*tau
    s2 = b*b*T+2*b*p*tau+p*p*tau
    assert s2 == b*b*(T-tau) + B*B*tau
    old = next(r for r in csv_rows(CHAIN/'outputs/shield-summary.csv') if F(r['shield_g_cm2'])==3)
    for x,key in ((B,'peak_upper_s_inv'),(s1,'N_total_upper'),(s2,'S2_upper_s_inv')):
        assert abs(x/F(old[key])-1) < F(1,10**13)
    return dict(rates=rates, b=b, p=p, B=B, tau=tau, S1=s1, S2=s2)


def period(w,k):
    nominal = F(196*w*k, NS)
    return nominal, nominal*XM-J, nominal*XP+J


def risk_upper(w,k,env,d):
    factor = F(w*N*(N-1), 2*DREF**2)
    pplus = period(w,k)[2]
    accum = factor*(pplus+DE)*env['S2']
    aperture = factor*2*env['B']*DE*env['S1']
    return {'accumulation':accum, 'aperture':aperture,'execution':DELTA,'direct':d,
            'total':min(F(1),accum+aperture+DELTA+d)}


def tail_lower(w,P0,env):
    """All physical periods >= P0 on one admissible clock, every phase including OFF."""
    tau = env['tau']
    pieces = ceil(tau/120)
    length = tau/pieces
    mu_rate = N*env['B']/DREF
    count = length/P0+2
    empty = max(F(0),length-count*DE)
    # T45/free-cell lemma (13)-(14). exp(-x)>=1-x, 1-exp(-Z)>=Z/(1+Z).
    assert mu_rate*length < 1
    z = pieces*w*F(N-1,2*N)*(1-mu_rate*length)*mu_rate**2*empty**2/(count+1)
    return max(F(0),z/(1+z)-DELTA)


def price(w,k,env,q,res):
    _,pminus,pplus = period(w,k)
    nmax = F(res['calendar']['necessary_class_maximum_reads_upper'])
    nlow = (1-DELTA)*w*max(F(0),T/pplus-2)
    nhi = min(nmax,w*(T/pminus+2)+DELTA*nmax)
    flips = N*w*env['S1']/DREF
    repairs = min(nhi,2*flips+q*nmax)
    result = {'reads_lower':nlow, 'reads_upper':nhi, 'repairs_upper':repairs,
              'repair_source_upper_bit_inversions':flips, 'post_failure_reads_charged':q*nmax}
    for coord, ticks in [('bus',48),('serial',68)]:
        lo = nlow*(ticks*XM/NS-J)
        hi = nhi*(ticks*XP/NS+J) + repairs*(56*XP/NS+J)
        key = 'pure_bus' if coord=='bus' else 'serial'
        app = {side: F(res['application'][key+'_mission_'+side])*T for side in ('lower','upper')}
        init = F(res['initialization'][key+'_upper_s'])
        result[coord] = {'lower_s':lo,'upper_s':hi,'lower_percent':100*lo/T,'upper_percent':100*hi/T,
                         'app_s':app,'init_upper_s':init,'known_total_upper_s':hi+app['upper']+init}
    return result


def class_floor(w,eps,env,res):
    lo,hi = F(0),F(1)
    while tail_lower(w,hi,env)<=eps:
        hi *= 2
        if hi>T: raise ValueError('No tail witness at the mission horizon')
    while hi-lo > F(1,10**11):
        mid = (lo+hi)/2
        if tail_lower(w,mid,env)>eps: hi=mid
        else: lo=mid
    assert tail_lower(w,hi,env)>eps
    need=(1-DELTA)*w*max(F(0),T/(hi+J)-2)
    nmax=F(res['calendar']['necessary_class_maximum_reads_upper'])
    available=F(res['resource']['available_serial_upper_for_necessary_exclusion'])*T
    bus,serial=(need*(ticks*XM/NS-J) for ticks in (48,68))
    return {'witness_threshold_bracket_s':[lo,hi], 'all_P_ge_excluded_s':hi,
            'Q_lower_on_tail':tail_lower(w,hi,env),'required_reads_lower':need,'maximum_reads_upper':nmax,
            'bus_lower_s':bus,'bus_lower_percent':100*bus/T,'serial_lower_s':serial,
            'serial_lower_percent':100*serial/T,'available_serial_upper_s':available,
            'excluded_by_count':need>nmax,'excluded_by_serial':serial>available}


def peak(res):
    # Bound every intersecting frame and both reserved application streams in 1 ms.
    window = F(res['resource']['cap_window_ns'])
    duration = max(124,144)*XP + J*NS
    frames = 2+ceil((window+duration+J*NS)/(1568*XM))
    app_each = 1+ceil(F(window+3000,1000020))
    serial = F(res['resource']['peak_including_full_reserved_management_slot'])
    bus = (frames*8*(104*XP+2*J*NS) + app_each*((48+104)*XP+3*J*NS) + frames*(64*XP+J*NS))/window
    assert bus <= serial < F(res['resource']['serial_cap'])
    return {'window_ns':window,'all_slot_bus_upper_percent':100*bus,'all_slot_serial_upper_percent':100*serial,
            'serial_limit_percent':100*F(res['resource']['serial_cap']),
            'remaining_serial_pp':100*F(res['resource']['peak_margin_for_unaccounted_serial_work']),
            'app_response_upper_ns':F(res['application']['inherited_response_envelope_ns']),
            'deadline_ns':res['application']['response_deadline_ns']}


def row(res,eps,env):
    w=res['words']; nominal,pm,pp=period(w,1)
    assert pm*NS==F(res['calendar']['cycle_lower_ns']) and pp*NS==F(res['calendar']['cycle_upper_ns'])
    u=risk_upper(w,1,env,F(0)); lower=tail_lower(w,nominal*XP,env)
    cap=INPUT['comparison']['period_menu']['max_kL']
    scale=F(w*N*(N-1),2*DREF**2)
    maximum_k=(eps-u['execution']-u['aperture']-scale*(J+DE)*env['S2'])/(scale*nominal*XP*env['S2'])
    k=min(cap,maximum_k.numerator//maximum_k.denominator)
    candidate=None
    if k>=1:
        risk=risk_upper(w,k,env,F(0));assert risk['total']<=eps
        assert k==cap or risk_upper(w,k+1,env,F(0))['total']>eps
        candidate={'k':k,'period_s':period(w,k),'risk':risk,'direct_plus_other_headroom':eps-risk['total'],
                   'price':price(w,k,env,risk['total'],res)}
    required=class_floor(w,eps,env,res)
    excluded=required['excluded_by_count'] or required['excluded_by_serial']
    assert not (candidate and excluded) and lower<=u['total']
    return {'W':w,'MiB':F(w,262144),'epsilon':eps,'continuous':{'k':1,'period_s':[nominal,pm,pp],
            'Q_lower':lower,'risk':u,'price':price(w,1,env,u['total'],res),'signed_headroom':eps-u['total']},
            'necessary':required,'candidate':candidate,'peak':peak(res),
            'direct_sensitivity_at_continuous':[{'D1':d,'upper':risk_upper(w,1,env,d)['total'],
                'passes':risk_upper(w,1,env,d)['total']<=eps} for d in DIRECT],
            'status':'confirmed_conditional' if candidate else 'whole_class_excluded_conditional' if excluded else 'unresolved'}


def create():
    env=environment()
    rows=[row(r,eps,env) for r in RESOURCE for eps in (F(1,1000),F(1,10000))]
    files=[CHAIN/'config.json',CHAIN/'outputs/components.csv',CHAIN/'outputs/shield-summary.csv',GRID/'inputs.json',
           GRID/'resource-result.json',GRID/'THEORY.md',EXP/'t413-cy62167-placement-d2/handoff.json',
           EXP/'mission-rise-rate-20261022/REPORT.md',EXP/'mission-rise-rate-20261022/outputs/pilot.json']
    return {'base':'921720b3370cc79a72477dc13836d3e6748b869f','environment':env,'T_s':T,'reference_bits':DREF,
            'clock':[XM,XP],'jitter_s':J,'aperture_s':DE,'delta_exec':DELTA,'rows':rows,
            'price_scope':'protection accesses; additional control, CPU and energy remain parameters',
            'source_sha256_LF':{str(p.relative_to(EXP.parent)).replace('\\','/'):hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in files}}


def table(data):
    lines=['# Постоянная защита на ГСО за 315 576 000 с', '',
      'Условный вход T141, 3 г/см², D₁=0. Нижние границы округлены вниз, верхние вверх. Цена — дополнительные обращения защиты. Периоды P₁ даны номинально, физический интервал и обе координаты полной стоимости содержатся в JSON.', '',
      '| МиБ | ε | P₁, мс | Q⁻…Q⁺ при P₁ | Шина при P₁, %; млн с | Необходимая цена шины, %; млн с | Допустимый кандидат, k / P, с | Верх шины кандидата, %; млн с | Запас по Q при P₁ | Исход |',
      '|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in data['rows']:
        c=r['continuous']; p=c['price']['bus']; n=r['necessary']; a=r['candidate']; u=a['price']['bus'] if a else None
        rng=lambda x,y:fmt(x,5)+'…'+fmt(y,5,True)
        lines.append('|'+' | '.join([fmt(r['MiB']),fmt(r['epsilon']),fmt(c['period_s'][0]*1000,9),rng(c['Q_lower'],c['risk']['total']),
          rng(p['lower_percent'],p['upper_percent'])+'; '+rng(p['lower_s']/10**6,p['upper_s']/10**6),
          fmt(n['bus_lower_percent'],5)+'; '+fmt(n['bus_lower_s']/10**6,5),
          str(a['k'])+' / '+fmt(a['period_s'][0],9) if a else '—',
          fmt(u['upper_percent'],5,True)+'; '+fmt(u['upper_s']/10**6,5,True) if a else '—',fmt(c['signed_headroom'],5),
          {'confirmed_conditional':'подтверждён','whole_class_excluded_conditional':'класс исключён','unresolved':'не установлено'}[r['status']]])+' |')
    lines += ['','У исключённых строк нижняя цена — необходимое требование гипотетического допустимого периода. Каждый его представитель потребовал бы больше разрешённого ресурса. Границы Q относятся к супремуму по объявленному классу. См. [договор и вывод](README.md).','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true'); parser.add_argument('--pilot',action='store_true')
    args=parser.parse_args()
    if args.pilot:
        r=row(RESOURCE[0],F(1,1000),environment())
        print(r['status'],r['candidate']['k'] if r['candidate'] else None,fmt(r['continuous']['risk']['total'],9,True));return
    data=create(); datafile=json.dumps(data,default=str,indent=2,ensure_ascii=False)+'\n'
    for name,content in [('fixed.json',datafile),('TABLE.md',table(data))]:
        target=HERE/name
        if args.check:
            if target.read_text(encoding='utf-8')!=content: raise SystemExit('Mismatch: '+name)
        else: target.write_text(content,encoding='utf-8',newline='\n')
    print('PASS: eight GEO rows')


if __name__=='__main__': main()
