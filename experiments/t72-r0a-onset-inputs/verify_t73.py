"""Directed verification of T73 SHA 7ed0f6c; exact rational decisions.

T58 supplies the certified exponential, rarity, integer-domain solver and
resource masks. No floating-point/libm result decides a pass/fail.
"""
from __future__ import annotations
import copy
import csv
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
THEORY_SHA='7ed0f6c0770ba21f12b03493171006dd0b82cc84'
spec=importlib.util.spec_from_file_location('t72_reused_t58',HERE.parent/'t58-fixed-baseline-r0b/certificate.py')
t58=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=t58
spec.loader.exec_module(t58)


def bounds(x):
    x=F(x)
    result=[]
    for mode in [ROUND_FLOOR,ROUND_CEILING]:
        with localcontext() as c:
            c.prec=24;c.rounding=mode
            result.append(str(Decimal(x.numerator)/Decimal(x.denominator)))
    return result


def load():
    return json.loads((HERE/'inputs/t73_7ed0f6c.json').read_text())


def variants():
    original=load()
    yield 'T73_published',original,'All exact published inputs; conditional, not physical qualification'
    # Retain every supplied T72 quota. The two absent fields are ADDITIONAL
    # explicit conditional requirements; no T72 number is reduced to pass.
    extended=copy.deepcopy(original)
    early=json.loads((HERE/'config.json').read_text(),parse_float=str)['conditional_r0a']
    extended['mark_contract']['D_star_full38_direct_exposure_upper']=early['full38_direct_exposure_upper_proposal']
    q=extended['whole_mission_quotas']
    for name,source in [('rho0','delta_initial_proposal'),('delta_svc','delta_service_proposal'),
                        ('delta_E','delta_ERR_proposal'),('delta_M','delta_monitor_joint_proposal')]:q[name]=early[source]
    q['K0']=0
    with (HERE.parent/'t68-v21-inputs/outputs/numerics.csv').open() as f:
        exact={F(r['rho']):r for r in csv.DictReader(f)}
    for env in extended['environments']:
        r=exact[F(env['shield_g_cm2'])]
        env['bbar_per_s'],env['solar_peak_per_s']=r['nuG'],r['nuS']
    yield 'T72_budgets_explicit_T73_extension',extended,('T72 D/four quotas/K0=0 retained; delta_exec=alpha_M=1e-6 ADDED explicitly. '
         'T73 monitor, total-load growth, 1ns paired calendar and full mark contract are additional assumptions; original T72 has no certified Poisson monitor.')
    revised=copy.deepcopy(extended)
    proposals=json.loads((HERE/'inputs/t72_explicit_changes.json').read_text())
    revised['service'].update(proposals['first_revision']['service'])
    revised['monitor'].update(proposals['first_revision']['monitor'])
    yield 'T72_explicit_same_method_revision',revised,('Same rule and unchanged T72 environmental/direct/known error inputs; explicit proposed changes: '
         'U 90 ticks, g119, ka85, hold5s/D6s; monitor a=1e11,A/a=1.001,w=.05,d=.01,lease=.175,k840000,z.01,vc.0001782. '
         'Stronger monitor and new timing need author qualification; no silent adoption.')
    shorter=copy.deepcopy(revised)
    shorter['service'].update(proposals['second_revision']['service'])
    yield 'T72_revision_shorter_return_hold',shorter,('Same explicit revision, hold reduced 5s -> 1s and price strip 6s -> 1.5s '
          'after the return-price bound failed. Both previous rows retained. Physical monitor/WCET requirements remain unqualified.')


