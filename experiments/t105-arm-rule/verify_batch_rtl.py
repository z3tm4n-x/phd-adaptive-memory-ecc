"""Actual collector vs all raw records; collision and omission mutation."""
import hashlib,json,struct,subprocess
from pathlib import Path
from batch_model import collect
HERE=Path(__file__).resolve().parent

def main():
    build=HERE/".build/batch-rtl";build.mkdir(parents=True,exist_ok=True)
    claims=[3,8,19,100,1000,2010,2100,2200,4500]
    ack={q+3 for q in claims}
    events={}
    lost=False
    for q in range(1,2001):
        lost=not lost
        events[q]=(q,5*q-1,q%31==0,lost)
    events.update({2100:(2100,10499,True,False),2200:(2200,10999,True,False)})
    # Include events on exactly the cut and acknowledgement edges.
    groups=[];prev=0
    for q in claims:
        groups.append((q-1,[e for t,e in sorted(events.items()) if prev<t<q]))
        prev=q-1
    expected=[b for b,_ in collect(0,groups)]
    lines=[];gen=0
    for q in range(4510):
        if q in events:
            _,src,err,loss=events[q];gen+=1
            record=(1<<130)|(gen<<66)|(src<<2)|(int(loss)<<1)|int(err)
        else:record=0
        lines.append(f"{q} {int(q==0)} {record:x} {int(q in claims)} {int(q in ack)}")
    (build/"inputs.txt").write_text("\n".join(lines)+"\n")
    source=(HERE/"history_batch.sv").read_text()
    rows=[]
    for mutant in (False,True):
        label="cut-event-omitted" if mutant else "actual"
        code=source.replace("if(event_valid) begin","if(event_valid && !cut) begin") if mutant else source
        sv=build/(label+".sv");sv.write_text(code)
        exe=build/(label+".vvp");output=build/(label+".txt")
        subprocess.run(["iverilog","-g2012","-s","tb_history_batch","-o",str(exe),
                        str(sv),str(HERE/"tb_history_batch.sv")],check=True)
        # Icarus' Verilog $fopen mangles non-ASCII command-line strings on
        # this build. ASCII relative file names, not a second path encoding.
        run=subprocess.run(["vvp",str(exe),"+INPUT=inputs.txt",
                            "+OUTPUT="+output.name],cwd=build,
                           text=True,capture_output=True,timeout=30)
        if not output.exists(): raise RuntimeError(run.stdout+run.stderr)
        observed=[]
        for line in output.read_text().splitlines():
            q,raw=line.split();blob=int(raw,16).to_bytes(96,"little")
            observed.append(struct.unpack("<10Q4I",blob))
        same=run.returncode==0 and observed==expected
        assert same if not mutant else not same,(label,run.stdout,observed,expected)
        rows.append({"case":label,"matches":same,"exit":run.returncode,"log":run.stdout+run.stderr})
    result={"status":"actual RTL collector checked, including immutable snapshots",
      "source_sha256":hashlib.sha256(source.encode()).hexdigest(),
      "source_events":len(events),"snapshot_count":len(expected),"cases":rows}
    (HERE/"outputs/batch-rtl.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
