"""Independent physical killed model and bounded falsification checks.

The physical oracle uses no auxiliary observation kernel. It enumerates a
joint distribution of mode, actual dirty-word mask and actual correction
count, keeping all surviving mass unnormalized. The policy is necessarily
shared as the object under test, not its physical probability law.
"""
from __future__ import annotations
import copy,json,math,time
import numpy as np
from scipy.linalg import expm
from numba import njit
import model,engine
from upstream import known_core,known_sim


def small_aux_scan(W,P,rate,lo,hi):
    """Piecewise-exact independent generator for C0/+,K0/+ and K moments."""
    probabilities=np.zeros((2,8));probabilities[0,0]=probabilities[1,1]=1
    moments=np.zeros((2,8));moments[0,0]=moments[1,1]=1
    for scanned in range(W):
        f=scanned/W;Q=np.zeros((8,8));C=np.zeros((4,4));R=np.zeros((4,4))
        for c in range(2):
            for k in range(2):
                for z,b in enumerate((lo,hi)):
                    i=z+2*k+4*c;Q[i,(1-z)+2*k+4*c]+=rate;Q[i,i]-=rate
                    if c==0:Q[i,z+2*k+4]+=b*(1-f);Q[i,i]-=b*(1-f)
                    if k==0:Q[i,z+2+4*c]+=b*f;Q[i,i]-=b*f
        for c in range(2):
            for z,b in enumerate((lo,hi)):
                i=z+2*c;C[i,1-z+2*c]+=rate;C[i,i]-=rate
                if c==0:C[i,z+2]+=b*(1-f);C[i,i]-=b*(1-f)
                R[i,i]=b*f
        A=np.block([[C,R],[np.zeros((4,4)),C]])
        probabilities=probabilities@expm(Q*P/W);moments=moments@expm(A*P/W)
    out=np.zeros((2,2,6))
    for z in range(2):
        for zz in range(2):
            out[z,zz]=[probabilities[z,zz],probabilities[z,zz+2],probabilities[z,zz+4],probabilities[z,zz+6],moments[z,zz+4],moments[z,zz+6]]
    return out

def toy_bank():
    cfg=copy.deepcopy(model.config())
    cfg['memory'].update(words=2,bits_per_word=32,pass_seconds=.1,reads_per_pass=8,writes_per_pass=8)
    cfg['environment'].update(b_low=.02,b_high=.4,dwell_interval_seconds=[3,300])
    cfg['horizon_seconds']=6;cfg['epsilon']=.25;cfg['periods_seconds']=[1,2,3]
    rates=model.rate_grid(cfg)*10;periods=np.array(cfg['periods_seconds'],float);ticks=(periods*10).astype(np.int64)
    K=np.empty((33,3,2,4,6))
    for j,a in enumerate(rates):
        sc=small_aux_scan(2,.1,a,.02,.4)
        for action,h in enumerate(periods):
            Q=np.zeros((4,4))
            for c in range(2):
                for z,b in enumerate((.02,.4)):
                    i=z+2*c;Q[i,1-z+2*c]=a;Q[i,i]=-a
                    if c==0:Q[i,z+2]=b;Q[i,i]-=b
            idle=expm(Q*(h-.1))[:2].reshape(2,2,2)
            K[j,action]=model.combine(idle,sc)
    T,J,f,s,V=model.value_tables(rates,periods,ticks,K,60,.1,.02,.4,2,0)
    cc=cfg['controller'];budget=(cfg['epsilon']-cc['beta'])/cc['continuous_transfer_factor']-cc['numerical_allowance']
    slack=budget-.5*(V[:,-1,0]+V[:,-1,1])
    if slack.min()<0:raise AssertionError('toy backup infeasible')
    return model.Bank(cfg,rates,K,T,J,f,s,V,slack,periods,ticks,np.zeros(33),0.)

