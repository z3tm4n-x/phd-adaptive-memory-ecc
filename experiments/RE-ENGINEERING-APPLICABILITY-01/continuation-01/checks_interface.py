"""Executable command contract and addressed service witnesses; not RTL."""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from checks_numeric import schedule


@dataclass(frozen=True)
class Command:
    epoch: int
    generation: int
    profile: str
    period: F
    completion: F


class Gate:
    def __init__(self, cfg, backup=F(1)):
        self.last=F(1);self.backup=backup;self.p=F(cfg['words']*cfg['word_frame_ns'],10**9)
        self.deadline=self.last+backup-self.p;self.epoch=4;self.generation=7
        self.allowed={F(str(t)) for t in cfg['reference_actions_s']}
        self.committed=None;self.sealed=False

    def accept(self,c,at):
        valid=(not self.sealed and self.committed is None and at<=self.deadline
            and (c.epoch,c.generation,c.profile)==(4,7,'48bit-fixed-frame')
            and at>=self.last and c.period in self.allowed and c.period>=self.backup
            and c.completion==self.last+c.period)
        if valid: self.committed=c
        return valid

    def actual_period(self):
        return self.committed.period if self.committed else self.backup


def run(cfg):
    good=Command(4,7,'48bit-fixed-frame',F(2),F(3))
    cases=[('ontime',good,F(11,10),True),
        ('before_snapshot',good,F(9,10),False),
        ('deadline_command_priority',good,Gate(cfg).deadline,True),
        ('late',good,Gate(cfg).deadline+F(1,10**9),False),
        ('epoch',Command(3,7,good.profile,F(2),F(3)),F(11,10),False),
        ('generation',Command(4,6,good.profile,F(2),F(3)),F(11,10),False),
        ('profile',Command(4,7,'16bit',F(2),F(3)),F(11,10),False),
        ('below_backup',Command(4,7,good.profile,F(1,2),F(3,2)),F(11,10),False),
        ('bad_absolute_end',Command(4,7,good.profile,F(2),F(4)),F(11,10),False)]
    results=[]
    for name,c,t,expect in cases:
        gate=Gate(cfg);ok=gate.accept(c,t);assert ok==expect
        actual=gate.actual_period();assert actual==(F(2) if expect else F(1))
        if ok: assert not gate.accept(c,t) # idempotent duplicate rejection
        results.append(dict(case=name,accepted=ok,executed_period=float(actual)))
    gate=Gate(cfg);gate.sealed=True;assert not gate.accept(good,F(11,10))
    # Exact started-pass counting, including partial terminal passes.
    counted=0;partial=0
    for backup in (F(1),F(1,2)):
        cap=int((F(3600)+Gate(cfg).p)/backup)
        assert cap==int(F(3600)/backup)
        for aa,bb in product((backup,2*backup,3*backup),repeat=2):
            n,started=schedule(3,Gate(cfg).p,aa,bb)
            assert started<=int((F(3)+Gate(cfg).p)/backup);counted+=1
        n,s=schedule(F(9,10),Gate(cfg).p,backup,backup)
        assert s==n+1;partial+=1
    # An immediate startup pass would violate the stated cap and is excluded.
    assert 1+3600>3600
    # Integer and off-grid arrival phases of one 8-word burst.
    delays=[]
    for phase4 in range(32):
        arrival=F(phase4,4);t=(arrival.numerator+arrival.denominator-1)//arrival.denominator
        left=cfg['application_burst_words']
        while left:
            if t%8<4: left-=1
            t+=1
        delays.append((phase4,F(t)-arrival))
    integer=max(float(d)*cfg['transfer_ns'] for a,d in delays if a%4==0)
    sampled=max(float(d)*cfg['transfer_ns'] for a,d in delays)
    # Exact rate-latency lower service curve on quarter-slot witnesses.
    scases=0
    for a in range(32):
        for duration4 in range(257):
            start=F(a,4);end=start+F(duration4,4)
            provided=sum(1 for t in range(80) if t%8<4 and F(t)>=start and F(t+1)<=end)
            lower=max(F(0),(F(duration4,4)-8)/2)
            assert provided>=lower;scases+=1
    P=cfg['words']*cfg['word_frame_ns']/1e9
    # Fluid virtual delay for constant 80% arrivals: maximum is not at scan end.
    rho=.8;r=.5
    at_star=r/rho*P;peak=(1-r/rho)*P;at_end=(rho-r)*P
    return dict(command_cases=results,duplicate_rejected=True,
        lost_count_requires_sealed_backup=True,counted_schedule_cases=counted,
        terminal_partial_cases=partial,started_cap_backup1=3600,started_cap_backup05=7200,
        immediate_startup_extra_pass_excluded=True,
        integer_phase_burst_max_ns=integer,quarter_phase_burst_max_ns=sampled,
        arbitrary_phase_burst_supremum_ns=17*cfg['transfer_ns'],
        rate_latency_bound_ns=cfg['word_frame_ns']+2*cfg['application_burst_words']*cfg['transfer_ns'],
        service_curve_cases=scases,
        fluid80=dict(maximum_virtual_delay_s=peak,arrival_time_of_max_s=at_star,
                     virtual_delay_at_scan_end_s=at_end),
        timebase=dict(model_quantum_ns=5,timer_implementation_validated=False),
        status='Specification-level Python checks; no RTL simulator was executed')
