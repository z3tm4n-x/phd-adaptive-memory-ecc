"""Uniform-in-D Fixed / two-block Precomputed certificates and class optima.

Reuses the accepted analytical bracket, independently evaluated with Decimal.
Continuous admissibility follows Holder interpolation, not grid membership.
"""
from __future__ import annotations
from decimal import Decimal as D,localcontext
import csv,json
from model import ROOT,load_config,rate_grid
from numeric_witness import continuum


def bracket(cfg,dwell,first,second=None):
    with localcontext() as ctx:
        ctx.prec=80;M=lambda x:x if isinstance(x,D) else D(str(x))
        W=cfg['memory']['words'];n=cfg['memory']['bits_per_word'];P=M(cfg['memory']['pass_seconds']);H=M(cfg['horizon_seconds'])
        a=M(first);b=a if second is None else M(second);lo=M(cfg['environment']['b_low']);hi=M(cfg['environment']['b_high'])
        mean=(lo+hi)/2;var=(hi-lo)**2/4;k=2/M(dwell);coef=M(n-1)/(2*n*W)
        def em1(x):return x.exp()-1
        def moment(t):return mean**2*t*t+2*var*(t/k+em1(-k*t)/(k*k))
        mx=P*(W+1)/(2*W);mx2=P*P*(W+1)*(2*W+1)/(6*W*W)
        bt2=(a-P)**2+2*(a-P)*mx+mx2+P*P-2*P*mx+mx2
        step=k*P/W;geom=em1(-k*P)/em1(-step)/W
        bexp=(-k*(a-P)-step).exp()*geom+geom
        bm2=mean**2*bt2+2*var*(a/k-(2-bexp)/(k*k))
        n1=H/a if second is None else H/2/a;n2=D(0) if second is None else H/2/b
        if n1!=int(n1) or n2!=int(n2):raise ValueError('Nonintegral block schedule')
        eq=coef*((n1-1)*moment(a)+n2*moment(b)+bm2)
        qmax=coef*hi*hi*((n1-1)*a*a+n2*b*b+bt2)
        dose=hi*max(a,b)/W;lower=-em1(-(-dose).exp()*qmax)*eq/qmax
        return float(lower),float(min(D(1),eq)),int(n1+n2)


def run(cfg=None):
    cfg=cfg or load_config();G=cfg['controller']['continuous_transfer_factor'];rows=[];summ=[];opt=[]
    for kind in ['Fixed','Precomputed']:
        for a in cfg['periods_seconds']:
            for b in ([None] if kind=='Fixed' else cfg['periods_seconds']):
                local=[]
                for j in range(33):
                    dwell=D(3000*32**2)/D((32+9*j)**2)
                    lo,hi,passes=bracket(cfg,dwell,a,b)
                    row=dict(policy=kind,first=a,second=a if b is None else b,grid=j,D=float(dwell),
                             lower=lo,upper=hi,passes=passes);rows.append(row);local.append(row)
                upper=G*(max(r['upper'] for r in local)+1e-12)
                # A single excluded D is sufficient to reject a uniform competitor.
                lower=max(r['lower'] for r in local)-1e-12
                summ.append(dict(policy=kind,first=a,second=a if b is None else b,passes=passes,
                                 continuum_upper=upper,witness_lower=lower,
                                 certified=upper<=cfg['epsilon']))
        candidates=[r for r in summ if r['policy']==kind and r['certified']]
        if not candidates:raise ValueError('No uniformly certified baseline')
        best=min(candidates,key=lambda r:(r['passes'],-r['first'],-r['second']))
        cheaper=[r for r in summ if r['policy']==kind and r['passes']<best['passes']]
        if not all(r['witness_lower']>cfg['epsilon'] for r in cheaper):raise ValueError('Class optimality unresolved')
        opt.append(dict(**best,rejected_cheaper=len(cheaper),least_cheaper_lower=min(r['witness_lower'] for r in cheaper)))
    for name,data in [('open_loop_grid.csv',rows),('open_loop_uniform.csv',summ),('open_loop_optima.csv',opt)]:
        with (ROOT/'outputs'/name).open('w',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=list(data[0]));wr.writeheader();wr.writerows(data)
    (ROOT/'outputs'/'continuum_witness.json').write_text(json.dumps(continuum(cfg),indent=2))
    print(json.dumps(opt,indent=2));return opt

if __name__=='__main__':run()
