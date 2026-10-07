"""One read-only repeat command. --write only creates NEW T114 result files."""
import argparse
import csv
import gzip
import hashlib
import json
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from pathlib import Path
import subprocess
import sys
import unittest

import calculate as c
from intervals import I, primitive, exposure


def addresses():
    keys=['record_id','satellite','direction','target_level_s_inv','repeat_rise_elapsed_s',
          'T113_approach_expected_inversions','H_value','H_from_response_s_inv','H_to_response_s_inv',
          'H_from_utc','H_to_utc','H_from_sha256','H_to_sha256']
    rows=[]
    with gzip.open(c.ROOT/'experiments/t113-onset-growth/outputs/crossings.csv.gz','rt') as f:
        for r in csv.DictReader(f):
            if r['record_id'] in ('944','9963') and r['response']=='main_loglog' and r['mask']=='screened':
                row={k:r[k] for k in keys};mass=F(r['T113_approach_expected_inversions'])
                phi=F(1)-F(1,524288)
                z=(I(0)-I(phi*mass)).exp()
                row.update(available_by='upcross bin START plus tau; not at the nominal crossing itself',
                    probability_no_interval_ERR_and_no_global_break_upper=F(z.hi),
                    scope='conditional diagnostic singleton model at published data32 integrated exposure; NOT a full38 transfer',
                    current_controller_state='not identified by integrated count or post-peak label',
                    mass_lower_available_at_upcross_without_intrabin_bound=F(0))
                rows.append(row)
    assert len(rows)==2
    return rows


def constant(p,profile):
    old=c.old.constant(p);cl=c.calendar(p,profile,1,c.CFG['growth_classes'][0])
    res=c.resource(cl,old['resources']['frame_max'],old['resources']['frame_min'])
    Pm,Pp=old['period_lower'],old['period_upper'];T=c.T
    q=old['risk_upper'];W=p['W'];life=p['T']
    mission=W*T['R']/Pm+(T['E']-T['R'])*(p['F']/life*(1+F(1,W))+p['K0']/life+W*q/Pm)+F('1e-4')+F('209e-9')/life
    floor=W*T['r_lower']/Pp-2*W*T['R']/life
    return dict(period_ticks=old['M_ticks'],period_min=Pm,period_max=Pp,risk_upper=q,next_risk_upper=old['next_risk_upper'],
                resources=res,mission_price_lower=floor,mission_price_upper_intercept=mission,
                class_lower=c.old.lower_class(p),constant_certificate_not_an_optimum=True,
                feasible=old['risk_upper']<=p['eps'] and res['placement_slack']>=0 and res['rate_max_sigma1']>=0 and res['burst_max_latency']>=1)


