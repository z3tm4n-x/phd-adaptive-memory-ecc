"""Reproduce the bounded study, without altering canonical inputs."""
import argparse,hashlib,json,platform,sys,time
from pathlib import Path
import numpy as np,scipy,numba,mpmath
import model,certify,baselines,verification,diagnostics,experiment
from upstream import verify

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');parser.add_argument('--retune',action='store_true');parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args();start=time.perf_counter();verify()
    certify.run();baselines.run();verification.run();diagnostics.run()
    if args.retune:experiment.pilot(args.workers)
    if args.full:experiment.full(args.workers)
    root=Path(__file__).resolve().parent
    manifest=dict(task=model.config()['task_id'],base=model.config()['base_commit'],full=args.full,retune=args.retune,elapsed_seconds=time.perf_counter()-start,
                  environment=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,numba=numba.__version__,mpmath=mpmath.__version__,platform=platform.platform()),
                  upstream_blobs=verify(),source_sha256=experiment.hash_sources(),output_sha256={})
    for p in sorted((root/'outputs').iterdir()):
        if p.is_file() and p.suffix in ('.json','.csv') and p.name!='manifest.json':manifest['output_sha256'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (root/'outputs'/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Reproduction completed. No SR PASS or RES promotion assigned.')
if __name__=='__main__':main()
