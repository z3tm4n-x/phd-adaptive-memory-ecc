#!/usr/bin/env python3
"""Post-result formula audit for RE-FIXED-ADAPTIVE-FEASIBILITY-01.

Deliberately does not import analyze.py.  It recomputes the principal witness,
continuous Fixed exclusion, RMW stress, missing-input fallback, hour slice and
stronger-ECC check from config constants and compares the executed pre-verification
source bytes with their published Git blob identities.
"""
from __future__ import annotations
import hashlib, json, math, platform, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
CFG = json.loads((ROOT / "config.json").read_text())

EXPECTED_GIT_BLOBS = {
    "ANALYSIS_CONTRACT.md": "d99a2eb5abd1556540ab39e5b914d0db35134384",
    "config.json": "e532df57cc298fbc961ab2ecbee20ac6e98a3dca",
    "analyze.py": "f6b9ce3907c9fa41d550b58d367a2bf6864d3a8e",
    "verify.py": "f8a43cde9e6a2bbdd905d0741f68e4675a909044",
}

def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

def F(e: float) -> float:
    return 1.0 - math.exp(-e)

def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)

def principal_constants():
    mib=4; eps=0.001; B=0.0025; app=0.5
    n=39; d=(n-1)/n; W=int(mib*1024*1024*8/32)
    H=CFG['temporal_shape']['hours']
    mu=W*n*CFG['error_rate_per_physical_bit_day']/24
    sh=CFG['temporal_shape']
    vmax=mu*sh['max_old_per_hour']/sh['mean_old_per_hour']
    v0=mu*sh['nu0_old_per_hour']/sh['mean_old_per_hour']
    A=H*mu
    s2=H*mu*mu*(1+sh['cv2_old'])
    tr=CFG['service_profiles'][str(mib)]['read_s']; tw=CFG['service_profiles'][str(mib)]['write_s']
    return locals()

def exactly_two_lb(c, tau_s: float) -> float:
    th=tau_s/3600.0
    a=c['vmax']/c['W']
    e=c['d']/2*math.exp(-a*th)*c['s2']/c['W']*max(0.0, th-2*th*th)
    return F(e)

def cauchy_lb_continuous(c, tau_s: float) -> float:
    # Upper-bound the number M of word/inter-check exposure intervals by
    # W*(H/tau_h + 2). Cauchy then lower-bounds sum lambda_j^2 by A^2/M.
    th=tau_s/3600.0
    a=c['vmax']/c['W']
    M_upper=c['W']*(c['H']/th + 2.0)
    e=c['d']/2*math.exp(-a*th)*c['A']*c['A']/M_upper
    return F(e)

def root_bisect(fun, target, lo, hi, it=160):
    for _ in range(it):
        m=(lo+hi)/2
        if fun(m)<=target: lo=m
        else: hi=m
    return lo