def calculate(cfg,env):
    sc,q,s,m,r=[cfg[k] for k in ['scenario','whole_mission_quotas','service','monitor','resources']]
    W,n,T,eps=sc['W'],sc['n'],F(sc['T_s']),F(sc['epsilon'])
    dt=F(s['tick_nominal_s']);xm,xp=F(s['constant_clock_scale_min']),F(s['constant_clock_scale_max'])
    lo=lambda k:F(s[k])*dt*xm
    hi=lambda k:F(s[k])*dt*xp
    cm,cp,gm,gp=lo('c_ticks'),hi('c_ticks'),lo('g_ticks'),hi('g_ticks')
    Gp,fp=hi('decision_lead_ticks'),hi('fence_ticks')
    maxgap=(2*s['g_ticks']-s['c_ticks'])*dt*xp
    ps=W*gp;pl=s['long_multiplier']*ps
    wm,wp=F(m['window_ticks'])*dt*xm,F(m['window_ticks'])*dt*xp
    dp=F(m['delivery_computation_deadline_after_window_ticks'])*dt*xp
    hm,hp=F(m['lease_end_from_window_start_ticks'])*dt*xm,F(m['lease_end_from_window_start_ticks'])*dt*xp
    J=t58.ceil(T/wm);k=m['k'];H=F(m['H']);vc=F(m['v_c_per_s'])
    b,S=F(env['bbar_per_s']),F(env['solar_peak_per_s']);B=b+S;FS=115776*S
    beta=F(n-1,2*n*W);_,s2=t58.rarity(B,b,FS,T)
    S2=F(env['S2_rational_upper_per_s'])
    if S2<s2:raise ValueError('Published rational S2 is not an upper')
    V=min(vc*vc*T,b*b*T+(vc+b)*FS) if vc>=b else vc*vc*T
    Dstar=F(cfg['mark_contract']['D_star_full38_direct_exposure_upper']);K=q['K0']
    errors=sum(F(q[x]) for x in ['rho0','delta_exec','delta_svc','delta_E','delta_M','alpha_M'])
    init=K*B*ps/W;short=beta*ps*S2;long=beta*pl*V;risk=errors+Dstar+init+short+long
    rho=max(F(cfg['environment_contract']['rho_entry_upper_per_s']),F(cfg['environment_contract']['rho_ongoing_upper_per_s']))
    l=F(cfg['environment_contract']['l_per_s']);z=F(m['z']);phi=F(m['phi_rational_lower'])
    if vc>l:raise ValueError('This finite certificate intentionally covers the specified linear LOW branch only')
    lower=max(F(0),vc-rho*l*hp)
    low_margin=F(m['a_M'])*wm*phi*lower-z*k-H
    alpha=F(q['alpha_M']);joint=J*t58.exp_neg(H)[1]
    rational_joint=J*F(3,8)**int(H)
    safe=hm-2*wp-Gp-maxgap-fp-ps
    time_margin=safe-dp
    mu=wp*(F(m['A_M'])*b+F(m['eta_M_per_s']))
    x=max(F(0),k-mu)
    tail_exp=x*x/(2*(mu+x/3)) if x else F(0)
    p=t58.exp_neg(tail_exp)[1] if x else F(1)
    # Conservative declared exponential envelope, not the exact Poisson tail.
    dE=F(cfg['own_ERR']['max_delivery_s']);false=F(cfg['own_ERR']['false_flag_rate_upper_per_s'])
    strip=F(s['price_strip_physical_s'])
    strip_required=hi('hold_ticks')+2*wp+dp+ps+dE+2*Gp+maxgap+fp+4*gp
    cf=cp/gm;cs=cf/s['long_multiplier'];CM=F(r['extra_monitor_control_rate']);sigM=F(r['extra_monitor_control_sigma_s'])
    pq=min(F(1),errors-F(q['alpha_M'])+Dstar+K*b*ps/W+beta*pl*b*b*T)
    bad=F(m['recognized_bad_window_probability'])
    def quiet(horizon):
        Jh=t58.ceil(horizon/wm)
        terms=[strip*(1+K)/horizon,strip*(b+false),F(Jh)*strip/horizon*(p+bad),pq]
        return cs+cf*min(F(1),sum(terms))+2*cp/horizon+CM+sigM/horizon
    Tq=F(9,10)*T;Kq=1000
    ret_boundary=strip*(Kq+K+Kq*B*(pl+dE))/Tq
    ret=cs+cf*min(F(1),strip*(b+false)+ret_boundary+strip*(1/wm+2*F(Kq)/Tq)*(p+bad)+risk)+2*cp*Kq/Tq+CM+sigM*Kq/Tq
    peak=(t58.mask_bound(2*cp,2*gm,F(r['peak_window_s']))+sigM+CM*F(r['peak_window_s']))/F(r['peak_window_s'])
    request=F(r['application_max_request_s']);block=2*cp+request;rate=1-block/(2*gm)
    delay=block+(F(r['application_sigma_s'])+sigM)/rate if rate>0 else F(10**9)
    payload=dict(B=B,bbar=b,solar_peak=S,FS=FS,S2_formula_exact=s2,S2_declared_upper=S2,Vc=V,
        short_period_upper_s=ps,long_period_upper_s=pl,Wc_upper_s=W*cp,
        required_joint_U_WCET_physical_s=cm,nominal_90ns_U_clock_margin_s=cm-F('0.00000009'),
        risk_short_pairs=short,risk_long_low_pairs=long,risk_initial=init,risk_direct=Dstar,risk_quotas=errors,
        risk_upper=risk,risk_margin=eps-risk,known_T72_subtotal_if_two_missing_quotas_excluded=risk-F(q['delta_exec'])-F(q['alpha_M']),
        LOW_load_lower=lower,LOW_margin=low_margin,joint_exp_upper=joint,joint_rational_upper=rational_joint,
        alpha_margin=alpha-rational_joint,J=J,d_safe_lower_s=safe,time_margin_s=time_margin,
        strip_required_upper_s=strip_required,strip_margin_s=strip-strip_required,
        quiet_mu_upper=mu,tail_Bernstein_exponent=tail_exp,tail_probability_upper=p,p_q=pq,
        quiet_mission_upper=quiet(T),quiet_24h_prepared_upper=quiet(F(86400)),
        quiet_returns_upper=ret,quiet_return_boundary=ret_boundary,
        quiet_margin=F(r['quiet_tax_limit'])-quiet(T),peak_upper=peak,peak_margin=F(r['peak_limit'])-peak,
        FIFO_rate_lower=rate,FIFO_margin=rate-F(r['application_rate'])-CM,
        app_delay_upper_s=delay,app_delay_margin_s=F(r['application_delay_limit_s'])-delay,
        decision_lead_margin_s=lo('decision_lead_ticks')-request-F(s['gate_logic_wcet_s']),
        delivery_margin_s=F(m['delivery_computation_deadline_after_window_ticks'])*dt*xm-F(m['required_delivery_computation_physical_max_s']),
        Dstar_required_max_by_risk=eps-errors-init-short-long,
        unsigned64_time_max=t58.ceil(T/(dt*xm))+int(m['lease_end_from_window_start_ticks'])+int(s['hold_ticks']))
    passed=all(payload[k]>=0 for k in ['risk_margin','LOW_margin','alpha_margin','time_margin_s','strip_margin_s','quiet_margin','peak_margin','FIFO_margin','app_delay_margin_s','decision_lead_margin_s','delivery_margin_s'])
    payload['all_scalar_tests_pass']=passed
    payload['passes_also_24h_and_returns']=passed and quiet(F(86400))<=F(r['quiet_tax_limit']) and ret<=F(r['quiet_tax_limit'])
    # Strong constant: every period quantum, not just the two selected frames.
    fixed_errors=sum(F(q[x]) for x in ['rho0','delta_exec','delta_svc'])
    intercept=fixed_errors+Dstar
    slope=beta*s2+K*B/W
    interval=t58.integer_interval((slope,intercept,F(0)),eps,dt*xp,1,t58.floor(T/(dt*xp)))
    M=interval[1] if interval else 0
    if M:
        resource=t58.Resource(W=W//2,c=2*cp,H=T,h=F(r['peak_window_s']),tax=F(1),peak=F(r['peak_limit']),
            delay=F(r['application_delay_limit_s']),sigma=F(r['application_sigma_s']),u=F(r['application_rate']),g=request,tick=dt,clock_error=1-xm)
        rv=t58.resources(resource,M)
        E1M=t58.floor((eps-intercept)/((beta*S2+K*B/W)*dt*xp))
        # Direct D is externally added, since only its mean upper is supplied.
        p52=t58.Risk(T=T,B=B,b=b,FS=FS,q=F(1,W),Q=F(1),chi=2*beta,eta=2*beta/W,K0=K,rho0=F(q['rho0']),delta_exec=F(q['delta_exec'])+F(q['delta_svc']))
        checked=t58.components(p52,M*dt*xm,M*dt*xp)['total']+Dstar
        payload.update(fixed_strong_M=M,fixed_E1_M=E1M,fixed_period_upper_s=M*dt*xp,
            fixed_risk_upper=checked,fixed_risk_next_quantum=intercept+(M+1)*dt*xp*slope,
            fixed_cost_lower=F(W*s['c_ticks'],M)-2*cp/T,
            fixed_cost_upper=F(W*s['c_ticks'],M)+2*cp/T,
            fixed_peak_upper=rv['peak_upper'],fixed_delay_upper_s=rv['delay_upper'] or F(10**9),
            fixed_resource_ok=t58.resource_ok(rv))
    # Published candidate and E3 are separate checks from the stronger search.
    A=env['fixed_candidate_frame_ticks'];tau=F(W,2)*A*dt*xp
    J0=24540;L=F(115776);tmin=W*cm/(F('.01')+2*cp/T)
    ell=(L-J0*cp)/(4*J0);N=2*W*J0;xcell=B*ell/W
    plo=F(n-1,2*n)*xcell*xcell*t58.exp_neg(xcell)[0]
    lower=t58.poisson_event(N*plo)[0]-F(q['delta_exec'])
    reused=t58.class_lower(W,n,B,L,cp,cm,T,F('.01'),delta_exec=F(q['delta_exec']),witness_admissible=True,deterministic_window_contract=True)
    # E2's 2c/T edge is for the balanced paired calendar. For genuinely
    # arbitrary per-word phases, two partial blocks per word give the safe
    # 2Wc/T edge. Recheck E3 with that weaker necessary condition as well.
    tmin_any=W*cm/(F('.01')+2*W*cp/T)
    payload.update(fixed_published_risk=intercept+tau*(beta*S2+K*B/W),fixed_published_cost_lower=F(2*s['c_ticks'],A)-2*cp/T,
        E3_tau_min_s=tmin,E3_J_required=t58.floor(L/tmin)+2,E3_J0_valid=J0>=t58.floor(L/tmin)+2,
        E3_arbitrary_phase_tau_min_s=tmin_any,E3_arbitrary_phase_J_required=t58.floor(L/tmin_any)+2,
        E3_arbitrary_phase_J0_valid=J0>=t58.floor(L/tmin_any)+2,
        E3_ell_s=ell,E3_cells=N,E3_exponent_lower=N*plo,E3_risk_lower=lower,T58_class_risk_lower=reused['lower'])
    return payload


