"""Directed Decimal enclosure, adapted from accepted T82/t80_err.py.

Decimal exp/ln are correctly rounded to nearest; adjacent values enclose
the exact result. Every algebraic operation below has an explicit context.
No global/default Decimal rounding is used for a scientific decision.
"""
from decimal import Decimal as D, Context, ROUND_FLOOR, ROUND_CEILING, ROUND_HALF_EVEN
from fractions import Fraction as F

DOWN = Context(prec=48, rounding=ROUND_FLOOR)
UP = Context(prec=48, rounding=ROUND_CEILING)
NEAR = Context(prec=48, rounding=ROUND_HALF_EVEN)


class I:
    def __init__(self, x, hi=None):
        if hi is not None:
            self.lo, self.hi = D(x), D(hi)
        elif isinstance(x, F):
            self.lo = DOWN.divide(D(x.numerator), D(x.denominator))
            self.hi = UP.divide(D(x.numerator), D(x.denominator))
        else:
            self.lo = self.hi = D(str(x))

    def __add__(self, b):
        b = b if isinstance(b, I) else I(b)
        return I(DOWN.add(self.lo, b.lo), UP.add(self.hi, b.hi))

    def __sub__(self, b):
        b = b if isinstance(b, I) else I(b)
        return I(DOWN.subtract(self.lo, b.hi), UP.subtract(self.hi, b.lo))

    def __mul__(self, b):
        b = b if isinstance(b, I) else I(b)
        return I(min(DOWN.multiply(a, c) for a in (self.lo, self.hi) for c in (b.lo, b.hi)),
                 max(UP.multiply(a, c) for a in (self.lo, self.hi) for c in (b.lo, b.hi)))

    def __truediv__(self, b):
        b = b if isinstance(b, I) else I(b)
        if b.lo <= 0 <= b.hi:
            raise ValueError('interval division across zero')
        return I(min(DOWN.divide(a, c) for a in (self.lo, self.hi) for c in (b.lo, b.hi)),
                 max(UP.divide(a, c) for a in (self.lo, self.hi) for c in (b.lo, b.hi)))

    def exp(self):
        return I(NEAR.next_minus(NEAR.exp(self.lo)), NEAR.next_plus(NEAR.exp(self.hi)))

    def ln(self):
        return I(NEAR.next_minus(NEAR.ln(self.lo)), NEAR.next_plus(NEAR.ln(self.hi)))


def primitive(q, t, rho, ell=F('0.001')):
    """Enclose integral_0^t H_ell^{-1}((H_ell(q)-rho*r)_+) dr."""
    if min(q, t, rho) < 0:
        raise ValueError('negative cone argument')
    if not rho:
        return I(q*t)
    if q <= ell:
        v = min(t, q/(rho*ell))
        return I(q*v-rho*ell*v*v/2)
    qi, ri, li, ti = map(I, (q, rho, ell, t))
    te = (qi/li).ln()/ri
    v1 = I(min(ti.lo, te.lo), min(ti.hi, te.hi))
    z = ti-te
    cap = I(1)/ri
    v2 = I(max(D(0), min(z.lo, cap.lo)), max(D(0), min(z.hi, cap.hi)))
    return qi/ri*(I(1)-(I(0)-ri*v1).exp())+li*(v2-ri*v2*v2/I(2))


def exposure(q, left, right, rho):
    if right < left:
        raise ValueError('reversed interval')
    z = primitive(q, right, rho)-primitive(q, left, rho)
    return I(max(D(0), z.lo), max(D(0), z.hi))
