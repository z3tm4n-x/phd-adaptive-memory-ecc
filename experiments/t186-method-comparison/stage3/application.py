"""Periodic useful work. Count every pulse; materialize only dirty visits.

q indexes a read/write pair. Addresses are a permutation, and each word's
next useful transaction can be found by modular arithmetic, not by replaying
the clean application requests. All counts use integer nanoseconds.
"""
from fractions import Fraction
from math import gcd
from reuse import calendar

ceildiv=calendar.ceildiv
DURATION={'read32':184,'write32':216}


class Application:
    def __init__(self,profile,config,words=524288):
        self.spec=profile
        self.id=profile['id']
        self.m=profile['pairs_per_epoch']
        self.epoch=profile['epoch_ns']
        self.first=config['first_ns']
        self.multiplier=config['address_multiplier']
        self.inverse=pow(self.multiplier,-1,words)
        self.words=words
        self.inbound=config['inbound_ns']
        self.outbound=config['outbound_ns']+config['ready_ns']
        self.offsets=profile['read_offsets_ns']
        self.write_delta=profile['write_offset_ns']
        self.residues=[]
        self.repeat_q=self.m*(1568//gcd(self.epoch,1568)) if self.m else 0
        self.repeat_ns=(1568//gcd(self.epoch,1568))*self.epoch
        if self.m:
            assert len(self.offsets)==self.m
            arrivals=sorted(self.arrival(q,kind) for q in range(2*self.m) for kind in DURATION)
            self.min_spacing=min(b-a for a,b in zip(arrivals,arrivals[1:]))
            assert self.min_spacing>3000,'this executor assumes isolated application transport'
            for kind in DURATION:
                for q in range(self.repeat_q):
                    self.residues.append(dict(q=q,kind=kind,arrival=self.arrival(q,kind),
                                             start=self.start(q,kind),duration=DURATION[kind]))
        else:self.min_spacing=None

    def arrival(self,q,kind):
        return self.first+(q//self.m)*self.epoch+self.offsets[q%self.m]+(self.write_delta if kind=='write32' else 0)

    def start(self,q,kind):
        return ceildiv(self.arrival(q,kind)+self.inbound-1312,1568)*1568+1312

    def word(self,q):
        return self.multiplier*q % self.words

    def last_q(self,t,kind,by_start=True):
        if not self.m:return -1
        delta=self.write_delta if kind=='write32' else 0
        epoch=(t-self.first-delta)//self.epoch
        if epoch<0:return -1
        within=t-self.first-delta-epoch*self.epoch
        r=max((r for r,off in enumerate(self.offsets) if off<=within),default=-1)
        q=epoch*self.m+r
        if by_start:
            while q>=0 and self.start(q,kind)>t:q-=1
        return q

    def next_for_word(self,w,t,kind='write32'):
        if not self.m:return None
        first_q=self.last_q(t-1,kind)+1
        q0=self.inverse*w % self.words
        q=q0+max(0,ceildiv(first_q-q0,self.words))*self.words
        return self.start(q,kind),q

    def active_for_word(self,w,t):
        if not self.m:return None
        q0=self.inverse*w % self.words
        for kind in DURATION:
            maximum=self.last_q(t,kind)
            q=q0+((maximum-q0)//self.words)*self.words
            if q>=0:
                s=self.start(q,kind)
                if s<=t<s+DURATION[kind]:return dict(start=s,q=q,kind=kind,word=w)
        return None

    @staticmethod
    def progression_count(first,step,exclusive_end):
        return max(0,ceildiv(exclusive_end-first,step))

    def pulse_prefix(self,t,kind=None):
        value=0
        for r in self.residues:
            if kind is not None and r['kind']!=kind:continue
            n=self.progression_count(r['start'],self.repeat_ns,t)
            if n:
                last=r['start']+(n-1)*self.repeat_ns
                value+=(n-1)*r['duration']+min(r['duration'],t-last)
        return value

    def work(self,a,b):
        return {kind+'_ns':self.pulse_prefix(b,kind)-self.pulse_prefix(a,kind) for kind in DURATION}

    def summary(self,H):
        counts={kind:dict(arrived=0,started=0,memory_completed=0,replied=0) for kind in DURATION}
        max_delay=0
        for r in self.residues:
            c=counts[r['kind']];step=self.repeat_ns
            c['arrived']+=self.progression_count(r['arrival'],step,H+1)
            c['started']+=self.progression_count(r['start'],step,H)
            c['memory_completed']+=self.progression_count(r['start']+r['duration'],step,H+1)
            c['replied']+=self.progression_count(r['start']+r['duration']+self.outbound,step,H+1)
            if r['start']<H:max_delay=max(max_delay,r['start']+r['duration']+self.outbound-r['arrival'])
        pending=[]
        if self.m:
            for kind in DURATION:
                q=self.last_q(H,kind,by_start=False)
                if q>=0:
                    s=self.start(q,kind);end=s+DURATION[kind];reply=end+self.outbound
                    if reply>H:
                        pending.append(dict(q=q,kind=kind,word=self.word(q),arrival=self.arrival(q,kind),
                                            start=s,end=end,reply=reply,charged_ns=max(0,min(H,end)-s),
                                            phase='inbound/wait' if s>=H else 'memory' if end>H else 'outbound/ready'))
        return dict(profile=self.id,counts=counts,pending=pending,max_response_delay_ns=max_delay,
                    minimum_arrival_spacing_ns=self.min_spacing,aggregation_residues=len(self.residues),
                    bus=self.work(0,H),transport_request_records=sum(x['arrived'] for x in counts.values()),
                    transport_completed_reply_records=sum(x['replied'] for x in counts.values()))

    def intervals(self,H):
        """Literal independent enumeration for short directed verification only."""
        if not self.m:return
        for kind in DURATION:
            q=0
            while self.start(q,kind)<H:
                yield dict(q=q,kind=kind,word=self.word(q),arrival=self.arrival(q,kind),start=self.start(q,kind))
                q+=1

    def interval_count_upper(self,width_ns):
        # The actual spacing gives a pathwise burst bound including one left-edge pulse.
        return 0 if not self.m else ceildiv(width_ns+216,self.min_spacing)+1
