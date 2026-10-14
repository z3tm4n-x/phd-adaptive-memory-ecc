"""Structural work certificate for the *published* ARM ELF, NOT a WCET.

Fail closed on a changed binary, an unrecognized PC write, an unranked cycle
or recursion. All alternatives in a function are charged, even incompatible
ones. Conditional instructions are charged as if executed. The small loops
have independently checked instruction/ranking templates; removing their
backedges must leave a DAG. There is deliberately no cycles/instruction knob.
"""
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from setup_tools import environment

HERE = Path(__file__).resolve().parent
ELF_HASH = '2daf3308d167b71f2c65f21dfd5b9acde00e93fe5f1cc3ada8581d50d254fb09'
BASE = 0xfffc0000
ROOT_FUNCTIONS = ('t105_driver_step',)
# Each loop can be entered only once per invocation (checked by the DAG).
# Bounds count visits to the whole loop, including its last non-taken branch.
LOOPS = (
    ('t105_crc32', 0x990, 0x9a8, 28, 'r0 increments by 1 to initial r0+28'),
    ('t105_driver_step', 0xb34, 0xb3c, 8, 'r3: controller+108 -> +140, step 4'),
    ('t105_driver_step', 0xb90, 0xb9c, 8, 'r3: controller+164 -> +196, step 4'),
    ('t105_driver_step', 0xbdc, 0xbf8, 4, 'r3: controller+108 -> +140, step 8; early exit safe'),
)
# Critical ranking setup and loop instructions. Full ELF identity is checked
# separately. These patterns also detect rank-breaking mutations independently.
PATTERNS = {
    0x928: [0xe3a0101c, 0xe1a00004, 0xe5848018, 0xe584e010, 0xe5846014, 0xeb00000d],
    0x978: [0xe3510000, 0x0a00000c, 0xe300cc94, 0xe0801001, 0xe3e02000, 0xe34fcffc,
            0xe4d03001, 0xe0233002, 0xe1500001, 0xe6ef3073, 0xe79c3103, 0xe0232422, 0x1afffff8],
    0xb24: [0xe285cf4a, 0xe284306c, 0xe284108c, 0x1a000029,
            0xe5a32004, 0xe1510003, 0x1afffffc],
    0xb84: [0xe28430a4, 0xe2852c02, 0xe28400c4, 0xe5b31004, 0xe1530000, 0xe4821004, 0x1afffffb],
    0xbdc: [0xe49c2004, 0xe5a32004, 0xe1530001, 0x0affffd4,
            0xe49c2004, 0xe5a32004, 0xe1530001, 0x1afffff7],
}
# Source/ABI address proof: r1/r5 is Device mailbox, never aliases controller;
# ip in the ERR loop is mailbox+296, r2 in the reply loop mailbox+512.
# Every other architectural data access is to OCM state, stack or CRC table.
MMIO_READ = {0x9ec, 0xa80, 0xa98, 0xaa4, 0xaac, 0xab4, 0xabc,
             0xae0, 0xaf4, 0xb44, 0xb50, 0xbdc, 0xbec, 0xc00, 0xc08}
MMIO_WRITE = {0xa30, 0xa60, 0xb98, 0xba8, 0xbc8, 0xc20, 0xc38, 0xc50}
KEYS = ('instructions', 'ocm_data_32bit_beats', 'mmio_reads', 'mmio_writes', 'dmb')


def parse(assembly, symbols):
    instructions = {}
    for line in assembly.splitlines():
        m = re.match(r'^([0-9a-f]+):\s+([0-9a-f]{8})\s+(\S+)\s*(.*)$', line)
        if m:
            a, word, op, operands = m.groups()
            instructions[int(a, 16)] = (int(word, 16), op, operands.split('@')[0].strip())
    functions = {}
    for line in symbols.splitlines():
        f = line.split()
        if len(f) == 4 and f[2] == 'T':
            functions[f[3]] = (int(f[0], 16), int(f[1], 16))
    return instructions, functions


def branch(word, pc):
    if word & 0x0e000000 != 0x0a000000:
        return None
    displacement = word & 0xffffff
    if displacement & 0x800000:
        displacement -= 1 << 24
    return pc + 8 + displacement * 4, bool(word & 0x01000000), word >> 28 == 14


def acyclic(graph):
    seen, active = set(), set()
    def visit(v):
        if v in active:
            raise ValueError('unranked cycle at ' + hex(v))
        if v in seen:
            return
        active.add(v)
        for n in graph[v]:
            if n not in graph:
                raise ValueError('branch outside function: ' + hex(n))
            visit(n)
        active.remove(v)
        seen.add(v)
    for v in graph:
        visit(v)


