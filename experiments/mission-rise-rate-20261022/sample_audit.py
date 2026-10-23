"""Replay the two pinned latest-day metadata/quality audits, not SEP estimates."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import h5py
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def clean(x):
    if isinstance(x,bytes):return x.decode('utf-8','replace')
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,np.generic):return clean(x.item())
    if isinstance(x,list):return [clean(v) for v in x]
    return x


def attrs(v):
    keys=['units','long_name','flag_values','flag_masks','flag_meanings','_FillValue',
          'valid_range','comments','comment','scale_factor','add_offset']
    return {k:clean(v.attrs[k]) for k in keys if k in v.attrs}


def counts(a):
    values,n=np.unique(a,return_counts=True)
    return [dict(value=clean(v),count=int(c)) for v,c in zip(values,n)]


def audit(path):
    result={}
    with h5py.File(path,'r') as f:
        result['global_attributes']={k:clean(v) for k,v in f.attrs.items()
            if any(s in k.lower() for s in ['time_coverage','date_created','version','algorithm_date','git_commit'])}
        variables={}
        for name,v in f.items():
            if not isinstance(v,h5py.Dataset):continue
            take=(name in ['time','L1a_SciData_TimeStamp','product_time','L1bRecordsInAvg',
                          'DiffProtonLowerEnergy','DiffProtonUpperEnergy','ExpectedLUTNotFound','yaw_flip_flag']
                  or 'DQF' in name or 'ValidL1bSamples' in name or 'Flux' in name)
            if not take:continue
            a=v[()];entry=dict(shape=list(v.shape),attributes=attrs(v))
            if a.size==0:
                entry['empty']=True
            elif name in ['time','L1a_SciData_TimeStamp']:
                entry.update(first=clean(a[0]),last=clean(a[-1]),
                             adjacent_differences=counts(np.diff(a,axis=0)))
            elif a.size<=100:entry['values']=clean(a)
            elif 'DQF' in name or 'Samples' in name or 'Records' in name or name=='yaw_flip_flag':
                entry['value_counts']=counts(a)
            elif 'Flux' in name:
                fill=np.asarray(v.attrs.get('_FillValue',[])).ravel()
                entry.update(nonfinite=int(np.count_nonzero(~np.isfinite(a))),
                    fill_count=int(np.count_nonzero(np.isin(a,fill))),
                    negative_count=int(np.count_nonzero(a<0)),
                    note='counts only, no event/rise extraction; raw numeric units preserved')
            variables[name]=entry
        result['variables']=variables
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--fetch',action='store_true',help='fetch only absent pinned files; verify SHA before audit')
    p.add_argument('--write',action='store_true')
    args=p.parse_args()
    if args.cache.resolve().is_relative_to(ROOT.resolve()):raise ValueError('raw cache must be outside repo')
    manifest_path=HERE/'sample-inputs.json'
    manifest=json.loads(manifest_path.read_text('utf-8'))
    results=[]
    for item in manifest:
        path=args.cache/item['name']
        if not path.exists() and args.fetch:
            with urllib.request.urlopen(item['url'],timeout=30) as response:
                data=response.read(16*1024*1024+1)
            if len(data)>16*1024*1024:raise ValueError('sample exceeds 16 MiB cap')
            if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('remote sample changed')
            args.cache.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('sample hash mismatch')
        results.append(dict(source=item,audit=audit(path)))
    l1,l2=results
    assert 'l1b' in l1['source']['name'] and 'l2' in l2['source']['name']
    checks={
        'l1b_86400_records':l1['audit']['variables']['L1a_SciData_TimeStamp']['shape']==[86400,2],
        'l1b_unit_spacing':l1['audit']['variables']['L1a_SciData_TimeStamp']['adjacent_differences']==[dict(value=1.0,count=172798)],
        'l2_1440_records':l2['audit']['variables']['time']['shape']==[1440],
        'l2_60s_spacing':l2['audit']['variables']['time']['adjacent_differences']==[dict(value=60.0,count=1439)],
        'l2_full_record_counts':l2['audit']['variables']['L1bRecordsInAvg']['value_counts']==[dict(value=60,count=1440)],
        'l1b_t1_degraded_not_silently_good':l1['audit']['variables']['T1_DifferentialProtonFluxDQFs']['value_counts']==[dict(value=16,count=1036800)],
        'l2_energy_units_preserved':l2['audit']['variables']['DiffProtonLowerEnergy']['attributes']['units']=='keV',
    }
    if not all(checks.values()):raise AssertionError(checks)
    result=dict(samples=results,checks=checks,all_passed=True,
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        input_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        software=dict(numpy=np.__version__,h5py=h5py.__version__),
        scientific_scope='latest complete day metadata/quality only; no mission coverage, slope quantile or physical Q')
    data=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
    target=HERE/'outputs/sample-audit.json'
    if args.write:target.write_bytes(data)
    elif target.read_bytes()!=data:raise SystemExit('sample audit replay differs; no files written')
    print(json.dumps(dict(samples=2,checks=len(checks),all_passed=True,wrote=args.write)))


if __name__=='__main__':main()
