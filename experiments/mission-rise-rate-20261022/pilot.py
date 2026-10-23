"""Preregistered conditional rho-only probe; never writes accepted results."""
from copy import deepcopy
from fractions import Fraction as F
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ACCEPTED = ROOT / 'experiments/t186-method-comparison/code-strength'
sys.path.insert(0, str(ACCEPTED))
import informational
import comparison as cmp


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, default=str) + '\n').encode()


def load():
    manifest = json.loads((HERE / 'frozen-inputs.json').read_text('utf-8'))
    for rel, expected in manifest['sha256'].items():
        if sha(ROOT / rel) != expected:
            raise ValueError('Frozen dependency changed: ' + rel)
    plan = json.loads((HERE / 'pilot-input.json').read_text('utf-8'))
    cfg = json.loads((ROOT / plan['common_input']).read_text('utf-8'))
    return cfg, plan, manifest


def altered(cfg, plan, rho):
    point = deepcopy(cfg)
    point['environment']['reference_growth_per_s'] = rho
    point['adaptive']['information_numeric'] = deepcopy(plan['information_numeric'])
    # Fail closed if a future edit changes another scientific premise.
    restored = deepcopy(point)
    restored['environment']['reference_growth_per_s'] = cfg['environment']['reference_growth_per_s']
    restored['adaptive']['information_numeric'] = cfg['adaptive']['information_numeric']
    if restored != cfg:
        raise ValueError('rho-only sensitivity contract violated')
    return point


def application_floor(cfg, n):
    """All mandatory application work, minus at most one terminal job/stream."""
    s = cmp.service(cfg, n)['lower']
    counts = cmp.count_apps(cfg)
    return (max(F(0), counts['read']-1)*s['app_read']
            + max(F(0), counts['write']-1)*s['app_write']
            + cfg['words']*s['initial']) / (F(cfg['mission_s'])*cmp.NS)


def limits(cfg):
    old = json.loads((ACCEPTED.parent / 'app-only/outputs/result.json').read_text('utf-8'))
    if sha(ACCEPTED / 'common-input.json') != old['common_input_sha256']:
        raise ValueError('OFF certificate belongs to a different input')
    cal = old['calendar']
    off_q = cmp.risk(cfg, 44, 2, cal['period_ns'], cal['aperture_ns'])
    if off_q['upper'] != F(old['Q_upper']):
        raise ValueError('OFF bound changed')
    off_cost = F(old['full_price']['all_history_core_SRAM_upper'])
    floor = application_floor(cfg, 39)
    fixed = {}
    for n, t in [(39, 1), (44, 2)]:
        k = cmp.select_fixed(cfg, n, t)
        risk = cmp.risk(cfg, n, t, cmp.period(cfg, k)['upper_ns'], cmp.service(cfg, n)['upper']['E'])
        fixed[str(n)] = dict(k=k, period=cmp.period(cfg, k), risk=risk,
                            cost=cmp.cost_result(cfg, n, t, k, risk['upper']))
    def support_floor(k):
        return floor + cmp.service(cfg,39)['lower']['R']*cmp.read_bounds(cfg,k)['lower']/(F(cfg['mission_s'])*cmp.NS)
    necessary={}
    for target in (5,10):
        ceiling=fixed['39']['cost']['core_SRAM_fraction_upper']/target
        lo,hi=1,2
        while support_floor(hi)>ceiling:lo,hi=hi,2*hi
        while hi-lo>1:
            mid=(lo+hi)//2
            if support_floor(mid)>ceiling:lo=mid
            else:hi=mid
        if support_floor(1)<=ceiling:hi=1
        odd=hi if hi%2 else hi+1
        necessary[str(target)]=dict(minimum_integer_k=hi,minimum_odd_k=odd,
            previous_k_floor=support_floor(hi-1) if hi>1 else None,
            first_k_floor=support_floor(hi),target_cost_ceiling=ceiling,
            scope='necessary from paid mandatory support only; not sufficient, no Q computed beyond preregistered grid')
    return dict(application_only_n39_bus_lower=floor, off_n44_bus_upper=off_cost,
        off_n44_Q_upper=off_q['upper'], off_risk=off_q,
        strong_class_core_bus_gain_ceiling=off_cost/floor,
        extra_OFF_bus_needed_even_for_possible_gain={str(g):max(F(0), g*floor-off_cost) for g in (5,10)},
        ceiling_basis='C_best_class <= C_OFF_upper, C_adaptive39 >= common_app39_lower; only declared serial bus core',
        full_bus_parameter_bound='G <= (C_OFF_upper+B_OFF_controller)/(C_app39_lower+B_adaptive_controller_lower)',
        scope='Conditional singleton v4 input; no hardware/physical or all-resource scalar conclusion',
        same_code_grid_core_gain_ceiling=fixed['39']['cost']['core_SRAM_fraction_upper']/support_floor(27),
        same_code_grid_adaptive_core_floor=support_floor(27),
        necessary_support_period_for_same_code_gain=necessary,
        fixed_candidates=fixed, fixed_class_lower=None,
        off_additional_scrub=0, off_gain_denominator_note='dedicated-scrub ratio to zero OFF is undefined, no positive savings over zero')