class PhysicalOracle:
    def __init__(self,bank,true_d):
        self.bank=bank;self.W=bank.cfg['memory']['words'];self.P=bank.cfg['memory']['pass_seconds'];self.dim=2**self.W
        self.Q=np.zeros((2*self.dim,2*self.dim));self.cache={};self.nodes=0;self.leaves=0
        lo=bank.cfg['environment']['b_low'];hi=bank.cfg['environment']['b_high'];n=bank.cfg['memory']['bits_per_word']
        for z,b in enumerate((lo,hi)):
            for mask in range(self.dim):
                i=z*self.dim+mask;self.Q[i,(1-z)*self.dim+mask]=1/true_d;self.Q[i,i]-=1/true_d
                for w in range(self.W):
                    if mask&(1<<w):
                        self.Q[i,z*self.dim+(mask^(1<<w))]+=b/(self.W*n)
                        self.Q[i,i]-=b/self.W # Remaining rate is irreversibly killed.
                    else:
                        self.Q[i,z*self.dim+(mask|(1<<w))]+=b/self.W;self.Q[i,i]-=b/self.W
    def exp(self,h):
        key=round(h,12)
        if key not in self.cache:self.cache[key]=expm(self.Q*h)
        return self.cache[key]
    def pass_map(self,v,tau,remaining):
        stop=min(tau,remaining);full=tau<=remaining+1e-12;start=tau-self.P
        current=np.zeros((self.W+1,len(v)));current[0]=v;last=0.
        for word in range(self.W):
            reset=start+(word+1)*self.P/self.W
            if reset>stop+1e-12:break
            current=current@self.exp(reset-last);last=reset;new=np.zeros_like(current)
            for c in range(self.W+1):
                for z in range(2):
                    for mask in range(self.dim):
                        dirty=1 if mask&(1<<word) else 0
                        if c+dirty<=self.W:new[c+dirty,z*self.dim+(mask&~(1<<word))]+=current[c,z*self.dim+mask]
            current=new
        current=current@self.exp(stop-last)
        return current,full
    def run(self,learning):
        bank=self.bank;initial=np.zeros(2*self.dim);initial[0]=initial[self.dim]=.5
        q,s,scores,rejected,active=bank.initial();survival=cost=0.;stopcost=0.;killed=0.
        stack=[(0,0,initial,q,s,scores,rejected,active)]
        args=engine.payload(bank);threshold=args[-2]
        while stack:
            t,passes,v,q,s,scores,rejected,active=stack.pop();self.nodes+=1;remaining=60-t
            a=model.choose(remaining,q,s,active,*model.controller_args(bank))
            model.spend(a,remaining,q,s,active,*model.controller_args(bank))
            endstates,full=self.pass_map(v,bank.periods[a],remaining*.1)
            live=float(endstates.sum());killed+=float(v.sum())-live
            if not full or t+bank.ticks[a]>=60:
                self.leaves+=1;survival+=live;cost+=live*(passes+(1 if full else 0));stopcost+=live*(1 if full else 0)
                continue
            stopcost+=live
            for y,child in enumerate((endstates[0],endstates[1:].sum(axis=0))):
                if child.sum()==0:continue
                qq=q.copy();ss=s.copy();sc=scores.copy();rr=rejected.copy();ac=active.copy()
                model.observe(a,y,qq,sc,rr,ac,bank.kernels,learning,threshold)
                stack.append((t+bank.ticks[a],passes+1,child,qq,ss,sc,rr,ac))
        return dict(F=1-survival,survival=survival,absorbed=killed,mass_error=abs(survival+killed-1),passes_given_survival=cost/survival,
                    stop_passes=stopcost,nodes=self.nodes,leaves=self.leaves)

@njit(cache=True)
def sequential_test_tree(kernels,ticks,threshold):
    # Twelve observations: 300 s after a zero, 150 s after a positive.
    # The complete adaptive observation experiment fits within H=3600 s.
    M=len(kernels);maxdepth=12
    qstore=np.zeros((maxdepth+1,M,6));qstore[0,:,:2]=.5
    lstore=np.ones((maxdepth+1,M));scores=np.zeros((maxdepth+1,M));rejs=np.zeros((maxdepth+1,M),np.bool_)
    branches=np.zeros(maxdepth+1,np.int64);prev=np.zeros(maxdepth+1,np.int64)
    mass=np.zeros(M);cross=np.zeros(M);depth=0;leaves=0
    while depth>=0:
        if depth==maxdepth:
            for j in range(M):
                mass[j]+=lstore[depth,j]
                if rejs[depth,j]:cross[j]+=lstore[depth,j]
            leaves+=1;depth-=1;continue
        if branches[depth]>=2:
            branches[depth]=0;depth-=1;continue
        y=branches[depth];branches[depth]+=1;a=11 if prev[depth]==0 else 10
        q=qstore[depth].copy();ss=scores[depth].copy();rr=rejs[depth].copy();act=np.ones(M,np.bool_)
        for j in range(M):
            ell=0.
            for old in range(4):
                for new in range(4):ell+=q[j,old]*kernels[j,a,y,old,new]
            lstore[depth+1,j]=lstore[depth,j]*ell
        model.observe(a,y,q,ss,rr,act,kernels,True,threshold)
        qstore[depth+1]=q;scores[depth+1]=ss;rejs[depth+1]=rr;prev[depth+1]=y
        depth+=1;branches[depth]=0
    return mass,cross,leaves


