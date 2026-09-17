#!/usr/bin/env python3
"""Generate deterministic numeric Package-A inputs. Never run COSRAD or policy trials."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, platform, re, sys, zipfile
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from numpy.polynomial.legendre import leggauss
ROOT=Path(__file__).resolve().parents[1]

def readcsv(name):
    with (ROOT/name).open(newline='') as f:return list(csv.DictReader(f))
def writecsv(name, fields, rows):
    with (ROOT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def writejson(name,value):
    (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def ion_sigma(L):
    a=np.asarray(L,float)
    if np.any(~np.isfinite(a)) or np.any(a<0):raise ValueError('invalid LET')
    return 2.6e-7 * (-np.expm1(-np.maximum((a-.15)/70,0)**1.2))

def ion_iso60(L, order=96):
    a=np.atleast_1d(np.asarray(L,float)); x,w=leggauss(order)
    mu=.75+.25*x
    val=.25*np.sum(w[None,:]*mu[None,:]*ion_sigma(a[:,None]/mu[None,:]),axis=1)
    return val

def proton_anchors():
    p=[]
    for r in readcsv('inputs/proton_repository_points.csv'):
        if r['status']=='EXPERIMENTAL_MARKER_DIGITIZATION':
            p.append((float(r['energy_MeV']),float(r['sigma_cm2_per_bit'])))
    for r in readcsv('inputs/proton_supplementary_points.csv'):
        p.append((float(r['energy_MeV']),float(r['sigma_cm2_per_bit'])))
    p.sort();return np.asarray(p)

def proton_sigma(E):
    a=np.asarray(E,float)
    if np.any(~np.isfinite(a)) or np.any(a<0):raise ValueError('invalid proton energy')
    p=proton_anchors(); safe=np.maximum(a,np.finfo(float).tiny)
    s=np.exp(np.interp(np.log(safe),np.log(p[:,0]),np.log(p[:,1])))
    # Explicit continuations, not fitted experimental data or confidence bounds.
    s=np.where(a<p[0,0],p[0,1]*(a/p[0,0])**2,s)
    return s

def proton_tag(E):
    p=proton_anchors()
    if E<.6:return 'ASSUMPTION_low_E_quadratic'
    if E>186:return 'ASSUMPTION_high_E_constant'
    if 5<E<40:return 'ASSUMPTION_unmeasured_5_to_40_bridge'
    if np.any(np.isclose(p[:,0],E,rtol=0,atol=1e-11)):return 'EXPERIMENTAL_marker_anchor'
    return 'INTERPOLATION_loglog_between_anchors'

def archive_manifest(path):
    raw=Path(path).read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    expected='84b578195499782bb70570dc1dd6d492711a3f6e7f167528912295bf6a2e7beb'
    if sha!=expected or len(raw)!=69464:raise ValueError('not the authorized historical results.zip')
    records=[]; parser_rows=[]
    with zipfile.ZipFile(path) as z:
        members=[i for i in z.infolist() if not i.is_dir()]
        if len(members)!=38:raise ValueError('unexpected member count')
        for item in sorted(members,key=lambda x:x.filename):
            if not re.fullmatch(r'results/[a-z0-9_]+\.txt',item.filename):raise ValueError('unexpected member name')
            b=z.read(item);text=b.decode('ascii');lines=text.splitlines();header=[];nums=[]
            for line in lines:
                split=line.split()
                if split and all(re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?',t) for t in split):
                    nums.append([float(t) for t in split])
                else:header.append(line)
            if not nums or len(set(map(len,nums)))!=1:raise ValueError('ragged or empty numeric table: '+item.filename)
            a=np.asarray(nums)
            if not np.all(np.isfinite(a)) or np.any(a<0):raise ValueError('invalid numeric values')
            records.append({'member':item.filename,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'rows':len(a),'columns':a.shape[1]})
            parser_rows.append({'member':item.filename,'header_lines':header,'first_column_min':float(a[:,0].min()),'first_column_max':float(a[:,0].max()),'numeric_rows':len(a),'numeric_columns':a.shape[1]})
    writecsv('provenance/cosrad_old_member_manifest.csv',list(records[0]),records)
    writejson('provenance/cosrad_old_archive.json',{'sha256':sha,'bytes':len(raw),'member_count':38,'shielding_g_cm2':[1.5,1.75,2,2.25,2.5,2.75,3,3.5,4],'is_new_1mm_input':False,'native_headers_and_numeric_shapes':parser_rows})

def main():
    pa=argparse.ArgumentParser();pa.add_argument('--archive',type=Path);args=pa.parse_args()
    E=np.unique(np.r_[0,np.geomspace(.001,1e5,401),np.linspace(.5,1.5,101),proton_anchors()[:,0],29,184,186,500])
    s=proton_sigma(E)
    rows=[{'energy_MeV':format(float(e),'.12g'),'sigma_cm2_per_bit':format(float(v),'.12e'),'origin':proton_tag(e)} for e,v in zip(E,s)]
    writecsv('inputs/proton_response.csv',list(rows[0]),rows)
    # Two numeric columns, with no metadata strings, for adaptable import.
    with (ROOT/'inputs/proton_response_2col.txt').open('w') as f:
        for e,v in zip(E,s):f.write(f'{e:.12e}\t{v:.12e}\n')
    L=np.unique(np.r_[0,.075,.15,np.geomspace(.001,1000,401),[1,5,10,20,40,60,80,100,200,500]])
    normal=ion_sigma(L); iso=ion_iso60(L)
    rows=[{'LET_MeV_cm2_mg':f'{l:.12g}','sigma_normal_cm2_per_bit':f'{v:.12e}','sigma_iso60_cm2_per_bit':f'{a:.12e}'} for l,v,a in zip(L,normal,iso)]
    writecsv('inputs/ion_response.csv',list(rows[0]),rows)
    with (ROOT/'inputs/ion_normal_2col.txt').open('w') as f:
        for l,v in zip(L,normal):f.write(f'{l:.12e}\t{v:.12e}\n')
    # Independent adaptive-quadrature check, including the exact threshold break.
    checks=[]
    for l in [.01,.075,.1,.15,.3,1,10,70,200,1000]:
        points=[l/.15] if .5<l/.15<1 else None
        oracle,err=quad(lambda mu:mu*float(ion_sigma(l/mu)),.5,1,epsabs=1e-20,epsrel=2e-10,points=points,limit=200)
        v=float(ion_iso60(l)[0]);checks.append({'LET':l,'gauss96':v,'adaptive_quad':oracle,'absolute_difference':abs(v-oracle),'quad_reported_error_not_proof':err})
    writejson('outputs/response_checks.json',{'ion_independent_scalar_checks':checks,'maximum_absolute_disagreement':max(v['absolute_difference'] for v in checks),'constant_sigma_exact_angular_factor':0.375,'note':'agreement checks a scalar implementation; not COSRAD operator identity or certified arithmetic','proton_grid_points':len(E),'ion_grid_points':len(L),'new_measured_anchor_count':3,'frozen_main_measured_anchor_count':len(proton_anchors()),'proton_peak_anchor_sigma':float(proton_sigma(1)),'active_bits':39*2**20,'pass_seconds':2**20*300e-9})
    if args.archive:archive_manifest(args.archive)
    print(json.dumps({'proton_rows':len(E),'ion_rows':len(L),'new_1mm_COSRAD_run':False,'policy_trials':0,'scalar_max_abs_difference':max(v['absolute_difference'] for v in checks)},indent=2))

if __name__=='__main__':main()
