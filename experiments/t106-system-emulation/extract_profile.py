"""Recover the already selected T67 event, not a new radiation calculation.

No RADAR execution, interpolation of time, filling, retuning or policy results.
Only the accepted cached response and accepted SGPS adapter are called.
"""
import argparse
from datetime import datetime,timezone
import gzip
import hashlib
import json
from pathlib import Path
import platform
import sys
import urllib.request
import numpy as np

HERE=Path(__file__).resolve().parent
T67=HERE.parent/'t67-goes-growth'
sys.path.insert(0,str(HERE/'.tools/netcdf'))
sys.path.insert(0,str(T67))
from analyze import prepare_group
from response import Response,PINNED

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stamp(s):return int(datetime.fromisoformat(s).timestamp())

def main(download=False):
    source=T67/'outputs/source_manifest.json'
    manifest=json.loads(source.read_text())
    event=next(e for e in manifest['events'] if e['id']=='sep_20240608_0255')
    begin,end=stamp(event['analysis_start']),stamp(event['analysis_end_exclusive'])
    files=[r for r in manifest['files'] if r['satellite']==16 and r['cadence_s']==60 and r['selected_version']
           and stamp(datetime.strptime(r['date'],'%Y%m%d').replace(tzinfo=timezone.utc).isoformat())<end
           and stamp(datetime.strptime(r['date'],'%Y%m%d').replace(tzinfo=timezone.utc).isoformat())+86400>begin]
    assert len(files)==5
    cache=HERE/'.build/t67-source';cache.mkdir(parents=True,exist_ok=True)
    for row in files:
        path=cache/row['name']
        if not path.exists():
            if not download:raise FileNotFoundError(str(path)+'; repeat with --download')
            with urllib.request.urlopen(row['url'],timeout=90) as r:data=r.read()
            assert hashlib.sha256(data).hexdigest()==row['sha256'],row['name']
            path.write_bytes(data)
        assert sha(path)==row['sha256'] and path.stat().st_size==row['bytes']
        print('verified',row['name'],flush=True)
    data,audits=prepare_group(files,cache,Response())
    use=(data['time']>=begin)&(data['time']<end)
    times=data['time'][use];rate=data['main_loglog'][use,0];good=data['screened'][use,0]&np.isfinite(rate)
    assert np.all(times==times.astype(np.int64)) and np.all(np.diff(times)==60)
    assert int(times[0])==begin and int(times[-1])+60==end
    records=[[int(t),float(r) if np.isfinite(r) else None,bool(g)] for t,r,g in zip(times,rate,good)]
    payload={'columns':['interval_start_unix_s','T67_model_inversions_per_s','screened_E'],
             'duration_s':60,'records':records}
    out=HERE/'outputs';out.mkdir(exist_ok=True)
    encoded=(json.dumps(payload,separators=(',',':'),allow_nan=False)+'\n').encode()
    (out/'t67-profile.json.gz').write_bytes(gzip.compress(encoded,mtime=0))
    holes=[];active=None
    for t,g in zip(times,good):
        if not g and active is None:active=int(t)
        if g and active is not None:holes.append([active,int(t)]);active=None
    if active is not None:holes.append([active,end])
    import netCDF4
    result={'event':event,'direction':'E','model':'main_loglog','mask':'screened',
        'bins':len(records),'usable_bins':int(good.sum()),'missing_intervals_unix_s':holes,
        'source_model':{'bits':16777216,'Al_mm':10,'is_R0A_full38_3g_calibration':False},
        'R0A_normalization':'NOT_APPLIED; no policy comparison on this extraction',
        'peak_model_per_s':float(rate[good].max()),'integral_valid_model_inversions':float(rate[good].sum()*60),
        'profile_sha256':sha(out/'t67-profile.json.gz'),'source_manifest_sha256':sha(source),
        'files':files,'adapter_audits':audits,
        'source_sha256':{str(p.relative_to(HERE.parents[1])):sha(p) for p in
          [HERE/'extract_profile.py',T67/'analyze.py',T67/'sgps.py',T67/'nc_reader.py',T67/'response.py',*PINNED]},
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'netCDF4':netCDF4.__version__,
                       'netcdf_c':netCDF4.getlibversion()},
        'scope':'recovered exact selected T67 event; not new response/transport, not physical calibration or completed scenario2'}
    (out/'t67-profile.json').write_text(json.dumps(result,indent=2,allow_nan=False,default=lambda x:x.tolist())+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','source_sha256','adapter_audits','event')},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--download',action='store_true');args=p.parse_args();main(args.download)
