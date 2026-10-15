"""Test-only empty-history compression around unchanged production C.

Not a controller and not a CPU timing model. Public ABI is the only shared
definition; this file does not call the absolute-deadline test oracle.
"""
import ctypes as C
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ARM=HERE.parent/'t105-arm-rule'
MAX=(1<<64)-1


class Rule(C.Structure):
    _fields_=[(x,C.c_uint64) for x in ('now','generation','last_err','short_left','long_left','recovery_left')]+[
        ('flags',C.c_uint32),('reserved',C.c_uint32)]


class State(C.Structure):
    _fields_=[('rule',Rule),('sequence',C.c_uint64),('start_tick',C.c_uint64)]


class Batch(C.Structure):
    _fields_=[(x,C.c_uint64) for x in ('sequence','base_generation','end_generation','end_tick',
        'start_tick','first_err_source','last_err_source','first_err_tick','last_err_tick','last_recovery_tick')]+[
        (x,C.c_uint32) for x in ('event_count','err_count','flags','reserved')]


class Decision(C.Structure):
    _fields_=[(x,C.c_uint64) for x in ('sequence','generation','not_before')]+[
        ('flags',C.c_uint32),('crc',C.c_uint32)]


def library():
    out=HERE/'.build/empty-rule';out.mkdir(parents=True,exist_ok=True)
    so=out/'production.so'
    subprocess.run(['gcc','-shared','-fPIC','-O2','-std=c11','-Wall','-Wextra','-Werror',
                    *[str(ARM/p) for p in ('rule.c','batch.c','crc32.c')],'-o',str(so)],check=True)
    lib=C.CDLL(str(so))
    lib.t105_batch_init.argtypes=[C.POINTER(State)];lib.t105_batch_init.restype=None
    lib.t105_batch_apply.argtypes=[C.POINTER(State),C.POINTER(Batch)];lib.t105_batch_apply.restype=C.c_int
    lib.t105_decide.argtypes=[C.POINTER(State),C.POINTER(Decision)];lib.t105_decide.restype=C.c_int
    return lib


def apply(lib,state,batch):
    if not lib.t105_batch_apply(C.byref(state),C.byref(batch)):
        raise ValueError('production rejects batch')
    d=Decision()
    if not lib.t105_decide(C.byref(state),C.byref(d)):
        raise ValueError('production decision fault')
    return d


def empty_packet(state,end):
    return Batch(state.sequence+1,state.rule.generation,state.rule.generation,end,state.start_tick,
                 0,0,0,0,0,0,0,1+2*bool(state.rule.flags&1),0)


def advance_empty(lib,state,packets,step):
    """Exactly k no-event packets, represented by a sequence adjustment + C.

    Only the caller can prove the physical interval is empty. This function
    is never a runtime reset or a permissible way to omit a raw event.
    Returned before/after state plus count/step defines every omitted packet.
    It does NOT establish the delivery time or validity of an installed LOW.
    """
    if packets<1 or step<1 or not state.sequence or not state.rule.flags&2 or state.rule.flags&8:
        raise ValueError('not a live nonfaulted sequence')
    end=state.rule.now+packets*step
    if end>MAX or state.sequence+packets>MAX:
        raise ValueError('64-bit overflow')
    before=bytes(state)
    state.sequence+=packets-1
    d=apply(lib,state,empty_packet(state,end))
    return {'before':before.hex(),'after':bytes(state).hex(),'decision':bytes(d).hex(),
            'packets':packets,'step_slow_ticks':step,'represented_elapsed_ns':packets*step*20}
