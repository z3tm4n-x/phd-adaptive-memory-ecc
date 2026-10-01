"""Audit the decisive points and remove overlap from the nominal holdout."""
from __future__ import annotations
import csv
from datetime import datetime,timezone
import gzip
import json
import math
from pathlib import Path
import numpy as np
from analyze import write_csv,stamp,iso
from growth import window_extreme,fastest_e_fold,h_l
import sgps
from response import Response


def table(path):
    op=gzip.open if str(path).endswith('.gz') else open
    with op(path,'rt',newline='') as f:return list(csv.DictReader(f))


def supplement(manifest,raw,series_dir,out):
    metrics=table(out/'growth_metrics.csv.gz')
    sums=table(out/'series_summary.csv.gz')
    rho=table(out/'rho_candidates.csv')
    cfg=json.loads(Path(__file__).with_name('config.json').read_text())
    # Event names alone are not a time-disjoint validation set: Nov 14's
    # prehistory overlaps the named Nov 11 case. Remove every training interval.
    purged=[]
    train=[(stamp(e['analysis_start']),stamp(e['analysis_end_exclusive'])) for e in manifest['events'] if not e['holdout']]
    for sat in cfg['satellites']:
        for cad in (60,300):
            p=series_dir/f'g{sat}_{cad}.npz'
            if not p.exists():continue
            with np.load(p) as g:
                t,sig,x=g['time'],g['signature'],g['main_loglog']
                unique=np.ones(len(t),bool)
                for a,b in train:unique &= ~((t>=a)&(t<b))
                for e in manifest['events']:
                    if not e['holdout']:continue
                    m=(t>=stamp(e['analysis_start']))&(t<stamp(e['analysis_end_exclusive']))
                    if not np.any(m):continue
                    for d,direction in enumerate(('E','W')):
                        v=m&unique&g['screened'][:,d]&np.isfinite(x[:,d])
                        for level in cfg['absolute_rate_levels_s-1']:
                            for lag in cfg['windows_s']:
                                r=window_extreme(t,x[:,d],v,sig,cad,lag,level)
                                base={'event_id':e['id'],'holdout':True,'cadence_s':cad,'mask':'screened','level_s-1':level,'window_s':lag,
                                      'satellite':sat,'direction':direction,'retained_bins':int(np.sum(v)),
                                      'removed_overlap_bins':int(np.sum(m&~unique)),'pairs':r['pairs']}
                                if r.get('h'):
                                    rate,i,j=r['h'];base.update({'rho_observed_s-1':rate,'start_utc':iso(t[i]),'end_utc':iso(t[j]),
                                                               'start_value_s-1':float(x[i,d]),'end_value_s-1':float(x[j,d])})
                                purged.append(base)
    write_csv(out/'time_disjoint_holdout.csv',purged)
    # Compact table retains which sensor supplies each extremum, rather than
    # pretending one synthetic satellite/direction achieves every endpoint.
    short=[]
    for e in manifest['events']:
        for cad in (60,300):
            rows=[r for r in sums if r['event_id']==e['id'] and r['cadence_s']==str(cad) and r['series']=='main_loglog' and r['mask']=='screened' and r['peak']]
            if not rows:continue
            peak=max(rows,key=lambda r:float(r['peak']))
            q={'event_id':e['id'],'author_dates':';'.join(e.get('author_dates',[])),'cadence_s':cad,'status':'descriptive model extrema; screened',
               'peak_s-1':peak['peak'],'peak_satellite':peak['satellite'],'peak_direction':peak['direction'],'peak_start_utc':peak['peak_start_utc']}
            for level in cfg['absolute_rate_levels_s-1']:
                rows=[r for r in metrics if r['event_id']==e['id'] and r['cadence_s']==str(cad) and r['series']=='main_loglog' and r['mask']=='screened'
                      and r['level_label']==f'abs_{level:g}' and r['e_min_s']]
                if rows:
                    r=min(rows,key=lambda r:(float(r['e_min_s']),r['e_start_utc'],r['satellite'],r['direction']))
                    for key in ('e_min_s','e_start_utc','e_end_utc','e_bin_integral','satellite','direction'):
                        q[f'{key}_l{level:g}']=r[key]
            short.append(q)
    write_csv(out/'reference_events.csv',short)
    # Audit main native-increment maxima and fastest author e-folds.
    cases=[]
    for r in rho:
        if r['mask']=='screened' and r['window_s']==r['cadence_s']:
            cases.append({'label':'native_rho','event_id':r['event_id'],'satellite':int(r['satellite']),'cadence_s':int(r['cadence_s']),
                          'direction':r['direction'],'level':float(r['level_s-1']),'start':r['start_utc'],'end':r['end_utc']})
    for r in short:
        if r['author_dates'] and r.get('e_min_s_l0.001'):
            cases.append({'label':'author_efold','event_id':r['event_id'],'satellite':int(r['satellite_l0.001']),'cadence_s':r['cadence_s'],
                          'direction':r['direction_l0.001'],'level':.001,'start':r['e_start_utc_l0.001'],'end':r['e_end_utc_l0.001']})
    model=Response();loaded={};points=[]
    for case in cases:
        for endpoint in ('start','end'):
            t=stamp(case[endpoint]);date=datetime.fromtimestamp(t,timezone.utc).strftime('%Y%m%d')
            files=[r for r in manifest['files'] if r['satellite']==case['satellite'] and r['cadence_s']==case['cadence_s']
                   and (r['date']==date or (r['product_prefix']=='se' and date.startswith('201709')))]
            if len(files)!=1:raise ValueError('Ambiguous source for extremum')
            r=files[0]
            if r['name'] not in loaded:
                s=sgps.read(raw/r['name']);loaded[r['name']]=(s,model.calculate(s))
            s,m=loaded[r['name']];ii=np.flatnonzero(s.time==t)
            assert len(ii)==1
            i=int(ii[0]);d=('E','W').index(case['direction']);sensor=1-d if s.yaw[i]==0 else d
            kp,ks,_=model.channel_kernel(s,sensor,'main_loglog')
            total=float(m['main_loglog'][i,d]);core=float(m['core_only'][i,d]);radius=float(s.uncertainty[i,d,:13]@(kp+ks))
            row={**case,'endpoint':endpoint,'utc':case[endpoint],'file':r['name'],'sha256':r['sha256'],
                 'main_s-1':total,'core_s-1':core,'high_energy_fraction':(total-core)/total,
                 'core_L1_reported_uncertainty_radius_s-1':radius,'screened':bool(m['screened'][i,d]),'strict':bool(m['strict'][i,d]),
                 'low_sigma_scenario_s-1':float(min(m[k][i,d] for k in model.models)),
                 'high_sigma_scenario_s-1':float(max(m[k][i,d] for k in model.models))}
            for c,name in ((6,'P6'),(7,'P7'),(13,'P11')):
                row[name+'_reported_flux']=float(s.flux[i,d,c]);row[name+'_reported_uncertainty']=float(s.uncertainty[i,d,c])
                row[name+'_strict']=bool(s.strict[i,d,c])
            points.append(row)
    write_csv(out/'extremum_source_audit.csv',points)
    candidates=[]
    for level in cfg['absolute_rate_levels_s-1']:
        rows=[r for r in rho if r['mask']=='screened' and r['level_s-1']==str(level) and r['window_s']==r['cadence_s']]
        if not rows:continue
        obs=max(float(r['rho_observed_s-1']) for r in rows)
        # A visibly declared engineering proposal, NOT a confidence bound.
        proposal=math.ceil(2*obs*1000)/1000
        candidates.append({'threshold_inversions_s-1':level,'rho_observed_native_s-1':obs,
                           'rho_illustrative_2x_rounded_up_s-1':proposal,'proposal_status':'author decision; no future coverage assigned',
                           'conditional_min_e_fold_s_above_threshold':1/proposal})
    payload={'scenario':'R0-A diagnostic 32 data bits x 2^19, protons, 10 mm Al, isotropic equivalent per direction',
             'candidates':candidates,'recommended_starting_threshold_inversions_s-1':.001,
             'recommendation_reason':'fixed significant absolute floor; retain .01/.1 sensitivity, not selected to pass T57',
             'continuous_growth_contract':None,'future_joint_coverage_probability':None,'full_word_parent_mapping':None,
             'operational_observation_delay_bound_s':None,'confidence_intervals_computed':False,
             'counter_impossibility_proved':False,'adaptive_gain_proved':False}
    peak=max(float(r['peak']) for r in sums if r['series']=='main_loglog' and r['mask']=='screened' and r['cadence_s']=='60' and r['peak'])
    payload['observed_peak_model_s-1']=peak
    payload['peak_status']='maximum retained 1-minute main-model bin, not a future ceiling'
    payload['selected_union_exposure_reference']='selected_union.csv; per satellite/direction/mask, not mission fluence'
    payload['future_exposure_budget']=None
    payload['rho_status']='finite-bin diagnostic; measurement/model errors do not have simultaneous coverage'
    for r in table(out/'selected_union.csv'):
        if r['peak_model_s-1']:
            assert float(r['sum_model_inversions']) <= float(r['peak_model_s-1'])*int(r['unique_retained_s'])*(1+1e-12)
    (out/'theorist_inputs.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    return payload
