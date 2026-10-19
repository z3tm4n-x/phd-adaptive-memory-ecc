"""Freeze/verify inherited source hashes; never updates accepted packages."""
import argparse,hashlib,json,platform,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def paths():
    roots=[REPO/'experiments/t105-arm-rule',REPO/'experiments/t104-rtl-resume']
    found=[]
    for root in roots:
        for p in root.rglob('*'):
            if any(x.startswith('.') for x in p.relative_to(root).parts):continue
            if p.is_file() and (p.suffix in ('.sv','.c','.h','.S','.ld','.tcl','.xdc','.py') or
                p.name in ('firmware.elf','startup.elf','startup_profile.json','full-top.json','route-reuse.json')):
                found.append(p)
    return sorted(found)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
    dest=HERE/'inputs.json'
    actual={str(p.relative_to(REPO)):sha(p) for p in paths()}
    if args.freeze:
        assert not dest.exists(),'do not silently re-freeze accepted inputs'
        dest.write_text(json.dumps({'base':'94f0b8ffb35e6840e1ff03e55e32989aa8ac4a7d',
          'issue_updated_at':'2026-10-14T09:08:05Z','accepted_source_sha256':actual},indent=2)+'\n')
    else:
        expected=json.loads(dest.read_text())['accepted_source_sha256']
        assert actual==expected,'accepted source changed'
    print('accepted inputs unchanged:',len(actual))
if __name__=='__main__':main()
