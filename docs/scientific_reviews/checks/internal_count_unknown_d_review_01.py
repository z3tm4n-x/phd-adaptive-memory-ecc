"""Bounded SR checks; no production outputs, pilot, or Monte Carlo are written.

Run: python -B THIS_FILE REPOSITORY_ROOT EXTERNAL_OUTPUT_DIR STAGE
STAGE: audit, coeff, logic, baselines, scanner.
The logic check executes undecorated production Python bodies, NOT Numba/JIT.
Numba imports and decorators are removed in memory by AST; sources stay intact.
"""
from __future__ import annotations
import ast, csv, hashlib, itertools, json, math, pathlib, subprocess, sys, types
from decimal import Decimal, localcontext
import numpy as np
from scipy.linalg import expm

REPO = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2]).resolve()
E = REPO / 'experiments/RE-INTERNAL-COUNT-UNKNOWN-D-01'
assert E != OUT and E not in OUT.parents
OUT.mkdir(parents=True, exist_ok=True)
sys.dont_write_bytecode = True
sys.path.insert(0, str(E))

def load(name):
    path = E / (name + '.py')
    tree = ast.parse(path.read_text())
    tree.body = [x for x in tree.body if not (isinstance(x, ast.ImportFrom) and x.module == 'numba')]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node.decorator_list = [d for d in node.decorator_list if not
                (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == 'njit')]
    module = types.ModuleType(name); module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(tree, str(path), 'exec'), module.__dict__)
    return module

def save(name, obj):
    (OUT / (name+'.json')).write_text(json.dumps(obj, indent=2) + '\n')
    print(name, json.dumps(obj), flush=True)

def rows(name):
    with (E / 'outputs' / name).open() as f:
        return list(csv.DictReader(f))

