"""Candidate control/tag proof; CRC arithmetic is checked by check_crc.py.

All packet bits and arrival edges are adversarial at the transport cut. The
transport safety/progress proof is separate. No acceptance flag is assumed.
"""
import hashlib,json,subprocess,time,zlib
from pathlib import Path
from guard_proof import STUB
HERE=Path(__file__).resolve().parent

def oracle(length):
    zero=bytes(length)
    c=zlib.crc32(zero)
    columns=[zlib.crc32((1<<i).to_bytes(length,'little'))^c for i in range(8*length)]
    bits=[]
    for j in reversed(range(32)):
        mask=sum(1<<i for i,col in enumerate(columns) if col>>j&1)
        bits.append(f"(^(payload & 128'h{mask:032x})) ^ 1'b{(c>>j)&1}")
    return '{'+','.join(bits)+'}'

def main():
    source=(HERE/'candidate_link.sv').read_text()
    assertions=r'''
(* anyseq *) reg proof_crc_ok;
reg proof_seen=0;
reg [31:0] proof_target=0,proof_prepared_target=0;
reg [31:0] proof_tag[0:3];
integer j;
initial for(j=0;j<4;j=j+1) proof_tag[j]=0;
always @(posedge fast_clk) begin
 proof_seen<=1;
 assert($onehot0(check_valid));
 assert(!receipt || (checking && check_valid==0));
 assert(checking==(receipt || check_valid!=0));
 if(proof_seen && checking && $past(checking) && !$past(receipt)) begin
  assert(payload==$past(payload));
  assert(expected_crc==$past(expected_crc));
 end
 if(proof_seen) begin
  assert((&target_equal)==($past(payload[31:0])==$past(expected_target)));
 end
 // No flight may overlap the next beacon: established separately by the
 // full <=600.506ns roundtrip versus >=1567.98432ns frame spacing.
 assume(!checking || (!frame_pulse && !beacon_capture));
 if(check_valid[17]) begin
  assert(!receipt);
  assert((&target_equal)==(payload[31:0]==expected_target));
 end
 if(check_valid[17] && crc_good && (&target_equal) && !frame_pulse &&
    (&generation_equal) && uninterrupted && !invalidate && !loss) begin
  proof_tag[payload[1:0]]<=payload[31:0];
  proof_target<=expected_target;
 end
 if(installed) begin
  assert(installed_frame==proof_target);
  assert($past(check_valid[17]));
 end
 for(j=0;j<4;j=j+1) if(cache_low[j]) begin
  assert(cache_tag[j]==proof_tag[j][3:2]);
  assert(proof_tag[j][1:0]==j);
  assert(proof_tag[j][31:4]==0);
 end
 proof_prepared_target<=freeze_frame;
 if(prepared_permit) begin
  assert(proof_prepared_target[31:4]==0);
 end
'''
    assertions+='end\n'
    build=HERE.parent/'.build'/('physical-candidate-'+str(time.time_ns()));build.mkdir(parents=True)
    rows=[]
    for name in ['actual','early-install-mutant','tag-mutant']:
        code=source.replace('assign crc_good=&crc_equal && reserved_good;',
                            'assign crc_good=proof_crc_ok;')
        if name=='early-install-mutant':code=code.replace('if(check_valid[17]) begin','if(check_valid[0]) begin')
        if name=='tag-mutant':code=code.replace('cache_tag[payload[1:0]]<=payload[3:2];',"cache_tag[payload[1:0]]<=payload[3:2]^2'd1;")
        code=code.replace('endmodule',assertions+'\nendmodule')+'\n'+STUB
        (build/(name+'.sv')).write_text(code)
        command=f'read_verilog -formal -sv {name}.sv; prep -top proof; flatten; memory_map; opt; async2sync; opt; sat -seq 1 -tempinduct -maxsteps 24 -set-assumes -prove-asserts -verify -timeout 90 -dump_json {name}-counterexample.json -show dut.check_valid -show dut.receipt -show dut.crc_good -show dut.payload -show dut.expected_target -show dut.checking -show dut.beacon_capture -show dut.frame_pulse'
        r=subprocess.run(['yosys','-Q','-T','-p',command],cwd=build,text=True,capture_output=True,timeout=180)
        log=r.stdout+r.stderr;(build/(name+'.log')).write_text(log)
        row={'case':name,'proved':r.returncode==0 and 'Induction step proven: SUCCESS' in log,
             'counterexample':'model found for base case: FAIL' in log or 'SAT proof finished - model found' in log,
             'log_sha256':hashlib.sha256(log.encode()).hexdigest()}
        rows.append(row);print(row,flush=True)
        if name=='actual':assert row['proved'],log[-4000:]
        else:assert row['counterexample'] and not row['proved'],log[-4000:]
    report={'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'build':str(build),'cases':rows,
            'arithmetic_cut':'arbitrary CRC acceptance; independent full affine basis check in check_crc.py',
            'contract':'initialized; no candidate checking across the next frame beacon; proven transport bound',
            'scope':'all128 payload bits, valid-pipeline alignment, installed target and cache tag; not CRC arithmetic'}
    (build/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(build,flush=True)
if __name__=='__main__':main()
