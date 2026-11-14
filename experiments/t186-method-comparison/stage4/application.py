"""Exact prefix price without enumerating a huge app/fixed-calendar LCM."""
from reuse import legacy_app
from grid import Grid
DURATION=legacy_app.DURATION

class Application(legacy_app.Application):
    def __init__(self,profile,config,grid=None,words=524288):
        self.grid=grid or Grid(words);self.words=self.grid.words
        self.spec=profile;self.id=profile['id'];self.m=profile['pairs_per_epoch']
        self.epoch=profile['epoch_ns'];self.first=config['first_ns']
        self.multiplier=config['address_multiplier'];self.inverse=pow(self.multiplier,-1,self.words)
        self.inbound=config['inbound_ns'];self.outbound=config['outbound_ns']+config['ready_ns']
        self.offsets=profile['read_offsets_ns'];self.write_delta=profile['write_offset_ns']
        if self.m:
            points=sorted(self.arrival(q,k) for q in range(2*self.m) for k in DURATION)
            self.min_spacing=min(b-a for a,b in zip(points,points[1:]))
            assert self.min_spacing>3000
        else:self.min_spacing=None

    def start(self,q,kind):return self.grid.grant(self.arrival(q,kind)+self.inbound)

    def pulse_prefix(self,t,kind=None):
        if kind is None:return sum(self.pulse_prefix(t,k) for k in DURATION)
        q=self.last_q(t-1,kind)
        return (q+1)*DURATION[kind]-max(0,self.start(q,kind)+DURATION[kind]-t) if q>=0 else 0

    def summary(self,H):
        counts={};pending=[]
        for k,d in DURATION.items():
            counts[k]=dict(arrived=self.last_q(H,k,False)+1,started=self.last_q(H-1,k)+1,
                           memory_completed=self.last_q(H-d,k)+1,replied=self.last_q(H-d-self.outbound,k)+1)
            q=self.last_q(H,k,False)
            if q>=0:
                s=self.start(q,k);end=s+d;reply=end+self.outbound
                if reply>H:pending.append(dict(q=q,kind=k,word=self.word(q),arrival=self.arrival(q,k),start=s,end=end,
                                              reply=reply,charged_ns=max(0,min(H,end)-s),
                                              phase='inbound/wait' if s>=H else 'memory' if end>H else 'outbound/ready'))
        return dict(profile=self.id,counts=counts,pending=pending,bus=self.work(0,H),
                    response_delay_bound_ns=self.inbound+self.grid.max_frame+max(DURATION.values())+self.outbound,
                    response_bound_scope='deterministic calendar bound, not an observed maximum or physical WCET',
                    minimum_arrival_spacing_ns=self.min_spacing,aggregation='integer prefix counts; no joint-period enumeration',
                    transport_request_records=sum(v['arrived'] for v in counts.values()),
                    transport_completed_reply_records=sum(v['replied'] for v in counts.values()))