def report():
    # Addressed candidates fixed in source, not a policy/tree/global optimization.
    selected={
      'singleton_read':[(7,7),(21,29),(23,41)],
      'singleton_write':[(5,5),(21,27),(23,39)],
      'MCU_calibrated_write':[(3,3),(19,25),(21,35)],
      'MCU2_write':[(1,1),(7,13),(11,19)],
      'MCU4_write':[(1,1),(1,1),(1,3)],
      'uncalibrated_write':[(1,1),(1,1),(1,1)]}
    main=c.old.environment(c.old.HANDOFF['rows'][0]);rows=[]
    for prof in c.CFG['profiles']:
        for idx,gr in enumerate(c.CFG['growth_classes']):
            if prof['name']=='uncalibrated_write' and idx:continue
            for stage in (2,1):
                k=selected[prof['name']][idx][0 if stage==2 else 1]
                r=c.compute(main,prof,gr,k,stage)
                preview_k=k
                while not r['certified'] and k>1:
                    r['candidate_role']='rejected_preview_not_a_certificate';rows.append(r)
                    k-=2;r=c.compute(main,prof,gr,k,stage)
                if not r['certified']:raise AssertionError('no fallback on main row')
                r['candidate_role']='presented'
                rows.append(r)
                # Preserve rejection of the next odd action in the declared local grid.
                nxt=c.compute(main,prof,gr,preview_k+2,stage);nxt['candidate_role']='next_odd_diagnostic';rows.append(nxt)
                print(prof['name'],gr['name'],stage,k,'Q<=',c.old.text_number(r['risk_upper']),
                    'C<=',c.old.text_number(100*r['price']['mission_upper_intercept']),
                    '% gain>=',c.old.text_number(r['gain_lower'],False,6),flush=True)
    secondary=c.old.environment(c.old.HANDOFF['rows'][1])
    for prof in c.CFG['profiles'][:2]:
        r=c.compute(secondary,prof,c.CFG['growth_classes'][0],1,2);r['candidate_role']='secondary_short_gate';rows.append(r)
    const={p['shield']:constant(p,c.CFG['profiles'][1]) for p in (main,secondary)}
    # Lower bound on this certificate family, NOT on physical failure.
    target=c.calendar(main,c.CFG['profiles'][1],33,c.CFG['growth_classes'][0]);q=F('.05')
    mx=exposure(q,target['tau']+target['lag'],F(1000),F('.048'))
    rlo=F((I(0)-I(target['phi'])*I(mx.hi)).exp().lo)
    optimistic=main['errors']+main['D']+target['Pl']*q*q*rlo*main['FS']/(2*main['W']*(q-main['b']))
    barrier=dict(ka=33,Pl=target['Pl'],q=q,old_lag=target['tau']+target['lag'],
        maximum_past_mass_upper=F(mx.hi),LOW_factor_lower=rlo,
        any_affine_certificate_lower_even_Ps_zero=optimistic,
        scope='lower of the whole old-history certificate family at this long period, all h/w; NOT lower failure probability',
        target_price_if_risk_passed=c.price(main,target,c.CFG['profiles'][1],main['eps'],2))
    return dict(task=114,base_sha=c.CFG['base_sha'],numbers='exact fractions; rounded human tables are outward',
                rows=rows,constant_E=const,T113_addressed=addresses(),certificate_barrier=barrier,
                verdict='conditional proof; main-rho tenfold and quiet-one-percent NOT established; no physical qualification',
                full_application_price='add Rupper*rate_w to protection tax; add Awrite*rate_w+Aread*rate_r to all-bus intercept',
                unknowns=c.CFG['unknowns'],accepted_files_changed=False)


