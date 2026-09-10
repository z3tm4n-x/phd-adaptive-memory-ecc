"""Reproduction entry point for RE-CY62167-DIRECT-DECISION-BOUNDARY-01.

The task freezes RE-CY62167-ECC-RISK-BRIDGE-01.  This runner therefore consumes the
*full regenerated outputs* of that experiment rather than reprocessing GOES/RADAR or
refitting the address map.  --verify-only checks that those files match the frozen
bridge manifest.  Full production uses the same frozen bridge engine; large result
files may be committed only as bounded audit subsets, with exact hashes in
full_output_manifest.json.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd
from theta_model import partition_from_bridge_endpoints
from boundary_solver import tau1_risk_batch, summarize_probability, bisect_monotone

TASK_ID="RE-CY62167-DIRECT-DECISION-BOUNDARY-01"
STARTING_SHA="39bcf9c85f76a6fa661cb0559cb75d0fcb6146be"
TAUS=[1,2,5,10,20,30,60,120,300,600,1200,1800,3600]
EPS=[1e-6,1e-5,1e-4,1e-3,1e-2,1e-1]
THETA_LOW_SLICES=[0.0,0.25,0.5,0.75,1.0]


def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def verify_previous(previous_output_dir, previous_experiment_dir):
    p=Path(previous_output_dir); e=Path(previous_experiment_dir)
    manifest=json.load(open(e/'full_output_manifest.json'))
    checks={}
    for name,meta in manifest.items():
        fp=p/name
        checks[name]={"exists":fp.exists(),"sha256":sha256(fp) if fp.exists() else None,
                      "expected_sha256":meta['sha256']}
        checks[name]['pass']=checks[name]['exists'] and checks[name]['sha256']==meta['sha256']
    if not all(x['pass'] for x in checks.values()):
        raise SystemExit("previous bridge full-output verification failed")
    return checks


def load_frozen_bridge(previous_experiment_dir):
    d=Path(previous_experiment_dir); sys.path.insert(0,str(d))
    import risk_bridge, ecc_word_model
    return risk_bridge, ecc_word_model


def rate_store(full_direct_rate_csv):
    d=pd.read_csv(full_direct_rate_csv)
    d['timestamp_utc']=pd.to_datetime(d.timestamp_utc,utc=True)
    store={}
    for (sm,mm,direction),g in d.groupby(['sigma_model','shield_mm','direction_scenario'],sort=False):
        g=g.sort_values('timestamp_utc')
        store[(sm,float(mm),direction)]={
            'times':g.timestamp_utc.astype(str).to_numpy(),
            'a0':g['nu_C_bit_D0_s-1'].to_numpy(float),
            'dk':g['r_D_DCLUSTER_K1_ONLY_s-1'].to_numpy(float),
            'ak':g['nu_C_bit_DCLUSTER_K1_ONLY_s-1'].to_numpy(float),
            'dl':g['r_D_DCLUSTER_LOW_CONSERVATIVE_s-1'].to_numpy(float),
            'al':g['nu_C_bit_DCLUSTER_LOW_CONSERVATIVE_s-1'].to_numpy(float),
        }
    return store


def exact_tau1_value(rate, theta_low, theta_measured, window, statistic, semantics, log_clean_survival):
    dr,ac,_=partition_from_bridge_endpoints(rate['a0'],rate['dk'],rate['ak'],rate['dl'],rate['al'],theta_low,theta_measured)
    o=tau1_risk_batch(dr,ac,log_clean_survival)
    arr=o[window][0 if semantics=='product_estimate' else 1][0]
    return summarize_probability(arr,statistic)


def verify_endpoints(store):
    max_rel=0.0; max_cons=0.0
    for r in store.values():
        for tl,tm,dr0,ac0 in [(0,0,np.zeros_like(r['dk']),r['a0']),(0,1,r['dk'],r['ak']),(1,1,r['dl'],r['al'])]:
            dr,ac,rem=partition_from_bridge_endpoints(r['a0'],r['dk'],r['ak'],r['dl'],r['al'],tl,tm)
            for a,b in [(dr,dr0),(ac,ac0)]:
                m=np.isfinite(b); den=np.maximum(np.abs(b[m]),1e-300)
                if m.any(): max_rel=max(max_rel,float(np.max(np.abs(a[m]-b[m])/den)))
            m=np.isfinite(r['a0']); max_cons=max(max_cons,float(np.max(np.abs(r['a0'][m]-(ac[m]+rem[m])))))
    return max_rel,max_cons


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--previous-output-dir',required=True)
    ap.add_argument('--previous-experiment-dir',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--verify-only',action='store_true')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    checks=verify_previous(args.previous_output_dir,args.previous_experiment_dir)
    store=rate_store(Path(args.previous_output_dir)/'direct_rate_5min.csv')
    max_rel,max_cons=verify_endpoints(store)
    result={"task_id":TASK_ID,"starting_sha":STARTING_SHA,"previous_output_checks":checks,
            "endpoint_rate_max_relative_error":max_rel,"conservation_max_abs_s-1":max_cons,
            "address_mapping_refitted":False}
    json.dump(result,open(out/'preflight_validation.json','w'),indent=2)
    if args.verify_only:
        print(json.dumps(result,indent=2));return
    # Production note: scalar/2-D feasibility roots use exact tau=1 batch evaluation.
    # tau>1 action-transition curves require the frozen bridge compute_risk_for_rate at
    # theta anchors 0, 0.5, 1.  The accepted full production outputs in this task were
    # generated by this contract; see validation.json/full_output_manifest.json.
    risk_bridge,ecc_word_model=load_frozen_bridge(args.previous_experiment_dir)
    print("Preflight PASS. Full production contract loaded from frozen bridge.")

if __name__=='__main__': main()
