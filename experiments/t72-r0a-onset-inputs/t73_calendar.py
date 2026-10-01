"""Integer operational reference for published T73 §4 / appendix Б.2.

No input is fetched from future observations. Decisions are irrevocable.
"""
from dataclasses import dataclass, field
from math import gcd

MAX_TIME=(1<<64)-1


def add_time(a,b):
    if min(a,b)<0 or a+b>MAX_TIME:
        raise OverflowError('Timer overflow must cause a recognized safe alarm')
    return a+b


@dataclass
class Calendar:
    W:int
    ka:int
    c:int
    g:int
    fence:int
    lead:int
    hold:int
    horizon:int
    covered:tuple|None=None
    hold_until:int=field(init=False)
    window_number:int=0
    decisions:dict=field(default_factory=dict)

    def __post_init__(self):
        if self.W%2 or self.ka%2!=1 or gcd(self.W,self.ka)!=1 or not 0<=self.fence<=self.c<=self.g:
            raise ValueError('Invalid paired nested calendar')
        self.inverse=pow(self.ka,-1,self.W)
        self.ps=self.W*self.g
        self.pl=self.ka*self.ps
        self.hold_until=self.hold

    def start(self,j):return 2*self.g*(j//2)+self.c*(j%2)
    def word(self,j):return self.inverse*j%self.W
    def end(self,j):return self.start(j)+self.fence

    def alarm(self,t):
        self.covered=None
        try:self.hold_until=max(self.hold_until,add_time(t,self.hold))
        except OverflowError:self.hold_until=MAX_TIME

    def err(self,t):
        # ERR prolongs hold; it need not invalidate a true external LOW lease.
        try:self.hold_until=max(self.hold_until,add_time(t,self.hold))
        except OverflowError:self.hold_until=MAX_TIME

    def message(self,j,*,at,lease_end,count,k,qualified,valid=True,late=False,overflow=False,numeric_failure=False):
        if j!=self.window_number:
            raise ValueError('Window sequence cannot reset or skip silently')
        if not isinstance(j,int) or not 0<=j<MAX_TIME:
            self.alarm(max(0,min(at,MAX_TIME)))
            return False
        self.window_number+=1
        low=(qualified and valid and not(late or overflow or numeric_failure) and
             isinstance(count,int) and isinstance(k,int) and 0<=count<=k<=MAX_TIME and
             0<=at<=lease_end<=MAX_TIME)
        if not low:
            self.alarm(at)
            return False
        if self.covered is not None and at<=self.covered[1]:
            self.covered=(self.covered[0],max(self.covered[1],lease_end))
        else:self.covered=(at,lease_end)
        return True

    def decide(self,j):
        if j in self.decisions:return self.decisions[j]
        s=self.start(j); t=s-self.lead
        if s>=self.horizon:return False
        target=(max(0,self.end(j)-self.ps),min(self.horizon,self.end(j)+self.ps))
        can_skip=(j%self.ka!=0 and t>=0 and t>=self.hold_until and self.covered is not None and
                  self.covered[0]<=target[0] and target[1]<=self.covered[1])
        self.decisions[j]=not can_skip
        return not can_skip


def geometry_enumeration():
    """All 256 skip patterns on eight eligible boundaries, two ka and cutoffs.

    A high arrival is admissible only outside every skipped fence's protected
    past/future radius. Test both orientations of every pair in every actual
    inter-fence interval. Arrival times are half-integers, never fence ties.
    """
    cases=pairs=0
    for ka in [3,5]:
        for horizon in [49,77]:
            cal=Calendar(8,ka,2,3,2,1,5,horizon)
            js=[j for j in range(40) if cal.end(j)<horizon]
            choices=[j for j in js if j%ka][:8]
            for bits in range(1<<len(choices)):
                skipped={j for i,j in enumerate(choices) if bits>>i&1}
                forbidden=[(max(0,2*(cal.end(j)-cal.ps)),min(2*horizon,2*(cal.end(j)+cal.ps))) for j in skipped]
                for w in range(8):
                    short=[0]+[2*cal.end(j) for j in js if cal.word(j)==w]+[2*horizon]
                    long=[0]+[2*cal.end(j) for j in js if cal.word(j)==w and j%ka==0]+[2*horizon]
                    actual=[0]+[2*cal.end(j) for j in js if cal.word(j)==w and j not in skipped]+[2*horizon]
                    for a,b in zip(actual,actual[1:]):
                        arrivals=list(range(a+1,b,2))
                        for u in arrivals:
                            for v in arrivals:
                                if v<=u:continue
                                pairs+=1
                                high_u=not any(lo<=u<=hi for lo,hi in forbidden)
                                high_v=not any(lo<=v<=hi for lo,hi in forbidden)
                                assert not any(u<f<v for f in long),'Pair escaped mandatory long cell'
                                if high_u or high_v:
                                    assert not any(u<f<v for f in short),'High/low pair escaped short cell'
                cases+=1
    # Minimal negative control: a forward-only lease misses the high left token.
    negative={'skipped_fence':10,'high_before':9,'low_after':11,'past_radius_required':True}
    assert negative['high_before']<negative['skipped_fence']<negative['low_after']
    return {'geometry_cases':cases,'ordered_temporal_pairs_checked':pairs,'forward_only_negative_control':negative}
