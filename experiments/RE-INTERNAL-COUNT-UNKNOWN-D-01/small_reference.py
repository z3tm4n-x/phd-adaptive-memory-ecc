"""Independent killed physical model and finite auxiliary moment check.

The killed model never calls the auxiliary observation helper. Its transient
states are (environment, dirty-word mask). Same-bit cancellation rate is b/(nW),
different-bit events leave transient mass irreversibly. Counts come from word
reset maps. The auxiliary small-scan builder is a SEPARATE test/implementation
backend, not the killed physical law.
"""
from __future__ import annotations
import copy,math
import numpy as np
from scipy.linalg import expm


def exact_aux_scan(cfg,a):
    W=cfg['memory']['words'];P=cfg['memory']['pass_seconds']
    rates=[cfg['environment']['b_low'],cfg['environment']['b_high']]
    result=np.zeros((2,2,6))
    for z0 in range(2):
        p=np.zeros(8);p[z0]=1;mom=np.zeros(8);mom[z0]=1
        for w in range(W):
            f=w/W;Q=np.zeros((8,8));Q4=np.zeros((4,4));B=np.zeros((4,4))
            for k in range(2):
                for c in range(2):
                    for z,b in enumerate(rates):
                        i=z+2*c+4*k;Q[i,1-z+2*c+4*k]+=a;Q[i,i]-=a
                        if c==0:Q[i,z+2+4*k]+=b*(1-f);Q[i,i]-=b*(1-f)
                        if k==0:Q[i,z+2*c+4]+=b*f;Q[i,i]-=b*f
            for c in range(2):
                for z,b in enumerate(rates):
                    i=z+2*c;Q4[i,1-z+2*c]+=a;Q4[i,i]-=a;B[i,i]=b*f
                    if c==0:Q4[i,z+2]+=b*(1-f);Q4[i,i]-=b*(1-f)
            p=p@expm(Q*P/W)
            block=np.block([[Q4,B],[np.zeros((4,4)),Q4]])
            mom=mom@expm(block*P/W)
        for zz in range(2):
            result[z0,zz]=[p[zz],p[zz+4],p[zz+2],p[zz+6],mom[4+zz],mom[6+zz]]
    return result


class PhysicalOracle:
    def __init__(self,cfg,D):
        self.cfg=cfg;self.W=cfg['memory']['words'];self.P=cfg['memory']['pass_seconds']
        self.n=cfg['memory']['bits_per_word'];self.S=2*(1<<self.W);self.cache={};self.exp_cache={}
        a=1/D;rates=[cfg['environment']['b_low'],cfg['environment']['b_high']]
        Q=np.zeros((self.S,self.S));masks=1<<self.W
        for z,b in enumerate(rates):
            for mask in range(masks):
                i=z*masks+mask;Q[i,(1-z)*masks+mask]+=a;Q[i,i]-=a
                for w in range(self.W):
                    if mask&(1<<w):Q[i,z*masks+(mask^(1<<w))]+=b/(self.W*self.n)
                    else:Q[i,z*masks+(mask|(1<<w))]+=b/self.W
                    Q[i,i]-=b/self.W
        self.Q=Q
    def evolve(self,h):
        key=round(h,13)
        if key not in self.exp_cache:self.exp_cache[key]=expm(self.Q*h)
        return self.exp_cache[key]
    def kernel(self,tau,h=None):
        h=tau if h is None else h;key=(round(tau,13),round(h,13))
        if key in self.cache:return self.cache[key]
        S=self.S;W=self.W;masks=1<<W
        # Matrix from each possible physical starting state to (count flag,state).
        A=np.zeros((S,2,S));A[:,0,:]=np.eye(S);last=0.
        for w in range(W):
            reset=tau-self.P+(w+1)*self.P/W
            if reset>h+1e-13:break
            E=self.evolve(reset-last)
            for flag in range(2):A[:,flag,:]=A[:,flag,:]@E
            B=np.zeros_like(A)
            for flag in range(2):
                for z in range(2):
                    for mask in range(masks):
                        dirty=bool(mask&(1<<w));dest=z*masks+(mask&~(1<<w))
                        B[:,1 if (flag or dirty) else 0,dest]+=A[:,flag,z*masks+mask]
            A=B;last=reset
        E=self.evolve(h-last)
        for flag in range(2):A[:,flag,:]=A[:,flag,:]@E
        K=A.transpose(1,0,2);self.cache[key]=K;return K
    @property
    def initial(self):
        p=np.zeros(self.S);p[0]=p[1<<self.W]=.5;return p


def evaluate(bank,D,learn=True,max_nodes=1000000):
    from model import choose,observe,retained,controller_args
    cfg=bank.cfg;oracle=PhysicalOracle(cfg,D);total=len(bank.value[0])-1
    cc=cfg['controller'];threshold=math.log(cc['continuous_transfer_factor']/cc['beta'])+cc['test_log_margin']
    nodes=0;failure=0.;survival=0.;survivor_passes=0.;unresolved=0.;removed_mass=0.
    stack=[(0,oracle.initial,bank.initial,bank.slack.copy(),np.zeros(len(bank.rates)),
            np.zeros(len(bank.rates),bool),0)]
    while stack:
        tick,p,q,s,logs,rejected,passes=stack.pop();nodes+=1
        if nodes>max_nodes:raise RuntimeError('Small tree limit, no silent pruning')
        mass=float(p.sum())
        if mass<1e-18:
            unresolved+=mass;continue
        rem=total-tick;active=retained(rejected) if learn else np.ones(len(q),bool)
        a,snew,_=choose(q,s,active,rem,*controller_args(bank))
        tau=float(bank.periods[a]);dt=min(rem,int(bank.ticks[a]));h=dt*cc['time_tick_seconds']
        K=oracle.kernel(tau,h);nextp=np.array([p@K[y] for y in range(2)])
        left=float(nextp.sum());failure+=mass-left
        if dt==rem:
            survival+=left;survivor_passes+=left*(passes+(tau<=h+1e-12));continue
        for y in range(2):
            ll=logs.copy();rr=rejected.copy();newq=observe(q,ll,rr,a,y,bank.kernels,threshold,learn)
            stack.append((tick+dt,nextp[y],newq,snew.copy(),ll,rr,passes+1))
    return dict(D=D,learning=learn,nodes=nodes,F_lower=failure,F_upper=failure+unresolved,
                survival=survival,mass_residual=abs(failure+survival+unresolved-1),
                unresolved_mass=unresolved,passes_given_survival=survivor_passes/survival)


def small_config(cfg):
    c=copy.deepcopy(cfg);c['memory'].update(words=2,bits_per_word=32,pass_seconds=.1)
    c['environment'].update(b_low=.01,b_high=.3);c['horizon_seconds']=6;c['epsilon']=.1
    c['periods_seconds']=[.2,.5,1,2,5]
    c['controller']['continuous_transfer_factor']=1.;c['controller']['numerical_allowance']=.001
    return c
