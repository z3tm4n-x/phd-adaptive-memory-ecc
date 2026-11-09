"""Reconstruct the pinned one-minute T67 selection on the actual PR419 T141 response."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import numpy as np
from prior import activate, EXPERIMENTS


def selected():
    data=json.loads((EXPERIMENTS/'t67-goes-growth/outputs/source_manifest.json').read_text(encoding='utf-8'))
    return [f for f in data['files'] if f['cadence_s']==60]


def execute(previous,cache,local,limit):
    activate(previous)
    import goes_profile as goes
    goes.DT=60  # fold() checks cadence and returns integer indices since 2017 on this grid.
    raw=cache/'raw';out=cache/'folded'
    raw.mkdir(parents=True,exist_ok=True);out.mkdir(exist_ok=True)
    local_files={p.name:p for p in local.rglob('*avg1m*.nc')} if local else {}
    rows=selected()
    if limit:rows=rows[:limit]
    def fetch(row):
        path=local_files.get(row['name'],raw/row['name'])
        if not path.exists():
            try:
                data=goes.get(row['url'])
                if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Different source SHA-256')
                tmp=path.with_suffix('.partial');tmp.write_bytes(data);tmp.replace(path)
            except (ValueError,OSError) as error:return row,None,str(error)
        with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
        if sha!=row['sha256']:return row,None,'Different source SHA-256'
        return row,path,None
    result={'ok':[],'errors':{}}
    for a in range(0,len(rows),32):
        with ThreadPoolExecutor(max_workers=8) as pool:
            for row,path,error in pool.map(fetch,rows[a:a+32]):
                if error:
                    result['errors'][row['name']]=error
                    continue
                target=out/(row['name']+'.npz')
                if not target.exists():
                    ids,values,audit=goes.fold(path)
                    assert audit['sha256']==row['sha256'] and audit['satellite']==row['satellite']
                    tmp=target.with_suffix('.partial.npz')
                    np.savez_compressed(tmp,index=ids,values=values);tmp.replace(target)
                result['ok'].append(row['name'])
        tmp=cache/'receipt.tmp.json'
        tmp.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        tmp.replace(cache/'receipt.json')
        print(f'{a+len(rows[a:a+32])}/{len(rows)} files, {len(result["errors"])} open',flush=True)
    if result['errors']:raise SystemExit('Unresolved source files; rerun to retry')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--previous',type=Path,required=True);p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--local',type=Path);p.add_argument('--limit',type=int)
    args=p.parse_args();execute(args.previous,args.cache,args.local,args.limit)
