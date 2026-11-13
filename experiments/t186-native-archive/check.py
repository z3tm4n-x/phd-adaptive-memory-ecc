"""Independent event-list oracle for service phases, full history and weak-write branches."""
from itertools import product
import json

import numpy as np

from replay import A,CAP,EXP,L,OLD,W,branch_envelope,replay


CAL = json.loads((EXP/"t196-native-err-20261110/calendar.json").read_bytes())
FRAME,OFFSETS = CAL["frame_ns"],CAL["visit_offsets_ns"]
COUNTS = (5,10,19,38,75,149,298,596)


def oracle(events,horizon):
    """Literal passes and chronological service of every word that ever has a hit."""
    by_word = {}
    for tick,w,bit in events:
        by_word.setdefault(w,[]).append((tick,bit))
    phases = {w:tuple((a//4)*FRAME+OFFSETS[a%4] for a in (w,w+W)) for w in by_word}
    out = []
    def visit(start,rnd,step,last_bad,scan_count,price,repairs,masks,positions):
        while start<horizon:
            stop = min(start+L,horizon)
            duration = stop-start
            frames,rem = divmod(duration,FRAME)
            read_fee = frames*400+sum(min(100,max(0,rem-f)) for f in OFFSETS)
            outcomes = {}
            for w,timeline in by_word.items():
                before = positions[w]
                while positions[w]<len(timeline) and timeline[positions[w]][0]<stop:
                    positions[w] += 1
                hits = timeline[before:positions[w]]
                if not hits and not masks[w]:
                    continue
                branches = [(masks[w],0,0,0)]
                for off in (*phases[w],None):
                    addr_time = stop if off is None else min(stop,start+off)
                    new = []
                    for mask,i,ns,nv in branches:
                        while i<len(hits) and hits[i][0]<addr_time:
                            mask ^= 1<<hits[i][1]
                            assert mask.bit_count()<=1, "The oracle fixture must remain correctable"
                            i += 1
                        if addr_time==stop:
                            new.append((mask,i,ns,nv))
                            continue
                        end = min(stop,addr_time+(200 if mask else 100))
                        if i<len(hits) and hits[i][0]<end:
                            ts,bit = hits[i]
                            assert mask==0
                            new.append((1<<bit,i+1,ns,nv))
                            if ts<=addr_time+60:
                                d = min(100,max(0,stop-addr_time-100))
                                for residual in (0,1<<bit):
                                    new.append((residual,i+1,ns+d,nv+int(stop>=addr_time+200)))
                        else:
                            d = min(100,max(0,stop-addr_time-100)) if mask else 0
                            repaired = bool(mask and stop>=addr_time+200)
                            new.append((0 if repaired else mask,i,ns+d,nv+int(repaired)))
                    branches = new
                outcomes[w] = branches
            next_states = []
            for combination in product(*outcomes.values()):
                next_masks = masks.copy()
                add = count = 0
                for w,(mask,_,fee,nv) in zip(outcomes,combination):
                    next_masks[w] = mask
                    add += fee
                    count += nv
                bad = (rnd+CAP-1)//CAP if count and rnd else last_bad
                stride = step
                if rnd%CAP==0:
                    stride = 2**sum(rnd//CAP-bad>=n for n in COUNTS)
                elif count:
                    stride = 1
                next_states.append((start+stride*L,rnd+stride,stride,bad,scan_count+1,
                                    price+read_fee+add,repairs+count,next_masks))
            if len(next_states)>1:
                for state in next_states:
                    visit(*state,positions.copy())
                return
            start,rnd,step,last_bad,scan_count,price,repairs,masks = next_states[0]
        for w,timeline in by_word.items():
            mask = masks[w]
            for ts,bit in timeline[positions[w]:]:
                if ts<horizon:
                    mask ^= 1<<bit
                    assert mask.bit_count()<=1
        out.append((price,scan_count,repairs))
    visit(0,0,1,0,0,0,0,{w:0 for w in by_word},{w:0 for w in by_word})
    return out


def main():
    old_t = np.array([L//4,L//4,2*L+30000,2*L+30000],dtype=np.int64)
    old_w = np.array([0,1,16,24],dtype=np.int64)
    old_b = np.array([33,4,37,2],dtype=np.int64)
    old = OLD["replay"](old_t,old_w,old_b,1800*L+177)
    new = replay(old_t,old_w,old_b,1800*L+177,True,False)
    assert old==(new[0]+new[1],new[4],new[2],new[5])
    fixtures = [
        ([],8000*L+310),
        ([(L//4,W-1,37),(L//4,0,32),(1800*L+2077,W-1,4)],5200*L+320),
        ([(1280*L+L//4,0,2),(1280*L+L//4,1,37)],6200*L+260),
        ([(2000*L+9340,64,21),(2000*L+9359,64,21)],5200*L+250),
        ([(L//4,0,4)],L//2+133),
    ]
    for off in (0,39,60,61,99):
        fixtures.append(([(L//2+off,0,37)],3800*L+311))
    for ev,horizon in fixtures:
        arrays = tuple(np.array([e[j] for e in ev],np.int64) for j in range(3))
        literal = oracle(ev,horizon)
        bounds = branch_envelope(arrays,horizon,replay(*arrays,horizon))
        assert bounds[4]==0
        for col,where in [(0,0),(1,5),(2,7)]:
            values = [row[col] for row in literal]
            assert (min(values),max(values))==tuple(bounds[where:where+2])
    print(f"Independent literal passes and all local choices agree on {len(fixtures)} fixtures; #465 control passed.")


if __name__=="__main__":
    main()