def explicit_scanner(times,words,bits,bank,learning):
    # Independently enumerate ALL physical checks in chronological order.
    cfg=bank.cfg;W=cfg['memory']['words'];P=cfg['memory']['pass_seconds'];H=cfg['horizon_seconds']
    dirty=[None]*W;q,s,sc,r,ac=bank.initial();tick=0;ix=0;passes=0;observations=[];args=model.controller_args(bank)
    while tick<int(round(H/.1)):
        remaining=int(round(H/.1))-tick;a=model.choose(remaining,q,s,ac,*args);model.spend(a,remaining,q,s,ac,*args)
        t=tick*.1;end=min(H,t+bank.periods[a]);count=0;events=[]
        while ix<len(times) and times[ix]<end-1e-12:
            events.append((times[ix],1,int(words[ix]),int(bits[ix])));ix+=1
        for w in range(W):
            rt=t+bank.periods[a]-P+(w+1)*P/W
            if rt<=end+1e-12:events.append((rt,0,w,-1))
        for et,kind,w,bit in sorted(events):
            if kind==0:
                if dirty[w] is not None:count+=1;dirty[w]=None
            elif dirty[w] is None:dirty[w]=bit
            elif dirty[w]==bit:dirty[w]=None
            else:return 1,passes,et,observations
        if t+bank.periods[a]>H+1e-10:break
        passes+=1;observations.append(count);tick+=bank.ticks[a]
        if tick<int(round(H/.1)):model.observe(a,count,q,sc,r,ac,bank.kernels,learning,engine.payload(bank)[-2])
    return 0,passes,H,observations

