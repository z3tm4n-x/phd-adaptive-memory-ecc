"""Verbatim T166 positive-series and outward-decimal helpers; pinned in sources.json."""
from fractions import Fraction as F
from functools import lru_cache

@lru_cache(maxsize=None)
def exponential_enclosure(x, terms):
    """e^-x in [1/(S+R),1/S]; R bounds tail of positive e^x series."""
    if x < 0 or terms < 2 or x >= terms+2:
        raise ValueError("positive-series tail ratio must be below one")
    term = total = F(1)
    for k in range(1, terms+1):
        term *= x/k
        total += term
    next_term = term*x/(terms+1)
    tail = next_term/(1-x/F(terms+2))
    return 1/(total+tail), 1/total, tail

def fixed_decimal(x, places, upper=False):
    scale = 10**places
    q,r = divmod(x.numerator*scale, x.denominator)
    if upper and r:
        q += 1
    sign = "-" if q < 0 else ""
    digits = str(abs(q)).zfill(places+1)
    return sign + digits[:-places] + "." + digits[-places:] if places else str(q)

def enclosure(lo, hi, places=36):
    if not lo <= hi:
        raise ArithmeticError("reversed enclosure")
    a, b = fixed_decimal(lo, places), fixed_decimal(hi, places, True)
    midpoint = (F(a)+F(b))/2
    radius = (F(b)-F(a))/2
    return dict(lower=a, upper=b, midpoint=fixed_decimal(midpoint,places+1),
                absolute_error=fixed_decimal(radius,places+1))
