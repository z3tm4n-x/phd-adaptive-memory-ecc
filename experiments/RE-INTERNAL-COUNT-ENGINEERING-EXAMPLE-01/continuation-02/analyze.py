"""Preregistered paired analysis, resource vector and article-ready figures."""
import csv, json, math
import numpy as np
from scipy.stats import beta,t
from reference import ROOT,config,packed,accepted
import engine

NAMES=['Proposed','Count-disabled','Fixed','Precomputed','PA-DOM']
def cp(k,n,a=.05):
    return [0. if k==0 else float(beta.ppf(a/2,k,n-k+1)),1. if k==n else float(beta.ppf(1-a/2,k+1,n-k))]
def mean_ci(x,a=.05):
    if len(x)<2:return [float('nan')]*3
    m=float(np.mean(x));d=float(t.ppf(1-a/2,len(x)-1)*np.std(x,ddof=1)/np.sqrt(len(x)))
    return [m,m-d,m+d]
def paired_risk(x,y,a):
    plus=int(np.sum((x==1)&(y==0)));minus=int(np.sum((x==0)&(y==1)));n=len(x)
    p=cp(plus,n,a/2);m=cp(minus,n,a/2)
    return [(plus-minus)/n,p[0]-m[1],p[1]-m[0]],[[int(np.sum((x==i)&(y==j))) for j in range(2)] for i in range(2)]
def ratio_ci(x,y,a):
    if len(x)<2 or np.mean(y)<=0:return [float('nan')]*3
    r=np.mean(x)/np.mean(y);influence=-(x-r*y)/np.mean(y)
    width=t.ppf(1-a/2,len(x)-1)*np.std(influence,ddof=1)/np.sqrt(len(x))
    return [float(1-r),float(1-r-width),float(1-r+width)]
