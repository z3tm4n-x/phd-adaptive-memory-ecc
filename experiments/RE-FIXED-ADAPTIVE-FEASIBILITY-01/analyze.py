#!/usr/bin/env python3
import csv, json, math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'config.json').read_text())
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)

def W_for(mib): return int(mib*1024*1024*8/32)
def F_from_E(e): return 1-math.exp(-max(0.0,e))
def root_bisect(fun,target,lo,hi,it=100):
    for _ in range(it):
        m=(lo+hi)/2
        if fun(m)<=target: lo=m
        else: hi=m
    return lo

def metrics(mib,eps,budget,app):
    n=CFG['ecc']['word_bits']; d=(n-1)/n; W=W_for(mib)
    sh=CFG['temporal_shape']; H=sh['hours']
    mu=W*n*CFG['error_rate_per_physical_bit_day']/24
    scale=mu/sh['mean_old_per_hour']; vmax=scale*sh['max_old_per_hour']; v0=scale*sh['nu0_old_per_hour']
    s2=H*mu*mu*(1+sh['cv2_old']); A=H*mu
    def fixed_lb(tau_s):
        th=tau_s/3600
        lammax=vmax/W*min(th,1.0)
        if tau_s < 1800:
            qv=d/2*math.exp(-lammax)*s2/W*max(0.0,th-2*th*th)
        else: qv=0.0
        M=W*(math.ceil(H*3600/tau_s)+1)
        qm=d/2*math.exp(-vmax/W*min(tau_s/3600,1.0))*A*A/M
        return max(F_from_E(qv),F_from_E(qm))
    tau_root=root_bisect(fixed_lb,eps,1e-6,min(900.0,CFG['fixed_period_max_s']))
    prof=CFG['service_profiles'][str(mib)]; tr=prof['read_s']; tw=prof['write_s']
    fixed_read_min=tr*W/tau_root
    hat_sum_lower=A+v0-vmax
    ratio_int_ub=sh['lag1_eta']*A*A/hat_sum_lower
    coeff=d/(2*W)
    delta=A*vmax*max(tr,tw)/(3600*W)
    pair_budget=max(0.0,CFG['causal_risk_margin']*eps-delta)
    C=pair_budget/(coeff*ratio_int_ub)
    hat_sum_upper=A+v0
    ravg=(hat_sum_upper/H)/C
    rpeak=vmax/C
    pass_service=W*(tr+tw)
    causal_avg=ravg*pass_service/3600
    causal_peak=rpeak*pass_service/3600
    causal_risk=coeff*C*ratio_int_ub+delta
    grab=tr+tw; app_word=max(tr,tw)
    denom=1-app-causal_peak
    delay_us=math.inf if denom<=0 else (CFG['application_burst_words']*app_word+grab)/denom*1e6
    causal_ok=(causal_risk<=eps and causal_avg<=budget and causal_peak<=CFG['peak_scrub_budget'] and denom>0 and delay_us<=CFG['application_deadline_us'])
    fixed_impossible=(budget<fixed_read_min)
    return dict(memory_mib=mib,epsilon=eps,budget=budget,application_load=app,W=W,mean_rate_h=mu,max_rate_h=vmax,
                fixed_tau_safe_upper_s=tau_root,fixed_required_read_fraction_lb=fixed_read_min,
                causal_C=C,causal_risk_upper=causal_risk,causal_avg_fraction_worst_rw=causal_avg,
                causal_peak_fraction_worst_rw=causal_peak,app_delay_bound_us=delay_us,
                fixed_proven_impossible=fixed_impossible,causal_full_contract=causal_ok,
                level1_witness=bool(fixed_impossible and causal_ok))

def hour_peak(mib,eps,budget):
    n=CFG['ecc']['word_bits']; d=(n-1)/n; W=W_for(mib); sh=CFG['temporal_shape']
    mu=W*n*CFG['error_rate_per_physical_bit_day']/24; v=mu*sh['max_old_per_hour']/sh['mean_old_per_hour']
    prof=CFG['service_profiles'][str(mib)]; tr=prof['read_s']
    def lb(tau):
        m=max(0,math.floor(3600/tau)-1); lam=v/W*(tau/3600); q=W*m*d/2*math.exp(-lam)*lam*lam
        return F_from_E(q)
    root=root_bisect(lb,eps,1e-6,900)
    return {'memory_mib':mib,'epsilon':eps,'budget':budget,'peak_hour_fixed_tau_safe_upper_s':root,'peak_hour_fixed_read_fraction_lb':tr*W/root}

def stronger_ecc(mib,eps,budget,app):
    W=W_for(mib); sh=CFG['temporal_shape']; n=CFG['ecc']['stronger_word_bits']
    prof=CFG['service_profiles'][str(mib)]; tr=prof['read_s']; tw=prof['write_s']; H=sh['hours']
    mu=W*n*CFG['error_rate_per_physical_bit_day']/24; vmax=mu*sh['max_old_per_hour']/sh['mean_old_per_hour']
    s2=H*mu*mu*(1+sh['cv2_old']); s3ub=vmax*s2
    tau=W*(tr+tw)/budget
    th=tau/3600
    distinct3=(n-1)*(n-2)/(n*n)
    E3=distinct3/6*(th*th)/(W*W)*s3ub
    peak=budget; denom=1-app-peak
    delay=math.inf if denom<=0 else (CFG['application_burst_words']*max(tr,tw)+(tr+tw))/denom*1e6
    return {'memory_mib':mib,'epsilon':eps,'budget':budget,'application_load':app,'tau_s':tau,'risk_upper_triples':E3,
            'avg_fraction_worst_rw':budget,'peak_fraction':peak,'delay_bound_us':delay,
            'full_contract':E3<=eps and peak<=CFG['peak_scrub_budget'] and denom>0 and delay<=CFG['application_deadline_us'],
            'architecture_status':'ANALYTIC_VARIANT_NOT_DROP_IN'}

def main():
    rows=[]
    for m in CFG['memory_mib']:
      for e in CFG['epsilons']:
       for b in CFG['average_service_budgets']:
        for a in CFG['application_loads']: rows.append(metrics(m,e,b,a))
    fields=list(rows[0]);
    with (OUT/'level1_map.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    witnesses=[r for r in rows if r['level1_witness'] and r['memory_mib'] in CFG['primary_documented_memory_mib']]
    gate=bool(witnesses)
    hrs=[hour_peak(r['memory_mib'],r['epsilon'],r['budget']) for r in witnesses]
    (OUT/'hour_slice.json').write_text(json.dumps(hrs,indent=2))
    strong=[stronger_ecc(r['memory_mib'],r['epsilon'],r['budget'],r['application_load']) for r in witnesses]
    (OUT/'stronger_ecc.json').write_text(json.dumps(strong,indent=2))
    summary={'level1_gate_open':gate,'witness_count':len(witnesses),'witnesses':witnesses,
             'level2_rule':'If gate opens, external lag-1 witness is the first established feedback method. Precomputed exact-future schedules are inadmissible leakage; counter-only and RES-003 require separate compatible stochastic transfer and are dispositioned, not credited by old runs.',
             'level3_res004_executed':False}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
