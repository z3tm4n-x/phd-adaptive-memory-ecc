#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
from semantic_model import WordState, PassState, Command, CommandEndpoint, Op, WordBoundaryArbiter

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'config.json').read_text())
OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True)

def require(x,msg):
    if not x: raise AssertionError(msg)

def principal():
    W=4*1024*1024*8//32
    n=39; H=CFG['temporal_shape']['hours']; eps=0.001
    er=CFG['error_rate_per_physical_bit_day']
    mu=W*n*er/24
    sh=CFG['temporal_shape']
    vmax=mu*sh['max_old_per_hour']/sh['mean_old_per_hour']
    v0=mu*sh['nu0_old_per_hour']/sh['mean_old_per_hour']
    A=H*mu
    tr=CFG['service_profiles']['4']['read_s']; tw=CFG['service_profiles']['4']['write_s']
    coeff=(n-1)/(2*n*W)
    hat_sum_lower=A+v0-vmax
    ratio=sh['lag1_eta']*A*A/hat_sum_lower
    rmw=A*vmax*max(tr,tw)/(3600*W)
    C=(CFG['causal_risk_margin']*eps-rmw)/(coeff*ratio)
    hat_sum_upper=A+v0
    ravg=(hat_sum_upper/H)/C
    rpeak=vmax/C
    grab=tr+tw
    app_word=max(tr,tw)
    service=W*grab
    avg=ravg*service/3600
    peak=rpeak*service/3600
    return locals()

def semantic_transition_checks():
    checks=[]
    w=WordState(); require(w.read_and_decode(0.0)=='clean','clean decode'); require(not w.correction_pending,'clean scheduled write')
    require(not w.complete_conditional_write(1.0),'clean write happened'); checks.append('clean_no_write')

    w=WordState(); require(w.read_and_decode(0.0)=='clean','post-read clean decode'); w.inject_toggle(3,0.5)
    require(not w.complete_conditional_write(1.0),'post-read clean unexpectedly wrote'); require(w.errors=={3},'post-read clean upset lost'); checks.append('post_read_error_persists_without_write')

    w=WordState(); w.inject_toggle(5,0.0); require(w.read_and_decode(1.0)=='correctable','single not correctable'); require(w.errors=={5},'read mutated physical word')
    require(w.complete_conditional_write(2.0),'conditional write missing'); require(w.errors==set(),'single not cleared'); checks.append('single_corrected_on_write')

    w=WordState(); w.inject_toggle(1,0.0); require(w.read_and_decode(1.0)=='correctable','rmw initial'); w.inject_toggle(2,1.5)
    require(w.first_cap_time==1.5,'E_cap not triggered by second distinct error'); require(w.complete_conditional_write(2.0),'rmw write absent'); require(w.errors==set(),'pending image did not write'); require(w.first_cap_time==1.5,'first passage erased'); checks.append('rmw_second_error_first_passage')

    w=WordState(); w.inject_toggle(7,0.0); w.read_and_decode(0.5); w.inject_toggle(7,0.75); require(w.first_cap_time is None,'same-bit toggle false E_cap'); checks.append('same_bit_toggle_not_false_cap')

    p=PassState(3); p.commit_word(False); p.commit_word(False); require(not p.completed and p.snapshot_count is None,'partial pass snapshot'); p.commit_word(True)
    require(p.completed and p.snapshot_count==1,'last correction missing from snapshot'); checks.append('last_word_snapshot')
    p2=PassState(3); p2.commit_word(True); require(not p2.completed and p2.snapshot_count is None,'partial pass treated complete'); checks.append('partial_pass_not_complete')

    ep=CommandEndpoint(fallback_period=1.0,deadline=9.0)
    require(ep.choose(Command(8.999,5.0))==('command',5.0),'on-time command rejected'); require(ep.choose(Command(9.001,5.0))==('fallback',1.0),'late command accepted'); checks.append('deadline_fallback_transition')

    arb=WordBoundaryArbiter(app_word_s=80e-9,scrub_grab_s=140e-9)
    app=Op('app',0.0,80e-9); scrub=arb.dispatch_scrub(40e-9,app)
    require(scrub.start==app.end and scrub.start>=app.end,'arbiter overlap'); checks.append('app_conflict_resolved_at_word_boundary')
    return checks