def save_csv(name,rows):
    with (ROOT/'outputs'/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    c=config();a=c['statistics']['family_alpha']/c['statistics']['family_size'];epsilon=c['epsilon'][0]
    policy_rows=[];pair_rows=[];results={}
    for case in c['cases']:
        raw=np.load(ROOT/'outputs'/f'test_{case}.npz');v=raw['rows'];n=len(v);policies=[];pairs=[]
        assert n==c['simulation']['validation_trials'] and v[:,:,11].sum()==0
        for i,name in enumerate(NAMES):
            x=v[:,i];surv=x[:,0]==0;k=int(x[:,0].sum());ci=cp(k,n,a);nominal=cp(k,n)
            resource=mean_ci(x[surv,7]);passes=mean_ci(x[surv,2]);status='supports_requirement' if ci[1]<=epsilon else ('supports_violation' if ci[0]>epsilon else 'unresolved')
            row=dict(case=case,policy=name,N=n,failures=k,F=k/n,F95_low=nominal[0],F95_high=nominal[1],F95_upper=1. if k==n else float(beta.ppf(.95,k+1,n-k)),family_low=ci[0],family_high=ci[1],status=status,survivors=int(surv.sum()),survivor_reservation_s=resource[0],survivor_reservation95_low=resource[1],survivor_reservation95_high=resource[2],survivor_passes=passes[0],survivor_passes95_low=passes[1],survivor_passes95_high=passes[2],stop_reservation_s=float(x[:,7].mean()),stop_complete_passes=float(x[:,2].mean()),stop_partial_pass_equivalent=float(x[:,3].mean()),stop_read_transactions=float(x[:,4].mean()),stop_completed_writes=float(x[:,5].mean()),stop_actual_bus_s=float(x[:,6].mean()),survivor_read_transactions=float(x[surv,4].mean()),survivor_completed_writes=float(x[surv,5].mean()),survivor_actual_bus_s=float(x[surv,6].mean()),survivor_updates=float(x[surv,8].mean()),survivor_average_service_reservation_fraction=resource[0]/c['horizon_seconds'],minimum_likelihood=float(x[:,10].min()),computational_failures=int(x[:,11].sum()))
            policies.append(row);policy_rows.append(row)
        for j in range(1,5):
            J=(v[:,0,0]==0)&(v[:,j,0]==0);risk,table=paired_risk(v[:,0,0],v[:,j,0],a)
            d=mean_ci(v[J,0,7]-v[J,j,7],a);G=ratio_ci(v[J,0,7],v[J,j,7],a)
            updates=float(v[J,0,8].mean()) if J.any() else float('nan')
            saving=-d[0];allowed=saving/updates if updates>0 else float('nan')
            row=dict(case=case,comparator=NAMES[j],both_survive=table[0][0],only_comparator_fails=table[0][1],only_proposed_fails=table[1][0],both_fail=table[1][1],risk_difference=risk[0],risk_difference_low=risk[1],risk_difference_high=risk[2],J=int(J.sum()),proposed_reservation_J=float(v[J,0,7].mean()),other_reservation_J=float(v[J,j,7].mean()),reservation_difference=d[0],reservation_difference_low=d[1],reservation_difference_high=d[2],G=G[0],G_low=G[1],G_high=G[2],saving_s_per_proposed_update=allowed,saving_lower_s_per_proposed_update=-d[2]/updates if updates>0 else float('nan'),meaningful_effect=('established' if G[1]>=.1 else 'below_10_percent' if G[2]<.1 else 'unresolved'),resource_precision_sufficient=bool(J.sum()>=100))
            pairs.append(row);pair_rows.append(row)
        results[case]=dict(policies=policies,pairs=pairs)
    save_csv('policy_comparison.csv',policy_rows);save_csv('paired_comparison.csv',pair_rows)
    (ROOT/'outputs/analysis.json').write_text(json.dumps(dict(alpha_each=a,resource_intervals='asymptotic',results=results),indent=2)+'\n',newline='\n')
    figures(c,results)
    print(json.dumps({case:[(r['policy'],r['F'],r['family_low'],r['family_high'],r['survivor_reservation_s']) for r in val['policies']] for case,val in results.items()},indent=2))

def figures(c,results):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=ROOT/'figures';out.mkdir(exist_ok=True)
    fig,axes=plt.subplots(1,3,figsize=(12,4),constrained_layout=True)
    for ax,(case,value) in zip(axes,results.items()):
        for row in value['policies']:
            ax.errorbar(row['survivor_reservation_s'],row['F'],xerr=[[row['survivor_reservation_s']-row['survivor_reservation95_low']],[row['survivor_reservation95_high']-row['survivor_reservation_s']]],yerr=[[row['F']-row['family_low']],[row['family_high']-row['F']]],fmt='o',label=row['policy'])
        ax.axhline(.1,color='black',ls='--',lw=.8);ax.set_title(case);ax.set_xlabel('Service reservation, s | own survival');ax.set_ylabel('P(first capability exceedance)')
    axes[0].legend(fontsize=8);fig.savefig(out/'risk_resource.png',dpi=170);plt.close(fig)
    s=engine.stream(c['simulation']['illustration_seed'],0,0,c);p=packed()
    r,tr=engine.run(*s[:4],np.array([0,0,0,0.,0.,0.,0.]),accepted.args(p),c['executor']['latch_before_commit_seconds'],True)
    np.savez_compressed(ROOT/'outputs/illustration.npz',trace=tr,segments=s[5],result=r,event_sha256=s[4])
    fig,axes=plt.subplots(3,1,figsize=(10,6),sharex=True,constrained_layout=True)
    for start,end,z,rate in s[5]:axes[0].plot([start,end],[rate,rate],color='tab:blue')
    axes[0].set_ylabel('Group arrivals / s\n(all chips)')
    axes[1].step(tr[:,2],tr[:,3],where='post');axes[1].set_ylabel('Own completed count')
    axes[2].step(tr[:,0],tr[:,1],where='post');axes[2].set_ylabel('Chosen period, s');axes[2].set_xlabel('Relative time, s')
    if r[0]:
        for ax in axes:ax.axvline(r[1],color='red',ls='--')
    fig.suptitle('Preregistered illustration seed; no selection for visual effect')
    fig.savefig(out/'illustration.png',dpi=170);plt.close(fig)

if __name__=='__main__':main()
