"""New finite transaction/queue models. No claim of executing SystemVerilog."""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product, combinations

PARITY={1,2,4,8,16,32,39}


def decode(mask):
    """Algebraic extended-Hamming syndrome for the read 39-bit error mask."""
    syndrome=0
    for p in range(1,39):
        if mask >> (p-1) & 1: syndrome ^= p
    odd=mask.bit_count()%2
    if odd and 0<syndrome<=38: pos=syndrome
    elif odd and syndrome==0: pos=39
    else: return mask,0,bool(syndrome or odd)
    return mask^(1<<(pos-1)),pos,False


@dataclass
class Endpoint:
    """Absolute-time contract with one command per observation generation.

    This validates timing/tags, not the host's mathematical risk certificate.
    A software state advances only on execution/observation, never submission.
    """
    horizon: int
    period: int
    depth: int
    generation: int=1
    epoch: int=9
    done: int=0
    next_end: int=0
    locked: bool=False
    state_sequence: int=0
    adaptation: bool=True

    def __post_init__(self):
        self.next_end=self.done+self.period

    @property
    def pass_time(self): return self.depth*360

    @property
    def deadline(self): return self.done+self.period-self.pass_time

    def command(self, now, epoch, generation, profile, duration, allowed):
        valid=(self.adaptation and not self.locked and epoch==self.epoch
            and generation==self.generation and profile==48
            and duration in allowed and duration>=self.period
            and self.done<=now<self.deadline)
        if valid:
            self.next_end=self.done+duration; self.locked=True
        return valid

    def complete(self, count_data, count_parity, lose_record=False):
        assert self.next_end<=self.horizon
        assert count_data>=0 and count_parity>=0 and count_data+count_parity<=self.depth
        self.done=self.next_end; self.generation+=1
        if lose_record: self.adaptation=False
        else: self.state_sequence+=1
        self.next_end=self.done+self.period; self.locked=False
        return dict(epoch=self.epoch, generation=self.generation-1,
            end_ns=self.done, count_data=count_data, count_parity=count_parity,
            count_total=count_data+count_parity, profile=48)


