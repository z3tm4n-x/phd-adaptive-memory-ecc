"""Python specification checks of the pinned decoder and the proposed word slot.

This is not execution, synthesis, or equivalence checking of SystemVerilog.
"""
from itertools import combinations

PARITY={1,2,4,8,16,32,39}
MASK=(1<<39)-1


def encode(data: int) -> int:
    if not 0<=data<1<<32: raise ValueError('32-bit payload required')
    out=0;j=0
    for pos in range(1,39):
        if pos not in PARITY:
            out|=((data>>j)&1)<<(pos-1);j+=1
    for p in (1,2,4,8,16,32):
        bit=sum((out>>(pos-1))&1 for pos in range(1,39) if pos&p)%2
        out|=bit<<(p-1)
    return out|((out.bit_count()%2)<<38)


def decode(raw: int):
    """Algebraic specification matching the inspected 39-bit decoder branches."""
    word=raw&MASK;syndrome=0
    for pos in range(1,39):
        if (word>>(pos-1))&1: syndrome^=pos
    odd=word.bit_count()%2
    if syndrome==0 and odd==0: return word,0,False
    if odd and syndrome<=38:
        pos=syndrome or 39
        return word^(1<<(pos-1)),pos,False
    return word,0,True


def run(cfg):
    singles=doubles=0
    for payload in (0,0xffffffff,0xa5a5a5a5):
        code=encode(payload);assert decode(code)==(code,0,False)
        for pos in range(1,40):
            assert decode(code^(1<<(pos-1)))==(code,pos,False);singles+=1
        for a,b in combinations(range(39),2):
            assert decode(code^(1<<a)^(1<<b))[2];doubles+=1
    assert singles==117 and doubles==2223
    # RMW snapshots: real read latch versus an independent check at write credit.
    # One fault: before read, after read, or after write. Every protected position.
    phases=[('before_read',170),('inside_guard_before_read',190),
            ('after_read_before_write',270),('after_write',370)]
    traces=[];coupled=breaks=0
    for label,at in phases:
        for pos in range(1,40):
            code=encode(0x12345678);fault=1<<(pos-1)
            real_at_read=code^(fault if at<225 else 0)
            latched,corrected,due=decode(real_at_read)
            real_end=latched^(fault if at>360 else 0)
            ideal_before_write=code^(fault if at<360 else 0)
            ideal_end,ideal_corrected,_=decode(ideal_before_write)
            if at>360: ideal_end^=fault
            real_count=int(corrected>0);ideal_count=int(ideal_corrected>0)
            same=(real_end,real_count)==(ideal_end,ideal_count)
            if label=='after_read_before_write': assert not same;breaks+=1
            else: assert same;coupled+=1
            if pos in (1,3,39):
                traces.append(dict(phase=label,bit=pos,real_count=real_count,
                    ideal_count=ideal_count,dirty_after=bool(real_end^code),same=same))
    # Position 1 is parity: suppressing parity corrections breaks binary observation.
    full=decode(encode(0)^1)[1];assert full==1 and full in PARITY
    # Padding bits never enter the codeword, assuming no cross-coupling to address/control.
    padding=0
    for pos in range(39,48):
        assert decode(encode(123)^(1<<pos))==(encode(123),0,False);padding+=1
    # A shared read bus may change after decode; an unlatched write uses wrong data.
    a=encode(0x12345678);b=encode(0x87654321)
    latch=decode(a^(1<<2))[0];unlatched=decode(b)[0]
    assert latch==a and unlatched!=a
    # First passage is irreversible, even if a third flip removes a prior error.
    state=0;first_passage=False
    for bit in (2,5,5):
        state^=1<<bit;first_passage|=state.bit_count()>1
    assert first_passage and state.bit_count()==1
    # A post-write arrival survives pass end and is counted at the next read.
    dirty=encode(0)^(1<<2);assert decode(dirty)[1]==3
    return dict(single_bit_cases=singles,double_bit_cases=doubles,
        padding_cases=padding,coupled_single_fault_cases=coupled,
        rmw_counter_divergence_cases=breaks,word_traces=traces,
        parity_witness=dict(full_count=1,data_count=0,binary_observations_differ=True),
        read_latch_witness=dict(latched_correct=True,unlatched_wrong_payload=True),
        first_passage_not_erased=True,post_write_residual_preserved=True,
        status='Finite Python algebra/event checks, not a verified RTL port')
