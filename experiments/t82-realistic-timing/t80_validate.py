"""Independent Decimal-90 equations, read-only checks of delivered rows."""
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import csv


def dec(x):
    x=F(x)
    return D(x.numerator)/D(x.denominator)


def independent_checks(out,ps):
    checks=[]
    with localcontext() as ctx:
        ctx.prec=90
        for row in csv.DictReader((out/'ERR_best.csv').open()):
            if row['status']!='certified_conditional':continue
            p=ps[int(row['context_id'])]
            n,W,T=D(p['n']),D(p['W']),dec(p['T'])
            b,B,Ps,S2=map(dec,(p['b'],p['B'],p['Ps'],p['S2']))
            ka=D(row['ka']);Pl=ka*Ps;Q=D(row['Q']);beta0=1/(2*W)
            errors=sum(dec(p['q'][k]) for k in ('rho0','delta_exec','delta_svc','delta_E'))
            risk=errors+dec(p['Dstar'])+p['K']*B*Ps/W+beta0*min(Pl*S2,Ps*S2+Pl*Q)
            cf=dec(p['cp'])/dec(p['gm']);DE=D(row['DE'])
            pq=min(D(1),errors+dec(p['Dstar'])+p['K']*b*Ps/W+beta0*Pl*b*b*T)
            flags=DE*(b+dec(p['rF'])+dec(p['rloss']))
            quiet=cf/ka+cf*min(D(1),DE*(1+p['K'])/T+flags+pq)+(2*dec(p['cp'])+dec(p['sigmaX']))/T+dec(p['CX'])
            TQ=D('.9')*T;KQ=D(1000)
            boundary=DE*(KQ+p['K']+KQ*B*(Pl+dec(p['dE'])))/TQ
            returns=cf/ka+cf*min(D(1),boundary+flags+min(D(1),risk))+(2*dec(p['cp'])+dec(p['sigmaX']))*KQ/TQ+dec(p['CX'])
            diffs={k:str(abs(value-D(row[k]))) for k,value in
                   [('risk_upper',risk),('quiet_upper',quiet),('returns_upper',returns)]}
            assert all(D(v)<D('1e-20') for v in diffs.values()),diffs
            checks.append(dict(context_id=int(row['context_id']),mode='ERR-only',decimal90_differences=diffs))
        for row in csv.DictReader((out/'selected_fixed_class.csv').open()):
            if row['status']!='certified_conditional':continue
            p=ps[int(row['context_id'])];mode=row['mode']
            beta=D(p['n']-1)/(2*D(p['n'])*D(p['W']))
            Ps,T,b=map(dec,(p['Ps'],p['T'],p['b']))
            # theta and qR are inputs; reconstruct vc independently.
            qR=2*b;vc=qR+D(row['theta'])*(D('.001')-qR)
            V=min(vc*vc*T,b*b*T+(vc+b)*dec(p['FS']))
            names=['rho0','delta_exec','delta_svc','delta_M','alpha_M']+(['delta_E'] if mode=='combined' else [])
            err=sum(dec(p['q'][k]) for k in names)
            risk=err+dec(p['Dstar'])+p['K']*dec(p['B'])*Ps/D(p['W'])+beta*Ps*(dec(p['S2'])+D(row['ka'])*V)
            assert abs(risk-D(row['risk_upper']))<D('1e-20')
            checks.append(dict(context_id=int(row['context_id']),mode=mode,
                               risk_difference=str(abs(risk-D(row['risk_upper'])))))
        for row in csv.DictReader((out/'fixed_comparator.csv').open()):
            # Full-range boundary recomputed from raw environmental inputs,
            # without invoking T58 or the production fixed-period function.
            p=ps[len([r for r in checks if r.get('mode')=='fixed'])]
            T,b,B,FS=map(dec,(p['T'],p['b'],p['B'],p['FS']))
            s2=min(B*B*T,B*(b*T+FS),b*b*T+(B+b)*FS)
            beta=D(p['n']-1)/(2*D(p['n'])*D(p['W']))
            e=sum(dec(p['q'][k]) for k in ('rho0','delta_exec','delta_svc'))+dec(p['Dstar'])
            slope=dec(p['tp'])*(beta*s2+p['K']*B/D(p['W']))
            M=int((dec(p['eps'])-e)/slope)
            assert M==int(row['fixed_strong_M'])
            assert e+M*slope<=dec(p['eps'])<e+(M+1)*slope
            checks.append(dict(context_id=len([r for r in checks if r.get('mode')=='fixed']),mode='fixed',M=M,next_quantum_rejected=True))
    return dict(precision=90,points=len(checks),checks=checks,independent_of_production_equations=True,
                delivered_CSV_rounding_tolerance='1e-20; exact production acceptance remains directed',
                physical_qualification=False)