def write_results(out):
    out.mkdir(parents=True,exist_ok=True)
    rows=[];summaries=[];inputs=[]
    for name,cfg,status in variants():
        for env in cfg['environments']:
            v=calculate(cfg,env)
            for key,value in v.items():
                if isinstance(value,bool):a=b=str(value)
                else:a,b=bounds(value)
                rows.append({'set':name,'shield_g_cm2':env['shield_g_cm2'],'metric':key,'lower':a,'upper':b,
                             'arithmetic':'exact rational / T58 certified exponential; outward decimal display',
                             'theory_sha':THEORY_SHA})
            summaries.append({'set':name,'shield_g_cm2':env['shield_g_cm2'],'all_scalar_tests_pass':v['all_scalar_tests_pass'],
                              'passes_also_24h_and_returns':v['passes_also_24h_and_returns'],
                              **{k:bounds(v[k])[0 if k.endswith('_lower') else 1] for k in ['risk_upper','quiet_mission_upper','quiet_24h_prepared_upper','quiet_returns_upper','peak_upper','app_delay_upper_s','fixed_cost_lower']}})
        inputs.append({'set':name,'status':status,'input':cfg})
    def csvout(path,data):
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    csvout(out/'t73_directed_bounds.csv',rows);csvout(out/'t73_summary.csv',summaries)
    (out/'t73_checked_inputs.json').write_text(json.dumps({'theory_sha':THEORY_SHA,'variants':inputs},ensure_ascii=False,indent=2)+'\n')
    return summaries


if __name__=='__main__':
    print(json.dumps(write_results(HERE/'outputs'),indent=2))
