#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math
from datetime import datetime,timedelta
from decimal import Decimal
from pathlib import Path

def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def dt(s): return datetime.fromisoformat(s)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--upstream',required=True); ap.add_argument('--out',required=True); ap.add_argument('--manifest',required=True); a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text()); u=Path(a.upstream); exp=cfg['upstream_rate']
    got=sha256(u)
    if got!=exp['sha256']: raise SystemExit(f'upstream SHA mismatch: {got}')
    with u.open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
    if len(rows)!=exp['data_rows']: raise SystemExit(f'upstream row count mismatch: {len(rows)}')
    col=exp['column']; required={'timestamp_utc',col}
    if not required.issubset(rows[0]): raise SystemExit('required columns missing')
    t0=dt(cfg['slice']['start_utc']); end=t0+timedelta(seconds=cfg['slice']['horizon_s']); nbits=Decimal(cfg['slice']['data_bits_total'])
    selected=[]; seen=set()
    for r in rows:
        t=dt(r['timestamp_utc'])
        if t0<=t<end:
            if t in seen: raise SystemExit('duplicate timestamp')
            seen.add(t)
            try: nu=Decimal(r[col])
            except Exception as e: raise SystemExit(f'invalid rate at {t}: {e}')
            if not nu.is_finite() or nu<0: raise SystemExit(f'negative/nonfinite rate at {t}')
            selected.append((t,nu))
    selected.sort()
    expected=cfg['slice']['horizon_s']//cfg['slice']['bin_s']
    if len(selected)!=expected: raise SystemExit(f'selected row count {len(selected)} != {expected}')
    if selected[0][0]!=t0 or selected[-1][0]!=end-timedelta(seconds=cfg['slice']['bin_s']): raise SystemExit('selected endpoint mismatch')
    for (ta,_),(tb,_) in zip(selected,selected[1:]):
        if (tb-ta).total_seconds()!=cfg['slice']['bin_s']: raise SystemExit(f'gap/non-300s step: {ta} -> {tb}')
    out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['timestamp_utc','duration_s','nu_C_bit_DREG_s-1','r_per_bit_s-1'])
        for t,nu in selected:
            r=nu/nbits
            w.writerow([t.isoformat(),cfg['slice']['bin_s'],format(nu,'f'),format(r,'f')])
    man={'task':cfg['task'],'source_kind':'source-equivalent selected slice from exact frozen upstream whole-device rate','upstream_path':exp['path'],'upstream_sha256':got,'upstream_git_blob':exp['git_blob'],'upstream_rows':len(rows),'selected_start':selected[0][0].isoformat(),'selected_end_exclusive':end.isoformat(),'selected_rows':len(selected),'bin_s':cfg['slice']['bin_s'],'selected_output_sha256':sha256(out),'normalization':'nu_C_bit_DREG_s-1=d10_lambda_central_s-1; r=nu/2^24','historical_direct_rate_full_bytes_used':False}
    Path(a.manifest).write_text(json.dumps(man,indent=2,sort_keys=True)+'\n')
if __name__=='__main__': main()
