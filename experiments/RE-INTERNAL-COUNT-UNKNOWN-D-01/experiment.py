"""Separate pilot selection and never-retuned held-out paired evaluation."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,platform,sys,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy.stats import beta as beta_distribution,norm
import model,engine
from upstream import known_core,known_sim,verify

NAMES=['learning','frozen_uncertainty','Fixed','Precomputed','PA_DOM_one_setting','known_D_RES003_diagnostic']

def write_csv(path,rows):
    with Path(path).open('w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)

def upper(k,n,alpha=.05):
    return 1. if k==n else float(beta_distribution.ppf(1-alpha,k+1,n-k))

def two_sided(k,n):
    return (0. if k==0 else float(beta_distribution.ppf(.025,k,n-k+1)),1. if k==n else float(beta_distribution.ppf(.975,k+1,n-k)))

def hash_sources():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(model.ROOT.iterdir()) if p.suffix in ('.py','.json')}

def pilot_worker(arg):
    index,D=arg;cfg=model.config();sim=cfg['simulation'];packed=engine.known(D)
    policies=[[4,2,2,ms,cap,sim['analogue_growth'],sim['analogue_zero_mode']] for ms in sim['analogue_Ms'] for cap in sim['analogue_caps']]
    seed=sim['pilot_seed']+index*sim['seed_stride_per_dwell'];n=sim['pilot_trials_per_dwell'];start=time.perf_counter()
    data=known_sim.batch(packed,n,seed,policies);rows=[]
    for k,policy in enumerate(policies):
        failures=int(data[:,k,0].sum());surv=data[:,k,0]==0
        rows.append(dict(dwell=D,candidate=k,Ms=policy[3],cap=policy[4],growth=policy[5],zero_mode=policy[6],trials=n,seed=seed,
                         failures=failures,F=failures/n,upper95=upper(failures,n),passes_given_survival=float(data[surv,k,1].mean())))
    print('pilot complete',D,'seconds',time.perf_counter()-start,flush=True)
    return rows

def pilot(workers=4):
    cfg=model.config();out=model.ROOT/'outputs';out.mkdir(exist_ok=True);rows=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(pilot_worker,enumerate(cfg['simulation']['dwell_seconds'])):rows+=r
    candidates=[]
    for k in range(len(cfg['simulation']['analogue_Ms'])*len(cfg['simulation']['analogue_caps'])):
        records=sorted([r for r in rows if r['candidate']==k],key=lambda x:x['dwell'])
        if all(r['upper95']<=cfg['epsilon'] for r in records):
            vector=[r['passes_given_survival'] for r in records]
            candidates.append((max(vector),vector,records[0]['Ms'],records[0]['cap'],k))
    write_csv(out/'analogue_pilot.csv',rows)
    if not candidates:raise RuntimeError('No pilot candidate satisfies all fixed-point pilot screens; do not use held-out to tune')
    chosen=min(candidates)
    selected=dict(Ms=chosen[2],cap=chosen[3],growth=cfg['simulation']['analogue_growth'],zero_mode=cfg['simulation']['analogue_zero_mode'],
                  candidate=chosen[4],pilot_objective_max_survivor_passes=chosen[0],pilot_survivor_vector=chosen[1],eligible_candidates=len(candidates),
                  pilot_seed=cfg['simulation']['pilot_seed'],validation_seed=cfg['simulation']['validation_seed'],validation_used=False,
                  uniform_in_D_guarantee=False,selection_rule=cfg['simulation']['analogue_selection'],source_sha256=hash_sources())
    (out/'selected_analogue.json').write_text(json.dumps(selected,indent=2)+'\n');print(json.dumps(selected,indent=2),flush=True)
    return selected

def validation_worker(arg):
    index,D=arg;cfg=model.config();out=model.ROOT/'outputs';cache=model.ROOT/'cache';cache.mkdir(exist_ok=True)
    selected=json.loads((out/'selected_analogue.json').read_text())
    if selected['validation_used']:raise RuntimeError('Invalid pilot provenance')
    b=model.build(cfg);packed=engine.known(D);n=cfg['simulation']['validation_trials_per_dwell'];seed=cfg['simulation']['validation_seed']+index*cfg['simulation']['seed_stride_per_dwell']
    result=np.empty((n,6,12));start=time.perf_counter()
    for i in range(0,n,2000):
        last=min(n,i+2000)
        result[i:last]=engine.mixed_batch(last-i,seed+i,float(D),engine.payload(b),known_sim.args(packed),float(selected['Ms']),float(selected['cap']))
        print('held-out',D,last,'/',n,'seconds',round(time.perf_counter()-start,3),flush=True)
    if np.max(result[:,:2,1])>3600:raise AssertionError('Largest-feasible-action/backup invariant broken')
    np.savez_compressed(cache/f'heldout_{D}.npz',data=result,seed=seed,columns=np.array(engine.RESULT_COLUMNS))
    return dict(dwell=D,trials=n,seed=seed,seconds=time.perf_counter()-start,sha256=hashlib.sha256((cache/f'heldout_{D}.npz').read_bytes()).hexdigest())

def mask_summary(mask,rates):
    cells=[j for j in range(len(rates)-1) if int(mask)&(1<<j)]
    if not cells:return float('nan'),float('nan'),0,0.
    lower=1/rates[cells[-1]+1];upperD=1/rates[cells[0]]
    fraction=sum(math.log(rates[j+1]/rates[j]) for j in cells)/math.log(100.)
    return lower,upperD,len(cells),fraction

def contains_D(mask,D,rates):
    a=1/D
    return any((int(mask)&(1<<j)) and rates[j]-1e-14<=a<=rates[j+1]+1e-14 for j in range(len(rates)-1))

def summarize():
    cfg=model.config();out=model.ROOT/'outputs';cache=model.ROOT/'cache';rates=model.rate_grid(cfg)
    comparison=[];pairs=[];information=[];claims=[]
    for D in cfg['simulation']['dwell_seconds']:
        data=np.load(cache/f'heldout_{D}.npz')['data'];n=len(data)
        for k,name in enumerate(NAMES):
            failures=int(data[:,k,0].sum());surv=data[:,k,0]==0;v=data[surv,k,1];se=float(v.std(ddof=1)/math.sqrt(len(v)));ci=two_sided(failures,n)
            comparison.append(dict(dwell=D,policy=name,trials=n,failures=failures,F=failures/n,F_CI95_low=ci[0],F_CI95_high=ci[1],F_family95_upper=upper(failures,n,.05/30),
                                   survivors=int(surv.sum()),passes_given_survival=float(v.mean()),passes_CI95_low=float(v.mean()-1.96*se),passes_CI95_high=float(v.mean()+1.96*se),
                                   stop_passes_mean=float(data[:,k,1].mean()),busy_given_survival=float(data[surv,k,2].mean()),busy_stop_mean=float(data[:,k,2].mean()),
                                   reads_stop_mean=float(data[:,k,3].mean()),writes_stop_mean=float(data[:,k,4].mean()),updates_given_survival=float(data[surv,k,6].mean()),
                                   guarantee='uniform_continuum_certificate' if k<4 else 'finite_point_MC_only' if k==4 else 'known_parameter_diagnostic'))
        for k in range(1,6):
            both=(data[:,0,0]==0)&(data[:,k,0]==0);diff=data[both,k,1]-data[both,0,1];se=float(diff.std(ddof=1)/math.sqrt(len(diff)))
            risks=data[:,0,0]-data[:,k,0];rse=float(risks.std(ddof=1)/math.sqrt(n))
            pairs.append(dict(dwell=D,comparison=NAMES[k],common_survivors=int(both.sum()),saving_mean=float(diff.mean()),saving_CI95_low=float(diff.mean()-1.96*se),saving_CI95_high=float(diff.mean()+1.96*se),
                              risk_difference_learning_minus_other=float(risks.mean()),risk_diff_CI95_low=float(risks.mean()-1.96*rse),risk_diff_CI95_high=float(risks.mean()+1.96*rse),
                              stop_pass_saving=float((data[:,k,1]-data[:,0,1]).mean())))
        # Separate predeclared family: 10 individual survivor-mean bounds and
        # 5 common-survivor difference bounds, Hoeffding alpha=.05/15.
        alpha=.05/15;mean=[];radius=[]
        for k in (0,1):
            v=data[data[:,k,0]==0,k,1];mean.append(float(v.mean()));radius.append(3600*math.sqrt(math.log(1/alpha)/(2*len(v))))
        both=(data[:,0,0]==0)&(data[:,1,0]==0);diff=data[both,1,1]-data[both,0,1]
        paired_radius=7200*math.sqrt(math.log(1/alpha)/(2*len(diff)))
        claims.append(dict(dwell=D,individual_conditional_saving=mean[1]-mean[0],individual_family95_lower=mean[1]-mean[0]-sum(radius),
                           common_survivor_saving=float(diff.mean()),common_survivor_family95_lower=float(diff.mean()-paired_radius),
                           family_size=15,alpha_each=alpha,passes_bound_per_method=3600))
        surv=data[:,0,0]==0;sets=np.array([mask_summary(m,rates) for m in data[surv,0,7]])
        allmask=(1<<32)-1
        lost=np.array([not contains_D(m,D,rates) for m in data[:,0,7]])
        information.append(dict(dwell=D,surviving_missions=int(surv.sum()),fraction_survivors_with_smaller_set=float(np.mean(data[surv,0,7]!=allmask)),
                                median_set_hull_lower=float(np.nanmedian(sets[:,0])),median_set_hull_upper=float(np.nanmedian(sets[:,1])),median_retained_cells=float(np.median(sets[:,2])),
                                median_retained_log_range_fraction=float(np.median(sets[:,3])),median_first_shrink_time=float(np.median(data[surv,0,8])),
                                empty_sets_before_stop=int(data[:,0,9].sum()),true_D_absent_at_stop=int(lost.sum()),
                                interpretation='physical pre-stop diagnostic; not an unconditional auxiliary-coverage claim'))
    for name,rows in [('comparison.csv',comparison),('paired_comparison.csv',pairs),('learning_effect_family.csv',claims),('information_effect.csv',information)]:write_csv(out/name,rows)
    print('Final tables written; no retuning.',flush=True)
    return comparison,pairs,information,claims

def full(workers=4):
    cfg=model.config();out=model.ROOT/'outputs'
    if not (out/'verification.json').exists() or not (out/'numerical_certificate.json').exists():raise RuntimeError('Run deterministic certification and independent verification first')
    before=hash_sources();records=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(validation_worker,enumerate(cfg['simulation']['dwell_seconds'])):records.append(r)
    if before!=hash_sources():raise RuntimeError('Sources changed during held-out validation')
    results=summarize()
    report=dict(task=cfg['task_id'],base=cfg['base_commit'],completed=True,workers=workers,records=records,source_sha256=before,
                upstream_blobs=verify(),validation_tuned=False,python=sys.version,numpy=np.__version__,platform=platform.platform())
    (out/'execution_record.json').write_text(json.dumps(report,indent=2)+'\n');return results

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['pilot','full','summarize']);p.add_argument('--workers',type=int,default=4);args=p.parse_args()
    if args.stage=='pilot':pilot(args.workers)
    elif args.stage=='full':full(args.workers)
    else:summarize()
