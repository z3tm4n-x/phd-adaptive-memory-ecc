"""T150: common-history moments and a total probability model, including overflow."""
import math
import numpy as np
from scipy.stats import binom
from scipy.ndimage import maximum_filter1d


def rolling_moments(y, width, dt):
    """All trailing windows; O(n) maximum, no materialized window matrix."""
    y=np.asarray(y,float)
    if width<1 or width>len(y) or np.any(y<0) or not np.isfinite(y).all():
        raise ValueError('invalid rolling series/window')
    n=np.r_[0.,np.cumsum(y)]*dt
    s=np.r_[0.,np.cumsum(y*y)]*dt
    peak=maximum_filter1d(y,size=width,origin=(width-1)//2,mode='constant',cval=-np.inf)[width-1:]
    return n[width:]-n[:-width],s[width:]-s[:-width],peak


def gram_moments(x, dt):
    x = np.asarray(x, float)
    if x.ndim != 2 or not len(x) or np.any(x < 0) or not np.isfinite(x).all() or dt <= 0:
        raise ValueError('finite nonnegative common-bin rates required')
    return x.sum(axis=0)*dt, x.T@x*dt


def assemble(background, duration, integrals, gram):
    n, g = np.asarray(integrals), np.asarray(gram)
    if background < 0 or duration <= 0 or g.shape != (len(n), len(n)):
        raise ValueError('invalid moment dimensions')
    quiet = background**2*duration
    mixed = 2*background*n.sum()
    diagonal = np.trace(g)
    cross = g.sum()-diagonal
    return dict(F=background*duration+n.sum(), S2=quiet+mixed+diagonal+cross,
                background_S2=quiet, mixed_S2=mixed, solar_diagonal=diagonal,
                solar_cross=cross)


def pack(counts, duration, event_n, event_s2, event_peak, off, background, horizon):
    """Unconditional compound-Poisson experiment. Overflow is +inf, never resampled.

    On finite outcomes whole events occupy disjoint time and all remaining time
    has the specified off-mask moments. Event and off-mask rates exclude the
    constant background. This is a model, not a future solar-cycle prediction.
    """
    counts = np.asarray(counts)
    if np.any(counts < 0) or np.any(counts != counts.astype(np.int64)):
        raise ValueError('nonnegative integer event multiplicities required')
    occupied = counts@duration
    overflow = occupied > horizon
    quiet = np.maximum(0., horizon-occupied)
    n = counts@event_n+quiet*off['mean']
    s2 = counts@event_s2+quiet*off['mean_square']
    peak = np.maximum(np.max((counts > 0)*event_peak[None, :], axis=1),
                      np.where(quiet > 0, off['peak'], 0.))
    F = background*horizon+n
    S2 = background**2*horizon+2*background*n+s2
    shape = np.divide(s2, peak*n, out=np.zeros_like(s2), where=peak*n > 0)
    for a in (F, S2, peak, n, s2, shape):
        a[overflow] = np.inf
    return dict(F=F, S2=S2, peak=background+peak, solar_N=n, solar_S2=s2,
                r=shape, overflow=overflow, occupied=occupied)


def q90(a):
    """Order-statistic interval measures MC error at a FIXED model only."""
    ordered = np.sort(a)
    n = len(ordered)
    j = math.ceil(.9*n)-1
    lo = max(0, int(binom.ppf(.025, n, .9))-1)
    hi = min(n-1, int(binom.ppf(.975, n, .9)))
    return float(ordered[j]), float(ordered[lo]), float(ordered[hi])


def overflow_bound(mean, max_duration, horizon):
    k = math.floor(horizon/max_duration)+1
    log_upper = 0. if k <= mean else -mean+k*(1+math.log(mean/k))
    return dict(event_count_necessary=k, log_probability_upper=log_upper,
                probability_upper=math.exp(log_upper))


def shape_transfer(b, p, solar_n, r, horizon):
    if not 0 <= r <= 1 or solar_n > p*horizon or r*p*solar_n < solar_n**2/horizon-1e-8:
        raise ValueError('infeasible fixed-input shape')
    return b*b*horizon+2*b*solar_n+r*p*solar_n
