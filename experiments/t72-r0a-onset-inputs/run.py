"""T72 tables from accepted raw measurements and the frozen conditional grid."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import platform
import subprocess
import sys
import numpy as np
from counts import Integral, available
from onsets import inspect
from risk_inputs import input_rows, table, fixed_necessity
from prepare import prepare, T67
import analyze
from verify_t73 import write_results, THEORY_SHA
from t73_calendar import geometry_enumeration
from t73_resources import checks as resource_checks

HERE = Path(__file__).resolve().parent


def diagnostic(config, manifest, series_path, out):
    d = config['diagnostic']
    records, availability_rows, counts, signal_counts = [], [], [], []
    author_ids={e['id'] for e in manifest['events'] if e.get('author_dates')}
    for sat in [16,18,19]:
        for cad in d['cadences_s']:
            path = series_path/f'g{sat}_{cad}.npz'
            if not path.exists(): continue
            with np.load(path) as z: group = dict(z)
            sources=sorted([r for r in manifest['files'] if r['satellite']==sat and r['cadence_s']==cad],key=lambda r:r['date'])
            for event in manifest['events']:
                start,end,bg = [analyze.stamp(event[k]) for k in ['analysis_start','analysis_end_exclusive','background_start']]
                pick = (group['time'] >= bg) & (group['time'] < end)
                t,signature = group['time'][pick],group['signature'][pick]
                file_index=group['file_index'][pick]
                peak = None if event['kind']=='special_full_month' else analyze.stamp(event['peak_utc'])
                for model,mask,direction in itertools.product([d['response'],d['sensitivity_response']],d['masks'],['E','W']):
                    j = ['E','W'].index(direction)
                    x = group[model][pick,j]
                    valid = np.isfinite(x)
                    if mask!='reported': valid &= group['core_strict' if model=='core_only' and mask=='strict' else mask][pick,j]
                    base = {'event_id':event['id'],'satellite':sat,'cadence_s':cad,'direction':direction,
                            'response':model,'mask':mask,'catalogue_peak_utc':event['peak_utc'] if peak is not None else None,
                            'scenario':'T67 data32 10mmAl proton only; NOT full38 R0-A',
                            'quiet_level_s_inv':d['quiet_level_data32_inversions_s_inv'],'quiet_history_s':d['quiet_history_s']}
                    rows,status = inspect(t,x,valid,signature,cad,d['quiet_level_data32_inversions_s_inv'],d['quiet_history_s'],
                                          d['levels_data32_inversions_s_inv'],start,end,peak)
                    for s in status:
                        availability_rows.append({**base,**s,'expected_window_bins':int(np.ceil(end/cad)-np.ceil(start/cad))})
                    for row in rows:
                        i,root,rise = [row.pop(k) for k in ['target_index','quiet_root_index','rise_start_index']]
                        rid = len(records)+1
                        delta = float(t[i]-t[root]) if root is not None else None
                        resolved = root is not None and root < i
                        f = Integral(x[root:i],cad) if resolved else None
                        entry = {**base,**row,'record_id':rid,'target_bin_start_utc':analyze.iso(t[i]),
                                 'target_bin_end_utc':analyze.iso(t[i]+cad),'target_bin_response_s_inv':float(x[i]),
                                 'quiet_reference_start_utc':analyze.iso(t[root]-d['quiet_history_s']) if root is not None else None,
                                 'quiet_exit_bin_start_utc':analyze.iso(t[root]) if root is not None else None,
                                 'quiet_exit_bin_end_utc':analyze.iso(t[root]+cad) if root is not None else None,
                                 'elapsed_bin_starts_s':delta,
                                 'time_from_quiet_s':delta if resolved else None,
                                 'crossing_time_status':'native_bin_means_not_physical_crossing' if resolved else
                                    'unresolved_same_bin' if root is not None else 'no_confirmed_quiet_reference',
                                 'repeat_rise_start_utc':analyze.iso(t[rise]) if rise is not None else None,
                                 'repeat_rise_elapsed_s':float(t[i]-t[rise]) if rise is not None else None,
                                 'quiet_to_target_expected_inversions':float(f(delta)) if resolved else None,
                                 'integration_end_exclusive_utc':analyze.iso(t[i]),
                                 'known_at_earliest_utc':analyze.iso(t[i]+cad),
                                 'independence':'overlapping windows/satellites/directions are NOT independent events'}
                        target_source=sources[int(file_index[i])]
                        entry.update(target_source_name=target_source['name'],target_source_sha256=target_source['sha256'],
                            processing_version=target_source['version'],signature_id=int(signature[i]),
                            target_screened=bool(group['screened'][pick,j][i]),
                            target_strict=bool(group['strict'][pick,j][i]),
                            target_core_strict=bool(group['core_strict'][pick,j][i]),
                            mask_status='descriptive reported values may have rejected quality' if mask=='reported' else
                                        'screened admits dynamic-integration flag; strict may remove fast rises' if mask=='screened' else 'T67 strict quality')
                        if root is not None:
                            entry['quiet_exit_source_name']=sources[int(file_index[root])]['name']
                            entry['reference_interval_all_strict']=bool(np.all(group['strict'][pick,j][root:i+1]))
                        if resolved:
                            # Native H_l changes: descriptive, split by primary/repeat/post-peak.
                            yy=x[root:i+1]; level=row['target_level_s_inv']
                            h=np.where(yy<=level,yy/level,1+np.log(np.maximum(yy,1e-300)/level))
                            entry['max_H_increment_s_inv_on_reference_interval']=float(max(0.,np.max(np.diff(h)/cad,initial=0.)))
                        own_start=root if row['segment_type']=='primary_entry' else rise
                        if own_start is not None and own_start<i:
                            yy=x[own_start:i+1];level=row['target_level_s_inv']
                            h=np.where(yy<=level,yy/level,1+np.log(np.maximum(yy,1e-300)/level))
                            entry['own_rise_start_utc']=analyze.iso(t[own_start])
                            entry['own_rise_max_H_increment_s_inv']=float(max(0.,np.max(np.diff(h)/cad,initial=0.)))
                            entry['own_rise_expected_inversions']=float(np.sum(x[own_start:i])*cad)
                        records.append(entry)
                        # Main model only: sensitivities remain in onset table, not replicated count law.
                        if resolved and model==d['response']:
                            for period,phase,delay in itertools.product(d['periods_s'],d['phase_fractions'],d['delivery_delays_s']):
                                count = available(f,delta,period,phase,delay)
                                counts.append({'record_id':rid,'period_s':period,'phase_fraction':phase,'delivery_s':delay,
                                               'phase_layout':'uniform_full_period','availability_deadline_utc':analyze.iso(t[i]),
                                               'initial_state':'clean at quiet_exit for this diagnostic only',**count})
                            # Proposed nested-calendar method has a packed pass, not uniform phases over 6s.
                            for phase,delay in itertools.product(d['phase_fractions'],d['delivery_delays_s']):
                                counts.append({'record_id':rid,'period_s':6.,'phase_fraction':phase,'delivery_s':delay,
                                               'phase_layout':'packed_50ms_pass','availability_deadline_utc':analyze.iso(t[i]),
                                               'initial_state':'clean at quiet_exit for this diagnostic only',
                                               **available(f,delta,6.,phase,delay,phase_span=.05)})
                            # Readable comparison at the *availability* of the GOES bin,
                            # not at its start. Extra data are required, never zero-filled.
                            if event['id'] in author_ids and mask=='screened' and cad==60 and row['segment_type']=='primary_entry':
                                for external_delay in d['delivery_delays_s']:
                                    deadline=t[i]+cad+external_delay
                                    last=int(np.searchsorted(t,deadline,side='left'))
                                    ok=(last>i and last<=len(t) and t[last-1]+cad>=deadline and
                                        np.all(valid[root:last]) and np.all(np.diff(t[root:last])==cad) and
                                        np.all(signature[root:last]==signature[root]))
                                    for period,phase,err_delay in itertools.product([.05,6.],d['phase_fractions'],d['delivery_delays_s']):
                                        rec={'record_id':rid,'period_s':period,'phase_fraction':phase,
                                            'GOES_delivery_s':external_delay,'ERR_delivery_s':err_delay,
                                            'availability_deadline_utc':analyze.iso(deadline),'phase_layout':'uniform_full_period',
                                            'status':'resolved' if ok else 'missing_continuous_data_at_signal_deadline'}
                                        if ok:rec.update(available(Integral(x[root:last],cad),deadline-t[root],period,phase,err_delay))
                                        signal_counts.append(rec)
            print(json.dumps({'stage':'onsets','satellite':sat,'cadence_s':cad,'records':len(records),'count_rows':len(counts)}),flush=True)
    analyze.write_csv(out/'onsets.csv.gz',records)
    analyze.write_csv(out/'availability.csv',availability_rows)
    analyze.write_csv(out/'available_counts.csv.gz',counts)
    analyze.write_csv(out/'author_signal_counts.csv.gz',signal_counts)
    # All windows remain represented. Four named events are a readable index, not selection.
    reference=[r for r in records if r['event_id'] in author_ids and r['mask']=='screened' and r['response']=='main_loglog' and
               (r['segment_type']=='primary_entry' or r['status']!='confirmed_quiet_reference')]
    analyze.write_csv(out/'author_events.csv',reference)
    return {'onset_rows':len(records),'count_rows':len(counts),'availability_rows':len(availability_rows),
            'windows':len(manifest['events']),'confirmed_reference_rows':sum(r['status']=='confirmed_quiet_reference' for r in records),
            'reference_rows':len(reference),'signal_count_rows':len(signal_counts),'no_interpolation':True}


def early_numerics(config,out):
    out.mkdir(parents=True,exist_ok=True)
    inputs=list(input_rows(config))
    rows=table(config)
    reference=[r for r in rows if r['long_period_s']==6 and r['short_period_s']==.05 and r['monitor_solar_threshold_s_inv']==.0001
               and r['monitor_delay_s']==2 and r['hold_s'] in [5,10]]
    analyze.write_csv(out/'conditional_inputs.csv',inputs)
    analyze.write_csv(out/'method_grid.csv.gz',rows)
    analyze.write_csv(out/'reference_method.csv',reference)
    analyze.write_csv(out/'fixed_necessity.csv',[fixed_necessity(config['conditional_r0a'],r) for r in inputs])
    source=HERE.parent/'t68-v21-inputs/outputs/service.csv'
    with source.open(newline='') as f:
        audit=[r for r in csv.DictReader(f) if r['mode']=='internal_x8_known']
    analyze.write_csv(out/'T68_16_63_audit.csv',audit)
    (out/'theorist_inputs.json').write_text(json.dumps({'config':config,'conditional_environment':inputs,
         'reference_substitution':reference,'not_yet_proved':['#73 causal calendar and long-interval ceiling',
             'full38 physical Theta joint coverage','ERR parity and count coupling','U clean fence and WCET',
             'monitor qualification and application peak/delay constraints'],
         'diagnostic_level_to_risk_threshold_mapping':None,'GOES_shield_full38_conversion':None},ensure_ascii=False,indent=2)+'\n')
    return {'grid_rows':len(rows),'algebra_pass_rows':sum(r['conditional_algebra_pass'] for r in rows),
            'physical_qualification':False,'theory73_proof_available':False}


def numerics(config,out):
    early=early_numerics(config,out/'early')
    checked=write_results(out)
    (out/'verification_protocol.json').write_text(json.dumps({'theory_sha':THEORY_SHA,
        'geometry':geometry_enumeration(),'resources':resource_checks(),
        'finite_checks_are_not_physical_qualification':True},indent=2)+'\n')
    return {'theory_sha':THEORY_SHA,'checked_sets':checked,'early_candidate_superseded_by_T73':early,
            'physical_qualification':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--numerical-only',action='store_true')
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(HERE),'-p','test_*.py','-v'],check=True)
    config=json.loads((HERE/'config.json').read_text())
    summary={'numerics':numerics(config,args.out)}
    if not args.numerical_only:
        manifest,series=prepare(args.cache)
        summary['GOES']=diagnostic(config,manifest,series,args.out)
    sources=[HERE/'config.json',HERE/'inputs/t73_7ed0f6c.json',T67/'outputs/source_manifest.json',T67/'METHOD.md',
             HERE.parent/'t58-fixed-baseline-r0b/certificate.py',
             HERE.parent/'t68-v21-inputs/outputs/numerics.csv',HERE.parent/'t68-v21-inputs/outputs/service.csv']
    sources+=sorted(HERE.glob('*.py'))
    sources.append(HERE/'inputs/t72_explicit_changes.json')
    (args.out/'provenance.json').write_text(json.dumps({'base':config['base_commit'],'python':platform.python_version(),'numpy':np.__version__,
       'theory_sha':THEORY_SHA,'engineer_revision':'git commit containing these source hashes (PR #77; no self-referential output SHA)',
       'source_sha256':{str(p.relative_to(HERE.parents[1])):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
       'source_bytes_manifest':'../t67-goes-growth/outputs/source_manifest.json','accepted_packages_modified':False},indent=2)+'\n')
    (args.out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
