"""Batch8 progression counts and a small causal boundary model, no T-tick loop."""
from fractions import Fraction as F
from model import NS,ceil


def q_ns(j):return 1568*(j//8)+164*(j%8)


def prefix_indices(t_ns):
    """Number of nonnegative potential starts strictly before t_ns."""
    t=F(t_ns)
    if t<=0:return 0
    frames=t//1568; rem=t-frames*1568
    return frames*8+min(8,ceil(rem/164))


def pass_prefix(indices,k,W):
    return (indices//(k*W))*W+min(W,indices%(k*W))


def count(k,W,left,right):
    """Starts q in [left,right), times in seconds, including complete started E."""
    if right<=left:return 0
    return pass_prefix(prefix_indices(right*NS),k,W)-pass_prefix(prefix_indices(left*NS),k,W)


def union(bands):
    out=[]
    for a,b in sorted(bands):
        if b<=a:continue
        if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(b,out[-1][1]))
        else:out.append((a,b))
    return out


def nominal_bands(s,eta,include_edges=True):
    """Healthy schedule, zero time error, nominal clock, worst allowed command delay."""
    eta=F(eta);lead=s.hplus+s.delay+s.freeze+s.H+s.et
    first=ceil(1800-eta-lead)
    last=(2400+eta+s.H+s.et)//1
    # Command available at equality is applied before freeze.
    a=F(first)+s.delay+F(320,NS)
    b=F(last+1)+s.delay+F(320,NS)
    bands=[(a+5400*r,b+5400*r) for r in range(s.m['windows'])]
    if include_edges:
        bands.extend([(F(0),s.hold_nominal+2*s.delay+F(320,NS)),(s.T-s.C,s.T)])
    return union([(max(F(0),a),min(s.T,b)) for a,b in bands])


def schedule_counts(s,eta):
    bands=nominal_bands(s,eta)
    slow=count(s.kL,s.W,F(0),s.T)
    high_extra=sum(count(s.kH,s.W,a,b)-count(s.kL,s.W,a,b) for a,b in bands)
    # Pass zero belongs to both supports; no startup double count.
    reads=slow+high_extra
    last_j=prefix_indices(s.T*NS)-1
    last_pass=last_j//s.W
    last_high_pass=last_pass//s.kH*s.kH
    last_selected=min(last_j,(last_high_pass+1)*s.W-1)
    return dict(clock='nominal scale 1, zero endpoint jitter, delay=10ms, time-error=0',
        band_components=len(bands),slow_reads_exact=slow,high_extra_reads_exact=high_extra,
        total_reads_exact=reads,all_fast_reads_exact=count(s.kH,s.W,F(0),s.T),
        total_potential_starts=last_j+1,last_potential_start_s=F(q_ns(last_j),NS),
        last_selected_start_s=F(q_ns(last_selected),NS),
        last_selected_completed_at_T=F(q_ns(last_selected),NS)+s.E<=s.T,
        exact_count_is_not_stochastic_cost=True,
        algorithm='one arithmetic-progression prefix difference per band; O(number_of_windows), not words times windows')


def predicate(s,t,eta,r,error=F(0),right_guard=True):
    a=1800+5400*r-F(eta);b=2400+5400*r+F(eta)
    return (t+error-s.et<=b+(s.H if right_guard else 0)
            and t+error+s.hplus+s.delay+s.freeze+s.H+s.et>=a)


def mode_at(s,j,eta,r,xi=F(1),delay=None,error=F(0),jitter=F(0),loss=None,false_poll=None,right_guard=True):
    """Closed-form latest-ready poll; one-shot restoration hold. q/phi opposite jitter."""
    delay=s.delay if delay is None else F(delay)
    q=F(q_ns(j),NS)*xi+jitter
    phi=F(q_ns(j)-320,NS)*xi-jitter
    i=(phi-delay)//xi
    hold=s.hold_nominal*xi
    if i<0 or phi<hold+2*delay or q>=s.T-s.C:return True
    t=i*xi
    if loss and loss[0]<=t<loss[1]:return True
    if false_poll is not None and i==false_poll:return True
    if loss:
        fresh=ceil(loss[1]/xi)*xi
        if fresh+delay<=phi<fresh+2*delay+hold:return True
    if false_poll is not None:
        fresh=(false_poll+1)*xi
        if fresh+delay<=phi<fresh+2*delay+hold:return True
    return predicate(s,t,eta,r,error,right_guard)


def critical_indices(s,t,xi=F(1)):
    """Both sides of batch and pass edges near a time, plus representative word phases."""
    j=prefix_indices(t*NS/xi);p=j//s.W
    out=set(range(max(0,j-20),j+21))
    for pp in range(max(0,p-2*s.kH),p+2*s.kH+1):
        if pp%s.kH==0 or pp%s.kL==0:
            for off in (0,1,7,8,s.W//2,s.W-8,s.W-1):out.add(pp*s.W+off)
    return out


def boundary_checks(s):
    checked=0; guaranteed=0; price_band=0
    for eta in (F(0),F(30),F(30999,1000),F(1200)):
        for r in (0,1,s.m['windows']-1):
            a=1800+5400*r-eta;b=2400+5400*r+eta
            for xi in (s.xm,F(1),s.xp):
                for delay in (F(0),s.delay):
                    for error in (-s.et,s.et):
                        for jitter in (-s.J/2,s.J/2):
                            candidates=set()
                            for edge in (a-s.H,a,b,b+s.H,a-s.C,b+s.C):
                                candidates.update(critical_indices(s,edge,xi))
                            for j in candidates:
                                q=F(q_ns(j),NS)*xi+jitter
                                if not 0<=q<s.T:continue
                                fast=mode_at(s,j,eta,r,xi,delay,error,jitter)
                                selected=j<s.W or (j//s.W)%s.kL==0 or ((j//s.W)%s.kH==0 and fast)
                                if a-s.H+2*s.J<=q<=b+s.H-2*s.J and (j//s.W)%s.kH==0:
                                    assert selected,('missed guaranteed slot',eta,r,j)
                                    guaranteed+=1
                                if fast and s.C<q<s.T-s.C:
                                    assert a-s.C<=q<=b+s.C,('outside paid healthy band',eta,r,q)
                                    price_band+=1
                                checked+=1
    # Loss/return near an exit; actual full-size calendar, no clean-state reset.
    loss_cases=[]
    for eta in (F(0),F(30),F(1200)):
        a=1800-eta;b=2400+eta;lost=(a-3,b+F(1,3))
        fresh=ceil(lost[1]);end=F(fresh)+2*s.delay+s.hold_upper+s.freeze
        probes=set()
        for t in (lost[0],lost[1],F(fresh)+s.delay,F(fresh)+2*s.delay+s.hold_upper,end):
            probes.update(critical_indices(s,t))
        actual_fast=[]
        for j in probes:
            q=F(q_ns(j),NS)
            fast=mode_at(s,j,eta,0,loss=lost)
            if fast and not mode_at(s,j,eta,0):
                assert lost[0]<=q<=lost[1]+2*s.C
                actual_fast.append(q)
        assert end-lost[1]<=2*s.C
        loss_cases.append(dict(eta_s=eta,loss_interval_s=lost,fresh_check_s=F(fresh),
            latest_return_LOW_freeze_effect_s=end,extra_high_duration_after_loss_s=end-lost[1],
            extra_probe_slots=len(actual_fast),paid_extension_s=2*s.C))
    return dict(checked_slots=checked,guaranteed_high_slots=guaranteed,
        healthy_FAST_band_checks=price_band,loss_cases=loss_cases,
        scope='finite adversarial boundary probes plus algebraic AP identities; not proof by simulation')


class Selector:
    """One latest-command register and one recovery generation, not a clean-state reset."""
    def __init__(self,H=F(1)):
        self.H=H;self.seq=-1;self.generation=0;self.lost=True
        self.holding=True;self.until=F(0);self.request_fast=True

    def command(self,seq,ready,request_fast,healthy=True):
        if seq<=self.seq:return False
        self.seq=seq;self.request_fast=request_fast
        if not healthy:
            self.lost=True;self.holding=True;self.generation+=1
        elif self.lost:
            self.lost=False;self.holding=True;self.generation+=1
            self.until=ready+self.H
        return True

    def expire(self,generation,ready):
        if generation==self.generation and not self.lost and ready>=self.until:
            self.holding=False

    def fast(self):return self.lost or self.holding or self.request_fast
