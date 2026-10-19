"""Integer E-service simulator, scheduling only currently dirty words.

Clean service is reconstructed when an inversion lands during an implicit
operation; this includes a late inversion after a clean latch. Baseline work
is integrated over every executed slot, regardless of dirty queue activity.
"""
from fractions import Fraction
import heapq
import time


def ceildiv(a, b):
    return -(-a//b)


class Grid:
    def __init__(self, words=524288):
        assert words >= 8 and words % 8 == 0
        self.words = words
        self.inverse = pow(3, -1, words)

    def start(self, j):
        return (j//8)*1568+(j%8)*164

    def first(self, t):
        j = max(0, (t//1568)*8)
        while self.start(j) < t:
            j += 1
        return j

    def address(self, j):
        return self.inverse*j % self.words

    def eligible(self, j, k):
        return j < self.words or j % k == 0

    def count(self, a, b, k):
        warm = max(0, min(b, self.words)-a)
        a = max(a, self.words)
        return warm+max(0, ceildiv(b,k)-ceildiv(a,k))

    def work(self, a, b, k, t):
        if b <= a or t <= self.start(a):
            return 0
        full = min(b, self.first(t-92+1))
        val = self.count(a, max(a,full), k)*92
        j = max(a,full)
        if j < b and self.start(j) < t and self.eligible(j,k):
            val += min(92,t-self.start(j))
        return val


def run(horizon, marks, apps, policy, literal=False, deadline=None):
    grid = Grid(policy.words)
    heap, serial = [], 0
    errors, active, versions = {}, {}, {}
    corrections, applications, errs, delivered = [], [], [], []
    explicit, literal_pulses = [], []
    counts = {}
    first = None
    max_dirty = max_heap = max_active = 0
    last_timer = object()

    def push(t, priority, kind, x):
        nonlocal serial, max_heap
        if 0 <= t <= horizon:
            serial += 1
            heapq.heappush(heap,(t,priority,serial,kind,x))
            max_heap = max(max_heap,len(heap))

    def schedule_policy():
        nonlocal last_timer
        if policy.timer != last_timer:
            last_timer = policy.timer
            if last_timer is not None:
                push(last_timer,2,'timer',last_timer)

    def schedule_word(w, t):
        if literal or w in active or not errors.get(w):
            return
        j0 = (3*w) % grid.words
        j = j0+max(0,ceildiv(grid.first(t)-j0,grid.words))*grid.words
        versions[w] = versions.get(w,0)+1
        push(grid.start(j),4,'control',(j,versions[w]))

    def begin(w, s, j=None, arrival=None, observed_clean=False):
        nonlocal max_active
        assert w not in active, ('overlapping word transactions',w,s)
        tx = dict(start=s,word=w,slot=j,arrival=arrival,err=False,end=None)
        active[w] = tx
        explicit.append(tx)
        max_active = max(max_active,len(active))
        if observed_clean:
            tx['end'] = s+92
            push(s+92,7,'release',tx)
        else:
            push(s+60,5,'snapshot',tx)
        return tx

    for x in marks:
        assert 0 <= x['word'] < grid.words and 0 <= x['bit'] < 38
        push(x['t'],0,'injection',x)
    for x in apps:
        s = ceildiv(x['arrival_ns']+320-1312,1568)*1568+1312
        push(s,4,'app',x)
    if literal:
        # Independent exhaustive slot traversal, intended only for small checks.
        push(0,4,'literal_control',0)
    schedule_policy()

    while heap:
        t,_,_,kind,x = heapq.heappop(heap)
        counts[kind] = counts.get(kind,0)+1
        if deadline is not None and sum(counts.values()) % 1024 == 0 and time.perf_counter() > deadline:
            raise TimeoutError('registered benchmark wall budget reached')
        if kind == 'injection':
            w,bit = x['word'],x['bit']
            e = errors.setdefault(w,{})
            if bit in e:
                del e[bit]
            else:
                e[bit] = t
            if len(e) > 1 and first is None:
                first = dict(t=t,word=w,bits=sorted(e))
            if not e:
                errors.pop(w,None)
                versions[w] = versions.get(w,0)+1
            elif not literal and w not in active:
                # A previously implicit clean slot can already be in flight.
                j0 = (3*w) % grid.words
                last = grid.first(t+1)-1
                j = j0+((last-j0)//grid.words)*grid.words
                s = grid.start(j) if j >= 0 else -1000
                if j >= 0 and s <= t < s+92 and grid.eligible(j,policy.mode(s-320)) and s < horizon:
                    versions[w] = versions.get(w,0)+1
                    begin(w,s,j,observed_clean=t > s+60)
                else:
                    schedule_word(w,t)
            max_dirty = max(max_dirty,len(errors))
        elif kind in ('control','literal_control'):
            j = x if kind == 'literal_control' else x[0]
            w = grid.address(j)
            if kind == 'literal_control':
                push(grid.start(j+1),4,'literal_control',j+1)
            elif versions.get(w) != x[1] or not errors.get(w) or w in active:
                continue
            if t >= horizon:
                continue
            if grid.eligible(j,policy.mode(t-320)):
                begin(w,t,j)
            else:
                schedule_word(w,grid.start(j+grid.words))
        elif kind == 'app':
            if t >= horizon:
                continue
            response = t+184+320+80
            applications.append(dict(arrival_ns=x['arrival_ns'],grant_ns=t,response_ns=response,
                                     delay_ns=response-x['arrival_ns'],response_within_horizon=response<=horizon))
            begin(x['word'],t,arrival=x['arrival_ns'])
        elif kind == 'snapshot':
            tx = x
            tx['err'] = bool(errors.get(tx['word']))
            control = tx['slot'] is not None
            duration = (148 if tx['err'] else 92) if control else 184
            tx['end'] = tx['start']+duration
            if control and tx['err']:
                corrections.append((tx['start']+92,tx['start']+148))
                push(tx['start']+64,1,'publish',tx)
                push(tx['start']+132,6,'commit',tx)
            if literal and control:
                literal_pulses.append((tx['start'],tx['end']))
            push(tx['end'],7,'release',tx)
        elif kind == 'publish':
            errs.append(dict(t=t,word=x['word'],slot=x['slot']))
            policy.publish(t)
            push((t//policy.cut+1)*policy.cut,1,'deliver',t)
            schedule_policy()
        elif kind == 'deliver':
            delivered.append(dict(t=t,source=x))
            policy.observe(t,x)
            schedule_policy()
        elif kind == 'timer':
            if x != policy.timer:
                continue
            policy.wake(t)
            schedule_policy()
        elif kind == 'commit':
            w = x['word']
            e = {b:born for b,born in errors.get(w,{}).items() if born >= x['start']}
            if e:
                errors[w] = e
            else:
                errors.pop(w,None)
        elif kind == 'release':
            active.pop(x['word'])
            schedule_word(x['word'],t)
        else:
            raise AssertionError(kind)
    policy.finish(horizon)
    total_slots = grid.first(horizon)
    cuts = [(0,policy.modes[0])]
    cuts += [(grid.first(t+320),k) for t,k in zip(policy.times[1:],policy.modes[1:]) if grid.first(t+320)<total_slots]
    cuts.append((total_slots,1))
    segments = [(a,b,k) for (a,k),(b,_) in zip(cuts,cuts[1:]) if b>a]
    def pulses(intervals,a,b):
        return sum(max(0,min(b,y)-max(a,x)) for x,y in intervals)
    def base(t):
        return sum(grid.work(a,b,k,t) for a,b,k in segments)
    def price(a,b):
        v = dict(control_base_ns=base(b)-base(a),correction_extra_ns=pulses(corrections,a,b),
                 application_read_ns=pulses([(q['grant_ns'],q['grant_ns']+184) for q in applications],a,b))
        v['total_ns'] = sum(v.values())
        return v
    bus = price(0,horizon)
    started = sum(grid.count(a,b,k) for a,b,k in segments)
    unfinished = []
    if total_slots:
        j = total_slots-1
        s = grid.start(j)
        if grid.eligible(j,policy.mode(s-320)):
            tx = active.get(grid.address(j))
            end = tx['end'] if tx and tx['slot']==j else (s+92 if s+60<=horizon else None)
            if end is None or end>horizon:
                unfinished.append(dict(kind='control',start_ns=s,end_ns=end,charged_ns=horizon-s))
    for q in applications:
        if q['grant_ns']+184>horizon:
            unfinished.append(dict(kind='read32',start_ns=q['grant_ns'],end_ns=q['grant_ns']+184,
                                   charged_ns=horizon-q['grant_ns']))
    if literal:
        pending = [(q['start'],q['start']+92) for q in active.values() if q['slot'] is not None and q['end'] is None]
        assert pulses(literal_pulses+pending,0,horizon) == bus['control_base_ns']+bus['correction_extra_ns']
        assert sum(q['slot'] is not None for q in explicit) == started
    return dict(horizon_ns=horizon,first_exceedance=first,Q_MC=None,
                started_control_operations=started,completed_control_operations=started-sum(q['kind']=='control' for q in unfinished),
                started_application_operations=len(applications),unfinished_operations=unfinished,bus=bus,
                mean_bus_fraction_exact=str(Fraction(bus['total_ns'],horizon)),mean_bus_percent=100*bus['total_ns']/horizon,
                bus_after_first_exceedance=price(first['t'],horizon) if first else None,
                mode_history=[dict(t_ns=t,k=k) for t,k in zip(policy.times,policy.modes)],
                effective_segments=[dict(first_slot=a,end_slot=b,k=k) for a,b,k in segments],
                err_events=errs,delivered_ERR=delivered,algorithm_cost=policy.costs(horizon),
                application=applications,max_application_delay_ns=max((q['delay_ns'] for q in applications),default=0),
                residual_errors={str(w):{str(b):v for b,v in sorted(e.items())} for w,e in sorted(errors.items())},
                simulator_work=dict(event_counts=counts,explicit_transactions=len(explicit),max_dirty_words=max_dirty,
                                    max_active_transactions=max_active,max_heap=max_heap))
