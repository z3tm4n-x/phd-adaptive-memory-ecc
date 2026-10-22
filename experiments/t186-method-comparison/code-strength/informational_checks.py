"""Addressed checks of W/threshold transfer and whole-cell certificates."""
from fractions import Fraction as F
import json

from codec import ROOT
from informational import intervals,calendar,coefficient,majorant,endpoint_upper


def run(cfg,information):
    passed=[]
    def check(name,x):
        if not x:raise AssertionError(name)
        passed.append(name)
    W=cfg['words'];factor=F(39,152);rho=F('.048')
    for q in (F('.0001'),F('.001'),F('.1')):
        for t in (F(2),F(90),F(200)):
            old=intervals.primitive(q,t,rho,F('.001'))
            new=intervals.primitive(q*factor,t,rho,F('.001')*factor)
            # Intervals enclose the exact scale identity, not merely close floats.
            scaled=old*intervals.I(factor)
            check(f'growth cone scales q AND ell at {q},{t}',new.lo<=scaled.hi and scaled.lo<=new.hi)
    for row in information['candidates']:
        k=row['k'];c=row['calendar'];p=row['environment'];ma=row['majorant'];cells=ma['cells']
        check(f'k{k} new exposure and lower channel',p['rate_scale']==factor and p['ell']==F('.001')*factor and c['phi']==1-F(1,W))
        check(f'k{k} addresses and timers',k*c['inverse_address']%W==1 and c['zero_union_slack']>=0 and c['recovery']['lower']>=c['long_timer']['upper']+c['tau'])
        check(f'k{k} all q-cells contiguous and complete',cells[0]['lo']==p['b'] and cells[-1]['hi']==p['B'] and all(x['hi']==y['lo'] for x,y in zip(cells,cells[1:])))
        check(f'k{k} interval certificates not point samples',all(x['left_slack']>=0 and x['right_slack']>=0 and
              ma['u']+ma['v']*((x['lo']+x['hi'])/2-p['b'])-x['K_upper']*((x['lo']+x['hi'])/2)**2>=0 for x in cells))
        check(f'k{k} below-background covered',ma['below_background_slack']>=0)
        check(f'k{k} computed K is nonincreasing',all(x['K_upper']>=y['K_upper'] for x,y in zip(cells,cells[1:])))
        check(f'k{k} coupling uses beta0',row['risk']['coupling_beta']==F(1,2*W))
        # A2/B2 generalization: deviation of mandatory phase from k*g*r is
        # at most7(g-c); interval count <= length/step +2 endpoints + deviation.
        M=cfg['adaptive']['information_numeric']['phase_cells'];ratio=c['TP']/c['TM']
        excess=F(W,k*M)*(ratio-1)+F(7*(c['g']-c['c']),k*c['g'])*ratio+2+2*c['J']/(k*c['g']*c['TM'])
        check(f'k{k} four-word phase discrepancy valid at new W',excess<4)
        phases=[k*c['g']*r+(c['c']-c['g'])*(k*r%8) for r in range(W)]
        length=F(W*c['g'],M);circ=phases+[x+k*W*c['g'] for x in phases]
        end=0;count=0
        for start in range(W):
            while end<start+W and M*(circ[end]-circ[start])<=length*M:end+=1
            count=max(count,end-start)
        check(f'k{k} exact cyclic phase-count oracle',count<=F(W,k*M)+4)
    selected=information['selected'];c=selected['calendar'];p=selected['environment']
    for q in (p['b'],p['ell'],p['B']/2,p['B']):
        n=c['ka']//2;lo,hi=F(3,8),F(4,8)
        for side in (False,True):
            coarse=endpoint_upper(q,p['rho'],p['ell'],c,n,lo,hi,side)
            for a,b in ((lo,(lo+hi)/2),((lo+hi)/2,hi)):
                check(f'phase refinement enclosure q{q} side{side} a{a}',
                      endpoint_upper(q,p['rho'],p['ell'],c,n,a,b,side)<=coarse)
    c1=calendar(cfg,1)
    check('ka1 reduces to mandatory Ps',coefficient(p['B'],p['rho'],p['ell'],c1)==c1['Ps'])
    check('selected greatest preregistered admissible ka',selected['k']==max(x['k'] for x in information['candidates'] if x['sufficient_for_target']))
    # Accepted T119 anchor: same source calendar and environment must produce
    # the EXACT old u/v/integral, despite the now-general W/ell interface.
    old=json.loads((ROOT/'experiments/t119-err-joint-bound/report.json').read_text())['rows'][0]
    oc={k:F(v) if isinstance(v,str) else v for k,v in old['calendar'].items()}
    oc.update(W=524288,c=164,TM=F('.99999e-9'),TP=F('1.00001e-9'),J=F('.5e-9'),gate=320)
    oc['d']=oc['tau']-oc['Pl']+(oc['ka']*oc['g']+7*(oc['g']-164))*oc['TP']+2*oc['J']
    oc['protected_window']=oc['w']-2*oc['J']
    b,B,FS,T=F('.000154704'),F('.244682704'),F('28310.473728'),F(315576000)
    op=dict(b=b,B=B,FS=FS,T=T,ell=F('.001'),rho=F('.048'),S2=b*b*T+(B+b)*FS)
    replay=majorant(cfg,oc,op)
    check('accepted T119 anchor u v integral reproduced exactly',all(replay[k]==F(old['majorant'][k]) for k in ('u','v','integral')))
    return dict(count=len(passed),checks=passed,
                total_certified_q_cells=sum(x['majorant']['cells_count'] for x in information['candidates']),
                phase_words_enumerated=W*len(information['candidates']),old_T119_anchor_exact=True,
                independent_theory_acceptance=False)
