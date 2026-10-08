"""Read-only T119 repeat; --write writes only the NEW T119 report.json."""
import argparse
from pathlib import Path
from fractions import Fraction as F
import hashlib
import json
import subprocess
import sys
import unittest
import joint as j
import balance
import history_checks
import balance_preview

HERE=Path(__file__).resolve().parent
CFG=json.loads((HERE/'config.json').read_text())


def blob(path):
    data=path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()


def config_for(row):
    p=j.accepted.old.environment(j.accepted.old.HANDOFF['rows'][0 if row['shield']=='3' else 1])
    prof=next(x for x in j.accepted.CFG['profiles'] if x['name']==row['profile'])
    gr=dict(j.accepted.CFG['growth_classes'][0],w_s=str(row['w']),h_s=str(row['h']))
    return p,prof,gr


def preview_grid(p,prof):
    rows=[]
    for w,h in CFG['timer_family_s']:
        gr=dict(j.accepted.CFG['growth_classes'][0],w_s=str(w),h_s=str(h))
        for stage in (2,1):
            ks=list(CFG['first_multipliers'])
            if stage==1 and h in (120,180):ks.append(7)
            for ka in sorted(ks):
                q=j.preview(p,prof,gr,ka,stage)
                c=j.accepted.calendar(p,prof,ka,gr)
                price=j.accepted.price(p,c,prof,F(str(q)),stage)
                rows.append(dict(w=w,h=h,stage=stage,ka=ka,risk_preview=format(q,'.12g'),
                     price_preview=format(float(price['mission_upper_intercept']),'.12g'),
                     candidate_only=True,admission_authority=False))
    return rows


