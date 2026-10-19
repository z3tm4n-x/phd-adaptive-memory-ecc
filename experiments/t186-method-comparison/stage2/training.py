"""Exact rational ridge; train labels are delivered ERR, never true marks."""
from fractions import Fraction as F
from policies import HOUR


def fit(deliveries):
    pairs=[]
    hourly={}
    for name,history in sorted(deliveries.items()):
        assert name.startswith('train_')
        counts=[0]*24
        for item in history:
            hour=item['t']//HOUR
            if hour<24:
                counts[hour]+=1
        hourly[name]=counts
        for h in range(6,24):
            pairs.append(([1]+counts[h-6:h],counts[h]))
    size=7
    A=[[sum(F(x[i])*x[j] for x,y in pairs)+(1 if i==j and i else 0) for j in range(size)] for i in range(size)]
    rhs=[sum(F(x[i])*y for x,y in pairs) for i in range(size)]
    M=[a+[y] for a,y in zip(A,rhs)]
    for j in range(size):
        p=next(i for i in range(j,size) if M[i][j])
        M[j],M[p]=M[p],M[j]
        d=M[j][j]
        M[j]=[x/d for x in M[j]]
        for i in range(size):
            if i!=j:
                d=M[i][j]
                M[i]=[a-d*b for a,b in zip(M[i],M[j])]
    weights=[row[-1] for row in M]
    assert all(sum(A[i][j]*weights[j] for j in range(size))==rhs[i] for i in range(size))
    return dict(weights=[str(x) for x in weights],weights_decimal=[float(x) for x in weights],
                normal_equations_residual_exact=['0']*7,training_pairs=len(pairs),
                hourly_delivered_ERR=hourly,ridge=1,intercept_penalized=False,
                scope='own Chen analog; training on fixed-FAST observation law; adaptive covariate shift unresolved')
