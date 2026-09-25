"""Parameter transfer only: unchanged accepted singleton controller + SR ledger."""
from pathlib import Path
import json, math, sys, hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent
ACCEPTED=ROOT.parents[1]/'RE-INTERNAL-COUNT-CONTROL-01'
sys.path.insert(0,str(ACCEPTED))
import core
import simulate as accepted

def config():
    return json.loads((ROOT/'config.json').read_text(encoding='utf-8'))

def sr_ledger(c):
    d=c['environment']['mean_dwell_seconds'][0]
    old=core.arithmetic_ledger(c,d); terms=old['terms'].copy()
    H=c['horizon_seconds']; hi=c['environment']['b_high'];cc=c['controller']
    nb=math.ceil(H/cc['backup_period_seconds']);N=int(H/min(c['periods_seconds']))
    vmax=(H+cc['backup_period_seconds'])*(cc['pending_cap']*hi+hi*hi*cc['backup_period_seconds']/2)/c['memory']['words']
    u=2**-53; gamma=lambda j:j*u/(1-j*u)
    terms['value_recursion']=2*N*25*gamma(256*nb)*vmax
    return dict(terms=terms,total_bound=sum(terms.values()),vmax=vmax,affine_guard=25,elementary_function_ulp_assumption=4)

def build():
    c=config(); ledger=sr_ledger(c)
    assert ledger['total_bound']<=c['controller']['numerical_allowance']
    m=core.build_model(c,c['environment']['mean_dwell_seconds'][0],cache=False)
    p=accepted.pack(m,c['epsilon'][0])
    assert np.all(m.kernels>=0) and np.isfinite(m.kernels).all()
    from decimal import Decimal,localcontext
    with localcontext() as ctx:
        ctx.prec=60
        mass_error=max(abs(sum((Decimal(float(x)) for x in m.kernels[a,:,i,:].flat),Decimal(0))-1) for a in range(len(m.periods)) for i in range(len(m.initial)))
    k=c['controller']['pending_cap'];C=c['controller']['count_cap']
    for a in range(len(m.periods)):
        for y in range(C+1):
            for i in range(2*(k+1)):
                row=m.kernels[a,y,i]
                if y<C and i%(k+1)>y: assert np.all(row==0)
                else: assert np.all(row>0)
    cert=dict(reference_only='singleton uniform marks, instantaneous correction at scan epochs; NOT a grouped-model certificate',parameters=c,error=m.error,sr_arithmetic=ledger,backup_potential=float(m.initial@m.value[-1]),delta=m.error['whole_horizon_delta'],initial_slack=p.slack,decimal_row_mass_error=str(mass_error),minimum_positive_entry=float(m.kernels[m.kernels>0].min()),build_seconds=m.build_seconds if hasattr(m,'build_seconds') else None,accepted_source_sha256={f:hashlib.sha256((ACCEPTED/f).read_bytes()).hexdigest() for f in ('core.py','simulate.py','derivation.md')})
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs/reference_certificate.json').write_text(json.dumps(cert,indent=2)+'\n',encoding='utf-8',newline='\n')
    np.savez_compressed(ROOT/'outputs/controller_tables.npz',**{f:getattr(p,f) for f in p.__dataclass_fields__})
    print(json.dumps({k:cert[k] for k in ('backup_potential','delta','initial_slack','decimal_row_mass_error','minimum_positive_entry')}))
    return m,p

def packed():
    a=np.load(ROOT/'outputs/controller_tables.npz')
    return accepted.Packed(**{k:(a[k].item() if a[k].ndim==0 else a[k]) for k in a.files})

if __name__=='__main__': build()
