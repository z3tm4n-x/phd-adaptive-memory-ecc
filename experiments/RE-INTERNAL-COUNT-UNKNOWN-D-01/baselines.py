"""Uniform-in-D Fixed and two-block optima in the declared finite classes.

The exogenous-schedule first-passage bracket is the accepted RES-003 formula,
now evaluated by directed interval arithmetic at all 33 rational generators.
The continuum interpolation applies to the complete failure event, not to a
collection of independently reselected generators.
"""
import csv,json
from fractions import Fraction
from certify import I,continuum
import model

def brackets(cfg,rate,first,second=None):
    W=cfg['memory']['words'];n=cfg['memory']['bits_per_word'];P=I(cfg['memory']['pass_seconds']);H=I(cfg['horizon_seconds'])
    t1=I(first);t2=I(first if second is None else second)
    lo=I(cfg['environment']['b_low']);hi=I(cfg['environment']['b_high'])
    mean=(lo+hi)/2;var=(hi-lo).square()/4;k=2*rate;coef=I(n-1)/(2*n*W)
    def moment(t):return mean.square()*t.square()+2*var*(t/k+((-k*t).exp()-1)/k.square())
    mx=P*(W+1)/(2*W);mx2=P.square()*(W+1)*(2*W+1)/(6*W*W)
    bt2=(t1-P).square()+2*(t1-P)*mx+mx2+P.square()-2*P*mx+mx2
    step=k*P/W;geom=((-k*P).exp()-1)/((-step).exp()-1)/W
    bexp=(-k*(t1-P)-step).exp()*geom+geom
    bm2=mean.square()*bt2+2*var*(t1/k-(2-bexp)/k.square())
    Hf=Fraction(str(cfg['horizon_seconds']));f1=Fraction(str(first));f2=Fraction(str(first if second is None else second))
    n1=Hf/f1 if second is None else Hf/2/f1;n2=0 if second is None else Hf/2/f2
    if int(n1)!=n1 or int(n2)!=n2:raise ValueError('nonintegral block schedule')
    n1=int(n1);n2=int(n2)
    expected=coef*((n1-1)*moment(t1)+n2*moment(t2)+bm2)
    qmax=coef*hi.square()*((n1-1)*t1.square()+n2*t2.square()+bt2)
    dose=hi*I(max(first,first if second is None else second))/W
    lower=(1-(-(-dose).exp()*qmax).exp())*expected/qmax
    return lower,expected,n1+n2,qmax

def run():
    cfg=model.config();G=I(cfg['controller']['continuous_transfer_factor']);eps=I(cfg['epsilon'])
    continuum(cfg);rows=[];allrows=[];opt=[]
    for kind in ['Fixed','Precomputed']:
        for first in cfg['periods_seconds']:
            seconds=[None] if kind=='Fixed' else cfg['periods_seconds']
            for second in seconds:
                maxhi=I(0).hi;bestlower=I(0).lo;witness=None;node_of_max=None
                for j in range(33):
                    rate=I((32+9*j)**2)/(3000*32**2)
                    lb,ub,passes,qmax=brackets(cfg,rate,first,second)
                    if ub.hi>maxhi:maxhi=ub.hi;node_of_max=j
                    if lb.lo>bestlower:bestlower=lb.lo;witness=j
                    allrows.append(dict(policy=kind,first=first,second=first if second is None else second,node=j,
                                        lower=str(lb.lo),upper=str(ub.hi),passes=passes))
                bound=G*I(maxhi)
                rows.append(dict(policy=kind,first=first,second=first if second is None else second,passes=passes,
                                 uniform_upper=str(min(I(1).hi,bound.hi)),max_node_upper=str(maxhi),upper_node=node_of_max,
                                 exclusion_witness_lower=str(bestlower),exclusion_node=witness,
                                 uniform_feasible=bound.hi<=eps.lo,uniform_infeasible=bestlower>eps.hi))
        admissible=[r for r in rows if r['policy']==kind and r['uniform_feasible']]
        if not admissible:raise ArithmeticError('no uniformly certified baseline')
        best=min(admissible,key=lambda r:(r['passes'],-r['first'],-r['second']))
        cheaper=[r for r in rows if r['policy']==kind and r['passes']<best['passes']]
        if not all(r['uniform_infeasible'] for r in cheaper):raise ArithmeticError('optimum not resolved')
        opt.append(dict(**best,cheaper_excluded=len(cheaper),optimal_in_declared_class=True,
                        weakest_cheaper_lower=min(float(r['exclusion_witness_lower']) for r in cheaper)))
    out=model.ROOT/'outputs';out.mkdir(exist_ok=True)
    for name,data in [('open_loop_uniform.csv',rows),('open_loop_all_nodes.csv',allrows)]:
        with (out/name).open('w',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=list(data[0]));wr.writeheader();wr.writerows(data)
    (out/'open_loop_optima.json').write_text(json.dumps(opt,indent=2)+'\n')
    print(json.dumps(opt,indent=2));return opt
if __name__=='__main__':run()
