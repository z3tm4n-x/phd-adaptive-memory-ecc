"""Pinned T67 download/parser reuse; outputs only to T72/external cache."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile
import numpy as np

HERE = Path(__file__).resolve().parent
T67 = HERE.parent/'t67-goes-growth'
sys.path.insert(0, str(T67))
import analyze
import selection
from response import Response


def prepare(cache, pilot=False):
    cache.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((T67/'outputs/source_manifest.json').read_text())
    if pilot:
        manifest = {**manifest, 'files': [r for r in manifest['files'] if
                    (r['satellite']==19 and r['cadence_s']==60 and r['date']=='20260119') or
                    r['version']=='special_2_0_0']}
    verified = selection.download(manifest, cache/'raw', cache/('pilot_manifest.json' if pilot else 'verified_manifest.json'))
    response = Response()
    series = cache/('pilot_series' if pilot else 'series')
    series.mkdir(exist_ok=True)
    config_hash = hashlib.sha256((T67/'config.json').read_bytes()).hexdigest()
    source_code_hash = hashlib.sha256(b''.join((T67/n).read_bytes() for n in ['analyze.py','response.py','sgps.py','nc_reader.py'])).hexdigest()
    for sat in [16,18,19]:
        for cad in [60,300]:
            rows = [r for r in verified['files'] if r['satellite']==sat and r['cadence_s']==cad]
            if not rows: continue
            key = hashlib.sha256(json.dumps(sorted([(r['name'],r['sha256']) for r in rows])).encode()+config_hash.encode()+source_code_hash.encode()).hexdigest()
            path = series/f'g{sat}_{cad}.npz'
            ledger = path.with_suffix('.json')
            if path.exists() and ledger.exists() and json.loads(ledger.read_text()).get('key') == key:
                info=json.loads(ledger.read_text())
                checksum=hashlib.sha256(path.read_bytes()).hexdigest()
                if info.get('derived_sha256',checksum)!=checksum:
                    raise ValueError('Derived cache checksum mismatch: '+str(path))
                with zipfile.ZipFile(path) as z:
                    if z.testzip() is not None:raise ValueError('Derived array CRC mismatch')
                with np.load(path) as z:
                    if set(['time','main_loglog','core_only','screened','strict','core_strict','signature','file_index']) <= set(z.files):
                        if 'derived_sha256' not in info:
                            ledger.write_text(json.dumps({**info,'derived_sha256':checksum},indent=2)+'\n')
                        print(f'validated derived group G{sat}/{cad}', flush=True)
                        continue
            print(f'parse pinned group G{sat}/{cad}, {len(rows)} files', flush=True)
            group, audits = analyze.prepare_group(rows, cache/'raw', response)
            # Keep just the response and flags required by T72, not new physics.
            arrays = {k:group[k] for k in ['time','main_loglog','core_only','screened','strict','core_strict','signature','file_index']}
            analyze.save_series(path, arrays)
            ledger.write_text(json.dumps({'key':key,'files':len(rows),'bins':len(group['time']),
                'source_code_hash':source_code_hash,'T67_config_sha256':config_hash,
                'derived_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}, indent=2)+'\n')
    return verified, series


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--pilot',action='store_true')
    a=p.parse_args()
    prepare(a.cache,a.pilot)
