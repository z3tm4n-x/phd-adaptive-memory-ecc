"""Bounded-budget safety proof attempt with actual executor endpoints.

Unlike rpc_contract.sv this does NOT substitute an abstract endpoint. Build-only
assertions are inserted in actual modules. No assumptions, no forced arm,
no narrowed timestamp/address/payload. ABC may return undecided: report it.
"""
import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

from integration_check import MODULES
from pdr_check import classify

HERE = Path(__file__).resolve().parent
PORT_CHECKS = '''
    // Queue ownership and credit belong to the ACTUAL RPC endpoint.
    always @(posedge mem_clk) begin
        assert(!retire[p] || queue_state[p*2+:2]==3);
        assert(queue_state[p*2+:2]==0 || occupied);
        if(queue_state[p*2+:2]==1 || queue_state[p*2+:2]==2)
            assert(response_ready);
        // Bad-input replies may remain high after being captured; a normal
        // release pulse must find the bridge ready on that exact edge.
        if(reply_valid[p] && queue_state[p*2+:2]==2) assert(response_ready);
    end
'''
CORE_CHECKS = '''
    always @(posedge clk) begin
        assert(!go || (!busy && ready));
        assert(!app_grant || (!control_due && state[grant_owner]==1));
        if(app_grant) begin
            assert(chosen[1:0]==1 || chosen[1:0]==2);
            assert(chosen[7:4]!=0);
        end
        if(state[0]==2) assert(busy && active_app && owner==0);
        if(state[1]==2) assert(busy && active_app && owner==1);
        if(release_due && active_app) assert(state[owner]==2);
        assert(!(state[0]==2 && state[1]==2));
    end
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--seconds', type=int, default=120)
    p.add_argument('--write', action='store_true')
    p.add_argument('--ownership-invariants', action='store_true',
                   help='assert (never assume) exact queue/RPC occupancy relations')
    args = p.parse_args()
    if not 1 <= args.seconds <= 120:
        p.error('predeclared maximum 120s per attempt')
    start = time.monotonic()
    out = HERE/'.build'/f'composition-{time.time_ns()}'
    out.mkdir(parents=True)
    originals = {}
    for module in MODULES:
        path = HERE/'rtl'/f'{module}.sv'
        source = path.read_text(encoding='utf-8')
        originals[path.name] = sha(path)
        if module == 'executor':
            marker = '    end endgenerate'
            if source.count(marker) != 1:
                raise ValueError('executor instrumentation drift')
            properties = PORT_CHECKS
            if args.ownership_invariants:
                source = source.replace('wire link_ready, send, response_ready, occupied;',
                                        'wire link_ready, send, response_ready, occupied, proof_delivered, proof_replied;')
                source = source.replace('.dst_occupied(occupied));',
                                        '.dst_occupied(occupied),.proof_delivered(proof_delivered),.proof_replied(proof_replied));')
                properties += '''
                always @(posedge mem_clk) begin
                    assert(proof_delivered == (queue_state[p*2+:2]!=0));
                    assert(!proof_replied || queue_state[p*2+:2]==3);
                end
                '''
            source = source.replace(marker, properties+marker)
        elif module == 'executor_core':
            source = source.replace('endmodule', CORE_CHECKS+'\nendmodule')
        elif module == 'rpc_cdc' and args.ownership_invariants:
            source = source.replace('output wire dst_occupied\n',
                                    'output wire dst_occupied, proof_delivered, proof_replied\n')
            source = source.replace('endmodule',
                                    'assign proof_delivered=delivered; assign proof_replied=replied;\nendmodule')
        (out/path.name).write_text(source, encoding='utf-8')
    # Backend contains six already-proved invariants, retained and proved
    # again, not imported as assumptions. Sixteen new composition properties.
    count = 26 if args.ownership_invariants else 22
    # A property-only root: ordinary executor output pins are NOT bad-state
    # predicates. ABC otherwise treats normal AIGER outputs as properties too.
    source = (HERE/'rtl/executor.sv').read_text()
    ports = re.search(r'\)\(\n(.*?)\n\);', source, re.S)[1]
    declarations = [s.strip().rstrip(',') for s in re.split(r'(?=input wire|output wire)', ports) if s.strip()]
    inputs = [s for s in declarations if s.startswith('input')]
    outputs = [s.replace('output wire', 'wire', 1)+';' for s in declarations if s.startswith('output')]
    harness = ('module composition #(parameter WORD_BITS=19)('+','.join(inputs)+');\n'
               +'\n'.join(outputs)+'\nexecutor dut(.*);\nendmodule\n')
    (out/'root.sv').write_text(harness, encoding='utf-8')
    script = ('read_verilog -formal -sv '+ ' '.join(m+'.sv' for m in MODULES)+' root.sv; '
              'prep -top composition; flatten; memory_map; clk2fflogic; opt; techmap; opt; '
              'abc -g AND; opt_clean; write_aiger -zinit -symbols -map design.map design.aig')
    (out/'build.ys').write_text(script+'\n', encoding='utf-8')
    with (out/'yosys.log').open('w') as log:
        synth = subprocess.run(['yosys', '-Q', '-T', '-s', 'build.ys'], cwd=out,
                               stdout=log, stderr=subprocess.STDOUT, timeout=120)
    if synth.returncode:
        raise RuntimeError(f'composition translation failed: {out}')
    header = (out/'design.aig').read_bytes().splitlines()[0].decode()
    fields = header.split()
    if len(fields) != 10 or fields[4] != '0' or int(fields[6]) != count or any(int(v) for v in fields[7:]):
        raise ValueError(f'unexpected property-only AIGER: {header}')
    command = f'read_aiger design.aig; pdr -a -v -d -I invariant.pla -T {args.seconds}'
    engine = subprocess.run(['yosys-abc', '-c', command], cwd=out, text=True,
                            capture_output=True, timeout=args.seconds+30)
    (out/'abc.log').write_text(engine.stdout+engine.stderr, encoding='utf-8')
    result = classify(header, engine.stdout+engine.stderr, count, engine.returncode)
    result.update(expected_properties=count, new_properties=count-6, aiger_header=header,
                  ownership_invariants=args.ownership_invariants,
                  source_sha256=originals, checker_sha256=sha(Path(__file__)),
                  build_source_sha256={p.name: sha(p) for p in out.glob('*.sv')},
                  evidence_sha256={p.name: sha(p) for p in out.iterdir() if p.suffix in ('.ys', '.log', '.aig', '.map', '.pla')},
                  raw_directory=str(out), elapsed_s=round(time.monotonic()-start, 3),
                  time_limit_s=args.seconds, clock_model='arbitrary Boolean edges; clk2fflogic',
                  assumptions=0, word_bits=19, timestamp_bits=64,
                  limitations=['safety only; no bounded liveness or physical CDC',
                               'unproved properties must remain open',
                               'reachability/nonvacuity also exercised by integration regression'])
    if args.write:
        name = 'composition_ownership.json' if args.ownership_invariants else 'composition.json'
        (HERE/'outputs'/name).write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
