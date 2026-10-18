"""Unchanged E slots, with the T196 sufficient fixed calendar as a new class."""
from reuse import calendar
ceildiv=calendar.ceildiv

class Grid(calendar.Grid):
    def __init__(self,words=524288,period=None):
        super().__init__(words)
        self.startup=words*196;self.period=period;self.groups=words//8
        assert period is None or period%4==0 and period>=self.startup
        self.max_frame=1568 if period is None else 4*ceildiv(period,4*self.groups)
        self.max_gap=self.max_frame-7*164

    def phase(self,r):return 4*((r*self.period)//(4*self.groups))

    def group_before(self,u):
        r=min(self.groups-1,u*self.groups//self.period+1)
        while self.phase(r)>u:r-=1
        while r+1<self.groups and self.phase(r+1)<=u:r+=1
        return r

    def start(self,j):
        if self.period is None or j<self.words:return super().start(j)
        n,q=divmod(j-self.words,self.words);r,l=divmod(q,8)
        return self.startup+n*self.period+self.phase(r)+164*l

    def first(self,t):
        if self.period is None or t<self.startup:return super().first(t)
        n,u=divmod(t-self.startup,self.period);r=self.group_before(u)
        l=min(8,ceildiv(u-self.phase(r),164))
        return self.words+n*self.words+8*r+l

    def grant(self,t):
        """First app-start >= t. The caller has already charged ingress."""
        if self.period is None:return max(0,ceildiv(t-1312,1568))*1568+1312
        if t<self.startup:
            s=max(0,ceildiv(t-1312,1568))*1568+1312
            if s<self.startup:return s
        v=t-self.startup-1312
        if v<=0:return self.startup+1312
        n,u=divmod(v,self.period);r=self.group_before(u)
        if self.phase(r)<u:r+=1
        if r==self.groups:n+=1;r=0
        return self.startup+n*self.period+self.phase(r)+1312
