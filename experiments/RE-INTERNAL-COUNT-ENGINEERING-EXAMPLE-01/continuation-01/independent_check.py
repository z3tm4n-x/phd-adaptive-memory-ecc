"""Independent finite word/bit oracle; no audit mapping/generator helpers.

Enumeration and Poisson uniformization, not expm or dirty-count transitions.
Shared inputs: declared word/bit counts, event marking law, time and rate.
"""
from itertools import combinations, product
import math


def enumerate_survival(words, bits, bit_rate, duration, group_size, tol=1e-14):
    states = list(product(range(bits+1), repeat=words))  # 0 clean; 1..n erroneous bit
    index = {s:i for i,s in enumerate(states)}
    groups = list(combinations(range(words), group_size))
    marks = [(ws, ps) for ws in groups for ps in product(range(1,bits+1), repeat=group_size)]
    destinations = []
    for state in states:
        row = {}
        for ws, ps in marks:
            updated = list(state)
            killed = False
            for word, position in zip(ws,ps):
                if updated[word] == 0:
                    updated[word] = position
                elif updated[word] == position:
                    updated[word] = 0
                else:
                    killed = True
                    break
            if not killed:
                j = index[tuple(updated)]
                row[j] = row.get(j,0) + 1/len(marks)
        destinations.append(row)
    x = bit_rate*duration/group_size
    v = [0.0]*len(states)
    v[index[(0,)*words]] = 1.0
    weight = math.exp(-x)
    cdf = weight
    survival = weight
    for step in range(1,10000):
        out = [0.0]*len(states)
        for i, mass in enumerate(v):
            for j, probability in destinations[i].items():
                out[j] += mass*probability
        v = out
        weight *= x/step
        cdf += weight
        survival += weight*sum(v)
        if step > x and 1-cdf < tol:
            return survival, max(0.0,1-cdf)
    raise RuntimeError('Poisson tail did not converge')
