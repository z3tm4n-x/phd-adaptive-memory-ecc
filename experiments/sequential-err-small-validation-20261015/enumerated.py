"""Independent full-memory enumeration; deterministic phase selects active word."""
from fractions import Fraction
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import expm_multiply

def generator(W,n):
    masks=1<<W
    A=2*masks
    rows,cols,data=[],[],[]
    for state in range(A):
        mask=state%masks
        rows.append(state); cols.append(state); data.append(-1.)
        for w in range(W):
            dirty=(mask>>w)&1
            rows.append(state); cols.append(state^(1<<w))
            data.append(1/(W*n) if dirty else 1/W)
            if dirty:
                rows.append(state); cols.append(A); data.append((n-1)/(W*n))
    G=coo_matrix((data,(rows,cols)),shape=(A+1,A+1)).tocsr()
    if np.max(np.abs(np.asarray(G.sum(axis=1)).ravel()))>1e-14:
        raise ArithmeticError("global generator row sums")
    return G

def reference(case,disable_service=False):
    W,n=case["W"],case["n"]
    masks=1<<W; A=2*masks
    G=generator(W,n)
    v=np.zeros(A+1); v[0]=1.
    points={}
    def at(t):
        return points.setdefault(t,dict(read=[],release=[],rate=None))
    if not disable_service:
        for k in range(int(case["T"]/case["period"])+2):
            for w in range(W):
                e=Fraction(k*W+w,W)*case["period"]
                f=e+case["D"]
                if e<=case["T"]: at(e)["read"].append(w)
                if f<=case["T"]: at(f)["release"].append(w)
    for a,b,r in case["segments"]:
        at(a)["rate"]=float(r); at(b)
    at(case["T"])
    previous,rate=Fraction(0),0.
    max_drift=min_mass=0.
    active=None
    for t,op in sorted(points.items()):
        if t>previous and rate:
            v=expm_multiply(G.T*(rate*float(t-previous)),v,
                           traceA=-A*rate*float(t-previous))
        for w in op["read"]:
            if active is not None:
                raise ArithmeticError("global pending overlap")
            destinations=np.arange(A+1,dtype=np.int64)
            physical=destinations[:-1]%masks
            destinations[:-1]=physical+((physical>>w)&1)*masks
            v=np.bincount(destinations,weights=v,minlength=A+1)
            active=w
        for w in op["release"]:
            if active!=w:
                raise ArithmeticError("release without matching snapshot")
            destinations=np.arange(A+1,dtype=np.int64)
            physical=destinations[:-1]%masks
            pending=destinations[:-1]//masks
            destinations[:-1]=np.where(pending,physical&~(1<<w),physical)
            v=np.bincount(destinations,weights=v,minlength=A+1)
            active=None
        max_drift=max(max_drift,abs(float(v.sum())-1))
        min_mass=min(min_mass,float(v.min()))
        if op["rate"] is not None: rate=op["rate"]
        previous=t
    if max_drift>2e-12 or min_mass< -2e-12:
        raise ArithmeticError("full-memory mass check")
    return dict(Q=float(v[A]),states=A+1,max_mass_drift=max_drift,min_probability=min_mass,
                active_operation_word_at_T=active,precision="float64 independent cross-check; not certificate")