def row(cfg, plan, rho, k):
    point = altered(cfg, plan, rho)
    info = informational.compute(point, k)
    price = cmp.cost_result(point, 39, 1, k, info['risk']['upper'], True, info['calendar'])
    s = cmp.service(cfg, 39)
    apps = cmp.count_apps(cfg)
    common_upper = (apps['read']*s['upper']['app_read']+apps['write']*s['upper']['app_write']
                    +cfg['words']*s['upper']['initial'])/(F(cfg['mission_s'])*cmp.NS)
    # Algebraically disjoint common cost and added scrub, both on full history.
    price['additional_scrub_bus_upper'] = price['core_SRAM_fraction_upper']-common_upper
    return dict(rho_per_s=rho, k=k, information=info, cost=price,
                physical_Q=None, class_lower=None)


def outputs(cfg, plan, base, rows):
    fixed = base['fixed_candidates']['39']['cost']
    summaries = []
    for r in rows:
        risk=r['information']['risk'];price=r['cost']
        # Sufficient comparison of this fixed candidate's lower with adaptive upper.
        ratio=fixed['core_SRAM_fraction_lower']/price['core_SRAM_fraction_upper']
        summaries.append(dict(rho_per_s=r['rho_per_s'],ka=r['k'],
            Q_upper=float(risk['upper']), meets_half_epsilon=r['information']['sufficient_for_target'],
            joint_coupling=float(risk['terms']['joint_coupling']),E_cross=float(risk['terms']['E_cross']),
            lifetime_exceptions=float(risk['terms']['lifetime_exceptions']),
            period_s=float(r['information']['calendar']['Pl']),
            additional_scrub_bus_upper=float(price['additional_scrub_bus_upper']),
            core_bus_upper=float(price['core_SRAM_fraction_upper']),
            payload_Bps=float(price['payload_rate_Bps']),
            selected_fixed_lower_over_adaptive_upper=float(ratio),
            ratio_scope='selected fixed candidate only; not best-class gain'))
    chosen=[]
    for rho in plan['rho_per_s']:
        valid=[r for r in rows if r['rho_per_s']==rho and r['information']['sufficient_for_target']]
        r=max(valid,key=lambda r:r['k']) if valid else None
        chosen.append(dict(rho_per_s=rho,k=None if r is None else r['k'],
            Q_upper=None if r is None else r['information']['risk']['upper'],
            core_bus_upper=None if r is None else r['cost']['core_SRAM_fraction_upper']))
    out=io.StringIO(newline='')
    writer=csv.DictWriter(out,fieldnames=list(summaries[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(summaries)
    result=dict(status='EXPLORATORY_CONDITIONAL_RHO_ONLY',plan=plan,
                limits=base,rows=rows,selected_on_preregistered_grid=chosen,
                physical_Q=None,mission_rho_quantile=None,changed_accepted_files=False)
    return {'pilot.json':encoded(result),'pilot.csv':out.getvalue().encode()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--probe',action='store_true',help='time only rho=.048, k=27; no output files')
    args=parser.parse_args()
    cfg,plan,manifest=load()
    start=time.perf_counter()
    if args.probe:
        r=row(cfg,plan,plan['rho_per_s'][0],max(plan['ka']))
        elapsed=time.perf_counter()-start
        print(json.dumps(dict(probe_elapsed_s=elapsed,Q_upper=float(r['information']['risk']['upper']),
            rough_36_row_seconds=36*elapsed,scope='timing estimate, not measured full run')),flush=True)
        return
    base=limits(cfg)
    print(json.dumps(dict(strong_class_core_bus_gain_ceiling=float(base['strong_class_core_bus_gain_ceiling']),
                          off_n44_Q_upper=float(base['off_n44_Q_upper']))),flush=True)
    rows=[]
    for rho in plan['rho_per_s']:
        for k in plan['ka']:
            r=row(cfg,plan,rho,k);rows.append(r)
            print(json.dumps(dict(rho=rho,k=k,Q_upper=float(r['information']['risk']['upper']),
                                  elapsed_s=time.perf_counter()-start)),flush=True)
    payloads=outputs(cfg,plan,base,rows)
    checks=validate(cfg,plan,base,rows)
    payloads['checks.json']=encoded(checks)
    output_hashes={name:hashlib.sha256(data).hexdigest() for name,data in payloads.items()}
    payloads['replay.json']=encoded(dict(input_sha256=manifest['sha256'],
        code_sha256={name:sha(HERE/name) for name in ['pilot.py']},
        output_sha256=output_hashes,python_requirement='>=3.10; standard library only',
        plan_commit='065519e2eaaa49f6a6187533c223d65c7477896b',
        physical_acceptance=False))
    out=HERE/'outputs'
    if args.write:
        out.mkdir(exist_ok=True)
        for name,data in payloads.items():(out/name).write_bytes(data)
    else:
        mismatches=[name for name,data in payloads.items() if not (out/name).exists() or (out/name).read_bytes()!=data]
        if mismatches:raise SystemExit('Replay differs; no files written: '+', '.join(mismatches))
    # Detect any accidental mutation of the inputs after execution as well.
    load()
    print(json.dumps(dict(rows=len(rows),checks=len(checks['checks']),elapsed_s=time.perf_counter()-start,
                          wrote_new_outputs=args.write,all_passed=True)),flush=True)


def validate(cfg,plan,base,rows):
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(name)
    check('complete fixed 9 by 4 grid',len(rows)==36 and {(r['rho_per_s'],r['k']) for r in rows}=={(rho,k) for rho in plan['rho_per_s'] for k in plan['ka']})
    check('OFF feasible at unchanged target',base['off_n44_Q_upper']<=F(cfg['epsilon'])/2)
    check('application floor positive',base['application_only_n39_bus_lower']>0)
    check('strong-class core ceiling below five',base['strong_class_core_bus_gain_ceiling']<5)
    check('same-code preregistered grid ceiling below five',base['same_code_grid_core_gain_ceiling']<5)
    for target,limit in base['necessary_support_period_for_same_code_gain'].items():
        check('necessary period bracket for gain '+target,
              limit['first_k_floor']<=limit['target_cost_ceiling'] and
              (limit['previous_k_floor'] is None or limit['previous_k_floor']>limit['target_cost_ceiling']))
    for k in plan['ka']:
        rr=[r for r in rows if r['k']==k]
        check(f'k{k} fixed cross and exception terms independent of rho',len({(r['information']['risk']['terms']['E_cross'],r['information']['risk']['terms']['lifetime_exceptions']) for r in rr})==1)
        # Coarse adaptive q refinement need not be monotone; test the actual
        # backward-cone exposure at fixed points, not a rounded display value.
        ell=rr[0]['information']['environment']['ell']
        q=10*ell;a,b=F(5),F(15)
        cones=[informational.exposure(q,a,b,F(rho),ell) for rho in plan['rho_per_s']]
        check(f'k{k} nested growth cones',all(x.lo<=y.hi for x,y in zip(cones,cones[1:])))
        z=informational.exposure(q,a,b,F(0),ell)
        check(f'k{k} exact rho zero exposure',F(z.lo)<=q*(b-a)<=F(z.hi))
        mom=informational.moment(q,b,F(0),ell)
        check(f'k{k} exact rho zero first moment',F(mom.lo)<=q*b*b/2<=F(mom.hi))
    for r in rows:
        i=r['information'];p=r['cost'];name=f"rho={r['rho_per_s']}, k={r['k']}"
        check(name+' Q decomposition',i['risk']['upper']==min(F(1),sum(i['risk']['terms'].values())))
        check(name+' closed-cell certificate',i['majorant']['below_background_slack']>=0 and all(c['left_slack']>=0 and c['right_slack']>=0 for c in i['majorant']['cells']))
        check(name+' application paid and nonnegative scrub',p['additional_scrub_bus_upper']>=0 and p['core_SRAM_fraction_upper']>=base['application_only_n39_bus_lower'])
        check(name+' unknown remains unknown',r['physical_Q'] is None and r['class_lower'] is None and i['risk']['physical_unconditional_probability'] is None)
        check(name+' holds and all-history paid',i['calendar']['zero_union_slack']>=0 and p['bad_history_paid'] and p['pending_paid'] and p['after_A_paid'])
    # A drifted manifest must fail before computing: checked by load() each run.
    return dict(all_passed=True,checks=checks,scope='targeted mathematical/contract checks, not physical validation')


if __name__=='__main__':main()