def run():
    start=time.perf_counter();rows=[];b=model.build();q,s,sc,rr,active=b.initial();args=model.controller_args(b)
    # Independent six-state block exponential for integrated-rate moments.
    maxerr=0.
    for a in b.rates[::4]:
        Q=np.array([[-a,a],[a,-a]]);L=np.diag([b.cfg['environment']['b_low'],b.cfg['environment']['b_high']])
        A=np.block([[Q,L,np.zeros((2,2))],[np.zeros((2,2)),Q,2*L],[np.zeros((2,4)),Q]])
        for h in b.periods:
            E=expm(A*h);f,z=model.moments(h,a,L[0,0],L[1,1])
            maxerr=max(maxerr,float(np.max(abs(f-E[:2,2:4].sum(axis=1))/(1+abs(f)))),float(np.max(abs(z-E[:2,4:6].sum(axis=1))/(1+abs(z)))))
    assert maxerr<1e-9;rows.append(dict(test='independent_integrated_moments',passed=True,max_scaled_error=maxerr))
    # All binary observation branches, exact potential identity in the model.
    worst=0.;rng=np.random.default_rng(170916001)
    for iteration in range(50):
        remaining=36000-iteration*10;a=model.choose(remaining,q,s,active,*args)
        old=s.copy();d=np.array([model.delta_for(j,a,remaining,q,*args[:-1]) for j in range(33)])
        for j in range(33):
            stat=q[j];p=stat[:2]+stat[2:4];expected=0.
            for y in range(2):
                new=stat[:4]@b.kernels[j,a,y];ell=new[:4].sum();new/=ell
                nr=remaining-b.ticks[a];pn=new[:2]+new[2:4]
                expected+=ell*(pn@b.value[j,nr,:2]+new[4:]@b.value[j,nr,2:]+old[j]-d[j])
            reward=p@b.second[j,a]+stat[4:]@b.first[j,a]
            current=p@b.value[j,remaining,:2]+stat[4:]@b.value[j,remaining,2:]+old[j]
            worst=max(worst,abs(reward+expected-current))
        model.spend(a,remaining,q,s,active,*args)
        model.observe(a,int(rng.random()<.5),q,sc,rr,active,b.kernels,False,engine.payload(b)[-2])
    assert worst<1e-12;rows.append(dict(test='all_branch_vector_potential_identity',passed=True,max_error=worst))
    assert np.all(active);qbefore=q.copy();model.observe(2,0,q,sc,rr,active,b.kernels,False,engine.payload(b)[-2]);assert np.all(active) and np.max(abs(q-qbefore))>0
    rows.append(dict(test='frozen_keeps_all_D_but_updates_hidden_state',passed=True))
    active[:]=False;before=s.copy();a=model.choose(100,q,s,active,*args);model.spend(a,100,q,s,active,*args)
    assert b.periods[a]==1 and np.array_equal(s,before);rows.append(dict(test='empty_set_executes_backup_without_reset',passed=True))
    mass,cross,leaves=sequential_test_tree(b.kernels,b.ticks,engine.payload(b)[-2])
    beta=b.cfg['controller']['beta']/b.cfg['controller']['continuous_transfer_factor']
    assert max(abs(mass-1))<1e-10 and max(cross)<=beta+1e-12
    rows.append(dict(test='complete_adaptive_likelihood_tree',passed=True,leaves=int(leaves),maximum_crossing_probability=float(max(cross)),node_budget=beta,mass_residual=float(max(abs(mass-1)))))
    # Frozen/kernel reduction versus the accepted full numeric-count filter.
    full=known_core.build_model(known_core.load_config(),300,cache=False);basis=model.scan_basis(b.cfg)
    scn=model.scan_from_basis(b.cfg,1/300,basis);mx=0.
    for a,h in enumerate(b.periods):
        kk=model.combine(model.idle(h-b.cfg['memory']['pass_seconds'],1/300,b.cfg['environment']['b_low'],b.cfg['environment']['b_high']),scn)
        old=np.arange(1,27,dtype=float);old/=old.sum();red=np.zeros(6)
        for z in range(2):
            red[z]=old[z*13];red[2+z]=old[z*13+1:(z+1)*13].sum();red[4+z]=old[z*13:(z+1)*13]@np.arange(13)
        for y in range(2):
            fk=full.kernels[a,0] if y==0 else full.kernels[a,1:].sum(axis=0);dist=old@fk;expected=np.zeros(6)
            for z in range(2):
                expected[z]=dist[z*13];expected[2+z]=dist[z*13+1:(z+1)*13].sum();expected[4+z]=dist[z*13:(z+1)*13]@np.arange(13)
            mx=max(mx,float(max(abs(red[:4]@kk[y]-expected))))
    assert mx<1e-10;rows.append(dict(test='binary_reduction_vs_accepted_full_count_kernel',passed=True,max_absolute_error=mx,shared_scan_quadrature=True))
    toy=toy_bank();oracle=[]
    for D in [3,10,30,300]:
        for learning in (True,False):
            record=PhysicalOracle(toy,D).run(learning);assert record['mass_error']<1e-10 and record['F']<toy.cfg['epsilon']
            oracle.append(dict(dwell=D,learning=learning,**record))
    rows.append(dict(test='independent_killed_physical_tree',passed=True,cases=len(oracle),maximum_F=max(x['F'] for x in oracle),epsilon=toy.cfg['epsilon']))
    for seed in range(170916100,170916300):
        ts,ws,bs=known_sim._stream(seed,6.,10.,.02,.4,2,32)
        for enabled in (True,False):
            ref=explicit_scanner(ts,ws,bs,toy,enabled)
            tr=np.empty((7,18));got=engine.run_bank(ts,ws,bs,enabled,engine.payload(toy),np.full(2,-1,np.int8),np.empty(2),np.empty(2,np.int32),np.empty(2,np.int32),tr,True)
            assert int(got[0])==ref[0] and int(got[1])==ref[1] and abs(got[5]-ref[2])<1e-10
            assert np.array_equal(tr[:int(got[-1]),3],ref[3])
    rows.append(dict(test='independent_all_word_scanner_vs_lazy',passed=True,paired_paths=400,discrepancies=0))
    out=model.ROOT/'outputs';out.mkdir(exist_ok=True)
    report=dict(status='ENGINEERING_TESTS_COMPLETED_NOT_SCIENTIFIC_REVIEW',tests=rows,physical_oracle=oracle,toy_contract=toy.cfg,seconds=time.perf_counter()-start)
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report
if __name__=='__main__':run()
