"""Executable functional contract. Not a physical SRAM or cycle-accurate RTL simulator."""
from dataclasses import dataclass

PARITY=(1,2,4,8,16,32,39)
DATA=tuple(p for p in range(1,39) if p not in PARITY)
def encode(data):
    cw=sum(((data>>i)&1)<<(p-1) for i,p in enumerate(DATA))
    for p in PARITY[:-1]:
        cw |= (sum((cw>>(j-1))&1 for j in range(1,39) if j&p)%2)<<(p-1)
    return cw | ((cw.bit_count()%2)<<38)
def pack(cw):
    return sum(((cw>>(p-1))&1)<<i for i,p in enumerate(DATA+PARITY))
def unpack(bus):
    return sum(((bus>>i)&1)<<(p-1) for i,p in enumerate(DATA+PARITY))
def decode(cw):
    syndrome=0
    for p in range(1,39):
        if (cw>>(p-1))&1: syndrome^=p
    odd=cw.bit_count()%2
    if not odd and syndrome: return cw,False,True
    if odd:
        p=syndrome or 39
        if syndrome>38: return cw,False,True
        return cw^(1<<(p-1)),True,False
    return cw,False,False

@dataclass
class Slot:
    kind: str="scrub"
    image: int=0
    pending: bool=True
    fault: bool=False
    invalid: bool=False
    quiesce: bool=False
    ack: bool=False
    latched: int=0
    latched_err: int=0
    write: bool=False
    driven: bool=False
    we_n: bool=True
    qualified: bool=True
    def step(self,t,dq=0,err=0,soft_reset=False,hard_reset=False,commit_ok=True):
        if hard_reset:
            self.invalid=True; self.pending=False; self.ack=False
            self.driven=False; self.we_n=True
            return
        self.quiesce |= soft_reset
        if not commit_ok: self.invalid=True
        if self.kind=="prep" and t==0:
            self.latched=pack(encode(self.image)); self.write=True
        if self.kind!="prep" and t==8:
            self.latched=dq; self.latched_err=err
        if self.kind!="prep" and t==10:
            cw,corrected,uncorrectable=decode(unpack(self.latched))
            self.fault|=uncorrectable
            self.latched=pack(cw)
            self.write=self.kind=="scrub" and not uncorrectable and (corrected or bool(self.latched_err))
        if t==12: self.driven=self.write
        if t==13: self.we_n=not self.write
        if t==19: self.we_n=True
        if t==21: self.driven=False
        if t==24:
            self.pending=False
            self.ack=not(self.fault or self.invalid) and self.qualified and self.we_n and not self.driven
def scrub_start(w,k=0,N=524288,P=100000000):
    return k*P+w*P//N
def prepare_end(w):
    return -20000000+24*(w+1)
def epoch_valid(completed, pending, ready, safe, invalid):
    return completed==524288 and pending==0 and ready and safe and not invalid
def saturated_reads(starts,stop):
    """Earliest legal requests, one outstanding, no phase displacement."""
    reads=[]; next_accept=0; busy_until=0; ix=0
    for t in range(stop):
        while ix<len(starts) and starts[ix]<t: ix+=1
        if ix<len(starts) and starts[ix]==t:
            assert t>=busy_until
            busy_until=t+24
        elif t>=busy_until and t>=next_accept and (ix==len(starts) or t+24<=starts[ix]):
            reads.append(t); busy_until=t+24; next_accept=t+48
    return reads