def analyze(ins, functions):
    for first, words in PATTERNS.items():
        if [ins[BASE+first+4*i][0] for i in range(len(words))] != words:
            raise ValueError('loop/call ranking template changed at ' + hex(first))
    by_address = {a: name for name, (a, _) in functions.items()}
    results, active = {}, set()
    def function(name):
        if name in active:
            raise ValueError('recursive call')
        if name in results:
            return results[name]['upper']
        active.add(name)
        start, size = functions[name]
        graph, calls, local = {}, {}, Counter()
        ranks = {BASE+end: (BASE+begin, cap) for fn, begin, end, cap, _ in LOOPS if fn == name}
        removed = set()
        for pc in range(start, start+size, 4):
            word, op, operands = ins[pc]
            if op == '.word':
                # Literal pools inside symbol extents are not executable.
                # Any CFG edge into one is rejected by acyclic().
                continue
            edge = branch(word, pc)
            return_op = (word & 0x0fffffff == 0x012fff1e or
                         (op.startswith('pop') and re.search(r'\bpc\b', operands)))
            if edge:
                target, call, unconditional = edge
                if call:
                    if target not in by_address:
                        raise ValueError('unknown call')
                    calls[pc] = by_address[target]
                    graph[pc] = [pc+4]
                else:
                    graph[pc] = [target] + ([] if unconditional else [pc+4])
            elif return_op:
                graph[pc] = [] if word >> 28 == 14 else [pc+4]
            else:
                # No jump tables, indirect calls, exception returns or other
                # PC writes are permitted in these four concrete functions.
                if (operands.split(',')[0] == 'pc' or
                    ('{' in operands and re.search(r'\bpc\b', operands)) or
                    op.startswith(('bx', 'blx', 'svc', 'swi', 'rfe'))):
                    raise ValueError('unmodeled control transfer at ' + hex(pc))
                graph[pc] = [pc+4]
            if pc in ranks:
                target, _ = ranks[pc]
                if target not in graph[pc]:
                    raise ValueError('rank edge missing')
                graph[pc].remove(target)
                removed.add(pc)
            weight = 1
            for fn, begin, end, cap, _ in LOOPS:
                if fn == name and BASE+begin <= pc <= BASE+end:
                    weight = cap
            local['instructions'] += weight
            off = pc-BASE
            memory = op.startswith(('ldr', 'str', 'ldm', 'stm', 'push', 'pop'))
            if off in MMIO_READ | MMIO_WRITE:
                expected = 'ldr' if off in MMIO_READ else 'str'
                if not op.startswith(expected):
                    raise ValueError('MMIO instruction changed')
                local['mmio_reads' if off in MMIO_READ else 'mmio_writes'] += weight
            elif memory:
                if '{' in operands:
                    beats = len(operands.split('{')[1].split('}')[0].split(','))
                else:
                    beats = 2 if op.startswith(('ldrd', 'strd')) else 1
                local['ocm_data_32bit_beats'] += weight * beats
            if op == 'dmb':
                local['dmb'] += weight
        if removed != set(ranks):
            raise ValueError('unverified rank')
        acyclic(graph)
        # Loop blocks have one external entry and no calls or nested cycles.
        # Prevent a DAG path from re-entering the same ranked loop elsewhere.
        for fn, begin, end, _, _ in LOOPS:
            if fn != name:
                continue
            nodes = set(range(BASE+begin, BASE+end+4, 4))
            incoming = {(v, n) for v, edges in graph.items() for n in edges if n in nodes and v not in nodes}
            if any(n != BASE+begin for _, n in incoming) or any(n in calls for n in nodes):
                raise ValueError('unsupported loop entry/call')
        total = local.copy()
        for callee in calls.values():
            total.update(function(callee))
        active.remove(name)
        results[name] = {'symbol_32bit_words': size//4, 'code_locations': len(graph),
                         'calls': list(calls.values()),
                         'upper': {k: total[k] for k in KEYS}}
        return results[name]['upper']
    for name in ROOT_FUNCTIONS:
        function(name)
    return results


def main():
    elf = HERE/'outputs/firmware.elf'
    digest = hashlib.sha256(elf.read_bytes()).hexdigest()
    if digest != ELF_HASH:
        raise ValueError('Re-establish ranking/address proofs for changed firmware')
    env = environment()
    assembly = subprocess.check_output(['arm-none-eabi-objdump', '-d', str(elf)], text=True, env=env)
    symbols = subprocess.check_output(['arm-none-eabi-nm', '-S', str(elf)], text=True, env=env)
    ins, functions = parse(assembly, symbols)
    functions_result = analyze(ins, functions)
    # Main's healthy loop: two MOVs, BL (charged separately), CMP, BGE.
    if [ins[BASE+0xc74+4*i][0] for i in range(5)] != [
            0xe3a01101, 0xe1a00004, 0xebffff55, 0xe3500000, 0xaafffffa]:
        raise ValueError('main healthy loop changed')
    step = functions_result['t105_driver_step']['upper'].copy()
    step['instructions'] += 5
    result = {
        'kind': 'structural upper per driver invocation plus main loop, NOT cycles or WCET',
        'ELF_sha256': digest, 'functions': functions_result, 'service_visit_upper': step,
        'ranked_loops': [{'function': f, 'first': hex(BASE+a), 'last': hex(BASE+b),
                         'visits_upper': n, 'ranking': why} for f,a,b,n,why in LOOPS],
        'aggregation': 'sum ALL branch alternatives, then add callees; intentionally not a feasible longest path',
        'unbounded_in_source': 'number of status-poll visits; per-access hardware completion; fault WFI is terminal',
        'model_parameters_ns': {'instruction_fetch_and_core_progress': None,
                               'OCM_32bit_data_access': None, 'GP_read_completion': None,
                               'GP_write_completion': None, 'DMB_additional_ordering': None},
        'service_upper_ns': None, 'is_WCET': False,
        'assumptions': ['fixed binary and reviewed ranking templates', 'valid aligned disjoint OCM/MMIO pointers',
                        'no code/data corruption or asynchronous exceptions',
                        'architectural execution terminates each instruction; no time implied'],
    }
    (HERE/'outputs/service-work.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