def schedule_checks(c):
    checks=[]
    arb=WordBoundaryArbiter(c['app_word'],c['grab'])
    release_spacing=3600.0/(c['W']*c['rpeak'])
    rho_scrub=c['grab']/release_spacing
    require(abs(rho_scrub-c['peak'])<1e-14,'release schedule resource mismatch')
    require(release_spacing>c['grab']+c['app_word'],'scrub releases can bunch after one app-word block')

    max_late=0.0; prev_end=-math.inf
    trace=[]
    for k in range(16):
        due=k*release_spacing
        app=Op('app', max(0.0,due-1e-12), c['app_word'])
        scrub=arb.dispatch_scrub(due,app)
        late=scrub.start-due; max_late=max(max_late,late)
        require(late<=c['app_word']+1e-18,'scrub delayed beyond one app word')
        require(scrub.start>=prev_end-1e-18,'scrub jobs overlap/bunch')
        prev_end=scrub.end
        trace.append({'k':k,'due_s':due,'start_s':scrub.start,'lateness_s':late,'end_s':scrub.end})
    checks.append('word_boundary_schedule_no_bunching')

    phase_inflation=1.0+c['rpeak']*c['app_word']/3600.0
    pair_nominal=0.00095-c['rmw']
    risk_with_phase_lateness=pair_nominal*phase_inflation+c['rmw']
    require(risk_with_phase_lateness<c['eps'],'actual word-boundary schedule breaks risk certificate')
    checks.append('risk_schedule_phase_lateness_paid')

    sigma_app=CFG['application_burst_words']*c['app_word']
    rho_app=0.50
    require(rho_app < 1-rho_scrub,'unstable application envelope')
    service_curve_delay=(sigma_app+c['grab'])/(1-rho_scrub)
    busy_period_bound=(sigma_app+c['grab'])/(1-rho_app-rho_scrub)
    require(busy_period_bound*1e6 < CFG['application_deadline_us'],'busy-period delay fails')
    require(service_curve_delay<=busy_period_bound,'tight delay exceeds conservative bound')
    checks.append('executor_delay_from_release_envelope')

    for T in [release_spacing,2*release_spacing,1e-6,10e-6,1e-3,1.0]:
        exact_discrete=(math.floor(T/release_spacing)+1)*c['grab']
        envelope=c['grab']+rho_scrub*T
        require(exact_discrete<=envelope+1e-18,'release envelope arithmetic')
    checks.append('release_envelope_spot_checks')

    return checks, {
        'release_spacing_s_at_peak':release_spacing,
        'scrub_grab_s':c['grab'],
        'app_word_max_s':c['app_word'],
        'max_scrub_lateness_s':max_late,
        'rho_scrub_peak':rho_scrub,
        'phase_integral_inflation_max':phase_inflation,
        'risk_upper_with_word_boundary_lateness':risk_with_phase_lateness,
        'application_sigma_service_s':sigma_app,
        'application_rho':rho_app,
        'leftover_service_rate':1-rho_scrub,
        'service_curve_delay_us':service_curve_delay*1e6,
        'busy_period_delay_us':busy_period_bound*1e6,
        'trace':trace,
    }

def budget_and_information(c):
    H=c['H']; B=0.0025; missing=148
    nominal=c['avg']
    fallback=nominal+missing/H*c['peak']
    cold_plus_missing=nominal+(missing+1)/H*c['peak']
    upper=0.0039503977189538015
    out={
      'nominal_warm_start':{'lower_fraction':nominal,'upper_fixed_separator_fraction':upper,'control_cost_reserve_at_0p25':B-nominal},
      'fallback_148h_warm_start':{'lower_fraction':fallback,'upper_fixed_separator_fraction':upper,'control_cost_reserve_at_0p25':B-fallback},
      'cold_start_plus_148h_fallback':{'lower_fraction':cold_plus_missing,'upper_fixed_separator_fraction':upper,'control_cost_reserve_at_0p25':B-cold_plus_missing},
      'information_contract':{
        'offline_design_constants':['error_rate_per_physical_bit_day','mean_old_per_hour','max_old_per_hour','lag1_eta','C'],
        'runtime_hour_h_ge_1':'only completed previous-hour scalar rate estimate, assuming it is delivered by the next decision boundary',
        'first_hour_warm_start':'requires a valid completed pre-t0 hour scalar; this is an explicit warm-start assumption',
        'first_hour_cold_start':'if no pre-t0 scalar exists, use calibrated peak-rate fallback for one hour',
        'missing_hour':'use calibrated peak-rate fallback',
        'not_established':['positive operational delivery-latency margin','future rate <= retrospective calibrated maximum','held-out transfer of mean/max/lag1_eta/C'],
        'claim_scope':'causal execution conditional on retrospectively calibrated/transferred design constants; not an independently validated prospective calibration'
      }
    }
    require(fallback<B and cold_plus_missing<B,'fallback scenario exceeds 0.25%')
    require(nominal<fallback<cold_plus_missing<upper,'budget domain ordering')
    return out

def main():
    c=principal()
    sem=semantic_transition_checks()
    sch,schout=schedule_checks(c)
    bud=budget_and_information(c)
    result={'passed':True,'semantic_checks':sem,'schedule_checks':sch,'semantic_check_count':len(sem),'schedule_check_count':len(sch),'executor':schout,'budget_domains':bud}
    (OUT/'repair_verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (OUT/'executor_schedule.json').write_text(json.dumps(schout,indent=2,sort_keys=True)+'\n')
    (OUT/'budget_domains.json').write_text(json.dumps(bud,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=='__main__': main()
