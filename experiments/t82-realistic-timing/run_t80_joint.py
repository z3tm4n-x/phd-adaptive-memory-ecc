"""Offline addressed ff85fc8 replay: exactly the old 12 pilot tuples."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from fractions import Fraction as F
import hashlib
import itertools
import json
import lzma
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

import t80_engine as old
import t80_joint as j
from run_t80 import contexts, fixed_row, csv_write as old_csv_write, json_write, decimal_text
from t80_validate import independent_checks as old_checks


def csv_write(path,rows,fields=None):
    # These are admissible bounds on requirements, NOT upward result bounds.
    lower_names={'D_allow','pstar','pstar_whole','pstar_return','target',
                 'a_mass','v_flat','vc','hF_slack','contrast_upper'}
    # contrast_upper is an upper interval endpoint, so keep it upward.
    lower_names.remove('contrast_upper')
    def formatted():
        for r in rows:
            yield {k:decimal_text(v,False) if k in lower_names and isinstance(v,F) else v for k,v in r.items()}
    converted=formatted()
    if fields is None:converted=list(converted)
    old_csv_write(path,converted,fields)


def signature(p):
    return tuple(p[k] for k in ('n','W','T','eps','K','tm','tp','c','g','G','b','B','FS',
                               'S2','Dstar','dE','CX','sigmaX','mode')) + tuple(
        F(p['q'][k]) for k in ('rho0','delta_exec','delta_svc','delta_E','delta_M','alpha_M'))


def read_old():
    with lzma.open(old.HERE/'outputs/t80/pilot_grid.csv.xz','rt') as stream:
        rows=list(csv.DictReader(stream))
    def key(r):
        return (int(r['context_id']),r['kind'],r['mode'])+tuple(F(r[k]) for k in ('qratio','rho_e','DQ','aM','w','d'))
    return {key(r):r for r in rows}


def bounded_old(p,r):
    if r['status']!='certified_conditional':return None
    cf=p['cp']/p['gm'];T=p['T'];TQ=F('.9')*T
    return max(min(F(r['quiet_upper']),cf+(2*p['cp']+p['sigmaX'])/T+p['CX']),
               min(F(r['returns_upper']),cf+(2*p['cp']+p['sigmaX'])*1000/TQ+p['CX']))


class Evaluator:
    def __init__(self):
        self.cache={};self.records=[];self.flat={}

    def get(self,p,am,w,d,qr,rho,DQ,kind,mode,divisor,low_type):
        p=dict(p,mode=mode);p=j.cadence_context(p,divisor)
        key=(signature(p),am,w,d,qr,kind,divisor,low_type)
        if low_type=='reset-slow':key+=(rho,DQ)
        if key in self.cache:return self.cache[key]
        rid=len(self.records)
        base=dict(id=rid,set_representative=p['set'],architecture=p['architecture'],shield=p['shield'],
                  margin=p['margin'],mode=mode,aM=am,w=w,d=d,qratio=qr,rho_e=(rho if low_type=='reset-slow' else None),
                  DQ=(DQ if low_type=='reset-slow' else None),kind=kind,divisor=divisor,low_type=low_type,
                  c=p['c'],g=p['g'],channel_rate=p['CX'],sigmaX=p['sigmaX'],
                  peak_upper=p['resource']['peak'],delay_upper_s=p['resource']['delay'],
                  Dstar=p['Dstar'],quota_upper=old.errors(p['q'],mode),physical_qualification=False)
        base['initial_risk_upper']=p['K']*p['B']*p['Ps']/p['W']
        gate=old.short_gate(p,mode)
        if not gate['short_pass']:
            result=dict(status='short_risk',risk_upper=gate['short_risk_upper'],short_pairs_upper=gate['short_pairs_upper'])
        elif not p['cadence_pass']:
            result=dict(status='cadence_resource')
        else:
            m=j.window(p,am,w,d,qr,kind,divisor)
            base.update({k:m[k] for k in ('wm','wp','Delta_m','Delta_p','dticks','dp','dmin','J','H','ring_counters',
                                          'hF_ticks','hF_max','hF_slack','physical_cadence_qualified')})
            if low_type=='reset-slow':
                result=j.best_reset(p,m,rho,DQ)
                result.update(j.conflict_B3(p,m))
                _,dm=j.strips(p,m,DQ,'reset-slow')
                result['B3_price_saturated']=(result['B3_applies'] and m['J']*dm/p['T']*result['pM_B3_lower']>=1)
                result['B4_positive_contrast_requires_w_below_s']=(m['qR']-m['bU'])**2/(2*F('.048')*F('.001')*p['b'])
            else:
                fkey=(signature(p),am,w,d,kind,divisor)
                if fkey not in self.flat:self.flat[fkey]=j.best_direct(p,m,only_flat=True)
                flat=self.flat[fkey]
                regular=j.best_direct(p,m,include_flat=False)
                accepted=[r for r in (flat,regular) if r['status']=='certified_conditional']
                result=dict(min(accepted,key=lambda r:r['objective']) if accepted else regular)
                result['minimum_whole_quiet']=min((r['minimum_whole_quiet'] for r in accepted),default=None)
                result['flat_status']=flat['status'];result['old_vc_status']=regular['status']
                result['flat_objective']=flat.get('objective');result['old_vc_objective']=regular.get('objective')
        record=base|result
        if 'Q' in record:record['pair_risk_upper']=p['beta']*record['Q']
        self.records.append(record);self.cache[key]=rid
        return rid


def choose(records,ids):
    good=[records[i] for i in ids if records[i]['status']=='certified_conditional']
    return min(good,key=lambda r:(r['objective'],r['divisor'],r['id'])) if good else None


def table_run(out,ps):
    baseline=read_old();ev=Evaluator();classes=[];counts=Counter()
    axes=old.SOURCE['pilot'];pilot=list(itertools.product(map(F,axes['a_M']),map(F,axes['w_s']),map(F,axes['d_s'])))
    fam=old.FAMILY
    def records():
        start=time.monotonic()
        for ci,p in enumerate(ps):
            for kind,mode,qr,rho,DQ in itertools.product(fam['monitor_types'],old.MODES[:2],
                  map(F,fam['q_R_over_bbar_separate_classes']),map(F,fam['rho_e_per_s_separate_classes']),map(F,fam['D_Q_s_separate_classes'])):
                ids0=[];idsF=[];ids_allR=[];ids_allF=[];oldrows=[]
                for am,w,d in pilot:
                    br=baseline[(ci,kind,mode,qr,rho,DQ,am,w,d)]
                    r0=ev.get(p,am,w,d,qr,rho,DQ,kind,mode,2,'reset-slow')
                    f0=ev.get(p,am,w,d,qr,rho,DQ,kind,mode,2,'direct-fast')
                    idsR=[r0];idsF0=[f0]
                    for ty,idx,ids in [('reset-slow',r0,idsR),('direct-fast',f0,idsF0)]:
                        row=ev.records[idx]
                        if row['status'] not in ('short_risk','cadence_resource') and not row.get('full_goal_pass',False):
                            for div in (8,32):ids.append(ev.get(p,am,w,d,qr,rho,DQ,kind,mode,div,ty))
                    oldval=bounded_old(p,br)
                    if oldval is not None:oldrows.append((oldval,br))
                    ids0.append(r0);idsF.append(f0);ids_allR+=idsR;ids_allF+=idsF0
                    counts['pilot_tuples']+=1
                    yield dict(context_id=ci,kind=kind,mode=mode,qratio=qr,rho_e=rho,DQ=DQ,aM=am,w=w,d=d,
                               old_status=br['status'],old_objective_upper=oldval,
                               joint_reset_half_id=r0,direct_half_id=f0,
                               addressed_reset_ids=';'.join(map(str,idsR[1:])),
                               addressed_direct_ids=';'.join(map(str,idsF0[1:])))
                row=dict(context_id=ci,**old.ident(p),kind=kind,mode=mode,qratio=qr,rho_e=rho,DQ=DQ,
                         old_upper=min((r[0] for r in oldrows),default=None),old_theory_sha=j.CONFIG['baseline_theory_sha'])
                for tag,ids in [('joint_reset',ids0),('direct',idsF),('reset_addressed',ids_allR),('direct_addressed',ids_allF)]:
                    r=choose(ev.records,ids)
                    row.update({tag+'_id':None if r is None else r['id'],tag+'_upper':None if r is None else r['objective'],
                                tag+'_risk':None if r is None else r['risk_upper'],tag+'_goal':None if r is None else r['full_goal_pass']})
                classes.append(row)
            print(f'joint pilot {ci+1}/{len(ps)}: {len(ev.records)} distinct calculations, {time.monotonic()-start:.1f}s',flush=True)
    csv_write(out/'pilot.csv.xz',records(),['context_id','kind','mode','qratio','rho_e','DQ','aM','w','d',
        'old_status','old_objective_upper','joint_reset_half_id','direct_half_id','addressed_reset_ids','addressed_direct_ids'])
    csv_write(out/'calculations.csv.xz',ev.records)
    csv_write(out/'classes.csv.xz',classes)
    selected=[r for r in classes if r['qratio']==2 and r['rho_e']==F('1e-6') and r['DQ']==300]
    csv_write(out/'headline.csv',selected)
    # Exact rational records of rows used in independent checks/reports.
    picked=sorted({r[tag+'_id'] for r in selected for tag in ('joint_reset','direct','reset_addressed','direct_addressed') if r[tag+'_id'] is not None})
    json_write(out/'selected.json',[ev.records[i] for i in picked])
    json_write(out/'class_index.json',dict(rows=len(classes),fixed_keys=['set','architecture','shield','margin','kind','mode','qratio','rho_e','DQ'],
        source_of_old_rows='immutable outputs/t80/pilot_grid.csv.xz',channel_combinations=12,
        arithmetic_reuse='identical operands may share calculation id; environment labels and minima remain separate',
        counts=dict(counts),distinct_calculations=len(ev.records),full_grid_expanded=False))
    return ev,classes,selected


def controls(out,ps):
    result=old_checks(old.HERE/'outputs/t80',ps)
    json_write(out/'baseline_68_checks.json',result)
    csv_write(out/'fixed_comparator.csv',[fixed_row(p) for p in ps])
    csv_write(out/'short_gate.csv',[old.short_gate(p,mode) for p in ps for mode in old.MODES])
    with (old.HERE/'outputs/t80/ERR_best.csv').open() as f:rows=list(csv.DictReader(f))
    from t80_err import err_price
    checked=[]
    for row in rows:
        ci=int(row['context_id']);p=ps[ci]
        if row['status']=='certified_conditional':
            r=err_price(p,int(row['ka']),F(row['h']),F(row['risk_upper']))
            for k in ('quiet_upper','returns_upper'):
                assert abs(r[k]-F(row[k]))<F('1e-20')
            row.update(calendar_return_edge=str(j.price_edges(p,F('.9')*p['T'],1000)[0]),
                       control_return_edge=str(j.price_edges(p,F('.9')*p['T'],1000)[1]))
        row.update(formula='old T80 (9)/(10), NOT (6a)',physical_aE=None,
                   return_edges_already_present_in_a0f6ec=True,source_sha=j.CONFIG['previous_delivery_sha'])
        checked.append(row)
    csv_write(out/'ERR_control.csv',checked)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out',type=Path,default=old.HERE/'outputs/t80_joint')
    args=ap.parse_args();out=args.out.resolve()
    if not out.is_relative_to(old.HERE) or out==old.HERE/'outputs/t80':raise ValueError('new T82 output directory required')
    out.mkdir(parents=True,exist_ok=True)
    j.source_check();ps=contexts()
    oldpaths=sorted((old.HERE/'outputs/t80').glob('*'))
    hashes={str(p.relative_to(old.HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in oldpaths if p.is_file()}
    tests=subprocess.run([sys.executable,'-X','utf8','-B','-m','unittest','discover','-s',str(old.HERE),'-p','test_t80*.py','-v'],
                         stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (out/'tests.log').write_text(tests.stdout,encoding='utf-8')
    if tests.returncode:raise RuntimeError(tests.stdout)
    controls(out,ps)
    ev,classes,selected=table_run(out,ps)
    from t80_joint_validate import validate,diagnostics
    check=validate(ev,ps)
    json_write(out/'independent_checks.json',check)
    diagnostics(out,ev,ps,selected,csv_write,json_write)
    from t80_joint_report import report
    report(out,ev,ps,selected)
    assert hashes=={path:hashlib.sha256((old.HERE/path).read_bytes()).hexdigest() for path in hashes}
    json_write(out/'protocol.json',dict(theory_sha=j.CONFIG['theory_sha'],architecture_sha=j.CONFIG['architecture_sha'],
        previous_delivery_sha=j.CONFIG['previous_delivery_sha'],baseline_theory_sha=j.CONFIG['baseline_theory_sha'],
        python=platform.python_version(),tests_passed=int(re.search(r'Ran (\d+) tests',tests.stdout).group(1)),
        baseline_independent_points=68,new_checks=check['points'],old_output_hashes_unchanged=hashes,
        physical_qualification=False,no_GOES_no_RTL_no_physical_campaign=True,
        new_file_hashes={str(p.relative_to(old.HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            sorted(old.HERE.glob('*joint*.py'))+[old.HERE/'t80_joint_config.json',old.HERE/'T80_JOINT_METHOD.md']}))
    print(f'Complete: {len(classes)} fixed classes, {len(ev.records)} calculations, {check["points"]} independent checks',flush=True)


if __name__=='__main__':main()