def report():
    baseline=j.ROOT/'experiments/t114-two-stage-err/report.json'
    old=json.loads(baseline.read_text())
    assert blob(baseline)=='267861539cfe2d1e861654ccbe118760e5a1a3c9'
    checks=[]
    def check(name,val):
        if not val:raise AssertionError(name)
        checks.append(name)
    rows=[]
    for case in CFG['directed_cases']:
        p,prof,gr=config_for(case)
        r=j.compute(p,prof,gr,case['ka'],case['stage'],**{k:v for k,v in CFG['numerics'].items() if k!='decimal_precision'})
        r['name']=case['name'];r['shield']=case['shield']
        co=old['constant_E'][case['shield']]
        lb=F(co['class_lower']['read_price_lower'])
        pr=r['price'];c=r['calendar']
        rw,rr=F(1000),F(1000)
        app=CFG['application_region_example'];sigma=F(app['joint_burst']);rate=F(app['joint_offer_rate_max_per_s'])
        common_frame=max(F(co['resources']['frame_max']),c['frame'])
        res=j.accepted.resource(c,frame_max=common_frame)
        peak=res['peak_control_no_application']+c['app']*(sigma+rate*F('.001003'))/F('.001')
        dly=F('1.1')*(j.accepted.T['req']+sigma*common_frame+j.accepted.JIT+c['app']+j.accepted.T['reply']+F('1e-7'))
        r['joint_application_example']=dict(joint_burst=sigma,joint_rate=rate,mean_w_bound=rw,mean_r_bound=rr,
              whole_bus_peak_upper=peak,response_upper=dly,
              protection_mission_upper=pr['mission_upper_intercept']+pr['write_observation_price_per_request']*rw,
              whole_bus_mission_upper=pr['mission_upper_intercept']+c['app']*rw+j.accepted.T['app']*rr,
              measured_application=None)
        r['certified']=r['certified'] and peak<=F('.8') and dly<=F('3e-6') and min(res[k] for k in ('app_margin_slack','placement_slack','gate_slack'))>=0
        r['gain_intercept_lower']=lb/pr['mission_upper_intercept'] if r['certified'] else None
        r['gain_at_nonzero_application_lower']=lb/r['joint_application_example']['whole_bus_mission_upper'] if r['certified'] else None
        r['tenfold_write_rate_headroom']=(lb/10-pr['mission_upper_intercept'])/j.accepted.T['R']
        r['quiet_write_rate_headroom']=(F('.01')-pr['quiet_upper_intercept'])/j.accepted.T['R']
        check(case['name']+':affine_intervals',r['majorant']['slack']>=0)
        check(case['name']+':all_risk_terms',r['risk_upper']==p['errors']+p['D']+r['initial']+r['cross']['X']+r['majorant']['integral']/(2*p['W']))
        check(case['name']+':one_global_bad_price',pr['global_bad_probability']==min(F(1),r['risk_upper']))
        check(case['name']+':nonzero_aperture',r['cross']['X']>0 and pr['aperture_extra_fast_fraction']>0)
        rows.append(r)
        print(case['name'],'upper=',j.accepted.old.text_number(r['risk_upper']),
              'mission %=',j.accepted.old.text_number(100*pr['mission_upper_intercept']),
              'certified=',r['certified'],flush=True)
    p,prof,gr=config_for(CFG['directed_cases'][0])
    bc=CFG['balance_addressed'];cg=j.accepted.calendar(p,prof,bc['ka'],gr)
    bal=balance.verify(p,cg,F(CFG['rho_per_s']),bc['stage'],F(bc['alpha_per_s']),F(bc['q0_per_s']),F(bc['A']),
                       phase_cells=bc['phase_cells'],q_cells=bc['q_cells'],z_cells=bc['z_cells'])
    cross=j.accepted.old.cross(dict(p,beta=F(1,2*p['W'])),cg['Ps_min'],cg['Pl'],bc['ka'],p['S2exact'],j.accepted.T['d'])
    bal['risk_upper']=p['errors']+p['D']+p['K0']*p['B']*(cg['Ps']+j.accepted.T['d'])/p['W']+cross['X']+bal['integral']/(2*p['W'])
    bal['risk_pass']=bal['risk_upper']<=p['eps']
    check('balance_full_rectangles',bal['verified'] and bal['max_slope_excess']<=0)
    target=j.accepted.calendar(p,prof,33,gr);q=F('.05')
    K=j.coefficient(q,F('.048'),target,2,8)
    Klo=j.coefficient_lower(q,F('.048'),target,2,8)
    check('barrier_uses_lower_not_upper_enclosure',0<Klo<=K)
    check('barrier_positive_intercept_cost',p['T']>=p['FS']/(q-p['b']))
    barrier=p['errors']+p['D']+q*q*Klo*p['FS']/(2*p['W']*(q-p['b']))
    target_cross=j.accepted.old.cross(dict(p,beta=F(1,2*p['W'])),target['Ps_min'],target['Pl'],33,p['S2exact'],j.accepted.T['d'])
    target_available=2*p['W']*(p['eps']-p['errors']-p['D']-p['K0']*p['B']*(target['Ps']+j.accepted.T['d'])/p['W']-target_cross['X'])
    check('remaining_majorant_obstacle',barrier>p['eps'])
    names={x['name']:x for x in rows}
    check('presented_one_is_admitted',names['one_presented']['certified'])
    check('presented_two_is_admitted',names['two_presented']['certified'])
    check('same_rule_two_risk_improved',names['same_rule_two']['risk_upper']<F(next(x for x in old['rows'] if x['profile']=='MCU_calibrated_write' and x['growth']=='main' and x['stages']==2 and x['candidate_role']=='presented')['risk_upper']))
    check('tenfold_not_claimed',all(x['tenfold_write_rate_headroom']<0 for x in rows if x['certified']))
    check('quiet_one_percent_not_claimed',all(x['quiet_write_rate_headroom']<0 for x in rows if x['certified']))
    pins={name:blob(j.ROOT/name) for name in [
        'theory/t114-two-stage-err.md','theory/t114-two-stage-err-appendix.md',
        'experiments/t114-two-stage-err/config.json','experiments/t114-two-stage-err/report.json',
        'experiments/t114-two-stage-err/HANDOFF.md','experiments/t114-two-stage-err/calculate.py',
        'experiments/t114-two-stage-err/rule.py','experiments/t114-two-stage-err/intervals.py',
        'theory/t57-uniform-count.md','theory/t57-uniform-count-appendix.md']}
    previous=[x for x in old['rows'] if x['profile']=='MCU_calibrated_write' and x['growth']=='main' and x['candidate_role']=='presented']
    histories=history_checks.run()
    check('explicit_same_trajectory_histories',all(x['refinement_confirmed'] for c in histories['cases'] for x in c['rows']))
    check('observed_full_partial_freeze_transitions',len(histories['write_freeze_boundaries'])==6)
    storage_best,storage_trials=balance_preview.find()
    new_sources={name:blob(HERE/name) for name in ['config.json','joint.py','balance.py',
           'balance_preview.py','history_checks.py','test_joint.py','verify.py']}
    return dict(task=119,base=CFG['base_sha'],plan_sha=CFG['plan_commit_before_search'],
           new_source_blobs=new_sources,
           pinned_sources=pins,rows=rows,accepted_T114_comparison=previous,constant_E=old['constant_E'],
           balance_addressed=bal,certificate_expression_barrier=dict(ka=33,q=q,K_upper=K,K_lower=Klo,lower=barrier,
              pair_integral_available=target_available,
              scope='this specified pointwise relaxation; NOT failure probability or impossibility of ERR'),
           storage_preview=dict(best=storage_best,all_trials=storage_trials,admission_authority=False),
           preview_grid=preview_grid(p,prof),explicit_histories=histories,checks=checks,unknowns=j.accepted.CFG['unknowns'],
           verdict='partial conditional joint-bound improvement; main tenfold and quiet1% OPEN; balance candidate does not close target',
           old_report_rewritten=False)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true');args=ap.parse_args()
    base=subprocess.run([sys.executable,'-B',str(j.ROOT/'experiments/t114-two-stage-err/verify.py')],cwd=j.ROOT,text=True,capture_output=True)
    if base.returncode:raise RuntimeError(base.stdout+base.stderr)
    tests=unittest.defaultTestLoader.discover(str(HERE),'test_joint.py');result=unittest.TextTestRunner(verbosity=1).run(tests)
    if not result.wasSuccessful():raise AssertionError('tests')
    out=report();out['verification']=dict(new_tests=result.testsRun,checks=len(out['checks']),
       T114_repeated_read_only=True,T114_final_line=base.stdout.strip().splitlines()[-1])
    encoded=json.dumps(j.accepted.old.serial(out),indent=2,ensure_ascii=False)+'\n'
    path=HERE/'report.json'
    if args.write:path.write_text(encoded)
    if not path.exists() or path.read_text()!=encoded:raise AssertionError('T119 report differs; inspect before --write')
    print('T119:',result.testsRun,'tests;',len(out['checks']),'checks; directed joint and balance certificates; T114 unchanged.')


if __name__=='__main__':main()
