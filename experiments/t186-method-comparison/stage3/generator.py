"""NHPP by cumulative-hazard inversion; continuous law is explicit.

Uniforms drive interarrival integrated intensities. Word/bit labels use an
independent PRNG stream so changing address resolution cannot change times.
50-digit Decimal calculations avoid a long-mission binary64 time ulp.
Integer ns rounding is a declared simulation convention, not continuum Q.
"""
from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal as D,localcontext,ROUND_CEILING
from functools import cached_property
import math
import random
from reuse import formats

NS=10**9


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    low: D
    high: D

    @cached_property
    def slope(self):return (self.high/self.low).ln()/D(self.end-self.start) if self.high!=self.low else D(0)

    def hazard(self,u):
        a=self.slope
        return self.low*((a*u).exp()-1)/a if a else self.low*u

    @cached_property
    def mass(self):return self.hazard(self.end-self.start)

    def inverse(self,h):
        a=self.slope
        return (1+a*h/self.low).ln()/a if a else h/self.low


def parts(ep,env):
    if ep['shape']!='mission':
        lo=float(env['background_per_s'])
        return [Segment(a,b,D(env['background_per_s']) if x==lo else D(env['peak_per_s']),D(env['background_per_s']) if y==lo else D(env['peak_per_s'])) for a,b,x,y in formats.segments(ep,env)]
    b,B=D(env['background_per_s']),D(env['peak_per_s'])
    out=[];previous=0
    for i in range(ep['peaks']):
        s=ep['first_peak_s']+i*ep['peak_interval_s'];r,h,f=ep['rise_s'],ep['hold_s'],ep['fall_s']
        assert previous<=s and s+r+h+f<=ep['horizon_s']
        out += [Segment(previous,s,b,b),Segment(s,s+r,b,B),Segment(s+r,s+r+h,B,B),Segment(s+r+h,s+r+h+f,B,b)]
        previous=s+r+h+f
    out.append(Segment(previous,ep['horizon_s'],b,b))
    return out


def uniform(rng):return D(rng.getrandbits(53)+1)/D(2**53+1)


def generate(ep,cfg,keep_hazards=False):
    with localcontext() as ctx:
        ctx.prec=50
        return _generate(ep,cfg,keep_hazards)


def _generate(ep,cfg,keep_hazards):
    segments=parts(ep,cfg['environment'])
    rates=random.Random(ep['seed']);labels=random.Random(ep['seed']^0x186032023)
    target=-uniform(rates).ln();left=D(0);marks=[];draws=1;maximum_residual=D(0)
    hazards=[]
    for seg in segments:
        right=left+seg.mass
        while target<right:
            local=target-left;u=seg.inverse(local)
            maximum_residual=max(maximum_residual,abs(seg.hazard(u)-local))
            t=D(seg.start)+u
            assert D(seg.start)<=t<=D(seg.end)
            marks.append(dict(t=int((t*NS).to_integral_value(rounding=ROUND_CEILING)),word=labels.randrange(cfg['memory']['words']),bit=labels.randrange(cfg['memory']['bits'])))
            if keep_hazards:hazards.append(str(target))
            target+=-uniform(rates).ln();draws+=1
        left=right
    return dict(episode=ep['id'],horizon_ns=ep['horizon_s']*NS,seed=ep['seed'],marks=marks,
                generation=dict(event_count=len(marks),exponential_draws=draws,segments=len(segments),
                                integrated_intensity=str(left),maximum_inverse_hazard_residual=str(maximum_residual),
                                global_thinning_expected_candidates=str(D(cfg['environment']['peak_per_s'])*ep['horizon_s']),
                                time_rounding='50-digit Decimal inverse then ceil to integer ns'),
                **({'hazards':hazards} if keep_hazards else {}))


def hazard_at(t,segments):
    return sum(s.hazard(min(t,s.end)-s.start) for s in segments if t>s.start)
