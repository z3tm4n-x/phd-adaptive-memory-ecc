"""Sparse replay of the public rule. Time and charged work are integer ns."""
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys

REF = Path(__file__).resolve().parents[1] / "RE-CY62167-EXECUTOR-TIMING-GATE-01/reference-continuation-01"
sys.path.insert(0, str(REF))
from witness import decode

NS = 10**9


@dataclass(frozen=True)
class Calendar:
    words: int = 65536
    quiet: int = 730

    def __post_init__(self):
        assert self.words >= 8 and self.words % 8 == 0
        object.__setattr__(self, "inv3", pow(3, -1, self.words))

    @property
    def L(self):
        return 196*self.words

    @property
    def P(self):
        return 32*self.L

    @property
    def drain(self):
        return self.L-256

    def q(self, word):
        position = (word*self.inv3) % self.words
        return 1568*(position//8) + 164*(position%8)

    def prefix_reads(self, elapsed):
        frames, remainder = divmod(max(0,elapsed),1568)
        return min(self.words, frames*8+min(8,(remainder+163)//164))


class Controller:
    """This interface receives only complete cell reports and local tick indices."""
    def __init__(self, calendar, adaptive):
        self.cal = calendar
        self.adaptive = adaptive
        self.z = 0
        self.fast = True
        self.switches = []
        self.invalid_cells = 0

    @property
    def step(self):
        return (1 if self.fast else 32) if self.adaptive else 4

    def switch(self, j, fast, reason):
        if self.adaptive and self.fast != fast:
            self.fast = fast
            self.switches.append((j,fast,reason))

    def close(self, j, count, invalid):
        self.invalid_cells += int(invalid)
        if not self.adaptive:
            return
        if invalid or count:
            self.z = 0
            self.switch(j,True,"invalid" if invalid else "correction")
        else:
            self.empty(j,1,False)

    def empty(self, first, number, invalid):
        if not number:
            return
        if invalid:
            self.invalid_cells += number
            self.z = 0
            self.switch(first,True,"invalid")
        elif self.adaptive:
            needed = self.cal.quiet-self.z
            if self.fast and number >= needed:
                self.switch(first+needed-1,False,"quiet")
            self.z = min(self.cal.quiet,self.z+number)


class Memory:
    def __init__(self, calendar, end, repair_log):
        self.cal = calendar
        self.end = end
        self.masks = {}
        self.repairs = 0
        self.first_failure = None
        self.terminal_pending_dirty = {}
        self.repaired_last = None
        self.repair_log = repair_log

    def inspect(self, mask, t):
        if mask.bit_count() > 1 and (self.first_failure is None or t < self.first_failure):
            self.first_failure = t

    def word(self, word, hits, rounds, reports):
        """Only this word is touched here. Both words of a parent keep its time."""
        mask = self.masks.get(word,0)
        i = 0
        fault = False
        def arrivals_until(limit):
            nonlocal i,mask
            while i < len(hits) and hits[i][0] < limit:
                t,bit = hits[i]
                mask ^= 1 << bit
                self.inspect(mask,t)
                i += 1
        phase = self.cal.q(word)
        last_word = (3*(self.cal.words-1)) % self.cal.words
        for r in rounds:
            start = r*self.cal.L+phase
            if start >= self.end:
                break
            arrivals_until(start)
            if not mask:
                if i == len(hits):
                    break
                continue
            snapshot = mask
            if mask.bit_count() == 1:
                corrected,repair,due = 0,True,False
            else:
                corrected,repair,due = decode(mask)
            release = start + (124 if repair else 68)
            if repair:
                self.repairs += 1
                if self.repair_log is not None:
                    self.repair_log.append(start)
                if word == last_word and (self.repaired_last is None or r > self.repaired_last):
                    self.repaired_last = r
            arrivals_until(min(self.end,release))
            if release <= self.end:
                mask ^= snapshot ^ corrected
                self.inspect(mask,release)
                fault |= due
                if repair:
                    reports.append((word,start,release))
            else:
                self.terminal_pending_dirty[word] = (snapshot,corrected,release)
            if not mask and i == len(hits):
                break
        arrivals_until(self.end)   # hits supplied to this call belong only to this epoch
        if mask:
            self.masks[word] = mask
        else:
            self.masks.pop(word,None)
        return fault


def counts(cal, end, controller, mem):
    switches = controller.switches
    changes = [(0,1 if controller.adaptive else 4)]
    changes += [(j*cal.P,1 if fast else 32) for j,fast,_ in switches]
    starts = full = issued = fast_ns = reads = 0
    partial = 0
    pending = None
    for (a,step), b in zip(changes,[t for t,_ in changes[1:]]+[end]):
        period = step*cal.L
        length = b-a
        n = (length+period-1)//period
        last = a+(n-1)*period
        last_q = cal.q((3*(cal.words-1))%cal.words)
        last_cost = 124 if mem.repaired_last == last//cal.L else 68
        last_reads = cal.prefix_reads(b-last)
        closed = last+last_q+last_cost <= b
        starts += n
        full += n-1+int(closed)
        issued += n-1+int(last+cal.drain <= b)
        reads += (n-1)*cal.words+last_reads
        if b == end:
            partial = 0 if closed else last_reads
            # A clean E may also still be open at T.
            if last_reads:
                last_word = (3*(last_reads-1))%cal.words
                t = last + cal.q(last_word)
                until = mem.terminal_pending_dirty.get(last_word,(0,0,t+68))[2]
                if t < end < until:
                    pending = [last_word,t,until]
        if step == 1:
            fast_ns += length
    # Cell commands change after the common scan. Shifting every transition
    # by the same drain time cancels in pairs; only the terminal state matters.
    command_fast = fast_ns + (cal.drain if switches and not switches[-1][1] else 0)
    return dict(started_passes=starts,complete_passes=full,public_passes=issued,
                terminal_partial_reads=partial,terminal_pending=pending,word_reads=reads,
                repair_writes=mem.repairs,read_bus_ns=48*reads,write_bus_ns=56*mem.repairs,
                protection_bus_ns=48*reads+56*mem.repairs,fast_ns=fast_ns if controller.adaptive else None,
                fast_command_ns=command_fast if controller.adaptive else None,
                switches=len(switches),to_fast=sum(fast for _,fast,_ in switches),
                to_rare=sum(not fast for _,fast,_ in switches),
                closed_common_cells=max(0,(end-cal.drain)//cal.P),
                invalid_cells=controller.invalid_cells,first_weight_above_one_ns=mem.first_failure,
                terminal_words_with_residual=len(mem.masks))


def simulate(marks, adaptive, end, cal=Calendar(), repair_log=None):
    ctrl = Controller(cal,adaptive)
    mem = Memory(cal,end,repair_log)
    groups = defaultdict(lambda: defaultdict(list))
    last = max(0,(end-1-cal.drain)//cal.P+1)
    for t,w1,b1,w2,b2 in marks:
        t = int(t)
        if not 0 <= t < end:
            raise ValueError("particle outside the open-right horizon")
        j = max(0,(t-cal.drain)//cal.P+1)
        groups[j][int(w1)].append((t,int(b1)))
        groups[j][int(w2)].append((t,int(b2)))
    # A hit after its word's final snapshot can first be seen in the next cell.
    # After that extra cell, untouched residual words have stable decoder outputs.
    active = {0,last,*groups.keys()}
    active.update(j+1 for j in groups if j < last)
    after = 0
    returns = []
    for j in sorted(active):
        if j > after:
            stable = [decode(mask) for mask in mem.masks.values()]
            assert not any(repair for _,repair,_ in stable)
            ctrl.empty(after,j-after,any(fault for _,_,fault in stable))
        step = ctrl.step
        first = (j-1)*32+step if j else 0
        rounds = range(first,32*j+1,step)
        repairs = []
        bad = False
        hits = groups.get(j,{})
        for word in sorted(mem.masks.keys() | hits.keys()):
            bad |= mem.word(word,hits.get(word,()),rounds,repairs)
        decision = j*cal.P+cal.drain
        if j and decision < end:
            prior_fast = ctrl.fast
            ctrl.close(j,len(repairs),bad)
            if ctrl.adaptive and not prior_fast and ctrl.fast:
                returns.append((j,sorted(repairs,key=lambda record:record[2])))
        after = j+1
    result = counts(cal,end,ctrl,mem)
    return result, ctrl.switches, returns, mem.masks
