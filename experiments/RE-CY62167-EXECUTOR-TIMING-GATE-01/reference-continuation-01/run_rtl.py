"""Execute actual RTL against independent Python-produced logical vectors."""
import hashlib, itertools, json, os, subprocess, time
from pathlib import Path
import witness
ROOT=Path(__file__).resolve().parent
TMP=ROOT.parents[3]/"tmp/iverilog"
BIN=Path(os.environ.get("IVERILOG_BIN",str(TMP/"ucrt64/bin")))
def main():
    TMP.mkdir(parents=True,exist_ok=True)
    vectors=[]
    def add(bus,expected,kind,err,write,fault,mode=0):
        vectors.append(f"{bus:012x} {expected:012x} {kind} {err} {write} {fault} {mode}")
    for image in (0,0xffffffff,0xdeadbeef,0xaaaaaaaa,0x55555555):
        cw=witness.encode(image); bus=witness.pack(cw)
        for e in (0,1,2,4,7): add(bus,bus,1,e,int(e!=0),0)
        for bit in range(39): add(witness.pack(cw^(1<<bit)),bus,1,0,1,0)
        for a,b in itertools.combinations(range(39),2): add(witness.pack(cw^(1<<a)^(1<<b)),0,1,7,0,1)
        add(bus,bus,2,7,0,0)
        for mode in range(5): add(image,bus,0,0,1,0,mode)
    raw=("\n".join(vectors)+"\n").encode()
    (TMP/"vectors.txt").write_bytes(raw)
    start=time.perf_counter()
    commands=[
      [str(BIN/"iverilog.exe"),"-g2012","-s","reference_tb","-o","../../../../tmp/iverilog/reference.vvp","reference_slot.sv","reference_tb.sv"],
      [str(BIN/"vvp.exe"),"../../../../tmp/iverilog/reference.vvp","+vectors=../../../../tmp/iverilog/vectors.txt"]]
    commands += [
      [str(BIN/"iverilog.exe"),"-g2012","-s","schedule_tb","-o","../../../../tmp/iverilog/schedule.vvp","reference_slot.sv","reference_schedule.sv","schedule_tb.sv"],
      [str(BIN/"vvp.exe"),"../../../../tmp/iverilog/schedule.vvp"]]
    results=[]
    env=os.environ.copy()
    env["PATH"]=str(BIN)+os.pathsep+env.get("PATH","")
    for cmd in commands:
        r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=60,env=env)
        results.append({"command":cmd,"exit_code":r.returncode,"stdout":r.stdout,"stderr":r.stderr})
        if r.returncode: break
    mutations=[]
    source=(ROOT/"reference_slot.sv").read_text()
    for name,old,new in (
        ("direct_bus_to_codeword","code=from_bus(latched)","code=latched[38:0]"),
        ("omit_ERR_only","(corrected || |latched_err)","corrected")):
        assert source.count(old)==1
        modified=source.replace(old,new)
        (TMP/"mutant_slot.sv").write_text(modified,encoding="utf-8",newline="\n")
        comp=subprocess.run([str(BIN/"iverilog.exe"),"-g2012","-s","reference_tb","-o",
          "../../../../tmp/iverilog/mutant.vvp","../../../../tmp/iverilog/mutant_slot.sv",
          "reference_tb.sv"],cwd=ROOT,text=True,capture_output=True,timeout=60,env=env)
        sim=subprocess.run([str(BIN/"vvp.exe"),"../../../../tmp/iverilog/mutant.vvp",
          "+vectors=../../../../tmp/iverilog/vectors.txt"],cwd=ROOT,text=True,capture_output=True,timeout=60,env=env) if comp.returncode==0 else None
        mutations.append({"mutation":name,"source_sha256":hashlib.sha256(modified.encode()).hexdigest(),
          "compile_exit":comp.returncode,"simulation_exit":None if sim is None else sim.returncode,
          "stdout":None if sim is None else sim.stdout,
          "rejected":comp.returncode==0 and sim is not None and sim.returncode!=0 and "FATAL:" in sim.stdout})
    out={"tool":"Icarus Verilog 13.0 stable, MSYS2 1~13.0-2","vectors":len(vectors),
      "vector_sha256":hashlib.sha256(raw).hexdigest(),"wall_s":time.perf_counter()-start,"runs":results,"sentinels":mutations,
      "scope":"actual slot RTL and integrated bounded scheduler simulation; epoch-state injection explicitly skips full prep; ideal digital SRAM stub, not analog/STA"}
    (ROOT/"rtl_results.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(out,indent=2))
    assert len(results)==4 and all(x["exit_code"]==0 for x in results)
    assert f"PASS reference_slot vectors={len(vectors)}" in results[1]["stdout"]
    assert "PASS schedule prep_prefix=5 scrub_slots=1024" in results[3]["stdout"]
    assert all(m["rejected"] for m in mutations)
if __name__=="__main__": main()