def main():
    c=principal_constants()
    checks=[]
    blobs={name:git_blob(ROOT/name) for name in EXPECTED_GIT_BLOBS}
    for name,sha in EXPECTED_GIT_BLOBS.items():
        assert_true(blobs[name]==sha, f"pre-verification blob mismatch: {name}")
        checks.append(f"git_blob:{name}")

    # Fixed continuous class.
    tau_resource=c['W']*c['tr']/c['B']
    fixed_at_resource=exactly_two_lb(c,tau_resource)
    fixed_at_900=exactly_two_lb(c,900.0)
    long_at_900=cauchy_lb_continuous(c,900.0)
    long_at_3600=cauchy_lb_continuous(c,3600.0)
    assert_true(fixed_at_resource>c['eps'] and fixed_at_900>c['eps'], "short-period endpoints do not exclude Fixed")
    # f(x)=exp(-a x)(x-2x^2). Derivative numerator is 2a x^2-(4+a)x+1.
    a=c['vmax']/c['W']
    disc=(4+a)**2-8*a
    roots=sorted(((4+a-math.sqrt(disc))/(4*a),(4+a+math.sqrt(disc))/(4*a))) if a>0 else [0.25,math.inf]
    x0=tau_resource/3600.0; x1=0.25
    critical=[r for r in roots if x0<r<x1]
    # Any interior critical point in this interval is a maximum: derivative is positive at x0.
    deriv_x0=1-4*x0-a*(x0-2*x0*x0)
    assert_true(deriv_x0>0 and len(critical)<=1, "unexpected shape of exactly-two lower bound")
    checks.append("fixed_short_continuous_unimodal")
    # g(x)=x exp(-a x)/(H+2x), derivative of log g is 1/x-a-2/(H+2x), positive through x in [.25,1].
    min_log_derivative=1.0-a-2.0/(c['H']+2.0)
    assert_true(min_log_derivative>0 and long_at_900>c['eps'] and long_at_3600>long_at_900, "long-period lower bound not monotone/excluding")
    checks.append("fixed_long_continuous_monotone")

    risk_root=root_bisect(lambda t: exactly_two_lb(c,t),c['eps'],1e-8,900.0)
    fixed_read_boundary=c['W']*c['tr']/risk_root
    assert_true(fixed_read_boundary>c['B'], "Fixed read boundary does not exceed principal budget")
    checks.append("fixed_resource_risk_separator")

    # Every Level-I witness emitted by the frozen analysis must also survive the
    # post-result continuous-tau audit; this prevents the 900 s search cap from
    # being mistaken for a proof beyond its range.
    frozen_summary=json.loads((OUT/'summary.json').read_text())
    witness_pairs=sorted({(int(r['memory_mib']),float(r['epsilon'])) for r in frozen_summary['witnesses']})
    continuous_witness_audit=[]
    for m,e in witness_pairs:
        Wm=int(m*1024*1024*8/32); mum=Wm*39*CFG['error_rate_per_physical_bit_day']/24
        vm=mum*CFG['temporal_shape']['max_old_per_hour']/CFG['temporal_shape']['mean_old_per_hour']
        s2m=CFG['temporal_shape']['hours']*mum*mum*(1+CFG['temporal_shape']['cv2_old']); Am=CFG['temporal_shape']['hours']*mum; am=vm/Wm
        def qvs(t):
            x=t/3600.0; ee=(38/39)/2*math.exp(-am*x)*s2m/Wm*max(0.0,x-2*x*x) if t<1800 else 0.0
            return F(ee)
        def qms(t):
            x=t/3600.0; M=Wm*(CFG['temporal_shape']['hours']/x+2.0); ee=(38/39)/2*math.exp(-am*x)*Am*Am/M
            return F(ee)
        assert_true(qvs(900)>e, f'witness {m}MiB eps={e}: short bound does not cover 900 s')
        l,h=900.0,1800.0
        if qvs(l)<=qms(l): cross=l
        else:
            for _ in range(140):
                md=(l+h)/2
                if qvs(md)>qms(md): l=md
                else: h=md
            cross=(l+h)/2
        postmin=max(qvs(cross),qms(cross))
        assert_true(postmin>e, f'witness {m}MiB eps={e}: continuous post-900 gap')
        continuous_witness_audit.append({'memory_mib':m,'epsilon':e,'post900_crossover_s':cross,'post900_min_lower_bound':postmin})
    checks.append('all_frozen_witness_pairs_continuous_tau')

    # Causal bound, independently from analyze.py.
    hat_sum_lower=c['A']+c['v0']-c['vmax']
    ratio_ub=CFG['temporal_shape']['lag1_eta']*c['A']*c['A']/hat_sum_lower
    coeff=c['d']/(2*c['W'])
    delta=c['A']*c['vmax']*max(c['tr'],c['tw'])/(3600*c['W'])
    pair_budget=CFG['causal_risk_margin']*c['eps']-delta
    C=pair_budget/(coeff*ratio_ub)
    pair=coeff*C*ratio_ub
    risk=pair+delta
    risk_4x=pair+4*delta
    hat_sum_upper=c['A']+c['v0']
    ravg=(hat_sum_upper/c['H'])/C
    rpeak=c['vmax']/C
    service=c['W']*(c['tr']+c['tw'])
    avg=ravg*service/3600
    peak=rpeak*service/3600
    assert_true(risk<=c['eps'] and risk_4x<c['eps'] and avg<c['B'] and peak<=CFG['peak_scrub_budget'], "causal principal contract failed")
    checks.append("causal_bound_and_4x_rmw")

    numerator=CFG['application_burst_words']*max(c['tr'],c['tw'])+(c['tr']+c['tw'])
    delay50=numerator/(1-0.5-peak)*1e6
    app_load_max=1-peak-numerator/(CFG['application_deadline_us']*1e-6)
    assert_true(delay50<=CFG['application_deadline_us'] and app_load_max>0.5, "application delay contract failed")
    checks.append("application_delay")

    missing_h=148
    fallback_avg=avg + missing_h/c['H']*(peak-avg)
    fallback_capacity_h=(c['B']-avg)/(peak-avg)*c['H']
    assert_true(fallback_avg<c['B'] and fallback_capacity_h>missing_h, "fallback budget failed")
    checks.append("missing_input_fallback")

    # Peak-hour Fixed slice.
    def hour_lb(tau_s):
        m=max(0,math.floor(3600/tau_s)-1)
        lam=c['vmax']/c['W']*(tau_s/3600)
        q=c['W']*m*c['d']/2*math.exp(-lam)*lam*lam
        return F(q)
    hour_root=root_bisect(hour_lb,c['eps'],1e-8,900.0)
    hour_read=c['W']*c['tr']/hour_root
    assert_true(hour_read<0.001, "hour slice unexpectedly needs >=0.1%")
    checks.append("hour_slice")

    # Stronger ECC architecture variant (t=2, 44-bit shortened BCH candidate).
    n2=44
    mu2=c['W']*n2*CFG['error_rate_per_physical_bit_day']/24
    vmax2=mu2*CFG['temporal_shape']['max_old_per_hour']/CFG['temporal_shape']['mean_old_per_hour']
    s2_2=c['H']*mu2*mu2*(1+CFG['temporal_shape']['cv2_old'])
    s3ub=vmax2*s2_2
    tau2=c['W']*(c['tr']+c['tw'])/c['B']
    th2=tau2/3600
    distinct3=(n2-1)*(n2-2)/(n2*n2)
    E3=distinct3/6*(th2*th2)/(c['W']*c['W'])*s3ub
    assert_true(E3<c['eps'], "stronger-ECC analytic upper failed")
    checks.append("stronger_ecc")

    out={
        "passed": True,
        "check_count": len(checks),
        "checks": checks,
        "preverification_blob_ids": blobs,
        "continuous_witness_audit": continuous_witness_audit,
        "principal": {
            "tau_resource_min_s": tau_resource,
            "fixed_exactly_two_lower_at_resource_tau": fixed_at_resource,
            "fixed_exactly_two_lower_at_900s": fixed_at_900,
            "fixed_cauchy_lower_at_900s": long_at_900,
            "fixed_cauchy_lower_at_3600s": long_at_3600,
            "fixed_risk_root_s": risk_root,
            "fixed_read_boundary_fraction": fixed_read_boundary,
            "causal_C": C,
            "causal_pair_upper": pair,
            "rmw_delta": delta,
            "causal_risk_upper": risk,
            "causal_risk_upper_4x_rmw": risk_4x,
            "causal_average_fraction": avg,
            "causal_peak_fraction": peak,
            "delay_bound_50pct_us": delay50,
            "max_application_load_for_100us": app_load_max,
            "fallback_148h_average_fraction": fallback_avg,
            "fallback_capacity_hours": fallback_capacity_h,
            "hour_fixed_risk_root_s": hour_root,
            "hour_fixed_read_boundary_fraction": hour_read,
            "stronger_ecc_tau_s": tau2,
            "stronger_ecc_triple_upper": E3,
        },
        "python": platform.python_version(),
    }
    OUT.mkdir(exist_ok=True)
    (OUT/'independent_check.json').write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))

if __name__ == '__main__':
    main()
