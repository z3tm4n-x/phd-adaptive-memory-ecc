"""Separate pilot and untouched held-out paired actual-bit experiment.

The 27-point pilot grid is inherited from the saved refinement at e4ffac70.
No setting or controller parameter is chosen from validation outcomes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,platform,sys,time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy.stats import beta as beta_distribution
from model import ROOT,load_config,build_bank,rate_grid
from known_reference import build_known
from simulate import batch

NAMES=['learning','frozen_uncertainty','Fixed','Precomputed','PA_DOM_one_setting','known_D_RES003_diagnostic']

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ROOT.glob('*')) if p.suffix in ('.py','.json')}

def upper(k,n,alpha=.05):
    return 1. if k==n else float(beta_distribution.ppf(1-alpha,k+1,n-k))

def ci(k,n):
    return (0. if k==0 else float(beta_distribution.ppf(.025,k,n-k+1)),
            1. if k==n else float(beta_distribution.ppf(.975,k+1,n-k)))

def pilot_worker(arg):
    i,D=arg;cfg=load_config();sim=cfg['simulation'];b=build_bank(cfg);known=build_known(cfg,D)
    policies=[[4,ms,cap,sim['analogue_growth']] for ms in sim['analogue_Ms'] for cap in sim['analogue_caps']]
    seed=sim['pilot_seed']+i*sim['seed_stride_per_dwell'];n=sim['pilot_trials_per_dwell'];start=time.perf_counter()
    data=batch(b,known,D,n,seed,policies);rows=[]
    for j,p in enumerate(policies):
        fail=int(data[:,j,0].sum());surv=data[:,j,0]==0
        rows.append(dict(dwell=D,candidate=j,Ms=p[1],cap=p[2],growth=p[3],zero_mode=1,trials=n,seed=seed,
                         failures=fail,F=fail/n,upper95=upper(fail,n),passes_given_survival=float(data[surv,j,1].mean())))
    print('pilot complete',D,'seconds',time.perf_counter()-start,flush=True);return rows

def pilot(workers=4):
    cfg=load_config();rows=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(pilot_worker,enumerate(cfg['simulation']['dwell_seconds'])):rows+=r
    write_csv(ROOT/'outputs'/'analogue_pilot.csv',rows);eligible=[]
    for j in range(len(cfg['simulation']['analogue_Ms'])*len(cfg['simulation']['analogue_caps'])):
        r=sorted([x for x in rows if x['candidate']==j],key=lambda x:x['dwell'])
        if all(x['upper95']<=cfg['epsilon'] for x in r):
            v=[x['passes_given_survival'] for x in r];eligible.append((max(v),v,r[0]['Ms'],r[0]['cap'],j))
    if not eligible:raise RuntimeError('No eligible pilot setting; never tune on held-out')
    x=min(eligible);chosen=dict(Ms=x[2],cap=x[3],growth=cfg['simulation']['analogue_growth'],zero_mode=1,
        candidate=x[4],max_survivor_passes=x[0],survivor_vector=x[1],eligible_candidates=len(eligible),
        pilot_seed=cfg['simulation']['pilot_seed'],validation_seed=cfg['simulation']['validation_seed'],
        validation_used=False,uniform_in_D_guarantee=False,source_sha256=hashes(),selection_rule=cfg['simulation']['analogue_selection'])
    (ROOT/'outputs'/'selected_analogue.json').write_text(json.dumps(chosen,indent=2)+'\n')
    print(json.dumps(chosen,indent=2),flush=True);return chosen

def validation_worker(arg):
    i,D=arg;cfg=load_config();sim=cfg['simulation'];selected=json.loads((ROOT/'outputs'/'selected_analogue.json').read_text())
    if selected['validation_used']:raise RuntimeError('Invalid pilot provenance')
    b=build_bank(cfg);known=build_known(cfg,D);n=sim['validation_trials_per_dwell'];seed=sim['validation_seed']+i*sim['seed_stride_per_dwell']
    policies=[[0,0,0,0],[1,0,0,0],[2,0,0,0],[3,0,0,0],
              [4,selected['Ms'],selected['cap'],selected['growth']],[5,0,0,0]]
    start=time.perf_counter();data=np.empty((n,6,10))
    for k in range(0,n,2000):
        end=min(k+2000,n);data[k:end]=batch(b,known,D,end-k,seed+k,policies)
        print('held-out',D,end,'/',n,'seconds',round(time.perf_counter()-start,3),flush=True)
    if data[:,:2,1].max()>3600:raise AssertionError('Backup/largest-action invariant')
    path=ROOT/'cache'/f'heldout_{D}.npz';path.parent.mkdir(exist_ok=True)
    np.savez_compressed(path,data=data,seed=seed)
    return dict(dwell=D,seed=seed,trials=n,seconds=time.perf_counter()-start,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def summarize():
    cfg=load_config();comparison=[];pairs=[];family=[];info=[]
    for D in cfg['simulation']['dwell_seconds']:
        data=np.load(ROOT/'cache'/f'heldout_{D}.npz')['data'];n=len(data)
        for j,name in enumerate(NAMES):
            fail=int(data[:,j,0].sum());surv=data[:,j,0]==0;v=data[surv,j,1];se=float(v.std(ddof=1)/math.sqrt(len(v)));lo,hi=ci(fail,n)
            comparison.append(dict(dwell=D,policy=name,trials=n,failures=fail,F=fail/n,F_CI95_low=lo,F_CI95_high=hi,F_family95_upper=upper(fail,n,.05/30),
                survivors=int(surv.sum()),passes_given_survival=float(v.mean()),passes_CI95_low=float(v.mean()-1.96*se),passes_CI95_high=float(v.mean()+1.96*se),
                stop_passes_mean=float(data[:,j,1].mean()),busy_given_survival=float(data[surv,j,2].mean()),busy_stop_mean=float(data[:,j,2].mean()),
                reads_stop_mean=float(data[:,j,3].mean()),writes_stop_mean=float(data[:,j,4].mean()),updates_given_survival=float(data[surv,j,6].mean()),
                guarantee='uniform_continuum_certificate' if j<4 else 'finite_point_MC_only' if j==4 else 'known_parameter_diagnostic'))
        for j in range(1,6):
            both=(data[:,0,0]==0)&(data[:,j,0]==0);v=data[both,j,1]-data[both,0,1];se=float(v.std(ddof=1)/math.sqrt(len(v)))
            risk=data[:,0,0]-data[:,j,0];rse=float(risk.std(ddof=1)/math.sqrt(n))
            pairs.append(dict(dwell=D,comparison=NAMES[j],common_survivors=int(both.sum()),saving_mean=float(v.mean()),saving_CI95_low=float(v.mean()-1.96*se),saving_CI95_high=float(v.mean()+1.96*se),
                risk_difference_learning_minus_other=float(risk.mean()),risk_diff_CI95_low=float(risk.mean()-1.96*rse),risk_diff_CI95_high=float(risk.mean()+1.96*rse),
                stop_pass_saving=float((data[:,j,1]-data[:,0,1]).mean())))
        alpha=.05/15;means=[];radius=[]
        for j in [0,1]:
            v=data[data[:,j,0]==0,j,1];means.append(float(v.mean()));radius.append(3600*math.sqrt(math.log(1/alpha)/(2*len(v))))
        both=(data[:,0,0]==0)&(data[:,1,0]==0);v=data[both,1,1]-data[both,0,1]
        pr=7200*math.sqrt(math.log(1/alpha)/(2*len(v)))
        family.append(dict(dwell=D,individual_conditional_saving=means[1]-means[0],individual_family95_lower=means[1]-means[0]-sum(radius),
            common_survivor_saving=float(v.mean()),common_survivor_family95_lower=float(v.mean()-pr),family_size=15,alpha_each=alpha,passes_bound_per_method=3600))
        surv=data[:,0,0]==0;first=data[surv,0,8];rates=rate_grid(cfg);allmask=(1<<32)-1
        stats=[];lost=0
        for index,mask0 in enumerate(data[:,0,7]):
            mask=int(mask0);cells=[j for j in range(32) if mask&(1<<j)]
            contains=any(rates[j]-1e-14<=1/D<=rates[j+1]+1e-14 for j in cells)
            if not contains:lost+=1
            if surv[index]:
                stats.append([1/rates[cells[-1]+1],1/rates[cells[0]],len(cells),sum(math.log(rates[j+1]/rates[j]) for j in cells)/math.log(100.)] if cells else [np.nan,np.nan,0,0.])
        stats=np.array(stats)
        info.append(dict(dwell=D,survivors=int(surv.sum()),fraction_with_smaller_D_set=float(np.mean(data[surv,0,7]!=allmask)),
            median_set_hull_lower=float(np.nanmedian(stats[:,0])),median_set_hull_upper=float(np.nanmedian(stats[:,1])),
            median_retained_cells=float(np.median(stats[:,2])),median_retained_log_fraction=float(np.median(stats[:,3])),
            median_first_shrink_time=float(np.median(first[first>=0])) if np.any(first>=0) else None,
            empty_sets_before_stop=int(np.sum(data[:,0,9]>=0)),true_D_absent_at_stop=lost,
            note='physical pre-stop diagnostic, not unconditional auxiliary coverage'))
    for name,rows in [('comparison.csv',comparison),('paired_comparison.csv',pairs),('learning_effect_family.csv',family),('information_effect.csv',info)]:
        write_csv(ROOT/'outputs'/name,rows)
    return comparison,pairs,family,info

def full(workers=4):
    cfg=load_config()
    for file in ['tests.json','numeric_witness.json','selected_analogue.json','continuum_witness.json']:
        if not (ROOT/'outputs'/file).exists():raise RuntimeError('Missing prerequisite '+file)
    before=hashes();records=[]
    (ROOT/'outputs'/'validation_lock.json').write_text(json.dumps(dict(source_sha256=before,
        pilot_selection_sha256=hashlib.sha256((ROOT/'outputs'/'selected_analogue.json').read_bytes()).hexdigest(),
        validation_seed=cfg['simulation']['validation_seed'],retuning_permitted=False),indent=2)+'\n')
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(validation_worker,enumerate(cfg['simulation']['dwell_seconds'])):records.append(r)
    if before!=hashes():raise RuntimeError('Executable sources changed during held-out')
    summarize()
    (ROOT/'outputs'/'execution_record.json').write_text(json.dumps(dict(task=cfg['task_id'],base=cfg['base_commit'],completed=True,
        records=records,source_sha256=before,workers=workers,validation_tuned=False,python=sys.version,numpy=np.__version__,platform=platform.platform()),indent=2)+'\n')
    print('HELD-OUT COMPLETED: 100000 paired missions, 600000 policy executions; no retuning.',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['pilot','full','summarize']);parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if args.stage=='pilot':pilot(args.workers)
    elif args.stage=='full':full(args.workers)
    else:summarize()
