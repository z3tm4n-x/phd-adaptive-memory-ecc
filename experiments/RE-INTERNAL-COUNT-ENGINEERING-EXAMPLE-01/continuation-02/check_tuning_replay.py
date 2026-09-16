"""Replay every selected baseline tuning trial with final pre-test executor."""
import json,multiprocessing as mp
import numpy as np
from reference import ROOT,config
from run_experiment import batch,init_worker

def main():
    c=config();selection=json.loads((ROOT/'outputs/selected_policies.json').read_text());checked=0;difference=0.;hashes=0
    for case,name in enumerate(c['cases']):
        raw=np.load(ROOT/'outputs'/f'tune_{name}.npz');policies=np.array(selection[name]['policies'][2:]);indices=[]
        for p in policies:indices.append(int(np.flatnonzero(np.all(raw['policies']==p,axis=1))[0]))
        jobs=[('tune',case,i,min(i+20,len(raw['rows'])),policies) for i in range(0,len(raw['rows']),20)]
        with mp.Pool(6,initializer=init_worker) as pool:
            for begin,r,h,s in pool.imap_unordered(batch,jobs):
                old=raw['rows'][begin:begin+len(r)][:,indices]
                difference=max(difference,float(np.max(np.abs(old-r))))
                assert np.array_equal(h,raw['event_sha256'][begin:begin+len(r)])
                checked+=len(r)*len(policies);hashes+=len(h)
    result=dict(selected_baseline_trial_records_checked=checked,stream_hashes_checked=hashes,maximum_absolute_field_difference=difference,scope='reproduction with corrected boundary accounting; independent oracle is separate')
    (ROOT/'outputs/tuning_replay.json').write_text(json.dumps(result,indent=2)+'\n',newline='\n');print(json.dumps(result));assert difference==0

if __name__=='__main__':main()
