"""Independent enumeration of all 2**W live states plus absorption (float audit)."""
from fractions import Fraction
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import expm_multiply

def generator(W,n):
    A = 1 << W
    rows,cols,data = [],[],[]
    for state in range(A):
        rows.append(state); cols.append(state); data.append(-1.)
        for word in range(W):
            dirty = (state >> word) & 1
            rows.append(state); cols.append(state ^ (1 << word))
            data.append(1/(W*n) if dirty else 1/W)
            if dirty:
                rows.append(state); cols.append(A); data.append((n-1)/(W*n))
    matrix = coo_matrix((data,(rows,cols)),shape=(A+1,A+1)).tocsr()
    if np.max(np.abs(np.asarray(matrix.sum(axis=1)).ravel())) > 1e-14:
        raise ArithmeticError("global generator row sums")
    return matrix

def enumerate_reference(case, disable_fences=False):
    W,n = case["W"],case["n"]
    G = generator(W,n)
    A = 1 << W
    probability = np.zeros(A+1); probability[0] = 1.
    events = {}
    def point(t):
        return events.setdefault(t,dict(fences=[],rate=None))
    # Direct index expression, not exact.py's interval/schedule construction.
    if not disable_fences:
        for k in range(int(case["T"]/case["period"])+2):
            for word in range(W):
                t = Fraction(k*W+word,W)*case["period"]+case["D"]
                if t <= case["T"]:
                    point(t)["fences"].append(word)
    for a,b,r in case["segments"]:
        point(a)["rate"] = float(r)
        point(b)
    point(case["T"])
    previous,rate = Fraction(0),0.
    max_drift,min_mass = 0.,0.
    for instant,action in sorted(events.items()):
        if instant > previous and rate:
            probability = expm_multiply((G.T*(rate*float(instant-previous))),probability,
                                        traceA=-rate*float(instant-previous)*A)
        for word in action["fences"]:
            destinations = np.arange(A+1,dtype=np.int64)
            destinations[:-1] &= ~(1 << word)
            probability = np.bincount(destinations,weights=probability,minlength=A+1)
        max_drift = max(max_drift,abs(float(probability.sum())-1))
        min_mass = min(min_mass,float(probability.min()))
        if action["rate"] is not None:
            rate = action["rate"]
        previous = instant
    if max_drift > 2e-12 or min_mass < -2e-12:
        raise ArithmeticError("enumerated reference mass failure")
    return dict(Q=float(probability[A]),states=A+1,max_mass_drift=max_drift,
                min_probability=min_mass,precision="float64 cross-check, not the certificate")
