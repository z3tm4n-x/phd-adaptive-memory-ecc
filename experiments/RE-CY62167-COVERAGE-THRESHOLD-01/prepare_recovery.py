"""Materialize exact historical inputs; no scientific calculation."""
import base64, hashlib, json, subprocess, zlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
BASE='64a7a1f436b2abd6997d37d14e6ce571e3a480c8'
HIST='96e6d724e8c8d79c63c91a00b753e6d4b1796c92'
ADD='7971484c4d054f521cc0086e2df6d4d0f63ed7b7'

def main():
    specs=[(ADD,'docs/research_gates/RE-CY62167-COVERAGE-THRESHOLD-01-INPUT-RECOVERY.md','recovery/ORCHESTRATOR_INPUT_RECOVERY.md','eb61e4eae2557f1ed62658a618c3edc137e3fb0e')]
    for name,sha in [('radar_converged.py','3302ab0648988a42f6a1892f52f844f20aee22b9'),('radar_adapter.py','8e706e5f2475542f1a6b7fd31e96df9752aa1f42'),('sigma_model.py','7988bea35dbcb106d4b178deb7dab2c7df03862a')]:
        specs.append((HIST,'experiments/RE-GOES19-PROTON-RATE-01/'+name,'recovery/historical/'+name,sha))
    specs.append((HIST,'experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv','recovery/historical/sigma_bit_experimental.csv','624c3e50526a6c9dbf5d534e6d600c56802df036'))
    for name in ['upstream_interface.py.zlib.b85','risk_bridge.py.zlib.b85','registered_direct_by_energy.csv']:
        specs.append((BASE,'experiments/RE-CY62167-ECC-RISK-BRIDGE-01/'+name,'recovery/historical/'+name,None))
    for name in ['goes19_adapter.py','rate_pipeline.py']:
        specs.append((BASE,'experiments/RE-GOES19-PROTON-RATE-01/'+name,'recovery/historical/'+name,None))
    entries=[]
    for commit,path,dest,expected in specs:
        raw=subprocess.check_output(['git','-C',str(REPO),'show',commit+':'+path])
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if expected and blob!=expected:raise ValueError(path)
        out=HERE/dest;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
        entries.append(dict(commit=commit,source_path=path,package_path=dest,git_blob=blob,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw)))
        if path.endswith('.zlib.b85'):
            decoded=zlib.decompress(base64.b85decode(raw));d=out.with_name(out.name.removesuffix('.zlib.b85'));d.write_bytes(decoded)
            entries.append(dict(derived_from=dest,package_path=str(d.relative_to(HERE)),sha256=hashlib.sha256(decoded).hexdigest(),bytes=len(decoded)))
    (HERE/'recovery/source_manifest.json').write_text(json.dumps(entries,indent=2)+'\n')
    print('materialized',len(entries),'source identities; no science executed')

if __name__=='__main__':main()
