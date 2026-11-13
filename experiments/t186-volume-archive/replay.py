"""Paired native-x16 calendars for the registered 64 KiB example, derived from PR 484."""
from pathlib import Path
from runpy import run_path

import numpy as np
from numba import njit


EXP = Path(__file__).resolve().parent.parent
OLD = run_path(str(EXP/"native-example-20261111/decade.py"))
W = 16384
A = 2*W
T, PHASE = OLD["T"], OLD["PHASE"]
MODEL = run_path(str(EXP/"t186-native-cost-map/calculate.py"))
RULE = MODEL["Ladder"](W)
L = int(RULE.scan.L * 10**9)
CAP = 2**(len(RULE.levels)-1)
THRESHOLDS = np.asarray(RULE.counts, dtype=np.int64)
NO_CHOICES = np.empty(0,dtype=np.int64)
OLD_READ = OLD["read_ns_until"]


@njit
def read_ns_until(length):
    return OLD_READ(min(length,L))


@njit
def replay(ticks, words, bits, horizon, fixed_ns=0, skip=True, choices=NO_CHOICES):
    masks = np.zeros(W,dtype=np.int64)
    marked = np.zeros(W,dtype=np.bool_)
    touched = np.empty(W,dtype=np.int64)
    carry = np.empty(W,dtype=np.int64)
    ncarry = 0
    rnd, step, bad, pos = 0,1,0,0
    scans, reads_ns, writes_ns, repairs, used = 0,0,0,0,0
    resets, returns, last_reset_cell = 0,0,-1
    base_ns = fixed_ns if fixed_ns else L
    while rnd*base_ns < horizon:
        start = rnd*base_ns
        end = min(horizon,start+L)
        nxt = pos
        while nxt<len(ticks) and ticks[nxt]<end:
            nxt += 1
        # This batch may start in the quiet gap after the previous charged scan.
        # Word-by-word traversal does not establish the earliest stop across words.
        unpriced = horizon-min(start,ticks[pos]) if pos<nxt else horizon-start
        empty = ncarry==0 and pos==nxt
        n = ncarry
        for j in range(ncarry):
            w = carry[j]
            marked[w] = True
            touched[j] = w
        for k in range(pos,nxt):
            w = words[k]
            if not marked[w]:
                touched[n] = w
                n += 1
                marked[w] = True
        ncarry, extra, complete = 0,0,0
        for j in range(n):
            w = touched[j]
            k, mask = pos,masks[w]
            for half in range(3):
                addr = w+half*W
                visit = start+addr//4*1400+PHASE[addr%4] if half<2 else end
                while k<nxt and ticks[k]<min(visit,end):
                    if words[k]==w:
                        mask ^= np.int64(1)<<bits[k]
                        if mask & (mask-1):
                            return reads_ns,writes_ns,scans,repairs,unpriced,1,0,resets,returns
                    k += 1
                if half==2 or visit>=end:
                    continue
                release = visit+(200 if mask else 100)
                # A first birth inside the *addressed* aperture is ambiguous.
                # A no-write read preserves it. A write may clear or retain it.
                # The selected report is already fixed after the +60 ns sample.
                write = mask!=0
                residual = 0
                aperture_hit = False
                while k<nxt and ticks[k]<min(release,end):
                    if words[k]==w:
                        born = np.int64(1)<<bits[k]
                        if aperture_hit or mask:
                            # Several births or an old live defect at this visit:
                            # retain the full remaining interval as an outer bound.
                            return reads_ns,writes_ns,scans,repairs,unpriced,3,0,resets,returns
                        aperture_hit = True
                        options = 3 if ticks[k]<=visit+60 else 1
                        if used>=len(choices):
                            return reads_ns,writes_ns,scans,repairs,unpriced,2,options,resets,returns
                        choice = choices[used]
                        used += 1
                        assert 0<=choice<options
                        write = choice!=0
                        release = visit+(200 if write else 100)
                        residual = 0 if choice==1 else born
                    k += 1
                if write:
                    extra += max(0,min(100,end-visit-100))
                    if release<=end:
                        mask = residual
                        complete += 1
                elif aperture_hit:
                    mask = residual
            masks[w] = mask
            marked[w] = False
            if mask:
                carry[ncarry] = w
                ncarry += 1
        pos = nxt
        if not fixed_ns:
            previous_step = step
            if complete:
                bad = (rnd+CAP-1)//CAP
                if bad != last_reset_cell:
                    resets += 1
                    last_reset_cell = bad
            if rnd%CAP==0:
                step = 1
                for threshold in THRESHOLDS:
                    if rnd//CAP-bad >= threshold:
                        step *= 2
            elif complete:
                step = 1
            if complete and previous_step>1 and step==1:
                returns += 1
        groups = 1
        if skip and empty and end-start==L:
            next_hit = ticks[pos] if pos<len(ticks) else horizon
            groups += (next_hit-end)//(step*base_ns)
            if not fixed_ns and step<CAP:
                level = 0
                while 2**level != step:
                    level += 1
                next_gate = (bad+THRESHOLDS[level])*CAP
                groups = min(groups,max(1,(next_gate-rnd+step-1)//step))
        reads_ns += (groups-1)*A*100+read_ns_until(end-start)
        writes_ns += extra
        repairs += complete
        scans += groups
        rnd += groups*step
    # A parent between the last scan and T still contributes to physical state.
    # No further read can take place in that gap on the nominal calendar.
    for k in range(pos,len(ticks)):
        if ticks[k]>=horizon:
            break
        w = words[k]
        masks[w] ^= np.int64(1)<<bits[k]
        if masks[w] & (masks[w]-1):
            return reads_ns,writes_ns,scans,repairs,horizon-ticks[k],1,0,resets,returns
    return reads_ns,writes_ns,scans,repairs,0,0,0,resets,returns


def branch_envelope(data, horizon, fixed_ns=0, skip=True):
    """Bounds on occupied ns, scans, writes, distinct dirty cells and slow-to-fast returns."""
    pending = [()]
    minima = np.full(5, np.iinfo(np.int64).max, dtype=np.int64)
    maxima = np.zeros(5, dtype=np.int64)
    splits = leaves = open_leaves = 0
    while pending:
        route = pending.pop()
        choices = np.asarray(route,dtype=np.int64)
        read,write,scans,repairs,tail,reason,options,resets,returns = replay(
            *data, horizon, fixed_ns, skip, choices)
        if reason == 2 and len(route) < 12:
            pending.extend(route+(choice,) for choice in range(options))
            splits += 1
            continue
        lower = np.array([read+write, scans, repairs, resets, returns], dtype=np.int64)
        upper = lower.copy()
        if reason:
            open_leaves += 1
            # Include any started pass and the final prefix. One pass can
            # generate at most A writes and one reset or transition.
            extra_passes = tail//(fixed_ns or L)+2
            upper += np.array([tail, extra_passes, A*extra_passes,
                               0 if fixed_ns else extra_passes, 0 if fixed_ns else extra_passes])
            if fixed_ns:
                # Both the address calendar and all read slots are independent
                # of every report, even after an uncorrectable word.
                full, rem = divmod(horizon, fixed_ns)
                all_reads = full*A*100+read_ns_until(min(rem,L))
                all_scans = full+int(rem>0)
                lower[0] = all_reads+write
                upper[0] = min(upper[0], all_reads+write+(all_scans-scans)*A*100)
                lower[1] = upper[1] = all_scans
        leaves += 1
        minima = np.minimum(lower, minima)
        maxima = np.maximum(upper, maxima)
    return minima, maxima, (splits, leaves, open_leaves)


def selftest():
    def case(events, end, fixed=0):
        data = tuple(np.asarray([e[i] for e in events],dtype=np.int64) for i in range(3))
        result = branch_envelope(data,end,fixed)
        slow = branch_envelope(data,end,fixed,False)
        assert all(np.array_equal(a,b) for a,b in zip(result,slow))
        return result

    for p in (0,2*L+1400):
        for end in (60,300,L-30,L,L+50,7*L+1700):
            lo,hi,_ = case([], end,p)
            full,remainder = divmod(end,p or L)
            expected = full*A*100+read_ns_until(min(L,remainder))
            assert lo[0]==hi[0]==expected
            assert lo[1]==hi[1]==full+int(remainder>0)
        lo,hi,_ = case([(L//4,0,37),(L//4,1,0)],L,p)
        assert lo[2]==hi[2]==2 and lo[0]==A*100+200
        assert lo[3]==hi[3]==int(p==0) and lo[4]==0
        lo,hi,st = case([(30,0,37)],L,p)
        assert st==(1,3,0) and (lo[0],hi[0])==(A*100+100,A*100+200)
    # Two repairs in one scan are one dirty cell. Once the ladder is slow
    # a new singleton forces one return to fast. A fixed schedule never does.
    gate = int(THRESHOLDS[0])*CAP*L
    lo,hi,_ = case([(gate+L+1000,0,5),(gate+L+1000,1,7)],gate+4*L)
    assert lo[2]==hi[2]==2 and lo[3]==hi[3]==1 and lo[4]==hi[4]==1
    # A genuine two-bit state during the terminal gap has no invented cost.
    lo,hi,stat = case([(L+1,0,1),(L+5,0,0)],L+10,2*L)
    assert stat[2]==1 and lo[0]==hi[0]==A*100
