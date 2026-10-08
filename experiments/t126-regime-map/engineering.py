"""T126 bounded map. Exact rational decisions; no new sufficient theorem.

Accepted T58/T95/T110/T114 code and reports are read-only dependencies.
All files produced by --write are confined to this task's outputs directory.
"""
import argparse
import csv
import hashlib
import importlib.util
import io
import itertools
import json
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path
import subprocess
import sys
from urllib.request import urlopen

import bounds
import verify as theory

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'outputs'
PINS = json.loads((HERE/'engineering-inputs.json').read_text(encoding='utf-8'))
GRID = json.loads((HERE/'grid.json').read_text(encoding='utf-8'))
from certificate import (Risk, Resource, fixed_period, resources, resource_ok,
                         first_resource_tick, class_lower, components)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    obj = importlib.util.module_from_spec(spec)
    sys.modules[name] = obj
    spec.loader.exec_module(obj)
    return obj


sys.path.insert(0, str(ROOT/'experiments/t114-two-stage-err'))
t114 = module('t126_accepted_t114', 'experiments/t114-two-stage-err/calculate.py')


def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'), parse_float=Decimal)


def blob_hash(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()


def verify_blob(data, wanted):
    if blob_hash(data) != wanted:
        raise ValueError('pinned input blob mismatch')
    return data


def t127_inputs():
    """Read exact published version even before merge; no moving branch refs."""
    result, receipt = {}, []
    for short, wanted in PINS['t127_git_blobs'].items():
        path = 'experiments/t127-cy62167-pdi/'+short
        p = subprocess.run(['git', 'show', PINS['t127_sha']+':'+path],
                           cwd=ROOT, capture_output=True)
        if p.returncode == 0:
            data = p.stdout
        else:
            url = ('https://raw.githubusercontent.com/z3tm4n-x/'
                   'phd-adaptive-memory-ecc/'+PINS['t127_sha']+'/'+path)
            with urlopen(url, timeout=45) as f:
                data = f.read()
        verify_blob(data, wanted)
        receipt.append(dict(path=path, sha=PINS['t127_sha'], git_blob=wanted,
                            sha256=hashlib.sha256(data).hexdigest()))
        if short.endswith('.json'):
            result[short] = json.loads(data, parse_float=Decimal)
    return result, receipt


def lower_price(W, n, T, B, witness, removed, paid_lower, paid_upper, eps, de=F(0)):
    """One fixed split, no search over witnesses; failure -> unknown, not zero."""
    if not witness['admissible']:
        return dict(value=None, reason=witness['reason'])
    L = witness['L']; split = F(PINS['necessary_split_s'])
    tick = F(PINS['necessary_inverse_tick_s'])
    tail = bounds.tail_lower(W, n, B, L, removed, split, de)
    def lo(P):
        return bounds.moderate_lower(W, n, B, L, removed, P, split, de)
    left, right = removed//tick+1, split//tick
    top = lo(right*tick)
    if tail is None or top is None or tail <= eps or top <= eps:
        return dict(value=None, reason='declared_split_or_tail_does_not_exclude',
                    tail=tail, moderate_at_split=top, split=split)
    for _ in range(PINS['necessary_bisection_steps_max']):
        if right-left <= 1:
            break
        mid = (left+right)//2
        if lo(mid*tick) > eps:
            right = mid
        else:
            left = mid
    else:
        raise AssertionError('bounded inversion exhausted')
    P0 = right*tick
    assert lo(P0) > eps
    return dict(value=bounds.price_floor(W, paid_lower, paid_upper, P0, T),
                P0=P0, predecessor=P0-tick, Q_lower=lo(P0),
                predecessor_Q_lower=lo(P0-tick), tail=tail, split=split,
                removed=removed, paid_lower=paid_lower, paid_upper=paid_upper,
                delta_exec=de, reason=None,
                scope='candidate T126 necessary bound; arbitrary fixed phases')


def r0b_rows():
    cfg = load('experiments/t58-fixed-baseline-r0b/config.json')
    hist = load('experiments/t58-fixed-baseline-r0b/summary.json')['history']
    T = F(hist['T_s']); n = cfg['scenario']['n']; result = []
    app, rc = cfg['app_diagnostic'], cfg['reference_point_rule']['table_resources']
    tick = F(cfg['actions']['tick_s']); mlo, mhi = int(cfg['actions']['M_min']), int(cfg['actions']['M_max'])
    for W, speed, eps_s in itertools.product(GRID['r0b']['W'], GRID['r0b']['R_eff_bit_s'], GRID['epsilon']):
        N = n*W; eps = F(eps_s); c = F(n, speed)
        p = Risk(T, F(hist['B_per_bit_s_inverse'])*N, F(hist['bbar_per_bit_s_inverse'])*N,
                 F(hist['FS_per_bit'])*N, F(1,W), F(1), F(n-1,n*W), F(n-1,n*W*W), D=c)
        r = Resource(W, c, T, F(rc['h_s']), F(1), F(rc['peak']), F(rc['delay_s']),
                     F(app['sigma_s']), F(app['u']), F(app['g_s']), tick)
        win = fixed_period(p,r,eps,mlo,mhi)
        rm = first_resource_tick(r,mlo,mhi)
        wit = bounds.plateau(T,p.B,p.b,p.FS)
        floor = lower_price(W,n,T,p.B,wit,c,c,c,eps)
        price = win['resource']['tax_upper'] if win['selected_tick'] else None
        Q = win['upper_components']['total'] if price is not None else None
        for bud_s in GRID['quiet_protection_budgets']:
            budget = F(bud_s)
            lower = class_lower(W,n,p.B,wit['L'],c,c,T,budget,
                                witness_admissible=True,deterministic_window_contract=True)
            budget_run = fixed_period(p,replace(r,tax=budget),eps,mlo,mhi)
            ok = price is not None and price <= budget
            assert ok == (budget_run['selected_tick'] is not None)
            accepted_excluded = lower['lower'] > eps
            candidate_excluded = floor['value'] is not None and floor['value'] > budget
            excluded = accepted_excluded or candidate_excluded
            lab = bounds.status(constant_ok=ok, fixed_excluded=excluded)
            result.append(dict(id=f'R0B_W{W}_R{speed}_e{eps_s}_c{bud_s}', example_id='A1' if W==262144 else 'A2',
                family='R0B_grid', domain='T58/diagnostic/independent-uniform-singleton-full39/U/fixed-calendar',
                source_sha=PINS['main_base'], qualification='conditional_model_not_future_physical_bound',
                n=n,W=W,T=T,epsilon=eps,quiet_budget=budget,R_eff_bit_s=speed,
                B=p.B,b=p.b,FS=p.FS,Dstar=F(0),Dstar_kind='exact_in_singleton_diagnostic_only',
                environment_square_upper=p.moments()[1],witness=wit,
                coordinates=theory.coordinates(n,W,T,eps,F(0),p.b,p.B,p.FS,rm*tick if rm else None),
                P_min_kind='minimum_of_T58_sufficient_resource_tests_without_price_budget',
                P_min=rm*tick if rm else None,first_resource_tick=rm,
                full_tick_range=[mlo,mhi],tick=tick,selected_tick=win['selected_tick'],
                selected_period=win['selected_tick']*tick if price is not None else None,
                Q_upper=Q,Q_upper_scope='T52/U uniform lifetime bound of presented Fixed',
                Q_lower_at_budget=lower['lower'],Q_lower_scope='entire deterministic T58 fixed class at this budget',
                class_lower_at_budget=lower,constant_excluded=excluded,
                constant_excluded_T58=accepted_excluded,
                constant_excluded_candidate_T126=candidate_excluded,
                constant_quiet_lower=floor['value'],constant_mission_lower=floor['value'],
                constant_quiet_upper=price,constant_mission_upper=price,necessary_price=floor,
                adaptive_quiet_upper=None,adaptive_mission_upper=None,quiet_gain_lower=None,
                full_bus_quiet_upper=None if price is None else price+r.u+r.sigma/T,
                full_bus_mission_upper=None if price is None else price+r.u+r.sigma/T,
                cost_scope='full quiet horizon T, continue after first exceedance; returning quiet not established',
                resource=win['resource'],
                all_bus_peak_upper=None if win['resource'] is None else win['resource']['peak_upper']+(r.sigma+r.u*(r.h+r.delay))/r.h,
                all_bus_peak_scope='T58 offered-work envelope expanded left by the admitted response deadline',
                risk_at_resource_boundary=components(p,rm*tick)['total'] if rm else None,
                resource_at_boundary=resources(r,rm) if rm else None,
                margin_10pct='additional assumed joint WCET <= reserved c/1.1; not measured',
                channel={'kind':'none'},application=cfg['app_diagnostic'],status=lab,
                fixed_search=win,missing_inputs=['future physical Lambda/Theta','preparation and joint WCET qualification',
                                               'adaptive lifetime certificate in this full39 class']))
    assert len(result)==36
    return result


def constant_quiet(p, co, rate, observed_writes):
    """Export T110 constant cost, plus the explicit T114/G3 corrections.

    This is the accepted returning-quiet formula, NOT the mission scalar.
    Full lifetime global bad probability is charged once, as in its source.
    """
    old = t114.old.constant(p)
    assert old['M_ticks'] == co['period_ticks']
    pc = t114.CFG['price_contract']; tq = F(pc['quiet_fraction'])*p['T']; kq=pc['quiet_components']
    # Original constant correction-token rate uses P+d, not adaptive tau.
    rate_base = p['b']+(p['K0']+kq*p['B']*(old['period_upper']+t114.T['d']))/tq
    aperture = (t114.T['E']-t114.T['R'])*(p['b']+kq*p['B']*(old['period_upper']+t114.T['d'])/tq)/p['W']
    X = F(pc['X_rate'])+kq*(F(pc['X_burst_s'])+F(pc['X_rate'])*F('3e-6'))/tq
    offered_q = rate+kq*(1+rate*F('3e-6'))/tq
    obs = t114.T['R'] if observed_writes else F(0)
    app = F('217.002160e-9') if observed_writes else t114.T['app']
    intercept = old['cost_upper']+aperture+X
    return dict(source='T110 constant.cost_upper; T114 appendix G3 aperture, X and observed-write addends',
                old_returning_cost=old['cost_upper'],correction_rate_base=rate_base,
                aperture_addend=aperture,X_addend=X,intercept=intercept,
                offered_quiet_rate=offered_q,observation_addend=obs*offered_q,
                quiet_upper=intercept+obs*offered_q,total_bus_quiet_upper=intercept+app*offered_q,
                TQ_lower=tq,components_max=kq,physical_application_unknown=True)


def accepted_controls():
    buds=list(map(F,GRID['quiet_protection_budgets'])); out=[]
    for anchor in theory.monitor_anchors(buds):
        for j,budget in enumerate(buds):
            a=dict(anchor)
            a.update(id=anchor['id']+f'_c{budget}',family='T95_control',quiet_budget=budget,
                     Q_upper=anchor['risk_upper'],status=anchor['statuses'][j],source_sha=PINS['main_base'],
                     Q_upper_scope='accepted T95 combined U; original environment and monitor only',
                     Q_lower_at_budget=None,constant_excluded=anchor['constant_excluded_by_budget'][j],
                     constant_mission_upper=anchor['constant_quiet_upper'],
                     constant_mission_upper_reason='same deterministic full-U duty; returning edge KQ/TQ >= 1/T conservatively covers the whole mission',
                     full_bus_quiet_upper=None,full_bus_mission_upper=None,
                     missing_inputs=[anchor['unresolved']])
            out.append(a)
    rep=load('experiments/t114-two-stage-err/report.json'); envrows=t114.old.HANDOFF['rows']
    for index, row in enumerate(rep['rows']):
        p=t114.old.environment(next(x for x in envrows if x['shield']==row['shield']))
        co=rep['constant_E'][row['shield']]; cf=co['feasible']
        prof=next(x for x in t114.CFG['profiles'] if x['name']==row['profile'])
        observed=prof['observed_writes']
        rate=min(F(row['resources']['rate_max_sigma1']),F(co['resources']['rate_max_sigma1']))
        if rate<0: rate=None
        Q=F(row['risk_upper']); pr=row['price']
        usable=row['certified'] and rate is not None
        if rate is not None:
            tq=F(t114.CFG['price_contract']['quiet_fraction'])*p['T']; kq=t114.CFG['price_contract']['quiet_components']
            rq=rate+kq*(1+rate*F('3e-6'))/tq; rt=rate+1/p['T']
            obs=F(pr['write_observation_price_per_request'])
            app=F(pr['total_bus_application_write_per_request'] if observed else pr['total_bus_application_read_per_request'])
            quiet=F(pr['quiet_upper_intercept'])+obs*rq
            mission=F(pr['mission_upper_intercept'])+obs*rt
            cq=constant_quiet(p,co,rate,observed) if cf else None
        else:
            rq=rt=quiet=mission=cq=None; obs=F(0);app=F(0)
        floor=F(co['class_lower']['read_price_lower'])
        for bud in buds:
            cok=cf and cq is not None and cq['quiet_upper']<=bud
            aok=usable and quiet<=bud
            exclude=floor>bud or co['class_lower']['fixed_class_resource_excluded']
            label=bounds.status(constant_ok=cok,adaptive_ok=aok,fixed_excluded=exclude)
            out.append(dict(id=f'T114_{index}_{row["profile"]}_{row["growth"]}_{row["stages"]}_c{bud}',
                example_id='A3',family='T114_control',source_sha=PINS['main_base'],
                domain=f'T114/E/{row["profile"]}/{row["growth"]}/original_environment',
                qualification='accepted_conditional_contract_not_device_qualification',
                n=p['n'],W=p['W'],T=p['T'],epsilon=p['eps'],quiet_budget=bud,Dstar=p['D'],
                B=p['B'],b=p['b'],FS=p['FS'],shield_g_cm2=row['shield'],
                coordinates=theory.coordinates(p['n'],p['W'],p['T'],p['eps'],p['D'],p['b'],p['B'],p['FS']),
                candidate_role=row['candidate_role'],profile=row['profile'],growth=row['growth'],stages=row['stages'],
                Q_upper=Q,Q_upper_scope='T114 (3)-(4), original inputs only',
                Q_lower_at_budget=None,Q_lower_scope='see accepted class_lower for period threshold',
                constant_risk_upper=F(co['risk_upper']),class_lower=co['class_lower'],constant_excluded=exclude,
                constant_quiet_lower=floor,constant_quiet_upper=cq['quiet_upper'] if cq else None,
                constant_mission_lower=floor,
                constant_mission_upper=F(co['mission_price_upper_intercept'])+obs*rt if cf and rt is not None else None,
                constant_quiet_export=cq,
                adaptive_quiet_upper=quiet,adaptive_mission_upper=mission,
                quiet_gain_lower=floor/quiet if usable else None,
                mission_gain_lower=floor/mission if usable else None,
                full_bus_quiet_upper=F(pr['quiet_upper_intercept'])+app*rq if rq is not None else None,
                full_bus_mission_upper=F(pr['mission_upper_intercept'])+app*rt if rt is not None else None,
                proposed_admission=usable,accepted_row_certified=row['certified'],
                resource=row['resources'],constant_resource=co['resources'],
                all_bus_peak_upper=None if rate is None else F(row['resources']['peak_control_no_application'])+app*(1+rate*F('.001003'))/F('.001'),
                application=dict(joint_burst=1,rate_upper=rate,observed_writes=observed,
                                 rate_scope='intersection with observed-write constant backend, conservative for read-only',
                                 offered_quiet_rate=rq,offered_mission_rate=rt,actual_load=None),
                channel=dict(profile=prof,growth=next(x for x in t114.CFG['growth_classes'] if x['name']==row['growth']),
                             timing=t114.CFG['timing_requirements'],price=t114.CFG['price_contract']),
                calendar=row['calendar'],P_min=None,P_min_kind='selected short period is not global minimum',
                status=label,missing_inputs=list(t114.CFG['unknowns'])))
    return out


def cy_rows(inputs):
    result=[]
    for source in inputs['outputs/inputs-126.json']['rows']:
        n,W,T=source['n'],source['W'],F(source['T_s'])
        b,B,N=map(F,(source['b_conditional_s'],source['B_conditional_s'],source['N_solar_conditional']))
        solar,mixed,total=map(F,(source['S2_solar_conditional'],source['S2_mixed_conditional'],source['S2_total_conditional']))
        bg=b*b*T; pm=F(source['P_min_calendar_s']); k=F(n-1,2*n*W)
        # Arithmetic tolerance only for pre-existing binary64 source serialization.
        assert abs(total-bg-solar-mixed) < F('1e-8')
        assert abs(mixed-2*b*N) < F('1e-8')
        for es,cs in itertools.product(GRID['epsilon'],GRID['quiet_protection_budgets']):
            eps,bud=F(es),F(cs)
            result.append(dict(id=f'CY_PDI_Al{source["shield_g_cm2"]}_e{es}_c{cs}',
                example_id='A3',example_group='CY62167_full38_shield_curve',family='CY_new_input',
                source_sha=PINS['t127_sha'],domain='T127 conditional full38 response; Lambda/Theta not qualified',
                qualification='unknown_physical_inputs',n=n,W=W,T=T,epsilon=eps,quiet_budget=bud,
                shield_g_cm2=str(source['shield_g_cm2']),b=b,B=B,FS=N,
                Dstar=None,delta=None,chi=None,joint_S2_quantile=None,Q_upper=None,Q_lower_at_budget=None,
                Q_upper_scope='not established',Q_lower_scope='not established',
                S2_background=bg,S2_solar_squared=solar,S2_mixed=mixed,S2_solar_excess=solar+mixed,S2_total=total,
                sigma_singleton_reference=k*pm*(solar+mixed)/eps,
                sigma_beta0_reference=pm*(solar+mixed)/(2*W*eps),
                eta_reference=total/bg,eta_actual=None,
                coordinate_kind='conditional serialized T127 model; NOT joint quantile nor rigorous physical bound',
                Q_without_unknown_D_arithmetic=F(source['Q_without_D_arithmetic']),
                arithmetic_margin_before_D=eps-F(source['Q_without_D_arithmetic']),
                P_min=pm,P_min_kind='minimum existing T114 batch8/c164/4-tick family only',
                resource=inputs['outputs/service.json'],
                constant_quiet_lower=None,constant_quiet_upper=None,constant_mission_upper=None,
                adaptive_quiet_upper=None,adaptive_mission_upper=None,quiet_gain_lower=None,
                full_bus_quiet_upper=None,full_bus_mission_upper=None,constant_excluded=False,
                status='unknown',missing_inputs=source['missing_inputs'],
                lower_witness_status='unknown membership; old 30.81/33.68 percent not transferred'))
    return result


def build():
    inputs, receipt=t127_inputs()
    sources=theory.pin_sources()
    rows=r0b_rows()+accepted_controls()+cy_rows(inputs)
    rows.append(dict(id='A4_missing',example_id='A4',family='other_sram',status='unknown',
        domain='Cypress CY62167EV30LL-45ZXA datecodes 1843/1525; REDW2020 Fig8',
        source_sha=None,part_revision='datecode 1843 CNA and 1525 RADEF, not pooled',
        low_energy_curve_verified=True,transferable_response_upper=None,
        Q_upper=None,constant_quiet_lower=None,constant_quiet_upper=None,
        missing_inputs=['traceable numerical curve/uncertainty for chosen unit/datecode',
                        'energy/angle/package transfer and same-revision high-energy response',
                        'full external39 parent marks, environment and service tuple']))
    r0=[r for r in rows if r['family']=='R0B_grid']
    summary=dict(r0b_constant_sufficient=sum(r['status']=='constant_sufficient' for r in r0),
                 r0b_fixed_excluded_T58=sum(r['constant_excluded_T58'] for r in r0),
                 r0b_fixed_excluded_candidate_extra=sum(r['constant_excluded_candidate_T126'] and not r['constant_excluded_T58'] for r in r0),
                 r0b_unknown_without_fixed_exclusion=sum(r['status']=='unknown' and not r['constant_excluded'] for r in r0),
                 r0b_adaptive_certified=0)
    return dict(task=126,stage='bounded_engineering_first_map',pins=PINS,
                engineering_plan_commit='10f7911aa6b74e36e8a42f17e3698079a5cbd9fd',t127_sources=receipt,accepted_sources=sources,
                rows=rows,r0b_cells=36,cy_shield_cells=36,cy_example_count=1,
                summary=summary,
                necessary_checks=theory.necessary_cases(),
                physical_qualification_claimed=False,new_theory_accepted=False,
                boundary_refinement_rounds_used=0,missing_orbital_inputs={
                    'ephemeris_time_error_and_online_availability':None,
                    'joint_environment_memory_response':None,'raw_ICARE_archive':None,
                    'particle_sensor_is_online_input':False})


def serial(x):
    if isinstance(x,(F,Decimal)):return str(x)
    if isinstance(x,dict):return {k:serial(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [serial(v) for v in x]
    return x


def table(rows):
    fields=['id','example_id','family','domain','qualification','status','constant_excluded',
            'constant_excluded_T58','constant_excluded_candidate_T126',
            'n','W','epsilon','quiet_budget','R_eff_bit_s','shield_g_cm2','Q_upper','Q_lower_at_budget',
            'constant_quiet_lower','constant_quiet_upper','constant_mission_upper','adaptive_quiet_upper',
            'adaptive_mission_upper','quiet_gain_lower','full_bus_quiet_upper','full_bus_mission_upper',
            'P_min','P_min_kind','selected_period','candidate_role','profile','growth','stages',
            'proposed_admission','source_sha','missing_inputs']
    out=io.StringIO(newline=''); w=csv.DictWriter(out,fieldnames=fields,lineterminator='\n');w.writeheader()
    for row in rows:
        rr={}
        for key in fields:
            val=row.get(key)
            if isinstance(val,F): val=theory.decimal(val,18,upper=not ('lower' in key))
            if isinstance(val,list): val='; '.join(val)
            rr[key]='' if val is None else val
        w.writerow(rr)
    return out.getvalue()


def outputs(report):
    return {'map.json':json.dumps(serial(report),ensure_ascii=False,indent=2)+'\n',
            'map.csv':table(report['rows'])}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--write',action='store_true'); args=ap.parse_args()
    r=build()
    for name,data in outputs(r).items():
        p=OUT/name
        if args.write:
            OUT.mkdir(exist_ok=True)
            p.write_text(data,encoding='utf-8',newline='\n')
        else:
            assert p.read_bytes()==data.encode('utf-8'), 'changed output: '+name
    counts={}
    for row in r['rows']: counts[row['status']]=counts.get(row['status'],0)+1
    print(json.dumps(dict(rows=len(r['rows']),statuses=counts),ensure_ascii=False))


if __name__=='__main__':main()
