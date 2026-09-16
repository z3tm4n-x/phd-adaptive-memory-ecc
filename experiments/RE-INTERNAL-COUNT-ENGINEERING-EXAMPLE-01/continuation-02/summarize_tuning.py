"""Compact complete candidate scores; preserve excluded candidates and cache hashes."""
import csv,hashlib,json
import numpy as np
from scipy.stats import beta
from reference import ROOT,config

def main():
    c=config();scores=[];manifest=[]
    for case in c['cases']:
        path=ROOT/'outputs'/f'tune_{case}.npz';raw=np.load(path);r=raw['rows'];n=len(r)
        for j,p in enumerate(raw['policies']):
            k=int(r[:,j,0].sum());alive=r[:,j,0]==0
            scores.append(dict(case=case,candidate=j,kind=int(p[0]),first_period=c['periods_seconds'][int(p[1])],second_period=c['periods_seconds'][int(p[2])],Ms=p[3],cap=p[4],growth=p[5],zero_mode=p[6],N=n,failures=k,F=k/n,upper95=1. if k==n else beta.ppf(.95,k+1,n-k),survivors=int(alive.sum()),survivor_reservation_s=float(r[alive,j,7].mean()) if alive.any() else float('nan')))
        manifest.append(dict(case=case,cache_path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size,regeneration='run_experiment.py tune --workers 6 --batch-size 10',published_scores='tuning_candidates.csv',development_only=True))
    with (ROOT/'outputs/tuning_candidates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(scores[0]));w.writeheader();w.writerows(scores)
    (ROOT/'outputs/tuning_cache_provenance.json').write_text(json.dumps(manifest,indent=2)+'\n',newline='\n')
    print(f'{len(scores)} candidate rows')

if __name__=='__main__':main()
