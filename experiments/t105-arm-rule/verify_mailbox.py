"""C/RTL co-simulation with real AXI channel stalls; independent raw oracle."""
import hashlib,json,struct,subprocess,zlib
from pathlib import Path
from batch_model import collect
from verify_batch import decision_expected
HERE=Path(__file__).resolve().parent

def main():
    root=HERE/".build/mailbox";root.mkdir(parents=True,exist_ok=True)
    sources=[HERE/f for f in ("mailbox_vpi.c","rule.c","batch.c","crc32.c")]
    # Installed Ubuntu wrapper contains the invalid literal compiler flag
    # "0-3". Compile against its public VPI headers/libraries directly;
    # do not alter the installed tool or silently ignore a source error.
    run=subprocess.run(["gcc","-O2","-std=c11","-Wall","-Wextra","-Werror",
                       "-fPIC","-shared","-I/usr/include/iverilog","-I"+str(HERE),
                       *map(str,sources),"-lveriuser","-lvpi","-o","mailbox_vpi.vpi"],cwd=root,
                       text=True,capture_output=True)
    (root/"build.log").write_text(run.stdout+run.stderr)
    assert run.returncode==0,run.stdout+run.stderr
    exe=root/"tb.vvp"
    subprocess.run(["iverilog","-g2012","-s","tb_mailbox","-o",str(exe),
      *[str(HERE/x) for x in ("history_batch.sv","rule_mailbox.sv","tb_mailbox.sv")]],check=True)
    results=[]
    for mode,label in enumerate(("valid","bad-crc","replay-sequence","wrong-generation",
                                 "forbidden-runtime-config")):
        folder=root/label;folder.mkdir(exist_ok=True)
        run=subprocess.run(["vvp","-M",str(root),"-m","mailbox_vpi",str(exe),"+MODE="+str(mode)],
                           cwd=folder,text=True,capture_output=True,timeout=30)
        log=run.stdout+run.stderr;(folder/"run.log").write_text(log)
        assert run.returncode==0 and ("MAILBOX_OK" if mode in (0,4) else "MAILBOX_REJECTED") in log,log
        if mode==4:assert "CONFIG_READONLY rejected=1013" in log,log
        raw=[]
        for line in (folder/"raw.txt").read_text().splitlines():
            q,v=line.split();q=int(q);v=int(v,16)
            # The testbench starts driving at the first falling edge;
            # the free-running peripheral tick has already advanced once.
            raw.append((q+1,(v>>2)&((1<<64)-1),v&1,(v>>1)&1))
        records=[];groups=[];previous=0
        for line in (folder/"trace.txt").read_text().splitlines():
            b,d=line.split();b=struct.unpack("<10Q4I",int(b,16).to_bytes(96,"little"))
            d=struct.unpack("<QQQII",int(d,16).to_bytes(32,"little"))
            records.append((b,d));groups.append((b[3],[e for e in raw if previous<e[0]<=b[3]]))
            previous=b[3]
        expected=collect(1,groups)
        for (b,d),(eb,state) in zip(records,expected):
            assert b==eb,(label,b,eb)
            assert d==decision_expected(b[0],state),(label,d,state)
            assert d[-1]==zlib.crc32(struct.pack("<QQQI",*d[:-1]))
        results.append({"case":label,"packets":len(records),"events":len(raw),
          "log":log.strip(),"trace_sha256":hashlib.sha256((folder/"trace.txt").read_bytes()).hexdigest()})
    out={"kind":"native production C + actual AXI-Lite/collector RTL; NOT ARM/AXI timing",
         "independent_checker":"Python raw-event Oracle, no batch C or RTL helper",
         "cases":results,"partial_commit_rejected":True,"immutable_banks":True,
         "independent_AW_W_and_BR_backpressure":True,
         "runtime_configuration":"absent; all 1013 non-command aligned addresses reject with no retained snapshot/decision/ACK change",
         "CPU_WCET":None}
    (HERE/"outputs/mailbox.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
