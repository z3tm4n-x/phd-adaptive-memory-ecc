"""Exact bounded-memory integration of checked bus intervals.

No controller/RTL/acceleration code is called. Adjacent observed clean pulses
may be stored as an equal periodic function, not inferred from policy intent.
Within a partition without endpoint piece changes, a sliding integral obeys
F(x+4704)=F(x)+constant. Its maximum lies in the first or last period.
"""
import bisect

PERIOD=4704
STARTS=tuple((r//8)*1568+(r%8)*164 for r in range(24))
LOW=STARTS[::3]
EDGES=tuple(sorted(set(STARTS+tuple(s+92 for s in STARTS))))


def integral(t,low=False):
    if t<=0:return 0
    q,r=divmod(t,PERIOD);starts=LOW if low else STARTS
    i=bisect.bisect_left(starts,r)
    return q*len(starts)*92+(max(i-1,0)*92+min(r-starts[i-1],92) if i else 0)


class Ledger:
    def __init__(self):
        self.pieces=[];self.total=0

    def add(self,a,b,mode):
        if b<=a:return
        # mode: -1 = continuous busy, 0/1 = checked FAST/LOW pulse train.
        value=b-a if mode==-1 else integral(b,bool(mode))-integral(a,bool(mode))
        assert value>=0
        self.total+=value
        allowed={mode}
        if mode==0 and b-a==92 and integral(b,True)-integral(a,True)==92:
            allowed.add(1)
        if self.pieces:
            pa,pb,pm,pv=self.pieces[-1];assert pb<=a,('bus overlap',pb,a)
            for m in pm & allowed:
                gap=a-pb if m==-1 else integral(a,bool(m))-integral(pb,bool(m))
                if gap==0:
                    self.pieces[-1]=(pa,b,{m},pv+value);return
        self.pieces.append((a,b,allowed,value))

    def explicit(self,a,b):
        # A true clean CONTROL pulse can be represented by the same function.
        # Corrective/application/partial pulses remain explicit, not rounded.
        if b-a==92 and integral(b)-integral(a)==92:self.add(a,b,0)
        else:self.add(a,b,-1)

    def peak(self,horizon,width=1_000_000):
        assert horizon>=width
        pieces=[(a,b,min(m),v) for a,b,m,v in self.pieces]
        ends=[b for a,b,m,v in pieces];sums=[0]
        for a,b,m,v in pieces:sums.append(sums[-1]+v)
        assert sums[-1]==self.total
        def prefix(t):
            i=bisect.bisect_right(ends,t);v=sums[i]
            if i<len(pieces):
                a,b,m,_=pieces[i]
                if t>a:v+=t-a if m==-1 else integral(t,bool(m))-integral(a,bool(m))
            return v
        boundaries={0,horizon-width}
        for a,b,m,v in pieces:
            for p in (a,b,a-width,b-width):
                if 0<=p<=horizon-width:boundaries.add(p)
        boundaries=sorted(boundaries)
        residues=sorted(set(EDGES+tuple((s-width)%PERIOD for s in EDGES)))
        best=(-1,0)
        def candidate(x):
            nonlocal best
            v=prefix(x+width)-prefix(x)
            if (v,-x)>best:best=(v,-x)
        for a,b in zip(boundaries,boundaries[1:]):
            for lo,hi in ((a,min(b,a+PERIOD)),(max(a,b-PERIOD),b)):
                candidate(lo);candidate(hi)
                for q in range(lo//PERIOD,hi//PERIOD+1):
                    base=q*PERIOD
                    for r in residues:
                        x=base+r
                        if lo<=x<=hi:candidate(x)
        if len(boundaries)==1:candidate(boundaries[0])
        return best[0],-best[1]
