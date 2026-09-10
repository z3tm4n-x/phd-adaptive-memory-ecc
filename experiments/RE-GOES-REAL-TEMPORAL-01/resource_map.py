#!/usr/bin/env python3
"""Exact-coordinate alignment of repaired policy maps into resource regions.

No distance-based interval dropping or merging is used. Verified root enclosures
remain explicit BOUNDARY-ENCLOSURE bands and are excluded from certified saving
summaries rather than silently assigned an action.
"""
from __future__ import annotations
import argparse,csv,json,math
from fractions import Fraction
from collections import defaultdict
from decimal import Decimal as D,getcontext
from pathlib import Path


def read_csv(p):
    with Path(p).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))

def write_csv(p,rows):
    rows=list(rows);fields=sorted({k for r in rows for k in r}) if rows else []
    with Path(p).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)

def dec(x):return D(str(x))
def key_policy(r):return (r['label'],r['shield'],r['epsilon'],r['kind'],r.get('L_s',''))
def contains_region(r,g):return dec(r['g_lo_open'])<g<dec(r['g_hi_open'])
def contains_boundary(r,g):return dec(r['root_lo'])<g<dec(r['root_hi'])
def find_one(rows,g):
    z=[r for r in rows if contains_region(r,g)]
    if len(z)>1:raise RuntimeError(f'overlapping resolved policy regions at g={g}')
    return z[0] if z else None

def boundary_hit(rows,g):
    z=[r for r in rows if contains_boundary(r,g)]
    return z

def nint(x):return '' if x in ('',None) else int(x)
def dstr(x):return '' if x is None else str(x)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--dir',required=True)
    a=ap.parse_args();getcontext().prec=80;cfg=json.loads(Path(a.config).read_text());d=Path(a.dir)
    pr=read_csv(d/'policy_regions.csv');bd=read_csv(d/'decision_boundaries.csv');base=read_csv(d/'baseline_actions.csv')
    P=D(cfg['restoration']['full_pass_duration_s'])
    pg=defaultdict(list);bg=defaultdict(list)
    for r in pr:pg[key_policy(r)].append(r)
    for r in bd:bg[key_policy(r)].append(r)
    pre={(r['shield'],r['epsilon']):r for r in base if r['comparator']=='Precomputed'}
    out=[]
    delayed_keys=sorted(k for k in pg if k[3]=='Delayed')
    for k in delayed_keys:
        label,shield,eps,_,L=k; dk=k;ik=(label,shield,eps,'Ideal','')
        drs=pg[dk];irs=pg[ik];dbs=bg.get(dk,[]);ibs=bg.get(ik,[])
        if not irs:raise RuntimeError(f'missing Ideal map {ik}')
        replay_display=drs[0]['replay_g_min']
        rnum=drs[0].get('replay_g_min_exact_numerator','');rden=drs[0].get('replay_g_min_exact_denominator','')
        replay_frac=Fraction(int(rnum),int(rden)) if rnum and rden else Fraction(0,1)
        cuts={D(0),D(1)}
        for r in drs+irs:cuts.update((dec(r['g_lo_open']),dec(r['g_hi_open'])))
        for r in dbs+ibs:cuts.update((dec(r['root_lo']),dec(r['root_hi'])))
        cuts=sorted(x for x in cuts if D(0)<=x<=D(1))
        prev=None
        for lo,hi in zip(cuts[:-1],cuts[1:]):
            if hi<=lo:continue
            mid=(lo+hi)/2;dr=find_one(drs,mid);ir=find_one(irs,mid);dh=boundary_hit(dbs,mid);ih=boundary_hit(ibs,mid)
            if dr is None or ir is None:
                if not(dh or ih):raise RuntimeError(f'unexplained policy-map gap {k} ({lo},{hi})')
                cov='BOUNDARY-ENCLOSURE'
            else:cov='OPEN-RESOLVED-CELL'
            b=pre[(shield,eps)]; exact_ref=(label!='EARLIEST_INVALID')
            row={'label':label,'shield':shield,'epsilon':eps,'L_s':L,'g_lo_open':str(lo),'g_hi_open':str(hi),'g_representative':str(mid),
                 'coverage_status':cov,'replay_g_min':replay_display,'replay_g_min_exact_numerator':rnum,'replay_g_min_exact_denominator':rden,
                 'replay_compatible':int(Fraction(mid)>=replay_frac),
                 'precomputed_status':b['status'],'precomputed_passes':b.get('passes','') if b['status']=='CERTIFIED' else '',
                 'delayed_status':'BOUNDARY-ENCLOSURE' if dr is None else dr['status'],'delayed_passes':'' if dr is None else dr.get('passes',''),
                 'ideal_status':'BOUNDARY-ENCLOSURE' if ir is None else ir['status'],
                 'ideal_exact_replay_available':int(exact_ref),
                 'ideal_cost_semantics':'EXACT-REFERENCE-REPLAY' if exact_ref else 'COMPATIBLE-COMPLETION-STRESS',
                 'ideal_passes':'','ideal_compatible_completion_stress_passes':'',
                 'pre_minus_delayed_passes':'','delayed_minus_ideal_passes':'','retention':'',
                 'pre_minus_delayed_occupied_s':'','pre_minus_delayed_occupancy_pp':'',
                 'delayed_minus_ideal_occupied_s':'','delayed_minus_ideal_occupancy_pp':''}
            if ir is not None and ir['status']=='CERTIFIED':
                if exact_ref:row['ideal_passes']=ir.get('passes','')
                else:row['ideal_compatible_completion_stress_passes']=ir.get('passes','')
            if cov=='OPEN-RESOLVED-CELL' and b['status']=='CERTIFIED' and dr['status']=='CERTIFIED':
                q=int(b['passes'])-int(dr['passes']);row['pre_minus_delayed_passes']=q
                occ=P*D(q);row['pre_minus_delayed_occupied_s']=str(occ);row['pre_minus_delayed_occupancy_pp']=str(occ/D(6))
            if cov=='OPEN-RESOLVED-CELL' and exact_ref and dr['status']=='CERTIFIED' and ir['status']=='CERTIFIED':
                q=int(dr['passes'])-int(ir['passes']);row['delayed_minus_ideal_passes']=q
                occ=P*D(q);row['delayed_minus_ideal_occupied_s']=str(occ);row['delayed_minus_ideal_occupancy_pp']=str(occ/D(6))
                if b['status']=='CERTIFIED':
                    den=int(b['passes'])-int(ir['passes'])
                    if den>0:row['retention']=str(D(int(b['passes'])-int(dr['passes']))/D(den))
            # Merge only exact-adjacent regions with identical reported semantics; never across a boundary enclosure.
            sig=tuple(row[x] for x in row if x not in ('g_lo_open','g_hi_open','g_representative'))
            if prev is not None and prev[1]==sig and prev[0]['g_hi_open']==row['g_lo_open'] and row['coverage_status']=='OPEN-RESOLVED-CELL':
                prev[0]['g_hi_open']=row['g_hi_open'];prev[0]['g_representative']=str((dec(prev[0]['g_lo_open'])+hi)/2)
            else:
                prev=[row,sig];out.append(prev)
    rows=[x[0] for x in out];write_csv(d/'resource_comparison.csv',rows)
    print(json.dumps({'status':'PASS','resource_regions':len(rows),'boundary_enclosure_regions':sum(r['coverage_status']=='BOUNDARY-ENCLOSURE' for r in rows)},sort_keys=True))
if __name__=='__main__':main()
