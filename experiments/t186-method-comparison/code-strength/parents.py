"""Exact projection of the common conditional 48-position parent law.

p_s are fractions of bit-hit exposure, not frequencies among parents.
This supplies algebraic coefficients, not a physical p_s or an adaptive Q.
"""
from fractions import Fraction as F
from math import comb
from cost import exact


def choose(n,k):
    return comb(n,k) if 0 <= k <= n else 0


def projected_groups(n, fractions, physical_positions=48):
    N = physical_positions
    if type(n) is not int or type(N) is not int or not 1 <= n <= N:
        raise ValueError("integer active and allocated position counts required")
    if any(isinstance(s,(float,bool)) or str(int(s)) != str(s) for s in fractions):
        raise ValueError("integer parent sizes required")
    p = {int(s):exact(value) for s,value in fractions.items()}
    if len(p)!=len(fractions):
        raise ValueError("duplicate normalized parent size")
    if not p or any(not 1 <= s <= N or v < 0 for s,v in p.items()) or sum(p.values()) != 1:
        raise ValueError("p_s must be a nonnegative normalized bit-hit allocation")
    groups = [F(0) for _ in range(n+1)]
    for s,weight in p.items():
        for j in range(n+1):
            hyper = F(choose(n,j)*choose(N-n,s-j),choose(N,s))
            groups[j] += F(N,s)*weight*hyper
    if sum(F(j)*g for j,g in enumerate(groups)) != n:
        raise ArithmeticError("per-bit exposure conservation failed")
    return groups  # lambda_j = groups[j] * r(t); j=0 is a non-code event


def witness_coefficients(n,t,groups):
    if len(groups) != n+1 or min(groups) < 0 or t not in (1,2) or n <= t:
        raise ValueError("invalid projection/code")
    a = groups[1]
    direct = sum(groups[t+1:])
    if t == 1:
        return dict(linear_direct=direct, quadratic=F(n-1,2*n)*a*a, cubic=F(0))
    b = groups[2]
    return dict(linear_direct=direct,
                quadratic=F(n-2,n)*a*b + (1-F(1,comb(n,2)))*b*b/2,
                cubic=F((n-1)*(n-2),6*n*n)*a**3)


def fixed_u_moment_terms(W,P,moments,coefficients):
    """T187 singleton/constant-mixture U algebra; not an E/app/adaptive test.

    Caller must establish deterministic U cells, initial/service budgets and
    the common class. The direct term is a lifetime expected-count upper.
    No input, period or price is selected by this function.
    """
    if type(W) is not int or W < 1 or exact(P) <= 0:
        raise ValueError("positive memory and period required")
    P=exact(P)
    if any(exact(v) < 0 for v in moments.values()) or any(exact(v) < 0 for v in coefficients.values()):
        raise ValueError("negative moment/coefficient")
    return dict(direct=W*coefficients["linear_direct"]*moments["M1"],
                quadratic=W*coefficients["quadratic"]*P*moments["M2"],
                cubic=W*coefficients["cubic"]*P*P*moments["M3"],
                initial_other_budget=None, E_window_term=None,
                status="pieces only, not complete Q or certificate")
