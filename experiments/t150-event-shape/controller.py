"""T150: addressed sufficient requirements, not a new physical certificate.

Runs separately from radiation.py to keep the accepted packages' historical
module names isolated. Accepted source files and reports are read-only.
"""
import argparse
import copy
import csv
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/t88-dstar-sensitivity'))
import engine as theory


def encode(v):
    if isinstance(v,F):return str(v)
    if isinstance(v,dict):return {k:encode(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [encode(x) for x in v]
    return v


def json_write(path,v):
    path.write_text(json.dumps(encode(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def csv_write(path,rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def fixed_candidate(p,direct):
    """T52 sufficient constant calendar, using an ADDITIONAL declared S2 cap.

    This is an upper for one feasible constant, never a necessary lower of the
    optimum constant class. The old class lower is not transferred to a new cap.
    """
    t=theory.j.t58
    e=sum(F(p['q'][k]) for k in ('rho0','delta_exec','delta_svc'))
    square=min(p['S2'],t.rarity(p['B'],p['b'],p['FS'],p['T'])[1])
    slope=p['beta']*square+p['K']*p['B']/p['W']
    M=t.floor((p['eps']-e-direct)/(p['tp']*slope))
    if M<=0:return dict(feasible=False,M=M)
    r=t.Resource(W=p['W']//2,c=2*p['cp'],H=p['T'],h=F('.001'),tax=F(1),peak=F('.8'),
        delay=F('3e-6')/(1+p['margin']),sigma=F(p['cfg']['resources']['application_sigma_s']),
        u=F(p['cfg']['resources']['application_rate']),g=F(p['cfg']['resources']['application_max_request_s']),
        tick=F('1e-9'),clock_error=F('.00001'))
    rv=t.resources(r,M)
    cost=F(p['W']*p['c'],M)
    return dict(feasible=t.resource_ok(rv),M=M,period_upper=M*p['tp'],
        risk=e+direct+M*p['tp']*slope,cost_lower=cost-2*p['cp']/p['T'],
        cost_upper=cost+2*p['cp']/p['T'],peak=rv['peak_upper'],delay=rv['delay_upper'])


def mission_price(p,quiet):
    # Same >=90% quiet coverage and <=1000 intervals as accepted T146.
    return F('.9')*quiet+F('.1')*(p['cp']/p['gm']+p['CX'])+(2*p['cp']+p['sigmaX'])*1001/p['T']


def main(out):
    out.mkdir(parents=True,exist_ok=True)
    t146=json.loads((ROOT/'experiments/next-route-20261013/route-report.json').read_text())
    t119=json.loads((ROOT/'experiments/t119-err-joint-bound/report.json').read_text())
    point=next(r for r in t119['rows'] if r['name']=='one_presented')
    rec=t146['recommended'];Dref=F(rec['Dstar'])
    template=theory.calendar(theory.context('3','combined'),176)
    template['Dstar']=Dref
    resource_cfg=copy.deepcopy(template['cfg'])
    resource_cfg['resources']['extra_monitor_control_rate']=str(template['CX']+F('.001'))
    paid_resource=theory.resources(resource_cfg)
    paid_delay=(1+template['margin'])*paid_resource['delay']
    paid_peak=paid_resource['peak']+(F('45e-9')+F('.04')*(F('.001')+2*paid_delay)+F('90e-9'))/F('.001')
    paid_resource_pass=paid_resource['ok'] and paid_delay<=F('3e-6') and paid_peak<=F('.8')
    assert paid_resource_pass
    old=dict(shield_g_cm2='3',response_case='old_R0A',choice='accepted_rectangle',
        background_s_inv=str(template['b']),solar_peak_s_inv=str(template['B']-template['b']),
        F_solar=str(template['FS']),F=str(template['b']*template['T']+template['FS']),S2_s_inv='6940')
    inputs=list(csv.DictReader((out/'shape-transfer.csv').open(encoding='utf-8')))
    selected=[old]+[r for r in inputs if r['response_case'] in ('full','no_low') and
        (r['choice']=='rectangle' or (float(r['mean_events'] or 0)>100 and r['choice']=='model_r_q90'))]
    gates=[];potentials=[];records=[]
    # Same physical service/calendar class; policies may use different ka.
    # A single ERR ka=1 is fallback, not a claim that it is the best ERR policy.
    # ka=3 / h=120 is one addressed ERR candidate, not a complete grid search.
    for row in selected:
        p=copy.deepcopy(template)
        p.update(b=F(row['background_s_inv']),B=F(row['background_s_inv'])+F(row['solar_peak_s_inv']),
                 FS=F(row['F_solar']),S2=F(row['S2_s_inv']))
        b,B,FS,S2,T=(p[k] for k in ('b','B','FS','S2','T'))
        init=p['K']*B*p['Ps']/p['W']
        vc=F(rec['vc_per_s'])  # same T146 channel threshold, windows and a=1e5
        m=theory.j.window(p,F(100000),F(1),F(1),F(2),'total_load',2)
        cb=theory.j.pair_bound(dict(p,Dstar=F(0)),101,vc)
        channel_cap=p['eps']-cb['risk_upper']
        err_base=theory.old.errors(p['q'],'ERR-only')+init
        aE=F(p['W']-1,p['W'])
        r0=6*p['Ps']+p['dE']+p['Gp']+p['f']
        major=theory.err.majorant(B,b,T,FS,S2,aE,r0,F(120))
        err_pair=p['beta0']*min(3*p['Ps']*S2,p['Ps']*S2+3*p['Ps']*major['Q'])
        err_cap=p['eps']-err_base-err_pair
        # Necessary condition for the DECLARED sufficient bound to pass even
        # with 100% bus and perfect information. It is not a physical lower risk.
        ideal_short=p['W']*p['cm']
        eps_net=p['eps']-theory.old.errors(p['q'],'combined')-Dref
        r_req=(eps_net/ (p['beta']*ideal_short)-b*b*T-2*b*FS)/((B-b)*FS)
        requirements=dict(shield_g_cm2=row['shield_g_cm2'],response_case=row['response_case'],choice=row['choice'],
            S2_s_inv=float(S2),D_max_channel_g176_ka101=float(channel_cap),
            D_max_ERR_g176_ka3_h120=float(err_cap),
            D_max_always_short_combined=float(p['eps']-theory.old.errors(p['q'],'combined')-init-p['beta']*p['Ps']*S2),
            S2_cap_at_100pct_bus_Dref=float(eps_net/(p['beta']*ideal_short)),
            necessary_r_for_short_term_Dref=float(r_req),
            necessary_r_at_80pct_bus_Dref=float((F('.8')*eps_net/(p['beta']*ideal_short)-b*b*T-2*b*FS)/((B-b)*FS)),
            c_word_max_100pct_bus_Dref_s=float(eps_net/(p['beta']*p['W']*S2)),
            lower_ERR_assumed=float(aE),growth_rho_assumed_per_s=.048,
            scope='requirements for stated sufficient formulas; no physical impossibility claim')
        gates.append(requirements)
        for d in (F(0),Dref,F('.0005')):
            p['Dstar']=d
            fixed=fixed_candidate(p,d)
            # Fix the SAME pair allowance for the chosen constant and its
            # oracle relaxation; the latter is not a feasible causal policy.
            fixed_quota=sum(F(p['q'][k]) for k in ('rho0','delta_exec','delta_svc'))
            fixed_initial=p['K']*B*fixed.get('period_upper',F(0))/p['W']
            Epairbudget=p['eps']-d-fixed_quota-fixed_initial
            assert Epairbudget>0
            f=b*T+FS
            ideal=p['W']*p['cp']*p['beta']*f*f/(T*Epairbudget)
            Gideal=T*S2/(f*f)
            potentials.append(dict(shield_g_cm2=row['shield_g_cm2'],response_case=row['response_case'],choice=row['choice'],
                D_assumed=float(d),F=float(f),S2_s_inv=float(S2),G_ideal=float(Gideal),
                pair_allowance_from_fixed=float(Epairbudget),fixed_nonpair_quota=float(fixed_quota),
                fixed_initial_allowance=float(fixed_initial),
                oracle_pair_only_price=float(ideal),fixed_sufficient_feasible=fixed['feasible'],
                fixed_period_upper_s=float(fixed.get('period_upper',0)),fixed_price_upper=float(fixed.get('cost_upper',0)),
                declared_fixed_over_oracle=float(fixed['cost_lower']/ideal) if fixed['feasible'] else None,
                meaning='pair-functional relaxation with fixed-reference pair allowance; oracle adds no information/resource/delay costs',
                optimum_constant_lower=None,physical_gain=None))
            # Always-short own-ERR fallback and candidate; no monitor expense
            # is removed from the shared base X envelope, a conservative choice.
            for ka,lower in ((1,aE),(3,aE),(3,F(0))):
                q=major['Q'] if lower else S2
                ep=p['beta0']*min(ka*p['Ps']*S2,p['Ps']*S2+ka*p['Ps']*q)
                risk=err_base+d+ep
                pr=theory.err.err_price(p,ka,F(120),risk)
                cost=mission_price(p,pr['returns_upper'])
                admitted=risk<=p['eps'] and p['resource_pass']
                records.append(dict(shield_g_cm2=row['shield_g_cm2'],response_case=row['response_case'],choice=row['choice'],
                    D_assumed=float(d),policy=f'ERR_ka{ka}_a{float(lower):.6g}',risk_upper=float(risk),
                    risk_sufficient=bool(admitted),price_upper=float(cost),channel_a_assumed=None,
                    fixed_feasible=fixed['feasible'],
                    G_vs_declared_fixed_conditional=float(fixed['cost_lower']/cost) if fixed['feasible'] and admitted else None,
                    G_cert_optimum_constant=None,physical_Gcert=None,
                    status='conditional arithmetic under required parents/ERR/growth/quiet/service; not accepted new physics'))
            ch=theory.j.evaluate(p,m,101,vc,'direct-fast',F(0),vc_kind='fixed_T146')
            ch_ok=ch['status']=='certified_conditional' and paid_resource_pass
            cost=None
            if ch_ok:
                cost=mission_price(p,ch['returns_upper'])+p['cp']/p['gm']*F('.001')+F('.001')
            records.append(dict(shield_g_cm2=row['shield_g_cm2'],response_case=row['response_case'],choice=row['choice'],
                D_assumed=float(d),policy='channel_T146_a100000',risk_upper=float(ch['risk_upper']),
                risk_sufficient=bool(ch_ok),price_upper=float(cost) if cost else None,channel_a_assumed=100000,
                fixed_feasible=fixed['feasible'],
                G_vs_declared_fixed_conditional=float(fixed['cost_lower']/cost) if fixed['feasible'] and ch_ok else None,
                G_cert_optimum_constant=None,physical_Gcert=None,
                status=ch['status']+'; extra outage=.001 and X=.001 charged when admissible'))
            if row['response_case']=='old_R0A' and d==Dref:
                assert ch_ok and cost==F(rec['mission_paid_upper'])
                assert fixed['M']==t146['fixed_witness_recomputed']['M']
    csv_write(out/'controller-requirements.csv',gates)
    csv_write(out/'controller-comparison.csv',records)
    csv_write(out/'potentials.csv',potentials)
    anchors=dict(old_R0A_S2=6940,Dstar_old=float(Dref),
        T119_ERR_E_gain_lower=str(point['gain_at_nonzero_application_lower']),
        T119_ERR_E_gain_decimal=float(F(point['gain_at_nonzero_application_lower'])),
        T119_scope='accepted E service, g196 ka5 h120; not full-U or r4 ka3',
        T135_scope='accepted E/r4 implementation point remains unchanged; no numerical transplant',
        T146_fullU_class_gain_lower=rec['gain_lower'],T146_fullU_class_gain_decimal=float(F(rec['gain_lower'])),
        T146_service='full-U100, g176 ka101; different from T119 E',
        common_channel_full_peak_upper=paid_peak,common_channel_application_delay_upper=paid_delay,
        new_Gcert_optimum_constant=None,
        required_before_release=['physical or explicitly assumed joint deterministic radiation cap',
            'marked-parent law/word uniformity and full38 Dstar',
            'lower ERR or lower-Laplace channel, growth and delays',
            'quiet fraction and return/outage/price requirements',
            'matching service and a new lower of optimum constant class'],
        Pi_vs_epsilon='If the environment lies outside the admitted cap with probability .1, a conditional memory bound .001 alone gives only unconditional <=.1+.9*.001, not .001.',
        scope='selected fixed comparator and sufficient requirements; no new class-optimal certificate')
    json_write(out/'controller-contract.json',anchors)
    deps=[Path(m.__file__).resolve() for m in list(sys.modules.values())
          if getattr(m,'__file__',None) and str(ROOT/'experiments') in str(Path(m.__file__).resolve())]
    deps=sorted(set(deps+[ROOT/'experiments/next-route-20261013/route-report.json',
        ROOT/'experiments/t119-err-joint-bound/report.json',
        ROOT/'experiments/t135-demo-operating-point/report-final.json']))
    json_write(out/'controller-provenance.json',dict(code_sha256=digest(Path(__file__)),
        input_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in deps},
        declared_radiation_sha256=digest(out/'shape-transfer.csv'),
        output_sha256={n:digest(out/n) for n in ('controller-requirements.csv','controller-comparison.csv','potentials.csv','controller-contract.json')}))
    print(f'T150 controller requirements: {len(gates)} radiation cases, {len(records)} scoped substitutions')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=HERE/'outputs')
    main(p.parse_args().out)