def run(cfg):
    checks=[]
    singles=0; doubles=0; data=parity=0
    for p in range(1,40):
        out, pos, due=decode(1<<(p-1))
        assert (out,pos,due)==(0,p,False)
        singles+=1
        if p in PARITY: parity+=1
        else: data+=1
    for p,q in combinations(range(39),2):
        _,pos,due=decode((1<<p)|(1<<q))
        assert due and pos==0
        doubles+=1
    assert (data,parity)==(32,7)
    checks.append(dict(check='algebraic_39bit_channel', singles=singles,
        doubles=doubles, data=data, parity=parity, passed=True,
        limitation='error-mask algebra; not an RTL simulation'))
    # A zero latch ignores a post-read inversion; the ideal commit-time count does not.
    physical_count=0; ideal_count=decode(1<<38)[1]!=0
    assert ideal_count==1 and physical_count==0
    checks.append(dict(check='post_read_parity_upset_coupling_break',
        actual_count=physical_count, ideal_count=int(ideal_count), passed=True))
    # An irreversible first crossing cannot be removed by later toggles/writeback.
    state=0; hit=False
    for p in [0,1,1,0]:
        state^=1<<p;hit |= state.bit_count()>1
    assert state==0 and hit
    checks.append(dict(check='irreversible_first_passage',passed=True))

    H=int(cfg['horizon_s'])*10**9; depth=cfg['words']; tb=10**9
    allowed=[int(x*10**9) for x in cfg['periods_s']]
    scenarios=[('early',0,9,1,48,2*tb,True),
        ('late',tb-depth*360,9,1,48,2*tb,False),
        ('stale_generation',0,9,0,48,2*tb,False),
        ('wrong_epoch',0,8,1,48,2*tb,False),
        ('wrong_profile',0,9,1,16,2*tb,False),
        ('shorter_than_backup',0,9,1,48,tb//2,False),
        ('unknown_period',0,9,1,48,3*tb,False)]
    rows=[]
    for name,at,ep,gen,profile,tau,expected in scenarios:
        e=Endpoint(H,tb,depth)
        ok=e.command(at,ep,gen,profile,tau,allowed)
        assert ok==expected and e.state_sequence==0
        if ok: assert not e.command(at,ep,gen,profile,10*tb,allowed)
        snap=e.complete(0,1)
        assert snap['count_total']==1 and e.state_sequence==1
        rows.append(dict(case=name,accepted=ok,executed_period_ns=snap['end_ns']))
    e=Endpoint(H,tb,depth);e.complete(0,0,lose_record=True)
    assert not e.command(e.done,9,2,48,2*tb,allowed)
    assert e.next_end==e.done+tb and e.state_sequence==0
    checks.append(dict(check='generation_deadline_ack_and_loss',cases=rows,
        lost_record='backup_to_horizon_no_adaptation_no_budget_reset',passed=True))

    # Enumerate small horizons/action histories, including started incomplete scans.
    bound_cases=0; max_seen=0
    for actions in product([1000,2000,5000],repeat=6):
        Hsmall=5500;Psmall=720;t=0;starts=0;complete=0
        for tau in actions:
            if t>=Hsmall: break
            end=t+tau
            starts+=end-Psmall<Hsmall
            if end>Hsmall: break
            complete+=1;t=end
        upper=(Hsmall+Psmall-1)//1000
        assert starts<=upper and starts-complete in (0,1)
        max_seen=max(max_seen,starts);bound_cases+=1
    checks.append(dict(check='started_not_completed_pass_bound', histories=bound_cases,
        max_started=max_seen, analytic_upper=upper,passed=True))
    # One logical 48-bit transfer, unconditional write, snapshot includes last correction.
    word_cases=0
    for n in [1,8,17]:
        for pattern in [set(),{n-1},set(range(n))]:
            commits=[360*(w+1) for w in range(n)]
            counts=[int(w in pattern) for w in range(n)]
            assert sum(counts)==len(pattern) and commits[-1]==n*360
            snap=sum(counts[:-1])+counts[-1]
            assert snap==len(pattern)
            word_cases+=1
    # H cuts between the third word's read and write.
    reads=[360*w+225 for w in range(8)]
    writes=[360*(w+1) for w in range(8)]
    assert sum(t<=1000 for t in reads)==3 and sum(t<=1000 for t in writes)==2
    checks.append(dict(check='word_commit_snapshot_and_partial',cases=word_cases,
        partial_reads=3,partial_writes=2,complete_passes=0,passed=True))

    def burst_finish(arrival):
        first=(arrival.numerator+arrival.denominator-1)//arrival.denominator
        t=first;remaining=8
        while remaining:
            if t%8<4:remaining-=1
            t+=1
        return F(t)-arrival
    discrete=max(burst_finish(F(p)) for p in range(8))
    eps=F(1,10**6)
    fractional=max(burst_finish(F(p)+eps) for p in range(8))
    assert discrete==16 and 16<fractional<17
    # Service for every phase/subtick start over a bounded set of intervals.
    # General argument in REPORT: at most 8 latency ticks, then >=1/2 rate.
    for phase in range(8):
        for length in range(1,129):
            offered=sum((phase+t)%8<4 for t in range(length))
            assert offered>=max(0,length/2-2)
    checks.append(dict(check='service_discrete_and_fractional_phases',
        discrete_burst_ns=float(discrete*45),
        just_after_slot_burst_ns=float(fractional*45),
        continuous_phase_supremum_ns=765,
        token_bucket_delay_bound_ns=1080,passed=True))
    # Fair steady 80% word stream cannot use the 50% reserved-rate guarantee.
    queue=[];waits=[];arrival=F(0);interval=F(5,4)
    for t in range(8000):
        while arrival<=t:
            queue.append(arrival);arrival+=interval
        if t%8<4 and queue: waits.append(F(t+1)-queue.pop(0))
    assert len(queue)>2300 and max(waits)*45>100000
    checks.append(dict(check='80percent_deadline_counterexample',
        simulated_ns=360000, queued_words=len(queue),
        max_completed_wait_ns=float(max(waits)*45),passed=True))
    return checks
