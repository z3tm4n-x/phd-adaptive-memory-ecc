"""Independent small scalar fold: no imports from T141 production/legacy code.

Shares only input tables and the declared interpolation model. Adaptive scalar
quadrature replaces production Gauss nodes and vector response evaluators.
This is arithmetic independence, not independent physical measurements/review.
"""
import argparse
import bisect
import csv
import hashlib
import json
import math
from pathlib import Path
from scipy.integrate import quad

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def scalar_fold(rho,band):
    source=ROOT/'experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv'
    rows=list(csv.DictReader(source.open(encoding='utf-8')))
    points=sorted((float(r['energy_mev']),float(r['sigma_bit_cm2_per_bit']))
                  for r in rows if r['sigma_bit_cm2_per_bit'])
    energy=[x for x,_ in points]
    slope=(points[1][1]-points[0][1])/(points[1][0]-points[0][0])
    zero=points[0][0]-points[0][1]/slope
    def response(e):
        if band=='low' and e>=5:return 0.
        if band=='high' and e<5:return 0.
        if e<energy[0]:return max(0.,points[0][1]+slope*(e-energy[0]))
        if e>=energy[-1]:return points[-1][1]
        k=bisect.bisect_right(energy,e)-1
        x0,y0=points[k];x1,y1=points[k+1]
        return y0*math.exp(math.log(e/x0)*math.log(y1/y0)/math.log(x1/x0))
    spec=[]
    path=ROOT/'experiments/t68-v21-inputs/inputs/cosrad_main/sp_x.txt'
    col={2.5:5,3.:7,3.5:8,4.:9}[rho]
    for line in path.read_text().splitlines():
        try:r=[float(v) for v in line.split()]
        except ValueError:continue
        if len(r)==10:spec.append((r[0],r[col]))
    se=[x for x,_ in spec]
    def flux(e):
        k=min(len(se)-2,max(0,bisect.bisect_right(se,e)-1))
        x0,y0=spec[k];x1,y1=spec[k+1]
        f=math.log(e/x0)/math.log(x1/x0)
        value=math.exp(math.log(max(y0,1e-300))*(1-f)+math.log(max(y1,1e-300))*f)
        return 0. if value<1e-290 else value
    cuts=sorted({*se,*[x for x in energy+[zero,5.] if se[0]<x<se[-1]]})
    values=[quad(lambda e:response(e)*flux(e),a,b,epsabs=1e-22,epsrel=2e-11,limit=100)
            for a,b in zip(cuts[:-1],cuts[1:])]
    return 19922944*math.fsum(v[0] for v in values),19922944*math.fsum(v[1] for v in values)


def main(out):
    comp=list(csv.DictReader((out/'components.csv').open(encoding='utf-8')))
    independent=[]
    for band in ('low','high'):
        value,error=scalar_fold(3.,band)
        prod=float(next(r['lambda_s_inv'] for r in comp if float(r['shield_g_cm2'])==3. and r['phase']=='solar' and r['component']=='H_'+band))
        rel=abs(value-prod)/value
        if rel>2e-8:raise AssertionError('Independent scalar fold discrepancy')
        independent.append(dict(shield_g_cm2=3.,band=band,scalar_s_inv=value,production_s_inv=prod,
                                relative_difference=rel,quad_error_diagnostic_s_inv=error))
    # Verify the original byte manifests, not only fresh hashes of current bytes.
    manifest=json.loads((ROOT/'experiments/t68-v21-inputs/source_inputs.json').read_text())
    matches={}
    for name,record in manifest['main']['members'].items():
        p=ROOT/'experiments/t68-v21-inputs'/name
        matches[name]=sha(p)==record['sha256']
    originals={
        'calc_v18.zip':'14ac38ff24c1bf1a199278f08a7c807176b8b613f434719309050248b8929b83',
        'article-cy62167-v21.docx':'1de5ee1f05e5e2355928f5ff4d1a221d2e8cb9e7bfef86e2bd31aebbe0655385'}
    for name,wanted in originals.items():
        matches[name]=sha(ROOT/'experiments/t68-v21-inputs/inputs'/name)==wanted
    if not all(matches.values()):raise AssertionError('Historical input hash mismatch')
    squares=[]
    for row in csv.DictReader((out/'shield-summary.csv').open(encoding='utf-8')):
        v={k:float(row[k]) for k in ('S2_background_s_inv','S2_background_solar_s_inv',
            'S2_solar_diagonal_s_inv','S2_solar_cross_s_inv','S2_upper_s_inv')}
        total=math.fsum(v[k] for k in v if k!='S2_upper_s_inv')
        if not math.isclose(total,v['S2_upper_s_inv'],rel_tol=2e-15):raise AssertionError('Missing cross term')
        squares.append(dict(shield_g_cm2=float(row['shield_g_cm2']),sum_components_s_inv=total,
                            cross_s_inv=v['S2_solar_cross_s_inv']))
    contract=json.loads((out/'contract.json').read_text(encoding='utf-8'))
    assert contract['design_probability']['physical_q90_s_inv'] is None
    assert contract['physical_unresolved']['full38_Dstar'] is None
    assert contract['differences_from_R0A']['replacement_authorized'] is False
    events=list(csv.DictReader((out/'profile-events.csv').open(encoding='utf-8')))
    max_residual=0.
    for row in events:
        full=float(row['H_solar_S2_s_inv'])
        check=math.fsum(float(row[k]) for k in ('H_low_S2_s_inv','H_high_S2_s_inv','twice_low_high_s_inv'))
        rel=abs(full-check)/full
        max_residual=max(max_residual,rel)
    assert max_residual<2e-13
    payload=dict(status='PASS',independent_scalar_folds=independent,historical_hash_matches=matches,
                 complete_square_checks=squares,profile_band_square_max_relative_difference=max_residual,
                 physical_unknowns_preserved=True,
                 source_independence='same published inputs; separate scalar evaluator and adaptive nodes; not independent scientific review')
    (out/'checks.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    print('T141 independent small fold, historical hashes and full-square accounting: PASS')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=HERE/'outputs')
    main(p.parse_args().out)
