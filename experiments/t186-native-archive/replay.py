"""Native x16 replay on the registered w,w+W map, including the final quiet gap."""
from pathlib import Path
from runpy import run_path

import numpy as np
from numba import njit


EXP = Path(__file__).resolve().parent.parent
OLD = run_path(str(EXP/"native-example-20261111/decade.py"))
A,W,L,T,CAP = (OLD[k] for k in ("A","W","L","T","CAP"))
PHASE, THRESHOLDS, read_ns_until = (OLD[k] for k in ("PHASE","THRESHOLDS","read_ns_until"))
NO_CHOICES = np.empty(0,dtype=np.int64)


@njit
def replay(ticks, words, bits, horizon, skip=True, split_halves=True, choices=NO_CHOICES):
    masks = np.zeros(W,dtype=np.int64)
    marked = np.zeros(W,dtype=np.bool_)
    touched = np.empty(W,dtype=np.int64)
    carry = np.empty(W,dtype=np.int64)
    ncarry = 0
    rnd, step, bad, pos = 0,1,0,0
    scans, reads_ns, writes_ns, repairs, used = 0,0,0,0,0
    while rnd*L < horizon:
        start = rnd*L
        end = min(horizon,start+L)
        nxt = pos
        while nxt<len(ticks) and ticks[nxt]<end:
            nxt += 1
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
                addr = w+half*W if split_halves else 2*w+half
                visit = start+addr//4*1400+PHASE[addr%4] if half<2 else end
                while k<nxt and ticks[k]<min(visit,end):
                    if words[k]==w:
                        mask ^= np.int64(1)<<bits[k]
                        if mask & (mask-1):
                            return reads_ns,writes_ns,scans,repairs,horizon-start,1,0
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
                            return reads_ns,writes_ns,scans,repairs,horizon-start,3,0
                        aperture_hit = True
                        options = 3 if ticks[k]<=visit+60 else 1
                        if used>=len(choices):
                            return reads_ns,writes_ns,scans,repairs,horizon-start,2,options
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
        if complete and rnd>0:
            bad = (rnd+CAP-1)//CAP
        if rnd%CAP==0:
            step = 1
            for threshold in THRESHOLDS:
                if rnd//CAP-bad >= threshold:
                    step *= 2
        elif complete:
            step = 1
        groups = 1
        if skip and empty and end-start==L:
            next_hit = ticks[pos] if pos<len(ticks) else horizon
            groups += (next_hit-end)//(step*L)
            if step<CAP:
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
            return reads_ns,writes_ns,scans,repairs,horizon-ticks[k],1,0
    return reads_ns,writes_ns,scans,repairs,0,0,0


def branch_envelope(data, horizon, coarse):
    """Evaluate every allowed local outcome. A non-enumerated tail stays charged."""
    paths = [((),coarse)]
    leaves = []
    splits = 0
    while paths:
        route, row = paths.pop()
        read,write,scans,repairs,tail,reason,options = row
        if reason==2 and len(route)<12:
            splits += 1
            for choice in range(options):
                child = route+(choice,)
                result = replay(*data,horizon,True,True,np.asarray(child,dtype=np.int64))
                paths.append((child,result))
        else:
            leaves.append((read+write,read+write+tail,scans,repairs,reason))
    return min(r[0] for r in leaves),max(r[1] for r in leaves),splits,len(leaves),sum(r[-1]!=0 for r in leaves)


def selftest():
    def trial(ts,ws,bs,end):
        data = tuple(np.array(x,dtype=np.int64) for x in (ts,ws,bs))
        val = replay(*data,end)
        assert val == replay(*data,end,False)
        return val
    assert trial([L//4],[0],[37],L)[1:4] == (100,1,1)
    assert trial([L//2+201],[0],[37],L)[1]==0
    assert trial([L//2+201],[0],[37],2*L)[1]==100
    assert trial([L//2+60],[0],[37],L)[-2:]==(2,3)
    assert trial([1000,1010],[0,0],[0,1],L)[-2]==1
    assert trial([1000,1010],[0,0],[0,0],L)[1]==0
    assert trial([L//4,L//4],[W-1,0],[37,32],L)[1]==200
    edge = 5*CAP*L+L
    assert trial([edge+201,edge+205],[0,0],[1,0],edge+210)[-3:]==(5,1,0)
    assert trial([L//4],[0],[1],L//2+150)[1]==50
    assert trial([],[],[],300)[0]==160
    for offset,leaves in [(30,3),(70,1)]:
        data = tuple(np.array(x,dtype=np.int64) for x in ([offset],[0],[37]))
        coarse = replay(*data,L)
        lo,hi,_,n,unresolved = branch_envelope(data,L,coarse)
        assert (lo,hi)==(A*100+100,A*100+(200 if leaves==3 else 100))
        assert n==leaves and unresolved==0