def regression(r):
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    p=c.old.environment(c.old.HANDOFF['rows'][0]);pr=c.CFG['profiles'][1];gr=c.CFG['growth_classes'][0]
    cl=c.calendar(p,pr,5,gr)
    check('application_read_then_merged_write_not_free',cl['app']==F('217.002160e-9') and cl['app']>c.T['app'])
    check('old_192_tail_cannot_fit_full_observed_write',8*(192-164)*c.TM < F('1.1')*cl['app'])
    check('new_196_tail_has_positive_margins',min(c.resource(cl)[k] for k in ['app_margin_slack','placement_slack','gate_slack'])>0)
    check('passes_are_calendar_not_busy_sums',cl['Ps']>p['W']*c.T['E'])
    check('per_word_phase_and_mandatory_order',all((pow(5,-1,p['W'])*(5*j))%p['W']==j%p['W'] for j in [0,1,7,100,p['W']-1]))
    bands=c.bands(cl)
    check('old_bands_disjoint',all(bands[i][1]==bands[i+1][0] for i in range(len(bands)-1)))
    check('band_delays_force_confirmation',all(b-a+cl['tau']<=cl['w'] for a,b,n in bands if n))
    check('old_tokens_precede_pair_witness',cl['tau']>=cl['Pl']>=cl['Ps'])
    check('no_infinite_numeric_refinement',c.CFG['numerical_contract']['refinements']==8)
    z=dict(cl,phi=F(0));rr,_=c.low_upper(F('.1'),F('.048'),z)
    check('zero_information_is_no_discount',rr==1)
    priced=c.price(p,cl,pr,F('.001'),2)
    check('intra_E_repeated_parent_not_free',priced['aperture_extra_flag_rate_upper']==p['F']/(p['W']*p['T']) and priced['aperture_extra_fast_fraction']>0)
    check('overlapping_voids_are_not_independent',(I(-1).exp()).lo>(I(-2).exp()).hi)
    # Independent Decimal-100 primitive and products at boundaries and active cells.
    def dec(x):return D(x.numerator)/D(x.denominator)
    def prim(q,t,rho):
        ell=D('.001')
        if q<=ell:
            u=min(t,q/(rho*ell));return q*u-rho*ell*u*u/2
        te=(q/ell).ln()/rho;v=min(t,te);z=max(D(0),min(t-te,1/rho))
        return q/rho*(1-(-rho*v).exp())+ell*(z-rho*z*z/2)
    with localcontext() as ctx:
        ctx.prec=100
        for rho in [F('.048'),F(1,60),F(1,180)]:
            for q in [F(0),p['b'],F('.001'),F('.01'),p['B']]:
                for t in [F(0),F('.5'),F(20),F(100),F(1000)]:
                    iv=primitive(q,t,rho);ref=prim(dec(q),dec(t),dec(rho))
                    if q<=F('.001'):
                        v=min(t,q/(rho*F('.001')));exact=q*v-rho*F('.001')*v*v/2
                        check(f'primitive_exact:{rho}:{q}:{t}',F(iv.lo)<=exact<=F(iv.hi))
                    else:
                        check(f'primitive100:{rho}:{q}:{t}',iv.lo-D('1e-80')<=ref<=iv.hi+D('1e-80'))
    for row in r['rows']:
        c1=row['calendar'];name=f'{row["shield"]}:{row["profile"]}:{row["growth"]}:{row["stages"]}:{c1["ka"]}'
        check(name+':affine',row['majorant']['min_slack']>=0)
        check(name+':global_bad_once',row['price']['global_bad_probability']==min(F(1),row['risk_upper']))
        check(name+':all_terms',row['risk_upper']==F('6e-6')+F(c.old.HANDOFF['rows'][0 if row['shield']=='3' else 1]['Dstar'])+row['initial']+row['pair_risk']+row['cross']['X'])
        check(name+':positive_aperture',row['cross']['X']>0)
        check(name+':zero_aperture',c.old.cross(dict(p,beta=F(1,2*p['W'])),c1['Ps_min'],c1['Pl'],c1['ka'],p['S2exact'],F(0))['X']==0)
    for shield,co in r['constant_E'].items():
        check(shield+':constant_scalar_boundary',co['risk_upper']<=F('.001')<co['next_risk_upper'])
        check(shield+':necessary_not_sufficient',co['class_lower']['risk_lower_at_P0']>F('.001'))
    check('secondary_constant_exclusion_preserved',r['constant_E']['2.5']['class_lower']['fixed_class_resource_excluded'])
    check('main_no_tenfold_claim',not any(x['tenfold_pass'] for x in r['rows'] if x['growth']=='main'))
    check('quiet_goal_not_renamed',not any(x['quiet_one_percent_pass'] for x in r['rows']))
    check('all_unknowns_still_null',all(v is None for v in r['unknowns'].values()))
    rr=c.resource(cl);rate=rr['rate_max_sigma1'];h=F('.001');dl=F('3e-6')
    peak=rr['peak_control_no_application']+cl['app']*(1+rate*(h+dl))/h
    check('whole_bus_peak_boundary',peak==F('.8'))
    check('beyond_peak_boundary_rejected',peak+cl['app']*F(1)*(h+dl)/h>F('.8'))
    check('queue_including_reply_is_finite',c.old.ceil(F(1)+rate*dl)==2)
    check('certificate_barrier_not_physical_impossibility',r['certificate_barrier']['any_affine_certificate_lower_even_Ps_zero']>F('.002'))
    return checks


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');args=ap.parse_args()
    baseline=subprocess.run([sys.executable,'-B',str(c.ROOT/'experiments/t110-err-write-service/verify.py')],cwd=c.ROOT,text=True,capture_output=True)
    if baseline.returncode:raise RuntimeError(baseline.stdout+baseline.stderr)
    tests=unittest.defaultTestLoader.discover(str(c.HERE),'test_rule.py')
    result=unittest.TextTestRunner(verbosity=1).run(tests)
    if not result.wasSuccessful():raise AssertionError('state model failed')
    r=report();checks=regression(r)
    pins=json.loads((c.HERE/'pinned_sources.json').read_text())
    for name,wanted in pins.items():
        data=(c.ROOT/name).read_bytes();got=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
        if got!=wanted:raise AssertionError('changed accepted input '+name)
    r['verification']=dict(state_model_tests=result.testsRun,numeric_checks=len(checks),checks=checks,
        accepted_T110_stdout=baseline.stdout,accepted_outputs_rewritten=False,pinned_sources=pins)
    text=json.dumps(c.old.serial(r),ensure_ascii=False,indent=2)+'\n';out=c.HERE/'report.json'
    if args.write:out.write_text(text)
    if not out.exists() or out.read_text()!=text:raise AssertionError('report differs; inspect before --write')
    print(f'T114: {result.testsRun} state tests; {len(checks)} numeric/proof-boundary checks; accepted T110 unchanged.')


if __name__=='__main__':main()