def audit():
    manifest = json.loads((E/'delivery_tools/delivery_manifest_2026-09-10.json').read_text())
    tree_manifest=json.loads((E/'outputs/delivery_tree_manifest_2026-09-10.json').read_text())
    for row in manifest['files']+tree_manifest['files']:
        data = (E/row['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        blob = subprocess.check_output(['git','rev-parse','f1b1418b5f75630433af9c8d0e5586f328532a15:experiments/RE-INTERNAL-COUNT-UNKNOWN-D-01/'+row['path']], cwd=REPO, text=True).strip()
        assert blob == row['git_blob_sha1']
    cfg = json.loads((E/'config.json').read_text())
    primary=[]
    for dwell in cfg['simulation']['dwell_seconds']:
        data=np.load(E/f'cache/heldout_{dwell}.npz',allow_pickle=False)['data']
        assert data.shape == (20000,6,10)
        assert np.all((data[:,:2,1]>=0)&(data[:,:2,1]<=3600))
        surv=data[:,:,0]==0
        means=[math.fsum(data[surv[:,j],j,1])/int(surv[:,j].sum()) for j in [0,1]]
        rad=[3600*math.sqrt(math.log(300)/(2*surv[:,j].sum())) for j in [0,1]]
        both=surv[:,0]&surv[:,1]
        joint=math.fsum(data[both,1,1]-data[both,0,1])/int(both.sum())
        lower=means[1]-means[0]-sum(rad)
        jl=joint-7200*math.sqrt(math.log(300)/(2*both.sum()))
        expected=next(r for r in rows('learning_effect_family.csv') if int(r['dwell'])==dwell)
        assert abs(lower-float(expected['individual_family95_lower']))<1e-10
        assert abs(jl-float(expected['common_survivor_family95_lower']))<1e-10
        assert np.all(data[:,1,7]==2**32-1)
        assert np.all(data[:,1,8:10]==-1)
        for j in [2,3]:
            assert np.all(data[surv[:,j],j,1] == (3600 if j==2 else 2700))
        primary.append(dict(D=dwell,failures=[int((~surv[:,j]).sum()) for j in [0,1]],means=means,
          lower=lower,joint_lower=jl,stop_saving=float(np.mean(data[:,1,1]-data[:,0,1]))))
    pilot=rows('analogue_pilot.csv'); eligible=[]
    for candidate in range(27):
        rr=sorted([r for r in pilot if int(r['candidate'])==candidate],key=lambda r:float(r['dwell']))
        assert len(rr)==5
        if all(float(r['upper95'])<=.1 for r in rr):
            v=[float(r['passes_given_survival']) for r in rr]
            eligible.append((max(v),v,float(rr[0]['Ms']),float(rr[0]['cap']),candidate))
    chosen=min(eligible); selected=json.loads((E/'outputs/selected_analogue.json').read_text())
    assert chosen[4]==selected['candidate'] and chosen[2]==selected['Ms'] and chosen[3]==selected['cap']
    seedsets=[]
    for typ in ['pilot','validation']:
        sim=cfg['simulation']; seedsets.append(set(s for i in range(5) for s in range(sim[typ+'_seed']+i*sim['seed_stride_per_dwell'],sim[typ+'_seed']+i*sim['seed_stride_per_dwell']+sim[typ+'_trials_per_dwell'])))
    assert not seedsets[0]&seedsets[1]
    save('audit',dict(original_blob_checks=len(manifest['files']),delivery_blob_checks=len(tree_manifest['files']),primary=primary,pilot_selected=chosen,pilot_eligible=len(eligible),disjoint_declared_seeds=True))

def coeff():
    model=load('model'); witness=load('numeric_witness')
    witness.ROOT=OUT; (OUT/'outputs').mkdir(exist_ok=True)
    r=witness.verify(model.load_config())
    save('coefficient_summary',{k:v for k,v in r.items() if k not in ['rows','continuum']})

def baselines():
    m=load('model'); cfg=m.load_config(); W=cfg['memory']['words']
    P=np.longdouble(str(cfg['memory']['pass_seconds'])); H=3600
    # Actual word reset phases, explicitly averaged, no geometric-sum helper.
    phases=np.arange(1,W+1,dtype=np.longdouble)*P/W
    lo=np.longdouble(str(cfg['environment']['b_low']));hi=np.longdouble(str(cfg['environment']['b_high']))
    mu=(lo+hi)/2;var=(hi-lo)**2/4;factor=np.longdouble(31)/(64*W)
    archived=rows('open_loop_grid.csv'); error=0.; independent=[]
    for j in range(33):
        a=np.longdouble((32+9*j)**2)/np.longdouble(3000*32**2); k=2*a
        def second(t):return mu*mu*t*t+2*var*(k*t+np.expm1(-k*t))/(k*k)
        boundary={t:(np.mean(second(np.longdouble(str(t))-P+phases)+second(P-phases)),
                       np.mean((np.longdouble(str(t))-P+phases)**2+(P-phases)**2)) for t in cfg['periods_seconds']}
        for row in [r for r in archived if int(r['grid'])==j]:
            t1=np.longdouble(row['first']);t2=np.longdouble(row['second']);fixed=row['policy']=='Fixed'
            n1=int(round(H/t1 if fixed else H/2/t1));n2=0 if fixed else int(round(H/2/t2))
            eq=factor*((n1-1)*second(t1)+n2*second(t2)+boundary[float(t1)][0])
            qm=factor*hi*hi*((n1-1)*t1*t1+n2*t2*t2+boundary[float(t1)][1])
            lower=-np.expm1(-np.exp(-hi*max(t1,t2)/W)*qm)*eq/qm
            error=max(error,abs(float(lower)-float(row['lower'])),abs(float(min(1,eq))-float(row['upper'])))
            assert n1+n2==int(row['passes'])
            independent.append((row['policy'],float(t1),float(t2),n1+n2,float(lower),float(min(1,eq))))
    assert error<1e-10 and len(independent)==5148
    optima=[]
    for kind in ['Fixed','Precomputed']:
        uniform=[]
        for t1,t2 in sorted({(r[1],r[2]) for r in independent if r[0]==kind}):
            local=[r for r in independent if r[:3]==(kind,t1,t2)]
            uniform.append((local[0][3],-t1,-t2,1.064*(max(r[5] for r in local)+1e-12),max(r[4] for r in local)-1e-12))
        best=min(r for r in uniform if r[3]<=.1)
        cheaper=[r for r in uniform if r[0]<best[0]]
        assert all(r[4]>.1 for r in cheaper)
        optima.append(dict(kind=kind,passes=best[0],periods=[-best[1],-best[2]],upper=best[3],excluded=len(cheaper),minimum_lower=min(r[4] for r in cheaper)))
    # Independent rational exponent calculation (80 digits), not witness helper.
    with localcontext() as dc:
        dc.prec=80
        vals=[]
        for j in range(32):
            a=Decimal((32+9*j)**2)/Decimal(3000*32**2);b=Decimal((41+9*j)**2)/Decimal(3000*32**2)
            vals.append((Decimal(3600)*(b-a)**2/(8*a)).exp())
        g=max(vals);assert g<Decimal('1.064')
    save('baselines',dict(rows=5148,word_phases=W,max_absolute_error=error,optima=optima,continuum_factor=str(g)))

def scanner():
    m=load('model'); sm=load('small_reference'); load('known_reference'); sim=load('simulate'); ts=load('tests')
    cfg=sm.small_config(m.load_config());b=m.build_bank(cfg,[.1,1/3,1.]);known=ts.dummy_known();checked=0
    for seed in range(20):
        epochs,words,bits=sim.stream(565600+seed,6,3,.01,.3,2)
        for kind in [0,1]:
            trace=np.empty((40,18));state=np.full(2,-1,np.int8)
            actual=sim.run(epochs,words,bits,kind,.12,5.,3.,*sim.pack_args(b,known,3.),state,np.empty(2),np.empty(2,np.int32),np.empty(2,np.int32),trace,True)
            f,p,t,c=ts.explicit_scan(b,epochs,words,bits,kind==0)
            assert bool(actual[0])==f and actual[1]==p and abs(actual[5]-t)<1e-10
            assert c==trace[:int(actual[-1]),2].astype(int).tolist();checked+=1
    save('scanner',dict(paths=checked,discrepancies=0,scope='first 20 seeds of existing scanner fixture, two policies; Python RNG/JIT equivalence not asserted'))

def logic():
    m=load('model'); cfg=m.load_config(); small=load('small_reference')
    b=m.build_bank(cfg)
    save('bank',dict(min_slack=float(b.slack.min()),arithmetic=b.arithmetic))
    backup_error=0.
    for j in range(33):
        aug=np.eye(3);aug[:2,:2]=b.transition[j,2]
        aug[:2,2]=b.reward[j,2,:2]+b.pending[j,2]@b.reward[j,2,2:]
        independent=(np.linalg.matrix_power(aug,3599)@np.r_[b.reward[j,2,:2],1])[:2]
        backup_error=max(backup_error,float(np.max(abs(independent-b.value[j,-1,:2]))))
    assert backup_error<1e-11
    # Separate block-PGF exponential: not the production moment formula.
    lo,hi=cfg['environment']['b_low'],cfg['environment']['b_high']
    moment_error=0.; rewards=np.zeros_like(b.reward)
    for j,a in enumerate(b.rates):
        Q=np.array([[-a,a],[a,-a]]); B=np.diag([lo,hi]); Z=np.zeros((2,2))
        G=np.block([[Q,B,Z],[Z,Q,2*B],[Z,Z,Q]])
        for h in sorted(set([.1,.9]+list(b.periods))):
            ex=expm(h*G); first=ex[:2,2:4].sum(1); second=ex[:2,4:6].sum(1)
            p1,p2=m.moments(h,a,lo,hi)
            moment_error=max(moment_error,float(np.max(abs(p1-first)/(1+first))),float(np.max(abs(p2-second)/(1+second))))
            ix=np.flatnonzero(b.periods==h)
            if len(ix):rewards[j,ix[0]]=np.r_[second/(2*cfg['memory']['words']),first/cfg['memory']['words']]
    assert moment_error<1e-9
    # Explicit finite K probabilities, NOT the six-statistic generator backend.
    # An absorbing K=12 cap incurs negligible tail here; moments match through 12.
    sc=small.small_config(cfg); sb=m.build_bank(sc,[.1,1/3,1.]); aux_error=0.
    for j,a in enumerate(sb.rates):
        for ai,tau in enumerate(sb.periods):
            nstates=52
            prob=np.zeros((2,nstates));prob[0,0]=prob[1,1]=1
            for dt,f in [(tau-.1,0),(.05,0),(.05,.5)]:
                gen=np.zeros((nstates,nstates))
                for k,c,z in itertools.product(range(13),range(2),range(2)):
                    ix=4*k+2*c+z; rate=[.01,.3][z]
                    for dest,r in [(4*k+2*c+1-z,a),(4*k+2+z,rate*(1-f)) if c==0 else (ix,0),
                                   (4*(k+1)+2*c+z,rate*f) if k<12 else (ix,0)]:
                        gen[ix,dest]+=r;gen[ix,ix]-=r
                prob=prob@expm(gen*dt)
            ref=np.zeros((2,4,6))
            for start in range(2):
                for k,c,z in itertools.product(range(13),range(2),range(2)):
                    p=prob[start,4*k+2*c+z]
                    ref[c,start,z+2*(k>0)]+=p;ref[c,start,4+z]+=k*p
                    ref[1,2+start,z+2*(k>0)]+=p;ref[1,2+start,4+z]+=k*p
            aux_error=max(aux_error,float(np.max(abs(ref-sb.kernels[j,ai]))))
    assert aux_error<1e-12
    # All rejection configurations of a 7-endpoint analogue of the same cell rule.
    for rr in itertools.product([False,True],repeat=7):
        expected={x for i in range(6) if not(rr[i] and rr[i+1]) for x in [i,i+1]}
        assert set(np.flatnonzero(m.retained(np.array(rr))))==expected
    aa,ss,_=m.choose(b.initial,b.slack,np.zeros(33,bool),36000,*m.controller_args(b))
    assert aa==2 and np.array_equal(ss,b.slack)
    # Production-linked tree check: independently accumulated likelihood vectors.
    max_lr_error=0.; max_filter_error=0.; max_potential_error=0.
    q=b.initial; logs=np.zeros(33); rej=np.zeros(33,bool); likelihood=np.ones(33)
    rng=np.random.default_rng(42190)
    for step in range(120):
        action=int(rng.integers(12)); y=int(rng.integers(2)); rem=36000-step*10
        raw=np.einsum('ji,jyik->yjk',q[:,:4],b.kernels[:,action])
        ell=raw[:,:,:4].sum(2); nextq=raw/ell[:,:,None]
        oldE=likelihood.mean()/likelihood
        nextlike=ell*likelihood[None,:]
        expected=(ell*(nextlike.mean(1)[:,None]/nextlike)).sum(0)
        max_lr_error=max(max_lr_error,float(np.max(abs(expected-oldE)/(1+oldE))))
        val=(q[:,:2]+q[:,2:4])*b.value[:,rem,:2]
        val=val.sum(1)+(q[:,4:]*b.value[:,rem,2:]).sum(1)
        nr=rem-min(rem,int(b.ticks[action])); nv=b.value[:,nr]
        future=(((nextq[:,:,:2]+nextq[:,:,2:4])*nv[None,:,:2]).sum(2)+(nextq[:,:,4:]*nv[None,:,2:]).sum(2))
        one=((q[:,:2]+q[:,2:4])*rewards[:,action,:2]).sum(1)+(q[:,4:]*rewards[:,action,2:]).sum(1)
        independent_delta=one+(ell*future).sum(0)-val
        prod=np.array([m.action_delta(q,j,action,rem,*m.controller_args(b)[:-1])[0] for j in range(33)])
        max_potential_error=max(max_potential_error,float(np.max(abs(prod-independent_delta))))
        actual=m.observe(q,logs,rej,action,y,b.kernels,math.log(1.064/.005)+.001,False)
        max_filter_error=max(max_filter_error,float(np.max(abs(actual-nextq[y]))))
        likelihood*=ell[y]; likelihood/=likelihood.max()
        assert np.max(abs(logs-np.log(likelihood)))<1e-10 and not rej.any()
        q=actual
        assert np.max(q[:,4:].sum(1))<=hi*cfg['memory']['pass_seconds']/2+1e-12
    assert max_lr_error<1e-10 and max_filter_error<1e-12 and max_potential_error<1e-10
    # Replay OWN saved counts. Independently enumerate all actions via observation
    # branches and PGF rewards, not via action_delta/choose. Production linked too.
    trace_results=[]; threshold=math.log(1.064/.005)+.001
    for dwell,learn in [(300,True),(3000,True),(300,False),(3000,False)]:
        q=b.initial;s=b.slack.copy();logs=np.zeros(33);rej=np.zeros(33,bool);now=0;local=[];count=0
        def independent_choose(active,rem):
            value=((q[:,:2]+q[:,2:4])*b.value[:,rem,:2]).sum(1)+(q[:,4:]*b.value[:,rem,2:]).sum(1)
            deltas=[]
            for a in range(12):
                dt=min(rem,int(b.ticks[a]));nr=rem-dt
                if dt<int(b.ticks[a]):
                    # Terminal reward uses a different exposure; not exercised by these full traces.
                    r=np.zeros((33,4))
                    for j,rate in enumerate(b.rates):
                        f,se=m.moments(dt*.1,rate,lo,hi);r[j]=np.r_[se/(2*cfg['memory']['words']),f/cfg['memory']['words']]
                else:r=rewards[:,a]
                reward=((q[:,:2]+q[:,2:4])*r[:,:2]).sum(1)+(q[:,4:]*r[:,2:]).sum(1)
                raw=np.einsum('ji,jyik->yjk',q[:,:4],b.kernels[:,a])
                nv=b.value[:,nr]
                future=(((raw[:,:,:2]+raw[:,:,2:4])*nv[None,:,:2]).sum(2)+(raw[:,:,4:]*nv[None,:,2:]).sum(2)).sum(0)
                deltas.append(reward+future-value)
            feasible=[a for a in range(12) if np.all(deltas[a][active]<=s[active]*min(rem,b.ticks[a])/rem+1e-13)]
            return max(feasible),deltas
        for row in rows(f'trace_{dwell}_{"learning" if learn else "frozen"}.csv'):
            rem=36000-now;active=m.retained(rej) if learn else np.ones(33,bool)
            a,new_s,_=m.choose(q,s,active,rem,*m.controller_args(b))
            ai,dd=independent_choose(active,rem)
            assert a==ai and b.periods[a]==float(row['previous_period_s'])
            assert np.max(abs(new_s[active]-np.maximum(0,s[active]-dd[a][active])))<1e-10
            s=new_s;now+=int(b.ticks[a]);oldmask=sum(1<<j for j in range(32) if not(rej[j] and rej[j+1]))
            oldactive=active.copy()
            if now<36000:
                y=int(float(row['own_count'])!=0)
                raw=np.einsum('ji,jik->jk',q[:,:4],b.kernels[:,a,y])
                ll=logs+np.log(raw[:,:4].sum(1));ll-=ll.max()
                expected_rej=rej | (np.log(np.exp(ll).mean())-ll>threshold) if learn else rej.copy()
                q=m.observe(q,logs,rej,a,int(float(row['own_count'])),b.kernels,threshold,learn)
                assert np.array_equal(rej,expected_rej) and np.max(abs(logs-ll))<1e-10
                active=m.retained(rej) if learn else active
                mask=sum(1<<j for j in range(32) if not(rej[j] and rej[j+1]))
                assert mask==int(float(row['D_cell_mask_after'])) and oldmask==int(float(row['D_cell_mask_before']))
                if learn and oldmask!=mask:
                    olda,_=independent_choose(oldactive,36000-now);newa,_=independent_choose(active,36000-now)
                    assert b.periods[olda]==float(row['local_previous_set_period']) and b.periods[newa]==float(row['local_refined_set_period'])
                    if olda!=newa:local.append([now*.1,float(b.periods[olda]),float(b.periods[newa])])
            count+=1
        trace_results.append(dict(D=dwell,learning=learn,decisions=count,local_effects=local))
    # Small killed tree is an existing production-linked independent physical oracle;
    # execution here is not a new independent controller implementation.
    oracle=[small.evaluate(sb,D,learn) for D in [1.,3.,10.] for learn in [True,False]]
    save('logic',dict(backup_matrix_power_error=backup_error,moment_scaled_error=moment_error,finite_count_aux_error=aux_error,
      likelihood_martingale_error=max_lr_error,filter_error=max_filter_error,potential_error=max_potential_error,
      cell_patterns=128,traces=trace_results,small_oracle=oracle,execution='undecorated Python source, NOT JIT'))

if __name__=='__main__':
    {'audit':audit,'coeff':coeff,'logic':logic,'baselines':baselines,'scanner':scanner}[sys.argv[3]]()
