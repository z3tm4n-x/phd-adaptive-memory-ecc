"""Independent absolute-deadline oracle, no C or RTL update helper imports.

Deadlines are unbounded Python integers. The API's time is the sequence of
processing edges; source time is used ONLY for association of ERR events.
The accepted E/calendar reference is separate and unchanged.
"""
from dataclasses import dataclass

@dataclass
class Oracle:
    now: int=0
    generation: int=0
    last_err: int=0
    short_expiry: int|None=None
    long_expiry: int|None=None
    recovery_expiry: int|None=None
    healthy: bool=True
    started: bool=False
    seen_err: bool=False
    fault: bool=False
    blocked: bool=False
    seen_time: bool=False
    nw: int=4500045002
    nh: int=9000090002
    nr: int=9015504896
    pair: int=22500225010

    def apply(self,v):
        now,gen,src,flags,reserved=v
        if reserved or flags & ~31 or now<self.now or (self.seen_time and now==self.now):
            self.fault=True;return self.snapshot()
        old_healthy=self.healthy
        # A pre-start timer does not advance. Valid missions start before
        # any history. Pre-start event inputs are outside this test contract.
        self.now=now;self.seen_time=True;self.blocked=bool(flags&2)
        if flags&1 and not self.started:
            self.started=True; self.recovery_expiry=now+self.nr
        self.fault |= bool(flags&16)
        if flags&2:
            self.fault |= self.generation==(1<<64)-1 or gen!=self.generation+1
            self.generation=gen;self.healthy=not bool(flags&8)
            if self.healthy and not old_healthy:self.recovery_expiry=now+self.nr
            if flags&4:
                self.short_expiry=now+self.nw
                if self.seen_err and 0<=src-self.last_err<=self.pair:
                    self.long_expiry=now+self.nh
                self.last_err=src;self.seen_err=True
        return self.snapshot()

    def snapshot(self):
        short=max(0,(self.short_expiry or 0)-self.now)
        long=max(0,(self.long_expiry or 0)-self.now)
        rec=self.nr if self.recovery_expiry is None else max(0,self.recovery_expiry-self.now)
        flags=int(self.healthy)+2*self.started+4*self.seen_err+8*self.fault+16*self.blocked+32*self.seen_time
        return (self.now,self.generation,self.last_err,short,long,rec,flags,0)

    def low(self):
        values=self.snapshot()
        return int(self.started and self.healthy and not self.fault and not self.blocked
                   and not any(values[3:6]))
